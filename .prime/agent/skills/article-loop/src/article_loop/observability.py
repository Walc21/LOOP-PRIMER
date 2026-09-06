"""Small, durable, redacted structured logging for M12.

The logger is deliberately independent from the Prime Agent.  It accepts an
allowlist of operational fields, hashes every record, fsyncs each write and
rotates without deleting an older log.  Unknown fields are dropped before a
record reaches disk, which keeps prompts, article text and credentials out of
the observability surface by construction.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping


SCHEMA_VERSION = "1.0.0"
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_EVENT_TYPES = frozenset({
    "budget_reserved", "budget_admitted", "budget_reconciled",
    "budget_released", "budget_uncertain", "budget_authorized",
    "budget_progress", "budget_alert", "budget_paused", "budget_resumed",
    "budget_stopped", "supervisor_step",
    "inference_routed", "inference_receipt", "inference_uncertain",
})
_SAFE_KEYS = frozenset({
    "alert_code", "assurance", "attempt", "available", "call_id",
    "cache_tokens", "cost_microunits",
    "children", "confirmed", "cycle_id", "deadline_at", "department_id",
    "estimate_tokens", "event_type", "extra_judgment", "last_improvement_cycle",
    "input_tokens", "level", "limit", "limit_name", "model", "orphan_after_seconds",
    "output_tokens", "over_estimate",
    "profile", "provider", "reason_code", "remaining", "reservation_id",
    "retries", "role_id", "state", "status", "threshold", "total_tokens",
    "uncertain", "usage_tokens", "wall_time_seconds", "currency", "scope",
    "backend_type", "finish_reason", "independence_group", "receipt_id",
    "route_decision_hash", "routing_policy_hash", "target_id", "usage_available",
})
_SAFE_SCALARS = (str, int, float, bool)


class ObservabilityError(RuntimeError):
    """The structured log cannot be safely written or verified."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _safe_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise ObservabilityError(f"{label} is invalid")
    return value


def redact_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return only safe scalar operational fields from a payload."""
    if not isinstance(payload, Mapping):
        raise ObservabilityError("log payload must be an object")
    result: dict[str, Any] = {}
    for key, value in payload.items():
        if key not in _SAFE_KEYS or not isinstance(key, str):
            continue
        if isinstance(value, bool):
            result[key] = value
        elif isinstance(value, int):
            if value < 0:
                raise ObservabilityError(f"negative log value: {key}")
            result[key] = value
        elif isinstance(value, float):
            if not math.isfinite(value) or value < 0:
                raise ObservabilityError(f"invalid log value: {key}")
            result[key] = value
        elif isinstance(value, str):
            if len(value) > 512 or "\x00" in value:
                raise ObservabilityError(f"invalid log string: {key}")
            result[key] = value
    return result


class StructuredLogger:
    """Append-only JSONL logger with content-addressed records and rotation."""

    def __init__(
        self,
        root: str | Path,
        run_id: str,
        *,
        max_bytes: int = 65536,
        clock: Any | None = None,
        read_only: bool = False,
    ):
        raw_root = Path(root)
        if raw_root.is_symlink() or not raw_root.is_dir():
            raise ObservabilityError("root must be an existing non-symlink directory")
        self.root = raw_root.resolve()
        self.run_id = _safe_id(run_id, "run_id")
        if type(max_bytes) is not int or max_bytes < 1024:
            raise ObservabilityError("max_bytes must be an integer >= 1024")
        self.max_bytes = max_bytes
        self.clock = clock
        if type(read_only) is not bool:
            raise ObservabilityError("read_only must be boolean")
        self.read_only = read_only
        self.log_dir = self.root / "logs"
        self.lock_dir = self.root / "state" / "locks"
        if self.read_only:
            self._ensure_readable_dir(self.log_dir)
            self._ensure_readable_dir(self.lock_dir)
        else:
            self._ensure_dir(self.log_dir)
            self._ensure_dir(self.lock_dir)

    def _ensure_dir(self, path: Path) -> None:
        if path.exists() and (path.is_symlink() or not path.is_dir()):
            raise ObservabilityError(f"unsafe log directory: {path.name}")
        path.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            raise ObservabilityError(f"unsafe log directory: {path.name}")

    @staticmethod
    def _ensure_readable_dir(path: Path) -> None:
        """Validate an optional directory without creating it for observation."""
        if path.exists() and (path.is_symlink() or not path.is_dir()):
            raise ObservabilityError(f"unsafe log directory: {path.name}")

    @property
    def path(self) -> Path:
        path = self.log_dir / f"{self.run_id}.jsonl"
        if path.is_symlink():
            raise ObservabilityError("log file is symlinked")
        if path.exists() and not path.is_file():
            raise ObservabilityError("log path is not a regular file")
        return path

    @property
    def lock_path(self) -> Path:
        path = self.lock_dir / f"{self.run_id}.observability.lock"
        if path.is_symlink():
            raise ObservabilityError("log lock is symlinked")
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
        descriptor, name = tempfile.mkstemp(prefix=".tmp-log-", dir=path.parent)
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

    def _all_log_paths(self) -> list[Path]:
        paths = []
        for path in self.log_dir.glob(f"{self.run_id}*.jsonl"):
            if path.is_symlink() or not path.is_file():
                raise ObservabilityError("unsafe rotated log")
            paths.append(path)
        return paths

    def read_events(self) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for path in self._all_log_paths():
            for line in path.read_bytes().splitlines(keepends=True):
                if not line.endswith(b"\n"):
                    raise ObservabilityError("partial structured log record")
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ObservabilityError("invalid structured log JSON") from error
                self._validate_event(item)
                events.append(item)
        events.sort(key=lambda item: item["sequence"])
        previous: str | None = None
        for sequence, item in enumerate(events):
            if item["sequence"] != sequence or item["previous_event_hash"] != previous:
                raise ObservabilityError("structured log chain is invalid")
            if item["event_hash"] != self._event_hash(item):
                raise ObservabilityError("structured log hash mismatch")
            previous = item["event_hash"]
        return events

    def _validate_event(self, item: Any) -> None:
        fields = {
            "schema_version", "event_id", "sequence", "run_id", "occurred_at",
            "level", "event_type", "payload", "previous_event_hash", "event_hash",
        }
        if not isinstance(item, dict) or set(item) != fields:
            raise ObservabilityError("structured log fields are invalid")
        if item["schema_version"] != SCHEMA_VERSION or item["run_id"] != self.run_id:
            raise ObservabilityError("structured log identity is invalid")
        if type(item["sequence"]) is not int or item["sequence"] < 0:
            raise ObservabilityError("structured log sequence is invalid")
        if not _valid_timestamp(item["occurred_at"]):
            raise ObservabilityError("structured log timestamp is invalid")
        _safe_id(item["event_id"], "event_id")
        if item["level"] not in {"INFO", "WARNING", "ERROR"}:
            raise ObservabilityError("structured log level is invalid")
        if item["event_type"] not in _EVENT_TYPES:
            raise ObservabilityError("structured log event type is invalid")
        if not isinstance(item["payload"], dict):
            raise ObservabilityError("structured log payload is invalid")
        try:
            if redact_payload(item["payload"]) != item["payload"]:
                raise ObservabilityError("structured log payload is not allowlisted")
        except ObservabilityError:
            raise
        if item["previous_event_hash"] is not None and not re.fullmatch(r"[a-f0-9]{64}", item["previous_event_hash"]):
            raise ObservabilityError("structured log previous hash is invalid")
        if not re.fullmatch(r"[a-f0-9]{64}", item["event_hash"]):
            raise ObservabilityError("structured log hash is invalid")

    @staticmethod
    def _event_hash(item: Mapping[str, Any]) -> str:
        body = dict(item)
        body.pop("event_hash", None)
        return _hash(_canonical(body))

    def _rotate_locked(self, current: Path, sequence: int) -> None:
        if not current.exists():
            return
        rotated = self.log_dir / f"{self.run_id}.{sequence:08d}.jsonl"
        if rotated.exists() or rotated.is_symlink():
            raise ObservabilityError("rotated log target already exists")
        os.replace(current, rotated)
        self._fsync_dir(self.log_dir)

    def emit(
        self,
        event_type: str,
        payload: Mapping[str, Any],
        *,
        level: str = "INFO",
    ) -> dict[str, Any]:
        if self.read_only:
            raise ObservabilityError("read-only logger cannot emit events")
        if event_type not in _EVENT_TYPES:
            raise ObservabilityError("unsupported structured log event")
        if level not in {"INFO", "WARNING", "ERROR"}:
            raise ObservabilityError("invalid structured log level")
        safe_payload = redact_payload(payload)
        with self._lock():
            events = self.read_events()
            sequence = len(events)
            previous = events[-1]["event_hash"] if events else None
            event = {
                "schema_version": SCHEMA_VERSION,
                "event_id": f"{self.run_id}:log:{sequence:08d}",
                "sequence": sequence,
                "run_id": self.run_id,
                "occurred_at": _now() if self.clock is None else self.clock.now_utc(),
                "level": level,
                "event_type": event_type,
                "payload": safe_payload,
                "previous_event_hash": previous,
            }
            if previous is not None and _valid_timestamp(event["occurred_at"]):
                prior_time = next(item["occurred_at"] for item in reversed(events) if item["event_hash"] == previous)
                if datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00")) < datetime.fromisoformat(prior_time.replace("Z", "+00:00")):
                    event["occurred_at"] = prior_time
            event["event_hash"] = self._event_hash(event)
            encoded = _canonical(event) + b"\n"
            current = self.path
            if len(encoded) > self.max_bytes:
                raise ObservabilityError("structured log event exceeds max_bytes")
            if current.exists() and current.stat().st_size + len(encoded) > self.max_bytes:
                self._rotate_locked(current, sequence)
            prior = current.read_bytes() if current.exists() else b""
            self._atomic_bytes(current, prior + encoded)
            self._validate_event(event)
            return event

    def status(self) -> dict[str, Any]:
        events = self.read_events()
        files = []
        for path in sorted(self._all_log_paths(), key=lambda value: value.name):
            files.append({"path": str(path.relative_to(self.root)), "bytes": path.stat().st_size})
        return {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "event_count": len(events),
            "files": files,
            "last_event_hash": events[-1]["event_hash"] if events else None,
        }


__all__ = ["ObservabilityError", "SCHEMA_VERSION", "StructuredLogger", "redact_payload"]
