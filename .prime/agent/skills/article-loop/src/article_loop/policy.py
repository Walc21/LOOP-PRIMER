"""M10 deterministic decision policy.

The policy has no authority over ``versions/``.  It only revalidates published
M7--M9 evidence, derives a closed decision, publishes that immutable decision,
and records ``DIAGNOSED -> DECIDED`` in the existing durable event log.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from .diagnosis import DiagnosisError, load_history_series, verify_published_diagnosis
from .evaluation import DIMENSIONS
from .state_machine import State
from .store import DurableStore, StoreError
from .synthesis import _inventory, _json, _sha, _walk, tree_hash


POLICY_CONFIG = "config/decision-policy.yaml"
DECISION_SCHEMA = "decision.schema.json"
_ACTIONS = frozenset({
    "PROMOTE", "ARCHIVE_PARETO", "REJECT", "REFOCUS_AND_CONTINUE",
    "CONTINUE_UNCHANGED", "REQUEST_EXTRA_JUDGMENT", "PAUSE", "FINALIZE",
    "ABORT_TECHNICAL",
})
_CLASSIFICATIONS = frozenset({
    "EVOLVING", "LOCAL_PLATEAU", "GLOBAL_PLATEAU", "OSCILLATING",
    "REGRESSING", "INCONCLUSIVE", "TECHNICAL_FAILURE",
})


class PolicyError(RuntimeError):
    """The decision cannot be derived safely from immutable evidence."""


def _canonical(value: Mapping[str, Any]) -> bytes:
    return _json(value)


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contained(root: Path, relative: str, *, exists: bool = False) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise PolicyError("managed path is invalid")
    path = root.joinpath(*Path(relative).parts)
    try:
        path.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise PolicyError("managed path escapes project root") from exc
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise PolicyError("managed path contains a symlink")
    if exists and not path.exists():
        raise PolicyError("managed path is missing")
    return path


def _read_canonical_json(path: Path, label: str) -> dict[str, Any]:
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise PolicyError(f"{label} is not a regular file")
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyError(f"{label} is unreadable") from exc
    if not isinstance(value, dict) or raw != _canonical(value):
        raise PolicyError(f"{label} bytes are not canonical")
    return value


def _validate_schema(root: Path, schema_name: str, value: Mapping[str, Any]) -> None:
    try:
        schema = json.loads((root / "config" / "schemas" / schema_name).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(value)
    except (OSError, json.JSONDecodeError, jsonschema.ValidationError) as exc:
        raise PolicyError(f"{schema_name} validation failed") from exc


def load_policy(root: str | Path) -> tuple[dict[str, Any], str]:
    """Load the exact, closed M10 table and its cryptographic identity."""
    root_path = Path(root).resolve()
    path = _contained(root_path, POLICY_CONFIG, exists=True)
    try:
        raw = path.read_bytes()
        value = yaml.safe_load(raw)
    except (OSError, yaml.YAMLError) as exc:
        raise PolicyError("decision policy cannot be parsed") from exc
    expected_keys = {
        "schema_version", "extra_judgment_limit", "technical_retry_limit",
        "precedence", "classification_actions", "finalization_required_roles",
    }
    if not isinstance(value, dict) or set(value) != expected_keys or value.get("schema_version") != "1.0.0":
        raise PolicyError("decision policy shape is not canonical")
    for name in ("extra_judgment_limit", "technical_retry_limit"):
        number = value.get(name)
        if isinstance(number, bool) or not isinstance(number, int) or number < 0:
            raise PolicyError("decision policy limit is invalid")
    precedence = value.get("precedence")
    expected_precedence = [
        "TECHNICAL_FAILURE", "MATH_HARD_GATE_FAILED", "REGRESSING", "INCONCLUSIVE",
        "LOCAL_PLATEAU", "GLOBAL_PLATEAU", "OSCILLATING", "EVALUATED_CANDIDATE",
    ]
    if precedence != expected_precedence:
        raise PolicyError("decision policy precedence is not canonical")
    mapping = value.get("classification_actions")
    if not isinstance(mapping, dict) or set(mapping) != _CLASSIFICATIONS:
        raise PolicyError("decision policy classifications are incomplete")
    if any(action not in _ACTIONS for action in mapping.values()):
        raise PolicyError("decision policy has an unknown action")
    if mapping != {
        "TECHNICAL_FAILURE": "ABORT_TECHNICAL", "REGRESSING": "REJECT",
        "INCONCLUSIVE": "REQUEST_EXTRA_JUDGMENT", "LOCAL_PLATEAU": "REFOCUS_AND_CONTINUE",
        "GLOBAL_PLATEAU": "PAUSE", "OSCILLATING": "REFOCUS_AND_CONTINUE",
        "EVOLVING": "CONTINUE_UNCHANGED",
    }:
        raise PolicyError("decision policy action table is not canonical")
    if value.get("finalization_required_roles") != ["W22", "W51", "W53"]:
        raise PolicyError("finalization role policy is not canonical")
    return value, hashlib.sha256(raw).hexdigest()


def _candidate(root: Path, candidate_id: str, expected_hash: str) -> tuple[dict[str, Any], Path]:
    candidate_dir = _contained(root, f"versions/challengers/{candidate_id}", exists=True)
    if not candidate_dir.is_dir() or candidate_dir.is_symlink():
        raise PolicyError("challenger directory is unsafe")
    manifest = _read_canonical_json(candidate_dir / "manifest.json", "challenger manifest")
    _validate_schema(root, "candidate-manifest.schema.json", manifest)
    if (
        manifest.get("candidate_kind") != "challenger"
        or manifest.get("candidate_id") != candidate_id
        or manifest.get("content_hash") != expected_hash
        or tree_hash(candidate_dir, exclude={"manifest.json"}) != expected_hash
        or manifest.get("inventory") != _inventory(candidate_dir, {"manifest.json"})
    ):
        raise PolicyError("challenger content binding differs")
    for _, path, info in _walk(candidate_dir):
        if stat.S_IMODE(info.st_mode) & 0o222:
            raise PolicyError("challenger became writable")
        if path.is_symlink():
            raise PolicyError("challenger contains a symlink")
    return manifest, candidate_dir


def _prior_extra_judgments(root: Path, run_id: str) -> int:
    base = _contained(root, f"state/decisions/{run_id}")
    if not base.exists():
        return 0
    if not base.is_dir() or base.is_symlink():
        raise PolicyError("decision history directory is unsafe")
    count = 0
    for path in sorted(base.glob("c*/decision.json")):
        decision = _read_canonical_json(path, "prior decision")
        if decision.get("run_id") == run_id and decision.get("action") == "REQUEST_EXTRA_JUDGMENT":
            count += 1
    return count


def _prior_technical_failures(root: Path, run_id: str) -> int:
    """Count immutable technical checkpoints already requested for this run."""
    base = _contained(root, f"state/decisions/{run_id}")
    if not base.exists():
        return 0
    if not base.is_dir() or base.is_symlink():
        raise PolicyError("decision history directory is unsafe")
    count = 0
    for path in sorted(base.glob("c*/decision.json")):
        decision = _read_canonical_json(path, "prior decision")
        if decision.get("run_id") == run_id and decision.get("action") == "ABORT_TECHNICAL":
            count += 1
    return count


def _finalization_ready(root: Path, run_id: str, cycle_id: int, candidate_id: str, required_roles: list[str]) -> list[str]:
    """Return final-gate IDs only when every finalization prerequisite is local.

    M10 does not rerun a final gate.  A future authorized operation must first
    publish the small final reports in this canonical, content-addressed path.
    """
    base = _contained(root, f"state/final-gates/{run_id}/c{cycle_id:04d}")
    if not base.exists() or not base.is_dir() or base.is_symlink():
        return []
    reports: list[str] = []
    observed_roles: set[str] = set()
    for path in sorted(base.glob("*.json")):
        report = _read_canonical_json(path, "final gate report")
        if (
            report.get("run_id") != run_id or report.get("cycle_id") != cycle_id
            or report.get("candidate_id") != candidate_id or report.get("overall_pass") is not True
            or not isinstance(report.get("report_id"), str) or not report["report_id"]
            or not isinstance(report.get("roles"), list)
        ):
            raise PolicyError("final gate report is invalid")
        observed_roles.update(report["roles"])
        reports.append(report["report_id"])
    if not set(required_roles).issubset(observed_roles):
        return []
    return reports


def _dominates(record: Any) -> bool:
    dimensions = sorted(record.dimension_scores_challenger)
    if not dimensions or not record.correctness_math_pass:
        return False
    deltas = [record.dimension_scores_challenger[d] - record.dimension_scores_champion[d] for d in dimensions]
    return all(delta >= 0 for delta in deltas) and any(delta > 0 for delta in deltas)


def _non_dominated(record: Any) -> bool:
    dimensions = sorted(record.dimension_scores_challenger)
    if not dimensions or not record.correctness_math_pass:
        return False
    deltas = [record.dimension_scores_challenger[d] - record.dimension_scores_champion[d] for d in dimensions]
    return any(delta >= 0 for delta in deltas)


def _score_vector(scores: Mapping[str, Any], label: str) -> dict[str, float]:
    if not isinstance(scores, Mapping) or set(scores) != set(DIMENSIONS):
        raise PolicyError(f"{label} does not contain the eight canonical dimensions")
    result: dict[str, float] = {}
    for dimension in DIMENSIONS:
        value = scores[dimension]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or not 0 <= value <= 5:
            raise PolicyError(f"{label} has an invalid score")
        result[dimension] = float(value)
    return result


def _dominates_scores(left: Mapping[str, float], right: Mapping[str, float]) -> bool:
    return all(left[key] >= right[key] for key in DIMENSIONS) and any(left[key] > right[key] for key in DIMENSIONS)


def pareto_relation(root: str | Path, record: Any) -> dict[str, list[str]]:
    """Compare an eligible challenger with every immutable Pareto reference.

    References are retained even when a later challenger dominates them.  The
    returned relation makes that fact explicit instead of silently deleting
    historical evidence.
    """
    if record.correctness_math_pass is not True:
        raise PolicyError("Pareto comparison requires the mathematical hard gate")
    root_path = Path(root).resolve()
    candidate_scores = _score_vector(record.dimension_scores_challenger, "challenger scores")
    base = _contained(root_path, "versions/pareto")
    if not base.exists():
        return {"dominated_by": [], "dominates": []}
    if not base.is_dir() or base.is_symlink():
        raise PolicyError("Pareto frontier directory is unsafe")
    dominated_by: list[str] = []
    dominates: list[str] = []
    for directory in sorted(base.iterdir(), key=lambda item: item.name):
        if directory.name.startswith("."):
            continue
        if not directory.is_dir() or directory.is_symlink():
            raise PolicyError("Pareto frontier entry is unsafe")
        reference = _read_canonical_json(directory / "reference.json", "Pareto reference")
        identifier = reference.get("candidate_id")
        if not isinstance(identifier, str) or not identifier:
            raise PolicyError("Pareto reference identity is invalid")
        if identifier == record.candidate_id:
            continue
        if reference.get("correctness_math_pass") is not True:
            raise PolicyError("Pareto reference lacks the mathematical hard gate")
        reference_scores = _score_vector(reference.get("scores"), "Pareto reference scores")
        if _dominates_scores(reference_scores, candidate_scores):
            dominated_by.append(identifier)
        if _dominates_scores(candidate_scores, reference_scores):
            dominates.append(identifier)
    return {"dominated_by": dominated_by, "dominates": dominates}


def choose_action(
    record: Any,
    diagnosis: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    prior_extra_judgments: int,
    final_gate_report_ids: list[str],
    frontier_relation: Mapping[str, Any] | None = None,
) -> tuple[str, str | None]:
    """Pure closed disposition table over already revalidated evidence."""
    classification = diagnosis.get("classification")
    if classification not in _CLASSIFICATIONS:
        raise PolicyError("diagnosis classification is not canonical")
    if classification == "TECHNICAL_FAILURE":
        return "ABORT_TECHNICAL", "TECHNICAL_FAILURE"
    if not record.gate_report.get("correctness_math_pass") or not record.correctness_math_pass:
        return "REJECT", "GATE_FAILED"
    if classification == "REGRESSING":
        return "REJECT", "JURY_UNFAVORABLE"
    if classification == "INCONCLUSIVE":
        if prior_extra_judgments < policy["extra_judgment_limit"]:
            return "REQUEST_EXTRA_JUDGMENT", "INCONCLUSIVE_EVALUATION"
        return "PAUSE", "INCONCLUSIVE_LIMIT_REACHED"
    if classification == "LOCAL_PLATEAU":
        return "REFOCUS_AND_CONTINUE", "LOCAL_PLATEAU"
    if classification == "GLOBAL_PLATEAU":
        if final_gate_report_ids:
            return "FINALIZE", "POLICY_SATISFIED"
        return "PAUSE", "TECHNICAL_BLOCK"
    if classification == "OSCILLATING":
        return "REFOCUS_AND_CONTINUE", "OSCILLATING"
    if not record.gate_report.get("overall_pass"):
        return "ABORT_TECHNICAL", "TECHNICAL_FAILURE"
    if record.challenger_eligible and record.overall_outcome == "challenger_favored" and _dominates(record):
        return "PROMOTE", None
    if record.candidate_content_hash == record.base_hash:
        return "CONTINUE_UNCHANGED", "NO_MATERIAL_CHANGE"
    if _non_dominated(record):
        if frontier_relation is not None:
            if set(frontier_relation) != {"dominated_by", "dominates"} or any(
                not isinstance(frontier_relation[key], list) or any(not isinstance(value, str) or not value for value in frontier_relation[key])
                for key in frontier_relation
            ):
                raise PolicyError("Pareto relation is invalid")
            if frontier_relation["dominated_by"]:
                return "REJECT", "PARETO_DOMINATED"
        return "ARCHIVE_PARETO", None
    return "REJECT", "JURY_UNFAVORABLE"


def _decision_id(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload.pop("decision_id", None)
    return f"dec-{_sha(_canonical(payload))[:32]}"


def _decision_for(
    *,
    run_id: str,
    cycle_id: int,
    record: Any,
    diagnosis: Mapping[str, Any],
    policy_hash: str,
    action: str,
    reason_code: str | None,
    final_gate_report_ids: list[str],
    pareto_relation: Mapping[str, Any] | None,
    technical_checkpoint: Mapping[str, Any] | None,
) -> dict[str, Any]:
    candidate_id: str | None = record.candidate_id
    candidate_hash: str | None = record.candidate_content_hash
    gate_id: str | None = record.gate_report.get("report_id")
    verdict_ids: list[str] = list(record.evaluation_report.get("verdict_ids", []))
    diagnosis_id: str | None = diagnosis.get("diagnosis_id")
    if action == "REJECT" and reason_code == "GATE_FAILED":
        verdict_ids = []
    if action in {"PAUSE", "ABORT_TECHNICAL"}:
        candidate_id = candidate_hash = gate_id = diagnosis_id = None
        verdict_ids = []
    value: dict[str, Any] = {
        "schema_version": "1.1.0", "run_id": run_id, "cycle_id": cycle_id,
        "candidate_id": candidate_id, "candidate_content_hash": candidate_hash,
        # The latest DIAGNOSED event is immutable, so this timestamp is stable
        # across retries and participates in the content address.
        "decided_at": diagnosis["created_at"], "action": action,
        "gate_report_id": gate_id, "verdict_ids": verdict_ids,
        "diagnosis_id": diagnosis_id,
        "basis_locators": [
            f"config/decision-policy.yaml",
            f"state/diagnosis/{run_id}/c{cycle_id:04d}/diagnosis.json",
            f"state/evaluations/{run_id}/c{cycle_id:04d}/evaluation.json",
            record.gate_report["report_locator"],
            f"versions/challengers/{record.candidate_id}/manifest.json",
        ],
        "reason_code": reason_code,
        "inconclusive_evaluation_id": (
            record.evaluation_report["evaluation_id"] if action == "REQUEST_EXTRA_JUDGMENT" else None
        ),
        "final_gate_report_ids": final_gate_report_ids if action == "FINALIZE" else [],
        "content_modification_allowed": False, "authorized_by": "M00",
        "policy_config_hash": policy_hash,
        "pareto_relation": dict(pareto_relation) if pareto_relation is not None else None,
        "technical_checkpoint": dict(technical_checkpoint) if technical_checkpoint is not None else None,
    }
    value["decision_id"] = _decision_id(value)
    return value


def _atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=".m10-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if temporary.exists():
            temporary.unlink()


def _publish_decision(root: Path, decision: Mapping[str, Any]) -> tuple[str, str]:
    run_id, cycle_id = decision["run_id"], decision["cycle_id"]
    directory = _contained(root, f"state/decisions/{run_id}/c{cycle_id:04d}")
    directory.mkdir(parents=True, exist_ok=True)
    if directory.is_symlink():
        raise PolicyError("decision publication directory is unsafe")
    path = directory / "decision.json"
    raw = _canonical(decision)
    if path.exists():
        current = _read_canonical_json(path, "published decision")
        if current != dict(decision):
            raise PolicyError("conflicting decision is already published")
    else:
        _atomic_write(path, raw)
        os.chmod(path, 0o444)
        if path.read_bytes() != raw or stat.S_IMODE(path.stat().st_mode) & 0o222:
            raise PolicyError("published decision did not become immutable")
    return f"state/decisions/{run_id}/c{cycle_id:04d}/decision.json", _sha(raw)


def decide(root: str | Path, run_id: str, *, cycle_id: int | None = None) -> dict[str, Any]:
    """Revalidate M7--M9 and publish exactly one M10 Decision."""
    root_path = Path(root).resolve()
    store = DurableStore(root_path)
    events = store.read_events(run_id)
    if not events:
        raise PolicyError("policy requires active state DIAGNOSED")
    if events[-1].get("state_to") == State.DECIDED.value:
        active_cycle = events[-1].get("cycle_id")
        if cycle_id is not None and cycle_id != active_cycle:
            raise PolicyError("policy cycle does not match the active DECIDED state")
        decision, _, _ = load_published_decision(root_path, run_id, active_cycle)
        return decision
    if events[-1].get("state_to") != State.DIAGNOSED.value:
        raise PolicyError("policy requires active state DIAGNOSED")
    active_cycle = events[-1].get("cycle_id")
    if cycle_id is None:
        cycle_id = active_cycle
    if isinstance(cycle_id, bool) or not isinstance(cycle_id, int) or cycle_id != active_cycle:
        raise PolicyError("policy cycle does not match the active DIAGNOSED state")
    try:
        diagnosis, _ = verify_published_diagnosis(root_path, run_id, cycle_id, store=store)
        series = load_history_series(root_path, run_id, cycle_id, store=store)
    except (DiagnosisError, StoreError) as exc:
        raise PolicyError("published M7--M9 evidence is invalid") from exc
    record = series[-1]
    if diagnosis.get("candidate_id") != record.candidate_id or diagnosis.get("candidate_content_hash") != record.candidate_content_hash:
        raise PolicyError("diagnosis candidate binding differs")
    _candidate(root_path, record.candidate_id, record.candidate_content_hash)
    policy, policy_hash = load_policy(root_path)
    final_gates = _finalization_ready(
        root_path, run_id, cycle_id, record.candidate_id, policy["finalization_required_roles"],
    )
    action, reason = choose_action(
        record, diagnosis, policy,
        prior_extra_judgments=_prior_extra_judgments(root_path, run_id),
        final_gate_report_ids=final_gates,
    )
    relation: dict[str, list[str]] | None = None
    if action == "ARCHIVE_PARETO":
        relation = pareto_relation(root_path, record)
        action, reason = choose_action(
            record, diagnosis, policy,
            prior_extra_judgments=_prior_extra_judgments(root_path, run_id),
            final_gate_report_ids=final_gates, frontier_relation=relation,
        )
    technical_checkpoint: dict[str, Any] | None = None
    if action == "ABORT_TECHNICAL":
        prior = _prior_technical_failures(root_path, run_id)
        technical_checkpoint = {
            "attempt": prior + 1,
            "limit": policy["technical_retry_limit"],
            "retry_allowed": prior < policy["technical_retry_limit"],
            "backoff_seconds": 0,
        }
    decision = _decision_for(
        run_id=run_id, cycle_id=cycle_id, record=record, diagnosis=diagnosis,
        policy_hash=policy_hash, action=action, reason_code=reason,
        final_gate_report_ids=final_gates,
        pareto_relation=relation, technical_checkpoint=technical_checkpoint,
    )
    _validate_schema(root_path, DECISION_SCHEMA, decision)
    locator, decision_hash = _publish_decision(root_path, decision)
    event = store.record(
        run_id, State.DECIDED, event_id=f"decision:{decision['decision_id']}",
        idempotency_key=f"decision:{run_id}:c{cycle_id:04d}", actor_id="M00",
        event_type="DECIDED", payload={
            "decision_id": decision["decision_id"], "decision_locator": locator,
            "decision_hash": decision_hash, "action": action,
            "candidate_id": decision["candidate_id"],
            "candidate_content_hash": decision["candidate_content_hash"],
        }, artifact_hashes=[decision_hash],
    )
    if event["payload"].get("decision_hash") != decision_hash:
        raise PolicyError("DECIDED event binding differs from the decision")
    return decision


def load_published_decision(root: str | Path, run_id: str, cycle_id: int) -> tuple[dict[str, Any], str, dict[str, Any]]:
    """Load a Decision and prove that the active DECIDED event binds its bytes."""
    root_path = Path(root).resolve()
    store = DurableStore(root_path)
    events = store.read_events(run_id)
    if not events or events[-1].get("state_to") != State.DECIDED.value or events[-1].get("cycle_id") != cycle_id:
        raise PolicyError("finalizer requires active state DECIDED")
    event = events[-1]
    locator = f"state/decisions/{run_id}/c{cycle_id:04d}/decision.json"
    if event.get("payload", {}).get("decision_locator") != locator:
        raise PolicyError("DECIDED event locator is not canonical")
    decision = _read_canonical_json(_contained(root_path, locator, exists=True), "published decision")
    _validate_schema(root_path, DECISION_SCHEMA, decision)
    digest = _sha(_canonical(decision))
    if (
        event["payload"].get("decision_id") != decision.get("decision_id")
        or event["payload"].get("decision_hash") != digest
        or event.get("artifact_hashes") != [digest]
        or decision.get("run_id") != run_id or decision.get("cycle_id") != cycle_id
        or decision.get("policy_config_hash") != load_policy(root_path)[1]
        or decision.get("decision_id") != _decision_id(decision)
    ):
        raise PolicyError("DECIDED event or policy binding differs")
    return decision, digest, event


__all__ = [
    "PolicyError", "choose_action", "decide", "load_policy", "load_published_decision", "pareto_relation",
]
