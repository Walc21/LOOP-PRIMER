"""ADR-047: journal containment must reject even in-root and dangling links."""
from pathlib import Path
import os
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))
from article_loop.store import DurableStore, IntegrityError, StoreError

class JournalPathTests(unittest.TestCase):
    def test_symlinked_journal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reader = DurableStore(root)
            directory = root / 'state/events'
            directory.mkdir(parents=True, exist_ok=True)
            journal = directory / 'run.jsonl'
            target = root / "other.jsonl"
            for exists in (False, True):
                with self.subTest(target_exists=exists):
                    if exists:
                        target.write_bytes(b"")
                    journal.symlink_to(target)
                    with self.assertRaisesRegex(StoreError, "symlink"):
                        reader.read_events("run")
                    journal.unlink()

    def test_traversal_and_partial_record_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reader = DurableStore(root)
            for run in ("../escape", "run/child", ".", ".."):
                with self.subTest(run=run), self.assertRaises(StoreError):
                    reader.read_events(run)
            directory = root / 'state/events'
            directory.mkdir(parents=True, exist_ok=True)
            (directory / 'run.jsonl').write_bytes(b"{}")
            with self.assertRaisesRegex(IntegrityError, "partial"):
                reader.read_events("run")

    def test_symlinked_parent_is_rejected_even_when_target_is_absent(self):
        for relative in ("state", "state/events"):
            with self.subTest(parent=relative), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "root"
                root.mkdir()
                reader = DurableStore(root)
                directory = root / relative
                directory.rename(root / "saved-directory")
                directory.symlink_to(Path(temporary) / "root-escape", target_is_directory=True)
                with self.assertRaisesRegex(StoreError, "symlink"):
                    reader.read_events("run")

    def test_special_journal_is_rejected_before_open(self):
        for kind in ("directory", "fifo"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                reader = DurableStore(root)
                journal = root / "state/events/run.jsonl"
                if kind == "fifo":
                    os.mkfifo(journal)
                else:
                    journal.mkdir()
                with self.assertRaisesRegex(StoreError, "regular file"):
                    reader.read_events("run")

    def test_malformed_json_uses_integrity_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reader = DurableStore(root)
            for raw in (b'"\xff"\n', b'[' * 1024 + b'0' + b']' * 1024 + b'\n'):
                with self.subTest(raw=raw[:20]):
                    (root / "state/events/run.jsonl").write_bytes(raw)
                    with self.assertRaises(IntegrityError):
                        reader.read_events("run")

    def test_missing_journal_observation_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reader = DurableStore(root, read_only=True)
            self.assertEqual(reader.read_events("run"), [])
            self.assertEqual(list(root.iterdir()), [])
