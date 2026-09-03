"""Offline M10 policy and transactional-finalization regressions."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))

from article_loop import DurableStore, State, finalize
from article_loop.diagnosis import diagnose_cycle
from article_loop.finalization import FinalizationError, TransactionalFinalizer
from article_loop.policy import PolicyError, choose_action, decide, load_policy, pareto_relation
from control import test_m9_diagnosis as m9_tests


def _record(*, math=True, overall=True, eligible=True, outcome="challenger_favored", delta=1.0, same=False):
    scores_a = {"correctness_math": 4.0, "clarity": 4.0}
    scores_b = {key: value + delta for key, value in scores_a.items()}
    return SimpleNamespace(
        candidate_id="c-fixture", candidate_content_hash="a" * 64,
        base_hash=("a" if same else "b") * 64,
        gate_report={"overall_pass": overall, "correctness_math_pass": math, "report_id": "gate-1", "report_locator": "state/gates/c-fixture/report.json"},
        evaluation_report={"evaluation_id": "eval-1", "verdict_ids": ["v1", "v2"]},
        correctness_math_pass=math, challenger_eligible=eligible,
        overall_outcome=outcome, dimension_scores_challenger=scores_b,
        dimension_scores_champion=scores_a,
    )


class M10PolicyTableTests(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "extra_judgment_limit": 1,
            "classification_actions": {},
        }

    def action(self, classification, **record):
        diagnosis = {"classification": classification}
        return choose_action(_record(**record), diagnosis, self.policy, prior_extra_judgments=0, final_gate_report_ids=[])[0]

    def test_all_policy_rows_and_actions_are_closed(self):
        self.assertEqual(self.action("TECHNICAL_FAILURE"), "ABORT_TECHNICAL")
        self.assertEqual(self.action("REGRESSING"), "REJECT")
        self.assertEqual(self.action("INCONCLUSIVE"), "REQUEST_EXTRA_JUDGMENT")
        self.assertEqual(self.action("LOCAL_PLATEAU"), "REFOCUS_AND_CONTINUE")
        self.assertEqual(self.action("GLOBAL_PLATEAU"), "PAUSE")
        self.assertEqual(self.action("OSCILLATING"), "REFOCUS_AND_CONTINUE")
        self.assertEqual(self.action("EVOLVING"), "PROMOTE")
        self.assertEqual(self.action("EVOLVING", eligible=False, delta=0.0, same=True), "CONTINUE_UNCHANGED")
        self.assertEqual(self.action("EVOLVING", eligible=False, delta=0.0), "ARCHIVE_PARETO")

    def test_hard_math_gate_and_extra_judgment_limit_have_precedence(self):
        self.assertEqual(self.action("EVOLVING", math=False), "REJECT")
        action, reason = choose_action(
            _record(), {"classification": "INCONCLUSIVE"}, self.policy,
            prior_extra_judgments=1, final_gate_report_ids=[],
        )
        self.assertEqual((action, reason), ("PAUSE", "INCONCLUSIVE_LIMIT_REACHED"))

    def test_global_plateau_can_finalize_only_with_final_gate_evidence(self):
        action, reason = choose_action(
            _record(), {"classification": "GLOBAL_PLATEAU"}, self.policy,
            prior_extra_judgments=0, final_gate_report_ids=["final-1"],
        )
        self.assertEqual((action, reason), ("FINALIZE", "POLICY_SATISFIED"))

    def test_pareto_dominated_candidate_is_rejected_by_the_closed_table(self):
        action, reason = choose_action(
            _record(eligible=False, delta=0.0), {"classification": "EVOLVING"}, self.policy,
            prior_extra_judgments=0, final_gate_report_ids=[],
            frontier_relation={"dominated_by": ["candidate-existing"], "dominates": []},
        )
        self.assertEqual((action, reason), ("REJECT", "PARETO_DOMINATED"))


class M10ParetoTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.dimensions = tuple(m9_tests.DIMENSIONS)

    def _record(self, scores, *, math=True):
        return SimpleNamespace(
            candidate_id="candidate-current", correctness_math_pass=math,
            dimension_scores_challenger=dict(scores),
        )

    def _reference(self, identifier, scores):
        path = self.root / "versions" / "pareto" / identifier
        path.mkdir(parents=True)
        value = {
            "candidate_id": identifier, "candidate_content_hash": "a" * 64,
            "decision_id": "decision-" + identifier, "action": "ARCHIVE_PARETO",
            "applied_at": "2026-09-03T00:00:00Z", "reason_code": None,
            "scores": dict(scores), "correctness_math_pass": True,
            "pareto_relation": {"dominated_by": [], "dominates": []},
        }
        (path / "reference.json").write_text(
            json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8",
        )

    def test_full_eight_dimension_dominance_tradeoff_tie_and_hard_gate(self):
        reference = {dimension: 3.0 for dimension in self.dimensions}
        self._reference("candidate-existing", reference)
        with self.subTest("dominates"):
            self.assertEqual(
                pareto_relation(self.root, self._record({dimension: 4.0 for dimension in self.dimensions})),
                {"dominated_by": [], "dominates": ["candidate-existing"]},
            )
        with self.subTest("dominated"):
            self.assertEqual(
                pareto_relation(self.root, self._record({dimension: 2.0 for dimension in self.dimensions})),
                {"dominated_by": ["candidate-existing"], "dominates": []},
            )
        with self.subTest("tradeoff"):
            tradeoff = {dimension: (4.0 if index % 2 else 2.0) for index, dimension in enumerate(self.dimensions)}
            self.assertEqual(pareto_relation(self.root, self._record(tradeoff)), {"dominated_by": [], "dominates": []})
        with self.subTest("tie"):
            self.assertEqual(pareto_relation(self.root, self._record(reference)), {"dominated_by": [], "dominates": []})
        with self.subTest("hard gate"):
            with self.assertRaisesRegex(PolicyError, "mathematical hard gate"):
                pareto_relation(self.root, self._record(reference, math=False))


class M10IntegrationTests(unittest.TestCase):
    """Reuse M9's complete offline fixture to exercise the real M10 boundary."""

    @classmethod
    def setUpClass(cls):
        m9_tests.M9DiagnosisTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        m9_tests.M9DiagnosisTests.tearDownClass()

    def setUp(self):
        self.fixture = m9_tests.M9DiagnosisTests("runTest")
        self.fixture.setUp()
        self.root = self.fixture.root
        self.run_id = self.fixture.run_id

    def tearDown(self):
        self.fixture.tearDown()

    def _diagnosed_evolving_run(self):
        scores_a = {dimension: 3 for dimension in m9_tests.DIMENSIONS}
        scores_b = {dimension: 5 for dimension in m9_tests.DIMENSIONS}
        jurors = {
            juror_id: m9_tests.DimensionScoresJurorAdapter(
                juror_id=juror_id, specialty=specialty, preferred_winner="B",
                scores_a=scores_a, scores_b=scores_b,
            )
            for juror_id, specialty in (
                ("juror-math", "correctness_math"),
                ("juror-contrib", "scientific_contribution"),
                ("juror-clarity", "clarity"),
            )
        }
        m8 = self.fixture._setup_cycle_up_to_evaluated(
            cycle_id=0, preferred_winner="B", juror_adapters=jurors,
        )
        diagnosis = diagnose_cycle(
            self.root, self.run_id, cycle_id=0,
            candidate_id=m8["manifest"]["candidate_id"], window_size=1,
        )
        self.assertEqual(diagnosis["classification"], "EVOLVING")
        return m8, diagnosis

    def test_policy_publishes_content_addressed_decision_and_is_idempotent(self):
        _, diagnosis = self._diagnosed_evolving_run()
        first = decide(self.root, self.run_id, cycle_id=0)
        second = decide(self.root, self.run_id, cycle_id=0)
        self.assertEqual(first, second)
        self.assertEqual(first["action"], "PROMOTE")
        self.assertEqual(first["decided_at"], diagnosis["created_at"])
        events = DurableStore(self.root).read_events(self.run_id)
        self.assertEqual(events[-1]["state_to"], State.DECIDED)
        decision_path = self.root / "state/decisions" / self.run_id / "c0000/decision.json"
        self.assertEqual(oct(decision_path.stat().st_mode & 0o777), "0o444")

    def test_promotion_is_exactly_once_and_keeps_challenger_immutable(self):
        m8, _ = self._diagnosed_evolving_run()
        decision = decide(self.root, self.run_id, cycle_id=0)
        challenger = self.root / "versions/challengers" / m8["manifest"]["candidate_id"]
        before = {path.relative_to(challenger).as_posix(): path.read_bytes() for path in challenger.rglob("*") if path.is_file()}
        finalizer = TransactionalFinalizer(self.root, clock=lambda: "2026-09-03T00:00:00Z")
        first = finalizer.finalize(self.run_id, cycle_id=0)
        second = finalizer.finalize(self.run_id, cycle_id=0)
        self.assertEqual(first, second)
        self.assertEqual(first["action"], decision["action"])
        self.assertEqual(first["state_after"], State.CYCLE_COMPLETE)
        self.assertEqual({path.relative_to(challenger).as_posix(): path.read_bytes() for path in challenger.rglob("*") if path.is_file()}, before)
        pointer = json.loads((self.root / "versions/champion/current.json").read_text(encoding="utf-8"))
        self.assertEqual(pointer["content_hash"], m8["manifest"]["content_hash"])
        self.assertTrue((self.root / "versions/champion/v0001").is_dir())

    def test_public_finalize_delegates_to_the_m10_decision_finalizer(self):
        self._diagnosed_evolving_run()
        decide(self.root, self.run_id, cycle_id=0)
        receipt = asyncio.run(finalize(self.root))
        self.assertEqual(receipt["state_after"], State.CYCLE_COMPLETE)
        self.assertEqual(DurableStore(self.root).read_events(self.run_id)[-1]["state_to"], State.CYCLE_COMPLETE)

    def test_crash_after_destination_rename_recovers_without_second_champion(self):
        self._diagnosed_evolving_run()
        decide(self.root, self.run_id, cycle_id=0)

        def crash(stage):
            if stage == "after_destination_rename":
                raise RuntimeError("simulated crash")

        with self.assertRaisesRegex(RuntimeError, "simulated crash"):
            TransactionalFinalizer(self.root, fault=crash, clock=lambda: "2026-09-03T00:00:00Z").finalize(self.run_id, cycle_id=0)
        receipt = TransactionalFinalizer(self.root, clock=lambda: "2026-09-03T00:00:00Z").finalize(self.run_id, cycle_id=0)
        self.assertEqual(receipt["state_after"], State.CYCLE_COMPLETE)
        versions = sorted(path.name for path in (self.root / "versions/champion").iterdir() if path.is_dir())
        self.assertEqual(versions, ["v0000", "v0001"])

    def test_crash_after_pointer_swap_recovers_without_overwriting_history(self):
        self._diagnosed_evolving_run()
        decide(self.root, self.run_id, cycle_id=0)

        def crash(stage):
            if stage == "after_pointer_swap":
                raise RuntimeError("simulated crash")

        with self.assertRaisesRegex(RuntimeError, "simulated crash"):
            TransactionalFinalizer(self.root, fault=crash, clock=lambda: "2026-09-03T00:00:00Z").finalize(self.run_id, cycle_id=0)
        receipt = TransactionalFinalizer(self.root, clock=lambda: "2026-09-03T00:00:00Z").finalize(self.run_id, cycle_id=0)
        self.assertEqual(receipt["state_after"], State.CYCLE_COMPLETE)
        self.assertEqual(
            sorted(path.name for path in (self.root / "versions/champion").iterdir() if path.is_dir()),
            ["v0000", "v0001"],
        )

    def test_mutated_challenger_after_decision_blocks_finalizer_without_effect(self):
        m8, _ = self._diagnosed_evolving_run()
        decide(self.root, self.run_id, cycle_id=0)
        candidate = self.root / "versions/challengers" / m8["manifest"]["candidate_id"]
        target = next(path for path in candidate.rglob("*") if path.is_file() and path.name != "manifest.json")
        os.chmod(target, 0o644)
        target.write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(FinalizationError, "evaluation evidence cannot be revalidated"):
            TransactionalFinalizer(self.root).finalize(self.run_id, cycle_id=0)
        self.assertFalse((self.root / "versions/champion/current.json").exists())


class M10CliTests(unittest.TestCase):
    def test_cli_rejects_unsupported_json_parameter(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        payload = Path(temporary.name) / "payload.json"
        payload.write_text(json.dumps({"run_id": "r", "test_mode": True}), encoding="utf-8")
        import subprocess
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/04_compensation_policy.py"), "--input", str(payload)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("unsupported parameters", result.stderr)
