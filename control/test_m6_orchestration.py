"""Deterministic local validation suite for M6 orchestrator and journal."""
from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from article_loop.adapters import FakeRLMAdapter
from article_loop.orchestrator import Orchestrator
from article_loop.store import DurableStore


class M6OrchestrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="test_m6_orch_")
        self.root = Path(self.temp_dir)
        self.store = DurableStore(self.root)
        self.adapter = FakeRLMAdapter()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fake_adapter_spawn_and_lifecycle(self) -> None:
        async def run_test():
            child = await self.adapter.spawn_subagent(
                prompt="Test prompt",
                name="S10",
                session_dir=str(self.root / "workspaces" / "test"),
                model="test-model",
            )
            self.assertEqual(child.name, "S10")
            children = await self.adapter.list_subagents()
            self.assertEqual(len(children), 1)
            await self.adapter.delete_subagent(child.rlm_child_id)
            children_after = await self.adapter.list_subagents()
            self.assertEqual(len(children_after), 0)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
