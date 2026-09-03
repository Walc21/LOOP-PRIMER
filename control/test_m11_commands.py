"""Offline tests for the M11 command and Prime Agent integration surfaces."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import article_loop_command as command  # noqa: E402


class M11TemplateTests(unittest.TestCase):
    def test_exact_flat_template_discovery_and_frontmatter(self):
        discovered = tuple(sorted(path.stem for path in command.TEMPLATE_DIR.glob("*.md")))
        self.assertEqual(discovered, tuple(sorted(command.TEMPLATE_NAMES)))
        for name in command.TEMPLATE_NAMES:
            with self.subTest(name=name):
                path = command.TEMPLATE_DIR / f"{name}.md"
                lines = path.read_text(encoding="utf-8").splitlines()
                self.assertEqual(lines[0], "---")
                end = lines.index("---", 1)
                metadata = yaml.safe_load("\n".join(lines[1:end]))
                self.assertEqual(set(metadata), {"description", "argument-hint"})
                self.assertIsInstance(metadata["description"], str)
                self.assertIn("article_loop", "\n".join(lines[end + 1 :]))

    def test_append_system_is_additive_and_has_m11_guardrails(self):
        append = (ROOT / ".prime/agent/APPEND_SYSTEM.md").read_text(encoding="utf-8")
        self.assertIn("python3 scripts/ai_context.py", append)
        self.assertIn("## Guardrails operacionais M11", append)
        self.assertIn("AGENTS.md", append)
        self.assertIn("article-loop/SKILL.md", append)
        self.assertIn("FINALIZED", append)
        self.assertEqual(append.count("## Guardrails operacionais M11"), 1)

    def test_project_settings_are_not_invented(self):
        self.assertFalse((ROOT / ".prime/agent/settings.json").exists())
        result = command.check_project(ROOT)
        self.assertEqual(result["settings"], "omitted_unconfirmed")


class M11CommandBridgeTests(unittest.TestCase):
    def invoke(self, argv: list[str]) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
            code = command.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_check_reports_safe_local_defaults(self):
        code, stdout, stderr = self.invoke(["check", "--root", str(ROOT)])
        self.assertEqual(code, 0, stderr)
        value = json.loads(stdout)
        self.assertEqual(value["status"], "success")
        self.assertFalse(value["result"]["execution"]["model_execution_enabled"])
        self.assertFalse(value["result"]["prime_agent_discovered"])
        self.assertEqual(value["result"]["m12"]["unit"], "tokens")
        self.assertEqual(value["result"]["m12"]["profiles"], {"calibration": False, "overnight": False})

    def test_require_live_rejects_current_fail_closed_configuration(self):
        code, stdout, stderr = self.invoke(["check", "--root", str(ROOT), "--require-live"])
        self.assertEqual(code, 3)
        self.assertEqual(stdout, "")
        self.assertIn("live execution", stderr)

    def test_unknown_json_field_cannot_select_test_double(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as handle:
            json.dump({"test_mode": True}, handle)
            handle.flush()
            code, stdout, stderr = self.invoke(
                ["status", "--root", str(ROOT), "--input", handle.name]
            )
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("unsupported parameters", stderr)

    def test_commands_route_to_one_existing_public_api(self):
        cases = [
            ("bootstrap", "bootstrap", ["--pdf", str(ROOT / "README.md")]),
            ("preflight", "preflight", []),
            ("run", "run_cycle", ["--dry-run"]),
            ("status", "status", []),
            ("checkpoint", "checkpoint", []),
            ("pause", "pause", []),
            ("resume", "resume", []),
            ("stop", "stop", []),
            ("finalize", "finalize", []),
        ]
        for command_name, api_name, extra in cases:
            with self.subTest(command=command_name):
                api = AsyncMock(return_value={"command": command_name})
                with patch.object(command, api_name, api):
                    code, stdout, stderr = self.invoke(
                        [command_name, "--root", str(ROOT), *extra]
                    )
                self.assertEqual(code, 0, stderr)
                self.assertEqual(json.loads(stdout)["result"]["command"], command_name)
                api.assert_awaited_once()

    def test_cli_and_json_values_cannot_conflict(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as handle:
            json.dump({"dry_run": True}, handle)
            handle.flush()
            code, stdout, stderr = self.invoke(
                ["run", "--root", str(ROOT), "--input", handle.name, "--live"]
            )
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("conflicting values", stderr)

    def test_invalid_identifiers_are_rejected_before_api(self):
        api = AsyncMock(return_value={})
        with patch.object(command, "status", api):
            code, stdout, stderr = self.invoke(
                ["status", "--root", str(ROOT), "--run-id", "../escape"]
            )
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("safe", stderr)
        api.assert_not_awaited()

    def test_live_run_without_explicit_adapter_fails_closed(self):
        # The command bridge reaches the existing API, which fails closed
        # before any child admission when no prepared run is available.
        with patch.object(command, "run_cycle", wraps=command.run_cycle) as api:
            code, stdout, stderr = self.invoke(
                ["run", "--root", str(ROOT), "--live"]
            )
        self.assertEqual(code, 3)
        self.assertEqual(stdout, "")
        self.assertIn("exactly one bootstrapped M6 run", stderr)
        api.assert_called_once()


class M11ShellTests(unittest.TestCase):
    def run_shell(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(ROOT / "bin/start-prime.sh"), *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_launcher_defaults_to_no_prime_no_model_dry_run(self):
        result = self.run_shell()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"prime_started": false', result.stdout)
        self.assertIn('"model_called": false', result.stdout)

    def test_launcher_rejects_unknown_template_without_execution(self):
        result = self.run_shell("--template", "$(touch /tmp/article-loop-m11-injection)")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unsupported project template", result.stderr)

    def test_launcher_requires_authorization_for_live_mode(self):
        result = self.run_shell("--live")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--authorize-live", result.stderr)

    def test_launcher_current_live_path_stops_at_fail_closed_budget(self):
        result = self.run_shell("--live", "--authorize-live")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("live execution is not explicitly enabled and authorized", result.stderr)
        self.assertNotIn("prime-agent is not available in PATH", result.stderr)

    def test_launcher_outside_project_root_fails_before_prime(self):
        result = self.run_shell("--root", tempfile.gettempdir())
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("prime_started", result.stdout)


if __name__ == "__main__":
    unittest.main()
