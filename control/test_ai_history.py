import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ai_history import _validated_timestamp, _strings, _text, load_entries
from ai_handoff_common import HandoffError

class TestAIHistoryValidators(unittest.TestCase):
    def test_validated_timestamp_valid(self):
        self.assertEqual(_validated_timestamp("2023-01-01T12:00:00Z"), "2023-01-01T12:00:00Z")
        self.assertEqual(_validated_timestamp("2023-01-01T12:00:00+00:00"), "2023-01-01T12:00:00Z")
        self.assertEqual(_validated_timestamp("2023-01-01T12:00:00-03:00"), "2023-01-01T12:00:00-03:00")

    def test_validated_timestamp_invalid(self):
        with self.assertRaises(HandoffError) as ctx:
            _validated_timestamp("invalid-date")
        self.assertIn("deve ser ISO 8601", str(ctx.exception))

        with self.assertRaises(HandoffError) as ctx:
            _validated_timestamp("2023-01-01T12:00:00")
        self.assertIn("deve conter fuso", str(ctx.exception))

    def test_strings_valid(self):
        self.assertEqual(_strings(None, "field"), [])
        self.assertEqual(_strings(["a", "b"], "field"), ["a", "b"])
        self.assertEqual(_strings([" a ", "b "], "field"), ["a", "b"])

    def test_strings_invalid(self):
        with self.assertRaises(HandoffError):
            _strings("not-a-list", "field")
        with self.assertRaises(HandoffError):
            _strings(["", "b"], "field")
        with self.assertRaises(HandoffError):
            _strings([1, "b"], "field")

    def test_text_valid(self):
        self.assertEqual(_text(None, "field"), None)
        self.assertEqual(_text(" valid ", "field"), "valid")

    def test_text_invalid(self):
        with self.assertRaises(HandoffError):
            _text(None, "field", required=True)
        with self.assertRaises(HandoffError):
            _text("", "field")
        with self.assertRaises(HandoffError):
            _text("   ", "field")
        with self.assertRaises(HandoffError):
            _text("a" * 20001, "field")

class TestAIHistoryLedger(unittest.TestCase):
    def test_load_entries_not_exists(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "missing.jsonl"
            self.assertEqual(load_entries(path), [])

    def test_load_entries_valid(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"
            path.write_text('{"session_id": "s1"}\n{"session_id": "s2"}\n')
            entries = load_entries(path)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0]["session_id"], "s1")

    def test_load_entries_truncated(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"
            path.write_bytes(b'{"session_id": "s1"}')
            with self.assertRaises(HandoffError) as ctx:
                load_entries(path)
            self.assertIn("sem newline final", str(ctx.exception))

    def test_load_entries_invalid_json(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"
            path.write_text('{"session_id": "s1"\n')
            with self.assertRaises(HandoffError) as ctx:
                load_entries(path)
            self.assertIn("inválido na linha", str(ctx.exception))

    def test_load_entries_missing_session_id(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"
            path.write_text('{"other": "value"}\n')
            with self.assertRaises(HandoffError) as ctx:
                load_entries(path)
            self.assertIn("entrada inválida no ledger", str(ctx.exception))

    def test_load_entries_duplicate_session_id(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ledger.jsonl"
            path.write_text('{"session_id": "s1"}\n{"session_id": "s1"}\n')
            with self.assertRaises(HandoffError) as ctx:
                load_entries(path)
            self.assertIn("duplicado no ledger", str(ctx.exception))


from ai_history import infer_milestone, _adr_headings, _delta_count, _delta_summary, render_history

class TestAIHistoryHelpers(unittest.TestCase):
    def test_infer_milestone(self):
        self.assertEqual(infer_milestone("feat: Marco 0 e 0.5"), "M0/M0.5")
        self.assertEqual(infer_milestone("fix: MARCO 1"), "M1")
        self.assertEqual(infer_milestone("M1 AND M1.1 setup"), "M1/M1.1")
        self.assertEqual(infer_milestone("M2 and M3"), "M2/M3")
        self.assertEqual(infer_milestone("BOOTSTRAP the project"), "M3")
        self.assertEqual(infer_milestone("Random commit"), "sem marco explícito")

    def test_adr_headings(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            docs = root / "docs"
            docs.mkdir()
            docs.joinpath("decisions.md").write_text("## ADR-001 — First\n## ADR-002 — Second\n")
            self.assertEqual(_adr_headings(root), ["ADR-001 — First", "ADR-002 — Second"])

        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(_adr_headings(Path(d)), [])

    def test_delta_count(self):
        delta = {"added": [1, 2], "modified": [1], "deleted": []}
        self.assertEqual(_delta_count(delta), 3)
        self.assertEqual(_delta_count({}), 0)

    def test_delta_summary(self):
        delta = {"added": [1, 2], "modified": [1], "deleted": []}
        self.assertEqual(_delta_summary(delta), "2 adicionados, 1 modificados, 0 removidos")

class TestAIHistoryRender(unittest.TestCase):
    def test_render_history_empty(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            snapshot = {"fingerprint": "123", "recorded_at": "2023-01-01T00:00:00Z", "files": {}}
            history = render_history(root, [], snapshot)
            self.assertIn("Repositório Git indisponível nesta cópia.", history)
            self.assertIn("Nenhuma ADR encontrada", history)
            self.assertIn("Nenhuma sessão estruturada foi registrada ainda.", history)

import argparse
from unittest.mock import patch, MagicMock
from io import StringIO
from ai_history import _entry_payload, main, parser

class TestAIHistoryCLI(unittest.TestCase):
    def test_entry_payload_args(self):
        args = argparse.Namespace(
            entry_file=None,
            stdin_json=False,
            summary="test summary",
            change=["c1", "c2"],
            decision=["d1"],
            validation=[],
            risk=["r1"],
            next_step=[]
        )
        payload = _entry_payload(args)
        self.assertEqual(payload["summary"], "test summary")
        self.assertEqual(payload["changes"], ["c1", "c2"])
        self.assertEqual(payload["decisions"], ["d1"])
        self.assertNotIn("validations", payload)
        self.assertEqual(payload["risks"], ["r1"])

    def test_entry_payload_stdin(self):
        args = argparse.Namespace(
            entry_file=None,
            stdin_json=True,
            summary=None,
            change=[],
            decision=[],
            validation=[],
            risk=[],
            next_step=[]
        )
        with patch('sys.stdin', StringIO('{"summary": "stdin summary", "changes": ["sc1"]}')):
            payload = _entry_payload(args)
            self.assertEqual(payload["summary"], "stdin summary")
            self.assertEqual(payload.get("changes"), ["sc1"])

    def test_entry_payload_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('{"summary": "file summary"}')
            f_path = f.name

        args = argparse.Namespace(
            entry_file=f_path,
            stdin_json=False,
            summary=None,
            change=[],
            decision=[],
            validation=[],
            risk=[],
            next_step=[]
        )
        payload = _entry_payload(args)
        self.assertEqual(payload["summary"], "file summary")
        Path(f_path).unlink()

    @patch('ai_history.update_history')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_success(self, mock_stdout, mock_update):
        mock_update.return_value = {"status": "recorded"}
        with patch('sys.argv', ['ai_history.py', '--root', '.', '--summary', 'test', '--auto']):
            self.assertEqual(main(['--root', '.', '--summary', 'test', '--auto']), 0)
            self.assertIn('"status": "recorded"', mock_stdout.getvalue())

    @patch('sys.stderr', new_callable=StringIO)
    def test_main_error(self, mock_stderr):
        self.assertEqual(main(['--root', '.', '--bootstrap-only', '--summary', 'should fail']), 2)
        self.assertIn('"status": "error"', mock_stderr.getvalue())
        self.assertIn("--bootstrap-only não aceita", mock_stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
