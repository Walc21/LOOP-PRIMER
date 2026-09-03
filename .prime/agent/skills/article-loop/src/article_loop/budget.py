"""Durable, conservative budget accounting for M12.

The ledger is a local append-only hash chain.  A reservation is the only
admission primitive exposed to a consumer: it is made under the run lock,
counts against all applicable limits, and remains open until a receipt proves
reconciliation or non-admission.  Unknown outcomes stay ``uncertain``.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Any, Callable, Iterable, Mapping, Sequence

try:
    import yaml
except ImportError:  # pragma: no cover - project environments already use PyYAML
    yaml = None


if yaml is not None:
    class _UniqueSafeLoader(yaml.SafeLoader):
        """Safe YAML loader which rejects duplicate mapping keys."""

    def _construct_unique_mapping(loader, node, deep=False):  # noqa: ANN001, ANN202
        loader.flatten_mapping(node)
        mapping = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            try:
                duplicate = key in mapping
            except TypeError as error:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping", node.start_mark,
                    "found an unhashable mapping key", key_node.start_mark,
                ) from error
            if duplicate:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping", node.start_mark,
                    f"found duplicate key: {key!r}", key_node.start_mark,
                )
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    _UniqueSafeLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        _construct_unique_mapping,
    )

from .observability import StructuredLogger


SCHEMA_VERSION = "1.0.0"
MAX_INTEGER = 2**63 - 1
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")
_EVENT_TYPES = frozenset({
    "AUTHORIZATION", "RESERVED", "ADMITTED", "RECONCILED", "RELEASED",
    "UNCERTAIN", "PROGRESS", "ALERT", "PAUSED", "RESUMED", "STOPPED",
})
_ALERT_THRESHOLDS = (0.50, 0.80, 0.95, 1.00)


class BudgetError(RuntimeError):
    """Base error for M12 budget operations."""


class BudgetIntegrityError(BudgetError):
    """The budget ledger or its content-addressed events are not trustworthy."""


class BudgetExceeded(BudgetError):
    """A reservation would exceed a configured limit."""


class BudgetAuthorizationError(BudgetError):
    """Live admission lacks a valid, run-bound authorization."""


class BudgetIdempotencyError(BudgetError):
    """A repeated operation conflicts with its original durable bytes."""


class BudgetStateError(BudgetError):
    """A reservation or control transition is not valid in its current state."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _timestamp(value: Any, label: str = "timestamp") -> str:
    if not isinstance(value, str):
        raise BudgetError(f"{label} is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise BudgetError(f"{label} is invalid") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise BudgetError(f"{label} must contain a timezone")
    return value


def _safe_id(value: Any, label: str, *, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise BudgetError(f"{label} is invalid")
    return value


def _integer(value: Any, label: str, *, allow_none: bool = False) -> int | None:
    if value is None and allow_none:
        return None
    if type(value) is not int or value < 0 or value > MAX_INTEGER:
        raise BudgetError(f"{label} must be a non-negative bounded integer")
    return value


def _add(left: int, right: int, label: str) -> int:
    if type(left) is not int or type(right) is not int or left < 0 or right < 0:
        raise BudgetError(f"{label} is not a non-negative integer")
    result = left + right
    if result > MAX_INTEGER:
        raise BudgetError(f"{label} overflows the canonical integer bound")
    return result


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _validate_payload(payload: Mapping[str, Any]) -> None:
    """Keep durable budget payloads scalar, bounded and non-sensitive by shape."""
    if not isinstance(payload, Mapping):
        raise BudgetError("budget payload must be an object")
    for key, value in payload.items():
        if not isinstance(key, str) or not key or len(key) > 128:
            raise BudgetError("budget payload key is invalid")
        if value is None or isinstance(value, bool):
            continue
        if type(value) is int:
            if value < 0 or value > MAX_INTEGER:
                raise BudgetError(f"budget payload integer is invalid: {key}")
            continue
        if isinstance(value, float):
            if not math.isfinite(value) or value < 0:
                raise BudgetError(f"budget payload number is invalid: {key}")
            continue
        if isinstance(value, str):
            if len(value) > 512 or "\x00" in value:
                raise BudgetError(f"budget payload string is invalid: {key}")
            continue
        raise BudgetError(f"budget payload value is not scalar: {key}")


@dataclass(frozen=True)
class BudgetLimits:
    """Hierarchical limits; ``None`` means not configured for that dimension."""

    total_tokens: int | None = None
    per_cycle_tokens: int | None = None
    per_department_tokens: int | None = None
    per_role_tokens: int | None = None
    per_model_tokens: int | None = None
    max_calls: int | None = None
    max_concurrent_children: int | None = None
    max_retries: int | None = None
    max_wall_time_seconds: int | None = None
    max_cycles: int | None = None
    max_cycles_without_improvement: int | None = None
    max_extra_judgments: int | None = None

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            _integer(value, name, allow_none=True)


@dataclass(frozen=True)
class RunAuthorization:
    run_id: str
    profile: str | None
    config_hash: str
    provider: str | None
    model: str | None
    token_limit: int
    approved_at: str
    approval_reference: str
    routing_policy_hash: str | None = None
    max_run_cost_microunits: int | None = None
    currency: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RunAuthorization":
        if not isinstance(value, Mapping):
            raise BudgetAuthorizationError("authorization must be an object")
        run_id = _safe_id(value.get("run_id"), "authorization.run_id")
        profile = _safe_id(value.get("profile"), "authorization.profile", allow_none=True)
        config_hash = value.get("config_hash")
        if not isinstance(config_hash, str) or _SHA.fullmatch(config_hash) is None:
            raise BudgetAuthorizationError("authorization.config_hash is invalid")
        provider = _safe_id(value.get("provider"), "authorization.provider", allow_none=True)
        model = _safe_id(value.get("model"), "authorization.model", allow_none=True)
        token_limit = _integer(value.get("token_limit"), "authorization.token_limit")
        approved_at = _timestamp(value.get("approved_at"), "authorization.approved_at")
        reference = value.get("approval_reference")
        if not isinstance(reference, str) or not reference.strip() or len(reference) > 256:
            raise BudgetAuthorizationError("authorization.approval_reference is invalid")
        routing_policy_hash = value.get("routing_policy_hash")
        if routing_policy_hash is not None and (
            not isinstance(routing_policy_hash, str) or _SHA.fullmatch(routing_policy_hash) is None
        ):
            raise BudgetAuthorizationError("authorization.routing_policy_hash is invalid")
        max_run_cost = _integer(
            value.get("max_run_cost_microunits"),
            "authorization.max_run_cost_microunits", allow_none=True,
        )
        currency = value.get("currency")
        if currency is not None and (
            not isinstance(currency, str) or re.fullmatch(r"[A-Z]{3}", currency) is None
        ):
            raise BudgetAuthorizationError("authorization.currency is invalid")
        if (max_run_cost is None) != (currency is None):
            raise BudgetAuthorizationError("authorization monetary ceiling and currency must be paired")
        return cls(
            run_id, profile, config_hash, provider, model, token_limit,
            approved_at, reference.strip(), routing_policy_hash,
            max_run_cost, currency,
        )

    def public(self) -> dict[str, Any]:
        result = {
            "run_id": self.run_id,
            "profile": self.profile,
            "config_hash": self.config_hash,
            "provider": self.provider,
            "model": self.model,
            "token_limit": self.token_limit,
            "approved_at": self.approved_at,
            "approval_reference": self.approval_reference,
        }
        # Preserve the historical event bytes and fixtures for legacy
        # single-target authorizations.
        if self.routing_policy_hash is not None:
            result["routing_policy_hash"] = self.routing_policy_hash
        if self.max_run_cost_microunits is not None:
            result["max_run_cost_microunits"] = self.max_run_cost_microunits
            result["currency"] = self.currency
        return result


class ManualClock:
    """Injectable UTC/monotonic clock for deterministic tests."""

    def __init__(self, *, current: datetime | None = None, monotonic: float = 0.0):
        self.current = current or datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.monotonic_value = monotonic

    def now_utc(self) -> str:
        return self.current.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def monotonic(self) -> float:
        return self.monotonic_value

    def advance(self, *, seconds: int | float = 0) -> None:
        if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError("seconds must be finite and non-negative")
        self.current += timedelta(seconds=seconds)
        self.monotonic_value += float(seconds)


def _limits_from_mapping(value: Mapping[str, Any]) -> BudgetLimits:
    if not isinstance(value, Mapping):
        raise BudgetError("budget limits must be an object")
    aliases = {
        "tokens": "total_tokens", "total_token_limit": "total_tokens",
        "wall_time_seconds": "max_wall_time_seconds",
        "max_token_calls": "max_calls",
    }
    normalized: dict[str, Any] = {}
    for key, item in value.items():
        normalized[aliases.get(key, key)] = item
    fields = set(BudgetLimits.__dataclass_fields__)
    unknown = set(normalized) - fields
    if unknown:
        raise BudgetError("unknown budget limits: " + ", ".join(sorted(unknown)))
    return BudgetLimits(**{key: normalized.get(key) for key in fields})


def load_budget_config(root: str | Path) -> Mapping[str, Any]:
    if yaml is None:
        raise BudgetError("PyYAML is required to load budget configuration")
    path = Path(root) / "config" / "budgets.yaml"
    if path.is_symlink() or not path.is_file():
        raise BudgetError("config/budgets.yaml is missing or unsafe")
    try:
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueSafeLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise BudgetError("config/budgets.yaml cannot be read") from error
    if not isinstance(value, Mapping):
        raise BudgetError("config/budgets.yaml must contain an object")
    return value


class BudgetLedger:
    """A hash-bound budget ledger for exactly one ``run_id``."""

    def __init__(
        self,
        root: str | Path,
        run_id: str,
        *,
        limits: BudgetLimits | None = None,
        profile: str | None = None,
        config_hash: str | None = None,
        currency: str | None = None,
        max_run_cost_microunits: int | None = None,
        live_enabled: bool = False,
        deadline_at: str | None = None,
        max_integer: int = MAX_INTEGER,
        orphan_after_seconds: int = 900,
        clock: Any | None = None,
        logger: StructuredLogger | None = None,
        inference_policy: Mapping[str, Any] | None = None,
        routing_policy_hash: str | None = None,
    ):
        raw_root = Path(root)
        if raw_root.is_symlink() or not raw_root.is_dir():
            raise BudgetError("root must be an existing non-symlink directory")
        self.root = raw_root.resolve()
        self.run_id = _safe_id(run_id, "run_id")
        if type(max_integer) is not int or max_integer < 1 or max_integer > MAX_INTEGER:
            raise BudgetError("max_integer is invalid")
        self.max_integer = max_integer
        self.limits = limits or BudgetLimits()
        for name, value in asdict(self.limits).items():
            if value is not None and value > self.max_integer:
                raise BudgetError(f"{name} exceeds max_integer")
        self._limits_hash = _hash(_canonical(asdict(self.limits)))
        self.profile = _safe_id(profile, "profile", allow_none=True)
        if config_hash is None:
            config_hash = _hash(_canonical({"limits": asdict(self.limits), "profile": self.profile}))
        if not isinstance(config_hash, str) or _SHA.fullmatch(config_hash) is None:
            raise BudgetError("config_hash is invalid")
        self.config_hash = config_hash
        self.inference_policy = dict(inference_policy) if isinstance(inference_policy, Mapping) else None
        computed_routing_hash = (
            _hash(_canonical(self.inference_policy)) if self.inference_policy is not None else None
        )
        if routing_policy_hash is not None and (
            not isinstance(routing_policy_hash, str) or _SHA.fullmatch(routing_policy_hash) is None
        ):
            raise BudgetError("routing_policy_hash is invalid")
        if routing_policy_hash is not None and routing_policy_hash != computed_routing_hash:
            raise BudgetIntegrityError("routing policy hash differs from configured policy")
        self.routing_policy_hash = routing_policy_hash or computed_routing_hash
        if currency is not None:
            if not isinstance(currency, str) or re.fullmatch(r"[A-Z]{3}", currency) is None:
                raise BudgetError("currency must be an ISO-like uppercase code")
        self.currency = currency
        self.max_run_cost_microunits = _integer(
            max_run_cost_microunits, "max_run_cost_microunits", allow_none=True,
        )
        if self.max_run_cost_microunits is not None and self.currency is None:
            raise BudgetError("monetary ceiling requires a currency")
        if type(live_enabled) is not bool:
            raise BudgetError("live_enabled must be boolean")
        self.live_enabled = live_enabled
        self.deadline_at = _timestamp(deadline_at, "deadline_at") if deadline_at is not None else None
        self.orphan_after_seconds = _integer(orphan_after_seconds, "orphan_after_seconds")
        self.clock = clock or ManualClock(current=datetime.now(timezone.utc), monotonic=time.monotonic())
        if not callable(getattr(self.clock, "now_utc", None)) or not callable(getattr(self.clock, "monotonic", None)):
            raise BudgetError("clock must expose now_utc() and monotonic()")
        self._started_monotonic = float(self.clock.monotonic())
        self.budget_dir = self.root / "state" / "budgets"
        self.lock_dir = self.root / "state" / "locks"
        self._ensure_dir(self.budget_dir)
        self._ensure_dir(self.lock_dir)
        existing = self.read_events() if self.ledger_path.exists() else []
        self._resume_elapsed = float(existing[-1]["monotonic_elapsed_seconds"]) if existing else 0.0
        persisted_deadlines = [
            item["payload"].get("deadline_at")
            for item in existing
            if isinstance(item.get("payload"), Mapping) and item["payload"].get("deadline_at")
        ]
        if persisted_deadlines:
            deadlines = [_parse_datetime(value) for value in persisted_deadlines]
            if self.deadline_at is not None:
                deadlines.append(_parse_datetime(self.deadline_at))
            self.deadline_at = min(deadlines).isoformat().replace("+00:00", "Z")
        persisted_reservations = [
            item["payload"] for item in existing
            if item.get("event_type") == "RESERVED" and isinstance(item.get("payload"), Mapping)
        ]
        if persisted_reservations:
            persisted = persisted_reservations[0]
            expected_binding = {
                "budget_config_hash": self.config_hash,
                "budget_limits_hash": self._limits_hash,
                "budget_max_integer": self.max_integer,
                "budget_currency": self.currency,
            }
            if self.max_run_cost_microunits is not None:
                expected_binding["budget_max_run_cost_microunits"] = self.max_run_cost_microunits
            actual_binding = {key: persisted.get(key) for key in expected_binding}
            if actual_binding != expected_binding:
                raise BudgetIntegrityError("run budget binding cannot be enlarged or changed")
        self.logger = logger or StructuredLogger(self.root, self.run_id)

    @classmethod
    def from_project(
        cls,
        root: str | Path,
        run_id: str,
        *,
        profile: str | None = None,
        clock: Any | None = None,
    ) -> "BudgetLedger":
        config = load_budget_config(root)
        section = config.get("budget")
        if not isinstance(section, Mapping):
            raise BudgetError("budget section is missing")
        max_integer = _integer(section.get("max_integer", MAX_INTEGER), "budget.max_integer")
        limits_data = section.get("limits", {})
        active_profile: Mapping[str, Any] | None = None
        if profile is not None:
            profiles = section.get("profiles")
            if not isinstance(profiles, Mapping) or not isinstance(profiles.get(profile), Mapping):
                raise BudgetError("unknown budget profile")
            active_profile = profiles[profile]
            if active_profile.get("enabled") is not True:
                raise BudgetAuthorizationError("budget profile is not enabled")
            limits_data = active_profile.get("limits", active_profile)
        limits = _limits_from_mapping(limits_data)
        execution = config.get("model_execution", {})
        if not isinstance(execution, Mapping):
            raise BudgetError("model_execution configuration is invalid")
        observability = config.get("observability", {})
        if not isinstance(observability, Mapping):
            raise BudgetError("observability configuration is invalid")
        config_hash = _hash(_canonical(config))
        logger = StructuredLogger(
            root,
            run_id,
            max_bytes=_integer(observability.get("max_log_bytes", 65536), "max_log_bytes"),
            clock=clock,
        )
        inference = config.get("inference")
        if not isinstance(inference, Mapping):
            raise BudgetError("inference configuration is invalid")
        return cls(
            root,
            run_id,
            limits=limits,
            profile=profile,
            config_hash=config_hash,
            currency=section.get("currency", execution.get("currency")),
            max_run_cost_microunits=_integer(
                section.get("max_run_cost_microunits"),
                "budget.max_run_cost_microunits", allow_none=True,
            ),
            live_enabled=execution.get("enabled") is True and active_profile is not None,
            max_integer=max_integer,
            orphan_after_seconds=_integer(observability.get("orphan_after_seconds", 900), "orphan_after_seconds"),
            clock=clock,
            logger=logger,
            inference_policy=inference,
            routing_policy_hash=_hash(_canonical(inference)),
        )

    def _ensure_dir(self, path: Path) -> None:
        if path.exists() and (path.is_symlink() or not path.is_dir()):
            raise BudgetError(f"unsafe budget directory: {path.name}")
        path.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            raise BudgetError(f"unsafe budget directory: {path.name}")

    @property
    def ledger_path(self) -> Path:
        path = self.budget_dir / f"{self.run_id}.jsonl"
        if path.is_symlink():
            raise BudgetIntegrityError("budget ledger is symlinked")
        return path

    @property
    def lock_path(self) -> Path:
        path = self.lock_dir / f"{self.run_id}.budget.lock"
        if path.is_symlink():
            raise BudgetIntegrityError("budget lock is symlinked")
        return path

    @contextmanager
    def _lock(self):
        with self.lock_path.open("a+", encoding="utf-8") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    @staticmethod
    def _fsync_dir(path: Path) -> None:
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _atomic_bytes(self, path: Path, data: bytes) -> None:
        descriptor, name = tempfile.mkstemp(prefix=".tmp-budget-", dir=path.parent)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            self._fsync_dir(path.parent)
        finally:
            if temporary.exists():
                temporary.unlink()

    def read_events(self) -> list[dict[str, Any]]:
        path = self.ledger_path
        if not path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line in path.read_bytes().splitlines(keepends=True):
            if not line.endswith(b"\n"):
                raise BudgetIntegrityError("partial budget event")
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise BudgetIntegrityError("invalid budget event JSON") from error
            self._validate_event(event, len(events), events[-1]["event_hash"] if events else None)
            events.append(event)
        return events

    def _validate_event(self, event: Any, sequence: int, previous: str | None) -> None:
        fields = {
            "schema_version", "event_id", "sequence", "idempotency_key", "event_type", "run_id",
            "cycle_id", "department_id", "role_id", "call_id", "attempt",
            "occurred_at", "monotonic_elapsed_seconds", "payload",
            "previous_event_hash", "event_hash",
        }
        if not isinstance(event, dict) or set(event) != fields:
            raise BudgetIntegrityError("budget event fields are invalid")
        if event["schema_version"] != SCHEMA_VERSION or event["run_id"] != self.run_id:
            raise BudgetIntegrityError("budget event identity is invalid")
        _safe_id(event["event_id"], "event_id")
        if type(event["sequence"]) is not int or event["sequence"] != sequence:
            raise BudgetIntegrityError("budget event sequence is invalid")
        if not isinstance(event["idempotency_key"], str) or not event["idempotency_key"] or len(event["idempotency_key"]) > 256:
            raise BudgetIntegrityError("budget idempotency key is invalid")
        if event["event_type"] not in _EVENT_TYPES:
            raise BudgetIntegrityError("budget event type is invalid")
        if type(event["cycle_id"]) is not int or event["cycle_id"] < 0:
            raise BudgetIntegrityError("budget cycle_id is invalid")
        if type(event["attempt"]) is not int or event["attempt"] < 0:
            raise BudgetIntegrityError("budget attempt is invalid")
        for key in ("department_id", "role_id", "call_id"):
            _safe_id(event[key], key, allow_none=True)
        try:
            _timestamp(event["occurred_at"], "occurred_at")
        except BudgetError as error:
            raise BudgetIntegrityError(str(error)) from error
        elapsed = event["monotonic_elapsed_seconds"]
        if (not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool)
                or not math.isfinite(elapsed) or elapsed < 0):
            raise BudgetIntegrityError("budget monotonic duration is invalid")
        if not isinstance(event["payload"], dict):
            raise BudgetIntegrityError("budget payload is invalid")
        try:
            _validate_payload(event["payload"])
        except BudgetError as error:
            raise BudgetIntegrityError("budget payload values are invalid") from error
        if event["previous_event_hash"] != previous:
            raise BudgetIntegrityError("budget event chain is invalid")
        if not isinstance(event["event_hash"], str) or _SHA.fullmatch(event["event_hash"]) is None:
            raise BudgetIntegrityError("budget event hash is invalid")
        if event["event_hash"] != self._event_hash(event):
            raise BudgetIntegrityError("budget event hash mismatch")

    @staticmethod
    def _event_hash(event: Mapping[str, Any]) -> str:
        body = dict(event)
        body.pop("event_hash", None)
        return _hash(_canonical(body))

    def _elapsed(self) -> float:
        value = float(self.clock.monotonic()) - self._started_monotonic
        return max(0.0, self._resume_elapsed + value)

    def _append_locked(
        self,
        event_type: str,
        *,
        idempotency_key: str,
        cycle_id: int = 0,
        department_id: str | None = None,
        role_id: str | None = None,
        call_id: str | None = None,
        attempt: int = 0,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if event_type not in _EVENT_TYPES:
            raise BudgetError("unsupported budget event type")
        if not isinstance(idempotency_key, str) or not idempotency_key or len(idempotency_key) > 256:
            raise BudgetError("idempotency_key is invalid")
        cycle_id = _integer(cycle_id, "cycle_id")
        attempt = _integer(attempt, "attempt")
        department_id = _safe_id(department_id, "department_id", allow_none=True)
        role_id = _safe_id(role_id, "role_id", allow_none=True)
        call_id = _safe_id(call_id, "call_id", allow_none=True)
        durable_payload = dict(payload or {})
        _validate_payload(durable_payload)
        events = self.read_events()
        for prior in events:
            if prior["idempotency_key"] == idempotency_key:
                if (
                    prior["event_type"] == event_type
                    and prior["cycle_id"] == cycle_id
                    and prior["department_id"] == department_id
                    and prior["role_id"] == role_id
                    and prior["call_id"] == call_id
                    and prior["attempt"] == attempt
                    and prior["payload"] == durable_payload
                ):
                    return prior
                raise BudgetIdempotencyError("conflicting budget event retry")
        occurred_at = _timestamp(self.clock.now_utc(), "occurred_at")
        if events and _parse_datetime(occurred_at) < _parse_datetime(events[-1]["occurred_at"]):
            occurred_at = events[-1]["occurred_at"]
        event = {
            "schema_version": SCHEMA_VERSION,
            "event_id": f"budget:{len(events):08d}",
            "sequence": len(events),
            "idempotency_key": idempotency_key,
            "event_type": event_type,
            "run_id": self.run_id,
            "cycle_id": cycle_id,
            "department_id": department_id,
            "role_id": role_id,
            "call_id": call_id,
            "attempt": attempt,
            "occurred_at": occurred_at,
            "monotonic_elapsed_seconds": self._elapsed(),
            "payload": durable_payload,
            "previous_event_hash": events[-1]["event_hash"] if events else None,
        }
        event["event_hash"] = self._event_hash(event)
        encoded = _canonical(event) + b"\n"
        prior_bytes = self.ledger_path.read_bytes() if self.ledger_path.exists() else b""
        self._atomic_bytes(self.ledger_path, prior_bytes + encoded)
        self.read_events()
        try:
            log_event_type = {
                "AUTHORIZATION": "budget_authorized",
            }.get(event_type, "budget_" + event_type.lower())
            self.logger.emit(
                log_event_type,
                {**event["payload"], "event_type": event_type, "call_id": call_id,
                 "cycle_id": cycle_id, "department_id": department_id,
                 "role_id": role_id, "attempt": attempt},
                level="WARNING" if event_type in {"ALERT", "UNCERTAIN"} else "INFO",
            )
        except Exception as error:
            raise BudgetIntegrityError("structured budget log could not be written") from error
        return event

    def _state_locked(self, events: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
        events = list(events if events is not None else self.read_events())
        reservations: dict[str, dict[str, Any]] = {}
        alerts: list[dict[str, Any]] = []
        authorization: dict[str, Any] | None = None
        progress: list[dict[str, Any]] = []
        state = "RUNNING"
        for event in events:
            payload = event["payload"]
            reservation_id = payload.get("reservation_id")
            if event["event_type"] == "AUTHORIZATION":
                if authorization is not None and authorization != payload:
                    raise BudgetIntegrityError("conflicting authorization events")
                authorization = dict(payload)
            elif event["event_type"] == "RESERVED":
                if not isinstance(reservation_id, str):
                    raise BudgetIntegrityError("reservation event lacks identity")
                if reservation_id in reservations:
                    raise BudgetIntegrityError("duplicate reservation lifecycle")
                reservations[reservation_id] = {**payload, "status": "RESERVED", "reserved_at": event["occurred_at"]}
            elif event["event_type"] in {"ADMITTED", "RECONCILED", "RELEASED", "UNCERTAIN"}:
                if reservation_id not in reservations:
                    raise BudgetIntegrityError("reservation lifecycle has no RESERVED event")
                item = reservations[reservation_id]
                if event["event_type"] == "ADMITTED":
                    if item["status"] != "RESERVED":
                        raise BudgetIntegrityError("ADMITTED is not a valid reservation transition")
                    if item.get("receipt_id") is not None and item.get("receipt_id") != payload.get("receipt_id"):
                        raise BudgetIntegrityError("conflicting admission receipt")
                    item.update({"status": "ADMITTED", "receipt_id": payload.get("receipt_id")})
                elif event["event_type"] == "RECONCILED":
                    if item["status"] not in {"ADMITTED", "UNCERTAIN"}:
                        raise BudgetIntegrityError("RECONCILED is not a valid reservation transition")
                    if item.get("receipt_id") != payload.get("receipt_id"):
                        raise BudgetIntegrityError("conflicting reconciliation receipt")
                    item.update({**payload, "status": "RECONCILED"})
                elif event["event_type"] == "RELEASED":
                    if item["status"] != "RESERVED":
                        raise BudgetIntegrityError("RELEASED is not a valid reservation transition")
                    item.update({**payload, "status": "RELEASED"})
                else:
                    if item["status"] not in {"RESERVED", "ADMITTED", "UNCERTAIN"}:
                        raise BudgetIntegrityError("UNCERTAIN is not a valid reservation transition")
                    if item.get("receipt_id") is not None and payload.get("receipt_id") not in {None, item.get("receipt_id")}:
                        raise BudgetIntegrityError("conflicting uncertain receipt")
                    item.update({**payload, "status": "UNCERTAIN"})
            elif event["event_type"] == "ALERT":
                alerts.append(dict(payload))
            elif event["event_type"] == "PROGRESS":
                progress.append(dict(payload))
            elif event["event_type"] == "PAUSED":
                if state != "RUNNING":
                    raise BudgetIntegrityError("PAUSED is not a valid control transition")
                state = "PAUSED"
            elif event["event_type"] == "RESUMED":
                if state != "PAUSED":
                    raise BudgetIntegrityError("RESUMED is not a valid control transition")
                state = "RUNNING"
            elif event["event_type"] == "STOPPED":
                if state == "STOPPED":
                    raise BudgetIntegrityError("duplicate STOPPED control event")
                state = "STOPPED"
        return {
            "events": events,
            "reservations": reservations,
            "alerts": alerts,
            "authorization": authorization,
            "progress": progress,
            "state": state,
        }

    @staticmethod
    def _open(item: Mapping[str, Any]) -> bool:
        return item.get("status") in {"RESERVED", "ADMITTED", "UNCERTAIN"}

    def _aggregates(self, state: Mapping[str, Any]) -> dict[str, Any]:
        reservations = list(state["reservations"].values())
        confirmed = [item for item in reservations if item.get("status") == "RECONCILED"]
        open_items = [item for item in reservations if self._open(item)]

        def sum_field(items: Iterable[Mapping[str, Any]], field: str, default: int = 0) -> int:
            total = 0
            for item in items:
                value = item.get(field, default)
                if value is None:
                    value = default
                total = _add(total, _integer(value, field) or 0, field)
            return total

        def scoped(items: Iterable[Mapping[str, Any]], field: str, value: str | None) -> int:
            return sum_field((item for item in items if value is not None and item.get(field) == value), "usage_tokens")

        confirmed_tokens = sum_field(confirmed, "usage_tokens")
        reserved_tokens = sum_field(open_items, "estimate_tokens")
        confirmed_wall = sum_field(confirmed, "wall_time_seconds")
        reserved_wall = sum_field(open_items, "estimated_wall_time_seconds")
        confirmed_cost = sum_field(confirmed, "cost_microunits")
        reserved_cost = sum_field(open_items, "estimated_cost_microunits")
        return {
            "confirmed_tokens": confirmed_tokens,
            "reserved_tokens": reserved_tokens,
            "available_tokens": max(0, (self.limits.total_tokens - confirmed_tokens - reserved_tokens) if self.limits.total_tokens is not None else MAX_INTEGER),
            "confirmed_wall_time_seconds": confirmed_wall,
            "reserved_wall_time_seconds": reserved_wall,
            "confirmed_cost_microunits": confirmed_cost,
            "reserved_cost_microunits": reserved_cost,
            "available_cost_microunits": max(
                0,
                self.max_run_cost_microunits - confirmed_cost - reserved_cost,
            ) if self.max_run_cost_microunits is not None else MAX_INTEGER,
            "calls": len(reservations),
            "active_calls": len(open_items),
            "retries": sum(item.get("attempt", 0) for item in reservations),
            "active_children": sum(item.get("children", 0) for item in open_items),
            "extra_judgments": sum(1 for item in reservations if item.get("extra_judgment") is True),
            "scope_usage": scoped(confirmed, "department_id", None),
        }

    def _check_deadline(self) -> None:
        if self.deadline_at and _parse_datetime(self.clock.now_utc()) >= _parse_datetime(self.deadline_at):
            raise BudgetExceeded("budget deadline has expired")

    def _check_limit(self, name: str, used: int, requested: int) -> None:
        limit = getattr(self.limits, name)
        total = _add(used, requested, name)
        if limit is not None and total > limit:
            raise BudgetExceeded(f"{name} exceeded: {total}>{limit}")

    def _check_reservation_limits(
        self,
        state: Mapping[str, Any],
        *,
        cycle_id: int,
        department_id: str | None,
        role_id: str | None,
        model: str | None,
        estimate_tokens: int,
        estimated_cost_microunits: int,
        estimated_wall_time_seconds: int,
        children: int,
        attempt: int,
        extra_judgment: bool,
        deadline_at: str | None,
    ) -> None:
        if state["state"] in {"PAUSED", "STOPPED"}:
            raise BudgetStateError(f"run is {state['state'].lower()}")
        stop = self.root / "control" / "STOP"
        if stop.exists() or stop.is_symlink():
            raise BudgetStateError("control/STOP blocks new reservations")
        self._check_deadline()
        if deadline_at is not None and _parse_datetime(self.clock.now_utc()) >= _parse_datetime(deadline_at):
            raise BudgetExceeded("reservation deadline has expired")
        if self.limits.max_cycles is not None and cycle_id >= self.limits.max_cycles:
            raise BudgetExceeded("max_cycles exceeded")
        reservations = list(state["reservations"].values())
        confirmed = [item for item in reservations if item.get("status") == "RECONCILED"]
        open_items = [item for item in reservations if self._open(item)]
        if any(item.get("status") == "RECONCILED" and item.get("usage_tokens", 0) > item.get("estimate_tokens", 0) for item in reservations):
            raise BudgetExceeded("a prior call exceeded its estimate; new reservations are blocked")
        if any(
            item.get("status") == "RECONCILED"
            and int(item.get("cost_microunits", 0) or 0) > int(item.get("estimated_cost_microunits", 0) or 0)
            for item in reservations
        ):
            raise BudgetExceeded("a prior call exceeded its monetary reserve; new reservations are blocked")
        confirmed_cost = sum(int(item.get("cost_microunits", 0) or 0) for item in confirmed)
        open_cost = sum(int(item.get("estimated_cost_microunits", 0) or 0) for item in open_items)
        if (
            self.max_run_cost_microunits is not None
            and _add(_add(confirmed_cost, open_cost, "cost_microunits"), estimated_cost_microunits, "cost_microunits")
            > self.max_run_cost_microunits
        ):
            raise BudgetExceeded("max_run_cost_microunits exceeded")
        self._check_limit("total_tokens", sum(int(item.get("usage_tokens", 0) or 0) for item in confirmed) + sum(int(item.get("estimate_tokens", 0) or 0) for item in open_items), estimate_tokens)
        for name, field, value in (
            ("per_cycle_tokens", "cycle_id", cycle_id),
            ("per_department_tokens", "department_id", department_id),
            ("per_role_tokens", "role_id", role_id),
            ("per_model_tokens", "model", model),
        ):
            prior = sum(int(item.get("usage_tokens", 0) or 0) for item in confirmed if value is not None and item.get(field) == value)
            prior += sum(int(item.get("estimate_tokens", 0) or 0) for item in open_items if value is not None and item.get(field) == value)
            if value is not None:
                self._check_limit(name, prior, estimate_tokens)
        self._check_limit("max_wall_time_seconds", sum(int(item.get("wall_time_seconds", 0) or 0) for item in confirmed) + sum(int(item.get("estimated_wall_time_seconds", 0) or 0) for item in open_items), estimated_wall_time_seconds)
        self._check_limit("max_calls", len(reservations), 1)
        self._check_limit("max_concurrent_children", sum(int(item.get("children", 0) or 0) for item in open_items), children)
        self._check_limit("max_retries", sum(int(item.get("attempt", 0) or 0) for item in reservations), attempt)
        self._check_limit("max_extra_judgments", sum(1 for item in reservations if item.get("extra_judgment") is True), int(extra_judgment))
        no_progress_limit = self.limits.max_cycles_without_improvement
        if no_progress_limit is not None and no_progress_limit > 0:
            improved = [item["cycle_id"] for item in state["progress"] if item.get("improved") is True]
            last_improvement = max(improved) if improved else -1
            if cycle_id - last_improvement > no_progress_limit:
                raise BudgetExceeded("max_cycles_without_improvement exceeded")

    def _routed_target_authorized(
        self, *, provider: str | None, model: str | None, role_id: str | None,
    ) -> bool:
        policy = self.inference_policy
        if not isinstance(policy, Mapping) or policy.get("enabled") is not True:
            return False
        if provider is None or model is None or role_id is None:
            return False
        targets = policy.get("targets")
        routes = policy.get("role_routes")
        if not isinstance(targets, Mapping) or not isinstance(routes, Mapping):
            return False
        route = routes.get(role_id)
        if not isinstance(route, Mapping) or not isinstance(route.get("targets"), list):
            return False
        permitted_ids = set(route["targets"])
        for target_id, target in targets.items():
            if target_id not in permitted_ids or not isinstance(target, Mapping):
                continue
            if target.get("provider") != provider or target.get("model") != model:
                continue
            if target.get("enabled") is not True:
                continue
            local = target.get("local") is True
            paid = target.get("paid") is True
            if local and policy.get("allow_local") is not True:
                continue
            if not local and policy.get("allow_remote") is not True:
                continue
            if paid and (
                policy.get("allow_paid") is not True
                or self.max_run_cost_microunits is None
                or self.currency is None
            ):
                continue
            return True
        return False

    def _authorization_valid(
        self, state: Mapping[str, Any], *, provider: str | None,
        model: str | None, role_id: str | None, estimate_tokens: int,
        estimated_cost_microunits: int,
    ) -> None:
        if not self.live_enabled:
            raise BudgetAuthorizationError("live execution is disabled")
        raw = state.get("authorization")
        if not raw:
            raise BudgetAuthorizationError("live execution requires run authorization")
        try:
            auth = RunAuthorization.from_mapping(raw)
        except BudgetAuthorizationError:
            raise
        if auth.run_id != self.run_id or auth.config_hash != self.config_hash or auth.profile != self.profile:
            raise BudgetAuthorizationError("authorization is not bound to this run/config/profile")
        if estimate_tokens > auth.token_limit:
            raise BudgetAuthorizationError("authorization token ceiling differs")
        if self.max_run_cost_microunits is not None:
            if (
                auth.max_run_cost_microunits != self.max_run_cost_microunits
                or auth.currency != self.currency
                or estimated_cost_microunits > auth.max_run_cost_microunits
            ):
                raise BudgetAuthorizationError("authorization monetary ceiling/currency differs")
        if auth.routing_policy_hash is None:
            if auth.provider != provider or auth.model != model:
                raise BudgetAuthorizationError("authorization provider/model/teto differs")
        else:
            if auth.provider is not None or auth.model is not None:
                raise BudgetAuthorizationError("routed authorization cannot pin provider/model")
            if auth.routing_policy_hash != self.routing_policy_hash:
                raise BudgetAuthorizationError("authorization routing policy hash differs")
            if not self._routed_target_authorized(provider=provider, model=model, role_id=role_id):
                raise BudgetAuthorizationError("provider/model is not an authorized routed target")
        now = _parse_datetime(self.clock.now_utc())
        approved = _parse_datetime(auth.approved_at)
        if approved > now:
            raise BudgetAuthorizationError("authorization timestamp is in the future")
        if approved < now - timedelta(days=3650):
            raise BudgetAuthorizationError("authorization is expired")

    def authorize(self, authorization: RunAuthorization | Mapping[str, Any]) -> dict[str, Any]:
        auth = authorization if isinstance(authorization, RunAuthorization) else RunAuthorization.from_mapping(authorization)
        if auth.run_id != self.run_id or auth.config_hash != self.config_hash or auth.profile != self.profile:
            raise BudgetAuthorizationError("authorization is not bound to this run/config/profile")
        if auth.token_limit < 1 or auth.token_limit > self.max_integer:
            raise BudgetAuthorizationError("authorization token limit is invalid")
        if self.limits.total_tokens is not None and auth.token_limit > self.limits.total_tokens:
            raise BudgetAuthorizationError("authorization token limit exceeds configured ceiling")
        if auth.routing_policy_hash is not None:
            if auth.provider is not None or auth.model is not None:
                raise BudgetAuthorizationError("routed authorization requires null provider/model")
            if auth.routing_policy_hash != self.routing_policy_hash:
                raise BudgetAuthorizationError("authorization routing policy hash differs")
        if self.max_run_cost_microunits is not None and (
            auth.max_run_cost_microunits != self.max_run_cost_microunits
            or auth.currency != self.currency
        ):
            raise BudgetAuthorizationError("authorization monetary ceiling/currency differs")
        with self._lock():
            state = self._state_locked()
            previous = state.get("authorization")
            if previous is not None and previous != auth.public():
                raise BudgetAuthorizationError("authorization cannot be replaced in a run")
            return self._append_locked(
                "AUTHORIZATION", idempotency_key=f"authorization:{self.run_id}",
                payload=auth.public(),
            )

    def reserve(
        self,
        call_id: str,
        estimate_tokens: int,
        *,
        cycle_id: int = 0,
        department_id: str | None = None,
        role_id: str | None = None,
        attempt: int = 0,
        provider: str | None = None,
        model: str | None = None,
        estimated_wall_time_seconds: int = 0,
        estimated_cost_microunits: int = 0,
        children: int = 0,
        deadline_at: str | None = None,
        extra_judgment: bool = False,
        live: bool = False,
        dry_run: bool = False,
        reservation_id: str | None = None,
    ) -> dict[str, Any]:
        _safe_id(call_id, "call_id")
        estimate_tokens = _integer(estimate_tokens, "estimate_tokens")
        if estimate_tokens > self.max_integer:
            raise BudgetError("estimate_tokens exceeds the canonical integer bound")
        cycle_id = _integer(cycle_id, "cycle_id")
        attempt = _integer(attempt, "attempt")
        department_id = _safe_id(department_id, "department_id", allow_none=True)
        role_id = _safe_id(role_id, "role_id", allow_none=True)
        provider = _safe_id(provider, "provider", allow_none=True)
        model = _safe_id(model, "model", allow_none=True)
        estimated_wall_time_seconds = _integer(estimated_wall_time_seconds, "estimated_wall_time_seconds")
        estimated_cost_microunits = _integer(estimated_cost_microunits, "estimated_cost_microunits")
        children = _integer(children, "children")
        if type(extra_judgment) is not bool or type(live) is not bool or type(dry_run) is not bool:
            raise BudgetError("boolean reservation flags are invalid")
        if deadline_at is not None:
            deadline_at = _timestamp(deadline_at, "deadline_at")
        if reservation_id is None:
            reservation_id = "r-" + _hash(_canonical([self.run_id, call_id, cycle_id, attempt]))[:40]
        else:
            _safe_id(reservation_id, "reservation_id")
        if dry_run:
            return {
                "status": "dry_run", "reservation_id": reservation_id,
                "run_id": self.run_id, "call_id": call_id, "estimate_tokens": estimate_tokens,
                "estimated_cost_microunits": estimated_cost_microunits,
                "usage_tokens": 0, "model_called": False,
            }
        with self._lock():
            state = self._state_locked()
            prior = state["reservations"].get(reservation_id)
            if prior is not None:
                expected = {
                    "call_id": call_id, "estimate_tokens": estimate_tokens,
                    "estimated_cost_microunits": estimated_cost_microunits,
                    "cycle_id": cycle_id, "department_id": department_id,
                    "role_id": role_id, "attempt": attempt,
                    "provider": provider, "model": model,
                    "estimated_wall_time_seconds": estimated_wall_time_seconds,
                    "children": children, "extra_judgment": extra_judgment,
                    "live": live,
                }
                if any(
                    prior.get(key, 0 if key == "estimated_cost_microunits" else None) != value
                    for key, value in expected.items()
                ):
                    raise BudgetIdempotencyError("conflicting reservation retry")
                return dict(prior)
            self._check_reservation_limits(
                state, cycle_id=cycle_id, department_id=department_id, role_id=role_id,
                model=model, estimate_tokens=estimate_tokens,
                estimated_cost_microunits=estimated_cost_microunits,
                estimated_wall_time_seconds=estimated_wall_time_seconds,
                children=children, attempt=attempt, extra_judgment=extra_judgment,
                deadline_at=deadline_at,
            )
            if live:
                self._authorization_valid(
                    state, provider=provider, model=model, role_id=role_id,
                    estimate_tokens=estimate_tokens,
                    estimated_cost_microunits=estimated_cost_microunits,
                )
            payload = {
                "reservation_id": reservation_id, "call_id": call_id,
                "estimate_tokens": estimate_tokens, "cycle_id": cycle_id,
                "estimated_cost_microunits": estimated_cost_microunits,
                "department_id": department_id, "role_id": role_id,
                "attempt": attempt, "provider": provider, "model": model,
                "estimated_wall_time_seconds": estimated_wall_time_seconds,
                "children": children, "deadline_at": deadline_at or self.deadline_at,
                "extra_judgment": extra_judgment, "live": live,
                "budget_config_hash": self.config_hash,
                "budget_limits_hash": self._limits_hash,
                "budget_max_integer": self.max_integer,
                "budget_currency": self.currency,
            }
            if self.max_run_cost_microunits is not None:
                payload["budget_max_run_cost_microunits"] = self.max_run_cost_microunits
            event = self._append_locked(
                "RESERVED", idempotency_key=f"reserve:{reservation_id}",
                cycle_id=cycle_id, department_id=department_id, role_id=role_id,
                call_id=call_id, attempt=attempt, payload=payload,
            )
            self._emit_threshold_alerts_locked()
            return {**payload, "status": "reserved", "event_hash": event["event_hash"]}

    def _find(self, state: Mapping[str, Any], reservation_id: str) -> dict[str, Any]:
        _safe_id(reservation_id, "reservation_id")
        try:
            return state["reservations"][reservation_id]
        except KeyError as error:
            raise BudgetStateError("unknown reservation") from error

    def admit(self, reservation_id: str, receipt_id: str) -> dict[str, Any]:
        _safe_id(receipt_id, "receipt_id")
        with self._lock():
            state = self._state_locked(); item = self._find(state, reservation_id)
            if item["status"] == "ADMITTED" and item.get("receipt_id") == receipt_id:
                return item
            if item["status"] != "RESERVED":
                raise BudgetStateError("only a RESERVED operation can be admitted")
            event = self._append_locked(
                "ADMITTED", idempotency_key=f"admit:{reservation_id}",
                cycle_id=item["cycle_id"], department_id=item.get("department_id"),
                role_id=item.get("role_id"), call_id=item["call_id"], attempt=item["attempt"],
                payload={"reservation_id": reservation_id, "receipt_id": receipt_id},
            )
            return {**item, "status": "ADMITTED", "receipt_id": receipt_id, "event_hash": event["event_hash"]}

    def mark_uncertain(self, reservation_id: str, reason_code: str, *, receipt_id: str | None = None) -> dict[str, Any]:
        _safe_id(reason_code, "reason_code")
        if receipt_id is not None:
            _safe_id(receipt_id, "receipt_id")
        with self._lock():
            state = self._state_locked(); item = self._find(state, reservation_id)
            if item["status"] not in {"RESERVED", "ADMITTED", "UNCERTAIN"}:
                raise BudgetStateError("reservation is not uncertain-compatible")
            if item["status"] == "UNCERTAIN" and item.get("reason_code") == reason_code:
                return item
            payload = {"reservation_id": reservation_id, "reason_code": reason_code}
            if receipt_id is not None:
                payload["receipt_id"] = receipt_id
            self._append_locked(
                "UNCERTAIN", idempotency_key=f"uncertain:{reservation_id}:{reason_code}",
                cycle_id=item["cycle_id"], department_id=item.get("department_id"),
                role_id=item.get("role_id"), call_id=item["call_id"], attempt=item["attempt"],
                payload=payload,
            )
            return self._state_locked()["reservations"][reservation_id]

    def reconcile(
        self,
        reservation_id: str,
        *,
        receipt_id: str,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cache_tokens: int | None = None,
        wall_time_seconds: int | None = None,
        cost_microunits: int | None = None,
        currency: str | None = None,
        usage_available: bool | None = None,
    ) -> dict[str, Any]:
        _safe_id(receipt_id, "receipt_id")
        values = {"input_tokens": input_tokens, "output_tokens": output_tokens, "cache_tokens": cache_tokens}
        for name, value in values.items():
            _integer(value, name, allow_none=True)
        _integer(wall_time_seconds, "wall_time_seconds", allow_none=True)
        _integer(cost_microunits, "cost_microunits", allow_none=True)
        if type(usage_available) is not bool and usage_available is not None:
            raise BudgetError("usage_available must be boolean")
        if currency is not None and (not isinstance(currency, str) or re.fullmatch(r"[A-Z]{3}", currency) is None):
            raise BudgetError("currency is invalid")
        if cost_microunits is not None and currency != self.currency:
            raise BudgetError("currency diverges from ledger configuration")
        if currency is not None and cost_microunits is None:
            raise BudgetError("currency requires a calculable cost")
        with self._lock():
            state = self._state_locked(); item = self._find(state, reservation_id)
            if item.get("receipt_id") != receipt_id:
                raise BudgetIdempotencyError("reconciliation receipt differs")
            if item["status"] == "RECONCILED":
                return item
            if item["status"] not in {"ADMITTED", "UNCERTAIN"}:
                raise BudgetStateError("only an admitted operation can reconcile")
            if usage_available is False or (usage_available is None and any(value is None for value in values.values())):
                payload = {"reservation_id": reservation_id, "reason_code": "usage_unavailable", "receipt_id": receipt_id}
                self._append_locked(
                    "UNCERTAIN", idempotency_key=f"uncertain:{reservation_id}:usage_unavailable",
                    cycle_id=item["cycle_id"], department_id=item.get("department_id"),
                    role_id=item.get("role_id"), call_id=item["call_id"], attempt=item["attempt"],
                    payload=payload,
                )
                return self._state_locked()["reservations"][reservation_id]
            if usage_available is True and any(value is None for value in values.values()):
                raise BudgetError("reported usage must include input/output/cache tokens")
            components = [int(value or 0) for value in values.values()]
            usage_tokens = 0
            for value in components:
                usage_tokens = _add(usage_tokens, value, "usage_tokens")
            wall = item["estimated_wall_time_seconds"] if wall_time_seconds is None else wall_time_seconds
            payload = {
                "reservation_id": reservation_id, "receipt_id": receipt_id,
                "input_tokens": components[0], "output_tokens": components[1],
                "cache_tokens": components[2], "usage_tokens": usage_tokens,
                "wall_time_seconds": wall, "cost_microunits": cost_microunits,
                "currency": currency, "assurance": "reported" if usage_available is True or all(value is not None for value in values.values()) else "estimated",
                "over_estimate": usage_tokens > item["estimate_tokens"],
                "over_cost_reserve": (
                    cost_microunits is not None
                    and cost_microunits > int(item.get("estimated_cost_microunits", 0) or 0)
                ),
            }
            event = self._append_locked(
                "RECONCILED", idempotency_key=f"reconcile:{reservation_id}",
                cycle_id=item["cycle_id"], department_id=item.get("department_id"),
                role_id=item.get("role_id"), call_id=item["call_id"], attempt=item["attempt"],
                payload=payload,
            )
            self._emit_threshold_alerts_locked()
            return {**self._state_locked()["reservations"][reservation_id], "event_hash": event["event_hash"]}

    def release_unadmitted(self, reservation_id: str, proof: str) -> dict[str, Any]:
        if not isinstance(proof, str) or not proof.strip() or len(proof) > 256:
            raise BudgetStateError("non-admission proof is required")
        with self._lock():
            state = self._state_locked(); item = self._find(state, reservation_id)
            if item["status"] == "RELEASED" and item.get("proof") == proof.strip():
                return item
            if item["status"] != "RESERVED":
                raise BudgetStateError("only an unadmitted reservation can be released")
            self._append_locked(
                "RELEASED", idempotency_key=f"release:{reservation_id}",
                cycle_id=item["cycle_id"], department_id=item.get("department_id"),
                role_id=item.get("role_id"), call_id=item["call_id"], attempt=item["attempt"],
                payload={"reservation_id": reservation_id, "proof": proof.strip(), "admitted": False},
            )
            return self._state_locked()["reservations"][reservation_id]

    def record_progress(self, cycle_id: int, *, improved: bool, diagnosis_code: str | None = None) -> dict[str, Any]:
        cycle_id = _integer(cycle_id, "cycle_id")
        if type(improved) is not bool:
            raise BudgetError("improved must be boolean")
        diagnosis_code = _safe_id(diagnosis_code, "diagnosis_code", allow_none=True)
        key = f"progress:{self.run_id}:c{cycle_id:04d}"
        with self._lock():
            event = self._append_locked(
                "PROGRESS", idempotency_key=key, cycle_id=cycle_id,
                payload={"cycle_id": cycle_id, "improved": improved, "diagnosis_code": diagnosis_code},
            )
            self._emit_threshold_alerts_locked()
            return event

    def pause(self, reason_code: str = "operator_pause") -> dict[str, Any]:
        _safe_id(reason_code, "reason_code")
        with self._lock():
            state = self._state_locked()
            if state["state"] == "PAUSED":
                return state
            if state["state"] == "STOPPED":
                raise BudgetStateError("stopped run cannot pause")
            self._append_locked("PAUSED", idempotency_key=f"pause:{self.run_id}:{len(state['events'])}", payload={"reason_code": reason_code})
            return self._state_locked()

    def resume(self) -> dict[str, Any]:
        with self._lock():
            state = self._state_locked()
            if state["state"] != "PAUSED":
                raise BudgetStateError("run is not paused")
            self._append_locked("RESUMED", idempotency_key=f"resume:{self.run_id}:{len(state['events'])}", payload={})
            return self._state_locked()

    def stop(self, reason_code: str = "operator_stop") -> dict[str, Any]:
        _safe_id(reason_code, "reason_code")
        with self._lock():
            state = self._state_locked()
            if state["state"] == "STOPPED":
                return state
            self._append_locked("STOPPED", idempotency_key=f"stop:{self.run_id}:{len(state['events'])}", payload={"reason_code": reason_code})
            return self._state_locked()

    def _emit_alert_locked(self, payload: Mapping[str, Any], *, cycle_id: int = 0) -> None:
        alert_key = payload.get("alert_key")
        if not isinstance(alert_key, str):
            raise BudgetError("alert key is required")
        state = self._state_locked()
        if any(item.get("alert_key") == alert_key for item in state["alerts"]):
            return
        self._append_locked("ALERT", idempotency_key=f"alert:{alert_key}", cycle_id=cycle_id, payload=dict(payload))

    @staticmethod
    def _committed(item: Mapping[str, Any], *, confirmed_field: str, reserved_field: str) -> tuple[int, int]:
        if item.get("status") == "RECONCILED":
            return _integer(item.get(confirmed_field, 0) or 0, confirmed_field) or 0, 0
        if BudgetLedger._open(item):
            return 0, _integer(item.get(reserved_field, 0) or 0, reserved_field) or 0
        return 0, 0

    def _emit_threshold_alerts_locked(self, *, current_cycle: int | None = None) -> None:
        state = self._state_locked()
        reservations = list(state["reservations"].values())
        def committed_tokens(item: Mapping[str, Any]) -> int:
            confirmed, reserved = self._committed(item, confirmed_field="usage_tokens", reserved_field="estimate_tokens")
            return _add(confirmed, reserved, "total_tokens")

        def committed_wall(item: Mapping[str, Any]) -> int:
            confirmed, reserved = self._committed(item, confirmed_field="wall_time_seconds", reserved_field="estimated_wall_time_seconds")
            return _add(confirmed, reserved, "wall_time_seconds")

        def emit_threshold(name: str, limit: int | None, used: int, *, scope: str | None = None, cycle_id: int = 0) -> None:
            if limit is None or limit == 0:
                return
            ratio = used / limit
            for threshold in _ALERT_THRESHOLDS:
                if ratio >= threshold:
                    payload = {
                        "alert_key": f"{name}:{scope or '_'}:{int(threshold * 100)}",
                        "alert_code": "budget_threshold",
                        "limit_name": name, "limit": limit,
                        "threshold": int(threshold * 100), "remaining": max(0, limit - used),
                    }
                    if scope is not None:
                        payload["scope"] = scope
                    self._emit_alert_locked(payload, cycle_id=cycle_id)

        confirmed = [item for item in reservations if item.get("status") == "RECONCILED"]
        open_items = [item for item in reservations if self._open(item)]
        emit_threshold("total_tokens", self.limits.total_tokens, sum(committed_tokens(item) for item in reservations), cycle_id=current_cycle or 0)
        for name, field in (
            ("per_cycle_tokens", "cycle_id"),
            ("per_department_tokens", "department_id"),
            ("per_role_tokens", "role_id"),
            ("per_model_tokens", "model"),
        ):
            limit = getattr(self.limits, name)
            scopes = sorted({str(item[field]) for item in reservations if item.get(field) is not None})
            for scope in scopes:
                used = sum(committed_tokens(item) for item in reservations if str(item.get(field)) == scope)
                emit_threshold(name, limit, used, scope=scope, cycle_id=current_cycle or 0)
        emit_threshold("max_wall_time_seconds", self.limits.max_wall_time_seconds, sum(committed_wall(item) for item in reservations), cycle_id=current_cycle or 0)
        emit_threshold("max_calls", self.limits.max_calls, len(reservations), cycle_id=current_cycle or 0)
        emit_threshold("max_concurrent_children", self.limits.max_concurrent_children, sum(_integer(item.get("children", 0) or 0, "children") or 0 for item in open_items), cycle_id=current_cycle or 0)
        emit_threshold("max_retries", self.limits.max_retries, sum(_integer(item.get("attempt", 0) or 0, "attempt") or 0 for item in reservations), cycle_id=current_cycle or 0)
        emit_threshold("max_extra_judgments", self.limits.max_extra_judgments, sum(1 for item in reservations if item.get("extra_judgment") is True), cycle_id=current_cycle or 0)
        now = _parse_datetime(self.clock.now_utc())
        if self.deadline_at and now >= _parse_datetime(self.deadline_at):
            self._emit_alert_locked({"alert_key": "deadline", "alert_code": "deadline", "deadline_at": self.deadline_at}, cycle_id=current_cycle or 0)
        for item in open_items:
            try:
                age = (now - _parse_datetime(item["reserved_at"])).total_seconds()
            except (KeyError, ValueError):
                continue
            if age >= self.orphan_after_seconds:
                self._emit_alert_locked({
                    "alert_key": f"orphan:{item['reservation_id']}",
                    "alert_code": "orphan_reservation", "reservation_id": item["reservation_id"],
                    "orphan_after_seconds": self.orphan_after_seconds,
                }, cycle_id=item["cycle_id"])
        progress = state["progress"]
        if self.limits.max_cycles_without_improvement is not None and self.limits.max_cycles_without_improvement > 0 and current_cycle is not None:
            improved = [item["cycle_id"] for item in progress if item.get("improved") is True]
            last = max(improved) if improved else -1
            if current_cycle - last >= self.limits.max_cycles_without_improvement:
                self._emit_alert_locked({
                    "alert_key": f"no_progress:{current_cycle}",
                    "alert_code": "no_progress",
                    "last_improvement_cycle": last if last >= 0 else None,
                    "limit": self.limits.max_cycles_without_improvement,
                }, cycle_id=current_cycle)

    def check_alerts(self, *, current_cycle: int | None = None) -> list[dict[str, Any]]:
        if current_cycle is not None:
            _integer(current_cycle, "current_cycle")
        with self._lock():
            self._emit_threshold_alerts_locked(current_cycle=current_cycle)
            return list(self._state_locked()["alerts"])

    def status(self, *, current_cycle: int | None = None) -> dict[str, Any]:
        self.check_alerts(current_cycle=current_cycle)
        state = self._state_locked()
        reservations = list(state["reservations"].values())
        confirmed = [item for item in reservations if item.get("status") == "RECONCILED"]
        open_items = [item for item in reservations if self._open(item)]
        def metric(item: Mapping[str, Any], confirmed_field: str, reserved_field: str) -> tuple[int, int]:
            return self._committed(item, confirmed_field=confirmed_field, reserved_field=reserved_field)

        def report(name: str, unit: str, limit: int | None, confirmed_value: int, reserved_value: int) -> dict[str, Any]:
            committed_value = _add(confirmed_value, reserved_value, name)
            return {
                "unit": unit, "limit": limit, "confirmed": confirmed_value,
                "reserved": reserved_value, "committed": committed_value,
                "available": max(0, limit - committed_value) if limit is not None else None,
            }

        def scoped_report(name: str, field: str, limit: int | None) -> dict[str, Any]:
            scopes = sorted({str(item[field]) for item in reservations if item.get(field) is not None})
            result: dict[str, Any] = {}
            for scope in scopes:
                scoped_confirmed = [item for item in confirmed if str(item.get(field)) == scope]
                scoped_open = [item for item in open_items if str(item.get(field)) == scope]
                confirmed_value = sum(metric(item, "usage_tokens", "estimate_tokens")[0] for item in scoped_confirmed)
                reserved_value = sum(metric(item, "usage_tokens", "estimate_tokens")[1] for item in scoped_open)
                result[scope] = report(name, "tokens", limit, confirmed_value, reserved_value)
            return result

        confirmed_tokens = sum(metric(item, "usage_tokens", "estimate_tokens")[0] for item in confirmed)
        reserved_tokens = sum(metric(item, "usage_tokens", "estimate_tokens")[1] for item in open_items)
        confirmed_wall = sum(metric(item, "wall_time_seconds", "estimated_wall_time_seconds")[0] for item in confirmed)
        reserved_wall = sum(metric(item, "wall_time_seconds", "estimated_wall_time_seconds")[1] for item in open_items)
        confirmed_cost = sum(metric(item, "cost_microunits", "estimated_cost_microunits")[0] for item in confirmed)
        reserved_cost = sum(metric(item, "cost_microunits", "estimated_cost_microunits")[1] for item in open_items)
        cycle_values = [item["cycle_id"] for item in reservations]
        progress_cycles = [item["cycle_id"] for item in state["progress"]]
        effective_cycle = current_cycle if current_cycle is not None else max(cycle_values + progress_cycles, default=None)
        cycles_started = (effective_cycle + 1) if effective_cycle is not None else 0
        uncertain = any(item.get("status") == "UNCERTAIN" for item in reservations)
        usage_known = all(item.get("assurance") == "reported" for item in confirmed) if confirmed else False
        improvements = [item for item in state["progress"] if item.get("improved") is True]
        last_improvement = max(improvements, key=lambda item: item["cycle_id"]) if improvements else None
        last_improvement_cycle = last_improvement["cycle_id"] if last_improvement else -1
        cycles_without_improvement = max(0, (effective_cycle - last_improvement_cycle) if effective_cycle is not None else 0)
        assurance = "uncertain" if uncertain else ("reported" if usage_known else "estimated")
        usage_by_limit: dict[str, Any] = {
            "total_tokens": report("total_tokens", "tokens", self.limits.total_tokens, confirmed_tokens, reserved_tokens),
            "per_cycle_tokens": scoped_report("per_cycle_tokens", "cycle_id", self.limits.per_cycle_tokens),
            "per_department_tokens": scoped_report("per_department_tokens", "department_id", self.limits.per_department_tokens),
            "per_role_tokens": scoped_report("per_role_tokens", "role_id", self.limits.per_role_tokens),
            "per_model_tokens": scoped_report("per_model_tokens", "model", self.limits.per_model_tokens),
            "max_wall_time_seconds": report("max_wall_time_seconds", "seconds", self.limits.max_wall_time_seconds, confirmed_wall, reserved_wall),
            "max_calls": report("max_calls", "calls", self.limits.max_calls, len(reservations), 0),
            "max_concurrent_children": report("max_concurrent_children", "children", self.limits.max_concurrent_children, 0, sum(_integer(item.get("children", 0) or 0, "children") or 0 for item in open_items)),
            "max_retries": report("max_retries", "retries", self.limits.max_retries, sum(_integer(item.get("attempt", 0) or 0, "attempt") or 0 for item in reservations), 0),
            "max_extra_judgments": report("max_extra_judgments", "judgments", self.limits.max_extra_judgments, sum(1 for item in reservations if item.get("extra_judgment") is True), 0),
            "max_cycles": report("max_cycles", "cycles", self.limits.max_cycles, cycles_started, 0),
            "max_cycles_without_improvement": report("max_cycles_without_improvement", "cycles", self.limits.max_cycles_without_improvement, cycles_without_improvement, 0),
            "max_run_cost_microunits": report(
                "max_run_cost_microunits", "microunits",
                self.max_run_cost_microunits, confirmed_cost, reserved_cost,
            ),
        }
        balance = {
            name: (value["available"] if isinstance(value, Mapping) and "available" in value else {
                scope: item["available"] for scope, item in value.items()
            }) for name, value in usage_by_limit.items()
        }
        public_reservations = []
        for item in reservations:
            public_item = {key: value for key, value in item.items() if key != "proof"}
            public_reservations.append(public_item)
        alerts = list(state["alerts"])
        if state["state"] == "STOPPED":
            next_action = "stopped"
        elif state["state"] == "PAUSED":
            next_action = "resume_or_stop"
        elif uncertain:
            next_action = "reconcile_uncertain_receipts"
        elif alerts:
            next_action = "inspect_alerts_before_next_reservation"
        else:
            next_action = "continue_within_limits"
        diagnosis = next((item.get("diagnosis_code") for item in reversed(state["progress"]) if item.get("diagnosis_code")), None)
        return {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "cycle_id": effective_cycle,
            "profile": self.profile,
            "config_hash": self.config_hash,
            "state": state["state"],
            "limits": {**asdict(self.limits), "unit": "tokens", "max_integer": self.max_integer},
            "usage": {
                "confirmed_tokens": confirmed_tokens,
                "reserved_tokens": reserved_tokens,
                "total_reconciled_tokens": confirmed_tokens,
                "confirmed_cost_microunits": confirmed_cost,
                "reserved_cost_microunits": reserved_cost,
                "total_cost_microunits": _add(confirmed_cost, reserved_cost, "cost_microunits"),
                "currency": self.currency,
                "by_limit": usage_by_limit,
            },
            "usage_by_limit": usage_by_limit,
            "balance": balance,
            "available": {
                "total_tokens": balance["total_tokens"],
                "cost_microunits": balance["max_run_cost_microunits"],
                "wall_time_seconds": balance["max_wall_time_seconds"],
                "calls": balance["max_calls"],
                "concurrent_children": balance["max_concurrent_children"],
            },
            "reservations": sorted(public_reservations, key=lambda item: item["reservation_id"]),
            "open_reservations": len(open_items),
            "children": sum(int(item.get("children", 0) or 0) for item in open_items),
            "calls": len(reservations),
            "retries": sum(int(item.get("attempt", 0) or 0) for item in reservations),
            "last_improvement": last_improvement,
            "diagnosis": diagnosis,
            "next_action": next_action,
            "champion_hash": None,
            "candidate_hash": None,
            "alerts": alerts,
            "assurance": assurance,
            "authorization": {"present": state["authorization"] is not None, "profile": self.profile, "config_hash": self.config_hash},
            "deadline_at": self.deadline_at,
            "ledger_path": str(self.ledger_path.relative_to(self.root)),
            "log": self.logger.status(),
        }

    def human_status(self, *, current_cycle: int | None = None) -> str:
        value = self.status(current_cycle=current_cycle)
        usage = value["usage"]
        return "\n".join((
            f"run={value['run_id']} state={value['state']} assurance={value['assurance']}",
            f"tokens confirmed={usage['confirmed_tokens']} reserved={usage['reserved_tokens']} available={value['available']['total_tokens']}",
            f"cost {usage['currency']} confirmed={usage['confirmed_cost_microunits']} reserved={usage['reserved_cost_microunits']} available={value['available']['cost_microunits']}",
            f"reservations open={value['open_reservations']} calls={value['calls']} retries={value['retries']} children={value['children']}",
            f"alerts={len(value['alerts'])} last_improvement={value['last_improvement']}",
        ))


class LimitedSupervisor:
    """Execute caller-provided operations through one bounded ledger step."""

    def __init__(self, ledger: BudgetLedger, *, max_steps: int = 1):
        self.ledger = ledger
        self.max_steps = _integer(max_steps, "max_steps")
        self.steps = 0

    def execute(
        self,
        call_id: str,
        estimate_tokens: int,
        operation: Callable[[Mapping[str, Any]], Mapping[str, Any] | None],
        *,
        receipt_id: str,
        cycle_id: int = 0,
        department_id: str | None = None,
        role_id: str | None = None,
        attempt: int = 0,
        provider: str | None = None,
        model: str | None = None,
        estimated_wall_time_seconds: int = 0,
        children: int = 0,
        live: bool = False,
    ) -> dict[str, Any]:
        if self.steps >= self.max_steps:
            raise BudgetExceeded("limited supervisor step ceiling reached")
        reservation = self.ledger.reserve(
            call_id, estimate_tokens, cycle_id=cycle_id, department_id=department_id,
            role_id=role_id, attempt=attempt, provider=provider, model=model,
            estimated_wall_time_seconds=estimated_wall_time_seconds, children=children,
            live=live,
        )
        admitted = self.ledger.admit(reservation["reservation_id"], receipt_id)
        self.steps += 1
        try:
            result = operation(admitted)
        except Exception:
            self.ledger.mark_uncertain(reservation["reservation_id"], "operation_exception", receipt_id=receipt_id)
            raise
        result = dict(result or {})
        reconciled = self.ledger.reconcile(
            reservation["reservation_id"], receipt_id=receipt_id,
            input_tokens=result.get("input_tokens"), output_tokens=result.get("output_tokens"),
            cache_tokens=result.get("cache_tokens"), wall_time_seconds=result.get("wall_time_seconds"),
            cost_microunits=result.get("cost_microunits"), currency=result.get("currency"),
            usage_available=result.get("usage_available"),
        )
        return {"reservation": reservation, "admitted": admitted, "reconciled": reconciled, "steps": self.steps}


__all__ = [
    "BudgetAuthorizationError", "BudgetError", "BudgetExceeded", "BudgetIdempotencyError",
    "BudgetIntegrityError", "BudgetLedger", "BudgetLimits", "BudgetStateError",
    "LimitedSupervisor", "MAX_INTEGER", "ManualClock", "RunAuthorization",
    "load_budget_config",
]
