"""Tests for the canonical local runtime and CI compatibility policy."""
from __future__ import annotations

from pathlib import Path
import re
import shlex
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PythonRuntimePolicyTests(unittest.TestCase):
    def test_local_runtime_is_cpython_314_in_checkout_venv(self) -> None:
        self.assertEqual((ROOT / ".python-version").read_text(encoding="utf-8"), "3.14\n")
        if sys.version_info[:2] != (3, 14):
            self.skipTest("lower CI jobs prove package compatibility, not local runtime")
        result = subprocess.run(
            [str(ROOT / "bin/python-runtime.sh"), str(ROOT)],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    @staticmethod
    def _active_shell_lines(source: str) -> list[str]:
        """Return shell lines, excluding comments and embedded heredoc bodies."""
        active: list[str] = []
        heredoc_end: str | None = None
        for raw_line in source.splitlines():
            line = raw_line.strip()
            if heredoc_end is not None:
                if line == heredoc_end:
                    heredoc_end = None
                continue
            if not line or line.startswith("#"):
                continue
            active.append(line)
            heredoc = re.search(r"<<-?(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1", line)
            if heredoc is not None:
                heredoc_end = heredoc.group(2)
        return active

    @classmethod
    def _active_runtime_commands(cls, source: str) -> list[tuple[str, str]]:
        """Return (command, line) pairs for active python/python3/pip calls."""
        commands: list[tuple[str, str]] = []
        separators = {";", "&&", "||", "|", "&", "("}
        control_words = {"if", "elif", "then", "while", "until", "do", "else", "!"}
        command_prefixes = {"exec", "command", "env"}
        assignment = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

        for line in cls._active_shell_lines(source):
            lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|()")
            lexer.whitespace_split = True
            lexer.commenters = ""
            expecting_command = True
            for token in lexer:
                if token in separators:
                    expecting_command = True
                    continue
                if token == ")":
                    expecting_command = False
                    continue
                if token in control_words:
                    expecting_command = True
                    continue
                if not expecting_command:
                    continue
                if assignment.match(token) or token in command_prefixes:
                    continue
                expecting_command = False
                if token.rsplit("/", 1)[-1] in {"python", "python3", "pip"}:
                    commands.append((token, line))
        return commands

    def test_launchers_use_only_checkout_python(self) -> None:
        expected_commands = {
            "check.sh": [
                'exec "$ROOT/.venv/bin/python" '
                '"$ROOT/scripts/article_loop_command.py" check --root "$ROOT"',
            ],
            "preflight.sh": [
                "exec \"$ROOT/.venv/bin/python\" -c 'import sys; from pathlib "
                "import Path; sys.path.insert(0, str(Path(sys.argv[1]) / "
                "\".prime/agent/skills/article-loop/src\")); from article_loop "
                "import ingest; result = ingest(sys.argv[1]); print(\"{}: {} "
                "({})\".format(result[\"status\"], result[\"champion\"], "
                "result[\"sha256\"]))' \"$ROOT\"",
            ],
            "start-control-center.sh": [
                'exec "$ROOT/.venv/bin/python" -m article_loop.control_center '
                '--root "$ROOT" --host 127.0.0.1 --port "$PORT"',
            ],
            "start-prime.sh": [
                '"$ROOT/.venv/bin/python" '
                '"$ROOT/scripts/article_loop_command.py" preflight --root "$ROOT"',
                "\"$ROOT/.venv/bin/python\" - \"$ROOT\" \"$TEMPLATE\" <<'PY'",
                '"$ROOT/.venv/bin/python" '
                '"$ROOT/scripts/article_loop_command.py" check --root "$ROOT" '
                '--require-live',
            ],
        }
        for name, expected in expected_commands.items():
            with self.subTest(name=name):
                source = (ROOT / "bin" / name).read_text(encoding="utf-8")
                self.assertEqual(
                    self._active_runtime_commands(source),
                    [("$ROOT/.venv/bin/python", line) for line in expected],
                )

        bootstrap = (ROOT / "bin/bootstrap-deps.sh").read_text(encoding="utf-8")
        self.assertIn('command -v python3.14', bootstrap)
        self.assertIn('"$ROOT/.venv/bin/python" -m pip', bootstrap)
        self.assertIn("foi movida", bootstrap)
        self.assertIn("Remova-a", bootstrap)

    def test_canonical_entrypoint_commands_do_not_regress_to_python3(self) -> None:
        architecture = (ROOT / "docs/architecture.md").read_text(encoding="utf-8")
        m13_command = ".venv/bin/python scripts/m13_system_check.py"
        self.assertTrue((ROOT / "scripts/m13_system_check.py").is_file())
        self.assertIn(f"`{m13_command}`", architecture)
        self.assertNotIn("`python3 scripts/m13_system_check.py`", architecture)

        decisions = (ROOT / "docs/decisions.md").read_text(encoding="utf-8")
        adr_038 = decisions.split("## ADR-038", 1)[1].split("\n## ADR-", 1)[0]
        decision = adr_038.split("### Decisão", 1)[1].split("\n### ", 1)[0]
        amendment = adr_038.split(
            "### Emenda de runtime canônico — 2026-09-18", 1
        )[1]
        historical_command = "python3 -m article_loop.control_center"
        control_center_command = (
            "$ROOT/.venv/bin/python -m article_loop.control_center"
        )
        self.assertIn(f"`{historical_command}`", decision)
        self.assertNotIn(f"`{control_center_command}`", decision)
        self.assertIn(f"`{control_center_command}`", amendment)

        launcher = (ROOT / "bin/start-control-center.sh").read_text(encoding="utf-8")
        active_exec_lines = [
            line.strip() for line in launcher.splitlines()
            if line.lstrip().startswith("exec ")
        ]
        self.assertEqual(active_exec_lines, [
            'exec "$ROOT/.venv/bin/python" -m article_loop.control_center '
            '--root "$ROOT" --host 127.0.0.1 --port "$PORT"'
        ])
        self.assertNotIn("python3", active_exec_lines[0])

    def test_ci_uses_isolated_venv_for_each_compatibility_version(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn('python-version: ["3.11", "3.12", "3.13", "3.14"]', workflow)
        self.assertIn("python -m venv .venv", workflow)
        for module in ("pip", "py_compile", "unittest"):
            self.assertIn(f".venv/bin/python -m {module}", workflow)
        self.assertFalse(any(
            line.strip().startswith("pip ") for line in workflow.splitlines()
        ))
        self.assertIn("bash -n bin/*.sh", workflow)
        self.assertIn("dash -n bin/bootstrap-deps.sh bin/preflight.sh bin/python-runtime.sh", workflow)
        self.assertIn("node --check .prime/agent/skills/article-loop/src/article_loop/control_center_static/app.js", workflow)


if __name__ == "__main__":
    unittest.main()
