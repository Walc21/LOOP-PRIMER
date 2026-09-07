"""Create-only official M6 smoke for exactly one routed AgentTask.

This module is inert unless both execution and fresh human authorization are
strictly true.  It never resumes an attempt and never calls M7 or a later
scientific stage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any, Mapping
from urllib.parse import urlsplit

from .budget import BudgetLedger, BudgetLimits, RunAuthorization
from .execution import ContextMaterializer
from .inference import (
    InferenceBackendError, InferenceOutputError, InferenceRequest,
    InferenceRuntime, ModelRegistry, canonical_bytes, sha256,
)
from .inference_backends import LocalOpenAICompatibleBackend
from .ingestion import validate_source_ready
from .prompts import compile_prompt, expected_prompt_version


SMOKE_ROLES = frozenset({"S10", "W11"})
_ATTEMPT = re.compile(r"attempt-[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")
_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_RUN = re.compile(r"ingest-[a-f0-9]{64}\Z")
_CONFIG_FIELDS = {
    "schema_version", "enabled", "m3_root", "m3_run_id", "attempt_root",
    "role_id", "model", "endpoint", "deadline_utc", "timeout_seconds",
    "context_limit", "max_output_tokens", "max_calls", "max_concurrency",
    "max_retries", "max_cycles", "max_cost_microunits", "deny_remote",
}


class M6SmokeError(RuntimeError):
    """The official single-task smoke contract was not satisfied."""


def _utc(value: Any, *, label: str) -> str:
    if not isinstance(value, str):
        raise M6SmokeError(f"{label} is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise M6SmokeError(f"{label} is invalid") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise M6SmokeError(f"{label} must be absolute UTC")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _integer(value: Any, *, label: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum or value > 2**63 - 1:
        raise M6SmokeError(f"{label} is invalid")
    return value


def _endpoint(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 2048 or any(ord(ch) < 32 for ch in value):
        raise M6SmokeError("endpoint is invalid")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise M6SmokeError("endpoint is invalid") from error
    if (
        parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
        or parsed.username is not None or parsed.password is not None
        or port is None or not (1 <= port <= 65535)
        or parsed.query or parsed.fragment or not parsed.path.startswith("/")
        or "\\" in parsed.path or ".." in Path(parsed.path).parts
    ):
        raise M6SmokeError("endpoint must be explicit HTTP on literal 127.0.0.1 with a port")
    return value


def _no_symlink_components(path: Path, *, allow_missing_leaf: bool = False) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for index, component in enumerate(absolute.parts[1:], 1):
        current = current / component
        try:
            info = current.lstat()
        except FileNotFoundError:
            if allow_missing_leaf and index == len(absolute.parts) - 1:
                return
            raise M6SmokeError("path component is missing")
        except OSError as error:
            raise M6SmokeError("path component is unreadable") from error
        if stat.S_ISLNK(info.st_mode):
            raise M6SmokeError("path crosses a symlink")


def _direct_child(path: Path, parent: Path, *, must_exist: bool) -> Path:
    raw_parent = parent.absolute()
    raw_path = path.absolute()
    _no_symlink_components(raw_parent, allow_missing_leaf=not must_exist)
    if raw_path.parent != raw_parent:
        raise M6SmokeError("path must be a direct child of its allowed runtime root")
    if must_exist or raw_parent.exists():
        _no_symlink_components(raw_path, allow_missing_leaf=not must_exist)
    if must_exist and (not raw_path.is_dir() or raw_path.is_symlink()):
        raise M6SmokeError("runtime root is missing or unsafe")
    if not must_exist and raw_path.exists():
        raise M6SmokeError("attempt root already exists; resume and overwrite are forbidden")
    return raw_path.resolve(strict=must_exist)


@dataclass(frozen=True)
class SmokeConfig:
    schema_version: str
    enabled: bool
    m3_root: Path
    m3_run_id: str
    attempt_root: Path
    role_id: str
    model: str
    endpoint: str
    deadline_utc: str
    timeout_seconds: int
    context_limit: int
    max_output_tokens: int
    max_calls: int
    max_concurrency: int
    max_retries: int
    max_cycles: int
    max_cost_microunits: int
    deny_remote: bool

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SmokeConfig":
        if not isinstance(value, Mapping) or set(value) != _CONFIG_FIELDS:
            raise M6SmokeError("smoke configuration fields are invalid")
        if value.get("schema_version") != "1.0.0":
            raise M6SmokeError("smoke configuration version is invalid")
        if type(value.get("enabled")) is not bool:
            raise M6SmokeError("enabled must be boolean")
        role = value.get("role_id")
        if role not in SMOKE_ROLES:
            raise M6SmokeError("role_id must be S10 or W11")
        model = value.get("model")
        if not isinstance(model, str) or _MODEL.fullmatch(model) is None:
            raise M6SmokeError("model is invalid")
        run = value.get("m3_run_id")
        if not isinstance(run, str) or _RUN.fullmatch(run) is None:
            raise M6SmokeError("m3_run_id is invalid")
        if not isinstance(value.get("m3_root"), str) or not isinstance(value.get("attempt_root"), str):
            raise M6SmokeError("runtime roots must be explicit paths")
        if type(value.get("deny_remote")) is not bool or value["deny_remote"] is not True:
            raise M6SmokeError("deny_remote must be strictly true")
        fixed = {
            "max_calls": 1, "max_concurrency": 1, "max_retries": 0,
            "max_cycles": 1, "max_cost_microunits": 0,
        }
        for name, expected in fixed.items():
            if type(value.get(name)) is not int or value[name] != expected:
                raise M6SmokeError(f"{name} must equal {expected}")
        timeout = _integer(value.get("timeout_seconds"), label="timeout_seconds", minimum=1)
        context = _integer(value.get("context_limit"), label="context_limit", minimum=1)
        output = _integer(value.get("max_output_tokens"), label="max_output_tokens", minimum=1)
        if output >= context:
            raise M6SmokeError("max_output_tokens must be smaller than context_limit")
        return cls(
            "1.0.0", value["enabled"], Path(value["m3_root"]), run,
            Path(value["attempt_root"]), role, model, _endpoint(value["endpoint"]),
            _utc(value["deadline_utc"], label="deadline_utc"), timeout, context,
            output, 1, 1, 0, 1, 0, True,
        )

    def public(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "enabled": self.enabled,
            "m3_root": str(self.m3_root), "m3_run_id": self.m3_run_id,
            "attempt_root": str(self.attempt_root), "role_id": self.role_id,
            "model": self.model, "endpoint": self.endpoint,
            "deadline_utc": self.deadline_utc,
            "timeout_seconds": self.timeout_seconds,
            "context_limit": self.context_limit,
            "max_output_tokens": self.max_output_tokens,
            "max_calls": self.max_calls,
            "max_concurrency": self.max_concurrency,
            "max_retries": self.max_retries, "max_cycles": self.max_cycles,
            "max_cost_microunits": self.max_cost_microunits,
            "deny_remote": self.deny_remote,
        }


def _now(clock: Any | None) -> str:
    return _utc(
        clock.now_utc() if clock is not None else datetime.now(timezone.utc).isoformat(),
        label="current time",
    )


def _deadline_allows(config: SmokeConfig, clock: Any | None) -> None:
    now = datetime.fromisoformat(_now(clock).replace("Z", "+00:00"))
    deadline = datetime.fromisoformat(config.deadline_utc.replace("Z", "+00:00"))
    if now >= deadline:
        raise M6SmokeError("deadline has expired")
    if config.timeout_seconds > (deadline - now).total_seconds():
        raise M6SmokeError("deadline cannot admit the configured timeout")


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_once(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise M6SmokeError(f"refusing to overwrite {path.name}")
    data = canonical_bytes(value) + b"\n"
    descriptor, name = tempfile.mkstemp(prefix=".tmp-m6-smoke-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_once_bytes(path: Path, data: bytes) -> None:
    if path.exists() or path.is_symlink():
        raise M6SmokeError(f"refusing to overwrite {path.name}")
    descriptor, name = tempfile.mkstemp(prefix=".tmp-m6-smoke-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def _policy(config: SmokeConfig, *, test_double: bool) -> dict[str, Any]:
    target_id = "official-local-single-task"
    return {
        "schema_version": "1.0.0", "enabled": True,
        "allow_local": True, "allow_remote": False, "allow_paid": False,
        "routing_mode": "deterministic",
        "targets": {
            target_id: {
                "target_id": target_id, "provider": "local-loopback",
                "model": config.model,
                "backend_type": "fake" if test_double else "local_openai_compatible",
                "enabled": True, "local": True, "paid": False, "tier": "low",
                "capabilities": ["language", "structured_output"],
                "context_limit": config.context_limit,
                "max_output_tokens": config.max_output_tokens,
                "independence_group": "official-smoke-local",
                "endpoint": config.endpoint, "api_key_env": None,
                "timeout_seconds": config.timeout_seconds,
                "fallback_target": None,
                "pricing": {
                    "currency": "USD", "input_microunits_per_million": 0,
                    "output_microunits_per_million": 0,
                    "cached_input_microunits_per_million": 0,
                },
            }
        },
        "role_routes": {
            config.role_id: {
                "targets": [target_id],
                "required_capabilities": ["language", "structured_output"],
            }
        },
        "escalation": {"enabled": False, "max_route_attempts": 1},
        "independence": {
            "jury_must_differ_from_producer_group": True, "mode": "model",
        },
    }


def _task(
    contract_root: Path, config: SmokeConfig, binding: Mapping[str, Any],
    run_id: str, clock: Any | None,
) -> dict[str, Any]:
    schema = "department-packet.schema.json" if config.role_id == "S10" else "agent-proposal.schema.json"
    extracted = str(binding["extracted_path"])
    champion_manifest = str(Path(str(binding["champion_path"])) / "manifest.json")
    locators = [f"readonly:{extracted}", f"readonly:{champion_manifest}"]
    return {
        "schema_version": "1.1.0",
        "task_id": f"{run_id}-{config.role_id}-c0000",
        "run_id": run_id, "cycle_id": 0, "role_id": config.role_id,
        "activation_mode": "RUN", "created_at": _now(clock),
        "base_hash": binding["base_hash"],
        "scope": ["official-m6-single-task-smoke", f"role:{config.role_id}"],
        "input_locators": locators,
        "requested_output_schema": schema,
        "prompt_version": expected_prompt_version(contract_root, config.role_id, schema),
        "constraints": [
            "one_task_only", "no_m7", "no_continuation", "inputs_read_only",
            "receipt_required", "reconciliation_required",
        ],
    }


def run_official_smoke(
    contract_root: str | Path, config: SmokeConfig, *,
    allowed_m3_parent: str | Path, allowed_attempt_parent: str | Path,
    human_authorized: bool = False, allow_test_doubles: bool = False,
    backend: Any | None = None, clock: Any | None = None,
) -> dict[str, Any]:
    """Execute at most one routed call; the attempt can never be resumed."""
    if not isinstance(config, SmokeConfig):
        raise M6SmokeError("validated SmokeConfig is required")
    if type(human_authorized) is not bool or type(allow_test_doubles) is not bool:
        raise M6SmokeError("execution authorizations must be strictly boolean")
    if not config.enabled:
        return {"status": "DISABLED", "executed": False, "calls": 0}
    if not human_authorized:
        raise M6SmokeError("fresh human authorization is required")

    contracts = Path(contract_root)
    if contracts.is_symlink() or not contracts.is_dir():
        raise M6SmokeError("contract root is missing or unsafe")
    contracts = contracts.resolve()
    m3_root = _direct_child(config.m3_root, Path(allowed_m3_parent), must_exist=True)
    attempt = _direct_child(config.attempt_root, Path(allowed_attempt_parent), must_exist=False)
    if _ATTEMPT.fullmatch(attempt.name) is None:
        raise M6SmokeError("attempt root must end in a new attempt UUID")
    is_double = getattr(backend, "is_test_double", False) is True
    if is_double and not allow_test_doubles:
        raise M6SmokeError("test double requires API-only authorization")
    if allow_test_doubles and not is_double:
        raise M6SmokeError("test-double authorization requires an explicit test double")
    if backend is not None and not is_double and not isinstance(backend, LocalOpenAICompatibleBackend):
        raise M6SmokeError("production backend injection is not permitted")
    _deadline_allows(config, clock)
    first_binding = validate_source_ready(m3_root, config.m3_run_id)

    attempt.parent.mkdir(parents=False, exist_ok=True)
    if attempt.parent.is_symlink():
        raise M6SmokeError("attempt parent is unsafe")
    attempt.mkdir(exist_ok=False)
    _fsync_directory(attempt.parent)
    for relative in ("state", "state/locks", "state/budgets", "logs", "inputs"):
        directory = attempt / relative
        directory.mkdir()
        _fsync_directory(directory.parent)

    suffix = attempt.name.removeprefix("attempt-")
    run_id = f"m6-smoke-{suffix}"
    _write_once(attempt / "smoke-config.json", config.public())
    _write_once(attempt / "source-binding.json", first_binding)
    _write_once(attempt / "authorization.json", {
        "schema_version": "1.0.0", "run_id": run_id,
        "human_authorized": True, "authorized_at": _now(clock),
        "scope": "one-local-routed-M6-task",
    })

    task = _task(contracts, config, first_binding, run_id, clock)
    view = {
        "task": task, "excerpts": task["input_locators"],
        "dependent_claims": [],
        "rubric": {"locator": task["input_locators"][1], "role_id": config.role_id},
        "local_history": [],
    }
    materializer = ContextMaterializer(m3_root, schema_root=contracts)
    context = materializer.materialize(
        task, view, privacy_mode="deny_remote",
        context_limit=config.context_limit,
        max_output_tokens=config.max_output_tokens,
    )
    compiled = compile_prompt(
        contracts, task,
        {key: task[key] for key in (
            "run_id", "cycle_id", "base_hash", "activation_mode", "scope",
            "input_locators",
        )},
    )
    prompt = compiled.text + "\n# Materialized authorized M3 context\n" + context.prompt_fragment()
    if config.role_id == "W11":
        prompt += (
            "\n# Routed output ownership\nEmit only the scientific AgentProposal payload; "
            "LOOP derives protocol identity from the validated AgentTask.\n"
        )
    estimate = max(1, (len(prompt.encode("utf-8")) + 3) // 4)
    if estimate + config.max_output_tokens > config.context_limit:
        raise M6SmokeError("compiled prompt and context exceed context_limit")
    _write_once(attempt / "inputs" / "task.json", task)
    _write_once(attempt / "inputs" / "view.json", view)
    _write_once_bytes(attempt / "inputs" / "prompt.txt", prompt.encode("utf-8"))
    _write_once(attempt / "inputs" / "prompt-manifest.json", {
        "prompt_sha256": sha256(prompt.encode("utf-8")),
        "context_hash": context.context_hash,
        "estimated_tokens": estimate,
    })

    policy = _policy(config, test_double=is_double)
    registry = ModelRegistry(policy, privacy_mode="deny_remote")
    limits = BudgetLimits(
        total_tokens=config.context_limit,
        per_cycle_tokens=config.context_limit,
        per_department_tokens=config.context_limit,
        per_role_tokens=config.context_limit,
        per_model_tokens=config.context_limit,
        max_calls=1, max_concurrent_children=1, max_retries=0,
        max_wall_time_seconds=config.timeout_seconds, max_cycles=1,
        max_cycles_without_improvement=0, max_extra_judgments=0,
    )
    config_hash = sha256(canonical_bytes(config.public()))
    ledger = BudgetLedger(
        attempt, run_id, limits=limits, config_hash=config_hash,
        currency="USD", max_run_cost_microunits=0, live_enabled=True,
        deadline_at=config.deadline_utc, clock=clock,
        inference_policy=policy, routing_policy_hash=registry.policy_hash,
    )
    ledger.authorize(RunAuthorization(
        run_id, None, config_hash, None, None, config.context_limit,
        _now(clock), "fresh-human-authorization-current-invocation",
        registry.policy_hash, 0, "USD",
    ))
    selected_backend = backend or LocalOpenAICompatibleBackend(project_root=contracts)
    runtime = InferenceRuntime(
        attempt, ledger, registry,
        {"fake" if is_double else "local_openai_compatible": selected_backend},
        clock=clock, contract_root=contracts,
    )
    request = InferenceRequest.from_agent_task(
        contracts, task, prompt=prompt,
        required_capabilities=("language", "structured_output"),
        estimate_tokens=estimate, max_output_tokens=config.max_output_tokens,
        context_hash=context.context_hash, privacy_mode="deny_remote",
    )

    try:
        # The second full M3 check is deliberately adjacent to route/reserve/send.
        _deadline_allows(config, clock)
        second_binding = validate_source_ready(m3_root, config.m3_run_id)
        if canonical_bytes(second_binding) != canonical_bytes(first_binding):
            raise M6SmokeError("M3 binding changed while the smoke was prepared")
        _deadline_allows(config, clock)
        result = runtime.execute(
            request, live=not is_double, allow_test_doubles=is_double,
        )
    except InferenceBackendError as error:
        ledger.stop("single_task_smoke_terminal_failure")
        status = "UNCERTAIN" if error.sent else "FAILED_PRE_SEND"
        outcome = {
            "schema_version": "1.0.0", "status": status,
            "run_id": run_id, "role_id": config.role_id, "calls": 1,
            "receipt_created": False, "retry_performed": False,
            "refund_performed": False, "m7_started": False,
            "reason_code": error.reason_code,
        }
        _write_once(attempt / "outcome.json", outcome)
        return outcome
    except Exception as error:
        ledger.stop("single_task_smoke_terminal_failure")
        status_view = ledger.status()
        reservations = status_view["reservations"]
        receipts = runtime.store.receipts()
        if any(item.get("status") == "UNCERTAIN" for item in reservations):
            status = "UNCERTAIN"
        elif isinstance(error, InferenceOutputError):
            status = "FAILED_OUTPUT"
        else:
            status = "FAILED_CLOSED"
        outcome = {
            "schema_version": "1.0.0", "status": status,
            "run_id": run_id, "role_id": config.role_id,
            "calls": len(reservations), "receipt_created": bool(receipts),
            "retry_performed": False, "refund_performed": False,
            "m7_started": False, "reason_code": type(error).__name__,
        }
        _write_once(attempt / "outcome.json", outcome)
        return outcome

    ledger.stop("single_task_smoke_complete")
    outcome = {
        "schema_version": "1.0.0", "status": "STOPPED_AFTER_ONE_TASK",
        "run_id": run_id, "role_id": config.role_id, "calls": 1,
        "receipt_created": result.get("receipt") is not None,
        "reconciled": result.get("reconciled", {}).get("status") == "RECONCILED",
        "retry_performed": False, "refund_performed": False,
        "m7_started": False,
        "call_id": result.get("receipt", {}).get("call_id"),
    }
    _write_once(attempt / "outcome.json", outcome)
    return outcome


__all__ = ["M6SmokeError", "SMOKE_ROLES", "SmokeConfig", "run_official_smoke"]
