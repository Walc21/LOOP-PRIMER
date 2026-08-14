"""M4 prompt contracts are local fixtures; they never start real agents."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime" / "agent" / "skills" / "article-loop" / "src"
sys.path.insert(0, str(SRC))

from article_loop.prompts import (  # noqa: E402
    ROLE_IDS,
    PromptContractError,
    PromptIntegrityError,
    PromptRegistry,
    compile_manager_prompt,
    compile_prompt,
    validate_output,
)

FIXTURES = ROOT / "control" / "fixtures" / "m4"
BASE_HASH = "0" * 64


def task_for(role_id: str) -> dict[str, object]:
    return {
        "schema_version": "1.1.0",
        "task_id": f"task-{role_id}",
        "run_id": "run-fixture",
        "cycle_id": 0,
        "role_id": role_id,
        "activation_mode": "RUN",
        "created_at": "2026-08-13T12:00:00Z",
        "base_hash": BASE_HASH,
        "scope": ["page:1"],
        "input_locators": ["article.pdf#page=1"],
        "requested_output_schema": (
            "department-packet.schema.json" if role_id.startswith("S") else "agent-proposal.schema.json"
        ),
        "prompt_version": "m4",
        "constraints": ["offline"],
    }


def context_for(task: dict[str, object]) -> dict[str, object]:
    return {key: task[key] for key in ("run_id", "cycle_id", "base_hash", "activation_mode", "scope", "input_locators")}


class PromptContractsTests(unittest.TestCase):
    def copy_contract_root(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        destination = Path(temp.name)
        shutil.copytree(ROOT / "prompts", destination / "prompts")
        shutil.copytree(ROOT / "config", destination / "config")
        return temp

    def test_all_21_compiled_prompts_match_snapshots(self) -> None:
        expected = json.loads((FIXTURES / "prompt-snapshots.json").read_text(encoding="utf-8"))
        actual: dict[str, str] = {}
        registry = PromptRegistry(ROOT)
        for role_id in sorted(ROLE_IDS):
            if role_id == "M00":
                compiled = compile_manager_prompt(ROOT, {"run_id": "run-fixture", "cycle_id": 0, "base_hash": BASE_HASH})
            else:
                task = task_for(role_id)
                compiled = compile_prompt(ROOT, task, context_for(task))
            actual[role_id] = hashlib.sha256(compiled.text.encode("utf-8")).hexdigest()
            self.assertTrue(compiled.text.startswith("# Núcleo estável de revisão auditável"))
            self.assertEqual(compiled.immutable_hash, hashlib.sha256((
                registry.immutable("global")[1] + registry.immutable(role_id)[1]
            ).encode("ascii")).hexdigest())
        self.assertEqual(actual, expected)

    def test_prompt_contract_sections_and_required_dependencies(self) -> None:
        headings = ("Papel", "Objetivo", "Escopo permitido", "Entradas", "Critérios de sucesso", "Evidências exigidas", "Formato de saída", "Validações", "Dependências", "Limites de autonomia", "Regra de parada")
        for role_id in ROLE_IDS:
            text = (ROOT / "prompts" / "immutable" / f"{role_id}.md").read_text(encoding="utf-8")
            for heading in headings:
                self.assertIn(heading, text)
        global_core = (ROOT / "prompts" / "immutable" / "global.md").read_text(encoding="utf-8")
        self.assertNotIn("chain of thought", global_core.lower())
        self.assertIn("S30 -> S20", (ROOT / "prompts" / "immutable" / "S30.md").read_text(encoding="utf-8"))
        self.assertIn("S40 -> S20", (ROOT / "prompts" / "immutable" / "S40.md").read_text(encoding="utf-8"))
        self.assertIn("S50: sem autoridade semântica", (ROOT / "prompts" / "immutable" / "S50.md").read_text(encoding="utf-8"))

    def test_structured_output_fixtures_validate(self) -> None:
        proposal = json.loads((FIXTURES / "agent_proposal.json").read_text(encoding="utf-8"))
        packet = json.loads((FIXTURES / "department_packet.json").read_text(encoding="utf-8"))
        validate_output(ROOT, "agent-proposal.schema.json", proposal)
        validate_output(ROOT, "department-packet.schema.json", packet)
        proposal["confidence"] = 2
        with self.assertRaises(PromptContractError):
            validate_output(ROOT, "agent-proposal.schema.json", proposal)

    def test_immutable_overwrite_and_unknown_version_block_execution(self) -> None:
        with self.copy_contract_root() as temporary:
            root = Path(temporary)
            core = root / "prompts" / "immutable" / "W11.md"
            core.write_text(core.read_text(encoding="utf-8") + "\nmutação indevida\n", encoding="utf-8")
            task = task_for("W11")
            with self.assertRaises(PromptIntegrityError):
                compile_prompt(root, task, context_for(task))
        task = task_for("W11")
        with self.assertRaises(PromptIntegrityError):
            compile_prompt(ROOT, task, context_for(task), overlay_version="desconhecida")

    def test_invalid_overlay_and_unknown_rollback_block_execution(self) -> None:
        task = task_for("W11")
        compiled = compile_prompt(ROOT, task, context_for(task), overlay_version="v1")
        self.assertIn("# Overlay versionado", compiled.text)
        with self.copy_contract_root() as temporary:
            root = Path(temporary)
            overlay_path = root / "prompts" / "overlays" / "W11" / "v1.yaml"
            overlay_path.write_text("instructions: ausente\n", encoding="utf-8")
            with self.assertRaises(PromptIntegrityError):
                compile_prompt(root, task, context_for(task), overlay_version="v1")
        with self.copy_contract_root() as temporary:
            root = Path(temporary)
            overlay_path = root / "prompts" / "overlays" / "W11" / "v1.yaml"
            overlay = yaml.safe_load(overlay_path.read_text(encoding="utf-8"))
            overlay["rollback"] = "inexistente"
            payload = {key: value for key, value in overlay.items() if key != "hash"}
            overlay["hash"] = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
            overlay_path.write_text(yaml.safe_dump(overlay, allow_unicode=True, sort_keys=False), encoding="utf-8")
            registry_path = root / "prompts" / "registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["overlays"]["W11"]["v1"]["hash"] = overlay["hash"]
            registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(PromptIntegrityError, "rollback"):
                compile_prompt(root, task, context_for(task), overlay_version="v1")

    def test_context_is_closed_and_never_exposes_champion(self) -> None:
        task = task_for("W11")
        context = context_for(task)
        context["champion"] = "candidate-secret"
        with self.assertRaisesRegex(PromptContractError, "not permitted"):
            compile_prompt(ROOT, task, context)
        compiled = compile_prompt(ROOT, task, context_for(task))
        self.assertNotIn("candidate-secret", compiled.text)


if __name__ == "__main__":
    unittest.main()
