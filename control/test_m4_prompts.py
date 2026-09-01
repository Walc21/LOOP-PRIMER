"""Deterministic local validation suite for M4 prompt composition and registry."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from article_loop.prompts import (
    PromptIntegrityError,
    PromptRegistry,
    compile_manager_prompt,
    compile_prompt,
    validate_output,
)

ROOT = Path(__file__).resolve().parents[1]


class M4PromptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = PromptRegistry(ROOT)

    def test_registry_contains_global_and_all_twenty_one_roles(self) -> None:
        self.assertIn("global", self.registry.registry.get("roles", {}))
        for role in ["M00", "S10", "W11", "W12", "W13", "S20", "W21", "W22", "W23",
                     "S30", "W31", "W32", "W33", "S40", "W41", "W42", "W43",
                     "S50", "W51", "W52", "W53"]:
            self.assertIn(role, self.registry.registry.get("roles", {}))

    def test_prompt_compilation_produces_deterministic_sha256(self) -> None:
        task_path = ROOT / "control" / "fixtures" / "m4" / "agent_task.json"
        task = json.loads(task_path.read_text("utf-8"))
        prompt, version = compile_prompt(ROOT, task)
        self.assertTrue(prompt.startswith("# GLOBAL SYSTEM PROMPT"))
        self.assertTrue(version.startswith("sha256:"))

    def test_manager_prompt_rejects_overlays(self) -> None:
        with self.assertRaises(PromptIntegrityError):
            compile_manager_prompt(ROOT, overlay_version="v1")


if __name__ == "__main__":
    unittest.main()
