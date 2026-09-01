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
import zipfile

import jsonschema

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))

from article_loop import FakeRLMAdapter, Orchestrator, ingest
from article_loop.activation import ActivationPlanner
from article_loop.blackboard import Blackboard, Impact
from article_loop.gates import REQUIRED_GATES, compare, record_math_verification, run_gates
from article_loop.state_machine import State
from article_loop.store import DurableStore, IntegrityError
from article_loop.synthesis import M7Pipeline, SynthesisError, tree_hash


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
        with zipfile.ZipFile(self.root / "input/inbox/source.zip", "w") as archive:
            archive.writestr(
                "paper.tex",
                "\\documentclass{article}\n\\begin{document}\nFixture $x=1$.\\label{fixture}\n\\end{document}\n",
            )
        ingest(self.root)
        self.fake = FakeRLMAdapter()
        self.orchestrator = Orchestrator(self.root, self.fake)
        self.initial = asyncio.run(self.orchestrator.bootstrap(self.pdf))
        self.run_id = self.initial["run_id"]
        claim = Blackboard(self.root).append(self.run_id, "claims", {
            "text": "Fixture theorem", "type": "theorem", "location": {"page": 1, "section": "proof"},
            "dependencies": [], "evidence": ["page:1"], "status": "active", "severity": 10,
            "source_hash": self.initial["base_hash"], "last_validated_cycle": 0,
        })
        self.claim_id = claim["claim_id"]
        impact = Impact(claims=(self.claim_id,), sections=("section:proof",), equations=("equation:1",), references=("reference:1",), roles=tuple(f"W{i}{j}" for i in range(1, 6) for j in range(1, 4)), severity=10)
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
        value = f"M6 evidence for {role}\n"
        return {
            "schema_version": "1.1.0", "proposal_id": f"p-{role}", "role_id": role, "cycle_id": 0,
            "base_hash": self.initial["base_hash"], "scope": ["proof"], "evidence_locators": ["page:1"],
            "patch_or_operations": {"kind": "operations", "operations": [{"op": "add", "target": target, "value": value}]},
            "affected_claims": [self.claim_id] if role == "W22" else [], "dependencies": [],
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

    def _approve(self, candidate):
        return record_math_verification(
            candidate, claim_id=self.claim_id, proposal_id="p-W22", verifier_id="local-fixture",
            verifier_version="1.0.0", method="manual-proof-check", summary="Fixture identity checked independently.",
        )

    def _candidate_state(self, *, approve=False):
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        store = DurableStore(self.root)
        pipe.record_synthesis(store, synthesis)
        manifest = pipe.build(synthesis, self.root / "versions/champion/v0000")
        pipe.record_candidate(store, manifest)
        candidate = self.root / "versions/challengers" / manifest["candidate_id"]
        if approve:
            self._approve(candidate)
        return state, pipe, store, manifest, candidate

    @staticmethod
    def _canonical(value):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

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
        approval = self._approve(candidate)
        self.assertEqual(approval["claim_id"], self.claim_id)
        self.assertFalse(any(path.stat().st_mode & 0o222 for path in candidate.rglob("*")))
        self.assertFalse(candidate.stat().st_mode & 0o222)
        self.assertNotEqual((champion / "baseline.pdf").stat().st_ino, (candidate / "baseline.pdf").stat().st_ino)
        self.assertTrue((candidate / "latex-source/paper.tex").is_file())
        report = pipe.execute_and_record_gates(store, candidate)
        self.assertTrue(report["overall_pass"], report)
        jsonschema.validate(report, json.loads((self.root / "config/schemas/gate-report.schema.json").read_text()))
        self.assertEqual(tuple(item["gate_id"] for item in report["gates"]), REQUIRED_GATES)
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
        os.chmod(candidate / "evidence/w11.txt", 0o644)
        with self.assertRaises(Exception):
            pipe.build(synthesis, self.root / "versions/champion/v0000")

    def test_writable_published_root_is_rejected(self):
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        manifest = pipe.build(synthesis, self.root / "versions/champion/v0000")
        candidate = self.root / "versions/challengers" / manifest["candidate_id"]
        os.chmod(candidate, 0o755)
        try:
            with self.assertRaises(IntegrityError):
                pipe.build(synthesis, self.root / "versions/champion/v0000")
        finally:
            os.chmod(candidate, 0o555)

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
        store = DurableStore(self.root)
        pipe.record_synthesis(store, synthesis)
        manifest = pipe.build(synthesis, self.root / "versions/champion/v0000")
        pipe.record_candidate(store, manifest)
        candidate = self.root / "versions/challengers" / manifest["candidate_id"]
        self._approve(candidate)

        class LyingAdapter:
            def __getattr__(self, name):
                raise AssertionError(f"gate adapter was consulted: {name}")

        report = run_gates(candidate, adapter=LyingAdapter())
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

    def test_publication_recovers_when_interrupted_after_parent_fsync(self):
        state = self._m6_state()
        normal = M7Pipeline(self.root)
        synthesis = normal.synthesize(state["receipts"], run_id=self.run_id)
        with self.assertRaises(RuntimeError):
            M7Pipeline(self.root, fault=lambda point: (_ for _ in ()).throw(RuntimeError(point)) if point == "after_parent_fsync" else None).build(synthesis, self.root / "versions/champion/v0000")
        manifest = normal.build(synthesis, self.root / "versions/champion/v0000")
        candidate = self.root / "versions/challengers" / manifest["candidate_id"]
        self.assertFalse(candidate.stat().st_mode & 0o222)
        self.assertEqual(list((self.root / "versions/challengers").iterdir()), [candidate])

    def test_candidate_event_retry_is_exactly_once_around_both_fault_points(self):
        state = self._m6_state()
        normal = M7Pipeline(self.root)
        synthesis = normal.synthesize(state["receipts"], run_id=self.run_id)
        store = DurableStore(self.root)
        normal.record_synthesis(store, synthesis)
        manifest = normal.build(synthesis, self.root / "versions/champion/v0000")
        for fault_point, expected_after_fault in (("before_candidate_built_event", "SYNTHESIS_READY"),
                                                  ("after_candidate_built_event", "CANDIDATE_BUILT")):
            faulty = M7Pipeline(
                self.root,
                fault=lambda point, target=fault_point: (_ for _ in ()).throw(RuntimeError(point)) if point == target else None,
            )
            with self.assertRaises(RuntimeError):
                faulty.record_candidate(store, manifest)
            self.assertEqual(store.snapshot(self.run_id)["state"], expected_after_fault)
            normal.record_candidate(store, manifest)
            events = [event for event in store.read_events(self.run_id) if event["state_to"] == "CANDIDATE_BUILT"]
            self.assertEqual(len(events), 1)

    def test_request_and_similarly_named_file_do_not_count_as_math_approval(self):
        _, _, _, _, candidate = self._candidate_state()
        # A canonical W22 request and a suggestive filename are still not an approval.
        (self.root / "S20-W22-approval.json").write_text('{"approved": true}', encoding="utf-8")
        report = run_gates(candidate)
        checks = {item["gate_id"]: item["passed"] for item in report["gates"]}
        self.assertTrue(checks["math_critical_issues"])
        self.assertFalse(checks["correctness_math"])

    def test_failed_gates_leave_the_run_at_candidate_built(self):
        _, pipe, store, _, candidate = self._candidate_state()
        report = run_gates(candidate)
        with self.assertRaises(SynthesisError):
            pipe.record_gates(store, report["report_locator"])
        self.assertEqual(store.snapshot(self.run_id)["state"], "CANDIDATE_BUILT")

    def test_candidate_built_event_must_bind_the_exact_published_candidate(self):
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        store = DurableStore(self.root)
        pipe.record_synthesis(store, synthesis)
        manifest = pipe.build(synthesis, self.root / "versions/champion/v0000")
        store.record(
            self.run_id, State.CANDIDATE_BUILT,
            event_id="fixture:wrong-candidate", idempotency_key="fixture:wrong-candidate",
            actor_id="fixture", event_type="M7_ARTIFACT",
            payload={"candidate_id": "c-wrong", "candidate_hash": "0" * 64},
            artifact_hashes=["0" * 64],
        )
        candidate = self.root / "versions/challengers" / manifest["candidate_id"]
        self._approve(candidate)
        report = run_gates(candidate)
        checks = {gate["gate_id"]: gate["passed"] for gate in report["gates"]}
        self.assertFalse(checks["contracts_state"])
        with self.assertRaises(SynthesisError):
            pipe.record_gates(store, report["report_locator"])
        self.assertEqual(store.snapshot(self.run_id)["state"], "CANDIDATE_BUILT")

    def test_m7_never_mutates_champion_pareto_or_rejected_records(self):
        pareto = self.root / "state" / "pareto.json"
        rejected = self.root / "versions" / "rejected" / "r0001.json"
        rejected.parent.mkdir(parents=True)
        pareto.write_bytes(b'{"frontier":[]}\n')
        rejected.write_bytes(b'{"candidate":"retained"}\n')
        champion = self.root / "versions/champion/v0000"
        before = {
            "champion": tree_hash(champion),
            "pareto": hashlib.sha256(pareto.read_bytes()).hexdigest(),
            "rejected": hashlib.sha256(rejected.read_bytes()).hexdigest(),
        }
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        manifest = pipe.build(synthesis, self.root / "versions/champion/v0000")
        run_gates(self.root / "versions/challengers" / manifest["candidate_id"])
        self.assertEqual(before, {
            "champion": tree_hash(champion),
            "pareto": hashlib.sha256(pareto.read_bytes()).hexdigest(),
            "rejected": hashlib.sha256(rejected.read_bytes()).hexdigest(),
        })

    def test_forged_persisted_gate_report_cannot_advance_state(self):
        _, pipe, store, manifest, candidate = self._candidate_state(approve=True)
        report = run_gates(candidate)
        self.assertTrue(report["overall_pass"])
        forged = json.loads(json.dumps(report))
        forged["gates"][0].update({"passed": False, "exit_code": 99, "command": "false"})
        forged["overall_pass"] = True
        for field in ("report_hash", "report_id", "report_locator"):
            forged.pop(field)
        digest = hashlib.sha256(self._canonical(forged)).hexdigest()
        forged["report_hash"] = digest
        forged["report_id"] = "g-" + digest[:32]
        forged["report_locator"] = f"state/gates/{manifest['candidate_id']}/{digest}.json"
        path = self.root / forged["report_locator"]
        path.write_bytes(self._canonical(forged))
        with self.assertRaises(SynthesisError):
            pipe.record_gates(store, forged["report_locator"])
        self.assertEqual(store.snapshot(self.run_id)["state"], "CANDIDATE_BUILT")

    def test_entirely_forged_mapping_without_run_gates_is_rejected(self):
        _, pipe, store, _, _ = self._candidate_state()
        with self.assertRaises(SynthesisError):
            pipe.record_gates(store, {"overall_pass": True, "correctness_math_pass": True})
        self.assertEqual(store.snapshot(self.run_id)["state"], "CANDIDATE_BUILT")

    def test_bad_math_evidence_locator_fails_correctness_gate(self):
        _, _, _, manifest, candidate = self._candidate_state(approve=True)
        directory = self.root / "state/math-verifications" / manifest["candidate_id"]
        original = next(directory.glob("*.json"))
        verification = json.loads(original.read_bytes())
        verification["evidence_locator"] = f"state/math-evidence/{manifest['candidate_id']}/{'0' * 64}.json"
        for field in ("verification_hash", "verification_id", "verification_locator"):
            verification.pop(field)
        digest = hashlib.sha256(self._canonical(verification)).hexdigest()
        verification["verification_hash"] = digest
        verification["verification_id"] = "mv-" + digest[:32]
        verification["verification_locator"] = f"state/math-verifications/{manifest['candidate_id']}/{digest}.json"
        os.unlink(original)
        (self.root / verification["verification_locator"]).write_bytes(self._canonical(verification))
        report = run_gates(candidate)
        self.assertFalse({gate["gate_id"]: gate["passed"] for gate in report["gates"]}["correctness_math"])

    def test_persisted_open_critical_math_issue_fails_gate(self):
        _, _, _, manifest, candidate = self._candidate_state(approve=True)
        Blackboard(self.root).append(self.run_id, "issues", {
            "record_id": "issue-critical-fixture", "issue_type": "math", "run_id": self.run_id,
            "cycle_id": 0, "base_hash": manifest["base_hash"], "candidate_id": manifest["candidate_id"],
            "claim_id": self.claim_id, "severity": "CRITICAL", "status": "open",
            "summary": "Unresolved fixture objection", "evidence_locators": ["page:1"],
        })
        report = run_gates(candidate)
        checks = {gate["gate_id"]: gate["passed"] for gate in report["gates"]}
        self.assertFalse(checks["math_critical_issues"])
        self.assertFalse(report["overall_pass"])


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
