"""Offline regression tests for the Marco 2 durable-state core."""

from __future__ import annotations

import json
import errno
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))

from article_loop import DurableStore, IntegrityError, State, StopRequested, StoreError, TransitionError
from article_loop.store import _DIRECTORY_FSYNC_UNSUPPORTED_ERRNOS
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

    def forged_events(self, mutate):
        """Apply a mutation while retaining a valid hash chain."""
        log = self.root / "state/events/run-1.jsonl"
        events = [json.loads(line) for line in log.read_text().splitlines()]
        mutate(events)
        previous = None
        for event in events:
            event["previous_event_hash"] = previous
            event["event_hash"] = self.store._ehash(event)
            previous = event["event_hash"]
        log.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events))

    def assert_record_rejected_without_log(self, **overrides):
        values = {
            "event_id": "event-1", "idempotency_key": "key-1", "actor_id": "test",
            "event_type": "STATE_RECORDED", "artifact_hashes": [], "initial": True,
        }
        values.update(overrides)
        with self.assertRaises(StoreError):
            self.store.record("run-1", State.NEW, **values)
        self.assertFalse((self.root / "state/events/run-1.jsonl").exists())

    def test_directory_fsync_tolerates_only_documented_unsupported_errors(self):
        self.assertEqual(
            _DIRECTORY_FSYNC_UNSUPPORTED_ERRNOS,
            frozenset({errno.EINVAL, errno.ENOTSUP, getattr(errno, "EOPNOTSUPP", errno.ENOTSUP)}),
        )
        with (
            mock.patch("article_loop.store.os.open", return_value=17),
            mock.patch("article_loop.store.os.fsync", side_effect=OSError(errno.EINVAL, "unsupported")),
            mock.patch("article_loop.store.os.close"),
        ):
            self.store._fsync_directory(self.root)

        with (
            mock.patch("article_loop.store.os.open", return_value=17),
            mock.patch("article_loop.store.os.fsync", side_effect=OSError(errno.EIO, "disk failure")),
            mock.patch("article_loop.store.os.close"),
        ):
            with self.assertRaises(OSError) as raised:
                self.store._fsync_directory(self.root)
        self.assertEqual(raised.exception.errno, errno.EIO)

    def test_directory_fsync_io_error_fails_atomic_publication(self):
        target = self.root / "state" / "events" / "publication.json"
        with mock.patch.object(
            self.store, "_fsync_directory", side_effect=OSError(errno.EIO, "disk failure"),
        ):
            with self.assertRaises(OSError) as raised:
                self.store._atomic_bytes(target, b"durable payload")
        self.assertEqual(raised.exception.errno, errno.EIO)

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
        self.assertTrue(is_valid_transition(State.COMMITTING, State.FINALIZED))

    def test_all_invalid_transitions(self):
        allowed = {(current, target) for current, target in FORWARD.items()}
        allowed |= {(current, State.PAUSED) for current in State if current not in {State.PAUSED, State.FINALIZED, State.TECHNICAL_FAILURE}}
        allowed |= {(current, State.TECHNICAL_FAILURE) for current in State if current not in {State.FINALIZED, State.TECHNICAL_FAILURE}}
        allowed |= {(State.CYCLE_COMPLETE, State.CYCLE_PLANNED), (State.CYCLE_COMPLETE, State.FINALIZED), (State.COMMITTING, State.FINALIZED)}
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

    def test_crash_before_rename_leaves_prior_log_valid(self):
        def fault(stage):
            if stage == "after_fsync_before_rename":
                raise RuntimeError("simulated crash")

        crashing = DurableStore(self.root, fault=fault)
        with self.assertRaisesRegex(RuntimeError, "simulated crash"):
            crashing.create_run("run-1")
        recovered = DurableStore(self.root)
        self.assertEqual(recovered.read_events("run-1"), [])
        self.assertEqual(recovered.create_run("run-1")["sequence"], 0)

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

    def test_semantic_replay_rejects_forged_hash_valid_logs(self):
        cases = {
            "new_to_finalized": lambda events: events[1].update(state_to=State.FINALIZED.value),
            "divergent_state_from": lambda events: events[1].update(state_from=State.SOURCE_READY.value),
            "changed_cycle": lambda events: events[1].update(cycle_id=1),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name):
                self.created()
                self.event(State.INGESTED)
                self.forged_events(mutate)
                with self.assertRaises(IntegrityError):
                    self.store.read_events("run-1")
                self.temporary.cleanup()
                self.setUp()

    def test_semantic_replay_rejects_invalid_initial_event(self):
        self.created()
        self.forged_events(lambda events: events[0].update(state_to=State.INGESTED.value))
        with self.assertRaises(IntegrityError):
            self.store.read_events("run-1")

    def test_semantic_replay_rejects_forged_pause_and_resume(self):
        self.created()
        self.event(State.INGESTED)
        self.store.pause("run-1", event_id="pause", idempotency_key="pause", actor_id="test")
        self.forged_events(lambda events: events[2]["payload"].update(resume_state=State.NEW.value))
        with self.assertRaises(IntegrityError):
            self.store.read_events("run-1")

        self.temporary.cleanup()
        self.setUp()
        self.created()
        self.event(State.INGESTED)
        self.store.pause("run-1", event_id="pause", idempotency_key="pause", actor_id="test")
        self.store.resume("run-1", event_id="resume", idempotency_key="resume", actor_id="test")
        self.forged_events(lambda events: events[3].update(state_to=State.SOURCE_READY.value))
        with self.assertRaises(IntegrityError):
            self.store.read_events("run-1")

    def test_semantic_replay_rejects_event_after_terminal_state(self):
        self.advance_to(State.CYCLE_COMPLETE)
        self.event(State.FINALIZED)
        log = self.root / "state/events/run-1.jsonl"
        events = [json.loads(line) for line in log.read_text().splitlines()]
        terminal = dict(events[-1])
        terminal.update(
            event_id="after-terminal", idempotency_key="after-terminal",
            state_from=State.FINALIZED.value, state_to=State.TECHNICAL_FAILURE.value,
            sequence=len(events), previous_event_hash=events[-1]["event_hash"],
        )
        terminal["event_hash"] = self.store._ehash(terminal)
        log.write_text(log.read_text() + json.dumps(terminal, sort_keys=True) + "\n")
        with self.assertRaises(IntegrityError):
            self.store.read_events("run-1")

    def test_event_commit_faults_are_recoverable_and_idempotent(self):
        stages = {
            "before_temp_write": False,
            "during_preparation": False,
            "after_fsync_before_rename": False,
            "after_rename": True,
            "before_final_verification": True,
        }
        for stage, committed in stages.items():
            with self.subTest(stage=stage):
                def fault(current_stage, expected=stage):
                    if current_stage == expected:
                        raise RuntimeError(expected)

                crashing = DurableStore(self.root, fault=fault)
                with self.assertRaisesRegex(RuntimeError, stage):
                    crashing.create_run("run-1")
                log = self.root / "state/events/run-1.jsonl"
                if log.exists():
                    self.assertTrue(log.read_bytes().endswith(b"\n"))
                events = DurableStore(self.root).read_events("run-1")
                self.assertEqual(len(events), int(committed))
                event = DurableStore(self.root).create_run("run-1")
                self.assertEqual(event["sequence"], 0)
                self.assertEqual(len(DurableStore(self.root).read_events("run-1")), 1)
                self.temporary.cleanup()
                self.setUp()

    def test_record_rejects_empty_event_id_without_log_change(self):
        self.assert_record_rejected_without_log(event_id="")

    def test_record_rejects_empty_idempotency_key_without_log_change(self):
        self.assert_record_rejected_without_log(idempotency_key="")

    def test_record_rejects_oversized_idempotency_key_without_log_change(self):
        self.assert_record_rejected_without_log(idempotency_key="x" * 257)

    def test_record_rejects_empty_actor_id_without_log_change(self):
        self.assert_record_rejected_without_log(actor_id="")

    def test_record_rejects_empty_event_type_without_log_change(self):
        self.assert_record_rejected_without_log(event_type="")

    def test_record_rejects_invalid_artifact_hash_without_log_change(self):
        self.assert_record_rejected_without_log(artifact_hashes=["not-a-hash"])

    def test_record_rejects_duplicate_artifact_hash_without_log_change(self):
        digest = "a" * 64
        self.assert_record_rejected_without_log(artifact_hashes=[digest, digest])

    def test_replay_rejects_unknown_schema_version_with_valid_hash_chain(self):
        self.created()
        self.forged_events(lambda events: events[0].update(schema_version="9.9.9"))
        with self.assertRaises(IntegrityError):
            self.store.read_events("run-1")

    def test_replay_rejects_invalid_occurred_at_with_valid_hash_chain(self):
        self.created()
        self.forged_events(lambda events: events[0].update(occurred_at="not-a-timestamp"))
        with self.assertRaises(IntegrityError):
            self.store.read_events("run-1")

    def test_replay_rejects_duplicate_artifact_hash_with_valid_hash_chain(self):
        self.created()
        digest = "a" * 64
        self.forged_events(lambda events: events[0].update(artifact_hashes=[digest, digest]))
        with self.assertRaises(IntegrityError):
            self.store.read_events("run-1")

    def test_replay_rejects_boolean_sequence_or_cycle_id_with_valid_hash_chain(self):
        for field in ("sequence", "cycle_id"):
            with self.subTest(field=field):
                self.created()
                self.forged_events(lambda events, field=field: events[0].update({field: True}))
                with self.assertRaises(IntegrityError):
                    self.store.read_events("run-1")
                self.temporary.cleanup()
                self.setUp()

    def test_replay_rejects_additional_property_with_valid_hash_chain(self):
        self.created()
        self.forged_events(lambda events: events[0].update(unexpected="forged"))
        with self.assertRaises(IntegrityError):
            self.store.read_events("run-1")


if __name__ == "__main__":
    unittest.main()
