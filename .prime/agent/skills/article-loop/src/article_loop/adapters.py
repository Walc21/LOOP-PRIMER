"""Small, explicit adapters around the installed RLM surfaces.

The adapter deliberately models the session which is making a call.  It never
pretends that a root-session ``rlm`` call can create a grandchild.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ChildHandle:
    child_id: str
    name: str
    session_dir: str
    model: str | None = None
    parent_id: str | None = None
    actor_role: str = "M00"
    depth: int = 0


class PrimeRLMAdapter:
    """Adapter for one already-authorized, current Prime session.

    ``rlm_api`` and ``agent_message`` are injected by that session.  No remote
    session construction is attempted: a submanager must construct its own
    adapter when its prompt is running.
    """
    is_prime = True

    def __init__(self, rlm_api: Any, agent_message: Any, *, actor_role: str,
                 actor_id: str, depth: int):
        self.rlm_api, self.agent_message = rlm_api, agent_message
        self.actor_role, self.actor_id, self.depth = actor_role, actor_id, depth

    async def spawn(self, prompt: str, *, name: str) -> ChildHandle:
        handle = await self.rlm_api(prompt, name=name)
        return ChildHandle(str(getattr(handle, "id", handle)), name,
                           str(getattr(handle, "session_dir", "")),
                           getattr(handle, "model", None), self.actor_id,
                           self.actor_role, self.depth + 1)

    async def list_subagents(self) -> list[ChildHandle]:
        result = await self.rlm_api.list_subagents()
        return [ChildHandle(str(getattr(x, "id", x)), str(getattr(x, "name", "")),
                            str(getattr(x, "session_dir", "")), getattr(x, "model", None),
                            self.actor_id, self.actor_role, self.depth + 1) for x in result]

    async def send_parent(self, message: str) -> None:
        # The installed documented subset has no ``mode`` argument.
        await self.agent_message.send(message, receiver_role="parent")

    async def delete_subagent(self, child_id: str) -> None:
        await self.rlm_api.delete_subagent(child_id)


class FakeRLMAdapter:
    """Deterministic in-memory RLM proof; it is never selected implicitly."""
    is_prime = False

    def __init__(self, *, actor_role: str = "M00", actor_id: str = "root",
                 depth: int = 0, registry: dict[str, ChildHandle] | None = None,
                 calls: list[dict[str, Any]] | None = None,
                 messages: list[dict[str, Any]] | None = None,
                 cancelled: list[str] | None = None):
        self.actor_role, self.actor_id, self.depth = actor_role, actor_id, depth
        self.registry = registry if registry is not None else {}
        self.calls = calls if calls is not None else []
        self.messages = messages if messages is not None else []
        self.cancelled = cancelled if cancelled is not None else []

    async def spawn(self, prompt: str, *, name: str) -> ChildHandle:
        prior = next((x for x in self.registry.values() if x.name == name), None)
        if prior is not None:
            return prior
        child = ChildHandle("fake-" + str(len(self.registry) + 1), name,
                            str(Path(".fake-sessions") / name), None,
                            self.actor_id, self.actor_role, self.depth + 1)
        self.registry[child.child_id] = child
        self.calls.append({"name": name, "parent_id": self.actor_id,
                           "actor_role": self.actor_role, "depth": self.depth,
                           "prompt": prompt})
        return child

    async def list_subagents(self) -> list[ChildHandle]:
        return [x for x in self.registry.values() if x.parent_id == self.actor_id]

    def for_child(self, child: ChildHandle | str, *, actor_role: str | None = None) -> "FakeRLMAdapter":
        if isinstance(child, str):
            try: child = self.registry[child]
            except KeyError as error: raise ValueError("unknown fake child") from error
        return FakeRLMAdapter(actor_role=actor_role or child.name.rsplit("-", 1)[-1].upper(),
                              actor_id=child.child_id, depth=child.depth,
                              registry=self.registry, calls=self.calls,
                              messages=self.messages, cancelled=self.cancelled)

    async def send_parent(self, message: str) -> None:
        self.messages.append({"sender_id": self.actor_id, "actor_role": self.actor_role,
                              "depth": self.depth, "message": message})

    async def delete_subagent(self, child_id: str) -> None:
        self.cancelled.append(child_id)
        self.registry.pop(child_id, None)

    async def preflight(self) -> dict[str, Any]:
        return {"adapter": "fake", "actor_role": self.actor_role, "depth": self.depth}
