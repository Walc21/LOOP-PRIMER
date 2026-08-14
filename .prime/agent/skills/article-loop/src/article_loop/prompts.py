"""Deterministic, local prompt-contract compilation for M4.

This module composes text only.  It neither invokes Prime Agent nor writes a
candidate, challenger, or champion.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
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
TASK_CONTEXT_FIELDS = (
    "run_id", "cycle_id", "base_hash", "activation_mode", "scope", "input_locators",
)


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

    def _entry(self, role_id: str) -> Mapping[str, Any]:
        entry = self.registry.get("immutable", {}).get(role_id)
        if not isinstance(entry, dict):
            raise PromptIntegrityError(f"unknown immutable prompt: {role_id}")
        return entry

    def immutable(self, role_id: str) -> tuple[str, str]:
        entry = self._entry(role_id)
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise PromptIntegrityError(f"invalid immutable registry entry: {role_id}")
        path = self.prompt_root / relative
        if path.resolve().parent != (self.prompt_root / "immutable").resolve() or not path.is_file():
            raise PromptIntegrityError(f"invalid immutable prompt path: {role_id}")
        raw = path.read_bytes()
        actual = _sha256_bytes(raw)
        if actual != expected:
            raise PromptIntegrityError(f"immutable prompt hash mismatch: {role_id}")
        return raw.decode("utf-8"), actual

    def overlay(self, role_id: str, version: str | None) -> tuple[str, Mapping[str, Any]]:
        if version is None:
            return "", {}
        versions = self.registry.get("overlays", {}).get(role_id, {})
        entry = versions.get(version) if isinstance(versions, dict) else None
        if not isinstance(entry, dict):
            raise PromptIntegrityError(f"unknown overlay version: {role_id}/{version}")
        relative, expected = entry.get("path"), entry.get("hash")
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise PromptIntegrityError("invalid overlay registry entry")
        path = self.prompt_root / relative
        expected_parent = (self.prompt_root / "overlays" / role_id).resolve()
        if path.resolve().parent != expected_parent or not path.is_file():
            raise PromptIntegrityError("invalid overlay path")
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            raise PromptIntegrityError("invalid overlay yaml") from error
        required = {"parent_version", "diagnostic", "author", "evidence", "scope", "hash", "rollback", "instructions"}
        if not isinstance(document, dict) or set(document) != required:
            raise PromptIntegrityError("overlay has invalid fields")
        calculated = _sha256_bytes(_canonical_json({key: value for key, value in document.items() if key != "hash"}))
        if document["hash"] != expected or calculated != expected:
            raise PromptIntegrityError("overlay hash mismatch")
        if document["parent_version"] is not None and document["parent_version"] not in versions:
            raise PromptIntegrityError("overlay parent version is unknown")
        rollback = document["rollback"]
        if rollback is not None and rollback not in versions:
            raise PromptIntegrityError("overlay rollback is unknown")
        if not all(isinstance(document[key], str) and document[key] for key in ("diagnostic", "author", "instructions")):
            raise PromptIntegrityError("overlay text is invalid")
        if not isinstance(document["evidence"], list) or not document["evidence"] or not isinstance(document["scope"], list) or not document["scope"]:
            raise PromptIntegrityError("overlay evidence or scope is invalid")
        return "\n\n# Overlay versionado\n" + document["instructions"].strip() + "\n", document


def _schema(root: Path, name: str) -> Mapping[str, Any]:
    try:
        return json.loads((root / "config" / "schemas" / name).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PromptContractError(f"output schema unavailable: {name}") from error


def validate_output(root: str | Path, schema_name: str, output: Mapping[str, Any]) -> None:
    if schema_name not in {"agent-proposal.schema.json", "department-packet.schema.json"}:
        raise PromptContractError("unsupported output schema")
    try:
        jsonschema.Draft202012Validator(_schema(Path(root), schema_name)).validate(dict(output))
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
        jsonschema.Draft202012Validator(task_schema).validate(dict(task))
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

    registry = PromptRegistry(root)
    stable, stable_hash = registry.immutable("global")
    role_core, role_hash = registry.immutable(role_id)
    overlay, _ = registry.overlay(role_id, overlay_version)
    schema_name = task["requested_output_schema"]
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
