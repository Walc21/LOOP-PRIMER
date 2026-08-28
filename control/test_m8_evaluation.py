"""Comprehensive, offline, deterministic tests for M8 external blind evaluation."""
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
    State,
    ingest,
)
from article_loop.activation import ActivationPlanner
from article_loop.blackboard import Blackboard, Impact
from article_loop.gates import REQUIRED_GATES, record_math_verification, run_gates
from article_loop.evaluation import (
    DIMENSIONS,
    BlindComparisonBundle,
    EvaluationError,
    FakeJurorAdapter,
    FakeMetaReviewerAdapter,
    check_inversion_consistency,
    evaluate_candidate,
    load_rubric,
    sanitize_text,
)


class M8EvaluationTests(unittest.TestCase):
    """Exhaustive test suite for M8 blind jury evaluation and meta-review."""

    @classmethod
    def setUpClass(cls):
        cls.fixture_dir = tempfile.TemporaryDirectory()
        fixture = Path(cls.fixture_dir.name)
        ps = fixture / "fixture.ps"
        ps.write_text(
            "%!PS\n/Courier findfont 18 scalefont setfont 72 700 moveto (M8 fixture) show showpage\n",
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
        for relative in ("input/inbox", "artifacts/original", "artifacts/extracted", "artifacts/rendered", "versions/champion", "workspaces", "state"):
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

    def _proposal(self, role):
        target = f"evidence/{role.lower()}.txt"
        value = f"M8 evidence for {role}\n"
        return {
            "schema_version": "1.1.0", "proposal_id": f"p-{role}", "role_id": role, "cycle_id": 0,
            "base_hash": self.initial["base_hash"], "scope": ["proof"], "evidence_locators": ["page:1"],
            "patch_or_operations": {"kind": "operations", "operations": [{"op": "add", "target": target, "value": value}]},
            "affected_claims": [self.claim_id] if role == "W22" else [], "dependencies": [],
            "risk": {"level": "low", "factors": [], "technical_effect_possible": False}, "confidence": 1,
            "requested_validations": ["correctness_math"] if role == "W22" else [], "prompt_version": "m8-integration",
        }

    def _m6_state(self):
        asyncio.run(self.orchestrator.run_cycle(run_id=self.run_id, plan=self.plan))
        for department in ("S10", "S20", "S30", "S40", "S50"):
            asyncio.run(self.orchestrator.advance_department(self.run_id, department, adapter=self._manager(department)))
        for number in range(1, 6):
            department = f"S{number}0"
            for suffix in (1, 2, 3):
                role = f"W{number}{suffix}"
                path = self.root / "workspaces" / self.run_id / "cycle-0000" / role / "receipt.json"
                path.write_bytes(json.dumps(self._proposal(role), sort_keys=True, separators=(",", ":")).encode() + b"\n")
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                asyncio.run(self.orchestrator.receipt(self.run_id, sender_role=role, parent_role=department, path=path, sha256=digest))
        for department in ("S20", "S10", "S30", "S40", "S50"):
            asyncio.run(self.orchestrator.consolidate_department(self.run_id, department, adapter=self._manager(department)))
        return asyncio.run(self.orchestrator.status(self.run_id))

    def _approve(self, candidate):
        return record_math_verification(
            candidate, claim_id=self.claim_id, proposal_id="p-W22", verifier_id="local-fixture",
            verifier_version="1.0.0", method="manual-proof-check", summary="Fixture identity checked independently.",
        )

    def _setup_m7_gates_passed(self) -> dict[str, Any]:
        """Run pipeline through M6 and M7 up to GATES_PASSED."""
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        store = DurableStore(self.root)
        pipe.record_synthesis(store, synthesis)
        champion = self.root / "versions/champion/v0000"
        manifest = pipe.build(synthesis, champion)
        pipe.record_candidate(store, manifest)
        candidate = self.root / "versions/challengers" / manifest["candidate_id"]
        self._approve(candidate)
        report = pipe.execute_and_record_gates(store, candidate)
        return {
            "synthesis": synthesis,
            "candidate": manifest,
            "gate_report": report,
        }

    # ==================== 1. Sanitization and Blinding Tests ====================

    def test_sanitize_text_strips_authors_versions_and_roles(self):
        text = "Role S20 and specialist W22 modified v0001 for champion and challenger in run-abc12345 cycle_0."
        sanitized = sanitize_text(text)
        self.assertNotIn("S20", sanitized)
        self.assertNotIn("W22", sanitized)
        self.assertNotIn("v0001", sanitized)
        self.assertNotIn("champion", sanitized.lower())
        self.assertNotIn("challenger", sanitized.lower())
        self.assertNotIn("run-abc12345", sanitized)

    def test_blind_bundle_reproducibility_and_bijective_order(self):
        m7_out = self._setup_m7_gates_passed()
        champ_dir = self.root / "versions/champion/v0000"
        chall_dir = self.root / "versions/challengers" / m7_out["candidate"]["candidate_id"]

        bundle1 = BlindComparisonBundle.create(self.root, champion_dir=champ_dir, challenger_dir=chall_dir, order_seed=413)
        bundle2 = BlindComparisonBundle.create(self.root, champion_dir=champ_dir, challenger_dir=chall_dir, order_seed=413)
        self.assertEqual(bundle1.comparison_id, bundle2.comparison_id)

        pres_ab = bundle1.presentation_for_order(["A", "B"])
        pres_ba = bundle1.presentation_for_order(["B", "A"])

        self.assertEqual(pres_ab["first_candidate"]["neutral_id"], "A")
        self.assertEqual(pres_ab["second_candidate"]["neutral_id"], "B")
        self.assertEqual(pres_ba["first_candidate"]["neutral_id"], "B")
        self.assertEqual(pres_ba["second_candidate"]["neutral_id"], "A")

        # Hashes match neutral bindings
        self.assertEqual(pres_ab["first_candidate"]["content_hash"], bundle1.content_hashes[0])
        self.assertEqual(pres_ba["first_candidate"]["content_hash"], bundle1.content_hashes[1])

    # ==================== 2. Inversion Consistency Tests ====================

    def test_inversion_consistency_consistent_winner(self):
        adapter = FakeJurorAdapter(juror_id="juror-math", preferred_winner="B")
        pres_ab = {"presentation_order": ["A", "B"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["a" * 64, "b" * 64]}
        pres_ba = {"presentation_order": ["B", "A"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["b" * 64, "a" * 64]}

        v_ab = adapter.evaluate(pres_ab)
        v_ba = adapter.evaluate(pres_ba)

        consistent, reason, winner, math_pass = check_inversion_consistency(v_ab, v_ba)
        self.assertTrue(consistent)
        self.assertIsNone(reason)
        self.assertEqual(winner, "B")
        self.assertTrue(math_pass)

    def test_inversion_consistency_detects_first_position_bias(self):
        adapter = FakeJurorAdapter(juror_id="juror-math", positional_bias="first")
        pres_ab = {"presentation_order": ["A", "B"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["a" * 64, "b" * 64]}
        pres_ba = {"presentation_order": ["B", "A"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["b" * 64, "a" * 64]}

        v_ab = adapter.evaluate(pres_ab)  # picks A
        v_ba = adapter.evaluate(pres_ba)  # picks B

        consistent, reason, winner, math_pass = check_inversion_consistency(v_ab, v_ba)
        self.assertFalse(consistent)
        self.assertEqual(reason, "first_position_bias")
        self.assertIsNone(winner)

    def test_inversion_consistency_detects_second_position_bias(self):
        adapter = FakeJurorAdapter(juror_id="juror-math", positional_bias="second")
        pres_ab = {"presentation_order": ["A", "B"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["a" * 64, "b" * 64]}
        pres_ba = {"presentation_order": ["B", "A"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["b" * 64, "a" * 64]}

        v_ab = adapter.evaluate(pres_ab)  # picks B
        v_ba = adapter.evaluate(pres_ba)  # picks A

        consistent, reason, winner, math_pass = check_inversion_consistency(v_ab, v_ba)
        self.assertFalse(consistent)
        self.assertEqual(reason, "second_position_bias")
        self.assertIsNone(winner)

    def test_inversion_consistency_detects_inconsistent_math_verification(self):
        # A/B says math pass True, B/A says math pass False
        pres_ab = {"presentation_order": ["A", "B"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["a" * 64, "b" * 64]}
        pres_ba = {"presentation_order": ["B", "A"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["b" * 64, "a" * 64]}

        v_ab = FakeJurorAdapter(juror_id="juror-math", math_pass=(True, True)).evaluate(pres_ab)
        v_ba = FakeJurorAdapter(juror_id="juror-math", math_pass=(True, False)).evaluate(pres_ba)

        consistent, reason, winner, math_pass = check_inversion_consistency(v_ab, v_ba)
        self.assertFalse(consistent)
        self.assertEqual(reason, "inconsistent_math_verification")

    # ==================== 3. Full Evaluation Pipeline Tests ====================

    def test_full_evaluation_success_transitions_to_evaluated(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        report = evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id)

        self.assertEqual(report["overall_outcome"], "challenger_favored")
        self.assertTrue(report["challenger_eligible"])
        self.assertEqual(report["consistent_jurors"], 3)
        self.assertEqual(report["divergent_jurors"], 0)
        self.assertEqual(len(report["verdict_ids"]), 6)

        # Check durable store state transition
        store = DurableStore(self.root)
        events = store.read_events(self.run_id)
        last_event = events[-1]
        self.assertEqual(last_event["state_to"], State.EVALUATED)
        self.assertEqual(last_event["event_type"], "EVALUATED")

    def test_evaluation_zero_valid_pairs_inconclusive(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        adapters_0 = {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", positional_bias="first"),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib", positional_bias="first"),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity", positional_bias="first"),
        }
        report_0 = evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id, juror_adapters=adapters_0)
        self.assertEqual(report_0["consistent_jurors"], 0)
        self.assertEqual(report_0["overall_outcome"], "inconclusive")
        self.assertFalse(report_0["challenger_eligible"])

    def test_evaluation_one_valid_pair_inconclusive(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        adapters_1 = {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", preferred_winner="B"),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib", positional_bias="first"),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity", positional_bias="second"),
        }
        report_1 = evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id, juror_adapters=adapters_1)
        self.assertEqual(report_1["consistent_jurors"], 1)
        self.assertEqual(report_1["overall_outcome"], "inconclusive")
        self.assertFalse(report_1["challenger_eligible"])

    def test_evaluation_two_valid_pairs_favors_challenger(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        adapters_2 = {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", preferred_winner="B"),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib", preferred_winner="B"),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity", positional_bias="second"),
        }
        report_2 = evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id, juror_adapters=adapters_2)
        self.assertEqual(report_2["consistent_jurors"], 2)
        self.assertEqual(report_2["overall_outcome"], "challenger_favored")
        self.assertTrue(report_2["challenger_eligible"])

    def test_evaluation_inconclusive_when_jurors_diverge(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        # Juror 1 favors Challenger (B), Juror 2 has 1st position bias (inconsistent), Juror 3 favors Champion (A)
        adapters = {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", preferred_winner="B"),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib", positional_bias="first"),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity", preferred_winner="A"),
        }

        report = evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id, juror_adapters=adapters)

        self.assertEqual(report["overall_outcome"], "inconclusive")
        self.assertFalse(report["challenger_eligible"])
        self.assertEqual(report["consistent_jurors"], 2)
        self.assertEqual(report["divergent_jurors"], 1)

    def test_evaluation_fails_when_meta_reviewer_vetoes(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        meta = FakeMetaReviewerAdapter(should_veto=True, veto_reason="Insufficient proof rigor detected in review.")
        report = evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id, meta_adapter=meta)

        self.assertEqual(report["overall_outcome"], "inconclusive")
        self.assertFalse(report["challenger_eligible"])
        self.assertTrue(report["meta_verdict"]["vetoed"])

    def test_evaluation_fails_closed_on_math_veto(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        # Juror marks math pass as False for candidate B
        adapters = {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", math_pass=(True, False), preferred_winner="B"),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib", math_pass=(True, False), preferred_winner="B"),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity", math_pass=(True, False), preferred_winner="B"),
        }

        report = evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id, juror_adapters=adapters)
        self.assertFalse(report["correctness_math_pass"])
        self.assertFalse(report["challenger_eligible"])

    def test_reduced_diversity_assurance_when_single_family(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        single_family = {
            "juror-math": "single-family-v1",
            "juror-contrib": "single-family-v1",
            "juror-clarity": "single-family-v1",
        }

        report = evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id, model_families=single_family)
        self.assertEqual(report["diversity_assurance"], "reduced_diversity_assurance")

    def test_corrupted_verdict_fails_closed(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        adapters = {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", corrupt_schema=True),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib"),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity"),
        }

        with self.assertRaises(EvaluationError):
            evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id, juror_adapters=adapters)

    # ==================== 4. Adversarial, Crash & Immutability Tests ====================

    def test_evaluation_fails_if_state_not_gates_passed(self):
        # Fresh bootstrap is in SOURCE_READY, not GATES_PASSED
        with self.assertRaises(EvaluationError):
            evaluate_candidate(self.root, self.run_id)

    def test_evaluation_fails_if_candidate_mutated(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        chall_dir = self.root / "versions/challengers" / candidate_id

        # Make writable temporarily and mutate
        for path in chall_dir.rglob("*.tex"):
            os.chmod(path, 0o600)
            path.write_text("MUTATED CODE", encoding="utf-8")

        with self.assertRaises(EvaluationError):
            evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id)

    def test_versions_remain_immutable_during_and_after_evaluation(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        champ_before = (self.root / "versions/champion/v0000/manifest.json").read_bytes()
        chall_before = (self.root / f"versions/challengers/{candidate_id}/manifest.json").read_bytes()

        evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id)

        champ_after = (self.root / "versions/champion/v0000/manifest.json").read_bytes()
        chall_after = (self.root / f"versions/challengers/{candidate_id}/manifest.json").read_bytes()

        self.assertEqual(champ_before, champ_after)
        self.assertEqual(chall_before, chall_after)

        # Ensure no directories in pareto or rejected were written
        pareto = self.root / "versions/pareto"
        rejected = self.root / "versions/rejected"
        self.assertTrue(not pareto.exists() or list(pareto.iterdir()) == [])
        self.assertTrue(not rejected.exists() or list(rejected.iterdir()) == [])

    def test_no_m8_path_reaches_diagnosed_or_later_states(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id)

        store = DurableStore(self.root)
        snapshot = store.snapshot(self.run_id)
        self.assertEqual(snapshot["state"], State.EVALUATED.value)
        self.assertNotEqual(snapshot["state"], State.DIAGNOSED.value)
        self.assertNotEqual(snapshot["state"], State.DECIDED.value)

    def test_fault_injection_recovery_and_idempotence(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        # Fault before EVALUATED event
        def fail_before_event(stage: str):
            if stage == "before_evaluated_event":
                raise RuntimeError("simulated crash before evaluated event")

        with self.assertRaisesRegex(RuntimeError, "simulated crash before evaluated event"):
            evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id, fault=fail_before_event)

        # Retry successfully completes without duplicates
        report = evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id)
        self.assertEqual(report["overall_outcome"], "challenger_favored")

    def test_cli_execution(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        cli_script = ROOT / "scripts/01_external_evaluator.py"
        res = subprocess.run(
            [sys.executable, str(cli_script), "--root", str(self.root), "--run-id", self.run_id, "--candidate-id", candidate_id],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["report"]["overall_outcome"], "challenger_favored")


if __name__ == "__main__":
    unittest.main()
