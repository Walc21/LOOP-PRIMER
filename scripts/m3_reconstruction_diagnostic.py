#!/usr/bin/env python3
"""Create one offline, hash-bound M3 reconstruction diagnostic.

The command has one allowlisted input: ``input/inbox/artigo.pdf`` below the
repository root.  It never resumes an attempt, starts a model, or accepts a
path, endpoint, command, or credential from its caller.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Any
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime" / "agent" / "skills" / "article-loop" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop.ingestion import (  # noqa: E402
    IngestionError,
    LatexCompileError,
    _compile_latex,
    _lines,
    _normalized_latex,
    _pdf_info,
    _sha256,
    _tool,
)


EXPECTED_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class DiagnosticError(RuntimeError):
    """The strictly local diagnostic could not establish its input boundary."""


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _diagnostics_parent() -> Path:
    current = ROOT
    if current.is_symlink() or not current.is_dir():
        raise DiagnosticError("repository root is unsafe")
    for part in ("runtime", "m3-diagnostics"):
        current = current / part
        if current.exists():
            if current.is_symlink() or not current.is_dir():
                raise DiagnosticError("diagnostic parent is unsafe")
        else:
            current.mkdir(mode=0o700)
            _fsync_directory(current.parent)
    return current


def _input_pdf(expected_sha256: str) -> Path:
    if EXPECTED_SHA256.fullmatch(expected_sha256) is None:
        raise DiagnosticError("expected PDF SHA-256 is invalid")
    path = ROOT / "input" / "inbox" / "artigo.pdf"
    try:
        info = path.lstat()
    except OSError as error:
        raise DiagnosticError("allowlisted input PDF is unavailable") from error
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_size == 0:
        raise DiagnosticError("allowlisted input PDF is unsafe")
    if _sha256(path) != expected_sha256:
        raise DiagnosticError("allowlisted input PDF SHA-256 differs from expectation")
    return path


def _write_report(directory: Path, report: dict[str, Any]) -> None:
    path = directory / "report.json"
    payload = json.dumps(report, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    _fsync_directory(directory)


def diagnose(expected_pdf_sha256: str) -> dict[str, Any]:
    """Rebuild M3 extraction transiently and persist metadata only once."""
    pdf = _input_pdf(expected_pdf_sha256)
    parent = _diagnostics_parent()
    diagnostic_id = "diagnostic-" + str(uuid4())
    directory = parent / diagnostic_id
    os.mkdir(directory, mode=0o700)
    _fsync_directory(parent)
    report: dict[str, Any] = {
        "diagnostic_id": diagnostic_id,
        "input_sha256": expected_pdf_sha256,
        "reconstructed_sha256": None,
        "classification": "LATEX_RECONSTRUCTION_UNSAFE",
        "returncode": None,
        "duration_ms": 0,
        "output_bytes": 0,
        "output_sha256": hashlib.sha256(b"").hexdigest(),
    }
    try:
        with tempfile.TemporaryDirectory(prefix=".m3-diagnostic-work-", dir=parent) as raw_workspace:
            workspace = Path(raw_workspace)
            pages = int(_pdf_info(pdf)["Pages"])
            text_pages: list[str] = []
            for page in range(1, pages + 1):
                extracted = workspace / f"page-{page}.txt"
                _tool(
                    ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), str(extracted)],
                    error="PDF text extraction failed",
                )
                text_pages.append(extracted.read_text(encoding="utf-8", errors="strict"))
            lines, *_ = _lines(text_pages)
            reconstructed = workspace / "reconstructed.tex"
            reconstructed.write_text(_normalized_latex(lines, []), encoding="ascii", newline="\n")
            report["reconstructed_sha256"] = _sha256(reconstructed)
            try:
                report.update(_compile_latex(reconstructed, workspace))
            except LatexCompileError as error:
                report.update(error.diagnostic())
    except IngestionError:
        # Tool diagnostics can contain untrusted PDF-derived output.  The
        # durable report intentionally records only this safe classification.
        pass
    _write_report(directory, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-pdf-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        report = diagnose(args.expected_pdf_sha256)
    except DiagnosticError as error:
        print(json.dumps({"status": "blocked", "cause": str(error)}, sort_keys=True))
        return 2
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
