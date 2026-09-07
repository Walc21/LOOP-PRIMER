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
from unittest.mock import patch

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

    def fixture(self, name="artigo.pdf", text="Fixture Equation x = 1 [1]"):
        postscript = self.root / "fixture.ps"
        postscript.write_text(
            f"%!PS\n/Courier findfont 18 scalefont setfont 72 700 moveto ({text}) show showpage\n"
        )
        subprocess.run(["gs", "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", f"-sOutputFile={self.root / 'input/inbox' / name}", str(postscript)], check=True)
        return self.root / "input/inbox" / name

    def source_zip(self, *members):
        path = self.root / "input/inbox/source.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name, contents in members:
                archive.writestr(name, contents)
        return path

    @staticmethod
    def valid_tex(body="Fixture"):
        return f"\\documentclass{{article}}\n\\begin{{document}}{body}\\end{{document}}\n"

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
        self.source_zip(("paper.tex", self.valid_tex()))
        result = ingest(self.root)
        provenance = json.loads((self.root / "versions/champion/v0000/ingestion-manifest.json").read_text())
        self.assertEqual("SOURCE_ZIP", provenance["source_mode"])
        self.assertTrue((self.root / "versions/champion/v0000/latex-source/paper.tex").is_file())
        self.assertEqual("idempotent", ingest(self.root)["status"])
        self.assertEqual(3, len(DurableStore(self.root).read_events(result["run_id"])))

    def test_altered_source_zip_after_success_is_rejected(self):
        self.fixture(); self.source_zip(("paper.tex", self.valid_tex("first"))); ingest(self.root)
        self.source_zip(("paper.tex", self.valid_tex("second")))
        with self.assertRaisesRegex(IngestionError, "source.zip identity"):
            ingest(self.root)

    def test_removed_source_zip_after_success_is_rejected(self):
        self.fixture(); source = self.source_zip(("paper.tex", self.valid_tex())); ingest(self.root)
        source.unlink()
        with self.assertRaisesRegex(IngestionError, "source.zip identity"):
            ingest(self.root)

    def test_added_source_zip_after_pdf_only_success_is_rejected(self):
        self.fixture(); ingest(self.root)
        self.source_zip(("paper.tex", self.valid_tex()))
        with self.assertRaisesRegex(IngestionError, "source.zip identity"):
            ingest(self.root)

    def test_altered_source_zip_after_source_ready_crash_is_rejected(self):
        self.fixture(); self.source_zip(("paper.tex", self.valid_tex("first")))
        with self.assertRaisesRegex(RuntimeError, "before_champion_publish"):
            ingest(self.root, fault=lambda stage: (_ for _ in ()).throw(RuntimeError(stage)) if stage == "before_champion_publish" else None)
        self.source_zip(("paper.tex", self.valid_tex("second")))
        with self.assertRaisesRegex(IngestionError, "source.zip identity"):
            ingest(self.root)
        self.assertFalse((self.root / "versions/champion/v0000").exists())

    def test_removed_source_zip_after_source_ready_crash_is_rejected(self):
        self.fixture(); source = self.source_zip(("paper.tex", self.valid_tex()))
        with self.assertRaisesRegex(RuntimeError, "before_champion_publish"):
            ingest(self.root, fault=lambda stage: (_ for _ in ()).throw(RuntimeError(stage)) if stage == "before_champion_publish" else None)
        source.unlink()
        with self.assertRaisesRegex(IngestionError, "source.zip identity"):
            ingest(self.root)
        self.assertFalse((self.root / "versions/champion/v0000").exists())

    def test_added_source_zip_during_source_ready_recovery_is_rejected(self):
        self.fixture()
        with self.assertRaisesRegex(RuntimeError, "before_champion_publish"):
            ingest(self.root, fault=lambda stage: (_ for _ in ()).throw(RuntimeError(stage)) if stage == "before_champion_publish" else None)
        self.source_zip(("paper.tex", self.valid_tex()))
        with self.assertRaisesRegex(IngestionError, "source.zip identity"):
            ingest(self.root)
        self.assertFalse((self.root / "versions/champion/v0000").exists())

    def test_source_zip_hashes_in_events_and_champion_coincide(self):
        self.fixture(); source = self.source_zip(("paper.tex", self.valid_tex()))
        result = ingest(self.root)
        expected = {
            "input_sha256": result["sha256"], "source_zip_present": True,
            "source_zip_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "source_zip_size_bytes": source.stat().st_size, "source_mode": "SOURCE_ZIP",
        }
        events = DurableStore(self.root).read_events(result["run_id"])
        for event in events[1:]:
            self.assertEqual(expected, event["payload"]["source_identity"])
            self.assertEqual(expected["source_zip_sha256"], event["payload"]["source_zip_sha256"])
        provenance = json.loads((self.root / "versions/champion/v0000/ingestion-manifest.json").read_text())
        self.assertEqual(expected, provenance["source_identity"])
        self.assertEqual(expected["source_zip_sha256"], provenance["source_zip"]["sha256"])
        self.assertEqual(expected["source_zip_size_bytes"], provenance["source_zip"]["size_bytes"])

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

    def test_author_year_reference_is_inventory_without_lowercase_false_candidate(self):
        from article_loop.ingestion import _lines

        lines, _, references, _, candidates = _lines(
            ["Euler 1748\nauthor 2024\nDOI:10.1000/example"]
        )
        self.assertEqual([lines[0], lines[2]], references)
        self.assertEqual(references, candidates)

        self.fixture(text="Euler 1748")
        result = ingest(self.root)
        snapshot = DurableStore(self.root).snapshot(result["run_id"])
        self.assertEqual(State.SOURCE_READY.value, snapshot["state"])
        normalized = json.loads(
            (self.root / "versions/champion/v0000/source/normalized.json").read_text()
        )
        self.assertEqual(normalized["references"], normalized["reference_candidates"])

    def test_reconstruction_is_ascii_safe_bounded_and_has_no_pdf_commands(self):
        from article_loop.ingestion import MAX_TEX_LINE_CHARS, _normalized_latex
        untrusted = (
            "alpha α ≤ ∑ √ “smart quotes” 😀 \\input{never} $ & # ^ _ % ~ "
            "\x00\x1f\x7f\x85" + "x" * 1_000
        )
        rendered = _normalized_latex([{"text": untrusted}], [])
        self.assertTrue(rendered.isascii())
        self.assertEqual(rendered, _normalized_latex([{"text": untrusted}], []))
        self.assertTrue(all(len(line) <= MAX_TEX_LINE_CHARS for line in rendered.splitlines()))
        self.assertIn(r"\hbadness=10000", rendered)
        self.assertIn(r"\hfuzz=10000pt", rendered)
        for marker in ("[U+03B1]", "[U+2264]", "[U+2211]", "[U+221A]", "[U+1F600]", "[CTRL-U+0000]", "[CTRL-U+0085]"):
            self.assertIn(marker, rendered)
        self.assertNotIn("\\input", rendered)
        self.assertIn(r"\textbackslash{}input\{never\}", rendered)

    def test_compiler_failure_stays_ingested_with_limited_hash_bound_diagnostic(self):
        from article_loop.ingestion import LatexCompileError
        pdf = self.fixture()
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        failure = LatexCompileError(
            "LATEX_EXIT_NONZERO", returncode=1, duration_ms=12,
            output_bytes=44, output_sha256="a" * 64,
        )
        with patch("article_loop.ingestion._compile_latex", side_effect=failure):
            with self.assertRaises(LatexCompileError) as raised:
                ingest(self.root)
        report = raised.exception.diagnostic()
        self.assertEqual({"classification", "returncode", "duration_ms", "output_bytes", "output_sha256"}, set(report))
        self.assertEqual("LATEX_EXIT_NONZERO", report["classification"])
        self.assertNotIn("Fixture Equation", str(raised.exception))
        events = DurableStore(self.root).read_events(f"ingest-{digest}")
        self.assertEqual([State.NEW.value, State.INGESTED.value], [event["state_to"] for event in events])
        self.assertFalse((self.root / "versions/champion/v0000").exists())
        self.assertFalse((self.root / "versions/challengers").exists())
        self.assertFalse((self.root / "state/reservations").exists())
        self.assertFalse((self.root / "state/receipts").exists())

    def test_hash_bound_offline_diagnostic_writes_metadata_only(self):
        import importlib.util
        script = ROOT / "scripts/m3_reconstruction_diagnostic.py"
        spec = importlib.util.spec_from_file_location("m3_reconstruction_diagnostic_test", script)
        assert spec and spec.loader
        diagnostic = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(diagnostic)
        pdf = self.fixture()
        expected = hashlib.sha256(pdf.read_bytes()).hexdigest()
        with patch.object(diagnostic, "ROOT", self.root):
            report = diagnostic.diagnose(expected)
        report_path = self.root / "runtime/m3-diagnostics" / report["diagnostic_id"] / "report.json"
        self.assertTrue(report_path.is_file())
        self.assertEqual(report, json.loads(report_path.read_text(encoding="utf-8")))
        self.assertEqual(expected, report["input_sha256"])
        self.assertEqual({"diagnostic_id", "input_sha256", "reconstructed_sha256", "classification", "returncode", "duration_ms", "output_bytes", "output_sha256"}, set(report))
        self.assertNotIn("Fixture Equation", report_path.read_text(encoding="utf-8"))

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
        source = self.root / "input/inbox/source.zip"
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("paper.tex", "\\documentclass{article}\n\\begin{document}\n\\def\\broken{\n\\end{document}\n")
        ingest(self.root)
        champion = self.root / "versions/champion/v0000"
        provenance = json.loads((champion / "ingestion-manifest.json").read_text())
        normalized = json.loads((champion / "source/normalized.json").read_text())
        self.assertEqual("PDF_ONLY_RECONSTRUCTION", provenance["source_mode"])
        self.assertFalse((champion / "latex-source").exists())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), provenance["source_zip"]["sha256"])
        self.assertEqual(source.stat().st_size, provenance["source_zip"]["size_bytes"])
        self.assertIn("SOURCE_ZIP_STRUCTURALLY_INVALID", [issue["code"] for issue in normalized["issues"]])

    def test_valid_main_with_truncated_tex_member_falls_back_to_pdf_only(self):
        self.fixture()
        source = self.source_zip(
            ("main.tex", self.valid_tex()),
            ("appendix.tex", "\\documentclass{article}\n\\begin{document}\n\\def\\broken{\n\\end{document}\n"),
        )
        ingest(self.root)
        champion = self.root / "versions/champion/v0000"
        provenance = json.loads((champion / "ingestion-manifest.json").read_text())
        normalized = json.loads((champion / "source/normalized.json").read_text())
        self.assertEqual("PDF_ONLY_RECONSTRUCTION", provenance["source_mode"])
        self.assertFalse((champion / "latex-source").exists())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), provenance["source_zip"]["sha256"])
        self.assertEqual(source.stat().st_size, provenance["source_zip"]["size_bytes"])
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
