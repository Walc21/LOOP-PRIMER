"""Deterministic local validation suite for M5 blackboard and activation planner."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from article_loop.activation import ActivationPlanner
from article_loop.blackboard import Blackboard


class M5BlackboardActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="test_m5_bb_")
        self.root = Path(self.temp_dir)
        self.blackboard = Blackboard(self.root)
        self.planner = ActivationPlanner()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_blackboard_appends_and_reads_claims_idempotently(self) -> None:
        run_id = "run-bb-001"
        claim_data = {
            "record_id": "claim-001",
            "text": "Core lemma statement",
            "kind": "theorem",
            "section": "proof",
            "severity": "CRITICAL",
            "status": "active",
            "cycle_id": 0,
            "source_hash": "a" * 64,
        }
        self.blackboard.append(run_id, "claims", claim_data)
        claims = self.blackboard.read(run_id, "claims")
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["record_id"], "claim-001")

    def test_activation_planner_cycle_zero_activates_manager_and_submanagers(self) -> None:
        run_id = "run-act-001"
        plan = self.planner.plan(
            self.root,
            run_id=run_id,
            cycle_id=0,
            base_hash="b" * 64,
        )
        self.assertFalse(plan.paused)
        self.assertIn("M00", [r["role_id"] for r in plan.activation_map["roles"]])


if __name__ == "__main__":
    unittest.main()
