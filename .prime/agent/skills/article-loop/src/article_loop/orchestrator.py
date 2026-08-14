"""Durable, receipt-driven M6 orchestration (offline until an adapter is used)."""
from __future__ import annotations

import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .activation import ActivationMode, ActivationPlanner, CHILDREN, DEPARTMENTS
from .adapters import FakeRLMAdapter
from .blackboard import Impact
from .prompts import PromptContractError, validate_output

SCHEMA_VERSION = "1.1.0"

def _now() -> str: return datetime.now(timezone.utc).isoformat()
def _hash(value: bytes) -> str: return hashlib.sha256(value).hexdigest()
def _root(root: str | Path) -> Path: return Path(root).resolve()
def _path(root: str | Path, run_id: str) -> Path:
    target = _root(root) / "state" / "orchestration" / f"{run_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True); return target
def _read(root: str | Path, run_id: str) -> dict[str, Any]:
    target = _path(root, run_id)
    if not target.exists(): raise ValueError(f"unknown run: {run_id}")
    return json.loads(target.read_text(encoding="utf-8"))
def _write(root: str | Path, state: Mapping[str, Any]) -> None:
    target = _path(root, state["run_id"]); temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(state, sort_keys=True, indent=2) + "\n", encoding="utf-8"); temp.replace(target)
def _name(run_id: str, cycle: int, role: str) -> str: return f"article-loop-{run_id}-c{cycle:04d}-{role.lower()}"
def _department(role: str) -> str:
    return "S" + role[1] + "0" if role.startswith("W") else role

def _validate_document(root: Path, target: Path, sender_role: str) -> dict[str, Any]:
    """Validate a child artifact before its parent may consume it."""
    document = json.loads(target.read_text(encoding="utf-8"))
    schema = "department-packet.schema.json" if sender_role.startswith("S") else "agent-proposal.schema.json"
    try:
        validate_output(root, schema, document)
    except PromptContractError as error:
        raise ValueError(f"receipt artifact fails {schema}: {error}") from error
    identity_field = "department_id" if sender_role.startswith("S") else "role_id"
    if document[identity_field] != sender_role:
        raise ValueError("receipt artifact identity does not match its sender")
    return document

class Orchestrator:
    def __init__(self, root: str | Path, adapter: Any | None = None): self.root, self.adapter = _root(root), adapter or FakeRLMAdapter()
    async def bootstrap(self, pdf_path: str | Path) -> dict[str, Any]:
        source = Path(pdf_path)
        if not source.is_file(): raise ValueError("pdf_path must name an existing regular file")
        digest = _hash(source.read_bytes()); run_id = f"run-{digest[:16]}"
        target = _path(self.root, run_id)
        if target.exists(): return _read(self.root, run_id)
        state = {"schema_version": SCHEMA_VERSION, "run_id": run_id, "pdf_path": str(source.resolve()), "pdf_sha256": digest, "cycle_id": 0, "paused": False, "stopped": False, "finalized": False, "activation": {}, "children": {}, "receipts": {}, "events": [{"type":"BOOTSTRAPPED","at":_now()}]}
        _write(self.root, state); return state
    async def preflight(self) -> Mapping[str, Any]: return await self.adapter.preflight()
    async def run_cycle(self, *, cycle_id: int | None = None, dry_run: bool = False, run_id: str | None = None) -> dict[str, Any]:
        if run_id is None: run_id = self._only_run()
        state = _read(self.root, run_id); cycle = state["cycle_id"] if cycle_id is None else cycle_id
        if state["paused"] or state["stopped"] or state["finalized"]: return state
        plan = ActivationPlanner().plan(cycle_id=cycle, impact=Impact((),(),(),(),()))
        state["cycle_id"] = cycle
        state["activation"] = {entry.role_id: entry.mode.value for entry in plan.entries}
        state["events"].append({"type":"CYCLE_PLANNED","cycle_id":cycle,"at":_now()})
        for entry in plan.entries:
            if entry.role_id == "M00" or entry.mode is ActivationMode.FREEZE: continue
            # Root admits only active departments.  Specialists are admitted by
            # the submanager turn via `advance_department`.
            if entry.role_id.startswith("W"): continue
            await self._admit(state, entry.role_id, cycle, dry_run)
        _write(self.root, state); return state
    async def advance_department(self, run_id: str, department: str, *, dry_run: bool = False) -> dict[str, Any]:
        if department not in DEPARTMENTS: raise ValueError("unknown department")
        state = _read(self.root, run_id)
        if department not in state["children"]: raise ValueError("department was not admitted")
        for role in CHILDREN[department]:
            if state["activation"].get(role) != ActivationMode.FREEZE.value:
                await self._admit(state, role, state["cycle_id"], dry_run)
        _write(self.root, state); return state
    async def receipt(self, run_id: str, *, sender_role: str, parent_role: str, path: str | Path, sha256: str, schema_version: str = SCHEMA_VERSION) -> dict[str, Any]:
        state = _read(self.root, run_id)
        if parent_role == "M00" and sender_role.startswith("W"): raise ValueError("grandchild cannot message root")
        if sender_role not in state["children"]: raise ValueError("unknown sender")
        target = Path(path).resolve()
        if self.root not in target.parents or not target.is_file(): raise ValueError("receipt path escapes workspace")
        if schema_version != SCHEMA_VERSION or _hash(target.read_bytes()) != sha256: raise ValueError("receipt hash or schema_version is invalid")
        _validate_document(self.root, target, sender_role)
        key = f"{sender_role}:{sha256}"
        if key not in state["receipts"]:
            state["receipts"][key] = {"sender_role":sender_role,"parent_role":parent_role,"path":str(target),"sha256":sha256,"schema_version":schema_version}
            state["children"][sender_role]["status"] = "RECEIVED"
            state["events"].append({"type":"RECEIPT_ACCEPTED","sender_role":sender_role,"at":_now()})
            _write(self.root, state)
        return state
    async def consolidate_department(self, run_id: str, department: str) -> dict[str, Any]:
        """Create the only payload a submanager may send to the root manager."""
        state = _read(self.root, run_id)
        if department not in DEPARTMENTS or department not in state["children"]:
            raise ValueError("department was not admitted")
        workers = [role for role in CHILDREN[department] if role in state["children"]]
        received = {item["sender_role"]: item for item in state["receipts"].values()}
        missing = [role for role in workers if role not in received]
        if missing:
            raise ValueError(f"department has pending child receipts: {', '.join(missing)}")
        proposals = [_validate_document(self.root, Path(received[role]["path"]), role) for role in workers]
        dependency_reviews: list[dict[str, Any]] = []
        packet_status = "complete"
        if department in {"S30", "S40"}:
            technical_ids = {proposal["proposal_id"] for proposal in proposals if proposal["risk"]["technical_effect_possible"]}
            review_receipt = received.get("S20")
            if technical_ids:
                reviews = [] if review_receipt is None else _validate_document(self.root, Path(review_receipt["path"]), "S20").get("dependency_reviews", [])
                dependency_reviews = [review for review in reviews if review["proposal_id"] in technical_ids and review["status"] == "approved"]
                if technical_ids != {review["proposal_id"] for review in dependency_reviews}:
                    packet_status = "blocked"
        packet = {
            "schema_version": SCHEMA_VERSION,
            "packet_id": f"{run_id}-{department}-c{state['cycle_id']:04d}",
            "run_id": run_id,
            "cycle_id": state["cycle_id"],
            "department_id": department,
            "base_hash": state["pdf_sha256"],
            "proposal_ids": [proposal["proposal_id"] for proposal in proposals],
            "specialist_task_ids": [state["children"][role]["task_hash"] for role in workers],
            "dependency_reviews": dependency_reviews,
            "status": packet_status,
            "no_change_justification": None,
            "evidence_locators": [f"workspace:{received[role]['path']}" for role in workers],
            "created_at": _now(),
        }
        workspace = self._workspace(state, department)
        target = workspace / "department-packet.json"
        payload = json.dumps(packet, sort_keys=True, indent=2).encode() + b"\n"
        target.write_bytes(payload)
        digest = _hash(payload)
        await self.receipt(run_id, sender_role=department, parent_role="M00", path=target, sha256=digest)
        await self.adapter.send_parent(json.dumps({"path": str(target), "sha256": digest, "schema_version": SCHEMA_VERSION}))
        return _read(self.root, run_id)
    async def mark_failed(self, run_id: str, sender_role: str, reason: str) -> dict[str, Any]:
        state = _read(self.root, run_id)
        if sender_role not in state["children"]: raise ValueError("unknown sender")
        state["children"][sender_role]["status"] = "FAILED"
        state["events"].append({"type":"CHILD_FAILED","role":sender_role,"reason":reason,"at":_now()})
        _write(self.root, state); return state
    async def pause(self, run_id: str) -> dict[str, Any]: return await self._flag(run_id, "paused", True, "PAUSED")
    async def resume(self, run_id: str) -> dict[str, Any]: return await self._flag(run_id, "paused", False, "RESUMED")
    async def stop(self, run_id: str) -> dict[str, Any]:
        state = await self._flag(run_id, "stopped", True, "STOPPED")
        # Persist a cancellation record before removing a child session: this is
        # the durable receipt for intentionally silent/cancelled children.
        for role, item in state["children"].items():
            if item["status"] not in {"RECEIVED", "FAILED"}:
                item["status"] = "CANCELLED"
                state["events"].append({"type":"CHILD_CANCELLED","role":role,"at":_now()})
        _write(self.root, state)
        for item in state["children"].values():
            await self.adapter.delete(type("H", (), {"child_id":item["child_id"]})())
        return _read(self.root, run_id)
    async def finalize(self, run_id: str) -> dict[str, Any]: return await self._flag(run_id, "finalized", True, "FINALIZED")
    async def checkpoint(self, run_id: str) -> dict[str, Any]: return _read(self.root, run_id)
    async def status(self, run_id: str | None = None) -> dict[str, Any]: return _read(self.root, run_id or self._only_run())
    def _only_run(self) -> str:
        files = list((_root(self.root)/"state"/"orchestration").glob("*.json")) if (_root(self.root)/"state"/"orchestration").exists() else []
        if len(files) != 1: raise ValueError("run_id is required unless exactly one run exists")
        return files[0].stem
    async def _admit(self, state: dict[str, Any], role: str, cycle: int, dry_run: bool) -> None:
        if role in state["children"]: return
        name = _name(state["run_id"], cycle, role)
        if dry_run: handle = {"child_id":"dry-run-"+role,"name":name,"session_dir":"","model":None}
        else:
            admitted = await self.adapter.spawn(f"role={role}; run={state['run_id']}; cycle={cycle}", name=name)
            handle = {"child_id":admitted.child_id,"name":admitted.name,"session_dir":admitted.session_dir,"model":admitted.model}
        handle["task_hash"] = _hash(f"{state['run_id']}:{cycle}:{role}".encode())
        handle["workspace"] = str(self._workspace(state, role))
        handle["status"] = "ADMITTED"; state["children"][role] = handle
        state["events"].append({
            "type":"CHILD_ADMITTED", "role":role, "child_id":handle["child_id"],
            "session_dir":handle["session_dir"], "task_hash":handle["task_hash"],
            "status":handle["status"], "at":_now(),
        })
    def _workspace(self, state: Mapping[str, Any], role: str) -> Path:
        target = self.root / "workspaces" / state["run_id"] / f"c{state['cycle_id']:04d}" / role.lower()
        target.mkdir(parents=True, exist_ok=True)
        return target
    async def _flag(self, run_id: str, flag: str, value: bool, event: str) -> dict[str, Any]:
        state = _read(self.root, run_id); state[flag] = value; state["events"].append({"type":event,"at":_now()}); _write(self.root,state); return state
