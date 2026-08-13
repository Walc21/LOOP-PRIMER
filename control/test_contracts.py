"""Deterministic, offline contract tests for the M1 scaffold."""

from __future__ import annotations

import json
import copy
import subprocess
import unittest
from collections import Counter
from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
ROLE_DIR = CONFIG / "roles"
SCHEMA_DIR = CONFIG / "schemas"

ROLE_IDS = {
    "M00",
    "S10", "W11", "W12", "W13",
    "S20", "W21", "W22", "W23",
    "S30", "W31", "W32", "W33",
    "S40", "W41", "W42", "W43",
    "S50", "W51", "W52", "W53",
}
STATES = [
    "NEW", "INGESTED", "SOURCE_READY", "CYCLE_PLANNED",
    "DEPARTMENTS_RUNNING", "SYNTHESIS_READY", "CANDIDATE_BUILT",
    "GATES_PASSED", "EVALUATED", "DIAGNOSED", "DECIDED", "COMMITTING",
    "CYCLE_COMPLETE", "PAUSED", "FINALIZED", "TECHNICAL_FAILURE",
]
ACTIONS = [
    "PROMOTE", "ARCHIVE_PARETO", "REJECT", "REFOCUS_AND_CONTINUE",
    "CONTINUE_UNCHANGED", "REQUEST_EXTRA_JUDGMENT", "PAUSE", "FINALIZE",
    "ABORT_TECHNICAL",
]
DIMENSIONS = {
    "correctness_math", "proof_completeness", "logical_coherence",
    "scientific_contribution", "semantic_precision", "clarity",
    "format_integrity", "reproducibility",
}
SCHEMA_FILES = {
    "run-manifest.schema.json", "event.schema.json", "snapshot.schema.json",
    "agent-task.schema.json", "agent-proposal.schema.json",
    "department-packet.schema.json", "candidate-manifest.schema.json",
    "gate-report.schema.json", "jury-verdict.schema.json",
    "diagnosis.schema.json", "decision.schema.json",
    "finalization-receipt.schema.json",
}


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def load_json(path: Path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


class ConfigurationTests(unittest.TestCase):
    def test_all_yaml_is_parseable(self):
        yaml_files = sorted(CONFIG.rglob("*.yaml"))
        self.assertGreaterEqual(len(yaml_files), 25)
        for path in yaml_files:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsInstance(load_yaml(path), dict)

    def test_canonical_states_and_actions(self):
        system = load_yaml(CONFIG / "system.yaml")
        self.assertEqual(system["states"], STATES)
        self.assertEqual(system["actions"], ACTIONS)

    def test_eight_evaluation_dimensions(self):
        rubric = load_yaml(CONFIG / "rubrics" / "evaluation.yaml")
        dimensions = rubric["dimensions"]
        self.assertEqual({item["id"] for item in dimensions}, DIMENSIONS)
        self.assertEqual(len(dimensions), 8)
        math = next(item for item in dimensions if item["id"] == "correctness_math")
        self.assertTrue(math["hard_gate"])
        self.assertFalse(math["compensable"])


class RoleCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = sorted(ROLE_DIR.glob("*.yaml"))
        cls.roles = [load_yaml(path) for path in cls.paths]
        cls.by_id = {role["id"]: role for role in cls.roles}

    def test_exact_ids_without_duplicates(self):
        ids = [role["id"] for role in self.roles]
        self.assertEqual(len(ids), 21)
        self.assertEqual(len(set(ids)), 21, "duplicate role IDs")
        self.assertEqual(set(ids), ROLE_IDS)
        self.assertEqual({path.stem for path in self.paths}, ROLE_IDS)

    def test_one_plus_five_plus_fifteen(self):
        counts = Counter(role["kind"] for role in self.roles)
        self.assertEqual(counts, {"manager": 1, "submanager": 5, "specialist": 15})
        depths = Counter(role["rlm_depth"] for role in self.roles)
        self.assertEqual(depths, {0: 1, 1: 5, 2: 15})

    def test_parent_child_topology(self):
        manager = self.by_id["M00"]
        self.assertIsNone(manager["parent_id"])
        self.assertEqual(len(manager["children_ids"]), 5)
        for role in self.roles:
            with self.subTest(role=role["id"]):
                for child_id in role["children_ids"]:
                    self.assertIn(child_id, self.by_id)
                    self.assertEqual(self.by_id[child_id]["parent_id"], role["id"])
                if role["kind"] == "submanager":
                    self.assertEqual(len(role["children_ids"]), 3)
                if role["kind"] == "specialist":
                    self.assertEqual(role["children_ids"], [])


class SchemaContractTests(unittest.TestCase):
    def test_exact_schema_catalog_and_meta_validation(self):
        paths = sorted(SCHEMA_DIR.glob("*.schema.json"))
        self.assertEqual({path.name for path in paths}, SCHEMA_FILES)
        self.assertEqual(len(paths), 12)
        for path in paths:
            with self.subTest(path=path.name):
                schema = load_json(path)
                jsonschema.Draft202012Validator.check_schema(schema)

    def test_agent_proposal_required_fields_and_private_reasoning_rejection(self):
        schema = load_json(SCHEMA_DIR / "agent-proposal.schema.json")
        required = {
            "proposal_id", "role_id", "cycle_id", "base_hash", "scope",
            "evidence_locators", "patch_or_operations", "affected_claims",
            "dependencies", "risk", "confidence", "requested_validations",
            "prompt_version",
        }
        self.assertTrue(required.issubset(set(schema["required"])))
        proposal = {
            "schema_version": "1.1.0",
            "proposal_id": "proposal-1",
            "role_id": "W22",
            "cycle_id": 1,
            "base_hash": "a" * 64,
            "scope": ["theorem:1"],
            "evidence_locators": ["artifacts/extracted/page-1.txt#L1"],
            "patch_or_operations": {
                "kind": "operations",
                "operations": [{"op": "replace", "target": "theorem:1", "value": "Revised statement"}],
            },
            "affected_claims": ["claim-1"],
            "dependencies": ["S20-review"],
            "risk": {"level": "high", "factors": ["proof change"], "technical_effect_possible": True},
            "confidence": 0.8,
            "requested_validations": ["correctness_math"],
            "prompt_version": "sha256:" + "b" * 64,
        }
        jsonschema.Draft202012Validator(schema).validate(proposal)
        proposal["chain_of_thought"] = "must never be persisted"
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(proposal)


class RepositorySafetyTests(unittest.TestCase):
    def check_ignored(self, relative_path: str) -> bool:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", relative_path],
            cwd=ROOT,
            check=False,
        )
        return result.returncode == 0

    def test_runtime_and_secret_examples_are_ignored(self):
        ignored = [
            "input/inbox/artigo.pdf", "input/inbox/source.zip",
            "state/events/run-1.jsonl", "state/locks/run-1.lock",
            "versions/challengers/candidate-1/manifest.json",
            "workspaces/run-1/draft.tex", "logs/run-1.log", ".env",
            ".prime/agent/sessions/session.jsonl",
        ]
        for path in ignored:
            with self.subTest(path=path):
                self.assertTrue(self.check_ignored(path))

    def test_versioned_contracts_are_not_ignored(self):
        committed = [
            "config/system.yaml",
            "config/schemas/agent-proposal.schema.json",
            "config/roles/M00.yaml",
            "input/inbox/.gitkeep",
        ]
        for path in committed:
            with self.subTest(path=path):
                self.assertFalse(self.check_ignored(path))



class ScaffoldTests(unittest.TestCase):
    def test_canonical_directories_exist(self):
        directories = [
            ".prime/agent/prompts", ".prime/agent/skills/article-loop",
            "config/roles", "config/rubrics", "config/schemas", "input/inbox",
            "artifacts/original", "artifacts/extracted", "artifacts/rendered",
            "prompts/immutable", "prompts/overlays", "state/events",
            "state/snapshots", "state/checkpoints", "state/claims",
            "state/issues", "state/decisions", "state/locks",
            "versions/champion", "versions/challengers", "versions/pareto",
            "versions/rejected", "workspaces", "reports", "logs", "control",
            "scripts", "bin", "docs",
        ]
        for directory in directories:
            with self.subTest(directory=directory):
                self.assertTrue((ROOT / directory).is_dir())

    def test_future_stubs_are_present_and_inert(self):
        scripts = {
            "01_external_evaluator.py", "02_stagnation_detector.py",
            "03_refocus_generator.py", "04_compensation_policy.py",
            "05_transactional_finalizer.py",
        }
        self.assertEqual(
            {path.name for path in (ROOT / "scripts").glob("[0-9][0-9]_*.py")},
            scripts,
        )
        for name in ("start-prime.sh", "check.sh"):
            path = ROOT / "bin" / name
            self.assertTrue(path.is_file())
            self.assertEqual(path.stat().st_mode & 0o111, 0)
        self.assertTrue((ROOT / "bin/preflight.sh").is_file())
        self.assertNotEqual((ROOT / "bin/preflight.sh").stat().st_mode & 0o111, 0)


class ConditionalContractTests(unittest.TestCase):
    HASH_A = "a" * 64
    HASH_B = "b" * 64
    WHEN = "2026-08-13T12:00:00Z"

    def validator(self, schema_name):
        schema = load_json(SCHEMA_DIR / schema_name)
        return jsonschema.Draft202012Validator(
            schema,
            format_checker=jsonschema.FormatChecker(),
        )

    def assert_valid(self, schema_name, instance):
        errors = sorted(
            self.validator(schema_name).iter_errors(instance),
            key=lambda error: list(error.path),
        )
        self.assertEqual(errors, [], "\n".join(error.message for error in errors))

    def assert_invalid(self, schema_name, instance):
        self.assertTrue(list(self.validator(schema_name).iter_errors(instance)))

    def agent_task(self, role_id, requested_output_schema):
        return {
            "schema_version": "1.1.0",
            "task_id": "task-1",
            "run_id": "run-1",
            "cycle_id": 1,
            "role_id": role_id,
            "activation_mode": "RUN",
            "created_at": self.WHEN,
            "base_hash": self.HASH_A,
            "scope": ["section:1"],
            "input_locators": ["artifacts/extracted/article.tex"],
            "requested_output_schema": requested_output_schema,
            "prompt_version": "prompt-v1",
            "constraints": ["evidence-only"],
        }

    def candidate(self, kind):
        baseline = kind == "baseline"
        return {
            "schema_version": "1.1.0",
            "candidate_id": "v0000" if baseline else "v0001",
            "candidate_kind": kind,
            "run_id": "run-1",
            "cycle_id": 0 if baseline else 1,
            "base_candidate_id": None if baseline else "v0000",
            "built_at": self.WHEN,
            "workspace_hash": self.HASH_A,
            "content_hash": self.HASH_B,
            "source_proposal_ids": [] if baseline else ["proposal-1"],
            "merge_receipt_locator": None if baseline else "reports/merge-v0001.json",
            "immutable": True,
        }

    def department_packet(self, status):
        no_change = status == "no_change"
        return {
            "schema_version": "1.1.0",
            "packet_id": "packet-1",
            "run_id": "run-1",
            "cycle_id": 1,
            "department_id": "S10",
            "base_hash": self.HASH_A,
            "proposal_ids": [] if no_change else ["proposal-1"],
            "specialist_task_ids": [] if no_change else ["task-W11"],
            "dependency_reviews": [],
            "status": status,
            "no_change_justification": (
                "Nenhuma seção estrutural foi afetada pelo diff verificado."
                if no_change else None
            ),
            "evidence_locators": ["state/claims/impact-map.json#S10"],
            "created_at": self.WHEN,
        }

    def diagnosis(self, classification):
        return {
            "schema_version": "1.1.0",
            "diagnosis_id": "diagnosis-1",
            "run_id": "run-1",
            "cycle_id": 1,
            "candidate_id": "v0001",
            "candidate_content_hash": self.HASH_A,
            "created_at": self.WHEN,
            "gate_report_id": "gate-report-1",
            "verdict_ids": ["verdict-1"],
            "classification": classification,
            "signals": ["score-delta"],
            "recommended_mode": "SHIFT" if "PLATEAU" in classification else "CHECK",
            "focus": ["proof:1"],
            "evidence_locators": ["reports/progress.json"],
        }

    def scores(self, value):
        return {dimension: value for dimension in DIMENSIONS}

    def jury_verdict(self, order=("A", "B"), outcome="winner"):
        return {
            "schema_version": "1.1.0",
            "verdict_id": "verdict-1",
            "comparison_id": "comparison-1",
            "juror_id": "juror-1",
            "candidate_neutral_ids": ["A", "B"],
            "content_hashes": [self.HASH_A, self.HASH_B],
            "presentation_order": list(order),
            "order_seed": 413,
            "rubric_version": "rubric-v1",
            "dimension_scores": [self.scores(4), self.scores(3)],
            "outcome": outcome,
            "winner_neutral_id": "A" if outcome == "winner" else None,
            "correctness_math_pass": [True, True],
            "evidence_locators": ["reports/jury/evidence-1.json"],
            "submitted_at": self.WHEN,
        }

    def decision(self, action):
        instance = {
            "schema_version": "1.1.0",
            "decision_id": "decision-1",
            "run_id": "run-1",
            "cycle_id": 1,
            "candidate_id": "v0001",
            "candidate_content_hash": self.HASH_A,
            "decided_at": self.WHEN,
            "action": action,
            "gate_report_id": "gate-report-1",
            "verdict_ids": ["verdict-1"],
            "diagnosis_id": "diagnosis-1",
            "basis_locators": ["state/decisions/basis-1.json"],
            "reason_code": None,
            "inconclusive_evaluation_id": None,
            "final_gate_report_ids": [],
            "content_modification_allowed": False,
            "authorized_by": "M00",
        }
        if action == "REJECT":
            instance.update(reason_code="GATE_FAILED", verdict_ids=[])
        elif action == "REFOCUS_AND_CONTINUE":
            instance["reason_code"] = "LOCAL_PLATEAU"
        elif action == "CONTINUE_UNCHANGED":
            instance["reason_code"] = "EVOLVING"
        elif action == "REQUEST_EXTRA_JUDGMENT":
            instance.update(
                reason_code="INCONCLUSIVE_EVALUATION",
                inconclusive_evaluation_id="evaluation-1",
            )
        elif action == "PAUSE":
            instance.update(
                candidate_id=None,
                candidate_content_hash=None,
                gate_report_id=None,
                verdict_ids=[],
                diagnosis_id=None,
                reason_code="BUDGET_EXHAUSTED",
            )
        elif action == "FINALIZE":
            instance.update(
                reason_code="POLICY_SATISFIED",
                final_gate_report_ids=["final-gate-report-1"],
            )
        elif action == "ABORT_TECHNICAL":
            instance.update(
                candidate_id=None,
                candidate_content_hash=None,
                gate_report_id=None,
                verdict_ids=[],
                diagnosis_id=None,
                reason_code="TECHNICAL_FAILURE",
            )
        return instance

    def run_manifest(self, state="NEW", source_mode="PDF_ONLY_RECONSTRUCTION"):
        input_record = None
        if state != "NEW":
            input_record = {
                "path": "input/inbox/artigo.pdf",
                "sha256": self.HASH_A,
                "size_bytes": 1024,
                "source_mode": source_mode,
                "source_zip": None,
            }
            if source_mode == "SOURCE_ZIP":
                input_record["source_zip"] = {
                    "safe_path": "input/inbox/source.zip",
                    "sha256": self.HASH_B,
                    "size_bytes": 2048,
                    "safe_inspection_passed": True,
                }
        return {
            "schema_version": "1.1.0",
            "run_id": "run-1",
            "created_at": self.WHEN,
            "state": state,
            "cycle_id": 0,
            "input": input_record,
            "config_hash": self.HASH_A,
            "budget_config_hash": self.HASH_B,
            "role_ids": sorted(ROLE_IDS),
            "current_candidate_id": None,
        }

    def event(self, sequence=0, state_from=None, state_to="NEW"):
        return {
            "schema_version": "1.1.0",
            "event_id": f"event-{sequence}",
            "idempotency_key": f"run-1:event-{sequence}",
            "run_id": "run-1",
            "cycle_id": 0,
            "sequence": sequence,
            "occurred_at": self.WHEN,
            "event_type": "RUN_CREATED" if sequence == 0 else "STATE_RECORDED",
            "state_from": state_from,
            "state_to": state_to,
            "actor_id": "system",
            "payload": {},
            "artifact_hashes": [],
            "previous_event_hash": None if sequence == 0 else self.HASH_A,
            "event_hash": self.HASH_B,
        }

    def snapshot(self, event_sequence=-1, state="NEW"):
        initial = event_sequence == -1
        return {
            "schema_version": "1.1.0",
            "snapshot_id": "snapshot-initial" if initial else "snapshot-1",
            "run_id": "run-1",
            "cycle_id": 0,
            "event_sequence": event_sequence,
            "created_at": self.WHEN,
            "state": state,
            "last_event_id": None if initial else f"event-{event_sequence}",
            "last_event_hash": None if initial else self.HASH_A,
            "data": {},
            "data_hash": self.HASH_A,
            "snapshot_hash": self.HASH_B,
        }

    def test_m00_allows_exactly_run(self):
        manager = load_yaml(ROLE_DIR / "M00.yaml")
        self.assertEqual(manager["allowed_activation_modes"], ["RUN"])

    def test_no_cycle_can_freeze_m00(self):
        manager = load_yaml(ROLE_DIR / "M00.yaml")
        self.assertNotIn("FREEZE", manager["allowed_activation_modes"])
        self.assertInvalidAgentTaskForM00("FREEZE")

    def assertInvalidAgentTaskForM00(self, mode):
        task = self.agent_task("S10", "department-packet.schema.json")
        task.update(role_id="M00", activation_mode=mode)
        self.assert_invalid("agent-task.schema.json", task)

    def test_agent_task_submanager_positive(self):
        self.assert_valid(
            "agent-task.schema.json",
            self.agent_task("S20", "department-packet.schema.json"),
        )

    def test_agent_task_specialist_positive(self):
        self.assert_valid(
            "agent-task.schema.json",
            self.agent_task("W22", "agent-proposal.schema.json"),
        )

    def test_agent_task_wrong_output_combinations_negative(self):
        self.assert_invalid(
            "agent-task.schema.json",
            self.agent_task("S20", "agent-proposal.schema.json"),
        )
        self.assert_invalid(
            "agent-task.schema.json",
            self.agent_task("W22", "department-packet.schema.json"),
        )

    def test_agent_task_m00_negative(self):
        self.assertInvalidAgentTaskForM00("RUN")

    def test_candidate_baseline_v0000_positive(self):
        self.assert_valid("candidate-manifest.schema.json", self.candidate("baseline"))

    def test_candidate_challenger_positive_and_empty_proposals_negative(self):
        challenger = self.candidate("challenger")
        self.assert_valid("candidate-manifest.schema.json", challenger)
        challenger["source_proposal_ids"] = []
        self.assert_invalid("candidate-manifest.schema.json", challenger)

    def test_candidate_baseline_with_base_negative(self):
        baseline = self.candidate("baseline")
        baseline["base_candidate_id"] = "v-1"
        self.assert_invalid("candidate-manifest.schema.json", baseline)

    def test_department_packet_no_change_positive(self):
        self.assert_valid(
            "department-packet.schema.json",
            self.department_packet("no_change"),
        )

    def test_department_packet_no_change_cannot_fake_specialists(self):
        packet = self.department_packet("no_change")
        packet["specialist_task_ids"] = ["task-W11"]
        self.assert_invalid("department-packet.schema.json", packet)
        packet = self.department_packet("no_change")
        packet["proposal_ids"] = ["proposal-1"]
        self.assert_invalid("department-packet.schema.json", packet)

    def test_department_packet_complete_requires_proposal(self):
        packet = self.department_packet("complete")
        self.assert_valid("department-packet.schema.json", packet)
        packet["proposal_ids"] = []
        self.assert_invalid("department-packet.schema.json", packet)

    def test_diagnosis_all_classifications_positive(self):
        classifications = [
            "EVOLVING", "LOCAL_PLATEAU", "GLOBAL_PLATEAU", "OSCILLATING",
            "REGRESSING", "INCONCLUSIVE", "TECHNICAL_FAILURE",
        ]
        for classification in classifications:
            with self.subTest(classification=classification):
                self.assert_valid(
                    "diagnosis.schema.json",
                    self.diagnosis(classification),
                )

    def test_diagnosis_invalid_classification_negative(self):
        diagnosis = self.diagnosis("EVOLVING")
        diagnosis["classification"] = "PLATEAU"
        self.assert_invalid("diagnosis.schema.json", diagnosis)

    def test_jury_ab_positive(self):
        self.assert_valid("jury-verdict.schema.json", self.jury_verdict(("A", "B")))

    def test_jury_ba_positive(self):
        self.assert_valid("jury-verdict.schema.json", self.jury_verdict(("B", "A")))

    def test_jury_repeated_candidates_negative(self):
        verdict = self.jury_verdict()
        verdict["candidate_neutral_ids"] = ["A", "A"]
        self.assert_invalid("jury-verdict.schema.json", verdict)

    def test_jury_winner_absent_negative(self):
        verdict = self.jury_verdict(outcome="winner")
        verdict["winner_neutral_id"] = None
        self.assert_invalid("jury-verdict.schema.json", verdict)

    def test_jury_winner_present_on_tie_negative(self):
        verdict = self.jury_verdict(outcome="tie")
        verdict["winner_neutral_id"] = "A"
        self.assert_invalid("jury-verdict.schema.json", verdict)

    def test_jury_invalid_hash_negative(self):
        verdict = self.jury_verdict()
        verdict["content_hashes"][0] = "not-a-hash"
        self.assert_invalid("jury-verdict.schema.json", verdict)

    def test_jury_blinding_leaks_negative(self):
        for field in ("champion", "challenger", "author_role", "team_name"):
            with self.subTest(field=field):
                verdict = self.jury_verdict()
                verdict[field] = "forbidden"
                self.assert_invalid("jury-verdict.schema.json", verdict)

    def test_decision_all_nine_actions_positive(self):
        for action in ACTIONS:
            with self.subTest(action=action):
                self.assert_valid("decision.schema.json", self.decision(action))
        jury_reject = self.decision("REJECT")
        jury_reject.update(reason_code="JURY_UNFAVORABLE", verdict_ids=["verdict-1"])
        self.assert_valid("decision.schema.json", jury_reject)

    def test_decision_all_nine_actions_negative(self):
        mutations = {
            "PROMOTE": ("verdict_ids", []),
            "ARCHIVE_PARETO": ("gate_report_id", None),
            "REJECT": ("verdict_ids", ["unexpected-verdict"]),
            "REFOCUS_AND_CONTINUE": ("diagnosis_id", None),
            "CONTINUE_UNCHANGED": ("reason_code", None),
            "REQUEST_EXTRA_JUDGMENT": ("inconclusive_evaluation_id", None),
            "PAUSE": ("reason_code", None),
            "FINALIZE": ("final_gate_report_ids", []),
            "ABORT_TECHNICAL": ("verdict_ids", ["unexpected-verdict"]),
        }
        for action, (field, value) in mutations.items():
            with self.subTest(action=action):
                instance = self.decision(action)
                instance[field] = value
                self.assert_invalid("decision.schema.json", instance)

    def test_run_manifest_new_without_input_positive(self):
        self.assert_valid("run-manifest.schema.json", self.run_manifest("NEW"))

    def test_run_manifest_ingested_without_hash_negative(self):
        manifest = self.run_manifest("INGESTED")
        del manifest["input"]["sha256"]
        self.assert_invalid("run-manifest.schema.json", manifest)

    def test_run_manifest_ingested_complete_positive(self):
        self.assert_valid("run-manifest.schema.json", self.run_manifest("INGESTED"))

    def test_run_manifest_source_zip_provenance_positive(self):
        self.assert_valid(
            "run-manifest.schema.json",
            self.run_manifest("INGESTED", "SOURCE_ZIP"),
        )

    def test_event_initial_and_subsequent_positive(self):
        self.assert_valid("event.schema.json", self.event())
        self.assert_valid("event.schema.json", self.event(1, "NEW", "INGESTED"))

    def test_event_previous_hash_sequence_invariants_negative(self):
        later = self.event(1, "NEW", "INGESTED")
        later["previous_event_hash"] = None
        self.assert_invalid("event.schema.json", later)
        initial = self.event()
        initial["previous_event_hash"] = self.HASH_A
        self.assert_invalid("event.schema.json", initial)

    def test_event_pause_resume_and_failure_structurally_allowed(self):
        cases = [
            self.event(2, "CYCLE_PLANNED", "PAUSED"),
            self.event(3, "PAUSED", "CYCLE_PLANNED"),
            self.event(4, "DEPARTMENTS_RUNNING", "TECHNICAL_FAILURE"),
        ]
        for event in cases:
            self.assert_valid("event.schema.json", event)

    def test_snapshot_initial_and_later_positive(self):
        self.assert_valid("snapshot.schema.json", self.snapshot())
        self.assert_valid("snapshot.schema.json", self.snapshot(0, "NEW"))
        self.assert_valid("snapshot.schema.json", self.snapshot(3, "PAUSED"))
        self.assert_valid("snapshot.schema.json", self.snapshot(4, "TECHNICAL_FAILURE"))

    def test_snapshot_event_linkage_negative(self):
        later = self.snapshot(0, "NEW")
        later["last_event_hash"] = None
        self.assert_invalid("snapshot.schema.json", later)
        initial = self.snapshot()
        initial["last_event_id"] = "event-0"
        self.assert_invalid("snapshot.schema.json", initial)

    def test_gate_report_positive_and_hard_math_negative(self):
        report = {
            "schema_version": "1.1.0",
            "report_id": "gate-report-1",
            "candidate_id": "v0001",
            "candidate_content_hash": self.HASH_A,
            "generated_at": self.WHEN,
            "overall_pass": True,
            "correctness_math_pass": True,
            "gates": [{
                "gate_id": "math",
                "command": "local-check",
                "verifier_version": "1",
                "input_hash": self.HASH_A,
                "exit_code": 0,
                "passed": True,
                "evidence_locators": ["reports/gates/math.txt"],
            }],
        }
        self.assert_valid("gate-report.schema.json", report)
        report["correctness_math_pass"] = False
        self.assert_invalid("gate-report.schema.json", report)

    def test_finalization_receipt_positive_and_content_change_negative(self):
        receipt = {
            "schema_version": "1.1.0",
            "receipt_id": "receipt-1",
            "run_id": "run-1",
            "cycle_id": 1,
            "decision_id": "decision-1",
            "candidate_id": "v0001",
            "action": "PROMOTE",
            "applied_at": self.WHEN,
            "state_before": "COMMITTING",
            "state_after": "CYCLE_COMPLETE",
            "content_hash_before": self.HASH_A,
            "content_hash_after": self.HASH_A,
            "hash_revalidated": True,
            "atomic": True,
            "content_modified": False,
            "destination": "versions/champion/v0001",
        }
        self.assert_valid("finalization-receipt.schema.json", receipt)
        receipt["content_modified"] = True
        self.assert_invalid("finalization-receipt.schema.json", receipt)


if __name__ == "__main__":
    unittest.main()
