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
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
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
SRC = ROOT / ".prime" / "agent" / "skills" / "article-loop" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop.activation import ActivationPlanner, PlanningLimits
from article_loop.blackboard import Blackboard, Impact
from article_loop.budget import BudgetLedger, RunAuthorization
from article_loop.control_center import run_detail
from article_loop.execution import DualExecutionAdapter, DualExecutionController, ExecutionPolicy
from article_loop.inference import InferenceRuntime, ModelRegistry, sha256
from article_loop.inference_backends import (
    OPENAI_CHAT_COMPLETIONS_JSON_SCHEMA, LocalOpenAICompatibleBackend,
)
from article_loop.ingestion import ingest
from article_loop.orchestrator import Orchestrator
from article_loop.state_machine import State
from article_loop.store import DurableStore
from article_loop.synthesis import M7Pipeline, SynthesisError
from article_loop.gates import run_gates


APPROVAL_REFERENCE = "user-authorized-local-loopback-full-cycle-2026-09-06"
ENDPOINT = "http://127.0.0.1:11434/v1/chat/completions"
MODELS_ENDPOINT = "http://127.0.0.1:11434/v1/models"
PROFILE = "local_full_cycle"
PDF_RELATIVE = Path("input/inbox/artigo.pdf")
RUNTIME_RELATIVE = Path("runtime/local-full-cycle")
MAX_WALL_SECONDS = 18_000
MAX_TOKENS = 1_500_000
MAX_CALLS = 96
MAX_CONCURRENCY = 5
SAFE_ATTEMPT = re.compile(r"attempt-[0-9a-f-]{36}\Z")
SAFE_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
WORKER_ROLES = tuple(f"W{department}{worker}" for department in range(1, 6) for worker in range(1, 4))
DEPARTMENTS = tuple(f"S{department}0" for department in range(1, 6))


class LocalCycleError(RuntimeError):
    """A safe stop with an attempt-local diagnostic."""


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
    if not names or any(not isinstance(name, str) or SAFE_MODEL.fullmatch(name) is None for name in names):
        raise LocalCycleError("local models endpoint returned unsafe model identifiers")
    return sorted(set(names))


def _target(target_id: str, model: str, group: str) -> dict[str, Any]:
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
        "context_limit": 8192,
        "max_output_tokens": 1024,
        "independence_group": group,
        "endpoint": ENDPOINT,
        "api_key_env": None,
        "timeout_seconds": 600,
        "fallback_target": None,
        "pricing": None,
    }


def _configure(attempt: Path, producer_model: str, juror_model: str) -> tuple[str, str]:
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
        "max_retries": 1,
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
        "approval_reference": APPROVAL_REFERENCE,
    }
    config["budget"] = {
        **dict(config["budget"]),
        "currency": "USD", "max_run_cost_microunits": 0,
        "limits": limits,
        "profiles": {PROFILE: {"enabled": True, "limits": limits}},
        "default_profile": PROFILE,
    }
    config["inference"] = {
        "schema_version": "1.0.0", "enabled": True,
        "allow_local": True, "allow_remote": False, "allow_paid": False,
        "routing_mode": "deterministic",
        "targets": {
            "producer": _target("producer", producer_model, "local-producer"),
            "juror": _target("juror", juror_model, "local-juror"),
        },
        "role_routes": {
            **{role: {"targets": ["producer"], "required_capabilities": ["language", "structured_output"]} for role in WORKER_ROLES},
            "M00": {"targets": ["juror"], "required_capabilities": ["language", "structured_output"]},
            "S10": {"targets": ["juror"], "required_capabilities": ["language", "structured_output"]},
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


def prepare(*, producer_model: str, juror_model: str, attempt_id: str | None = None) -> dict[str, Any]:
    if producer_model == juror_model:
        raise LocalCycleError("producer and juror must be distinct local models")
    if any(SAFE_MODEL.fullmatch(model) is None for model in (producer_model, juror_model)):
        raise LocalCycleError("model identifier is invalid")
    _require_no_stop(ROOT)
    source, size, digest = _source_pdf()
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
        for relative in ("artifacts", "versions", "workspaces", "state", "reports", "control"):
            (staging / relative).mkdir()
        config_hash, routing_hash = _configure(staging, producer_model, juror_model)
        plan = {
            "schema_version": "1.0.0",
            "attempt_id": attempt_id,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": {"relative_path": PDF_RELATIVE.as_posix(), "size_bytes": size, "sha256": digest},
            "authorization_reference": APPROVAL_REFERENCE,
            "endpoint": ENDPOINT,
            "models": {"producer": producer_model, "juror_meta": juror_model},
            "config_sha256": config_hash,
            "routing_policy_sha256": routing_hash,
            "limits": {"max_wall_seconds": MAX_WALL_SECONDS, "max_tokens": MAX_TOKENS, "max_calls": MAX_CALLS, "max_concurrency": MAX_CONCURRENCY, "max_retries": 1, "max_cycles": 1, "external_cost_microunits": 0},
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
    _require_no_stop(ROOT)
    _require_no_stop(attempt)
    names = _loopback_models()
    selected = plan.get("models", {})
    if not isinstance(selected, dict) or selected.get("producer") not in names or selected.get("juror_meta") not in names:
        raise LocalCycleError("selected local models are not available from loopback service")
    registry = ModelRegistry.from_project(attempt)
    policy = ExecutionPolicy.from_project(attempt)
    if (not registry.enabled or registry.allow_remote or registry.allow_paid
            or any(not target.local or target.paid or target.backend_type != "local_openai_compatible" for target in registry.targets.values())
            or any(policy.layer(department) != "routed" for department in DEPARTMENTS)):
        raise LocalCycleError("attempt configuration does not satisfy local-only policy")
    backend = LocalOpenAICompatibleBackend(
        project_root=attempt,
        structured_output_dialect=OPENAI_CHAT_COMPLETIONS_JSON_SCHEMA,
    )
    backend_status = {target_id: dict(backend.preflight(target)) for target_id, target in registry.targets.items()}
    return {"attempt_id": attempt_id, "models_detected": names, "selected_models": selected, "endpoint": ENDPOINT, "config_sha256": plan["config_sha256"], "routing_policy_sha256": plan["routing_policy_sha256"], "backend": backend_status, "local_only": True}


def _persist_activation(root: Path, run_id: str) -> dict[str, Any]:
    store = DurableStore(root)
    events = store.read_events(run_id)
    base_hash = events[-1]["payload"].get("base_hash")
    if not isinstance(base_hash, str) or len(base_hash) != 64:
        raise LocalCycleError("M3 source state has no canonical base hash")
    board = Blackboard(root)
    claim = board.append(run_id, "claims", {
        "text": "Local-only full-cycle authorization bound to the frozen input; this is provenance, not a mathematical assertion.",
        "type": "provenance", "location": {"page": 1, "section": "source"},
        "dependencies": [], "evidence": ["page:1"], "status": "active",
        "severity": 1, "source_hash": base_hash, "last_validated_cycle": 0,
    })
    impact = Impact(
        claims=(claim["claim_id"],), sections=("source",), equations=(), references=(),
        roles=WORKER_ROLES, severity=1,
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


def _authorize(ledger: BudgetLedger) -> None:
    authorization = RunAuthorization(
        ledger.run_id, PROFILE, ledger.config_hash, None, None, MAX_TOKENS,
        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        APPROVAL_REFERENCE, ledger.routing_policy_hash, 0, "USD",
    )
    ledger.authorize(authorization)


def _checkpoint(orchestrator: Orchestrator, run_id: str, *, reason: str, attempt: Path) -> None:
    result: dict[str, Any] = {"reason": reason, "run_id": run_id}
    try:
        result["orchestration"] = asyncio.run(orchestrator.pause(run_id))
    except Exception as error:
        result["pause_error"] = f"{type(error).__name__}: {error}"
    _atomic_json(attempt / "outcome.json", result)


def run(attempt_id: str) -> dict[str, Any]:
    attempt = _attempt_dir(attempt_id)
    plan = _read_plan(attempt)
    if (attempt / "outcome.json").exists():
        raise LocalCycleError("attempt already has a terminal outcome record; inspect status")
    preflight(attempt_id)
    started = time.monotonic()
    interrupted = {"value": False}

    def on_sigint(_signum: int, _frame: Any) -> None:
        interrupted["value"] = True

    previous = signal.signal(signal.SIGINT, on_sigint)
    source = plan.get("source")
    source_hash = source.get("sha256") if isinstance(source, Mapping) else None
    if not isinstance(source_hash, str) or re.fullmatch(r"[a-f0-9]{64}", source_hash) is None:
        raise LocalCycleError("run plan source hash is invalid")
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
        orchestrator = Orchestrator(attempt, adapter=adapter)
        asyncio.run(orchestrator.bootstrap(attempt / PDF_RELATIVE))
        activation = _persist_activation(attempt, run_id)
        ledger = BudgetLedger.from_project(attempt, run_id, profile=PROFILE)
        _authorize(ledger)
        registry = ModelRegistry.from_project(attempt)
        backend = LocalOpenAICompatibleBackend(
            project_root=attempt,
            structured_output_dialect=OPENAI_CHAT_COMPLETIONS_JSON_SCHEMA,
        )
        runtime = InferenceRuntime(attempt, ledger, registry, {"local_openai_compatible": backend})
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
        pipe = M7Pipeline(attempt)
        synthesis = pipe.synthesize(state["receipts"], run_id=run_id)
        store = DurableStore(attempt)
        pipe.record_synthesis(store, synthesis)
        candidate = pipe.build(synthesis, attempt / "versions/champion/v0000")
        pipe.record_candidate(store, candidate)
        report = run_gates(attempt / "versions/challengers" / candidate["candidate_id"])
        try:
            pipe.record_gates(store, report["report_locator"])
        except SynthesisError as error:
            # A failed hard scientific gate is canonical evidence.  It cannot
            # advance to jury/decision without fabricated math verification.
            outcome = {"status": "gates_failed", "run_id": run_id, "candidate_id": candidate["candidate_id"], "gate_report_locator": report["report_locator"], "gate_report_hash": report["report_hash"], "cause": str(error), "state": DurableStore(attempt).snapshot(run_id)["state"], "inspection": "python3 scripts/local_loopback_full_cycle.py status --attempt-id " + attempt_id}
            _atomic_json(attempt / "outcome.json", outcome)
            return outcome
        raise LocalCycleError("unexpected M7 gate pass requires routed M8 continuation implementation")
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
    prepared.add_argument("--attempt-id")
    for name in ("preflight", "run", "status"):
        command = commands.add_parser(name)
        command.add_argument("--attempt-id", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            value = prepare(producer_model=args.producer_model, juror_model=args.juror_model, attempt_id=args.attempt_id)
        elif args.command == "preflight":
            value = preflight(args.attempt_id)
        elif args.command == "run":
            value = run(args.attempt_id)
        else:
            value = status(args.attempt_id)
    except LocalCycleError as error:
        value = {"status": "blocked", "cause": str(error)}
        print(json.dumps(value, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
