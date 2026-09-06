"""Append-only local durable state with replay, locks and atomic snapshots."""

from __future__ import annotations

import fcntl
import errno
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
_SHA256 = re.compile(r"[a-f0-9]{64}\Z")
_EVENT_FIELDS = frozenset({
    "schema_version", "event_id", "idempotency_key", "run_id", "cycle_id",
    "sequence", "occurred_at", "event_type", "state_from", "state_to",
    "actor_id", "payload", "artifact_hashes", "previous_event_hash", "event_hash",
})
# Directory fsync is optional only on filesystems that explicitly report it as
# unsupported.  Every other open, fsync, or close error is a failed durable
# publication and must propagate to the caller.
_DIRECTORY_FSYNC_UNSUPPORTED_ERRNOS = frozenset({
    errno.EINVAL,
    errno.ENOTSUP,
    getattr(errno, "EOPNOTSUPP", errno.ENOTSUP),
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


def _is_timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


class DurableStore:
    """Filesystem-only event store rooted at an existing project directory."""

    def __init__(
        self,
        root: str | Path,
        *,
        fault: Callable[[str], None] | None = None,
        read_only: bool = False,
    ):
        raw_root = Path(root)
        if raw_root.is_symlink():
            raise StoreError("root must not be a symlink")
        self.root = raw_root.resolve()
        self.fault = fault
        if type(read_only) is not bool:
            raise StoreError("read_only must be boolean")
        self.read_only = read_only
        if not self.root.is_dir():
            raise StoreError("root must be an existing directory")
        for relative in ("state/events", "state/snapshots", "state/checkpoints", "state/locks"):
            path = self.root / relative
            if self.read_only:
                if path.exists() and (path.is_symlink() or not path.is_dir()):
                    raise StoreError("runtime state directory is unsafe")
            else:
                path.mkdir(parents=True, exist_ok=True)

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

    def _fault(self, stage: str) -> None:
        if self.fault:
            self.fault(stage)

    def _fsync_directory(self, directory: Path) -> None:
        try:
            descriptor = os.open(directory, os.O_RDONLY)
        except OSError as error:
            if error.errno in _DIRECTORY_FSYNC_UNSUPPORTED_ERRNOS:
                return
            raise
        try:
            os.fsync(descriptor)
        except OSError as error:
            if error.errno not in _DIRECTORY_FSYNC_UNSUPPORTED_ERRNOS:
                raise
        finally:
            os.close(descriptor)

    def _atomic_bytes(self, path: Path, data: bytes) -> None:
        self._fault("before_temp_write")
        descriptor, temporary_name = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                self._fault("during_preparation")
                stream.flush()
                os.fsync(stream.fileno())
            self._fault("after_fsync_before_rename")
            self._fault("before_rename")
            os.replace(temporary, path)
            self._fsync_directory(path.parent)
            self._fault("after_rename")
            self._fault("before_final_verification")
            if _hash(path.read_bytes()) != _hash(data):
                raise IntegrityError("atomic hash verification failed")
        finally:
            if temporary.exists():
                temporary.unlink()

    def _atomic(self, path: Path, value: Mapping[str, Any]) -> None:
        self._atomic_bytes(path, _bytes(value))

    def _validate_record_parameters(
        self, run_id: str, target: State, event_id: Any, idempotency_key: Any,
        actor_id: Any, event_type: Any, payload: Any, artifact_hashes: Any,
    ) -> None:
        self._run_id(run_id)
        if not isinstance(target, State):
            raise StoreError("target state is invalid")
        if not isinstance(event_id, str) or not event_id:
            raise StoreError("event_id is invalid")
        if (not isinstance(idempotency_key, str) or not idempotency_key
                or len(idempotency_key) > 256):
            raise StoreError("idempotency_key is invalid")
        if not isinstance(actor_id, str) or not actor_id:
            raise StoreError("actor_id is invalid")
        if not isinstance(event_type, str) or not event_type:
            raise StoreError("event_type is invalid")
        if payload is not None and not isinstance(payload, Mapping):
            raise StoreError("payload is invalid")
        if artifact_hashes is not None:
            if not isinstance(artifact_hashes, list):
                raise StoreError("artifact_hashes is invalid")
            if not all(_is_sha256(value) for value in artifact_hashes):
                raise StoreError("artifact_hashes are invalid")
            if len(artifact_hashes) != len(set(artifact_hashes)):
                raise StoreError("artifact_hashes must be unique")

    def _validate_event(self, event: Any, run_id: str, sequence: int, previous_hash: str | None) -> None:
        if not isinstance(event, dict) or set(event) != _EVENT_FIELDS:
            raise IntegrityError("event fields are invalid")
        if event["schema_version"] != SCHEMA_VERSION:
            raise IntegrityError("event schema_version is invalid")
        try:
            self._run_id(event["run_id"])
        except StoreError as error:
            raise IntegrityError("event run_id is invalid") from error
        if (type(event["sequence"]) is not int or event["sequence"] < 0
                or type(event["cycle_id"]) is not int or event["cycle_id"] < 0):
            raise IntegrityError("event sequence or cycle_id is invalid")
        if event["run_id"] != run_id or event["sequence"] != sequence:
            raise IntegrityError("event run_id or sequence mismatch")
        if not _is_timestamp(event["occurred_at"]):
            raise IntegrityError("event occurred_at is invalid")
        if not isinstance(event["event_id"], str) or not event["event_id"]:
            raise IntegrityError("event_id is invalid")
        if (not isinstance(event["idempotency_key"], str) or not event["idempotency_key"]
                or len(event["idempotency_key"]) > 256):
            raise IntegrityError("idempotency_key is invalid")
        if not isinstance(event["event_type"], str) or not event["event_type"]:
            raise IntegrityError("event_type is invalid")
        if not isinstance(event["actor_id"], str) or not event["actor_id"]:
            raise IntegrityError("actor_id is invalid")
        if event["previous_event_hash"] != previous_hash:
            raise IntegrityError("event chain mismatch")
        if not isinstance(event["payload"], dict) or not isinstance(event["artifact_hashes"], list):
            raise IntegrityError("event payload is invalid")
        if not all(_is_sha256(value) for value in event["artifact_hashes"]):
            raise IntegrityError("event artifact_hashes are invalid")
        if len(event["artifact_hashes"]) != len(set(event["artifact_hashes"])):
            raise IntegrityError("event artifact_hashes are not unique")
        if sequence == 0:
            if event["previous_event_hash"] is not None:
                raise IntegrityError("initial previous_event_hash is invalid")
        elif not _is_sha256(event["previous_event_hash"]):
            raise IntegrityError("event previous_event_hash is invalid")
        if not _is_sha256(event["event_hash"]):
            raise IntegrityError("event_hash is invalid")
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
            self._validate_replay_transition(event, events)
            if any(previous["event_id"] == event["event_id"] for previous in events):
                raise IntegrityError("duplicate event_id in log")
            if any(previous["idempotency_key"] == event["idempotency_key"] for previous in events):
                raise IntegrityError("duplicate idempotency_key in log")
            events.append(event)
        return events

    def _validate_replay_transition(
        self, event: Mapping[str, Any], events: list[dict[str, Any]]
    ) -> None:
        """Validate state-machine semantics in addition to event integrity."""
        target = State(event["state_to"])
        if not events:
            if (event["sequence"] != 0 or event["state_from"] is not None
                    or target is not State.NEW or event["previous_event_hash"] is not None
                    or event["cycle_id"] != 0):
                raise IntegrityError("initial event semantics are invalid")
            return

        previous = events[-1]
        current = State(previous["state_to"])
        if event["state_from"] != current.value:
            raise IntegrityError("event state_from does not match prior state")
        expected_cycle = previous["cycle_id"] + int(
            current is State.CYCLE_COMPLETE and target is State.CYCLE_PLANNED
        )
        if event["cycle_id"] != expected_cycle:
            raise IntegrityError("event cycle_id transition is invalid")
        resume_to = None
        if current is State.PAUSED:
            resume_value = previous["payload"].get("resume_state")
            try:
                resume_to = State(resume_value)
            except (TypeError, ValueError) as error:
                raise IntegrityError("paused event has invalid resume_state") from error
            if resume_to in {State.PAUSED, State.FINALIZED, State.TECHNICAL_FAILURE}:
                raise IntegrityError("paused event has invalid resume_state")
        if target is State.PAUSED:
            resume_value = event["payload"].get("resume_state")
            try:
                resume_state = State(resume_value)
            except (TypeError, ValueError) as error:
                raise IntegrityError("pause event has invalid resume_state") from error
            if resume_state is not current:
                raise IntegrityError("pause event resume_state does not match prior state")
        try:
            require_transition(current, target, resume_to=resume_to)
        except TransitionError as error:
            raise IntegrityError("event state transition is invalid") from error

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
        self._validate_record_parameters(
            run_id, target, event_id, idempotency_key, actor_id, event_type,
            payload, artifact_hashes,
        )
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
                "payload": event_payload, "artifact_hashes": sorted(artifact_hashes or []),
                "previous_event_hash": events[-1]["event_hash"] if events else None,
            }
            event["event_hash"] = self._ehash(event)
            self._validate_event(
                event, run_id, len(events), events[-1]["event_hash"] if events else None,
            )
            log = self._log(run_id)
            prior = log.read_bytes() if log.exists() else b""
            self._atomic_bytes(log, prior + _bytes(event) + b"\n")
            self.read_events(run_id)
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
