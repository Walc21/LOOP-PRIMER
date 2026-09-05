"""M12.5.1 dual execution wiring, offline and fail-closed by default.

The module does not start Prime or a model.  It selects the already-authorized
execution layer per department, gives routed departments a durable local
control actor, materializes only M6-authorized context, and returns scientific
output through the existing M6 receipt boundary.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping, Sequence

import jsonschema

from .adapters import ChildHandle
from .budget import load_budget_config
from .inference import (
    InferenceConfigError, InferenceIntegrityError, InferenceRequest,
    InferenceRuntime, ModelRegistry, PRIVACY_MODES, canonical_bytes, sha256,
)
from .orchestrator import Orchestrator, OrchestrationError, SCHEMA_VERSION as M6_SCHEMA_VERSION


DEPARTMENTS = frozenset({f"S{number}0" for number in range(1, 6)})
WORKERS = frozenset({f"W{department}{worker}" for department in range(1, 6) for worker in range(1, 4)})
TEXT_SUFFIXES = frozenset({".txt", ".tex", ".bib", ".md", ".json", ".yaml", ".yml"})
_ROLE_SUFFIX = re.compile(r"-(s[1-5]0|w[1-5][1-3])\Z")


class ExecutionError(RuntimeError):
    """Execution configuration, context, or dual-layer integration failed."""


@dataclass(frozen=True)
class ExecutionPolicy:
    enabled: bool
    mode: str
    departments: Mapping[str, str]
    remote_content_mode: str
    config_hash: str

    @classmethod
    def from_mapping(cls, config: Mapping[str, Any]) -> "ExecutionPolicy":
        execution = config.get("execution")
        privacy = config.get("privacy")
        if not isinstance(execution, Mapping) or set(execution) != {
            "schema_version", "enabled", "mode", "departments",
        }:
            raise ExecutionError("execution configuration fields are invalid")
        if execution.get("schema_version") != "1.0.0" or execution.get("mode") != "dual":
            raise ExecutionError("execution configuration version/mode is invalid")
        if type(execution.get("enabled")) is not bool:
            raise ExecutionError("execution.enabled must be boolean")
        departments = execution.get("departments")
        if not isinstance(departments, Mapping) or any(
            role not in DEPARTMENTS or layer not in {"prime", "routed"}
            for role, layer in departments.items()
        ):
            raise ExecutionError("execution department map is invalid")
        if not isinstance(privacy, Mapping) or set(privacy) != {
            "schema_version", "remote_content_mode",
        }:
            raise ExecutionError("privacy configuration fields are invalid")
        privacy_mode = privacy.get("remote_content_mode")
        if privacy.get("schema_version") != "1.0.0" or privacy_mode not in PRIVACY_MODES:
            raise ExecutionError("privacy configuration is invalid")
        return cls(
            execution["enabled"], execution["mode"], dict(departments),
            privacy_mode, sha256(canonical_bytes(config)),
        )

    @classmethod
    def from_project(cls, root: str | Path) -> "ExecutionPolicy":
        return cls.from_mapping(load_budget_config(root))

    def layer(self, department: str) -> str:
        if department not in DEPARTMENTS:
            raise ExecutionError("unknown department")
        if not self.enabled:
            raise ExecutionError("execution is disabled")
        try:
            return self.departments[department]
        except KeyError as error:
            raise ExecutionError("department has no execution layer") from error


@dataclass(frozen=True)
class ContextItem:
    locator: str
    source: str
    sha256: str
    text: str

    def public(self) -> dict[str, Any]:
        return {"locator": self.locator, "source": self.source, "sha256": self.sha256, "text": self.text}


@dataclass(frozen=True)
class MaterializedContext:
    task_id: str
    privacy_mode: str
    items: tuple[ContextItem, ...]
    omitted_binary_locators: tuple[str, ...]
    context_hash: str
    estimated_tokens: int

    def prompt_fragment(self) -> str:
        value = {
            "task_id": self.task_id,
            "privacy_mode": self.privacy_mode,
            "items": [item.public() for item in self.items],
            "omitted_binary_locators": list(self.omitted_binary_locators),
            "context_hash": self.context_hash,
        }
        return canonical_bytes(value).decode("ascii")


class ContextMaterializer:
    """Resolve only locators present in an AgentTask and its closed M5 view."""

    def __init__(self, root: str | Path):
        raw = Path(root)
        if raw.is_symlink() or not raw.is_dir():
            raise ExecutionError("context root must be a regular directory")
        self.root = raw.resolve()

    def _contained(self, raw: str) -> Path:
        path = Path(raw)
        if not path.is_absolute():
            path = self.root / path
        current = Path(path.anchor)
        for component in path.parts[1:]:
            current = current / component
            if current.is_symlink():
                raise ExecutionError("context locator crosses a symlink")
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise ExecutionError("context locator does not exist") from error
        if resolved != self.root and self.root not in resolved.parents:
            raise ExecutionError("context locator escapes the project root")
        current = resolved
        while current != self.root:
            if current.is_symlink():
                raise ExecutionError("context locator crosses a symlink")
            current = current.parent
        return resolved

    @staticmethod
    def _read_text(path: Path) -> str:
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            raise ExecutionError("context source is not an authorized text file")
        try:
            data = path.read_bytes()
            text = data.decode("utf-8")
        except (OSError, UnicodeError) as error:
            raise ExecutionError("context text is unreadable") from error
        if "\x00" in text:
            raise ExecutionError("context text contains a NUL byte")
        return text

    def _path_items(self, locator: str, raw_path: str) -> tuple[list[ContextItem], bool]:
        path = self._contained(raw_path)
        if path.is_file() and path.suffix.lower() == ".pdf":
            # Deliberately do not open or hash the immutable binary PDF.  M3's
            # extracted text locator is a separate required task input.
            return [], True
        candidates: list[Path]
        if path.is_dir():
            candidates = []
            for candidate in sorted(path.rglob("*")):
                if candidate.is_symlink():
                    raise ExecutionError("context tree contains a symlink")
                if candidate.is_file() and candidate.suffix.lower() in TEXT_SUFFIXES:
                    candidates.append(candidate)
        else:
            candidates = [path]
        result = []
        for candidate in candidates:
            text = self._read_text(candidate)
            source = str(candidate.relative_to(self.root))
            result.append(ContextItem(locator, source, sha256(text.encode("utf-8")), text))
        return result, False

    def _blackboard_item(self, run_id: str, locator: str, view: Mapping[str, Any]) -> ContextItem:
        token = locator.split(":", 1)[1]
        matching = []
        source = "closed-view"
        for key in ("dependent_claims", "local_history"):
            matching.extend(
                dict(value) for value in view.get(key, [])
                if isinstance(value, Mapping) and value.get("locator") == locator
            )
        directory = self.root / "state" / "blackboard" / run_id
        if directory.exists():
            directory = self._contained(str(directory))
            for path in sorted(directory.glob("*.jsonl")):
                if path.is_symlink() or not path.is_file():
                    raise ExecutionError("blackboard ledger is unsafe")
                try:
                    for line in path.read_text(encoding="utf-8").splitlines():
                        value = json.loads(line)
                        if isinstance(value, Mapping) and (
                            value.get("record_id") == token or value.get("claim_id") == token
                        ):
                            matching.append(dict(value))
                            source = str(path.relative_to(self.root))
                except (OSError, UnicodeError, json.JSONDecodeError) as error:
                    raise ExecutionError("blackboard ledger is unreadable") from error
        text = canonical_bytes(matching).decode("ascii")
        return ContextItem(locator, source, sha256(text.encode("ascii")), text)

    def materialize(
        self, task: Mapping[str, Any], view: Mapping[str, Any], *,
        privacy_mode: str, context_limit: int, max_output_tokens: int,
        overhead_tokens: int = 512,
    ) -> MaterializedContext:
        if privacy_mode not in PRIVACY_MODES:
            raise ExecutionError("privacy mode is invalid")
        schema_path = self.root / "config/schemas/agent-task.schema.json"
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(task)
        except (OSError, json.JSONDecodeError, jsonschema.ValidationError) as error:
            raise ExecutionError("AgentTask is invalid") from error
        if not isinstance(view, Mapping) or view.get("task") != task:
            raise ExecutionError("closed view is not bound to AgentTask")
        if any(type(value) is not int or value < 0 for value in (context_limit, max_output_tokens, overhead_tokens)):
            raise ExecutionError("context limits must be non-negative integers")
        authorized = set(task["input_locators"])
        view_locators: set[str] = set()
        for key in ("excerpts",):
            values = view.get(key, [])
            if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
                raise ExecutionError("closed view locators are invalid")
            view_locators.update(values)
        for key in ("dependent_claims", "local_history"):
            values = view.get(key, [])
            if not isinstance(values, list):
                raise ExecutionError("closed view items are invalid")
            for value in values:
                if not isinstance(value, Mapping) or not isinstance(value.get("locator"), str):
                    raise ExecutionError("closed view item lacks a locator")
                view_locators.add(value["locator"])
        rubric = view.get("rubric")
        if rubric is not None:
            if not isinstance(rubric, Mapping) or not isinstance(rubric.get("locator"), str):
                raise ExecutionError("closed rubric locator is invalid")
            view_locators.add(rubric["locator"])
        if not view_locators.issubset(authorized):
            raise ExecutionError("closed view widens AgentTask locators")
        items: list[ContextItem] = []
        omitted: list[str] = []
        for locator in sorted(view_locators):
            if locator.startswith("readonly:history:"):
                resolved, binary = self._path_items(locator, locator[len("readonly:history:"):])
            elif locator.startswith("readonly:"):
                resolved, binary = self._path_items(locator, locator[len("readonly:"):])
            elif locator.startswith("blackboard:"):
                resolved = [self._blackboard_item(task["run_id"], locator, view)]
                binary = False
            else:
                raise ExecutionError("unsupported context locator")
            items.extend(resolved)
            if binary:
                omitted.append(locator)
        if omitted and not items:
            raise ExecutionError("binary PDF locator has no authorized extracted text companion")
        identity = {
            "task_id": task["task_id"], "privacy_mode": privacy_mode,
            "items": [item.public() for item in items],
            "omitted_binary_locators": omitted,
        }
        context_hash = sha256(canonical_bytes(identity))
        estimated = (len(canonical_bytes(identity)) + 3) // 4
        if estimated + max_output_tokens + overhead_tokens > context_limit:
            raise ExecutionError("materialized context exceeds the target context limit")
        return MaterializedContext(
            task["task_id"], privacy_mode, tuple(items), tuple(omitted),
            context_hash, estimated,
        )

    @staticmethod
    def enforce_remote_policy(context: MaterializedContext, *, target_local: bool) -> None:
        if type(target_local) is not bool:
            raise ExecutionError("target locality must be boolean")
        if not target_local and context.privacy_mode == "deny_remote":
            raise ExecutionError("privacy policy denies remote content")


class RoutedControlAdapter:
    """Operational, local control actor; it persists handles, never model text."""

    is_prime = False
    is_test_double = False

    def __init__(self, root: str | Path, run_id: str, *, actor_role: str, actor_id: str, depth: int):
        self.root = Path(root).resolve()
        self.run_id = run_id
        self.actor_role = actor_role
        self.actor_id = actor_id
        self.depth = depth
        self.directory = self.root / "state" / "execution" / run_id / "handles"
        self.actors_directory = self.root / "state" / "execution" / run_id / "actors"
        self.lock_path = self.root / "state" / "locks" / f"{run_id}.execution.lock"
        for path in (self.root / "state/execution", self.root / "state/execution" / run_id, self.directory, self.actors_directory, self.root / "state/locks"):
            if path.exists() and (path.is_symlink() or not path.is_dir()):
                raise ExecutionError("unsafe execution state directory")
            path.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _lock(self):
        if self.lock_path.is_symlink():
            raise ExecutionError("execution lock is symlinked")
        with self.lock_path.open("a+", encoding="utf-8") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    @staticmethod
    def _role(name: str) -> str:
        match = _ROLE_SUFFIX.search(name)
        if match is None:
            raise ExecutionError("deterministic child name lacks a role")
        return match.group(1).upper()

    def _expected(self, role: str) -> bool:
        if self.actor_role == "M00":
            return self.depth == 0 and role in DEPARTMENTS
        return self.actor_role in DEPARTMENTS and self.depth == 1 and role in WORKERS and role[1] == self.actor_role[1]

    def _read(self, path: Path) -> ChildHandle:
        if path.is_symlink() or not path.is_file():
            raise ExecutionError("routed handle is unsafe")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ExecutionError("routed handle is invalid") from error
        fields = {"child_id", "name", "session_dir", "model", "parent_id", "actor_role", "depth", "prompt_hash"}
        if not isinstance(value, dict) or set(value) != fields:
            raise ExecutionError("routed handle fields are invalid")
        handle = ChildHandle(**{key: value[key] for key in fields - {"prompt_hash"}})
        if handle.parent_id != self.actor_id or handle.actor_role != self.actor_role or handle.depth != self.depth + 1:
            raise ExecutionError("routed handle parent/depth differs")
        return handle

    async def spawn(self, prompt: str, *, name: str) -> ChildHandle:
        if not isinstance(prompt, str) or not prompt or not isinstance(name, str):
            raise ExecutionError("routed admission input is invalid")
        role = self._role(name)
        if not self._expected(role):
            raise ExecutionError("routed control actor cannot admit this role")
        child_id = "routed-" + hashlib.sha256(f"{self.run_id}\0{self.actor_id}\0{name}".encode()).hexdigest()[:40]
        path = self.directory / f"{child_id}.json"
        value = {
            "child_id": child_id, "name": name,
            "session_dir": str(self.actors_directory / child_id),
            "model": None, "parent_id": self.actor_id,
            "actor_role": self.actor_role, "depth": self.depth + 1,
            "prompt_hash": sha256(prompt.encode("utf-8")),
        }
        encoded = canonical_bytes(value) + b"\n"
        with self._lock():
            actor_directory = self.actors_directory / child_id
            if actor_directory.exists() and (actor_directory.is_symlink() or not actor_directory.is_dir()):
                raise ExecutionError("routed actor directory is unsafe")
            actor_directory.mkdir(exist_ok=True)
            actors_fd = os.open(self.actors_directory, os.O_RDONLY)
            try: os.fsync(actors_fd)
            finally: os.close(actors_fd)
            if path.exists():
                if path.read_bytes() != encoded:
                    raise ExecutionError("conflicting routed admission")
            else:
                descriptor, temporary_name = tempfile.mkstemp(prefix=".tmp-handle-", dir=self.directory)
                temporary = Path(temporary_name)
                try:
                    with os.fdopen(descriptor, "wb") as stream:
                        stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
                    os.replace(temporary, path)
                    directory_fd = os.open(self.directory, os.O_RDONLY)
                    try: os.fsync(directory_fd)
                    finally: os.close(directory_fd)
                finally:
                    if temporary.exists(): temporary.unlink()
        return self._read(path)

    async def list_subagents(self) -> list[ChildHandle]:
        result = []
        for path in sorted(self.directory.glob("routed-*.json")):
            try:
                handle = self._read(path)
            except ExecutionError:
                value = json.loads(path.read_text(encoding="utf-8"))
                if value.get("parent_id") != self.actor_id:
                    continue
                raise
            if handle.parent_id == self.actor_id:
                result.append(handle)
        return result

    async def send_parent(self, message: str) -> None:
        # M6 already persists the receipt.  The control actor deliberately
        # retains no copy of the message or scientific content.
        if not isinstance(message, str) or not message:
            raise ExecutionError("receipt envelope is invalid")

    async def delete_subagent(self, child_id: str) -> None:
        # Cancellation remains journaled by M6.  Durable handles are evidence
        # and therefore are not deleted by this adapter.
        if child_id not in {item.child_id for item in await self.list_subagents()}:
            raise ExecutionError("routed child is not owned by this actor")

    async def preflight(self) -> dict[str, Any]:
        return {"adapter": "routed_control", "actor_role": self.actor_role, "depth": self.depth, "persistent": True, "network": False}

    def for_child(self, child: ChildHandle, *, actor_role: str) -> "RoutedControlAdapter":
        if child.parent_id != self.actor_id or child.depth != self.depth + 1:
            raise ExecutionError("child does not belong to routed actor")
        return RoutedControlAdapter(
            self.root, self.run_id, actor_role=actor_role,
            actor_id=child.child_id, depth=child.depth,
        )


class DualExecutionAdapter:
    """Root M6 adapter choosing Prime or routed control per department."""

    actor_role = "M00"
    actor_id = "root"
    depth = 0

    def __init__(self, root: str | Path, run_id: str, policy: ExecutionPolicy, *, prime_adapter: Any | None = None):
        self.root = Path(root).resolve()
        self.run_id = run_id
        self.policy = policy
        self.prime_adapter = prime_adapter
        self.routed = RoutedControlAdapter(self.root, run_id, actor_role="M00", actor_id="root", depth=0)

    async def spawn(self, prompt: str, *, name: str) -> ChildHandle:
        department = RoutedControlAdapter._role(name)
        layer = self.policy.layer(department)
        if layer == "routed":
            return await self.routed.spawn(prompt, name=name)
        if self.prime_adapter is None:
            raise ExecutionError("Prime department requires an injected Prime session adapter")
        return await self.prime_adapter.spawn(prompt, name=name)

    async def list_subagents(self) -> list[ChildHandle]:
        values = await self.routed.list_subagents()
        if self.prime_adapter is not None:
            values.extend(await self.prime_adapter.list_subagents())
        return values

    async def delete_subagent(self, child_id: str) -> None:
        if child_id.startswith("routed-"):
            await self.routed.delete_subagent(child_id)
        elif self.prime_adapter is None:
            raise ExecutionError("Prime adapter is unavailable")
        else:
            await self.prime_adapter.delete_subagent(child_id)

    async def preflight(self) -> dict[str, Any]:
        return {
            "adapter": "dual", "execution_enabled": self.policy.enabled,
            "department_layers": dict(sorted(self.policy.departments.items())),
            "privacy_mode": self.policy.remote_content_mode,
            "prime_injected": self.prime_adapter is not None,
        }

    def department_adapter(self, child: Mapping[str, Any], *, prime_child_adapter: Any | None = None) -> Any:
        department = child.get("role_id")
        layer = self.policy.layer(str(department))
        if layer == "routed":
            handle = ChildHandle(**{key: child[key] for key in ChildHandle.__dataclass_fields__})
            return self.routed.for_child(handle, actor_role=str(department))
        if prime_child_adapter is None:
            raise ExecutionError("Prime child session adapter must be supplied by that session")
        return prime_child_adapter


class DualExecutionController:
    """Bridge routed Wxx output back into the unchanged M6 receipt flow."""

    def __init__(self, root: str | Path, policy: ExecutionPolicy, registry: ModelRegistry):
        self.root = Path(root).resolve()
        self.policy = policy
        self.registry = registry
        self.materializer = ContextMaterializer(self.root)

    async def execute_routed_department(
        self, orchestrator: Orchestrator, run_id: str, department: str,
        adapter: RoutedControlAdapter, runtime: InferenceRuntime, *,
        allow_test_doubles: bool = False, live: bool = False,
    ) -> dict[str, Any]:
        if type(allow_test_doubles) is not bool or type(live) is not bool:
            raise ExecutionError("execution flags must be strictly boolean")
        if self.policy.layer(department) != "routed":
            raise ExecutionError("department is not configured for routed execution")
        state = await orchestrator.advance_department(run_id, department, adapter=adapter)
        for role in (f"W{department[1]}1", f"W{department[1]}2", f"W{department[1]}3"):
            if state["activation"].get(role) == "FREEZE" or role in state["receipts"]:
                continue
            child = state["children"][role]
            workspace = Path(child["workspace"])
            try:
                task = json.loads((workspace / "task.json").read_text(encoding="utf-8"))
                view = json.loads((workspace / "view.json").read_text(encoding="utf-8"))
                compiled_prompt = (workspace / "prompt.txt").read_text(encoding="utf-8")
            except (OSError, json.JSONDecodeError) as error:
                raise ExecutionError("M6 task workspace is unreadable") from error
            route = self.registry.role_routes.get(role)
            if route is None:
                raise ExecutionError("routed worker has no model route")
            targets = [self.registry.target(target_id) for target_id in route["targets"] if self.registry.target(target_id).enabled]
            if not targets:
                raise ExecutionError("routed worker has no enabled target")
            context_limit = min(target.context_limit for target in targets)
            max_output = min(target.max_output_tokens for target in targets)
            context = self.materializer.materialize(
                task, view, privacy_mode=self.policy.remote_content_mode,
                context_limit=context_limit, max_output_tokens=max_output,
            )
            prompt = compiled_prompt + "\n\n# Materialized authorized context\n" + context.prompt_fragment()
            if task["requested_output_schema"] == "agent-proposal.schema.json":
                prompt += (
                    "\n\n# Routed model output contract\n"
                    "Emit only the scientific proposal payload. Do not emit protocol "
                    "metadata: schema_version, proposal_id, role_id, cycle_id, "
                    "base_hash, or prompt_version. LOOP derives those fields from "
                    "the validated AgentTask after payload validation.\n"
                )
            estimate_tokens = (len(prompt.encode("utf-8")) + 3) // 4
            if estimate_tokens + max_output > context_limit:
                raise ExecutionError("compiled prompt and context exceed target context limit")
            request = InferenceRequest.from_agent_task(
                self.root, task, prompt=prompt,
                required_capabilities=route["required_capabilities"],
                estimate_tokens=max(1, estimate_tokens),
                max_output_tokens=max_output, context_hash=context.context_hash,
                privacy_mode=self.policy.remote_content_mode,
            )
            decision = runtime.router.route(request, runtime.ledger.status(current_cycle=request.cycle_id))
            target = self.registry.target(str(decision.target_id))
            self.materializer.enforce_remote_policy(context, target_local=target.local)
            outcome = runtime.execute(
                request, live=live, allow_test_doubles=allow_test_doubles,
            )
            receipt = outcome["receipt"]
            if receipt is None or receipt.get("finish_reason") == "schema_invalid":
                raise ExecutionError("routed worker did not produce a valid scientific output")
            published = runtime.store.materialize_output(receipt["call_id"], workspace)
            state = await orchestrator.receipt(
                run_id, sender_role=role, parent_role=department,
                path=published["path"], sha256=published["sha256"],
                schema_version=M6_SCHEMA_VERSION,
            )
        return await orchestrator.consolidate_department(run_id, department, adapter=adapter)


def execution_readiness(root: str | Path) -> dict[str, Any]:
    config = load_budget_config(root)
    policy = ExecutionPolicy.from_mapping(config)
    registry = ModelRegistry(config["inference"])
    missing = []
    if not policy.departments: missing.append("department_execution_map")
    if not any(target.local for target in registry.targets.values()): missing.append("local_target")
    if not any(not target.local for target in registry.targets.values()): missing.append("remote_target")
    if not any(target.pricing is not None for target in registry.targets.values()): missing.append("target_pricing")
    if not registry.role_routes: missing.append("role_routes")
    missing.append("run_authorization")
    configured = not missing and policy.enabled and registry.enabled
    return {
        "schema_version": "1.0.0",
        "implementation_ready": True,
        "configuration_ready": configured,
        "live_ready": False,
        "execution_enabled": policy.enabled,
        "mode": policy.mode,
        "department_layers": dict(sorted(policy.departments.items())),
        "privacy_mode": policy.remote_content_mode,
        "max_run_cost_microunits": config["budget"].get("max_run_cost_microunits"),
        "currency": config["budget"].get("currency"),
        "missing_configuration": missing,
    }


__all__ = [
    "ContextItem", "ContextMaterializer", "DualExecutionAdapter",
    "DualExecutionController", "ExecutionError", "ExecutionPolicy",
    "MaterializedContext", "RoutedControlAdapter", "execution_readiness",
]
