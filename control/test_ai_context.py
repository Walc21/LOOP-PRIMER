from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import ai_context
from ai_context import (
    _read,
    _section,
    _milestones,
    _yaml_list,
    _yaml_scalar,
    _roles,
    _schemas,
    _python_api,
    _tests,
    _handoff_order,
    _history_digest,
    _normalize_diff_preview,
    _bounded_excerpt,
    _truncate_diff_preview,
    _recent_sessions,
    render_context,
    _stored_context_fingerprint,
    inspect_context,
    parser,
    main,
    HandoffError,
)
from ai_history import LEDGER_RELATIVE

class AIContextTests(unittest.TestCase):
    def test_read_missing_file_returns_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = _read(root, "missing.txt", "default_value")
            self.assertEqual(result, "default_value")

    def test_read_symlink_raises_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "target.txt").write_text("target")
            (root / "symlink.txt").symlink_to(root / "target.txt")
            with self.assertRaises(HandoffError):
                _read(root, "symlink.txt")

    def test_section_extraction(self):
        text = "# H1\n\n## H2\n\ncontent\n\n## H2 next\n"
        self.assertEqual(_section(text, "H2"), "## H2\n\ncontent")
        self.assertEqual(_section(text, "Missing"), "")

    def test_milestones_parsing(self):
        plans = "| M1 | delivery 1 | concluído | acc 1 |\n| M2.1 | delivery 2 | pendente | acc 2 |"
        milestones = _milestones(plans)
        self.assertEqual(len(milestones), 2)
        self.assertEqual(milestones[0]["id"], "M1")
        self.assertEqual(milestones[0]["status"], "concluído")
        self.assertEqual(milestones[1]["id"], "M2.1")

    def test_yaml_list(self):
        yaml_text = "states:\n  - NEW\n  - RUNNING\nother:\n  - NONE"
        self.assertEqual(_yaml_list(yaml_text, "states"), ["NEW", "RUNNING"])
        self.assertEqual(_yaml_list(yaml_text, "missing"), [])

    def test_yaml_scalar(self):
        yaml_text = 'id: "test"\nname: test_name\nempty: ""\nnull_val: null\ntilde: ~'
        self.assertEqual(_yaml_scalar(yaml_text, "id"), "test")
        self.assertEqual(_yaml_scalar(yaml_text, "name"), "test_name")
        self.assertIsNone(_yaml_scalar(yaml_text, "empty"))
        self.assertIsNone(_yaml_scalar(yaml_text, "null_val"))
        self.assertIsNone(_yaml_scalar(yaml_text, "tilde"))
        self.assertIsNone(_yaml_scalar(yaml_text, "missing"))

    def test_roles_parsing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            roles_dir = root / "config/roles"
            roles_dir.mkdir(parents=True)
            (roles_dir / "r1.yaml").write_text("id: 1\nname: role1\n", encoding="utf-8")
            (roles_dir / "r2.yaml").write_text("id: 2\nname: role2\n", encoding="utf-8")

            roles = _roles(root)
            self.assertEqual(len(roles), 2)
            self.assertEqual(roles[0]["id"], "1")
            self.assertEqual(roles[1]["name"], "role2")

    def test_roles_missing_dir(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(_roles(root), [])

    def test_schemas_parsing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            schemas_dir = root / "config/schemas"
            schemas_dir.mkdir(parents=True)
            (schemas_dir / "s1.json").write_text('{"title": "Schema 1", "required": ["id"], "properties": {"id": {}}}', encoding="utf-8")
            (schemas_dir / "s2.json").write_text('invalid json', encoding="utf-8")

            schemas = _schemas(root)
            self.assertEqual(len(schemas), 2)
            self.assertEqual(schemas[0]["title"], "Schema 1")
            self.assertEqual(schemas[0]["required"], ["id"])
            self.assertEqual(schemas[0]["properties"], ["id"])
            self.assertEqual(schemas[1]["title"], "JSON inválido")

    def test_schemas_missing_dir(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(_schemas(root), [])

    def test_python_api(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            py_file = root / "module.py"
            py_file.write_text("class Test:\n    def method(self):\n        pass\n\ndef func():\n    pass\n\nasync def async_func():\n    pass", encoding="utf-8")

            api = _python_api(py_file)
            self.assertEqual(len(api), 3)
            self.assertIn("class Test [method]", api)
            self.assertIn("func()", api)
            self.assertIn("async async_func()", api)

            py_file.write_text("invalid python syntax", encoding="utf-8")
            api_invalid = _python_api(py_file)
            self.assertTrue(api_invalid[0].startswith("erro de parsing:"))

    def test_tests_parsing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            control_dir = root / "control"
            control_dir.mkdir(parents=True)
            (control_dir / "test_module.py").write_text("def test_feature():\n    pass\n\nasync def test_async_feature():\n    pass", encoding="utf-8")
            (control_dir / "test_invalid.py").write_text("invalid python", encoding="utf-8")

            tests = _tests(root)
            self.assertEqual(len(tests), 2)
            tests_by_name = {t["name"]: t for t in tests}
            self.assertEqual(tests_by_name["test_module.py"]["count"], 2)
            self.assertEqual(tests_by_name["test_module.py"]["topics"], ["feature", "async feature"])
            self.assertEqual(tests_by_name["test_invalid.py"]["count"], 0)
            self.assertEqual(tests_by_name["test_invalid.py"]["topics"], ["Python inválido"])

    def test_tests_missing_dir(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(_tests(root), [])

    def test_handoff_order(self):
        self.assertEqual(_handoff_order(Path("1_para_2.md")), (1, 0, "1_para_2.md"))
        self.assertEqual(_handoff_order(Path("1_2_para_3.md")), (1, 2, "1_2_para_3.md"))
        self.assertEqual(_handoff_order(Path("1_final.md")), (1, 0, "1_final.md"))
        self.assertEqual(_handoff_order(Path("not_matching.md")), (-1, -1, "not_matching.md"))

    def test_history_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            history_text = "## Evolution\n| M1 | - | - | - | - |\n## Atualizações de sessão\n"
            digest = _history_digest(root, history_text)
            self.assertTrue(any("Marco histórico" in line for line in digest))

            digest_empty = _history_digest(root, "")
            self.assertTrue(any("Histórico ainda não existe" in line for line in digest_empty))

            ledger_dir = root / LEDGER_RELATIVE.parent
            ledger_dir.mkdir(parents=True, exist_ok=True)
            (root / LEDGER_RELATIVE).write_text('{"session_id": "1", "summary": "test session", "changes": ["change 1"]}\n', encoding="utf-8")

            digest_with_ledger = _history_digest(root, history_text)
            self.assertTrue(any("Sessões estruturadas registradas: 1" in line for line in digest_with_ledger))

    def test_normalize_diff_preview(self):
        self.assertEqual(_normalize_diff_preview("line1 \t\nline2  \n"), "line1\nline2")

    def test_bounded_excerpt(self):
        text = "short text"
        self.assertEqual(_bounded_excerpt(text, limit=20, label="test"), "short text")

        long_text = "line1\nline2\nline3"
        excerpt = _bounded_excerpt(long_text, limit=10, label="test")
        self.assertTrue("truncado em 10 caracteres" in excerpt)

    def test_truncate_diff_preview(self):
        text = "short diff"
        self.assertEqual(_truncate_diff_preview(text, limit=20), "short diff")

        long_diff = "line1\nline2\nline3"
        truncated = _truncate_diff_preview(long_diff, limit=10)
        self.assertTrue("diff truncado em 10 caracteres" in truncated)

    def test_recent_sessions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertTrue(any("Nenhuma sessão" in line for line in _recent_sessions(root)))

            ledger_dir = root / LEDGER_RELATIVE.parent
            ledger_dir.mkdir(parents=True, exist_ok=True)
            (root / LEDGER_RELATIVE).write_text('{"session_id": "1", "summary": "test session", "changes": ["change 1"]}\n', encoding="utf-8")

            sessions = _recent_sessions(root)
            self.assertTrue(any("Sessões estruturadas registradas: 1" in line for line in sessions))

    def test_stored_context_fingerprint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output_file = root / "AI_CONTEXT.md"
            self.assertIsNone(_stored_context_fingerprint(output_file))

            output_file.write_text("- Fingerprint atual das fontes: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`\n", encoding="utf-8")
            self.assertEqual(_stored_context_fingerprint(output_file), "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

    def test_main_missing_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "nonexistent"
            with patch("sys.stderr", new=sys.stderr):
                ret = main(["--root", str(root)])
                self.assertEqual(ret, 2)

    def test_main_invalid_diff_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ret = main(["--root", str(root), "--diff-limit", "-1"])
            self.assertEqual(ret, 2)

    def test_main_output_outside_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ret = main(["--root", str(root), "--output", "../outside.md"])
            self.assertEqual(ret, 2)

    def test_main_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir(parents=True)
            (root / "config").mkdir(parents=True)
            def snapshot():
                return {p.relative_to(root).as_posix(): p.read_bytes() if p.is_file() else None
                        for p in root.rglob("*")}
            for existing in (False, True):
                with self.subTest(existing=existing):
                    if existing:
                        (root / "AI_CONTEXT.md").write_bytes(b"stale sentinel\n")
                    before = snapshot()
                    ret = main(["--root", str(root), "--check"])
                    self.assertEqual(ret, 1)
                    self.assertEqual(snapshot(), before)

    def test_main_write_and_stdout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir(parents=True)
            (root / "config").mkdir(parents=True)
            ret = main(["--root", str(root), "--stdout"])
            self.assertEqual(ret, 0)
            self.assertTrue((root / "AI_CONTEXT.md").exists())


    def test_main_execution_raises_system_exit(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "ai_context.py"), "--root", temporary, "--check"],
                cwd=temporary, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertTrue(json.loads(result.stdout)["stale"])
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_module_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing"
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "ai_context.py"), "--root", str(missing), "--check"],
                cwd=temporary, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stderr)["status"], "error")

    def test_runpy(self):
        import runpy
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(sys, "argv", ["ai_context.py", "--root", temporary, "--check"]):
                with self.assertRaises(SystemExit) as raised:
                    runpy.run_path(str(SCRIPTS / "ai_context.py"), run_name="__main__")
            self.assertEqual(raised.exception.code, 1)
            self.assertEqual(list(Path(temporary).iterdir()), [])
