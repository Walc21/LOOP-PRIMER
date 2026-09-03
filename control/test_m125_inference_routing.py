"""Offline acceptance and adversarial tests for M12.5 inference routing."""

from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import threading
import time
import unittest
import urllib.error


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime/agent/skills/article-loop/src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop.budget import (  # noqa: E402
    BudgetAuthorizationError,
    BudgetError,
    BudgetIntegrityError,
    BudgetLedger,
    BudgetLimits,
    ManualClock,
    RunAuthorization,
    load_budget_config,
)
from article_loop.inference import (  # noqa: E402
    InferenceBackendError,
    InferenceConfigError,
    InferenceIntegrityError,
    InferenceOutputError,
    InferenceRequest,
    InferenceResult,
    InferenceRoutingError,
    InferenceRuntime,
    InferenceStore,
    ModelRegistry,
    ModelRouter,
    PRIME_PER_CHILD_MODEL_SELECTION,
)
from article_loop.inference_backends import (  # noqa: E402
    FakeInferenceBackend,
    LocalOpenAICompatibleBackend,
)


def target(
    target_id: str, *, backend_type: str = "fake", local: bool = True,
    paid: bool = False, tier: str = "mid", group: str | None = None,
    endpoint: str | None = None, enabled: bool = True,
    fallback_target: str | None = None,
) -> dict:
    return {
        "target_id": target_id,
        "provider": "provider-" + target_id,
        "model": "model-" + target_id,
        "backend_type": backend_type,
        "enabled": enabled,
        "local": local,
        "paid": paid,
        "tier": tier,
        "capabilities": ["language", "structured_output", "math_high_assurance"],
        "context_limit": 8192,
        "max_output_tokens": 2048,
        "independence_group": group or "group-" + target_id,
        "endpoint": endpoint,
        "api_key_env": None,
        "timeout_seconds": 1,
        "fallback_target": fallback_target,
    }


def policy(*targets: dict, enabled: bool = True, allow_local: bool = True) -> dict:
    values = {item["target_id"]: item for item in targets}
    return {
        "schema_version": "1.0.0",
        "enabled": enabled,
        "allow_local": allow_local,
        "allow_remote": False,
        "allow_paid": False,
        "routing_mode": "deterministic",
        "targets": values,
        "role_routes": {
            "W41": {
                "targets": list(values),
                "required_capabilities": ["language", "structured_output"],
            }
        } if values else {},
        "escalation": {"enabled": True, "max_route_attempts": 2},
        "independence": {"jury_must_differ_from_producer_group": True},
    }


def proposal() -> dict:
    return {
        "schema_version": "1.1.0", "proposal_id": "p-W41", "role_id": "W41",
        "cycle_id": 0, "base_hash": "a" * 64, "scope": ["language"],
        "evidence_locators": ["page:1"],
        "patch_or_operations": {"kind": "operations", "operations": [{"op": "annotate", "target": "text", "value": "note"}]},
        "affected_claims": [], "dependencies": [],
        "risk": {"level": "low", "factors": [], "technical_effect_possible": False},
        "confidence": 1, "requested_validations": [], "prompt_version": "test",
    }


class M125Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "config/schemas").mkdir(parents=True)
        (self.root / "control").mkdir()
        for name in ("agent-task.schema.json", "agent-proposal.schema.json", "inference-receipt.schema.json"):
            shutil.copy(ROOT / "config/schemas" / name, self.root / "config/schemas" / name)
        self.clock = ManualClock(current=datetime(2026, 1, 1, tzinfo=timezone.utc))

    def tearDown(self):
        self.temp.cleanup()

    def task(self, mode: str = "RUN") -> dict:
        return {
            "schema_version": "1.1.0", "task_id": "run-1-W41-c0000",
            "run_id": "run-1", "cycle_id": 0, "role_id": "W41",
            "activation_mode": mode, "created_at": "2026-01-01T00:00:00Z",
            "base_hash": "a" * 64, "scope": ["language"],
            "input_locators": ["readonly:fixture"],
            "requested_output_schema": "agent-proposal.schema.json",
            "prompt_version": "test", "constraints": ["receipt_only"],
        }

    def request(self, mode: str = "RUN", **kwargs) -> InferenceRequest:
        return InferenceRequest.from_agent_task(
            self.root, self.task(mode), prompt="review the bounded fixture",
            required_capabilities=["language", "structured_output"],
            estimate_tokens=20, max_output_tokens=100, **kwargs,
        )

    def ledger(self, route_policy: dict, **kwargs) -> BudgetLedger:
        return BudgetLedger(
            self.root, "run-1",
            limits=BudgetLimits(total_tokens=200, per_model_tokens=100, max_calls=5, max_retries=2, max_wall_time_seconds=10),
            clock=self.clock, inference_policy=route_policy, **kwargs,
        )

    def runtime(self, route_policy: dict, backend, **kwargs) -> InferenceRuntime:
        registry = ModelRegistry(route_policy)
        ledger = self.ledger(route_policy)
        return InferenceRuntime(self.root, ledger, registry, {next(iter(registry.targets.values())).backend_type: backend}, clock=self.clock, **kwargs)


class M125ConfigurationAndRoutingTests(M125Base):
    def test_project_defaults_are_fail_closed(self):
        registry = ModelRegistry.from_project(ROOT)
        status = registry.status()
        self.assertFalse(status["enabled"])
        self.assertEqual(status["enabled_targets"], [])
        self.assertFalse(status["paid_runtime_ready"])
        self.assertEqual(status["prime_child_model_routing"], "unsupported_verified")

    def test_disabled_inference_never_calls_backend(self):
        route_policy = policy(enabled=False)
        backend = FakeInferenceBackend()
        runtime = InferenceRuntime(self.root, self.ledger(route_policy), ModelRegistry(route_policy), {"fake": backend}, clock=self.clock)
        with self.assertRaises(Exception):
            runtime.execute(self.request(), allow_test_doubles=True)
        self.assertEqual(backend.calls, [])

    def test_unknown_target_role_duplicate_and_fallback_cycle_are_rejected(self):
        one = target("one")
        bad_target = policy(one)
        bad_target["role_routes"]["W41"]["targets"] = ["missing"]
        with self.assertRaises(InferenceConfigError):
            ModelRegistry(bad_target)
        bad_role = policy(one)
        bad_role["role_routes"]["UNKNOWN"] = bad_role["role_routes"].pop("W41")
        with self.assertRaises(InferenceConfigError):
            ModelRegistry(bad_role)
        duplicate = policy(one)
        duplicate["targets"] = [one, dict(one)]
        with self.assertRaises(InferenceConfigError):
            ModelRegistry(duplicate)
        a = target("a", fallback_target="b")
        b = target("b", fallback_target="a")
        with self.assertRaises(InferenceConfigError):
            ModelRegistry(policy(a, b))

    def test_duplicate_target_key_in_yaml_is_rejected_before_routing(self):
        (self.root / "config/budgets.yaml").write_text(
            "inference:\n  targets:\n    same: {}\n    same: {}\n",
            encoding="utf-8",
        )
        with self.assertRaises(BudgetError):
            load_budget_config(self.root)

    def test_secret_literal_remote_http_and_unapproved_local_are_rejected(self):
        secret = target("secret")
        secret["api_key_env"] = "sk-literal"
        with self.assertRaises(InferenceConfigError):
            ModelRegistry(policy(secret))
        remote = target("remote", backend_type="remote_openai_compatible", local=False, endpoint="http://example.invalid/v1/chat/completions")
        remote_policy = policy(remote, allow_local=False)
        remote_policy["allow_remote"] = True
        with self.assertRaises(InferenceConfigError):
            ModelRegistry(remote_policy)
        with self.assertRaises(InferenceConfigError):
            ModelRegistry(policy(target("local"), allow_local=False))

    def test_loopback_local_requires_explicit_enablement_and_paid_stays_closed(self):
        local = target("local", backend_type="local_openai_compatible", endpoint="http://127.0.0.1:9999/v1/chat/completions")
        self.assertEqual(ModelRegistry(policy(local)).status()["enabled_targets"], ["local"])
        paid = target("paid", paid=True)
        with self.assertRaises(InferenceConfigError):
            ModelRegistry(policy(paid))

    def test_route_and_hash_are_deterministic_and_policy_target_changes_matter(self):
        first_policy = policy(target("small"), target("large"))
        registry = ModelRegistry(first_policy)
        request = self.request()
        one = ModelRouter(registry).route(request)
        two = ModelRouter(registry).route(request)
        self.assertEqual(one.decision_hash, two.decision_hash)
        self.clock.advance(seconds=10)
        store = InferenceStore(self.root, "run-1", clock=self.clock)
        persisted_one = store.persist_route(one)
        self.clock.advance(seconds=10)
        persisted_two = store.persist_route(two)
        self.assertEqual(persisted_one, persisted_two)
        changed = policy(target("other"))
        changed_decision = ModelRouter(ModelRegistry(changed)).route(request)
        self.assertNotEqual(registry.policy_hash, ModelRegistry(changed).policy_hash)
        self.assertNotEqual(one.decision_hash, changed_decision.decision_hash)

    def test_freeze_selects_nothing(self):
        registry = ModelRegistry(policy(target("small")))
        decision = ModelRouter(registry).route(self.request("FREEZE"))
        self.assertEqual(decision.reason_code, "NO_INFERENCE_REQUIRED")
        self.assertIsNone(decision.target_id)

    def test_prompt_larger_than_target_bound_has_no_route(self):
        registry = ModelRegistry(policy(target("bounded")))
        oversized = InferenceRequest.from_agent_task(
            self.root, self.task(), prompt="x" * 140_000,
            required_capabilities=["language", "structured_output"],
            estimate_tokens=20, max_output_tokens=100,
        )
        with self.assertRaises(InferenceRoutingError):
            ModelRouter(registry).route(oversized)

    def test_escalation_is_closed_bounded_and_not_self_confidence_driven(self):
        registry = ModelRegistry(policy(target("small"), target("large", tier="high_assurance")))
        router = ModelRouter(registry)
        first = router.route(self.request())
        second_request = self.request().escalated(first.decision_hash, "DETERMINISTIC_GATE_FAILED")
        second = router.route(second_request)
        self.assertEqual((first.target_id, second.target_id), ("small", "large"))
        with self.assertRaises(Exception):
            self.request().escalated(first.decision_hash, "SELF_CONFIDENCE_LOW")
        third = second_request.escalated(second.decision_hash, "BACKEND_FAILURE")
        with self.assertRaises(Exception):
            router.route(third)

    def test_jury_independence_is_enforced(self):
        same = target("same", group="producer-group")
        independent = target("independent", group="jury-group")
        request = self.request(jury=True, producer_target="producer", producer_group="producer-group")
        decision = ModelRouter(ModelRegistry(policy(same, independent))).route(request)
        self.assertEqual(decision.target_id, "independent")
        with self.assertRaises(Exception):
            ModelRouter(ModelRegistry(policy(same))).route(request)


class M125BudgetCompatibilityTests(M125Base):
    def test_legacy_authorization_public_shape_and_admission_remain_unchanged(self):
        route_policy = policy(target("legacy"))
        ledger = self.ledger(route_policy, config_hash="b" * 64, profile="calibration", live_enabled=True)
        authorization = RunAuthorization.from_mapping({
            "run_id": "run-1", "profile": "calibration", "config_hash": "b" * 64,
            "provider": "provider-legacy", "model": "model-legacy", "token_limit": 50,
            "approved_at": self.clock.now_utc(), "approval_reference": "approval-legacy",
        })
        self.assertNotIn("routing_policy_hash", authorization.public())
        ledger.authorize(authorization)
        self.assertEqual(ledger.reserve("legacy-call", 10, role_id="W41", provider="provider-legacy", model="model-legacy", live=True)["status"], "reserved")

    def test_routed_authorization_accepts_only_bound_enabled_role_target(self):
        route_policy = policy(target("routed"))
        registry = ModelRegistry(route_policy)
        ledger = self.ledger(route_policy, config_hash="c" * 64, profile="calibration", live_enabled=True)
        authorization = {
            "run_id": "run-1", "profile": "calibration", "config_hash": "c" * 64,
            "provider": None, "model": None, "routing_policy_hash": registry.policy_hash,
            "token_limit": 50, "approved_at": self.clock.now_utc(),
            "approval_reference": "approval-routed",
        }
        ledger.authorize(authorization)
        reservation = ledger.reserve("routed-call", 10, role_id="W41", provider="provider-routed", model="model-routed", live=True)
        self.assertEqual(reservation["model"], "model-routed")
        with self.assertRaises(BudgetAuthorizationError):
            ledger.reserve("unknown-target", 1, role_id="W41", provider="provider-x", model="model-x", live=True)
        with self.assertRaises(BudgetAuthorizationError):
            ledger.reserve("unknown-role", 1, role_id="W42", provider="provider-routed", model="model-routed", live=True)

    def test_routed_authorization_rejects_disabled_and_divergent_policy(self):
        disabled_target = target("off", enabled=False)
        route_policy = policy(disabled_target)
        registry = ModelRegistry(route_policy)
        ledger = self.ledger(route_policy, config_hash="d" * 64, profile="calibration", live_enabled=True)
        auth = {
            "run_id": "run-1", "profile": "calibration", "config_hash": "d" * 64,
            "provider": None, "model": None, "routing_policy_hash": registry.policy_hash,
            "token_limit": 50, "approved_at": self.clock.now_utc(), "approval_reference": "approval",
        }
        ledger.authorize(auth)
        with self.assertRaises(BudgetAuthorizationError):
            ledger.reserve("disabled", 1, role_id="W41", provider="provider-off", model="model-off", live=True)
        other = self.ledger(route_policy, config_hash="e" * 64, profile="calibration", live_enabled=True)
        with self.assertRaises(BudgetAuthorizationError):
            other.authorize({**auth, "config_hash": "e" * 64, "routing_policy_hash": "0" * 64})

    def test_changed_run_binding_fails_and_selected_model_is_accounted(self):
        route_policy = policy(target("small"))
        backend = FakeInferenceBackend(result=InferenceResult(json.dumps(proposal()), 3, 4, 1, True, wall_time_seconds=1, finish_reason="stop"))
        runtime = self.runtime(route_policy, backend)
        runtime.execute(self.request(), allow_test_doubles=True)
        self.assertEqual(runtime.ledger.status()["usage_by_limit"]["per_model_tokens"]["model-small"]["confirmed"], 8)
        with self.assertRaises(BudgetIntegrityError):
            BudgetLedger(self.root, "run-1", limits=runtime.ledger.limits, config_hash="f" * 64, inference_policy=route_policy, clock=self.clock)

    def test_runtime_rejects_registry_ledger_policy_drift(self):
        ledger_policy = policy(target("ledger"))
        registry_policy = policy(target("registry"))
        with self.assertRaises(InferenceIntegrityError):
            InferenceRuntime(
                self.root, self.ledger(ledger_policy), ModelRegistry(registry_policy),
                {"fake": FakeInferenceBackend()}, clock=self.clock,
            )


class M125TransactionTests(M125Base):
    def test_route_reserve_admit_backend_receipt_reconcile_order(self):
        route_policy = policy(target("ordered"))
        registry = ModelRegistry(route_policy)
        ledger = self.ledger(route_policy)
        seen = {}

        class OrderedBackend:
            is_test_double = True

            def preflight(self, _target):
                return {"ready": True}

            def complete(inner_self, request, _target):
                route_files = list((self.root / "state/inference/run-1/routes").glob("*.json"))
                reservations = ledger.status()["reservations"]
                seen.update(route=bool(route_files), status=reservations[0]["status"])
                return InferenceResult(json.dumps(proposal()), 2, 2, 0, True, wall_time_seconds=1, finish_reason="stop")

        runtime = InferenceRuntime(self.root, ledger, registry, {"fake": OrderedBackend()}, clock=self.clock)
        outcome = runtime.execute(self.request(), allow_test_doubles=True)
        self.assertEqual(seen, {"route": True, "status": "ADMITTED"})
        self.assertEqual(outcome["reconciled"]["status"], "RECONCILED")
        self.assertTrue(list((self.root / "state/inference/run-1/receipts").glob("*.json")))

    def test_crash_after_receipt_recovers_without_second_backend_call(self):
        route_policy = policy(target("recover"))
        backend = FakeInferenceBackend(result=InferenceResult(json.dumps(proposal()), 2, 2, 0, True, wall_time_seconds=1, finish_reason="stop"))
        raised = False

        def fault(stage):
            nonlocal raised
            if stage == "after_receipt" and not raised:
                raised = True
                raise SystemExit("simulated process death")

        runtime = self.runtime(route_policy, backend, fault=fault)
        with self.assertRaises(SystemExit):
            runtime.execute(self.request(), allow_test_doubles=True)
        self.assertEqual(runtime.ledger.status()["reservations"][0]["status"], "ADMITTED")
        recovered = InferenceRuntime(self.root, runtime.ledger, runtime.registry, {"fake": backend}, clock=self.clock)
        outcome = recovered.execute(self.request(), allow_test_doubles=True)
        self.assertTrue(outcome["replayed"])
        self.assertEqual(len(backend.calls), 1)
        self.assertEqual(outcome["reconciled"]["status"], "RECONCILED")

    def test_exception_after_admission_is_uncertain_and_never_refunded(self):
        route_policy = policy(target("fail"))
        backend = FakeInferenceBackend(failure="timeout")
        runtime = self.runtime(route_policy, backend)
        with self.assertRaises(InferenceBackendError):
            runtime.execute(self.request(), allow_test_doubles=True)
        status = runtime.ledger.status()
        self.assertEqual(status["reservations"][0]["status"], "UNCERTAIN")
        self.assertEqual(status["usage"]["reserved_tokens"], 20)
        self.assertEqual(len(backend.calls), 1)

    def test_backend_content_over_routed_bound_is_uncertain(self):
        route_policy = policy(target("oversized"))
        backend = FakeInferenceBackend(result=InferenceResult("x" * 70_000))
        runtime = self.runtime(route_policy, backend)
        with self.assertRaises(InferenceBackendError):
            runtime.execute(self.request(), allow_test_doubles=True)
        self.assertEqual(runtime.ledger.status()["reservations"][0]["status"], "UNCERTAIN")

    def test_real_backend_requires_live_run_authorization(self):
        route_policy = policy(target("real"))

        class RealBackend:
            is_test_double = False

            def preflight(self, _target):
                return {"ready": True}

            def complete(self, _request, _target):
                raise AssertionError("must not be called without live authorization")

        runtime = self.runtime(route_policy, RealBackend())
        with self.assertRaises(InferenceBackendError):
            runtime.execute(self.request())
        self.assertEqual(runtime.ledger.read_events(), [])

    def test_duplicate_call_is_idempotent_and_conflicting_receipt_rejected(self):
        route_policy = policy(target("repeat"))
        backend = FakeInferenceBackend(result=InferenceResult(json.dumps(proposal()), 1, 1, 0, True, wall_time_seconds=1, finish_reason="stop"))
        runtime = self.runtime(route_policy, backend)
        first = runtime.execute(self.request(), allow_test_doubles=True)
        second = runtime.execute(self.request(), allow_test_doubles=True)
        self.assertTrue(second["replayed"])
        self.assertEqual(len(backend.calls), 1)
        path = runtime.store.receipts_dir / f"{first['receipt']['call_id']}.json"
        copied = runtime.store.receipts_dir / "different-call.json"
        shutil.copy(path, copied)
        with self.assertRaises(InferenceIntegrityError):
            runtime.store.receipt_for_call("different-call")
        copied.unlink()
        value = json.loads(path.read_text())
        value["response_hash"] = "0" * 64
        path.write_text(json.dumps(value))
        with self.assertRaises(InferenceIntegrityError):
            runtime.execute(self.request(), allow_test_doubles=True)

    def test_freeze_has_no_route_file_reservation_or_backend_call(self):
        route_policy = policy(target("freeze"))
        backend = FakeInferenceBackend()
        runtime = self.runtime(route_policy, backend)
        outcome = runtime.execute(self.request("FREEZE"), allow_test_doubles=True)
        self.assertEqual(outcome["decision"]["reason_code"], "NO_INFERENCE_REQUIRED")
        self.assertEqual(runtime.ledger.read_events(), [])
        self.assertEqual(runtime.store.routes(), [])
        self.assertEqual(backend.calls, [])

    def test_schema_invalid_is_receipted_reconciled_and_escalatable(self):
        route_policy = policy(target("small"), target("large"))
        backend = FakeInferenceBackend(failure="schema_invalid")
        runtime = self.runtime(route_policy, backend)
        request = self.request()
        first = runtime.router.route(request)
        with self.assertRaises(InferenceOutputError):
            runtime.execute(request, allow_test_doubles=True)
        self.assertEqual(runtime.ledger.status()["reservations"][0]["status"], "RECONCILED")
        second = runtime.escalation(request, first, "OUTPUT_SCHEMA_INVALID")
        self.assertEqual(second.target_id, "large")

    def test_receipt_and_logs_never_persist_prompt_or_response(self):
        route_policy = policy(target("redacted"))
        sensitive_prompt = "PROMPT-SHOULD-NOT-PERSIST"
        response = proposal()
        response["patch_or_operations"]["operations"][0]["value"] = "RESPONSE-SHOULD-NOT-PERSIST"
        backend = FakeInferenceBackend(result=InferenceResult(json.dumps(response), 1, 1, 0, True, wall_time_seconds=1, finish_reason="stop"))
        runtime = self.runtime(route_policy, backend)
        request = InferenceRequest.from_agent_task(self.root, self.task(), prompt=sensitive_prompt, required_capabilities=["language", "structured_output"], estimate_tokens=20, max_output_tokens=100)
        runtime.execute(request, allow_test_doubles=True)
        durable = "\n".join(path.read_text(errors="ignore") for path in (self.root / "state").rglob("*") if path.is_file())
        durable += "\n" + "\n".join(path.read_text(errors="ignore") for path in (self.root / "logs").rglob("*") if path.is_file())
        self.assertNotIn(sensitive_prompt, durable)
        self.assertNotIn("RESPONSE-SHOULD-NOT-PERSIST", durable)

    def test_symlink_and_path_traversal_are_rejected(self):
        with self.assertRaises(Exception):
            InferenceStore(self.root, "../escape")
        (self.root / "state").mkdir(exist_ok=True)
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / "state/inference").symlink_to(outside)
        with self.assertRaises(InferenceIntegrityError):
            InferenceStore(self.root, "run-1")


class _FixtureHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):  # noqa: A002
        return

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.server.last_body = self.rfile.read(length)
        if self.path == "/timeout":
            time.sleep(1.3)
            return
        if self.path == "/closed":
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/valid")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if self.path == "/error":
            self.send_response(500)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if self.path == "/malformed":
            raw = b"not-json"
        elif self.path == "/oversize":
            raw = b"x" * 2048
        else:
            envelope = {"choices": [{"message": {"content": json.dumps(proposal())}, "finish_reason": "stop"}]}
            if self.path == "/valid":
                envelope["usage"] = {"prompt_tokens": 3, "completion_tokens": 4, "prompt_tokens_details": {"cached_tokens": 1}}
            raw = json.dumps(envelope).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except BrokenPipeError:
            pass


class M125LoopbackBackendTests(M125Base):
    @classmethod
    def setUpClass(cls):
        try:
            cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _FixtureHandler)
        except PermissionError as error:
            raise unittest.SkipTest("environment forbids loopback sockets") from error
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def local_target(self, path: str) -> object:
        port = self.server.server_address[1]
        value = target("http", backend_type="local_openai_compatible", endpoint=f"http://127.0.0.1:{port}{path}")
        return ModelRegistry(policy(value)).target("http")

    def test_request_valid_response_and_usage(self):
        backend = LocalOpenAICompatibleBackend(max_response_bytes=4096)
        result = backend.complete(self.request(), self.local_target("/valid"))
        self.assertTrue(result.usage_available)
        self.assertEqual((result.input_tokens, result.output_tokens, result.cache_tokens), (3, 4, 1))
        sent = json.loads(self.server.last_body)
        self.assertEqual(sent["model"], "model-http")
        self.assertEqual(sent["messages"][0]["content"], self.request().prompt)

    def test_usage_absent_remains_unknown(self):
        result = LocalOpenAICompatibleBackend().complete(self.request(), self.local_target("/usage-absent"))
        self.assertFalse(result.usage_available)
        self.assertIsNone(result.input_tokens)

    def test_malformed_oversize_http_error_redirect_timeout_and_closed_fail(self):
        cases = {
            "/malformed": "BACKEND_FAILURE",
            "/oversize": "BACKEND_FAILURE",
            "/error": "BACKEND_FAILURE",
            "/redirect": "BACKEND_FAILURE",
            "/timeout": "TIMEOUT",
            "/closed": "BACKEND_FAILURE",
        }
        for path, reason in cases.items():
            with self.subTest(path=path):
                backend = LocalOpenAICompatibleBackend(max_response_bytes=1024)
                with self.assertRaises(InferenceBackendError) as caught:
                    backend.complete(self.request(), self.local_target(path))
                self.assertEqual(caught.exception.reason_code, reason)


class M125BackendUnitTests(M125Base):
    class Response:
        def __init__(self, raw: bytes):
            self.raw = raw

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            return self.raw[:limit]

    class Opener:
        def __init__(self, response=None, error=None):
            self.response = response
            self.error = error
            self.request = None

        def open(self, request, timeout):
            self.request = request
            self.timeout = timeout
            if self.error is not None:
                raise self.error
            return self.response

    def local_target(self):
        value = target("unit", backend_type="local_openai_compatible", endpoint="http://127.0.0.1:9999/v1/chat/completions")
        return ModelRegistry(policy(value)).target("unit")

    def test_openai_request_and_response_parse_without_persisting_content(self):
        envelope = {
            "choices": [{"message": {"content": json.dumps(proposal())}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 4, "prompt_tokens_details": {"cached_tokens": 1}},
        }
        opener = self.Opener(self.Response(json.dumps(envelope).encode()))
        backend = LocalOpenAICompatibleBackend(max_response_bytes=4096)
        backend._opener = opener
        result = backend.complete(self.request(), self.local_target())
        sent = json.loads(opener.request.data)
        self.assertEqual(sent["messages"][0]["content"], self.request().prompt)
        self.assertEqual((result.input_tokens, result.output_tokens, result.cache_tokens), (3, 4, 1))

    def test_unknown_usage_malformed_oversize_redirect_and_timeout_fail_closed(self):
        no_usage = {"choices": [{"message": {"content": json.dumps(proposal())}, "finish_reason": "stop"}]}
        backend = LocalOpenAICompatibleBackend(max_response_bytes=4096)
        backend._opener = self.Opener(self.Response(json.dumps(no_usage).encode()))
        self.assertFalse(backend.complete(self.request(), self.local_target()).usage_available)
        cases = [
            (self.Response(b"not-json"), None, "BACKEND_FAILURE"),
            (self.Response(b"x" * 2048), None, "BACKEND_FAILURE"),
            (None, TimeoutError(), "TIMEOUT"),
            (None, urllib.error.URLError(ConnectionResetError("closed")), "BACKEND_FAILURE"),
            (None, urllib.error.HTTPError("http://127.0.0.1/", 302, "redirect", {}, None), "BACKEND_FAILURE"),
        ]
        for response, error, reason in cases:
            with self.subTest(reason=reason, error=type(error).__name__ if error else "response"):
                candidate = LocalOpenAICompatibleBackend(max_response_bytes=1024)
                candidate._opener = self.Opener(response, error)
                try:
                    with self.assertRaises(InferenceBackendError) as caught:
                        candidate.complete(self.request(), self.local_target())
                    self.assertEqual(caught.exception.reason_code, reason)
                finally:
                    if isinstance(error, urllib.error.HTTPError):
                        error.close()


class M125PrimeBoundaryTests(unittest.TestCase):
    def test_prime_selection_is_not_claimed_and_adapter_signature_stays_minimal(self):
        import inspect
        from article_loop.adapters import PrimeRLMAdapter

        self.assertEqual(PRIME_PER_CHILD_MODEL_SELECTION, "unsupported_verified")
        self.assertEqual(list(inspect.signature(PrimeRLMAdapter.spawn).parameters), ["self", "prompt", "name"])
        source = inspect.getsource(PrimeRLMAdapter.spawn)
        self.assertNotIn("model=", source)


if __name__ == "__main__":
    unittest.main()
