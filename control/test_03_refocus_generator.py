"""Tests for the M9 Prompt Refocus Generator CLI."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime/agent/skills/article-loop/src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop.refocus import RefocusError
import importlib.util

# Load the script as a module so we can mock generate_refocus_plan
spec = importlib.util.spec_from_file_location("refocus_generator", str(ROOT / "scripts/03_refocus_generator.py"))
refocus_generator = importlib.util.module_from_spec(spec)
sys.modules["refocus_generator"] = refocus_generator
spec.loader.exec_module(refocus_generator)


class TestRefocusGeneratorCLI(unittest.TestCase):
    """Test suite for the 03_refocus_generator.py CLI script."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.script_path = str(ROOT / "scripts/03_refocus_generator.py")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _run_cli(self, *args, input_data=None, check=False):
        """Helper to run the CLI script via subprocess."""
        cmd = [sys.executable, self.script_path, "--root", str(self.root)] + list(args)
        kwargs = {"capture_output": True, "text": True, "check": check}
        if input_data is not None:
            kwargs["input"] = input_data
        return subprocess.run(cmd, **kwargs)

    def test_input_parsing_error_invalid_json(self):
        """Test with invalid JSON input via stdin."""
        result = self._run_cli("--input", "-", input_data="invalid json")
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stderr)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "input_parsing_error")

    def test_input_parsing_error_not_object(self):
        """Test with JSON array instead of object via stdin."""
        result = self._run_cli("--input", "-", input_data="[]")
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stderr)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "input_parsing_error")
        self.assertIn("must be an object", data["message"])

    def test_invalid_root_parameter(self):
        """Test missing or invalid root parameter via input."""
        result = self._run_cli("--input", "-", input_data='{"root": ""}')
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stderr)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "invalid_parameter")
        self.assertIn("root must be a non-empty", data["message"])

    def test_missing_run_id(self):
        """Test missing --run-id parameter."""
        result = self._run_cli("--cycle-id", "0")
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stderr)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "missing_parameter")

    def test_invalid_cycle_id(self):
        """Test invalid --cycle-id (negative)."""
        result = self._run_cli("--run-id", "run123", "--cycle-id", "-1")
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stderr)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "invalid_parameter")
        self.assertIn("cycle-id must be a non-negative integer", data["message"])

    def test_invalid_diagnosis_locator(self):
        """Test diagnosis-locator that does not match canonical format."""
        result = self._run_cli("--run-id", "run123", "--cycle-id", "0", "--diagnosis-locator", "invalid/path.json")
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stderr)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "invalid_parameter")
        self.assertIn("must identify the canonical diagnosis", data["message"])

    def test_file_not_found_specified_locator(self):
        """Test specified canonical diagnosis locator does not exist."""
        canonical = "state/diagnosis/run123/c0000/diagnosis.json"
        result = self._run_cli("--run-id", "run123", "--cycle-id", "0", "--diagnosis-locator", canonical)
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stderr)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "file_not_found")

    def test_json_parse_error_specified_locator(self):
        """Test specified canonical diagnosis locator exists but is invalid JSON."""
        canonical = "state/diagnosis/run123/c0000/diagnosis.json"
        path = self.root / canonical
        path.parent.mkdir(parents=True)
        path.write_text("invalid json")

        result = self._run_cli("--run-id", "run123", "--cycle-id", "0", "--diagnosis-locator", canonical)
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stderr)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "json_parse_error")

    def test_diagnosis_not_found_default_locator(self):
        """Test default locator does not exist."""
        result = self._run_cli("--run-id", "run123", "--cycle-id", "0")
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stderr)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "diagnosis_not_found")

    def test_json_parse_error_default_locator(self):
        """Test default locator exists but is invalid JSON."""
        canonical = "state/diagnosis/run123/c0000/diagnosis.json"
        path = self.root / canonical
        path.parent.mkdir(parents=True)
        path.write_text("invalid json")

        result = self._run_cli("--run-id", "run123", "--cycle-id", "0")
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stderr)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["error_type"], "json_parse_error")

    @patch("refocus_generator.generate_refocus_plan")
    def test_refocus_error(self, mock_generate):
        """Test handling of RefocusError from generate_refocus_plan."""
        mock_generate.side_effect = RefocusError("simulated refocus error")
        canonical = "state/diagnosis/run123/c0000/diagnosis.json"
        path = self.root / canonical
        path.parent.mkdir(parents=True)
        path.write_text('{"classification": "LOCAL_PLATEAU"}')

        with patch("sys.argv", ["03_refocus_generator.py", "--root", str(self.root), "--run-id", "run123", "--cycle-id", "0"]):
            with patch("sys.stderr", new=sys.stderr) as mock_stderr:
                from io import StringIO
                sys.stderr = StringIO()

                # `main()` directly returns integer exit codes
                return_code = refocus_generator.main()
                self.assertEqual(return_code, 2)

                sys.stderr.seek(0)
                data = json.loads(sys.stderr.read())
                self.assertEqual(data["status"], "error")
                self.assertEqual(data["error_type"], "refocus_error")
                self.assertIn("simulated refocus error", data["message"])
                sys.stderr = mock_stderr

    @patch("refocus_generator.generate_refocus_plan")
    def test_unexpected_error(self, mock_generate):
        """Test handling of unexpected exception from generate_refocus_plan."""
        mock_generate.side_effect = ValueError("simulated unexpected error")
        canonical = "state/diagnosis/run123/c0000/diagnosis.json"
        path = self.root / canonical
        path.parent.mkdir(parents=True)
        path.write_text('{"classification": "LOCAL_PLATEAU"}')

        with patch("sys.argv", ["03_refocus_generator.py", "--root", str(self.root), "--run-id", "run123", "--cycle-id", "0"]):
            with patch("sys.stderr", new=sys.stderr) as mock_stderr:
                from io import StringIO
                sys.stderr = StringIO()

                return_code = refocus_generator.main()
                self.assertEqual(return_code, 3)

                sys.stderr.seek(0)
                data = json.loads(sys.stderr.read())
                self.assertEqual(data["status"], "error")
                self.assertEqual(data["error_type"], "unexpected_error")
                self.assertIn("simulated unexpected error", data["message"])
                sys.stderr = mock_stderr

    @patch("refocus_generator.generate_refocus_plan")
    def test_success(self, mock_generate):
        """Test successful plan generation."""
        dummy_plan = {"classification": "LOCAL_PLATEAU", "strategy": "targeted_bottleneck"}
        mock_generate.return_value = dummy_plan
        canonical = "state/diagnosis/run123/c0000/diagnosis.json"
        path = self.root / canonical
        path.parent.mkdir(parents=True)
        path.write_text('{"classification": "LOCAL_PLATEAU"}')

        with patch("sys.argv", ["03_refocus_generator.py", "--root", str(self.root), "--run-id", "run123", "--cycle-id", "0"]):
            with patch("sys.stdout", new=sys.stdout) as mock_stdout:
                from io import StringIO
                sys.stdout = StringIO()

                return_code = refocus_generator.main()
                self.assertEqual(return_code, 0)

                sys.stdout.seek(0)
                data = json.loads(sys.stdout.read())
                self.assertEqual(data["status"], "success")
                self.assertEqual(data["refocus_plan"], dummy_plan)
                sys.stdout = mock_stdout


if __name__ == '__main__':
    unittest.main()
