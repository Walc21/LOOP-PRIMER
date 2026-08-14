"""M6 receipt orchestration, deliberately local and replayable.

This module does not run Prime.  A live caller injects an adapter representing
the current Prime session; tests inject ``FakeRLMAdapter``.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping
import jsonschema

from .activation import ActivationMode, ActivationPlan, ActivationEntry, PlanningLimits, CHILDREN, DEPARTMENTS, specialist_view, submanager_view
from .adapters import ChildHandle, PrimeRLMAdapter
from .prompts import PromptContractError, compile_prompt, expected_prompt_version, validate_output
from .store import DurableStore, StoreError, TransitionError
from .ingestion import _persisted_source_identity, _source_identity, _verify_artifacts, _verify_champion
from .state_machine import State

SCHEMA_VERSION = "1.1.0"
_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")
_PARENTS = {**{f"W{d}{n}": f"S{d}0" for d in range(1, 6) for n in range(1, 4)}, **{f"S{d}0": "M00" for d in range(1, 6)}}


class OrchestrationError(ValueError):
    pass


def _now() -> str: return datetime.now(timezone.utc).isoformat()
def _bytes(value: Any) -> bytes: return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
def _hash(value: bytes) -> str: return hashlib.sha256(value).hexdigest()
def _name(run: str, cycle: int, role: str) -> str: return f"article-loop-{run}-c{cycle:04d}-{role.lower()}"
def _dept(role: str) -> str: return f"S{role[1]}0" if role.startswith("W") else role


class Orchestrator:
    def __init__(self, root: str | Path, adapter: Any | None = None):
        self.root = Path(root).resolve()
        if self.root.is_symlink() or not self.root.is_dir():
            raise OrchestrationError("root must be a regular existing directory")
        self.adapter = adapter

    def _run(self, run_id: str) -> str:
        if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id) or run_id in {".", ".."}:
            raise OrchestrationError("run_id must be a simple identifier")
        return run_id

    def _managed(self, *parts: str, create: bool = False) -> Path:
        current = self.root
        for part in parts:
            if not part or Path(part).name != part:
                raise OrchestrationError("unsafe managed path component")
            current = current / part
            if current.is_symlink():
                raise OrchestrationError("symlink in managed orchestration path")
            if create: current.mkdir(exist_ok=True)
            if current.exists() and (not current.is_dir() or current.is_symlink()):
                raise OrchestrationError("managed path is not a regular directory")
            if self.root != current.resolve() and self.root not in current.resolve().parents:
                raise OrchestrationError("managed path escapes root")
        return current

    def _dir(self, run: str, *, create: bool = True) -> Path:
        return self._managed("state", "orchestration", self._run(run), create=create)

    def _file(self, run: str, name: str) -> Path:
        directory = self._dir(run)
        path = directory / name
        if path.is_symlink(): raise OrchestrationError("symlinked orchestration file")
        return path

    @contextmanager
    def _lock(self, run: str):
        lock = self._file(run, ".lock")
        with lock.open("a+", encoding="utf-8") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            try: yield
            finally: fcntl.flock(stream, fcntl.LOCK_UN)

    @staticmethod
    def _fsync_dir(directory: Path) -> None:
        fd = os.open(directory, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)

    def _atomic(self, path: Path, value: Any) -> None:
        data = _bytes(value) + b"\n"; fd, temp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data); f.flush(); os.fsync(f.fileno())
            os.replace(temp, path); self._fsync_dir(path.parent)
        finally:
            if os.path.exists(temp): os.unlink(temp)

    def _atomic_bytes(self, path: Path, data: bytes) -> None:
        fd, temp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data); f.flush(); os.fsync(f.fileno())
            os.replace(temp, path); self._fsync_dir(path.parent)
        finally:
            if os.path.exists(temp): os.unlink(temp)

    def _events(self, run: str) -> list[dict[str, Any]]:
        path = self._file(run, "journal.jsonl")
        if not path.exists(): return []
        result = []
        for line in path.read_bytes().splitlines(keepends=True):
            if not line.endswith(b"\n"): raise OrchestrationError("partial orchestration journal")
            try: item = json.loads(line)
            except json.JSONDecodeError as error: raise OrchestrationError("invalid orchestration journal") from error
            if not isinstance(item, dict) or set(item) != {"schema_version","sequence","previous_hash","event_hash","idempotency_key","event_type","payload","at"}:
                raise OrchestrationError("invalid orchestration journal event")
            previous = result[-1]["event_hash"] if result else None
            body = {k:v for k,v in item.items() if k != "event_hash"}
            if (item["schema_version"] != SCHEMA_VERSION or type(item["sequence"]) is not int or item["sequence"] != len(result)
                    or item["previous_hash"] != previous or not isinstance(item["idempotency_key"], str) or not item["idempotency_key"]
                    or not isinstance(item["event_type"], str) or not isinstance(item["payload"], dict)
                    or not _SHA.fullmatch(item["event_hash"]) or item["event_hash"] != _hash(_bytes(body))):
                raise OrchestrationError("invalid orchestration journal chain")
            if any(x["idempotency_key"] == item["idempotency_key"] for x in result): raise OrchestrationError("duplicate journal idempotency key")
            result.append(item)
        return result

    def _append(self, run: str, kind: str, key: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        events = self._events(run)
        for event in events:
            if event["idempotency_key"] == key:
                if event["event_type"] == kind and event["payload"] == dict(payload): return event
                raise OrchestrationError("journal idempotency conflict")
        body = {"schema_version": SCHEMA_VERSION, "sequence": len(events), "previous_hash": events[-1]["event_hash"] if events else None,
                "idempotency_key": key, "event_type": kind, "payload": dict(payload), "at": _now()}
        event = {**body, "event_hash": _hash(_bytes(body))}
        path = self._file(run, "journal.jsonl")
        with path.open("ab") as f: f.write(_bytes(event) + b"\n"); f.flush(); os.fsync(f.fileno())
        self._fsync_dir(path.parent); return event

    def _state(self, run: str) -> dict[str, Any]:
        events = self._events(run)
        state: dict[str, Any] = {"run_id": run, "cycle_id": 0, "state": "SOURCE_READY", "paused": False, "stopped": False, "finalized": False,
                                 "base_hash": None, "pdf_path": None, "activation": {}, "activation_hash": None,
                                 "children": {}, "receipts": {}, "children_by_cycle": {}, "receipts_by_cycle": {}, "events": len(events)}
        for e in events:
            p = e["payload"]; k = e["event_type"]
            if k == "BOOTSTRAPPED": state.update(p)
            elif k == "PLAN":
                cycle = str(p["cycle_id"])
                state.update({"cycle_id": p["cycle_id"], "activation": p["activation"], "activation_hash": p["activation_hash"], "state": "CYCLE_PLANNED",
                              "children": state["children_by_cycle"].setdefault(cycle, {}), "receipts": state["receipts_by_cycle"].setdefault(cycle, {})})
            elif k == "DEPARTMENTS_RUNNING": state["state"] = "DEPARTMENTS_RUNNING"
            elif k == "HANDLE":
                state["children_by_cycle"].setdefault(str(p["cycle_id"]), {})[p["role_id"]] = p
                if p["cycle_id"] == state["cycle_id"]: state["children"][p["role_id"]] = p
            elif k == "RECEIPT":
                state["receipts_by_cycle"].setdefault(str(p["cycle_id"]), {})[p["sender_role"]] = p
                if p["cycle_id"] == state["cycle_id"]:
                    state["receipts"][p["sender_role"]] = p; state["children"][p["sender_role"]]["status"] = "RECEIVED"
            elif k == "FAILED": state["children"][p["role_id"]]["status"] = "FAILED"
            elif k == "CANCELLED": state["children"][p["role_id"]]["status"] = "CANCELLED"
            elif k == "PAUSED": state["paused"] = True
            elif k == "RESUMED": state["paused"] = False
            elif k == "STOPPED": state["stopped"] = True
            elif k == "FINALIZED": state["finalized"] = True
        return state

    def _snapshot(self, run: str) -> dict[str, Any]:
        state = self._state(run); state["snapshot_hash"] = _hash(_bytes(state)); return state

    def _save_snapshot(self, run: str) -> dict[str, Any]:
        state = self._snapshot(run); self._atomic(self._file(run, "snapshot.json"), state); return state

    def _guard(self, state: Mapping[str, Any]) -> None:
        if state["paused"] or state["stopped"] or state["finalized"]: raise OrchestrationError("execution is not mutable")

    def _workspace(self, run: str, cycle: int, role: str) -> Path:
        return self._managed("workspaces", self._run(run), f"cycle-{cycle:04d}", role, create=True)

    def _regular(self, path: Path, base: Path) -> None:
        current = base
        try: parts = path.relative_to(base).parts
        except ValueError as error: raise OrchestrationError("path escapes canonical workspace") from error
        for part in parts:
            current = current / part
            if current.is_symlink(): raise OrchestrationError("symlinked receipt or workspace")
        if not path.is_file() or path.is_symlink(): raise OrchestrationError("receipt must be a regular file")

    async def bootstrap(self, pdf_path: str | Path) -> dict[str, Any]:
        source = Path(pdf_path)
        if source.is_symlink() or not source.is_file(): raise OrchestrationError("pdf must be a regular file")
        digest = _hash(source.read_bytes()); run = self._run("ingest-" + digest)
        store = DurableStore(self.root)
        if store.snapshot(run)["state"] != State.SOURCE_READY.value: raise OrchestrationError("M3 run is not SOURCE_READY")
        champion = self.root / "versions" / "champion" / "v0000"; manifest = champion / "manifest.json"; ingest = champion / "ingestion-manifest.json"
        for path in (champion, manifest, ingest, champion / "baseline.pdf", self.root / "artifacts" / "original" / digest):
            if path.is_symlink() or not path.exists(): raise OrchestrationError("M3 champion is unsafe or missing")
        try: cm, im = json.loads(manifest.read_text()), json.loads(ingest.read_text())
        except (OSError, json.JSONDecodeError) as error: raise OrchestrationError("M3 manifests are unreadable") from error
        if cm.get("run_id") != run or not _SHA.fullmatch(str(cm.get("content_hash", ""))) or im.get("input_sha256") != digest:
            raise OrchestrationError("PDF, M3 run, champion or manifest diverges")
        try:
            identity = _persisted_source_identity(store, run)
            if identity is None: raise OrchestrationError("M3 source identity is missing")
            # M3's verifier also rejects unsafe descendants and a changed frozen PDF.
            hashes = _verify_artifacts(self.root / "artifacts" / "original" / digest,
                                       self.root / "artifacts" / "extracted" / digest,
                                       self.root / "artifacts" / "rendered" / digest, digest)
            _verify_champion(champion, digest, hashes, identity)
        except Exception as error:
            if isinstance(error, OrchestrationError): raise
            raise OrchestrationError("PDF, M3 artifacts, champion or manifest diverges") from error
        with self._lock(run):
            if self._events(run): return self._snapshot(run)
            self._append(run, "BOOTSTRAPPED", f"{run}:bootstrap", {"run_id":run, "pdf_path":str(source.resolve()), "pdf_sha256":digest, "base_hash":cm["content_hash"]})
            return self._save_snapshot(run)

    async def preflight(self) -> Mapping[str, Any]:
        if self.adapter is None: return {"configured": False, "reason": "explicit PrimeRLMAdapter required for live execution"}
        return await self.adapter.preflight()

    def _plan(self, plan: ActivationPlan | Mapping[str, Any]) -> tuple[dict[str, str], dict[str, Any], bool]:
        if isinstance(plan, ActivationPlan): raw = plan.activation_map(); paused = plan.paused
        elif isinstance(plan, Mapping): raw = dict(plan); paused = bool(raw.get("paused"))
        else: raise OrchestrationError("ActivationPlan M5 is required")
        roles = raw.get("roles")
        if not isinstance(raw.get("cycle_id"), int) or not isinstance(roles, list): raise OrchestrationError("invalid ActivationPlan activation_map")
        mapping = {x.get("role_id"): x.get("mode") for x in roles if isinstance(x, Mapping)}
        if set(mapping) != {"M00", *DEPARTMENTS, *[w for x in CHILDREN.values() for w in x]} or any(v not in {x.value for x in ActivationMode} for v in mapping.values()):
            raise OrchestrationError("activation map is incomplete or invalid")
        return mapping, raw, paused

    def _load_plan(self, run: str, cycle_id: int | None) -> Mapping[str, Any]:
        """Read the immutable M5 map; public calls never invent a plan."""
        directory = self._managed("state", "blackboard", self._run(run), create=False)
        candidates = [directory / "activation_map.json"]
        if cycle_id is not None:
            candidates.insert(0, directory / f"activation-c{cycle_id:04d}.json")
        for path in candidates:
            if path.exists():
                if path.is_symlink(): raise OrchestrationError("symlinked M5 activation map")
                try: return json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as error: raise OrchestrationError("invalid persisted M5 activation map") from error
        raise OrchestrationError("a persisted M5 ActivationPlan is required")

    async def run_cycle(self, *, cycle_id: int | None = None, dry_run: bool = False, run_id: str | None = None, plan: ActivationPlan | Mapping[str, Any] | None = None) -> dict[str, Any]:
        run = self._run(run_id or self._only_run()); state = self._state(run); self._guard(state)
        if not dry_run and not isinstance(self.adapter, PrimeRLMAdapter) and self.adapter is None:
            raise OrchestrationError("live execution requires an explicit PrimeRLMAdapter")
        if self.adapter is not None and getattr(self.adapter, "actor_role", "M00") != "M00": raise OrchestrationError("only M00 may plan a root cycle")
        if plan is None: plan = self._load_plan(run, cycle_id)
        mapping, raw, paused = self._plan(plan); cycle = raw["cycle_id"] if cycle_id is None else cycle_id
        if cycle != raw["cycle_id"]: raise OrchestrationError("cycle differs from ActivationPlan")
        digest = _hash(_bytes(raw))
        with self._lock(run):
            state = self._state(run); self._guard(state)
            if state["activation_hash"] and (state["cycle_id"] == cycle and state["activation_hash"] != digest): raise OrchestrationError("cannot replace a persisted activation map")
            preview = self._file(run, f"preview-c{cycle:04d}.json")
            if dry_run:
                self._atomic(preview, {"dry_run":True,"activation_hash":digest,"activation_map":raw}); return self._snapshot(run)
            if not state["activation_hash"]:
                self._atomic(self._file(run, f"activation-c{cycle:04d}.json"), raw)
                self._append(run,"PLAN",f"{run}:c{cycle}:plan",{"cycle_id":cycle,"activation":mapping,"activation_hash":digest})
            if paused:
                self._append(run,"PAUSED",f"{run}:c{cycle}:plan-paused",{"reason":"activation_plan_paused"}); return self._save_snapshot(run)
        store = DurableStore(self.root)
        try:
            if store.snapshot(run)["state"] == State.SOURCE_READY.value:
                store.record(run, State.CYCLE_PLANNED, event_id=f"{run}:m6:c{cycle}:planned", idempotency_key=f"{run}:m6:c{cycle}:planned", actor_id="m6", event_type="M6_CYCLE_PLANNED", payload={"activation_hash":digest})
        except (StoreError, TransitionError) as error:
            raise OrchestrationError("canonical M3/M6 transition rejected") from error
        # Each admission persists independently under the run lock.
        for role in DEPARTMENTS:
            if mapping[role] != "FREEZE": await self._admit(run, cycle, role, self.adapter)
        with self._lock(run):
            self._append(run,"DEPARTMENTS_RUNNING",f"{run}:c{cycle}:departments",{})
            result = self._save_snapshot(run)
        try:
            if store.snapshot(run)["state"] == State.CYCLE_PLANNED.value:
                store.record(run, State.DEPARTMENTS_RUNNING, event_id=f"{run}:m6:c{cycle}:departments", idempotency_key=f"{run}:m6:c{cycle}:departments", actor_id="m6", event_type="M6_DEPARTMENTS_RUNNING", payload={"activation_hash":digest})
        except (StoreError, TransitionError) as error:
            raise OrchestrationError("canonical department transition rejected") from error
        return result

    async def _admit(self, run: str, cycle: int, role: str, adapter: Any) -> dict[str, Any]:
        if adapter is None: raise OrchestrationError("adapter required")
        parent = _PARENTS.get(role)
        if parent != getattr(adapter, "actor_role", None): raise OrchestrationError("actor cannot admit this role")
        expected_depth = 1 if role.startswith("S") else 2
        if getattr(adapter, "depth", None) != expected_depth - 1: raise OrchestrationError("invalid actor depth")
        with self._lock(run):
            state = self._state(run); self._guard(state)
            if state["activation"].get(role) == "FREEZE": raise OrchestrationError("FREEZE may not be admitted")
            old = state["children"].get(role)
            if old and old["cycle_id"] == cycle: return old
            workspace = self._workspace(run, cycle, role)
            task = self._task(state, role, workspace)
            try:
                task_schema = json.loads((self.root / "config" / "schemas" / "agent-task.schema.json").read_text(encoding="utf-8"))
                jsonschema.Draft202012Validator(task_schema).validate(task)
            except (OSError, json.JSONDecodeError, jsonschema.ValidationError) as error:
                raise OrchestrationError("AgentTask is invalid") from error
            task_bytes = _bytes(task) + b"\n"; task_hash = _hash(task_bytes)
            compiled = compile_prompt(self.root, task, self._context(task))
            view = submanager_view(task, []) if role.startswith("S") else specialist_view(task, excerpts=[], dependent_claims=[], rubric={"role":role}, local_history=[])
            for name, value in (("task.json",task),("view.json",view)):
                target=workspace/name
                if target.exists() and target.read_bytes() != (_bytes(value)+b"\n"): raise OrchestrationError("refusing to overwrite workspace artifact")
                if not target.exists(): self._atomic(target,value)
            prompt_target=workspace/"prompt.txt"
            prompt_bytes=compiled.text.encode()
            if prompt_target.exists() and prompt_target.read_bytes() != prompt_bytes: raise OrchestrationError("refusing to overwrite workspace artifact")
            if not prompt_target.exists(): self._atomic_bytes(prompt_target,prompt_bytes)
            artifact = {"task_hash":task_hash,"view_hash":_hash(_bytes(view)+b"\n"),"prompt_hash":_hash(prompt_bytes),"prompt_version":task["prompt_version"],"workspace":str(workspace)}
            self._append(run,"ADMISSION_PREPARED",f"{run}:c{cycle}:{role}:prepared",{"role_id":role,"cycle_id":cycle,**artifact})
        # A process may die after rlm() admits the child but before HANDLE is
        # journaled. The deterministic name reconciles that narrow window.
        name = _name(run, cycle, role)
        existing = next((item for item in await adapter.list_subagents() if item.name == name), None)
        handle = existing or await adapter.spawn(compiled.text + "\nWorkspace permitido: " + str(workspace) + "\nEnvie ao pai apenas receipt {path,sha256,schema_version}.", name=name)
        with self._lock(run):
            state=self._state(run); old=state["children"].get(role)
            if old and old["cycle_id"] == cycle: return old
            record={"role_id":role,"cycle_id":cycle,"child_id":handle.child_id,"name":handle.name,"session_dir":handle.session_dir,"parent_id":handle.parent_id,"actor_role":handle.actor_role,"depth":handle.depth,"status":"ADMITTED",**artifact}
            self._append(run,"HANDLE",f"{run}:c{cycle}:{role}:handle",record); return self._save_snapshot(run)["children"][role]

    def _context(self, task: Mapping[str, Any]) -> dict[str, Any]: return {k:task[k] for k in ("run_id","cycle_id","base_hash","activation_mode","scope","input_locators")}
    def _task(self, state: Mapping[str, Any], role: str, workspace: Path) -> dict[str, Any]:
        schema="department-packet.schema.json" if role.startswith("S") else "agent-proposal.schema.json"
        scope=[f"role:{role}"]; inputs=[f"workspace:{workspace}"]
        return {"schema_version":SCHEMA_VERSION,"task_id":f"{state['run_id']}-{role}-c{state['cycle_id']:04d}","run_id":state["run_id"],"cycle_id":state["cycle_id"],"role_id":role,"activation_mode":state["activation"][role],"created_at":_now(),"base_hash":state["base_hash"],"scope":scope,"input_locators":inputs,"requested_output_schema":schema,"prompt_version":expected_prompt_version(self.root,role,schema),"constraints":["workspace_isolated","receipt_only","no_champion_write"]}

    async def advance_department(self, run_id: str, department: str, *, adapter: Any | None = None, dry_run: bool = False) -> dict[str, Any]:
        run=self._run(run_id); adapter=adapter or self.adapter
        if department not in DEPARTMENTS or adapter is None or getattr(adapter,"actor_role",None)!=department: raise OrchestrationError("department actor context is required")
        state=self._state(run); self._guard(state); handle=state["children"].get(department)
        if not handle or handle["child_id"] != getattr(adapter,"actor_id",None) or handle["depth"] != 1: raise OrchestrationError("submanager session does not match admitted handle")
        if dry_run: return state
        for role in CHILDREN[department]:
            if state["activation"].get(role) != "FREEZE": await self._admit(run,state["cycle_id"],role,adapter)
        return self._save_snapshot(run)

    async def receipt(self, run_id: str, *, sender_role: str, parent_role: str, path: str | Path, sha256: str, schema_version: str=SCHEMA_VERSION) -> dict[str, Any]:
        run=self._run(run_id)
        if _PARENTS.get(sender_role) != parent_role or not _SHA.fullmatch(sha256) or schema_version != SCHEMA_VERSION: raise OrchestrationError("invalid receipt parentage or envelope")
        with self._lock(run):
            state=self._state(run); self._guard(state); child=state["children"].get(sender_role)
            if not child or child["cycle_id"] != state["cycle_id"] or child["status"] in {"FAILED","CANCELLED"}: raise OrchestrationError("sender is not receipt-compatible")
            workspace=self._workspace(run,state["cycle_id"],sender_role); target=Path(path)
            self._regular(target,workspace)
            if target.parent != workspace or _hash(target.read_bytes()) != sha256: raise OrchestrationError("receipt location or hash differs")
            schema="department-packet.schema.json" if sender_role.startswith("S") else "agent-proposal.schema.json"
            try: document=json.loads(target.read_text()); validate_output(self.root,schema,document)
            except (json.JSONDecodeError,PromptContractError) as error: raise OrchestrationError("receipt schema invalid") from error
            if sender_role.startswith("W"):
                good=document.get("role_id")==sender_role and document.get("cycle_id")==state["cycle_id"] and document.get("base_hash")==state["base_hash"]
            else: good=document.get("department_id")==sender_role and document.get("run_id")==run and document.get("cycle_id")==state["cycle_id"] and document.get("base_hash")==state["base_hash"]
            if not good: raise OrchestrationError("receipt identity differs")
            old=state["receipts"].get(sender_role)
            if old:
                if old["sha256"] == sha256 and old["path"] == str(target): return state
                raise OrchestrationError("conflicting second receipt")
            payload={"sender_role":sender_role,"parent_role":parent_role,"path":str(target),"sha256":sha256,"schema_version":schema_version,"cycle_id":state["cycle_id"]}
            self._append(run,"RECEIPT",f"{run}:c{state['cycle_id']}:{sender_role}:receipt",payload); return self._save_snapshot(run)

    async def mark_failed(self, run_id: str, sender_role: str, reason: str) -> dict[str, Any]:
        run=self._run(run_id)
        with self._lock(run):
            state=self._state(run); self._guard(state); child=state["children"].get(sender_role)
            if not child or child["status"] == "RECEIVED": raise OrchestrationError("illegal failure transition")
            self._append(run,"FAILED",f"{run}:c{state['cycle_id']}:{sender_role}:failed",{"role_id":sender_role,"reason":reason}); return self._save_snapshot(run)

    async def cancel(self, run_id: str, role: str) -> dict[str, Any]:
        run=self._run(run_id)
        with self._lock(run):
            state=self._state(run); self._guard(state); child=state["children"].get(role)
            if not child: raise OrchestrationError("unknown child")
            self._append(run,"CANCELLED",f"{run}:c{state['cycle_id']}:{role}:cancelled",{"role_id":role})
            result=self._save_snapshot(run)
        if self.adapter is not None: await self.adapter.delete_subagent(child["child_id"])
        return result

    async def consolidate_department(self, run_id: str, department: str, *, adapter: Any | None=None) -> dict[str, Any]:
        run=self._run(run_id); adapter=adapter or self.adapter
        if getattr(adapter,"actor_role",None)!=department: raise OrchestrationError("only the owning submanager consolidates")
        state=self._state(run); self._guard(state); workers=[r for r in CHILDREN[department] if state["activation"].get(r)!="FREEZE"]
        if any(r not in state["receipts"] for r in workers): raise OrchestrationError("department has pending receipts")
        proposals=[json.loads(Path(state["receipts"][r]["path"]).read_text()) for r in workers]
        packet={"schema_version":SCHEMA_VERSION,"packet_id":f"{run}-{department}-c{state['cycle_id']:04d}","run_id":run,"cycle_id":state["cycle_id"],"department_id":department,"base_hash":state["base_hash"],"proposal_ids":[x["proposal_id"] for x in proposals],"specialist_task_ids":[state["children"][r]["task_hash"] for r in workers],"dependency_reviews":[],"status":"complete","no_change_justification":None,"evidence_locators":[state["receipts"][r]["path"] for r in workers],"created_at":_now()}
        target=self._workspace(run,state["cycle_id"],department)/"department-packet.json"; self._atomic(target,packet)
        result=await self.receipt(run,sender_role=department,parent_role="M00",path=target,sha256=_hash(target.read_bytes()))
        await adapter.send_parent(_bytes({"path":str(target),"sha256":_hash(target.read_bytes()),"schema_version":SCHEMA_VERSION}).decode())
        return result

    async def pause(self, run_id: str) -> dict[str, Any]: return await self._flag(run_id,"PAUSED",{})
    async def resume(self, run_id: str) -> dict[str, Any]:
        run=self._run(run_id)
        with self._lock(run):
            state=self._state(run)
            if state["stopped"] or state["finalized"] or not state["paused"]: raise OrchestrationError("execution cannot resume")
            self._append(run,"RESUMED",f"{run}:resume:{len(self._events(run))}",{}); return self._save_snapshot(run)
    async def stop(self, run_id: str) -> dict[str, Any]: return await self._flag(run_id,"STOPPED",{})
    async def finalize(self, run_id: str) -> dict[str, Any]: return await self._flag(run_id,"FINALIZED",{})
    async def _flag(self, run_id: str, event: str, payload: Mapping[str,Any]) -> dict[str, Any]:
        run=self._run(run_id)
        with self._lock(run):
            state=self._state(run)
            if state["stopped"] or state["finalized"]: raise OrchestrationError("execution is terminal")
            self._append(run,event,f"{run}:{event.lower()}",payload); return self._save_snapshot(run)
    async def checkpoint(self, run_id: str) -> dict[str, Any]:
        run=self._run(run_id)
        with self._lock(run):
            state=self._save_snapshot(run); self._atomic(self._file(run,f"checkpoint-{len(self._events(run)):06d}.json"),state); return state
    async def status(self, run_id: str | None=None) -> dict[str, Any]: return self._snapshot(self._run(run_id or self._only_run()))
    def _only_run(self) -> str:
        directory=self._managed("state","orchestration",create=True); runs=[x.name for x in directory.iterdir() if x.is_dir() and not x.is_symlink()]
        if len(runs)!=1: raise OrchestrationError("exactly one bootstrapped M6 run is required")
        return self._run(runs[0])
