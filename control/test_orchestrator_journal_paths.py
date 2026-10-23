"""ADR-047: journal containment must reject even in-root and dangling links."""
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))
from article_loop.orchestrator import Orchestrator, OrchestrationError

class JournalPathTests(unittest.TestCase):
    def test_symlinked_journal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reader = Orchestrator(root)
            directory = root / 'state/orchestration/run'
            directory.mkdir(parents=True, exist_ok=True)
            journal = directory / 'journal.jsonl'
            target = root / "other.jsonl"
            for exists in (False, True):
                with self.subTest(target_exists=exists):
                    if exists:
                        target.write_bytes(b"")
                    journal.symlink_to(target)
                    with self.assertRaisesRegex(OrchestrationError, "symlink"):
                        reader._events("run")
                    journal.unlink()

    def test_traversal_and_partial_record_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reader = Orchestrator(root)
            for run in ("../escape", "run/child", ".", ".."):
                with self.subTest(run=run), self.assertRaises(OrchestrationError):
                    reader._events(run)
            directory = root / 'state/orchestration/run'
            directory.mkdir(parents=True, exist_ok=True)
            (directory / 'journal.jsonl').write_bytes(b"{}")
            with self.assertRaisesRegex(OrchestrationError, "partial"):
                reader._events("run")

    def test_symlinked_root_is_rejected_before_resolving(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            target.mkdir()
            root = Path(temporary) / "root"
            root.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(OrchestrationError, "symlink"):
                Orchestrator(root)

    def test_symlinked_parent_is_rejected_even_when_target_is_absent(self):
        for relative in ("state", "state/orchestration", "state/orchestration/run"):
            with self.subTest(parent=relative), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "root"
                root.mkdir()
                reader = Orchestrator(root)
                (root / "state/orchestration/run").mkdir(parents=True)
                directory = root / relative
                directory.rename(root / "saved-directory")
                directory.symlink_to(Path(temporary) / "root-escape", target_is_directory=True)
                with self.assertRaisesRegex(OrchestrationError, "symlink"):
                    reader._events("run")

    def test_special_journal_is_rejected_before_open(self):
        for kind in ("directory", "fifo"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                reader = Orchestrator(root)
                journal = reader._file("run", "journal.jsonl")
                if kind == "fifo":
                    os.mkfifo(journal)
                else:
                    journal.mkdir()
                with self.assertRaisesRegex(OrchestrationError, "regular file"):
                    reader._events("run")

    def test_malformed_json_and_hash_types_use_orchestration_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reader = Orchestrator(root)
            journal = reader._file("run", "journal.jsonl")
            event = reader._append("run", "STOPPED", "stop", {})
            malformed = [
                b'"\xff"\n', b'[' * 1024 + b'0' + b']' * 1024 + b'\n',
                json.dumps({**event, "at": "\ud800"}).encode() + b"\n",
            ]
            for value in (None, 0, [], {}):
                malformed.append(json.dumps({**event, "event_hash": value}).encode() + b"\n")
            for raw in malformed:
                with self.subTest(raw=raw):
                    journal.write_bytes(raw)
                    with self.assertRaises(OrchestrationError):
                        reader._events("run")

    def test_missing_journal_observation_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(Orchestrator(root)._events("run"), [])
            self.assertEqual(list(root.iterdir()), [])
