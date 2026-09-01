"""Deterministic local validation suite for M3 ingestion and baseline candidate."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from article_loop import DurableStore, State
from article_loop.ingestion import IngestionError, ingest


class M3IngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="test_m3_ingest_")
        self.root = Path(self.temp_dir)
        self.store = DurableStore(self.root)
        self.inbox = self.root / "input" / "inbox"
        self.inbox.mkdir(parents=True, exist_ok=True)

        for d in [
            "artifacts/original", "artifacts/extracted", "artifacts/rendered",
            "state/events", "state/snapshots", "state/checkpoints", "state/claims",
            "state/issues", "state/decisions", "state/locks",
            "versions/champion", "versions/challengers", "versions/pareto",
            "versions/rejected", "workspaces", "reports", "logs", "config/schemas",
        ]:
            (self.root / d).mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_missing_input_pdf_raises_ingestion_error(self) -> None:
        with self.assertRaises(IngestionError):
            ingest(self.root)

    def test_corrupted_input_pdf_raises_ingestion_error(self) -> None:
        pdf_path = self.inbox / "artigo.pdf"
        pdf_path.write_bytes(b"not a valid pdf content")

        with self.assertRaises(IngestionError):
            ingest(self.root)


if __name__ == "__main__":
    unittest.main()
