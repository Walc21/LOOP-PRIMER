import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))

from article_loop import (  # noqa: E402
    BudgetExceeded, BudgetIntegrityError, BudgetLedger, BudgetLimits,
    ContextMaterializer, DualExecutionAdapter, DualExecutionController,
    ExecutionError, ExecutionPolicy, FakeInferenceBackend, FakeRLMAdapter,
    InferenceBackendError, InferenceIntegrityError, InferenceRequest,
    InferenceResult, InferenceRuntime, ModelRegistry, ModelRouter,
    Orchestrator, RoutedControlAdapter, RunAuthorization, TargetPricing,
    RemoteOpenAICompatibleBackend, execution_readiness, ingest,
)
from article_loop.activation import ActivationPlanner  # noqa: E402
from article_loop.blackboard import Impact  # noqa: E402
from article_loop.orchestrator import OrchestrationError  # noqa: E402


def target(target_id, *, model=None, local=True, paid=False, pricing=None):
    return {
        "target_id": target_id,
        "provider": "provider-one",
        "model": model or "model-" + target_id,
        "backend_type": "fake",
        "enabled": True,
        "local": local,
        "paid": paid,
        "tier": "mid",
        "capabilities": ["language", "structured_output", "math_high_assurance"],
        "context_limit": 1_000_000,
        "max_output_tokens": 1000,
        "independence_group": "legacy-group-" + target_id,
        "endpoint": None,
        "api_key_env": None,
        "timeout_seconds": 1,
        "fallback_target": None,
        "pricing": pricing,
    }


def routing_policy(targets, routes, *, allow_remote=True, allow_paid=False, independence_mode="model"):
    return {
        "schema_version": "1.0.0",
        "enabled": True,
        "allow_local": True,
        "allow_remote": allow_remote,
        "allow_paid": allow_paid,
        "routing_mode": "deterministic",
        "targets": {item["target_id"]: item for item in targets},
        "role_routes": {
            role: {"targets": ids, "required_capabilities": ["language", "structured_output"]}
            for role, ids in routes.items()
        },
        "escalation": {"enabled": True, "max_route_attempts": 3},
        "independence": {
            "jury_must_differ_from_producer_group": True,
            "mode": independence_mode,
        },
    }


def task(root, *, role="W11", locator=None):
    return {
        "schema_version": "1.1.0",
        "task_id": f"run-one-{role}-c0000",
        "run_id": "run-one",
        "cycle_id": 0,
        "role_id": role,
        "activation_mode": "RUN",
        "created_at": "2026-01-01T00:00:00Z",
        "base_hash": "a" * 64,
        "scope": ["proof"],
        "input_locators": [locator or f"readonly:{root / 'allowed.txt'}"],
        "requested_output_schema": "agent-proposal.schema.json",
        "prompt_version": "test",
        "constraints": ["receipt_only"],
    }


def proposal(role="W11", *, base_hash="a" * 64, cycle=0):
    return {
        "schema_version": "1.1.0",
        "proposal_id": f"p-{role}",
        "role_id": role,
        "cycle_id": cycle,
        "base_hash": base_hash,
        "scope": ["proof"],
        "evidence_locators": ["page:1"],
        "patch_or_operations": {
            "kind": "operations",
            "operations": [{"op": "annotate", "target": "proof", "value": "bounded note"}],
        },
        "affected_claims": [],
        "dependencies": [],
        "risk": {"level": "low", "factors": [], "technical_effect_possible": False},
        "confidence": 1,
        "requested_validations": [],
        "prompt_version": "test",
    }


def scientific_payload(role="W11", *, base_hash="a" * 64, cycle=0):
    value = proposal(role, base_hash=base_hash, cycle=cycle)
    for field in (
        "schema_version", "proposal_id", "role_id", "cycle_id", "base_hash",
        "prompt_version",
    ):
        del value[field]
    return value


class ContextAndConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "config", self.root / "config")
        (self.root / "allowed.txt").write_text("authorized context", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_project_defaults_distinguish_implementation_configuration_and_live(self):
        status = execution_readiness(ROOT)
        self.assertTrue(status["implementation_ready"])
        self.assertFalse(status["configuration_ready"])
        self.assertFalse(status["live_ready"])
        self.assertEqual(status["privacy_mode"], "deny_remote")
        self.assertEqual(status["max_run_cost_microunits"], 10_000_000)
        self.assertEqual(status["currency"], "USD")
        self.assertEqual(
            set(status["missing_configuration"]),
            {"department_execution_map", "local_target", "remote_target", "target_pricing", "role_routes", "run_authorization"},
        )

    def test_materializer_is_closed_hash_bound_and_does_not_load_pdf(self):
        pdf = self.root / "original.pdf"
        pdf.write_bytes(b"DO_NOT_READ_BINARY_PDF")
        current = task(self.root)
        current["input_locators"].append(f"readonly:{pdf}")
        view = {"task": current, "excerpts": current["input_locators"], "dependent_claims": [], "rubric": {"locator": current["input_locators"][0]}, "local_history": []}
        context = ContextMaterializer(self.root).materialize(
            current, view, privacy_mode="scoped_remote",
            context_limit=1000, max_output_tokens=10, overhead_tokens=0,
        )
        self.assertIn("authorized context", context.prompt_fragment())
        self.assertNotIn("DO_NOT_READ_BINARY_PDF", context.prompt_fragment())
        self.assertEqual(context.omitted_binary_locators, (f"readonly:{pdf}",))
        self.assertEqual(len(context.context_hash), 64)

    def test_materializer_rejects_traversal_symlink_unlisted_locator_and_overflow(self):
        materializer = ContextMaterializer(self.root)
        outside = task(self.root, locator="readonly:/etc/hosts")
        with self.assertRaises(ExecutionError):
            materializer.materialize(outside, {"task": outside, "excerpts": outside["input_locators"], "dependent_claims": [], "rubric": None, "local_history": []}, privacy_mode="full_remote", context_limit=1000, max_output_tokens=10, overhead_tokens=0)
        link = self.root / "link.txt"
        link.symlink_to(self.root / "allowed.txt")
        linked = task(self.root, locator=f"readonly:{link}")
        with self.assertRaises(ExecutionError):
            materializer.materialize(linked, {"task": linked, "excerpts": linked["input_locators"], "dependent_claims": [], "rubric": None, "local_history": []}, privacy_mode="full_remote", context_limit=1000, max_output_tokens=10, overhead_tokens=0)
        current = task(self.root)
        widened = {"task": current, "excerpts": ["readonly:/etc/hosts"], "dependent_claims": [], "rubric": None, "local_history": []}
        with self.assertRaises(ExecutionError):
            materializer.materialize(current, widened, privacy_mode="scoped_remote", context_limit=1000, max_output_tokens=10, overhead_tokens=0)
        with self.assertRaises(ExecutionError):
            materializer.materialize(current, {"task": current, "excerpts": current["input_locators"], "dependent_claims": [], "rubric": None, "local_history": []}, privacy_mode="scoped_remote", context_limit=1, max_output_tokens=1, overhead_tokens=0)

    def test_full_remote_requires_explicit_locator_and_deny_remote_blocks_route(self):
        marker = self.root / "explicit.txt"
        marker.write_text("DO_NOT_EXFILTRATE_12345", encoding="utf-8")
        current = task(self.root, locator=f"readonly:{marker}")
        view = {"task": current, "excerpts": current["input_locators"], "dependent_claims": [], "rubric": None, "local_history": []}
        full = ContextMaterializer(self.root).materialize(
            current, view, privacy_mode="full_remote",
            context_limit=1000, max_output_tokens=10, overhead_tokens=0,
        )
        self.assertIn("DO_NOT_EXFILTRATE_12345", full.prompt_fragment())
        remote = target("remote", local=False)
        registry = ModelRegistry(routing_policy([remote], {"W11": ["remote"]}))
        request = InferenceRequest.from_agent_task(
            self.root, current, prompt="bounded", required_capabilities=["language"],
            estimate_tokens=1, max_output_tokens=1,
            context_hash=full.context_hash, privacy_mode="deny_remote",
        )
        with self.assertRaises(Exception):
            ModelRouter(registry).route(request)


class MonetaryAndJuryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def ledger(self, run="run-one", ceiling=10_000_000):
        return BudgetLedger(
            self.root, run, limits=BudgetLimits(total_tokens=10_000, max_calls=20),
            currency="USD", max_run_cost_microunits=ceiling,
        )

    def test_integer_pricing_exact_ceiling_and_one_microunit_over(self):
        pricing = TargetPricing("USD", 2_000_000, 4_000_000)
        self.assertEqual(pricing.cost(3, 2), 14)
        ledger = self.ledger()
        ledger.reserve("exact", 1, estimated_cost_microunits=10_000_000)
        with self.assertRaises(BudgetExceeded):
            ledger.reserve("over", 1, estimated_cost_microunits=1)
        status = ledger.status()
        self.assertEqual(status["usage"]["reserved_cost_microunits"], 10_000_000)
        self.assertEqual(status["available"]["cost_microunits"], 0)

    def test_concurrent_reservations_unknown_cost_overrun_and_restart_binding(self):
        ledger = self.ledger()
        def reserve(index):
            try:
                ledger.reserve(f"parallel-{index}", 1, estimated_cost_microunits=6_000_000)
                return "ok"
            except BudgetExceeded:
                return "blocked"
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(reserve, (1, 2))), ["blocked", "ok"])
        resumed = self.ledger()
        self.assertEqual(resumed.status()["usage"]["reserved_cost_microunits"], 6_000_000)
        with self.assertRaises(BudgetIntegrityError):
            self.ledger(ceiling=10_000_001)

        other = self.ledger("unknown")
        reservation = other.reserve("unknown-cost", 5, estimated_cost_microunits=10_000_000)
        other.admit(reservation["reservation_id"], "receipt-unknown")
        other.reconcile(reservation["reservation_id"], receipt_id="receipt-unknown", usage_available=False)
        self.assertEqual(other.status()["available"]["cost_microunits"], 0)

        overrun = self.ledger("overrun")
        reservation = overrun.reserve("first", 5, estimated_cost_microunits=5)
        overrun.admit(reservation["reservation_id"], "receipt-first")
        overrun.reconcile(reservation["reservation_id"], receipt_id="receipt-first", input_tokens=1, output_tokens=1, cache_tokens=0, cost_microunits=6, currency="USD", usage_available=True)
        with self.assertRaises(BudgetExceeded):
            overrun.reserve("second", 1, estimated_cost_microunits=1)

    def test_authorization_binds_ceiling_currency_and_jury_uses_model(self):
        ledger = self.ledger()
        auth = RunAuthorization(
            "run-one", None, ledger.config_hash, None, None, 100,
            datetime.now(timezone.utc).isoformat(), "test approval", None,
            10_000_000, "USD",
        )
        ledger.authorize(auth)
        self.assertTrue(ledger.status()["authorization"]["present"])

        model_a = target("a", model="same-model")
        model_b = target("b", model="different-model")
        policy = routing_policy([model_a, model_b], {"W11": ["a", "b"]})
        registry = ModelRegistry(policy)
        current = task(self.root)
        request = InferenceRequest.from_agent_task(
            ROOT, current, prompt="jury", required_capabilities=["language"],
            estimate_tokens=1, max_output_tokens=1, jury=True,
            producer_target="producer", producer_group="other-group",
            producer_model="same-model", context_hash="b" * 64,
            privacy_mode="scoped_remote",
        )
        decision = ModelRouter(registry).route(request)
        self.assertEqual(decision.model, "different-model")
        only_a = ModelRegistry(routing_policy([model_a], {"W11": ["a"]}))
        with self.assertRaises(Exception):
            ModelRouter(only_a).route(request)


class RuntimeRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "config/schemas").mkdir(parents=True)
        (self.root / "control").mkdir()
        for name in ("agent-task.schema.json", "agent-proposal.schema.json", "inference-receipt.schema.json"):
            shutil.copy(ROOT / "config/schemas" / name, self.root / "config/schemas" / name)
        self.policy = routing_policy([target("local")], {"W11": ["local"]}, allow_remote=False)
        self.backend = FakeInferenceBackend(result=InferenceResult(json.dumps(scientific_payload()), 10, 5, 0, True, wall_time_seconds=1, finish_reason="stop"))

    def tearDown(self):
        self.temp.cleanup()

    def runtime(self, *, fault=None):
        ledger = BudgetLedger(
            self.root, "run-one", limits=BudgetLimits(total_tokens=1000, max_calls=5),
            inference_policy=self.policy, currency="USD",
            max_run_cost_microunits=10_000_000,
        )
        registry = ModelRegistry(self.policy)
        return InferenceRuntime(self.root, ledger, registry, {"fake": self.backend}, fault=fault)

    def request(self):
        return InferenceRequest.from_agent_task(
            self.root, task(self.root), prompt="bounded prompt",
            required_capabilities=["language", "structured_output"],
            estimate_tokens=20, max_output_tokens=100,
            context_hash="c" * 64, privacy_mode="scoped_remote",
        )

    def test_output_before_receipt_recovers_without_another_backend_call(self):
        def crash(stage):
            if stage == "after_output":
                raise SystemExit("crash")
        with self.assertRaises(SystemExit):
            self.runtime(fault=crash).execute(self.request(), allow_test_doubles=True)
        self.assertEqual(len(self.backend.calls), 1)
        ledger = BudgetLedger(
            self.root, "run-one", limits=BudgetLimits(total_tokens=1000, max_calls=5),
            inference_policy=self.policy, currency="USD",
            max_run_cost_microunits=10_000_000,
        )
        recovered = InferenceRuntime(
            self.root, ledger, ModelRegistry(self.policy), {},
        ).execute(self.request(), allow_test_doubles=True)
        self.assertTrue(recovered["recovered_from_output"])
        self.assertEqual(len(self.backend.calls), 1)
        self.assertEqual(recovered["receipt"]["context_hash"], "c" * 64)
        self.assertEqual(recovered["receipt"]["privacy_mode"], "scoped_remote")

    def test_reserved_before_admission_requires_proof_and_reconciled_replay_is_call_free(self):
        def crash_after_reserve(stage):
            if stage == "after_reserve":
                raise SystemExit("crash")
        runtime = self.runtime(fault=crash_after_reserve)
        with self.assertRaises(SystemExit):
            runtime.execute(self.request(), allow_test_doubles=True)
        self.assertEqual(self.backend.calls, [])
        with self.assertRaises(InferenceIntegrityError):
            self.runtime().execute(self.request(), allow_test_doubles=True)
        reservation = runtime.ledger.status()["reservations"][0]
        released = runtime.ledger.release_unadmitted(
            reservation["reservation_id"], "backend invocation was not reached",
        )
        self.assertEqual(released["status"], "RELEASED")

        other_root = Path(tempfile.mkdtemp())
        try:
            (other_root / "config/schemas").mkdir(parents=True)
            (other_root / "control").mkdir()
            for name in ("agent-task.schema.json", "agent-proposal.schema.json", "inference-receipt.schema.json"):
                shutil.copy(ROOT / "config/schemas" / name, other_root / "config/schemas" / name)
            other_backend = FakeInferenceBackend(result=self.backend.result)
            policy = self.policy
            ledger = BudgetLedger(other_root, "run-one", limits=BudgetLimits(total_tokens=1000, max_calls=5), inference_policy=policy, currency="USD", max_run_cost_microunits=10_000_000)
            registry = ModelRegistry(policy)
            def crash_after_reconcile(stage):
                if stage == "after_reconcile":
                    raise SystemExit("crash")
            first = InferenceRuntime(other_root, ledger, registry, {"fake": other_backend}, fault=crash_after_reconcile)
            other_request = InferenceRequest.from_agent_task(other_root, task(other_root), prompt="bounded prompt", required_capabilities=["language", "structured_output"], estimate_tokens=20, max_output_tokens=100, context_hash="c" * 64, privacy_mode="scoped_remote")
            with self.assertRaises(SystemExit):
                first.execute(other_request, allow_test_doubles=True)
            replay = InferenceRuntime(other_root, BudgetLedger(other_root, "run-one", limits=BudgetLimits(total_tokens=1000, max_calls=5), inference_policy=policy, currency="USD", max_run_cost_microunits=10_000_000), registry, {"fake": other_backend})
            self.assertTrue(replay.execute(other_request, allow_test_doubles=True)["replayed"])
            self.assertEqual(len(other_backend.calls), 1)
        finally:
            shutil.rmtree(other_root)

    def test_admitted_unknown_is_not_retried_and_output_divergence_fails_closed(self):
        def crash(stage):
            if stage == "after_admit":
                raise SystemExit("crash")
        with self.assertRaises(SystemExit):
            self.runtime(fault=crash).execute(self.request(), allow_test_doubles=True)
        with self.assertRaises(InferenceBackendError):
            self.runtime().execute(self.request(), allow_test_doubles=True)
        self.assertEqual(self.backend.calls, [])

    def test_persisted_output_hash_divergence_blocks_replay(self):
        outcome = self.runtime().execute(self.request(), allow_test_doubles=True)
        output = self.root / outcome["receipt"]["output_locator"]
        output.write_text("{}\n", encoding="utf-8")
        with self.assertRaises(InferenceIntegrityError):
            self.runtime().execute(self.request(), allow_test_doubles=True)
        self.assertEqual(len(self.backend.calls), 1)

    def test_reconciled_output_can_be_rematerialized_for_m6_without_reinference(self):
        first = self.runtime().execute(self.request(), allow_test_doubles=True)
        workspace = self.root / "workspaces/run-one/cycle-0000/W11"
        workspace.mkdir(parents=True)
        published = self.runtime().store.materialize_output(first["receipt"]["call_id"], workspace)
        (workspace / "agent-proposal.json").unlink()
        replay = self.runtime().execute(self.request(), allow_test_doubles=True)
        again = self.runtime().store.materialize_output(replay["receipt"]["call_id"], workspace)
        self.assertEqual(published["sha256"], again["sha256"])
        self.assertEqual(len(self.backend.calls), 1)


class RoleAwareBackend:
    is_test_double = True

    def __init__(self, base_hash):
        self.base_hash = base_hash
        self.calls = []

    def preflight(self, target):
        return {"ready": True, "test_double": True, "network": False}

    def complete(self, request, target):
        self.calls.append({"role": request.role_id, "target": target.target_id, "prompt": request.prompt})
        return InferenceResult(
            json.dumps(scientific_payload(request.role_id, base_hash=request.base_hash, cycle=request.cycle_id)),
            10, 5, 0, True, wall_time_seconds=1, finish_reason="stop",
        )


class RemoteBackendContractTests(unittest.TestCase):
    def test_https_backend_disables_proxy_redirect_and_parses_bounded_usage(self):
        raw = json.dumps({
            "choices": [{"message": {"content": json.dumps(scientific_payload())}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 7, "completion_tokens": 5, "prompt_tokens_details": {"cached_tokens": 2}},
        }).encode()
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit): return raw
        remote = target("https", local=False)
        remote.update({
            "backend_type": "remote_openai_compatible",
            "endpoint": "https://models.example.invalid/v1/chat/completions",
            "api_key_env": "M1251_TEST_API_KEY",
        })
        selected = ModelRegistry(routing_policy([remote], {"W11": ["https"]})).target("https")
        backend = RemoteOpenAICompatibleBackend(
            project_root=ROOT, max_response_bytes=100_000,
        )
        current = task(ROOT)
        request = InferenceRequest.from_agent_task(ROOT, current, prompt="bounded", required_capabilities=["language"], estimate_tokens=1, max_output_tokens=1, context_hash="d" * 64, privacy_mode="scoped_remote")
        with mock.patch.dict(os.environ, {"M1251_TEST_API_KEY": "unit-test-only"}, clear=False):
            with mock.patch.object(backend._opener, "open", return_value=Response()) as opened:
                result = backend.complete(request, selected)
        self.assertEqual((result.input_tokens, result.output_tokens, result.cache_tokens), (7, 5, 2))
        self.assertEqual(result.finish_reason, "stop")
        sent = opened.call_args.args[0]
        self.assertEqual(sent.full_url, selected.endpoint)
        self.assertEqual(backend.preflight(selected)["proxies"], False)
        self.assertEqual(backend.preflight(selected)["redirects"], False)


class EndToEndDualExecutionTests(unittest.TestCase):
    def setUp(self):
        if shutil.which("gs") is None:
            self.skipTest("ghostscript is required by the existing M3 fixture")
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for relative in ("input/inbox", "artifacts/original", "artifacts/extracted", "artifacts/rendered", "versions/champion", "workspaces", "state"):
            (self.root / relative).mkdir(parents=True, exist_ok=True)
        shutil.copytree(ROOT / "config", self.root / "config", dirs_exist_ok=True)
        shutil.copytree(ROOT / "prompts", self.root / "prompts")
        (self.root / "DO_NOT_EXFILTRATE.txt").write_text("DO_NOT_EXFILTRATE_12345", encoding="utf-8")
        source = self.root / "fixture.ps"
        source.write_text("%!PS\n/Courier findfont 18 scalefont setfont 72 700 moveto (Fixture x = 1 [1]) show showpage\n")
        self.pdf = self.root / "input/inbox/artigo.pdf"
        subprocess.run(["gs", "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", f"-sOutputFile={self.pdf}", str(source)], check=True)
        ingested = ingest(self.root)
        self.base_hash = json.loads((self.root / "versions/champion/v0000/manifest.json").read_text())["content_hash"]
        self.run = ingested["run_id"]

    def tearDown(self):
        self.temp.cleanup()

    def test_dual_prime_test_double_requires_root_authorization_before_m6_writes(self):
        impact = Impact(
            ("claim:fixture",), ("section:proof",), ("equation:1",), ("reference:1",),
            ("W11",), 10,
        )
        plan = ActivationPlanner().plan(cycle_id=0, impact=impact).activation_map()
        blackboard = self.root / "state/blackboard" / self.run
        blackboard.mkdir(parents=True)
        encoded = json.dumps(plan, sort_keys=True, separators=(",", ":"))
        (blackboard / "activation-c0000.json").write_text(encoded)
        (blackboard / "activation_map.json").write_text(encoded)
        execution = ExecutionPolicy(
            True, "dual",
            {"S10": "routed", "S20": "prime", "S30": "prime", "S40": "prime", "S50": "prime"},
            "scoped_remote", "d" * 64,
        )
        fake_prime = FakeRLMAdapter()
        dual = DualExecutionAdapter(self.root, self.run, execution, prime_adapter=fake_prime)
        orchestrator = Orchestrator(self.root, dual)
        asyncio.run(orchestrator.bootstrap(self.pdf))
        journal = self.root / "state/orchestration" / self.run / "journal.jsonl"
        before = journal.read_bytes()

        with self.assertRaisesRegex(OrchestrationError, "test double requires"):
            asyncio.run(orchestrator.run_cycle(run_id=self.run, plan=plan))

        self.assertEqual(journal.read_bytes(), before)
        self.assertEqual(fake_prime.calls, [])
        self.assertFalse((self.root / "workspaces" / self.run).exists())

        with self.assertRaisesRegex(ExecutionError, "Prime layer adapter"):
            DualExecutionAdapter(self.root, self.run, execution, prime_adapter=object())

    def test_s10_routed_workers_rejoin_m6_while_s20_remains_prime(self):
        impact = Impact(
            ("claim:fixture",), ("section:proof",), ("equation:1",), ("reference:1",),
            ("W11", "W12", "W13", "W21"), 10,
        )
        plan = ActivationPlanner().plan(cycle_id=0, impact=impact).activation_map()
        blackboard = self.root / "state/blackboard" / self.run
        blackboard.mkdir(parents=True)
        encoded = json.dumps(plan, sort_keys=True, separators=(",", ":"))
        (blackboard / "activation-c0000.json").write_text(encoded)
        (blackboard / "activation_map.json").write_text(encoded)

        execution = ExecutionPolicy(
            True, "dual",
            {"S10": "routed", "S20": "prime", "S30": "prime", "S40": "prime", "S50": "prime"},
            "scoped_remote", "d" * 64,
        )
        prime = FakeRLMAdapter()
        dual = DualExecutionAdapter(self.root, self.run, execution, prime_adapter=prime)
        orchestrator = Orchestrator(self.root, dual)
        asyncio.run(orchestrator.bootstrap(self.pdf))
        state = asyncio.run(orchestrator.run_cycle(
            run_id=self.run, plan=plan, allow_test_doubles=True,
        ))
        self.assertTrue(state["children"]["S10"]["child_id"].startswith("routed-"))
        self.assertTrue(state["children"]["S20"]["child_id"].startswith("fake-"))

        targets = [
            target("local-w11"),
            target("remote-w12", local=False),
            target("local-w13"),
        ]
        policy = routing_policy(
            targets,
            {"W11": ["local-w11"], "W12": ["remote-w12"], "W13": ["local-w13"]},
        )
        registry = ModelRegistry(policy)
        ledger = BudgetLedger(
            self.root, self.run,
            limits=BudgetLimits(total_tokens=100_000, max_calls=10, max_wall_time_seconds=100),
            inference_policy=policy, currency="USD", max_run_cost_microunits=10_000_000,
        )
        backend = RoleAwareBackend(self.base_hash)
        runtime = InferenceRuntime(self.root, ledger, registry, {"fake": backend})
        controller = DualExecutionController(self.root, execution, registry)
        manager = dual.department_adapter(state["children"]["S10"])
        final = asyncio.run(controller.execute_routed_department(
            orchestrator, self.run, "S10", manager, runtime,
            allow_test_doubles=True,
        ))
        self.assertTrue({"W11", "W12", "W13", "S10"}.issubset(final["receipts"]))
        self.assertEqual({call["role"] for call in backend.calls}, {"W11", "W12", "W13"})
        routes = {call["role"]: call["target"] for call in backend.calls}
        self.assertEqual(routes, {"W11": "local-w11", "W12": "remote-w12", "W13": "local-w13"})
        remote_prompt = next(call["prompt"] for call in backend.calls if call["role"] == "W12")
        self.assertNotIn("DO_NOT_EXFILTRATE_12345", remote_prompt)
        packet = json.loads(Path(final["receipts"]["S10"]["path"]).read_text())
        self.assertEqual(packet["department_id"], "S10")
        self.assertEqual(len(packet["proposal_ids"]), 3)
        self.assertTrue(all(value.startswith("p-") for value in packet["proposal_ids"]))

    def test_routed_workspace_revalidation_precedes_router_budget_backend_and_receipt(self):
        impact = Impact(
            ("claim:fixture",), ("section:proof",), ("equation:1",), ("reference:1",),
            ("W11", "W12", "W13"), 10,
        )
        plan = ActivationPlanner().plan(cycle_id=0, impact=impact).activation_map()
        blackboard = self.root / "state/blackboard" / self.run
        blackboard.mkdir(parents=True)
        encoded = json.dumps(plan, sort_keys=True, separators=(",", ":"))
        (blackboard / "activation-c0000.json").write_text(encoded)
        (blackboard / "activation_map.json").write_text(encoded)

        execution = ExecutionPolicy(
            True, "dual",
            {"S10": "routed", "S20": "prime", "S30": "prime", "S40": "prime", "S50": "prime"},
            "scoped_remote", "d" * 64,
        )
        dual = DualExecutionAdapter(
            self.root, self.run, execution, prime_adapter=FakeRLMAdapter(),
        )
        orchestrator = Orchestrator(self.root, dual)
        asyncio.run(orchestrator.bootstrap(self.pdf))
        state = asyncio.run(orchestrator.run_cycle(
            run_id=self.run, plan=plan, allow_test_doubles=True,
        ))
        manager = dual.department_adapter(state["children"]["S10"])
        state = asyncio.run(orchestrator.advance_department(
            self.run, "S10", adapter=manager,
        ))
        child = state["children"]["W11"]
        workspace = Path(child["workspace"])

        policy = routing_policy(
            [target("local-w11"), target("local-w12"), target("local-w13")],
            {"W11": ["local-w11"], "W12": ["local-w12"], "W13": ["local-w13"]},
        )
        registry = ModelRegistry(policy)
        ledger = BudgetLedger(
            self.root, self.run,
            limits=BudgetLimits(total_tokens=100_000, max_calls=10, max_wall_time_seconds=100),
            inference_policy=policy, currency="USD", max_run_cost_microunits=10_000_000,
        )
        backend = RoleAwareBackend(self.base_hash)
        runtime = InferenceRuntime(self.root, ledger, registry, {"fake": backend})
        controller = DualExecutionController(self.root, execution, registry)
        budget_before = ledger.read_events()
        originals = {
            name: (workspace / name).read_bytes()
            for name in ("task.json", "view.json", "prompt.txt")
        }

        def assert_rejected():
            with mock.patch.object(runtime.router, "route", side_effect=AssertionError("router must not run")) as routed, \
                    mock.patch.object(runtime, "execute", side_effect=AssertionError("runtime must not run")) as executed:
                with self.assertRaises(ExecutionError):
                    asyncio.run(controller.execute_routed_department(
                        orchestrator, self.run, "S10", manager, runtime,
                        allow_test_doubles=True,
                    ))
            self.assertFalse(routed.called)
            self.assertFalse(executed.called)
            self.assertEqual(ledger.read_events(), budget_before)
            self.assertEqual(backend.calls, [])
            self.assertNotIn("W11", asyncio.run(orchestrator.status(self.run))["receipts"])

        for name in ("task.json", "view.json", "prompt.txt"):
            with self.subTest(case=f"tampered-{name}"):
                path = workspace / name
                path.write_bytes(originals[name] + b" ")
                assert_rejected()
                path.write_bytes(originals[name])

        replacement = self.root / "replacement-input.json"
        replacement.write_bytes(originals["task.json"])
        task_path = workspace / "task.json"
        task_path.unlink()
        task_path.symlink_to(replacement)
        try:
            with self.subTest(case="symlinked-file"):
                assert_rejected()
        finally:
            task_path.unlink()
            task_path.write_bytes(originals["task.json"])

        relocated = workspace.parent / (workspace.name + "-relocated")
        workspace.rename(relocated)
        workspace.symlink_to(relocated, target_is_directory=True)
        try:
            with self.subTest(case="symlinked-workspace"):
                assert_rejected()
        finally:
            workspace.unlink()
            relocated.rename(workspace)


if __name__ == "__main__":
    unittest.main()
