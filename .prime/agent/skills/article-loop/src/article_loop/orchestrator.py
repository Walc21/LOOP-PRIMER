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
            self._validate_event(item["event_type"], item["payload"])
            if any(x["idempotency_key"] == item["idempotency_key"] for x in result): raise OrchestrationError("duplicate journal idempotency key")
            result.append(item)
        return result

    @staticmethod
    def _validate_event(kind: str, payload: Mapping[str, Any]) -> None:
        """Keep replay closed: every event has one small, typed envelope."""
        required: dict[str, set[str]] = {
            "BOOTSTRAPPED": {"run_id", "pdf_path", "pdf_sha256", "base_hash"},
            "PLAN": {"cycle_id", "activation", "activation_hash", "raw"},
            "DEPARTMENTS_RUNNING": set(),
            "ADMISSION_PREPARED": {"role_id", "cycle_id", "task_hash", "view_hash", "prompt_hash", "prompt_version", "workspace"},
            "SPAWN_INTENT": {"role_id", "cycle_id", "name", "parent_id"},
            "HANDLE": {"role_id", "cycle_id", "child_id", "name", "session_dir", "model", "parent_id", "actor_role", "depth", "status", "task_hash", "view_hash", "prompt_hash", "prompt_version", "workspace"},
            "RECEIPT": {"sender_role", "parent_role", "path", "immutable_path", "sha256", "schema_version", "cycle_id"},
            "FAILED": {"role_id", "reason"}, "CANCELLED": {"role_id"},
            "PAUSED": {"pause_id", "resume_state"}, "RESUMED": {"pause_id"},
            "STOPPED": set(), "FINALIZED": set(),
        }
        if kind not in required or not isinstance(payload, Mapping):
            raise OrchestrationError("unknown or malformed orchestration event")
        keys = set(payload)
        if kind == "CANCELLED":
            if not keys.issubset({"role_id", "pending_owner"}) or "role_id" not in keys:
                raise OrchestrationError("invalid CANCELLED payload")
        elif keys != required[kind]:
            raise OrchestrationError("invalid orchestration event payload")
        if kind in {"PLAN", "ADMISSION_PREPARED", "SPAWN_INTENT", "HANDLE", "RECEIPT"} and type(payload.get("cycle_id")) is not int:
            raise OrchestrationError("event cycle_id is invalid")
        if kind == "PLAN" and (not isinstance(payload["activation"], Mapping) or not isinstance(payload["raw"], Mapping) or not _SHA.fullmatch(str(payload["activation_hash"]))):
            raise OrchestrationError("invalid PLAN payload")
        if kind == "HANDLE" and (payload["status"] != "ADMITTED" or type(payload["depth"]) is not int or not all(isinstance(payload[x], str) and payload[x] for x in ("role_id", "child_id", "name", "session_dir", "parent_id", "actor_role"))):
            raise OrchestrationError("invalid HANDLE payload")
        if kind == "RECEIPT" and (not _SHA.fullmatch(str(payload["sha256"])) or payload["schema_version"] != SCHEMA_VERSION):
            raise OrchestrationError("invalid RECEIPT payload")
        if kind in {"PAUSED", "RESUMED"} and not isinstance(payload["pause_id"], str):
            raise OrchestrationError("invalid pause event")

    def _append(self, run: str, kind: str, key: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        self._validate_event(kind, payload)
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
                                 "plans_by_cycle": {}, "activation_by_cycle": {}, "activation_hash_by_cycle": {},
                                 "children": {}, "receipts": {}, "children_by_cycle": {}, "receipts_by_cycle": {}, "events": len(events)}
        for e in events:
            p = e["payload"]; k = e["event_type"]
            if k == "BOOTSTRAPPED": state.update(p)
            elif k == "PLAN":
                cycle = str(p["cycle_id"])
                state["plans_by_cycle"][cycle] = p["raw"]
                state["activation_by_cycle"][cycle] = p["activation"]
                state["activation_hash_by_cycle"][cycle] = p["activation_hash"]
                state.update({"cycle_id": p["cycle_id"], "activation": p["activation"], "activation_hash": p["activation_hash"], "state": "CYCLE_PLANNED",
                              "children": state["children_by_cycle"].setdefault(cycle, {}), "receipts": state["receipts_by_cycle"].setdefault(cycle, {})})
            elif k == "DEPARTMENTS_RUNNING": state["state"] = "DEPARTMENTS_RUNNING"
            elif k == "HANDLE":
                state["children_by_cycle"].setdefault(str(p["cycle_id"]), {})[p["role_id"]] = p
                if p["cycle_id"] == state["cycle_id"]: state["children"][p["role_id"]] = p
            elif k == "RECEIPT":
                state["receipts_by_cycle"].setdefault(str(p["cycle_id"]), {})[p["sender_role"]] = p
                if p["cycle_id"] == state["cycle_id"]:
                    state["receipts"][p["sender_role"]] = p
                    if p["sender_role"] in state["children"]: state["children"][p["sender_role"]]["status"] = "RECEIVED"
            elif k == "FAILED" and p["role_id"] in state["children"]: state["children"][p["role_id"]]["status"] = "FAILED"
            elif k == "CANCELLED" and p["role_id"] in state["children"]: state["children"][p["role_id"]]["status"] = "CANCELLED"
            elif k == "PAUSED": state.update({"paused": True, "pause_id": p["pause_id"], "resume_state": p["resume_state"]})
            elif k == "RESUMED": state.update({"paused": False, "resume_state": None})
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
        roles = raw.get("roles"); expected = {"cycle_id","paused","checkpoint","budget","roles"}
        if (set(raw) != expected or type(raw.get("cycle_id")) is not int or raw["cycle_id"] < 0
                or type(raw.get("paused")) is not bool or not isinstance(roles, list) or not isinstance(raw.get("budget"), Mapping)):
            raise OrchestrationError("invalid ActivationPlan activation_map")
        budget=raw["budget"]; limits=budget.get("limits")
        if set(budget) != {"limits","estimated_tokens","wall_time_seconds"} or not isinstance(limits, Mapping) or set(limits) != set(PlanningLimits.__dataclass_fields__) or any(type(v) is not int for v in limits.values()): raise OrchestrationError("invalid ActivationPlan budget")
        checkpoint = raw["checkpoint"]
        if raw["paused"] != (checkpoint is not None):
            raise OrchestrationError("paused plan requires exactly one checkpoint")
        required={"role_id","mode","justification","estimated_tokens","wall_time_seconds","inputs","expected_outputs"}
        if any(not isinstance(x, Mapping) or set(x)!=required for x in roles): raise OrchestrationError("invalid ActivationPlan role entry")
        if any(not isinstance(x["role_id"], str) or not isinstance(x["mode"], str)
               or not isinstance(x["justification"], str) for x in roles):
            raise OrchestrationError("activation role fields are invalid")
        role_order = ("M00", *tuple(role for department in DEPARTMENTS for role in (department, *CHILDREN[department])))
        all_roles=set(role_order)
        mapping = {x["role_id"]: x["mode"] for x in roles}
        if (len(roles) != len(role_order) or tuple(x["role_id"] for x in roles) != role_order
                or len(mapping) != len(role_order) or set(mapping) != all_roles
                or any(v not in {x.value for x in ActivationMode} for v in mapping.values())
                or mapping["M00"] != "RUN"):
            raise OrchestrationError("activation map is incomplete or invalid")
        active=[]
        for entry in roles:
            if (not isinstance(entry["role_id"], str) or not entry["role_id"]
                    or not isinstance(entry["mode"], str) or not entry["mode"]
                    or not isinstance(entry["justification"], str) or not entry["justification"]):
                raise OrchestrationError("activation role fields are invalid")
            if type(entry["estimated_tokens"]) is not int or type(entry["wall_time_seconds"]) is not int or not isinstance(entry["inputs"],list) or not isinstance(entry["expected_outputs"],list):
                raise OrchestrationError("activation role work fields are invalid")
            zero = entry["estimated_tokens"] == 0 and entry["wall_time_seconds"] == 0 and entry["inputs"] == [] and entry["expected_outputs"] == []
            if entry["mode"] == "FREEZE":
                if not zero: raise OrchestrationError("FREEZE activation entry carries work")
            else:
                expected_outputs = (["activation_map.json"] if entry["role_id"] == "M00" else
                                    ["department-packet.schema.json"] if entry["role_id"].startswith("S") else
                                    ["agent-proposal.schema.json"])
                expected_tokens = 500 if entry["role_id"] == "M00" or entry["role_id"].startswith("S") else 900
                expected_wall = 60 if expected_tokens == 500 else 120
                inputs = entry["inputs"]
                if (entry["estimated_tokens"] != expected_tokens or entry["wall_time_seconds"] != expected_wall
                        or entry["expected_outputs"] != expected_outputs
                        or not inputs or any(not isinstance(value, str) or not value for value in inputs)
                        or len(inputs) != len(set(inputs))
                        or (inputs != ["snapshot"] and inputs != sorted(inputs))):
                    raise OrchestrationError("active activation entry diverges from M5")
                active.append(entry)
        active_inputs = [entry["inputs"] for entry in active]
        if not active_inputs or any(inputs != active_inputs[0] for inputs in active_inputs):
            raise OrchestrationError("active ActivationPlan inputs diverge")
        for department in DEPARTMENTS:
            if mapping[department] == "FREEZE" and any(mapping[child] != "FREEZE" for child in CHILDREN[department]):
                raise OrchestrationError("active worker requires active department")
        if raw["cycle_id"] == 0:
            if any(mapping[department] != "RUN" for department in DEPARTMENTS):
                raise OrchestrationError("cycle zero departments must RUN")
            if any(all(mapping[child] == "FREEZE" for child in CHILDREN[department]) for department in DEPARTMENTS):
                raise OrchestrationError("cycle zero requires one focal worker per department")
            for role in role_order:
                if mapping[role] != "FREEZE" and mapping[role] != ("CHECK" if role in {"W22", "W53"} else "RUN"):
                    raise OrchestrationError("cycle zero mode diverges from M5")
        elif any(mapping[role] != "CHECK" for role in ("W22", "W53") if mapping[role] != "FREEZE"):
            raise OrchestrationError("critical verifier mode diverges from M5")
        if budget["estimated_tokens"] != sum(x["estimated_tokens"] for x in active) or budget["wall_time_seconds"] != sum(x["wall_time_seconds"] for x in active): raise OrchestrationError("activation budget is forged")
        def constraints_for(mandatory: set[str]) -> tuple[list[str], list[str]]:
            active_roles={entry["role_id"] for entry in active}
            missing=sorted(mandatory-active_roles)
            department_counts={department:sum(entry["role_id"] == department or entry["role_id"] in CHILDREN[department] for entry in active) for department in DEPARTMENTS}
            child_counts={department:sum(entry["role_id"] in CHILDREN[department] for entry in active) for department in DEPARTMENTS}
            constraints=[]
            if missing: constraints.append("missing_mandatory")
            if len(active)>limits["max_active_per_cycle"]: constraints.append("cycle_limit")
            if budget["estimated_tokens"]>limits["max_estimated_tokens"]: constraints.append("token_limit")
            if budget["wall_time_seconds"]>limits["max_wall_time_seconds"]: constraints.append("wall_time_limit")
            if any(value>limits["max_active_per_department"] for value in department_counts.values()): constraints.append("department_limit")
            if any(value>limits["max_children_per_manager"] for value in child_counts.values()): constraints.append("children_limit")
            if limits["max_active_per_role"]<1 and active: constraints.append("role_limit")
            return constraints, missing
        if not paused and constraints_for(set())[0]:
            raise OrchestrationError("activation limits incoherent")
        if paused:
            checkpoint_fields = {"reason", "constraints", "mandatory_roles", "missing_mandatory", "active_roles", "estimated_tokens", "wall_time_seconds", "limits"}
            allowed_reasons = {"mandatory_coverage_missing", "mandatory_coverage_exceeds_limits", "department_limit_exhausted", "budget_exhausted"}
            allowed_constraints = {"missing_mandatory", "cycle_limit", "token_limit", "wall_time_limit", "department_limit", "children_limit", "role_limit"}
            if (not isinstance(checkpoint, Mapping) or set(checkpoint) != checkpoint_fields
                    or checkpoint.get("reason") not in allowed_reasons
                    or not isinstance(checkpoint.get("constraints"), list)
                    or not checkpoint["constraints"]
                    or any(not isinstance(item, str) for item in checkpoint["constraints"])
                    or len(checkpoint["constraints"]) != len(set(checkpoint["constraints"]))
                    or any(item not in allowed_constraints for item in checkpoint["constraints"])
                    or any(not isinstance(checkpoint.get(name), list) for name in ("mandatory_roles", "missing_mandatory"))
                    or any(not isinstance(role, str) for role in checkpoint["mandatory_roles"] + checkpoint["missing_mandatory"])
                    or any(type(checkpoint.get(name)) is not int for name in ("active_roles", "estimated_tokens", "wall_time_seconds"))
                    or not isinstance(checkpoint.get("limits"), Mapping)
                    or set(checkpoint["limits"]) != set(PlanningLimits.__dataclass_fields__)):
                raise OrchestrationError("invalid paused ActivationPlan checkpoint")
            mandatory = checkpoint["mandatory_roles"]; missing = checkpoint["missing_mandatory"]
            proof_mandatory = ["S20", "W22"]
            finalization_mandatory = ["S50", "W51", "W53"]
            permitted_mandatory = ([], proof_mandatory, finalization_mandatory, sorted(proof_mandatory + finalization_mandatory))
            if (mandatory != sorted(set(mandatory)) or missing != sorted(set(missing))
                    or any(role not in all_roles for role in mandatory + missing)
                    or mandatory not in permitted_mandatory
                    or missing != []
                    or any(mapping[role] == "FREEZE" for role in mandatory)
                    or (mapping["W22"] != "FREEZE" and proof_mandatory != mandatory and sorted(proof_mandatory + finalization_mandatory) != mandatory)
                    or (mapping["W53"] != "FREEZE" and finalization_mandatory != mandatory and sorted(proof_mandatory + finalization_mandatory) != mandatory)
                    or any(type(value) is not int for value in checkpoint["limits"].values())
                    or checkpoint["active_roles"] != len(active)
                    or checkpoint["estimated_tokens"] != budget["estimated_tokens"]
                    or checkpoint["wall_time_seconds"] != budget["wall_time_seconds"]
                    or dict(checkpoint["limits"]) != dict(limits)
                    or missing != sorted(set(mandatory) - {entry["role_id"] for entry in active})):
                raise OrchestrationError("paused ActivationPlan checkpoint diverges from plan")
            constraints, real_missing = constraints_for(set(mandatory))
            if missing != real_missing or checkpoint["constraints"] != constraints:
                raise OrchestrationError("paused ActivationPlan checkpoint constraints diverge from plan")
            if not constraints:
                raise OrchestrationError("paused ActivationPlan has no real constraint violation")
            expected_reason = (
                "mandatory_coverage_missing" if missing else
                "mandatory_coverage_exceeds_limits" if mandatory else
                "department_limit_exhausted" if constraints == ["department_limit"] else
                "budget_exhausted"
            )
            if checkpoint["reason"] != expected_reason:
                raise OrchestrationError("paused ActivationPlan checkpoint reason diverges from constraints")
        return mapping, raw, paused

    def _canonical(self, run: str, target: State, *, event_id: str, event_type: str, payload: Mapping[str, Any]) -> None:
        """Commit canonical state first; DurableStore idempotency closes retry gaps."""
        store = DurableStore(self.root)
        try:
            store.record(run, target, event_id=event_id, idempotency_key=event_id,
                         actor_id="m6", event_type=event_type, payload=payload)
        except (StoreError, TransitionError) as error:
            raise OrchestrationError("canonical M3/M6 transition rejected") from error

    def _frozen_receipt(self, run: str, receipt: Mapping[str, Any]) -> bytes:
        sha256 = receipt.get("sha256")
        if not isinstance(sha256, str) or not _SHA.fullmatch(sha256):
            raise OrchestrationError("immutable receipt hash is invalid")
        expected = self._managed("state", "orchestration", run, "receipts", sha256, create=False) / "artifact.json"
        frozen = Path(receipt.get("immutable_path", ""))
        if frozen != expected or frozen.is_symlink() or not frozen.is_file():
            raise OrchestrationError("immutable receipt is unsafe")
        data = frozen.read_bytes()
        if _hash(data) != sha256:
            raise OrchestrationError("immutable receipt hash differs")
        return data

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
        persisted = self._load_plan(run, cycle_id)
        if plan is None: plan = persisted
        mapping, raw, paused = self._plan(plan); cycle = raw["cycle_id"] if cycle_id is None else cycle_id
        if cycle != raw["cycle_id"]: raise OrchestrationError("cycle differs from ActivationPlan")
        digest = _hash(_bytes(raw))
        if _hash(_bytes(persisted)) != digest:
            raise OrchestrationError("ActivationPlan hash differs from persisted M5 artifact")
        with self._lock(run):
            state = self._state(run); self._guard(state)
            old_hash=state["activation_hash_by_cycle"].get(str(cycle))
            if old_hash and old_hash != digest: raise OrchestrationError("cannot replace a persisted activation map")
            if cycle != state["cycle_id"] and cycle != state["cycle_id"] + 1: raise OrchestrationError("cycle is not the next canonical cycle")
            preview = self._file(run, f"preview-c{cycle:04d}.json")
            if dry_run:
                self._atomic(preview, {"dry_run":True,"activation_hash":digest,"activation_map":raw}); return self._snapshot(run)
            if not old_hash:
                if cycle != state["cycle_id"] and DurableStore(self.root).snapshot(run)["state"] != State.CYCLE_COMPLETE.value: raise OrchestrationError("prior cycle is not complete")
                plan_file=self._file(run, f"activation-c{cycle:04d}.json")
                if plan_file.exists() and plan_file.read_bytes() != _bytes(raw) + b"\n": raise OrchestrationError("immutable PLAN artifact conflicts")
                if not plan_file.exists(): self._atomic(plan_file, raw)
            # Reconcile either side of an interrupted mirror before treating
            # the cycle as ready.  The DurableStore idempotency key makes this
            # safe for normal reentry and for a crash after its commit.
            self._canonical(run, State.CYCLE_PLANNED, event_id=f"{run}:m6:c{cycle}:planned", event_type="M6_CYCLE_PLANNED", payload={"activation_hash":digest})
            self._append(run,"PLAN",f"{run}:c{cycle}:plan",{"cycle_id":cycle,"activation":mapping,"activation_hash":digest,"raw":raw})
        if paused:
            # A paused M5 plan is recorded as CYCLE_PLANNED, then paused with
            # the same concrete transition rules as an operator request.
            return await self.pause(run)
        # Each admission persists independently under the run lock.
        for role in DEPARTMENTS:
            if mapping[role] != "FREEZE": await self._admit(run, cycle, role, self.adapter)
        with self._lock(run):
            self._canonical(run, State.DEPARTMENTS_RUNNING, event_id=f"{run}:m6:c{cycle}:departments", event_type="M6_DEPARTMENTS_RUNNING", payload={"activation_hash":digest})
            self._append(run,"DEPARTMENTS_RUNNING",f"{run}:c{cycle}:departments",{})
            result = self._save_snapshot(run)
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
            if role.startswith("S"):
                # A submanager receives only task/proposal material of direct
                # children.  It never receives another department's context.
                children = [{"role_id": child, "task_hash": state["children"][child]["task_hash"]}
                            for child in CHILDREN[role] if child in state["children"]]
                view = submanager_view(task, children)
            else:
                # A specialist gets an explicit local slice, never an editable
                # champion nor a global blackboard dump.
                view = specialist_view(
                    task,
                    excerpts=[item for item in task["input_locators"] if item.startswith("readonly:")],
                    dependent_claims=[{"locator": item} for item in task["input_locators"] if item.startswith("blackboard:")],
                    rubric={"locator": next(item for item in task["input_locators"] if item.endswith("evaluation.yaml")), "role_id": role},
                    local_history=[{"locator": item} for item in task["input_locators"] if item.startswith("readonly:history:")],
                )
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
            # This intent is the admission ownership token.  A concurrent pass
            # can reconcile it but must not issue a second spawn.
            intent_key=f"{run}:c{cycle}:{role}:intent"
            owns_intent=not any(event["idempotency_key"] == intent_key for event in self._events(run))
            self._append(run,"SPAWN_INTENT",intent_key,{"role_id":role,"cycle_id":cycle,"name":_name(run,cycle,role),"parent_id":getattr(adapter,"actor_id",None)})
        # A process may die after rlm() admits the child but before HANDLE is
        # journaled. The deterministic name reconciles that narrow window.
        name = _name(run, cycle, role)
        existing = next((item for item in await adapter.list_subagents() if item.name == name), None)
        if existing is not None:
            handle = existing
        elif not owns_intent:
            # A prior owner may have died after intent.  Do not turn this
            # uncertainty into a duplicate child; a later reconciliation can
            # observe the deterministic name and journal HANDLE.
            raise OrchestrationError("active SPAWN_INTENT awaits reconciliation")
        else:
            handle = await adapter.spawn(compiled.text + "\nWorkspace permitido: " + str(workspace) + "\nEnvie ao pai apenas receipt {path,sha256,schema_version}.", name=name)
        with self._lock(run):
            state=self._state(run); old=state["children"].get(role)
            if old and old["cycle_id"] == cycle: return old
            if not isinstance(handle, ChildHandle) or not all(isinstance(x,str) and x for x in (handle.child_id,handle.name,handle.session_dir)):
                raise OrchestrationError("adapter returned incomplete handle")
            if handle.parent_id != getattr(adapter,"actor_id",None) or handle.actor_role != getattr(adapter,"actor_role",None) or handle.depth != expected_depth:
                raise OrchestrationError("adapter handle parent, actor or depth differs")
            record={"role_id":role,"cycle_id":cycle,"child_id":handle.child_id,"name":handle.name,"session_dir":handle.session_dir,"model":handle.model,"parent_id":handle.parent_id,"actor_role":handle.actor_role,"depth":handle.depth,"status":"ADMITTED",**artifact}
            self._append(run,"HANDLE",f"{run}:c{cycle}:{role}:handle",record); return self._save_snapshot(run)["children"][role]

    def _context(self, task: Mapping[str, Any]) -> dict[str, Any]: return {k:task[k] for k in ("run_id","cycle_id","base_hash","activation_mode","scope","input_locators")}
    def _task(self, state: Mapping[str, Any], role: str, workspace: Path) -> dict[str, Any]:
        schema="department-packet.schema.json" if role.startswith("S") else "agent-proposal.schema.json"
        champion=self.root / "versions" / "champion" / "v0000"
        extracted=self.root / "artifacts" / "extracted" / str(state["pdf_sha256"])
        rendered=self.root / "artifacts" / "rendered" / str(state["pdf_sha256"])
        rubric=self.root / "config" / "rubrics" / "evaluation.yaml"
        plan_inputs=state["plans_by_cycle"][str(state["cycle_id"])]["roles"]
        entry=next(item for item in plan_inputs if item["role_id"] == role)
        scope=sorted(set([f"role:{role}", *entry["inputs"]]))
        inputs=[f"readonly:{champion / 'baseline.pdf'}", f"readonly:{champion / 'manifest.json'}", f"readonly:{extracted}", f"readonly:{rendered}", f"readonly:{rubric}", *[f"blackboard:{item}" for item in entry["inputs"]]]
        if role.startswith("W"):
            # A specialist sees only the immutable source context and its own
            # local blackboard slice; its output workspace is deliberately not
            # advertised as an input locator.
            inputs.append(f"readonly:history:{self._dir(state['run_id']) / 'snapshot.json'}")
        else:
            inputs.extend(f"child-task:{state['children'][child]['task_hash']}" for child in CHILDREN[role] if child in state["children"])
        return {"schema_version":SCHEMA_VERSION,"task_id":f"{state['run_id']}-{role}-c{state['cycle_id']:04d}","run_id":state["run_id"],"cycle_id":state["cycle_id"],"role_id":role,"activation_mode":state["activation"][role],"created_at":_now(),"base_hash":state["base_hash"],"scope":scope,"input_locators":inputs,"requested_output_schema":schema,"prompt_version":expected_prompt_version(self.root,role,schema),"constraints":["workspace_isolated_output_only","receipt_only","no_champion_write","inputs_read_only"]}

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
            old=state["receipts"].get(sender_role)
            if old:
                if old.get("sha256") != sha256 or old.get("path") != str(Path(path)) or old.get("parent_role") != parent_role or old.get("schema_version") != schema_version or old.get("cycle_id") != state["cycle_id"]:
                    raise OrchestrationError("conflicting second receipt")
                data=self._frozen_receipt(run,old)
                schema="department-packet.schema.json" if sender_role.startswith("S") else "agent-proposal.schema.json"
                try: document=json.loads(data); validate_output(self.root,schema,document)
                except (json.JSONDecodeError,PromptContractError) as error: raise OrchestrationError("immutable receipt schema invalid") from error
                if sender_role.startswith("W"):
                    good=document.get("role_id")==sender_role and document.get("cycle_id")==state["cycle_id"] and document.get("base_hash")==state["base_hash"]
                else:
                    good=document.get("department_id")==sender_role and document.get("run_id")==run and document.get("cycle_id")==state["cycle_id"] and document.get("base_hash")==state["base_hash"]
                if not good: raise OrchestrationError("immutable receipt identity differs")
                return state
            workspace=self._workspace(run,state["cycle_id"],sender_role); target=Path(path)
            self._regular(target,workspace)
            # The untrusted workspace file is consumed exactly once.  Hashing,
            # parsing, validation and freezing must all describe this single
            # byte sequence; rereading it would admit a TOCTOU substitution.
            data=target.read_bytes()
            if target.parent != workspace or _hash(data) != sha256: raise OrchestrationError("receipt location or hash differs")
            schema="department-packet.schema.json" if sender_role.startswith("S") else "agent-proposal.schema.json"
            try: document=json.loads(data); validate_output(self.root,schema,document)
            except (json.JSONDecodeError,PromptContractError) as error: raise OrchestrationError("receipt schema invalid") from error
            if sender_role.startswith("W"):
                good=document.get("role_id")==sender_role and document.get("cycle_id")==state["cycle_id"] and document.get("base_hash")==state["base_hash"]
            else: good=document.get("department_id")==sender_role and document.get("run_id")==run and document.get("cycle_id")==state["cycle_id"] and document.get("base_hash")==state["base_hash"]
            if not good: raise OrchestrationError("receipt identity differs")
            immutable=self._managed("state","orchestration",run,"receipts",sha256,create=True)/"artifact.json"
            if immutable.exists() and immutable.read_bytes()!=data: raise OrchestrationError("content-addressed receipt conflict")
            if not immutable.exists(): self._atomic_bytes(immutable,data)
            # Confirm the bytes we have frozen before making the RECEIPT
            # durable.  All later consumers use immutable_path exclusively.
            if _hash(self._frozen_receipt(run,{"immutable_path":str(immutable),"sha256":sha256})) != sha256:
                raise OrchestrationError("immutable receipt hash differs")
            payload={"sender_role":sender_role,"parent_role":parent_role,"path":str(target),"immutable_path":str(immutable),"sha256":sha256,"schema_version":schema_version,"cycle_id":state["cycle_id"]}
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
        state=self._state(run); self._guard(state); target=self._workspace(run,state["cycle_id"],department)/"department-packet.json"
        accepted=state["receipts"].get(department)
        if accepted:
            if accepted.get("parent_role") != "M00" or accepted.get("path") != str(target) or accepted.get("cycle_id") != state["cycle_id"] or accepted.get("schema_version") != SCHEMA_VERSION:
                raise OrchestrationError("accepted DepartmentPacket envelope differs")
            encoded=self._frozen_receipt(run,accepted)
            try: packet=json.loads(encoded); validate_output(self.root,"department-packet.schema.json",packet)
            except (json.JSONDecodeError, PromptContractError) as error: raise OrchestrationError("immutable DepartmentPacket schema invalid") from error
            if packet.get("run_id") != run or packet.get("cycle_id") != state["cycle_id"] or packet.get("department_id") != department or packet.get("base_hash") != state["base_hash"]:
                raise OrchestrationError("immutable DepartmentPacket identity differs")
            if target.is_symlink(): raise OrchestrationError("symlinked DepartmentPacket workspace")
            if target.exists() and not target.is_file(): raise OrchestrationError("DepartmentPacket workspace is not a regular file")
            # The frozen receipt is authoritative: never consult mutable bytes
            # to decide a retry or to derive the receipt hash.
            self._atomic_bytes(target,encoded)
            result=await self.receipt(run,sender_role=department,parent_role="M00",path=accepted["path"],sha256=accepted["sha256"],schema_version=accepted["schema_version"])
            await adapter.send_parent(_bytes({"path":accepted["path"],"sha256":accepted["sha256"],"schema_version":accepted["schema_version"]}).decode())
            return result
        workers=[r for r in CHILDREN[department] if state["activation"].get(r)!="FREEZE"]
        if any(r not in state["receipts"] for r in workers): raise OrchestrationError("department has pending receipts")
        proposals=[]
        for r in workers:
            receipt=state["receipts"][r]
            try: proposal=json.loads(self._frozen_receipt(run,receipt)); validate_output(self.root,"agent-proposal.schema.json",proposal)
            except (json.JSONDecodeError, PromptContractError) as error: raise OrchestrationError("immutable receipt schema invalid") from error
            if proposal.get("role_id")!=r or proposal.get("cycle_id")!=state["cycle_id"] or proposal.get("base_hash")!=state["base_hash"]: raise OrchestrationError("immutable receipt identity differs")
            proposals.append(proposal)
        technical=[x for x in proposals if x.get("risk",{}).get("technical_effect_possible")]
        if target.exists():
            self._regular(target, self._workspace(run,state["cycle_id"],department))
            # Publication is write-once.  A retry only reuses these exact bytes
            # (including created_at), then may resend its envelope to M00.
            encoded=target.read_bytes()
            try:
                packet=json.loads(encoded)
                validate_output(self.root,"department-packet.schema.json",packet)
            except (json.JSONDecodeError, PromptContractError) as error: raise OrchestrationError("existing DepartmentPacket is invalid") from error
            if packet.get("run_id") != run or packet.get("cycle_id") != state["cycle_id"] or packet.get("department_id") != department or packet.get("base_hash") != state["base_hash"]:
                raise OrchestrationError("existing DepartmentPacket identity differs")
        else:
            review_index: dict[str, dict[str, Any]]={}
            s20=state["receipts"].get("S20")
            if s20:
                try: source_packet=json.loads(self._frozen_receipt(run,s20)); validate_output(self.root,"department-packet.schema.json",source_packet)
                except (json.JSONDecodeError, PromptContractError) as error: raise OrchestrationError("S20 dependency packet is invalid") from error
                if source_packet.get("department_id") != "S20" or source_packet.get("run_id") != run or source_packet.get("cycle_id") != state["cycle_id"] or source_packet.get("base_hash") != state["base_hash"]: raise OrchestrationError("S20 dependency packet identity differs")
                review_index={x["proposal_id"]:x for x in source_packet["dependency_reviews"]}
            reviews=[]; missing_review=False
            for proposal in technical:
                review=review_index.get(proposal["proposal_id"])
                valid=isinstance(review,dict) and review.get("proposal_id")==proposal["proposal_id"] and review.get("reviewer_role_id")=="S20" and review.get("status")=="approved" and review.get("cycle_id")==state["cycle_id"] and review.get("base_hash")==state["base_hash"] and isinstance(review.get("evidence_locators"),list) and bool(review["evidence_locators"])
                if valid: reviews.append(review)
                else: missing_review=True
            status="no_change" if not workers else ("blocked" if missing_review else "complete")
            packet={"schema_version":SCHEMA_VERSION,"packet_id":f"{run}-{department}-c{state['cycle_id']:04d}","run_id":run,"cycle_id":state["cycle_id"],"department_id":department,"base_hash":state["base_hash"],"proposal_ids":[x["proposal_id"] for x in proposals],"specialist_task_ids":[state["children"][r]["task_hash"] for r in workers],"dependency_reviews":reviews,"status":status,"no_change_justification":"no active worker exists for this department" if not workers else None,"evidence_locators":[state["receipts"][r]["immutable_path"] for r in workers] or [str(self.root / "versions" / "champion" / "v0000" / "manifest.json")],"created_at":_now()}
            try: validate_output(self.root,"department-packet.schema.json",packet)
            except PromptContractError as error: raise OrchestrationError("generated DepartmentPacket is invalid") from error
            encoded=_bytes(packet)+b"\n"
            # Admission/consolidation can be resumed concurrently.  Only the
            # owner holding this journal lock can publish a new packet; a
            # loser consumes the already-published immutable byte sequence.
            with self._lock(run):
                if target.exists():
                    self._regular(target, self._workspace(run,state["cycle_id"],department))
                    encoded=target.read_bytes()
                    try:
                        packet=json.loads(encoded)
                        validate_output(self.root,"department-packet.schema.json",packet)
                    except (json.JSONDecodeError, PromptContractError) as error:
                        raise OrchestrationError("concurrent DepartmentPacket is invalid") from error
                    if packet.get("run_id") != run or packet.get("cycle_id") != state["cycle_id"] or packet.get("department_id") != department or packet.get("base_hash") != state["base_hash"]:
                        raise OrchestrationError("concurrent DepartmentPacket identity differs")
                else:
                    self._atomic_bytes(target,encoded)
        digest=_hash(encoded)
        result=await self.receipt(run,sender_role=department,parent_role="M00",path=target,sha256=digest)
        await adapter.send_parent(_bytes({"path":str(target),"sha256":digest,"schema_version":SCHEMA_VERSION}).decode())
        return result

    async def pause(self, run_id: str) -> dict[str, Any]:
        run=self._run(run_id)
        with self._lock(run):
            state=self._state(run)
            if state["paused"]:
                pause_id=state.get("pause_id")
                if not isinstance(pause_id,str): raise OrchestrationError("paused journal lacks pause id")
                self._canonical(run,State.PAUSED,event_id=pause_id,event_type="M6_PAUSED",payload={"resume_state":state.get("resume_state")})
                return state
            if state["stopped"] or state["finalized"]: raise OrchestrationError("execution is terminal")
            pause_id=f"{run}:pause:{len(self._events(run))}"
            payload={"pause_id":pause_id,"resume_state":state["state"]}
            self._canonical(run,State.PAUSED,event_id=pause_id,event_type="M6_PAUSED",payload=payload)
            self._append(run,"PAUSED",pause_id,payload)
            return self._save_snapshot(run)
    async def resume(self, run_id: str) -> dict[str, Any]:
        run=self._run(run_id)
        with self._lock(run):
            state=self._state(run)
            if state["stopped"] or state["finalized"] or not state["paused"]: raise OrchestrationError("execution cannot resume")
            pause_id=state.get("pause_id"); resume_state=state.get("resume_state")
            if not isinstance(pause_id,str) or resume_state not in {item.value for item in State}: raise OrchestrationError("paused journal is malformed")
            key=f"{run}:resume:{pause_id}"; payload={"pause_id":pause_id}
            # Do not use DurableStore.resume(): after a crash between its
            # commit and RESUMED, record() recognizes this idempotency key.
            self._canonical(run,State(resume_state),event_id=key,event_type="M6_RESUMED",payload=payload)
            self._append(run,"RESUMED",key,payload)
            return self._save_snapshot(run)
    async def stop(self, run_id: str) -> dict[str, Any]:
        run=self._run(run_id)
        with self._lock(run):
            state=self._state(run)
            stop_id=f"{run}:m6:stopped"
            if state["stopped"]:
                self._canonical(run,State.TECHNICAL_FAILURE,event_id=stop_id,event_type="M6_STOPPED",payload={"reason":"operator_stop"})
                return state
            if state["finalized"]: raise OrchestrationError("execution is terminal")
            for role, child in state["children"].items():
                if child["status"] == "ADMITTED": self._append(run,"CANCELLED",f"{run}:c{state['cycle_id']}:{role}:cancelled",{"role_id":role,"pending_owner":child["parent_id"] != getattr(self.adapter,"actor_id",None)})
            self._canonical(run,State.TECHNICAL_FAILURE,event_id=stop_id,event_type="M6_STOPPED",payload={"reason":"operator_stop"})
            self._append(run,"STOPPED",stop_id,{})
            result=self._save_snapshot(run)
        # Only the owning actor may remove direct children; unresolved owners
        # remain journaled as pending cancellation, never false success.
        if self.adapter:
            for child in state["children"].values():
                if child["parent_id"] == getattr(self.adapter,"actor_id",None): await self.adapter.delete_subagent(child["child_id"])
        return result
    async def finalize(self, run_id: str) -> dict[str, Any]:
        run=self._run(run_id)
        if DurableStore(self.root).snapshot(run)["state"] != State.CYCLE_COMPLETE.value: raise OrchestrationError("M10 finalization requires CYCLE_COMPLETE")
        return await self._flag(run,"FINALIZED",{})
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
