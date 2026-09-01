"""Deterministic local validation suite for M9 stagnation diagnosis and CAS refocus."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from article_loop.diagnosis import (
    DEFAULT_MDE,
    DEFAULT_WINDOW_SIZE,
    VALID_CLASSIFICATIONS,
    DiagnosisError,
    classify_cycle_progress,
    diagnose_cycle,
    verify_published_diagnosis,
)
from article_loop.refocus import (
    ALLOWED_REFOCUS_CLASSIFICATIONS,
    RefocusError,
    generate_refocus_plan,
)
from article_loop.store import DurableStore


class M9DiagnosisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="test_m9_diag_")
        self.root = Path(self.temp_dir)
        self.store = DurableStore(self.root)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_classifications_catalog(self) -> None:
        self.assertEqual(len(VALID_CLASSIFICATIONS), 7)
        self.assertIn("EVOLVING", VALID_CLASSIFICATIONS)
        self.assertIn("LOCAL_PLATEAU", VALID_CLASSIFICATIONS)
        self.assertIn("GLOBAL_PLATEAU", VALID_CLASSIFICATIONS)
        self.assertIn("OSCILLATING", VALID_CLASSIFICATIONS)
        self.assertIn("REGRESSING", VALID_CLASSIFICATIONS)
        self.assertIn("INCONCLUSIVE", VALID_CLASSIFICATIONS)
        self.assertIn("TECHNICAL_FAILURE", VALID_CLASSIFICATIONS)


if __name__ == "__main__":
    unittest.main()
