"""Offline acceptance tests for the loopback-only M14 Control Center."""
from __future__ import annotations

import copy
import http.client
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))

from article_loop.budget import BudgetLedger, BudgetLimits
from article_loop.control_center import (
    ControlCenterError,
    ControlPlane,
    LocalControlHTTPServer,
)
from article_loop.state_machine import State
from article_loop.store import DurableStore


class ControlCenterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "project"
        self.root.mkdir()
        shutil.copytree(ROOT / "config", self.root / "config")
        for relative in ("state/events", "state/snapshots", "state/checkpoints", "state/locks", "logs"):
            (self.root / relative).mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def make_run(self, run_id="run-1", artifact_hashes=None):
        store = DurableStore(self.root)
        store.create_run(run_id)
        store.record(
            run_id, State.INGESTED, event_id=f"{run_id}:ingested",
            idempotency_key=f"{run_id}:ingested", actor_id="test", event_type="TEST_INGESTED",
            artifact_hashes=artifact_hashes,
        )
        return run_id

    def test_status_without_run_is_read_only(self):
        before = sorted(
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*") if path.is_file()
        )
        plane = ControlPlane(self.root)
        self.assertEqual(plane.runs()["runs"], [])
        self.assertEqual(plane.system_status()["active_runs"], [])
        self.assertEqual(
            sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*") if path.is_file()),
            before,
        )
        self.assertFalse((self.root / "state/control-center").exists())

    def test_run_projection_rebuilds_after_control_plane_restart(self):
        run_id = self.make_run()
        first = ControlPlane(self.root).runs()["runs"][0]
        second = ControlPlane(self.root).runs()["runs"][0]
        self.assertEqual(first["run_id"], run_id)
        self.assertEqual(first["version_hash"], second["version_hash"])
        self.assertEqual(first["state"], State.INGESTED.value)

    def test_event_cursor_backfills_and_deduplicates(self):
        run_id = self.make_run()
        plane = ControlPlane(self.root)
        first = plane.events(limit=1)
        self.assertEqual(len(first["events"]), 1)
        second = plane.events(cursor=first["next_cursor"], limit=10)
        self.assertEqual(len(second["events"]), 1)
        final = plane.events(cursor=second["next_cursor"], limit=10)
        self.assertEqual(final["events"], [])
        with self.assertRaises(ControlCenterError):
            plane.events(cursor="lost-cursor")
        self.assertEqual(first["events"][0]["source"], f"run:{run_id}")

    def test_sse_serves_confirmed_event_with_resumable_cursor(self):
        self.make_run()
        server = LocalControlHTTPServer(self.root, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = None
        try:
            port = server.server_address[1]
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
            connection.request("GET", "/api/v1/events/stream", headers={"Host": f"127.0.0.1:{port}"})
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.getheader("Content-Type"), "text/event-stream; charset=utf-8")
            lines = [response.fp.readline().decode("utf-8").strip() for _ in range(3)]
            self.assertTrue(lines[0].startswith("id: v1."))
            self.assertEqual(lines[1], "event: durable")
            self.assertIn('"source":"run:run-1"', lines[2])
        finally:
            if connection is not None:
                connection.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_evidence_projection_is_empty_without_published_stage_artifacts(self):
        run_id = self.make_run()
        evidence = ControlPlane(self.root).evidence(run_id)
        self.assertEqual(evidence["gates"], [])
        self.assertEqual(evidence["jury"]["status"], "not_started")

    def test_artifact_links_are_journal_allowlisted_metadata_only(self):
        digest = "a" * 64
        run_id = self.make_run(artifact_hashes=[digest])
        plane = ControlPlane(self.root)
        listed = plane.artifacts(run_id)
        self.assertEqual(listed["artifacts"][0]["href"], f"/api/v1/runs/{run_id}/artifacts/{digest}")
        self.assertEqual(plane.artifact_metadata(run_id, digest)["content_available"], False)
        with self.assertRaises(ControlCenterError):
            plane.artifact_metadata(run_id, "b" * 64)

    def test_run_pagination_has_bounded_cursor(self):
        for number in range(3):
            self.make_run(f"run-{number}")
        plane = ControlPlane(self.root)
        page = plane.runs(limit=2)
        self.assertEqual(len(page["runs"]), 2)
        self.assertEqual(len(plane.runs(cursor=page["next_cursor"], limit=2)["runs"]), 1)

    def test_mutation_replay_is_idempotent_and_audited(self):
        plane = ControlPlane(self.root)
        calls = []
        payload = {"confirmed": True, "expected_hash": "a" * 64}
        operation = lambda: (calls.append("called") or {"snapshot_hash": "b" * 64})
        first = plane._mutate(
            action="test_action", idempotency_key="same-key", request=payload,
            expected_hash="a" * 64, before_hash="a" * 64, run_id=None, draft_id=None,
            operation=operation,
        )
        second = plane._mutate(
            action="test_action", idempotency_key="same-key", request=payload,
            expected_hash="a" * 64, before_hash="a" * 64, run_id=None, draft_id=None,
            operation=operation,
        )
        self.assertEqual(calls, ["called"])
        self.assertEqual(first, second)
        self.assertEqual([item["outcome"] for item in plane.audit.read_events()], ["PREPARED", "APPLIED"])

    def test_concurrent_same_idempotency_key_invokes_operation_once(self):
        plane = ControlPlane(self.root)
        barrier = threading.Barrier(2)
        calls = []
        results = []
        errors = []

        def operation():
            calls.append("called")
            time.sleep(0.05)
            return {"snapshot_hash": "b" * 64}

        def invoke():
            try:
                barrier.wait(timeout=2)
                results.append(plane._mutate(
                    action="concurrent_action", idempotency_key="shared-key",
                    request={"confirmed": True, "expected_hash": "a" * 64},
                    expected_hash="a" * 64, before_hash="a" * 64,
                    run_id=None, draft_id=None, operation=operation,
                ))
            except Exception as error:  # test harness preserves failures from either worker
                errors.append(error)

        threads = [threading.Thread(target=invoke) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=3)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertEqual(calls, ["called"])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], results[1])
        self.assertEqual([item["outcome"] for item in plane.audit.read_events()], ["PREPARED", "APPLIED"])

    def test_stale_run_hash_fails_before_canonical_operation(self):
        run_id = self.make_run()
        plane = ControlPlane(self.root)
        with self.assertRaises(ControlCenterError) as raised:
            plane.run_action(run_id, "pause", {"confirmed": True, "expected_hash": "0" * 64}, "stale")
        self.assertEqual(raised.exception.code, "STALE_VERSION")
        self.assertFalse((self.root / "state/control-center").exists())

    def test_controls_delegate_only_to_canonical_public_operations(self):
        run_id = self.make_run()
        plane = ControlPlane(self.root)
        version = plane.runs()["runs"][0]["version_hash"]

        class FakeOrchestrator:
            calls = []

            def __init__(self, root):
                self.root = root

            async def checkpoint(self, observed_run, **kwargs):
                self.calls.append(("checkpoint", observed_run))
                return {"snapshot_hash": "c" * 64, "run_id": observed_run}

            async def pause(self, observed_run, **kwargs):
                self.calls.append(("pause", observed_run))
                return {"snapshot_hash": "c" * 64, "run_id": observed_run}

            async def resume(self, observed_run, **kwargs):
                self.calls.append(("resume", observed_run))
                return {"snapshot_hash": "c" * 64, "run_id": observed_run}

            async def stop(self, observed_run, **kwargs):
                self.calls.append(("stop", observed_run))
                return {"snapshot_hash": "c" * 64, "run_id": observed_run}

        detail = {"run_id": run_id, "version_hash": version, "cycle_id": 0, "orchestration": {"snapshot_hash": version}}
        with patch("article_loop.control_center.run_detail", return_value=detail), patch("article_loop.control_center.Orchestrator", FakeOrchestrator), patch(
            "article_loop.control_center.finalize_decision",
            return_value={"snapshot_hash": "c" * 64, "run_id": run_id},
        ) as finalizer:
            for action in ("checkpoint", "pause", "resume", "stop", "finalize"):
                result = plane.run_action(run_id, action, {"confirmed": True, "expected_hash": version}, f"{action}-key")
                self.assertTrue(result["ok"])
                self.assertEqual(result["result"]["run_id"], run_id)
        self.assertEqual(FakeOrchestrator.calls, [(action, run_id) for action in ("checkpoint", "pause", "resume", "stop")])
        finalizer.assert_called_once_with(plane.root, run_id, cycle_id=0)

    def test_active_run_blocks_configuration_application(self):
        self.make_run()
        plane = ControlPlane(self.root)
        current = next(item for item in plane.config.list() if item["path"] == "config/budgets.yaml")
        value = copy.deepcopy(current["value"])
        value["local_execution"]["max_gate_output_bytes"] += 1
        draft = plane.config.create_draft({"config_path": current["path"], "base_hash": current["hash"], "value": value})
        plane.config.validate_draft(draft["draft_id"])
        with self.assertRaises(ControlCenterError) as raised:
            plane.config.apply_draft(draft["draft_id"])
        self.assertEqual(raised.exception.code, "ACTIVE_RUN_CONFIG_LOCK")

    def test_concurrent_configuration_application_allows_one_base_hash_winner(self):
        plane = ControlPlane(self.root)
        current = next(item for item in plane.config.list() if item["path"] == "config/budgets.yaml")

        def validated_draft(increment):
            value = copy.deepcopy(current["value"])
            value["local_execution"]["max_gate_output_bytes"] += increment
            draft = plane.config.create_draft({"config_path": current["path"], "base_hash": current["hash"], "value": value})
            return plane.config.validate_draft(draft["draft_id"])

        drafts = [validated_draft(1), validated_draft(2)]
        barrier = threading.Barrier(2)
        applied = []
        errors = []

        def apply(draft):
            try:
                barrier.wait(timeout=2)
                applied.append(plane.config.apply_draft(draft["draft_id"]))
            except Exception as error:  # test harness preserves failures from either worker
                errors.append(error)

        threads = [threading.Thread(target=apply, args=(draft,)) for draft in drafts]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=3)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(len(applied), 1)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], ControlCenterError)
        self.assertEqual(errors[0].code, "STALE_VERSION")
        self.assertEqual(plane.config._load(current["path"])[1], applied[0]["applied_hash"])

    def test_configuration_rejects_unknown_fields_and_non_strict_boolean(self):
        plane = ControlPlane(self.root)
        current = next(item for item in plane.config.list() if item["path"] == "config/budgets.yaml")
        unknown = copy.deepcopy(current["value"])
        unknown["unexpected"] = True
        with self.assertRaises(ControlCenterError):
            plane.config.validate(current["path"], unknown)
        wrong_boolean = copy.deepcopy(current["value"])
        wrong_boolean["execution"]["enabled"] = 1
        with self.assertRaises(ControlCenterError):
            plane.config.validate(current["path"], wrong_boolean)

    def test_read_only_budget_status_keeps_uncertain_separate_without_writes(self):
        ledger = BudgetLedger(self.root, "budget-run", limits=BudgetLimits(total_tokens=10), currency="USD")
        reservation = ledger.reserve("call-1", 5)
        ledger.admit(reservation["reservation_id"], "receipt-1")
        ledger.mark_uncertain(reservation["reservation_id"], "usage_unavailable", receipt_id="receipt-1")
        before = sorted(path.relative_to(self.root) for path in self.root.rglob("*") if path.is_file())
        observed = BudgetLedger(self.root, "budget-run", limits=BudgetLimits(total_tokens=10), currency="USD", read_only=True).status(read_only=True)
        after = sorted(path.relative_to(self.root) for path in self.root.rglob("*") if path.is_file())
        self.assertEqual(observed["assurance"], "uncertain")
        self.assertEqual(observed["usage"]["confirmed_cost_microunits"], 0)
        self.assertEqual(before, after)

    def test_unsafe_path_and_symlinked_runtime_are_rejected(self):
        plane = ControlPlane(self.root)
        with self.assertRaises(ControlCenterError):
            plane.config._path("config/../budgets.yaml")
        target = self.root / "state/events/elsewhere.jsonl"
        target.symlink_to(self.root / "config/system.yaml")
        with self.assertRaises(ControlCenterError):
            plane.runs()

    def test_redaction_never_returns_secret_like_values(self):
        from article_loop.control_center import _redact

        projected = _redact({"api_key": "do-not-return", "nested": {"cookie": "also-hidden"}})
        self.assertNotIn("do-not-return", json.dumps(projected))
        self.assertNotIn("also-hidden", json.dumps(projected))

    def test_production_control_rejects_adapter_and_test_double_payload(self):
        run_id = self.make_run()
        plane = ControlPlane(self.root)
        version = plane.runs()["runs"][0]["version_hash"]
        with self.assertRaises(ControlCenterError):
            plane.run_action(
                run_id, "pause",
                {"confirmed": True, "expected_hash": version, "adapter": "fake"},
                "fake-adapter",
            )

    def test_loopback_server_rejects_remote_bind_and_bad_host_origin(self):
        with self.assertRaises(ControlCenterError):
            LocalControlHTTPServer(self.root, host="0.0.0.0", port=0)
        server = LocalControlHTTPServer(self.root, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
            connection.request("GET", "/api/v1/health", headers={"Host": "example.invalid"})
            response = connection.getresponse()
            self.assertEqual(response.status, 403)
            response.read()
            connection.close()
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
            connection.request(
                "POST", "/api/v1/preflight",
                body=json.dumps({"confirmed": True, "expected_hash": "a" * 64}),
                headers={"Host": f"127.0.0.1:{port}", "Origin": "http://example.invalid", "Content-Type": "application/json", "Idempotency-Key": "bad-origin"},
            )
            response = connection.getresponse()
            self.assertEqual(response.status, 403)
            response.read()
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_static_interface_is_local_and_has_no_cdn(self):
        server = LocalControlHTTPServer(self.root, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
            connection.request("GET", "/", headers={"Host": f"127.0.0.1:{port}"})
            response = connection.getresponse()
            body = response.read().decode()
            self.assertEqual(response.status, 200)
            self.assertNotIn("https://", body)
            self.assertIn("Central de Controle", body)
            self.assertIn("file://", body)
            connection.close()
            for path, expected_type, marker in (
                ("/assets/styles.css", "text/css", ":root"),
                ("/assets/app.js", "javascript", "EventSource"),
            ):
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                connection.request("GET", path, headers={"Host": f"127.0.0.1:{port}"})
                response = connection.getresponse()
                asset = response.read().decode("utf-8")
                self.assertEqual(response.status, 200)
                self.assertIn(expected_type, response.getheader("Content-Type"))
                self.assertIn(marker, asset)
                self.assertNotRegex(asset, r"https?://")
                connection.close()
            script = (ROOT / ".prime/agent/skills/article-loop/src/article_loop/control_center_static/app.js").read_text(encoding="utf-8")
            self.assertIn("EventSource", script)
            self.assertIn("Reconectando", script)
            self.assertIn("polling local ativo", script)
            self.assertIn("target[name] = defaultFor(schema);", script)
            self.assertNotIn("target[name] = defaultFor(schema?.additionalProperties);", script)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_launcher_is_limited_to_the_canonical_loopback_server(self):
        launcher = ROOT / "bin/start-control-center.sh"
        source = launcher.read_text(encoding="utf-8")
        self.assertIn("exec python3 -m article_loop.control_center", source)
        self.assertIn("--host 127.0.0.1", source)
        self.assertIn('export PYTHONPATH="$ROOT/.prime/agent/skills/article-loop/src"', source)
        for forbidden in ("prime-agent", "ollama", "run_cycle", "bootstrap", "curl", "wget"):
            self.assertNotIn(forbidden, source)
        with tempfile.TemporaryDirectory() as outside:
            result = subprocess.run(
                ["bash", str(launcher), "--port", "8766"], cwd=outside, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("valid article-loop project root", result.stderr)
        invalid_port = subprocess.run(
            ["bash", str(launcher), "--port", "0"], cwd=ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(invalid_port.returncode, 2)
        self.assertIn("1024 to 65535", invalid_port.stderr)
