"""Deterministic, local, progress stagnation detection and diagnosis (M9).

M9 consumes the canonical evaluation from M8 (state/evaluations/<run_id>/c<cycle>/)
and historical cycle records to produce a content-addressed Diagnosis and transition
the state machine from EVALUATED to DIAGNOSED.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .activation import CHILDREN, DEPARTMENTS
from .blackboard import Blackboard, BlackboardError
from .evaluation import (
    DIMENSIONS,
    EVALUATION_MANIFEST_SCHEMA,
    EvaluationError,
    _revalidate_published_evaluation,
    _validate_schema,
)
from .gates import verify_gate_report
from .state_machine import State
from .store import DurableStore
from .synthesis import (
    _contained,
    _fsync,
    _fsync_tree_dirs,
    _json,
    _regular,
    _sha,
    _walk,
    tree_hash,
)

SCHEMA_VERSION = "1.1.0"
DIAGNOSIS_SCHEMA = "diagnosis.schema.json"
DIAGNOSIS_MANIFEST_SCHEMA = "diagnosis-manifest.schema.json"

VALID_CLASSIFICATIONS = frozenset({
    "EVOLVING",
    "LOCAL_PLATEAU",
    "GLOBAL_PLATEAU",
    "OSCILLATING",
    "REGRESSING",
    "INCONCLUSIVE",
    "TECHNICAL_FAILURE",
})

DEFAULT_WINDOW_SIZE = 3
DEFAULT_MDE = 0.25  # Minimum Detectable Effect on 0..5 scale


class DiagnosisError(RuntimeError):
    """Raised when diagnosis preconditions, schemas, or classification invariants fail."""


def _read_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        _regular(path)
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise DiagnosisError(f"cannot read canonical JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise DiagnosisError(f"canonical JSON must be an object: {path.name}")
    return value, raw


def _write_synced_file(path: Path, data: bytes) -> None:
    """Write binary data to path, flush and fsync file descriptor."""
    with path.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _managed_directory(root: Path, relative: str, *, create: bool) -> Path:
    """Return a canonical real output directory without traversing symlinks."""
    try:
        path = _contained(root, relative)
        if path.exists() or path.is_symlink():
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                raise DiagnosisError("managed diagnosis directory is not a real directory")
        elif create:
            path.mkdir(parents=True)
        if path.exists() and path.resolve().relative_to(root) != Path(relative):
            raise DiagnosisError("managed diagnosis directory is not canonical")
        return path
    except DiagnosisError:
        raise
    except Exception as exc:
        raise DiagnosisError("managed diagnosis directory is unsafe") from exc


def _harden_read_only(tree: Path) -> None:
    """Set files to 0444 and directories to 0555 before publishing."""
    for rel, path, sinfo in _walk(tree):
        if stat.S_ISDIR(sinfo.st_mode):
            os.chmod(path, 0o555)
        elif stat.S_ISREG(sinfo.st_mode):
            os.chmod(path, 0o444)
    os.chmod(tree, 0o555)


def _cleanup_staging(staging_path: Path) -> None:
    """Clean up staging directory, restoring permissions if hardened, without suppressing errors."""
    if not staging_path.exists():
        return
    for root_dir, dirs, files in os.walk(staging_path, topdown=False):
        for fname in files:
            fpath = Path(root_dir) / fname
            try:
                os.chmod(fpath, 0o600)
            except OSError:
                pass
        for dname in dirs:
            dpath = Path(root_dir) / dname
            try:
                os.chmod(dpath, 0o700)
            except OSError:
                pass
    try:
        os.chmod(staging_path, 0o700)
    except OSError:
        pass

    def _onerror(func: Any, path: str, exc_info: Any) -> None:
        try:
            os.chmod(path, 0o700)
            func(path)
        except OSError:
            pass

    shutil.rmtree(staging_path, onerror=_onerror)
    if staging_path.exists():
        try:
            os.chmod(staging_path, 0o700)
        except OSError:
            pass
        shutil.rmtree(staging_path)


@dataclass(frozen=True)
class CycleRecord:
    """Structured record of an evaluated cycle."""
    cycle_id: int
    candidate_id: str
    candidate_content_hash: str
    base_hash: str
    gate_report: dict[str, Any]
    evaluation_report: dict[str, Any]
    meta_verdict: dict[str, Any]
    verdicts: list[dict[str, Any]]
    activation_map: dict[str, Any] | None
    dimension_scores_challenger: dict[str, float]
    dimension_scores_champion: dict[str, float]
    correctness_math_pass: bool
    overall_outcome: str
    challenger_eligible: bool
    active_issues: list[dict[str, Any]]
    gate_report_hash: str = ""
    evaluation_report_hash: str = ""


def _history_hash(series: Sequence[CycleRecord]) -> str:
    """Bind every non-derived classification input across the effective history."""
    return _sha(_json([
        {
            "cycle_id": record.cycle_id,
            "candidate_id": record.candidate_id,
            "candidate_content_hash": record.candidate_content_hash,
            "base_hash": record.base_hash,
            "gate_report_hash": record.gate_report_hash,
            "evaluation_report_hash": record.evaluation_report_hash,
            "activation_map": record.activation_map,
            "active_issues": record.active_issues,
        }
        for record in series
    ]))


_DEPARTMENT_DIMENSIONS = {
    "S10": ("logical_coherence",),
    "S20": ("correctness_math", "proof_completeness"),
    "S30": ("scientific_contribution",),
    "S40": ("semantic_precision", "clarity"),
    "S50": ("format_integrity", "reproducibility"),
}

_DEPARTMENT_PRIMARY_ROLE = {
    "S10": "W12",
    "S20": "W22",
    "S30": "W31",
    "S40": "W42",
    "S50": "W51",
}

_ISSUE_SEVERITY = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def _validate_classification_parameters(window_size: int, mde: float) -> tuple[int, float]:
    if isinstance(window_size, bool) or not isinstance(window_size, int) or window_size <= 0:
        raise DiagnosisError("window_size must be a positive integer")
    if isinstance(mde, bool) or not isinstance(mde, (int, float)) or not math.isfinite(float(mde)):
        raise DiagnosisError("mde must be a finite number")
    normalized_mde = float(mde)
    if not 0.0 <= normalized_mde <= 5.0:
        raise DiagnosisError("mde must be between 0 and 5")
    return window_size, normalized_mde


def _validate_activation_map(value: Mapping[str, Any], cycle_id: int) -> dict[str, Any]:
    result = dict(value)
    if "roles" in result:
        if result.get("cycle_id") != cycle_id or not isinstance(result.get("roles"), list):
            raise DiagnosisError(f"cycle c{cycle_id:04d} activation map identity is invalid")
        roles = result["roles"]
        role_ids = [entry.get("role_id") for entry in roles if isinstance(entry, Mapping)]
        canonical_roles = {"M00", *DEPARTMENTS, *(role for children in CHILDREN.values() for role in children)}
        if (
            len(roles) != len(canonical_roles)
            or len(role_ids) != len(roles)
            or set(role_ids) != canonical_roles
            or any(entry.get("mode") not in {"RUN", "CHECK", "SHIFT", "FREEZE"} for entry in roles)
        ):
            raise DiagnosisError(f"cycle c{cycle_id:04d} activation map roles are invalid")
        return result
    for role_id, entry in result.items():
        if role_id not in {"M00", *DEPARTMENTS, *(role for children in CHILDREN.values() for role in children)}:
            raise DiagnosisError(f"cycle c{cycle_id:04d} activation map contains unknown role")
        if not isinstance(entry, Mapping) or entry.get("mode") not in {"RUN", "CHECK", "SHIFT", "FREEZE"}:
            raise DiagnosisError(f"cycle c{cycle_id:04d} activation map entry is invalid")
    return result


def _active_roles(activation_map: Mapping[str, Any] | None) -> set[str]:
    if activation_map is None:
        return {role for children in CHILDREN.values() for role in children}
    if isinstance(activation_map.get("roles"), list):
        return {
            str(entry["role_id"])
            for entry in activation_map["roles"]
            if isinstance(entry, Mapping) and entry.get("mode") != "FREEZE"
        }
    return {
        str(role_id)
        for role_id, entry in activation_map.items()
        if isinstance(entry, Mapping) and entry.get("mode") != "FREEZE"
    }


def _active_departments(record: CycleRecord) -> tuple[str, ...]:
    roles = _active_roles(record.activation_map)
    return tuple(department for department in DEPARTMENTS if any(role in roles for role in CHILDREN[department]))


def _active_dimensions(record: CycleRecord) -> tuple[str, ...]:
    active = set(_active_departments(record))
    return tuple(
        dimension
        for department in DEPARTMENTS
        if department in active
        for dimension in _DEPARTMENT_DIMENSIONS[department]
    )


def _issue_severity_total(issues: Sequence[Mapping[str, Any]]) -> int:
    total = 0
    for issue in issues:
        severity = issue.get("severity", 0)
        if isinstance(severity, str):
            if severity not in _ISSUE_SEVERITY:
                raise DiagnosisError("issue severity is not canonical")
            total += _ISSUE_SEVERITY[severity]
        elif isinstance(severity, int) and not isinstance(severity, bool) and severity >= 0:
            total += severity
        else:
            raise DiagnosisError("issue severity is invalid")
    return total


def load_history_series(
    root: Path,
    run_id: str,
    target_cycle_id: int,
    *,
    store: DurableStore | None = None,
) -> list[CycleRecord]:
    """Load and revalidate closed cycle records from cycle 0 up to target_cycle_id.

    Revalidates integrity of each cycle and strictly enforces:
      - Continuous cycle sequence (0, 1, ..., target_cycle_id)
      - Run ID matching
      - Zero look-ahead: cycles > target_cycle_id are ignored/forbidden
      - Artifact presence and hash verification
    """
    if isinstance(target_cycle_id, bool) or not isinstance(target_cycle_id, int) or target_cycle_id < 0:
        raise DiagnosisError("target_cycle_id must be a non-negative integer")
    root = Path(root).resolve()
    active_store = store or DurableStore(root)
    try:
        events = active_store.read_events(run_id)
        issue_records = Blackboard(root).read(run_id, "issues")
    except (BlackboardError, OSError, ValueError) as exc:
        raise DiagnosisError("cannot reconstitute canonical run history") from exc

    evaluated_events: dict[int, dict[str, Any]] = {}
    for event in events:
        if event.get("event_type") == "EVALUATED" and event.get("state_to") == State.EVALUATED.value:
            cid = event.get("cycle_id")
            if cid in evaluated_events:
                raise DiagnosisError(f"duplicate EVALUATED event for cycle c{cid:04d}")
            evaluated_events[cid] = event

    records: list[CycleRecord] = []
    for cid in range(target_cycle_id + 1):
        eval_dir = root / "state" / "evaluations" / run_id / f"c{cid:04d}"
        if not eval_dir.is_dir():
            label = "target cycle" if cid == target_cycle_id else "historical series gap"
            raise DiagnosisError(f"{label}: cycle c{cid:04d} evaluation missing")

        manifest_path = eval_dir / "manifest.json"
        try:
            manifest, raw_manifest = _read_json(manifest_path)
            _validate_schema(root, EVALUATION_MANIFEST_SCHEMA, manifest)
        except (DiagnosisError, EvaluationError) as exc:
            raise DiagnosisError(f"cycle c{cid:04d} evaluation manifest is invalid") from exc
        if raw_manifest != _json(manifest):
            raise DiagnosisError(f"cycle c{cid:04d} evaluation manifest bytes are not canonical")
        candidate_id = manifest.get("candidate_id")
        gate_report_locator = manifest.get("gate_report_locator")
        if not isinstance(candidate_id, str) or not candidate_id or not isinstance(gate_report_locator, str) or not gate_report_locator:
            raise DiagnosisError(f"cycle c{cid:04d} evaluation manifest identity is incomplete")

        try:
            eval_report, recovered_hashes = _revalidate_published_evaluation(
                root,
                eval_dir,
                expected_run_id=run_id,
                expected_cycle_id=cid,
                expected_candidate_id=candidate_id,
                expected_gate_report_locator=gate_report_locator,
            )
            gate_report = verify_gate_report(root, gate_report_locator, require_candidate_built=False)
            meta_verdict, _ = _read_json(eval_dir / "meta-verdict.json")
            verdicts = [_read_json(path)[0] for path in sorted((eval_dir / "verdicts").glob("*.json"))]
        except Exception as exc:
            raise DiagnosisError(f"cycle c{cid:04d} evaluation integrity verification failed") from exc

        evaluated_event = evaluated_events.get(cid)
        if evaluated_event is None:
            raise DiagnosisError(f"cycle c{cid:04d} has no canonical EVALUATED event")
        event_payload = evaluated_event.get("payload", {})
        canonical_eval_locator = f"state/evaluations/{run_id}/c{cid:04d}/evaluation.json"
        if (
            event_payload.get("candidate_id") != candidate_id
            or event_payload.get("candidate_content_hash") != eval_report.get("candidate_content_hash")
            or event_payload.get("candidate_hash") != gate_report.get("candidate_hash")
            or event_payload.get("base_hash") != eval_report.get("base_hash")
            or event_payload.get("evaluation_id") != eval_report.get("evaluation_id")
            or event_payload.get("comparison_id") != eval_report.get("comparison_id")
            or event_payload.get("overall_outcome") != eval_report.get("overall_outcome")
            or event_payload.get("challenger_eligible") != eval_report.get("challenger_eligible")
            or event_payload.get("verdict_ids") != eval_report.get("verdict_ids")
            or event_payload.get("evaluation_locator") != canonical_eval_locator
            or evaluated_event.get("artifact_hashes") != recovered_hashes
        ):
            raise DiagnosisError(f"cycle c{cid:04d} EVALUATED event binding differs from published evidence")

        activation_map: dict[str, Any] | None = None
        activation_locator = f"state/blackboard/{run_id}/activation-c{cid:04d}.json"
        activation_path = _contained(root, activation_locator)
        if activation_path.exists():
            activation_value, _ = _read_json(activation_path)
            activation_map = _validate_activation_map(activation_value, cid)

        active_issues: list[dict[str, Any]] = []
        for issue in issue_records:
            issue_id = issue.get("record_id") or issue.get("issue_id")
            issue_status = issue.get("status")
            if not isinstance(issue_id, str) or not issue_id:
                raise DiagnosisError("blackboard issue is missing a canonical identifier")
            if not isinstance(issue_status, str) or not issue_status:
                raise DiagnosisError("blackboard issue has invalid status")
            issue_cycle = issue.get("cycle_id")
            if isinstance(issue_cycle, bool) or not isinstance(issue_cycle, int) or issue_cycle < 0:
                raise DiagnosisError("blackboard issue has invalid cycle_id")
            if issue.get("run_id", run_id) != run_id:
                raise DiagnosisError("blackboard issue mixes run identities")
            if issue_cycle <= cid and issue_status in {"active", "open", "reopened"}:
                _issue_severity_total([issue])
                active_issues.append(dict(issue))

        consistent_ids = {
            verdict_id
            for item in eval_report["juror_evaluations"]
            if item["consistent"]
            for verdict_id in (item["verdict_ab_id"], item["verdict_ba_id"])
        }
        scores_challenger: dict[str, list[float]] = {dimension: [] for dimension in DIMENSIONS}
        scores_champion: dict[str, list[float]] = {dimension: [] for dimension in DIMENSIONS}
        for verdict in verdicts:
            if verdict["verdict_id"] not in consistent_ids:
                continue
            # dimension_scores and correctness_math_pass are always indexed by
            # neutral identity [A, B], independently of presentation_order.
            for dimension in DIMENSIONS:
                scores_champion[dimension].append(float(verdict["dimension_scores"][0][dimension]))
                scores_challenger[dimension].append(float(verdict["dimension_scores"][1][dimension]))
        avg_challenger = {
            dimension: sum(values) / len(values) if values else 0.0
            for dimension, values in scores_challenger.items()
        }
        avg_champion = {
            dimension: sum(values) / len(values) if values else 0.0
            for dimension, values in scores_champion.items()
        }

        records.append(CycleRecord(
            cycle_id=cid,
            candidate_id=candidate_id,
            candidate_content_hash=eval_report["candidate_content_hash"],
            base_hash=eval_report["base_hash"],
            gate_report=gate_report,
            evaluation_report=eval_report,
            meta_verdict=meta_verdict,
            verdicts=verdicts,
            activation_map=activation_map,
            dimension_scores_challenger=avg_challenger,
            dimension_scores_champion=avg_champion,
            correctness_math_pass=eval_report["correctness_math_pass"],
            overall_outcome=eval_report["overall_outcome"],
            challenger_eligible=eval_report["challenger_eligible"],
            active_issues=active_issues,
            gate_report_hash=manifest["gate_report_hash"],
            evaluation_report_hash=manifest["evaluation_report_hash"],
        ))

    return records


def classify_cycle_progress(
    series: Sequence[CycleRecord],
    *,
    window_size: int = DEFAULT_WINDOW_SIZE,
    mde: float = DEFAULT_MDE,
) -> tuple[str, list[str], str, list[str]]:
    """Determine the deterministic progress classification and explanation signals.

    Returns:
      (classification, signals, recommended_mode, focus_areas)

    Strict Precedence Order:
      1. TECHNICAL_FAILURE
      2. REGRESSING on a lost mathematical hard gate
      3. INCONCLUSIVE (insufficient window, jury noise / all divergent)
      4. REGRESSING (core dimension regression or worsened severity)
      5. OSCILLATING (score flip-flops or reopened issues over window)
      6. LOCAL_PLATEAU (full window, global delta < MDE, localized bottleneck)
      7. GLOBAL_PLATEAU (full window, global delta < MDE, no localized bottleneck)
      8. EVOLVING (material gain >= MDE, no regression)
    """
    window_size, mde = _validate_classification_parameters(window_size, mde)
    if not series:
        return "INCONCLUSIVE", ["empty_series"], "CHECK", ["all"]
    cycle_ids = [record.cycle_id for record in series]
    if any(isinstance(cycle_id, bool) or not isinstance(cycle_id, int) or cycle_id < 0 for cycle_id in cycle_ids):
        raise DiagnosisError("series contains an invalid cycle_id")
    if any(current_id != prior_id + 1 for prior_id, current_id in zip(cycle_ids, cycle_ids[1:])):
        raise DiagnosisError("series cycle sequence is not contiguous")

    current = series[-1]
    signals: list[str] = []
    signals.append(f"cycle_id:{current.cycle_id}")
    signals.append(f"candidate_id:{current.candidate_id}")
    signals.append(f"window_size_configured:{window_size}")
    effective_window = list(series[-min(len(series), window_size):])
    signals.append(f"effective_window_length:{len(effective_window)}")

    # 1. Check TECHNICAL_FAILURE
    # Look for technical gate failures or unmeasured article quality
    gate_failures: list[str] = []
    for g in current.gate_report.get("gates", []):
        if not g.get("passed"):
            gate_failures.append(g.get("gate_id", "unknown_gate"))

    # If any gate failed, inspect if it is technical vs scientific math
    technical_gates = {
        "contracts_state", "source_provenance", "latex_compile_safe", "render",
        "pdf_valid", "references_labels", "asset_inventory", "local_budget",
        "manifest_integrity", "forbidden_metatext",
    }
    has_technical_failure = any(gid in technical_gates for gid in gate_failures)
    if has_technical_failure:
        signals.append(f"technical_gate_failures:{','.join(sorted(gate_failures))}")
        return "TECHNICAL_FAILURE", signals, "CHECK", ["infrastructure"]

    if (
        current.gate_report.get("overall_pass") is False
        and current.gate_report.get("correctness_math_pass") is not False
        and "correctness_math" not in gate_failures
    ):
        signals.append("gate_report_overall_pass_false_non_math")
        return "TECHNICAL_FAILURE", signals, "CHECK", ["infrastructure"]

    # A mathematical hard-gate loss is never masked by an inconclusive jury.
    if not current.correctness_math_pass or not current.gate_report.get("correctness_math_pass"):
        signals.append("math_hard_gate_lost")
        return "REGRESSING", signals, "CHECK", ["section:proof", "theorem"]

    # 2. Check INCONCLUSIVE
    # Check if jury was inconclusive or divergent
    consistent_jurors = current.evaluation_report.get("consistent_jurors", 0)
    if consistent_jurors < 2 or current.overall_outcome == "inconclusive":
        signals.append(f"jury_inconclusive:consistent_count={consistent_jurors}")
        if current.meta_verdict.get("vetoed"):
            signals.append(f"meta_reviewer_veto:{current.meta_verdict.get('veto_reason')}")
        return "INCONCLUSIVE", signals, "CHECK", ["jury_divergence"]

    # 3. Check remaining REGRESSING signals
    active_dimensions = _active_dimensions(current)
    if not active_dimensions:
        signals.append("all_specialist_dimensions_frozen")
        return "INCONCLUSIVE", signals, "CHECK", ["activation"]

    # B. Score regression on correctness_math or core dimensions
    math_delta = current.dimension_scores_challenger.get("correctness_math", 0) - current.dimension_scores_champion.get("correctness_math", 0)
    if "correctness_math" in active_dimensions and math_delta < -0.01:
        signals.append(f"math_score_regressed:{math_delta:.2f}")
        return "REGRESSING", signals, "CHECK", ["correctness_math"]

    # C. Strong regression in multiple dimensions (e.g. champion favored)
    if current.overall_outcome == "champion_favored":
        signals.append("champion_favored_by_jury")
        # Identify which dimensions dropped most
        dropped_dims = [
            d for d in active_dimensions
            if (current.dimension_scores_challenger.get(d, 0) - current.dimension_scores_champion.get(d, 0)) < -mde
        ]
        if dropped_dims:
            signals.append(f"regressed_dimensions:{','.join(sorted(dropped_dims))}")
            return "REGRESSING", signals, "CHECK", dropped_dims or ["all"]

    # D. Issue severity worsened
    if len(effective_window) >= 2:
        prev = effective_window[-2]
        sev_curr = _issue_severity_total(current.active_issues)
        sev_prev = _issue_severity_total(prev.active_issues)
        if sev_curr > sev_prev + 5:  # significant severity spike
            signals.append(f"issue_severity_increased:{sev_prev}->{sev_curr}")
            return "REGRESSING", signals, "CHECK", ["issues"]

    # 4. Check OSCILLATING (requires window >= 2)
    if len(effective_window) >= 2:
        reopened_issue_ids = sorted({
            str(issue.get("record_id") or issue.get("issue_id"))
            for record in effective_window
            for issue in record.active_issues
            if issue.get("status") == "reopened" and issue.get("cycle_id") == record.cycle_id
        })
        if reopened_issue_ids:
            signals.append(f"issues_reopened:{','.join(reopened_issue_ids)}")
            return "OSCILLATING", signals, "SHIFT", ["issues", "stabilization"]

        # Check for alternating trade-offs or reversals in dimensions
        reversals = 0
        for d in _active_dimensions(current):
            deltas: list[float] = []
            for i in range(len(effective_window)):
                c_rec = effective_window[i]
                d_delta = c_rec.dimension_scores_challenger.get(d, 0) - c_rec.dimension_scores_champion.get(d, 0)
                deltas.append(d_delta)
            # Check every adjacent pair in the effective window, not only the
            # most recent pair, and ignore sub-MDE numerical noise.
            if any(
                left * right < 0 and min(abs(left), abs(right)) >= mde
                for left, right in zip(deltas, deltas[1:])
            ):
                reversals += 1
                signals.append(f"oscillation_in_dimension:{d}")

        if reversals >= 2:
            signals.append(f"multiple_reversals_detected:{reversals}")
            return "OSCILLATING", signals, "SHIFT", ["stabilization"]

    # 5. Check EVOLVING (material validated gain in current cycle)
    # Calculate overall score delta for challenger vs champion in current cycle
    score_deltas = {
        d: current.dimension_scores_challenger.get(d, 0) - current.dimension_scores_champion.get(d, 0)
        for d in active_dimensions
    }
    avg_delta = sum(score_deltas.values()) / len(score_deltas)
    signals.append(f"average_score_delta:{avg_delta:+.2f}")

    if (
        current.challenger_eligible
        and current.overall_outcome == "challenger_favored"
        and avg_delta >= mde
        and current.correctness_math_pass
    ):
        signals.append(f"material_gain_validated:delta={avg_delta:.2f}>={mde:.2f}")
        return "EVOLVING", signals, "RUN", ["continuation"]

    # 6. Check PLATEAU (Local vs Global)
    # Stagnation / Plateau CANNOT be declared with an incomplete window!
    # If the window is smaller than required window_size and no evolving/regressing, return INCONCLUSIVE
    if len(effective_window) < window_size:
        signals.append(f"insufficient_window_for_plateau:{len(effective_window)}<{window_size}")
        return "INCONCLUSIVE", signals, "CHECK", ["insufficient_history"]

    # Full window available: check if all cycles in window have |avg_delta| < mde
    window_deltas = []
    for c_rec in effective_window:
        c_deltas = [
            c_rec.dimension_scores_challenger.get(d, 0) - c_rec.dimension_scores_champion.get(d, 0)
            for d in _active_dimensions(c_rec)
        ]
        window_deltas.append(sum(c_deltas) / len(c_deltas))

    is_stagnant = all(abs(d) < mde for d in window_deltas)
    signals.append(f"window_average_deltas:{[round(x, 2) for x in window_deltas]}")

    if is_stagnant:
        # Differentiate between LOCAL_PLATEAU and GLOBAL_PLATEAU
        # Inspect departmental / dimension bottlenecks
        dept_avg_scores: dict[str, float] = {}
        active_departments = _active_departments(current)
        active_roles = _active_roles(current.activation_map)
        for dept in active_departments:
            dims = _DEPARTMENT_DIMENSIONS[dept]
            scores = [current.dimension_scores_challenger.get(d, 0) for d in dims]
            dept_avg_scores[dept] = sum(scores) / len(scores) if scores else 0.0

        # Check if there is a single clear lagging department (e.g. score < 3.0 or significantly lower than others)
        sorted_depts = sorted(dept_avg_scores.items(), key=lambda kv: kv[1])
        lowest_dept, lowest_score = sorted_depts[0]
        second_score = sorted_depts[1][1] if len(sorted_depts) > 1 else 5.0

        signals.append(f"department_scores:{json.dumps(dept_avg_scores, sort_keys=True)}")

        if lowest_score < 3.0 and second_score >= 3.0:
            signals.append(f"localized_departmental_bottleneck:{lowest_dept}={lowest_score:.2f}")
            # Map department to primary specialist role
            preferred_role = _DEPARTMENT_PRIMARY_ROLE[lowest_dept]
            focus_role = preferred_role if preferred_role in active_roles else next(
                (role for role in CHILDREN[lowest_dept] if role in active_roles),
                preferred_role,
            )
            return "LOCAL_PLATEAU", signals, "SHIFT", [lowest_dept, focus_role]

        # No single localized bottleneck -> GLOBAL_PLATEAU
        signals.append("global_stagnation_across_all_departments")
        return "GLOBAL_PLATEAU", signals, "SHIFT", ["general_refocus"]

    # A score direction that was not validated by the M8 eligibility and
    # challenger-favored outcome may never be promoted to EVOLVING.
    if avg_delta >= 0.0:
        signals.append("positive_direction_not_validated_by_jury")
        return "INCONCLUSIVE", signals, "CHECK", ["unvalidated_direction"]
    return "INCONCLUSIVE", signals, "CHECK", ["ambiguous_direction"]


def _verify_diagnosis_classification(
    diagnosis: Mapping[str, Any],
    series: Sequence[CycleRecord],
) -> None:
    """Recompute the diagnosis decision from its committed source parameters."""
    classification, signals, recommended_mode, focus = classify_cycle_progress(
        series,
        window_size=diagnosis.get("window_size"),
        mde=diagnosis.get("mde"),
    )
    if (
        diagnosis.get("classification") != classification
        or diagnosis.get("signals") != signals
        or diagnosis.get("recommended_mode") != recommended_mode
        or diagnosis.get("focus") != focus
    ):
        raise DiagnosisError("published diagnosis classification differs from recomputed history")


def _diagnosis_id_for(diagnosis_without_id: Mapping[str, Any]) -> str:
    body = dict(diagnosis_without_id)
    body.pop("diagnosis_id", None)
    return f"diag-{_sha(_json(body))}"


def _revalidate_published_diagnosis(
    root: Path,
    diag_dir: Path,
    *,
    expected_run_id: str,
    expected_cycle_id: int,
    expected_candidate_id: str,
    expected_candidate_content_hash: str | None = None,
    expected_base_hash: str | None = None,
    expected_gate_report_hash: str | None = None,
    expected_evaluation_report_hash: str | None = None,
    expected_history_hash: str | None = None,
    expected_window_size: int | None = None,
    expected_mde: float | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Revalidate a canonical diagnosis and all manifest bindings."""
    root = Path(root).resolve()
    canonical_dir = f"state/diagnosis/{expected_run_id}/c{expected_cycle_id:04d}"
    try:
        relative_dir = diag_dir.resolve().relative_to(root).as_posix()
    except (OSError, ValueError) as exc:
        raise DiagnosisError("published diagnosis directory escapes project root") from exc
    if relative_dir != canonical_dir:
        raise DiagnosisError("published diagnosis directory is not canonical")
    _contained(root, canonical_dir, True)

    manifest_path = diag_dir / "manifest.json"
    diag_path = diag_dir / "diagnosis.json"

    if not manifest_path.exists() or not diag_path.exists():
        raise DiagnosisError("published diagnosis directory missing core artifacts")

    manifest, raw_man = _read_json(manifest_path)
    diagnosis, raw_diag = _read_json(diag_path)

    try:
        _validate_schema(root, DIAGNOSIS_MANIFEST_SCHEMA, manifest)
        _validate_schema(root, DIAGNOSIS_SCHEMA, diagnosis)
    except EvaluationError as exc:
        raise DiagnosisError("published diagnosis schema validation failed") from exc
    if raw_man != _json(manifest) or raw_diag != _json(diagnosis):
        raise DiagnosisError("published diagnosis JSON bytes are not canonical")

    if (
        manifest.get("run_id") != expected_run_id
        or manifest.get("cycle_id") != expected_cycle_id
        or manifest.get("candidate_id") != expected_candidate_id
    ):
        raise DiagnosisError("published diagnosis manifest does not match active run/cycle/candidate")

    if (
        diagnosis.get("run_id") != expected_run_id
        or diagnosis.get("cycle_id") != expected_cycle_id
        or diagnosis.get("candidate_id") != expected_candidate_id
    ):
        raise DiagnosisError("published diagnosis does not match active run/cycle/candidate")

    if (
        manifest.get("diagnosis_id") != diagnosis.get("diagnosis_id")
        or manifest.get("classification") != diagnosis.get("classification")
        or manifest.get("created_at") != diagnosis.get("created_at")
        or manifest.get("gate_report_hash") != diagnosis.get("gate_report_hash")
        or manifest.get("evaluation_report_hash") != diagnosis.get("evaluation_report_hash")
    ):
        raise DiagnosisError("published diagnosis manifest semantic binding differs")
    if diagnosis.get("diagnosis_id") != _diagnosis_id_for(diagnosis):
        raise DiagnosisError("published diagnosis_id is not content-addressed")
    if expected_candidate_content_hash is not None and diagnosis.get("candidate_content_hash") != expected_candidate_content_hash:
        raise DiagnosisError("published diagnosis candidate_content_hash differs")
    if expected_base_hash is not None and diagnosis.get("base_hash") != expected_base_hash:
        raise DiagnosisError("published diagnosis base_hash differs")
    if expected_gate_report_hash is not None and manifest.get("gate_report_hash") != expected_gate_report_hash:
        raise DiagnosisError("published diagnosis GateReport hash differs")
    if expected_evaluation_report_hash is not None and manifest.get("evaluation_report_hash") != expected_evaluation_report_hash:
        raise DiagnosisError("published diagnosis EvaluationReport hash differs")
    if expected_history_hash is not None and diagnosis.get("history_hash") != expected_history_hash:
        raise DiagnosisError("published diagnosis history hash differs")
    if expected_window_size is not None and diagnosis.get("window_size") != expected_window_size:
        raise DiagnosisError("published diagnosis window_size differs from requested classification")
    if expected_mde is not None and diagnosis.get("mde") != expected_mde:
        raise DiagnosisError("published diagnosis mde differs from requested classification")

    if manifest.get("diagnosis_hash") != _sha(raw_diag):
        raise DiagnosisError("published manifest diagnosis_hash mismatch")

    current_tree_hash = tree_hash(diag_dir, exclude={"manifest.json"})
    if manifest.get("tree_content_hash") != current_tree_hash:
        raise DiagnosisError("published diagnosis tree content hash mismatch")

    entries = _walk(diag_dir)
    if {relative for relative, _, _ in entries} != {"diagnosis.json", "manifest.json"}:
        raise DiagnosisError("published diagnosis directory contains unexpected artifacts")
    if stat.S_IMODE(diag_dir.lstat().st_mode) != 0o555 or any(
        stat.S_IMODE(info.st_mode) != 0o444 for _, _, info in entries
    ):
        raise DiagnosisError("published diagnosis permissions are not immutable")

    recovered_hashes = sorted([
        _sha(raw_diag),
        _sha(raw_man),
    ])

    return diagnosis, recovered_hashes


def verify_published_diagnosis(
    root: Path | str,
    run_id: str,
    cycle_id: int,
    *,
    store: DurableStore | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Verify the canonical M9 artifact and its durable DIAGNOSED event."""
    if not isinstance(run_id, str) or not run_id:
        raise DiagnosisError("run_id must be a non-empty string")
    if isinstance(cycle_id, bool) or not isinstance(cycle_id, int) or cycle_id < 0:
        raise DiagnosisError("cycle_id must be a non-negative integer")
    root_path = Path(root).resolve()
    active_store = store or DurableStore(root_path)
    events = active_store.read_events(run_id)
    if not events:
        raise DiagnosisError("run has no events")
    event = events[-1]
    if (
        event.get("state_to") != State.DIAGNOSED.value
        or event.get("event_type") != "DIAGNOSED"
        or event.get("cycle_id") != cycle_id
    ):
        raise DiagnosisError("refocus requires the active canonical DIAGNOSED event")
    payload = event.get("payload", {})
    candidate_id = payload.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise DiagnosisError("active DIAGNOSED event is missing candidate_id")
    series = load_history_series(root_path, run_id, cycle_id, store=active_store)
    if not series:
        raise DiagnosisError("canonical diagnosis has no verified evaluation history")
    current_record = series[-1]
    diagnosis, hashes = _revalidate_published_diagnosis(
        root_path,
        root_path / "state" / "diagnosis" / run_id / f"c{cycle_id:04d}",
        expected_run_id=run_id,
        expected_cycle_id=cycle_id,
        expected_candidate_id=candidate_id,
        expected_candidate_content_hash=payload.get("candidate_content_hash"),
        expected_base_hash=current_record.base_hash,
        expected_gate_report_hash=current_record.gate_report_hash,
        expected_evaluation_report_hash=current_record.evaluation_report_hash,
        expected_history_hash=_history_hash(series),
    )
    canonical_locator = f"state/diagnosis/{run_id}/c{cycle_id:04d}/diagnosis.json"
    if (
        payload.get("diagnosis_id") != diagnosis.get("diagnosis_id")
        or payload.get("classification") != diagnosis.get("classification")
        or payload.get("recommended_mode") != diagnosis.get("recommended_mode")
        or payload.get("diagnosis_locator") != canonical_locator
        or payload.get("candidate_content_hash") != current_record.candidate_content_hash
        or payload.get("base_hash") != current_record.base_hash
        or event.get("artifact_hashes") != hashes
    ):
        raise DiagnosisError("DIAGNOSED event binding differs from published diagnosis")
    expected_evidence = [
        f"state/evaluations/{run_id}/c{cycle_id:04d}/evaluation.json",
        current_record.gate_report["report_locator"],
    ]
    evaluated_event = next(
        (
            item for item in reversed(events[:-1])
            if item.get("event_type") == "EVALUATED" and item.get("cycle_id") == cycle_id
        ),
        None,
    )
    if (
        evaluated_event is None
        or diagnosis.get("created_at") != evaluated_event.get("occurred_at")
        or diagnosis.get("candidate_content_hash") != current_record.candidate_content_hash
        or diagnosis.get("base_hash") != current_record.base_hash
        or diagnosis.get("gate_report_id") != current_record.gate_report.get("report_id")
        or diagnosis.get("verdict_ids") != current_record.evaluation_report.get("verdict_ids")
        or diagnosis.get("evidence_locators") != expected_evidence
    ):
        raise DiagnosisError("published diagnosis evidence differs from verified evaluation history")
    _verify_diagnosis_classification(diagnosis, series)
    return diagnosis, hashes


def diagnose_cycle(
    root: Path | str,
    run_id: str,
    *,
    cycle_id: int | None = None,
    candidate_id: str | None = None,
    window_size: int = DEFAULT_WINDOW_SIZE,
    mde: float = DEFAULT_MDE,
    store: DurableStore | None = None,
    fault: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Execute the canonical progress stagnation detection and diagnosis pipeline for M9.

    Preconditions:
      - Active state in DurableStore must be State.EVALUATED
      - Historical series of closed cycles up to cycle_id is valid and contiguous
      - Evaluation artifacts and GateReports verify cryptographically
    Postconditions:
      - Canonical Diagnosis object generated and schema-validated
      - Published transactionally in state/diagnosis/<run_id>/c<cycle:04d>/
      - State transitioned to State.DIAGNOSED in DurableStore
      - State.DECIDED is NEVER reached by M9
    """
    if not isinstance(run_id, str) or not run_id:
        raise DiagnosisError("run_id must be a non-empty string")
    if cycle_id is not None and (
        isinstance(cycle_id, bool) or not isinstance(cycle_id, int) or cycle_id < 0
    ):
        raise DiagnosisError("cycle_id must be a non-negative integer")
    if candidate_id is not None and (not isinstance(candidate_id, str) or not candidate_id):
        raise DiagnosisError("candidate_id must be a non-empty string")
    root = Path(root).resolve()
    store = store or DurableStore(root)
    window_size, mde = _validate_classification_parameters(window_size, mde)

    def _trigger_fault(stage: str) -> None:
        if fault:
            fault(stage)

    # 1. Verify active state in DurableStore
    events = store.read_events(run_id)
    if not events:
        raise DiagnosisError("run has no events")

    last_event = events[-1]
    current_state = State(last_event["state_to"])
    effective_cycle_id = last_event["cycle_id"]
    event_payload = last_event.get("payload", {})
    event_candidate_id = event_payload.get("candidate_id")
    event_candidate_hash = event_payload.get("candidate_content_hash")
    event_base_hash = event_payload.get("base_hash")
    event_evaluation_locator = event_payload.get("evaluation_locator")

    if current_state == State.DIAGNOSED and last_event.get("event_type") == "DIAGNOSED":
        if cycle_id is not None and cycle_id != effective_cycle_id:
            raise DiagnosisError(f"cycle_id {cycle_id} diverges from active DIAGNOSED event cycle {effective_cycle_id}")
        if candidate_id is not None and candidate_id != event_candidate_id:
            raise DiagnosisError(f"candidate_id '{candidate_id}' diverges from active DIAGNOSED event candidate '{event_candidate_id}'")
        existing_diag, _ = verify_published_diagnosis(root, run_id, effective_cycle_id, store=store)
        if existing_diag.get("window_size") != window_size or existing_diag.get("mde") != mde:
            raise DiagnosisError("classification parameters diverge from published diagnosis")
        return existing_diag

    if current_state != State.EVALUATED:
        raise DiagnosisError(f"diagnosis requires state EVALUATED, found: {current_state}")

    if not event_candidate_id:
        raise DiagnosisError("active EVALUATED event missing candidate_id")
    if (
        not isinstance(event_candidate_hash, str)
        or len(event_candidate_hash) != 64
        or not isinstance(event_base_hash, str)
        or len(event_base_hash) != 64
    ):
        raise DiagnosisError("active EVALUATED event is missing canonical content hashes")

    if cycle_id is not None and cycle_id != effective_cycle_id:
        raise DiagnosisError(f"cycle_id {cycle_id} diverges from active EVALUATED event cycle {effective_cycle_id}")

    if candidate_id is not None and candidate_id != event_candidate_id:
        raise DiagnosisError(f"candidate_id '{candidate_id}' diverges from active EVALUATED event candidate '{event_candidate_id}'")

    _trigger_fault("after_preconditions_verified")

    # 2. Revalidate the complete M8 history and its event-log bindings before
    # accepting either a fresh or a crash-recovered diagnosis publication.
    series = load_history_series(root, run_id, effective_cycle_id, store=store)
    if not series:
        raise DiagnosisError(f"no historical series available for cycle {effective_cycle_id}")
    current_record = series[-1]
    if (
        current_record.candidate_id != event_candidate_id
        or current_record.candidate_content_hash != event_candidate_hash
        or current_record.base_hash != event_base_hash
        or event_evaluation_locator != f"state/evaluations/{run_id}/c{effective_cycle_id:04d}/evaluation.json"
    ):
        raise DiagnosisError("active EVALUATED event differs from verified evaluation history")

    # 3. Check for already published diagnosis (Idempotent Recovery & Crash Safety)
    diag_parent = _managed_directory(root, f"state/diagnosis/{run_id}", create=False)
    diag_dir = diag_parent / f"c{effective_cycle_id:04d}"
    if diag_dir.exists():
        existing_diag, recovered_hashes = _revalidate_published_diagnosis(
            root,
            diag_dir,
            expected_run_id=run_id,
            expected_cycle_id=effective_cycle_id,
            expected_candidate_id=event_candidate_id,
            expected_candidate_content_hash=current_record.candidate_content_hash,
            expected_base_hash=current_record.base_hash,
            expected_gate_report_hash=current_record.gate_report_hash,
            expected_evaluation_report_hash=current_record.evaluation_report_hash,
            expected_history_hash=_history_hash(series),
            expected_window_size=window_size,
            expected_mde=mde,
        )
        _verify_diagnosis_classification(existing_diag, series)
        event_id = f"evt-diagnosed-c{effective_cycle_id:04d}-{event_candidate_id}"
        idempotency_key = f"diagnosed:{run_id}:c{effective_cycle_id:04d}:{event_candidate_id}"
        store.record(
            run_id=run_id,
            target=State.DIAGNOSED,
            event_id=event_id,
            idempotency_key=idempotency_key,
            actor_id="M00",
            event_type="DIAGNOSED",
            payload={
                "candidate_id": event_candidate_id,
                "candidate_content_hash": event_candidate_hash,
                "base_hash": event_base_hash,
                "diagnosis_id": existing_diag["diagnosis_id"],
                "classification": existing_diag["classification"],
                "recommended_mode": existing_diag["recommended_mode"],
                "diagnosis_locator": f"state/diagnosis/{run_id}/c{effective_cycle_id:04d}/diagnosis.json",
            },
            artifact_hashes=recovered_hashes,
        )
        return existing_diag

    # 4. Classify progress using pure classification engine
    classification, signals, recommended_mode, focus = classify_cycle_progress(
        series,
        window_size=window_size,
        mde=mde,
    )

    _trigger_fault("after_classification_computed")

    # 5. Build a fully content-addressed, retry-stable Diagnosis.  The durable
    # EVALUATED event timestamp supplies a stable creation time across crashes.
    evidence_locators = [
        f"state/evaluations/{run_id}/c{effective_cycle_id:04d}/evaluation.json",
        current_record.gate_report["report_locator"],
    ]
    verdict_ids = list(current_record.evaluation_report["verdict_ids"])
    diagnosis_without_id = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "cycle_id": effective_cycle_id,
        "candidate_id": event_candidate_id,
        "candidate_content_hash": current_record.candidate_content_hash,
        "base_hash": current_record.base_hash,
        "created_at": last_event["occurred_at"],
        "gate_report_id": current_record.gate_report["report_id"],
        "gate_report_hash": current_record.gate_report_hash,
        "evaluation_report_hash": current_record.evaluation_report_hash,
        "history_hash": _history_hash(series),
        "verdict_ids": verdict_ids,
        "window_size": window_size,
        "mde": mde,
        "classification": classification,
        "signals": signals,
        "recommended_mode": recommended_mode,
        "focus": focus,
        "evidence_locators": evidence_locators,
    }
    diag_id = _diagnosis_id_for(diagnosis_without_id)
    diagnosis = {"diagnosis_id": diag_id, **diagnosis_without_id}
    try:
        _validate_schema(root, DIAGNOSIS_SCHEMA, diagnosis)
    except EvaluationError as exc:
        raise DiagnosisError("generated diagnosis does not satisfy its schema") from exc

    # 6. Write-once staging and transactional publication
    diag_parent = _managed_directory(root, f"state/diagnosis/{run_id}", create=True)
    staging = tempfile.mkdtemp(prefix=f".staging_diag_c{effective_cycle_id:04d}_", dir=diag_parent)
    staging_path = Path(staging)

    try:
        diag_path = staging_path / "diagnosis.json"
        diag_bytes = _json(diagnosis)
        _write_synced_file(diag_path, diag_bytes)
        diag_hash = _sha(diag_bytes)

        staging_tree_content_hash = tree_hash(staging_path, exclude={"manifest.json"})

        manifest_data = {
            "schema_version": SCHEMA_VERSION,
            "diagnosis_id": diag_id,
            "run_id": run_id,
            "cycle_id": effective_cycle_id,
            "candidate_id": event_candidate_id,
            "classification": classification,
            "diagnosis_hash": diag_hash,
            "gate_report_hash": current_record.gate_report_hash,
            "evaluation_report_hash": current_record.evaluation_report_hash,
            "tree_content_hash": staging_tree_content_hash,
            "created_at": diagnosis["created_at"],
        }

        try:
            _validate_schema(root, DIAGNOSIS_MANIFEST_SCHEMA, manifest_data)
        except EvaluationError as exc:
            raise DiagnosisError("generated diagnosis manifest does not satisfy its schema") from exc
        manifest_path = staging_path / "manifest.json"
        manifest_bytes = _json(manifest_data)
        _write_synced_file(manifest_path, manifest_bytes)
        manifest_hash = _sha(manifest_bytes)

        _fsync_tree_dirs(staging_path)
        _harden_read_only(staging_path)
        _fsync_tree_dirs(staging_path)

        _trigger_fault("before_diagnosis_published")

        os.replace(staging_path, diag_dir)
        _fsync(diag_dir.parent)

    except Exception:
        _cleanup_staging(staging_path)
        raise

    _trigger_fault("after_diagnosis_published")

    _revalidate_published_diagnosis(
        root,
        diag_dir,
        expected_run_id=run_id,
        expected_cycle_id=effective_cycle_id,
        expected_candidate_id=event_candidate_id,
        expected_candidate_content_hash=current_record.candidate_content_hash,
        expected_base_hash=current_record.base_hash,
        expected_gate_report_hash=current_record.gate_report_hash,
        expected_evaluation_report_hash=current_record.evaluation_report_hash,
        expected_history_hash=_history_hash(series),
        expected_window_size=window_size,
        expected_mde=mde,
    )

    # 7. Record DIAGNOSED event in DurableStore
    artifact_hashes = sorted([
        diag_hash,
        manifest_hash,
    ])

    event_id = f"evt-diagnosed-c{effective_cycle_id:04d}-{event_candidate_id}"
    idempotency_key = f"diagnosed:{run_id}:c{effective_cycle_id:04d}:{event_candidate_id}"

    store.record(
        run_id=run_id,
        target=State.DIAGNOSED,
        event_id=event_id,
        idempotency_key=idempotency_key,
        actor_id="M00",
        event_type="DIAGNOSED",
        payload={
            "candidate_id": event_candidate_id,
            "candidate_content_hash": current_record.candidate_content_hash,
            "base_hash": event_base_hash,
            "diagnosis_id": diag_id,
            "classification": classification,
            "recommended_mode": recommended_mode,
            "diagnosis_locator": f"state/diagnosis/{run_id}/c{effective_cycle_id:04d}/diagnosis.json",
        },
        artifact_hashes=artifact_hashes,
    )

    return diagnosis
