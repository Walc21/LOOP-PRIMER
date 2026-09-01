"""Deterministic local validation suite for M7 synthesis merge and validation gates."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from article_loop.gates import verify_gate_report
from article_loop.synthesis import M7Pipeline


class M7SynthesisGatesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="test_m7_synth_")
        self.root = Path(self.temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_pipeline_initialization(self) -> None:
        pipeline = M7Pipeline(self.root)
        self.assertEqual(pipeline.root, self.root)


if __name__ == "__main__":
    unittest.main()
