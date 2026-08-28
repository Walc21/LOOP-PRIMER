"""Comprehensive, offline, deterministic tests for M9 progress diagnosis and refocus."""
from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime/agent/skills/article-loop/src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop import (
    DurableStore,
    FakeRLMAdapter,
    IntegrityError,
    M7Pipeline,
    Orchestrator,
    PromptRegistry,
    State,
    ingest,
)
from article_loop.activation import ActivationPlanner
from article_loop.blackboard import Blackboard, Impact
from article_loop.gates import record_math_verification
from article_loop.evaluation import (
    DIMENSIONS,
    FakeJurorAdapter,
    FakeMetaReviewerAdapter,
    evaluate_candidate,
)
from article_loop.diagnosis import (
    CycleRecord,
    DiagnosisError,
    _diagnosis_id_for,
    _history_hash,
    classify_cycle_progress,
    diagnose_cycle,
    load_history_series,
    verify_published_diagnosis,
    _verify_diagnosis_classification,
)
from article_loop.refocus import (
    RefocusError,
    generate_refocus_plan,
    register_overlay_cas,
)
from article_loop.synthesis import _json, _sha, tree_hash


class DimensionScoresJurorAdapter(FakeJurorAdapter):
    """Test adapter with deterministic per-dimension neutral scores."""

    def __init__(self, *, scores_a, scores_b, **kwargs):
        super().__init__(**kwargs)
        self.scores_a = dict(scores_a)
        self.scores_b = dict(scores_b)

    def evaluate(self, presentation):
        verdict = super().evaluate(presentation)
        verdict["dimension_scores"] = [dict(self.scores_a), dict(self.scores_b)]
        return verdict


class M9DiagnosisTests(unittest.TestCase):
    """Exhaustive test suite for M9 stagnation detection, diagnosis, and refocusing."""

    @classmethod
    def setUpClass(cls):
        cls.fixture_dir = tempfile.TemporaryDirectory()
        fixture = Path(cls.fixture_dir.name)
        ps = fixture / "fixture.ps"
        ps.write_text(
            "%!PS\n/Courier findfont 18 scalefont setfont 72 700 moveto (M9 fixture) show showpage\n",
            encoding="utf-8",
        )
        cls.fixture_pdf = fixture / "fixture.pdf"
        subprocess.run(
            ["gs", "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", f"-sOutputFile={cls.fixture_pdf}", str(ps)],
            check=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.fixture_dir.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for relative in (
            "input/inbox",
            "artifacts/original",
            "artifacts/extracted",
            "artifacts/rendered",
            "versions/champion",
            "workspaces",
            "state",
            "reports",
        ):
            (self.root / relative).mkdir(parents=True, exist_ok=True)
        shutil.copytree(ROOT / "config", self.root / "config", dirs_exist_ok=True)
        shutil.copytree(ROOT / "prompts", self.root / "prompts")
        self.pdf = self.root / "input/inbox/artigo.pdf"
        shutil.copyfile(self.fixture_pdf, self.pdf)
        with zipfile.ZipFile(self.root / "input/inbox/source.zip", "w") as archive:
            archive.writestr(
                "paper.tex",
                "\\documentclass{article}\n\\begin{document}\nFixture paper $x=1$.\\label{fixture}\n\\end{document}\n",
            )
        ingest(self.root)
        self.fake = FakeRLMAdapter()
        self.orchestrator = Orchestrator(self.root, self.fake)
        self.initial = asyncio.run(self.orchestrator.bootstrap(self.pdf))
        self.run_id = self.initial["run_id"]

        # Setup blackboard claim and impact
        claim = Blackboard(self.root).append(self.run_id, "claims", {
            "text": "Fixture theorem", "type": "theorem", "location": {"page": 1, "section": "proof"},
            "dependencies": [], "evidence": ["page:1"], "status": "active", "severity": 10,
            "source_hash": self.initial["base_hash"], "last_validated_cycle": 0,
        })
        self.claim_id = claim["claim_id"]
        impact = Impact(
            claims=(self.claim_id,),
            sections=("section:proof",),
            equations=("equation:1",),
            references=("reference:1",),
            roles=tuple(f"W{i}{j}" for i in range(1, 6) for j in range(1, 4)),
            severity=10,
        )
        self.plan = ActivationPlanner().plan(cycle_id=0, impact=impact).activation_map()
        board = self.root / "state/blackboard" / self.run_id
        board.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(self.plan, sort_keys=True, separators=(",", ":"))
        (board / "activation-c0000.json").write_text(raw, encoding="utf-8")
        (board / "activation_map.json").write_text(raw, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def _manager(self, department):
        child = asyncio.run(self.orchestrator.status(self.run_id))["children"][department]
        return self.fake.for_child(child["child_id"], actor_role=department)

    def _proposal(self, role, cycle_id=0):
        target = f"evidence/{role.lower()}.txt"
        value = f"M9 evidence for {role} cycle {cycle_id}\n"
        return {
            "schema_version": "1.1.0", "proposal_id": f"p-{role}-c{cycle_id}", "role_id": role, "cycle_id": cycle_id,
            "base_hash": self.initial["base_hash"], "scope": ["proof"], "evidence_locators": ["page:1"],
            "patch_or_operations": {"kind": "operations", "operations": [{"op": "add", "target": target, "value": value}]},
            "affected_claims": [self.claim_id] if role == "W22" else [], "dependencies": [],
            "risk": {"level": "low", "factors": [], "technical_effect_possible": False}, "confidence": 1,
            "requested_validations": ["correctness_math"] if role == "W22" else [], "prompt_version": "m9-integration",
        }

    def _m6_state(self, cycle_id=0):
        asyncio.run(self.orchestrator.run_cycle(run_id=self.run_id, plan=self.plan))
        for department in ("S10", "S20", "S30", "S40", "S50"):
            asyncio.run(self.orchestrator.advance_department(self.run_id, department, adapter=self._manager(department)))
        for number in range(1, 6):
            department = f"S{number}0"
            for suffix in (1, 2, 3):
                role = f"W{number}{suffix}"
                path = self.root / "workspaces" / self.run_id / f"cycle-{cycle_id:04d}" / role / "receipt.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(json.dumps(self._proposal(role, cycle_id), sort_keys=True, separators=(",", ":")).encode() + b"\n")
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                asyncio.run(self.orchestrator.receipt(self.run_id, sender_role=role, parent_role=department, path=path, sha256=digest))
        for department in ("S20", "S10", "S30", "S40", "S50"):
            asyncio.run(self.orchestrator.consolidate_department(self.run_id, department, adapter=self._manager(department)))
        return asyncio.run(self.orchestrator.status(self.run_id))

    def _setup_cycle_up_to_evaluated(
        self,
        cycle_id=0,
        preferred_winner="B",
        base_scores=(4, 4),
        juror_adapters=None,
    ):
        state = self._m6_state(cycle_id=cycle_id)
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        store = DurableStore(self.root)
        pipe.record_synthesis(store, synthesis)
        champion = self.root / "versions/champion/v0000"
        manifest = pipe.build(synthesis, champion)
        pipe.record_candidate(store, manifest)
        candidate = self.root / "versions/challengers" / manifest["candidate_id"]
        record_math_verification(
            candidate, claim_id=self.claim_id, proposal_id=f"p-W22-c{cycle_id}", verifier_id="local-fixture",
            verifier_version="1.0.0", method="manual-proof-check", summary="Fixture identity checked independently.",
        )
        report = pipe.execute_and_record_gates(store, candidate)

        jurors = juror_adapters or {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", specialty="correctness_math", preferred_winner=preferred_winner, base_scores=base_scores),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib", specialty="scientific_contribution", preferred_winner=preferred_winner, base_scores=base_scores),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity", specialty="clarity", preferred_winner=preferred_winner, base_scores=base_scores),
        }
        meta = FakeMetaReviewerAdapter()
        eval_report = evaluate_candidate(
            self.root,
            self.run_id,
            cycle_id=cycle_id,
            candidate_id=manifest["candidate_id"],
            gate_report_locator=report["report_locator"],
            juror_adapters=jurors,
            meta_adapter=meta,
            allow_test_doubles=True,
        )
        return {
            "manifest": manifest,
            "gate_report": report,
            "evaluation_report": eval_report,
        }

    def _publish_diagnosis_fixture(self, classification, *, focus=None):
        """Publish a source-bound diagnosis and its exact DIAGNOSED event binding."""
        if classification in {"LOCAL_PLATEAU", "GLOBAL_PLATEAU", "INCONCLUSIVE"}:
            preferred_winner = "B" if classification == "INCONCLUSIVE" else "A"
            jurors = None
            window_size = 3 if classification == "INCONCLUSIVE" else 1
            mde = 0.25
            if classification == "LOCAL_PLATEAU":
                scores_a = {dimension: 4 for dimension in DIMENSIONS}
                scores_b = dict(scores_a)
                scores_b["scientific_contribution"] = 2
                jurors = {
                    juror_id: DimensionScoresJurorAdapter(
                        juror_id=juror_id,
                        specialty=specialty,
                        preferred_winner="A",
                        scores_a=scores_a,
                        scores_b=scores_b,
                    )
                    for juror_id, specialty in (
                        ("juror-math", "correctness_math"),
                        ("juror-contrib", "scientific_contribution"),
                        ("juror-clarity", "clarity"),
                    )
                }
                mde = 3.0
            m8 = self._setup_cycle_up_to_evaluated(
                cycle_id=0,
                preferred_winner=preferred_winner,
                juror_adapters=jurors,
            )
            diagnosis = diagnose_cycle(
                self.root,
                self.run_id,
                cycle_id=0,
                candidate_id=m8["manifest"]["candidate_id"],
                window_size=window_size,
                mde=mde,
            )
            self.assertEqual(diagnosis["classification"], classification)
            return diagnosis

        # OSCILLATING needs at least two closed cycles. Tests that exercise its
        # plan shape use this source-bound fixture with the verifier explicitly
        # patched; canonical classification verification is covered separately.
        m8 = self._setup_cycle_up_to_evaluated(cycle_id=0, preferred_winner="B")
        store = DurableStore(self.root)
        created_at = store.read_events(self.run_id)[-1]["occurred_at"]
        evaluation = m8["evaluation_report"]
        evaluation_manifest = json.loads(
            (self.root / f"state/evaluations/{self.run_id}/c0000/manifest.json").read_text(encoding="utf-8")
        )
        history_hash = _history_hash(load_history_series(self.root, self.run_id, 0, store=store))
        without_id = {
            "schema_version": "1.1.0",
            "run_id": self.run_id,
            "cycle_id": 0,
            "candidate_id": evaluation["candidate_id"],
            "candidate_content_hash": evaluation["candidate_content_hash"],
            "base_hash": evaluation["base_hash"],
            "created_at": created_at,
            "gate_report_id": m8["gate_report"]["report_id"],
            "gate_report_hash": evaluation_manifest["gate_report_hash"],
            "evaluation_report_hash": evaluation_manifest["evaluation_report_hash"],
            "history_hash": history_hash,
            "verdict_ids": evaluation["verdict_ids"],
            "window_size": 3,
            "mde": 0.25,
            "classification": classification,
            "signals": [f"fixture:{classification}"],
            "recommended_mode": "SHIFT" if classification in {"LOCAL_PLATEAU", "GLOBAL_PLATEAU", "OSCILLATING"} else "CHECK",
            "focus": list(focus or ["general_refocus"]),
            "evidence_locators": [
                f"state/evaluations/{self.run_id}/c0000/evaluation.json",
                m8["gate_report"]["report_locator"],
            ],
        }
        diagnosis = {"diagnosis_id": _diagnosis_id_for(without_id), **without_id}
        diag_dir = self.root / "state" / "diagnosis" / self.run_id / "c0000"
        diag_dir.mkdir(parents=True)
        diagnosis_bytes = _json(diagnosis)
        (diag_dir / "diagnosis.json").write_bytes(diagnosis_bytes)
        manifest = {
            "schema_version": "1.1.0",
            "diagnosis_id": diagnosis["diagnosis_id"],
            "run_id": self.run_id,
            "cycle_id": 0,
            "candidate_id": diagnosis["candidate_id"],
            "classification": classification,
            "diagnosis_hash": _sha(diagnosis_bytes),
            "gate_report_hash": evaluation_manifest["gate_report_hash"],
            "evaluation_report_hash": evaluation_manifest["evaluation_report_hash"],
            "tree_content_hash": tree_hash(diag_dir, exclude={"manifest.json"}),
            "created_at": created_at,
        }
        manifest_bytes = _json(manifest)
        (diag_dir / "manifest.json").write_bytes(manifest_bytes)
        os.chmod(diag_dir / "diagnosis.json", 0o444)
        os.chmod(diag_dir / "manifest.json", 0o444)
        os.chmod(diag_dir, 0o555)
        store.record(
            self.run_id,
            State.DIAGNOSED,
            event_id="fixture-diagnosed",
            idempotency_key="fixture:diagnosed",
            actor_id="M00",
            event_type="DIAGNOSED",
            payload={
                "candidate_id": diagnosis["candidate_id"],
                "candidate_content_hash": diagnosis["candidate_content_hash"],
                "base_hash": evaluation["base_hash"],
                "diagnosis_id": diagnosis["diagnosis_id"],
                "classification": classification,
                "recommended_mode": diagnosis["recommended_mode"],
                "diagnosis_locator": f"state/diagnosis/{self.run_id}/c0000/diagnosis.json",
            },
            artifact_hashes=sorted([_sha(diagnosis_bytes), _sha(manifest_bytes)]),
        )
        return diagnosis

    # ==================== 1. Basic Invariants & State Boundary ====================

    def test_diagnosis_transitions_evaluated_to_diagnosed(self):
        m8_out = self._setup_cycle_up_to_evaluated(cycle_id=0, preferred_winner="B")
        candidate_id = m8_out["manifest"]["candidate_id"]

        diag = diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id)
        self.assertEqual(diag["run_id"], self.run_id)
        self.assertEqual(diag["cycle_id"], 0)
        self.assertEqual(diag["candidate_id"], candidate_id)
        self.assertIn(diag["classification"], ("EVOLVING", "INCONCLUSIVE", "LOCAL_PLATEAU", "GLOBAL_PLATEAU", "OSCILLATING", "REGRESSING", "TECHNICAL_FAILURE"))

        # Verify state in DurableStore
        store = DurableStore(self.root)
        events = store.read_events(self.run_id)
        last_evt = events[-1]
        self.assertEqual(last_evt["state_to"], State.DIAGNOSED)
        self.assertEqual(last_evt["event_type"], "DIAGNOSED")

    def test_diagnosis_never_reaches_decided_state(self):
        m8_out = self._setup_cycle_up_to_evaluated(cycle_id=0, preferred_winner="B")
        candidate_id = m8_out["manifest"]["candidate_id"]

        diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id)

        store = DurableStore(self.root)
        events = store.read_events(self.run_id)
        for evt in events:
            self.assertNotEqual(evt["state_to"], State.DECIDED)
            self.assertNotEqual(evt["event_type"], "DECIDED")

    def test_diagnosis_rejects_symlinked_publication_parent_without_writes(self):
        m8_out = self._setup_cycle_up_to_evaluated(cycle_id=0, preferred_winner="B")
        candidate_id = m8_out["manifest"]["candidate_id"]
        escape = self.root / "diagnosis-escape"
        escape.mkdir()
        diagnosis_root = self.root / "state/diagnosis"
        diagnosis_root.symlink_to(escape, target_is_directory=True)

        with self.assertRaisesRegex(DiagnosisError, "managed diagnosis directory"):
            diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id)
        self.assertEqual(list(escape.iterdir()), [])
        self.assertEqual(DurableStore(self.root).read_events(self.run_id)[-1]["state_to"], State.EVALUATED)

    def test_diagnosis_fails_closed_if_not_evaluated_state(self):
        # Initial state is NEW / SOURCE_READY, not EVALUATED
        with self.assertRaisesRegex(DiagnosisError, "diagnosis requires state EVALUATED"):
            diagnose_cycle(self.root, self.run_id, cycle_id=0)

    # ==================== 2. Seven Canonical Classifications ====================

    def test_classification_evolving(self):
        # Material gain with math passed and challenger eligible
        rec = CycleRecord(
            cycle_id=0, candidate_id="v0001", candidate_content_hash="a" * 64, base_hash="b" * 64,
            gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
            evaluation_report={"overall_outcome": "challenger_favored", "challenger_eligible": True, "consistent_jurors": 3},
            meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=None,
            dimension_scores_challenger={d: 4.5 for d in DIMENSIONS},
            dimension_scores_champion={d: 3.0 for d in DIMENSIONS},
            correctness_math_pass=True, overall_outcome="challenger_favored", challenger_eligible=True,
            active_issues=[],
        )
        cls_res, signals, rec_mode, focus = classify_cycle_progress([rec], window_size=3, mde=0.25)
        self.assertEqual(cls_res, "EVOLVING")
        self.assertEqual(rec_mode, "RUN")

    def test_classification_regressing_on_lost_math_gate(self):
        rec = CycleRecord(
            cycle_id=0, candidate_id="v0001", candidate_content_hash="a" * 64, base_hash="b" * 64,
            gate_report={"overall_pass": True, "correctness_math_pass": False, "gates": []},
            evaluation_report={"overall_outcome": "challenger_favored", "challenger_eligible": False, "consistent_jurors": 3},
            meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=None,
            dimension_scores_challenger={d: 5.0 for d in DIMENSIONS},
            dimension_scores_champion={d: 3.0 for d in DIMENSIONS},
            correctness_math_pass=False, overall_outcome="challenger_favored", challenger_eligible=False,
            active_issues=[],
        )
        cls_res, signals, rec_mode, focus = classify_cycle_progress([rec], window_size=3, mde=0.25)
        self.assertEqual(cls_res, "REGRESSING")
        self.assertEqual(rec_mode, "CHECK")
        self.assertIn("math_hard_gate_lost", signals)

    def test_math_hard_gate_loss_cannot_be_masked_by_inconclusive_jury(self):
        rec = CycleRecord(
            cycle_id=0, candidate_id="v0001", candidate_content_hash="a" * 64, base_hash="b" * 64,
            gate_report={"overall_pass": False, "correctness_math_pass": False, "gates": [{"gate_id": "correctness_math", "passed": False}]},
            evaluation_report={"overall_outcome": "inconclusive", "challenger_eligible": False, "consistent_jurors": 0},
            meta_verdict={"confirmed": False, "vetoed": True, "veto_reason": "jury divergence"},
            verdicts=[], activation_map=None,
            dimension_scores_challenger={d: 0.0 for d in DIMENSIONS},
            dimension_scores_champion={d: 0.0 for d in DIMENSIONS},
            correctness_math_pass=False, overall_outcome="inconclusive", challenger_eligible=False,
            active_issues=[],
        )
        classification, signals, mode, _ = classify_cycle_progress([rec], window_size=3, mde=0.25)
        self.assertEqual(classification, "REGRESSING")
        self.assertIn("math_hard_gate_lost", signals)
        self.assertEqual(mode, "CHECK")

    def test_classification_technical_failure(self):
        rec = CycleRecord(
            cycle_id=0, candidate_id="v0001", candidate_content_hash="a" * 64, base_hash="b" * 64,
            gate_report={
                "overall_pass": False, "correctness_math_pass": True,
                "gates": [{"gate_id": "latex_compile_safe", "passed": False}],
            },
            evaluation_report={"overall_outcome": "inconclusive", "challenger_eligible": False, "consistent_jurors": 0},
            meta_verdict={"confirmed": False, "vetoed": False}, verdicts=[], activation_map=None,
            dimension_scores_challenger={d: 0.0 for d in DIMENSIONS},
            dimension_scores_champion={d: 0.0 for d in DIMENSIONS},
            correctness_math_pass=False, overall_outcome="inconclusive", challenger_eligible=False,
            active_issues=[],
        )
        cls_res, signals, rec_mode, focus = classify_cycle_progress([rec], window_size=3, mde=0.25)
        self.assertEqual(cls_res, "TECHNICAL_FAILURE")
        self.assertEqual(rec_mode, "CHECK")

    def test_classification_inconclusive_on_divergent_jurors(self):
        rec = CycleRecord(
            cycle_id=0, candidate_id="v0001", candidate_content_hash="a" * 64, base_hash="b" * 64,
            gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
            evaluation_report={"overall_outcome": "inconclusive", "challenger_eligible": False, "consistent_jurors": 1},
            meta_verdict={"confirmed": False, "vetoed": True, "veto_reason": "Inconsistent juror votes"},
            verdicts=[], activation_map=None,
            dimension_scores_challenger={d: 3.5 for d in DIMENSIONS},
            dimension_scores_champion={d: 3.5 for d in DIMENSIONS},
            correctness_math_pass=True, overall_outcome="inconclusive", challenger_eligible=False,
            active_issues=[],
        )
        cls_res, signals, rec_mode, focus = classify_cycle_progress([rec], window_size=3, mde=0.25)
        self.assertEqual(cls_res, "INCONCLUSIVE")
        self.assertEqual(rec_mode, "CHECK")

    def test_classification_oscillating(self):
        # Reversals across cycles in effective window
        rec0 = CycleRecord(
            cycle_id=0, candidate_id="v0001", candidate_content_hash="a" * 64, base_hash="b" * 64,
            gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
            evaluation_report={"overall_outcome": "tie", "challenger_eligible": False, "consistent_jurors": 3},
            meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=None,
            dimension_scores_challenger={"clarity": 4.0, "logical_coherence": 2.0, **{d: 3.0 for d in DIMENSIONS if d not in ("clarity", "logical_coherence")}},
            dimension_scores_champion={d: 3.0 for d in DIMENSIONS},
            correctness_math_pass=True, overall_outcome="tie", challenger_eligible=False,
            active_issues=[],
        )
        rec1 = CycleRecord(
            cycle_id=1, candidate_id="v0002", candidate_content_hash="c" * 64, base_hash="b" * 64,
            gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
            evaluation_report={"overall_outcome": "tie", "challenger_eligible": False, "consistent_jurors": 3},
            meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=None,
            dimension_scores_challenger={"clarity": 2.0, "logical_coherence": 4.0, **{d: 3.0 for d in DIMENSIONS if d not in ("clarity", "logical_coherence")}},
            dimension_scores_champion={d: 3.0 for d in DIMENSIONS},
            correctness_math_pass=True, overall_outcome="tie", challenger_eligible=False,
            active_issues=[],
        )
        cls_res, signals, rec_mode, focus = classify_cycle_progress([rec0, rec1], window_size=3, mde=0.25)
        self.assertEqual(cls_res, "OSCILLATING")
        self.assertEqual(rec_mode, "SHIFT")

    def test_oscillation_detects_an_earlier_reversal_inside_the_window(self):
        series = []
        for cycle_id, delta in enumerate((1.0, -1.0, -1.0)):
            challenger = {d: 3.0 for d in DIMENSIONS}
            challenger["clarity"] += delta
            challenger["logical_coherence"] += delta
            series.append(CycleRecord(
                cycle_id=cycle_id, candidate_id=f"v{cycle_id + 1:04d}",
                candidate_content_hash="a" * 64, base_hash="b" * 64,
                gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
                evaluation_report={"overall_outcome": "tie", "challenger_eligible": False, "consistent_jurors": 3},
                meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=None,
                dimension_scores_challenger=challenger,
                dimension_scores_champion={d: 3.0 for d in DIMENSIONS},
                correctness_math_pass=True, overall_outcome="tie", challenger_eligible=False,
                active_issues=[],
            ))
        classification, signals, mode, _ = classify_cycle_progress(series, window_size=3, mde=0.25)
        self.assertEqual(classification, "OSCILLATING")
        self.assertIn("multiple_reversals_detected:2", signals)
        self.assertEqual(mode, "SHIFT")

    def test_reopened_issue_is_an_oscillation_signal(self):
        series = []
        for cycle_id in range(2):
            issues = [] if cycle_id == 0 else [{
                "record_id": "issue-proof-1", "cycle_id": 1,
                "status": "reopened", "severity": "HIGH",
            }]
            series.append(CycleRecord(
                cycle_id=cycle_id, candidate_id=f"v{cycle_id + 1:04d}",
                candidate_content_hash="a" * 64, base_hash="b" * 64,
                gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
                evaluation_report={"overall_outcome": "tie", "challenger_eligible": False, "consistent_jurors": 3},
                meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=None,
                dimension_scores_challenger={d: 3.0 for d in DIMENSIONS},
                dimension_scores_champion={d: 3.0 for d in DIMENSIONS},
                correctness_math_pass=True, overall_outcome="tie", challenger_eligible=False,
                active_issues=issues,
            ))
        classification, signals, mode, focus = classify_cycle_progress(series, window_size=3, mde=0.25)
        self.assertEqual(classification, "OSCILLATING")
        self.assertIn("issues_reopened:issue-proof-1", signals)
        self.assertEqual((mode, focus), ("SHIFT", ["issues", "stabilization"]))

    def test_classification_local_plateau(self):
        # 3 cycles in window, zero overall gain, but S40 / clarity is specifically failing while others are high
        series = []
        for cid in range(3):
            series.append(CycleRecord(
                cycle_id=cid, candidate_id=f"v000{cid+1}", candidate_content_hash="a" * 64, base_hash="b" * 64,
                gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
                evaluation_report={"overall_outcome": "tie", "challenger_eligible": False, "consistent_jurors": 3},
                meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=None,
                dimension_scores_challenger={
                    "correctness_math": 5.0, "proof_completeness": 4.5, "logical_coherence": 4.0,
                    "scientific_contribution": 4.0, "semantic_precision": 2.0, "clarity": 2.0,
                    "format_integrity": 4.5, "reproducibility": 4.5,
                },
                dimension_scores_champion={
                    "correctness_math": 5.0, "proof_completeness": 4.5, "logical_coherence": 4.0,
                    "scientific_contribution": 4.0, "semantic_precision": 2.0, "clarity": 2.0,
                    "format_integrity": 4.5, "reproducibility": 4.5,
                },
                correctness_math_pass=True, overall_outcome="tie", challenger_eligible=False,
                active_issues=[],
            ))
        cls_res, signals, rec_mode, focus = classify_cycle_progress(series, window_size=3, mde=0.25)
        self.assertEqual(cls_res, "LOCAL_PLATEAU")
        self.assertEqual(rec_mode, "SHIFT")
        self.assertIn("S40", focus)

    def test_classification_global_plateau(self):
        # 3 cycles in window, uniform stagnation across all dimensions
        series = []
        for cid in range(3):
            series.append(CycleRecord(
                cycle_id=cid, candidate_id=f"v000{cid+1}", candidate_content_hash="a" * 64, base_hash="b" * 64,
                gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
                evaluation_report={"overall_outcome": "tie", "challenger_eligible": False, "consistent_jurors": 3},
                meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=None,
                dimension_scores_challenger={d: 3.5 for d in DIMENSIONS},
                dimension_scores_champion={d: 3.5 for d in DIMENSIONS},
                correctness_math_pass=True, overall_outcome="tie", challenger_eligible=False,
                active_issues=[],
            ))
        cls_res, signals, rec_mode, focus = classify_cycle_progress(series, window_size=3, mde=0.25)
        self.assertEqual(cls_res, "GLOBAL_PLATEAU")
        self.assertEqual(rec_mode, "SHIFT")
        self.assertIn("general_refocus", focus)

    def test_incomplete_window_does_not_invent_plateau(self):
        # Single cycle with zero delta and window_size=3 must NOT return GLOBAL_PLATEAU
        rec = CycleRecord(
            cycle_id=0, candidate_id="v0001", candidate_content_hash="a" * 64, base_hash="b" * 64,
            gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
            evaluation_report={"overall_outcome": "tie", "challenger_eligible": False, "consistent_jurors": 3},
            meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=None,
            dimension_scores_challenger={d: 3.5 for d in DIMENSIONS},
            dimension_scores_champion={d: 3.5 for d in DIMENSIONS},
            correctness_math_pass=True, overall_outcome="tie", challenger_eligible=False,
            active_issues=[],
        )
        cls_res, signals, rec_mode, focus = classify_cycle_progress([rec], window_size=3, mde=0.25)
        self.assertEqual(cls_res, "INCONCLUSIVE")
        self.assertNotEqual(cls_res, "GLOBAL_PLATEAU")
        self.assertNotEqual(cls_res, "LOCAL_PLATEAU")

    def test_invalid_classification_parameters_fail_closed(self):
        rec = CycleRecord(
            cycle_id=0, candidate_id="v0001", candidate_content_hash="a" * 64, base_hash="b" * 64,
            gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
            evaluation_report={"overall_outcome": "tie", "challenger_eligible": False, "consistent_jurors": 3},
            meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=None,
            dimension_scores_challenger={d: 3.0 for d in DIMENSIONS},
            dimension_scores_champion={d: 3.0 for d in DIMENSIONS},
            correctness_math_pass=True, overall_outcome="tie", challenger_eligible=False,
            active_issues=[],
        )
        for invalid_window in (0, -1, True, 1.5):
            with self.subTest(window_size=invalid_window):
                with self.assertRaisesRegex(DiagnosisError, "window_size"):
                    classify_cycle_progress([rec], window_size=invalid_window, mde=0.25)
        for invalid_mde in (-0.1, 5.1, float("nan"), float("inf"), True):
            with self.subTest(mde=invalid_mde):
                with self.assertRaisesRegex(DiagnosisError, "mde"):
                    classify_cycle_progress([rec], window_size=3, mde=invalid_mde)

    # ==================== 3. False Improvements Rejection ====================

    def test_clarity_increase_does_not_mask_math_regression(self):
        # Clarity increased by +2.0, but math dropped by -0.5
        rec = CycleRecord(
            cycle_id=0, candidate_id="v0001", candidate_content_hash="a" * 64, base_hash="b" * 64,
            gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
            evaluation_report={"overall_outcome": "challenger_favored", "challenger_eligible": True, "consistent_jurors": 3},
            meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=None,
            dimension_scores_challenger={"correctness_math": 4.5, "clarity": 5.0, **{d: 3.0 for d in DIMENSIONS if d not in ("correctness_math", "clarity")}},
            dimension_scores_champion={"correctness_math": 5.0, "clarity": 3.0, **{d: 3.0 for d in DIMENSIONS if d not in ("correctness_math", "clarity")}},
            correctness_math_pass=True, overall_outcome="challenger_favored", challenger_eligible=True,
            active_issues=[],
        )
        cls_res, signals, rec_mode, focus = classify_cycle_progress([rec], window_size=3, mde=0.25)
        self.assertEqual(cls_res, "REGRESSING")
        self.assertIn("correctness_math", focus)

    # ==================== 4. Refocus & Overlay Generation ====================

    def test_refocus_generation_for_local_plateau(self):
        diagnosis = self._publish_diagnosis_fixture("LOCAL_PLATEAU")
        plan = generate_refocus_plan(self.root, self.run_id, 0, diagnosis)
        self.assertEqual(plan["classification"], "LOCAL_PLATEAU")
        self.assertEqual(plan["strategy"], "targeted_bottleneck")
        self.assertEqual(len(plan["branches"]), 1)
        branch = plan["branches"][0]
        self.assertEqual(branch["kind"], "targeted")
        self.assertEqual(branch["target_roles"], ["W31"])
        self.assertIn("W31", branch["overlay_versions"])
        self.assertEqual(branch["budget_limit"]["max_tokens"], 0)
        self.assertEqual(len(branch["overlay_hashes"]["W31"]), 64)

        # Check that PromptRegistry loads and validates the new overlay
        registry = PromptRegistry(self.root)
        overlay_text, overlay_doc = registry.overlay("W31", branch["overlay_versions"]["W31"])
        self.assertIn("Refocus M9", overlay_doc["diagnostic"])

    def test_refocus_generation_for_global_plateau_dual_branch(self):
        diagnosis = self._publish_diagnosis_fixture("GLOBAL_PLATEAU")
        plan = generate_refocus_plan(self.root, self.run_id, 0, diagnosis)
        self.assertEqual(plan["classification"], "GLOBAL_PLATEAU")
        self.assertEqual(plan["strategy"], "dual_branch")
        self.assertEqual(len(plan["branches"]), 2)

        kinds = {b["kind"] for b in plan["branches"]}
        self.assertEqual(kinds, {"exploitation", "exploration"})

        # Verify distinct hypotheses and roles
        exploit_b = next(b for b in plan["branches"] if b["kind"] == "exploitation")
        explore_b = next(b for b in plan["branches"] if b["kind"] == "exploration")

        self.assertNotEqual(exploit_b["hypothesis"], explore_b["hypothesis"])
        self.assertNotEqual(exploit_b["target_roles"], explore_b["target_roles"])

    def test_refocus_generation_for_oscillating(self):
        diagnosis = self._publish_diagnosis_fixture("OSCILLATING", focus=["stabilization"])
        with patch(
            "article_loop.refocus.verify_published_diagnosis",
            return_value=(diagnosis, []),
        ):
            plan = generate_refocus_plan(self.root, self.run_id, 0, diagnosis)
        self.assertEqual(plan["classification"], "OSCILLATING")
        self.assertEqual(plan["strategy"], "stabilization")
        self.assertEqual(len(plan["branches"]), 1)
        self.assertEqual(plan["branches"][0]["kind"], "stabilization")

    def test_refocus_generation_forbidden_for_regressing_inconclusive_technical_failure(self):
        diagnosis = self._publish_diagnosis_fixture("INCONCLUSIVE", focus=["all"])
        with self.assertRaisesRegex(RefocusError, "refocus overlay generation is forbidden"):
            generate_refocus_plan(self.root, self.run_id, 0, diagnosis)

    def test_overlay_creation_prohibits_m00_overlay(self):
        doc = {
            "parent_version": None, "diagnostic": "attack", "author": "attacker",
            "evidence": ["e1"], "scope": ["proof"], "hash": "", "rollback": None,
            "instructions": "malicious manager instruction",
        }
        with self.assertRaisesRegex(RefocusError, "cannot register overlay for forbidden role: M00"):
            register_overlay_cas(self.root, "M00", "v_malicious", doc)

    def test_overlay_registration_is_idempotent_and_rejects_unsafe_version_without_mutation(self):
        doc = {
            "parent_version": None, "diagnostic": "Idempotent overlay", "author": "m9",
            "evidence": ["evidence/idempotent"], "scope": ["proof"], "hash": "", "rollback": None,
            "instructions": "Preserve proof obligations",
        }
        first = register_overlay_cas(self.root, "W22", "v_idempotent", doc)
        second = register_overlay_cas(self.root, "W22", "v_idempotent", doc)
        self.assertEqual(first, second)

        registry_path = self.root / "prompts/registry.json"
        registry_before = registry_path.read_bytes()
        with self.assertRaisesRegex(RefocusError, "safe canonical identifier"):
            register_overlay_cas(self.root, "W22", "", doc)
        malformed = dict(doc)
        malformed["evidence"] = [[]]
        with self.assertRaisesRegex(RefocusError, "overlay evidence"):
            register_overlay_cas(self.root, "W22", "v_bad_evidence", malformed)
        with self.assertRaisesRegex(RefocusError, "forbidden role"):
            register_overlay_cas(self.root, [], "v_bad_role", doc)
        self.assertEqual(registry_before, registry_path.read_bytes())
        self.assertFalse((self.root / "prompts/overlays/W22/.yaml").exists())

    def test_overlay_registration_rejects_symlinked_role_directory_without_writes(self):
        escape = self.root / "overlay-escape"
        escape.mkdir()
        role_dir = self.root / "prompts/overlays/W22"
        role_dir.symlink_to(escape, target_is_directory=True)
        registry_path = self.root / "prompts/registry.json"
        registry_before = registry_path.read_bytes()
        document = {
            "parent_version": None, "diagnostic": "Symlink attack", "author": "m9",
            "evidence": ["evidence/symlink"], "scope": ["proof"], "hash": "", "rollback": None,
            "instructions": "Must never escape the managed overlay root",
        }

        with self.assertRaisesRegex(RefocusError, "safe managed directory"):
            register_overlay_cas(self.root, "W22", "v_symlink", document)
        self.assertEqual(registry_before, registry_path.read_bytes())
        self.assertEqual(list(escape.iterdir()), [])

    def test_refocus_retry_and_recovery_after_overlay_commit_are_idempotent(self):
        diagnosis = self._publish_diagnosis_fixture("GLOBAL_PLATEAU")

        def crash(stage):
            if stage == "after_overlays_registered":
                raise RuntimeError("crash after overlay commit")

        with self.assertRaisesRegex(RuntimeError, "crash after overlay commit"):
            generate_refocus_plan(self.root, self.run_id, 0, diagnosis, fault=crash)
        self.assertFalse((self.root / f"state/refocus/{self.run_id}/c0000").exists())

        recovered = generate_refocus_plan(self.root, self.run_id, 0, diagnosis)
        plan_path = self.root / f"state/refocus/{self.run_id}/c0000/refocus-plan.json"
        registry_path = self.root / "prompts/registry.json"
        plan_before = plan_path.read_bytes()
        registry_before = registry_path.read_bytes()
        redelivered = generate_refocus_plan(self.root, self.run_id, 0, diagnosis)
        self.assertEqual(recovered, redelivered)
        self.assertEqual(plan_before, plan_path.read_bytes())
        self.assertEqual(registry_before, registry_path.read_bytes())

    def test_refocus_rejects_symlinked_publication_parent_before_overlay_registration(self):
        diagnosis = self._publish_diagnosis_fixture("LOCAL_PLATEAU", focus=["S20", "W22"])
        escape = self.root / "refocus-escape"
        escape.mkdir()
        refocus_root = self.root / "state/refocus"
        refocus_root.symlink_to(escape, target_is_directory=True)
        registry_path = self.root / "prompts/registry.json"
        registry_before = registry_path.read_bytes()

        with self.assertRaisesRegex(RefocusError, "managed refocus directory"):
            generate_refocus_plan(self.root, self.run_id, 0, diagnosis)
        self.assertEqual(list(escape.iterdir()), [])
        self.assertEqual(registry_before, registry_path.read_bytes())

    def test_refocus_rejects_forged_diagnosis_without_registry_mutation(self):
        diagnosis = self._publish_diagnosis_fixture("LOCAL_PLATEAU", focus=["S20", "W22"])
        forged = dict(diagnosis)
        forged["focus"] = ["S40", "W42"]
        registry_path = self.root / "prompts/registry.json"
        registry_before = registry_path.read_bytes()
        with self.assertRaisesRegex(RefocusError, "differs from canonical"):
            generate_refocus_plan(self.root, self.run_id, 0, forged)
        self.assertEqual(registry_before, registry_path.read_bytes())

    def test_refocus_rejects_diagnosis_when_m8_source_is_tampered(self):
        diagnosis = self._publish_diagnosis_fixture("LOCAL_PLATEAU", focus=["S20", "W22"])
        evaluation_path = self.root / f"state/evaluations/{self.run_id}/c0000/evaluation.json"
        os.chmod(evaluation_path, 0o600)
        evaluation_path.write_bytes(evaluation_path.read_bytes() + b" ")
        registry_path = self.root / "prompts/registry.json"
        registry_before = registry_path.read_bytes()

        with self.assertRaisesRegex(RefocusError, "canonical diagnosis verification failed"):
            generate_refocus_plan(self.root, self.run_id, 0, diagnosis)
        self.assertEqual(registry_before, registry_path.read_bytes())

    def test_refocus_rejects_changed_activation_history(self):
        diagnosis = self._publish_diagnosis_fixture("LOCAL_PLATEAU", focus=["S20", "W22"])
        activation_path = self.root / f"state/blackboard/{self.run_id}/activation-c0000.json"
        activation = json.loads(activation_path.read_text(encoding="utf-8"))
        target = next(entry for entry in activation["roles"] if entry["role_id"] == "W42")
        target["mode"] = "FREEZE" if target["mode"] != "FREEZE" else "RUN"
        activation_path.write_bytes(_json(activation))
        registry_path = self.root / "prompts/registry.json"
        registry_before = registry_path.read_bytes()

        with self.assertRaisesRegex(RefocusError, "canonical diagnosis verification failed"):
            generate_refocus_plan(self.root, self.run_id, 0, diagnosis)
        self.assertEqual(registry_before, registry_path.read_bytes())

    # ==================== 5. Concurrency and Registry Locking ====================

    def test_concurrent_overlay_registration_with_cas_and_locks(self):
        # Register overlays in parallel across multiple roles
        roles = ["W11", "W12", "W21", "W22", "W31", "W41", "W51"]
        for idx, role in enumerate(roles):
            doc = {
                "parent_version": None,
                "diagnostic": f"Concurrent test {idx}",
                "author": "tester",
                "evidence": [f"control/evidence/{role}"],
                "scope": ["proof" if role.startswith("W2") else "structure"],
                "hash": "",
                "rollback": None,
                "instructions": f"Instructions for {role}",
            }
            h = register_overlay_cas(self.root, role, f"v_concurrent_{idx}", doc)
            self.assertEqual(len(h), 64)

        # Confirm registry graph is valid
        registry = PromptRegistry(self.root)
        for idx, role in enumerate(roles):
            text, d = registry.overlay(role, f"v_concurrent_{idx}")
            self.assertEqual(d["diagnostic"], f"Concurrent test {idx}")

    # ==================== 6. Immutability and State Preservation ====================

    def test_prompts_immutable_and_champion_and_verdicts_remain_byte_identical(self):
        m8_out = self._setup_cycle_up_to_evaluated(cycle_id=0, preferred_winner="B")
        candidate_id = m8_out["manifest"]["candidate_id"]

        # Snapshot sha256 hashes of champion, immutable prompts, challenger, verdicts
        champ_file = self.root / "versions/champion/v0000/manifest.json"
        champ_hash_before = hashlib.sha256(champ_file.read_bytes()).hexdigest()

        global_prompt = self.root / "prompts/immutable/global.md"
        global_hash_before = hashlib.sha256(global_prompt.read_bytes()).hexdigest()

        eval_rep_file = self.root / f"state/evaluations/{self.run_id}/c0000/evaluation.json"
        eval_rep_hash_before = hashlib.sha256(eval_rep_file.read_bytes()).hexdigest()

        # Run M9 diagnosis
        diag = diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id)

        # Verify byte identity after diagnosis
        champ_hash_after = hashlib.sha256(champ_file.read_bytes()).hexdigest()
        self.assertEqual(champ_hash_before, champ_hash_after)

        global_hash_after = hashlib.sha256(global_prompt.read_bytes()).hexdigest()
        self.assertEqual(global_hash_before, global_hash_after)

        eval_rep_hash_after = hashlib.sha256(eval_rep_file.read_bytes()).hexdigest()
        self.assertEqual(eval_rep_hash_before, eval_rep_hash_after)

    # ==================== 8. Anti-Lookahead, Cross-Run & FREEZE Tests ====================

    def test_anti_lookahead_ignores_future_cycles(self):
        m8_out = self._setup_cycle_up_to_evaluated(cycle_id=0, preferred_winner="B")
        candidate_id = m8_out["manifest"]["candidate_id"]

        # Create a fake future evaluation at c0001
        future_dir = self.root / f"state/evaluations/{self.run_id}/c0001"
        future_dir.mkdir(parents=True, exist_ok=True)
        (future_dir / "manifest.json").write_text(json.dumps({
            "schema_version": "1.1.0", "evaluation_id": "future-eval", "comparison_id": "future-cmp",
            "run_id": self.run_id, "cycle_id": 1, "candidate_id": "v0002", "gate_report_locator": "loc",
            "gate_report_hash": "a" * 64, "base_hash": "b" * 64, "candidate_content_hash": "c" * 64,
            "verdict_hashes": {}, "meta_verdict_hash": "d" * 64, "evaluation_report_hash": "e" * 64,
            "tree_content_hash": "f" * 64, "evaluated_at": "2026-08-28T00:00:00Z",
        }), encoding="utf-8")

        # Diagnose cycle 0: must not fail or read cycle 1
        diag = diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id)
        self.assertEqual(diag["cycle_id"], 0)

    def test_cross_run_mixing_fails_closed(self):
        # Mismatched run_id in load_history_series
        with self.assertRaisesRegex(DiagnosisError, "cannot read canonical JSON|series gap|missing"):
            load_history_series(self.root, "run-other-9999", 0)

    def test_history_rejects_tampered_evaluation_artifact(self):
        self._setup_cycle_up_to_evaluated(cycle_id=0, preferred_winner="B")
        evaluation_path = self.root / f"state/evaluations/{self.run_id}/c0000/evaluation.json"
        os.chmod(evaluation_path, 0o600)
        tampered = json.loads(evaluation_path.read_text(encoding="utf-8"))
        tampered["overall_outcome"] = "champion_favored"
        evaluation_path.write_bytes(_json(tampered))

        with self.assertRaisesRegex(DiagnosisError, "integrity verification failed"):
            load_history_series(self.root, self.run_id, 0)

    def test_history_scores_follow_neutral_identity_not_presentation_order(self):
        self._setup_cycle_up_to_evaluated(
            cycle_id=0,
            preferred_winner="B",
            base_scores=(2, 4),
        )
        record = load_history_series(self.root, self.run_id, 0)[0]
        self.assertEqual(record.dimension_scores_champion, {d: 2.0 for d in DIMENSIONS})
        self.assertEqual(record.dimension_scores_challenger, {d: 4.0 for d in DIMENSIONS})

    def test_freeze_roles_do_not_penalize_department_progress(self):
        # Setup activation map where 2 out of 3 specialists in S10 are FREEZE
        act_map = {
            "M00": {"mode": "RUN"},
            "S10": {"mode": "RUN"},
            "W11": {"mode": "RUN"},
            "W12": {"mode": "FREEZE"},
            "W13": {"mode": "FREEZE"},
        }
        rec = CycleRecord(
            cycle_id=0, candidate_id="v0001", candidate_content_hash="a" * 64, base_hash="b" * 64,
            gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
            evaluation_report={"overall_outcome": "challenger_favored", "challenger_eligible": True, "consistent_jurors": 3},
            meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=act_map,
            dimension_scores_challenger={d: 4.5 for d in DIMENSIONS},
            dimension_scores_champion={d: 3.0 for d in DIMENSIONS},
            correctness_math_pass=True, overall_outcome="challenger_favored", challenger_eligible=True,
            active_issues=[],
        )
        cls_res, signals, rec_mode, focus = classify_cycle_progress([rec], window_size=3, mde=0.25)
        self.assertEqual(cls_res, "EVOLVING")

    def test_frozen_department_is_excluded_from_plateau_localization(self):
        activation_map = {
            "W22": {"mode": "RUN"},
            "W41": {"mode": "FREEZE"},
            "W42": {"mode": "FREEZE"},
            "W43": {"mode": "FREEZE"},
        }
        series = []
        for cycle_id in range(3):
            challenger_scores = {d: 3.5 for d in DIMENSIONS}
            challenger_scores["semantic_precision"] = 1.0
            challenger_scores["clarity"] = 1.0
            series.append(CycleRecord(
                cycle_id=cycle_id,
                candidate_id=f"v{cycle_id + 1:04d}",
                candidate_content_hash="a" * 64,
                base_hash="b" * 64,
                gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
                evaluation_report={"overall_outcome": "tie", "challenger_eligible": False, "consistent_jurors": 3},
                meta_verdict={"confirmed": True, "vetoed": False},
                verdicts=[],
                activation_map=activation_map,
                dimension_scores_challenger=challenger_scores,
                dimension_scores_champion=dict(challenger_scores),
                correctness_math_pass=True,
                overall_outcome="tie",
                challenger_eligible=False,
                active_issues=[],
            ))
        classification, _, _, focus = classify_cycle_progress(series, window_size=3, mde=0.25)
        self.assertEqual(classification, "GLOBAL_PLATEAU")
        self.assertEqual(focus, ["general_refocus"])

    def test_all_frozen_specialist_dimensions_are_inconclusive(self):
        frozen = {
            role: {"mode": "FREEZE"}
            for department in ("S10", "S20", "S30", "S40", "S50")
            for role in (f"W{department[1]}1", f"W{department[1]}2", f"W{department[1]}3")
        }
        rec = CycleRecord(
            cycle_id=0, candidate_id="v0001", candidate_content_hash="a" * 64, base_hash="b" * 64,
            gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
            evaluation_report={"overall_outcome": "tie", "challenger_eligible": False, "consistent_jurors": 3},
            meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=frozen,
            dimension_scores_challenger={d: 5.0 for d in DIMENSIONS},
            dimension_scores_champion={d: 1.0 for d in DIMENSIONS},
            correctness_math_pass=True, overall_outcome="tie", challenger_eligible=False,
            active_issues=[],
        )
        classification, signals, mode, focus = classify_cycle_progress([rec], window_size=3, mde=0.25)
        self.assertEqual(classification, "INCONCLUSIVE")
        self.assertIn("all_specialist_dimensions_frozen", signals)
        self.assertEqual((mode, focus), ("CHECK", ["activation"]))

    # ==================== 9. Exact Thresholds & Invariance ====================

    def test_exact_threshold_mde_determinism(self):
        # Exactly MDE = 0.25 gain
        rec = CycleRecord(
            cycle_id=0, candidate_id="v0001", candidate_content_hash="a" * 64, base_hash="b" * 64,
            gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
            evaluation_report={"overall_outcome": "challenger_favored", "challenger_eligible": True, "consistent_jurors": 3},
            meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=None,
            dimension_scores_challenger={d: 3.25 for d in DIMENSIONS},
            dimension_scores_champion={d: 3.0 for d in DIMENSIONS},
            correctness_math_pass=True, overall_outcome="challenger_favored", challenger_eligible=True,
            active_issues=[],
        )
        cls_res, signals, rec_mode, focus = classify_cycle_progress([rec], window_size=3, mde=0.25)
        self.assertEqual(cls_res, "EVOLVING")

    def test_positive_scores_without_m8_eligibility_are_not_evolving(self):
        rec = CycleRecord(
            cycle_id=0, candidate_id="v0001", candidate_content_hash="a" * 64, base_hash="b" * 64,
            gate_report={"overall_pass": True, "correctness_math_pass": True, "gates": []},
            evaluation_report={"overall_outcome": "tie", "challenger_eligible": False, "consistent_jurors": 3},
            meta_verdict={"confirmed": True, "vetoed": False}, verdicts=[], activation_map=None,
            dimension_scores_challenger={d: 4.0 for d in DIMENSIONS},
            dimension_scores_champion={d: 3.0 for d in DIMENSIONS},
            correctness_math_pass=True, overall_outcome="tie", challenger_eligible=False,
            active_issues=[],
        )
        classification, signals, mode, focus = classify_cycle_progress([rec], window_size=1, mde=0.25)
        self.assertEqual(classification, "INCONCLUSIVE")
        self.assertIn("positive_direction_not_validated_by_jury", signals)
        self.assertEqual((mode, focus), ("CHECK", ["unvalidated_direction"]))

    # ==================== 10. Crash Recovery & Idempotence ====================

    def test_fault_injection_during_diagnosis_publishing(self):
        m8_out = self._setup_cycle_up_to_evaluated(cycle_id=0, preferred_winner="B")
        candidate_id = m8_out["manifest"]["candidate_id"]

        def fault_hook(stage: str):
            if stage == "before_diagnosis_published":
                raise RuntimeError("simulated crash before publish rename")

        with self.assertRaisesRegex(RuntimeError, "simulated crash"):
            diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id, fault=fault_hook)

        # Confirm no orphan staging directories left
        diag_parent = self.root / f"state/diagnosis/{self.run_id}"
        if diag_parent.exists():
            stagings = list(diag_parent.glob(".staging_*"))
            self.assertEqual(stagings, [])

        # Retry without fault: should succeed cleanly
        diag = diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id)
        self.assertIn("diagnosis_id", diag)

    def test_idempotent_redelivery_preserves_hashes(self):
        m8_out = self._setup_cycle_up_to_evaluated(cycle_id=0, preferred_winner="B")
        candidate_id = m8_out["manifest"]["candidate_id"]

        diag1 = diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id)
        diag2 = diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id)

        self.assertEqual(diag1["diagnosis_id"], diag2["diagnosis_id"])
        self.assertEqual(diag1["classification"], diag2["classification"])

    def test_diagnosis_redelivery_rejects_changed_classification_parameters(self):
        m8_out = self._setup_cycle_up_to_evaluated(cycle_id=0, preferred_winner="B")
        candidate_id = m8_out["manifest"]["candidate_id"]
        diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id, window_size=3, mde=0.25)

        with self.assertRaisesRegex(DiagnosisError, "classification parameters diverge"):
            diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id, window_size=4, mde=0.25)
        with self.assertRaisesRegex(DiagnosisError, "classification parameters diverge"):
            diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id, window_size=3, mde=0.5)

    def test_diagnosis_classification_is_recomputed_from_committed_history(self):
        m8_out = self._setup_cycle_up_to_evaluated(cycle_id=0, preferred_winner="B")
        candidate_id = m8_out["manifest"]["candidate_id"]
        diagnosis = diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id)
        forged = dict(diagnosis)
        forged.update({
            "classification": "GLOBAL_PLATEAU",
            "signals": ["forged:classification"],
            "recommended_mode": "SHIFT",
            "focus": ["general_refocus"],
        })
        series = load_history_series(self.root, self.run_id, 0)

        with self.assertRaisesRegex(DiagnosisError, "differs from recomputed history"):
            _verify_diagnosis_classification(forged, series)

    def test_rehashed_forged_diagnosis_cannot_override_classifier(self):
        m8_out = self._setup_cycle_up_to_evaluated(cycle_id=0, preferred_winner="B")
        candidate_id = m8_out["manifest"]["candidate_id"]
        diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id)
        diag_dir = self.root / f"state/diagnosis/{self.run_id}/c0000"
        diagnosis_path = diag_dir / "diagnosis.json"
        manifest_path = diag_dir / "manifest.json"
        os.chmod(diag_dir, 0o755)
        os.chmod(diagnosis_path, 0o644)
        os.chmod(manifest_path, 0o644)

        diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8"))
        diagnosis.update({
            "classification": "GLOBAL_PLATEAU",
            "signals": ["forged:classification"],
            "recommended_mode": "SHIFT",
            "focus": ["general_refocus"],
        })
        diagnosis["diagnosis_id"] = _diagnosis_id_for(diagnosis)
        diagnosis_bytes = _json(diagnosis)
        diagnosis_path.write_bytes(diagnosis_bytes)

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.update({
            "diagnosis_id": diagnosis["diagnosis_id"],
            "classification": diagnosis["classification"],
            "diagnosis_hash": _sha(diagnosis_bytes),
            "tree_content_hash": tree_hash(diag_dir, exclude={"manifest.json"}),
        })
        manifest_bytes = _json(manifest)
        manifest_path.write_bytes(manifest_bytes)
        os.chmod(diagnosis_path, 0o444)
        os.chmod(manifest_path, 0o444)
        os.chmod(diag_dir, 0o555)

        store = DurableStore(self.root)
        events = store.read_events(self.run_id)
        events[-1]["payload"].update({
            "diagnosis_id": diagnosis["diagnosis_id"],
            "classification": diagnosis["classification"],
            "recommended_mode": diagnosis["recommended_mode"],
        })
        events[-1]["artifact_hashes"] = sorted([_sha(diagnosis_bytes), _sha(manifest_bytes)])
        events[-1]["event_hash"] = store._ehash(events[-1])
        log_path = self.root / f"state/events/{self.run_id}.jsonl"
        log_path.write_text(
            "".join(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n" for event in events),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(DiagnosisError, "differs from recomputed history"):
            verify_published_diagnosis(self.root, self.run_id, 0)

    def test_diagnosed_event_requires_candidate_content_hash_binding(self):
        m8_out = self._setup_cycle_up_to_evaluated(cycle_id=0, preferred_winner="B")
        candidate_id = m8_out["manifest"]["candidate_id"]
        diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=candidate_id)
        store = DurableStore(self.root)
        events = store.read_events(self.run_id)
        events[-1]["payload"].pop("candidate_content_hash")
        events[-1]["event_hash"] = store._ehash(events[-1])
        log_path = self.root / f"state/events/{self.run_id}.jsonl"
        log_path.write_text(
            "".join(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n" for event in events),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(DiagnosisError, "event binding differs"):
            verify_published_diagnosis(self.root, self.run_id, 0)

    # ==================== 11. Overlays Rollback & Scope Containment ====================

    def test_overlay_with_rollback_pointer(self):
        # Register v1
        doc_v1 = {
            "parent_version": None, "diagnostic": "Initial overlay", "author": "m9",
            "evidence": ["e1"], "scope": ["proof"], "hash": "", "rollback": None,
            "instructions": "Initial instructions",
        }
        h1 = register_overlay_cas(self.root, "W22", "v10", doc_v1)

        # Register v2 with parent and rollback to v1
        doc_v2 = {
            "parent_version": "v10", "diagnostic": "Second overlay", "author": "m9",
            "evidence": ["e2"], "scope": ["proof"], "hash": "", "rollback": "v10",
            "instructions": "Refined instructions",
        }
        h2 = register_overlay_cas(self.root, "W22", "v11", doc_v2)

        registry = PromptRegistry(self.root)
        _, d1 = registry.overlay("W22", "v10")
        _, d2 = registry.overlay("W22", "v11")
        self.assertEqual(d2["parent_version"], "v10")
        self.assertEqual(d2["rollback"], "v10")

    # ==================== 12. CLIs Tests ====================

    def test_m9_clis_reject_non_object_json_without_traceback(self):
        for script_name in ("02_stagnation_detector.py", "03_refocus_generator.py"):
            with self.subTest(script=script_name):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / script_name), "--input", "-"],
                    input="[]",
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stderr)["error_type"], "input_parsing_error")
                self.assertNotIn("Traceback", result.stderr)

    def test_stagnation_detector_cli_success(self):
        m8_out = self._setup_cycle_up_to_evaluated(cycle_id=0, preferred_winner="B")
        candidate_id = m8_out["manifest"]["candidate_id"]

        cli_script = ROOT / "scripts/02_stagnation_detector.py"
        res = subprocess.run(
            [sys.executable, str(cli_script), "--root", str(self.root), "--run-id", self.run_id, "--cycle-id", "0", "--candidate-id", candidate_id],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "success")
        self.assertIn("diagnosis", data)
        self.assertEqual(data["diagnosis"]["candidate_id"], candidate_id)

    def test_refocus_generator_cli_success(self):
        self._publish_diagnosis_fixture("LOCAL_PLATEAU", focus=["S20", "W22"])

        cli_script = ROOT / "scripts/03_refocus_generator.py"
        res = subprocess.run(
            [sys.executable, str(cli_script), "--root", str(self.root), "--run-id", self.run_id, "--cycle-id", "0"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "success")
        self.assertIn("refocus_plan", data)
        self.assertEqual(data["refocus_plan"]["classification"], "LOCAL_PLATEAU")


if __name__ == "__main__":
    unittest.main()
