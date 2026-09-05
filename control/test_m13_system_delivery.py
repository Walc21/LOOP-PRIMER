"""M13 acceptance: full real synthetic cycles and adversarial boundaries."""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import yaml

from control.m13_fixture import (
    ROOT, BETTER_TEX, SyntheticCycle, canonical, digest, fake_policy, remove_fixture,
)
from article_loop.delivery import DeliveryError, verify_delivery
from article_loop.diagnosis import DiagnosisError, diagnose_cycle, verify_published_diagnosis
from article_loop.evaluation import EvaluationError, FakeMetaReviewerAdapter, evaluate_candidate
from article_loop.finalization import FinalizationError, TransactionalFinalizer
from article_loop.gates import REQUIRED_GATES, run_gates
from article_loop.inference import InferenceRequest, InferenceRoutingError, ModelRegistry, ModelRouter
from article_loop.policy import PolicyError, decide
from article_loop.synthesis import SynthesisError


def inventory(root):
    return {p.relative_to(root).as_posix(): (digest(p), p.stat().st_mode) for p in root.rglob("*") if p.is_file() and not p.is_symlink()}


class M13SystemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Network is an external boundary; an accidental call fails the suite.
        self.network = patch.object(socket.socket, "connect", side_effect=AssertionError("M13 network forbidden"))
        self.network.start()
        self.addCleanup(self.network.stop)

    def fixture(self, *, routed=False):
        root = Path(self.temp.name) / "system"
        self.addCleanup(lambda: remove_fixture(root) if root.exists() else None)
        return SyntheticCycle(root, routed=routed)

    def evaluated(self, **kwargs):
        f = self.fixture()
        f.candidate()
        f.gates()
        f.evaluate(**kwargs)
        return f

    def decided(self):
        f = self.evaluated()
        f.diagnose()
        f.decide()
        return f

    def test_golden_ingestion_to_verified_promotion(self):
        f = self.fixture()
        f.run()
        report = verify_delivery(f.root, f.run_id)
        self.assertEqual(report["action"], "PROMOTE")
        self.assertEqual(report["state"], "CYCLE_COMPLETE")
        self.assertEqual(report["original_pdf"]["sha256"], f.pre_hash)
        self.assertEqual((digest(f.pdf), f.pdf.stat().st_size, f.pdf.stat().st_mode), (f.pre_hash, f.pre_size, f.pre_mode))
        self.assertEqual(len(report["proposal_ids"]), 15)
        self.assertEqual(len(report["department_packet_hashes"]), 5)
        self.assertEqual(len(report["verdict_ids"]), 6)
        self.assertEqual(tuple(gate["gate_id"] for gate in f.gate_report["gates"]), REQUIRED_GATES)
        self.assertEqual((f.root / report["artifact"]["locator"] / "latex-source/paper.tex").read_text(), BETTER_TEX)
        self.assertNotEqual(report["baseline"]["content_hash"], report["candidate"]["content_hash"])
        before = inventory(f.root)
        self.assertEqual(verify_delivery(f.root, f.run_id), report)
        self.assertEqual(inventory(f.root), before, "independent verification must be read-only")
        with self.assertRaises(DiagnosisError):
            verify_published_diagnosis(f.root, f.run_id, 0)

    def test_math_gate_failure_stops_before_jury_or_decision(self):
        f = self.fixture()
        f.candidate(approve_math=False)
        report = run_gates(f.candidate_dir)
        self.assertFalse(report["correctness_math_pass"])
        with self.assertRaises(SynthesisError):
            f.pipe.record_gates(f.store, report["report_locator"])
        with self.assertRaises(EvaluationError):
            evaluate_candidate(f.root, f.run_id)
        with self.assertRaises(PolicyError):
            decide(f.root, f.run_id, cycle_id=0)
        self.assertEqual(f.store.snapshot(f.run_id)["state"], "CANDIDATE_BUILT")
        self.assertFalse((f.root / "versions/champion/v0001").exists())

    def test_jury_math_veto_beats_excellent_scores_and_is_rejected(self):
        f = self.evaluated(math_pass=False, scores=(1, 5))
        self.assertFalse(f.evaluation["correctness_math_pass"])
        self.assertFalse(f.evaluation["challenger_eligible"])
        f.diagnose()
        self.assertEqual(f.decide()["action"], "REJECT")
        f.finalize()
        report = verify_delivery(f.root, f.run_id)
        self.assertEqual(report["action"], "REJECT")
        self.assertFalse((f.root / "versions/champion/v0001").exists())
        self.assertEqual(digest(f.pdf), f.pre_hash)

    def test_blind_presentations_invert_without_identity_leak(self):
        f = self.evaluated()
        forbidden = (f.run_id, f.manifest["candidate_id"], "v0000", "W41", "S40", "champion", "challenger", "workspaces", str(f.root))
        for juror in f.jurors.values():
            self.assertEqual({tuple(p["presentation_order"]) for p in juror.presentations}, {("A", "B"), ("B", "A")})
            for presentation in juror.presentations:
                body = json.dumps(presentation)
                for marker in forbidden:
                    self.assertNotIn(marker, body)
        self.assertTrue(all(item["consistent"] for item in f.evaluation["juror_evaluations"]))

    def test_positional_inconsistency_cannot_promote(self):
        f = self.evaluated(positional_bias="first")
        self.assertFalse(any(item["consistent"] for item in f.evaluation["juror_evaluations"]))
        self.assertFalse(f.evaluation["challenger_eligible"])
        f.diagnose()
        self.assertNotEqual(f.decide()["action"], "PROMOTE")
        f.finalize()
        self.assertFalse((f.root / "versions/champion/v0001").exists())

    def test_meta_cannot_substitute_gate_identity(self):
        class WrongGate(FakeMetaReviewerAdapter):
            def review(self, **kwargs):
                result = super().review(**kwargs)
                result["gate_report_id"] = "gate-forged"
                return result
        f = self.fixture()
        f.candidate()
        f.gates()
        with self.assertRaises(EvaluationError):
            f.evaluate(meta=WrongGate())
        self.assertEqual(f.store.snapshot(f.run_id)["state"], "GATES_PASSED")
        with self.assertRaises(DiagnosisError):
            f.diagnose()

    def test_replay_each_authoritative_stage_has_no_duplicate_effect(self):
        f = self.fixture(routed=True)
        f.candidate()
        calls = len(f.backend.calls)
        before = inventory(f.candidate_dir)
        self.assertEqual(f.pipe.build(f.synthesis, f.root / "versions/champion/v0000"), f.manifest)
        f.pipe.record_candidate(f.store, f.manifest)
        f.gates()
        f.evaluate()
        self.assertEqual(evaluate_candidate(f.root, f.run_id, cycle_id=0), f.evaluation)
        self.assertTrue(all(len(j.presentations) == 2 for j in f.jurors.values()))
        f.diagnose()
        self.assertEqual(f.diagnose(), f.diagnosis)
        first = f.decide()
        self.assertEqual(f.decide(), first)
        receipt = f.finalize()
        self.assertEqual(f.finalize(), receipt)
        self.assertEqual(len(f.backend.calls), calls)
        self.assertEqual(inventory(f.candidate_dir), before)
        events = f.store.read_events(f.run_id)
        for state in ("CANDIDATE_BUILT", "EVALUATED", "DIAGNOSED", "DECIDED", "COMMITTING", "CYCLE_COMPLETE"):
            self.assertEqual(sum(event["state_to"] == state for event in events), 1)
        verify_delivery(f.root, f.run_id)

    def test_finalizer_interruption_recovers_one_champion(self):
        f = self.decided()
        def crash(stage):
            if stage == "after_destination_rename":
                raise RuntimeError("M13 simulated interruption")
        with self.assertRaisesRegex(RuntimeError, "M13 simulated interruption"):
            f.finalize(fault=crash)
        self.assertEqual(f.store.snapshot(f.run_id)["state"], "COMMITTING")
        with self.assertRaises(DeliveryError):
            verify_delivery(f.root, f.run_id)
        f.finalize()
        report = verify_delivery(f.root, f.run_id)
        self.assertEqual(report["action"], "PROMOTE")
        self.assertEqual(sorted(p.name for p in (f.root / "versions/champion").iterdir() if p.is_dir()), ["v0000", "v0001"])

    def test_concurrent_finalization_has_one_published_truth(self):
        f = self.decided()
        barrier = threading.Barrier(2)
        def finalize(_):
            barrier.wait(timeout=10)
            return TransactionalFinalizer(f.root).finalize(f.run_id, cycle_id=0)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(finalize, range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(sum(e["event_type"] == "FINALIZATION_APPLIED" for e in f.store.read_events(f.run_id)), 1)
        verify_delivery(f.root, f.run_id)

    def test_mutated_challenger_blocks_finalization(self):
        f = self.decided()
        path = f.candidate_dir / "latex-source/paper.tex"
        path.chmod(0o644)
        path.write_text("tampered")
        path.chmod(0o444)
        with self.assertRaises(FinalizationError):
            f.finalize()
        self.assertFalse((f.root / "versions/champion/v0001").exists())

    def test_tampered_durable_artifacts_fail_independent_audit(self):
        f = self.fixture()
        f.run()
        report = verify_delivery(f.root, f.run_id)
        paths = {
            "original": f.pdf,
            "baseline": f.root / "versions/champion/v0000/baseline.pdf",
            "source_zip": f.root / "input/inbox/source.zip",
            "challenger": f.candidate_dir / "latex-source/paper.tex",
            "gate_report": f.root / f.gate_report["report_locator"],
            "verdict": next((f.root / f"state/evaluations/{f.run_id}/c0000/verdicts").glob("*.json")),
            "meta": f.root / f"state/evaluations/{f.run_id}/c0000/meta-verdict.json",
            "diagnosis": f.root / f"state/diagnosis/{f.run_id}/c0000/diagnosis.json",
            "decision": f.root / f"state/decisions/{f.run_id}/c0000/decision.json",
            "receipt": f.root / f"state/decisions/{f.run_id}/c0000/finalization-receipt.json",
            "synthesis": f.root / f.manifest["merge_receipt_locator"],
            "promoted": f.root / report["artifact"]["locator"] / "latex-source/paper.tex",
            "final_manifest": f.root / report["artifact"]["locator"] / "manifest.json",
        }
        for name, path in paths.items():
            with self.subTest(artifact=name):
                raw, mode = path.read_bytes(), path.stat().st_mode
                path.chmod(0o644)
                path.write_bytes(raw + b"!")
                path.chmod(mode)
                try:
                    with self.assertRaises(DeliveryError):
                        verify_delivery(f.root, f.run_id)
                finally:
                    path.chmod(0o644)
                    path.write_bytes(raw)
                    path.chmod(mode)
        self.assertEqual(verify_delivery(f.root, f.run_id), report)

    def test_missing_gate_and_symlink_are_rejected_without_repair(self):
        f = self.fixture()
        f.run()
        gate = f.root / f.gate_report["report_locator"]
        raw, mode = gate.read_bytes(), gate.stat().st_mode
        gate.parent.chmod(0o755)
        gate.unlink()
        with self.assertRaises(DeliveryError):
            verify_delivery(f.root, f.run_id)
        self.assertFalse(gate.exists())
        outside = Path(self.temp.name) / "external.json"
        outside.write_bytes(raw)
        gate.symlink_to(outside)
        with self.assertRaises(DeliveryError):
            verify_delivery(f.root, f.run_id)
        self.assertEqual(outside.read_bytes(), raw)
        gate.unlink()
        gate.write_bytes(raw)
        gate.chmod(mode)

    def test_forged_final_receipt_with_new_hash_is_not_authoritative(self):
        f = self.fixture()
        f.run()
        path = f.root / f"state/decisions/{f.run_id}/c0000/finalization-receipt.json"
        value = json.loads(path.read_bytes())
        value["destination"] = "versions/champion/v9999"
        body = {k: v for k, v in value.items() if k != "receipt_id"}
        value["receipt_id"] = "fin-" + hashlib.sha256(canonical(body)).hexdigest()[:32]
        path.chmod(0o644)
        path.write_bytes(canonical(value))
        path.chmod(0o444)
        with self.assertRaisesRegex(DeliveryError, "event binding"):
            verify_delivery(f.root, f.run_id)

    def test_routed_fake_payload_rejoins_complete_pipeline_and_audit(self):
        f = self.fixture(routed=True)
        f.run()
        report = verify_delivery(f.root, f.run_id)
        self.assertEqual(report["routed_inference"]["calls"], 3)
        self.assertEqual({r.role_id for r in f.backend.calls}, {"W41", "W42", "W43"})
        self.assertEqual(f.ledger.status()["open_reservations"], 0)
        before = inventory(f.root)
        verify_delivery(f.root, f.run_id)
        self.assertEqual(inventory(f.root), before)
        for request in f.backend.calls:
            outcome = f.runtime.execute(request, allow_test_doubles=True)
            self.assertTrue(outcome["replayed"])
            output = f.runtime.store.output_for_call(outcome["receipt"]["call_id"])
            self.assertEqual(output["document"]["role_id"], request.role_id)
            self.assertEqual(output["document"]["base_hash"], request.base_hash)
            self.assertEqual(output["document"]["prompt_version"], request.prompt_version)
        self.assertEqual(len(f.backend.calls), 3)

    def test_tradeoff_is_archived_with_verified_pareto_reference(self):
        f = self.evaluated(score_override={"clarity": 2})
        f.diagnose()
        self.assertEqual(f.decide()["action"], "ARCHIVE_PARETO")
        f.finalize()
        self.assertEqual(verify_delivery(f.root, f.run_id)["action"], "ARCHIVE_PARETO")
        self.assertFalse((f.root / "versions/champion/v0001").exists())

    def test_fresh_runs_reproduce_semantics_and_replay_exact_bytes(self):
        first = self.fixture()
        first.run()
        other = SyntheticCycle(Path(self.temp.name) / "independent")
        self.addCleanup(lambda: remove_fixture(other.root))
        other.run()
        a = verify_delivery(first.root, first.run_id)
        b = verify_delivery(other.root, other.run_id)
        for key in ("original_pdf", "proposal_ids", "action", "state", "system_path"):
            self.assertEqual(a[key], b[key])
        self.assertEqual(first.diagnosis["classification"], other.diagnosis["classification"])
        self.assertEqual((first.candidate_dir / "latex-source/paper.tex").read_bytes(), (other.candidate_dir / "latex-source/paper.tex").read_bytes())
        self.assertEqual(first.gate_report["overall_pass"], other.gate_report["overall_pass"])
        self.assertEqual(first.evaluation["overall_outcome"], other.evaluation["overall_outcome"])

    def test_corrupted_evaluation_blocks_diagnosis_and_decision(self):
        f = self.evaluated()
        path = f.root / f"state/evaluations/{f.run_id}/c0000/evaluation.json"
        path.chmod(0o644)
        path.write_bytes(path.read_bytes() + b"!")
        path.chmod(0o444)
        with self.assertRaises(DiagnosisError):
            f.diagnose()
        with self.assertRaises(PolicyError):
            f.decide()
        self.assertEqual(f.store.snapshot(f.run_id)["state"], "EVALUATED")

    def test_delivery_cli_verifies_in_an_independent_process(self):
        f = self.fixture()
        f.run()
        command = [sys.executable, str(ROOT / "scripts/m13_system_check.py"), "--verify-root", str(f.root), "--run-id", f.run_id]
        before = inventory(f.root)
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), verify_delivery(f.root, f.run_id))
        self.assertEqual(inventory(f.root), before)
        f.pdf.write_bytes(f.pdf.read_bytes() + b"!")
        failed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=60)
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(json.loads(failed.stderr)["status"], "fail")
        self.assertEqual(failed.stdout, "")

    def test_routed_artifact_tamper_and_missing_budget_fail_closed(self):
        f = self.fixture(routed=True)
        f.run()
        receipt = f.runtime.store.receipts()[0]
        output = f.root / receipt["output_locator"]
        raw, mode = output.read_bytes(), output.stat().st_mode
        output.chmod(0o644)
        output.write_bytes(raw + b"!")
        with self.assertRaises(DeliveryError):
            verify_delivery(f.root, f.run_id)
        output.write_bytes(raw)
        output.chmod(mode)
        ledger = f.ledger.ledger_path
        saved = ledger.read_bytes()
        ledger.unlink()
        with self.assertRaises(DeliveryError):
            verify_delivery(f.root, f.run_id)
        self.assertFalse(ledger.exists(), "audit must not create a replacement ledger")
        ledger.write_bytes(saved)
        verify_delivery(f.root, f.run_id)

    def test_router_rejects_producer_model_for_independent_jury(self):
        f = self.fixture(routed=True)
        f.candidate()
        current = json.loads((f.root / "workspaces" / f.run_id / "cycle-0000/W41/task.json").read_bytes())
        request = InferenceRequest.from_agent_task(f.root, current, prompt="synthetic independent jury routing check", required_capabilities=["language"], estimate_tokens=1, max_output_tokens=1, jury=True, producer_target="producer", producer_group="producer", producer_model="synthetic-producer", privacy_mode="deny_remote")
        self.assertEqual(ModelRouter(f.registry).route(request).model, "synthetic-judge")
        policy = fake_policy()
        policy["targets"]["judge"]["model"] = "synthetic-producer"
        with self.assertRaises(InferenceRoutingError):
            ModelRouter(ModelRegistry(policy)).route(request)

    def test_test_doubles_require_explicit_boolean_and_cannot_run_live(self):
        f = self.fixture(routed=True)
        f.candidate()
        f.gates()
        from article_loop.inference import InferenceError
        from article_loop.evaluation import FakeJurorAdapter
        for authorization in (False, "true", 1):
            with self.subTest(authorization=authorization):
                with self.assertRaises(EvaluationError):
                    evaluate_candidate(f.root, f.run_id, juror_adapters={"juror-math": FakeJurorAdapter(juror_id="juror-math")}, meta_adapter=FakeMetaReviewerAdapter(), allow_test_doubles=authorization)
        from dataclasses import replace
        request = replace(f.backend.calls[0], task_id="m13-live-rejection")
        with self.assertRaises(InferenceError):
            f.runtime.execute(request, live=True, allow_test_doubles=True)
        self.assertEqual(len(f.backend.calls), 3)


class M13ConfigurationTests(unittest.TestCase):
    def test_versioned_defaults_disable_all_model_execution(self):
        config = yaml.safe_load((ROOT / "config/budgets.yaml").read_text())
        self.assertIs(config["model_execution"]["enabled"], False)
        self.assertIs(config["model_execution"]["paid_apis_enabled"], False)
        self.assertIs(config["execution"]["enabled"], False)
        for key in ("enabled", "allow_local", "allow_remote", "allow_paid"):
            self.assertIs(config["inference"][key], False)
        self.assertEqual(config["inference"]["targets"], {})
        self.assertEqual(config["privacy"]["remote_content_mode"], "deny_remote")
        self.assertEqual(config["inference"]["independence"]["mode"], "model")

    def test_git_tracks_no_runtime_credentials_or_test_outputs(self):
        tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout.decode().split("\0")
        for name in filter(None, tracked):
            if name.startswith(("state/", "runtime/", "local-smoke/", "tmp/", "workspaces/", "artifacts/", "versions/", "reports/", "logs/")):
                self.assertEqual(Path(name).name, ".gitkeep", name)
            self.assertNotIn(Path(name).name, {".env", "auth.json", "credentials.json"})

    def test_verifier_invalid_inputs_do_not_create_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for run_id, cycle in (("../escape", 0), ("r", True), ("r", -1), ("r", 0)):
                with self.assertRaises(DeliveryError):
                    verify_delivery(root, run_id, cycle_id=cycle)
            self.assertEqual(list(root.iterdir()), [])

    def test_cli_preserves_existing_output_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "preserve.txt"
            marker.write_text("existing user data")
            result = subprocess.run([sys.executable, str(ROOT / "scripts/m13_system_check.py"), "--keep-workspace", temp], capture_output=True, text=True, check=False, timeout=30)
            self.assertEqual(result.returncode, 1)
            self.assertIn("existing output is preserved", result.stderr)
            self.assertEqual(marker.read_text(), "existing user data")


if __name__ == "__main__":
    unittest.main()
