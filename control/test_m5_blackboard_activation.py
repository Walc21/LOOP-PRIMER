"""Offline M5 tests: append-only memory, impact and sparse activation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))

from article_loop import (ActivationMode, ActivationPlanner, Blackboard,
                          BlackboardError, PlanningLimits, manager_view,
                          specialist_view, submanager_view)


SOURCE = "a" * 64


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
        self.assertEqual({entry.role_id for entry in first.entries if entry.role_id.startswith("S") and entry.mode != ActivationMode.FREEZE}, {"S10", "S20", "S30", "S40", "S50"})

    def test_new_proof_requires_w22_and_style_stays_sparse(self):
        proof_plan = self.planner.plan(cycle_id=2, impact=self.board.impact("run-1", ["theorem"]))
        modes = {entry.role_id: entry.mode for entry in proof_plan.entries}
        self.assertNotEqual(modes["W22"], ActivationMode.FREEZE)
        style_plan = self.planner.plan(cycle_id=2, impact=self.board.impact("run-1", ["style"]))
        style_modes = {entry.role_id: entry.mode for entry in style_plan.entries}
        self.assertEqual(style_modes["W22"], ActivationMode.FREEZE)
        self.assertEqual(style_modes["W51"], ActivationMode.FREEZE)

    def test_freeze_coverage_and_finalization_requirements(self):
        plan = self.planner.plan(cycle_id=5, impact=self.board.impact("run-1", []), history={"S20": {"dependencies_changed": True, "last_checked_cycle": 1}})
        modes = {entry.role_id: entry.mode for entry in plan.entries}
        self.assertNotEqual(modes["S20"], ActivationMode.FREEZE)
        self.assertNotEqual(modes["W21"], ActivationMode.FREEZE)
        finish = self.planner.plan(cycle_id=5, impact=self.board.impact("run-1", []), finalization_requested=True)
        finish_modes = {entry.role_id: entry.mode for entry in finish.entries}
        self.assertNotEqual(finish_modes["W51"], ActivationMode.FREEZE)
        self.assertNotEqual(finish_modes["W53"], ActivationMode.FREEZE)

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
        self.assertEqual(len(manager_view([{"department_id": f"S{i}0"} for i in range(1, 6)])["department_packets"]), 5)
        with self.assertRaises(ValueError):
            manager_view([])


if __name__ == "__main__":
    unittest.main()
