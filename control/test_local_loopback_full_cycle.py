"""Offline acceptance tests for the restricted local full-cycle entry point."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4


REPOSITORY = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY / "scripts" / "local_loopback_full_cycle.py"
SPEC = importlib.util.spec_from_file_location("local_loopback_full_cycle", SCRIPT)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


class LocalLoopbackEntryTests(unittest.TestCase):
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

    def prepare(self):
        return runner.prepare(
            producer_model="producer-local",
            juror_model="juror-local",
            attempt_id="attempt-" + str(uuid4()),
        )

    def test_prepare_creates_isolated_loopback_only_configuration(self):
        plan = self.prepare()
        attempt = self.root / "runtime/local-full-cycle" / plan["attempt_id"]
        self.assertTrue((attempt / "run-plan.json").is_file())
        self.assertEqual(plan["execution"]["backend"], "local_openai_compatible")
        self.assertFalse(plan["execution"]["remote_allowed"])
        self.assertFalse(plan["execution"]["paid_allowed"])
        registry = runner.ModelRegistry.from_project(attempt)
        self.assertEqual(set(registry.targets), {"producer", "juror"})
        for target in registry.targets.values():
            self.assertTrue(target.local)
            self.assertFalse(target.paid)
            self.assertEqual(target.endpoint, runner.ENDPOINT)
            self.assertIsNone(target.api_key_env)
            self.assertIsNone(target.fallback_target)
        self.assertEqual(runner.ExecutionPolicy.from_project(attempt).departments, {item: "routed" for item in runner.DEPARTMENTS})

    def test_stop_blocks_prepare_before_writing_an_attempt(self):
        (self.root / "control/STOP").write_text("stop\n", encoding="utf-8")
        with self.assertRaises(runner.LocalCycleError):
            self.prepare()
        parent = self.root / "runtime/local-full-cycle"
        self.assertFalse(parent.exists() and any(parent.iterdir()))

    def test_one_model_is_rejected_before_writing_an_attempt(self):
        with self.assertRaises(runner.LocalCycleError):
            runner.prepare(producer_model="same", juror_model="same", attempt_id="attempt-" + str(uuid4()))

    def test_preflight_requires_both_declared_models_from_loopback_catalog(self):
        plan = self.prepare()
        with patch.object(runner, "_loopback_models", return_value=["producer-local"]):
            with self.assertRaises(runner.LocalCycleError):
                runner.preflight(plan["attempt_id"])
        with patch.object(runner, "_loopback_models", return_value=["producer-local", "juror-local"]):
            report = runner.preflight(plan["attempt_id"])
        self.assertTrue(report["local_only"])
        self.assertEqual(report["selected_models"], {"producer": "producer-local", "juror_meta": "juror-local"})

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
            run_id, runner.State.INGESTED, event_id=run_id + ":ingested",
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
