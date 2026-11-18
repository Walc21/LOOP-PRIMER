#!/usr/bin/env python3
"""One auditable, local-only article-loop attempt.

This command is intentionally narrow.  It never accepts an endpoint, provider,
credential, arbitrary input path, or shell command from its caller.  An attempt
is created below ``runtime/local-full-cycle`` and contains its own project-local
configuration and durable canonical state.  The repository defaults stay
fail-closed.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import sys
import tempfile
import time
from typing import Any, Mapping
from urllib.parse import urlsplit
from uuid import uuid4

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / ".prime" / "agent" / "skills" / "article-loop" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop.activation import ActivationPlanner, PlanningLimits
from article_loop.blackboard import Blackboard, Impact
from article_loop.budget import BudgetLedger, MAX_EXPLICIT_WALL_EXTENSIONS, RunAuthorization
from article_loop.control_center import run_detail
from article_loop.delivery import verify_delivery
from article_loop.diagnosis import diagnose_cycle
from article_loop.evaluation import evaluate_candidate
from article_loop.execution import DualExecutionAdapter, DualExecutionController, ExecutionPolicy
from article_loop.finalization import TransactionalFinalizer
from article_loop.inference import InferenceRuntime, ModelRegistry, model_output_schema
from article_loop.inference_backends import (
    OPENAI_CHAT_COMPLETIONS_JSON_SCHEMA, LocalOpenAICompatibleBackend,
    build_openai_structured_request,
)
from article_loop.m6_smoke import CONTEXT_OVERHEAD_TOKENS, REQUEST_BYTES_PER_TOKEN, REQUEST_TOKEN_SAFETY_MULTIPLIER
from article_loop.ingestion import ingest
from article_loop.orchestrator import Orchestrator
from article_loop.policy import decide
from article_loop.routed_evaluation import RoutedJurorAdapter, RoutedMetaReviewerAdapter
from article_loop.store import DurableStore
from article_loop.synthesis import M7Pipeline, SynthesisError
from article_loop.gates import run_gates
from scripts.synthetic_article import APPROVED_REVISIONS, BASE_SOURCE, CLAIM, REVISED_SOURCE, verify_synthetic_candidate


ENDPOINT = "http://127.0.0.1:11434/v1/chat/completions"
MODELS_ENDPOINT = "http://127.0.0.1:11434/v1/models"
PROFILE = "local_full_cycle"
PDF_RELATIVE = Path("input/inbox/artigo.pdf")
ZIP_RELATIVE = Path("input/inbox/source.zip")
RUNTIME_RELATIVE = Path("runtime/local-full-cycle")
MAX_WALL_SECONDS = 3_600
MAX_TOKENS = 120_000
MAX_CALLS = 12
MAX_CONCURRENCY = 1
CONTEXT_LIMIT = 16_384
SAFE_ATTEMPT = re.compile(r"attempt-[0-9a-f-]{36}\Z")
SAFE_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
WORKER_ROLES = tuple(f"W{department}{worker}" for department in range(1, 6) for worker in range(1, 4))
DEPARTMENTS = tuple(f"S{department}0" for department in range(1, 6))


class LocalCycleError(RuntimeError):
    """A safe stop with an attempt-local diagnostic."""


class _RunClock:
    @staticmethod
    def now_utc() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    monotonic = staticmethod(time.monotonic)


class _SyntheticOrchestrator(Orchestrator):
    def _task(self, state: Mapping[str, Any], role: str, workspace: Path) -> dict[str, Any]:
        task = super()._task(state, role, workspace)
        if role.startswith("W"):
            source = self.root / "versions/champion/v0000/latex-source/paper.tex"
            rubric = self.root / "config/rubrics/evaluation.yaml"
            task["input_locators"] = [
                f"readonly:{source}", f"readonly:{rubric}",
                *(locator for locator in task["input_locators"] if locator.startswith("blackboard:clm-")),
            ]
        return task


def _synthetic_worker_prompt(request: Any, claim_id: str) -> Any:
    role = request.role_id
    if role == "W11":
        operation = ('Use one replace operation targeting latex-source/paper.tex. '
                     'The complete allowed replacement value, encoded as a JSON string, is '
                     + json.dumps(REVISED_SOURCE) + '.')
    else:
        operation = (f"Use one add operation targeting evidence/{role.lower()}.txt. "
                     "Write a short plain-text note on your role's finding for this article.")
    math_fields = ('Set requested_validations to ["correctness_math"] and affected_claims to '
                   + json.dumps([claim_id]) if role == "W22"
                   else "Set requested_validations and affected_claims to empty arrays.")
    prompt = request.prompt + (
        f"\n# Synthetic article scope for {role}\n"
        f"Return only a proposal in the supplied JSON Schema. Set scope to [\"role:{role}\"], "
        'evidence_locators to ["page:1"], dependencies to [], and risk.technical_effect_possible '
        f"to false. Set patch_or_operations.kind to operations. {operation} {math_fields}\n"
    )
    return replace(request, prompt=prompt, prompt_hash=_hash_bytes(prompt.encode("utf-8")))


def _check_synthetic_operations(proposals: list[dict[str, Any]]) -> None:
    for proposal in proposals:
        role = proposal["role_id"]
        change = proposal["patch_or_operations"]
        operations = change.get("operations", [])
        if len(operations) != 1 or change["kind"] != "operations":
            raise LocalCycleError(f"{role} must submit one synthetic article operation")
        operation = operations[0]
        if role == "W11":
            allowed = (operation["op"] == "replace" and operation["target"] == "latex-source/paper.tex"
                       and operation["value"] in APPROVED_REVISIONS)
        else:
            allowed = (operation["op"] == "add" and operation["target"] == f"evidence/{role.lower()}.txt"
                       and isinstance(operation["value"], str))
        if not allowed:
            raise LocalCycleError(f"{role} proposed a change outside the synthetic article scope")


def _admit_structured_request(root: Path, request: Any, target: Any,
                              context_variants: tuple[Any, ...] = ()) -> Any:
    suffix = ".schema.json"
    raw_name = request.requested_output_schema
    schema_name = (raw_name[:-len(suffix)] if raw_name.endswith(suffix) else Path(raw_name).stem).replace("-", "_")
    candidates = (target, *context_variants)
    estimates: list[int] = []
    for candidate in candidates:
        if request.max_output_tokens > candidate.max_output_tokens:
            raise LocalCycleError("context variant output ceiling is below the frozen request")
        body = build_openai_structured_request(
            dialect=OPENAI_CHAT_COMPLETIONS_JSON_SCHEMA, endpoint=candidate.endpoint,
            model=candidate.model, prompt=request.prompt, max_output_tokens=request.max_output_tokens,
            target_max_output_tokens=candidate.max_output_tokens, schema_name=schema_name,
            schema=model_output_schema(root, request),
        )
        estimates.append(max(1, (len(body.body_bytes) * REQUEST_TOKEN_SAFETY_MULTIPLIER
                                 + REQUEST_BYTES_PER_TOKEN - 1) // REQUEST_BYTES_PER_TOKEN))
    safe_input = max(estimates)
    required = safe_input + request.max_output_tokens + CONTEXT_OVERHEAD_TOKENS
    fitting = [candidate for candidate in candidates if required <= candidate.context_limit]
    if not fitting:
        actor = getattr(request, "actor_id", None) or getattr(request, "role_id", None) or target.model
        ceiling = max(candidate.context_limit for candidate in candidates)
        raise LocalCycleError(f"{actor}: structured request exceeds preauthorized context variants ({required} > {ceiling})")
    # Include the safety margin in estimate_tokens so ModelRouter selects the
    # smallest predeclared target whose context limit covers the same request.
    return replace(request, estimate_tokens=safe_input + CONTEXT_OVERHEAD_TOKENS)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise LocalCycleError(f"refusing to overwrite {path.name}")
    encoded = _canonical(value) + b"\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=".tmp-local-cycle-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def _regular(path: Path, *, label: str) -> os.stat_result:
    try:
        info = path.lstat()
    except OSError as error:
        raise LocalCycleError(f"{label} is unavailable") from error
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise LocalCycleError(f"{label} must be a regular non-symlink file")
    return info


def _contained(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise LocalCycleError("unsafe internal path")
    path = root
    for component in relative.parts:
        path = path / component
        if path.is_symlink():
            raise LocalCycleError("symlink in managed path")
    return path


def _source_pdf() -> tuple[Path, int, str]:
    path = _contained(ROOT, PDF_RELATIVE)
    info = _regular(path, label="input PDF")
    return path, info.st_size, _hash_bytes(path.read_bytes())


def _require_no_stop(root: Path) -> None:
    stop = _contained(root, Path("control/STOP"))
    if stop.exists() or stop.is_symlink():
        raise LocalCycleError("control/STOP is present")


def _attempt_dir(attempt_id: str) -> Path:
    if SAFE_ATTEMPT.fullmatch(attempt_id) is None:
        raise LocalCycleError("attempt id is invalid")
    parent = _contained(ROOT, RUNTIME_RELATIVE)
    parent.mkdir(parents=True, exist_ok=True)
    if parent.is_symlink() or not parent.is_dir():
        raise LocalCycleError("runtime parent is unsafe")
    return _contained(parent, Path(attempt_id))


def _read_plan(attempt: Path) -> dict[str, Any]:
    plan = _contained(attempt, Path("run-plan.json"))
    _regular(plan, label="run plan")
    try:
        value = json.loads(plan.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LocalCycleError("run plan is invalid") from error
    if not isinstance(value, dict):
        raise LocalCycleError("run plan is invalid")
    return value


def _loopback_models() -> list[str]:
    parsed = urlsplit(MODELS_ENDPOINT)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.port != 11434:
        raise LocalCycleError("local models endpoint is not literal loopback")
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=10)
    try:
        connection.request("GET", parsed.path)
        response = connection.getresponse()
        raw = response.read(1_048_577)
    except OSError as error:
        raise LocalCycleError("local OpenAI-compatible service is unavailable") from error
    finally:
        connection.close()
    if response.status != 200 or len(raw) > 1_048_576:
        raise LocalCycleError("local models endpoint did not return a bounded success")
    try:
        body = json.loads(raw.decode("utf-8"))
        data = body["data"]
        names = [item["id"] for item in data]
    except (UnicodeError, TypeError, KeyError, json.JSONDecodeError) as error:
        raise LocalCycleError("local models endpoint returned an invalid catalog") from error
    accepted = sorted({name for name in names if isinstance(name, str) and SAFE_MODEL.fullmatch(name)})
    if not accepted:
        raise LocalCycleError("local models endpoint returned no usable model identifiers")
    return accepted


def _target(target_id: str, model: str, group: str, *, context_limit: int = CONTEXT_LIMIT) -> dict[str, Any]:
    return {
        "target_id": target_id,
        "provider": "ollama-loopback",
        "model": model,
        "backend_type": "local_openai_compatible",
        "enabled": True,
        "local": True,
        "paid": False,
        "tier": "mid",
        "capabilities": ["language", "structured_output", "math_high_assurance"],
        "context_limit": context_limit,
        "max_output_tokens": 4096 if target_id.startswith("juror") else 2048,
        "independence_group": group,
        "endpoint": ENDPOINT,
        "api_key_env": None,
        # Jury calls repeatedly used 553–590s at the 4096-token output cap.
        # Give new jury attempts 50% headroom; producer calls stay bounded at 600s.
        "timeout_seconds": 900 if target_id.startswith("juror") else 600,
        "fallback_target": None,
        "pricing": None,
    }


def _configure(attempt: Path, producer_model: str, juror_model: str, approval_reference: str,
               producer_context_32k: str | None = None,
               juror_context_32k: str | None = None) -> tuple[str, str]:
    config_path = _contained(attempt, Path("config/budgets.yaml"))
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise LocalCycleError("base budget configuration is unreadable") from error
    if not isinstance(config, dict):
        raise LocalCycleError("base budget configuration is invalid")
    limits = {
        "total_tokens": MAX_TOKENS,
        "per_cycle_tokens": MAX_TOKENS,
        "per_department_tokens": 300_000,
        "per_role_tokens": 120_000,
        "per_model_tokens": MAX_TOKENS,
        "max_calls": MAX_CALLS,
        "max_concurrent_children": MAX_CONCURRENCY,
        "max_retries": 0,
        "max_wall_time_seconds": MAX_WALL_SECONDS,
        "max_cycles": 1,
        "max_cycles_without_improvement": 0,
        "max_extra_judgments": 0,
    }
    config["model_execution"] = {
        "enabled": True, "paid_apis_enabled": False,
        "provider": "local_openai_compatible", "currency": "USD",
        "total_cost_limit": 0, "per_cycle_cost_limit": 0,
        "max_model_calls": MAX_CALLS, "max_concurrent_children": MAX_CONCURRENCY,
    }
    config["execution"] = {
        "schema_version": "1.0.0", "enabled": True, "mode": "dual",
        "departments": {department: "routed" for department in DEPARTMENTS},
    }
    config["privacy"] = {"schema_version": "1.0.0", "remote_content_mode": "deny_remote"}
    config["authorization"] = {
        "required_for_model_calls": True, "required_for_paid_apis": True,
        "approval_reference": approval_reference,
    }
    config["budget"] = {
        **dict(config["budget"]),
        "currency": "USD", "max_run_cost_microunits": 0,
        "limits": limits,
        "profiles": {PROFILE: {"enabled": True, "limits": limits}},
        "default_profile": PROFILE,
    }
    targets = {
        "producer": _target("producer", producer_model, "local-producer"),
        "juror": _target("juror", juror_model, "local-juror"),
    }
    producer_route = ["producer"]
    juror_route = ["juror"]
    if producer_context_32k is not None:
        targets["producer-32k"] = _target(
            "producer-32k", producer_context_32k, "local-producer", context_limit=32_768,
        )
        producer_route.append("producer-32k")
    if juror_context_32k is not None:
        targets["juror-32k"] = _target(
            "juror-32k", juror_context_32k, "local-juror", context_limit=32_768,
        )
        juror_route.append("juror-32k")
    config["inference"] = {
        "schema_version": "1.0.0", "enabled": True,
        "allow_local": True, "allow_remote": False, "allow_paid": False,
        "routing_mode": "deterministic",
        "targets": targets,
        "role_routes": {
            **{role: {"targets": producer_route, "required_capabilities": ["language", "structured_output"]} for role in WORKER_ROLES},
            "M00": {"targets": juror_route, "required_capabilities": ["language", "structured_output"]},
            "S10": {"targets": juror_route, "required_capabilities": ["language", "structured_output"]},
        },
        "escalation": {"enabled": True, "max_route_attempts": 2},
        "independence": {"jury_must_differ_from_producer_group": True, "mode": "model"},
    }
    encoded = yaml.safe_dump(config, allow_unicode=True, sort_keys=False).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=".tmp-budget-", dir=config_path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, config_path)
        _fsync_directory(config_path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()
    return _hash_bytes(encoded), _hash_bytes(_canonical(config["inference"]))


def prepare(*, producer_model: str, juror_model: str, attempt_id: str | None = None,
            producer_context_32k: str | None = None,
            juror_context_32k: str | None = None) -> dict[str, Any]:
    models = [producer_model, juror_model, producer_context_32k, juror_context_32k]
    if (producer_model == juror_model or (producer_context_32k is None) != (juror_context_32k is None)
            or len([model for model in models if model is not None]) != len(set(model for model in models if model is not None))):
        raise LocalCycleError("producer and juror must be distinct local models")
    if any(SAFE_MODEL.fullmatch(model) is None for model in models if model is not None):
        raise LocalCycleError("model identifier is invalid")
    _require_no_stop(ROOT)
    source, size, digest = _source_pdf()
    source_zip = _contained(ROOT, ZIP_RELATIVE)
    zip_identity = None
    if source_zip.exists() or source_zip.is_symlink():
        zip_info = _regular(source_zip, label="source ZIP")
        zip_identity = {"relative_path": ZIP_RELATIVE.as_posix(), "size_bytes": zip_info.st_size,
                        "sha256": _hash_bytes(source_zip.read_bytes())}
    attempt_id = attempt_id or "attempt-" + str(uuid4())
    attempt = _attempt_dir(attempt_id)
    if attempt.exists():
        raise LocalCycleError("attempt destination already exists")
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=attempt.parent))
    try:
        shutil.copytree(ROOT / "config", staging / "config")
        shutil.copytree(ROOT / "prompts", staging / "prompts")
        (staging / "input/inbox").mkdir(parents=True)
        shutil.copy2(source, staging / PDF_RELATIVE)
        if zip_identity is not None:
            shutil.copy2(source_zip, staging / ZIP_RELATIVE)
            if _hash_bytes((staging / ZIP_RELATIVE).read_bytes()) != zip_identity["sha256"]:
                raise LocalCycleError("source ZIP changed during preparation")
        if _hash_bytes((staging / PDF_RELATIVE).read_bytes()) != digest:
            raise LocalCycleError("input PDF changed during preparation")
        for relative in ("artifacts", "versions", "workspaces", "state", "reports", "control"):
            (staging / relative).mkdir()
        approval_reference = f"human-authorized:{attempt_id}"
        config_hash, routing_hash = _configure(
            staging, producer_model, juror_model, approval_reference,
            producer_context_32k, juror_context_32k,
        )
        planned_models = {"producer": producer_model, "juror_meta": juror_model}
        if producer_context_32k is not None:
            planned_models["producer_context_32k"] = producer_context_32k
            planned_models["juror_context_32k"] = juror_context_32k
        plan = {
            "schema_version": "1.0.0",
            "attempt_id": attempt_id,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": {"relative_path": PDF_RELATIVE.as_posix(), "size_bytes": size, "sha256": digest},
            "source_zip": zip_identity,
            "authorization_reference": approval_reference,
            "endpoint": ENDPOINT,
            "models": planned_models,
            "config_sha256": config_hash,
            "routing_policy_sha256": routing_hash,
            "limits": {"max_wall_seconds": MAX_WALL_SECONDS, "max_tokens": MAX_TOKENS, "max_calls": MAX_CALLS, "max_concurrency": MAX_CONCURRENCY, "max_retries": 0, "max_cycles": 1, "external_cost_microunits": 0},
            "execution": {"departments": {department: "routed" for department in DEPARTMENTS}, "backend": "local_openai_compatible", "remote_allowed": False, "paid_allowed": False, "fallback": None},
        }
        _atomic_json(staging / "run-plan.json", plan)
        _fsync_directory(staging)
        os.replace(staging, attempt)
        _fsync_directory(attempt.parent)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return plan


def preflight(attempt_id: str) -> dict[str, Any]:
    attempt = _attempt_dir(attempt_id)
    plan = _read_plan(attempt)
    if plan.get("authorization_reference") != f"human-authorized:{attempt_id}":
        raise LocalCycleError("attempt uses an outdated authorization reference")
    _require_no_stop(ROOT)
    _require_no_stop(attempt)
    config = _contained(attempt, Path("config/budgets.yaml"))
    _regular(config, label="attempt configuration")
    if _hash_bytes(config.read_bytes()) != plan.get("config_sha256"):
        raise LocalCycleError("attempt configuration hash differs from plan")
    for relative, identity in ((PDF_RELATIVE, plan.get("source")), (ZIP_RELATIVE, plan.get("source_zip"))):
        path = _contained(attempt, relative)
        if identity is None and relative == ZIP_RELATIVE:
            if path.exists() or path.is_symlink():
                raise LocalCycleError("unexpected source ZIP")
            continue
        if not isinstance(identity, Mapping) or identity.get("relative_path") != relative.as_posix():
            raise LocalCycleError("source identity is invalid")
        info = _regular(path, label="attempt input")
        if info.st_size != identity.get("size_bytes") or _hash_bytes(path.read_bytes()) != identity.get("sha256"):
            raise LocalCycleError("attempt input differs from plan")
    names = _loopback_models()
    selected = plan.get("models", {})
    if not isinstance(selected, dict) or any(model not in names for model in selected.values()):
        raise LocalCycleError("selected local models are not available from loopback service")
    registry = ModelRegistry.from_project(attempt)
    expected_targets = {"producer": "producer", "juror": "juror_meta",
                        "producer-32k": "producer_context_32k", "juror-32k": "juror_context_32k"}
    if (registry.policy_hash != plan.get("routing_policy_sha256")
            or any(registry.target(target_id).model != selected[model_key]
                   for target_id, model_key in expected_targets.items() if model_key in selected)
            or any(target_id in registry.targets for target_id, model_key in expected_targets.items() if model_key not in selected)):
        raise LocalCycleError("attempt routing differs from plan")
    policy = ExecutionPolicy.from_project(attempt)
    if (not registry.enabled or registry.allow_remote or registry.allow_paid
            or any(not target.local or target.paid or target.backend_type != "local_openai_compatible" for target in registry.targets.values())
            or any(policy.layer(department) != "routed" for department in DEPARTMENTS)):
        raise LocalCycleError("attempt configuration does not satisfy local-only policy")
    backend = LocalOpenAICompatibleBackend(
        project_root=attempt,
        structured_output_dialect=OPENAI_CHAT_COMPLETIONS_JSON_SCHEMA,
        native_ollama_chat=True,
    )
    backend_status = {target_id: dict(backend.preflight(target)) for target_id, target in registry.targets.items()}
    return {"attempt_id": attempt_id, "models_detected": names, "selected_models": selected, "endpoint": ENDPOINT, "config_sha256": plan["config_sha256"], "routing_policy_sha256": plan["routing_policy_sha256"], "backend": backend_status, "local_only": True}


def _persist_activation(root: Path, run_id: str, base_hash: str, *, synthetic_article: bool = False) -> dict[str, Any]:
    if not isinstance(base_hash, str) or len(base_hash) != 64:
        raise LocalCycleError("M3 source state has no canonical base hash")
    board = Blackboard(root)
    claim = board.append(run_id, "claims", {
        "text": CLAIM if synthetic_article else "Local-only full-cycle authorization bound to the frozen input; this is provenance, not a mathematical assertion.",
        "type": "theorem" if synthetic_article else "provenance", "location": {"page": 1, "section": "source"},
        "dependencies": [], "evidence": ["page:1"], "status": "active",
        "severity": 1, "source_hash": base_hash, "last_validated_cycle": 0,
    })
    impact = Impact(
        claims=(claim["claim_id"],), sections=("source",), equations=(), references=(),
        roles=("W22",) if synthetic_article else WORKER_ROLES, severity=1,
    )
    plan = ActivationPlanner(PlanningLimits(
        max_active_per_cycle=21, max_active_per_department=4,
        max_children_per_manager=3, max_active_per_role=1,
        max_wall_time_seconds=MAX_WALL_SECONDS, max_estimated_tokens=20_000,
        freeze_dependency_cycles=2,
    )).plan(cycle_id=0, impact=impact)
    if plan.paused:
        raise LocalCycleError("M5 activation plan is paused")
    directory = root / "state" / "blackboard" / run_id
    plan.write_activation_map(directory / "activation_map.json")
    plan.write_activation_map(directory / "activation-c0000.json")
    return plan.activation_map()


def _authorize(ledger: BudgetLedger, approval_reference: str) -> None:
    authorization = RunAuthorization(
        ledger.run_id, PROFILE, ledger.config_hash, None, None, MAX_TOKENS,
        ledger.clock.now_utc(),
        approval_reference, ledger.routing_policy_hash, 0, "USD",
    )
    ledger.authorize(authorization)


def _checkpoint(orchestrator: Orchestrator, run_id: str, *, reason: str, attempt: Path) -> None:
    result: dict[str, Any] = {"reason": reason, "run_id": run_id}
    try:
        result["orchestration"] = asyncio.run(orchestrator.pause(run_id))
    except Exception as error:
        result["pause_error"] = f"{type(error).__name__}: {error}"
    _atomic_json(attempt / "outcome.json", result)


class _GuardedJuror:
    def __init__(self, adapter: Any, guard: Any):
        self.adapter = adapter
        self.guard = guard
        self.requires_test_mode = getattr(adapter, "requires_test_mode", False)
        self.is_test_double = getattr(adapter, "is_test_double", False)

    def evaluate(self, presentation: Mapping[str, Any]) -> dict[str, Any]:
        self.guard()
        return self.adapter.evaluate(presentation)


class _GuardedMetaReviewer:
    def __init__(self, adapter: Any, guard: Any):
        self.adapter = adapter
        self.guard = guard
        self.requires_test_mode = getattr(adapter, "requires_test_mode", False)
        self.is_test_double = getattr(adapter, "is_test_double", False)

    def review(self, **kwargs: Any) -> dict[str, Any]:
        self.guard()
        return self.adapter.review(**kwargs)


def _complete_cycle(attempt: Path, run_id: str, candidate_id: str, report_locator: str,
                    jurors: Mapping[str, Any], meta: Any, model_family: str,
                    guard: Any, *, allow_test_doubles: bool = False) -> dict[str, Any]:
    guard()
    evaluate_candidate(
        attempt, run_id, cycle_id=0, candidate_id=candidate_id,
        gate_report_locator=report_locator,
        juror_adapters={name: _GuardedJuror(adapter, guard) for name, adapter in jurors.items()},
        meta_adapter=_GuardedMetaReviewer(meta, guard),
        model_families={name: model_family for name in jurors},
        allow_test_doubles=allow_test_doubles,
    )
    guard()
    diagnose_cycle(attempt, run_id, cycle_id=0, candidate_id=candidate_id, window_size=1)
    guard()
    decision = decide(attempt, run_id, cycle_id=0)
    guard()
    receipt = TransactionalFinalizer(attempt).finalize(run_id, cycle_id=0)
    if receipt["action"] not in {"PROMOTE", "ARCHIVE_PARETO", "REJECT"}:
        return {"status": "stopped", "run_id": run_id, "action": receipt["action"],
                "state": receipt["state_after"]}
    guard()
    audit = verify_delivery(attempt, run_id, cycle_id=0)
    return {"status": "complete", "run_id": run_id, "candidate_id": candidate_id,
            "action": decision["action"], "state": audit["state"], "audit": audit}


def _bound_attempt_deadline(attempt: Path, run_id: str) -> str:
    ledger_path = _contained(attempt, Path("state/budgets") / f"{run_id}.jsonl")
    _regular(ledger_path, label="budget ledger")
    values = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if event.get("event_type") == "RESERVED":
            deadline = event.get("payload", {}).get("deadline_at")
            if isinstance(deadline, str):
                values.append(deadline)
    if not values:
        raise LocalCycleError("recovery requires the original run deadline")
    return values[0]


def _eligible_schema_failure(attempt: Path, run_id: str, registry: ModelRegistry,
                             ledger_status: Mapping[str, Any], already_used: set[str]) -> dict[str, Any] | None:
    receipts_dir = _contained(attempt, Path("state/inference") / run_id / "receipts")
    if receipts_dir.exists() and (receipts_dir.is_symlink() or not receipts_dir.is_dir()):
        raise LocalCycleError("inference receipts directory is unsafe")
    reservations = {item.get("reservation_id"): item for item in ledger_status.get("reservations", [])
                    if isinstance(item, Mapping)}
    candidates = []
    if not receipts_dir.exists():
        return None
    for path in receipts_dir.glob("*.json"):
        _regular(path, label="inference receipt")
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise LocalCycleError("recovery found an unreadable inference receipt") from error
        if (receipt.get("run_id") != run_id or receipt.get("target_id") not in {"juror", "juror-32k"}
                or receipt.get("finish_reason") != "schema_invalid"
                or receipt.get("actor_id") not in {"juror-math", "juror-contrib", "juror-clarity", "meta-reviewer"}
                or receipt.get("receipt_id") in already_used):
            continue
        target = registry.target(receipt["target_id"])
        reservation = reservations.get(receipt.get("reservation_id"))
        if (type(receipt.get("output_tokens")) is not int
                or receipt["output_tokens"] != target.max_output_tokens
                or reservation is None or reservation.get("status") != "RECONCILED"
                or reservation.get("receipt_id") != receipt.get("receipt_id")):
            continue
        candidates.append(receipt)
    return max(candidates, key=lambda item: item.get("created_at", "")) if candidates else None


def recover(attempt_id: str, *, human_authorized: bool = False) -> dict[str, Any]:
    """Continue a gated local run after a reconciled structured-output ceiling failure."""
    if human_authorized is not True:
        raise LocalCycleError("recovery requires current explicit human authorization")
    attempt = _attempt_dir(attempt_id)
    plan = _read_plan(attempt)
    plan_path = _contained(attempt, Path("run-plan.json"))
    original_plan_hash = _hash_bytes(plan_path.read_bytes())
    original_outcome_path = _contained(attempt, Path("outcome.json"))
    _regular(original_outcome_path, label="original terminal outcome")
    original_outcome_bytes = original_outcome_path.read_bytes()
    original_outcome = json.loads(original_outcome_bytes)
    if original_outcome.get("status") != "blocked":
        raise LocalCycleError("recovery is only valid for a blocked original outcome")
    run_id = original_outcome.get("run_id")
    expected_run_id = "ingest-" + str(plan.get("source", {}).get("sha256", ""))
    if run_id != expected_run_id:
        raise LocalCycleError("recovery run identity differs from the frozen source")
    if not (attempt / "versions/champion/v0000/latex-source/paper.tex").is_file():
        raise LocalCycleError("recovery requires the synthetic-article attempt")
    baseline = _contained(attempt, Path("versions/champion/v0000/latex-source/paper.tex"))
    if baseline.read_text(encoding="utf-8") != BASE_SOURCE:
        raise LocalCycleError("recovery source differs from the fixed synthetic article")

    events = DurableStore(attempt).read_events(run_id)
    if (not events or events[-1].get("event_type") != "M7_ARTIFACT"
            or events[-1].get("state_to") != "GATES_PASSED"):
        raise LocalCycleError("recovery requires the unchanged canonical GATES_PASSED state")
    event_payload = events[-1].get("payload", {})
    candidate_id, report_locator = event_payload.get("candidate_id"), event_payload.get("report_locator")
    if not isinstance(candidate_id, str) or not isinstance(report_locator, str):
        raise LocalCycleError("GATES_PASSED event lacks candidate or gate-report binding")
    evaluation_report = _contained(attempt, Path("state/evaluations") / run_id / "c0000/evaluation.json")
    if evaluation_report.exists() or evaluation_report.is_symlink():
        raise LocalCycleError("an evaluation artifact already exists; recovery would duplicate M8")

    deadline = _bound_attempt_deadline(attempt, run_id)
    created_dt = datetime.fromisoformat(plan["created_at"].replace("Z", "+00:00"))
    limits = plan.get("limits")
    original_max_wall = limits.get("max_wall_seconds") if isinstance(limits, Mapping) else None
    max_calls = limits.get("max_calls") if isinstance(limits, Mapping) else None
    if type(original_max_wall) is not int or type(max_calls) is not int:
        raise LocalCycleError("original run limits are invalid")

    _require_no_stop(ROOT)
    _require_no_stop(attempt)
    preflight(attempt_id)
    registry = ModelRegistry.from_project(attempt)
    ledger = BudgetLedger.from_project(
        attempt, run_id, profile=PROFILE, deadline_at=deadline, clock=_RunClock(),
    )
    budget_status = ledger.status(current_cycle=0, read_only=True)
    if (budget_status["open_reservations"] != 0
            or not budget_status["authorization"]["present"]):
        raise LocalCycleError("recovery requires authorization and closed reservations")
    if budget_status["calls"] >= max_calls + 7:
        raise LocalCycleError("the original call limit plus seven explicit M8 recoveries is exhausted")

    recovery_root = _contained(attempt, Path("recoveries"))
    plans_dir, results_dir = recovery_root / "plans", recovery_root / "results"
    for directory in (recovery_root, plans_dir, results_dir):
        if directory.exists() and (directory.is_symlink() or not directory.is_dir()):
            raise LocalCycleError("recovery evidence path is unsafe")
        directory.mkdir(parents=True, exist_ok=True)
    plan_files = sorted(plans_dir.glob("recovery-*.json"))
    result_files = sorted(results_dir.glob("recovery-*.json"))
    if any(path.is_symlink() or not path.is_file() for path in (*plan_files, *result_files)):
        raise LocalCycleError("recovery evidence contains an unsafe entry")
    if result_files and json.loads(result_files[-1].read_text(encoding="utf-8")).get("status") == "complete":
        raise LocalCycleError("the recovery chain already completed")
    used_receipts = {
        json.loads(path.read_text(encoding="utf-8")).get("failed_receipt_id")
        for path in plan_files
    }
    # A new schema-bound repair may reuse the latest failed receipt once when
    # its preceding v2 compact-prompt recovery was blocked. The request hash
    # changes with the bounded v3 payload schema; the old receipt stays immutable.
    reusable_failed_receipt = None
    if plan_files and result_files:
        prior_plan = json.loads(plan_files[-1].read_text(encoding="utf-8"))
        prior_result = json.loads(result_files[-1].read_text(encoding="utf-8"))
        if (prior_plan.get("repair") == "compact-routed-m8-prompt-v2"
                and prior_result.get("status") == "blocked"):
            reusable_failed_receipt = prior_plan.get("failed_receipt_id")
    failure = _eligible_schema_failure(
        attempt, run_id, registry, budget_status,
        used_receipts - ({reusable_failed_receipt} if reusable_failed_receipt else set()),
    )
    if failure is None:
        raise LocalCycleError("no new reconciled schema-invalid receipt exactly at the output ceiling")

    backend = LocalOpenAICompatibleBackend(
        project_root=attempt,
        structured_output_dialect=OPENAI_CHAT_COMPLETIONS_JSON_SCHEMA,
    )
    runtime = InferenceRuntime(attempt, ledger, registry, {"local_openai_compatible": backend})
    preflight_report = runtime.preflight()
    if any(not item.get("ready") for item in preflight_report.get("targets", {}).values()):
        raise LocalCycleError("local backends are not ready for the bound recovery route")

    original_outcome_hash = _hash_bytes(original_outcome_bytes)
    recovery_number = len(plan_files) + 1
    pending_extension = None
    wall_extensions = sum(
        1 for event in ledger.read_events()
        if event.get("event_type") == "LIMITS_EXTENDED"
        and "deadline_at" in event.get("payload", {})
    )
    if wall_extensions < MAX_EXPLICIT_WALL_EXTENSIONS:
        pending_extension = ledger.extend_recovery_runtime(
            approval_reference=f"human-authorized-recovery:{attempt_id}",
        )
    deadline_dt = datetime.fromisoformat(ledger.deadline_at.replace("Z", "+00:00"))
    max_wall = ledger.limits.max_wall_time_seconds
    if (type(max_wall) is not int or datetime.now(timezone.utc) >= deadline_dt
            or (datetime.now(timezone.utc) - created_dt).total_seconds() >= max_wall):
        raise LocalCycleError("bounded recovery deadline or wall-time limit is exhausted")
    runtime_start = time.monotonic()
    current_failure = failure

    def guard() -> None:
        _require_no_stop(ROOT)
        _require_no_stop(attempt)
        now = datetime.now(timezone.utc)
        if now >= deadline_dt or (now - created_dt).total_seconds() >= max_wall:
            raise LocalCycleError("original run deadline or wall-time limit reached")
        if time.monotonic() - runtime_start >= max_wall:
            raise LocalCycleError("recovery wall-time limit reached")

    while True:
        guard()
        if recovery_number > 7:
            raise LocalCycleError("the recovery-call extension ceiling is exhausted")
        approval_reference = f"human-authorized-recovery:{attempt_id}"
        extension_event = pending_extension or ledger.extend_call_limit(approval_reference=approval_reference)
        pending_extension = None
        recovery_id = f"recovery-{recovery_number:04d}"
        recovery_plan = {
            "schema_version": "1.0.0",
            "recovery_id": recovery_id,
            "attempt_id": attempt_id,
            "run_id": run_id,
            "original_plan_sha256": original_plan_hash,
            "original_outcome_sha256": original_outcome_hash,
            "failed_receipt_id": current_failure["receipt_id"],
            "failed_receipt_hash": current_failure["receipt_hash"],
            "failed_task_id": current_failure["task_id"],
            "failed_prompt_hash": current_failure["prompt_hash"],
            "model": current_failure["model"],
            "repair": "routed-m8-v6-native-ollama-think-off",
            "api_mode": "ollama_native_chat",
            "effective_endpoint": ENDPOINT.replace("/v1/chat/completions", "/api/chat"),
            "think": False,
            "budget_extension_event_hash": extension_event["event_hash"],
            "effective_deadline_at": ledger.deadline_at,
            "effective_max_wall_time_seconds": ledger.limits.max_wall_time_seconds,
            "runtime_extension_seconds": 3600 if "deadline_at" in extension_event["payload"] else 0,
            "calls_before": budget_status["calls"],
            "calls_after_limit_extension": ledger.limits.max_calls,
            "limits_unchanged": ["total_tokens", "per_cycle_tokens", "per_department_tokens",
                "per_role_tokens", "per_model_tokens", "max_concurrent_children",
                "max_retries", "max_cycles", "max_extra_judgments",
                "external_cost_microunits", "provider", "remote", "paid",
                "loopback_host", "model"],
            "authorization_reference": approval_reference,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        recovery_plan_path = plans_dir / f"{recovery_id}.json"
        recovery_result_path = results_dir / f"{recovery_id}.json"
        if recovery_plan_path.exists() or recovery_result_path.exists():
            raise LocalCycleError("recovery identity already exists")
        _atomic_json(recovery_plan_path, recovery_plan)
        used_receipts.add(current_failure["receipt_id"])
        if (not events or events[-1].get("event_hash") != DurableStore(attempt).read_events(run_id)[-1].get("event_hash")):
            raise LocalCycleError("canonical gate evidence changed before recovery")

        judge = registry.target("juror")
        jury_context_variants = ((registry.target("juror-32k"),)
                                 if "juror-32k" in registry.targets else ())
        repair_state = {
            "prompt_hash": current_failure["prompt_hash"], "number": recovery_number,
            "attempted_prompt_hashes": set(),
        }

        def prepare_request(request: Any) -> Any:
            # A prompt-version repair naturally creates a new identity. If the
            # compact prompt itself later hits the cap, change only that failed
            # task identity so valid prior M8 receipts remain replayable.
            if request.prompt_hash == repair_state["prompt_hash"]:
                request = replace(request, task_id=f"{request.task_id}-recovery-{repair_state['number']:04d}")
            repair_state["attempted_prompt_hashes"].add(request.prompt_hash)
            return _admit_structured_request(attempt, request, judge, jury_context_variants)

        options = {
            "run_id": run_id, "cycle_id": 0, "producer_target": "producer", "live": True,
            "max_output_tokens": judge.max_output_tokens,
            "prepare_request": prepare_request,
        }
        jurors = {name: RoutedJurorAdapter(attempt, runtime, juror_id=name, **options)
                  for name in ("juror-math", "juror-contrib", "juror-clarity")}
        meta = RoutedMetaReviewerAdapter(attempt, runtime, routing_role_id="S10", **options)
        try:
            outcome = _complete_cycle(attempt, run_id, candidate_id, report_locator,
                                      jurors, meta, judge.model, guard)
        except Exception as error:
            result = {"status": "blocked", "recovery_id": recovery_id,
                      "run_id": run_id, "stage": type(error).__name__, "cause": str(error),
                      "inspection": f"python3 scripts/local_loopback_full_cycle.py status --attempt-id {attempt_id}"}
            _atomic_json(recovery_result_path, result)
            current_status = ledger.status(current_cycle=0, read_only=True)
            next_failure = _eligible_schema_failure(attempt, run_id, registry, current_status, used_receipts)
            if (next_failure is None or next_failure["receipt_id"] == current_failure["receipt_id"]
                    or next_failure["prompt_hash"] in repair_state["attempted_prompt_hashes"]
                    or recovery_number >= 7 or current_status["open_reservations"] != 0):
                return result
            used_receipts.add(current_failure["receipt_id"])
            current_failure = next_failure
            recovery_number += 1
            budget_status = current_status
            continue
        outcome = {**outcome, "recovery_id": recovery_id,
                   "original_plan_sha256": original_plan_hash,
                   "original_outcome_sha256": original_outcome_hash}
        _atomic_json(recovery_result_path, outcome)
        return outcome


def run(attempt_id: str, *, human_authorized: bool = False, deadline: str | None = None,
        synthetic_article: bool = False) -> dict[str, Any]:
    if human_authorized is not True or not deadline:
        raise LocalCycleError("run requires explicit human authorization and UTC deadline")
    try:
        parsed_deadline = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        if parsed_deadline.utcoffset() is None or parsed_deadline.utcoffset().total_seconds() != 0 or parsed_deadline <= datetime.now(timezone.utc):
            raise ValueError("deadline must be future UTC")
    except (ValueError, OverflowError) as error:
        raise LocalCycleError("deadline must be a future UTC timestamp") from error
    attempt = _attempt_dir(attempt_id)
    plan = _read_plan(attempt)
    if (attempt / "outcome.json").exists():
        raise LocalCycleError("attempt already has a terminal outcome record; inspect status")
    preflight(attempt_id)
    started = time.monotonic()
    interrupted = {"value": False}

    def on_sigint(_signum: int, _frame: Any) -> None:
        interrupted["value"] = True

    def guard() -> None:
        _require_no_stop(ROOT)
        _require_no_stop(attempt)
        if interrupted["value"] or time.monotonic() - started >= MAX_WALL_SECONDS or datetime.now(timezone.utc) >= parsed_deadline:
            raise LocalCycleError("execution interrupted or deadline reached")

    source = plan.get("source")
    source_hash = source.get("sha256") if isinstance(source, Mapping) else None
    if not isinstance(source_hash, str) or re.fullmatch(r"[a-f0-9]{64}", source_hash) is None:
        raise LocalCycleError("run plan source hash is invalid")
    previous = signal.signal(signal.SIGINT, on_sigint)
    # M3 binds the run identifier to immutable input bytes, so the identity is
    # known even when SOURCE_READY cannot form.
    run_id: str | None = "ingest-" + source_hash
    orchestrator: Orchestrator | None = None
    try:
        _require_no_stop(ROOT)
        _require_no_stop(attempt)
        m3 = ingest(attempt)
        if m3["run_id"] != run_id:
            raise LocalCycleError("M3 run identity differs from the frozen input")
        policy = ExecutionPolicy.from_project(attempt)
        adapter = DualExecutionAdapter(attempt, run_id, policy)
        if synthetic_article:
            baseline = _contained(attempt, Path("versions/champion/v0000/latex-source/paper.tex"))
            _regular(baseline, label="synthetic article source")
            if baseline.read_text(encoding="utf-8") != BASE_SOURCE:
                raise LocalCycleError("synthetic article source differs from fixed fixture")
        orchestrator_type = _SyntheticOrchestrator if synthetic_article else Orchestrator
        orchestrator = orchestrator_type(attempt, adapter=adapter)
        asyncio.run(orchestrator.bootstrap(attempt / PDF_RELATIVE))
        state = asyncio.run(orchestrator.status(run_id))
        _persist_activation(attempt, run_id, state.get("base_hash"), synthetic_article=synthetic_article)
        claim_id = None
        if synthetic_article:
            (claim_id,) = Blackboard(attempt).claims(run_id)
        ledger = BudgetLedger.from_project(
            attempt, run_id, profile=PROFILE, deadline_at=deadline, clock=_RunClock(),
        )
        _authorize(ledger, f"human-authorized:{attempt_id}")
        registry = ModelRegistry.from_project(attempt)
        backend = LocalOpenAICompatibleBackend(
            project_root=attempt,
            structured_output_dialect=OPENAI_CHAT_COMPLETIONS_JSON_SCHEMA,
        )
        runtime = InferenceRuntime(attempt, ledger, registry, {"local_openai_compatible": backend})
        execute = runtime.execute

        def guarded_execute(request: Any, **kwargs: Any) -> dict[str, Any]:
            guard()
            if request.actor_kind != "evaluator":
                if claim_id is not None:
                    request = _synthetic_worker_prompt(request, claim_id)
                variants = ((registry.target("producer-32k"),)
                            if "producer-32k" in registry.targets else ())
                request = _admit_structured_request(attempt, request, registry.target("producer"), variants)
            return execute(request, **kwargs)

        runtime.execute = guarded_execute
        runtime_preflight = runtime.preflight()
        _atomic_json(attempt / "runtime-preflight.json", runtime_preflight)
        asyncio.run(orchestrator.run_cycle(run_id=run_id, cycle_id=0, allow_test_doubles=False))
        controller = DualExecutionController(attempt, policy, registry)
        for department in DEPARTMENTS:
            if interrupted["value"] or time.monotonic() - started >= MAX_WALL_SECONDS:
                _checkpoint(orchestrator, run_id, reason="SIGINT" if interrupted["value"] else "wall_time_limit", attempt=attempt)
                return _read_plan(attempt) | {"run_id": run_id, "status": "paused"}
            _require_no_stop(ROOT)
            _require_no_stop(attempt)
            state = asyncio.run(orchestrator.status(run_id))
            manager = adapter.department_adapter(state["children"][department])
            asyncio.run(controller.execute_routed_department(orchestrator, run_id, department, manager, runtime, live=True, allow_test_doubles=False))
        state = asyncio.run(orchestrator.status(run_id))
        guard()
        pipe = M7Pipeline(attempt)
        synthesis = pipe.synthesize(state["receipts"], run_id=run_id)
        if synthetic_article:
            _check_synthetic_operations(pipe._frozen_proposals(synthesis))
        store = DurableStore(attempt)
        pipe.record_synthesis(store, synthesis)
        candidate = pipe.build(synthesis, attempt / "versions/champion/v0000")
        pipe.record_candidate(store, candidate)
        if synthetic_article:
            guard()
            verify_synthetic_candidate(attempt / "versions/challengers" / candidate["candidate_id"])
        report = run_gates(attempt / "versions/challengers" / candidate["candidate_id"])
        try:
            pipe.record_gates(store, report["report_locator"])
        except SynthesisError as error:
            # A failed hard scientific gate is canonical evidence.  It cannot
            # advance to jury/decision without fabricated math verification.
            outcome = {"status": "gates_failed", "run_id": run_id, "candidate_id": candidate["candidate_id"], "gate_report_locator": report["report_locator"], "gate_report_hash": report["report_hash"], "cause": str(error), "state": DurableStore(attempt).snapshot(run_id)["state"], "inspection": "python3 scripts/local_loopback_full_cycle.py status --attempt-id " + attempt_id}
            _atomic_json(attempt / "outcome.json", outcome)
            return outcome
        judge = registry.target("juror")
        jury_context_variants = ((registry.target("juror-32k"),)
                                 if "juror-32k" in registry.targets else ())
        options = {
            "run_id": run_id, "cycle_id": 0, "producer_target": "producer", "live": True,
            "max_output_tokens": judge.max_output_tokens,
            "prepare_request": lambda request: _admit_structured_request(
                attempt, request, judge, jury_context_variants,
            ),
        }
        jurors = {name: RoutedJurorAdapter(attempt, runtime, juror_id=name, **options)
                  for name in ("juror-math", "juror-contrib", "juror-clarity")}
        meta = RoutedMetaReviewerAdapter(attempt, runtime, routing_role_id="S10", **options)
        outcome = _complete_cycle(attempt, run_id, candidate["candidate_id"], report["report_locator"],
                                  jurors, meta, judge.model, guard)
        _atomic_json(attempt / "outcome.json", outcome)
        return outcome
    except Exception as error:
        outcome = {"status": "blocked", "run_id": run_id, "stage": type(error).__name__, "cause": str(error), "recoverable": True, "inspection": "python3 scripts/local_loopback_full_cycle.py status --attempt-id " + attempt_id}
        if orchestrator is not None and run_id is not None:
            try:
                outcome["orchestration"] = asyncio.run(orchestrator.status(run_id))
            except Exception as status_error:
                outcome["status_error"] = f"{type(status_error).__name__}: {status_error}"
        _atomic_json(attempt / "outcome.json", outcome)
        return outcome
    finally:
        signal.signal(signal.SIGINT, previous)


def status(attempt_id: str) -> dict[str, Any]:
    attempt = _attempt_dir(attempt_id)
    plan = _read_plan(attempt)
    result: dict[str, Any] = {"attempt_id": attempt_id, "plan": plan}
    outcome = attempt / "outcome.json"
    if outcome.exists():
        _regular(outcome, label="outcome")
        result["outcome"] = json.loads(outcome.read_text(encoding="utf-8"))
    recovery_root = attempt / "recoveries"
    if recovery_root.exists():
        recovery_plans = recovery_root / "plans"
        recovery_results = recovery_root / "results"
        items = []
        if recovery_plans.exists() and recovery_results.exists():
            for plan_path in sorted(recovery_plans.glob("recovery-*.json")):
                _regular(plan_path, label="recovery plan")
                item = {"plan": json.loads(plan_path.read_text(encoding="utf-8"))}
                result_path = recovery_results / plan_path.name
                if result_path.exists():
                    _regular(result_path, label="recovery result")
                    item["result"] = json.loads(result_path.read_text(encoding="utf-8"))
                items.append(item)
        result["recoveries"] = items
        if items and isinstance(items[-1].get("result"), Mapping):
            result["effective_outcome"] = items[-1]["result"]
        elif "outcome" in result:
            result["effective_outcome"] = result["outcome"]
    events = attempt / "state/events"
    if events.exists():
        ids = sorted(item.stem for item in events.glob("*.jsonl") if item.is_file() and not item.is_symlink())
        if ids:
            result["canonical_run_ids"] = ids
            if len(ids) == 1:
                result["canonical_run_id"] = ids[0]
        result["canonical_runs"] = {run_id: run_detail(attempt, run_id) for run_id in ids}
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepared = commands.add_parser("prepare")
    prepared.add_argument("--producer-model", required=True)
    prepared.add_argument("--juror-model", required=True)
    prepared.add_argument("--producer-context-32k-model")
    prepared.add_argument("--juror-context-32k-model")
    prepared.add_argument("--attempt-id")
    for name in ("preflight", "run", "recover", "status"):
        command = commands.add_parser(name)
        command.add_argument("--attempt-id", required=True)
        if name == "run":
            command.add_argument("--human-authorized", action="store_true")
            command.add_argument("--deadline-utc", required=True)
            command.add_argument("--synthetic-article", action="store_true")
        elif name == "recover":
            command.add_argument("--human-authorized", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            value = prepare(
                producer_model=args.producer_model, juror_model=args.juror_model,
                producer_context_32k=args.producer_context_32k_model,
                juror_context_32k=args.juror_context_32k_model,
                attempt_id=args.attempt_id,
            )
        elif args.command == "preflight":
            value = preflight(args.attempt_id)
        elif args.command == "run":
            value = run(args.attempt_id, human_authorized=args.human_authorized,
                        deadline=args.deadline_utc, synthetic_article=args.synthetic_article)
        elif args.command == "recover":
            value = recover(args.attempt_id, human_authorized=args.human_authorized)
        else:
            value = status(args.attempt_id)
    except LocalCycleError as error:
        value = {"status": "blocked", "cause": str(error)}
        print(json.dumps(value, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 2 if args.command in {"run", "recover"} and value.get("status") != "complete" else 0


if __name__ == "__main__":
    raise SystemExit(main())
