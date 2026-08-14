"""Small, documented boundary around Prime Agent RLM surfaces.

The production adapter deliberately accepts injected kernel objects: importing
this module is offline and cannot start Prime Agent or a model.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping
import hashlib


@dataclass(frozen=True)
class ChildHandle:
    child_id: str
    name: str
    session_dir: str
    model: str | None = None


class PrimeRLMAdapter:
    """Adapter for the installed `rlm`/`agent_message` subset only."""
    def __init__(self, rlm_api: Any, agent_message: Any):
        self.rlm_api, self.agent_message = rlm_api, agent_message

    async def preflight(self) -> dict[str, Any]:
        # The interactive command itself belongs to the authorized root session.
        return {"required_command": "/rlm-max-depth 2", "global": False}

    async def spawn(self, prompt: str, *, name: str) -> ChildHandle:
        handle = await self.rlm_api(prompt, name=name)
        return ChildHandle(handle.rlm_child_id, handle.name, handle.session_dir, getattr(handle, "model", None))

    async def send_parent(self, message: str) -> Any:
        return await self.agent_message.send(message, receiver_role="parent")

    async def delete(self, handle: ChildHandle) -> None:
        for item in await self.rlm_api.list_subagents():
            if getattr(item, "rlm_child_id", None) == handle.child_id:
                await self.rlm_api.delete_subagent(item)
                return


class FakeRLMAdapter:
    """Offline admission recorder used by M6 tests; it never runs a model."""
    def __init__(self):
        self.children: dict[str, ChildHandle] = {}
        self.calls: list[dict[str, str]] = []
        self.messages: list[str] = []
        self.cancelled: list[str] = []

    async def preflight(self) -> dict[str, Any]:
        return {"required_command": "/rlm-max-depth 2", "global": False, "fake": True}

    async def spawn(self, prompt: str, *, name: str) -> ChildHandle:
        if name in self.children:
            return self.children[name]
        digest = hashlib.sha256(name.encode()).hexdigest()[:20]
        handle = ChildHandle(f"fake-{digest}", name, f".fake-sessions/{name}", "fake")
        self.children[name] = handle; self.calls.append({"name": name, "prompt": prompt})
        return handle

    async def send_parent(self, message: str) -> dict[str, str]:
        self.messages.append(message); return {"status": "recorded"}

    async def delete(self, handle: ChildHandle) -> None:
        self.cancelled.append(handle.child_id)

    def handle(self, name: str) -> Mapping[str, Any]:
        return asdict(self.children[name])
