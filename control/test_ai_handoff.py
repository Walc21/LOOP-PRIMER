from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ai_context import _bounded_excerpt, _normalize_diff_preview, _truncate_diff_preview, render_context
from ai_handoff_common import build_inventory, inventory_delta, inventory_fingerprint
from ai_history import infer_milestone, load_entries, update_history


class AIHandoffTests(unittest.TestCase):
    def test_embedded_previews_are_bounded_and_have_no_trailing_whitespace(self) -> None:
        normalized = _normalize_diff_preview("+line with spaces  \n+\t\n context\t\n")
        self.assertEqual(normalized, "+line with spaces\n+\n context")
        self.assertFalse(any(line.endswith((" ", "\t")) for line in normalized.splitlines()))

        excerpt = _bounded_excerpt("first\n" + "x" * 100, limit=20, label="fixture")
        self.assertTrue(excerpt.startswith("first\n"))
        self.assertIn("fixture truncado em 20 caracteres", excerpt)
        self.assertNotIn("x" * 100, excerpt)

        truncated_diff = _truncate_diff_preview("header\n+linha com espaços internos\n+final", limit=22)
        self.assertFalse(any(line.endswith((" ", "\t")) for line in truncated_diff.splitlines()))
        self.assertNotIn("+linha com ", truncated_diff)
        self.assertIn("diff truncado", truncated_diff)

    def test_tracked_generated_context_is_portable_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (root / "PLANS.md").write_text("# Plano\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("# Regras\n", encoding="utf-8")
            (root / "AI_CONTEXT.md").write_text("placeholder\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "AI Handoff Test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "handoff@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=root, check=True)

            first = render_context(root, diff_limit=5_000)
            (root / "AI_CONTEXT.md").write_text(first, encoding="utf-8")
            second = render_context(root, diff_limit=5_000)

            self.assertEqual(first, second)
            self.assertNotIn("diff --git a/AI_CONTEXT.md", second)
            self.assertNotIn(str(root), second)
            self.assertNotRegex(second, r"HEAD `[0-9a-f]{7,40}`")

    def test_repository_trigger_surfaces_preserve_start_and_end_protocol(self) -> None:
        required = {
            "AGENTS.md": ("python3 scripts/ai_context.py", "scripts/ai_history.py", "AI_CONTEXT.md"),
            "CLAUDE.md": ("python3 scripts/ai_context.py", "scripts/ai_history.py", "AI_CONTEXT.md"),
            ".prime/agent/APPEND_SYSTEM.md": (
                "python3 scripts/ai_context.py",
                "scripts/ai_history.py",
                "AI_CONTEXT.md",
            ),
            "GEMINI.md": ("AGENTS.md", "python3 scripts/ai_context.py", "AI_CONTEXT.md"),
            ".github/copilot-instructions.md": ("AGENTS.md", "python3 scripts/ai_context.py", "AI_CONTEXT.md"),
        }
        for relative, markers in required.items():
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                for marker in markers:
                    self.assertIn(marker, text)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("Entrada obrigatória para IAs", readme)
        self.assertNotIn("leia `AI_CONTEXT.md` integralmente", readme)
        self.assertIn("M10", readme)
        self.assertIn("reserved stubs", readme)

    def test_context_points_to_ai_sources_without_embedding_human_docs_or_full_inventory(self) -> None:
        context = render_context(ROOT, diff_limit=0)

        self.assertIn("## Autoridade e separação de audiências", context)
        self.assertIn("`AGENTS.md` é a política autoritativa", context)
        self.assertIn("`README.md`, `CONTRIBUTING.md` e `SECURITY.md`", context)
        self.assertNotIn("<agents_md>", context)
        self.assertNotIn("<readme>", context)
        self.assertNotIn("| Caminho | Tipo | Bytes |", context)
        self.assertLess(len(context.encode("utf-8")), 45_000)

    def test_inventory_is_content_addressed_and_excludes_generated_and_caches(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            (root / "src/app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
            (root / "AI_CONTEXT.md").write_text("recursive", encoding="utf-8")
            (root / ".venv").mkdir()
            (root / ".venv/ignored.py").write_text("secret = 1", encoding="utf-8")
            (root / ".env").write_text("TOKEN=never-read", encoding="utf-8")
            (root / "state/events").mkdir(parents=True)
            (root / "state/events/run.jsonl").write_text('{"event":"NEW"}\n', encoding="utf-8")

            inventory = build_inventory(root)

            self.assertIn("src/app.py", inventory)
            self.assertNotIn("AI_CONTEXT.md", inventory)
            self.assertNotIn(".venv/ignored.py", inventory)
            self.assertEqual(inventory[".env"]["kind"], "sensitive")
            self.assertIsNone(inventory[".env"]["sha256"])
            self.assertEqual(inventory["state/events/run.jsonl"]["kind"], "runtime")
            self.assertEqual(inventory["state/events/run.jsonl"]["lines"], None)
            self.assertIn("conteúdo não incorporado", inventory["state/events/run.jsonl"]["summary"])
            self.assertRegex(inventory_fingerprint(inventory), r"^[0-9a-f]{64}$")

    def test_delta_reports_add_modify_delete(self) -> None:
        previous = {
            "gone": {"kind": "text", "bytes": 1, "sha256": "a"},
            "same": {"kind": "text", "bytes": 1, "sha256": "b"},
            "changed": {"kind": "text", "bytes": 1, "sha256": "c"},
        }
        current = {
            "same": {"kind": "text", "bytes": 1, "sha256": "b"},
            "changed": {"kind": "text", "bytes": 2, "sha256": "d"},
            "new": {"kind": "text", "bytes": 1, "sha256": "e"},
        }
        delta = inventory_delta(previous, current)
        self.assertEqual([item["path"] for item in delta["added"]], ["new"])
        self.assertEqual([item["path"] for item in delta["modified"]], ["changed"])
        self.assertEqual([item["path"] for item in delta["deleted"]], ["gone"])

    def test_milestone_inference_covers_historical_subjects(self) -> None:
        self.assertEqual(infer_milestone("docs: checkpoint Marco 0 e 0.5"), "M0/M0.5")
        self.assertEqual(infer_milestone("docs: checkpoint Marco 0.6"), "M0.6")
        self.assertEqual(infer_milestone("feat: checkpoint M1 and M1.1"), "M1/M1.1")
        self.assertEqual(infer_milestone("fix(m9): semantic verification"), "M9")
        self.assertEqual(infer_milestone("Add local environment bootstrap"), "M3")

    def test_history_update_is_idempotent_and_context_consumes_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            (root / "docs/decisions.md").write_text("# ADRs\n\n## ADR-001 — Teste\n", encoding="utf-8")
            (root / "README.md").write_text("# Demo\n\nProjeto mínimo.\n", encoding="utf-8")
            (root / "PLANS.md").write_text(
                "# Plano\n\n| Marco | Entrega | Estado | Critério |\n|---|---|---|---|\n| M1 | base | concluído | ok |\n| M2 | próximo | pendente | ok |\n",
                encoding="utf-8",
            )
            (root / "AGENTS.md").write_text("# Regras\n\nSem rede.\n", encoding="utf-8")
            (root / "config").mkdir()
            (root / "config/system.yaml").write_text("states:\n  - NEW\nactions:\n  - STOP\n", encoding="utf-8")
            payload = {
                "summary": "Criado handoff mínimo.",
                "changes": ["Adicionado contexto."],
                "decisions": [],
                "validations": ["Teste local aprovado."],
                "risks": [],
                "next_steps": ["Continuar M2."],
            }

            first = update_history(
                root,
                payload,
                timestamp="2026-09-01T12:00:00Z",
                session_id="session-test-0001",
            )
            second = update_history(
                root,
                payload,
                timestamp="2026-09-01T13:00:00Z",
                session_id="session-test-0001",
            )

            self.assertEqual(first["status"], "recorded")
            self.assertEqual(second["status"], "idempotent")
            entries = load_entries(root / "docs/ai_sessions.jsonl")
            self.assertEqual(len(entries), 1)
            self.assertTrue(entries[0]["baseline_initialized"])
            self.assertEqual(entries[0]["file_delta"], {"added": [], "modified": [], "deleted": []})
            snapshot = json.loads((root / "docs/ai_snapshot.json").read_text("utf-8"))
            self.assertNotIn("docs/AI_HISTORY.md", snapshot["files"])
            context = render_context(root, diff_limit=0)
            self.assertIn("Criado handoff mínimo.", context)
            self.assertIn("M2", context)
            self.assertIn("README.md", context)
            self.assertNotIn("| Marco | Intervalo", context)


if __name__ == "__main__":
    unittest.main()
