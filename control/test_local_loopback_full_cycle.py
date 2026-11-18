"""Offline acceptance tests for the restricted local full-cycle entry point."""
from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZipFile


REPOSITORY = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY / "scripts" / "local_loopback_full_cycle.py"
SPEC = importlib.util.spec_from_file_location("local_loopback_full_cycle", SCRIPT)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)

from article_loop.state_machine import State  # noqa: E402


class LocalLoopbackEntryTests(unittest.TestCase):
    def test_synthetic_article_source_matches_verifier_contract(self):
        from scripts.synthetic_article import BASE_SOURCE

        path = REPOSITORY / "control/fixtures/artigo-sintetico.tex"
        self.assertEqual(path.read_text(encoding="utf-8"), BASE_SOURCE)

    def test_synthetic_cycle_reaches_audited_completion_with_bounded_context(self):
        from article_loop.inference import InferenceResult
        from control.m13_fixture import remove_fixture, synthetic_pdf
        from control.test_m131_routed_evaluation import JudgmentBackend

        (self.root / "input/inbox/artigo.pdf").write_bytes(synthetic_pdf())
        with ZipFile(self.root / "input/inbox/source.zip", "x") as archive:
            archive.writestr("paper.tex", runner.BASE_SOURCE)
        plan = self.prepare(context_recovery=True)
        attempt = self.root / runner.RUNTIME_RELATIVE / plan["attempt_id"]
        self.addCleanup(remove_fixture, attempt)
        jury = JudgmentBackend()
        roles = []
        registry = runner.ModelRegistry.from_project(attempt)
        from article_loop.inference import ModelRouter
        router = ModelRouter(registry)

        def complete(request, target):
            from dataclasses import replace
            route = router.route(replace(request, estimate_tokens=20_000))
            expected_variant = "juror-32k" if request.actor_kind == "evaluator" else "producer-32k"
            self.assertEqual(route.target_id, expected_variant)
            if request.actor_kind == "evaluator":
                self.assertEqual(request.max_output_tokens, target.max_output_tokens)
                self.assertEqual(request.max_output_tokens, 4096)
                self.assertEqual(target.target_id, "juror")
                return jury.complete(request, target)
            role = request.role_id
            self.assertEqual(target.target_id, "producer")
            roles.append(role)
            self.assertNotIn("/snapshot.json", request.prompt)
            self.assertIn("latex-source/paper.tex", request.prompt)
            claim_id, = runner.Blackboard(attempt).claims(request.run_id)
            operation = {"op": "add", "target": f"evidence/{role.lower()}.txt", "value": "Proof reviewed.\n"}
            if role == "W11":
                operation = {"op": "replace", "target": "latex-source/paper.tex",
                             "value": runner.REVISED_SOURCE.removesuffix("\n")}
            payload = {
                "scope": [f"role:{role}"], "evidence_locators": ["page:1"],
                "patch_or_operations": {"kind": "operations", "operations": [operation]},
                "affected_claims": [claim_id] if role == "W22" else [], "dependencies": [],
                "risk": {"level": "low", "factors": [], "technical_effect_possible": False},
                "confidence": 1, "requested_validations": ["correctness_math"] if role == "W22" else [],
            }
            return InferenceResult(json.dumps(payload), 50, 10, 0, True, finish_reason="stop")

        deadline = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        with patch.object(runner, "_loopback_models", return_value=[
                 "producer-local", "juror-local", "producer-local:32k", "juror-local:32k"]), \
             patch.object(runner.LocalOpenAICompatibleBackend, "complete", side_effect=complete):
            outcome = runner.run(plan["attempt_id"], human_authorized=True, deadline=deadline,
                                 synthetic_article=True)
        self.assertEqual(outcome["status"], "complete", outcome.get("cause"))
        self.assertEqual(outcome["state"], "CYCLE_COMPLETE")
        self.assertEqual(roles, ["W11", "W22", "W31", "W41", "W51"])
        self.assertEqual(len(jury.calls), 7)
        self.assertEqual(outcome["audit"]["routed_inference"]["calls"], 12)

    def test_same_attempt_recovers_a_reconciled_m8_output_ceiling_failure(self):
        from article_loop.inference import InferenceResult
        from control.m13_fixture import remove_fixture, synthetic_pdf
        from control.test_m131_routed_evaluation import JudgmentBackend

        (self.root / "input/inbox/artigo.pdf").write_bytes(synthetic_pdf())
        with ZipFile(self.root / "input/inbox/source.zip", "x") as archive:
            archive.writestr("paper.tex", runner.BASE_SOURCE)
        plan = self.prepare(context_recovery=True)
        attempt = self.root / runner.RUNTIME_RELATIVE / plan["attempt_id"]
        self.addCleanup(remove_fixture, attempt)
        jury = JudgmentBackend()
        failed_once = {"value": False}

        def complete(request, target):
            if request.actor_kind == "evaluator":
                if not failed_once["value"]:
                    failed_once["value"] = True
                    return InferenceResult("not-json", 1737, 4096, 0, True,
                                           wall_time_seconds=1, finish_reason="length")
                return jury.complete(request, target)
            role = request.role_id
            claim_id, = runner.Blackboard(attempt).claims(request.run_id)
            operation = {"op": "add", "target": f"evidence/{role.lower()}.txt", "value": "Proof reviewed.\n"}
            if role == "W11":
                operation = {"op": "replace", "target": "latex-source/paper.tex",
                             "value": runner.REVISED_SOURCE.removesuffix("\n")}
            payload = {
                "scope": [f"role:{role}"], "evidence_locators": ["page:1"],
                "patch_or_operations": {"kind": "operations", "operations": [operation]},
                "affected_claims": [claim_id] if role == "W22" else [], "dependencies": [],
                "risk": {"level": "low", "factors": [], "technical_effect_possible": False},
                "confidence": 1, "requested_validations": ["correctness_math"] if role == "W22" else [],
            }
            return InferenceResult(json.dumps(payload), 50, 10, 0, True,
                                   wall_time_seconds=1, finish_reason="stop")

        deadline = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        models = ["producer-local", "juror-local", "producer-local:32k", "juror-local:32k"]
        with patch.object(runner, "_loopback_models", return_value=models), \
             patch.object(runner.LocalOpenAICompatibleBackend, "preflight", return_value={"ready": True}), \
             patch.object(runner.LocalOpenAICompatibleBackend, "complete", side_effect=complete):
            initial = runner.run(plan["attempt_id"], human_authorized=True, deadline=deadline,
                                 synthetic_article=True)
            self.assertEqual(initial["status"], "blocked")
            self.assertIn("juror adapter", initial["cause"])
            completed = runner.recover(plan["attempt_id"], human_authorized=True)

        self.assertEqual(completed["status"], "complete", completed.get("cause"))
        self.assertEqual(completed["state"], "CYCLE_COMPLETE")
        self.assertEqual((attempt / "run-plan.json").read_bytes(),
                         runner._canonical(plan) + b"\n")
        self.assertEqual(json.loads((attempt / "outcome.json").read_text())["status"], "blocked")
        state = runner.status(plan["attempt_id"])
        self.assertEqual(state["effective_outcome"]["status"], "complete")
        ledger = runner.BudgetLedger.from_project(
            attempt, initial["run_id"], profile=runner.PROFILE,
            deadline_at=deadline, clock=runner._RunClock(),
        )
        budget = ledger.status(read_only=True)
        self.assertEqual(budget["limits"]["max_calls"], 13)
        self.assertEqual(budget["calls"], 13)
        self.assertEqual(budget["limit_extensions"], 1)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        shutil.copytree(REPOSITORY / "config", self.root / "config")
        shutil.copytree(REPOSITORY / "prompts", self.root / "prompts")
        (self.root / "input/inbox").mkdir(parents=True)
        # This suite exercises preparation only; use a local non-article
        # regular file so the GitHub checkout never needs the ignored PDF.
        (self.root / "input/inbox/artigo.pdf").write_bytes(
            b"%PDF-1.4\n% local synthetic fixture\n%%EOF\n"
        )
        (self.root / "control").mkdir()
        self.root_patch = patch.object(runner, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.temp.cleanup)

    def prepare(self, *, context_recovery=False):
        kwargs = {}
        if context_recovery:
            kwargs = {
                "producer_context_32k": "producer-local:32k",
                "juror_context_32k": "juror-local:32k",
            }
        return runner.prepare(
            producer_model="producer-local",
            juror_model="juror-local",
            attempt_id="attempt-" + str(uuid4()),
            **kwargs,
        )

    def test_prepare_creates_isolated_loopback_only_configuration(self):
        plan = self.prepare(context_recovery=True)
        attempt = self.root / "runtime/local-full-cycle" / plan["attempt_id"]
        self.assertTrue((attempt / "run-plan.json").is_file())
        self.assertEqual(plan["limits"]["max_wall_seconds"], 3600)
        self.assertEqual(plan["execution"]["backend"], "local_openai_compatible")
        self.assertFalse(plan["execution"]["remote_allowed"])
        self.assertFalse(plan["execution"]["paid_allowed"])
        registry = runner.ModelRegistry.from_project(attempt)
        self.assertEqual(set(registry.targets), {"producer", "producer-32k", "juror", "juror-32k"})
        self.assertEqual(registry.target("producer").max_output_tokens, 2048)
        self.assertEqual(registry.target("juror").max_output_tokens, 4096)
        self.assertEqual(registry.target("producer-32k").context_limit, 32768)
        self.assertEqual(registry.target("juror-32k").context_limit, 32768)
        self.assertEqual(registry.role_routes["W11"]["targets"], ("producer", "producer-32k"))
        self.assertEqual(registry.role_routes["M00"]["targets"], ("juror", "juror-32k"))
        for target in registry.targets.values():
            self.assertTrue(target.local)
            self.assertFalse(target.paid)
            self.assertEqual(target.endpoint, runner.ENDPOINT)
            self.assertIsNone(target.api_key_env)
            self.assertIsNone(target.fallback_target)
        self.assertEqual(runner.ExecutionPolicy.from_project(attempt).departments, {item: "routed" for item in runner.DEPARTMENTS})

    def test_prepare_copies_and_binds_optional_source_zip(self):
        source = self.root / "input/inbox/source.zip"
        source.write_bytes(b"synthetic source bytes")
        plan = self.prepare()
        attempt = self.root / "runtime/local-full-cycle" / plan["attempt_id"]
        self.assertEqual((attempt / "input/inbox/source.zip").read_bytes(), source.read_bytes())
        self.assertEqual(plan["source_zip"]["sha256"], runner._hash_bytes(source.read_bytes()))

    def test_stop_blocks_prepare_before_writing_an_attempt(self):
        (self.root / "control/STOP").write_text("stop\n", encoding="utf-8")
        with self.assertRaises(runner.LocalCycleError):
            self.prepare()
        parent = self.root / "runtime/local-full-cycle"
        self.assertFalse(parent.exists() and any(parent.iterdir()))

    def test_one_model_is_rejected_before_writing_an_attempt(self):
        with self.assertRaises(runner.LocalCycleError):
            runner.prepare(producer_model="same", juror_model="same", attempt_id="attempt-" + str(uuid4()))

    def test_run_requires_current_authorization_and_future_deadline(self):
        plan = self.prepare()
        attempt_id = plan["attempt_id"]
        with patch.object(runner, "preflight", side_effect=AssertionError("preflight called")):
            for authorized, deadline in ((False, "2099-01-01T00:00:00Z"),
                                         (True, None), (True, "2000-01-01T00:00:00Z")):
                with self.subTest(authorized=authorized, deadline=deadline):
                    with self.assertRaises(runner.LocalCycleError):
                        runner.run(attempt_id, human_authorized=authorized, deadline=deadline)

    def test_structured_admission_counts_body_and_rejects_overflow(self):
        @dataclass(frozen=True)
        class Request:
            requested_output_schema: str = "agent-proposal.schema.json"
            prompt: str = "prompt"
            max_output_tokens: int = 2048
            estimate_tokens: int = 1

        target = SimpleNamespace(endpoint="http://127.0.0.1:11434/v1/chat/completions",
                                 model="local", max_output_tokens=2048, context_limit=8192)
        fallback = SimpleNamespace(endpoint=target.endpoint, model="local:32k",
                                    max_output_tokens=2048, context_limit=32768)
        with patch.object(runner, "model_output_schema", return_value={}), \
             patch.object(runner, "build_openai_structured_request", return_value=SimpleNamespace(body_bytes=b"x" * 8000)):
            admitted = runner._admit_structured_request(self.root, Request(), target)
            self.assertEqual(admitted.estimate_tokens, 4512)
            target.context_limit = 6000
            admitted = runner._admit_structured_request(self.root, Request(), target, (fallback,))
            self.assertEqual(admitted.estimate_tokens, 4512)
            with self.assertRaisesRegex(runner.LocalCycleError, "exceeds preauthorized context variants"):
                runner._admit_structured_request(self.root, Request(), target)

    def test_preflight_requires_both_declared_models_from_loopback_catalog(self):
        plan = self.prepare()
        with patch.object(runner, "_loopback_models", return_value=["producer-local"]):
            with self.assertRaises(runner.LocalCycleError):
                runner.preflight(plan["attempt_id"])
        with patch.object(runner, "_loopback_models", return_value=["producer-local", "juror-local"]):
            report = runner.preflight(plan["attempt_id"])
        self.assertTrue(report["local_only"])
        self.assertEqual(report["selected_models"], {"producer": "producer-local", "juror_meta": "juror-local"})

    def test_catalog_ignores_unusable_names_without_blocking_valid_models(self):
        body = json.dumps({"data": [{"id": "local:2b"}, {"id": "owner/other:3b"}]}).encode()
        response = SimpleNamespace(status=200, read=lambda limit: body)
        connection = SimpleNamespace(request=lambda *args: None, getresponse=lambda: response, close=lambda: None)
        with patch.object(runner.http.client, "HTTPConnection", return_value=connection):
            self.assertEqual(runner._loopback_models(), ["local:2b"])

    def test_activation_uses_bootstrap_base_hash(self):
        from control.m13_fixture import SyntheticCycle, remove_fixture

        root = Path(self.temp.name) / "cycle"
        fixture = SyntheticCycle(root)
        self.addCleanup(lambda: remove_fixture(root) if root.exists() else None)
        board = root / "state/blackboard" / fixture.run_id
        for name in ("activation_map.json", "activation-c0000.json"):
            (board / name).unlink()
        with self.assertRaisesRegex(runner.LocalCycleError, "no canonical base hash"):
            runner._persist_activation(root, fixture.run_id, None, synthetic_article=True)
        result = runner._persist_activation(root, fixture.run_id, fixture.base_hash, synthetic_article=True)
        self.assertFalse(result["paused"])
        active = {entry["role_id"] for entry in result["roles"] if entry["mode"] != "FREEZE"}
        self.assertIn("W22", active)

    def test_preflight_rejects_changed_input_before_contacting_service(self):
        plan = self.prepare()
        attempt = self.root / "runtime/local-full-cycle" / plan["attempt_id"]
        (attempt / "input/inbox/artigo.pdf").write_bytes(b"changed")
        with patch.object(runner, "_loopback_models", side_effect=AssertionError("contacted service")):
            with self.assertRaisesRegex(runner.LocalCycleError, "input differs"):
                runner.preflight(plan["attempt_id"])

    def test_status_does_not_mutate_or_resume_a_prepared_attempt(self):
        plan = self.prepare()
        attempt = self.root / "runtime/local-full-cycle" / plan["attempt_id"]
        before = (attempt / "run-plan.json").read_bytes()
        result = runner.status(plan["attempt_id"])
        self.assertEqual(result["plan"], json.loads(before))
        self.assertEqual((attempt / "run-plan.json").read_bytes(), before)

    def test_status_reports_journal_run_id_when_historical_outcome_is_null(self):
        plan = self.prepare()
        attempt = self.root / "runtime/local-full-cycle" / plan["attempt_id"]
        run_id = "ingest-" + "a" * 64
        store = runner.DurableStore(attempt)
        store.create_run(run_id, actor_id="m3")
        store.record(
            run_id, State.INGESTED, event_id=run_id + ":ingested",
            idempotency_key=run_id + ":ingested", actor_id="m3",
            payload={"source_identity": {"input_sha256": "a" * 64}},
        )
        (attempt / "outcome.json").write_text(json.dumps({"run_id": None}), encoding="utf-8")
        result = runner.status(plan["attempt_id"])
        self.assertEqual(run_id, result["canonical_run_id"])
        self.assertEqual([run_id], result["canonical_run_ids"])
        self.assertIsNone(result["outcome"]["run_id"])


if __name__ == "__main__":
    unittest.main()
