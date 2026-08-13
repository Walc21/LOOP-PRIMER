"""Append-only local durable state with replay, locks and atomic snapshots."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .state_machine import State, TransitionError, require_transition

SCHEMA_VERSION = "1.1.0"
_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
_EVENT_FIELDS = frozenset({
    "schema_version", "event_id", "idempotency_key", "run_id", "cycle_id",
    "sequence", "occurred_at", "event_type", "state_from", "state_to",
    "actor_id", "payload", "artifact_hashes", "previous_event_hash", "event_hash",
})


class StoreError(RuntimeError):
    """Base error for local durable-state operations."""


class IntegrityError(StoreError):
    """The event log or snapshot cannot be trusted."""


class StopRequested(StoreError):
    """``control/STOP`` was present before the locked operation began."""


def _bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class DurableStore:
    """Filesystem-only event store rooted at an existing project directory."""

    def __init__(self, root: str | Path, *, fault: Callable[[str], None] | None = None):
        self.root = Path(root).resolve()
        self.fault = fault
        if not self.root.is_dir():
            raise StoreError("root must be an existing directory")
        for relative in ("state/events", "state/snapshots", "state/checkpoints", "state/locks"):
            (self.root / relative).mkdir(parents=True, exist_ok=True)

    def _p(self, relative: str) -> Path:
        path = (self.root / relative).resolve()
        if self.root not in path.parents:
            raise StoreError("path escapes validated root")
        return path

    def _run_id(self, run_id: str) -> str:
        if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id) or run_id in {".", ".."}:
            raise StoreError("run_id must be a simple identifier")
        return run_id

    def _log(self, run_id: str) -> Path:
        return self._p(f"state/events/{self._run_id(run_id)}.jsonl")

    def _snap(self, run_id: str) -> Path:
        return self._p(f"state/snapshots/{self._run_id(run_id)}.json")

    @contextmanager
    def _lock(self, run_id: str):
        with self._p(f"state/locks/{self._run_id(run_id)}.lock").open("a+") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

    def _ehash(self, event: Mapping[str, Any]) -> str:
        value = dict(event)
        value.pop("event_hash", None)
        return _hash(_bytes(value))

    def _atomic(self, path: Path, value: Mapping[str, Any]) -> None:
        data = _bytes(value)
        descriptor, temporary_name = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if self.fault:
                self.fault("before_rename")
            os.replace(temporary, path)
            if self.fault:
                self.fault("after_rename")
            if _hash(path.read_bytes()) != _hash(data):
                raise IntegrityError("atomic hash verification failed")
        finally:
            if temporary.exists():
                temporary.unlink()

    def _validate_event(self, event: Any, run_id: str, sequence: int, previous_hash: str | None) -> None:
        if not isinstance(event, dict) or set(event) != _EVENT_FIELDS:
            raise IntegrityError("event fields are invalid")
        if event["run_id"] != run_id or event["sequence"] != sequence:
            raise IntegrityError("event run_id or sequence mismatch")
        if event["previous_event_hash"] != previous_hash:
            raise IntegrityError("event chain mismatch")
        if not isinstance(event["event_id"], str) or not isinstance(event["idempotency_key"], str):
            raise IntegrityError("event identifiers are invalid")
        if not isinstance(event["payload"], dict) or not isinstance(event["artifact_hashes"], list):
            raise IntegrityError("event payload is invalid")
        try:
            State(event["state_to"])
            if event["state_from"] is not None:
                State(event["state_from"])
        except (TypeError, ValueError) as error:
            raise IntegrityError("event state is invalid") from error
        if event["event_hash"] != self._ehash(event):
            raise IntegrityError("event hash mismatch")

    def read_events(self, run_id: str) -> list[dict[str, Any]]:
        """Replay and fully validate the committed JSONL event log.

        A final record without a newline was never committed.  It is reported as
        corruption instead of being silently ignored, so an operator can retain
        the evidence and choose an explicit recovery action.
        """
        run_id = self._run_id(run_id)
        path = self._log(run_id)
        if not path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line in path.read_bytes().splitlines(keepends=True):
            if not line.endswith(b"\n"):
                raise IntegrityError("partial event line")
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise IntegrityError("invalid event JSON") from error
            previous_hash = events[-1]["event_hash"] if events else None
            self._validate_event(event, run_id, len(events), previous_hash)
            if any(previous["event_id"] == event["event_id"] for previous in events):
                raise IntegrityError("duplicate event_id in log")
            if any(previous["idempotency_key"] == event["idempotency_key"] for previous in events):
                raise IntegrityError("duplicate idempotency_key in log")
            events.append(event)
        return events

    def _snapshot(self, run_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
        if events:
            last = events[-1]
            state, sequence, cycle = last["state_to"], last["sequence"], last["cycle_id"]
            last_id, last_hash = last["event_id"], last["event_hash"]
            resume = last["payload"].get("resume_state") if state == State.PAUSED else None
        else:
            state, sequence, cycle, last_id, last_hash, resume = "NEW", -1, 0, None, None, None
        data = {"resume_state": resume}
        snapshot = {
            "schema_version": SCHEMA_VERSION,
            "snapshot_id": f"{run_id}:{sequence}",
            "run_id": run_id,
            "cycle_id": cycle,
            "event_sequence": sequence,
            "created_at": _now(),
            "state": state,
            "last_event_id": last_id,
            "last_event_hash": last_hash,
            "data": data,
            "data_hash": _hash(_bytes(data)),
        }
        snapshot["snapshot_hash"] = _hash(_bytes(snapshot))
        return snapshot

    def rebuild_snapshot(self, run_id: str, *, persist: bool = True) -> dict[str, Any]:
        run_id = self._run_id(run_id)
        snapshot = self._snapshot(run_id, self.read_events(run_id))
        if persist:
            self._atomic(self._snap(run_id), snapshot)
        return snapshot

    def snapshot(self, run_id: str) -> dict[str, Any]:
        return self.rebuild_snapshot(run_id, persist=False)

    def create_run(self, run_id: str, *, actor_id: str = "system", event_id: str | None = None):
        run_id = self._run_id(run_id)
        return self.record(
            run_id, State.NEW, event_id=event_id or f"{run_id}:created",
            idempotency_key=f"{run_id}:created", actor_id=actor_id,
            event_type="RUN_CREATED", initial=True,
        )

    def record(
        self, run_id: str, target: State, *, event_id: str, idempotency_key: str,
        actor_id: str, event_type: str = "STATE_RECORDED",
        payload: Mapping[str, Any] | None = None, artifact_hashes: list[str] | None = None,
        initial: bool = False,
    ) -> dict[str, Any]:
        run_id = self._run_id(run_id)
        with self._lock(run_id):
            if self._p("control/STOP").is_file():
                raise StopRequested("control/STOP blocks new operations")
            events = self.read_events(run_id)
            for event in events:
                if event["event_id"] == event_id or event["idempotency_key"] == idempotency_key:
                    if (event["event_id"] == event_id and event["idempotency_key"] == idempotency_key
                            and event["state_to"] == target.value):
                        return event
                    raise StoreError("idempotency conflict")
            if not events:
                if not initial or target is not State.NEW:
                    raise TransitionError("run must begin at NEW")
                current, state_from, cycle = State.NEW, None, 0
            else:
                current = State(events[-1]["state_to"])
                state_from = current.value
                resume_to = State(events[-1]["payload"]["resume_state"]) if current is State.PAUSED else None
                require_transition(current, target, resume_to=resume_to)
                cycle = events[-1]["cycle_id"] + int(
                    current is State.CYCLE_COMPLETE and target is State.CYCLE_PLANNED
                )
            event_payload = dict(payload or {})
            if target is State.PAUSED:
                event_payload["resume_state"] = current.value
            event = {
                "schema_version": SCHEMA_VERSION, "event_id": event_id,
                "idempotency_key": idempotency_key, "run_id": run_id,
                "cycle_id": cycle, "sequence": len(events), "occurred_at": _now(),
                "event_type": event_type, "state_from": state_from,
                "state_to": target.value, "actor_id": actor_id,
                "payload": event_payload, "artifact_hashes": sorted(set(artifact_hashes or [])),
                "previous_event_hash": events[-1]["event_hash"] if events else None,
            }
            event["event_hash"] = self._ehash(event)
            with self._log(run_id).open("ab") as stream:
                stream.write(_bytes(event) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            self.rebuild_snapshot(run_id, persist=True)
            return event

    def pause(self, run_id: str, **kwargs: Any) -> dict[str, Any]:
        return self.record(run_id, State.PAUSED, **kwargs)

    def resume(self, run_id: str, **kwargs: Any) -> dict[str, Any]:
        resume_state = self.snapshot(run_id)["data"]["resume_state"]
        if not resume_state:
            raise TransitionError("run is not paused")
        return self.record(run_id, State(resume_state), **kwargs)

    def checkpoint(self, run_id: str) -> dict[str, Any]:
        run_id = self._run_id(run_id)
        with self._lock(run_id):
            if self._p("control/STOP").is_file():
                raise StopRequested("control/STOP blocks new operations")
            snapshot = self.rebuild_snapshot(run_id, persist=True)
            self._atomic(self._p(f"state/checkpoints/{run_id}-{snapshot['event_sequence']}.json"), snapshot)
            return snapshot
