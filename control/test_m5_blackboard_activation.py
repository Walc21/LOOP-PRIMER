"""Offline M5 tests: append-only memory, impact and sparse activation."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))

from article_loop import (ActivationMode, ActivationPlanner, Blackboard,
                          BlackboardError, PlanningLimits, manager_view,
                          specialist_view, submanager_view)


SOURCE = "a" * 64
DEPARTMENTS = ("S10", "S20", "S30", "S40", "S50")


def department_packet(department, status="complete"):
    no_change = status == "no_change"
    return {
        "schema_version": "1.1.0", "packet_id": f"packet-{department}", "run_id": "run-1",
        "cycle_id": 0, "department_id": department, "base_hash": SOURCE,
        "proposal_ids": [] if no_change else [f"proposal-{department}"],
        "specialist_task_ids": [] if no_change else [f"task-{department}"],
        "dependency_reviews": [], "status": status,
        "no_change_justification": "No material change was proposed." if no_change else None,
        "evidence_locators": [f"evidence-{department}.json#record"],
        "created_at": "2026-08-13T12:00:00Z",
    }


def claim(text="A theorem", kind="theorem", location=None, dependencies=None, severity=70):
    return {
        "text": text, "type": kind, "location": location or {"section": "2", "equation": "(2.1)"},
        "dependencies": dependencies or [], "evidence": ["p2:l10-l20"], "status": "open",
        "severity": severity, "source_hash": SOURCE, "last_validated_cycle": 0,
    }


class BlackboardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.board = Blackboard(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_claim_is_stable_and_all_six_ledgers_are_append_only(self):
        first = self.board.append("run-1", "claims", claim())
        self.assertEqual(first["claim_id"], self.board.append("run-1", "claims", claim())["claim_id"])
        revision = dict(first); revision["status"] = "checked"; revision["last_validated_cycle"] = 1
        self.board.append("run-1", "claims", revision)
        self.assertEqual(len(self.board.read("run-1", "claims")), 2)
        self.assertEqual(self.board.claims("run-1")[first["claim_id"]]["status"], "checked")
        for ledger in ("issues", "tasks", "dependencies", "evidence", "decisions"):
            self.board.append("run-1", ledger, {"record_id": f"{ledger}-1", "value": ledger})
            with self.assertRaises(BlackboardError):
                self.board.append("run-1", ledger, {"record_id": f"{ledger}-1", "value": "changed"})

    def test_localized_and_indirect_dependency_impact(self):
        base = self.board.append("run-1", "claims", claim("Base definition", "definition", {"section": "1"}))
        dependent = self.board.append("run-1", "claims", claim("Theorem uses definition", "theorem", {"section": "3"}, [base["claim_id"]]))
        impact = self.board.impact("run-1", [base["claim_id"]])
        self.assertEqual(set(impact.claims), {base["claim_id"], dependent["claim_id"]})
        self.assertIn("W22", impact.roles)
        self.assertIn("3", impact.sections)

    def test_structured_changes_preserve_section_equation_reference_and_close_dependencies(self):
        base = self.board.append("run-1", "claims", claim("Equation base", "equation", {"section": "2", "equation": "(2.1)", "reference": "[7]"}, severity=90))
        middle = self.board.append("run-1", "claims", claim("Middle", "lemma", {"section": "3"}, [base["claim_id"]]))
        end = self.board.append("run-1", "claims", claim("End", "theorem", {"section": "4"}, [middle["claim_id"]]))
        section = self.board.impact("run-1", [{"location": {"section": "2"}}])
        both = self.board.impact("run-1", [{"kind": "equation", "location": "(2.1)"}])
        reference = self.board.impact("run-1", [{"location": {"reference": "[7]"}}])
        self.assertEqual(set(section.claims), {base["claim_id"], middle["claim_id"], end["claim_id"]})
        self.assertIn("(2.1)", both.equations)
        self.assertTrue({"W23", "W52"}.issubset(both.roles))
        self.assertIn("W51", reference.roles)
        self.assertEqual(both.severity, 90)

    def test_paths_partial_lines_and_concurrent_writers_are_safe(self):
        for invalid in ("", "../bad", "bad/run", ".", ".."):
            with self.assertRaises(BlackboardError): self.board.append(invalid, "issues", {"record_id": "x"})
        state = Path(self.temporary.name) / "state"; state.mkdir()
        outside = Path(self.temporary.name) / "outside"; outside.mkdir()
        (state / "blackboard").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(BlackboardError): self.board.append("run-1", "issues", {"record_id": "x"})
        (state / "blackboard").unlink()
        errors = []
        def writer(value):
            try: self.board.append("run-1", "issues", {"record_id": "same", "value": value})
            except BlackboardError as error: errors.append(error)
        threads = [threading.Thread(target=writer, args=(value,)) for value in ("a", "b")]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(len(self.board.read("run-1", "issues")), 1)
        self.assertEqual(len(errors), 1)
        ledger = Path(self.temporary.name) / "state/blackboard/run-1/issues.jsonl"
        with ledger.open("ab") as stream: stream.write(b'{"record_id":')
        with self.assertRaises(BlackboardError): self.board.read("run-1", "issues")

    def test_run_and_ledger_symlinks_are_rejected(self):
        root = Path(self.temporary.name)
        managed = root / "state/blackboard"; managed.mkdir(parents=True)
        outside = root / "outside-run"; outside.mkdir()
        (managed / "run-1").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(BlackboardError): self.board.read("run-1", "issues")
        (managed / "run-1").unlink(); (managed / "run-1").mkdir()
        (managed / "run-1/issues.jsonl").symlink_to(outside / "issues.jsonl")
        with self.assertRaises(BlackboardError): self.board.append("run-1", "issues", {"record_id": "x"})

    def test_notation_proof_and_style_are_conservatively_mapped(self):
        notation = self.board.impact("run-1", ["notation"])
        self.assertTrue({"W21", "W42"}.issubset(notation.roles))
        proof = self.board.impact("run-1", ["proof"])
        self.assertTrue({"S20", "W22"}.issubset(proof.roles))
        style = self.board.impact("run-1", ["style"])
        self.assertTrue({"W41", "W43"}.issubset(style.roles))


class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.board = Blackboard(self.temporary.name)
        self.planner = ActivationPlanner()

    def tearDown(self):
        self.temporary.cleanup()

    def test_same_snapshot_is_same_plan_and_first_cycle_covers_five_departments(self):
        impact = self.board.impact("run-1", [])
        first = self.planner.plan(cycle_id=0, impact=impact)
        second = self.planner.plan(cycle_id=0, impact=impact)
        self.assertEqual(first.activation_map(), second.activation_map())
        modes = {entry.role_id: entry.mode for entry in first.entries}
        self.assertEqual(modes["M00"], ActivationMode.RUN)
        self.assertEqual({role for role in DEPARTMENTS if modes[role] is ActivationMode.RUN}, set(DEPARTMENTS))
        focal = {"W11", "W21", "W31", "W41", "W51"}
        self.assertEqual({role for role, mode in modes.items() if role.startswith("W") and mode is ActivationMode.RUN}, focal)
        self.assertTrue(all(modes[role] is ActivationMode.FREEZE for role in modes if role.startswith("W") and role not in focal))

    def test_first_cycle_preserves_critical_and_impacted_workers(self):
        for change in ("theorem", "proof"):
            with self.subTest(change=change):
                plan = self.planner.plan(cycle_id=0, impact=self.board.impact("run-1", [change]))
                self.assertEqual({entry.role_id: entry.mode for entry in plan.entries}["W22"], ActivationMode.CHECK)
        finalization = self.planner.plan(cycle_id=0, impact=self.board.impact("run-1", []), finalization_requested=True)
        finalization_modes = {entry.role_id: entry.mode for entry in finalization.entries}
        self.assertEqual(finalization_modes["W51"], ActivationMode.RUN)
        self.assertEqual(finalization_modes["W53"], ActivationMode.CHECK)
        style = self.planner.plan(cycle_id=0, impact=self.board.impact("run-1", ["style"]))
        style_modes = {entry.role_id: entry.mode for entry in style.entries}
        self.assertEqual(style_modes["W41"], ActivationMode.RUN)
        self.assertEqual(style_modes["W43"], ActivationMode.RUN)
        notation = self.planner.plan(cycle_id=0, impact=self.board.impact("run-1", ["notation"]))
        notation_modes = {entry.role_id: entry.mode for entry in notation.entries}
        self.assertEqual(notation_modes["W21"], ActivationMode.RUN)
        self.assertEqual(notation_modes["W42"], ActivationMode.RUN)
        self.assertEqual(notation_modes["W22"], ActivationMode.FREEZE)

    def test_new_proof_requires_w22_and_style_stays_sparse(self):
        proof_plan = self.planner.plan(cycle_id=2, impact=self.board.impact("run-1", ["theorem"]))
        modes = {entry.role_id: entry.mode for entry in proof_plan.entries}
        self.assertNotEqual(modes["W22"], ActivationMode.FREEZE)
        style_plan = self.planner.plan(cycle_id=2, impact=self.board.impact("run-1", ["style"]))
        style_modes = {entry.role_id: entry.mode for entry in style_plan.entries}
        self.assertEqual(style_modes["W22"], ActivationMode.FREEZE)
        self.assertEqual(style_modes["W51"], ActivationMode.FREEZE)

    def test_isolated_notation_and_equation_do_not_require_w22(self):
        for change in ("notation", "equation"):
            with self.subTest(change=change):
                plan = self.planner.plan(cycle_id=2, impact=self.board.impact("run-1", [change]))
                self.assertEqual({entry.role_id: entry.mode for entry in plan.entries}["W22"], ActivationMode.FREEZE)

    def test_proof_and_indirect_theorem_dependency_require_w22_check(self):
        for change in ("theorem", "proof"):
            with self.subTest(change=change):
                plan = self.planner.plan(cycle_id=2, impact=self.board.impact("run-1", [change]))
                self.assertEqual({entry.role_id: entry.mode for entry in plan.entries}["W22"], ActivationMode.CHECK)
        definition = self.board.append("run-1", "claims", claim("Definition", "definition", {"section": "1"}))
        self.board.append("run-1", "claims", claim("Dependent theorem", "theorem", {"section": "2"}, [definition["claim_id"]]))
        plan = self.planner.plan(cycle_id=2, impact=self.board.impact("run-1", [definition["claim_id"]]))
        self.assertEqual({entry.role_id: entry.mode for entry in plan.entries}["W22"], ActivationMode.CHECK)

    def test_freeze_coverage_and_finalization_requirements(self):
        plan = self.planner.plan(cycle_id=5, impact=self.board.impact("run-1", []), history={"S20": {"dependencies_changed": True, "last_checked_cycle": 1}})
        modes = {entry.role_id: entry.mode for entry in plan.entries}
        self.assertNotEqual(modes["S20"], ActivationMode.FREEZE)
        self.assertNotEqual(modes["W21"], ActivationMode.FREEZE)
        finish = self.planner.plan(cycle_id=5, impact=self.board.impact("run-1", []), finalization_requested=True)
        finish_modes = {entry.role_id: entry.mode for entry in finish.entries}
        self.assertNotEqual(finish_modes["W51"], ActivationMode.FREEZE)
        self.assertNotEqual(finish_modes["W53"], ActivationMode.FREEZE)
        plateau_finish = self.planner.plan(cycle_id=5, impact=self.board.impact("run-1", []), finalization_requested=True, plateau=True)
        self.assertEqual({entry.role_id: entry.mode for entry in plateau_finish.entries}["W53"], ActivationMode.CHECK)

    def test_modes_use_severity_failures_and_shift_signals(self):
        low = self.planner.plan(cycle_id=2, impact=self.board.impact("run-1", ["style"]))
        high_impact = type(self.board.impact("run-1", ["style"]))((), (), (), (), ("S40", "W41"), 90)
        high = self.planner.plan(cycle_id=2, impact=high_impact)
        self.assertEqual({entry.role_id: entry.mode for entry in low.entries}["W41"], ActivationMode.CHECK)
        self.assertEqual({entry.role_id: entry.mode for entry in high.entries}["W41"], ActivationMode.RUN)
        proof = self.planner.plan(cycle_id=2, impact=self.board.impact("run-1", ["theorem"]))
        self.assertEqual({entry.role_id: entry.mode for entry in proof.entries}["W22"], ActivationMode.CHECK)
        theorem_plateau = self.planner.plan(cycle_id=2, impact=self.board.impact("run-1", ["theorem"]), plateau=True)
        self.assertEqual({entry.role_id: entry.mode for entry in theorem_plateau.entries}["W22"], ActivationMode.CHECK)
        for key, kwargs in (("plateau", {"plateau": True}), ("oscillation", {"oscillation": True}), ("diagnosis", {"diagnostic": True})):
            plan = self.planner.plan(cycle_id=2, impact=high_impact, **kwargs)
            self.assertEqual({entry.role_id: entry.mode for entry in plan.entries}["W41"], ActivationMode.SHIFT, key)
        failed = self.planner.plan(cycle_id=2, impact=high_impact, history={"W41": {"failure_count": 2}})
        self.assertEqual({entry.role_id: entry.mode for entry in failed.entries}["W41"], ActivationMode.SHIFT)

    def test_critical_limits_pause_without_dropping_coverage_and_freeze_is_empty(self):
        proof = ActivationPlanner(PlanningLimits(max_children_per_manager=0)).plan(cycle_id=2, impact=self.board.impact("run-1", ["theorem"]))
        self.assertTrue(proof.paused); self.assertIn("W22", proof.checkpoint["mandatory_roles"])
        finish = ActivationPlanner(PlanningLimits(max_children_per_manager=1)).plan(cycle_id=2, impact=self.board.impact("run-1", []), finalization_requested=True)
        self.assertTrue(finish.paused); self.assertEqual(finish.checkpoint["reason"], "mandatory_coverage_exceeds_limits")
        frozen = next(entry for entry in finish.entries if entry.role_id == "W22")
        self.assertEqual((frozen.estimated_tokens, frozen.wall_time_seconds, frozen.expected_outputs), (0, 0, ()))

    def test_first_cycle_critical_limits_and_missing_mandatory_pause(self):
        theorem = ActivationPlanner(PlanningLimits(max_children_per_manager=0)).plan(cycle_id=0, impact=self.board.impact("run-1", ["theorem"]))
        self.assertTrue(theorem.paused)
        self.assertIn("W22", theorem.checkpoint["mandatory_roles"])
        self.assertEqual(theorem.checkpoint["missing_mandatory"], [])
        finalization = ActivationPlanner(PlanningLimits(max_children_per_manager=1)).plan(cycle_id=0, impact=self.board.impact("run-1", []), finalization_requested=True)
        self.assertTrue(finalization.paused)
        self.assertIn("W53", finalization.checkpoint["mandatory_roles"])
        self.assertEqual(finalization.checkpoint["missing_mandatory"], [])
        entries = [entry for entry in theorem.entries if entry.role_id != "W22"]
        missing = self.planner._within_limits(0, entries, {"W22"})
        self.assertTrue(missing.paused)
        self.assertEqual(missing.checkpoint["reason"], "mandatory_coverage_missing")
        self.assertEqual(missing.checkpoint["missing_mandatory"], ["W22"])

    def test_budget_exhaustion_returns_checkpoint_without_expansion(self):
        tight = ActivationPlanner(PlanningLimits(max_estimated_tokens=1))
        plan = tight.plan(cycle_id=0, impact=self.board.impact("run-1", []))
        self.assertTrue(plan.paused)
        self.assertEqual(plan.checkpoint["reason"], "budget_exhausted")
        self.assertGreater(plan.checkpoint["estimated_tokens"], 1)
        departmental = ActivationPlanner(PlanningLimits(max_active_per_department=1)).plan(cycle_id=0, impact=self.board.impact("run-1", []))
        self.assertTrue(departmental.paused)
        self.assertEqual(departmental.checkpoint["reason"], "department_limit_exhausted")

    def test_activation_map_and_closed_views(self):
        plan = self.planner.plan(cycle_id=1, impact=self.board.impact("run-1", ["theorem"]))
        path = plan.write_activation_map(Path(self.temporary.name) / "activation_map.json")
        self.assertEqual(json.loads(path.read_text())["cycle_id"], 1)
        self.assertIn("budget", json.loads(path.read_text()))
        with self.assertRaises(FileExistsError):
            plan.write_activation_map(path)
        specialist = specialist_view({"task_id": "t"}, excerpts=["x"], dependent_claims=[{"claim_id": "c"}], rubric={"r": 1}, local_history=[{"cycle": 1}])
        self.assertEqual(set(specialist), {"task", "excerpts", "dependent_claims", "rubric", "local_history"})
        self.assertEqual(set(submanager_view({"task_id": "s"}, [{"proposal_id": "p"}])), {"task", "child_proposals"})
        complete = [department_packet(department) for department in DEPARTMENTS]
        no_change = [department_packet(department, "no_change") for department in DEPARTMENTS]
        self.assertEqual(manager_view(ROOT, complete)["department_packets"], complete)
        self.assertEqual(manager_view(ROOT, no_change)["department_packets"], no_change)
        blocked = [dict(packet) for packet in complete]; blocked[0] = department_packet("S10", "blocked")
        self.assertEqual(manager_view(ROOT, blocked)["department_packets"], blocked)
        fixture = json.loads((ROOT / "control/fixtures/m4/department_packet.json").read_text())
        fixture_packets = [department_packet(department) for department in DEPARTMENTS]
        for packet in fixture_packets:
            packet.update({key: fixture[key] for key in ("run_id", "cycle_id", "base_hash")})
        fixture_packets[2] = fixture
        self.assertEqual(manager_view(ROOT, fixture_packets)["department_packets"], fixture_packets)
        for status in (None, "COMPLETE", "NO_CHANGE", "invalid"):
            bad = [dict(packet) for packet in complete]
            if status is None:
                del bad[0]["status"]
            else:
                bad[0]["status"] = status
            with self.subTest(status=status):
                with self.assertRaises(ValueError): manager_view(ROOT, bad)
        extra = [dict(packet) for packet in complete]; extra[0]["extra"] = True
        partial = [dict(packet) for packet in complete]; del partial[0]["created_at"]
        bad_datetime = [dict(packet) for packet in complete]; bad_datetime[0]["created_at"] = "not-a-date-time"
        wrong_department = [dict(packet) for packet in complete]; wrong_department[0]["department_id"] = "S60"
        mismatched_run = [dict(packet) for packet in complete]; mismatched_run[1]["run_id"] = "run-2"
        mismatched_cycle = [dict(packet) for packet in complete]; mismatched_cycle[1]["cycle_id"] = 1
        mismatched_base = [dict(packet) for packet in complete]; mismatched_base[1]["base_hash"] = "b" * 64
        duplicate_packet_id = [dict(packet) for packet in complete]; duplicate_packet_id[1]["packet_id"] = duplicate_packet_id[0]["packet_id"]
        for bad in ([], complete[:-1], complete[:1] * 5, complete[1:] + complete[:1], wrong_department, extra, partial, bad_datetime, mismatched_run, mismatched_cycle, mismatched_base, duplicate_packet_id):
            with self.assertRaises(ValueError): manager_view(ROOT, bad)


if __name__ == "__main__":
    unittest.main()
