"""Tests for the 05_transactional_finalizer.py script."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

# Import the script as a module
import importlib.util
spec = importlib.util.spec_from_file_location("transactional_finalizer", SCRIPTS / "05_transactional_finalizer.py")
transactional_finalizer = importlib.util.module_from_spec(spec)
sys.modules["transactional_finalizer"] = transactional_finalizer
spec.loader.exec_module(transactional_finalizer)

from article_loop.finalization import FinalizationError

class TestTransactionalFinalizerScript(unittest.TestCase):
    def test_params_none_input(self):
        result = transactional_finalizer._params(None)
        self.assertEqual(result, {})

    @patch("sys.stdin", new_callable=io.StringIO)
    def test_params_stdin_valid(self, mock_stdin):
        mock_stdin.write('{"root": "/tmp", "run_id": "run-123", "cycle_id": 42}')
        mock_stdin.seek(0)
        result = transactional_finalizer._params("-")
        self.assertEqual(result, {"root": "/tmp", "run_id": "run-123", "cycle_id": 42})

    def test_params_file_valid(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write('{"run_id": "run-456"}')
            temp_path = f.name
        try:
            result = transactional_finalizer._params(temp_path)
            self.assertEqual(result, {"run_id": "run-456"})
        finally:
            Path(temp_path).unlink()

    @patch("sys.stdin", new_callable=io.StringIO)
    def test_params_invalid_json_type(self, mock_stdin):
        mock_stdin.write('["not", "a", "dict"]')
        mock_stdin.seek(0)
        with self.assertRaisesRegex(ValueError, "input JSON must be an object"):
            transactional_finalizer._params("-")

    @patch("sys.stdin", new_callable=io.StringIO)
    def test_params_unsupported_keys(self, mock_stdin):
        mock_stdin.write('{"run_id": "run-123", "unsupported_key": "value"}')
        mock_stdin.seek(0)
        with self.assertRaisesRegex(ValueError, "input JSON has unsupported parameters"):
            transactional_finalizer._params("-")

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.stderr", new_callable=io.StringIO)
    @patch("transactional_finalizer.finalize_decision")
    def test_main_success(self, mock_finalize, mock_stderr, mock_stdout):
        mock_finalize.return_value = {"tx_hash": "abc"}

        test_args = ["05_transactional_finalizer.py", "--run-id", "test-run", "--cycle-id", "5"]
        with patch.object(sys, "argv", test_args):
            return_code = transactional_finalizer.main()

        self.assertEqual(return_code, 0)
        output = json.loads(mock_stdout.getvalue())
        self.assertEqual(output["status"], "success")
        self.assertEqual(output["receipt"], {"tx_hash": "abc"})
        self.assertEqual(mock_stderr.getvalue(), "")
        mock_finalize.assert_called_once()
        self.assertEqual(mock_finalize.call_args[0][1], "test-run")
        self.assertEqual(mock_finalize.call_args[1]["cycle_id"], 5)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_main_missing_run_id(self, mock_stderr, mock_stdout):
        # By default, argparse arguments run_id is None unless specified
        test_args = ["05_transactional_finalizer.py"]
        with patch.object(sys, "argv", test_args):
            return_code = transactional_finalizer.main()

        self.assertEqual(return_code, 1)
        output = json.loads(mock_stderr.getvalue())
        self.assertEqual(output["status"], "error")
        self.assertEqual(output["error_type"], "input_error")
        self.assertIn("run_id is required", output["message"])

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_main_invalid_cycle_id(self, mock_stderr, mock_stdout):
        # We need to bypass argparse's type=int to test the validation logic
        # by passing it through stdin params
        test_args = ["05_transactional_finalizer.py", "--input", "-"]
        with patch.object(sys, "argv", test_args):
            with patch("sys.stdin", new_callable=io.StringIO) as mock_stdin:
                mock_stdin.write('{"run_id": "test", "cycle_id": -1}')
                mock_stdin.seek(0)
                return_code = transactional_finalizer.main()

        self.assertEqual(return_code, 1)
        output = json.loads(mock_stderr.getvalue())
        self.assertEqual(output["status"], "error")
        self.assertEqual(output["error_type"], "input_error")
        self.assertIn("cycle_id must be a non-negative integer", output["message"])

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.stderr", new_callable=io.StringIO)
    @patch("transactional_finalizer.finalize_decision")
    def test_main_finalization_error(self, mock_finalize, mock_stderr, mock_stdout):
        mock_finalize.side_effect = FinalizationError("Something went wrong")

        test_args = ["05_transactional_finalizer.py", "--run-id", "test-run"]
        with patch.object(sys, "argv", test_args):
            return_code = transactional_finalizer.main()

        self.assertEqual(return_code, 2)
        output = json.loads(mock_stderr.getvalue())
        self.assertEqual(output["status"], "error")
        self.assertEqual(output["error_type"], "finalization_error")
        self.assertEqual(output["message"], "Something went wrong")

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.stderr", new_callable=io.StringIO)
    @patch("transactional_finalizer.finalize_decision")
    def test_main_unexpected_error(self, mock_finalize, mock_stderr, mock_stdout):
        mock_finalize.side_effect = Exception("Boom!")

        test_args = ["05_transactional_finalizer.py", "--run-id", "test-run"]
        with patch.object(sys, "argv", test_args):
            return_code = transactional_finalizer.main()

        self.assertEqual(return_code, 3)
        output = json.loads(mock_stderr.getvalue())
        self.assertEqual(output["status"], "error")
        self.assertEqual(output["error_type"], "unexpected_error")
        self.assertEqual(output["message"], "Boom!")

if __name__ == "__main__":
    unittest.main()
