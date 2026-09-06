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


class M6OperationalAdapter:
    """Project-owned non-Prime root adapter authorized by the M6 boundary."""


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

    def _handle(self, value: Any) -> ChildHandle:
        """Convert only the documented Prime handle, never an object repr."""
        child_id = getattr(value, "rlm_child_id", None)
        name = getattr(value, "name", None)
        session_dir = getattr(value, "session_dir", None)
        model = getattr(value, "model", None)
        if not all(isinstance(x, str) and x for x in (child_id, name, session_dir)):
            raise ValueError("Prime returned an incomplete child handle")
        if model is not None and not isinstance(model, str):
            raise ValueError("Prime returned an invalid child model")
        return ChildHandle(child_id, name, session_dir, model, self.actor_id,
                           self.actor_role, self.depth + 1)

    async def preflight(self) -> dict[str, Any]:
        surfaces = {
            "rlm": callable(self.rlm_api),
            "list_subagents": callable(getattr(self.rlm_api, "list_subagents", None)),
            "delete_subagent": callable(getattr(self.rlm_api, "delete_subagent", None)),
            "agent_message.send": callable(getattr(self.agent_message, "send", None)),
        }
        if self.actor_role not in {"M00", "S10", "S20", "S30", "S40", "S50"} or self.depth not in {0, 1}:
            raise ValueError("invalid Prime actor role or depth")
        if (self.actor_role == "M00") != (self.depth == 0) or (self.actor_role != "M00") != (self.depth == 1):
            raise ValueError("Prime actor role/depth mismatch")
        if not all(surfaces.values()):
            raise ValueError("required Prime surface is unavailable")
        return {"adapter": "prime", "actor_role": self.actor_role, "depth": self.depth,
                "surfaces": surfaces, "required_session_command": "/rlm-max-depth 2"}

    async def spawn(self, prompt: str, *, name: str) -> ChildHandle:
        handle = await self.rlm_api(prompt, name=name)
        child = self._handle(handle)
        if child.name != name: raise ValueError("Prime child name differs from requested name")
        return child

    async def list_subagents(self) -> list[ChildHandle]:
        result = await self.rlm_api.list_subagents()
        if not isinstance(result, list): raise ValueError("Prime list_subagents returned invalid value")
        return [self._handle(x) for x in result]

    async def send_parent(self, message: str) -> None:
        # The installed documented subset has no ``mode`` argument.
        await self.agent_message.send(message, receiver_role="parent")

    async def delete_subagent(self, child_id: str) -> None:
        child = next((x for x in await self.list_subagents() if x.child_id == child_id), None)
        if child is None: raise ValueError("Prime child is not a direct child of this actor")
        # The installed API documents deletion by the direct child identity.
        await self.rlm_api.delete_subagent(child.child_id)


class FakeRLMAdapter:
    """Deterministic in-memory RLM proof; it is never selected implicitly."""
    is_prime = False
    is_test_double = True

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
