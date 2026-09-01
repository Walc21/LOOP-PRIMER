"""Deterministic local validation suite for M2 durable state and event store."""
from __future__ import annotations

import copy
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

from article_loop import (
    DurableStore,
    IntegrityError,
    State,
    StopRequested,
    StoreError,
    TransitionError,
)
from article_loop.store import _EVENT_SCHEMA_VERSION

SCHEMA_VERSION = _EVENT_SCHEMA_VERSION
TEST_ACTOR = "test-runner"


class M2DurableStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="test_m2_store_")
        self.root = Path(self.temp_dir)
        self.store = DurableStore(self.root)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _event_path(self, run_id: str) -> Path:
        return self.root / "state" / "events" / f"{run_id}.jsonl"

    def _snapshot_path(self, run_id: str) -> Path:
        return self.root / "state" / "snapshots" / f"{run_id}.json"

    def test_run_creation_initializes_empty_log_and_replays_new_state(self) -> None:
        run_id = "run-create-001"
        snapshot = self.store.create_run(run_id, actor_id=TEST_ACTOR)

        self.assertEqual(snapshot["run_id"], run_id)
        self.assertEqual(snapshot["state"], State.NEW.value)
        self.assertEqual(snapshot["cycle_id"], 0)
        self.assertEqual(snapshot["event_sequence"], 0)
        self.assertIsNotNone(snapshot["last_event_id"])
        self.assertIsNotNone(snapshot["last_event_hash"])

        events = self.store.read_events(run_id)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "RUN_CREATED")
        self.assertEqual(events[0]["state_to"], State.NEW.value)

    def test_record_appends_valid_transition_and_advances_sequence(self) -> None:
        run_id = "run-trans-001"
        self.store.create_run(run_id, actor_id=TEST_ACTOR)

        snap = self.store.record(
            run_id=run_id,
            target=State.INGESTED,
            event_id="evt-ingest-001",
            idempotency_key="idemp-ingest-001",
            actor_id=TEST_ACTOR,
            event_type="INGESTION_COMPLETED",
            payload={"pdf_hash": "a" * 64},
        )

        self.assertEqual(snap["state"], State.INGESTED.value)
        self.assertEqual(snap["event_sequence"], 1)

        events = self.store.read_events(run_id)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[1]["state_from"], State.NEW.value)
        self.assertEqual(events[1]["state_to"], State.INGESTED.value)
        self.assertEqual(events[1]["previous_event_hash"], events[0]["event_hash"])

    def test_invalid_state_transition_raises_transition_error_and_preserves_log(self) -> None:
        run_id = "run-invalid-001"
        self.store.create_run(run_id, actor_id=TEST_ACTOR)

        with self.assertRaises(TransitionError):
            self.store.record(
                run_id=run_id,
                target=State.GATES_PASSED,
                event_id="evt-invalid-001",
                idempotency_key="idemp-invalid-001",
                actor_id=TEST_ACTOR,
            )

        events = self.store.read_events(run_id)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["state_to"], State.NEW.value)

    def test_idempotent_event_replay_returns_existing_state_without_duplicating_log(self) -> None:
        run_id = "run-idemp-001"
        self.store.create_run(run_id, actor_id=TEST_ACTOR)

        snap1 = self.store.record(
            run_id=run_id,
            target=State.INGESTED,
            event_id="evt-001",
            idempotency_key="idemp-key-1",
            actor_id=TEST_ACTOR,
            event_type="INGEST_STEP",
        )

        snap2 = self.store.record(
            run_id=run_id,
            target=State.INGESTED,
            event_id="evt-001",
            idempotency_key="idemp-key-1",
            actor_id=TEST_ACTOR,
            event_type="INGEST_STEP",
        )

        self.assertEqual(snap1["snapshot_hash"], snap2["snapshot_hash"])
        events = self.store.read_events(run_id)
        self.assertEqual(len(events), 2)

    def test_stop_sentinel_blocks_mutating_operations(self) -> None:
        run_id = "run-stop-001"
        self.store.create_run(run_id, actor_id=TEST_ACTOR)

        stop_file = self.root / "control" / "STOP"
        stop_file.parent.mkdir(parents=True, exist_ok=True)
        stop_file.touch()

        with self.assertRaises(StopRequested):
            self.store.record(
                run_id=run_id,
                target=State.INGESTED,
                event_id="evt-stop-001",
                idempotency_key="idemp-stop-001",
                actor_id=TEST_ACTOR,
            )

        stop_file.unlink()

    def test_tampered_event_hash_raises_integrity_error(self) -> None:
        run_id = "run-tamper-001"
        self.store.create_run(run_id, actor_id=TEST_ACTOR)
        self.store.record(
            run_id=run_id,
            target=State.INGESTED,
            event_id="evt-tamper-1",
            idempotency_key="idemp-tamper-1",
            actor_id=TEST_ACTOR,
        )

        log_path = self._event_path(run_id)
        lines = log_path.read_text("utf-8").splitlines()
        first_evt = json.loads(lines[0])
        first_evt["event_hash"] = "0" * 64
        lines[0] = json.dumps(first_evt)
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        with self.assertRaises(IntegrityError):
            self.store.read_events(run_id)


if __name__ == "__main__":
    unittest.main()
