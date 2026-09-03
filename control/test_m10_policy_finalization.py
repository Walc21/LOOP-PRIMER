"""Offline M10 policy and transactional-finalization regressions."""

from __future__ import annotations

import asyncio
import hashlib
import json
import multiprocessing
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
from article_loop.diagnosis import diagnose_cycle, load_history_series
from article_loop.finalization import FinalizationError, TransactionalFinalizer
from article_loop.policy import PolicyError, _budget_exhausted, choose_action, decide, load_policy, pareto_relation, verify_finalization_evidence
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


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _content_id(prefix, field, value):
    body = dict(value)
    body.pop(field, None)
    return f"{prefix}-{hashlib.sha256(_canonical(body)).hexdigest()[:32]}"


def _finalize_worker(root, run_id, barrier, results):
    try:
        barrier.wait(timeout=20)
        receipt = TransactionalFinalizer(root).finalize(run_id, cycle_id=0)
        results.put(("ok", receipt["receipt_id"]))
    except Exception as exc:  # pragma: no cover - assertion occurs in parent
        results.put(("error", f"{type(exc).__name__}: {exc}"))


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

    def test_budget_limit_is_safe_at_the_boundary_and_pauses_when_exceeded(self):
        record = _record()
        record.activation_map = {
            "paused": False,
            "budget": {
                "limits": {"max_estimated_tokens": 10, "max_wall_time_seconds": 5},
                "estimated_tokens": 10,
                "wall_time_seconds": 5,
            },
        }
        self.assertFalse(_budget_exhausted(record))
        record.activation_map["budget"]["estimated_tokens"] = 11
        self.assertTrue(_budget_exhausted(record))
        self.assertEqual(
            choose_action(record, {"classification": "EVOLVING"}, self.policy,
                          prior_extra_judgments=0, final_gate_report_ids=[], budget_exhausted=True),
            ("PAUSE", "BUDGET_EXHAUSTED"),
        )


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

    def _diagnosed_with_scores(self, scores_a, scores_b, *, preferred_winner):
        jurors = {
            juror_id: m9_tests.DimensionScoresJurorAdapter(
                juror_id=juror_id, specialty=specialty, preferred_winner=preferred_winner,
                scores_a=scores_a, scores_b=scores_b,
            )
            for juror_id, specialty in (
                ("juror-math", "correctness_math"),
                ("juror-contrib", "scientific_contribution"),
                ("juror-clarity", "clarity"),
            )
        }
        m8 = self.fixture._setup_cycle_up_to_evaluated(
            cycle_id=0, preferred_winner=preferred_winner, juror_adapters=jurors,
        )
        diagnosis = diagnose_cycle(
            self.root, self.run_id, cycle_id=0,
            candidate_id=m8["manifest"]["candidate_id"], window_size=1,
        )
        return m8, diagnosis

    def _publish_final_gate_package(self):
        """Create only immutable fixture evidence; production M10 never creates it."""
        record = load_history_series(self.root, self.run_id, 0, store=DurableStore(self.root))[-1]
        candidate_manifest = self.root / "versions/challengers" / record.candidate_id / "manifest.json"
        manifest_hash = hashlib.sha256(candidate_manifest.read_bytes()).hexdigest()
        rendered = self.root / "artifacts/rendered" / self.run_id / "c0000" / "final.pdf"
        rendered.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.root / "input/inbox/artigo.pdf", rendered)
        os.chmod(rendered, 0o444)
        rendered_hash = hashlib.sha256(rendered.read_bytes()).hexdigest()
        report_dir = self.root / "reports" / self.run_id / "c0000"
        report_dir.mkdir(parents=True, exist_ok=True)
        final_path = report_dir / "final-report.json"
        final_report = {
            "schema_version": "1.0.0", "run_id": self.run_id, "cycle_id": 0,
            "candidate_id": record.candidate_id, "candidate_content_hash": record.candidate_content_hash,
            "gate_report_id": record.gate_report["report_id"], "required_roles": ["W22", "W51", "W53"],
            "candidate_manifest_hash": manifest_hash, "rendered_pdf_hash": rendered_hash, "overall_pass": True,
        }
        final_report["final_report_id"] = _content_id("fr", "final_report_id", final_report)
        final_path.write_bytes(_canonical(final_report))
        os.chmod(final_path, 0o444)
        references = {
            "candidate_manifest": {
                "locator": f"versions/challengers/{record.candidate_id}/manifest.json", "sha256": manifest_hash,
            },
            "rendered_pdf": {
                "locator": f"artifacts/rendered/{self.run_id}/c0000/final.pdf", "sha256": rendered_hash,
            },
            "final_report": {
                "locator": f"reports/{self.run_id}/c0000/final-report.json",
                "sha256": hashlib.sha256(final_path.read_bytes()).hexdigest(),
            },
        }
        final_gate_dir = self.root / "state/final-gates" / self.run_id / "c0000"
        final_gate_dir.mkdir(parents=True, exist_ok=True)
        paths = {"rendered_pdf": rendered, "final_report": final_path, "candidate_manifest": candidate_manifest}
        ids = []
        for role_id, gate_id in (("W22", "correctness_math"), ("W51", "manifest_integrity"), ("W53", "pdf_valid")):
            report = {
                "schema_version": "1.0.0", "run_id": self.run_id, "cycle_id": 0,
                "candidate_id": record.candidate_id, "candidate_content_hash": record.candidate_content_hash,
                "gate_report_id": record.gate_report["report_id"], "role_id": role_id,
                "gate_id": gate_id, "overall_pass": True, **references,
            }
            report["report_id"] = _content_id("fg", "report_id", report)
            path = final_gate_dir / f"{role_id}.json"
            path.write_bytes(_canonical(report))
            os.chmod(path, 0o444)
            paths[role_id] = path
            ids.append(report["report_id"])
        return record, sorted(ids), paths

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

    def test_local_plateau_and_inconclusive_publish_their_distinct_next_steps(self):
        self.fixture._publish_diagnosis_fixture("LOCAL_PLATEAU")
        decision = decide(self.root, self.run_id, cycle_id=0)
        self.assertEqual(decision["action"], "REFOCUS_AND_CONTINUE")
        receipt = TransactionalFinalizer(self.root).finalize(self.run_id, cycle_id=0)
        self.assertTrue((self.root / receipt["destination"]).is_file())

    def test_inconclusive_requests_one_extra_judgment(self):
        self.fixture._publish_diagnosis_fixture("INCONCLUSIVE")
        decision = decide(self.root, self.run_id, cycle_id=0)
        self.assertEqual(decision["action"], "REQUEST_EXTRA_JUDGMENT")
        receipt = TransactionalFinalizer(self.root).finalize(self.run_id, cycle_id=0)
        self.assertTrue((self.root / receipt["destination"]).is_file())

    def test_global_plateau_without_final_package_pauses(self):
        self.fixture._publish_diagnosis_fixture("GLOBAL_PLATEAU")
        decision = decide(self.root, self.run_id, cycle_id=0)
        self.assertEqual((decision["action"], decision["reason_code"]), ("PAUSE", "TECHNICAL_BLOCK"))
        receipt = TransactionalFinalizer(self.root).finalize(self.run_id, cycle_id=0)
        self.assertEqual((receipt["action"], receipt["state_after"]), ("PAUSE", State.PAUSED))

    def test_tradeoff_archives_with_an_immutable_pareto_reference(self):
        champion = {dimension: 4 for dimension in m9_tests.DIMENSIONS}
        tradeoff = {dimension: 5 for dimension in m9_tests.DIMENSIONS}
        tradeoff["clarity"] = 3
        _, diagnosis = self._diagnosed_with_scores(champion, tradeoff, preferred_winner="B")
        self.assertEqual(diagnosis["classification"], "EVOLVING")
        decision = decide(self.root, self.run_id, cycle_id=0)
        self.assertEqual(decision["action"], "ARCHIVE_PARETO")
        receipt = TransactionalFinalizer(self.root).finalize(self.run_id, cycle_id=0)
        self.assertTrue((self.root / receipt["destination"] / "reference.json").is_file())

    def test_regression_rejects_with_an_immutable_reference(self):
        champion = {dimension: 4 for dimension in m9_tests.DIMENSIONS}
        regressing = {dimension: 2 for dimension in m9_tests.DIMENSIONS}
        _, diagnosis = self._diagnosed_with_scores(champion, regressing, preferred_winner="A")
        self.assertEqual(diagnosis["classification"], "REGRESSING")
        decision = decide(self.root, self.run_id, cycle_id=0)
        self.assertEqual((decision["action"], decision["reason_code"]), ("REJECT", "JURY_UNFAVORABLE"))
        receipt = TransactionalFinalizer(self.root).finalize(self.run_id, cycle_id=0)
        self.assertTrue((self.root / receipt["destination"] / "reference.json").is_file())

    def test_global_plateau_finalizes_only_after_complete_hash_bound_package(self):
        self.fixture._publish_diagnosis_fixture("GLOBAL_PLATEAU")
        record, report_ids, _ = self._publish_final_gate_package()
        self.assertEqual(
            verify_finalization_evidence(self.root, self.run_id, 0, record, ["W22", "W51", "W53"]), report_ids,
        )
        decision = decide(self.root, self.run_id, cycle_id=0)
        self.assertEqual(decision["action"], "FINALIZE")
        self.assertEqual(decision["final_gate_report_ids"], report_ids)
        receipt = TransactionalFinalizer(self.root).finalize(self.run_id, cycle_id=0)
        self.assertEqual((receipt["action"], receipt["state_after"]), ("FINALIZE", State.FINALIZED))

    def test_final_gate_package_rejects_missing_or_mismatched_artifacts(self):
        self.fixture._publish_diagnosis_fixture("GLOBAL_PLATEAU")
        record, _, paths = self._publish_final_gate_package()
        for name in ("rendered_pdf", "final_report"):
            with self.subTest(name=name):
                path = paths[name]
                original = path.read_bytes()
                os.chmod(path, 0o644)
                path.unlink()
                with self.assertRaisesRegex(PolicyError, "(unavailable|missing)"):
                    verify_finalization_evidence(self.root, self.run_id, 0, record, ["W22", "W51", "W53"])
                path.write_bytes(original)
                os.chmod(path, 0o444)
        report = paths["W51"]
        body = json.loads(report.read_text(encoding="utf-8"))
        os.chmod(report, 0o644)
        body["gate_id"] = "pdf_valid"
        body["report_id"] = _content_id("fg", "report_id", body)
        report.write_bytes(_canonical(body))
        os.chmod(report, 0o444)
        with self.assertRaisesRegex(PolicyError, "role does not attest"):
            verify_finalization_evidence(self.root, self.run_id, 0, record, ["W22", "W51", "W53"])

    def test_decision_revalidation_blocks_final_artifact_mutation_after_decision(self):
        self.fixture._publish_diagnosis_fixture("GLOBAL_PLATEAU")
        _, _, paths = self._publish_final_gate_package()
        decide(self.root, self.run_id, cycle_id=0)
        target = paths["rendered_pdf"]
        os.chmod(target, 0o644)
        target.write_bytes(b"%PDF-tampered")
        os.chmod(target, 0o444)
        with self.assertRaisesRegex(FinalizationError, "closed policy"):
            TransactionalFinalizer(self.root).finalize(self.run_id, cycle_id=0)

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

    def test_every_durable_fault_boundary_recovers_exactly_once(self):
        self._diagnosed_evolving_run()
        decide(self.root, self.run_id, cycle_id=0)
        snapshot = tempfile.TemporaryDirectory()
        self.addCleanup(snapshot.cleanup)
        source = Path(snapshot.name) / "source"
        shutil.copytree(self.root, source)
        stages = (
            "after_file_fsync", "after_prepared", "after_hashes_revalidated",
            "before_destination_rename", "after_destination_rename", "after_pointer_swap",
            "after_destination_staged", "after_receipt", "after_checkpoint",
        )
        for stage in stages:
            with self.subTest(stage=stage):
                case = Path(snapshot.name) / stage
                shutil.copytree(source, case)
                tripped = False

                def crash(observed):
                    nonlocal tripped
                    if observed == stage and not tripped:
                        tripped = True
                        raise RuntimeError(f"simulated crash at {stage}")

                with self.assertRaisesRegex(RuntimeError, "simulated crash"):
                    TransactionalFinalizer(case, fault=crash).finalize(self.run_id, cycle_id=0)
                receipt = TransactionalFinalizer(case).finalize(self.run_id, cycle_id=0)
                self.assertEqual(receipt["state_after"], State.CYCLE_COMPLETE)
                self.assertEqual(
                    sorted(path.name for path in (case / "versions/champion").iterdir() if path.is_dir()),
                    ["v0000", "v0001"],
                )

    def test_two_processes_share_one_finalization_receipt(self):
        self._diagnosed_evolving_run()
        decide(self.root, self.run_id, cycle_id=0)
        context = multiprocessing.get_context("fork")
        barrier = context.Barrier(2)
        results = context.Queue()
        processes = [
            context.Process(target=_finalize_worker, args=(str(self.root), self.run_id, barrier, results))
            for _ in range(2)
        ]
        for process in processes:
            process.start()
        for process in processes:
            process.join(timeout=30)
            self.assertEqual(process.exitcode, 0)
        outcomes = [results.get(timeout=5) for _ in processes]
        self.assertEqual({outcome[0] for outcome in outcomes}, {"ok"})
        self.assertEqual(len({outcome[1] for outcome in outcomes}), 1)
        events = DurableStore(self.root).read_events(self.run_id)
        self.assertEqual(sum(event["event_type"] == "FINALIZATION_APPLIED" for event in events), 1)

    def test_adversarial_pointer_change_fails_closed_and_preserves_versions(self):
        self._diagnosed_evolving_run()
        decide(self.root, self.run_id, cycle_id=0)

        def mutate(stage):
            if stage == "after_destination_rename":
                pointer = self.root / "versions/champion/current.json"
                if pointer.exists():
                    os.chmod(pointer, 0o644)
                pointer.write_bytes(_canonical({"candidate_id": "v9999", "content_hash": "0" * 64}))
                os.chmod(pointer, 0o444)

        with self.assertRaisesRegex(FinalizationError, "pointer changed"):
            TransactionalFinalizer(self.root, fault=mutate).finalize(self.run_id, cycle_id=0)
        with self.assertRaisesRegex(FinalizationError, "compare-and-swap failed"):
            TransactionalFinalizer(self.root).finalize(self.run_id, cycle_id=0)
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
