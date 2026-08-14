"""Deterministic, local prompt-contract compilation for M4.

This module composes text only.  It neither invokes Prime Agent nor writes a
candidate, challenger, or champion.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import jsonschema
import yaml


class PromptIntegrityError(RuntimeError):
    """A registered immutable prompt or overlay did not verify."""


class PromptContractError(ValueError):
    """A task, context, or structured output is outside its contract."""


ROLE_IDS = frozenset({
    "M00", "S10", "S20", "S30", "S40", "S50",
    "W11", "W12", "W13", "W21", "W22", "W23", "W31", "W32", "W33",
    "W41", "W42", "W43", "W51", "W52", "W53",
})
IMMUTABLE_IDS = frozenset({"global", *ROLE_IDS})
OVERLAY_ROLE_IDS = ROLE_IDS - {"M00"}
TASK_CONTEXT_FIELDS = (
    "run_id", "cycle_id", "base_hash", "activation_mode", "scope", "input_locators",
)
FORMAT_CHECKER = jsonschema.FormatChecker()


@FORMAT_CHECKER.checks("date-time")
def _is_rfc3339_datetime(value: object) -> bool:
    """Supply date-time checking even when jsonschema optional extras are absent."""
    if not isinstance(value, str) or "T" not in value:
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class CompiledPrompt:
    role_id: str
    immutable_hash: str
    overlay_version: str | None
    output_schema: str
    text: str


class PromptRegistry:
    """Read-only view of a content-addressed prompt registry."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.prompt_root = self.root / "prompts"
        try:
            self.registry = json.loads((self.prompt_root / "registry.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise PromptIntegrityError("prompt registry is unreadable") from error
        if self.registry.get("schema_version") != "1.0.0":
            raise PromptIntegrityError("unknown prompt registry version")
        immutable = self.registry.get("immutable")
        if not isinstance(immutable, dict) or set(immutable) != IMMUTABLE_IDS:
            raise PromptIntegrityError("immutable prompt catalog must be exactly global plus canonical roles")
        overlays = self.registry.get("overlays")
        if not isinstance(overlays, dict) or set(overlays) - OVERLAY_ROLE_IDS:
            raise PromptIntegrityError("overlay catalog contains a non-canonical role")
        for role_id, versions in overlays.items():
            if not isinstance(versions, dict) or not versions:
                raise PromptIntegrityError(f"invalid overlay catalog: {role_id}")
            for version in versions:
                if not isinstance(version, str) or not version or "/" in version or "\\" in version:
                    raise PromptIntegrityError(f"invalid overlay version: {role_id}")

    def _regular_path(self, relative: str, expected_relative: str) -> Path:
        if relative != expected_relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise PromptIntegrityError("registered prompt path is not canonical")
        path = self.prompt_root / relative
        expected_root = self.prompt_root / Path(expected_relative).parent
        try:
            relative_parts = path.relative_to(self.prompt_root).parts
        except ValueError as error:
            raise PromptIntegrityError("registered prompt path escapes prompt root") from error
        current = self.prompt_root
        for part in relative_parts:
            current = current / part
            if current.is_symlink():
                raise PromptIntegrityError("registered prompt path may not be a symlink")
        if not path.is_file() or path.resolve().parent != expected_root.resolve():
            raise PromptIntegrityError("registered prompt path is not a regular contained file")
        return path

    def _entry(self, role_id: str) -> Mapping[str, Any]:
        entry = self.registry.get("immutable", {}).get(role_id)
        if not isinstance(entry, dict):
            raise PromptIntegrityError(f"unknown immutable prompt: {role_id}")
        return entry

    def immutable(self, role_id: str) -> tuple[str, str]:
        if role_id not in IMMUTABLE_IDS:
            raise PromptIntegrityError(f"unknown immutable prompt: {role_id}")
        entry = self._entry(role_id)
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise PromptIntegrityError(f"invalid immutable registry entry: {role_id}")
        filename = "global.md" if role_id == "global" else f"{role_id}.md"
        path = self._regular_path(relative, f"immutable/{filename}")
        raw = path.read_bytes()
        actual = _sha256_bytes(raw)
        if actual != expected:
            raise PromptIntegrityError(f"immutable prompt hash mismatch: {role_id}")
        return raw.decode("utf-8"), actual

    def _overlay_document(self, role_id: str, version: str, entry: Mapping[str, Any]) -> Mapping[str, Any]:
        relative, expected = entry.get("path"), entry.get("hash")
        if not isinstance(relative, str) or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise PromptIntegrityError("invalid overlay registry entry")
        path = self._regular_path(relative, f"overlays/{role_id}/{version}.yaml")
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            raise PromptIntegrityError("invalid overlay yaml") from error
        required = {"parent_version", "diagnostic", "author", "evidence", "scope", "hash", "rollback", "instructions"}
        if not isinstance(document, dict) or set(document) != required:
            raise PromptIntegrityError("overlay has invalid fields")
        calculated = _sha256_bytes(_canonical_json({key: value for key, value in document.items() if key != "hash"}))
        if document["hash"] != expected or calculated != expected:
            raise PromptIntegrityError("overlay hash mismatch")
        if not all(isinstance(document[key], str) and document[key].strip() for key in ("diagnostic", "author", "instructions")):
            raise PromptIntegrityError("overlay text is invalid")
        for key in ("evidence", "scope"):
            value = document[key]
            if (not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value) or len(value) != len(set(value))):
                raise PromptIntegrityError(f"overlay {key} is invalid")
        for key in ("parent_version", "rollback"):
            reference = document[key]
            if reference is not None and (not isinstance(reference, str) or not reference.strip()):
                raise PromptIntegrityError(f"overlay {key} is invalid")
        return document

    def _validate_overlay_graph(self, role_id: str, versions: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
        documents: dict[str, Mapping[str, Any]] = {}
        graph: dict[str, tuple[str, ...]] = {}
        for version, entry in versions.items():
            if not isinstance(entry, dict):
                raise PromptIntegrityError("invalid overlay registry entry")
            document = self._overlay_document(role_id, version, entry)
            documents[version] = document
            references = tuple(reference for reference in (document["parent_version"], document["rollback"]) if reference is not None)
            if any(reference not in versions for reference in references):
                raise PromptIntegrityError("overlay parent version or rollback is unknown")
            if version in references:
                raise PromptIntegrityError("overlay parent version or rollback is self-referential")
            graph[version] = references
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(version: str) -> None:
            if version in visiting:
                raise PromptIntegrityError("overlay parent version or rollback is cyclic")
            if version not in visited:
                visiting.add(version)
                for reference in graph[version]:
                    visit(reference)
                visiting.remove(version)
                visited.add(version)

        for version in graph:
            visit(version)
        return documents

    def overlay(self, role_id: str, version: str | None) -> tuple[str, Mapping[str, Any]]:
        if version is None:
            return "", {}
        if role_id == "M00":
            raise PromptContractError("M00 overlays require an explicit authorized scope contract")
        if role_id not in OVERLAY_ROLE_IDS:
            raise PromptIntegrityError(f"unknown overlay role: {role_id}")
        versions = self.registry.get("overlays", {}).get(role_id, {})
        entry = versions.get(version) if isinstance(versions, dict) else None
        if not isinstance(entry, dict):
            raise PromptIntegrityError(f"unknown overlay version: {role_id}/{version}")
        document = self._validate_overlay_graph(role_id, versions)[version]
        return "\n\n# Overlay versionado\n" + document["instructions"].strip() + "\n", document


def _schema(root: Path, name: str) -> Mapping[str, Any]:
    try:
        return json.loads((root / "config" / "schemas" / name).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PromptContractError(f"output schema unavailable: {name}") from error


def _schema_hash(root: Path, name: str) -> str:
    try:
        return _sha256_bytes((root / "config" / "schemas" / name).read_bytes())
    except OSError as error:
        raise PromptContractError(f"output schema unavailable: {name}") from error


def expected_prompt_version(root: str | Path, role_id: str, output_schema: str, *, overlay_version: str | None = None) -> str:
    """Return the content-addressed identity required before an AgentTask exists."""
    if role_id not in ROLE_IDS:
        raise PromptContractError("prompt version requires a canonical role")
    root_path = Path(root)
    registry = PromptRegistry(root_path)
    _, global_hash = registry.immutable("global")
    _, role_hash = registry.immutable(role_id)
    if overlay_version is None:
        overlay_identity: Mapping[str, Any] = {"version": None, "sha256": None}
    else:
        _, overlay = registry.overlay(role_id, overlay_version)
        overlay_identity = {"version": overlay_version, "sha256": overlay["hash"]}
    _schema(root_path, output_schema)
    identity = {
        "global_sha256": global_hash,
        "role_id": role_id,
        "role_sha256": role_hash,
        "overlay": overlay_identity,
        "output_schema": {"name": output_schema, "sha256": _schema_hash(root_path, output_schema)},
    }
    return "sha256:" + _sha256_bytes(_canonical_json(identity))


def validate_output(root: str | Path, schema_name: str, output: Mapping[str, Any]) -> None:
    if schema_name not in {"agent-proposal.schema.json", "department-packet.schema.json"}:
        raise PromptContractError("unsupported output schema")
    try:
        jsonschema.Draft202012Validator(_schema(Path(root), schema_name), format_checker=FORMAT_CHECKER).validate(dict(output))
    except jsonschema.ValidationError as error:
        raise PromptContractError(f"invalid structured output: {error.message}") from error


def compile_prompt(root: str | Path, task: Mapping[str, Any], cycle_context: Mapping[str, Any], *, overlay_version: str | None = None) -> CompiledPrompt:
    """Compile a role prompt with a closed context surface and verified inputs."""
    root = Path(root)
    role_id = task.get("role_id")
    if role_id not in ROLE_IDS or role_id == "M00":
        raise PromptContractError("AgentTask must target a configured non-M00 role")
    task_schema = _schema(root, "agent-task.schema.json")
    try:
        jsonschema.Draft202012Validator(task_schema, format_checker=FORMAT_CHECKER).validate(dict(task))
    except jsonschema.ValidationError as error:
        raise PromptContractError(f"invalid AgentTask: {error.message}") from error
    if set(cycle_context) - set(TASK_CONTEXT_FIELDS):
        raise PromptContractError("cycle context contains fields not permitted for a role")
    missing = set(TASK_CONTEXT_FIELDS) - set(cycle_context)
    if missing:
        raise PromptContractError(f"cycle context missing permitted fields: {sorted(missing)}")
    for field in TASK_CONTEXT_FIELDS:
        if cycle_context[field] != task[field]:
            raise PromptContractError(f"cycle context does not match AgentTask: {field}")

    schema_name = task["requested_output_schema"]
    expected_version = expected_prompt_version(root, role_id, schema_name, overlay_version=overlay_version)
    if task.get("prompt_version") != expected_version:
        raise PromptContractError("AgentTask prompt_version does not match compiled prompt identity")
    registry = PromptRegistry(root)
    stable, stable_hash = registry.immutable("global")
    role_core, role_hash = registry.immutable(role_id)
    overlay, overlay_document = registry.overlay(role_id, overlay_version)
    if overlay_document and not set(overlay_document["scope"]).issubset(set(task["scope"])):
        raise PromptContractError("overlay scope exceeds AgentTask scope")
    output_schema = json.dumps(_schema(root, schema_name), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    context = json.dumps({field: cycle_context[field] for field in TASK_CONTEXT_FIELDS}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    text = stable.rstrip() + "\n\n" + role_core.rstrip() + "\n\n# Contexto do ciclo\n" + context + overlay + "\n# Schema de saída\n" + output_schema + "\n"
    return CompiledPrompt(role_id, _sha256_bytes((stable_hash + role_hash).encode("ascii")), overlay_version, schema_name, text)


def compile_manager_prompt(root: str | Path, cycle_context: Mapping[str, Any], *, overlay_version: str | None = None) -> CompiledPrompt:
    """Compile M00's cycle contract; M00 deliberately has no AgentTask."""
    root = Path(root)
    required = {"run_id", "cycle_id", "base_hash"}
    if set(cycle_context) != required:
        raise PromptContractError("M00 context must contain only run_id, cycle_id, and base_hash")
    registry = PromptRegistry(root)
    stable, stable_hash = registry.immutable("global")
    role_core, role_hash = registry.immutable("M00")
    overlay, _ = registry.overlay("M00", overlay_version)
    schema_name = "agent-proposal.schema.json"
    output_schema = json.dumps(_schema(root, schema_name), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    context = json.dumps(dict(cycle_context), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    text = stable.rstrip() + "\n\n" + role_core.rstrip() + "\n\n# Contexto do ciclo\n" + context + overlay + "\n# Schema de saída\n" + output_schema + "\n"
    return CompiledPrompt("M00", _sha256_bytes((stable_hash + role_hash).encode("ascii")), overlay_version, schema_name, text)
