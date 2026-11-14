"""Offline regression tests for ADR-046 executable resolution."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))
from article_loop.gates import _run

class GateExecutableResolutionTests(unittest.TestCase):
    def test_invalid_names_never_reach_lookup_or_execution(self):
        for command in ("", "../pdflatex", "/usr/bin/pdflatex", "bin/tool", "tool;id", "tool\n", "tool\x00"):
            with self.subTest(command=command), patch("article_loop.gates.shutil.which") as which, patch("article_loop.gates.subprocess.run") as run:
                self.assertEqual(_run(command, [], cwd=ROOT, timeout=1)[1], 127)
                which.assert_not_called()
                run.assert_not_called()

    def test_missing_and_relative_resolution_fail_closed(self):
        for executable in (None, "bin/pdflatex", "./pdflatex"):
            with self.subTest(executable=executable), patch("article_loop.gates.shutil.which", return_value=executable), patch("article_loop.gates.subprocess.run") as run:
                self.assertEqual(_run("pdflatex", [], cwd=ROOT, timeout=1)[1], 127)
                run.assert_not_called()

    def test_relative_path_entry_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            tool = Path(temp) / "local-verifier"
            tool.write_text("#!/bin/sh\nexit 0\n")
            tool.chmod(0o755)
            relative = os.path.relpath(temp)
            with patch.dict(os.environ, {"PATH": relative}), patch("article_loop.gates.subprocess.run") as run:
                self.assertEqual(_run(tool.name, [], cwd=ROOT, timeout=1)[1], 127)
                run.assert_not_called()

    def test_absolute_executable_preserves_argument_boundaries(self):
        for command in ("pdflatex", "tool-name", "tool_name", "tool+name", "python3.14"):
            with self.subTest(command=command), patch("article_loop.gates.shutil.which", return_value="/usr/bin/" + command), patch("article_loop.gates.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "ok")) as run:
                self.assertEqual(_run(command, ["a b", ";echo bad"], cwd=ROOT, timeout=3)[:3], (True, 0, "ok"))
                self.assertEqual(run.call_args.args[0], ["/usr/bin/" + command, "a b", ";echo bad"])
                self.assertNotIn("shell", run.call_args.kwargs)
