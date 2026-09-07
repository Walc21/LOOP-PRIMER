"""Offline, fail-closed and recoverable M3 PDF ingestion."""

from __future__ import annotations

import hashlib
import json
import os
import re
import select
import shutil
import subprocess
import tempfile
import time
import unicodedata
import zipfile
import zlib
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from .state_machine import State
from .store import DurableStore, StoreError


class IngestionError(RuntimeError):
    """The inbox or an existing M3 publication is unsafe."""


class SourceReadyError(IngestionError):
    """The extracted baseline did not pass the conservative local gate."""


class LatexCompileError(IngestionError):
    """A bounded, article-content-free report of reconstruction compilation."""

    def __init__(self, classification: str, *, returncode: int | None,
                 duration_ms: int, output_bytes: int, output_sha256: str):
        self.classification = classification
        self.returncode = returncode
        self.duration_ms = duration_ms
        self.output_bytes = output_bytes
        self.output_sha256 = output_sha256
        super().__init__(
            f"{classification}: returncode={returncode}, duration_ms={duration_ms}, "
            f"output_bytes={output_bytes}, output_sha256={output_sha256}"
        )

    def diagnostic(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "returncode": self.returncode,
            "duration_ms": self.duration_ms,
            "output_bytes": self.output_bytes,
            "output_sha256": self.output_sha256,
        }


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _fsync_dir(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
        os.fsync(fd)
    except OSError:
        pass
    else:
        os.close(fd)


def _safe_child(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if root != path and root not in path.parents:
        raise IngestionError("derived path escapes project root")
    return path


_MANAGED_DIRECTORIES = (
    "input/inbox", "workspaces", "artifacts/original", "artifacts/extracted",
    "artifacts/rendered", "versions/champion", "config", "state",
)


def _managed_child(root: Path, relative: str) -> Path:
    """Return a managed path only when no existing component is a symlink."""
    candidate = root / relative
    current = root
    if root.is_symlink() or not root.is_dir():
        raise IngestionError("project root is missing or unsafe")
    for component in Path(relative).parts:
        current = current / component
        if current.is_symlink():
            raise IngestionError(f"managed path contains symlink: {relative}")
    resolved = candidate.resolve(strict=False)
    if resolved != root and root not in resolved.parents:
        raise IngestionError("managed path escapes validated project root")
    return candidate


def _validate_managed_directories(root: Path) -> None:
    for relative in _MANAGED_DIRECTORIES:
        _managed_child(root, relative)


def _fault(fault: Callable[[str], None] | None, stage: str) -> None:
    if fault:
        fault(stage)


def _tool(command: list[str], *, error: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IngestionError(f"{error}: {exc}") from exc
    if result.returncode:
        raise IngestionError(f"{error}: {' '.join(result.stderr.strip().splitlines()[-1:] or ['tool failure'])}")
    return result


def _inbox_file(root: Path, name: str) -> Path | None:
    inbox = root / "input/inbox"
    if not inbox.is_dir():
        raise IngestionError("input/inbox is missing")
    path = inbox / name
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file() or path.resolve().parent != inbox.resolve():
        raise IngestionError(f"input/inbox/{name} must be a regular file inside the inbox")
    return path


def _inbox_pdf(root: Path) -> Path:
    inbox = root / "input/inbox"
    pdfs = list(inbox.glob("*.pdf")) if inbox.is_dir() else []
    if len(pdfs) != 1:
        raise IngestionError(f"expected exactly one pending PDF in input/inbox; found {'none' if not pdfs else 'multiple'}")
    pdf = _inbox_file(root, "artigo.pdf")
    if pdf is None or pdf.stat().st_size == 0:
        raise IngestionError("input/inbox/artigo.pdf is empty or missing")
    return pdf


def _freeze(source: Path, destination: Path, *, fault: Callable[[str], None] | None, label: str) -> tuple[str, int]:
    """Copy one opened inode once; reject a path changed while it was copied."""
    _fault(fault, f"before_{label}_freeze")
    before = source.stat(follow_symlinks=False)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(source, flags)
    except OSError as exc:
        raise IngestionError(f"cannot safely open {source.name}") from exc
    digest = hashlib.sha256()
    size = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with os.fdopen(fd, "rb", closefd=True) as input_stream, destination.open("xb") as output:
            opened = os.fstat(input_stream.fileno())
            if not os.path.samestat(before, opened):
                raise IngestionError(f"{source.name} changed before freezing")
            while True:
                block = input_stream.read(1024 * 1024)
                if not block:
                    break
                digest.update(block); size += len(block); output.write(block)
            output.flush(); os.fsync(output.fileno())
    finally:
        # fd is already closed by fdopen on normal and exceptional paths.
        pass
    after = source.stat(follow_symlinks=False)
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise IngestionError(f"{source.name} changed concurrently while freezing")
    if size != destination.stat().st_size or digest.hexdigest() != _sha256(destination):
        raise IngestionError(f"frozen {source.name} verification failed")
    _fsync_dir(destination.parent)
    _fault(fault, f"after_{label}_freeze")
    return digest.hexdigest(), size


def _pdf_info(pdf: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in _tool(["pdfinfo", str(pdf)], error="invalid PDF (pdfinfo)").stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1); values[key.strip()] = value.strip()
    try:
        if int(values["Pages"]) < 1:
            raise ValueError
    except (KeyError, ValueError) as exc:
        raise IngestionError("invalid PDF: page count unavailable") from exc
    return values


def _write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, ensure_ascii=False, indent=2); stream.write("\n")
        stream.flush(); os.fsync(stream.fileno())


def _assert_tree(path: Path) -> None:
    if not path.is_dir() or path.is_symlink():
        raise IngestionError("managed artifact directory is missing or unsafe")
    for item in path.rglob("*"):
        if item.is_symlink() or not (item.is_file() or item.is_dir()):
            raise IngestionError("managed artifact contains symlink or special file")


def _sync_tree(path: Path) -> None:
    """Durably flush every staged regular file before publishing its tree."""
    _assert_tree(path)
    directories: list[Path] = []
    for item in path.rglob("*"):
        if item.is_file():
            with item.open("rb") as stream:
                os.fsync(stream.fileno())
        elif item.is_dir():
            directories.append(item)
    for directory in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        _fsync_dir(directory)
    _fsync_dir(path)


def _directory_hash(path: Path, *, exclude: set[str] | None = None) -> str:
    _assert_tree(path); digest = hashlib.sha256(); excluded = exclude or set()
    for item in sorted(path.rglob("*")):
        if item.is_file() and item.relative_to(path).as_posix() not in excluded:
            digest.update(item.relative_to(path).as_posix().encode()); digest.update(_sha256(item).encode())
    return digest.hexdigest()


def _latex_structurally_valid(text: str) -> bool:
    """Conservatively recognize one complete document without compiling TeX."""
    cleaned: list[str] = []
    for line in text.splitlines():
        position = 0
        while position < len(line):
            if line[position] == "%" and (position == 0 or len(line[:position]) - len(line[:position].rstrip("\\")) % 2 == 0):
                line = line[:position]
                break
            position += 1
        cleaned.append(line)
    source = "\n".join(cleaned)
    depth = 0
    escaped = False
    for character in source:
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth < 0:
                return False
    if depth:
        return False
    def unescaped(position: int) -> bool:
        preceding = 0
        while position > preceding and source[position - preceding - 1] == "\\":
            preceding += 1
        return preceding % 2 == 0

    environments: list[str] = []
    document_count = 0
    for match in re.finditer(r"\\(begin|end)\s*\{([^{}\s]+)\}", source):
        if not unescaped(match.start()):
            continue
        action, name = match.groups()
        if action == "begin":
            environments.append(name)
            if name == "document":
                document_count += 1
        elif not environments or environments.pop() != name:
            return False
    ends = [match for match in re.finditer(r"\\end\s*\{document\}", source) if unescaped(match.start())]
    classes = [match for match in re.finditer(r"\\documentclass(?:\[[^]]*\])?\s*\{[^{}]+\}", source) if unescaped(match.start())]
    return not environments and document_count == 1 and len(ends) == 1 and bool(classes)


def _zip_info(path: Path, limits: dict[str, Any]) -> dict[str, Any]:
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise IngestionError("source.zip is invalid") from exc
    with archive:
        members = archive.infolist(); names: set[str] = set(); files: set[str] = set(); directories: set[str] = set(); total = 0; tex = []
        if not members or len(members) > int(limits["maximum_zip_members"]): raise IngestionError("source.zip has an unsafe member count")
        for member in members:
            pure = PurePosixPath(member.filename); normalized = pure.as_posix().rstrip("/")
            kind = (member.external_attr >> 16) & 0o170000
            if not normalized or pure.is_absolute() or ".." in pure.parts or normalized in names: raise IngestionError("source.zip contains unsafe path or duplicate entry")
            if member.flag_bits & 1: raise IngestionError("source.zip contains encrypted entry")
            if kind not in {0, 0o100000, 0o040000}: raise IngestionError("source.zip contains symlink or special entry")
            names.add(normalized); (directories if member.is_dir() else files).add(normalized)
            total += member.file_size
            if member.file_size > int(limits["maximum_zip_member_bytes"]) or total > int(limits["maximum_zip_total_bytes"]) or (member.file_size and (not member.compress_size or member.file_size / member.compress_size > int(limits["maximum_zip_expansion_ratio"]))):
                raise IngestionError("source.zip exceeds safe extraction limits")
            if pure.suffix.lower() in {".tex", ".bib", ".sty", ".cls"} and not member.is_dir():
                try: archive.read(member).decode("utf-8", errors="strict")
                except UnicodeDecodeError as exc: raise IngestionError("source.zip textual member is not strict UTF-8") from exc
            if pure.suffix.lower() == ".tex" and not member.is_dir(): tex.append(normalized)
        if files & directories or any("/".join(name.split("/")[:i]) in files for name in names for i in range(1, len(name.split("/")))):
            raise IngestionError("source.zip has file-directory collision")
        invalid: list[str] = []
        for name in tex:
            text = archive.read(name).decode("utf-8")
            if not _latex_structurally_valid(text):
                invalid.append(name)
    return {"sha256": _sha256(path), "size_bytes": path.stat().st_size,
            "tex_members": tex, "invalid_tex_members": invalid,
            "safe_inspection_passed": True}


def _source_identity(input_sha256: str, zip_info: dict[str, Any] | None,
                     source_mode: str) -> dict[str, Any]:
    """The immutable bytes and source classification belonging to one run."""
    return {
        "input_sha256": input_sha256,
        "source_zip_present": zip_info is not None,
        "source_zip_sha256": zip_info["sha256"] if zip_info else None,
        "source_zip_size_bytes": zip_info["size_bytes"] if zip_info else None,
        "source_mode": source_mode,
    }


def _persisted_source_identity(store: DurableStore, run_id: str) -> dict[str, Any] | None:
    """Return the one identity committed by M3 events, failing closed on gaps."""
    identities: list[dict[str, Any]] = []
    for event in store.read_events(run_id):
        if event["state_to"] in {State.INGESTED.value, State.SOURCE_READY.value}:
            identity = event["payload"].get("source_identity")
            if not isinstance(identity, dict):
                raise IngestionError("persisted M3 source identity is missing")
            identities.append(identity)
    if not identities:
        return None
    if any(identity != identities[0] for identity in identities[1:]):
        raise IngestionError("persisted M3 source identities diverge")
    return identities[0]


def _require_source_identity(actual: dict[str, Any], persisted: dict[str, Any] | None) -> None:
    if persisted is not None and persisted != actual:
        raise IngestionError("source.zip identity differs from the persisted execution")


def _copy_zip(zip_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            if member.is_dir(): continue
            target = destination / PurePosixPath(member.filename); target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("xb") as output: shutil.copyfileobj(source, output)


def _lines(text_pages: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    lines=[]; equations=[]; references=[]; equation_candidates=[]; reference_candidates=[]; number=0
    for page, text in enumerate(text_pages, 1):
        for raw in text.splitlines():
            number += 1; value=raw.rstrip()
            if not value: continue
            line={"line": number, "page": page, "text": value}; lines.append(line)
            if re.search(r"(?:=|≤|≥|∫|∑|√|\$[^$]+\$|\b(?:sin|cos|log|lim)\b)", value, re.I):
                equation_candidates.append(line)
            if re.search(r"(?:=|≤|≥|∫|∑|√|\$[^$]+\$)", value): equations.append(line)
            explicit_reference = re.search(r"(?:\[[0-9,; -]+\]|doi:|arXiv:)", value, re.I)
            author_year_reference = re.search(r"\b[A-Z][A-Za-z-]+,? \d{4}", value)
            if explicit_reference or author_year_reference:
                reference_candidates.append(line)
                references.append(line)
    return lines, equations, references, equation_candidates, reference_candidates


_TEX_ESCAPES = {
    "\\": "\\textbackslash{}", "{": "\\{", "}": "\\}", "$": "\\$",
    "&": "\\&", "#": "\\#", "^": "\\textasciicircum{}", "_": "\\_",
    "%": "\\%", "~": "\\textasciitilde{}",
}
MAX_TEX_LINE_CHARS = 240
MAX_LATEX_OUTPUT_BYTES = 65_536
LATEX_TIMEOUT_SECONDS = 30


def _latex_tokens(text: str) -> list[str]:
    """Encode untrusted extracted text into visible, ASCII-only TeX tokens."""
    tokens: list[str] = []
    for character in text:
        codepoint = ord(character)
        category = unicodedata.category(character)
        if category.startswith("C") or codepoint == 0x7F:
            tokens.append(f"[CTRL-U+{codepoint:04X}]")
        elif codepoint > 0x7E:
            tokens.append(f"[U+{codepoint:04X}]")
        else:
            tokens.append(_TEX_ESCAPES.get(character, character))
    return tokens


def _latex_escape(text: str) -> str:
    return "".join(_latex_tokens(text))


def _latex_lines(text: str) -> list[str]:
    """Wrap token boundaries so extracted lines cannot exhaust TeX input lines."""
    result: list[str] = []
    current = ""
    for token in _latex_tokens(text):
        if len(token) > MAX_TEX_LINE_CHARS:
            raise IngestionError("LATEX_RECONSTRUCTION_UNSAFE: encoded token exceeds line limit")
        if current and len(current) + len(token) > MAX_TEX_LINE_CHARS:
            result.append(current)
            current = token
        else:
            current += token
    if current:
        result.append(current)
    return result or [""]


def _normalized_latex(lines: list[dict[str, Any]], issues: list[dict[str, Any]]) -> str:
    body=[
        "% Untrusted PDF extraction: plain text only; formulas require human review.",
        "\\documentclass{article}",
        # These fixed TeX primitives prevent untrusted layout from producing an
        # unbounded stream of box warnings.  They neither load files nor derive
        # commands from the PDF.
        "\\hbadness=10000",
        "\\hfuzz=10000pt",
        "\\begin{document}",
    ]
    for line in lines:
        body.extend(_latex_lines(line["text"]))
        body.append("\\par")
    if not lines: issues.append({"code":"NO_EXTRACTABLE_TEXT", "message":"PDF has no usable text; OCR is disabled"})
    return "\n".join(body + ["\\end{document}", ""])


def _compile_latex(tex: Path, workspace: Path) -> dict[str, Any]:
    """Compile only our escaped reconstruction, in an isolated directory."""
    compiler = shutil.which("pdflatex")
    if compiler is None:
        raise IngestionError("local pdflatex is required to verify reconstructed.tex")
    output = workspace / "latex-check"; output.mkdir()
    checked = output / "reconstructed.tex"; shutil.copy2(tex, checked)
    environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "TEXINPUTS": ".:", "openin_any": "p", "openout_any": "p"}
    command = [compiler, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", "-output-directory", str(output), checked.name]
    started = time.monotonic()
    digest = hashlib.sha256()
    output_bytes = 0
    timed_out = False
    oversized = False
    try:
        process = subprocess.Popen(command, cwd=output, env=environment,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
    except OSError as exc:
        raise LatexCompileError("LATEX_RECONSTRUCTION_UNSAFE", returncode=None,
                                duration_ms=0, output_bytes=0,
                                output_sha256=hashlib.sha256(b"").hexdigest()) from exc
    assert process.stdout is not None
    descriptor = process.stdout.fileno()
    while True:
        remaining = LATEX_TIMEOUT_SECONDS - (time.monotonic() - started)
        if remaining <= 0 and process.poll() is None:
            timed_out = True
            process.kill()
        readable, _, _ = select.select([descriptor], [], [], max(0.0, min(0.1, remaining)))
        if readable:
            read_limit = 1 if output_bytes >= MAX_LATEX_OUTPUT_BYTES else min(
                8192, MAX_LATEX_OUTPUT_BYTES - output_bytes,
            )
            block = os.read(descriptor, read_limit)
            if block:
                if output_bytes >= MAX_LATEX_OUTPUT_BYTES:
                    oversized = True
                    if process.poll() is None:
                        process.kill()
                    continue
                output_bytes += len(block)
                digest.update(block)
                if output_bytes >= MAX_LATEX_OUTPUT_BYTES and process.poll() is None:
                    # The next bounded one-byte read distinguishes an exact
                    # limit from additional compiler output without retaining
                    # article-derived terminal content.
                    continue
                continue
            break
        if process.poll() is not None:
            # Once its writer is closed, read any buffered tail or EOF directly.
            block = os.read(descriptor, 1)
            if not block:
                break
            if output_bytes >= MAX_LATEX_OUTPUT_BYTES:
                oversized = True
            else:
                output_bytes += len(block)
                digest.update(block)
    returncode = process.wait()
    process.stdout.close()
    duration_ms = max(0, round((time.monotonic() - started) * 1000))
    output_sha256 = digest.hexdigest()
    if timed_out:
        raise LatexCompileError("LATEX_TIMEOUT", returncode=returncode,
                                duration_ms=duration_ms, output_bytes=output_bytes,
                                output_sha256=output_sha256)
    if oversized:
        raise LatexCompileError("LATEX_OUTPUT_TOO_LARGE", returncode=returncode,
                                duration_ms=duration_ms, output_bytes=output_bytes,
                                output_sha256=output_sha256)
    if returncode != 0:
        raise LatexCompileError("LATEX_EXIT_NONZERO", returncode=returncode,
                                duration_ms=duration_ms, output_bytes=output_bytes,
                                output_sha256=output_sha256)
    return {
        "classification": "LATEX_OK",
        "returncode": returncode,
        "duration_ms": duration_ms,
        "output_bytes": output_bytes,
        "output_sha256": output_sha256,
    }


def _load_gates(root: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
        return dict(yaml.safe_load((root / "config/gates.yaml").read_text(encoding="utf-8"))["source_ready"])
    except Exception as exc: raise IngestionError(f"cannot load config/gates.yaml: {exc}") from exc


def _sample_pages(pages: int, count: int) -> list[int]:
    count=min(pages, count)
    return sorted({1 + round(i * (pages - 1) / max(1, count - 1)) for i in range(count)})


def _ppm_nonblank(path: Path) -> float:
    raw=path.read_bytes(); header, pixels = raw.split(b"\n255\n", 1)
    if not header.startswith(b"P6") or not pixels: raise IngestionError("visual render is not valid PPM")
    return sum(any(channel < 250 for channel in pixels[i:i+3]) for i in range(0, len(pixels) - 2, 3)) / (len(pixels) // 3)


def _source_ready(root: Path, pdf: Path, extracted: Path, pages: int, text_pages: list[str], equations: list[dict[str, Any]], references: list[dict[str, Any]], equation_candidates: list[dict[str, Any]], reference_candidates: list[dict[str, Any]]) -> dict[str, Any]:
    limits=_load_gates(root); sample=_sample_pages(pages, int(limits["visual_sample_pages"])); visual={}
    for page in sample:
        ppm=extracted / f"visual-{page}.ppm"; _tool(["pdftoppm", "-f", str(page), "-l", str(page), "-singlefile", "-r", "20", str(pdf), str(ppm.with_suffix(""))], error="visual sampling failed")
        visual[str(page)] = _ppm_nonblank(ppm); ppm.unlink()
    candidates = {line["line"] for line in equation_candidates}; eq_inventory = {entry["line"] for entry in equations}
    ref_candidates = {line["line"] for line in reference_candidates}; ref_inventory = {entry["line"] for entry in references}
    coverage=lambda present, expected: 1.0 if not expected else len(present & expected)/len(expected)
    checks={
        "page_count":{"actual":len(list((extracted/"pages").glob("page-*.png"))),"expected":pages},
        "text_coverage":{"actual":sum(bool(page.strip()) for page in text_pages)/pages,"minimum":limits["minimum_text_coverage"]},
        "equation_coverage":{"actual":coverage(eq_inventory,candidates),"minimum":limits["minimum_equation_coverage"],"candidates":len(candidates)},
        "reference_coverage":{"actual":coverage(ref_inventory,ref_candidates),"minimum":limits["minimum_reference_coverage"],"candidates":len(ref_candidates)},
        "visual_sample":{"sampled_pages":sample,"ratios":visual,"minimum":limits["visual_minimum_nonblank_ratio"]},
    }
    checks["page_count"]["passed"]=checks["page_count"]["actual"] == pages
    for name in ("text_coverage","equation_coverage","reference_coverage"): checks[name]["passed"]=checks[name]["actual"] >= checks[name]["minimum"]
    checks["visual_sample"]["passed"] = all(value >= checks["visual_sample"]["minimum"] for value in visual.values())
    if not all(item["passed"] for item in checks.values()): raise SourceReadyError("SOURCE_READY failed: " + ", ".join(name for name,item in checks.items() if not item["passed"]))
    return {"id":"SOURCE_READY","status":"passed","checked_at":_utcnow(),"limits":limits,"checks":checks,"scope":"local extraction comparability only; not mathematical equivalence"}


def _publish(stage: Path, target: Path, *, verify: Callable[[Path], None], fault: Callable[[str], None] | None, label: str) -> None:
    _fault(fault, f"before_{label}_publish")
    if target.exists(): verify(target)
    else:
        _sync_tree(stage); target.parent.mkdir(parents=True, exist_ok=True); _fsync_dir(target.parent); os.replace(stage, target); _fsync_dir(target.parent); verify(target)
    _fault(fault, f"after_{label}_publish")


def _read_json(path: Path) -> dict[str, Any]:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise IngestionError("manifest is missing or invalid") from exc


def _verify_artifacts(original: Path, extracted: Path, rendered: Path, digest: str) -> dict[str, str]:
    _assert_tree(original); _assert_tree(extracted); _assert_tree(rendered)
    if _sha256(original / "document.pdf") != digest: raise IngestionError("original artifact hash diverges")
    hashes={"original":_directory_hash(original, exclude={"manifest.json"}),"extracted":_directory_hash(extracted, exclude={"manifest.json"}),"rendered":_directory_hash(rendered, exclude={"manifest.json"})}
    for path,key in ((original,"original"),(extracted,"extracted"),(rendered,"rendered")):
        if _read_json(path / "manifest.json").get("directory_hash") != hashes[key]: raise IngestionError("artifact manifest hash diverges")
    return hashes


def _verify_champion(champion: Path, digest: str, hashes: dict[str,str],
                     source_identity: dict[str, Any]) -> None:
    _assert_tree(champion); provenance=_read_json(champion/"ingestion-manifest.json"); manifest=_read_json(champion/"manifest.json")
    if provenance.get("input_sha256") != digest or _sha256(champion/"baseline.pdf") != digest: raise IngestionError("champion baseline hash diverges")
    if provenance.get("source_identity") != source_identity:
        raise IngestionError("champion source identity diverges")
    if provenance.get("source_mode") != source_identity["source_mode"]:
        raise IngestionError("champion source mode diverges")
    source_zip = provenance.get("source_zip")
    if source_identity["source_zip_present"]:
        if not isinstance(source_zip, dict) or source_zip.get("sha256") != source_identity["source_zip_sha256"] or source_zip.get("size_bytes") != source_identity["source_zip_size_bytes"]:
            raise IngestionError("champion source.zip hash diverges")
    elif source_zip is not None:
        raise IngestionError("champion unexpectedly records source.zip")
    if provenance.get("artifact_hashes") != hashes or _directory_hash(champion, exclude={"manifest.json"}) != manifest.get("content_hash") or manifest.get("workspace_hash") != manifest.get("content_hash"):
        raise IngestionError("champion manifest or workspace hash diverges")
    if _directory_hash(champion/"source", exclude={"manifest.json"}) != hashes["extracted"]: raise IngestionError("champion source diverges from extracted artifact")


def validate_source_ready(root: str | Path, run_id: str) -> dict[str, Any]:
    """Revalidate one explicit canonical M3 run without writing to it."""
    supplied = Path(root)
    if supplied.is_symlink() or not supplied.is_dir():
        raise IngestionError("M3 root is missing or unsafe")
    project = supplied.resolve()
    _validate_managed_directories(project)
    pdf = _inbox_pdf(project)
    digest = _sha256(pdf)
    expected_run = f"ingest-{digest}"
    if run_id != expected_run:
        raise IngestionError("explicit M3 run differs from the canonical PDF identity")
    store = DurableStore(project, read_only=True)
    snapshot = store.snapshot(run_id)
    if snapshot["state"] != State.SOURCE_READY.value:
        raise IngestionError("M3 run is not SOURCE_READY")
    events = store.read_events(run_id)
    ready_events = [event for event in events if event["state_to"] == State.SOURCE_READY.value]
    if len(ready_events) != 1:
        raise IngestionError("M3 SOURCE_READY evidence is missing or ambiguous")

    original = _managed_child(project, f"artifacts/original/{digest}")
    extracted = _managed_child(project, f"artifacts/extracted/{digest}")
    rendered = _managed_child(project, f"artifacts/rendered/{digest}")
    champion = _managed_child(project, "versions/champion/v0000")
    required = (
        original / "document.pdf", original / "manifest.json",
        extracted / "manifest.json", extracted / "text.txt",
        extracted / "source_ready.json", rendered / "manifest.json",
        champion / "baseline.pdf", champion / "manifest.json",
        champion / "ingestion-manifest.json", champion / "source",
    )
    if any(path.is_symlink() or not path.exists() for path in required):
        raise IngestionError("canonical M3 evidence is unsafe or incomplete")
    hashes = _verify_artifacts(original, extracted, rendered, digest)
    source_identity = _persisted_source_identity(store, run_id)
    if source_identity is None:
        raise IngestionError("persisted M3 source identity is missing")
    _verify_champion(champion, digest, hashes, source_identity)
    source_ready = _read_json(extracted / "source_ready.json")
    event_payload = ready_events[0].get("payload", {})
    if (
        source_ready.get("id") != "SOURCE_READY"
        or source_ready.get("status") != "passed"
        or event_payload.get("gate") != source_ready
        or event_payload.get("artifacts") != hashes
    ):
        raise IngestionError("M3 SOURCE_READY gate or artifact binding diverges")
    champion_manifest = _read_json(champion / "manifest.json")
    base_hash = champion_manifest.get("content_hash")
    if champion_manifest.get("run_id") != run_id or not isinstance(base_hash, str) or re.fullmatch(r"[a-f0-9]{64}", base_hash) is None:
        raise IngestionError("M3 champion identity is invalid")
    return {
        "schema_version": "1.0.0",
        "m3_root": str(project),
        "run_id": run_id,
        "pdf_path": str(pdf.resolve()),
        "pdf_sha256": digest,
        "base_hash": base_hash,
        "artifact_hashes": hashes,
        "source_identity": source_identity,
        "extracted_path": str(extracted),
        "rendered_path": str(rendered),
        "champion_path": str(champion),
    }


def ingest(root: str | Path, *, fault: Callable[[str], None] | None = None) -> dict[str, Any]:
    """Freeze inbox bytes, prepare all outputs, then recoverably publish M3."""
    supplied_root = Path(root)
    if supplied_root.is_symlink():
        raise IngestionError("project root is missing or unsafe")
    project = supplied_root.resolve()
    _validate_managed_directories(project)
    pdf=_inbox_pdf(project); staging_root=_managed_child(project, "workspaces"); staging_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="m3-freeze-", dir=staging_root) as temporary:
        stage=Path(temporary); frozen_pdf=stage/"input.pdf"; digest,size=_freeze(pdf,frozen_pdf,fault=fault,label="input")
        zip_path=_inbox_file(project,"source.zip"); frozen_zip=None
        if zip_path:
            frozen_zip=stage/"source.zip"; _freeze(zip_path,frozen_zip,fault=fault,label="source_zip")
        limits=_load_gates(project)
        if size > int(limits["maximum_pdf_bytes"]): raise IngestionError("PDF exceeds configured size limit")
        info=_pdf_info(frozen_pdf); pages=int(info["Pages"])
        if pages > int(limits["maximum_pages"]): raise IngestionError("PDF exceeds configured page limit")
        zip_info=_zip_info(frozen_zip, limits) if frozen_zip else None
        source_zip=zip_info if zip_info and zip_info["tex_members"] and not zip_info["invalid_tex_members"] else None
        source_mode="SOURCE_ZIP" if source_zip else "PDF_ONLY_RECONSTRUCTION"
        run_id=f"ingest-{digest}"; store=DurableStore(project); store.create_run(run_id, actor_id="m3", event_id=f"{run_id}:new")
        source_identity = _source_identity(digest, zip_info, source_mode)
        persisted_identity = _persisted_source_identity(store, run_id)
        _require_source_identity(source_identity, persisted_identity)
        original=_managed_child(project, f"artifacts/original/{digest}"); extracted_artifact=_managed_child(project, f"artifacts/extracted/{digest}"); rendered_artifact=_managed_child(project, f"artifacts/rendered/{digest}"); champion=_managed_child(project, "versions/champion/v0000")
        if champion.exists():
            hashes=_verify_artifacts(original,extracted_artifact,rendered_artifact,digest); _verify_champion(champion,digest,hashes,source_identity)
            if store.snapshot(run_id)["state"] != State.SOURCE_READY: raise IngestionError("champion exists without SOURCE_READY event")
            return {"status":"idempotent","champion":"versions/champion/v0000","sha256":digest,"run_id":run_id}
        original_stage=stage/"original"; original_stage.mkdir(); shutil.copy2(frozen_pdf,original_stage/"document.pdf")
        _write_json(original_stage/"manifest.json",{"directory_hash":_directory_hash(original_stage),"input_sha256":digest,"size_bytes":size})
        _publish(original_stage,original,verify=lambda p: _assert_tree(p) if _sha256(p/"document.pdf")==digest else (_ for _ in ()).throw(IngestionError("original artifact hash diverges")),fault=fault,label="original")
        _fault(fault,"before_ingested_record")
        store.record(run_id,State.INGESTED,event_id=f"{run_id}:ingested",idempotency_key=f"{run_id}:ingested",actor_id="m3",event_type="M3_INGESTED",payload={**source_identity,"source_identity":source_identity,"input_size_bytes":size,"original_locator":f"artifacts/original/{digest}/document.pdf"},artifact_hashes=[_directory_hash(original, exclude={"manifest.json"})])
        _fault(fault,"after_ingested_record")
        extracted=stage/"extracted"; extracted.mkdir(); text_pages=[]
        for page in range(1,pages+1):
            output=extracted/f"text-page-{page}.txt"; _tool(["pdftotext","-f",str(page),"-l",str(page),"-layout",str(frozen_pdf),str(output)],error="PDF text extraction failed"); text_pages.append(output.read_text(encoding="utf-8",errors="strict"))
        (extracted/"text.txt").write_text("\f\n".join(text_pages),encoding="utf-8")
        _tool(["pdftotext","-bbox-layout",str(frozen_pdf),str(extracted/"coordinates.html")],error="PDF coordinate extraction failed")
        pages_dir=extracted/"pages"; pages_dir.mkdir(); _tool(["pdftoppm","-png","-r","100",str(frozen_pdf),str(pages_dir/"page")],error="PDF rendering failed")
        images=extracted/"images"; images.mkdir(); _tool(["pdfimages","-png",str(frozen_pdf),str(images/"image")],error="PDF image extraction failed")
        lines,equations,references,equation_candidates,reference_candidates=_lines(text_pages); issues=[]
        if zip_info and not source_zip: issues.append({"code":"SOURCE_ZIP_STRUCTURALLY_INVALID","message":"source.zip has no complete LaTeX document or contains a structurally invalid .tex member; PDF-only reconstruction used"})
        if not any(page.strip() for page in text_pages): issues.append({"code":"OCR_NOT_RUN","message":"scanned PDF detected; OCR adapter is disabled"})
        normalized={"schema_version":"1.1.0","source_mode":source_mode,"pages":pages,"blocks":[{"page":page,"line_start":min([x["line"] for x in lines if x["page"]==page],default=0),"line_end":max([x["line"] for x in lines if x["page"]==page],default=0)} for page in range(1,pages+1)],"lines":lines,"equations":equations,"equation_candidates":equation_candidates,"references":references,"reference_candidates":reference_candidates,"issues":issues}
        _write_json(extracted/"normalized.json",normalized); reconstructed=extracted/"reconstructed.tex"; reconstructed.write_text(_normalized_latex(lines,issues),encoding="utf-8"); _compile_latex(reconstructed, stage)
        gate=_source_ready(project,frozen_pdf,extracted,pages,text_pages,equations,references,equation_candidates,reference_candidates); _write_json(extracted/"source_ready.json",gate)
        rendered=stage/"rendered"; rendered.mkdir(); shutil.copytree(pages_dir,rendered/"pages")
        for directory in (extracted,rendered): _write_json(directory/"manifest.json",{"directory_hash":_directory_hash(directory),"input_sha256":digest,"size_bytes":size})
        _publish(extracted,extracted_artifact,verify=lambda p: _assert_tree(p),fault=fault,label="extracted")
        _publish(rendered,rendered_artifact,verify=lambda p: _assert_tree(p),fault=fault,label="rendered")
        hashes=_verify_artifacts(original,extracted_artifact,rendered_artifact,digest)
        _fault(fault,"before_source_ready_record"); store.record(run_id,State.SOURCE_READY,event_id=f"{run_id}:source-ready",idempotency_key=f"{run_id}:source-ready",actor_id="m3",event_type="M3_SOURCE_READY",payload={**source_identity,"source_identity":source_identity,"gate":gate,"artifacts":hashes},artifact_hashes=sorted(hashes.values())); _fault(fault,"after_source_ready_record")
        candidate=stage/"candidate"; candidate.mkdir(); shutil.copytree(extracted_artifact,candidate/"source"); shutil.copy2(original/"document.pdf",candidate/"baseline.pdf")
        if source_zip: _copy_zip(frozen_zip,candidate/"latex-source")
        _write_json(candidate/"ingestion-manifest.json",{"schema_version":"1.1.0","input_sha256":digest,"input_size_bytes":size,"original_locator":f"artifacts/original/{digest}/document.pdf","source_mode":normalized["source_mode"],"source_identity":source_identity,"source_zip":zip_info,"source_ready_gate":gate,"artifact_hashes":hashes})
        content_hash=_directory_hash(candidate); _write_json(candidate/"manifest.json",{"schema_version":"1.1.0","candidate_id":"v0000","candidate_kind":"baseline","run_id":run_id,"cycle_id":0,"base_candidate_id":None,"built_at":_utcnow(),"content_hash":content_hash,"workspace_hash":content_hash,"source_proposal_ids":[],"merge_receipt_locator":None,"immutable":True})
        _publish(candidate,champion,verify=lambda p: _verify_champion(p,digest,hashes,source_identity),fault=fault,label="champion")
    return {"status":"created","champion":"versions/champion/v0000","sha256":digest,"run_id":run_id}
