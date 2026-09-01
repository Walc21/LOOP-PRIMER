#!/usr/bin/env python3
"""Primitivas locais compartilhadas pelo handoff de contexto para IAs.

Este módulo não importa o runtime do article-loop e nunca executa arquivos do
repositório. A única integração externa opcional é leitura local do Git.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = "1.0.0"
GENERATED_PATHS = {
    "AI_CONTEXT.md",
    "docs/AI_HISTORY.md",
    "docs/ai_sessions.jsonl",
    "docs/ai_snapshot.json",
    "docs/ai_history.lock",
}
FALLBACK_EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
CANONICAL_RUNTIME_DIRS = (
    "input/inbox",
    "artifacts",
    "state",
    "versions",
    "workspaces",
    "reports",
    "logs",
)
SENSITIVE_BASENAMES = {"auth.json", ".env", "credentials.json", "secrets.json"}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}


class HandoffError(RuntimeError):
    """Falha fechada de inventário, histórico ou publicação de handoff."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_sensitive_path(relative: str) -> bool:
    path = Path(relative)
    lowered = path.name.lower()
    if lowered in SENSITIVE_BASENAMES or path.suffix.lower() in SENSITIVE_SUFFIXES:
        return True
    if lowered.startswith(".env.") and lowered != ".env.example":
        return True
    return any(token in lowered for token in ("credential", "secret", "private_key"))


def run_local(command: list[str], *, cwd: Path, timeout: int = 15, check: bool = False) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=check,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        if check:
            raise HandoffError(f"comando local falhou: {command[0]}: {exc}") from exc
        return subprocess.CompletedProcess(command, 1, "", str(exc))


def git_root(root: Path) -> bool:
    result = run_local(["git", "rev-parse", "--is-inside-work-tree"], cwd=root)
    return result.returncode == 0 and result.stdout.strip() == "true"


def list_relevant_paths(root: Path) -> list[str]:
    """Lista arquivos versionados e não ignorados, ou faz fallback sem Git."""
    root = root.resolve()
    paths: set[str] = set()
    if git_root(root):
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
        if result.returncode != 0:
            raise HandoffError(result.stderr.decode("utf-8", "replace").strip() or "git ls-files falhou")
        paths.update(part.decode("utf-8", "surrogateescape") for part in result.stdout.split(b"\0") if part)
    else:
        for current, directories, filenames in os.walk(root, followlinks=False):
            directories[:] = sorted(d for d in directories if d not in FALLBACK_EXCLUDED_DIRS)
            base = Path(current)
            for name in filenames:
                if name.endswith((".pyc", ".pyo")):
                    continue
                paths.add((base / name).relative_to(root).as_posix())
    for relative_directory in CANONICAL_RUNTIME_DIRS:
        directory = root / relative_directory
        if not directory.is_dir() or directory.is_symlink():
            if directory.is_symlink():
                paths.add(relative_directory)
            continue
        for current, directories, filenames in os.walk(directory, followlinks=False):
            base = Path(current)
            symlink_directories = [name for name in directories if (base / name).is_symlink()]
            for name in symlink_directories:
                paths.add((base / name).relative_to(root).as_posix())
            directories[:] = sorted(name for name in directories if name not in symlink_directories and name not in FALLBACK_EXCLUDED_DIRS)
            for name in filenames:
                paths.add((base / name).relative_to(root).as_posix())
    return sorted(path for path in paths if path not in GENERATED_PATHS)


def _markdown_summary(text: str) -> str:
    headings = [line.lstrip("# ").strip() for line in text.splitlines() if re.match(r"^#{1,3}\s+\S", line)]
    return "seções: " + "; ".join(headings[:5]) if headings else "Markdown sem headings"


def _python_summary(text: str) -> str:
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return f"Python inválido na linha {exc.lineno}"
    public: list[str] = []
    tests = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            tests += 1
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            public.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            public.append(node.name + "()")
    parts = []
    if public:
        parts.append("API: " + ", ".join(public[:14]))
    if tests:
        parts.append(f"{tests} testes")
    return "; ".join(parts) or "módulo Python interno"


def _json_summary(text: str) -> str:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        return f"JSON inválido na linha {exc.lineno}"
    if not isinstance(value, dict):
        return f"JSON {type(value).__name__}"
    if "$schema" in value or "$id" in value:
        required = value.get("required", [])
        return f"schema {value.get('title') or value.get('$id', '')}; {len(required)} campos obrigatórios"
    return "chaves: " + ", ".join(str(key) for key in list(value)[:10])


def _yaml_summary(text: str) -> str:
    keys = []
    for line in text.splitlines():
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s|$)", line)
        if match:
            keys.append(match.group(1))
    return "chaves: " + ", ".join(keys[:10]) if keys else "configuração YAML"


def summarize_text(relative: str, text: str) -> str:
    suffix = Path(relative).suffix.lower()
    if suffix == ".py":
        return _python_summary(text)
    if suffix == ".md":
        return _markdown_summary(text)
    if suffix == ".json":
        return _json_summary(text)
    if suffix in {".yaml", ".yml"}:
        return _yaml_summary(text)
    if suffix == ".sh":
        comments = [line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#") and not line.startswith("#!")]
        return comments[0] if comments else "script shell"
    first = next((line.strip() for line in text.splitlines() if line.strip()), "arquivo textual vazio")
    return first[:140]


def file_record(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode):
        return {"kind": "symlink", "bytes": info.st_size, "lines": None, "sha256": None, "summary": "link simbólico não seguido"}
    if not stat.S_ISREG(info.st_mode):
        return {"kind": "special", "bytes": info.st_size, "lines": None, "sha256": None, "summary": "arquivo não regular não lido"}
    if is_sensitive_path(relative):
        return {"kind": "sensitive", "bytes": info.st_size, "lines": None, "sha256": None, "summary": "conteúdo sensível deliberadamente não lido"}
    if any(relative == prefix or relative.startswith(prefix + "/") for prefix in CANONICAL_RUNTIME_DIRS):
        return {
            "kind": "runtime",
            "bytes": info.st_size,
            "lines": None,
            "sha256": sha256_file(path),
            "summary": "estado/artefato local identificado por hash; conteúdo não incorporado",
        }
    data = path.read_bytes()
    digest = sha256_bytes(data)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return {"kind": "binary", "bytes": len(data), "lines": None, "sha256": digest, "summary": "arquivo binário"}
    return {
        "kind": "text",
        "bytes": len(data),
        "lines": len(text.splitlines()),
        "sha256": digest,
        "summary": summarize_text(relative, text),
    }


def build_inventory(root: Path) -> dict[str, dict[str, Any]]:
    inventory: dict[str, dict[str, Any]] = {}
    for relative in list_relevant_paths(root):
        try:
            inventory[relative] = file_record(root, relative)
        except FileNotFoundError:
            continue
        except PermissionError:
            inventory[relative] = {"kind": "unreadable", "bytes": None, "lines": None, "sha256": None, "summary": "sem permissão de leitura"}
    return inventory


def inventory_fingerprint(inventory: Mapping[str, Mapping[str, Any]]) -> str:
    compact = {
        path: {"kind": item.get("kind"), "bytes": item.get("bytes"), "sha256": item.get("sha256")}
        for path, item in sorted(inventory.items())
    }
    return sha256_bytes(canonical_json(compact))


def snapshot_files(inventory: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        path: {"kind": item.get("kind"), "bytes": item.get("bytes"), "lines": item.get("lines"), "sha256": item.get("sha256")}
        for path, item in sorted(inventory.items())
    }


def inventory_delta(previous: Mapping[str, Mapping[str, Any]], current: Mapping[str, Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {"added": [], "modified": [], "deleted": []}
    old_paths, new_paths = set(previous), set(current)
    for path in sorted(new_paths - old_paths):
        result["added"].append({"path": path, "before": None, "after": current[path].get("sha256"), "bytes": current[path].get("bytes")})
    for path in sorted(old_paths - new_paths):
        result["deleted"].append({"path": path, "before": previous[path].get("sha256"), "after": None, "bytes": previous[path].get("bytes")})
    for path in sorted(old_paths & new_paths):
        before, after = previous[path], current[path]
        if (before.get("kind"), before.get("bytes"), before.get("sha256")) != (after.get("kind"), after.get("bytes"), after.get("sha256")):
            result["modified"].append({"path": path, "before": before.get("sha256"), "after": after.get("sha256"), "bytes": after.get("bytes")})
    return result


def git_state(root: Path) -> dict[str, Any]:
    if not git_root(root):
        return {"available": False, "branch": None, "head": None, "status": []}
    branch = run_local(["git", "branch", "--show-current"], cwd=root).stdout.strip() or "(detached)"
    head = run_local(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip() or None
    status_lines = run_local(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=root).stdout.splitlines()
    filtered = []
    for line in status_lines:
        path = line[3:].strip().strip('"') if len(line) >= 4 else line
        targets = [part.strip().strip('"') for part in path.split(" -> ")]
        if any(target in GENERATED_PATHS for target in targets):
            continue
        filtered.append(line)
    return {"available": True, "branch": branch, "head": head, "status": filtered}


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HandoffError(f"JSON de handoff inválido: {path}: {exc}") from exc


def atomic_write(path: Path, data: bytes) -> bool:
    """Publica bytes de forma atômica; retorna False quando já eram idênticos."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == data:
        return False
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
        return True
    finally:
        if temporary.exists():
            temporary.unlink()


def markdown_cell(value: Any, limit: int = 140) -> str:
    text = str(value if value is not None else "-").replace("\n", " ").replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
