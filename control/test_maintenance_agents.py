"""Static contract tests for the separate, ephemeral maintenance team."""
from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".prime/agent/skills/repo-maintenance/SKILL.md"
ROLES = ROOT / ".prime/agent/skills/repo-maintenance/references/roles.md"
DOC = ROOT / "docs/maintenance-agents.md"


class MaintenanceAgentContractTests(unittest.TestCase):
    def documents(self) -> dict[Path, str]:
        return {path: path.read_text(encoding="utf-8") for path in (SKILL, ROLES, DOC)}

    def test_project_local_markdown_structure_is_complete(self) -> None:
        documents = self.documents()
        self.assertTrue(SKILL.is_file())
        self.assertTrue(ROLES.is_file())
        self.assertTrue(DOC.is_file())
        self.assertIn("name: repo-maintenance", documents[SKILL])
        self.assertIn("maint-coordinator", "\n".join(documents.values()))
        self.assertIn("maint-implementer", "\n".join(documents.values()))
        self.assertIn("maint-verifier", "\n".join(documents.values()))

    def test_one_writer_then_read_only_verifier(self) -> None:
        text = "\n".join(self.documents().values())
        self.assertIn("exatamente um", text)
        self.assertIn("único escritor", text)
        self.assertIn("somente leitura", text)
        self.assertIn("Filhos são folhas", text)
        self.assertIn("não cria filhos", text)

    def test_only_verified_coordination_surfaces_are_named(self) -> None:
        text = "\n".join(self.documents().values())
        for surface in (
            "rlm.spawn", "rlm.list_subagents", "rlm.delete_subagent",
            "agent_message.send",
        ):
            self.assertIn(surface, text)
        for invented in (
            "call_skill(", "run_subagent(", "rlm.collect", "agent_observe",
            ".prime/agent/agents/", "team.yaml",
        ):
            if invented in {".prime/agent/agents/", "team.yaml"}:
                self.assertIn(invented, text)
            else:
                self.assertNotIn(invented, text)

    def test_handoff_v1_has_closed_state_and_required_fields(self) -> None:
        text = self.documents()[ROLES]
        for field in (
            "version=1", "task=", "role=", "phase=", "state=",
            "files=", "commands=", "risks=", "next=",
        ):
            self.assertIn(field, text)
        self.assertRegex(text, re.compile(r"state=PASS\|BLOCKED\|UNCERTAIN"))
        self.assertIn("cadeia de raciocínio", text)
        self.assertIn("segredo", text)


if __name__ == "__main__":
    unittest.main()
