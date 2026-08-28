"""Deterministic, local, blind external jury evaluation and meta-review (M8)."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

import jsonschema
import yaml

from .ingestion import _directory_hash
from .prompts import FORMAT_CHECKER
from .state_machine import State
from .store import DurableStore, IntegrityError, StoreError
from .synthesis import _atomic, _fsync, _fsync_tree_dirs, _inventory, _json, _regular, _sha, _walk, tree_hash

SCHEMA_VERSION = "1.1.0"
RUBRIC_VERSION = "1.0.0"
EVALUATION_SCHEMA = "jury-verdict.schema.json"

DIMENSIONS = (
    "correctness_math",
    "proof_completeness",
    "logical_coherence",
    "scientific_contribution",
    "semantic_precision",
    "clarity",
    "format_integrity",
    "reproducibility",
)

JUROR_SPECIALTIES = (
    ("juror-math", "correctness_math", "focal_math"),
    ("juror-contrib", "scientific_contribution", "focal_contribution"),
    ("juror-clarity", "clarity", "focal_clarity"),
)


class EvaluationError(RuntimeError):
    """Raised when blind evaluation preconditions, schemas, or invariants fail."""


def _validate_schema(root: Path, schema: str, value: Mapping[str, Any]) -> None:
    try:
        definition = json.loads((Path(root) / "config/schemas" / schema).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(definition, format_checker=FORMAT_CHECKER).validate(dict(value))
    except (OSError, json.JSONDecodeError, jsonschema.ValidationError, jsonschema.SchemaError) as exc:
        raise EvaluationError(f"invalid {schema}") from exc


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        _regular(path)
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"cannot read canonical JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise EvaluationError(f"canonical JSON must be an object: {path.name}")
    return value, raw


def _candidate_content_hash(candidate_dir: Path, manifest: Mapping[str, Any]) -> str:
    """Compute content hash using M3 directory hash for baseline or M7 tree hash for challengers."""
    if manifest.get("candidate_kind") == "baseline":
        return _directory_hash(candidate_dir, exclude={"manifest.json"})
    return tree_hash(candidate_dir, exclude={"manifest.json"})


def load_rubric(root: Path) -> dict[str, Any]:
    """Load and validate the evaluation rubric configuration."""
    rubric_path = root / "config/rubrics/evaluation.yaml"
    try:
        data = yaml.safe_load(rubric_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise EvaluationError(f"failed to load evaluation rubric: {exc}") from exc
    if not isinstance(data, dict) or "dimensions" not in data:
        raise EvaluationError("malformed rubric definition")
    dims = [d.get("id") for d in data.get("dimensions", []) if isinstance(d, dict)]
    if set(dims) != set(DIMENSIONS) or len(dims) != len(DIMENSIONS):
        raise EvaluationError("rubric dimensions mismatch canonical set")
    return data


def sanitize_text(text: str) -> str:
    """Sanitize raw text by removing author mentions, role IDs, and version strings."""
    sanitized = text
    # Remove author role tags (M00, S10-S50, W11-W53)
    sanitized = re.sub(r"\b(M00|S[1-5]0|W[1-5][1-3])\b", "[ROLE]", sanitized)
    # Remove version indicators (v0000, v0001, etc., champion, challenger)
    sanitized = re.sub(r"\bv\d{4}\b", "[VERSION]", sanitized)
    sanitized = re.sub(r"\b(champion|challenger|pareto|rejected)\b", "[CANDIDATE]", sanitized, flags=re.IGNORECASE)
    # Remove run / cycle identifiers
    sanitized = re.sub(r"\brun-[a-zA-Z0-9_-]+\b", "[RUN]", sanitized)
    sanitized = re.sub(r"\bcycle[_-]?\d+\b", "[CYCLE]", sanitized, flags=re.IGNORECASE)
    return sanitized


class BlindComparisonBundle:
    """Sanitized, content-addressed A/B presentation bundle for blind evaluation."""

    def __init__(
        self,
        *,
        comparison_id: str,
        candidate_neutral_ids: Sequence[str],
        content_hashes: Sequence[str],
        rubric_version: str,
        candidate_a_content: dict[str, Any],
        candidate_b_content: dict[str, Any],
        order_seed: int,
    ):
        self.comparison_id = comparison_id
        self.candidate_neutral_ids = list(candidate_neutral_ids)
        self.content_hashes = list(content_hashes)
        self.rubric_version = rubric_version
        self.candidate_a_content = candidate_a_content
        self.candidate_b_content = candidate_b_content
        self.order_seed = order_seed

    def presentation_for_order(self, order: Sequence[str]) -> dict[str, Any]:
        """Return the presentation payload for order ('A', 'B') or ('B', 'A')."""
        if list(order) == ["A", "B"]:
            first_id, second_id = "A", "B"
            first_hash, second_hash = self.content_hashes[0], self.content_hashes[1]
            first_content, second_content = self.candidate_a_content, self.candidate_b_content
        elif list(order) == ["B", "A"]:
            first_id, second_id = "B", "A"
            first_hash, second_hash = self.content_hashes[1], self.content_hashes[0]
            first_content, second_content = self.candidate_b_content, self.candidate_a_content
        else:
            raise EvaluationError(f"invalid presentation order: {order}")

        return {
            "comparison_id": self.comparison_id,
            "presentation_order": list(order),
            "order_seed": self.order_seed,
            "rubric_version": self.rubric_version,
            "candidate_neutral_ids": ["A", "B"],
            "content_hashes": [first_hash, second_hash],
            "first_candidate": {
                "neutral_id": first_id,
                "content_hash": first_hash,
                "content": first_content,
            },
            "second_candidate": {
                "neutral_id": second_id,
                "content_hash": second_hash,
                "content": second_content,
            },
        }

    @classmethod
    def create(
        cls,
        root: Path,
        *,
        champion_dir: Path,
        challenger_dir: Path,
        order_seed: int = 413,
    ) -> BlindComparisonBundle:
        """Build and sanitize comparison bundle from champion and challenger directories."""
        champ_manifest_path = champion_dir / "manifest.json"
        chall_manifest_path = challenger_dir / "manifest.json"

        champ_manifest, _ = _read_json(champ_manifest_path)
        chall_manifest, _ = _read_json(chall_manifest_path)

        _validate_schema(root, "candidate-manifest.schema.json", champ_manifest)
        _validate_schema(root, "candidate-manifest.schema.json", chall_manifest)

        champ_hash = _candidate_content_hash(champion_dir, champ_manifest)
        chall_hash = _candidate_content_hash(challenger_dir, chall_manifest)

        if champ_hash != champ_manifest.get("content_hash"):
            raise EvaluationError("champion tree content hash mismatch")
        if chall_hash != chall_manifest.get("content_hash"):
            raise EvaluationError("challenger tree content hash mismatch")

        # Neutral binding: A is champion, B is challenger
        content_hashes = [champ_hash, chall_hash]

        # Extract sanitized texts
        def extract_content(candidate_dir: Path) -> dict[str, Any]:
            tex_files = {}
            for rel, path, sinfo in _walk(candidate_dir):
                if stat.S_ISREG(sinfo.st_mode) and (rel.endswith(".tex") or rel.endswith(".txt")):
                    try:
                        raw = path.read_text(encoding="utf-8", errors="replace")
                        tex_files[rel] = sanitize_text(raw)
                    except OSError:
                        pass
            return {"files": tex_files, "file_count": len(tex_files)}

        content_a = extract_content(champion_dir)
        content_b = extract_content(challenger_dir)

        comp_bytes = _json({
            "candidate_hashes": content_hashes,
            "rubric_version": RUBRIC_VERSION,
            "order_seed": order_seed,
        })
        comparison_id = f"cmp-{_sha(comp_bytes)}"

        return cls(
            comparison_id=comparison_id,
            candidate_neutral_ids=["A", "B"],
            content_hashes=content_hashes,
            rubric_version=RUBRIC_VERSION,
            candidate_a_content=content_a,
            candidate_b_content=content_b,
            order_seed=order_seed,
        )


class FakeJurorAdapter:
    """Deterministic fake juror adapter for offline, offline-tested evaluations."""

    def __init__(
        self,
        *,
        juror_id: str,
        specialty: str = "correctness_math",
        model_family: str = "fake-eval-v1",
        preferred_winner: str | None = "B",  # "A", "B", "tie", "inconclusive"
        positional_bias: str | None = None,  # "first", "second"
        math_pass: tuple[bool, bool] = (True, True),
        base_scores: tuple[int, int] = (4, 5),
        corrupt_schema: bool = False,
    ):
        self.juror_id = juror_id
        self.specialty = specialty
        self.model_family = model_family
        self.preferred_winner = preferred_winner
        self.positional_bias = positional_bias
        self.math_pass = math_pass
        self.base_scores = base_scores
        self.corrupt_schema = corrupt_schema

    def evaluate(self, presentation: dict[str, Any]) -> dict[str, Any]:
        """Generate a valid JuryVerdict according to configuration and presentation order."""
        order = presentation["presentation_order"]
        comparison_id = presentation["comparison_id"]
        order_seed = presentation["order_seed"]
        content_hashes = presentation["content_hashes"]

        if self.corrupt_schema:
            return {"invalid": "payload"}

        # Determine outcome based on bias or preference
        if self.positional_bias == "first":
            # Always chooses first presented candidate
            winner = order[0]
            outcome = "winner"
        elif self.positional_bias == "second":
            # Always chooses second presented candidate
            winner = order[1]
            outcome = "winner"
        elif self.preferred_winner in {"A", "B"}:
            winner = self.preferred_winner
            outcome = "winner"
        elif self.preferred_winner == "tie":
            winner = None
            outcome = "tie"
        else:
            winner = None
            outcome = "inconclusive"

        score_a = {d: self.base_scores[0] for d in DIMENSIONS}
        score_b = {d: self.base_scores[1] for d in DIMENSIONS}

        # Match dimension_scores to candidate A and candidate B
        dimension_scores = [score_a, score_b]
        math_pass = list(self.math_pass)

        # Build verdict ID deterministically
        verdict_data = {
            "comparison_id": comparison_id,
            "juror_id": self.juror_id,
            "presentation_order": list(order),
            "order_seed": order_seed,
        }
        verdict_id = f"v-{_sha(_json(verdict_data))[:32]}"

        evidence_locators = [
            f"locators/{self.juror_id}/evidence-01.txt",
            f"locators/{self.juror_id}/evidence-02.txt",
        ]

        verdict = {
            "schema_version": SCHEMA_VERSION,
            "verdict_id": verdict_id,
            "comparison_id": comparison_id,
            "juror_id": self.juror_id,
            "candidate_neutral_ids": ["A", "B"],
            "content_hashes": content_hashes,
            "presentation_order": list(order),
            "order_seed": order_seed,
            "rubric_version": RUBRIC_VERSION,
            "dimension_scores": dimension_scores,
            "outcome": outcome,
            "winner_neutral_id": winner,
            "correctness_math_pass": math_pass,
            "evidence_locators": evidence_locators,
            "submitted_at": _now(),
        }
        return verdict


class FakeMetaReviewerAdapter:
    """Deterministic fake meta-reviewer adapter."""

    def __init__(
        self,
        *,
        meta_id: str = "meta-reviewer",
        should_confirm: bool = True,
        should_veto: bool = False,
        veto_reason: str | None = None,
        corrupt_schema: bool = False,
    ):
        self.meta_id = meta_id
        self.should_confirm = should_confirm
        self.should_veto = should_veto
        self.veto_reason = veto_reason
        self.corrupt_schema = corrupt_schema

    def review(
        self,
        *,
        comparison_id: str,
        consistent_verdicts: list[dict[str, Any]],
        divergences: list[dict[str, Any]],
        gate_report_summary: dict[str, Any],
    ) -> dict[str, Any]:
        """Perform meta-review and return structured review response."""
        if self.corrupt_schema:
            return {"broken": "response"}

        return {
            "schema_version": SCHEMA_VERSION,
            "meta_verdict_id": f"meta-{comparison_id[:24]}",
            "meta_reviewer_id": self.meta_id,
            "confirmed": bool(self.should_confirm and not self.should_veto),
            "vetoed": bool(self.should_veto),
            "veto_reason": self.veto_reason,
            "consistent_verdict_count": len(consistent_verdicts),
            "divergence_count": len(divergences),
            "explanation": "Meta-review verification completed against GateReport and jury consistency.",
            "reviewed_at": _now(),
        }


def check_inversion_consistency(
    verdict_ab: dict[str, Any],
    verdict_ba: dict[str, Any],
    tolerance: float = 1.0,
) -> tuple[bool, str | None, str | None, bool]:
    """Check inversion consistency between A/B and B/A presentations.

    Returns:
        (is_consistent, inconsistency_reason, inferred_winner, candidate_b_math_pass)
    """
    winner_ab = verdict_ab.get("winner_neutral_id")
    winner_ba = verdict_ba.get("winner_neutral_id")
    outcome_ab = verdict_ab.get("outcome")
    outcome_ba = verdict_ba.get("outcome")

    # Math correctness check for Candidate B (Challenger)
    math_ab = verdict_ab.get("correctness_math_pass", [False, False])
    math_ba = verdict_ba.get("correctness_math_pass", [False, False])

    # Index 1 is candidate B (Challenger)
    math_b_pass = bool(math_ab[1] and math_ba[1])

    # If math correctness disagrees across presentations, inconsistent
    if math_ab[1] != math_ba[1]:
        return False, "inconsistent_math_verification", None, False

    # Check outcome and winner consistency
    if outcome_ab != outcome_ba:
        return False, f"outcome_mismatch:{outcome_ab}_vs_{outcome_ba}", None, math_b_pass

    if outcome_ab == "winner":
        if winner_ab == winner_ba:
            # Both picked same underlying candidate!
            # Check dimension score consistency within tolerance
            scores_ab = verdict_ab.get("dimension_scores", [{}, {}])
            scores_ba = verdict_ba.get("dimension_scores", [{}, {}])
            for idx in (0, 1):
                for dim in DIMENSIONS:
                    val_ab = scores_ab[idx].get(dim, 0)
                    val_ba = scores_ba[idx].get(dim, 0)
                    if abs(val_ab - val_ba) > tolerance:
                        return False, f"dimension_score_drift:{dim}", None, math_b_pass
            return True, None, winner_ab, math_b_pass
        elif winner_ab == "A" and winner_ba == "B":
            return False, "first_position_bias", None, math_b_pass
        elif winner_ab == "B" and winner_ba == "A":
            return False, "second_position_bias", None, math_b_pass
        else:
            return False, "winner_divergence", None, math_b_pass

    elif outcome_ab == "tie":
        return True, None, "tie", math_b_pass
    else:
        return False, "inconclusive_verdict", None, math_b_pass


def evaluate_candidate(
    root: Path | str,
    run_id: str,
    *,
    cycle_id: int | None = None,
    candidate_id: str | None = None,
    gate_report_locator: str | None = None,
    order_seed: int = 413,
    juror_adapters: Mapping[str, Any] | None = None,
    meta_adapter: Any | None = None,
    model_families: Mapping[str, str] | None = None,
    store: DurableStore | None = None,
    fault: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Execute the canonical blind evaluation and meta-review pipeline for M8.

    Preconditions:
      - State must be State.GATES_PASSED
      - GateReport exists, is verified, overall_pass == True, correctness_math_pass == True
      - Champion and Challenger trees are immutable and match content hashes
    Postconditions:
      - All 6 verdicts validated, locked in immutable storage
      - Inversion consistency checked for 3 juror pairs
      - Meta-review executed and persisted
      - State transitioned to State.EVALUATED
      - Challenger and champion tree hashes verified unchanged
    """
    root = Path(root).resolve()
    store = store or DurableStore(root)

    def _trigger_fault(stage: str) -> None:
        if fault:
            fault(stage)

    # 1. Verify state and preconditions
    events = store.read_events(run_id)
    if not events:
        raise EvaluationError("run has no events")

    last_event = events[-1]
    current_state = State(last_event["state_to"])
    effective_cycle_id = last_event.get("cycle_id", 0) if cycle_id is None else cycle_id

    # Must be in GATES_PASSED
    if current_state != State.GATES_PASSED:
        raise EvaluationError(f"evaluation requires state GATES_PASSED, found: {current_state}")

    # 2. Find and validate GateReport
    eval_candidate_id = candidate_id
    if gate_report_locator:
        gate_report_path = root / gate_report_locator
    else:
        gates_base = root / "state/gates"
        if not gates_base.exists():
            raise EvaluationError("no gate reports directory found")
        if eval_candidate_id:
            report_files = sorted((gates_base / eval_candidate_id).glob("*.json"))
        else:
            report_files = sorted(gates_base.glob("*/*.json"))
        if not report_files:
            raise EvaluationError(f"no gate reports found for candidate {eval_candidate_id}")
        gate_report_path = report_files[-1]

    gate_report, _ = _read_json(gate_report_path)
    _validate_schema(root, "gate-report.schema.json", gate_report)

    if not gate_report.get("overall_pass"):
        raise EvaluationError("GateReport overall_pass is false; candidate cannot proceed to jury")
    if not gate_report.get("correctness_math_pass"):
        raise EvaluationError("GateReport correctness_math_pass is false; candidate cannot proceed to jury")

    eval_candidate_id = eval_candidate_id or gate_report["candidate_id"]
    challenger_content_hash = gate_report["candidate_content_hash"]

    # 3. Locate Champion and Challenger directories
    champion_dir = root / "versions/champion/v0000"
    if not champion_dir.exists():
        champ_dirs = sorted((root / "versions/champion").glob("v*"))
        if not champ_dirs:
            raise EvaluationError("champion directory missing")
        champion_dir = champ_dirs[0]

    challenger_dir = root / "versions/challengers" / eval_candidate_id
    if not challenger_dir.exists():
        raise EvaluationError(f"challenger directory missing: {eval_candidate_id}")

    champ_manifest, _ = _read_json(champion_dir / "manifest.json")
    chall_manifest, _ = _read_json(challenger_dir / "manifest.json")

    # Revalidate tree hashes before starting
    champ_hash_before = _candidate_content_hash(champion_dir, champ_manifest)
    chall_hash_before = _candidate_content_hash(challenger_dir, chall_manifest)

    if chall_hash_before != challenger_content_hash:
        raise EvaluationError("challenger content hash mismatch with GateReport")

    _trigger_fault("after_preconditions_verified")

    # 4. Build sanitized BlindComparisonBundle
    bundle = BlindComparisonBundle.create(
        root,
        champion_dir=champion_dir,
        challenger_dir=challenger_dir,
        order_seed=order_seed,
    )

    # 5. Prepare jurors and storage directories
    eval_dir = root / f"state/evaluations/{run_id}/c{effective_cycle_id:04d}"
    verdicts_dir = eval_dir / "verdicts"
    verdicts_dir.mkdir(parents=True, exist_ok=True)

    load_rubric(root)

    default_adapters = {
        "juror-math": FakeJurorAdapter(juror_id="juror-math", specialty="correctness_math"),
        "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib", specialty="scientific_contribution"),
        "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity", specialty="clarity"),
    }
    adapters = dict(juror_adapters or default_adapters)

    families = dict(model_families or {
        "juror-math": "eval-math-family",
        "juror-contrib": "eval-contrib-family",
        "juror-clarity": "eval-clarity-family",
    })

    unique_families = {families.get(jid) for jid, _, _ in JUROR_SPECIALTIES}
    diversity_assurance = "full_diversity" if len(unique_families) >= 3 else "reduced_diversity_assurance"

    verdicts: list[dict[str, Any]] = []
    juror_results: list[dict[str, Any]] = []
    consistent_verdicts: list[dict[str, Any]] = []
    divergences: list[dict[str, Any]] = []

    artifact_hashes: list[str] = []

    # 6. Execute A/B and B/A presentations for all 3 jurors
    for juror_id, specialty, _ in JUROR_SPECIALTIES:
        adapter = adapters.get(juror_id)
        if not adapter:
            raise EvaluationError(f"missing adapter for juror: {juror_id}")

        # Presentation 1: A/B
        pres_ab = bundle.presentation_for_order(["A", "B"])
        raw_v_ab = adapter.evaluate(pres_ab)
        _validate_schema(root, EVALUATION_SCHEMA, raw_v_ab)

        # Presentation 2: B/A
        pres_ba = bundle.presentation_for_order(["B", "A"])
        raw_v_ba = adapter.evaluate(pres_ba)
        _validate_schema(root, EVALUATION_SCHEMA, raw_v_ba)

        # Persist each verdict immutably
        for v in (raw_v_ab, raw_v_ba):
            v_path = verdicts_dir / f"{v['verdict_id']}.json"
            v_bytes = _json(v)
            _atomic(v_path, v_bytes)
            _fsync(v_path)
            artifact_hashes.append(_sha(v_bytes))
            verdicts.append(v)

        _trigger_fault(f"after_verdict_persisted_{juror_id}")

        # Check inversion consistency
        is_consistent, reason, inferred_winner, math_pass = check_inversion_consistency(raw_v_ab, raw_v_ba)

        juror_eval = {
            "juror_id": juror_id,
            "specialty": specialty,
            "model_family": families.get(juror_id, "unknown"),
            "consistent": is_consistent,
            "inconsistency_reason": reason,
            "inferred_winner": inferred_winner,
            "candidate_b_math_pass": math_pass,
            "verdict_ab_id": raw_v_ab["verdict_id"],
            "verdict_ba_id": raw_v_ba["verdict_id"],
        }
        juror_results.append(juror_eval)

        if is_consistent:
            consistent_verdicts.append(juror_eval)
        else:
            divergences.append(juror_eval)

    # 7. Execute Meta-Review
    meta_reviewer = meta_adapter or FakeMetaReviewerAdapter()
    gate_summary = {
        "report_id": gate_report["report_id"],
        "overall_pass": gate_report["overall_pass"],
        "correctness_math_pass": gate_report["correctness_math_pass"],
    }

    meta_result = meta_reviewer.review(
        comparison_id=bundle.comparison_id,
        consistent_verdicts=consistent_verdicts,
        divergences=divergences,
        gate_report_summary=gate_summary,
    )

    if not isinstance(meta_result, dict) or "confirmed" not in meta_result or "vetoed" not in meta_result:
        raise EvaluationError("meta-reviewer returned invalid structure")

    meta_path = eval_dir / "meta-verdict.json"
    meta_bytes = _json(meta_result)
    _atomic(meta_path, meta_bytes)
    _fsync(meta_path)
    artifact_hashes.append(_sha(meta_bytes))

    _trigger_fault("after_meta_review_persisted")

    # 8. Aggregation Logic
    # Candidate B is Challenger, Candidate A is Champion
    challenger_wins = sum(1 for j in consistent_verdicts if j["inferred_winner"] == "B")
    champion_wins = sum(1 for j in consistent_verdicts if j["inferred_winner"] == "A")
    ties = sum(1 for j in consistent_verdicts if j["inferred_winner"] == "tie")

    all_consistent_math_pass = all(j["candidate_b_math_pass"] for j in consistent_verdicts) if consistent_verdicts else False
    meta_confirmed = bool(meta_result.get("confirmed") and not meta_result.get("vetoed"))

    if (
        challenger_wins >= 2
        and meta_confirmed
        and all_consistent_math_pass
        and gate_report["overall_pass"]
        and gate_report["correctness_math_pass"]
    ):
        overall_outcome = "challenger_favored"
        challenger_eligible = True
    elif champion_wins >= 2:
        overall_outcome = "champion_favored"
        challenger_eligible = False
    elif ties >= 2:
        overall_outcome = "tie"
        challenger_eligible = False
    else:
        overall_outcome = "inconclusive"
        challenger_eligible = False

    # 9. Build and persist EvaluationReport
    eval_id = f"eval-{_sha(_json({'comparison_id': bundle.comparison_id, 'candidate_id': eval_candidate_id}))[:32]}"
    report = {
        "schema_version": SCHEMA_VERSION,
        "evaluation_id": eval_id,
        "run_id": run_id,
        "cycle_id": effective_cycle_id,
        "comparison_id": bundle.comparison_id,
        "candidate_id": eval_candidate_id,
        "base_hash": bundle.content_hashes[0],
        "candidate_content_hash": bundle.content_hashes[1],
        "gate_report_id": gate_report["report_id"],
        "order_seed": order_seed,
        "diversity_assurance": diversity_assurance,
        "total_jurors": len(JUROR_SPECIALTIES),
        "consistent_jurors": len(consistent_verdicts),
        "divergent_jurors": len(divergences),
        "challenger_wins": challenger_wins,
        "champion_wins": champion_wins,
        "ties": ties,
        "meta_confirmed": meta_confirmed,
        "overall_outcome": overall_outcome,
        "challenger_eligible": challenger_eligible,
        "correctness_math_pass": all_consistent_math_pass,
        "juror_evaluations": juror_results,
        "meta_verdict": meta_result,
        "verdict_ids": [v["verdict_id"] for v in verdicts],
        "evaluated_at": _now(),
    }

    report_path = eval_dir / "evaluation.json"
    report_bytes = _json(report)
    _atomic(report_path, report_bytes)
    _fsync(report_path)
    artifact_hashes.append(_sha(report_bytes))

    # Re-verify tree hashes to prove immutability
    champ_hash_after = _candidate_content_hash(champion_dir, champ_manifest)
    chall_hash_after = _candidate_content_hash(challenger_dir, chall_manifest)
    if champ_hash_after != champ_hash_before:
        raise EvaluationError("champion tree mutated during evaluation")
    if chall_hash_after != chall_hash_before:
        raise EvaluationError("challenger tree mutated during evaluation")

    _trigger_fault("before_evaluated_event")

    # 10. Record EVALUATED event in DurableStore
    event_id = f"evt-evaluated-c{effective_cycle_id:04d}-{eval_candidate_id}"
    idempotency_key = f"evaluated-{run_id}-c{effective_cycle_id:04d}-{eval_candidate_id}"
    store.record(
        run_id=run_id,
        target=State.EVALUATED,
        event_id=event_id,
        idempotency_key=idempotency_key,
        actor_id="M00",
        event_type="EVALUATED",
        payload={
            "candidate_id": eval_candidate_id,
            "candidate_content_hash": bundle.content_hashes[1],
            "base_hash": bundle.content_hashes[0],
            "evaluation_id": eval_id,
            "comparison_id": bundle.comparison_id,
            "overall_outcome": overall_outcome,
            "challenger_eligible": challenger_eligible,
            "verdict_ids": [v["verdict_id"] for v in verdicts],
            "evaluation_locator": f"state/evaluations/{run_id}/c{effective_cycle_id:04d}/evaluation.json",
        },
        artifact_hashes=sorted(set(artifact_hashes)),
    )

    _trigger_fault("after_evaluated_event")
    return report
