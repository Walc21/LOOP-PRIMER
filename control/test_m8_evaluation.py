"""Comprehensive, offline, deterministic tests for M8 external blind evaluation."""
from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime/agent/skills/article-loop/src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop import (
    DurableStore,
    FakeRLMAdapter,
    IntegrityError,
    M7Pipeline,
    Orchestrator,
    State,
    ingest,
    tree_hash,
)
from article_loop.activation import ActivationPlanner
from article_loop.blackboard import Blackboard, Impact
from article_loop.gates import REQUIRED_GATES, record_math_verification, run_gates
from article_loop.evaluation import (
    DIMENSIONS,
    BlindComparisonBundle,
    EvaluationError,
    FakeJurorAdapter,
    FakeMetaReviewerAdapter,
    check_inversion_consistency,
    evaluate_candidate,
    load_rubric,
    sanitize_text,
)


class DummyOperationalJurorAdapter:
    """Mock operational adapter (not a test double) for testing meta double enforcement."""
    is_test_double: bool = False

    def __init__(self, juror_id: str):
        self.juror_id = juror_id

    def evaluate(self, presentation: dict[str, Any]) -> dict[str, Any]:
        return {}


class M8EvaluationTests(unittest.TestCase):
    """Exhaustive test suite for M8 blind jury evaluation and meta-review."""

    @classmethod
    def setUpClass(cls):
        cls.fixture_dir = tempfile.TemporaryDirectory()
        fixture = Path(cls.fixture_dir.name)
        ps = fixture / "fixture.ps"
        ps.write_text(
            "%!PS\n/Courier findfont 18 scalefont setfont 72 700 moveto (M8 fixture) show showpage\n",
            encoding="utf-8",
        )
        cls.fixture_pdf = fixture / "fixture.pdf"
        subprocess.run(
            ["gs", "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", f"-sOutputFile={cls.fixture_pdf}", str(ps)],
            check=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.fixture_dir.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for relative in (
            "input/inbox",
            "artifacts/original",
            "artifacts/extracted",
            "artifacts/rendered",
            "versions/champion",
            "workspaces",
            "state",
        ):
            (self.root / relative).mkdir(parents=True, exist_ok=True)
        shutil.copytree(ROOT / "config", self.root / "config", dirs_exist_ok=True)
        shutil.copytree(ROOT / "prompts", self.root / "prompts")
        self.pdf = self.root / "input/inbox/artigo.pdf"
        shutil.copyfile(self.fixture_pdf, self.pdf)
        with zipfile.ZipFile(self.root / "input/inbox/source.zip", "w") as archive:
            archive.writestr(
                "paper.tex",
                "\\documentclass{article}\n\\begin{document}\nFixture paper $x=1$.\\label{fixture}\n\\end{document}\n",
            )
        ingest(self.root)
        self.fake = FakeRLMAdapter()
        self.orchestrator = Orchestrator(self.root, self.fake)
        self.initial = asyncio.run(self.orchestrator.bootstrap(self.pdf))
        self.run_id = self.initial["run_id"]

        # Setup blackboard claim and impact
        claim = Blackboard(self.root).append(self.run_id, "claims", {
            "text": "Fixture theorem", "type": "theorem", "location": {"page": 1, "section": "proof"},
            "dependencies": [], "evidence": ["page:1"], "status": "active", "severity": 10,
            "source_hash": self.initial["base_hash"], "last_validated_cycle": 0,
        })
        self.claim_id = claim["claim_id"]
        impact = Impact(
            claims=(self.claim_id,),
            sections=("section:proof",),
            equations=("equation:1",),
            references=("reference:1",),
            roles=tuple(f"W{i}{j}" for i in range(1, 6) for j in range(1, 4)),
            severity=10,
        )
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
        value = f"M8 evidence for {role}\n"
        return {
            "schema_version": "1.1.0", "proposal_id": f"p-{role}", "role_id": role, "cycle_id": 0,
            "base_hash": self.initial["base_hash"], "scope": ["proof"], "evidence_locators": ["page:1"],
            "patch_or_operations": {"kind": "operations", "operations": [{"op": "add", "target": target, "value": value}]},
            "affected_claims": [self.claim_id] if role == "W22" else [], "dependencies": [],
            "risk": {"level": "low", "factors": [], "technical_effect_possible": False}, "confidence": 1,
            "requested_validations": ["correctness_math"] if role == "W22" else [], "prompt_version": "m8-integration",
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

    def _setup_m7_gates_passed(self, champion: Path | None = None) -> dict[str, Any]:
        """Run pipeline through M6 and M7 up to GATES_PASSED."""
        state = self._m6_state()
        pipe = M7Pipeline(self.root)
        synthesis = pipe.synthesize(state["receipts"], run_id=self.run_id)
        store = DurableStore(self.root)
        pipe.record_synthesis(store, synthesis)
        champion = champion or self.root / "versions/champion/v0000"
        manifest = pipe.build(synthesis, champion)
        pipe.record_candidate(store, manifest)
        candidate = self.root / "versions/challengers" / manifest["candidate_id"]
        self._approve(candidate)
        report = pipe.execute_and_record_gates(store, candidate)
        return {
            "synthesis": synthesis,
            "candidate": manifest,
            "gate_report": report,
        }

    def _default_test_adapters(self, preferred_winner: str = "B"):
        jurors = {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", specialty="correctness_math", preferred_winner=preferred_winner),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib", specialty="scientific_contribution", preferred_winner=preferred_winner),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity", specialty="clarity", preferred_winner=preferred_winner),
        }
        meta = FakeMetaReviewerAdapter()
        return jurors, meta

    # ==================== 1. Sanitization and Blinding Tests ====================

    def test_sanitize_text_strips_authors_versions_and_roles(self):
        text = (
            "\\author[Short]{Alice \\thanks{alice@example.org} \\and Bob}\n"
            "Affiliation: Identifying University\n"
            "ORCID: https://orcid.org/0000-0002-1825-0097\n"
            "Role S20 and specialist W22 modified v00001 for champion and challenger "
            "in run-abc12345 cycle_0 in workspaces/run-1/cycle-0/W22."
        )
        sanitized = sanitize_text(text)
        self.assertNotIn("Alice", sanitized)
        self.assertNotIn("Bob", sanitized)
        self.assertNotIn("University", sanitized)
        self.assertNotIn("alice@example.org", sanitized)
        self.assertNotIn("0000-0002-1825-0097", sanitized)
        self.assertNotIn("S20", sanitized)
        self.assertNotIn("W22", sanitized)
        self.assertNotIn("v00001", sanitized)
        self.assertNotIn("champion", sanitized.lower())
        self.assertNotIn("challenger", sanitized.lower())
        self.assertNotIn("run-abc12345", sanitized)
        self.assertNotIn("workspaces", sanitized)

    def test_blind_bundle_reproducibility_and_bijective_order(self):
        m7_out = self._setup_m7_gates_passed()
        champ_dir = self.root / "versions/champion/v0000"
        chall_dir = self.root / "versions/challengers" / m7_out["candidate"]["candidate_id"]

        bundle1 = BlindComparisonBundle.create(self.root, champion_dir=champ_dir, challenger_dir=chall_dir, order_seed=413)
        bundle2 = BlindComparisonBundle.create(self.root, champion_dir=champ_dir, challenger_dir=chall_dir, order_seed=413)
        self.assertEqual(bundle1.comparison_id, bundle2.comparison_id)

        pres_ab = bundle1.presentation_for_order(["A", "B"])
        pres_ba = bundle1.presentation_for_order(["B", "A"])

        self.assertEqual(pres_ab["first_candidate"]["neutral_id"], "A")
        self.assertEqual(pres_ab["second_candidate"]["neutral_id"], "B")
        self.assertEqual(pres_ba["first_candidate"]["neutral_id"], "B")
        self.assertEqual(pres_ba["second_candidate"]["neutral_id"], "A")

        self.assertEqual(pres_ab["first_candidate"]["content_hash"], bundle1.content_hashes[0])
        self.assertEqual(pres_ba["first_candidate"]["content_hash"], bundle1.content_hashes[1])

    def test_blind_bundle_sanitizes_filenames_and_metadata(self):
        m7_out = self._setup_m7_gates_passed()
        champ_dir = self.root / "versions/champion/v0000"
        chall_dir = self.root / "versions/challengers" / m7_out["candidate"]["candidate_id"]

        bundle = BlindComparisonBundle.create(self.root, champion_dir=champ_dir, challenger_dir=chall_dir, order_seed=413)
        pres_ab = bundle.presentation_for_order(["A", "B"])

        # Check candidate file keys
        for cand_key in ("first_candidate", "second_candidate"):
            files = pres_ab[cand_key]["content"]["files"]
            for fname in files.keys():
                self.assertNotIn("W22", fname)
                self.assertNotIn("S20", fname)
                self.assertNotIn("v0000", fname)
                self.assertNotIn("v0001", fname)
                self.assertNotIn("champion", fname.lower())
                self.assertNotIn("challenger", fname.lower())
                self.assertRegex(fname, r"^document_\d{4}\.(tex|txt|bib)$")

    def test_evaluation_uses_challenger_bound_champion_not_v0000(self):
        promoted = self.root / "versions/champion/v0001"
        shutil.copytree(self.root / "versions/champion/v0000", promoted)
        promoted_manifest_path = promoted / "manifest.json"
        os.chmod(promoted_manifest_path, 0o644)
        promoted_manifest = json.loads(promoted_manifest_path.read_text(encoding="utf-8"))
        promoted_manifest["candidate_id"] = "v0001"
        promoted_manifest_path.write_text(json.dumps(promoted_manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.chmod(promoted_manifest_path, 0o444)

        m7_out = self._setup_m7_gates_passed(champion=promoted)
        legacy = self.root / "versions/champion/v0000/baseline.pdf"
        os.chmod(legacy, 0o644)
        legacy.write_bytes(b"obsolete champion must not be read")
        jurors, meta = self._default_test_adapters("B")
        report = evaluate_candidate(
            self.root,
            self.run_id,
            candidate_id=m7_out["candidate"]["candidate_id"],
            juror_adapters=jurors,
            meta_adapter=meta,
            allow_test_doubles=True,
        )
        self.assertEqual(report["base_hash"], promoted_manifest["content_hash"])

    def test_evaluation_rejects_invalid_order_seed_and_adapter_sets(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters()
        for invalid_seed in (-1, True, 1.5, "413"):
            with self.subTest(seed=invalid_seed):
                with self.assertRaisesRegex(EvaluationError, "order_seed"):
                    evaluate_candidate(
                        self.root, self.run_id, candidate_id=candidate_id,
                        order_seed=invalid_seed, juror_adapters=jurors, meta_adapter=meta,
                        allow_test_doubles=True,
                    )
        extra = dict(jurors)
        extra["juror-extra"] = FakeJurorAdapter(juror_id="juror-extra")
        with self.assertRaisesRegex(EvaluationError, "exactly the three canonical"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=extra, meta_adapter=meta, allow_test_doubles=True,
            )
        with self.assertRaisesRegex(EvaluationError, "juror_adapters must be an object"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=[], meta_adapter=meta, allow_test_doubles=True,
            )
        with self.assertRaisesRegex(EvaluationError, "model_families must be an object"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, model_families=[],
                allow_test_doubles=True,
            )
        with self.assertRaisesRegex(EvaluationError, "run_id must be a non-empty string"):
            evaluate_candidate(
                self.root, True, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True,
            )

    # ==================== 2. Inversion Consistency Tests ====================

    def test_inversion_consistency_consistent_winner(self):
        adapter = FakeJurorAdapter(juror_id="juror-math", preferred_winner="B")
        pres_ab = {"presentation_order": ["A", "B"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["a" * 64, "b" * 64]}
        pres_ba = {"presentation_order": ["B", "A"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["b" * 64, "a" * 64]}

        v_ab = adapter.evaluate(pres_ab)
        v_ba = adapter.evaluate(pres_ba)

        consistent, reason, winner, math_pass = check_inversion_consistency(v_ab, v_ba)
        self.assertTrue(consistent)
        self.assertIsNone(reason)
        self.assertEqual(winner, "B")
        self.assertTrue(math_pass)

    def test_inversion_consistency_detects_first_position_bias(self):
        adapter = FakeJurorAdapter(juror_id="juror-math", positional_bias="first")
        pres_ab = {"presentation_order": ["A", "B"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["a" * 64, "b" * 64]}
        pres_ba = {"presentation_order": ["B", "A"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["b" * 64, "a" * 64]}

        v_ab = adapter.evaluate(pres_ab)  # picks A
        v_ba = adapter.evaluate(pres_ba)  # picks B

        consistent, reason, winner, math_pass = check_inversion_consistency(v_ab, v_ba)
        self.assertFalse(consistent)
        self.assertEqual(reason, "first_position_bias")
        self.assertIsNone(winner)

    def test_inversion_consistency_detects_second_position_bias(self):
        adapter = FakeJurorAdapter(juror_id="juror-math", positional_bias="second")
        pres_ab = {"presentation_order": ["A", "B"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["a" * 64, "b" * 64]}
        pres_ba = {"presentation_order": ["B", "A"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["b" * 64, "a" * 64]}

        v_ab = adapter.evaluate(pres_ab)  # picks B
        v_ba = adapter.evaluate(pres_ba)  # picks A

        consistent, reason, winner, math_pass = check_inversion_consistency(v_ab, v_ba)
        self.assertFalse(consistent)
        self.assertEqual(reason, "second_position_bias")
        self.assertIsNone(winner)

    def test_inversion_consistency_detects_inconsistent_math_verification(self):
        pres_ab = {"presentation_order": ["A", "B"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["a" * 64, "b" * 64]}
        pres_ba = {"presentation_order": ["B", "A"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["b" * 64, "a" * 64]}

        v_ab = FakeJurorAdapter(juror_id="juror-math", math_pass=(True, True)).evaluate(pres_ab)
        v_ba = FakeJurorAdapter(juror_id="juror-math", math_pass=(True, False)).evaluate(pres_ba)

        consistent, reason, winner, math_pass = check_inversion_consistency(v_ab, v_ba)
        self.assertFalse(consistent)
        self.assertEqual(reason, "inconsistent_math_verification")

    def test_inversion_consistency_rejects_score_drift_even_for_ties(self):
        adapter = FakeJurorAdapter(juror_id="juror-math", preferred_winner="tie")
        pres_ab = {"presentation_order": ["A", "B"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["a" * 64, "b" * 64]}
        pres_ba = {"presentation_order": ["B", "A"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["a" * 64, "b" * 64]}
        verdict_ab = adapter.evaluate(pres_ab)
        verdict_ba = adapter.evaluate(pres_ba)
        verdict_ba["dimension_scores"][1]["clarity"] = 1

        consistent, reason, winner, math_pass = check_inversion_consistency(verdict_ab, verdict_ba)

        self.assertFalse(consistent)
        self.assertEqual(reason, "dimension_score_drift:clarity")
        self.assertIsNone(winner)
        self.assertTrue(math_pass)

    def test_inversion_consistency_detects_duplicate_verdict_id(self):
        pres_ab = {"presentation_order": ["A", "B"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["a" * 64, "b" * 64]}
        pres_ba = {"presentation_order": ["B", "A"], "comparison_id": "cmp-1", "order_seed": 413, "content_hashes": ["b" * 64, "a" * 64]}

        v_ab = FakeJurorAdapter(juror_id="juror-math", reused_verdict_id="v-reused-123").evaluate(pres_ab)
        v_ba = FakeJurorAdapter(juror_id="juror-math", reused_verdict_id="v-reused-123").evaluate(pres_ba)

        consistent, reason, winner, math_pass = check_inversion_consistency(v_ab, v_ba)
        self.assertFalse(consistent)
        self.assertEqual(reason, "duplicate_verdict_id_for_both_orders")

    # ==================== 3. Operational Boundary & CLI Tests ====================

    def test_evaluate_candidate_fails_closed_without_adapters(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        with self.assertRaisesRegex(EvaluationError, "no operational juror adapter configured"):
            evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id)

    def test_unauthorized_fake_juror_adapter_fails_closed(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters()

        with self.assertRaisesRegex(EvaluationError, "test double detected for juror adapter.*allow_test_doubles=True"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=False
            )

    def test_unauthorized_fake_meta_reviewer_adapter_fails_closed(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        meta = FakeMetaReviewerAdapter()
        operational_jurors = {
            "juror-math": DummyOperationalJurorAdapter("juror-math"),
            "juror-contrib": DummyOperationalJurorAdapter("juror-contrib"),
            "juror-clarity": DummyOperationalJurorAdapter("juror-clarity"),
        }

        with self.assertRaisesRegex(EvaluationError, "test double detected for meta-reviewer adapter.*allow_test_doubles=True"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=operational_jurors, meta_adapter=meta, allow_test_doubles=False
            )

    def test_unauthorized_test_doubles_do_not_publish_artifacts(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters()

        try:
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=False
            )
        except EvaluationError:
            pass

        eval_dir = self.root / f"state/evaluations/{self.run_id}"
        self.assertTrue(not eval_dir.exists() or list(eval_dir.iterdir()) == [])

    def test_cli_fails_closed_without_test_mode(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        cli_script = ROOT / "scripts/01_external_evaluator.py"
        res = subprocess.run(
            [sys.executable, str(cli_script), "--root", str(self.root), "--run-id", self.run_id, "--candidate-id", candidate_id],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 2)
        err = json.loads(res.stderr)
        self.assertEqual(err["status"], "error")
        self.assertIn("no operational juror adapter configured", err["message"])

        eval_dir = self.root / f"state/evaluations/{self.run_id}"
        self.assertTrue(not eval_dir.exists() or list(eval_dir.iterdir()) == [])

    def test_evaluator_cli_rejects_non_object_json_without_traceback(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/01_external_evaluator.py"), "--input", "-"],
            input="[]",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stderr)["error_type"], "input_parsing_error")
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_fails_closed_when_test_mode_injected_via_input_json_true(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        cli_script = ROOT / "scripts/01_external_evaluator.py"
        input_payload = {
            "root": str(self.root),
            "run_id": self.run_id,
            "candidate_id": candidate_id,
            "test_mode": True,
        }
        res = subprocess.run(
            [sys.executable, str(cli_script), "--input", "-"],
            input=json.dumps(input_payload),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 2)
        err = json.loads(res.stderr)
        self.assertEqual(err["status"], "error")
        self.assertIn("no operational juror adapter configured", err["message"])

        eval_dir = self.root / f"state/evaluations/{self.run_id}"
        self.assertTrue(not eval_dir.exists() or list(eval_dir.iterdir()) == [])

    def test_cli_fails_closed_when_test_mode_injected_via_input_json_string_false(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        cli_script = ROOT / "scripts/01_external_evaluator.py"
        input_payload = {
            "root": str(self.root),
            "run_id": self.run_id,
            "candidate_id": candidate_id,
            "test_mode": "false",
        }
        res = subprocess.run(
            [sys.executable, str(cli_script), "--input", "-"],
            input=json.dumps(input_payload),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 2)
        err = json.loads(res.stderr)
        self.assertEqual(err["status"], "error")
        self.assertIn("no operational juror adapter configured", err["message"])

        eval_dir = self.root / f"state/evaluations/{self.run_id}"
        self.assertTrue(not eval_dir.exists() or list(eval_dir.iterdir()) == [])

    def test_api_rejects_non_boolean_allow_test_doubles(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters()

        for invalid_val in ("false", "true", 1, 0, {}, [], None):
            with self.subTest(invalid_val=invalid_val):
                with self.assertRaisesRegex(EvaluationError, "allow_test_doubles must be a boolean"):
                    evaluate_candidate(
                        self.root, self.run_id, candidate_id=candidate_id,
                        juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=invalid_val  # type: ignore[arg-type]
                    )

        eval_dir = self.root / f"state/evaluations/{self.run_id}"
        self.assertTrue(not eval_dir.exists() or list(eval_dir.iterdir()) == [])

    def test_cli_succeeds_with_explicit_test_mode(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        cli_script = ROOT / "scripts/01_external_evaluator.py"
        res = subprocess.run(
            [
                sys.executable, str(cli_script), "--root", str(self.root), "--run-id", self.run_id,
                "--candidate-id", candidate_id, "--test-mode", "--test-winner", "B",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["report"]["overall_outcome"], "challenger_favored")

    # ==================== 4. Semantic Validation Tests ====================

    def test_verdict_semantic_validation_rejects_repeated_order_attack(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        # Juror returns A/B for both A/B and B/A presentations
        adapters = {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", repeat_order=["A", "B"]),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib"),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity"),
        }
        meta = FakeMetaReviewerAdapter()

        with self.assertRaisesRegex(EvaluationError, "presentation_order.*does not match requested"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=adapters, meta_adapter=meta, allow_test_doubles=True
            )

    def test_verdict_semantic_validation_rejects_reused_verdict_id_across_jurors(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        # Jurors return the exact same verdict_id
        adapters = {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", reused_verdict_id="v-static-id-001"),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib", reused_verdict_id="v-static-id-001"),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity"),
        }
        meta = FakeMetaReviewerAdapter()

        with self.assertRaisesRegex(EvaluationError, "duplicate verdict_id detected"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=adapters, meta_adapter=meta, allow_test_doubles=True
            )

    def test_verdict_semantic_validation_rejects_nan_scores(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        adapters, meta = self._default_test_adapters(preferred_winner="B")
        adapters["juror-math"] = FakeJurorAdapter(
            juror_id="juror-math",
            preferred_winner="B",
            base_scores=(float("nan"), 4),
        )

        with self.assertRaisesRegex(EvaluationError, "number between 0 and 5|invalid jury-verdict"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=adapters, meta_adapter=meta, allow_test_doubles=True,
            )

    def test_meta_verdict_validation_rejects_conflicting_confirmed_and_vetoed(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        jurors, _ = self._default_test_adapters()

        class BadMetaReviewer:
            is_test_double = True

            def review(self, **kwargs):
                return {
                    "schema_version": "1.1.0",
                    "meta_verdict_id": "meta-bad",
                    "meta_reviewer_id": "meta-reviewer",
                    "comparison_id": kwargs["comparison_id"],
                    "gate_report_id": kwargs["gate_report_summary"]["report_id"],
                    "confirmed": True,
                    "vetoed": True,
                    "veto_reason": "Conflicting state",
                    "consistent_verdict_count": len(kwargs["consistent_verdicts"]),
                    "divergence_count": len(kwargs["divergences"]),
                    "explanation": "Bad meta-review",
                    "evidence_locators": ["locators/meta.txt"],
                    "reviewed_at": "2026-08-28T00:00:00Z",
                }

        with self.assertRaisesRegex(EvaluationError, "invalid meta-verdict.schema.json|cannot be both confirmed and vetoed"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=BadMetaReviewer(), allow_test_doubles=True
            )

    def test_meta_verdict_validation_rejects_mismatched_counts(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        jurors, _ = self._default_test_adapters()

        class CountLyingMetaReviewer:
            is_test_double = True

            def review(self, **kwargs):
                return {
                    "schema_version": "1.1.0",
                    "meta_verdict_id": "meta-lying",
                    "meta_reviewer_id": "meta-reviewer",
                    "comparison_id": kwargs["comparison_id"],
                    "gate_report_id": kwargs["gate_report_summary"]["report_id"],
                    "confirmed": True,
                    "vetoed": False,
                    "veto_reason": None,
                    "consistent_verdict_count": 0,  # Lies about consistent count (should be 3)
                    "divergence_count": 3,
                    "explanation": "Lying counts",
                    "evidence_locators": ["locators/meta.txt"],
                    "reviewed_at": "2026-08-28T00:00:00Z",
                }

        with self.assertRaisesRegex(EvaluationError, "consistent_verdict_count does not match"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=CountLyingMetaReviewer(), allow_test_doubles=True
            )

    # ==================== 5. GateReport & Event Binding Tests ====================

    def test_evaluation_fails_if_state_not_gates_passed(self):
        jurors, meta = self._default_test_adapters()
        with self.assertRaisesRegex(EvaluationError, "evaluation requires state GATES_PASSED"):
            evaluate_candidate(self.root, self.run_id, juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True)

    def test_evaluation_fails_if_cycle_id_diverges(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters()

        with self.assertRaisesRegex(EvaluationError, "cycle_id 99 diverges from active GATES_PASSED event"):
            evaluate_candidate(
                self.root, self.run_id, cycle_id=99, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True
            )

    def test_evaluation_fails_if_candidate_id_diverges(self):
        self._setup_m7_gates_passed()
        jurors, meta = self._default_test_adapters()

        with self.assertRaisesRegex(EvaluationError, "candidate_id 'c-fake-123' diverges"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id="c-fake-123",
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True
            )

    def test_evaluation_fails_if_gate_report_locator_diverges(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters()

        with self.assertRaisesRegex(EvaluationError, "gate_report_locator diverges"):
            evaluate_candidate(
                self.root,
                self.run_id,
                candidate_id=candidate_id,
                gate_report_locator="state/gates/c-other/fake.json",
                juror_adapters=jurors,
                meta_adapter=meta,
                allow_test_doubles=True,
            )

    def test_divergent_or_missing_candidate_hash_in_gates_passed_event_fails_closed(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters()

        store = DurableStore(self.root)
        events_path = self.root / f"state/events/{self.run_id}.jsonl"
        lines = events_path.read_text(encoding="utf-8").strip().splitlines()
        last_evt = json.loads(lines[-1])

        # Case A: Missing candidate_hash in GATES_PASSED event
        corrupt_evt_no_hash = copy.deepcopy(last_evt)
        corrupt_evt_no_hash["payload"].pop("candidate_hash", None)
        corrupt_evt_no_hash["payload"].pop("candidate_content_hash", None)
        corrupt_evt_no_hash["event_hash"] = store._ehash(corrupt_evt_no_hash)
        new_lines_no_hash = lines[:-1] + [json.dumps(corrupt_evt_no_hash, sort_keys=True, separators=(",", ":"))]
        events_path.write_text("\n".join(new_lines_no_hash) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(EvaluationError, "active GATES_PASSED event is missing candidate_hash"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True
            )

        # Case B: Divergent candidate_hash in GATES_PASSED event
        corrupt_evt_diff_hash = copy.deepcopy(last_evt)
        corrupt_evt_diff_hash["payload"]["candidate_hash"] = "f" * 64
        corrupt_evt_diff_hash["event_hash"] = store._ehash(corrupt_evt_diff_hash)
        new_lines_diff_hash = lines[:-1] + [json.dumps(corrupt_evt_diff_hash, sort_keys=True, separators=(",", ":"))]
        events_path.write_text("\n".join(new_lines_diff_hash) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(EvaluationError, "does not match GateReport candidate_hash"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True
            )

        # Assert no evaluation artifacts were published
        eval_dir = self.root / f"state/evaluations/{self.run_id}"
        self.assertTrue(not eval_dir.exists() or list(eval_dir.iterdir()) == [])

    def test_evaluation_fails_if_candidate_mutated(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        chall_dir = self.root / "versions/challengers" / candidate_id
        jurors, meta = self._default_test_adapters()

        # Mutate candidate tex file
        for path in chall_dir.rglob("*.tex"):
            os.chmod(path, 0o600)
            path.write_text("MUTATED CODE", encoding="utf-8")

        with self.assertRaises(EvaluationError):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True
            )

    # ==================== 6. Full Evaluation & Aggregation Tests ====================

    def test_full_evaluation_success_transitions_to_evaluated(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters(preferred_winner="B")

        report = evaluate_candidate(
            self.root, self.run_id, candidate_id=candidate_id,
            juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True
        )

        self.assertEqual(report["overall_outcome"], "challenger_favored")
        self.assertTrue(report["challenger_eligible"])
        self.assertEqual(report["consistent_jurors"], 3)
        self.assertEqual(report["divergent_jurors"], 0)
        self.assertEqual(len(report["verdict_ids"]), 6)

        # Check durable store state transition
        store = DurableStore(self.root)
        events = store.read_events(self.run_id)
        last_event = events[-1]
        self.assertEqual(last_event["state_to"], State.EVALUATED)
        self.assertEqual(last_event["event_type"], "EVALUATED")

        # Check published evaluation manifest
        eval_dir = self.root / f"state/evaluations/{self.run_id}/c0000"
        self.assertTrue((eval_dir / "manifest.json").is_file())
        self.assertTrue((eval_dir / "evaluation.json").is_file())
        self.assertTrue((eval_dir / "meta-verdict.json").is_file())
        self.assertEqual(len(list((eval_dir / "verdicts").glob("*.json"))), 6)

    def test_evaluation_rejects_symlinked_publication_parent_without_writes(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters()
        escape = self.root / "evaluation-escape"
        escape.mkdir()
        evaluations_root = self.root / "state/evaluations"
        evaluations_root.symlink_to(escape, target_is_directory=True)

        with self.assertRaisesRegex(EvaluationError, "managed evaluation directory"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True,
            )
        self.assertEqual(list(escape.iterdir()), [])
        self.assertEqual(DurableStore(self.root).read_events(self.run_id)[-1]["state_to"], State.GATES_PASSED)

    def test_completed_evaluation_redelivery_is_read_only_and_needs_no_adapters(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters(preferred_winner="B")
        first = evaluate_candidate(
            self.root, self.run_id, candidate_id=candidate_id,
            juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True,
        )
        store = DurableStore(self.root)
        events_before = store.read_events(self.run_id)
        eval_dir = self.root / f"state/evaluations/{self.run_id}/c0000"
        bytes_before = {
            path.relative_to(eval_dir).as_posix(): path.read_bytes()
            for path in eval_dir.rglob("*")
            if path.is_file()
        }

        replay = evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id)

        self.assertEqual(first, replay)
        self.assertEqual(events_before, store.read_events(self.run_id))
        self.assertEqual(bytes_before, {
            path.relative_to(eval_dir).as_posix(): path.read_bytes()
            for path in eval_dir.rglob("*")
            if path.is_file()
        })

    def test_evaluation_zero_valid_pairs_inconclusive(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        adapters_0 = {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", positional_bias="first"),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib", positional_bias="first"),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity", positional_bias="first"),
        }
        meta = FakeMetaReviewerAdapter()
        report_0 = evaluate_candidate(
            self.root, self.run_id, candidate_id=candidate_id,
            juror_adapters=adapters_0, meta_adapter=meta, allow_test_doubles=True
        )
        self.assertEqual(report_0["consistent_jurors"], 0)
        self.assertEqual(report_0["overall_outcome"], "inconclusive")
        self.assertFalse(report_0["challenger_eligible"])

    def test_evaluation_one_valid_pair_inconclusive(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        adapters_1 = {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", preferred_winner="B"),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib", positional_bias="first"),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity", positional_bias="second"),
        }
        meta = FakeMetaReviewerAdapter()
        report_1 = evaluate_candidate(
            self.root, self.run_id, candidate_id=candidate_id,
            juror_adapters=adapters_1, meta_adapter=meta, allow_test_doubles=True
        )
        self.assertEqual(report_1["consistent_jurors"], 1)
        self.assertEqual(report_1["overall_outcome"], "inconclusive")
        self.assertFalse(report_1["challenger_eligible"])

    def test_evaluation_two_valid_pairs_favors_challenger(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        adapters_2 = {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", preferred_winner="B"),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib", preferred_winner="B"),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity", positional_bias="second"),
        }
        meta = FakeMetaReviewerAdapter()
        report_2 = evaluate_candidate(
            self.root, self.run_id, candidate_id=candidate_id,
            juror_adapters=adapters_2, meta_adapter=meta, allow_test_doubles=True
        )
        self.assertEqual(report_2["consistent_jurors"], 2)
        self.assertEqual(report_2["overall_outcome"], "challenger_favored")
        self.assertTrue(report_2["challenger_eligible"])

    def test_evaluation_fails_when_meta_reviewer_vetoes(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        jurors, _ = self._default_test_adapters(preferred_winner="B")
        meta = FakeMetaReviewerAdapter(should_veto=True, veto_reason="Insufficient proof rigor detected in review.")
        report = evaluate_candidate(
            self.root, self.run_id, candidate_id=candidate_id,
            juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True
        )

        self.assertEqual(report["overall_outcome"], "inconclusive")
        self.assertFalse(report["challenger_eligible"])
        self.assertTrue(report["meta_verdict"]["vetoed"])

    def test_evaluation_fails_closed_on_math_veto(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]

        adapters = {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", math_pass=(True, False), preferred_winner="B"),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib", math_pass=(True, False), preferred_winner="B"),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity", math_pass=(True, False), preferred_winner="B"),
        }
        meta = FakeMetaReviewerAdapter()

        report = evaluate_candidate(
            self.root, self.run_id, candidate_id=candidate_id,
            juror_adapters=adapters, meta_adapter=meta, allow_test_doubles=True
        )
        self.assertFalse(report["correctness_math_pass"])
        self.assertFalse(report["challenger_eligible"])

    def test_reduced_diversity_assurance_when_single_family(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters(preferred_winner="B")

        single_family = {
            "juror-math": "single-family-v1",
            "juror-contrib": "single-family-v1",
            "juror-clarity": "single-family-v1",
        }

        report = evaluate_candidate(
            self.root, self.run_id, candidate_id=candidate_id,
            juror_adapters=jurors, meta_adapter=meta, model_families=single_family,
            allow_test_doubles=True,
        )
        self.assertEqual(report["diversity_assurance"], "reduced_diversity_assurance")

    # ==================== 7. Immutability, Durability & Idempotency Tests ====================

    def test_fsync_durability_order_before_rename(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters(preferred_winner="B")

        events_log: list[tuple[str, str]] = []
        real_fsync = os.fsync
        real_replace = os.replace

        def logged_fsync(fd: int) -> None:
            events_log.append(("fsync", f"fd-{fd}"))
            real_fsync(fd)

        def logged_replace(src: Any, dst: Any) -> None:
            events_log.append(("replace", f"{src}->{dst}"))
            real_replace(src, dst)

        with patch("os.fsync", side_effect=logged_fsync), patch("os.replace", side_effect=logged_replace):
            report = evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True
            )

        self.assertEqual(report["overall_outcome"], "challenger_favored")

        eval_dir = self.root / f"state/evaluations/{self.run_id}/c0000"
        replace_indices = [
            idx for idx, (op, args) in enumerate(events_log)
            if op == "replace" and str(eval_dir) in args
        ]
        self.assertEqual(len(replace_indices), 1)
        replace_idx = replace_indices[0]

        fsyncs_before_replace = [e for e in events_log[:replace_idx] if e[0] == "fsync"]
        fsyncs_after_replace = [e for e in events_log[replace_idx + 1:] if e[0] == "fsync"]

        # At least 9 file fsyncs + directory tree fsyncs happened before replace
        self.assertGreaterEqual(len(fsyncs_before_replace), 9)
        # Directory parent fsync happened after replace
        self.assertGreaterEqual(len(fsyncs_after_replace), 1)

    def test_versions_remain_immutable_during_and_after_evaluation(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters()

        champ_before = (self.root / "versions/champion/v0000/manifest.json").read_bytes()
        chall_before = (self.root / f"versions/challengers/{candidate_id}/manifest.json").read_bytes()

        evaluate_candidate(
            self.root, self.run_id, candidate_id=candidate_id,
            juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True
        )

        champ_after = (self.root / "versions/champion/v0000/manifest.json").read_bytes()
        chall_after = (self.root / f"versions/challengers/{candidate_id}/manifest.json").read_bytes()

        self.assertEqual(champ_before, champ_after)
        self.assertEqual(chall_before, chall_after)

        pareto = self.root / "versions/pareto"
        rejected = self.root / "versions/rejected"
        self.assertTrue(not pareto.exists() or list(pareto.iterdir()) == [])
        self.assertTrue(not rejected.exists() or list(rejected.iterdir()) == [])

    def test_no_m8_path_reaches_diagnosed_or_later_states(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters()

        evaluate_candidate(
            self.root, self.run_id, candidate_id=candidate_id,
            juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True
        )

        store = DurableStore(self.root)
        snapshot = store.snapshot(self.run_id)
        self.assertEqual(snapshot["state"], State.EVALUATED.value)
        self.assertNotEqual(snapshot["state"], State.DIAGNOSED.value)
        self.assertNotEqual(snapshot["state"], State.DECIDED.value)

    def test_fault_injection_before_publish_recovery_and_clean_staging(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters(preferred_winner="B")

        def crash_before_publish(stage: str):
            if stage == "before_publish_rename":
                raise RuntimeError("simulated crash before publish")

        with self.assertRaisesRegex(RuntimeError, "simulated crash before publish"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True,
                fault=crash_before_publish
            )

        # Assert no leftover .staging_* directories remain
        eval_parent = self.root / f"state/evaluations/{self.run_id}"
        staging_dirs = [d for d in eval_parent.glob(".staging_*") if d.is_dir()]
        self.assertEqual(staging_dirs, [])

        # Retry successfully completes
        report = evaluate_candidate(
            self.root, self.run_id, candidate_id=candidate_id,
            juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True
        )
        self.assertEqual(report["overall_outcome"], "challenger_favored")

    def test_fault_injection_after_publish_before_event_recovery(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters(preferred_winner="B")

        def crash_before_event(stage: str):
            if stage == "before_evaluated_event":
                raise RuntimeError("simulated crash before evaluated event")

        with self.assertRaisesRegex(RuntimeError, "simulated crash before evaluated event"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True,
                fault=crash_before_event
            )

        # Published directory exists but EVALUATED event was not recorded yet
        eval_dir = self.root / f"state/evaluations/{self.run_id}/c0000"
        self.assertTrue(eval_dir.is_dir())

        # Retry should revalidate published directory and record EVALUATED event without recreating files
        report = evaluate_candidate(self.root, self.run_id, candidate_id=candidate_id)
        self.assertEqual(report["overall_outcome"], "challenger_favored")

        store = DurableStore(self.root)
        self.assertEqual(store.snapshot(self.run_id)["state"], State.EVALUATED.value)

    def test_post_publish_recovery_rejects_changed_order_seed(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters(preferred_winner="B")

        def crash_before_event(stage: str):
            if stage == "before_evaluated_event":
                raise RuntimeError("simulated crash before evaluated event")

        with self.assertRaisesRegex(RuntimeError, "simulated crash"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id, order_seed=99,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True,
                fault=crash_before_event,
            )

        with self.assertRaisesRegex(EvaluationError, "order_seed diverges"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id, order_seed=413,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True,
            )

    def test_recovery_preserves_all_nine_evidence_hashes(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters(preferred_winner="B")

        def crash_before_event(stage: str):
            if stage == "before_evaluated_event":
                raise RuntimeError("simulated crash before evaluated event")

        # 1. Interrupt after publish, before event
        with self.assertRaisesRegex(RuntimeError, "simulated crash before evaluated event"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True,
                fault=crash_before_event
            )

        # 2. Execute recovery
        report = evaluate_candidate(
            self.root, self.run_id, candidate_id=candidate_id,
            juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True
        )
        self.assertEqual(report["overall_outcome"], "challenger_favored")

        # 3. Read recorded event artifact_hashes
        store = DurableStore(self.root)
        events = store.read_events(self.run_id)
        last_event = events[-1]
        self.assertEqual(last_event["event_type"], "EVALUATED")
        recorded_hashes = last_event["artifact_hashes"]

        # 4. Compute actual 9 artifact hashes from the published tree on disk
        eval_dir = self.root / f"state/evaluations/{self.run_id}/c0000"
        expected_9_hashes = sorted([
            hashlib.sha256((eval_dir / "evaluation.json").read_bytes()).hexdigest(),
            hashlib.sha256((eval_dir / "meta-verdict.json").read_bytes()).hexdigest(),
            hashlib.sha256((eval_dir / "manifest.json").read_bytes()).hexdigest(),
            *(hashlib.sha256(vf.read_bytes()).hexdigest() for vf in sorted((eval_dir / "verdicts").glob("*.json"))),
        ])

        self.assertEqual(len(recorded_hashes), 9)
        self.assertEqual(recorded_hashes, expected_9_hashes)

    def test_collision_with_differing_existing_evaluation_directory_fails_closed(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters()

        eval_dir = self.root / f"state/evaluations/{self.run_id}/c0000"
        eval_dir.mkdir(parents=True, exist_ok=True)
        (eval_dir / "manifest.json").write_text("{}", encoding="utf-8")

        with self.assertRaisesRegex(EvaluationError, "published evaluation directory is missing core artifacts|published evaluation manifest"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True
            )

    def test_post_publish_tampering_of_evaluation_artifacts_detected(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters(preferred_winner="B")

        def crash_before_event(stage: str):
            if stage == "before_evaluated_event":
                raise RuntimeError("simulated crash before evaluated event")

        # First run publishes the directory, but crashes before recording the event
        with self.assertRaisesRegex(RuntimeError, "simulated crash before evaluated event"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True,
                fault=crash_before_event
            )

        eval_dir = self.root / f"state/evaluations/{self.run_id}/c0000"
        eval_json = eval_dir / "evaluation.json"

        # Tamper with evaluation.json by making writable and changing contents
        os.chmod(eval_dir, 0o755)
        os.chmod(eval_json, 0o644)
        data = json.loads(eval_json.read_text(encoding="utf-8"))
        data["overall_outcome"] = "champion_favored"
        eval_json.write_text(json.dumps(data), encoding="utf-8")

        # Retry should detect tampering against manifest hash and fail closed
        with self.assertRaisesRegex(EvaluationError, "evaluation report bytes are not canonical|evaluation_report_hash mismatch"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True
            )

    def test_recovery_rejects_rehashed_unexpected_artifact(self):
        m7_out = self._setup_m7_gates_passed()
        candidate_id = m7_out["candidate"]["candidate_id"]
        jurors, meta = self._default_test_adapters(preferred_winner="B")

        def crash_before_event(stage: str):
            if stage == "before_evaluated_event":
                raise RuntimeError("simulated crash before evaluated event")

        with self.assertRaisesRegex(RuntimeError, "simulated crash"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True,
                fault=crash_before_event,
            )

        eval_dir = self.root / f"state/evaluations/{self.run_id}/c0000"
        manifest_path = eval_dir / "manifest.json"
        os.chmod(eval_dir, 0o755)
        extra = eval_dir / "unexpected.txt"
        extra.write_text("not part of the M8 publication contract\n", encoding="utf-8")
        os.chmod(extra, 0o444)
        os.chmod(manifest_path, 0o644)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["tree_content_hash"] = tree_hash(eval_dir, exclude={"manifest.json"})
        manifest_path.write_bytes(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
        os.chmod(manifest_path, 0o444)
        os.chmod(eval_dir, 0o555)

        with self.assertRaisesRegex(EvaluationError, "unexpected artifacts"):
            evaluate_candidate(
                self.root, self.run_id, candidate_id=candidate_id,
                juror_adapters=jurors, meta_adapter=meta, allow_test_doubles=True,
            )


if __name__ == "__main__":
    unittest.main()
