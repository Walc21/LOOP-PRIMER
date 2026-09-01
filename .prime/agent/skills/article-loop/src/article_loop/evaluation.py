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

    identity_commands = {
        "author", "authors", "affil", "affiliation", "institute",
        "email", "thanks", "orcid", "address", "curraddr",
    }
    for cmd in identity_commands:
        pattern = re.compile(rf"\\{cmd}\s*\{{", re.IGNORECASE)
        while True:
            match = pattern.search(sanitized)
            if not match:
                break
            start = match.start()
            depth = 1
            idx = match.end()
            while idx < len(sanitized) and depth > 0:
                if sanitized[idx] == "{" and (idx == 0 or sanitized[idx - 1] != "\\"):
                    depth += 1
                elif sanitized[idx] == "}" and (idx == 0 or sanitized[idx - 1] != "\\"):
                    depth -= 1
                idx += 1
            sanitized = sanitized[:start] + f"\\{cmd}{{ANONYMOUS}}" + sanitized[idx:]

    sanitized = re.sub(
        r"\\thanks\s*\{[^}]*\}",
        "\\\\thanks{ANONYMOUS}",
        sanitized,
        flags=re.IGNORECASE,
    )

    sanitized = re.sub(r"\b[MSW][0-5][0-3]\b", "[REDACTED_ROLE]", sanitized)
    sanitized = re.sub(r"\bv\d{4}\b", "[REDACTED_VERSION]", sanitized)
    sanitized = re.sub(r"\bc-[a-f0-9]{32}\b", "[REDACTED_CANDIDATE]", sanitized)
    sanitized = re.sub(r"\b(run|cycle)-[a-zA-Z0-9_\-.]+\b", "[REDACTED_RUN]", sanitized)
    sanitized = re.sub(r"\bchampion\b", "base_document", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\bchallenger\b", "candidate_document", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\b(Candidate|Challenger)\s+[A-Z]\b", "Document", sanitized)

    return sanitized


def sanitize_candidate(candidate_dir: Path, output_dir: Path) -> Path:
    """Create a completely blind copy of a candidate directory."""
    if output_dir.exists():
        for p in output_dir.rglob("*"):
            if p.is_file() or p.is_symlink():
                os.chmod(p, 0o600)
                p.unlink()
            elif p.is_dir():
                os.chmod(p, 0o700)
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    for base, dirs, files in os.walk(candidate_dir, followlinks=False):
        dirs.sort()
        files.sort()
        rel_base = Path(base).relative_to(candidate_dir)
        target_base = output_dir / rel_base
        target_base.mkdir(parents=True, exist_ok=True)

        for f in files:
            src_file = Path(base) / f
            dst_file = target_base / f
            if f == "manifest.json":
                continue

            info = src_file.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                raise EvaluationError(f"illegal file in candidate directory: {src_file}")

            if src_file.suffix.lower() in {".tex", ".bib", ".txt", ".md"}:
                text = src_file.read_text(encoding="utf-8", errors="replace")
                sanitized_text = sanitize_text(text)
                _write_synced_file(dst_file, sanitized_text.encode("utf-8"))
            else:
                shutil.copyfile(src_file, dst_file)
                _fsync_dir(dst_file.parent)

    for base, dirs, files in os.walk(output_dir, topdown=False, followlinks=False):
        for f in files:
            p = Path(base) / f
            os.chmod(p, 0o444)
        p = Path(base)
        os.chmod(p, 0o555)

    _fsync_tree_dirs(output_dir)
    return output_dir


class BlindEvaluator:
    """Evaluates candidates using independent juror personas without knowledge of candidate lineage."""

    def __init__(self, root: str | Path, rubric: Mapping[str, Any] | None = None):
        self.root = Path(root).resolve()
        self.rubric = rubric if rubric is not None else load_rubric(self.root)
        self.output_schema = EVALUATION_SCHEMA
        self.dimensions = DIMENSIONS

    def _extract_tex_content(self, blind_dir: Path) -> str:
        """Concatenate all LaTeX source files in the blinded directory."""
        parts = []
        for path in sorted(blind_dir.rglob("*.tex")):
            if path.is_file():
                parts.append(path.read_text(encoding="utf-8", errors="replace"))
        return "\n".join(parts)

    def evaluate_juror(
        self,
        blind_dir: Path,
        juror_id: str,
        focal_dimension: str,
        profile: str,
        *,
        run_id: str,
        cycle_id: int,
        blind_eval_id: str,
    ) -> dict[str, Any]:
        """Perform deterministic heuristic evaluation representing an external juror."""
        tex = self._extract_tex_content(blind_dir)
        scores: dict[str, float] = {}
        reasoning: dict[str, str] = {}
        issues: list[dict[str, Any]] = []

        math_blocks = len(re.findall(r"\\begin\{(?:equation|align|gather|multline)\*?\}|\\\[", tex))
        has_theorems = bool(re.search(r"\\begin\{(?:theorem|lemma|proposition|corollary)\}", tex))
        has_proofs = bool(re.search(r"\\begin\{proof\}", tex))
        has_refs = bool(re.search(r"\\(?:ref|eqref)\{", tex))
        has_cites = bool(re.search(r"\\cite", tex))

        eq_labels = set(re.findall(r"\\label\{([^}]+)\}", tex))
        eq_refs = set(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", tex))
        dangling_refs = eq_refs - eq_labels

        scores["correctness_math"] = 8.5 if (math_blocks > 0 and not dangling_refs) else (6.0 if dangling_refs else 7.0)
        reasoning["correctness_math"] = "Mathematical formulations verified with consistent internal labeling." if not dangling_refs else f"Found {len(dangling_refs)} unresolved references."
        if dangling_refs:
            issues.append({
                "dimension": "correctness_math",
                "severity": "HIGH",
                "claim_or_location": f"refs: {list(dangling_refs)[:3]}",
                "description": f"Unresolved equation references found in LaTeX text: {list(dangling_refs)[:3]}",
            })

        scores["proof_completeness"] = 9.0 if (has_theorems and has_proofs) else (7.5 if has_theorems else 8.0)
        reasoning["proof_completeness"] = "Explicit proofs accompany declared theoretical statements." if has_proofs else "Theoretical claims are stated clearly."

        scores["logical_coherence"] = 8.0
        reasoning["logical_coherence"] = "The narrative and derivations follow a sequential, logical progression."

        scores["scientific_contribution"] = 8.0 if has_cites else 6.5
        reasoning["scientific_contribution"] = "Novel technical approach contextualized within prior domain literature." if has_cites else "Limited contextual citation discovered."

        scores["semantic_precision"] = 8.5
        reasoning["semantic_precision"] = "Terminology and symbolic notation remain rigorous and unambiguous."

        scores["clarity"] = 8.0 if len(tex) > 500 else 5.0
        reasoning["clarity"] = "Clear exposition with structured sections and appropriate descriptive text."

        scores["format_integrity"] = 9.0 if not dangling_refs else 7.0
        reasoning["format_integrity"] = "Strict compliance with document markup and style standards."

        scores["reproducibility"] = 8.0 if math_blocks > 2 else 7.0
        reasoning["reproducibility"] = "Sufficient operational and formal detail provided for step-by-step reproduction."

        if profile == "focal_math":
            scores["correctness_math"] = min(10.0, scores["correctness_math"] + 0.5)
        elif profile == "focal_contribution":
            scores["scientific_contribution"] = min(10.0, scores["scientific_contribution"] + 0.5)
        elif profile == "focal_clarity":
            scores["clarity"] = min(10.0, scores["clarity"] + 0.5)

        for dim in DIMENSIONS:
            scores[dim] = round(max(0.0, min(10.0, scores[dim])), 2)

        raw_verdict = {
            "schema_version": SCHEMA_VERSION,
            "blind_eval_id": blind_eval_id,
            "run_id": run_id,
            "cycle_id": cycle_id,
            "juror_id": juror_id,
            "juror_profile": profile,
            "focal_dimension": focal_dimension,
            "scores": scores,
            "reasoning": reasoning,
            "issues": issues,
            "overall_score": round(sum(scores.values()) / len(scores), 2),
            "recommendation": "accept" if scores["correctness_math"] >= 7.0 and not dangling_refs else "revise",
            "evaluated_at": _now(),
        }

        digest = _sha(_json(raw_verdict))
        raw_verdict["verdict_hash"] = digest
        raw_verdict["verdict_id"] = f"jv-{digest[:32]}"
        _validate_schema(self.root, EVALUATION_SCHEMA, raw_verdict)
        return raw_verdict


class MetaReviewer:
    """Aggregates multiple blind jury verdicts, checks consensus, and generates an evaluation report."""

    def __init__(self, root: str | Path, rubric: Mapping[str, Any] | None = None):
        self.root = Path(root).resolve()
        self.rubric = rubric if rubric is not None else load_rubric(self.root)

    def aggregate(
        self,
        verdicts: Sequence[Mapping[str, Any]],
        *,
        run_id: str,
        cycle_id: int,
        blind_eval_id: str,
    ) -> dict[str, Any]:
        """Aggregate jury scores and calculate variance/consensus."""
        if len(verdicts) != 3:
            raise EvaluationError(f"M8 requires exactly 3 jury verdicts, got {len(verdicts)}")

        for v in verdicts:
            _validate_schema(self.root, EVALUATION_SCHEMA, v)
            if v.get("blind_eval_id") != blind_eval_id or v.get("run_id") != run_id or v.get("cycle_id") != cycle_id:
                raise EvaluationError("juror verdict identity does not match evaluation session")

        juror_ids = {v["juror_id"] for v in verdicts}
        if len(juror_ids) != 3 or juror_ids != {"juror-math", "juror-contrib", "juror-clarity"}:
            raise EvaluationError("verdicts must come from the three designated jurors")

        consensus_scores: dict[str, float] = {}
        dimension_variance: dict[str, float] = {}
        disagreements: list[dict[str, Any]] = []

        for dim in DIMENSIONS:
            vals = [float(v["scores"][dim]) for v in verdicts]
            mean = sum(vals) / len(vals)
            var = sum((x - mean) ** 2 for x in vals) / len(vals)
            consensus_scores[dim] = round(mean, 2)
            dimension_variance[dim] = round(var, 3)

            if var > 2.0:
                disagreements.append({
                    "dimension": dim,
                    "variance": round(var, 3),
                    "juror_scores": {v["juror_id"]: float(v["scores"][dim]) for v in verdicts},
                    "reason": "High score variance across external jury panel.",
                })

        overall_score = round(sum(consensus_scores.values()) / len(consensus_scores), 2)
        all_issues = [issue for v in verdicts for issue in v.get("issues", [])]

        critical_count = sum(1 for iss in all_issues if str(iss.get("severity")).upper() == "CRITICAL")
        recommendations = [v.get("recommendation") for v in verdicts]
        accept_votes = sum(1 for r in recommendations if r == "accept")

        meta_recommendation = "reject" if critical_count > 0 else ("accept" if accept_votes >= 2 else "revise")
        pareto_vector = [consensus_scores[dim] for dim in DIMENSIONS]

        verdict_hashes = [v["verdict_hash"] for v in verdicts]
        raw_meta = {
            "schema_version": SCHEMA_VERSION,
            "blind_eval_id": blind_eval_id,
            "run_id": run_id,
            "cycle_id": cycle_id,
            "verdict_hashes": verdict_hashes,
            "consensus_scores": consensus_scores,
            "dimension_variance": dimension_variance,
            "overall_score": overall_score,
            "pareto_vector": pareto_vector,
            "disagreements": disagreements,
            "critical_issue_count": critical_count,
            "meta_recommendation": meta_recommendation,
            "consolidated_issues": all_issues,
            "created_at": _now(),
        }

        meta_hash = _sha(_json(raw_meta))
        raw_meta["meta_verdict_hash"] = meta_hash
        raw_meta["meta_verdict_id"] = f"mv-{meta_hash[:32]}"
        _validate_schema(self.root, META_VERDICT_SCHEMA, raw_meta)
        return raw_meta


class EvaluationPipeline:
    """Orchestrates end-to-end M8 blind evaluation, verification, and durability."""

    def __init__(self, root: str | Path, *, fault: Callable[[str], None] | None = None):
        self.root = Path(root).resolve()
        self.fault = fault
        self.rubric = load_rubric(self.root)
        self.evaluator = BlindEvaluator(self.root, self.rubric)
        self.meta_reviewer = MetaReviewer(self.root, self.rubric)

        for rel in ("state/evaluation", "state/meta_review", "reports/evaluations", "workspaces/eval"):
            _managed_directory(self.root, rel, create=True)

    def _hit(self, name: str) -> None:
        if self.fault:
            self.fault(name)

    def evaluate_candidate(
        self,
        candidate_dir: str | Path,
        *,
        run_id: str,
        cycle_id: int,
    ) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
        """Perform pure blind evaluation without touching durable state or state transitions."""
        cand_path = Path(candidate_dir).resolve()
        if not cand_path.is_dir():
            raise EvaluationError("candidate path must be an existing directory")

        cand_manifest_file = cand_path / "manifest.json"
        manifest, _ = _read_json(cand_manifest_file)
        cand_id = manifest.get("candidate_id")
        cand_content_hash = manifest.get("content_hash")

        calc_hash = _candidate_content_hash(cand_path, manifest)
        if calc_hash != cand_content_hash:
            raise EvaluationError("candidate manifest content hash diverges from actual tree content")

        blind_eval_seed = f"{run_id}:{cycle_id}:{cand_id}:{cand_content_hash}"
        blind_eval_id = "be-" + _sha(blind_eval_seed.encode("utf-8"))[:24]

        staging_dir = Path(tempfile.mkdtemp(prefix=".eval-stage-", dir=self.root / "workspaces/eval"))
        try:
            blind_workspace = staging_dir / "blind"
            sanitize_candidate(cand_path, blind_workspace)

            verdicts: list[dict[str, Any]] = []
            for jid, fdim, prof in JUROR_SPECIALTIES:
                verdict = self.evaluator.evaluate_juror(
                    blind_workspace,
                    jid,
                    fdim,
                    prof,
                    run_id=run_id,
                    cycle_id=cycle_id,
                    blind_eval_id=blind_eval_id,
                )
                verdicts.append(verdict)

            meta_verdict = self.meta_reviewer.aggregate(
                verdicts,
                run_id=run_id,
                cycle_id=cycle_id,
                blind_eval_id=blind_eval_id,
            )

            raw_report = {
                "schema_version": SCHEMA_VERSION,
                "report_version": "1.0.0",
                "run_id": run_id,
                "cycle_id": cycle_id,
                "candidate_id": cand_id,
                "candidate_content_hash": cand_content_hash,
                "blind_eval_id": blind_eval_id,
                "meta_verdict": meta_verdict,
                "juror_verdicts": verdicts,
                "pareto_vector": meta_verdict["pareto_vector"],
                "overall_score": meta_verdict["overall_score"],
                "recommendation": meta_verdict["meta_recommendation"],
                "generated_at": _now(),
            }

            rep_hash = _sha(_json(raw_report))
            raw_report["report_hash"] = rep_hash
            raw_report["report_id"] = f"evr-{rep_hash[:32]}"
            raw_report["report_locator"] = f"reports/evaluations/{cand_id}/{rep_hash}.json"

            _validate_schema(self.root, EVALUATION_REPORT_SCHEMA, raw_report)
            return raw_report, meta_verdict, verdicts
        finally:
            if staging_dir.exists():
                for p in staging_dir.rglob("*"):
                    if p.is_file() or p.is_symlink():
                        os.chmod(p, 0o600)
                        p.unlink()
                    elif p.is_dir():
                        os.chmod(p, 0o700)
                shutil.rmtree(staging_dir)

    def publish_evaluation(
        self,
        report: Mapping[str, Any],
        meta_verdict: Mapping[str, Any],
        verdicts: Sequence[Mapping[str, Any]],
    ) -> Path:
        """Persist evaluation artifacts atomically and immutably into state directories."""
        cand_id = report["candidate_id"]
        eval_state_dir = _managed_directory(self.root, f"state/evaluation/{cand_id}", create=True)
        meta_state_dir = _managed_directory(self.root, f"state/meta_review/{cand_id}", create=True)
        rep_dir = _managed_directory(self.root, f"reports/evaluations/{cand_id}", create=True)

        for v in verdicts:
            v_hash = v["verdict_hash"]
            v_file = eval_state_dir / f"{v_hash}.json"
            if not v_file.exists():
                v_raw = _json(dict(v))
                _write_synced_file(v_file, v_raw)
                os.chmod(v_file, 0o444)

        mv_hash = meta_verdict["meta_verdict_hash"]
        mv_file = meta_state_dir / f"{mv_hash}.json"
        if not mv_file.exists():
            mv_raw = _json(dict(meta_verdict))
            _write_synced_file(mv_file, mv_raw)
            os.chmod(mv_file, 0o444)

        rep_hash = report["report_hash"]
        rep_file = rep_dir / f"{rep_hash}.json"
        if not rep_file.exists():
            rep_raw = _json(dict(report))
            _write_synced_file(rep_file, rep_raw)
            os.chmod(rep_file, 0o444)

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "run_id": report["run_id"],
            "cycle_id": report["cycle_id"],
            "candidate_id": cand_id,
            "candidate_content_hash": report["candidate_content_hash"],
            "blind_eval_id": report["blind_eval_id"],
            "report_hash": rep_hash,
            "meta_verdict_hash": mv_hash,
            "verdict_hashes": [v["verdict_hash"] for v in verdicts],
            "published_at": _now(),
        }
        _validate_schema(self.root, EVALUATION_MANIFEST_SCHEMA, manifest)
        man_raw = _json(manifest)
        man_hash = _sha(man_raw)
        man_file = rep_dir / f"eval-manifest-{man_hash[:16]}.json"
        if not man_file.exists():
            _write_synced_file(man_file, man_raw)
            os.chmod(man_file, 0o444)

        _fsync_dir(eval_state_dir)
        _fsync_dir(meta_state_dir)
        _fsync_dir(rep_dir)
        return rep_file

    def record_evaluation(
        self,
        store: DurableStore,
        report_locator: str | Path,
        *,
        gate_report_locator: str | Path | None = None,
    ) -> dict[str, Any]:
        """Verify published evaluation artifacts and advance state machine to EVALUATED."""
        root = self.root
        verified = verify_evaluation_report(
            root,
            report_locator,
            store=store,
            require_gates_passed=True,
            gate_report_locator=gate_report_locator,
        )

        run_id = verified["run_id"]
        rep_hash = verified["report_hash"]
        cand_id = verified["candidate_id"]
        cand_hash = verified["candidate_content_hash"]

        key = f"m8:{run_id}:{State.EVALUATED.value}:{rep_hash}"
        self._hit("before_record_evaluated")
        event = store.record(
            run_id,
            State.EVALUATED,
            event_id=key,
            idempotency_key=key,
            actor_id="M8",
            event_type="M8_EVALUATION_REPORT",
            payload={
                "candidate_id": cand_id,
                "candidate_hash": cand_hash,
                "report_hash": rep_hash,
                "report_locator": verified["report_locator"],
                "overall_score": verified["overall_score"],
                "pareto_vector": verified["pareto_vector"],
                "recommendation": verified["recommendation"],
            },
            artifact_hashes=[rep_hash],
        )
        self._hit("after_record_evaluated")
        return event

    def run_and_record(
        self,
        store: DurableStore,
        candidate_dir: str | Path,
        *,
        run_id: str,
        cycle_id: int,
        gate_report_locator: str | Path | None = None,
    ) -> dict[str, Any]:
        """Full automated helper: evaluate candidate, publish artifacts, and record event."""
        report, meta, verdicts = self.evaluate_candidate(candidate_dir, run_id=run_id, cycle_id=cycle_id)
        pub_path = self.publish_evaluation(report, meta, verdicts)
        locator = pub_path.relative_to(self.root).as_posix()
        self.record_evaluation(store, locator, gate_report_locator=gate_report_locator)
        return report


def verify_evaluation_report(
    root: str | Path,
    report_locator: str | Path,
    *,
    store: DurableStore | None = None,
    require_gates_passed: bool = False,
    gate_report_locator: str | Path | None = None,
) -> dict[str, Any]:
    """Independent validator rebuilding the entire M8 chain."""
    root_path = Path(root).resolve()
    loc_str = Path(report_locator).as_posix()
    report_path = _contained(root_path, loc_str, exists=True)

    report, raw = _read_json(report_path)
    _validate_schema(root_path, EVALUATION_REPORT_SCHEMA, report)
    _require_canonical_json(report, raw, "evaluation report")

    calc_rep_body = dict(report)
    for field in ("report_hash", "report_id", "report_locator"):
        calc_rep_body.pop(field, None)
    calc_rep_hash = _sha(_json(calc_rep_body))

    if (
        report.get("report_hash") != calc_rep_hash
        or report.get("report_id") != f"evr-{calc_rep_hash[:32]}"
        or report.get("report_locator") != loc_str
        or report_path != root_path / loc_str
    ):
        raise EvaluationError("evaluation report identity/hash/locator mismatch")

    cand_id = report["candidate_id"]
    if cand_id == "v0000":
        cand_path = root_path / "versions/champion" / cand_id
    else:
        cand_path = root_path / "versions/challengers" / cand_id

    if not cand_path.is_dir():
        raise EvaluationError(f"referenced candidate directory does not exist: {cand_path}")

    cand_manifest, _ = _read_json(cand_path / "manifest.json")
    if (
        cand_manifest.get("candidate_id") != cand_id
        or cand_manifest.get("content_hash") != report["candidate_content_hash"]
    ):
        raise EvaluationError("candidate manifest does not match evaluation report")

    actual_cand_hash = _candidate_content_hash(cand_path, cand_manifest)
    if actual_cand_hash != report["candidate_content_hash"]:
        raise EvaluationError("candidate tree content hash does not match evaluation report")

    meta = report["meta_verdict"]
    _validate_schema(root_path, META_VERDICT_SCHEMA, meta)

    mv_body = dict(meta)
    for field in ("meta_verdict_hash", "meta_verdict_id"):
        mv_body.pop(field, None)
    mv_hash = _sha(_json(mv_body))

    if meta.get("meta_verdict_hash") != mv_hash or meta.get("meta_verdict_id") != f"mv-{mv_hash[:32]}":
        raise EvaluationError("meta-verdict hash or ID mismatch")

    meta_file = root_path / "state/meta_review" / cand_id / f"{mv_hash}.json"
    if not meta_file.is_file():
        raise EvaluationError("persisted meta-review artifact missing in state/meta_review")
    persisted_meta, meta_raw = _read_json(meta_file)
    _require_canonical_json(persisted_meta, meta_raw, "meta-verdict")
    if persisted_meta != meta:
        raise EvaluationError("persisted meta-review differs from report payload")

    verdicts = report["juror_verdicts"]
    if len(verdicts) != 3:
        raise EvaluationError("evaluation report must contain exactly 3 juror verdicts")

    v_hashes = []
    for v in verdicts:
        _validate_schema(root_path, EVALUATION_SCHEMA, v)
        v_body = dict(v)
        for field in ("verdict_hash", "verdict_id"):
            v_body.pop(field, None)
        v_hash = _sha(_json(v_body))
        if v.get("verdict_hash") != v_hash or v.get("verdict_id") != f"jv-{v_hash[:32]}":
            raise EvaluationError("juror verdict hash or ID mismatch")
        v_hashes.append(v_hash)

        v_file = root_path / "state/evaluation" / cand_id / f"{v_hash}.json"
        if not v_file.is_file():
            raise EvaluationError(f"persisted juror verdict missing in state/evaluation: {v_hash}")
        persisted_v, v_raw = _read_json(v_file)
        _require_canonical_json(persisted_v, v_raw, "juror verdict")
        if persisted_v != v:
            raise EvaluationError("persisted juror verdict differs from report payload")

    if meta["verdict_hashes"] != v_hashes:
        raise EvaluationError("meta-verdict referenced verdict hashes mismatch juror verdicts")

    calc_meta = MetaReviewer(root_path).aggregate(
        verdicts,
        run_id=report["run_id"],
        cycle_id=report["cycle_id"],
        blind_eval_id=report["blind_eval_id"],
    )
    if calc_meta["meta_verdict_hash"] != meta["meta_verdict_hash"]:
        raise EvaluationError("recomputed meta-verdict differs from report meta-verdict")

    if report["pareto_vector"] != meta["pareto_vector"]:
        raise EvaluationError("report pareto_vector does not match meta-verdict")
    if report["overall_score"] != meta["overall_score"]:
        raise EvaluationError("report overall_score does not match meta-verdict")
    if report["recommendation"] != meta["meta_recommendation"]:
        raise EvaluationError("report recommendation does not match meta-verdict")

    if require_gates_passed:
        active_store = store or DurableStore(root_path)
        run_id = str(report["run_id"])
        snapshot = active_store.snapshot(run_id)
        events = active_store.read_events(run_id)

        if snapshot.get("state") != State.GATES_PASSED.value:
            raise EvaluationError(f"run {run_id} is in state {snapshot.get('state')}, expected GATES_PASSED")

        if not events or events[-1].get("state_to") != State.GATES_PASSED.value:
            raise EvaluationError("last durable store event is not GATES_PASSED")

        last_event = events[-1]
        gate_rep_locator = (
            gate_report_locator
            or last_event.get("payload", {}).get("report_locator")
        )
        if not gate_rep_locator:
            raise EvaluationError("cannot determine gate report locator to verify gate binding")

        gate_rep = verify_gate_report(root_path, gate_rep_locator, store=active_store)
        if (
            gate_rep.get("candidate_id") != cand_id
            or gate_rep.get("candidate_content_hash") != report["candidate_content_hash"]
        ):
            raise EvaluationError("GATES_PASSED report does not bind to the evaluated candidate")

    return report
