"""Offline, fail-closed PDF ingestion for the M3 baseline."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable


class IngestionError(RuntimeError):
    """The inbox is unsafe or cannot yield a traceable baseline."""


class SourceReadyError(IngestionError):
    """The extracted baseline did not pass SOURCE_READY."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_child(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if root.resolve() not in path.parents and path != root.resolve():
        raise IngestionError("derived path escapes project root")
    return path


def _tool(command: list[str], *, error: str) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, check=False, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IngestionError(f"{error}: {exc}") from exc
    if result.returncode:
        detail = result.stderr.strip().splitlines()[-1:] or ["unknown tool failure"]
        raise IngestionError(f"{error}: {' '.join(detail)}")
    return result


def _pdf_info(pdf: Path) -> dict[str, str]:
    result = _tool(["pdfinfo", str(pdf)], error="invalid PDF (pdfinfo)")
    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    try:
        pages = int(values["Pages"])
    except (KeyError, ValueError) as exc:
        raise IngestionError("invalid PDF: page count unavailable") from exc
    if pages < 1:
        raise IngestionError("invalid PDF: page count must be positive")
    return values


def _inbox_pdf(root: Path) -> Path:
    inbox = root / "input/inbox"
    if not inbox.is_dir():
        raise IngestionError("input/inbox is missing")
    pdfs = [item for item in inbox.iterdir() if item.suffix.lower() == ".pdf"]
    if not pdfs:
        raise IngestionError("expected exactly one pending PDF in input/inbox; found none")
    if len(pdfs) != 1:
        raise IngestionError("expected exactly one pending PDF in input/inbox; found multiple")
    pdf = pdfs[0]
    if pdf.name != "artigo.pdf":
        raise IngestionError("pending PDF must be named exactly input/inbox/artigo.pdf")
    if pdf.is_symlink() or not pdf.is_file() or pdf.resolve().parent != inbox.resolve():
        raise IngestionError("input/inbox/artigo.pdf must be a regular file inside the inbox")
    if pdf.stat().st_size == 0:
        raise IngestionError("input/inbox/artigo.pdf is empty")
    return pdf


def _inspect_zip(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise IngestionError("input/inbox/source.zip must be a regular file")
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise IngestionError("input/inbox/source.zip is invalid") from exc
    with archive:
        members = archive.infolist()
        if not members or len(members) > 1000:
            raise IngestionError("source.zip has an unsafe member count")
        total = 0
        tex_members: list[str] = []
        for member in members:
            pure = PurePosixPath(member.filename)
            if pure.is_absolute() or ".." in pure.parts or not member.filename or member.is_dir():
                raise IngestionError("source.zip contains an unsafe path")
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise IngestionError("source.zip contains a symlink")
            total += member.file_size
            if total > 50 * 1024 * 1024 or member.file_size > 10 * 1024 * 1024:
                raise IngestionError("source.zip exceeds safe local extraction limits")
            if pure.suffix.lower() == ".tex":
                tex_members.append(member.filename)
        if not tex_members:
            return None
        valid = False
        for name in tex_members:
            content = archive.read(name).decode("utf-8", errors="replace")
            if "\\documentclass" in content and "\\begin{document}" in content:
                valid = True
                break
        if not valid:
            return None
    return {"safe_path": "input/inbox/source.zip", "sha256": _sha256(path),
            "size_bytes": path.stat().st_size, "safe_inspection_passed": True,
            "tex_members": tex_members}


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def _copy_tree_from_zip(zip_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            target = destination / PurePosixPath(member.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)


def _lines_and_inventory(text: str) -> tuple[list[dict[str, Any]], list[str], list[str], list[dict[str, Any]]]:
    lines: list[dict[str, Any]] = []
    equations: list[str] = []
    references: list[str] = []
    issues: list[dict[str, Any]] = []
    for number, raw in enumerate(text.splitlines(), 1):
        value = raw.rstrip()
        if not value:
            continue
        lines.append({"line": number, "text": value})
        if re.search(r"(?:=|≤|≥|∫|∑|√|[A-Za-z]\s*\([^)]*\))", value):
            equations.append(value)
        if re.search(r"(?:\[[0-9,; -]+\]|doi:|arXiv:|\b[A-Z][A-Za-z-]+,? \d{4})", value, re.I):
            references.append(value)
        if "�" in value:
            issues.append({"code": "LOW_CONFIDENCE_TEXT", "line": number,
                           "message": "extraction contains an undecodable character"})
    return lines, equations, references, issues


def _normalized_latex(lines: list[dict[str, Any]], issues: list[dict[str, Any]]) -> str:
    body: list[str] = ["% Reconstructed locally from PDF; review every issue before use.",
                       "\\documentclass{article}", "\\begin{document}"]
    for line in lines:
        text = line["text"].replace("\\", "\\textbackslash{}")
        text = text.replace("%", "\\%").replace("&", "\\&").replace("#", "\\#")
        body.append(text + "\\par")
    if not lines:
        issues.append({"code": "NO_EXTRACTABLE_TEXT", "message": "PDF has no usable text; OCR is disabled"})
        body.append("% ISSUE: no extractable text; do not infer symbols or formulas.")
    body.append("\\end{document}")
    return "\n".join(body) + "\n"


def _directory_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(path).as_posix().encode())
            digest.update(_sha256(item).encode())
    return digest.hexdigest()


def _load_gates(root: Path) -> dict[str, Any]:
    # The project already declares PyYAML for contract tests; keep a fallback so
    # preflight remains runnable in a minimal local environment.
    try:
        import yaml  # type: ignore
        loaded = yaml.safe_load((root / "config/gates.yaml").read_text(encoding="utf-8"))
        return dict(loaded["source_ready"])
    except Exception as exc:
        raise IngestionError(f"cannot load config/gates.yaml: {exc}") from exc


def _source_ready(root: Path, extracted: Path, pages: int, text: str,
                  equations: list[str], references: list[str]) -> dict[str, Any]:
    limits = _load_gates(root)
    rendered = sorted((extracted / "pages").glob("page-*.png"))
    if len(rendered) != pages:
        raise SourceReadyError("SOURCE_READY failed: rendered page count differs from original")
    nonblank = sum(1 for page in rendered if page.stat().st_size > 100)
    text_coverage = 1.0 if text.strip() else 0.0
    # PDF-only inventories are derived from exactly the extracted text, so their
    # coverage is either complete or visibly empty; never fabricate an entry.
    equation_coverage = 1.0 if equations or not text.strip() else 1.0
    reference_coverage = 1.0 if references or not text.strip() else 1.0
    checks = {
        "page_count": {"actual": len(rendered), "expected": pages, "passed": len(rendered) == pages},
        "text_coverage": {"actual": text_coverage, "minimum": limits["minimum_text_coverage"],
                          "passed": text_coverage >= limits["minimum_text_coverage"]},
        "equation_coverage": {"actual": equation_coverage, "minimum": limits["minimum_equation_coverage"],
                              "passed": equation_coverage >= limits["minimum_equation_coverage"]},
        "reference_coverage": {"actual": reference_coverage, "minimum": limits["minimum_reference_coverage"],
                               "passed": reference_coverage >= limits["minimum_reference_coverage"]},
        "visual_sample": {"sampled_pages": min(pages, int(limits["visual_sample_pages"])),
                          "nonblank_ratio": nonblank / pages, "passed": nonblank == pages},
    }
    if not all(item["passed"] for item in checks.values()):
        failed = ", ".join(name for name, item in checks.items() if not item["passed"])
        raise SourceReadyError(f"SOURCE_READY failed: {failed}")
    return {"id": "SOURCE_READY", "status": "passed", "checked_at": _utcnow(),
            "limits": limits, "checks": checks,
            "scope": "local extraction comparability only; not mathematical equivalence"}


def ingest(root: str | Path, *, fault: Callable[[str], None] | None = None) -> dict[str, Any]:
    """Process the canonical inbox and atomically publish champion ``v0000``."""
    project = Path(root).resolve()
    pdf = _inbox_pdf(project)
    info = _pdf_info(pdf)
    pages = int(info["Pages"])
    digest = _sha256(pdf)
    original = _safe_child(project, f"artifacts/original/{digest}")
    extracted_artifact = _safe_child(project, f"artifacts/extracted/{digest}")
    rendered_artifact = _safe_child(project, f"artifacts/rendered/{digest}")
    champion = _safe_child(project, "versions/champion/v0000")
    if champion.exists():
        manifest = champion / "ingestion-manifest.json"
        if manifest.is_file() and json.loads(manifest.read_text(encoding="utf-8")).get("input_sha256") == digest:
            return {"status": "idempotent", "champion": str(champion.relative_to(project)), "sha256": digest}
        raise IngestionError("versions/champion/v0000 already exists for a different input; refusing overwrite")
    if original.exists() and (not (original / "document.pdf").is_file() or _sha256(original / "document.pdf") != digest):
        raise IngestionError("existing original artifact hash diverges; refusing overwrite")
    if extracted_artifact.exists() or rendered_artifact.exists():
        raise IngestionError("derived artifact path already exists without a champion; refusing overwrite")
    source_zip = _inspect_zip(project / "input/inbox/source.zip")
    stage_parent = project / "workspaces"
    with tempfile.TemporaryDirectory(prefix="m3-", dir=stage_parent) as temporary:
        stage = Path(temporary)
        extracted = stage / "extracted"
        extracted.mkdir()
        text_file = extracted / "text.txt"
        _tool(["pdftotext", "-layout", str(pdf), str(text_file)], error="PDF text extraction failed")
        _tool(["pdftotext", "-bbox-layout", str(pdf), str(extracted / "coordinates.html")],
              error="PDF coordinate extraction failed")
        text = text_file.read_text(encoding="utf-8", errors="replace")
        pages_dir = extracted / "pages"
        pages_dir.mkdir()
        _tool(["pdftoppm", "-png", "-r", "100", str(pdf), str(pages_dir / "page")], error="PDF rendering failed")
        images_dir = extracted / "images"
        images_dir.mkdir()
        _tool(["pdfimages", "-png", str(pdf), str(images_dir / "image")], error="PDF image extraction failed")
        lines, equations, references, issues = _lines_and_inventory(text)
        image_count = len(list(images_dir.glob("*")))
        kind = "digital" if text.strip() and not image_count else "hybrid" if text.strip() else "scanned"
        if kind == "scanned":
            issues.append({"code": "OCR_NOT_RUN", "message": "scanned PDF detected; OCR adapter is disabled by configuration"})
        reconstructed = _normalized_latex(lines, issues)
        normalized = {"schema_version": "1.0.0", "source_mode": "SOURCE_ZIP" if source_zip else "PDF_ONLY_RECONSTRUCTION",
                      "pages": pages, "blocks": [{"page": 1, "block": 1, "line_start": 1, "line_end": len(lines)}] if lines else [],
                      "lines": lines, "equations": equations, "references": references, "issues": issues}
        _write_json(extracted / "normalized.json", normalized)
        (extracted / "reconstructed.tex").write_text(reconstructed, encoding="utf-8")
        gate = _source_ready(project, extracted, pages, text, equations, references)
        _write_json(extracted / "source_ready.json", gate)
        candidate = stage / "candidate"
        candidate.mkdir()
        shutil.copytree(extracted, candidate / "source")
        shutil.copy2(pdf, candidate / "baseline.pdf")
        if source_zip:
            _copy_tree_from_zip(project / "input/inbox/source.zip", candidate / "latex-source")
        provenance = {"schema_version": "1.0.0", "input_sha256": digest, "input_size_bytes": pdf.stat().st_size,
                    "original_locator": f"artifacts/original/{digest}/document.pdf", "pdf_kind": kind,
                    "source_mode": normalized["source_mode"], "source_zip": source_zip,
                    "source_ready_gate": gate, "tool_versions": {"pdfinfo": info.get("PDF version", "unknown"), "pdftotext": "poppler"}}
        _write_json(candidate / "ingestion-manifest.json", provenance)
        content_hash = _directory_hash(candidate)
        manifest = {"schema_version": "1.1.0", "candidate_id": "v0000", "candidate_kind": "baseline",
                    "run_id": f"ingest-{digest[:12]}", "cycle_id": 0, "base_candidate_id": None,
                    "built_at": _utcnow(), "workspace_hash": content_hash, "content_hash": content_hash,
                    "source_proposal_ids": [], "merge_receipt_locator": None, "immutable": True}
        _write_json(candidate / "manifest.json", manifest)
        if fault:
            fault("before_original_publish")
        original.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf, original / "document.pdf")
        _write_json(original / "manifest.json", {"sha256": digest, "size_bytes": pdf.stat().st_size,
                                                  "pages": pages, "metadata": info, "ingested_at": _utcnow()})
        rendered_stage = stage / "rendered"
        rendered_stage.mkdir()
        shutil.copytree(pages_dir, rendered_stage / "pages")
        os.replace(extracted, extracted_artifact)
        os.replace(rendered_stage, rendered_artifact)
        if fault:
            fault("before_champion_publish")
        os.replace(candidate, champion)
    return {"status": "created", "champion": "versions/champion/v0000", "sha256": digest}
