"""ADR-047: journal containment must reject even in-root and dangling links."""
from pathlib import Path
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))
from article_loop.store import DurableStore, StoreError

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
            with self.assertRaisesRegex(Exception, "partial"):
                reader.read_events("run")
