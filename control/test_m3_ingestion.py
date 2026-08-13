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

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))
from article_loop import IngestionError, SourceReadyError, ingest
from article_loop.store import DurableStore
from article_loop.state_machine import State


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
        schema = json.loads((ROOT / "config/schemas/candidate-manifest.schema.json").read_text())
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER
        ).validate(json.loads((champion / "manifest.json").read_text()))
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

    def test_frozen_pdf_survives_inbox_swap_and_event_log_is_canonical(self):
        pdf = self.fixture(); original = pdf.read_bytes()
        def swap(stage):
            if stage == "after_input_freeze":
                pdf.write_bytes(b"changed after freeze")
        result = ingest(self.root, fault=swap)
        digest = result["sha256"]
        self.assertEqual(hashlib.sha256(original).hexdigest(), digest)
        self.assertEqual(original, (self.root / "artifacts/original" / digest / "document.pdf").read_bytes())
        store = DurableStore(self.root)
        self.assertEqual(["NEW", "INGESTED", "SOURCE_READY"], [event["state_to"] for event in store.read_events(result["run_id"])])
        self.assertEqual("SOURCE_READY", store.rebuild_snapshot(result["run_id"])["state"])

    def test_tampering_never_returns_idempotent(self):
        result = ingest(self.root) if self.fixture() else None
        champion = self.root / "versions/champion/v0000"
        (champion / "baseline.pdf").write_bytes(b"tampered")
        with self.assertRaisesRegex(IngestionError, "baseline hash"):
            ingest(self.root)
        # Restore via a fresh fixture/project, then exercise derived and source files.
        self.temporary.cleanup(); self.setUp(); self.fixture(); result = ingest(self.root)
        digest = result["sha256"]
        (self.root / "artifacts/extracted" / digest / "text.txt").write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(IngestionError, "manifest hash"):
            ingest(self.root)

    def test_rendered_and_symlink_tampering_are_rejected(self):
        self.fixture(); result = ingest(self.root); digest = result["sha256"]
        (self.root / "artifacts/rendered" / digest / "pages/page-1.png").write_bytes(b"tampered")
        with self.assertRaisesRegex(IngestionError, "manifest hash"):
            ingest(self.root)
        self.temporary.cleanup(); self.setUp(); self.fixture(); ingest(self.root)
        champion = self.root / "versions/champion/v0000"
        (champion / "source/text.txt").unlink()
        (champion / "source/text.txt").symlink_to("/etc/passwd")
        with self.assertRaisesRegex(IngestionError, "symlink"):
            ingest(self.root)

    def test_publication_faults_recover_without_duplicate_events(self):
        self.fixture()
        for boundary in ("before_original_publish", "after_original_publish", "before_extracted_publish", "after_extracted_publish", "before_rendered_publish", "after_rendered_publish", "before_champion_publish", "after_champion_publish", "before_ingested_record", "after_ingested_record", "before_source_ready_record", "after_source_ready_record"):
            with self.subTest(boundary=boundary):
                with self.assertRaisesRegex(RuntimeError, boundary):
                    ingest(self.root, fault=lambda stage, wanted=boundary: (_ for _ in ()).throw(RuntimeError(stage)) if stage == wanted else None)
                result = ingest(self.root)
                events = DurableStore(self.root).read_events(result["run_id"])
                self.assertEqual(3, len(events))
                self.assertEqual(State.SOURCE_READY.value, events[-1]["state_to"])
                shutil.rmtree(self.root / "versions/champion/v0000")
                for path in (self.root / "artifacts/original", self.root / "artifacts/extracted", self.root / "artifacts/rendered"):
                    shutil.rmtree(path)
                    path.mkdir()
                for path in (self.root / "state/events", self.root / "state/snapshots"):
                    shutil.rmtree(path); path.mkdir()

    def test_gate_failure_has_no_source_ready_and_zip_cases_are_rejected(self):
        self.fixture()
        gates = self.root / "config/gates.yaml"
        gates.write_text(gates.read_text().replace("visual_minimum_nonblank_ratio: 0.001", "visual_minimum_nonblank_ratio: 1.0"))
        with self.assertRaises(SourceReadyError): ingest(self.root)
        digest = hashlib.sha256((self.root / "input/inbox/artigo.pdf").read_bytes()).hexdigest()
        self.assertEqual(["NEW", "INGESTED"], [event["state_to"] for event in DurableStore(self.root).read_events(f"ingest-{digest}")])
        self.assertTrue((self.root / "artifacts/original" / digest / "document.pdf").is_file())
        gates.write_text((ROOT / "config/gates.yaml").read_text())
        ingest(self.root)
        self.assertEqual(
            ["NEW", "INGESTED", "SOURCE_READY"],
            [event["state_to"] for event in DurableStore(self.root).read_events(f"ingest-{digest}")],
        )
        with zipfile.ZipFile(self.root / "input/inbox/source.zip", "w") as archive:
            archive.writestr("a.tex", "x"); archive.writestr("a.tex", "x")
        with self.assertRaisesRegex(IngestionError, "duplicate"): ingest(self.root)

    def test_latex_escaping_and_page_mapping(self):
        from article_loop.ingestion import _latex_escape, _lines
        self.assertEqual(r"\textbackslash{}\{\}\$\&\#\textasciicircum{}\_\%\textasciitilde{}", _latex_escape("\\{}$&#^_%~"))
        lines, *_ = _lines(["first", "second"])
        self.assertEqual([1, 2], [line["page"] for line in lines])

    def test_source_zip_is_frozen_before_later_inbox_change(self):
        self.fixture()
        source = self.root / "input/inbox/source.zip"
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("paper.tex", "\\documentclass{article}\n\\begin{document}A\\end{document}\n")
        def mutate(stage):
            if stage == "after_source_zip_freeze":
                source.write_bytes(b"different archive")
        ingest(self.root, fault=mutate)
        self.assertTrue((self.root / "versions/champion/v0000/latex-source/paper.tex").exists())

    def test_structurally_invalid_latex_falls_back_with_explicit_issue(self):
        self.fixture()
        with zipfile.ZipFile(self.root / "input/inbox/source.zip", "w") as archive:
            archive.writestr("paper.tex", "\\documentclass{article}\n\\begin{document}\n\\def\\broken{\n\\end{document}\n")
        ingest(self.root)
        champion = self.root / "versions/champion/v0000"
        provenance = json.loads((champion / "ingestion-manifest.json").read_text())
        normalized = json.loads((champion / "source/normalized.json").read_text())
        self.assertEqual("PDF_ONLY_RECONSTRUCTION", provenance["source_mode"])
        self.assertFalse((champion / "latex-source").exists())
        self.assertIn("SOURCE_ZIP_STRUCTURALLY_INVALID", [issue["code"] for issue in normalized["issues"]])

    def test_managed_parent_symlinks_are_rejected_without_external_writes(self):
        for relative in ("input/inbox", "workspaces", "artifacts/original", "artifacts/extracted", "artifacts/rendered", "versions/champion", "config", "state"):
            with self.subTest(relative=relative):
                self.fixture()
                outside = self.root / "outside"
                outside.mkdir(exist_ok=True)
                managed = self.root / relative
                managed.mkdir(parents=True, exist_ok=True)
                if relative == "input/inbox":
                    shutil.copy2(managed / "artigo.pdf", outside / "artigo.pdf")
                shutil.rmtree(managed)
                managed.symlink_to(outside, target_is_directory=True)
                before = sorted(item.relative_to(outside).as_posix() for item in outside.rglob("*"))
                with self.assertRaisesRegex(IngestionError, "symlink"):
                    ingest(self.root)
                self.assertEqual(before, sorted(item.relative_to(outside).as_posix() for item in outside.rglob("*")))
                managed.unlink()
                managed.mkdir(parents=True)
