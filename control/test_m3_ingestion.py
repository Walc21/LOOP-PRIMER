"""Offline M3 ingestion tests using a locally generated, non-article PDF."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))
from article_loop import IngestionError, SourceReadyError, ingest


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        for relative in ("input/inbox", "artifacts/original", "artifacts/extracted", "artifacts/rendered",
                         "versions/champion", "workspaces", "config"):
            (self.root / relative).mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "config/gates.yaml", self.root / "config/gates.yaml")

    def tearDown(self):
        self.temporary.cleanup()

    def fixture(self, name="artigo.pdf"):
        postscript = self.root / "fixture.ps"
        postscript.write_text("%!PS\n/Courier findfont 18 scalefont setfont 72 700 moveto (Fixture Equation x = 1 [1]) show showpage\n")
        subprocess.run(["gs", "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", f"-sOutputFile={self.root / 'input/inbox' / name}", str(postscript)], check=True)
        return self.root / "input/inbox" / name

    def test_digital_pdf_creates_traceable_champion_and_is_idempotent(self):
        pdf = self.fixture()
        result = ingest(self.root)
        self.assertEqual("created", result["status"])
        champion = self.root / "versions/champion/v0000"
        provenance = json.loads((champion / "ingestion-manifest.json").read_text())
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        self.assertEqual(digest, provenance["input_sha256"])
        self.assertTrue((self.root / "artifacts/original" / digest / "document.pdf").is_file())
        self.assertTrue((self.root / "artifacts/extracted" / digest / "coordinates.html").is_file())
        self.assertTrue((self.root / "artifacts/rendered" / digest / "pages/page-1.png").is_file())
        self.assertTrue((champion / "source/coordinates.html").is_file())
        self.assertEqual("idempotent", ingest(self.root)["status"])

    def test_corrupted_multiple_and_ambiguous_pdf_are_rejected(self):
        (self.root / "input/inbox/artigo.pdf").write_bytes(b"not a PDF")
        with self.assertRaisesRegex(IngestionError, "invalid PDF"):
            ingest(self.root)
        (self.root / "input/inbox/artigo.pdf").unlink()
        self.fixture()
        self.fixture("another.pdf")
        with self.assertRaisesRegex(IngestionError, "multiple"):
            ingest(self.root)

    def test_scanned_without_ocr_fails_with_actionable_issue(self):
        postscript = self.root / "blank.ps"
        postscript.write_text("%!PS\n72 72 moveto 200 0 rlineto stroke showpage\n")
        subprocess.run(["gs", "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", f"-sOutputFile={self.root / 'input/inbox/artigo.pdf'}", str(postscript)], check=True)
        with self.assertRaisesRegex(SourceReadyError, "text_coverage"):
            ingest(self.root)
        self.assertFalse((self.root / "versions/champion/v0000").exists())

    def test_malicious_zip_hash_divergence_and_publish_failure_are_safe(self):
        self.fixture()
        with zipfile.ZipFile(self.root / "input/inbox/source.zip", "w") as archive:
            archive.writestr("../escape.tex", "\\documentclass{article}\\begin{document}")
        with self.assertRaisesRegex(IngestionError, "unsafe path"):
            ingest(self.root)
        (self.root / "input/inbox/source.zip").unlink()
        digest = hashlib.sha256((self.root / "input/inbox/artigo.pdf").read_bytes()).hexdigest()
        target = self.root / "artifacts/original" / digest
        target.mkdir()
        (target / "document.pdf").write_bytes(b"wrong")
        with self.assertRaisesRegex(IngestionError, "hash diverges"):
            ingest(self.root)
        shutil.rmtree(target)
        with self.assertRaisesRegex(RuntimeError, "fault"):
            ingest(self.root, fault=lambda stage: (_ for _ in ()).throw(RuntimeError("fault")) if stage == "before_champion_publish" else None)
        self.assertFalse((self.root / "versions/champion/v0000").exists())

    def test_valid_source_zip_is_preferred(self):
        self.fixture()
        with zipfile.ZipFile(self.root / "input/inbox/source.zip", "w") as archive:
            archive.writestr("paper.tex", "\\documentclass{article}\n\\begin{document}Fixture\\end{document}\n")
        ingest(self.root)
        provenance = json.loads((self.root / "versions/champion/v0000/ingestion-manifest.json").read_text())
        self.assertEqual("SOURCE_ZIP", provenance["source_mode"])
        self.assertTrue((self.root / "versions/champion/v0000/latex-source/paper.tex").is_file())
