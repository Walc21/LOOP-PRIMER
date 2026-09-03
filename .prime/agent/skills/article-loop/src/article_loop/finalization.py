"""M10 crash-safe disposition finalizer.

This module never rebuilds or edits a challenger.  It only revalidates the
already evaluated content hash and either copies those exact content bytes into
a new immutable champion envelope or publishes immutable references to it.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

import jsonschema

from .diagnosis import load_history_series, verify_published_diagnosis
from .policy import PolicyError, _candidate, _canonical, _contained, _read_canonical_json, _validate_schema, load_policy, pareto_relation, validate_decision_disposition, verify_finalization_evidence
from .state_machine import State
from .store import DurableStore, StoreError
from .synthesis import _fsync, _fsync_tree_dirs, _inventory, _json, _sha, _walk, tree_hash


RECEIPT_SCHEMA = "finalization-receipt.schema.json"
DECISION_SCHEMA = "decision.schema.json"


class FinalizationError(RuntimeError):
    """A decision could not be applied exactly once and without mutation."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _receipt_id(value: Mapping[str, Any]) -> str:
    body = dict(value)
    body.pop("receipt_id", None)
    return f"fin-{_sha(_canonical(body))[:32]}"


class TransactionalFinalizer:
    """Apply one already-published Decision through an idempotent journal."""

    def __init__(
        self,
        root: str | Path,
        *,
        fault: Callable[[str], None] | None = None,
        clock: Callable[[], str] = _utc_now,
    ):
        self.root = Path(root).resolve()
        self.store = DurableStore(self.root)
        self.fault = fault
        self.clock = clock
        for relative in ("state/decisions", "state/locks", "versions/champion", "versions/pareto", "versions/rejected"):
            (self.root / relative).mkdir(parents=True, exist_ok=True)

    def _hit(self, stage: str) -> None:
        if self.fault:
            self.fault(stage)

    @contextmanager
    def _lock(self, run_id: str):
        path = _contained(self.root, f"state/locks/{run_id}.finalization.lock")
        with path.open("a+") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def _atomic(self, path: Path, data: bytes) -> None:
        descriptor, name = tempfile.mkstemp(prefix=".m10-", dir=path.parent)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            self._hit("after_file_fsync")
            os.replace(temporary, path)
            _fsync(path.parent)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _dir(self, run_id: str, cycle_id: int) -> Path:
        directory = _contained(self.root, f"state/decisions/{run_id}/c{cycle_id:04d}")
        directory.mkdir(parents=True, exist_ok=True)
        if directory.is_symlink():
            raise FinalizationError("finalization directory is unsafe")
        return directory

    def _journal(self, run_id: str, cycle_id: int) -> Path:
        return self._dir(run_id, cycle_id) / "transaction.json"

    def _receipt_path(self, run_id: str, cycle_id: int) -> Path:
        return self._dir(run_id, cycle_id) / "finalization-receipt.json"

    def _write_journal(self, run_id: str, cycle_id: int, value: Mapping[str, Any]) -> None:
        path = self._journal(run_id, cycle_id)
        body = dict(value)
        body["journal_hash"] = _sha(_canonical({key: val for key, val in body.items() if key != "journal_hash"}))
        self._atomic(path, _canonical(body))

    def _read_journal(self, run_id: str, cycle_id: int) -> dict[str, Any] | None:
        path = self._journal(run_id, cycle_id)
        if not path.exists():
            return None
        try:
            value = _read_canonical_json(path, "finalization journal")
        except PolicyError as exc:
            raise FinalizationError("finalization journal is invalid") from exc
        digest = value.get("journal_hash")
        expected = _sha(_canonical({key: val for key, val in value.items() if key != "journal_hash"}))
        if not isinstance(digest, str) or digest != expected:
            raise FinalizationError("finalization journal hash differs")
        return value

    def _load_decision(self, run_id: str, cycle_id: int) -> tuple[dict[str, Any], str]:
        locator = f"state/decisions/{run_id}/c{cycle_id:04d}/decision.json"
        try:
            decision = _read_canonical_json(_contained(self.root, locator, exists=True), "published decision")
            _validate_schema(self.root, DECISION_SCHEMA, decision)
            policy_hash = load_policy(self.root)[1]
        except PolicyError as exc:
            raise FinalizationError("published Decision cannot be revalidated") from exc
        digest = _sha(_canonical(decision))
        if (
            decision.get("run_id") != run_id or decision.get("cycle_id") != cycle_id
            or decision.get("policy_config_hash") != policy_hash
            or decision.get("content_modification_allowed") is not False
            or decision.get("authorized_by") != "M00"
        ):
            raise FinalizationError("Decision binding differs")
        expected_id = f"dec-{_sha(_canonical({key: value for key, value in decision.items() if key != 'decision_id'}))[:32]}"
        if decision.get("decision_id") != expected_id:
            raise FinalizationError("Decision content address differs")
        return decision, digest

    def _revalidate_evidence(self, decision: Mapping[str, Any], run_id: str, cycle_id: int) -> tuple[Any, dict[str, Any], Path]:
        try:
            series = load_history_series(self.root, run_id, cycle_id, store=self.store)
        except Exception as exc:
            raise FinalizationError("evaluation evidence cannot be revalidated") from exc
        if not series:
            raise FinalizationError("evaluation evidence is empty")
        record = series[-1]
        try:
            diagnosis, _ = verify_published_diagnosis(
                self.root, run_id, cycle_id, store=self.store, allow_m10_successor=True,
            )
        except Exception as exc:
            raise FinalizationError("diagnosis cannot be revalidated") from exc
        if (
            diagnosis.get("run_id") != run_id or diagnosis.get("cycle_id") != cycle_id
            or diagnosis.get("candidate_id") != record.candidate_id
            or diagnosis.get("candidate_content_hash") != record.candidate_content_hash
            or diagnosis.get("gate_report_id") != record.gate_report.get("report_id")
        ):
            raise FinalizationError("diagnosis binding differs")
        try:
            manifest, candidate_dir = _candidate(self.root, record.candidate_id, record.candidate_content_hash)
        except PolicyError as exc:
            raise FinalizationError("challenger bytes changed after evaluation") from exc
        try:
            validate_decision_disposition(self.root, decision, record, diagnosis)
        except PolicyError as exc:
            raise FinalizationError("Decision no longer matches the closed policy") from exc
        action = decision["action"]
        if action not in {"PAUSE", "ABORT_TECHNICAL"} and (
            decision.get("candidate_id") != record.candidate_id
            or decision.get("candidate_content_hash") != record.candidate_content_hash
            or decision.get("gate_report_id") != record.gate_report.get("report_id")
            or decision.get("diagnosis_id") != diagnosis.get("diagnosis_id")
        ):
            raise FinalizationError("Decision evidence differs from revalidated artifacts")
        if action == "PROMOTE" and not (
            record.gate_report.get("overall_pass") is True
            and record.correctness_math_pass is True
            and record.challenger_eligible is True
            and record.overall_outcome == "challenger_favored"
        ):
            raise FinalizationError("PROMOTE preconditions are no longer satisfied")
        if action == "FINALIZE" and not self._finalize_ready(decision, record, candidate_dir):
            raise FinalizationError("FINALIZE preconditions are not satisfied")
        if action == "ARCHIVE_PARETO" or (
            action == "REJECT" and decision.get("reason_code") == "PARETO_DOMINATED"
        ):
            try:
                observed_relation = pareto_relation(self.root, record)
            except PolicyError as exc:
                raise FinalizationError("Pareto frontier cannot be revalidated") from exc
            if decision.get("pareto_relation") != observed_relation:
                raise FinalizationError("Pareto frontier changed after Decision publication")
        return record, manifest, candidate_dir

    def _finalize_ready(self, decision: Mapping[str, Any], record: Any, candidate_dir: Path) -> bool:
        ids = decision.get("final_gate_report_ids")
        if not isinstance(ids, list) or not ids or not record.gate_report.get("overall_pass"):
            return False
        try:
            required_roles = load_policy(self.root)[0]["finalization_required_roles"]
            observed = verify_finalization_evidence(
                self.root, decision["run_id"], decision["cycle_id"], record,
                required_roles, expected_report_ids=ids,
            )
        except PolicyError:
            return False
        return observed == sorted(ids) and candidate_dir.is_dir()

    @staticmethod
    def _next_champion_id(base_candidate_id: str) -> str:
        match = re.fullmatch(r"v(\d{4,})", base_candidate_id)
        if match is None:
            raise FinalizationError("promotion base champion identifier is invalid")
        return f"v{(int(match.group(1)) + 1):0{len(match.group(1))}d}"

    def _read_pointer(self) -> dict[str, Any] | None:
        path = self.root / "versions" / "champion" / "current.json"
        if not path.exists():
            return None
        try:
            return _read_canonical_json(path, "champion pointer")
        except PolicyError as exc:
            raise FinalizationError("champion pointer is invalid") from exc

    def _copy_champion(self, decision: Mapping[str, Any], manifest: Mapping[str, Any], source: Path, applied_at: str) -> str:
        champion_root = self.root / "versions" / "champion"
        pointer = self._read_pointer()
        expected_previous = manifest.get("base_candidate_id")
        if not isinstance(expected_previous, str):
            raise FinalizationError("promotion base champion identity is absent")
        identifier = self._next_champion_id(expected_previous)
        destination = champion_root / identifier
        if pointer is not None and (
            pointer.get("candidate_id") == identifier
            and pointer.get("content_hash") == decision["candidate_content_hash"]
            and pointer.get("source_candidate_id") == decision["candidate_id"]
            and pointer.get("decision_id") == decision["decision_id"]
        ):
            try:
                existing = _read_canonical_json(destination / "manifest.json", "existing promoted champion")
            except PolicyError as exc:
                raise FinalizationError("promoted champion referenced by pointer is invalid") from exc
            if tree_hash(destination, exclude={"manifest.json"}) != existing.get("content_hash"):
                raise FinalizationError("promoted champion referenced by pointer changed")
            return f"versions/champion/{identifier}"
        if pointer is not None:
            if pointer.get("candidate_id") != expected_previous or pointer.get("content_hash") != manifest.get("base_hash"):
                raise FinalizationError("champion pointer compare-and-swap failed")
        elif not (champion_root / str(expected_previous)).is_dir():
            raise FinalizationError("base champion for promotion is absent")
        if destination.exists():
            try:
                existing = _read_canonical_json(destination / "manifest.json", "existing promoted champion")
            except PolicyError as exc:
                raise FinalizationError("existing promoted champion is invalid") from exc
            if (
                existing.get("candidate_id") != identifier
                or existing.get("content_hash") != decision["candidate_content_hash"]
                or tree_hash(destination, exclude={"manifest.json"}) != decision["candidate_content_hash"]
            ):
                raise FinalizationError("new champion version conflicts with this transaction")
            current = {
                "candidate_id": identifier, "content_hash": decision["candidate_content_hash"],
                "source_candidate_id": decision["candidate_id"],
                "decision_id": decision["decision_id"],
            }
            if self._read_pointer() != pointer:
                raise FinalizationError("champion pointer changed during promotion")
            self._atomic(champion_root / "current.json", _canonical(current))
            return f"versions/champion/{identifier}"
        stage = Path(tempfile.mkdtemp(prefix=f".m10-{identifier}-", dir=champion_root))
        try:
            for relative, source_path, info in _walk(source, {"manifest.json"}):
                target = stage / relative
                if stat.S_ISDIR(info.st_mode):
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source_path, target)
                    os.chmod(target, stat.S_IMODE(info.st_mode) & ~0o222)
                    _fsync(target)
            content_hash = tree_hash(stage)
            if content_hash != decision["candidate_content_hash"]:
                raise FinalizationError("promotion staging content differs from evaluated bytes")
            envelope = {
                "schema_version": "1.1.0", "candidate_id": identifier,
                "candidate_kind": "baseline", "run_id": decision["run_id"],
                "cycle_id": decision["cycle_id"], "base_candidate_id": None,
                "built_at": applied_at, "workspace_hash": content_hash,
                "content_hash": content_hash, "source_proposal_ids": [],
                "merge_receipt_locator": None, "immutable": True,
            }
            self._atomic(stage / "manifest.json", _canonical(envelope))
            _fsync_tree_dirs(stage)
            for _, path, info in _walk(stage):
                os.chmod(path, stat.S_IMODE(info.st_mode) & ~0o222)
            os.chmod(stage, stat.S_IMODE(stage.stat().st_mode) & ~0o222)
            _fsync_tree_dirs(stage)
            self._hit("before_destination_rename")
            os.replace(stage, destination)
            _fsync(champion_root)
            self._hit("after_destination_rename")
            current = {
                "candidate_id": identifier, "content_hash": content_hash,
                "source_candidate_id": decision["candidate_id"],
                "decision_id": decision["decision_id"],
            }
            if self._read_pointer() != pointer:
                raise FinalizationError("champion pointer changed during promotion")
            self._atomic(champion_root / "current.json", _canonical(current))
            self._hit("after_pointer_swap")
            return f"versions/champion/{identifier}"
        finally:
            if stage.exists():
                for base, dirs, files in os.walk(stage, topdown=False, followlinks=False):
                    for name in files:
                        os.chmod(Path(base) / name, 0o600)
                    for name in dirs:
                        os.chmod(Path(base) / name, 0o700)
                os.chmod(stage, 0o700)
                shutil.rmtree(stage)

    def _reference(self, category: str, decision: Mapping[str, Any], record: Any, applied_at: str) -> str:
        base = self.root / "versions" / category
        destination = base / str(record.candidate_id)
        reference = {
            "candidate_id": record.candidate_id,
            "candidate_content_hash": record.candidate_content_hash,
            "decision_id": decision["decision_id"], "action": decision["action"],
            "applied_at": applied_at,
            "reason_code": decision.get("reason_code"),
            "scores": dict(record.dimension_scores_challenger),
            "correctness_math_pass": bool(record.correctness_math_pass),
            "pareto_relation": decision.get("pareto_relation"),
        }
        if destination.exists():
            current = _read_canonical_json(destination / "reference.json", f"{category} reference")
            if current != reference:
                raise FinalizationError(f"conflicting {category} reference already exists")
            return f"versions/{category}/{record.candidate_id}"
        stage = Path(tempfile.mkdtemp(prefix=f".m10-{category}-", dir=base))
        try:
            self._atomic(stage / "reference.json", _canonical(reference))
            _fsync_tree_dirs(stage)
            os.chmod(stage / "reference.json", 0o444)
            os.chmod(stage, 0o555)
            _fsync_tree_dirs(stage)
            os.replace(stage, destination)
            _fsync(base)
            return f"versions/{category}/{record.candidate_id}"
        finally:
            if stage.exists():
                os.chmod(stage, 0o700)
                for child in stage.iterdir():
                    os.chmod(child, 0o600)
                shutil.rmtree(stage)

    def _apply_effect(self, decision: Mapping[str, Any], record: Any, manifest: Mapping[str, Any], candidate_dir: Path, applied_at: str) -> str | None:
        action = decision["action"]
        if action == "PROMOTE":
            return self._copy_champion(decision, manifest, candidate_dir, applied_at)
        if action == "ARCHIVE_PARETO":
            return self._reference("pareto", decision, record, applied_at)
        if action == "REJECT":
            return self._reference("rejected", decision, record, applied_at)
        if action == "REQUEST_EXTRA_JUDGMENT":
            path = self._dir(decision["run_id"], decision["cycle_id"]) / "extra-judgment.json"
            request = {"decision_id": decision["decision_id"], "evaluation_id": decision["inconclusive_evaluation_id"], "requested_at": applied_at}
            if path.exists() and _read_canonical_json(path, "extra judgment request") != request:
                raise FinalizationError("conflicting extra judgment request")
            if not path.exists():
                self._atomic(path, _canonical(request)); os.chmod(path, 0o444)
            return f"state/decisions/{decision['run_id']}/c{decision['cycle_id']:04d}/extra-judgment.json"
        if action == "ABORT_TECHNICAL":
            path = self._dir(decision["run_id"], decision["cycle_id"]) / "technical-checkpoint.json"
            checkpoint = decision.get("technical_checkpoint")
            if not isinstance(checkpoint, dict):
                raise FinalizationError("technical Decision has no bounded checkpoint")
            value = {
                "decision_id": decision["decision_id"], "attempt": checkpoint["attempt"],
                "limit": checkpoint["limit"], "retry_allowed": checkpoint["retry_allowed"],
                "backoff_seconds": checkpoint["backoff_seconds"], "checkpointed_at": applied_at,
            }
            if path.exists() and _read_canonical_json(path, "technical checkpoint") != value:
                raise FinalizationError("conflicting technical checkpoint")
            if not path.exists():
                self._atomic(path, _canonical(value)); os.chmod(path, 0o444)
            return f"state/decisions/{decision['run_id']}/c{decision['cycle_id']:04d}/technical-checkpoint.json"
        if action in {"REFOCUS_AND_CONTINUE", "CONTINUE_UNCHANGED"}:
            path = self._dir(decision["run_id"], decision["cycle_id"]) / "next-cycle.json"
            value = {"decision_id": decision["decision_id"], "action": action, "candidate_id": record.candidate_id, "prepared_at": applied_at}
            if path.exists() and _read_canonical_json(path, "next-cycle preparation") != value:
                raise FinalizationError("conflicting next-cycle preparation")
            if not path.exists():
                self._atomic(path, _canonical(value)); os.chmod(path, 0o444)
            return f"state/decisions/{decision['run_id']}/c{decision['cycle_id']:04d}/next-cycle.json"
        return None

    @staticmethod
    def _target(action: str) -> State:
        if action == "PAUSE":
            return State.PAUSED
        if action == "ABORT_TECHNICAL":
            return State.TECHNICAL_FAILURE
        if action == "FINALIZE":
            return State.FINALIZED
        return State.CYCLE_COMPLETE

    def _receipt(self, decision: Mapping[str, Any], record: Any, applied_at: str, destination: str | None, target: State) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": "1.1.0", "run_id": decision["run_id"],
            "cycle_id": decision["cycle_id"], "decision_id": decision["decision_id"],
            "candidate_id": record.candidate_id, "action": decision["action"],
            "applied_at": applied_at, "state_before": "COMMITTING",
            "state_after": target.value, "content_hash_before": record.candidate_content_hash,
            "content_hash_after": record.candidate_content_hash, "hash_revalidated": True,
            "atomic": True, "content_modified": False, "destination": destination,
        }
        value["receipt_id"] = _receipt_id(value)
        return value

    def _read_receipt(self, run_id: str, cycle_id: int) -> dict[str, Any] | None:
        path = self._receipt_path(run_id, cycle_id)
        if not path.exists():
            return None
        try:
            receipt = _read_canonical_json(path, "finalization receipt")
            _validate_schema(self.root, RECEIPT_SCHEMA, receipt)
        except PolicyError as exc:
            raise FinalizationError("finalization receipt is invalid") from exc
        if receipt.get("receipt_id") != _receipt_id(receipt):
            raise FinalizationError("finalization receipt content address differs")
        return receipt

    def finalize(self, run_id: str, *, cycle_id: int | None = None) -> dict[str, Any]:
        events = self.store.read_events(run_id)
        if not events:
            raise FinalizationError("run has no durable events")
        if cycle_id is None:
            cycle_id = events[-1]["cycle_id"]
        if isinstance(cycle_id, bool) or not isinstance(cycle_id, int) or cycle_id < 0:
            raise FinalizationError("cycle_id is invalid")
        with self._lock(run_id):
            events = self.store.read_events(run_id)
            current = State(events[-1]["state_to"])
            receipt = self._read_receipt(run_id, cycle_id)
            if receipt is not None:
                if receipt.get("run_id") != run_id or receipt.get("cycle_id") != cycle_id:
                    raise FinalizationError("receipt identity differs")
                target = State(receipt["state_after"])
                if current is target:
                    return receipt
                if current is not State.COMMITTING:
                    raise FinalizationError("receipt and durable state differ")
                decision, _ = self._load_decision(run_id, cycle_id)
                if receipt.get("decision_id") != decision.get("decision_id"):
                    raise FinalizationError("receipt decision binding differs")
                record, _, _ = self._revalidate_evidence(decision, run_id, cycle_id)
                expected_receipt = self._receipt(
                    decision, record, receipt["applied_at"], receipt["destination"], target,
                )
                if receipt != expected_receipt:
                    raise FinalizationError("recovered receipt differs from revalidated evidence")
                event = self.store.record(
                    run_id, target, event_id=f"finalization:{decision['decision_id']}:complete",
                    idempotency_key=f"finalization:{run_id}:c{cycle_id:04d}:complete", actor_id="M00",
                    event_type="FINALIZATION_APPLIED", payload={
                        "decision_id": decision["decision_id"], "receipt_id": receipt["receipt_id"],
                        "action": decision["action"], "destination": receipt["destination"],
                    }, artifact_hashes=[_sha(_canonical(receipt))],
                )
                if event["payload"].get("receipt_id") != receipt["receipt_id"]:
                    raise FinalizationError("recovered finalization event binding differs")
                self.store.checkpoint(run_id)
                return receipt
            if current not in {State.DECIDED, State.COMMITTING} or events[-1]["cycle_id"] != cycle_id:
                raise FinalizationError("finalizer requires DECIDED or recoverable COMMITTING state")
            decision, decision_hash = self._load_decision(run_id, cycle_id)
            journal = self._read_journal(run_id, cycle_id)
            if current is State.COMMITTING and (journal is None or journal.get("decision_id") != decision["decision_id"]):
                raise FinalizationError("COMMITTING state has no matching transaction journal")
            record, manifest, candidate_dir = self._revalidate_evidence(decision, run_id, cycle_id)
            applied_at = journal.get("applied_at") if journal else self.clock()
            if not isinstance(applied_at, str) or not applied_at:
                raise FinalizationError("transaction timestamp is invalid")
            journal = {
                "schema_version": "1.0.0", "run_id": run_id, "cycle_id": cycle_id,
                "decision_id": decision["decision_id"], "decision_hash": decision_hash,
                "action": decision["action"], "applied_at": applied_at, "phase": "PREPARED",
            }
            self._write_journal(run_id, cycle_id, journal)
            self._hit("after_prepared")
            if current is State.DECIDED:
                event = self.store.record(
                    run_id, State.COMMITTING, event_id=f"finalization:{decision['decision_id']}:committing",
                    idempotency_key=f"finalization:{run_id}:c{cycle_id:04d}:committing", actor_id="M00",
                    event_type="COMMITTING", payload={"decision_id": decision["decision_id"], "decision_hash": decision_hash},
                    artifact_hashes=[decision_hash],
                )
                if event["payload"].get("decision_hash") != decision_hash:
                    raise FinalizationError("COMMITTING event binding differs")
            journal["phase"] = "HASHES_REVALIDATED"
            self._write_journal(run_id, cycle_id, journal)
            self._hit("after_hashes_revalidated")
            destination = self._apply_effect(decision, record, manifest, candidate_dir, applied_at)
            journal["phase"] = "POINTER_SWAPPED" if decision["action"] == "PROMOTE" else "DESTINATION_STAGED"
            journal["destination"] = destination
            self._write_journal(run_id, cycle_id, journal)
            self._hit("after_destination_staged")
            target = self._target(decision["action"])
            receipt = self._receipt(decision, record, applied_at, destination, target)
            _validate_schema(self.root, RECEIPT_SCHEMA, receipt)
            receipt_path = self._receipt_path(run_id, cycle_id)
            if receipt_path.exists() and self._read_receipt(run_id, cycle_id) != receipt:
                raise FinalizationError("conflicting finalization receipt")
            if not receipt_path.exists():
                self._atomic(receipt_path, _canonical(receipt))
                os.chmod(receipt_path, 0o444)
            journal["phase"] = "EVENT_COMMITTED"
            self._write_journal(run_id, cycle_id, journal)
            self._hit("after_receipt")
            event = self.store.record(
                run_id, target, event_id=f"finalization:{decision['decision_id']}:complete",
                idempotency_key=f"finalization:{run_id}:c{cycle_id:04d}:complete", actor_id="M00",
                event_type="FINALIZATION_APPLIED", payload={
                    "decision_id": decision["decision_id"], "receipt_id": receipt["receipt_id"],
                    "action": decision["action"], "destination": destination,
                }, artifact_hashes=[_sha(_canonical(receipt))],
            )
            if event["payload"].get("receipt_id") != receipt["receipt_id"]:
                raise FinalizationError("finalization event binding differs")
            journal["phase"] = "CHECKPOINTED"
            self._write_journal(run_id, cycle_id, journal)
            self.store.checkpoint(run_id)
            self._hit("after_checkpoint")
            journal["phase"] = "COMPLETE"
            self._write_journal(run_id, cycle_id, journal)
            return receipt


def finalize_decision(root: str | Path, run_id: str, *, cycle_id: int | None = None, **kwargs: Any) -> dict[str, Any]:
    """Convenience API used by the JSON CLI and tests."""
    return TransactionalFinalizer(root, **kwargs).finalize(run_id, cycle_id=cycle_id)


__all__ = ["FinalizationError", "TransactionalFinalizer", "finalize_decision"]
