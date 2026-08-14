import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import jsonschema

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))

from article_loop import FakeRLMAdapter, Orchestrator, ingest
from article_loop.activation import ActivationPlanner
from article_loop.blackboard import Impact
from article_loop.gates import REQUIRED_GATES, compare, run_gates
from article_loop.store import DurableStore
from article_loop.synthesis import M7Pipeline, SynthesisError


class M7ReceiptIntegrationTests(unittest.TestCase):
    """M7 consumes only immutable receipts produced by a real local M6 run."""

    @classmethod
    def setUpClass(cls):
        cls.fixture_dir = tempfile.TemporaryDirectory()
        fixture = Path(cls.fixture_dir.name)
        ps = fixture / "fixture.ps"
        ps.write_text("%!PS\n/Courier findfont 18 scalefont setfont 72 700 moveto (M7 fixture) show showpage\n", encoding="utf-8")
        cls.fixture_pdf = fixture / "fixture.pdf"
        subprocess.run(["gs", "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", f"-sOutputFile={cls.fixture_pdf}", str(ps)], check=True)

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
        self.pdf = self.root / "input/inbox" / "artigo.pdf"
        shutil.copyfile(self.fixture_pdf, self.pdf)
        ingest(self.root)
        self.fake = FakeRLMAdapter()
        self.orchestrator = Orchestrator(self.root, self.fake)
        self.initial = asyncio.run(self.orchestrator.bootstrap(self.pdf))
        self.run_id = self.initial["run_id"]
        impact = Impact(claims=("claim:fixture",), sections=("section:proof",), equations=("equation:1",), references=("reference:1",), roles=tuple(f"W{i}{j}" for i in range(1, 6) for j in range(1, 4)), severity=10)
        self.plan = ActivationPlanner().plan(cycle_id=0, impact=impact).activation_map()
        board = self.root / "state/blackboard" / self.run_id
        board.mkdir(parents=True)
        raw = json.dumps(self.plan, sort_keys=True, separators=(",", ":"))
        (board / "activation-c0000.json").write_text(raw, encoding="utf-8")
        (board / "activation_map.json").write_text(raw, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def _manager(self, department):
        child = asyncio.run(self.orchestrator.status(self.run_id))["children"][department]
        return self.fake.for_child(child["child_id"], actor_role=department)

    def _proposal(self, role):
        target = "article.tex" if role == "W11" else f"evidence/{role.lower()}.txt"
        value = ("\\documentclass{article}\n\\begin{document}\nFixture $x=1$.\\label{fixture}\n\\end{document}\n" if role == "W11" else f"M6 evidence for {role}\n")
        return {
            "schema_version": "1.1.0", "proposal_id": f"p-{role}", "role_id": role, "cycle_id": 0,
            "base_hash": self.initial["base_hash"], "scope": ["proof"], "evidence_locators": ["page:1"],
            "patch_or_operations": {"kind": "operations", "operations": [{"op": "add", "target": target, "value": value}]},
            "affected_claims": ["claim:fixture"] if role == "W22" else [], "dependencies": [],
            "risk": {"level": "low", "factors": [], "technical_effect_possible": False}, "confidence": 1,
            "requested_validations": ["correctness_math"] if role == "W22" else [], "prompt_version": "m7-integration",
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
                # The newline is legitimate receipt data and remains hash-covered.
                path.write_bytes(json.dumps(self._proposal(role), sort_keys=True, separators=(",", ":")).encode() + b"\n")
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                asyncio.run(self.orchestrator.receipt(self.run_id, sender_role=role, parent_role=department, path=path, sha256=digest))
        for department in ("S20", "S10", "S30", "S40", "S50"):
            asyncio.run(self.orchestrator.consolidate_department(self.run_id, department, adapter=self._manager(department)))
        return asyncio.run(self.orchestrator.status(self.run_id))

    def test_real_m6_receipts_drive_all_m7_transitions_and_gates(self):
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        frozen = pipe.freeze_synthesis(synthesis)
        self.assertEqual(frozen.read_bytes(), synthesis["frozen_bytes"])
        store = DurableStore(self.root)
        pipe.record_synthesis(store, synthesis)
        champion = self.root / "versions/champion/v0000"
        manifest = pipe.build(synthesis, champion)
        jsonschema.validate(manifest, json.loads((self.root / "config/schemas/candidate-manifest.schema.json").read_text()))
        pipe.record_candidate(store, manifest)
        candidate = self.root / "versions/challengers" / manifest["candidate_id"]
        self.assertFalse(any(path.stat().st_mode & 0o222 for path in candidate.rglob("*")))
        self.assertNotEqual((champion / "baseline.pdf").stat().st_ino, (candidate / "baseline.pdf").stat().st_ino)
        report = run_gates(candidate)
        jsonschema.validate(report, json.loads((self.root / "config/schemas/gate-report.schema.json").read_text()))
        self.assertEqual(tuple(item["gate_id"] for item in report["gates"]), REQUIRED_GATES)
        self.assertTrue(report["overall_pass"])
        pipe.record_gates(store, report)
        self.assertEqual(store.snapshot(self.run_id)["state"], "GATES_PASSED")

    def test_receipt_path_hash_and_permission_tampering_fail_closed(self):
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        bad = {**state["receipts"], "S10": {**state["receipts"]["S10"], "immutable_path": "state/elsewhere/artifact.json"}}
        with self.assertRaises(SynthesisError):
            pipe.synthesize(bad, run_id=self.run_id)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        manifest = pipe.build(synthesis, self.root / "versions/champion/v0000")
        candidate = self.root / "versions/challengers" / manifest["candidate_id"]
        os.chmod(candidate / "article.tex", 0o644)
        with self.assertRaises(Exception):
            pipe.build(synthesis, self.root / "versions/champion/v0000")

    def test_semantically_equivalent_receipt_with_different_bytes_is_rejected(self):
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        receipt = Path(state["receipts"]["W11"]["immutable_path"])
        os.chmod(receipt.parent, 0o700)
        os.chmod(receipt, 0o600)
        # Same JSON value, different serialization: the original bytes remain
        # the evidence and must not be canonicalized before hashing.
        receipt.write_bytes(json.dumps(json.loads(receipt.read_bytes()), indent=2).encode("utf-8") + b"\n")
        with self.assertRaises(SynthesisError):
            pipe.build(synthesis, self.root / "versions/champion/v0000")

    def test_missing_or_swapped_worker_receipts_are_not_accepted(self):
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        absent = dict(state["receipts"]); absent.pop("W11")
        with self.assertRaises(SynthesisError):
            pipe.synthesize(absent, run_id=self.run_id)
        swapped = dict(state["receipts"]); swapped["W11"] = state["receipts"]["W12"]
        with self.assertRaises(SynthesisError):
            pipe.synthesize(swapped, run_id=self.run_id)

    def test_record_synthesis_uses_rebuilt_identity_not_caller_fields(self):
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        forged = dict(synthesis); forged["run_id"] = "other-run"
        store = DurableStore(self.root)
        pipe.record_synthesis(store, forged)
        self.assertEqual(store.snapshot(self.run_id)["state"], "SYNTHESIS_READY")
        self.assertNotIn("other-run", (self.root / "state" / "runs").as_posix())

    def test_adapter_cannot_declare_a_gate_pass(self):
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        manifest = pipe.build(synthesis, self.root / "versions/champion/v0000")

        class LyingAdapter:
            def __getattr__(self, name):
                raise AssertionError(f"gate adapter was consulted: {name}")

        report = run_gates(self.root / "versions/challengers" / manifest["candidate_id"], adapter=LyingAdapter())
        self.assertTrue(report["overall_pass"])

    def test_publication_recovers_before_and_after_rename_without_duplicates(self):
        state = self._m6_state()
        normal = M7Pipeline(self.root)
        synthesis = normal.synthesize(state["receipts"], run_id=self.run_id)
        with self.assertRaises(RuntimeError):
            M7Pipeline(self.root, fault=lambda point: (_ for _ in ()).throw(RuntimeError(point)) if point == "before_rename" else None).build(synthesis, self.root / "versions/champion/v0000")
        manifest = normal.build(synthesis, self.root / "versions/champion/v0000")
        candidate = self.root / "versions/challengers" / manifest["candidate_id"]
        self.assertEqual(normal.build(synthesis, self.root / "versions/champion/v0000"), manifest)
        self.assertEqual(list((self.root / "versions/challengers").iterdir()), [candidate])

    def test_publication_recovers_when_interrupted_after_rename(self):
        state = self._m6_state()
        normal = M7Pipeline(self.root)
        synthesis = normal.synthesize(state["receipts"], run_id=self.run_id)
        with self.assertRaises(RuntimeError):
            M7Pipeline(self.root, fault=lambda point: (_ for _ in ()).throw(RuntimeError(point)) if point == "after_rename" else None).build(synthesis, self.root / "versions/champion/v0000")
        manifest = normal.build(synthesis, self.root / "versions/champion/v0000")
        self.assertEqual(list((self.root / "versions/challengers").iterdir()), [self.root / "versions/challengers" / manifest["candidate_id"]])

    def test_s20_and_w22_must_remain_canonical_m6_evidence(self):
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        manifest = pipe.build(synthesis, self.root / "versions/champion/v0000")
        # A similarly named untrusted file cannot stand in for a missing M6 receipt.
        (self.root / "S20-W22-approval.json").write_text('{"approved": true}', encoding="utf-8")
        w22 = Path(state["receipts"]["W22"]["immutable_path"])
        os.chmod(w22.parent, 0o700)
        os.unlink(w22)
        report = run_gates(self.root / "versions/challengers" / manifest["candidate_id"])
        checks = {item["gate_id"]: item["passed"] for item in report["gates"]}
        self.assertFalse(checks["math_critical_issues"])
        self.assertFalse(checks["correctness_math"])

    def test_failed_gates_leave_the_run_at_candidate_built(self):
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        store = DurableStore(self.root)
        pipe.record_synthesis(store, synthesis)
        manifest = pipe.build(synthesis, self.root / "versions/champion/v0000")
        pipe.record_candidate(store, manifest)
        w22 = Path(state["receipts"]["W22"]["immutable_path"])
        os.chmod(w22.parent, 0o700)
        os.unlink(w22)
        report = run_gates(self.root / "versions/challengers" / manifest["candidate_id"])
        with self.assertRaises(SynthesisError):
            pipe.record_gates(store, report)
        self.assertEqual(store.snapshot(self.run_id)["state"], "CANDIDATE_BUILT")

    def test_m7_never_mutates_champion_pareto_or_rejected_records(self):
        pareto = self.root / "state" / "pareto.json"
        rejected = self.root / "versions" / "rejected" / "r0001.json"
        rejected.parent.mkdir(parents=True)
        pareto.write_bytes(b'{"frontier":[]}\n')
        rejected.write_bytes(b'{"candidate":"retained"}\n')
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in (pareto, rejected, self.root / "versions/champion/v0000/manifest.json")}
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        manifest = pipe.build(synthesis, self.root / "versions/champion/v0000")
        run_gates(self.root / "versions/challengers" / manifest["candidate_id"])
        self.assertEqual(before, {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in before})

    def test_gate_report_rejects_unknown_duplicate_or_failed_report(self):
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        store = DurableStore(self.root)
        pipe.record_synthesis(store, synthesis)
        manifest = pipe.build(synthesis, self.root / "versions/champion/v0000")
        pipe.record_candidate(store, manifest)
        report = run_gates(self.root / "versions/challengers" / manifest["candidate_id"])
        forged = json.loads(json.dumps(report)); forged["gates"][1]["gate_id"] = forged["gates"][0]["gate_id"]
        with self.assertRaises(SynthesisError): pipe.record_gates(store, forged)
        forged = json.loads(json.dumps(report)); forged["overall_pass"] = False
        with self.assertRaises(SynthesisError): pipe.record_gates(store, forged)


class M7ParetoTests(unittest.TestCase):
    def test_eight_dimensions_are_componentwise_and_cost_is_only_a_tiebreak(self):
        left = {"correctness_math_pass": False, "issues": [], "pareto_vector": [5, 0, 0, 0, 0, 0, 0, 0], "cost": 1}
        right = {"correctness_math_pass": False, "issues": [], "pareto_vector": [0, 5, 0, 0, 0, 0, 0, 0], "cost": 2}
        self.assertEqual(compare(left, right)["relation"], "incomparable")
        equal = {**left, "pareto_vector": [1] * 8, "cost": 9}
        self.assertEqual(compare(equal, {**equal, "cost": 1})["relation"], "right_dominates")
        with self.assertRaises(ValueError): compare(left, {**right, "pareto_vector": [0] * 7})
        with self.assertRaises(ValueError): compare(left, {**right, "pareto_vector": [0] * 7 + [float("nan")]})

    def test_scientific_priority_precedes_dimensions_without_authorizing_promotion(self):
        critical = {"correctness_math_pass": False, "issues": [{"severity": "CRITICAL"}], "pareto_vector": [100] * 8, "cost": 0}
        sound = {"correctness_math_pass": True, "issues": [], "pareto_vector": [0] * 8, "cost": 100}
        result = compare(critical, sound)
        self.assertEqual(result["relation"], "right_dominates")
        self.assertFalse(result["promotion_authorized"])
