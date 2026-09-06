"""Local, fail-closed HTTP control plane for article-loop.

The module deliberately contains no model, Prime Agent, subprocess, proxy, or
arbitrary-file capability.  It projects durable state through public readers
and delegates the small set of canonical control operations to their existing
public APIs.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import copy
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import mimetypes
import os
from pathlib import Path
import re
import stat
import tempfile
import threading
import time
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import jsonschema
import yaml

from .budget import BudgetError, BudgetLedger
from .execution import ExecutionError, execution_readiness
from .finalization import FinalizationError, finalize_decision
from .inference import InferenceConfigError, ModelRegistry, inference_preflight
from .observability import ObservabilityError, StructuredLogger
from .orchestrator import OrchestrationError, Orchestrator
from .state_machine import State
from .store import DurableStore, IntegrityError, StoreError


API_PREFIX = "/api/v1"
MAX_BODY_BYTES = 65_536
MAX_PAGE_SIZE = 100
MAX_CURSOR_BYTES = 8_192
MAX_CONFIG_BYTES = 524_288
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
TERMINAL_STATES = frozenset({"FINALIZED", "TECHNICAL_FAILURE"})
ROLE_IDS = (
    "M00", "S10", "S20", "S30", "S40", "S50",
    "W11", "W12", "W13", "W21", "W22", "W23", "W31", "W32", "W33",
    "W41", "W42", "W43", "W51", "W52", "W53",
)
STATIC_ROOT = Path(__file__).with_name("control_center_static")
_CONFIG_APPLY_LOCK = threading.RLock()
_MUTATION_LOCK = threading.RLock()
CONFIG_PATHS = (
    "config/system.yaml",
    "config/budgets.yaml",
    "config/gates.yaml",
    "config/decision-policy.yaml",
    *(f"config/roles/{role}.yaml" for role in ROLE_IDS),
    "config/rubrics/evaluation.yaml",
)
# Do not redact operational counters such as ``total_tokens``.  Credentials
# are redacted by their precise credential-like field names instead.
SENSITIVE_KEY = re.compile(r"(?:api[_-]?key|access[_-]?token|refresh[_-]?token|session[_-]?token|cookie|password|secret|credential)", re.I)


class ControlCenterError(RuntimeError):
    """A public control-plane request was malformed, stale, or unsafe."""

    def __init__(self, code: str, message: str, *, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_id(value: Any, label: str = "identifier") -> str:
    if not isinstance(value, str) or SAFE_ID.fullmatch(value) is None:
        raise ControlCenterError("INVALID_IDENTIFIER", f"{label} is invalid")
    return value


def _safe_hash(value: Any, label: str = "hash", *, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise ControlCenterError("INVALID_HASH", f"{label} must be a SHA-256 hash")
    return value


def _redact(value: Any, *, key: str | None = None) -> Any:
    """Keep operational structure without returning credential-like values."""
    if key is not None and SENSITIVE_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {str(item): _redact(child, key=str(item)) for item, child in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str) and len(value) > 2_048:
        return value[:2_048] + "…[truncated]"
    return value


def _contained(root: Path, relative: str, *, exists: bool = False) -> Path:
    raw = Path(relative)
    if raw.is_absolute() or ".." in raw.parts or not relative:
        raise ControlCenterError("UNSAFE_PATH", "path is outside the local allowlist")
    current = root
    for part in raw.parts:
        current = current / part
        if current.is_symlink():
            raise ControlCenterError("UNSAFE_PATH", "symlinked path is not allowed")
    try:
        resolved = current.resolve(strict=exists)
    except OSError as error:
        raise ControlCenterError("UNSAFE_PATH", "path cannot be resolved") from error
    if resolved != root and root not in resolved.parents:
        raise ControlCenterError("UNSAFE_PATH", "path escapes the project root")
    return current


def _atomic_bytes(path: Path, data: bytes) -> None:
    if path.is_symlink():
        raise ControlCenterError("UNSAFE_PATH", "refusing to replace a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise ControlCenterError("UNSAFE_PATH", "unsafe parent directory")
    descriptor, temporary_name = tempfile.mkstemp(prefix=".tmp-control-center-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_json(path: Path, *, maximum: int = MAX_BODY_BYTES) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise ControlCenterError("UNSAFE_PATH", "stored control-plane record is unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ControlCenterError("INTEGRITY_ERROR", "stored control-plane record is invalid") from error
    if not isinstance(value, dict):
        raise ControlCenterError("INTEGRITY_ERROR", "stored control-plane record is not an object")
    return value


def _public_event(event: Mapping[str, Any], source: str) -> dict[str, Any]:
    """Project durable events without exposing article text or blind metadata."""
    allowed_payload = {
        "run_id", "cycle_id", "candidate_id", "decision_id", "receipt_id", "action",
        "reason", "reason_code", "pause_id", "resume_state", "role_id", "department_id",
        "state", "status", "alert_code", "limit_name", "threshold", "available",
    }
    payload = event.get("payload")
    public_payload = {}
    if isinstance(payload, Mapping):
        public_payload = {
            key: _redact(value, key=key)
            for key, value in payload.items()
            if key in allowed_payload and isinstance(value, (str, int, float, bool, type(None)))
        }
    return {
        "source": source,
        "sequence": event.get("sequence"),
        "occurred_at": event.get("occurred_at", event.get("at")),
        "event_type": event.get("event_type"),
        "state_from": event.get("state_from"),
        "state_to": event.get("state_to"),
        "event_hash": event.get("event_hash"),
        "payload": public_payload,
    }


class AuditLedger:
    """Independent, hash-chained operator audit ledger.

    The ledger records intent before a potentially mutating canonical operation.
    A crash between intent and completion remains an explicit, fail-closed
    ``PREPARED`` record rather than being reported as success.
    """

    schema_name = "control-center-audit.schema.json"

    def __init__(self, root: str | Path):
        raw_root = Path(root)
        if raw_root.is_symlink() or not raw_root.is_dir():
            raise ControlCenterError("UNSAFE_ROOT", "project root must be a regular directory")
        self.root = raw_root.resolve()
        self.directory = self.root / "state" / "control-center"
        self.path = self.directory / "audit.jsonl"
        self.lock_path = self.directory / "audit.lock"
        self.schema_path = self.root / "config" / "schemas" / self.schema_name
        self._thread_lock = threading.RLock()

    def _check_directory(self, *, create: bool) -> None:
        _contained(self.root, "state")
        if self.directory.exists():
            if self.directory.is_symlink() or not self.directory.is_dir():
                raise ControlCenterError("UNSAFE_PATH", "control-center directory is unsafe")
        elif create:
            self.directory.mkdir(parents=True, exist_ok=False)
            descriptor = os.open(self.directory.parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)

    def _schema(self) -> dict[str, Any]:
        return _read_json(self.schema_path, maximum=MAX_CONFIG_BYTES)

    @contextmanager
    def exclusive(self, name: str, thread_lock: threading.RLock) -> Iterable[None]:
        """Hold a dedicated local lock across a complete critical operation."""
        if name not in {"config.lock", "operations.lock"}:
            raise ControlCenterError("UNSAFE_PATH", "control-plane lock is not allowed")
        with thread_lock:
            self._check_directory(create=True)
            path = self.directory / name
            flags = os.O_RDWR | os.O_CREAT
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(path, flags, 0o600)
            try:
                if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                    raise ControlCenterError("UNSAFE_PATH", "control-plane lock is unsafe")
                with os.fdopen(descriptor, "a+", encoding="utf-8") as stream:
                    descriptor = -1
                    fcntl.flock(stream, fcntl.LOCK_EX)
                    try:
                        yield
                    finally:
                        fcntl.flock(stream, fcntl.LOCK_UN)
            finally:
                if descriptor >= 0:
                    os.close(descriptor)

    def read_events(self) -> list[dict[str, Any]]:
        self._check_directory(create=False)
        if not self.path.exists():
            return []
        if self.path.is_symlink() or not self.path.is_file():
            raise ControlCenterError("INTEGRITY_ERROR", "audit ledger is unsafe")
        validator = jsonschema.Draft202012Validator(self._schema())
        events: list[dict[str, Any]] = []
        for line in self.path.read_bytes().splitlines(keepends=True):
            if not line.endswith(b"\n"):
                raise ControlCenterError("INTEGRITY_ERROR", "audit ledger has a partial record")
            try:
                event = json.loads(line)
                validator.validate(event)
            except (json.JSONDecodeError, jsonschema.ValidationError) as error:
                raise ControlCenterError("INTEGRITY_ERROR", "audit ledger record is invalid") from error
            previous = events[-1]["event_hash"] if events else None
            body = dict(event)
            observed_hash = body.pop("event_hash", None)
            if event["sequence"] != len(events) or event["previous_event_hash"] != previous or observed_hash != _hash(body):
                raise ControlCenterError("INTEGRITY_ERROR", "audit ledger chain is invalid")
            events.append(event)
        return events

    def append(
        self,
        *,
        action: str,
        idempotency_key: str,
        request_hash: str,
        expected_hash: str | None,
        before_hash: str | None,
        after_hash: str | None,
        outcome: str,
        run_id: str | None = None,
        draft_id: str | None = None,
        response_hash: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(action, str) or not action or len(action) > 80:
            raise ControlCenterError("INVALID_ACTION", "action is invalid")
        if not isinstance(idempotency_key, str) or not idempotency_key or len(idempotency_key) > 256:
            raise ControlCenterError("INVALID_IDEMPOTENCY_KEY", "Idempotency-Key is invalid")
        for value, label in ((request_hash, "request_hash"), (expected_hash, "expected_hash"), (before_hash, "before_hash"), (after_hash, "after_hash"), (response_hash, "response_hash")):
            _safe_hash(value, label, allow_none=True)
        if run_id is not None:
            _safe_id(run_id, "run_id")
        if draft_id is not None:
            _safe_id(draft_id, "draft_id")
        with self._thread_lock:
            self._check_directory(create=True)
            with self.lock_path.open("a+", encoding="utf-8") as stream:
                fcntl.flock(stream, fcntl.LOCK_EX)
                try:
                    events = self.read_events()
                    event = {
                        "schema_version": "1.0.0",
                        "event_id": f"cc-{len(events):08d}",
                        "sequence": len(events),
                        "occurred_at": _now(),
                        "action": action,
                        "idempotency_key": idempotency_key,
                        "request_hash": request_hash,
                        "expected_hash": expected_hash,
                        "before_hash": before_hash,
                        "after_hash": after_hash,
                        "outcome": outcome,
                        "run_id": run_id,
                        "draft_id": draft_id,
                        "response_hash": response_hash,
                        "previous_event_hash": events[-1]["event_hash"] if events else None,
                    }
                    event["event_hash"] = _hash(event)
                    jsonschema.Draft202012Validator(self._schema()).validate(event)
                    prior = self.path.read_bytes() if self.path.exists() else b""
                    _atomic_bytes(self.path, prior + _canonical(event) + b"\n")
                    return event
                finally:
                    fcntl.flock(stream, fcntl.LOCK_UN)


class IdempotencyStore:
    """Persist sanitized control responses separately from scientific state."""

    def __init__(self, ledger: AuditLedger):
        self.ledger = ledger
        self.directory = ledger.directory / "idempotency"

    def _path(self, key: str) -> Path:
        digest = _hash_bytes(key.encode("utf-8"))
        return self.directory / f"{digest}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        self.ledger._check_directory(create=False)
        path = self._path(key)
        if not path.exists():
            return None
        return _read_json(path)

    def put(self, key: str, value: Mapping[str, Any]) -> None:
        self.ledger._check_directory(create=True)
        self.directory.mkdir(exist_ok=True)
        if self.directory.is_symlink() or not self.directory.is_dir():
            raise ControlCenterError("UNSAFE_PATH", "idempotency directory is unsafe")
        _atomic_bytes(self._path(key), _canonical(dict(value)))


class ConfigurationRepository:
    """Allowlisted typed drafts for the project's versioned YAML surfaces."""

    draft_schema_name = "control-center-draft.schema.json"

    def __init__(self, root: str | Path, ledger: AuditLedger):
        self.root = ledger.root
        self.ledger = ledger
        self.draft_directory = ledger.directory / "drafts"
        self.schema_path = self.root / "config" / "schemas" / self.draft_schema_name

    def _path(self, relative: str) -> Path:
        if relative not in CONFIG_PATHS:
            raise ControlCenterError("CONFIG_NOT_ALLOWED", "configuration path is not editable", status=403)
        return _contained(self.root, relative, exists=True)

    def _load(self, relative: str) -> tuple[dict[str, Any], str]:
        path = self._path(relative)
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_CONFIG_BYTES:
            raise ControlCenterError("UNSAFE_PATH", "configuration file is unsafe")
        raw = path.read_bytes()
        try:
            value = yaml.safe_load(raw.decode("utf-8"))
        except (UnicodeDecodeError, yaml.YAMLError) as error:
            raise ControlCenterError("CONFIG_INVALID", "configuration YAML is invalid") from error
        if not isinstance(value, dict):
            raise ControlCenterError("CONFIG_INVALID", "configuration must be an object")
        return value, _hash_bytes(raw)

    @staticmethod
    def _schema_for(value: Any, *, key: str | None = None) -> dict[str, Any]:
        if key is not None and SENSITIVE_KEY.search(key):
            return {"type": "string", "writeOnly": True}
        if isinstance(value, bool):
            return {"type": "boolean"}
        if isinstance(value, int):
            return {"type": "integer"}
        if isinstance(value, float):
            return {"type": "number"}
        if value is None:
            return {"type": ["string", "integer", "null"]}
        if isinstance(value, str):
            return {"type": "string", "maxLength": 2048}
        if isinstance(value, list):
            item = ConfigurationRepository._schema_for(value[0]) if value else {"type": "string"}
            return {"type": "array", "items": item}
        if isinstance(value, Mapping):
            additional: bool | dict[str, Any] = False
            if key == "departments":
                additional = {"type": "string", "enum": ["prime", "routed"]}
            elif key == "role_routes":
                additional = {
                    "type": "object",
                    "properties": {
                        "targets": {"type": "array", "items": {"type": "string"}},
                        "required_capabilities": {"type": "array", "items": {"type": "string"}},
                    },
                    "additionalProperties": False,
                }
            elif key == "targets":
                additional = {
                    "type": "object",
                    "properties": {
                        "target_id": {"type": "string"}, "provider": {"type": "string"}, "model": {"type": "string"},
                        "backend_type": {"type": "string", "enum": ["fake", "local_openai_compatible", "remote_openai_compatible"]},
                        "enabled": {"type": "boolean"}, "local": {"type": "boolean"}, "paid": {"type": "boolean"},
                        "tier": {"type": "string", "enum": ["low", "mid", "high", "high_assurance"]},
                        "capabilities": {"type": "array", "items": {"type": "string"}},
                        "context_limit": {"type": "integer"}, "max_output_tokens": {"type": "integer"},
                        "independence_group": {"type": "string"}, "endpoint": {"type": ["string", "null"]},
                        "api_key_env": {"type": "string", "writeOnly": True}, "timeout_seconds": {"type": "integer"},
                        "fallback_target": {"type": ["string", "null"]},
                        "pricing": {"type": ["object", "null"]},
                    },
                    "additionalProperties": False,
                }
            return {
                "type": "object",
                "properties": {str(name): ConfigurationRepository._schema_for(item, key=str(name)) for name, item in value.items()},
                "additionalProperties": additional,
            }
        return {"type": "string"}

    def list(self) -> list[dict[str, Any]]:
        result = []
        for relative in CONFIG_PATHS:
            value, digest = self._load(relative)
            category = (
                "roles" if relative.startswith("config/roles/") else
                "rubrics" if "/rubrics/" in relative else
                "budget_and_inference" if relative.endswith("budgets.yaml") else
                Path(relative).stem
            )
            result.append({
                "path": relative,
                "category": category,
                "origin": "versioned_project_configuration",
                "hash": digest,
                "value": _redact(value),
                "schema": self._schema_for(value),
                "impact": "future_runs_only",
                "editable": True,
            })
        return result

    def _same_shape(self, template: Any, candidate: Any, location: str, *, dynamic: bool = False) -> None:
        if isinstance(template, bool):
            if type(candidate) is not bool:
                raise ControlCenterError("CONFIG_INVALID", f"{location} must be boolean")
            return
        if isinstance(template, int) and not isinstance(template, bool):
            if type(candidate) is not int or candidate < 0:
                raise ControlCenterError("CONFIG_INVALID", f"{location} must be a non-negative integer")
            return
        if isinstance(template, float):
            if isinstance(candidate, bool) or not isinstance(candidate, (int, float)) or not math.isfinite(candidate) or candidate < 0:
                raise ControlCenterError("CONFIG_INVALID", f"{location} must be a finite non-negative number")
            return
        if template is None:
            if candidate is not None and not isinstance(candidate, (str, int)):
                raise ControlCenterError("CONFIG_INVALID", f"{location} has an unsupported null replacement")
            return
        if isinstance(template, str):
            if not isinstance(candidate, str) or not candidate.strip() or len(candidate) > 2048 or "\x00" in candidate:
                raise ControlCenterError("CONFIG_INVALID", f"{location} must be a bounded string")
            return
        if isinstance(template, list):
            if not isinstance(candidate, list) or len(candidate) > 512:
                raise ControlCenterError("CONFIG_INVALID", f"{location} must be a bounded array")
            if template:
                for index, item in enumerate(candidate):
                    self._same_shape(template[0], item, f"{location}[{index}]")
            return
        if isinstance(template, Mapping):
            if not isinstance(candidate, Mapping):
                raise ControlCenterError("CONFIG_INVALID", f"{location} must be an object")
            expected = set(template)
            actual = set(candidate)
            if dynamic:
                if any(not isinstance(key, str) or SAFE_ID.fullmatch(key) is None for key in actual):
                    raise ControlCenterError("CONFIG_INVALID", f"{location} has an unsafe map key")
            elif actual != expected:
                raise ControlCenterError("CONFIG_INVALID", f"{location} has unknown or missing fields")
            for key in sorted(actual):
                if key in template:
                    child_location = f"{location}.{key}"
                    self._same_shape(
                        template[key], candidate[key], child_location,
                        dynamic=child_location.endswith(("targets", "role_routes", "departments")),
                    )
            return
        raise ControlCenterError("CONFIG_INVALID", f"{location} uses an unsupported configuration type")

    @staticmethod
    def _require_equal(base: Mapping[str, Any], candidate: Mapping[str, Any], keys: Iterable[str], label: str) -> None:
        for key in keys:
            if candidate.get(key) != base.get(key):
                raise ControlCenterError("CONFIG_IMMUTABLE_FIELD", f"{label}.{key} is a canonical immutable field")

    def validate(self, relative: str, candidate: Mapping[str, Any]) -> list[str]:
        base, _ = self._load(relative)
        if not isinstance(candidate, Mapping):
            raise ControlCenterError("CONFIG_INVALID", "typed configuration value must be an object")
        self._same_shape(base, candidate, relative)
        result = copy.deepcopy(dict(candidate))
        if relative == "config/system.yaml":
            self._require_equal(base, result, ("schema_version", "project", "activation_modes", "states", "actions", "pipeline", "authority"), "system")
            input_section = result.get("input")
            if not isinstance(input_section, Mapping) or any(Path(str(value)).is_absolute() or ".." in Path(str(value)).parts for value in input_section.values() if isinstance(value, str)):
                raise ControlCenterError("CONFIG_INVALID", "system input paths must remain relative and contained")
        elif relative == "config/budgets.yaml":
            for key in ("model_execution", "execution", "privacy", "rlm", "local_execution", "authorization", "budget", "observability", "inference"):
                if key not in result:
                    raise ControlCenterError("CONFIG_INVALID", "budget configuration is incomplete")
            try:
                policy = execution_readiness_from_mapping(result)
                registry = ModelRegistry(result["inference"])
            except (ExecutionError, InferenceConfigError, KeyError) as error:
                raise ControlCenterError("CONFIG_INVALID", "execution or inference configuration is invalid") from error
            if policy["privacy_mode"] not in {"deny_remote", "scoped_remote", "full_remote"} or type(registry.status()["enabled"]) is not bool:
                raise ControlCenterError("CONFIG_INVALID", "inference configuration is invalid")
        elif relative == "config/gates.yaml":
            self._require_equal(base, result, ("schema_version", "required_before_jury"), "gates")
            for base_gate, new_gate in zip(base.get("gates", []), result.get("gates", [])):
                self._require_equal(base_gate, new_gate, ("id", "command", "deterministic"), "gates")
            for base_gate, new_gate in zip(base.get("m7_gates", []), result.get("m7_gates", [])):
                self._require_equal(base_gate, new_gate, ("id", "command", "verifier_version"), "m7_gates")
        elif relative == "config/decision-policy.yaml":
            self._require_equal(base, result, ("schema_version", "precedence", "classification_actions", "finalization_required_roles"), "decision-policy")
        elif relative.startswith("config/roles/"):
            self._require_equal(base, result, ("schema_version", "id", "kind", "department", "rlm_depth", "parent_id", "children_ids", "produces_proposals_only", "writes_champion"), "role")
            if result.get("id") != Path(relative).stem or not set(result.get("allowed_activation_modes", [])).issubset({"RUN", "CHECK", "SHIFT", "FREEZE"}):
                raise ControlCenterError("CONFIG_INVALID", "role identity or activation modes are invalid")
        elif relative == "config/rubrics/evaluation.yaml":
            self._require_equal(base, result, ("schema_version", "scale"), "rubric")
            for before, after in zip(base.get("dimensions", []), result.get("dimensions", [])):
                self._require_equal(before, after, ("id", "hard_gate", "compensable"), "rubric.dimension")
                if not isinstance(after.get("pass_threshold"), int) or not result["scale"]["minimum"] <= after["pass_threshold"] <= result["scale"]["maximum"]:
                    raise ControlCenterError("CONFIG_INVALID", "rubric threshold is outside the configured scale")
        return ["schema and cross-configuration validation passed"]

    def _draft_path(self, draft_id: str) -> Path:
        _safe_id(draft_id, "draft_id")
        if not draft_id.startswith("draft-"):
            raise ControlCenterError("INVALID_IDENTIFIER", "draft identifier is invalid")
        return self.draft_directory / f"{draft_id}.json"

    @staticmethod
    def _diff(before: Any, after: Any, location: str = "") -> list[dict[str, Any]]:
        """Return a bounded, redacted logical diff for confirmation screens."""
        if isinstance(before, Mapping) and isinstance(after, Mapping):
            result: list[dict[str, Any]] = []
            for key in sorted(set(before) | set(after)):
                result.extend(ConfigurationRepository._diff(before.get(key), after.get(key), f"{location}.{key}".strip(".")))
                if len(result) >= 512:
                    return result[:512]
            return result
        if isinstance(before, list) and isinstance(after, list):
            result = []
            for index in range(max(len(before), len(after))):
                left = before[index] if index < len(before) else None
                right = after[index] if index < len(after) else None
                result.extend(ConfigurationRepository._diff(left, right, f"{location}[{index}]"))
                if len(result) >= 512:
                    return result[:512]
            return result
        if before != after:
            key = location.rsplit(".", 1)[-1]
            return [{"path": location or "$", "before": _redact(before, key=key), "after": _redact(after, key=key)}]
        return []

    def _draft_schema(self) -> dict[str, Any]:
        return _read_json(self.schema_path, maximum=MAX_CONFIG_BYTES)

    def _write_draft(self, draft: Mapping[str, Any]) -> None:
        self.ledger._check_directory(create=True)
        self.draft_directory.mkdir(exist_ok=True)
        if self.draft_directory.is_symlink() or not self.draft_directory.is_dir():
            raise ControlCenterError("UNSAFE_PATH", "draft directory is unsafe")
        jsonschema.Draft202012Validator(self._draft_schema()).validate(dict(draft))
        _atomic_bytes(self._draft_path(str(draft["draft_id"])), _canonical(dict(draft)))

    def read_draft(self, draft_id: str) -> dict[str, Any]:
        self.ledger._check_directory(create=False)
        draft = _read_json(self._draft_path(draft_id), maximum=MAX_CONFIG_BYTES)
        try:
            jsonschema.Draft202012Validator(self._draft_schema()).validate(draft)
        except jsonschema.ValidationError as error:
            raise ControlCenterError("INTEGRITY_ERROR", "configuration draft is invalid") from error
        return draft

    def create_draft(self, request: Mapping[str, Any]) -> dict[str, Any]:
        required = {"config_path", "base_hash", "value"}
        if set(request) != required:
            raise ControlCenterError("INVALID_REQUEST", "draft request has unsupported fields")
        relative = request["config_path"]
        if not isinstance(relative, str):
            raise ControlCenterError("CONFIG_INVALID", "config_path must be a string")
        base, current_hash = self._load(relative)
        if request["base_hash"] != current_hash:
            raise ControlCenterError("STALE_VERSION", "configuration hash is stale", status=409)
        messages = self.validate(relative, request["value"])
        draft = {
            "schema_version": "1.0.0",
            "draft_id": "draft-" + uuid4().hex,
            "created_at": _now(),
            "config_path": relative,
            "base_hash": current_hash,
            "candidate_hash": _hash(request["value"]),
            "status": "DRAFT",
            "validation": {"valid": True, "messages": messages},
            "diff": self._diff(base, request["value"]),
            "value": dict(request["value"]),
        }
        self._write_draft(draft)
        return self.public_draft(draft)

    def validate_draft(self, draft_id: str) -> dict[str, Any]:
        draft = self.read_draft(draft_id)
        if draft["status"] == "APPLIED":
            raise ControlCenterError("DRAFT_TERMINAL", "applied draft cannot be revalidated", status=409)
        messages = self.validate(draft["config_path"], draft["value"])
        draft["status"] = "VALIDATED"
        draft["validation"] = {"valid": True, "messages": messages}
        self._write_draft(draft)
        return self.public_draft(draft)

    def apply_draft(self, draft_id: str) -> dict[str, Any]:
        with self.ledger.exclusive("config.lock", _CONFIG_APPLY_LOCK):
            draft = self.read_draft(draft_id)
            if draft["status"] == "APPLIED":
                return self.public_draft(draft)
            if draft["status"] != "VALIDATED":
                raise ControlCenterError("DRAFT_NOT_VALIDATED", "draft must be validated before application", status=409)
            if active_runs(self.root):
                raise ControlCenterError("ACTIVE_RUN_CONFIG_LOCK", "configuration is immutable while a run is active", status=409)
            _, current_hash = self._load(draft["config_path"])
            if current_hash != draft["base_hash"]:
                raise ControlCenterError("STALE_VERSION", "configuration changed after the draft was created", status=409)
            self.validate(draft["config_path"], draft["value"])
            target = self._path(draft["config_path"])
            rendered = yaml.safe_dump(dict(draft["value"]), allow_unicode=True, sort_keys=False).encode("utf-8")
            _atomic_bytes(target, rendered)
            draft["status"] = "APPLIED"
            draft["applied_hash"] = _hash_bytes(rendered)
            self._write_draft(draft)
            return self.public_draft(draft)

    @staticmethod
    def public_draft(draft: Mapping[str, Any]) -> dict[str, Any]:
        return _redact(dict(draft))


def execution_readiness_from_mapping(config: Mapping[str, Any]) -> dict[str, Any]:
    """Validate M12.5 configuration without reading secrets or calling a backend."""
    from .execution import ExecutionPolicy

    policy = ExecutionPolicy.from_mapping(config)
    registry = ModelRegistry(config["inference"])
    return {
        "privacy_mode": policy.remote_content_mode,
        "execution_enabled": policy.enabled,
        "registry_enabled": registry.status()["enabled"],
    }


def _runtime_run_ids(root: Path) -> list[str]:
    runs: set[str] = set()
    for relative, suffix in (("state/events", ".jsonl"), ("state/orchestration", None)):
        directory = _contained(root, relative)
        if not directory.exists():
            continue
        if directory.is_symlink() or not directory.is_dir():
            raise ControlCenterError("UNSAFE_PATH", "runtime directory is unsafe")
        for path in directory.iterdir():
            if path.is_symlink():
                raise ControlCenterError("UNSAFE_PATH", "runtime directory contains a symlink")
            name = path.stem if suffix else path.name
            if suffix and (not path.is_file() or path.suffix != suffix):
                continue
            if suffix is None and not path.is_dir():
                continue
            if SAFE_ID.fullmatch(name):
                runs.add(name)
    return sorted(runs)


def _m6_status(root: Path, run_id: str) -> dict[str, Any] | None:
    directory = _contained(root, f"state/orchestration/{run_id}")
    if not directory.exists():
        return None
    if directory.is_symlink() or not directory.is_dir():
        raise ControlCenterError("UNSAFE_PATH", "orchestration directory is unsafe")
    try:
        # ``status`` was deliberately made a non-creating public projection.
        return asyncio.run(Orchestrator(root).status(run_id))
    except (OrchestrationError, RuntimeError) as error:
        raise ControlCenterError("INTEGRITY_ERROR", "orchestration status is invalid") from error


def run_detail(root: Path, run_id: str, *, include_timeline: bool = False) -> dict[str, Any]:
    run_id = _safe_id(run_id, "run_id")
    if run_id not in _runtime_run_ids(root):
        raise ControlCenterError("RUN_NOT_FOUND", "run does not exist", status=404)
    event_path = _contained(root, f"state/events/{run_id}.jsonl")
    events: list[dict[str, Any]] = []
    snapshot: dict[str, Any] | None = None
    if event_path.exists():
        try:
            store = DurableStore(root, read_only=True)
            events = store.read_events(run_id)
            snapshot = store.snapshot(run_id)
        except (StoreError, IntegrityError) as error:
            raise ControlCenterError("INTEGRITY_ERROR", "canonical run state is invalid") from error
    orchestration = _m6_status(root, run_id)
    state = (snapshot or {}).get("state") or (orchestration or {}).get("state") or "UNKNOWN"
    cycle_id = (orchestration or {}).get("cycle_id", (snapshot or {}).get("cycle_id"))
    # M2 rebuilds a display snapshot with a fresh ``created_at`` timestamp.
    # Its snapshot hash is therefore not an optimistic-concurrency version.
    # The final validated event hash is stable and changes on every transition.
    version_hash = (orchestration or {}).get("snapshot_hash") or (events[-1]["event_hash"] if events else None)
    if not isinstance(version_hash, str) or SHA256.fullmatch(version_hash) is None:
        version_hash = _hash({"run_id": run_id, "events": [event.get("event_hash") for event in events], "orchestration": orchestration})
    detail: dict[str, Any] = {
        "run_id": run_id,
        "state": state,
        "cycle_id": cycle_id,
        "version_hash": version_hash,
        "active": state not in TERMINAL_STATES,
        "last_event_hash": events[-1]["event_hash"] if events else None,
        "snapshot": _redact(snapshot) if snapshot is not None else None,
        "orchestration": _redact(orchestration) if orchestration is not None else None,
        "artifacts": sorted({artifact for event in events for artifact in event.get("artifact_hashes", []) if isinstance(artifact, str)}),
    }
    if include_timeline:
        detail["timeline"] = [_public_event(event, f"run:{run_id}") for event in events]
    return detail


def approved_artifacts(root: Path, run_id: str) -> dict[str, Any]:
    """Return links only for hashes already committed in the canonical journal.

    Artifact bytes are deliberately not served: their locations and visibility
    rules belong to the canonical stage readers.  These fixed metadata routes
    give the operator a stable, non-path-bearing reference without adding a
    generic file reader to the local HTTP surface.
    """
    detail = run_detail(root, run_id)
    return {
        "run_id": run_id,
        "artifacts": [{
            "sha256": digest,
            "approved": True,
            "href": f"{API_PREFIX}/runs/{run_id}/artifacts/{digest}",
        } for digest in detail["artifacts"]],
    }


def approved_artifact_metadata(root: Path, run_id: str, digest: str) -> dict[str, Any]:
    """Resolve one journal-approved digest without accepting a filesystem path."""
    digest = _safe_hash(digest, "artifact_hash")
    approved = approved_artifacts(root, run_id)["artifacts"]
    if not any(item["sha256"] == digest for item in approved):
        raise ControlCenterError("ARTIFACT_NOT_FOUND", "artifact is not approved for this run", status=404)
    return {"run_id": run_id, "sha256": digest, "approved": True, "content_available": False}


def _canonical_artifact(root: Path, locator: str, schema_name: str) -> dict[str, Any]:
    """Read one declared JSON artifact under containment and schema checks."""
    if not isinstance(locator, str) or not locator.endswith(".json"):
        raise ControlCenterError("INTEGRITY_ERROR", "artifact locator is invalid")
    path = _contained(root, locator, exists=True)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_CONFIG_BYTES:
        raise ControlCenterError("INTEGRITY_ERROR", "artifact is unsafe")
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
        schema = _read_json(_contained(root, f"config/schemas/{schema_name}", exists=True), maximum=MAX_CONFIG_BYTES)
        jsonschema.Draft202012Validator(schema).validate(value)
    except (UnicodeDecodeError, json.JSONDecodeError, jsonschema.ValidationError) as error:
        raise ControlCenterError("INTEGRITY_ERROR", "artifact schema is invalid") from error
    if not isinstance(value, dict) or raw != _canonical(value):
        raise ControlCenterError("INTEGRITY_ERROR", "artifact bytes are not canonical")
    return value


def _evidence_projection(root: Path, run_id: str) -> dict[str, Any]:
    """Project stage evidence while preserving the blind-jury boundary."""
    run_detail(root, run_id)
    events = DurableStore(root, read_only=True).read_events(run_id)
    result: dict[str, Any] = {
        "gates": [], "jury": {"status": "not_started"}, "diagnosis": None,
        "decision": None, "finalization": None,
    }
    for event in events:
        payload = event.get("payload") if isinstance(event.get("payload"), Mapping) else {}
        target = event.get("state_to")
        if target == State.GATES_PASSED.value and isinstance(payload.get("report_locator"), str):
            report = _canonical_artifact(root, payload["report_locator"], "gate-report.schema.json")
            result["gates"] = [{
                "gate_id": gate["gate_id"], "command": gate["command"], "verifier_version": gate["verifier_version"],
                "timeout_seconds": gate["timeout_seconds"], "input_hash": gate["input_hash"],
                "duration_ms": gate["duration_ms"], "exit_code": gate["exit_code"], "passed": gate["passed"],
                "classification": gate["classification"], "output": str(gate["output"])[:4096],
                "evidence_locators": list(gate.get("evidence_locators", []))[:32],
            } for gate in report.get("gates", [])]
        elif target == State.EVALUATED.value:
            locator = payload.get("evaluation_locator")
            if isinstance(locator, str):
                report = _canonical_artifact(root, locator, "evaluation-report.schema.json")
                # Do not return verdict documents, presentation order, neutral
                # candidate IDs, author information, or champion condition.
                result["jury"] = {
                    "status": "completed", "comparison_id": report.get("comparison_id"),
                    "overall_outcome": report.get("overall_outcome"),
                    "challenger_eligible": report.get("challenger_eligible"),
                    "correctness_math_pass": report.get("correctness_math_pass"),
                }
        elif target == State.DIAGNOSED.value:
            locator = payload.get("diagnosis_locator")
            if isinstance(locator, str):
                diagnosis = _canonical_artifact(root, locator, "diagnosis.schema.json")
                result["diagnosis"] = _redact({
                    key: diagnosis.get(key) for key in ("diagnosis_id", "classification", "recommended_mode", "reason_code", "signals", "next_focus", "evidence_locators")
                })
        elif target == State.DECIDED.value:
            locator = payload.get("decision_locator")
            if isinstance(locator, str):
                decision = _canonical_artifact(root, locator, "decision.schema.json")
                result["decision"] = _redact({
                    key: decision.get(key) for key in ("decision_id", "action", "reason_code", "pareto_relation", "basis_locators", "final_gate_report_ids")
                })
        elif event.get("event_type") == "FINALIZATION_APPLIED":
            cycle = event.get("cycle_id")
            if isinstance(cycle, int):
                locator = f"state/decisions/{run_id}/c{cycle:04d}/finalization-receipt.json"
                path = _contained(root, locator)
                if path.exists():
                    receipt = _canonical_artifact(root, locator, "finalization-receipt.schema.json")
                    result["finalization"] = _redact({
                        key: receipt.get(key) for key in ("receipt_id", "action", "applied_at", "state_before", "state_after", "content_hash_before", "content_hash_after", "destination")
                    })
    return result


def active_runs(root: Path) -> list[str]:
    active = []
    for run_id in _runtime_run_ids(root):
        if run_detail(root, run_id)["active"]:
            active.append(run_id)
    return active


class ControlPlane:
    """Typed application service behind the loopback HTTP handler."""

    def __init__(self, root: str | Path):
        raw_root = Path(root)
        if raw_root.is_symlink() or not raw_root.is_dir():
            raise ControlCenterError("UNSAFE_ROOT", "project root must be a regular directory")
        self.root = raw_root.resolve()
        self.audit = AuditLedger(self.root)
        self.idempotency = IdempotencyStore(self.audit)
        self.config = ConfigurationRepository(self.root, self.audit)

    def health(self) -> dict[str, Any]:
        directories = ("state", "config", "config/schemas", "logs")
        checked = []
        for relative in directories:
            path = _contained(self.root, relative)
            checked.append({"path": relative, "present": path.exists(), "safe": path.exists() and path.is_dir() and not path.is_symlink()})
        return {"api_version": "v1", "local_only": True, "status": "ok", "storage": checked}

    def runs(self, *, cursor: str | None = None, limit: int = 25) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= MAX_PAGE_SIZE:
            raise ControlCenterError("INVALID_PAGE", "limit is outside the allowed range")
        ids = _runtime_run_ids(self.root)
        offset = 0
        if cursor is not None:
            if not isinstance(cursor, str) or not cursor.isdigit():
                raise ControlCenterError("INVALID_PAGE", "run cursor is invalid")
            offset = int(cursor)
        selected = ids[offset:offset + limit]
        return {
            "runs": [run_detail(self.root, run_id) for run_id in selected],
            "next_cursor": str(offset + limit) if offset + limit < len(ids) else None,
            "total": len(ids),
        }

    def topology(self, run_id: str | None = None) -> dict[str, Any]:
        roles: dict[str, Any] = {}
        for role in ROLE_IDS:
            value, _ = self.config._load(f"config/roles/{role}.yaml")
            roles[role] = {
                "role_id": role,
                "parent_id": value["parent_id"],
                "department": value["department"],
                "kind": value["kind"],
                "state": "inactive",
                "activation_mode": None,
                "receipt": None,
                "error": None,
            }
        if run_id is not None:
            detail = run_detail(self.root, run_id)
            orchestration = detail.get("orchestration") or {}
            activation = orchestration.get("activation", {})
            children = orchestration.get("children", {})
            for role, item in roles.items():
                if role in activation:
                    item["activation_mode"] = activation[role]
                    item["state"] = "planned" if activation[role] != "FREEZE" else "inactive"
                child = children.get(role)
                if isinstance(child, Mapping):
                    status = str(child.get("status", ""))
                    item["state"] = {
                        "ADMITTED": "admitted", "RECEIVED": "completed", "FAILED": "failed", "CANCELLED": "cancelled",
                    }.get(status, status.lower() or item["state"])
                    # Receipt identity is retained as evidence, but no candidate
                    # authorship or jury presentation metadata is exposed here.
                    item["receipt"] = child.get("task_hash") if isinstance(child.get("task_hash"), str) else None
        return {"root": "M00", "roles": [roles[role] for role in ROLE_IDS]}

    def evidence(self, run_id: str) -> dict[str, Any]:
        return _evidence_projection(self.root, run_id)

    def artifacts(self, run_id: str) -> dict[str, Any]:
        return approved_artifacts(self.root, run_id)

    def artifact_metadata(self, run_id: str, digest: str) -> dict[str, Any]:
        return approved_artifact_metadata(self.root, run_id, digest)

    def budget(self, run_id: str | None = None) -> dict[str, Any]:
        selected = [run_id] if run_id is not None else _runtime_run_ids(self.root)
        budgets = []
        for current in selected:
            _safe_id(current, "run_id")
            ledger_path = _contained(self.root, f"state/budgets/{current}.jsonl")
            if not ledger_path.exists():
                continue
            try:
                ledger = BudgetLedger.from_project(self.root, current, read_only=True)
                budgets.append(_redact(ledger.status(read_only=True)))
            except (BudgetError, ObservabilityError) as error:
                budgets.append({"run_id": current, "status": "integrity_error", "error": "budget evidence cannot be projected"})
        return {"unit_policy": "integers_or_microunits_only", "budgets": budgets}

    def system_status(self) -> dict[str, Any]:
        try:
            readiness = execution_readiness(self.root)
        except (ExecutionError, InferenceConfigError, BudgetError) as error:
            readiness = {"implementation_ready": False, "live_ready": False, "error": "configuration is invalid"}
        try:
            routing = inference_preflight(self.root)
        except (InferenceConfigError, BudgetError):
            routing = {"enabled": False, "error": "inference configuration is invalid"}
        try:
            preflight = asyncio.run(Orchestrator(self.root).preflight())
        except (OrchestrationError, RuntimeError):
            preflight = {"configured": False, "reason": "preflight unavailable"}
        configurations = self.config.list()
        return {
            "health": self.health(),
            "runs": self.runs(limit=MAX_PAGE_SIZE),
            "active_runs": active_runs(self.root),
            "execution": _redact(readiness),
            "inference": _redact(routing),
            "preflight": _redact(preflight),
            "configuration_hash": _hash({item["path"]: item["hash"] for item in configurations}),
            "configuration": [{key: item[key] for key in ("path", "hash", "category", "impact")} for item in configurations],
        }

    def errors(self, *, cursor: str | None = None, limit: int = 50) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= MAX_PAGE_SIZE:
            raise ControlCenterError("INVALID_PAGE", "limit is outside the allowed range")
        records = [
            _public_event(event, "audit")
            for event in self.audit.read_events()
            if event.get("outcome") == "REJECTED"
        ]
        for run_id in _runtime_run_ids(self.root):
            log = _contained(self.root, f"logs/{run_id}.jsonl")
            if not log.exists():
                continue
            try:
                entries = StructuredLogger(self.root, run_id, read_only=True).read_events()
            except ObservabilityError:
                records.append({"source": f"log:{run_id}", "event_type": "INTEGRITY_ERROR", "payload": {}})
                continue
            records.extend(
                _public_event(entry, f"log:{run_id}")
                for entry in entries if entry.get("level") in {"WARNING", "ERROR"}
            )
        offset = int(cursor) if isinstance(cursor, str) and cursor.isdigit() else 0
        if cursor is not None and offset < 0:
            raise ControlCenterError("INVALID_PAGE", "error cursor is invalid")
        return {"errors": records[offset:offset + limit], "next_cursor": str(offset + limit) if offset + limit < len(records) else None}

    @staticmethod
    def _decode_cursor(value: str | None) -> dict[str, int]:
        if not value:
            return {}
        if not isinstance(value, str) or len(value.encode("utf-8")) > MAX_CURSOR_BYTES or not value.startswith("v1."):
            raise ControlCenterError("INVALID_CURSOR", "event cursor is invalid")
        try:
            padded = value[3:] + "=" * (-len(value[3:]) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ControlCenterError("INVALID_CURSOR", "event cursor is invalid") from error
        if not isinstance(decoded, dict) or len(decoded) > 256:
            raise ControlCenterError("INVALID_CURSOR", "event cursor is invalid")
        result: dict[str, int] = {}
        for source, sequence in decoded.items():
            if not isinstance(source, str) or not isinstance(sequence, int) or sequence < -1:
                raise ControlCenterError("INVALID_CURSOR", "event cursor is invalid")
            result[source] = sequence
        return result

    @staticmethod
    def _encode_cursor(value: Mapping[str, int]) -> str:
        token = base64.urlsafe_b64encode(_canonical(dict(sorted(value.items())))).decode("ascii").rstrip("=")
        return "v1." + token

    def _event_sources(self) -> dict[str, list[dict[str, Any]]]:
        sources: dict[str, list[dict[str, Any]]] = {"audit": self.audit.read_events()}
        for run_id in _runtime_run_ids(self.root):
            path = _contained(self.root, f"state/events/{run_id}.jsonl")
            if path.exists():
                try:
                    sources[f"run:{run_id}"] = DurableStore(self.root, read_only=True).read_events(run_id)
                except StoreError as error:
                    raise ControlCenterError("INTEGRITY_ERROR", "durable event log cannot be streamed") from error
        return sources

    def events(self, *, cursor: str | None = None, limit: int = 100) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= MAX_PAGE_SIZE:
            raise ControlCenterError("INVALID_PAGE", "event limit is outside the allowed range")
        seen = self._decode_cursor(cursor)
        next_seen = dict(seen)
        public: list[dict[str, Any]] = []
        for source, source_events in sorted(self._event_sources().items()):
            floor = seen.get(source, -1)
            for event in source_events:
                sequence = event.get("sequence")
                if not isinstance(sequence, int) or sequence <= floor:
                    continue
                if len(public) >= limit:
                    return {"events": public, "next_cursor": self._encode_cursor(next_seen), "has_more": True}
                item = _public_event(event, source)
                item["cursor"] = f"{source}:{sequence}:{str(event.get('event_hash', ''))[:16]}"
                public.append(item)
                next_seen[source] = sequence
        return {"events": public, "next_cursor": self._encode_cursor(next_seen), "has_more": False}

    def _mutate(
        self,
        *,
        action: str,
        idempotency_key: str,
        request: Mapping[str, Any],
        expected_hash: str | None,
        before_hash: str | None,
        run_id: str | None,
        draft_id: str | None,
        operation: Callable[[], Mapping[str, Any]],
    ) -> dict[str, Any]:
        if not isinstance(idempotency_key, str) or not idempotency_key or len(idempotency_key) > 256:
            raise ControlCenterError("INVALID_IDEMPOTENCY_KEY", "Idempotency-Key header is required")
        request_hash = _hash(request)
        with self.audit.exclusive("operations.lock", _MUTATION_LOCK):
            existing = self.idempotency.get(idempotency_key)
            if existing is not None:
                if existing.get("action") != action or existing.get("request_hash") != request_hash:
                    raise ControlCenterError("IDEMPOTENCY_CONFLICT", "Idempotency-Key was used for another request", status=409)
                response = existing.get("response")
                if not isinstance(response, Mapping) or existing.get("response_hash") != _hash(response):
                    raise ControlCenterError("INTEGRITY_ERROR", "stored idempotent result is invalid")
                return dict(response)
            self.audit.append(
                action=action, idempotency_key=idempotency_key, request_hash=request_hash,
                expected_hash=expected_hash, before_hash=before_hash, after_hash=None,
                outcome="PREPARED", run_id=run_id, draft_id=draft_id,
            )
            try:
                outcome = _redact(dict(operation()))
            except ControlCenterError as error:
                self.audit.append(
                    action=action, idempotency_key=idempotency_key, request_hash=request_hash,
                    expected_hash=expected_hash, before_hash=before_hash, after_hash=None,
                    outcome="REJECTED", run_id=run_id, draft_id=draft_id,
                )
                raise error
            except Exception as error:
                self.audit.append(
                    action=action, idempotency_key=idempotency_key, request_hash=request_hash,
                    expected_hash=expected_hash, before_hash=before_hash, after_hash=None,
                    outcome="REJECTED", run_id=run_id, draft_id=draft_id,
                )
                raise ControlCenterError("CANONICAL_OPERATION_FAILED", "canonical operation failed closed", status=409) from error
            response = {"ok": True, "action": action, "result": outcome}
            response_hash = _hash(response)
            after_hash = outcome.get("snapshot_hash") or outcome.get("version_hash") or outcome.get("applied_hash") or before_hash
            if not isinstance(after_hash, str) or SHA256.fullmatch(after_hash) is None:
                after_hash = before_hash
            self.idempotency.put(idempotency_key, {"action": action, "request_hash": request_hash, "response": response, "response_hash": response_hash})
            self.audit.append(
                action=action, idempotency_key=idempotency_key, request_hash=request_hash,
                expected_hash=expected_hash, before_hash=before_hash, after_hash=after_hash,
                outcome="APPLIED", run_id=run_id, draft_id=draft_id, response_hash=response_hash,
            )
            return response

    @staticmethod
    def _confirmed(body: Mapping[str, Any]) -> None:
        if body.get("confirmed") is not True:
            raise ControlCenterError("CONFIRMATION_REQUIRED", "explicit confirmed=true is required", status=409)

    def run_action(self, run_id: str, action: str, body: Mapping[str, Any], idempotency_key: str) -> dict[str, Any]:
        if set(body) != {"confirmed", "expected_hash"}:
            raise ControlCenterError("INVALID_REQUEST", "run action accepts only confirmed and expected_hash")
        self._confirmed(body)
        detail = run_detail(self.root, run_id)
        expected_hash = _safe_hash(body.get("expected_hash"), "expected_hash")
        if expected_hash != detail["version_hash"]:
            raise ControlCenterError("STALE_VERSION", "run state changed; refresh before controlling it", status=409)
        if action in {"checkpoint", "pause", "resume", "stop"} and detail.get("orchestration") is None:
            raise ControlCenterError("M6_NOT_BOOTSTRAPPED", "run is not bootstrapped for this canonical M6 control", status=409)
        operations: dict[str, Callable[[], Mapping[str, Any]]] = {
            "checkpoint": lambda: asyncio.run(Orchestrator(self.root).checkpoint(run_id, expected_snapshot_hash=expected_hash)),
            "pause": lambda: asyncio.run(Orchestrator(self.root).pause(run_id, expected_snapshot_hash=expected_hash)),
            "resume": lambda: asyncio.run(Orchestrator(self.root).resume(run_id, expected_snapshot_hash=expected_hash)),
            "stop": lambda: asyncio.run(Orchestrator(self.root).stop(run_id, expected_snapshot_hash=expected_hash)),
            "finalize": lambda: finalize_decision(self.root, run_id, cycle_id=detail.get("cycle_id")),
        }
        if action not in operations:
            raise ControlCenterError("INVALID_ACTION", "unsupported canonical action", status=404)
        return self._mutate(
            action=f"run_{action}", idempotency_key=idempotency_key, request=body,
            expected_hash=expected_hash, before_hash=detail["version_hash"], run_id=run_id,
            draft_id=None, operation=operations[action],
        )

    def preflight_action(self, body: Mapping[str, Any], idempotency_key: str) -> dict[str, Any]:
        if set(body) != {"confirmed", "expected_hash"}:
            raise ControlCenterError("INVALID_REQUEST", "preflight accepts only confirmed and expected_hash")
        self._confirmed(body)
        system = self.system_status()
        expected_hash = _safe_hash(body.get("expected_hash"), "expected_hash")
        if expected_hash != system["configuration_hash"]:
            raise ControlCenterError("STALE_VERSION", "configuration changed; refresh before preflight", status=409)
        return self._mutate(
            action="preflight", idempotency_key=idempotency_key, request=body,
            expected_hash=expected_hash, before_hash=expected_hash, run_id=None, draft_id=None,
            operation=lambda: asyncio.run(Orchestrator(self.root).preflight()),
        )

    def config_action(self, action: str, draft_id: str | None, body: Mapping[str, Any], idempotency_key: str) -> dict[str, Any]:
        self._confirmed(body)
        if action == "create":
            if set(body) != {"confirmed", "config_path", "base_hash", "value"}:
                raise ControlCenterError("INVALID_REQUEST", "draft creation fields are invalid")
            request = {key: body[key] for key in ("config_path", "base_hash", "value")}
            base_hash = _safe_hash(body["base_hash"], "base_hash")
            return self._mutate(
                action="config_draft_create", idempotency_key=idempotency_key, request=request,
                expected_hash=base_hash, before_hash=base_hash, run_id=None, draft_id=None,
                operation=lambda: self.config.create_draft(request),
            )
        if draft_id is None:
            raise ControlCenterError("INVALID_IDENTIFIER", "draft_id is required")
        if set(body) != {"confirmed", "expected_hash"}:
            raise ControlCenterError("INVALID_REQUEST", "draft action accepts only confirmed and expected_hash")
        draft = self.config.read_draft(draft_id)
        expected_hash = _safe_hash(body["expected_hash"], "expected_hash")
        if expected_hash != draft["candidate_hash"]:
            raise ControlCenterError("STALE_VERSION", "draft version is stale", status=409)
        operation = self.config.validate_draft if action == "validate" else self.config.apply_draft if action == "apply" else None
        if operation is None:
            raise ControlCenterError("INVALID_ACTION", "unsupported draft action", status=404)
        return self._mutate(
            action=f"config_draft_{action}", idempotency_key=idempotency_key, request=body,
            expected_hash=expected_hash, before_hash=draft["base_hash"], run_id=None, draft_id=draft_id,
            operation=lambda: operation(draft_id),
        )


class _LocalHandler(BaseHTTPRequestHandler):
    server: "LocalControlHTTPServer"
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        # Request paths and headers can contain user-controlled sensitive data.
        return

    def _expected_origins(self) -> set[str]:
        _, port = self.server.server_address[:2]
        return {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}

    def _verify_host(self) -> None:
        host = self.headers.get("Host", "")
        expected = {origin.removeprefix("http://") for origin in self._expected_origins()}
        if host not in expected:
            raise ControlCenterError("INVALID_HOST", "request Host must be loopback", status=403)
        origin = self.headers.get("Origin")
        if origin is not None and origin not in self._expected_origins():
            raise ControlCenterError("INVALID_ORIGIN", "request Origin must be loopback", status=403)

    def _verify_mutation(self) -> str:
        self._verify_host()
        if self.headers.get("Origin") not in self._expected_origins():
            raise ControlCenterError("CSRF_REJECTED", "same-origin Origin is required", status=403)
        fetch_site = self.headers.get("Sec-Fetch-Site")
        if fetch_site not in {None, "same-origin", "same-site"}:
            raise ControlCenterError("CSRF_REJECTED", "cross-site mutation is rejected", status=403)
        key = self.headers.get("Idempotency-Key")
        if not key:
            raise ControlCenterError("INVALID_IDEMPOTENCY_KEY", "Idempotency-Key header is required", status=400)
        return key

    def _body(self) -> dict[str, Any]:
        value = self.headers.get("Content-Length")
        try:
            length = int(value or "0")
        except ValueError as error:
            raise ControlCenterError("INVALID_REQUEST", "Content-Length is invalid") from error
        if length < 1 or length > MAX_BODY_BYTES:
            raise ControlCenterError("INVALID_REQUEST", "request body size is invalid")
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ControlCenterError("INVALID_REQUEST", "request body must be JSON") from error
        if not isinstance(body, dict):
            raise ControlCenterError("INVALID_REQUEST", "request body must be an object")
        return body

    def _headers(self, content_type: str) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")

    def _json(self, value: Mapping[str, Any], status: int = 200) -> None:
        payload = _canonical(dict(value))
        self.send_response(status)
        self._headers("application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _error(self, error: ControlCenterError) -> None:
        self._json({"ok": False, "error": {"code": error.code, "message": str(error)}}, error.status)

    def _static(self, path: str) -> None:
        name = {"/": "index.html", "/assets/app.js": "app.js", "/assets/styles.css": "styles.css"}.get(path)
        if name is None:
            raise ControlCenterError("NOT_FOUND", "resource was not found", status=404)
        target = STATIC_ROOT / name
        if target.is_symlink() or not target.is_file():
            raise ControlCenterError("NOT_FOUND", "local interface asset is unavailable", status=404)
        payload = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        self._headers(f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    @staticmethod
    def _query(query: str, name: str) -> str | None:
        values = parse_qs(query, strict_parsing=False).get(name, [])
        if len(values) > 1:
            raise ControlCenterError("INVALID_REQUEST", "query parameter is repeated")
        return values[0] if values else None

    def _sse(self, cursor: str | None) -> None:
        self.send_response(200)
        self._headers("text/event-stream; charset=utf-8")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        current = cursor
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            batch = self.server.plane.events(cursor=current, limit=MAX_PAGE_SIZE)
            for event in batch["events"]:
                positions = self.server.plane._decode_cursor(current)
                positions[str(event["source"])] = int(event["sequence"])
                current = self.server.plane._encode_cursor(positions)
                data = _canonical(event).decode("utf-8")
                self.wfile.write(f"id: {current}\nevent: durable\ndata: {data}\n\n".encode("utf-8"))
            self.wfile.write(b": keepalive\n\n")
            self.wfile.flush()
            if batch["events"]:
                current = batch["next_cursor"]
            time.sleep(0.5)

    def do_GET(self) -> None:  # noqa: N802
        try:
            self._verify_host()
            parsed = urlsplit(self.path)
            path = parsed.path
            if not path.startswith(API_PREFIX):
                self._static(path)
                return
            plane = self.server.plane
            if path == f"{API_PREFIX}/health":
                self._json(plane.health())
            elif path == f"{API_PREFIX}/system/status":
                self._json(plane.system_status())
            elif path == f"{API_PREFIX}/runs":
                limit = int(self._query(parsed.query, "limit") or "25")
                self._json(plane.runs(cursor=self._query(parsed.query, "cursor"), limit=limit))
            elif path == f"{API_PREFIX}/budget":
                self._json(plane.budget(self._query(parsed.query, "run_id")))
            elif path == f"{API_PREFIX}/config":
                self._json({"configuration": plane.config.list()})
            elif path == f"{API_PREFIX}/events":
                limit = int(self._query(parsed.query, "limit") or "100")
                self._json(plane.events(cursor=self._query(parsed.query, "cursor"), limit=limit))
            elif path == f"{API_PREFIX}/events/stream":
                self._sse(self.headers.get("Last-Event-ID") or self._query(parsed.query, "cursor"))
            elif path == f"{API_PREFIX}/errors":
                limit = int(self._query(parsed.query, "limit") or "50")
                self._json(plane.errors(cursor=self._query(parsed.query, "cursor"), limit=limit))
            elif path == f"{API_PREFIX}/audit":
                self._json({"events": [_redact(event) for event in plane.audit.read_events()]})
            else:
                artifact = re.fullmatch(r"/api/v1/runs/([A-Za-z0-9][A-Za-z0-9_.-]{0,127})/artifacts/([a-f0-9]{64})", path)
                if artifact is not None:
                    self._json(plane.artifact_metadata(*artifact.groups()))
                    return
                match = re.fullmatch(r"/api/v1/runs/([A-Za-z0-9][A-Za-z0-9_.-]{0,127})(?:/(timeline|artifacts|topology|evidence))?", path)
                if match is None:
                    raise ControlCenterError("NOT_FOUND", "endpoint was not found", status=404)
                run_id, view = match.groups()
                if view == "timeline":
                    self._json({"run_id": run_id, "timeline": run_detail(plane.root, run_id, include_timeline=True)["timeline"]})
                elif view == "artifacts":
                    self._json(plane.artifacts(run_id))
                elif view == "topology":
                    self._json(plane.topology(run_id))
                elif view == "evidence":
                    self._json(plane.evidence(run_id))
                else:
                    self._json(run_detail(plane.root, run_id))
        except ValueError:
            self._error(ControlCenterError("INVALID_REQUEST", "numeric query parameter is invalid"))
        except (BrokenPipeError, ConnectionResetError):
            return
        except ControlCenterError as error:
            self._error(error)

    def do_POST(self) -> None:  # noqa: N802
        try:
            key = self._verify_mutation()
            parsed = urlsplit(self.path)
            body = self._body()
            plane = self.server.plane
            if parsed.path == f"{API_PREFIX}/preflight":
                self._json(plane.preflight_action(body, key))
                return
            if parsed.path == f"{API_PREFIX}/config/drafts":
                self._json(plane.config_action("create", None, body, key), 201)
                return
            match = re.fullmatch(r"/api/v1/config/drafts/(draft-[a-f0-9]{32})/(validate|apply)", parsed.path)
            if match is not None:
                draft_id, action = match.groups()
                self._json(plane.config_action(action, draft_id, body, key))
                return
            match = re.fullmatch(r"/api/v1/runs/([A-Za-z0-9][A-Za-z0-9_.-]{0,127})/(checkpoint|pause|resume|stop|finalize)", parsed.path)
            if match is not None:
                run_id, action = match.groups()
                self._json(plane.run_action(run_id, action, body, key))
                return
            raise ControlCenterError("NOT_FOUND", "endpoint was not found", status=404)
        except ControlCenterError as error:
            self._error(error)


class LocalControlHTTPServer(ThreadingHTTPServer):
    """Threaded server whose constructor rejects every non-loopback bind."""

    daemon_threads = True

    def __init__(self, root: str | Path, host: str = "127.0.0.1", port: int = 8765):
        if host != "127.0.0.1":
            raise ControlCenterError("LOOPBACK_REQUIRED", "control center may bind only to 127.0.0.1")
        if type(port) is not int or not 0 <= port <= 65535:
            raise ControlCenterError("INVALID_PORT", "port is invalid")
        self.plane = ControlPlane(root)
        super().__init__((host, port), _LocalHandler)


def serve(root: str | Path = ".", host: str = "127.0.0.1", port: int = 8765) -> None:
    """Run the local server until interrupted by its local operator."""
    with LocalControlHTTPServer(root, host, port) as server:
        server.serve_forever(poll_interval=0.5)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local article-loop Control Center")
    parser.add_argument("--root", default=".")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    try:
        serve(args.root, args.host, args.port)
    except ControlCenterError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = [
    "AuditLedger", "ConfigurationRepository", "ControlCenterError", "ControlPlane",
    "IdempotencyStore", "LocalControlHTTPServer", "active_runs", "approved_artifacts",
    "approved_artifact_metadata", "main", "run_detail", "serve",
]
