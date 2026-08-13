"""Offline regression tests for the Marco 2 durable-state core."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))

from article_loop import DurableStore, IntegrityError, State, StopRequested, StoreError, TransitionError
from article_loop.state_machine import is_valid_transition


FORWARD = {
    State.NEW: State.INGESTED,
    State.INGESTED: State.SOURCE_READY,
    State.SOURCE_READY: State.CYCLE_PLANNED,
    State.CYCLE_PLANNED: State.DEPARTMENTS_RUNNING,
    State.DEPARTMENTS_RUNNING: State.SYNTHESIS_READY,
    State.SYNTHESIS_READY: State.CANDIDATE_BUILT,
    State.CANDIDATE_BUILT: State.GATES_PASSED,
    State.GATES_PASSED: State.EVALUATED,
    State.EVALUATED: State.DIAGNOSED,
    State.DIAGNOSED: State.DECIDED,
    State.DECIDED: State.COMMITTING,
    State.COMMITTING: State.CYCLE_COMPLETE,
}


class DurableStateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "control").mkdir()
        self.store = DurableStore(self.root)
        self.counter = 0

    def tearDown(self):
        self.temporary.cleanup()

    def event(self, target: State, run_id: str = "run-1"):
        self.counter += 1
        return self.store.record(
            run_id, target, event_id=f"event-{self.counter}",
            idempotency_key=f"key-{self.counter}", actor_id="test",
        )

    def created(self, run_id: str = "run-1"):
        return self.store.create_run(run_id, actor_id="test")

    def advance_to(self, target: State, run_id: str = "run-1"):
        self.created(run_id)
        current = State.NEW
        while current is not target:
            current = FORWARD[current]
            self.event(current, run_id)

    def test_all_valid_transitions(self):
        for current, target in FORWARD.items():
            with self.subTest(current=current, target=target):
                self.assertTrue(is_valid_transition(current, target))
        for current in set(State) - {State.FINALIZED, State.TECHNICAL_FAILURE, State.PAUSED}:
            with self.subTest(current=current, target=State.PAUSED):
                self.assertTrue(is_valid_transition(current, State.PAUSED))
            with self.subTest(current=current, target=State.TECHNICAL_FAILURE):
                self.assertTrue(is_valid_transition(current, State.TECHNICAL_FAILURE))
        for resume_state in set(State) - {State.PAUSED, State.FINALIZED, State.TECHNICAL_FAILURE}:
            with self.subTest(resume_state=resume_state):
                self.assertTrue(is_valid_transition(State.PAUSED, resume_state, resume_to=resume_state))
        self.assertTrue(is_valid_transition(State.PAUSED, State.TECHNICAL_FAILURE, resume_to=State.NEW))
        self.assertTrue(is_valid_transition(State.CYCLE_COMPLETE, State.CYCLE_PLANNED))
        self.assertTrue(is_valid_transition(State.CYCLE_COMPLETE, State.FINALIZED))

    def test_all_invalid_transitions(self):
        allowed = {(current, target) for current, target in FORWARD.items()}
        allowed |= {(current, State.PAUSED) for current in State if current not in {State.PAUSED, State.FINALIZED, State.TECHNICAL_FAILURE}}
        allowed |= {(current, State.TECHNICAL_FAILURE) for current in State if current not in {State.FINALIZED, State.TECHNICAL_FAILURE}}
        allowed |= {(State.CYCLE_COMPLETE, State.CYCLE_PLANNED), (State.CYCLE_COMPLETE, State.FINALIZED)}
        allowed.add((State.PAUSED, State.NEW))
        for current in State:
            for target in State:
                expected = (current, target) in allowed
                actual = is_valid_transition(current, target, resume_to=State.NEW)
                with self.subTest(current=current, target=target):
                    self.assertEqual(actual, expected)
        self.assertFalse(is_valid_transition(State.PAUSED, State.INGESTED, resume_to=State.NEW))
        self.assertFalse(is_valid_transition(State.PAUSED, State.NEW))

    def test_full_event_log_replay_and_snapshot_reconstruction(self):
        self.created()
        for target in FORWARD.values():
            self.event(target)
        self.event(State.CYCLE_PLANNED)
        events = self.store.read_events("run-1")
        rebuilt = DurableStore(self.root).rebuild_snapshot("run-1")
        self.assertEqual(len(events), 14)
        self.assertEqual(rebuilt["state"], State.CYCLE_PLANNED)
        self.assertEqual(rebuilt["event_sequence"], 13)
        self.assertEqual(rebuilt["last_event_hash"], events[-1]["event_hash"])

    def test_duplicate_event_id_and_idempotency_conflict(self):
        self.created()
        self.event(State.INGESTED)
        with self.assertRaises(StoreError):
            self.store.record("run-1", State.SOURCE_READY, event_id="event-1", idempotency_key="another", actor_id="test")
        with self.assertRaises(StoreError):
            self.store.record("run-1", State.SOURCE_READY, event_id="another", idempotency_key="key-1", actor_id="test")

    def test_partially_written_file_and_truncated_jsonl_are_rejected(self):
        self.created()
        log = self.root / "state/events/run-1.jsonl"
        with log.open("ab") as stream:
            stream.write(b'{"event_id":"unfinished"')
        with self.assertRaisesRegex(IntegrityError, "partial event line"):
            self.store.read_events("run-1")

    def test_corrupted_jsonl_is_rejected(self):
        self.created()
        log = self.root / "state/events/run-1.jsonl"
        with log.open("ab") as stream:
            stream.write(b"not-json\n")
        with self.assertRaisesRegex(IntegrityError, "invalid event JSON"):
            self.store.read_events("run-1")

    def test_crash_before_rename_leaves_replayable_log(self):
        def fault(stage):
            if stage == "before_rename":
                raise RuntimeError("simulated crash")

        crashing = DurableStore(self.root, fault=fault)
        with self.assertRaisesRegex(RuntimeError, "simulated crash"):
            crashing.create_run("run-1")
        recovered = DurableStore(self.root)
        self.assertEqual(recovered.read_events("run-1")[0]["state_to"], State.NEW)
        self.assertEqual(recovered.rebuild_snapshot("run-1")["event_sequence"], 0)

    def test_crash_after_rename_is_idempotently_recoverable(self):
        def fault(stage):
            if stage == "after_rename":
                raise RuntimeError("simulated crash")

        crashing = DurableStore(self.root, fault=fault)
        with self.assertRaisesRegex(RuntimeError, "simulated crash"):
            crashing.create_run("run-1")
        recovered = DurableStore(self.root)
        event = recovered.create_run("run-1")
        self.assertEqual(event["sequence"], 0)
        self.assertEqual(recovered.snapshot("run-1")["state"], State.NEW)

    def test_two_concurrent_writers_same_run_are_serialized(self):
        barrier = threading.Barrier(2)
        results, failures = [], []

        def writer():
            try:
                barrier.wait()
                results.append(DurableStore(self.root).create_run("run-1"))
            except Exception as error:  # test must report unexpected worker errors
                failures.append(error)

        threads = [threading.Thread(target=writer) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(failures, [])
        self.assertEqual([event["sequence"] for event in results], [0, 0])
        self.assertEqual(len(self.store.read_events("run-1")), 1)

    def test_hash_corruption_is_rejected(self):
        self.created()
        log = self.root / "state/events/run-1.jsonl"
        event = json.loads(log.read_text().strip())
        event["event_hash"] = "0" * 64
        log.write_text(json.dumps(event) + "\n")
        with self.assertRaisesRegex(IntegrityError, "event hash mismatch"):
            self.store.read_events("run-1")

    def test_checkpoint_pause_resume_and_safe_stop(self):
        self.created()
        self.event(State.INGESTED)
        checkpoint = self.store.checkpoint("run-1")
        self.assertTrue((self.root / "state/checkpoints/run-1-1.json").is_file())
        self.assertEqual(checkpoint["event_sequence"], 1)
        self.store.pause("run-1", event_id="pause", idempotency_key="pause", actor_id="test")
        resumed = self.store.resume("run-1", event_id="resume", idempotency_key="resume", actor_id="test")
        self.assertEqual(resumed["state_to"], State.INGESTED)
        (self.root / "control/STOP").write_text("operator stop\n")
        with self.assertRaises(StopRequested):
            self.event(State.SOURCE_READY)
        self.assertEqual(self.store.snapshot("run-1")["state"], State.INGESTED)

    def test_path_traversal_is_rejected(self):
        for run_id in ("../outside", "nested/run", ".", "..", "/absolute"):
            with self.subTest(run_id=run_id), self.assertRaises(StoreError):
                self.store.create_run(run_id)

    def test_idempotency_survives_restart(self):
        initial = self.created()
        restarted = DurableStore(self.root).create_run("run-1")
        self.assertEqual(restarted, initial)
        self.assertEqual(len(DurableStore(self.root).read_events("run-1")), 1)


if __name__ == "__main__":
    unittest.main()
