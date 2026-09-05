"""Deterministic, fail-closed inference routing for M12.5.

This module does not replace M6 or execute a role as an RLM child.  It turns a
validated AgentTask into a bounded inference operation and is the only layer
which joins routing, M12 admission, one backend call, an operational receipt,
and reconciliation.
"""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Mapping, Protocol, Sequence
from urllib.parse import urlsplit

import jsonschema

from .budget import BudgetLedger


SCHEMA_VERSION = "1.0.0"
RECEIPT_SCHEMA_VERSION = "1.1.0"
PRIME_PER_CHILD_MODEL_SELECTION = "unknown_on_current_version"
PAID_RUNTIME_READY = True
PRIVACY_MODES = frozenset({"deny_remote", "scoped_remote", "full_remote"})
ROLE_IDS = frozenset({
    "M00",
    *{f"S{department}0" for department in range(1, 6)},
    *{f"W{department}{worker}" for department in range(1, 6) for worker in range(1, 4)},
})
CAPABILITIES = frozenset({
    "language", "latex", "math_verification", "math_high_assurance",
    "long_context", "vision", "structured_output",
})
ESCALATION_REASONS = frozenset({
    "BACKEND_FAILURE", "TIMEOUT", "OUTPUT_SCHEMA_INVALID",
    "MANDATORY_EVIDENCE_MISSING", "DETERMINISTIC_GATE_FAILED",
    "CROSS_REVIEW_DISAGREEMENT", "INDEPENDENT_JUDGMENT_REQUIRED",
    "ROUTE_CAPABILITY_INSUFFICIENT",
})
BACKEND_TYPES = frozenset({"fake", "local_openai_compatible", "remote_openai_compatible"})
TIERS = frozenset({"low", "mid", "high", "high_assurance"})
FINISH_REASONS = frozenset({"stop", "length", "tool_call", "error", "unknown", "schema_invalid"})
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")
_ENV = re.compile(r"[A-Z_][A-Z0-9_]{0,127}\Z")


class InferenceError(RuntimeError):
    """Base error for M12.5."""


class InferenceConfigError(InferenceError):
    """The project-local inference policy is invalid."""


class InferenceRoutingError(InferenceError):
    """No authorized deterministic route exists."""


class InferenceIntegrityError(InferenceError):
    """A route or receipt is unsafe, corrupt, or conflicting."""


class InferenceBackendError(InferenceError):
    """A backend failed; ``sent`` indicates whether consumption is possible."""

    def __init__(self, reason_code: str, message: str, *, sent: bool):
        if reason_code not in ESCALATION_REASONS:
            raise ValueError("invalid backend reason code")
        super().__init__(message)
        self.reason_code = reason_code
        self.sent = sent


class InferenceOutputError(InferenceError):
    """The backend responded, but the requested output contract did not pass."""

    reason_code = "OUTPUT_SCHEMA_INVALID"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def routing_policy_hash(policy: Mapping[str, Any]) -> str:
    if not isinstance(policy, Mapping):
        raise InferenceConfigError("inference policy must be an object")
    return sha256(canonical_bytes(policy))


def load_requested_output_schema(
    root: str | Path, schema_name: str,
) -> dict[str, Any]:
    """Load one canonical project-local output schema, failing closed."""
    if (
        not isinstance(schema_name, str)
        or not schema_name
        or Path(schema_name).is_absolute()
        or Path(schema_name).name != schema_name
    ):
        raise InferenceIntegrityError("requested output schema name is unsafe")
    raw_root = Path(root)
    schema_dir = raw_root / "config" / "schemas"
    if schema_dir.is_symlink() or not schema_dir.is_dir():
        raise InferenceIntegrityError("canonical schema directory is missing or unsafe")
    canonical_dir = schema_dir.resolve()
    candidate = schema_dir / schema_name
    if candidate.is_symlink() or not candidate.is_file():
        raise InferenceIntegrityError("requested output schema is missing or unsafe")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise InferenceIntegrityError("requested output schema is missing or unsafe") from error
    if resolved.parent != canonical_dir:
        raise InferenceIntegrityError("requested output schema escapes canonical directory")
    try:
        schema = json.loads(resolved.read_text(encoding="utf-8"))
        if not isinstance(schema, dict):
            raise InferenceIntegrityError("requested output schema must be an object")
        if schema.get("$id") != schema_name:
            raise InferenceIntegrityError("requested output schema identity differs from task contract")
        jsonschema.Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, jsonschema.SchemaError) as error:
        raise InferenceIntegrityError("requested output schema is malformed") from error
    return schema


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_id(value: Any, label: str, *, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise InferenceConfigError(f"{label} is invalid")
    return value


def _bounded_int(value: Any, label: str, *, positive: bool = False) -> int:
    if type(value) is not int or value < (1 if positive else 0) or value > 2**63 - 1:
        raise InferenceConfigError(f"{label} is invalid")
    return value


def _timestamp(value: Any) -> str:
    if not isinstance(value, str):
        raise InferenceIntegrityError("timestamp is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise InferenceIntegrityError("timestamp is invalid") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InferenceIntegrityError("timestamp lacks timezone")
    return value


def _safe_endpoint(endpoint: str, *, local: bool) -> None:
    try:
        parsed = urlsplit(endpoint)
    except ValueError as error:
        raise InferenceConfigError("target endpoint is invalid") from error
    if parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise InferenceConfigError("target endpoint contains unsupported authority data")
    if not parsed.hostname or parsed.query:
        raise InferenceConfigError("target endpoint is incomplete")
    if local:
        if parsed.scheme not in {"http", "https"} or parsed.hostname.lower() not in {"127.0.0.1", "localhost", "::1"}:
            raise InferenceConfigError("local endpoint must use an explicit loopback host")
    elif parsed.scheme != "https":
        raise InferenceConfigError("remote endpoint must use HTTPS")


@dataclass(frozen=True)
class TargetPricing:
    """Integer microunits per one million tokens."""

    currency: str
    input_microunits_per_million: int
    output_microunits_per_million: int
    cached_input_microunits_per_million: int = 0

    def cost(self, input_tokens: int, output_tokens: int, cache_tokens: int = 0) -> int:
        values = (input_tokens, output_tokens, cache_tokens)
        if any(type(value) is not int or value < 0 for value in values):
            raise InferenceConfigError("token usage is invalid for pricing")
        uncached = max(0, input_tokens - cache_tokens)
        numerator = (
            uncached * self.input_microunits_per_million
            + cache_tokens * self.cached_input_microunits_per_million
            + output_tokens * self.output_microunits_per_million
        )
        return (numerator + 999_999) // 1_000_000


@dataclass(frozen=True)
class InferenceTarget:
    target_id: str
    provider: str
    model: str
    backend_type: str
    enabled: bool
    local: bool
    paid: bool
    tier: str
    capabilities: tuple[str, ...]
    context_limit: int
    max_output_tokens: int
    independence_group: str
    endpoint: str | None
    api_key_env: str | None
    timeout_seconds: int
    fallback_target: str | None = None
    pricing: TargetPricing | None = None

    def public(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id, "provider": self.provider,
            "model": self.model, "backend_type": self.backend_type,
            "enabled": self.enabled, "local": self.local, "paid": self.paid,
            "tier": self.tier, "capabilities": list(self.capabilities),
            "context_limit": self.context_limit,
            "max_output_tokens": self.max_output_tokens,
            "independence_group": self.independence_group,
            "endpoint": self.endpoint, "api_key_env": self.api_key_env,
            "timeout_seconds": self.timeout_seconds,
            "fallback_target": self.fallback_target,
            "pricing": None if self.pricing is None else {
                "currency": self.pricing.currency,
                "input_microunits_per_million": self.pricing.input_microunits_per_million,
                "output_microunits_per_million": self.pricing.output_microunits_per_million,
                "cached_input_microunits_per_million": self.pricing.cached_input_microunits_per_million,
            },
        }


class ModelRegistry:
    """Validated declarations of inference targets; it never performs calls."""

    _POLICY_FIELDS = {
        "schema_version", "enabled", "allow_local", "allow_remote", "allow_paid",
        "routing_mode", "targets", "role_routes", "escalation", "independence",
    }
    _TARGET_FIELDS = {
        "target_id", "provider", "model", "backend_type", "enabled", "local",
        "paid", "tier", "capabilities", "context_limit", "max_output_tokens",
        "independence_group", "endpoint", "api_key_env", "timeout_seconds",
        "fallback_target", "pricing",
    }

    def __init__(self, policy: Mapping[str, Any], *, privacy_mode: str | None = None):
        if not isinstance(policy, Mapping) or set(policy) != self._POLICY_FIELDS:
            raise InferenceConfigError("inference policy fields are invalid")
        if policy.get("schema_version") != SCHEMA_VERSION or policy.get("routing_mode") != "deterministic":
            raise InferenceConfigError("inference policy version/mode is invalid")
        for field in ("enabled", "allow_local", "allow_remote", "allow_paid"):
            if type(policy.get(field)) is not bool:
                raise InferenceConfigError(f"inference.{field} must be boolean")
        escalation = policy.get("escalation")
        independence = policy.get("independence")
        if not isinstance(escalation, Mapping) or set(escalation) != {"enabled", "max_route_attempts"}:
            raise InferenceConfigError("inference escalation policy is invalid")
        if type(escalation.get("enabled")) is not bool:
            raise InferenceConfigError("inference escalation.enabled must be boolean")
        _bounded_int(escalation.get("max_route_attempts"), "max_route_attempts", positive=True)
        if not isinstance(independence, Mapping) or set(independence) not in (
            {"jury_must_differ_from_producer_group"},
            {"jury_must_differ_from_producer_group", "mode"},
        ) or type(independence.get("jury_must_differ_from_producer_group")) is not bool:
            raise InferenceConfigError("inference independence policy is invalid")
        if independence.get("mode", "independence_group") not in {"model", "independence_group"}:
            raise InferenceConfigError("inference independence mode is invalid")

        self.enabled = policy["enabled"]
        self.allow_local = policy["allow_local"]
        self.allow_remote = policy["allow_remote"]
        self.allow_paid = policy["allow_paid"]
        if privacy_mode is not None and privacy_mode not in PRIVACY_MODES:
            raise InferenceConfigError("registry privacy mode is invalid")
        self.privacy_mode = privacy_mode

        raw_targets = policy.get("targets")
        pairs: list[tuple[str, Mapping[str, Any]]] = []
        if isinstance(raw_targets, Mapping):
            if any(not isinstance(key, str) for key in raw_targets):
                raise InferenceConfigError("inference target keys must be strings")
            pairs = list(raw_targets.items())
        elif isinstance(raw_targets, Sequence) and not isinstance(raw_targets, (str, bytes)):
            for value in raw_targets:
                if not isinstance(value, Mapping):
                    raise InferenceConfigError("inference target must be an object")
                pairs.append((str(value.get("target_id", "")), value))
        else:
            raise InferenceConfigError("inference targets must be an object or list")
        if len({key for key, _ in pairs}) != len(pairs):
            raise InferenceConfigError("duplicate inference target_id")
        self.targets: dict[str, InferenceTarget] = {}
        for target_id, raw in pairs:
            self.targets[target_id] = self._target(target_id, raw)
        if policy["enabled"] is False and any(target.enabled for target in self.targets.values()):
            raise InferenceConfigError("no target may be enabled while inference is disabled")
        self._validate_fallbacks()
        self.role_routes = self._routes(policy.get("role_routes"))
        self.policy = dict(policy)
        self.policy_hash = routing_policy_hash(policy)
        self.max_route_attempts = escalation["max_route_attempts"]
        self.escalation_enabled = escalation["enabled"]
        self.jury_independence = independence["jury_must_differ_from_producer_group"]
        self.jury_independence_mode = independence.get("mode", "independence_group")
        self.validate_enabled_policy()

    @classmethod
    def from_project(cls, root: str | Path) -> "ModelRegistry":
        from .budget import load_budget_config
        config = load_budget_config(root)
        policy = config.get("inference")
        if not isinstance(policy, Mapping):
            raise InferenceConfigError("config/budgets.yaml lacks inference policy")
        privacy = config.get("privacy")
        privacy_mode = privacy.get("remote_content_mode") if isinstance(privacy, Mapping) else None
        return cls(policy, privacy_mode=privacy_mode)

    def _target(self, key: str, raw: Mapping[str, Any]) -> InferenceTarget:
        if not isinstance(raw, Mapping):
            raise InferenceConfigError("inference target must be an object")
        expected = set(self._TARGET_FIELDS)
        if set(raw).issubset(expected) and expected - set(raw) <= {"fallback_target", "pricing"}:
            raw = {**raw, "fallback_target": raw.get("fallback_target"), "pricing": raw.get("pricing")}
        if set(raw) != expected:
            raise InferenceConfigError("inference target fields are invalid")
        target_id = _safe_id(raw.get("target_id"), "target_id")
        if key != target_id:
            raise InferenceConfigError("target key and target_id differ")
        provider = _safe_id(raw.get("provider"), "provider")
        model = _safe_id(raw.get("model"), "model")
        backend_type = raw.get("backend_type")
        if backend_type not in BACKEND_TYPES:
            raise InferenceConfigError("backend_type is invalid")
        for field in ("enabled", "local", "paid"):
            if type(raw.get(field)) is not bool:
                raise InferenceConfigError(f"target.{field} must be boolean")
        if raw.get("tier") not in TIERS:
            raise InferenceConfigError("target tier is invalid")
        capabilities = raw.get("capabilities")
        if not isinstance(capabilities, list) or len(capabilities) != len(set(capabilities)) or any(item not in CAPABILITIES for item in capabilities):
            raise InferenceConfigError("target capabilities are invalid")
        context_limit = _bounded_int(raw.get("context_limit"), "context_limit", positive=True)
        max_output_tokens = _bounded_int(raw.get("max_output_tokens"), "max_output_tokens", positive=True)
        timeout_seconds = _bounded_int(raw.get("timeout_seconds"), "timeout_seconds", positive=True)
        if max_output_tokens > context_limit:
            raise InferenceConfigError("target output limit exceeds context limit")
        group = _safe_id(raw.get("independence_group"), "independence_group")
        endpoint = raw.get("endpoint")
        if endpoint is not None and (not isinstance(endpoint, str) or len(endpoint) > 2048):
            raise InferenceConfigError("target endpoint is invalid")
        if endpoint is not None:
            _safe_endpoint(endpoint, local=raw["local"])
        if backend_type == "local_openai_compatible" and (not raw["local"] or endpoint is None):
            raise InferenceConfigError("local backend requires a loopback endpoint")
        if backend_type == "remote_openai_compatible" and (raw["local"] or endpoint is None):
            raise InferenceConfigError("remote backend requires an HTTPS endpoint")
        env_name = raw.get("api_key_env")
        if env_name is not None and (not isinstance(env_name, str) or _ENV.fullmatch(env_name) is None):
            raise InferenceConfigError("api_key_env must name an environment variable")
        fallback = _safe_id(raw.get("fallback_target"), "fallback_target", allow_none=True)
        pricing_raw = raw.get("pricing")
        pricing = None
        if pricing_raw is not None:
            expected_pricing = {
                "currency", "input_microunits_per_million",
                "output_microunits_per_million",
                "cached_input_microunits_per_million",
            }
            if not isinstance(pricing_raw, Mapping) or set(pricing_raw) not in (
                expected_pricing, expected_pricing - {"cached_input_microunits_per_million"},
            ):
                raise InferenceConfigError("target pricing fields are invalid")
            currency = pricing_raw.get("currency")
            if not isinstance(currency, str) or re.fullmatch(r"[A-Z]{3}", currency) is None:
                raise InferenceConfigError("target pricing currency is invalid")
            pricing = TargetPricing(
                currency,
                _bounded_int(pricing_raw.get("input_microunits_per_million"), "input price"),
                _bounded_int(pricing_raw.get("output_microunits_per_million"), "output price"),
                _bounded_int(pricing_raw.get("cached_input_microunits_per_million", 0), "cached input price"),
            )
        if raw["paid"] and pricing is None:
            raise InferenceConfigError("paid target requires explicit integer pricing")
        return InferenceTarget(
            target_id, provider, model, backend_type, raw["enabled"], raw["local"],
            raw["paid"], raw["tier"], tuple(capabilities), context_limit,
            max_output_tokens, group, endpoint, env_name, timeout_seconds, fallback,
            pricing,
        )

    def _validate_fallbacks(self) -> None:
        for target in self.targets.values():
            if target.fallback_target is not None and target.fallback_target not in self.targets:
                raise InferenceConfigError("fallback references an unknown target")
            seen: set[str] = set()
            current: InferenceTarget | None = target
            while current is not None and current.fallback_target is not None:
                if current.target_id in seen:
                    raise InferenceConfigError("fallback chain contains a cycle")
                seen.add(current.target_id)
                current = self.targets.get(current.fallback_target)
            if current is not None and current.target_id in seen:
                raise InferenceConfigError("fallback chain contains a cycle")

    def _routes(self, raw: Any) -> dict[str, dict[str, tuple[str, ...]]]:
        if not isinstance(raw, Mapping):
            raise InferenceConfigError("role_routes must be an object")
        routes: dict[str, dict[str, tuple[str, ...]]] = {}
        for role, route in raw.items():
            if role not in ROLE_IDS or not isinstance(route, Mapping) or set(route) != {"targets", "required_capabilities"}:
                raise InferenceConfigError("role route is invalid")
            targets = route.get("targets")
            capabilities = route.get("required_capabilities")
            if not isinstance(targets, list) or not targets or len(targets) != len(set(targets)) or any(item not in self.targets for item in targets):
                raise InferenceConfigError("role route targets are invalid")
            if not isinstance(capabilities, list) or len(capabilities) != len(set(capabilities)) or any(item not in CAPABILITIES for item in capabilities):
                raise InferenceConfigError("role route capabilities are invalid")
            routes[role] = {"targets": tuple(targets), "required_capabilities": tuple(capabilities)}
        return routes

    def validate_enabled_policy(self) -> None:
        for target in self.targets.values():
            if not target.enabled:
                continue
            if target.local and not self.allow_local:
                raise InferenceConfigError("enabled local target requires allow_local")
            if not target.local and not self.allow_remote:
                raise InferenceConfigError("enabled remote target requires allow_remote")
            if target.paid and (not self.allow_paid or target.pricing is None):
                raise InferenceConfigError("paid target requires allow_paid and explicit pricing")
            if target.backend_type == "fake":
                # A fake may exist in test policy, but a production preflight
                # must make its test-only nature explicit in status.
                continue

    def target(self, target_id: str) -> InferenceTarget:
        try:
            return self.targets[target_id]
        except KeyError as error:
            raise InferenceRoutingError("unknown inference target") from error

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "routing_policy_hash": self.policy_hash,
            "enabled_targets": sorted(target.target_id for target in self.targets.values() if target.enabled),
            "allow_local": self.allow_local,
            "allow_remote": self.allow_remote,
            "allow_paid": self.allow_paid,
            "privacy_mode": self.privacy_mode,
            "jury_independence_mode": self.jury_independence_mode,
            "paid_runtime_ready": PAID_RUNTIME_READY,
            "inference_backend_routing": "available" if self.enabled else "disabled",
            "prime_child_model_routing": PRIME_PER_CHILD_MODEL_SELECTION,
        }


@dataclass(frozen=True)
class InferenceRequest:
    run_id: str
    cycle_id: int
    task_id: str
    role_id: str
    department_id: str
    activation_mode: str
    prompt_hash: str
    prompt_version: str
    base_hash: str
    requested_output_schema: str
    required_capabilities: tuple[str, ...]
    estimate_tokens: int
    max_output_tokens: int
    attempt: int
    extra_judgment: bool
    jury: bool
    producer_target: str | None
    producer_group: str | None
    prompt: str
    escalation_from: str | None = None
    escalation_reason: str | None = None
    context_hash: str | None = None
    privacy_mode: str = "deny_remote"
    producer_model: str | None = None

    def __post_init__(self) -> None:
        _safe_id(self.run_id, "request.run_id")
        _safe_id(self.task_id, "request.task_id")
        if self.role_id not in ROLE_IDS:
            raise InferenceConfigError("request role_id is invalid")
        if self.department_id not in {"M00", *{f"S{item}0" for item in range(1, 6)}}:
            raise InferenceConfigError("request department_id is invalid")
        if self.activation_mode not in {"RUN", "CHECK", "SHIFT", "FREEZE"}:
            raise InferenceConfigError("request activation_mode is invalid")
        _bounded_int(self.cycle_id, "request.cycle_id")
        _bounded_int(self.estimate_tokens, "request.estimate_tokens")
        _bounded_int(self.max_output_tokens, "request.max_output_tokens", positive=True)
        _bounded_int(self.attempt, "request.attempt")
        if type(self.extra_judgment) is not bool or type(self.jury) is not bool:
            raise InferenceConfigError("request flags are invalid")
        if not isinstance(self.prompt, str) or not self.prompt or "\x00" in self.prompt:
            raise InferenceConfigError("request prompt is invalid")
        if self.prompt_hash != sha256(self.prompt.encode("utf-8")):
            raise InferenceConfigError("request prompt_hash is invalid")
        if not isinstance(self.prompt_version, str) or not self.prompt_version or len(self.prompt_version) > 256:
            raise InferenceConfigError("request prompt_version is invalid")
        if not isinstance(self.base_hash, str) or _SHA.fullmatch(self.base_hash) is None:
            raise InferenceConfigError("request base_hash is invalid")
        if self.requested_output_schema not in {"department-packet.schema.json", "agent-proposal.schema.json"}:
            raise InferenceConfigError("request output schema is invalid")
        if not isinstance(self.required_capabilities, tuple) or len(self.required_capabilities) != len(set(self.required_capabilities)) or any(item not in CAPABILITIES for item in self.required_capabilities):
            raise InferenceConfigError("request capabilities are invalid")
        if self.producer_target is not None:
            _safe_id(self.producer_target, "request.producer_target")
        if self.producer_group is not None:
            _safe_id(self.producer_group, "request.producer_group")
        if self.producer_model is not None:
            _safe_id(self.producer_model, "request.producer_model")
        if self.jury and (self.producer_target is None or self.producer_group is None):
            raise InferenceConfigError("jury request requires producer identity metadata")
        if self.context_hash is not None and _SHA.fullmatch(self.context_hash) is None:
            raise InferenceConfigError("request context_hash is invalid")
        if self.privacy_mode not in PRIVACY_MODES:
            raise InferenceConfigError("request privacy_mode is invalid")
        has_escalation = self.escalation_from is not None or self.escalation_reason is not None
        if self.attempt == 0 and has_escalation:
            raise InferenceConfigError("initial request cannot contain escalation metadata")
        if self.attempt > 0:
            if not isinstance(self.escalation_from, str) or _SHA.fullmatch(self.escalation_from) is None:
                raise InferenceConfigError("escalated request lacks a valid prior route")
            if self.escalation_reason not in ESCALATION_REASONS:
                raise InferenceConfigError("escalated request lacks a valid reason")

    @classmethod
    def from_agent_task(
        cls, root: str | Path, task: Mapping[str, Any], *, prompt: str,
        required_capabilities: Sequence[str], estimate_tokens: int,
        max_output_tokens: int, attempt: int = 0, extra_judgment: bool = False,
        jury: bool = False, producer_target: str | None = None,
        producer_group: str | None = None, escalation_from: str | None = None,
        escalation_reason: str | None = None, context_hash: str | None = None,
        privacy_mode: str = "deny_remote", producer_model: str | None = None,
    ) -> "InferenceRequest":
        schema_path = Path(root) / "config" / "schemas" / "agent-task.schema.json"
        if schema_path.is_symlink() or not schema_path.is_file():
            raise InferenceConfigError("AgentTask schema is missing or unsafe")
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(task)
        except (OSError, json.JSONDecodeError, jsonschema.ValidationError) as error:
            raise InferenceConfigError("AgentTask is invalid") from error
        if not isinstance(prompt, str) or not prompt or "\x00" in prompt:
            raise InferenceConfigError("prompt is invalid")
        caps = tuple(required_capabilities)
        if len(caps) != len(set(caps)) or any(item not in CAPABILITIES for item in caps):
            raise InferenceConfigError("required capabilities are invalid")
        _bounded_int(estimate_tokens, "estimate_tokens")
        _bounded_int(max_output_tokens, "max_output_tokens", positive=True)
        _bounded_int(attempt, "attempt")
        if type(extra_judgment) is not bool or type(jury) is not bool:
            raise InferenceConfigError("inference request flags are invalid")
        role = task["role_id"]
        department = role if role.startswith("S") else f"S{role[1]}0"
        if producer_target is not None:
            _safe_id(producer_target, "producer_target")
        if producer_group is not None:
            _safe_id(producer_group, "producer_group")
        if producer_model is not None:
            _safe_id(producer_model, "producer_model")
        if context_hash is not None and _SHA.fullmatch(context_hash) is None:
            raise InferenceConfigError("context_hash is invalid")
        if privacy_mode not in PRIVACY_MODES:
            raise InferenceConfigError("privacy_mode is invalid")
        if escalation_from is not None and _SHA.fullmatch(escalation_from) is None:
            raise InferenceConfigError("escalation_from is invalid")
        if escalation_reason is not None and escalation_reason not in ESCALATION_REASONS:
            raise InferenceConfigError("escalation_reason is invalid")
        return cls(
            run_id=task["run_id"], cycle_id=task["cycle_id"],
            task_id=task["task_id"], role_id=role, department_id=department,
            activation_mode=task["activation_mode"],
            prompt_hash=sha256(prompt.encode("utf-8")),
            prompt_version=task["prompt_version"], base_hash=task["base_hash"],
            requested_output_schema=task["requested_output_schema"],
            required_capabilities=caps, estimate_tokens=estimate_tokens,
            max_output_tokens=max_output_tokens, attempt=attempt,
            extra_judgment=extra_judgment, jury=jury,
            producer_target=producer_target, producer_group=producer_group,
            prompt=prompt, escalation_from=escalation_from,
            escalation_reason=escalation_reason, context_hash=context_hash,
            privacy_mode=privacy_mode, producer_model=producer_model,
        )

    def identity(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id, "cycle_id": self.cycle_id,
            "task_id": self.task_id, "role_id": self.role_id,
            "department_id": self.department_id,
            "activation_mode": self.activation_mode,
            "prompt_hash": self.prompt_hash, "prompt_version": self.prompt_version,
            "base_hash": self.base_hash,
            "requested_output_schema": self.requested_output_schema,
            "required_capabilities": list(self.required_capabilities),
            "estimate_tokens": self.estimate_tokens,
            "max_output_tokens": self.max_output_tokens,
            "attempt": self.attempt, "extra_judgment": self.extra_judgment,
            "jury": self.jury, "producer_target": self.producer_target,
            "producer_group": self.producer_group,
            "producer_model": self.producer_model,
            "context_hash": self.context_hash,
            "privacy_mode": self.privacy_mode,
            "escalation_from": self.escalation_from,
            "escalation_reason": self.escalation_reason,
        }

    @property
    def request_hash(self) -> str:
        return sha256(canonical_bytes(self.identity()))

    def escalated(self, previous_route_hash: str, reason_code: str) -> "InferenceRequest":
        if reason_code not in ESCALATION_REASONS:
            raise InferenceRoutingError("unsupported escalation reason")
        if _SHA.fullmatch(previous_route_hash) is None:
            raise InferenceRoutingError("previous route hash is invalid")
        return replace(
            self, attempt=self.attempt + 1, escalation_from=previous_route_hash,
            escalation_reason=reason_code,
        )


# M6 compares role, cycle and base for AgentProposal receipts.  The other
# fields below are also protocol-owned because they identify the canonical
# contract or are deterministically derived by LOOP, never the model.
_OUTPUT_IDENTITY_FIELDS = {
    "agent-proposal.schema.json": (
        ("role_id", "role_id"),
        ("cycle_id", "cycle_id"),
        ("base_hash", "base_hash"),
        ("prompt_version", "prompt_version"),
    ),
    "department-packet.schema.json": (
        ("run_id", "run_id"),
        ("department_id", "role_id"),
        ("cycle_id", "cycle_id"),
        ("base_hash", "base_hash"),
    ),
}

_AGENT_PROPOSAL_PROTOCOL_FIELDS = frozenset({
    "schema_version", "proposal_id", "role_id", "cycle_id", "base_hash",
    "prompt_version",
})
_AGENT_PROPOSAL_MODEL_FIELDS = frozenset({
    "scope", "evidence_locators", "patch_or_operations", "affected_claims",
    "dependencies", "risk", "confidence", "requested_validations",
})


def output_identity_values(request: InferenceRequest) -> dict[str, Any]:
    """Return only the AgentTask-derived identity M6 already requires."""
    try:
        bindings = _OUTPUT_IDENTITY_FIELDS[request.requested_output_schema]
    except KeyError as error:
        raise InferenceIntegrityError("output schema has no closed identity binding") from error
    return {field: getattr(request, request_field) for field, request_field in bindings}


def agent_proposal_payload_schema(
    canonical_schema: Mapping[str, Any],
) -> dict[str, Any]:
    """Project canonical constraints onto model-owned scientific fields only."""
    if not isinstance(canonical_schema, Mapping):
        raise InferenceIntegrityError("canonical output schema must be an object")
    if canonical_schema.get("$id") != "agent-proposal.schema.json":
        raise InferenceIntegrityError("canonical AgentProposal schema identity differs")
    def contains_reference(value: Any) -> bool:
        if isinstance(value, Mapping):
            return "$ref" in value or any(contains_reference(item) for item in value.values())
        if isinstance(value, list):
            return any(contains_reference(item) for item in value)
        return False

    if contains_reference(canonical_schema):
        raise InferenceIntegrityError("canonical output schema contains unsupported reference")
    schema = deepcopy(dict(canonical_schema))
    properties = schema.get("properties")
    required = schema.get("required")
    if not isinstance(properties, dict) or not isinstance(required, list):
        raise InferenceIntegrityError("canonical output schema properties are missing")
    fields = set(properties)
    if fields != _AGENT_PROPOSAL_PROTOCOL_FIELDS | _AGENT_PROPOSAL_MODEL_FIELDS:
        raise InferenceIntegrityError("AgentProposal field ownership is incomplete")
    if any(not isinstance(properties[field], dict) or "$ref" in properties[field]
           for field in fields):
        raise InferenceIntegrityError("AgentProposal property is unsafe")
    if set(required) != fields or any(not isinstance(field, str) for field in required):
        raise InferenceIntegrityError("AgentProposal required fields differ from ownership")
    payload = {
        "$schema": schema.get("$schema"),
        "$id": "agent-proposal-payload.schema.json",
        "title": "AgentProposalScientificPayload",
        "type": "object",
        "additionalProperties": False,
        "required": sorted(_AGENT_PROPOSAL_MODEL_FIELDS),
        "properties": {
            field: deepcopy(properties[field])
            for field in sorted(_AGENT_PROPOSAL_MODEL_FIELDS)
        },
    }
    try:
        jsonschema.Draft202012Validator.check_schema(payload)
    except jsonschema.SchemaError as error:
        raise InferenceIntegrityError("AgentProposal payload schema is malformed") from error
    return payload


def model_output_schema(root: str | Path, request: InferenceRequest) -> dict[str, Any]:
    """Select the strict model contract without changing the final contract."""
    canonical = load_requested_output_schema(root, request.requested_output_schema)
    if request.requested_output_schema == "agent-proposal.schema.json":
        return agent_proposal_payload_schema(canonical)
    return canonical


def trusted_protocol_envelope(
    root: str | Path, request: InferenceRequest, payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Create the non-model portion of an AgentProposal deterministically."""
    if request.requested_output_schema != "agent-proposal.schema.json":
        raise InferenceIntegrityError("trusted AgentProposal envelope requires AgentProposal request")
    if not isinstance(payload, Mapping) or set(payload) & _AGENT_PROPOSAL_PROTOCOL_FIELDS:
        raise InferenceIntegrityError("model payload overlaps trusted protocol fields")
    canonical = load_requested_output_schema(root, request.requested_output_schema)
    schema_version = canonical.get("properties", {}).get("schema_version", {}).get("const")
    if not isinstance(schema_version, str):
        raise InferenceIntegrityError("canonical AgentProposal schema_version is unsafe")
    proposal_id = "p-" + sha256(canonical_bytes({
        "task_id": request.task_id,
        "payload_sha256": sha256(canonical_bytes(payload)),
    }))[:48]
    return {
        "schema_version": schema_version, "proposal_id": proposal_id,
        "role_id": request.role_id, "cycle_id": request.cycle_id,
        "base_hash": request.base_hash, "prompt_version": request.prompt_version,
    }


def compose_agent_proposal(
    root: str | Path, request: InferenceRequest, payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate payload, compose trusted fields, then revalidate canonically."""
    canonical = load_requested_output_schema(root, request.requested_output_schema)
    if request.requested_output_schema != "agent-proposal.schema.json":
        raise InferenceIntegrityError("AgentProposal composition requested for another schema")
    if not isinstance(payload, Mapping):
        raise InferenceOutputError("model payload must be an object")
    try:
        jsonschema.Draft202012Validator(
            agent_proposal_payload_schema(canonical),
            format_checker=jsonschema.FormatChecker(),
        ).validate(payload)
    except jsonschema.ValidationError as error:
        raise InferenceOutputError("model payload violates scientific payload schema") from error
    envelope = trusted_protocol_envelope(root, request, payload)
    proposal = {**envelope, **deepcopy(dict(payload))}
    try:
        jsonschema.Draft202012Validator(
            canonical, format_checker=jsonschema.FormatChecker(),
        ).validate(proposal)
    except jsonschema.ValidationError as error:
        raise InferenceIntegrityError("composed AgentProposal violates canonical schema") from error
    if not output_identity_matches(request, proposal):
        raise InferenceIntegrityError("composed AgentProposal identity differs from AgentTask")
    return proposal


def output_identity_matches(request: InferenceRequest, document: Mapping[str, Any]) -> bool:
    """Check model bytes against the same authority independently of decoding."""
    if not isinstance(document, Mapping):
        return False
    return all(
        canonical_bytes(document.get(field)) == canonical_bytes(expected)
        for field, expected in output_identity_values(request).items()
    )


@dataclass(frozen=True)
class RouteDecision:
    request_hash: str
    routing_policy_hash: str
    target_id: str | None
    provider: str | None
    model: str | None
    backend_type: str | None
    reason_code: str
    attempt: int
    whether_local: bool | None
    whether_paid: bool | None
    required_capabilities: tuple[str, ...]
    matched_capabilities: tuple[str, ...]
    fallback_chain: tuple[str, ...]
    independence_group: str | None
    context_hash: str | None = None
    privacy_mode: str = "deny_remote"

    def identity(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "request_hash": self.request_hash,
            "routing_policy_hash": self.routing_policy_hash,
            "target_id": self.target_id, "provider": self.provider,
            "model": self.model, "backend_type": self.backend_type,
            "reason_code": self.reason_code, "attempt": self.attempt,
            "whether_local": self.whether_local, "whether_paid": self.whether_paid,
            "required_capabilities": list(self.required_capabilities),
            "matched_capabilities": list(self.matched_capabilities),
            "fallback_chain": list(self.fallback_chain),
            "independence_group": self.independence_group,
            "context_hash": self.context_hash,
            "privacy_mode": self.privacy_mode,
        }

    @property
    def decision_hash(self) -> str:
        return sha256(canonical_bytes(self.identity()))


class ModelRouter:
    """Pure deterministic selection over a validated registry."""

    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def _chain(self, role_targets: Sequence[str]) -> tuple[str, ...]:
        result: list[str] = []
        for first in role_targets:
            current: str | None = first
            while current is not None:
                if current not in result:
                    result.append(current)
                current = self.registry.target(current).fallback_target
        return tuple(result)

    def route(self, request: InferenceRequest, budget_status: Mapping[str, Any] | None = None) -> RouteDecision:
        if request.activation_mode == "FREEZE":
            return RouteDecision(
                request.request_hash, self.registry.policy_hash, None, None, None,
                None, "NO_INFERENCE_REQUIRED", request.attempt, None, None,
                request.required_capabilities, (), (), None,
                request.context_hash, request.privacy_mode,
            )
        if not self.registry.enabled:
            raise InferenceRoutingError("inference is disabled")
        if budget_status is not None and budget_status.get("state") in {"PAUSED", "STOPPED"}:
            raise InferenceRoutingError("budget state does not permit routing")
        route = self.registry.role_routes.get(request.role_id)
        if route is None:
            raise InferenceRoutingError("role has no inference route")
        required = tuple(sorted(set(request.required_capabilities) | set(route["required_capabilities"])))
        eligible: list[InferenceTarget] = []
        for target_id in self._chain(route["targets"]):
            target = self.registry.target(target_id)
            if not target.enabled:
                continue
            if target.local and not self.registry.allow_local:
                continue
            if not target.local and not self.registry.allow_remote:
                continue
            if target.paid and not self.registry.allow_paid:
                continue
            if not target.local and request.privacy_mode == "deny_remote":
                continue
            if request.max_output_tokens > target.max_output_tokens or request.estimate_tokens + request.max_output_tokens > target.context_limit:
                continue
            if len(request.prompt.encode("utf-8")) > max(4096, target.context_limit * 16):
                continue
            if not set(required).issubset(target.capabilities):
                continue
            if request.jury and self.registry.jury_independence:
                if self.registry.jury_independence_mode == "model":
                    if request.producer_model is None or request.producer_model == target.model:
                        continue
                elif request.producer_group == target.independence_group:
                    continue
            eligible.append(target)
        if not eligible:
            raise InferenceRoutingError("no authorized target satisfies required capabilities")
        if request.attempt >= self.registry.max_route_attempts:
            raise InferenceRoutingError("maximum route attempts reached")
        if request.attempt > 0:
            if not self.registry.escalation_enabled or request.escalation_reason not in ESCALATION_REASONS or request.escalation_from is None:
                raise InferenceRoutingError("escalation lacks a permitted evidence code")
        if request.attempt >= len(eligible):
            raise InferenceRoutingError("no higher authorized fallback target exists")
        target = eligible[request.attempt]
        reason = "ROLE_POLICY_MATCH" if request.attempt == 0 else str(request.escalation_reason)
        return RouteDecision(
            request.request_hash, self.registry.policy_hash, target.target_id,
            target.provider, target.model, target.backend_type, reason,
            request.attempt, target.local, target.paid, required,
            tuple(sorted(set(required) & set(target.capabilities))),
            tuple(item.target_id for item in eligible), target.independence_group,
            request.context_hash, request.privacy_mode,
        )


@dataclass(frozen=True)
class InferenceResult:
    response: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_tokens: int | None = None
    usage_available: bool = False
    cost_microunits: int | None = None
    currency: str | None = None
    wall_time_seconds: int = 0
    finish_reason: str = "unknown"

    def __post_init__(self) -> None:
        if not isinstance(self.response, str) or "\x00" in self.response:
            raise InferenceBackendError("BACKEND_FAILURE", "backend response is invalid", sent=True)
        for name in ("input_tokens", "output_tokens", "cache_tokens", "cost_microunits", "wall_time_seconds"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 0 or value > 2**63 - 1):
                raise InferenceBackendError("BACKEND_FAILURE", f"backend {name} is invalid", sent=True)
        if type(self.usage_available) is not bool:
            raise InferenceBackendError("BACKEND_FAILURE", "backend usage flag is invalid", sent=True)
        if self.finish_reason not in FINISH_REASONS:
            raise InferenceBackendError("BACKEND_FAILURE", "backend finish reason is invalid", sent=True)


class InferenceBackend(Protocol):
    is_test_double: bool

    def preflight(self, target: InferenceTarget) -> Mapping[str, Any]: ...
    def complete(self, request: InferenceRequest, target: InferenceTarget) -> InferenceResult: ...


@dataclass(frozen=True)
class InferenceReceipt:
    receipt_id: str
    run_id: str
    cycle_id: int
    task_id: str
    role_id: str
    call_id: str
    reservation_id: str
    route_decision_hash: str
    routing_policy_hash: str
    provider: str
    model: str
    target_id: str
    backend_type: str
    independence_group: str
    prompt_hash: str
    response_hash: str
    requested_output_schema: str
    input_tokens: int | None
    output_tokens: int | None
    cache_tokens: int | None
    usage_available: bool
    cost_microunits: int | None
    currency: str | None
    wall_time_seconds: int
    finish_reason: str
    attempt: int
    escalation_from: str | None
    escalation_reason: str | None
    created_at: str
    output_sha256: str | None = None
    output_locator: str | None = None
    context_hash: str | None = None
    privacy_mode: str = "deny_remote"

    def public(self) -> dict[str, Any]:
        return {"schema_version": RECEIPT_SCHEMA_VERSION, **self.__dict__}


class InferenceStore:
    """Write-once route and receipt storage under one per-run lock."""

    def __init__(self, root: str | Path, run_id: str, *, clock: Any | None = None):
        raw = Path(root)
        if raw.is_symlink() or not raw.is_dir():
            raise InferenceIntegrityError("root must be an existing non-symlink directory")
        self.root = raw.resolve()
        self.run_id = _safe_id(run_id, "run_id")
        self.clock = clock
        self.inference_dir = self.root / "state" / "inference" / self.run_id
        self.routes_dir = self.inference_dir / "routes"
        self.receipts_dir = self.inference_dir / "receipts"
        self.outputs_dir = self.inference_dir / "outputs"
        self.lock_dir = self.root / "state" / "locks"
        for path in (self.root / "state", self.root / "state" / "inference", self.inference_dir, self.routes_dir, self.receipts_dir, self.outputs_dir, self.lock_dir):
            self._ensure_dir(path)

    @staticmethod
    def _ensure_dir(path: Path) -> None:
        if path.exists() and (path.is_symlink() or not path.is_dir()):
            raise InferenceIntegrityError("unsafe inference directory")
        path.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            raise InferenceIntegrityError("symlinked inference directory")

    @property
    def lock_path(self) -> Path:
        path = self.lock_dir / f"{self.run_id}.inference.lock"
        if path.is_symlink():
            raise InferenceIntegrityError("inference lock is symlinked")
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

    def _atomic(self, path: Path, data: bytes) -> None:
        descriptor, name = tempfile.mkstemp(prefix=".tmp-inference-", dir=path.parent)
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

    def _regular_json(self, path: Path) -> dict[str, Any]:
        if path.is_symlink() or not path.is_file():
            raise InferenceIntegrityError("inference artifact is unsafe")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise InferenceIntegrityError("inference artifact is invalid JSON") from error
        if not isinstance(value, dict):
            raise InferenceIntegrityError("inference artifact must be an object")
        return value

    def persist_route(self, decision: RouteDecision) -> dict[str, Any]:
        path = self.routes_dir / f"{decision.decision_hash}.json"
        if path.is_symlink():
            raise InferenceIntegrityError("route path is symlinked")
        with self._lock():
            if path.exists():
                prior = self._regular_json(path)
                body = {key: value for key, value in prior.items() if key not in {"route_decision_hash", "created_at"}}
                if body != decision.identity() or prior.get("route_decision_hash") != decision.decision_hash:
                    raise InferenceIntegrityError("conflicting route decision")
                _timestamp(prior.get("created_at"))
                return prior
            value = {
                **decision.identity(), "route_decision_hash": decision.decision_hash,
                "created_at": self.clock.now_utc() if self.clock is not None else _now(),
            }
            _timestamp(value["created_at"])
            self._atomic(path, canonical_bytes(value) + b"\n")
            return self._regular_json(path)

    def _receipt_schema(self) -> Mapping[str, Any]:
        path = self.root / "config" / "schemas" / "inference-receipt.schema.json"
        if path.is_symlink() or not path.is_file():
            raise InferenceIntegrityError("inference receipt schema is missing or unsafe")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise InferenceIntegrityError("inference receipt schema is unreadable") from error
        return value

    def persist_receipt(self, receipt: InferenceReceipt) -> dict[str, Any]:
        if receipt.run_id != self.run_id:
            raise InferenceIntegrityError("receipt belongs to another run")
        value = receipt.public()
        value["receipt_hash"] = sha256(canonical_bytes(value))
        try:
            jsonschema.Draft202012Validator(self._receipt_schema(), format_checker=jsonschema.FormatChecker()).validate(value)
        except jsonschema.ValidationError as error:
            raise InferenceIntegrityError("inference receipt violates schema") from error
        path = self.receipts_dir / f"{receipt.call_id}.json"
        if path.is_symlink():
            raise InferenceIntegrityError("receipt path is symlinked")
        encoded = canonical_bytes(value) + b"\n"
        with self._lock():
            if path.exists():
                if path.read_bytes() != encoded:
                    raise InferenceIntegrityError("conflicting inference receipt")
                return self._regular_json(path)
            self._atomic(path, encoded)
            return self._regular_json(path)

    def persist_output(
        self, call_id: str, document: Mapping[str, Any], metadata: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Publish one validated scientific output as an fsynced write-once tree."""
        _safe_id(call_id, "call_id")
        if not isinstance(document, Mapping) or not isinstance(metadata, Mapping):
            raise InferenceIntegrityError("output document/metadata must be objects")
        output_bytes = canonical_bytes(document) + b"\n"
        output_sha = sha256(output_bytes)
        locator = f"state/inference/{self.run_id}/outputs/{call_id}/{output_sha}.json"
        manifest = {
            **dict(metadata), "schema_version": RECEIPT_SCHEMA_VERSION,
            "run_id": self.run_id, "call_id": call_id,
            "output_sha256": output_sha, "output_locator": locator,
            "output_size_bytes": len(output_bytes),
        }
        manifest["manifest_hash"] = sha256(canonical_bytes(manifest))
        encoded_manifest = canonical_bytes(manifest) + b"\n"
        final = self.outputs_dir / call_id
        if final.is_symlink():
            raise InferenceIntegrityError("output path is symlinked")
        with self._lock():
            if final.exists():
                prior = self.output_for_call(call_id)
                if prior is None or prior["bytes"] != output_bytes or prior["manifest"] != manifest:
                    raise InferenceIntegrityError("conflicting durable inference output")
                return prior["manifest"]
            temporary = Path(tempfile.mkdtemp(prefix=".tmp-output-", dir=self.outputs_dir))
            try:
                output_path = temporary / f"{output_sha}.json"
                manifest_path = temporary / "manifest.json"
                for path, data in ((output_path, output_bytes), (manifest_path, encoded_manifest)):
                    with path.open("wb") as stream:
                        stream.write(data)
                        stream.flush()
                        os.fsync(stream.fileno())
                self._fsync_dir(temporary)
                os.replace(temporary, final)
                self._fsync_dir(self.outputs_dir)
            finally:
                if temporary.exists():
                    shutil.rmtree(temporary)
        loaded = self.output_for_call(call_id)
        if loaded is None or loaded["manifest"] != manifest:
            raise InferenceIntegrityError("durable inference output verification failed")
        return manifest

    def output_for_call(self, call_id: str) -> dict[str, Any] | None:
        _safe_id(call_id, "call_id")
        directory = self.outputs_dir / call_id
        if not directory.exists():
            return None
        if directory.is_symlink() or not directory.is_dir():
            raise InferenceIntegrityError("durable output directory is unsafe")
        manifest_path = directory / "manifest.json"
        manifest = self._regular_json(manifest_path)
        advertised = manifest.get("manifest_hash")
        body = {key: value for key, value in manifest.items() if key != "manifest_hash"}
        if advertised != sha256(canonical_bytes(body)):
            raise InferenceIntegrityError("durable output manifest hash differs")
        if manifest.get("run_id") != self.run_id or manifest.get("call_id") != call_id:
            raise InferenceIntegrityError("durable output identity differs")
        output_sha = manifest.get("output_sha256")
        if not isinstance(output_sha, str) or _SHA.fullmatch(output_sha) is None:
            raise InferenceIntegrityError("durable output hash is invalid")
        if {path.name for path in directory.iterdir()} != {"manifest.json", f"{output_sha}.json"}:
            raise InferenceIntegrityError("durable output tree contains unexpected entries")
        output_path = directory / f"{output_sha}.json"
        if output_path.is_symlink() or not output_path.is_file():
            raise InferenceIntegrityError("durable output artifact is unsafe")
        data = output_path.read_bytes()
        if sha256(data) != output_sha or len(data) != manifest.get("output_size_bytes"):
            raise InferenceIntegrityError("durable output bytes differ")
        expected_locator = f"state/inference/{self.run_id}/outputs/{call_id}/{output_sha}.json"
        if manifest.get("output_locator") != expected_locator:
            raise InferenceIntegrityError("durable output locator differs")
        try:
            document = json.loads(data)
        except json.JSONDecodeError as error:
            raise InferenceIntegrityError("durable output is invalid JSON") from error
        if not isinstance(document, dict):
            raise InferenceIntegrityError("durable output must be an object")
        return {"manifest": manifest, "document": document, "bytes": data, "path": output_path}

    def materialize_output(self, call_id: str, workspace: str | Path) -> dict[str, Any]:
        loaded = self.output_for_call(call_id)
        if loaded is None:
            raise InferenceIntegrityError("durable output is missing")
        directory = Path(workspace)
        resolved = directory.resolve()
        if directory.is_symlink() or not directory.is_dir() or self.root not in resolved.parents:
            raise InferenceIntegrityError("M6 workspace is unsafe")
        target = directory / "agent-proposal.json"
        if target.is_symlink():
            raise InferenceIntegrityError("M6 output path is symlinked")
        data = loaded["bytes"]
        if target.exists():
            if not target.is_file() or target.read_bytes() != data:
                raise InferenceIntegrityError("M6 output conflicts with durable inference output")
        else:
            self._atomic(target, data)
        return {"path": str(target), "sha256": loaded["manifest"]["output_sha256"]}

    def receipt_for_call(self, call_id: str) -> dict[str, Any] | None:
        _safe_id(call_id, "call_id")
        path = self.receipts_dir / f"{call_id}.json"
        if not path.exists():
            return None
        value = self._regular_json(path)
        try:
            jsonschema.Draft202012Validator(self._receipt_schema(), format_checker=jsonschema.FormatChecker()).validate(value)
        except jsonschema.ValidationError as error:
            raise InferenceIntegrityError("persisted inference receipt violates schema") from error
        advertised = value.get("receipt_hash")
        body = {key: item for key, item in value.items() if key != "receipt_hash"}
        if not isinstance(advertised, str) or advertised != sha256(canonical_bytes(body)):
            raise InferenceIntegrityError("persisted inference receipt hash is invalid")
        if value.get("run_id") != self.run_id or value.get("call_id") != call_id:
            raise InferenceIntegrityError("persisted inference receipt path binding is invalid")
        return value

    def routes(self) -> list[dict[str, Any]]:
        values = []
        for path in sorted(self.routes_dir.glob("*.json")):
            value = self._regular_json(path)
            advertised = value.get("route_decision_hash")
            body = {key: item for key, item in value.items() if key not in {"route_decision_hash", "created_at"}}
            if not isinstance(advertised, str) or advertised != sha256(canonical_bytes(body)) or path.stem != advertised:
                raise InferenceIntegrityError("route decision hash is invalid")
            values.append(value)
        return values

    def receipts(self) -> list[dict[str, Any]]:
        values = []
        for path in sorted(self.receipts_dir.glob("*.json")):
            value = self.receipt_for_call(path.stem)
            if value is not None:
                values.append(value)
        return values


class InferenceRuntime:
    """Coordinate exactly one route/reserve/admit/backend/receipt/reconcile call."""

    def __init__(
        self, root: str | Path, ledger: BudgetLedger, registry: ModelRegistry,
        backends: Mapping[str, InferenceBackend], *, clock: Any | None = None,
        fault: Any | None = None,
    ):
        if ledger.run_id is None:
            raise InferenceConfigError("ledger run identity is invalid")
        self.root = Path(root).resolve()
        self.ledger = ledger
        self.registry = registry
        self.registry.validate_enabled_policy()
        if ledger.routing_policy_hash != registry.policy_hash:
            raise InferenceIntegrityError("registry and budget ledger use different routing policies")
        self.router = ModelRouter(registry)
        self.backends = dict(backends)
        self.clock = clock
        self.fault = fault
        self.store = InferenceStore(self.root, ledger.run_id, clock=clock)

    @staticmethod
    def call_id(request: InferenceRequest, decision: RouteDecision) -> str:
        body = [request.run_id, request.cycle_id, request.task_id, request.role_id,
                request.prompt_hash, decision.decision_hash, request.attempt]
        return "ic-" + sha256(canonical_bytes(body))[:48]

    @staticmethod
    def receipt_id(call_id: str) -> str:
        return "ir-" + sha256(call_id.encode("ascii"))[:48]

    def preflight(self) -> dict[str, Any]:
        result = self.registry.status()
        target_status: dict[str, Any] = {}
        for target_id in result["enabled_targets"]:
            target = self.registry.target(target_id)
            backend = self.backends.get(target.backend_type)
            if backend is None:
                target_status[target_id] = {"ready": False, "reason": "backend_not_registered"}
            else:
                target_status[target_id] = dict(backend.preflight(target))
        return {**result, "targets": target_status}

    def route(self, request: InferenceRequest) -> RouteDecision:
        decision = self.router.route(request, self.ledger.status(current_cycle=request.cycle_id))
        if decision.reason_code != "NO_INFERENCE_REQUIRED":
            self.store.persist_route(decision)
        return decision

    def _validated_document(self, request: InferenceRequest, response: str) -> dict[str, Any] | None:
        try:
            value = json.loads(response)
            if request.requested_output_schema == "agent-proposal.schema.json":
                return compose_agent_proposal(self.root, request, value)
            schema = load_requested_output_schema(self.root, request.requested_output_schema)
            jsonschema.Draft202012Validator(
                schema, format_checker=jsonschema.FormatChecker(),
            ).validate(value)
        except (json.JSONDecodeError, jsonschema.ValidationError, InferenceOutputError):
            return None
        if not isinstance(value, dict) or not output_identity_matches(request, value):
            return None
        return value

    def _validate_response_schema(self, request: InferenceRequest, response: str) -> bool:
        return self._validated_document(request, response) is not None

    @staticmethod
    def _receipt_from_manifest(manifest: Mapping[str, Any]) -> InferenceReceipt:
        names = InferenceReceipt.__dataclass_fields__
        try:
            return InferenceReceipt(**{name: manifest[name] for name in names})
        except (KeyError, TypeError) as error:
            raise InferenceIntegrityError("durable output lacks receipt reconstruction metadata") from error

    @staticmethod
    def _estimated_cost(request: InferenceRequest, target: InferenceTarget) -> int:
        if target.pricing is None:
            return 0
        return target.pricing.cost(request.estimate_tokens, request.max_output_tokens, 0)

    def _canonical_cost(self, result: InferenceResult, target: InferenceTarget) -> tuple[int | None, str | None]:
        if target.pricing is None:
            return result.cost_microunits, result.currency
        if not result.usage_available or any(
            value is None for value in (result.input_tokens, result.output_tokens, result.cache_tokens)
        ):
            return None, None
        cost = target.pricing.cost(
            int(result.input_tokens), int(result.output_tokens), int(result.cache_tokens),
        )
        return cost, target.pricing.currency

    def _reconcile_receipt(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return self.ledger.reconcile(
            value["reservation_id"], receipt_id=value["receipt_id"],
            input_tokens=value.get("input_tokens"), output_tokens=value.get("output_tokens"),
            cache_tokens=value.get("cache_tokens"), wall_time_seconds=value.get("wall_time_seconds"),
            cost_microunits=value.get("cost_microunits"), currency=value.get("currency"),
            usage_available=value.get("usage_available"),
        )

    def execute(
        self, request: InferenceRequest, *, live: bool = False,
        allow_test_doubles: bool = False,
    ) -> dict[str, Any]:
        if type(live) is not bool or type(allow_test_doubles) is not bool:
            raise InferenceConfigError("runtime flags must be strictly boolean")
        if self.registry.privacy_mode is not None and request.privacy_mode != self.registry.privacy_mode:
            raise InferenceRoutingError("request privacy mode differs from project policy")
        decision = self.router.route(request, self.ledger.status(current_cycle=request.cycle_id))
        if decision.reason_code == "NO_INFERENCE_REQUIRED":
            return {"decision": decision.identity(), "result": None, "receipt": None, "replayed": False}
        persisted_route = self.store.persist_route(decision)
        call_id = self.call_id(request, decision)
        existing = self.store.receipt_for_call(call_id)
        if existing is not None:
            if existing.get("route_decision_hash") != decision.decision_hash or existing.get("prompt_hash") != request.prompt_hash:
                raise InferenceIntegrityError("existing receipt conflicts with replayed request")
            if existing.get("output_sha256") is not None:
                durable = self.store.output_for_call(call_id)
                if (
                    durable is None
                    or durable["manifest"].get("output_sha256") != existing.get("output_sha256")
                    or durable["manifest"].get("output_locator") != existing.get("output_locator")
                    or durable["manifest"].get("context_hash") != existing.get("context_hash")
                    or durable["manifest"].get("privacy_mode") != existing.get("privacy_mode")
                ):
                    raise InferenceIntegrityError("receipt and durable output binding differ")
            reconciled = self._reconcile_receipt(existing)
            return {"decision": persisted_route, "result": None, "receipt": existing, "reconciled": reconciled, "replayed": True}
        target = self.registry.target(str(decision.target_id))
        if "structured_output" in target.capabilities:
            # Validate the exact project-local schema before reserve/admit so
            # an unsafe generation contract can never consume a backend call.
            model_output_schema(self.root, request)
        if not target.local and request.context_hash is None:
            raise InferenceRoutingError("remote routing requires a hash-bound materialized context")
        if target.paid and (
            target.pricing is None
            or self.ledger.max_run_cost_microunits is None
            or self.ledger.currency != target.pricing.currency
        ):
            raise InferenceRoutingError("paid routing lacks matching monetary enforcement")
        durable_output = self.store.output_for_call(call_id)
        backend = None
        if durable_output is None:
            backend = self.backends.get(target.backend_type)
            if backend is None:
                raise InferenceBackendError("BACKEND_FAILURE", "selected backend is not registered", sent=False)
            is_test_double = getattr(backend, "is_test_double", False)
            if is_test_double:
                if not allow_test_doubles or live:
                    raise InferenceBackendError("BACKEND_FAILURE", "test double is not authorized", sent=False)
            elif not live:
                raise InferenceBackendError("BACKEND_FAILURE", "real inference requires live authorization", sent=False)
        self.ledger.logger.emit("inference_routed", {
            "call_id": call_id, "target_id": target.target_id,
            "provider": target.provider, "model": target.model,
            "backend_type": target.backend_type,
            "route_decision_hash": decision.decision_hash,
            "routing_policy_hash": decision.routing_policy_hash,
            "attempt": request.attempt, "role_id": request.role_id,
            "cycle_id": request.cycle_id,
        })
        receipt_id = self.receipt_id(call_id)
        estimated_cost = self._estimated_cost(request, target)
        reservation = self.ledger.reserve(
            call_id, request.estimate_tokens, cycle_id=request.cycle_id,
            department_id=request.department_id, role_id=request.role_id,
            attempt=request.attempt, provider=target.provider, model=target.model,
            estimated_wall_time_seconds=target.timeout_seconds,
            estimated_cost_microunits=estimated_cost,
            extra_judgment=request.extra_judgment, live=live,
        )
        if durable_output is not None:
            if reservation.get("status") not in {"ADMITTED", "UNCERTAIN", "RECONCILED"}:
                raise InferenceIntegrityError("durable output exists before a compatible admission")
            recovered_receipt = self._receipt_from_manifest(durable_output["manifest"])
            persisted_receipt = self.store.persist_receipt(recovered_receipt)
            reconciled = self._reconcile_receipt(persisted_receipt)
            return {
                "decision": persisted_route, "result": None,
                "receipt": persisted_receipt, "reconciled": reconciled,
                "replayed": True, "recovered_from_output": True,
            }
        if reservation.get("status") == "RESERVED":
            raise InferenceIntegrityError("an earlier reservation requires explicit non-admission proof")
        if reservation.get("status") in {"ADMITTED", "UNCERTAIN"}:
            if reservation.get("status") == "ADMITTED":
                self.ledger.mark_uncertain(
                    reservation["reservation_id"], "response_unknown_after_admission",
                    receipt_id=receipt_id,
                )
            raise InferenceBackendError(
                "BACKEND_FAILURE", "admitted call has no durable response; automatic retry is forbidden",
                sent=True,
            )
        if self.fault is not None:
            self.fault("after_reserve")
        self.ledger.admit(reservation["reservation_id"], receipt_id)
        try:
            if self.fault is not None:
                self.fault("after_admit")
            if backend is None:
                raise InferenceIntegrityError("backend is unexpectedly unavailable for a new call")
            result = backend.complete(request, target)
            if not isinstance(result, InferenceResult):
                raise InferenceBackendError("BACKEND_FAILURE", "backend returned an invalid result", sent=True)
            if len(result.response.encode("utf-8")) > max(4096, target.max_output_tokens * 32):
                raise InferenceBackendError("BACKEND_FAILURE", "backend content exceeds the routed output bound", sent=True)
            document = self._validated_document(request, result.response)
            schema_valid = document is not None
            finish_reason = result.finish_reason if schema_valid else "schema_invalid"
            created_at = self.clock.now_utc() if self.clock is not None else _now()
            cost_microunits, currency = self._canonical_cost(result, target)
            receipt = InferenceReceipt(
                receipt_id, request.run_id, request.cycle_id, request.task_id,
                request.role_id, call_id, reservation["reservation_id"],
                decision.decision_hash, decision.routing_policy_hash,
                target.provider, target.model, target.target_id,
                target.backend_type, target.independence_group,
                request.prompt_hash, sha256(result.response.encode("utf-8")),
                request.requested_output_schema, result.input_tokens,
                result.output_tokens, result.cache_tokens, result.usage_available,
                cost_microunits, currency, result.wall_time_seconds,
                finish_reason, request.attempt, request.escalation_from,
                request.escalation_reason, created_at,
                None, None, request.context_hash, request.privacy_mode,
            )
            if document is not None:
                output_manifest = self.store.persist_output(
                    call_id, document, receipt.public() | {
                        "output_sha256": None, "output_locator": None,
                    },
                )
                receipt = replace(
                    receipt,
                    output_sha256=output_manifest["output_sha256"],
                    output_locator=output_manifest["output_locator"],
                )
                if self.fault is not None:
                    self.fault("after_output")
            persisted_receipt = self.store.persist_receipt(receipt)
            self.ledger.logger.emit("inference_receipt", {
                "call_id": call_id, "receipt_id": receipt_id,
                "target_id": target.target_id, "provider": target.provider,
                "model": target.model, "backend_type": target.backend_type,
                "finish_reason": finish_reason,
                "usage_available": result.usage_available,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "cache_tokens": result.cache_tokens,
                "wall_time_seconds": result.wall_time_seconds,
            })
            if self.fault is not None:
                self.fault("after_receipt")
            reconciled = self._reconcile_receipt(persisted_receipt)
        except InferenceOutputError:
            raise
        except BaseException as error:
            # SystemExit/KeyboardInterrupt model a process death and must leave
            # an already-persisted receipt recoverable rather than rewriting
            # the ledger during teardown.
            if not isinstance(error, (SystemExit, KeyboardInterrupt)):
                reason = error.reason_code if isinstance(error, InferenceBackendError) else "BACKEND_FAILURE"
                self.ledger.mark_uncertain(reservation["reservation_id"], reason.lower(), receipt_id=receipt_id)
                self.ledger.logger.emit("inference_uncertain", {
                    "call_id": call_id, "receipt_id": receipt_id,
                    "target_id": target.target_id, "reason_code": reason,
                    "attempt": request.attempt,
                }, level="WARNING")
            raise
        if not schema_valid:
            raise InferenceOutputError("backend output does not satisfy requested schema")
        if self.fault is not None:
            self.fault("after_reconcile")
        return {
            "decision": persisted_route, "result": result,
            "receipt": persisted_receipt, "reconciled": reconciled,
            "replayed": False,
        }

    def escalation(self, request: InferenceRequest, previous: RouteDecision, reason_code: str) -> RouteDecision:
        escalated = request.escalated(previous.decision_hash, reason_code)
        decision = self.router.route(escalated, self.ledger.status(current_cycle=request.cycle_id))
        self.store.persist_route(decision)
        return decision

    def status(self) -> dict[str, Any]:
        routes = sorted(
            self.store.routes(),
            key=lambda item: (str(item.get("created_at", "")), str(item.get("route_decision_hash", ""))),
        )
        receipts = self.store.receipts()
        calls_by_target: dict[str, int] = {}
        tokens_by_target: dict[str, int] = {}
        tokens_by_model: dict[str, int] = {}
        for receipt in receipts:
            target = receipt["target_id"]
            model = receipt["model"]
            calls_by_target[target] = calls_by_target.get(target, 0) + 1
            if receipt.get("usage_available"):
                tokens = sum(int(receipt.get(field) or 0) for field in ("input_tokens", "output_tokens", "cache_tokens"))
                tokens_by_target[target] = tokens_by_target.get(target, 0) + tokens
                tokens_by_model[model] = tokens_by_model.get(model, 0) + tokens
        budget = self.ledger.status()
        inference_reservations = [item for item in budget["reservations"] if str(item.get("call_id", "")).startswith("ic-")]
        return {
            **self.registry.status(),
            "calls_by_target": calls_by_target,
            "tokens_by_target": tokens_by_target,
            "tokens_by_model": tokens_by_model,
            "open_inference_calls": sum(item.get("status") in {"RESERVED", "ADMITTED"} for item in inference_reservations),
            "uncertain_inference_calls": sum(item.get("status") == "UNCERTAIN" for item in inference_reservations),
            "last_route_decision": routes[-1] if routes else None,
            "last_escalation": next((item for item in reversed(routes) if item.get("attempt", 0) > 0), None),
            "assurance": budget["assurance"],
        }


def inference_preflight(root: str | Path) -> dict[str, Any]:
    registry = ModelRegistry.from_project(root)
    registry.validate_enabled_policy()
    return registry.status()


__all__ = [
    "BACKEND_TYPES", "CAPABILITIES", "ESCALATION_REASONS", "InferenceBackend",
    "InferenceBackendError", "InferenceConfigError", "InferenceError",
    "InferenceIntegrityError", "InferenceOutputError", "InferenceReceipt",
    "InferenceRequest", "InferenceResult", "InferenceRuntime", "InferenceStore",
    "InferenceTarget", "ModelRegistry", "ModelRouter", "PAID_RUNTIME_READY",
    "PRIME_PER_CHILD_MODEL_SELECTION", "PRIVACY_MODES", "RECEIPT_SCHEMA_VERSION",
    "RouteDecision", "TargetPricing", "canonical_bytes",
    "inference_preflight", "routing_policy_hash", "sha256",
]
