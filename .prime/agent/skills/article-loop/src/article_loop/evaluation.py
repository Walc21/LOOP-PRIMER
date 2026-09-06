"""Deterministic, local, blind external jury evaluation and meta-review (M8)."""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import jsonschema
import yaml

from .gates import verify_gate_report
from .ingestion import _directory_hash, _fsync_dir
from .prompts import FORMAT_CHECKER
from .state_machine import State
from .store import DurableStore
from .synthesis import (
    _contained,
    _fsync_tree_dirs,
    _json,
    _regular,
    _sha,
    _walk,
    tree_hash,
)

SCHEMA_VERSION = "1.1.0"
RUBRIC_VERSION = "1.0.0"
EVALUATION_SCHEMA = "jury-verdict.schema.json"
META_VERDICT_SCHEMA = "meta-verdict.schema.json"
EVALUATION_REPORT_SCHEMA = "evaluation-report.schema.json"
EVALUATION_MANIFEST_SCHEMA = "evaluation-manifest.schema.json"

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
    """Validate data against Draft 2020-12 schema."""
    try:
        definition = json.loads((Path(root) / "config/schemas" / schema).read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(definition, format_checker=FORMAT_CHECKER).validate(dict(value))
    except (OSError, json.JSONDecodeError, jsonschema.ValidationError, jsonschema.SchemaError) as exc:
        raise EvaluationError(f"invalid {schema}: {exc}") from exc


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


def _require_canonical_json(value: Mapping[str, Any], raw: bytes, label: str) -> None:
    """Reject semantically equivalent but non-canonical durable JSON bytes."""
    if raw != _json(dict(value)):
        raise EvaluationError(f"published {label} bytes are not canonical")


def _write_synced_file(path: Path, data: bytes) -> None:
    """Write binary data to path, flush and fsync file descriptor."""
    with path.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _managed_directory(root: Path, relative: str, *, create: bool) -> Path:
    """Resolve a real contained output directory without following symlinks."""
    try:
        path = _contained(root, relative)
        if path.exists() or path.is_symlink():
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                raise EvaluationError("managed evaluation directory is not a real directory")
        elif create:
            path.mkdir(parents=True)
        if path.exists() and path.resolve().relative_to(root) != Path(relative):
            raise EvaluationError("managed evaluation directory is not canonical")
        return path
    except EvaluationError:
        raise
    except Exception as exc:
        raise EvaluationError("managed evaluation directory is unsafe") from exc


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
    """Sanitize text by removing author mentions, role IDs, version strings, run IDs, and candidate labels."""
    sanitized = text

    # Remove common LaTeX identity-bearing commands with balanced braced
    # arguments.  A plain regular expression is insufficient for constructs
    # such as ``\author{Alice \and Bob}`` or nested ``\thanks{...}`` values.
    identity_commands = {
        "author", "authors", "affil", "affiliation", "institute",
        "email", "ead", "orcid", "orcidlink", "thanks", "address",
    }
    command_names = "|".join(sorted(identity_commands, key=len, reverse=True))
    # A TeX control word ends at a non-letter boundary.  The boundary prevents
    # ``\authorinfo`` from being treated as ``\author`` plus leaked
    # ``info{...}``; the second alternative removes such unknown identity-
    # prefixed macros as a whole before a jury can receive their arguments.
    command_pattern = re.compile(
        r"\\(?:" + command_names + r")\*?(?=[^A-Za-z@]|$)"
        + r"|\\(?:" + command_names + r")[A-Za-z@]+\*?(?=[^A-Za-z@]|$)",
        flags=re.IGNORECASE,
    )
    cursor = 0
    pieces: list[str] = []
    while True:
        match = command_pattern.search(sanitized, cursor)
        if match is None:
            pieces.append(sanitized[cursor:])
            break
        pieces.append(sanitized[cursor:match.start()])
        end = match.end()
        while end < len(sanitized) and sanitized[end].isspace():
            end += 1
        if end < len(sanitized) and sanitized[end] == "[":
            closing = sanitized.find("]", end + 1)
            end = len(sanitized) if closing < 0 else closing + 1
            while end < len(sanitized) and sanitized[end].isspace():
                end += 1
        if end < len(sanitized) and sanitized[end] == "{":
            depth = 0
            index = end
            while index < len(sanitized):
                if sanitized[index] == "{" and (index == 0 or sanitized[index - 1] != "\\"):
                    depth += 1
                elif sanitized[index] == "}" and (index == 0 or sanitized[index - 1] != "\\"):
                    depth -= 1
                    if depth == 0:
                        index += 1
                        break
                index += 1
            end = index
        pieces.append("[IDENTITY_REDACTED]")
        cursor = end
    sanitized = "".join(pieces)

    # Remove equivalent plain-text metadata, emails, ORCID identifiers and
    # hyperref's PDF author field.
    sanitized = re.sub(
        r"(?im)^\s*%?\s*(?:authors?|affiliations?|institutes?|addresses?|emails?|orcids?)\s*:\s*.*$",
        "[IDENTITY_REDACTED]",
        sanitized,
    )
    sanitized = re.sub(r"(?i)pdfauthor\s*=\s*\{[^{}]*\}", "pdfauthor={[IDENTITY_REDACTED]}", sanitized)
    sanitized = re.sub(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[EMAIL_REDACTED]", sanitized)
    sanitized = re.sub(r"\b(?:https?://orcid\.org/)?\d{4}-\d{4}-\d{4}-[\dX]{4}\b", "[ORCID_REDACTED]", sanitized, flags=re.IGNORECASE)
    # Remove internal path references first
    sanitized = re.sub(r"\b(workspaces|versions|artifacts)/[^\s,;\"'>)]+", "[PATH]", sanitized)
    # Remove author role tags (M00, S10-S50, W11-W53)
    sanitized = re.sub(r"\b(M00|S[1-5]0|W[1-5][1-3])\b", "[ROLE]", sanitized)
    # Remove version indicators (v0000, v0001, etc.)
    sanitized = re.sub(r"\bv\d{4,}\b", "[VERSION]", sanitized)
    # Remove candidate labels
    sanitized = re.sub(r"\b(champion|challenger|pareto|rejected)\b", "[CANDIDATE]", sanitized, flags=re.IGNORECASE)
    # Remove run identifiers
    sanitized = re.sub(r"\brun-[a-zA-Z0-9_-]+\b", "[RUN]", sanitized)
    # Remove cycle identifiers
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
            "content_hashes": [self.content_hashes[0], self.content_hashes[1]],
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

        # Extract sanitized texts under deterministic names that cannot leak
        # authorship, role, version, or source-tree structure.
        def extract_content(candidate_dir: Path) -> dict[str, Any]:
            tex_files: dict[str, str] = {}
            file_idx = 0
            for rel, path, sinfo in sorted(_walk(candidate_dir), key=lambda item: item[0]):
                if stat.S_ISREG(sinfo.st_mode) and (rel.endswith(".tex") or rel.endswith(".txt") or rel.endswith(".bib")):
                    try:
                        raw = path.read_text(encoding="utf-8", errors="replace")
                        suffix = Path(rel).suffix.lower()
                        neutral_name = f"document_{file_idx:04d}{suffix}"
                        tex_files[neutral_name] = sanitize_text(raw)
                        file_idx += 1
                    except OSError as exc:
                        raise EvaluationError("candidate text cannot be read completely") from exc
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


def _validate_juror_verdict_response(
    root: Path,
    verdict: Mapping[str, Any],
    *,
    expected_juror_id: str,
    expected_presentation_order: list[str],
    bundle: BlindComparisonBundle,
    seen_verdict_ids: set[str],
) -> dict[str, Any]:
    """Strictly validate juror verdict schema and semantic alignment with requested presentation."""
    if verdict.get("comparison_id") != bundle.comparison_id:
        raise EvaluationError("verdict comparison_id does not match presentation bundle")

    if verdict.get("juror_id") != expected_juror_id:
        raise EvaluationError(f"verdict juror_id '{verdict.get('juror_id')}' does not match expected '{expected_juror_id}'")

    if verdict.get("candidate_neutral_ids") != ["A", "B"]:
        raise EvaluationError("verdict candidate_neutral_ids must be exactly ['A', 'B']")

    if verdict.get("presentation_order") != expected_presentation_order:
        raise EvaluationError(
            f"verdict presentation_order {verdict.get('presentation_order')} does not match requested {expected_presentation_order}"
        )

    _validate_schema(root, EVALUATION_SCHEMA, verdict)

    v_id = verdict.get("verdict_id")
    if not isinstance(v_id, str) or not v_id:
        raise EvaluationError("verdict_id is missing or empty")
    if v_id in seen_verdict_ids:
        raise EvaluationError(f"duplicate verdict_id detected: {v_id}")

    if verdict.get("order_seed") != bundle.order_seed:
        raise EvaluationError("verdict order_seed does not match presentation bundle")

    if verdict.get("rubric_version") != bundle.rubric_version:
        raise EvaluationError("verdict rubric_version does not match presentation bundle")

    if verdict.get("content_hashes") != bundle.content_hashes:
        raise EvaluationError("verdict content_hashes does not match canonical neutral candidate hashes")

    outcome = verdict.get("outcome")
    winner = verdict.get("winner_neutral_id")
    if outcome == "winner":
        if winner not in ("A", "B"):
            raise EvaluationError("verdict with outcome 'winner' must have winner_neutral_id 'A' or 'B'")
    else:
        if winner is not None:
            raise EvaluationError("verdict with outcome tie/inconclusive must have null winner_neutral_id")

    scores = verdict.get("dimension_scores")
    if not isinstance(scores, list) or len(scores) != 2:
        raise EvaluationError("verdict dimension_scores must contain exactly 2 candidates [A, B]")
    for idx, cand_scores in enumerate(scores):
        if not isinstance(cand_scores, dict):
            raise EvaluationError(f"dimension_scores[{idx}] must be a dictionary")
        for dim in DIMENSIONS:
            val = cand_scores.get(dim)
            if (
                isinstance(val, bool)
                or not isinstance(val, (int, float))
                or not math.isfinite(float(val))
                or val < 0
                or val > 5
            ):
                raise EvaluationError(f"dimension_scores[{idx}][{dim}] must be a number between 0 and 5, got {val}")

    math_pass = verdict.get("correctness_math_pass")
    if not isinstance(math_pass, list) or len(math_pass) != 2 or any(not isinstance(m, bool) for m in math_pass):
        raise EvaluationError("correctness_math_pass must be an array of exactly 2 booleans [math_A, math_B]")

    locators = verdict.get("evidence_locators")
    if not isinstance(locators, list) or len(locators) == 0:
        raise EvaluationError("evidence_locators must be a non-empty array")
    for loc in locators:
        if not isinstance(loc, str) or not loc.strip():
            raise EvaluationError("empty evidence locator")
        if loc.startswith("/") or ".." in Path(loc).parts:
            raise EvaluationError(f"unsafe evidence locator: {loc}")

    seen_verdict_ids.add(v_id)
    return dict(verdict)


def _validate_meta_verdict_response(
    root: Path,
    meta: Mapping[str, Any],
    *,
    bundle: BlindComparisonBundle,
    gate_report: Mapping[str, Any],
    consistent_count: int,
    divergence_count: int,
) -> dict[str, Any]:
    """Strictly validate meta-reviewer response schema and semantic alignment."""
    _validate_schema(root, META_VERDICT_SCHEMA, meta)

    if meta.get("comparison_id") != bundle.comparison_id:
        raise EvaluationError("meta-verdict comparison_id does not match presentation bundle")

    if meta.get("gate_report_id") != gate_report.get("report_id"):
        raise EvaluationError("meta-verdict gate_report_id does not match verified GateReport")

    if meta.get("consistent_verdict_count") != consistent_count:
        raise EvaluationError("meta-verdict consistent_verdict_count does not match actual consistent jury count")

    if meta.get("divergence_count") != divergence_count:
        raise EvaluationError("meta-verdict divergence_count does not match actual divergent jury count")

    confirmed = meta.get("confirmed")
    vetoed = meta.get("vetoed")
    if confirmed is True and vetoed is True:
        raise EvaluationError("meta-verdict cannot be both confirmed and vetoed")

    if vetoed is True and not meta.get("veto_reason"):
        raise EvaluationError("meta-verdict vetoed is true but veto_reason is missing")

    locators = meta.get("evidence_locators", [])
    if isinstance(locators, list):
        for loc in locators:
            if not isinstance(loc, str) or loc.startswith("/") or ".." in Path(loc).parts:
                raise EvaluationError(f"unsafe evidence locator in meta-verdict: {loc}")

    return dict(meta)


class FakeJurorAdapter:
    """Test-only deterministic fake juror adapter."""
    is_test_double: bool = True

    def __init__(
        self,
        *,
        juror_id: str,
        specialty: str = "correctness_math",
        model_family: str = "fake-eval-v1",
        preferred_winner: str | None = None,
        positional_bias: str | None = None,
        math_pass: tuple[bool, bool] = (True, True),
        base_scores: tuple[int, int] = (4, 4),
        corrupt_schema: bool = False,
        repeat_order: list[str] | None = None,
        reused_verdict_id: str | None = None,
    ):
        self.juror_id = juror_id
        self.specialty = specialty
        self.model_family = model_family
        self.preferred_winner = preferred_winner
        self.positional_bias = positional_bias
        self.math_pass = math_pass
        self.base_scores = base_scores
        self.corrupt_schema = corrupt_schema
        self.repeat_order = repeat_order
        self.reused_verdict_id = reused_verdict_id

    def evaluate(self, presentation: dict[str, Any]) -> dict[str, Any]:
        if self.corrupt_schema:
            return {"invalid": "payload"}

        order = self.repeat_order or presentation["presentation_order"]
        comparison_id = presentation["comparison_id"]
        order_seed = presentation["order_seed"]
        content_hashes = presentation["content_hashes"]

        if self.positional_bias == "first":
            winner = order[0]
            outcome = "winner"
        elif self.positional_bias == "second":
            winner = order[1]
            outcome = "winner"
        elif self.preferred_winner in ("A", "B"):
            winner = self.preferred_winner
            outcome = "winner"
        elif self.preferred_winner == "tie":
            winner = None
            outcome = "tie"
        elif self.preferred_winner == "inconclusive":
            winner = None
            outcome = "inconclusive"
        else:
            winner = None
            outcome = "inconclusive"

        score_a = {d: self.base_scores[0] for d in DIMENSIONS}
        score_b = {d: self.base_scores[1] for d in DIMENSIONS}

        dimension_scores = [score_a, score_b]
        math_pass = list(self.math_pass)

        if self.reused_verdict_id:
            verdict_id = self.reused_verdict_id
        else:
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

        return {
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


class FakeMetaReviewerAdapter:
    """Test-only deterministic fake meta-reviewer adapter."""
    is_test_double: bool = True

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
        if self.corrupt_schema:
            return {"broken": "response"}

        return {
            "schema_version": SCHEMA_VERSION,
            "meta_verdict_id": f"meta-{comparison_id[:24]}",
            "meta_reviewer_id": self.meta_id,
            "comparison_id": comparison_id,
            "gate_report_id": gate_report_summary["report_id"],
            "confirmed": bool(self.should_confirm and not self.should_veto),
            "vetoed": bool(self.should_veto),
            "veto_reason": self.veto_reason if self.should_veto else None,
            "consistent_verdict_count": len(consistent_verdicts),
            "divergence_count": len(divergences),
            "explanation": "Meta-review verification completed against GateReport and jury consistency.",
            "evidence_locators": ["locators/meta/meta-review-01.txt"],
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
    # 1. Anti-replay and order distinction
    if verdict_ab.get("verdict_id") == verdict_ba.get("verdict_id"):
        return False, "duplicate_verdict_id_for_both_orders", None, False
    if verdict_ab.get("presentation_order") != ["A", "B"] or verdict_ba.get("presentation_order") != ["B", "A"]:
        return False, "presentation_order_mismatch", None, False

    winner_ab = verdict_ab.get("winner_neutral_id")
    winner_ba = verdict_ba.get("winner_neutral_id")
    outcome_ab = verdict_ab.get("outcome")
    outcome_ba = verdict_ba.get("outcome")

    # Math correctness check for Candidate B (Challenger, index 1)
    math_ab = verdict_ab.get("correctness_math_pass", [False, False])
    math_ba = verdict_ba.get("correctness_math_pass", [False, False])

    math_b_pass = bool(math_ab[1] and math_ba[1])

    if math_ab != math_ba:
        return False, "inconsistent_math_verification", None, False

    if outcome_ab != outcome_ba:
        return False, f"outcome_mismatch:{outcome_ab}_vs_{outcome_ba}", None, math_b_pass

    scores_ab = verdict_ab.get("dimension_scores", [{}, {}])
    scores_ba = verdict_ba.get("dimension_scores", [{}, {}])
    for idx in (0, 1):
        for dim in DIMENSIONS:
            val_ab = scores_ab[idx].get(dim, 0)
            val_ba = scores_ba[idx].get(dim, 0)
            if abs(val_ab - val_ba) > tolerance:
                return False, f"dimension_score_drift:{dim}", None, math_b_pass

    if outcome_ab == "winner":
        if winner_ab == winner_ba:
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

    # First pass: restore write permissions recursively
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


def _revalidate_published_evaluation(
    root: Path,
    eval_dir: Path,
    *,
    expected_run_id: str,
    expected_cycle_id: int,
    expected_candidate_id: str,
    expected_gate_report_locator: str,
) -> tuple[dict[str, Any], list[str]]:
    """Revalidate every cryptographic and semantic M8 publication binding."""
    root = Path(root).resolve()
    try:
        relative_eval_dir = eval_dir.resolve().relative_to(root).as_posix()
    except (OSError, ValueError) as exc:
        raise EvaluationError("published evaluation directory escapes project root") from exc
    canonical_dir = f"state/evaluations/{expected_run_id}/c{expected_cycle_id:04d}"
    if relative_eval_dir != canonical_dir:
        raise EvaluationError("published evaluation directory is not canonical")
    _contained(root, canonical_dir, True)

    manifest_path = eval_dir / "manifest.json"
    eval_path = eval_dir / "evaluation.json"
    meta_path = eval_dir / "meta-verdict.json"
    verdicts_dir = eval_dir / "verdicts"

    if not manifest_path.exists() or not eval_path.exists() or not meta_path.exists() or not verdicts_dir.is_dir():
        raise EvaluationError("published evaluation directory is missing core artifacts")

    manifest, raw_man = _read_json(manifest_path)
    eval_report, raw_eval = _read_json(eval_path)
    meta_verdict, raw_meta = _read_json(meta_path)

    _validate_schema(root, EVALUATION_MANIFEST_SCHEMA, manifest)
    _validate_schema(root, EVALUATION_REPORT_SCHEMA, eval_report)
    _validate_schema(root, META_VERDICT_SCHEMA, meta_verdict)
    _require_canonical_json(manifest, raw_man, "evaluation manifest")
    _require_canonical_json(eval_report, raw_eval, "evaluation report")
    _require_canonical_json(meta_verdict, raw_meta, "meta-verdict")

    if (
        manifest.get("run_id") != expected_run_id
        or manifest.get("cycle_id") != expected_cycle_id
        or manifest.get("candidate_id") != expected_candidate_id
        or manifest.get("gate_report_locator") != expected_gate_report_locator
    ):
        raise EvaluationError("published evaluation manifest does not match expected run/cycle/candidate")

    if (
        eval_report.get("run_id") != expected_run_id
        or eval_report.get("cycle_id") != expected_cycle_id
        or eval_report.get("candidate_id") != expected_candidate_id
        or eval_report.get("gate_report_locator") != expected_gate_report_locator
    ):
        raise EvaluationError("published evaluation report does not match expected run/cycle/candidate")

    shared_fields = (
        "evaluation_id",
        "comparison_id",
        "run_id",
        "cycle_id",
        "candidate_id",
        "gate_report_locator",
        "base_hash",
        "candidate_content_hash",
        "diversity_assurance",
    )
    if any(manifest.get(field) != eval_report.get(field) for field in shared_fields):
        raise EvaluationError("published evaluation manifest/report identity differs")
    if manifest.get("rubric_version") != RUBRIC_VERSION:
        raise EvaluationError("published evaluation uses a non-canonical rubric version")
    if eval_report.get("meta_verdict") != meta_verdict:
        raise EvaluationError("embedded and published meta-verdict differ")
    if (
        meta_verdict.get("comparison_id") != eval_report.get("comparison_id")
        or meta_verdict.get("gate_report_id") != eval_report.get("gate_report_id")
    ):
        raise EvaluationError("meta-verdict identity differs from evaluation report")
    for locator in meta_verdict.get("evidence_locators", []):
        if Path(locator).is_absolute() or ".." in Path(locator).parts:
            raise EvaluationError("published meta-verdict contains unsafe evidence locator")

    try:
        gate_report = verify_gate_report(
            root,
            expected_gate_report_locator,
            require_candidate_built=False,
        )
    except Exception as exc:
        raise EvaluationError(f"published evaluation GateReport verification failed: {exc}") from exc
    if (
        gate_report.get("report_hash") != manifest.get("gate_report_hash")
        or gate_report.get("report_id") != eval_report.get("gate_report_id")
        or gate_report.get("run_id") != expected_run_id
        or gate_report.get("cycle_id") != expected_cycle_id
        or gate_report.get("candidate_id") != expected_candidate_id
        or gate_report.get("candidate_content_hash") != eval_report.get("candidate_content_hash")
    ):
        raise EvaluationError("published evaluation GateReport binding differs")

    challenger_dir = root / "versions" / "challengers" / expected_candidate_id
    try:
        challenger_relative = challenger_dir.resolve().relative_to(root).as_posix()
    except (OSError, ValueError) as exc:
        raise EvaluationError("challenger path escapes project root") from exc
    if challenger_relative != f"versions/challengers/{expected_candidate_id}":
        raise EvaluationError("challenger candidate_id is not a canonical direct child")
    challenger_manifest, challenger_manifest_raw = _read_json(challenger_dir / "manifest.json")
    _validate_schema(root, "candidate-manifest.schema.json", challenger_manifest)
    _require_canonical_json(challenger_manifest, challenger_manifest_raw, "challenger manifest")
    base_candidate_id = challenger_manifest.get("base_candidate_id")
    if not isinstance(base_candidate_id, str) or not re.fullmatch(r"v\d{4,}", base_candidate_id):
        raise EvaluationError("challenger base_candidate_id is not canonical")
    champion_dir = root / "versions" / "champion" / base_candidate_id
    champion_manifest, _ = _read_json(champion_dir / "manifest.json")
    _validate_schema(root, "candidate-manifest.schema.json", champion_manifest)
    champion_hash = _candidate_content_hash(champion_dir, champion_manifest)
    challenger_hash = _candidate_content_hash(challenger_dir, challenger_manifest)
    if (
        champion_manifest.get("candidate_id") != base_candidate_id
        or champion_hash != champion_manifest.get("content_hash")
        or challenger_hash != challenger_manifest.get("content_hash")
        or challenger_manifest.get("candidate_id") != expected_candidate_id
        or challenger_manifest.get("base_hash") != champion_hash
        or eval_report.get("base_hash") != champion_hash
        or eval_report.get("candidate_content_hash") != challenger_hash
    ):
        raise EvaluationError("published evaluation candidate/base binding differs")

    expected_comparison_payload = {
        'candidate_hashes': [champion_hash, challenger_hash],
        'rubric_version': RUBRIC_VERSION,
        'order_seed': eval_report['order_seed'],
    }
    expected_comparison_id = f"cmp-{_sha(_json(expected_comparison_payload))}"
    expected_evaluation_payload = {
        'comparison_id': expected_comparison_id,
        'candidate_id': expected_candidate_id,
    }
    expected_evaluation_id = f"eval-{_sha(_json(expected_evaluation_payload))[:32]}"
    if (
        eval_report.get("comparison_id") != expected_comparison_id
        or eval_report.get("evaluation_id") != expected_evaluation_id
    ):
        raise EvaluationError("published evaluation identity is not content-addressed to its comparison")

    # Verify verdict files
    verdict_files = sorted(verdicts_dir.glob("*.json"))
    if len(verdict_files) != 6:
        raise EvaluationError(f"published evaluation must have exactly 6 verdicts, found {len(verdict_files)}")

    computed_verdict_hashes: dict[str, str] = {}
    verdicts: list[dict[str, Any]] = []
    for vf in verdict_files:
        v_data, v_raw = _read_json(vf)
        _validate_schema(root, EVALUATION_SCHEMA, v_data)
        _require_canonical_json(v_data, v_raw, "jury verdict")
        v_id = v_data["verdict_id"]
        if vf.name != f"{v_id}.json":
            raise EvaluationError("verdict filename does not match verdict_id")
        if v_id in computed_verdict_hashes:
            raise EvaluationError("published evaluation contains duplicate verdict_id")
        if (
            v_data.get("comparison_id") != eval_report.get("comparison_id")
            or v_data.get("candidate_neutral_ids") != ["A", "B"]
            or v_data.get("content_hashes") != [champion_hash, challenger_hash]
            or v_data.get("order_seed") != eval_report.get("order_seed")
            or v_data.get("rubric_version") != manifest.get("rubric_version")
        ):
            raise EvaluationError("published verdict presentation binding differs")
        for candidate_scores in v_data.get("dimension_scores", []):
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or value < 0
                or value > 5
                for value in candidate_scores.values()
            ):
                raise EvaluationError("published verdict contains a non-finite or out-of-range score")
        for locator in v_data.get("evidence_locators", []):
            if Path(locator).is_absolute() or ".." in Path(locator).parts:
                raise EvaluationError("published verdict contains unsafe evidence locator")
        v_hash = _sha(v_raw)
        computed_verdict_hashes[v_id] = v_hash
        verdicts.append(v_data)

    if manifest.get("verdict_hashes") != computed_verdict_hashes:
        raise EvaluationError("published manifest verdict_hashes mismatch")

    if manifest.get("meta_verdict_hash") != _sha(raw_meta):
        raise EvaluationError("published manifest meta_verdict_hash mismatch")

    if manifest.get("evaluation_report_hash") != _sha(raw_eval):
        raise EvaluationError("published manifest evaluation_report_hash mismatch")

    report_verdict_ids = eval_report.get("verdict_ids", [])
    if len(report_verdict_ids) != len(set(report_verdict_ids)) or set(report_verdict_ids) != set(computed_verdict_hashes):
        raise EvaluationError("evaluation report verdict_ids differ from published verdicts")

    expected_jurors = {juror_id for juror_id, _, _ in JUROR_SPECIALTIES}
    grouped: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}
    for verdict in verdicts:
        juror_id = verdict.get("juror_id")
        if juror_id not in expected_jurors:
            raise EvaluationError("published verdict has non-canonical juror_id")
        order = tuple(verdict["presentation_order"])
        if order in grouped.setdefault(juror_id, {}):
            raise EvaluationError("published jury contains duplicate presentation order")
        grouped[juror_id][order] = verdict
    if set(grouped) != expected_jurors or any(set(items) != {("A", "B"), ("B", "A")} for items in grouped.values()):
        raise EvaluationError("published jury is not three complete inversion pairs")

    report_jurors = eval_report.get("juror_evaluations", [])
    by_juror = {item.get("juror_id"): item for item in report_jurors}
    if len(by_juror) != 3 or set(by_juror) != expected_jurors:
        raise EvaluationError("evaluation report juror_evaluations are not canonical")

    recomputed: list[dict[str, Any]] = []
    for juror_id, specialty, _ in JUROR_SPECIALTIES:
        verdict_ab = grouped[juror_id][("A", "B")]
        verdict_ba = grouped[juror_id][("B", "A")]
        consistent, reason, winner, math_pass = check_inversion_consistency(verdict_ab, verdict_ba)
        reported = by_juror[juror_id]
        expected_values = {
            "specialty": specialty,
            "consistent": consistent,
            "inconsistency_reason": reason,
            "inferred_winner": winner,
            "candidate_b_math_pass": math_pass,
            "verdict_ab_id": verdict_ab["verdict_id"],
            "verdict_ba_id": verdict_ba["verdict_id"],
        }
        if any(reported.get(key) != value for key, value in expected_values.items()):
            raise EvaluationError("evaluation report jury aggregation differs from verdicts")
        recomputed.append(reported)

    consistent_results = [item for item in recomputed if item["consistent"]]
    challenger_wins = sum(item["inferred_winner"] == "B" for item in consistent_results)
    champion_wins = sum(item["inferred_winner"] == "A" for item in consistent_results)
    ties = sum(item["inferred_winner"] == "tie" for item in consistent_results)
    divergent_count = len(recomputed) - len(consistent_results)
    all_math_pass = bool(consistent_results) and all(item["candidate_b_math_pass"] for item in consistent_results)
    meta_confirmed = bool(meta_verdict.get("confirmed") and not meta_verdict.get("vetoed"))
    if challenger_wins >= 2 and meta_confirmed and all_math_pass and gate_report["overall_pass"] and gate_report["correctness_math_pass"]:
        expected_outcome, expected_eligible = "challenger_favored", True
    elif champion_wins >= 2:
        expected_outcome, expected_eligible = "champion_favored", False
    elif ties >= 2:
        expected_outcome, expected_eligible = "tie", False
    else:
        expected_outcome, expected_eligible = "inconclusive", False
    expected_aggregates = {
        "total_jurors": 3,
        "consistent_jurors": len(consistent_results),
        "divergent_jurors": divergent_count,
        "challenger_wins": challenger_wins,
        "champion_wins": champion_wins,
        "ties": ties,
        "meta_confirmed": meta_confirmed,
        "overall_outcome": expected_outcome,
        "challenger_eligible": expected_eligible,
        "correctness_math_pass": all_math_pass,
    }
    if any(eval_report.get(key) != value for key, value in expected_aggregates.items()):
        raise EvaluationError("evaluation report aggregate differs from canonical jury result")
    if (
        meta_verdict.get("consistent_verdict_count") != len(consistent_results)
        or meta_verdict.get("divergence_count") != divergent_count
    ):
        raise EvaluationError("meta-verdict counts differ from canonical jury result")
    family_count = len({item["model_family"] for item in recomputed})
    expected_diversity = "full_diversity" if family_count == 3 else "reduced_diversity_assurance"
    if eval_report.get("diversity_assurance") != expected_diversity:
        raise EvaluationError("evaluation diversity assurance differs from model families")

    walked_entries = _walk(eval_dir)
    expected_entries = {
        "evaluation.json",
        "manifest.json",
        "meta-verdict.json",
        "verdicts",
        *(f"verdicts/{verdict_id}.json" for verdict_id in computed_verdict_hashes),
    }
    actual_entries = {relative for relative, _, _ in walked_entries}
    if actual_entries != expected_entries:
        raise EvaluationError("published evaluation directory contains unexpected artifacts")
    if stat.S_IMODE(eval_dir.lstat().st_mode) != 0o555 or any(
        stat.S_IMODE(info.st_mode) != (0o555 if stat.S_ISDIR(info.st_mode) else 0o444)
        for _, _, info in walked_entries
    ):
        raise EvaluationError("published evaluation permissions are not immutable")

    current_tree_hash = tree_hash(eval_dir, exclude={"manifest.json"})
    if manifest.get("tree_content_hash") != current_tree_hash:
        raise EvaluationError("published evaluation tree content hash mismatch")

    recovered_artifact_hashes = sorted([
        _sha(raw_eval),
        _sha(raw_meta),
        _sha(raw_man),
        *computed_verdict_hashes.values(),
    ])

    return eval_report, recovered_artifact_hashes


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
    allow_test_doubles: bool = False,
    store: DurableStore | None = None,
    fault: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Execute the canonical blind evaluation and meta-review pipeline for M8.

    Preconditions:
      - Active state in DurableStore must be State.GATES_PASSED
      - Active GATES_PASSED event contains candidate_hash matching GateReport candidate_hash
      - GateReport is verified with canonical verify_gate_report() and bound to event
      - cycle_id, candidate_id, and gate_report_locator match active GATES_PASSED event
      - Operational juror and meta-reviewer adapters are explicitly configured
      - Test doubles are rejected unless allow_test_doubles=True
      - Champion and Challenger trees match content hashes
    Postconditions:
      - All 6 verdicts validated, locked in immutable write-once storage
      - Inversion consistency checked for 3 juror pairs
      - Meta-review executed and persisted
      - State transitioned to State.EVALUATED in DurableStore
      - Challenger and champion tree hashes verified unchanged
    """
    if not isinstance(run_id, str) or not run_id:
        raise EvaluationError("run_id must be a non-empty string")
    if cycle_id is not None and (
        isinstance(cycle_id, bool) or not isinstance(cycle_id, int) or cycle_id < 0
    ):
        raise EvaluationError("cycle_id must be a non-negative integer")
    if candidate_id is not None and (not isinstance(candidate_id, str) or not candidate_id):
        raise EvaluationError("candidate_id must be a non-empty string")
    if gate_report_locator is not None and (
        not isinstance(gate_report_locator, str) or not gate_report_locator
    ):
        raise EvaluationError("gate_report_locator must be a non-empty string")
    if not isinstance(allow_test_doubles, bool):
        raise EvaluationError(f"allow_test_doubles must be a boolean, got {type(allow_test_doubles).__name__}")
    if isinstance(order_seed, bool) or not isinstance(order_seed, int) or order_seed < 0:
        raise EvaluationError("order_seed must be a non-negative integer")
    if juror_adapters is not None and not isinstance(juror_adapters, Mapping):
        raise EvaluationError("juror_adapters must be an object mapping canonical juror IDs to adapters")
    if model_families is not None and not isinstance(model_families, Mapping):
        raise EvaluationError("model_families must be an object mapping canonical juror IDs to identifiers")
    root = Path(root).resolve()
    store = store or DurableStore(root)

    def _trigger_fault(stage: str) -> None:
        if fault:
            fault(stage)

    # 1. Verify state and event log binding
    events = store.read_events(run_id)
    if not events:
        raise EvaluationError("run has no events")

    last_event = events[-1]
    current_state = State(last_event["state_to"])
    effective_cycle_id = last_event["cycle_id"]
    event_payload = last_event.get("payload", {})
    event_candidate_id = event_payload.get("candidate_id")

    # A completed delivery is a read-only replay: revalidate the immutable
    # publication and its exact EVALUATED event rather than requiring adapters
    # or attempting another jury run.
    if current_state == State.EVALUATED and last_event.get("event_type") == "EVALUATED":
        if cycle_id is not None and cycle_id != effective_cycle_id:
            raise EvaluationError(
                f"cycle_id {cycle_id} diverges from active EVALUATED event cycle {effective_cycle_id}"
            )
        if candidate_id is not None and candidate_id != event_candidate_id:
            raise EvaluationError(
                f"candidate_id '{candidate_id}' diverges from active EVALUATED event candidate '{event_candidate_id}'"
            )
        if not isinstance(event_candidate_id, str) or not event_candidate_id:
            raise EvaluationError("active EVALUATED event is missing candidate_id")
        canonical_locator = f"state/evaluations/{run_id}/c{effective_cycle_id:04d}/evaluation.json"
        eval_dir = root / "state" / "evaluations" / run_id / f"c{effective_cycle_id:04d}"
        manifest, _ = _read_json(eval_dir / "manifest.json")
        published_gate_locator = manifest.get("gate_report_locator")
        if not isinstance(published_gate_locator, str) or not published_gate_locator:
            raise EvaluationError("published evaluation manifest is missing gate_report_locator")
        if gate_report_locator is not None and gate_report_locator != published_gate_locator:
            raise EvaluationError("gate_report_locator diverges from published evaluation")
        existing_report, recovered_hashes = _revalidate_published_evaluation(
            root,
            eval_dir,
            expected_run_id=run_id,
            expected_cycle_id=effective_cycle_id,
            expected_candidate_id=event_candidate_id,
            expected_gate_report_locator=published_gate_locator,
        )
        try:
            published_gate = verify_gate_report(
                root,
                published_gate_locator,
                require_candidate_built=False,
            )
        except Exception as exc:
            raise EvaluationError("published evaluation GateReport verification failed") from exc
        if existing_report.get("order_seed") != order_seed:
            raise EvaluationError("order_seed diverges from published evaluation")
        if model_families is not None:
            reported_families = {
                item["juror_id"]: item["model_family"]
                for item in existing_report["juror_evaluations"]
            }
            if dict(model_families) != reported_families:
                raise EvaluationError("model_families diverges from published evaluation")
        if (
            event_payload.get("candidate_content_hash") != existing_report.get("candidate_content_hash")
            or event_payload.get("candidate_hash") != published_gate.get("candidate_hash")
            or event_payload.get("base_hash") != existing_report.get("base_hash")
            or event_payload.get("evaluation_id") != existing_report.get("evaluation_id")
            or event_payload.get("comparison_id") != existing_report.get("comparison_id")
            or event_payload.get("overall_outcome") != existing_report.get("overall_outcome")
            or event_payload.get("challenger_eligible") != existing_report.get("challenger_eligible")
            or event_payload.get("verdict_ids") != existing_report.get("verdict_ids")
            or event_payload.get("evaluation_locator") != canonical_locator
            or last_event.get("artifact_hashes") != recovered_hashes
        ):
            raise EvaluationError("EVALUATED event binding differs from published evaluation")
        return existing_report

    if current_state != State.GATES_PASSED:
        raise EvaluationError(f"evaluation requires state GATES_PASSED, found: {current_state}")

    event_report_locator = event_payload.get("report_locator")
    event_candidate_hash = event_payload.get("candidate_hash")

    if not event_candidate_id or not event_report_locator:
        raise EvaluationError("active GATES_PASSED event is missing candidate_id or report_locator in payload")

    if not event_candidate_hash or not isinstance(event_candidate_hash, str) or len(event_candidate_hash) != 64:
        raise EvaluationError("active GATES_PASSED event is missing candidate_hash in payload")

    # Strict parameter consistency checks
    if cycle_id is not None:
        if cycle_id != effective_cycle_id:
            raise EvaluationError(f"cycle_id {cycle_id} diverges from active GATES_PASSED event cycle {effective_cycle_id}")

    if candidate_id is not None:
        if candidate_id != event_candidate_id:
            raise EvaluationError(f"candidate_id '{candidate_id}' diverges from active GATES_PASSED event candidate '{event_candidate_id}'")

    if gate_report_locator is not None:
        if gate_report_locator != event_report_locator:
            raise EvaluationError("gate_report_locator diverges from active GATES_PASSED event report locator")

    # 2. Canonical verification of GateReport
    try:
        gate_report = verify_gate_report(root, event_report_locator, store=store, require_candidate_built=False)
    except Exception as exc:
        raise EvaluationError(f"gate report verification failed: {exc}") from exc

    if gate_report["run_id"] != run_id or gate_report["cycle_id"] != effective_cycle_id:
        raise EvaluationError("gate report run/cycle identity differs from active event")
    if gate_report["candidate_id"] != event_candidate_id:
        raise EvaluationError("gate report candidate_id differs from active event")
    if gate_report.get("candidate_hash") != event_candidate_hash:
        raise EvaluationError(
            f"active GATES_PASSED event candidate_hash '{event_candidate_hash}' does not match GateReport candidate_hash '{gate_report.get('candidate_hash')}'"
        )
    if not gate_report.get("overall_pass"):
        raise EvaluationError("GateReport overall_pass is false; candidate cannot proceed to jury")
    if not gate_report.get("correctness_math_pass"):
        raise EvaluationError("GateReport correctness_math_pass is false; candidate cannot proceed to jury")

    # 3. Locate and verify the Challenger and its explicitly bound Champion.
    challenger_dir = root / "versions/challengers" / event_candidate_id
    try:
        challenger_relative = challenger_dir.resolve().relative_to(root).as_posix()
    except (OSError, ValueError) as exc:
        raise EvaluationError("challenger path escapes project root") from exc
    if challenger_relative != f"versions/challengers/{event_candidate_id}" or not challenger_dir.is_dir():
        raise EvaluationError(f"challenger directory missing: {event_candidate_id}")

    chall_manifest, chall_manifest_raw = _read_json(challenger_dir / "manifest.json")
    _validate_schema(root, "candidate-manifest.schema.json", chall_manifest)
    _require_canonical_json(chall_manifest, chall_manifest_raw, "challenger manifest")
    if chall_manifest.get("candidate_id") != event_candidate_id:
        raise EvaluationError("challenger manifest candidate_id differs from active event")
    base_candidate_id = chall_manifest.get("base_candidate_id")
    if not isinstance(base_candidate_id, str) or not re.fullmatch(r"v\d{4,}", base_candidate_id):
        raise EvaluationError("challenger base_candidate_id is not canonical")
    champion_dir = root / "versions" / "champion" / base_candidate_id
    if not champion_dir.is_dir() or champion_dir.resolve().parent != (root / "versions/champion").resolve():
        raise EvaluationError(f"bound champion directory missing: {base_candidate_id}")
    champ_manifest, _ = _read_json(champion_dir / "manifest.json")
    _validate_schema(root, "candidate-manifest.schema.json", champ_manifest)
    if champ_manifest.get("candidate_id") != base_candidate_id:
        raise EvaluationError("champion manifest candidate_id differs from challenger base_candidate_id")

    champ_hash_before = _candidate_content_hash(champion_dir, champ_manifest)
    chall_hash_before = _candidate_content_hash(challenger_dir, chall_manifest)

    if champ_hash_before != champ_manifest.get("content_hash"):
        raise EvaluationError("champion content hash mismatch")
    if chall_hash_before != chall_manifest.get("content_hash"):
        raise EvaluationError("challenger content hash mismatch")
    if chall_hash_before != gate_report["candidate_content_hash"]:
        raise EvaluationError("challenger content hash mismatch with GateReport")
    if chall_manifest.get("base_hash") != champ_hash_before:
        raise EvaluationError("challenger base_hash mismatch with bound champion")

    eval_dir = root / f"state/evaluations/{run_id}/c{effective_cycle_id:04d}"
    _managed_directory(root, f"state/evaluations/{run_id}", create=False)

    # 4. Fail-closed Operational Boundary Check.  A crash recovery consumes
    # only the already-published immutable evidence and therefore must not
    # depend on the continued availability of external adapters.
    if not eval_dir.exists():
        if juror_adapters is None:
            raise EvaluationError("no operational juror adapter configured; operational evaluations require explicit juror adapters")
        if meta_adapter is None:
            raise EvaluationError("no operational meta-reviewer adapter configured; operational evaluations require an explicit meta-reviewer adapter")

        if not allow_test_doubles:
            for jid, adapter in juror_adapters.items():
                if getattr(adapter, "is_test_double", False) or getattr(adapter, "requires_test_mode", False):
                    raise EvaluationError(
                        f"test double detected for juror adapter '{jid}'; test doubles require allow_test_doubles=True"
                    )
            if getattr(meta_adapter, "is_test_double", False) or getattr(meta_adapter, "requires_test_mode", False):
                raise EvaluationError(
                    "test double detected for meta-reviewer adapter; test doubles require allow_test_doubles=True"
                )

        _trigger_fault("after_preconditions_verified")

    # 5. Check for already published evaluation (Idempotent Recovery & Crash Safety)
    if eval_dir.exists():
        existing_report, recovered_hashes = _revalidate_published_evaluation(
            root,
            eval_dir,
            expected_run_id=run_id,
            expected_cycle_id=effective_cycle_id,
            expected_candidate_id=event_candidate_id,
            expected_gate_report_locator=event_report_locator,
        )
        if existing_report.get("order_seed") != order_seed:
            raise EvaluationError("order_seed diverges from published evaluation")
        if model_families is not None:
            reported_families = {
                item["juror_id"]: item["model_family"]
                for item in existing_report["juror_evaluations"]
            }
            if dict(model_families) != reported_families:
                raise EvaluationError("model_families diverges from published evaluation")
        # Commit EVALUATED event if crash happened between publish and event
        event_id = f"evt-evaluated-c{effective_cycle_id:04d}-{event_candidate_id}"
        idempotency_key = f"evaluated:{run_id}:c{effective_cycle_id:04d}:{event_candidate_id}"
        store.record(
            run_id=run_id,
            target=State.EVALUATED,
            event_id=event_id,
            idempotency_key=idempotency_key,
            actor_id="M00",
            event_type="EVALUATED",
            payload={
                "candidate_id": event_candidate_id,
                "candidate_content_hash": chall_hash_before,
                "candidate_hash": event_candidate_hash,
                "base_hash": champ_hash_before,
                "evaluation_id": existing_report["evaluation_id"],
                "comparison_id": existing_report["comparison_id"],
                "overall_outcome": existing_report["overall_outcome"],
                "challenger_eligible": existing_report["challenger_eligible"],
                "verdict_ids": existing_report["verdict_ids"],
                "evaluation_locator": f"state/evaluations/{run_id}/c{effective_cycle_id:04d}/evaluation.json",
            },
            artifact_hashes=recovered_hashes,
        )
        return existing_report

    # 6. Build sanitized BlindComparisonBundle
    bundle = BlindComparisonBundle.create(
        root,
        champion_dir=champion_dir,
        challenger_dir=challenger_dir,
        order_seed=order_seed,
    )

    load_rubric(root)

    adapters = dict(juror_adapters)
    expected_jurors = {juror_id for juror_id, _, _ in JUROR_SPECIALTIES}
    if set(adapters) != expected_jurors:
        raise EvaluationError("juror adapters must contain exactly the three canonical juror IDs")
    families = dict({
        "juror-math": "eval-math-family",
        "juror-contrib": "eval-contrib-family",
        "juror-clarity": "eval-clarity-family",
    } if model_families is None else model_families)
    if set(families) != expected_jurors or any(not isinstance(value, str) or not value.strip() for value in families.values()):
        raise EvaluationError("model_families must map exactly the canonical jurors to non-empty identifiers")

    unique_families = {families.get(jid) for jid, _, _ in JUROR_SPECIALTIES}
    diversity_assurance = "full_diversity" if len(unique_families) >= 3 else "reduced_diversity_assurance"

    verdicts: list[dict[str, Any]] = []
    verdict_hashes: dict[str, str] = {}
    juror_results: list[dict[str, Any]] = []
    consistent_verdicts: list[dict[str, Any]] = []
    divergences: list[dict[str, Any]] = []
    seen_verdict_ids: set[str] = set()

    # 7. Execute A/B and B/A presentations for all 3 jurors
    for juror_id, specialty, _ in JUROR_SPECIALTIES:
        adapter = adapters.get(juror_id)
        if not adapter:
            raise EvaluationError(f"missing adapter for juror: {juror_id}")

        # Presentation 1: A/B
        pres_ab = bundle.presentation_for_order(["A", "B"])
        try:
            raw_v_ab = adapter.evaluate(pres_ab)
        except Exception as exc:
            raise EvaluationError(f"juror adapter '{juror_id}' failed for A/B presentation") from exc
        if not isinstance(raw_v_ab, Mapping):
            raise EvaluationError(f"juror adapter '{juror_id}' returned a non-object verdict")
        val_v_ab = _validate_juror_verdict_response(
            root,
            raw_v_ab,
            expected_juror_id=juror_id,
            expected_presentation_order=["A", "B"],
            bundle=bundle,
            seen_verdict_ids=seen_verdict_ids,
        )

        # Presentation 2: B/A
        pres_ba = bundle.presentation_for_order(["B", "A"])
        try:
            raw_v_ba = adapter.evaluate(pres_ba)
        except Exception as exc:
            raise EvaluationError(f"juror adapter '{juror_id}' failed for B/A presentation") from exc
        if not isinstance(raw_v_ba, Mapping):
            raise EvaluationError(f"juror adapter '{juror_id}' returned a non-object verdict")
        val_v_ba = _validate_juror_verdict_response(
            root,
            raw_v_ba,
            expected_juror_id=juror_id,
            expected_presentation_order=["B", "A"],
            bundle=bundle,
            seen_verdict_ids=seen_verdict_ids,
        )

        for v in (val_v_ab, val_v_ba):
            v_bytes = _json(v)
            verdict_hashes[v["verdict_id"]] = _sha(v_bytes)
            verdicts.append(v)

        _trigger_fault(f"after_verdicts_evaluated_{juror_id}")

        # Check inversion consistency
        is_consistent, reason, inferred_winner, math_pass = check_inversion_consistency(val_v_ab, val_v_ba)

        juror_eval = {
            "juror_id": juror_id,
            "specialty": specialty,
            "model_family": families.get(juror_id, "unknown"),
            "consistent": is_consistent,
            "inconsistency_reason": reason,
            "inferred_winner": inferred_winner,
            "candidate_b_math_pass": math_pass,
            "verdict_ab_id": val_v_ab["verdict_id"],
            "verdict_ba_id": val_v_ba["verdict_id"],
        }
        juror_results.append(juror_eval)

        if is_consistent:
            consistent_verdicts.append(juror_eval)
        else:
            divergences.append(juror_eval)

    # 8. Execute Meta-Review
    gate_summary = {
        "report_id": gate_report["report_id"],
        "overall_pass": gate_report["overall_pass"],
        "correctness_math_pass": gate_report["correctness_math_pass"],
    }

    try:
        raw_meta = meta_adapter.review(
            comparison_id=bundle.comparison_id,
            consistent_verdicts=consistent_verdicts,
            divergences=divergences,
            gate_report_summary=gate_summary,
        )
    except Exception as exc:
        raise EvaluationError("meta-reviewer adapter failed") from exc
    if not isinstance(raw_meta, Mapping):
        raise EvaluationError("meta-reviewer adapter returned a non-object verdict")

    meta_result = _validate_meta_verdict_response(
        root,
        raw_meta,
        bundle=bundle,
        gate_report=gate_report,
        consistent_count=len(consistent_verdicts),
        divergence_count=len(divergences),
    )

    _trigger_fault("after_meta_review_evaluated")

    # 9. Aggregation Logic
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

    eval_id = f"eval-{_sha(_json({'comparison_id': bundle.comparison_id, 'candidate_id': event_candidate_id}))[:32]}"
    report = {
        "schema_version": SCHEMA_VERSION,
        "evaluation_id": eval_id,
        "run_id": run_id,
        "cycle_id": effective_cycle_id,
        "comparison_id": bundle.comparison_id,
        "candidate_id": event_candidate_id,
        "base_hash": bundle.content_hashes[0],
        "candidate_content_hash": bundle.content_hashes[1],
        "gate_report_id": gate_report["report_id"],
        "gate_report_locator": event_report_locator,
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
    _validate_schema(root, EVALUATION_REPORT_SCHEMA, report)

    # 10. Write-Once Staging and Transactional Publishing
    _managed_directory(root, f"state/evaluations/{run_id}", create=True)
    staging = tempfile.mkdtemp(prefix=f".staging_c{effective_cycle_id:04d}_", dir=eval_dir.parent)
    staging_path = Path(staging)

    try:
        staging_verdicts = staging_path / "verdicts"
        staging_verdicts.mkdir(parents=True, exist_ok=True)

        for v in verdicts:
            v_path = staging_verdicts / f"{v['verdict_id']}.json"
            _write_synced_file(v_path, _json(v))

        meta_path = staging_path / "meta-verdict.json"
        meta_bytes = _json(meta_result)
        _write_synced_file(meta_path, meta_bytes)
        meta_hash = _sha(meta_bytes)

        report_path = staging_path / "evaluation.json"
        report_bytes = _json(report)
        _write_synced_file(report_path, report_bytes)
        report_hash = _sha(report_bytes)

        # Compute content hash of evaluation directory before manifest
        staging_tree_content_hash = tree_hash(staging_path, exclude={"manifest.json"})

        manifest_data = {
            "schema_version": SCHEMA_VERSION,
            "evaluation_id": eval_id,
            "comparison_id": bundle.comparison_id,
            "run_id": run_id,
            "cycle_id": effective_cycle_id,
            "candidate_id": event_candidate_id,
            "gate_report_locator": event_report_locator,
            "gate_report_hash": gate_report["report_hash"],
            "base_hash": bundle.content_hashes[0],
            "candidate_content_hash": bundle.content_hashes[1],
            "rubric_version": RUBRIC_VERSION,
            "diversity_assurance": diversity_assurance,
            "verdict_hashes": verdict_hashes,
            "meta_verdict_hash": meta_hash,
            "evaluation_report_hash": report_hash,
            "tree_content_hash": staging_tree_content_hash,
            "created_at": _now(),
        }
        _validate_schema(root, EVALUATION_MANIFEST_SCHEMA, manifest_data)
        manifest_bytes = _json(manifest_data)
        manifest_hash = _sha(manifest_bytes)
        _write_synced_file(staging_path / "manifest.json", manifest_bytes)

        # Sync staging directory tree before permission changes
        _fsync_tree_dirs(staging_path)

        # Harden permissions in staging (files 0444, dirs 0555)
        _harden_read_only(staging_path)

        # Sync staging directory tree after permission changes to persist directory inode changes
        _fsync_tree_dirs(staging_path)

        _trigger_fault("before_publish_rename")

        # Atomic publish
        if eval_dir.exists():
            raise EvaluationError(f"evaluation directory already exists: {eval_dir}")
        os.replace(staging_path, eval_dir)
        _fsync_dir(eval_dir.parent)

    finally:
        if staging_path.exists():
            _cleanup_staging(staging_path)

    _trigger_fault("after_publish_rename")

    # 11. Re-verify Published Directory and Content Immutability
    _revalidate_published_evaluation(
        root,
        eval_dir,
        expected_run_id=run_id,
        expected_cycle_id=effective_cycle_id,
        expected_candidate_id=event_candidate_id,
        expected_gate_report_locator=event_report_locator,
    )

    champ_hash_after = _candidate_content_hash(champion_dir, champ_manifest)
    chall_hash_after = _candidate_content_hash(challenger_dir, chall_manifest)
    if champ_hash_after != champ_hash_before:
        raise EvaluationError("champion tree mutated during evaluation")
    if chall_hash_after != chall_hash_before:
        raise EvaluationError("challenger tree mutated during evaluation")

    _trigger_fault("before_evaluated_event")

    # 12. Record EVALUATED event in DurableStore
    event_id = f"evt-evaluated-c{effective_cycle_id:04d}-{event_candidate_id}"
    idempotency_key = f"evaluated:{run_id}:c{effective_cycle_id:04d}:{event_candidate_id}"
    store.record(
        run_id=run_id,
        target=State.EVALUATED,
        event_id=event_id,
        idempotency_key=idempotency_key,
        actor_id="M00",
        event_type="EVALUATED",
        payload={
            "candidate_id": event_candidate_id,
            "candidate_content_hash": bundle.content_hashes[1],
            "candidate_hash": event_candidate_hash,
            "base_hash": bundle.content_hashes[0],
            "evaluation_id": eval_id,
            "comparison_id": bundle.comparison_id,
            "overall_outcome": overall_outcome,
            "challenger_eligible": challenger_eligible,
            "verdict_ids": [v["verdict_id"] for v in verdicts],
            "evaluation_locator": f"state/evaluations/{run_id}/c{effective_cycle_id:04d}/evaluation.json",
        },
        artifact_hashes=sorted([report_hash, meta_hash, manifest_hash, *verdict_hashes.values()]),
    )

    _trigger_fault("after_evaluated_event")
    return report
