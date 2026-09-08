"""Deterministic, networkless tests for the official one-task M6 smoke."""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from typing import Callable
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))

from article_loop.budget import ManualClock
from article_loop.inference import InferenceResult
from article_loop.inference import canonical_bytes
from article_loop.inference_backends import FakeInferenceBackend
from article_loop.ingestion import IngestionError, _directory_hash
from article_loop.m6_smoke import (
    CONTEXT_OVERHEAD_TOKENS, M6SmokeError, SmokeConfig,
    create_context_selection, preflight_official_smoke, run_official_smoke,
)
from article_loop.state_machine import State
from article_loop.store import DurableStore


ATTEMPT_ID = "attempt-12345678-1234-4123-8123-123456789abc"


def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        relative = item.relative_to(path).as_posix()
        digest.update(relative.encode())
        if item.is_symlink():
            digest.update(b"symlink:")
            digest.update(os.readlink(item).encode())
        elif item.is_file():
            digest.update(hashlib.sha256(item.read_bytes()).digest())
    return digest.hexdigest()


def _budget_events(attempt: Path, run_id: str) -> list[dict[str, object]]:
    path = attempt / "state/budgets" / f"{run_id}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _scientific_payload() -> dict[str, object]:
    return {
        "scope": ["abstract"],
        "evidence_locators": ["readonly:synthetic"],
        "patch_or_operations": {
            "kind": "operations",
            "operations": [{"op": "annotate", "target": "abstract", "value": "synthetic"}],
        },
        "affected_claims": [], "dependencies": [],
        "risk": {"level": "low", "factors": [], "technical_effect_possible": False},
        "confidence": 1.0, "requested_validations": [],
    }


def _build_m3(
    root: Path, *, source_ready: bool = True,
    page_texts: tuple[str, ...] = ("Synthetic M3 source.",),
) -> str:
    for relative in (
        "input/inbox", "workspaces", "artifacts/original", "artifacts/extracted",
        "artifacts/rendered", "versions/champion", "config", "state/events",
        "state/snapshots", "state/checkpoints", "state/locks",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)
    pdf = root / "input/inbox/artigo.pdf"
    pdf.write_bytes(b"%PDF-1.4\nsynthetic fixture only\n%%EOF\n")
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    run_id = "ingest-" + digest
    original = root / "artifacts/original" / digest
    extracted = root / "artifacts/extracted" / digest
    rendered = root / "artifacts/rendered" / digest
    original.mkdir(); extracted.mkdir(); rendered.mkdir()
    (original / "document.pdf").write_bytes(pdf.read_bytes())
    (extracted / "text.txt").write_text("\f\n".join(page_texts) + "\n", encoding="utf-8")
    lines = []
    blocks = []
    line_number = 1
    for page, text in enumerate(page_texts, 1):
        page_lines = text.splitlines() or [""]
        start = line_number
        for content in page_lines:
            lines.append({"page": page, "line": line_number, "text": content})
            line_number += 1
        blocks.append({"page": page, "line_start": start, "line_end": line_number - 1})
    _json(extracted / "normalized.json", {
        "schema_version": "1.1.0", "source_mode": "PDF_ONLY_RECONSTRUCTION",
        "pages": len(page_texts), "blocks": blocks, "lines": lines,
        "equations": [], "equation_candidates": [], "references": [],
        "reference_candidates": [], "issues": [],
    })
    gate = {"id": "SOURCE_READY", "status": "passed", "scope": "synthetic test fixture"}
    _json(extracted / "source_ready.json", gate)
    (rendered / "page-1.png").write_bytes(b"synthetic-render")
    for directory in (original, extracted, rendered):
        _json(directory / "manifest.json", {"directory_hash": _directory_hash(directory)})
    hashes = {
        "original": _directory_hash(original, exclude={"manifest.json"}),
        "extracted": _directory_hash(extracted, exclude={"manifest.json"}),
        "rendered": _directory_hash(rendered, exclude={"manifest.json"}),
    }
    source_identity = {
        "input_sha256": digest, "source_zip_present": False,
        "source_zip_sha256": None, "source_zip_size_bytes": None,
        "source_mode": "PDF_ONLY_RECONSTRUCTION",
    }
    store = DurableStore(root)
    store.create_run(run_id, actor_id="test-m3", event_id=f"{run_id}:new")
    store.record(
        run_id, State.INGESTED, event_id=f"{run_id}:ingested",
        idempotency_key=f"{run_id}:ingested", actor_id="test-m3",
        event_type="M3_INGESTED", payload={"source_identity": source_identity},
    )
    if source_ready:
        store.record(
            run_id, State.SOURCE_READY, event_id=f"{run_id}:source-ready",
            idempotency_key=f"{run_id}:source-ready", actor_id="test-m3",
            event_type="M3_SOURCE_READY",
            payload={"source_identity": source_identity, "gate": gate, "artifacts": hashes},
        )
    champion = root / "versions/champion/v0000"
    champion.mkdir()
    (champion / "baseline.pdf").write_bytes(pdf.read_bytes())
    shutil.copytree(extracted, champion / "source")
    _json(champion / "ingestion-manifest.json", {
        "input_sha256": digest, "source_identity": source_identity,
        "source_mode": source_identity["source_mode"], "source_zip": None,
        "artifact_hashes": hashes,
    })
    content_hash = _directory_hash(champion)
    _json(champion / "manifest.json", {
        "run_id": run_id, "content_hash": content_hash, "workspace_hash": content_hash,
    })
    return run_id


class OfficialM6SmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.m3_parent = self.base / "m3"
        self.attempt_parent = self.base / "smokes"
        self.selection_parent = self.base / "selections"
        self.m3_parent.mkdir(); self.attempt_parent.mkdir(); self.selection_parent.mkdir()
        self.m3 = self.m3_parent / "canonical-m3"
        self.run_id = _build_m3(self.m3)
        self.attempt = self.attempt_parent / ATTEMPT_ID
        self.selection = self.selection_parent / "selection-12345678-1234-4123-8123-123456789abc.json"
        create_context_selection(
            ROOT, self.m3, self.run_id, self.selection, [1],
            allowed_m3_parent=self.m3_parent,
            allowed_selection_parent=self.selection_parent,
        )
        from datetime import datetime, timezone
        self.clock = ManualClock(current=datetime(2026, 1, 1, tzinfo=timezone.utc))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def mapping(self, **changes: object) -> dict[str, object]:
        value: dict[str, object] = {
            "schema_version": "1.0.0", "enabled": True,
            "m3_root": str(self.m3), "m3_run_id": self.run_id,
            "attempt_root": str(self.attempt), "role_id": "W11",
            "selection_manifest": str(self.selection),
            "model": "operator-model", "endpoint": "http://127.0.0.1:11434/v1/chat/completions",
            "deadline_utc": "2026-01-01T00:10:00Z", "timeout_seconds": 30,
            "context_limit": 8192, "max_output_tokens": 512,
            "max_calls": 1, "max_concurrency": 1, "max_retries": 0,
            "max_cycles": 1, "max_cost_microunits": 0, "deny_remote": True,
        }
        value.update(changes)
        return value

    def execute_smoke(self, backend: object, **options: object) -> dict[str, object]:
        return run_official_smoke(
            ROOT, SmokeConfig.from_mapping(self.mapping()),
            allowed_m3_parent=self.m3_parent,
            allowed_attempt_parent=self.attempt_parent,
            allowed_selection_parent=self.selection_parent,
            human_authorized=True, allow_test_doubles=True,
            backend=backend, clock=self.clock, **options,
        )

    def backend(self, *, failure: str | None = None) -> FakeInferenceBackend:
        return FakeInferenceBackend(
            result=InferenceResult(
                json.dumps(_scientific_payload()), 10, 5, 0, True,
                wall_time_seconds=1, finish_reason="stop",
            ),
            failure=failure,
        )

    def test_default_configuration_executes_nothing(self) -> None:
        config = SmokeConfig.from_mapping(self.mapping(enabled=False))
        result = run_official_smoke(
            ROOT, config, allowed_m3_parent=self.m3_parent,
            allowed_attempt_parent=self.attempt_parent,
            allowed_selection_parent=self.selection_parent,
        )
        self.assertEqual({"status": "DISABLED", "executed": False, "calls": 0}, result)
        self.assertFalse(self.attempt.exists())

    def test_missing_human_authorization_blocks_before_backend(self) -> None:
        backend = self.backend()
        with self.assertRaisesRegex(M6SmokeError, "human authorization"):
            run_official_smoke(
                ROOT, SmokeConfig.from_mapping(self.mapping()),
                allowed_m3_parent=self.m3_parent,
                allowed_attempt_parent=self.attempt_parent,
                allowed_selection_parent=self.selection_parent, backend=backend,
            )
        self.assertEqual([], backend.calls)
        self.assertFalse(self.attempt.exists())

    def test_invalid_authorization_and_unauthorized_double_are_rejected(self) -> None:
        config = SmokeConfig.from_mapping(self.mapping())
        with self.assertRaisesRegex(M6SmokeError, "strictly boolean"):
            run_official_smoke(
                ROOT, config, allowed_m3_parent=self.m3_parent,
                allowed_attempt_parent=self.attempt_parent,
                allowed_selection_parent=self.selection_parent,
                human_authorized="yes",  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(M6SmokeError, "test double"):
            run_official_smoke(
                ROOT, config, allowed_m3_parent=self.m3_parent,
                allowed_attempt_parent=self.attempt_parent,
                allowed_selection_parent=self.selection_parent,
                human_authorized=True, backend=self.backend(),
            )
        self.assertFalse(self.attempt.exists())

    def test_only_literal_ipv4_loopback_is_accepted(self) -> None:
        self.assertEqual("S10", SmokeConfig.from_mapping(self.mapping(role_id="S10")).role_id)
        bad = (
            "http://localhost:11434/v1/chat/completions",
            "http://0.0.0.0:11434/v1/chat/completions",
            "http://192.168.1.2:11434/v1/chat/completions",
            "https://example.com/v1/chat/completions",
            "file:///tmp/model",
        )
        for endpoint in bad:
            with self.subTest(endpoint=endpoint), self.assertRaisesRegex(M6SmokeError, "127.0.0.1"):
                SmokeConfig.from_mapping(self.mapping(endpoint=endpoint))

    def test_single_call_limits_cannot_be_enlarged(self) -> None:
        for field, value in (
            ("max_calls", 2), ("max_concurrency", 2), ("max_retries", 1),
            ("max_cycles", 2), ("max_cost_microunits", 1), ("deny_remote", False),
        ):
            with self.subTest(field=field), self.assertRaises(M6SmokeError):
                SmokeConfig.from_mapping(self.mapping(**{field: value}))

    def test_deadline_missing_invalid_expired_or_insufficient_blocks_before_route(self) -> None:
        invalid = (None, "not-a-date", "2026-01-01T00:00:00Z", "2026-01-01T00:00:10Z")
        for index, deadline in enumerate(invalid):
            attempt = self.attempt_parent / f"attempt-12345678-1234-4123-8123-123456789ab{index}"
            mapping = self.mapping(deadline_utc=deadline, attempt_root=str(attempt))
            try:
                config = SmokeConfig.from_mapping(mapping)
            except M6SmokeError:
                continue
            with self.assertRaises(M6SmokeError):
                run_official_smoke(
                    ROOT, config, allowed_m3_parent=self.m3_parent,
                    allowed_attempt_parent=self.attempt_parent,
                    allowed_selection_parent=self.selection_parent,
                    human_authorized=True, allow_test_doubles=True,
                    backend=self.backend(), clock=self.clock,
                )
            self.assertFalse(attempt.exists())

    def test_large_selected_m3_block_is_blocked_before_attempt_or_any_effect(self) -> None:
        large_m3 = self.m3_parent / "large-m3"
        large_run = _build_m3(large_m3, page_texts=("x" * 40_000,))
        large_selection = self.selection_parent / "selection-22345678-1234-4123-8123-123456789abc.json"
        create_context_selection(
            ROOT, large_m3, large_run, large_selection, [1],
            allowed_m3_parent=self.m3_parent,
            allowed_selection_parent=self.selection_parent,
        )
        attempt = self.attempt_parent / "attempt-22345678-1234-4123-8123-123456789abc"
        backend = self.backend()
        before = _tree_hash(large_m3)
        with self.assertRaisesRegex(M6SmokeError, "before attempt creation"):
            run_official_smoke(
                ROOT, SmokeConfig.from_mapping(self.mapping(
                    m3_root=str(large_m3), m3_run_id=large_run,
                    selection_manifest=str(large_selection), attempt_root=str(attempt),
                )), allowed_m3_parent=self.m3_parent,
                allowed_attempt_parent=self.attempt_parent,
                allowed_selection_parent=self.selection_parent,
                human_authorized=True, allow_test_doubles=True,
                backend=backend, clock=self.clock,
            )
        self.assertFalse(attempt.exists(), "regression: the old flow created the attempt before overflow")
        self.assertEqual([], backend.calls)
        self.assertEqual(before, _tree_hash(large_m3))
        self.assertFalse(any(self.attempt_parent.rglob("routes")))
        self.assertFalse(any(self.attempt_parent.rglob("budgets")))
        self.assertFalse(any(self.attempt_parent.rglob("receipts")))

    def test_preflight_materializes_exact_prompt_without_creating_attempt(self) -> None:
        result = preflight_official_smoke(
            ROOT, SmokeConfig.from_mapping(self.mapping()),
            allowed_m3_parent=self.m3_parent,
            allowed_attempt_parent=self.attempt_parent,
            allowed_selection_parent=self.selection_parent,
            clock=self.clock,
        )
        self.assertEqual("READY", result["status"])
        self.assertFalse(result["attempt_created"])
        self.assertFalse(self.attempt.exists())
        admission = result["admission"]
        self.assertEqual(
            admission["total_admission_tokens"],
            admission["estimated_input_tokens"]
            + admission["reserved_output_tokens"]
            + admission["overhead_tokens"],
        )
        self.assertEqual(CONTEXT_OVERHEAD_TOKENS, admission["overhead_tokens"])
        self.assertLessEqual(admission["total_admission_tokens"], admission["context_limit"])

    def test_selection_missing_tampered_unsafe_or_noncanonical_blocks_before_attempt(self) -> None:
        with self.assertRaisesRegex(M6SmokeError, "selection paths"):
            SmokeConfig.from_mapping(self.mapping(selection_manifest=None))

        original = json.loads(self.selection.read_text(encoding="utf-8"))
        variants: list[tuple[str, Callable[[dict[str, object]], None]]] = [
            ("hash", lambda value: value.__setitem__("selection_hash", "0" * 64)),
            ("locator", lambda value: value["units"][0].__setitem__("locator", "readonly:/etc/passwd")),  # type: ignore[index,union-attr]
            ("incomplete", lambda value: value.pop("units")),
        ]
        for index, (name, mutate) in enumerate(variants):
            path = self.selection_parent / f"selection-32345678-1234-4123-8123-123456789ab{index}.json"
            value = json.loads(json.dumps(original))
            value["selection_id"] = path.stem
            mutate(value)
            path.write_bytes(canonical_bytes(value) + b"\n")
            attempt = self.attempt_parent / f"attempt-32345678-1234-4123-8123-123456789ab{index}"
            with self.subTest(name=name), self.assertRaises(M6SmokeError):
                run_official_smoke(
                    ROOT, SmokeConfig.from_mapping(self.mapping(
                        selection_manifest=str(path), attempt_root=str(attempt),
                    )), allowed_m3_parent=self.m3_parent,
                    allowed_attempt_parent=self.attempt_parent,
                    allowed_selection_parent=self.selection_parent,
                    human_authorized=True, allow_test_doubles=True,
                    backend=self.backend(), clock=self.clock,
                )
            self.assertFalse(attempt.exists())

        content_hash_path = self.selection_parent / "selection-32345678-1234-4123-8123-123456789ab3.json"
        content_hash_value = json.loads(json.dumps(original))
        content_hash_value["selection_id"] = content_hash_path.stem
        content_hash_value["units"][0]["content_sha256"] = "f" * 64
        content_hash_value["selection_hash"] = hashlib.sha256(canonical_bytes({
            key: value for key, value in content_hash_value.items()
            if key != "selection_hash"
        })).hexdigest()
        content_hash_path.write_bytes(canonical_bytes(content_hash_value) + b"\n")
        content_hash_attempt = self.attempt_parent / "attempt-32345678-1234-4123-8123-123456789ab3"
        with self.assertRaisesRegex(M6SmokeError, "canonical M3 block"):
            run_official_smoke(
                ROOT, SmokeConfig.from_mapping(self.mapping(
                    selection_manifest=str(content_hash_path),
                    attempt_root=str(content_hash_attempt),
                )), allowed_m3_parent=self.m3_parent,
                allowed_attempt_parent=self.attempt_parent,
                allowed_selection_parent=self.selection_parent,
                human_authorized=True, allow_test_doubles=True,
                backend=self.backend(), clock=self.clock,
            )
        self.assertFalse(content_hash_attempt.exists())

        outside = self.base / "selection-42345678-1234-4123-8123-123456789abc.json"
        outside.write_bytes(self.selection.read_bytes())
        with self.assertRaisesRegex(M6SmokeError, "direct selection"):
            preflight_official_smoke(
                ROOT, SmokeConfig.from_mapping(self.mapping(selection_manifest=str(outside))),
                allowed_m3_parent=self.m3_parent,
                allowed_attempt_parent=self.attempt_parent,
                allowed_selection_parent=self.selection_parent,
                clock=self.clock,
            )
        linked = self.selection_parent / "selection-52345678-1234-4123-8123-123456789abc.json"
        linked.symlink_to(self.selection)
        with self.assertRaisesRegex(M6SmokeError, "symlink"):
            preflight_official_smoke(
                ROOT, SmokeConfig.from_mapping(self.mapping(selection_manifest=str(linked))),
                allowed_m3_parent=self.m3_parent,
                allowed_attempt_parent=self.attempt_parent,
                allowed_selection_parent=self.selection_parent,
                clock=self.clock,
            )

    def test_cli_pre_attempt_failure_is_structured_json_without_traceback(self) -> None:
        from scripts import m6_official_smoke as cli
        argv = [
            "--m3-root", str(self.m3), "--m3-run-id", self.run_id,
            "--attempt-root", str(self.attempt),
            "--selection-manifest", str(self.selection), "--role", "W11",
            "--model", "operator-model",
            "--endpoint", "http://127.0.0.1:11434/v1/chat/completions",
            "--deadline-utc", "2026-01-01T00:10:00Z",
            "--timeout-seconds", "30", "--context-limit", "8192",
            "--max-output-tokens", "512", "--preflight-only",
        ]
        output = io.StringIO()
        with mock.patch.object(
            cli, "preflight_official_smoke",
            side_effect=M6SmokeError("selected M3 context exceeds context_limit before attempt creation"),
        ), redirect_stdout(output):
            code = cli.main(argv)
        value = json.loads(output.getvalue())
        self.assertEqual(2, code)
        self.assertEqual("BLOCKED", value["status"])
        self.assertNotIn("Traceback", output.getvalue())

    def test_selection_generator_is_inert_without_create(self) -> None:
        output = self.selection_parent / "selection-62345678-1234-4123-8123-123456789abc.json"
        result = subprocess.run(
            [
                sys.executable, str(ROOT / "scripts/m6_context_selection.py"),
                "--m3-root", str(self.m3), "--m3-run-id", self.run_id,
                "--output", str(output), "--page", "1",
            ], cwd=ROOT, check=False, text=True, capture_output=True,
        )
        self.assertEqual(0, result.returncode)
        self.assertEqual("DISABLED", json.loads(result.stdout)["status"])
        self.assertFalse(output.exists())
        with self.assertRaisesRegex(M6SmokeError, "already exists"):
            create_context_selection(
                ROOT, self.m3, self.run_id, self.selection, [1],
                allowed_m3_parent=self.m3_parent,
                allowed_selection_parent=self.selection_parent,
            )
        with self.assertRaisesRegex(M6SmokeError, "unique"):
            create_context_selection(
                ROOT, self.m3, self.run_id, output, [1, 1],
                allowed_m3_parent=self.m3_parent,
                allowed_selection_parent=self.selection_parent,
            )

    def test_source_ready_hash_symlink_and_traversal_fail_before_backend(self) -> None:
        cases: list[tuple[str, Callable[[Path], str]]] = []
        cases.append(("state", lambda root: _build_m3(root, source_ready=False)))
        def corrupt(root: Path) -> str:
            run = _build_m3(root)
            digest = run.removeprefix("ingest-")
            (root / "artifacts/extracted" / digest / "text.txt").write_text("changed", encoding="utf-8")
            return run
        cases.append(("hash", corrupt))
        def symlink(root: Path) -> str:
            run = _build_m3(root)
            digest = run.removeprefix("ingest-")
            text = root / "artifacts/extracted" / digest / "text.txt"
            text.unlink(); text.symlink_to("/etc/passwd")
            return run
        cases.append(("symlink", symlink))
        for index, (name, mutate) in enumerate(cases):
            bad = self.m3_parent / f"bad-{name}"
            run = mutate(bad)
            attempt = self.attempt_parent / f"attempt-22345678-1234-4123-8123-123456789ab{index}"
            backend = self.backend()
            with self.subTest(name=name), self.assertRaises((M6SmokeError, IngestionError)):
                run_official_smoke(
                    ROOT, SmokeConfig.from_mapping(self.mapping(
                        m3_root=str(bad), m3_run_id=run, attempt_root=str(attempt),
                    )), allowed_m3_parent=self.m3_parent,
                    allowed_attempt_parent=self.attempt_parent,
                    allowed_selection_parent=self.selection_parent,
                    human_authorized=True, allow_test_doubles=True,
                    backend=backend, clock=self.clock,
                )
            self.assertEqual([], backend.calls)
            self.assertFalse(attempt.exists())
        outside = self.base / "outside"
        outside.mkdir()
        with self.assertRaisesRegex(M6SmokeError, "direct child"):
            run_official_smoke(
                ROOT, SmokeConfig.from_mapping(self.mapping(m3_root=str(outside))),
                allowed_m3_parent=self.m3_parent,
                allowed_attempt_parent=self.attempt_parent,
                allowed_selection_parent=self.selection_parent,
                human_authorized=True, allow_test_doubles=True,
                backend=self.backend(), clock=self.clock,
            )

    def test_success_preserves_real_order_receipt_reconciliation_and_stop(self) -> None:
        seen: dict[str, object] = {}
        outer = self
        class OrderedBackend(FakeInferenceBackend):
            def complete(self, request, target):  # type: ignore[no-untyped-def]
                route_dir = outer.attempt / "state/inference" / request.run_id / "routes"
                seen["route"] = bool(list(route_dir.glob("*.json")))
                seen["status"] = _budget_events(outer.attempt, request.run_id)[-1]["event_type"]
                return super().complete(request, target)
        backend = OrderedBackend(result=self.backend().result)
        result = self.execute_smoke(backend)
        self.assertEqual("STOPPED_AFTER_ONE_TASK", result["status"])
        self.assertEqual({"route": True, "status": "ADMITTED"}, seen)
        self.assertTrue(result["receipt_created"])
        self.assertTrue(result["reconciled"])
        events = _budget_events(self.attempt, str(result["run_id"]))
        kinds = [event["event_type"] for event in events]
        self.assertLess(kinds.index("RESERVED"), kinds.index("ADMITTED"))
        self.assertLess(kinds.index("ADMITTED"), kinds.index("RECONCILED"))
        self.assertEqual("STOPPED", kinds[-1])
        self.assertEqual(1, len(backend.calls))
        self.assertFalse((self.attempt / "versions/challengers").exists())

    def test_persisted_selection_and_admission_are_exactly_the_prompt_inputs(self) -> None:
        result = self.execute_smoke(self.backend())
        persisted = self.attempt / "inputs/context-selection.json"
        self.assertEqual(self.selection.read_bytes(), persisted.read_bytes())
        manifest = json.loads(persisted.read_text(encoding="utf-8"))
        prompt = (self.attempt / "inputs/prompt.txt").read_bytes()
        prompt_manifest = json.loads(
            (self.attempt / "inputs/prompt-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(hashlib.sha256(self.selection.read_bytes()).hexdigest(), prompt_manifest["selection_manifest_sha256"])
        self.assertEqual(manifest["selection_hash"], prompt_manifest["selection_hash"])
        self.assertEqual(hashlib.sha256(prompt).hexdigest(), prompt_manifest["prompt_sha256"])
        admission = prompt_manifest["admission"]
        self.assertEqual(len(prompt), admission["compiled_prompt_and_context_bytes"])
        self.assertEqual(
            admission["total_admission_tokens"],
            prompt_manifest["estimated_tokens"]
            + self.mapping()["max_output_tokens"] + CONTEXT_OVERHEAD_TOKENS,
        )
        self.assertEqual("STOPPED_AFTER_ONE_TASK", result["status"])

    def test_m3_and_selection_are_revalidated_immediately_before_route(self) -> None:
        import article_loop.m6_smoke as smoke_module
        calls = 0
        original = smoke_module._source_binding

        def observed(*args, **kwargs):  # type: ignore[no-untyped-def]
            nonlocal calls
            calls += 1
            return original(*args, **kwargs)

        with mock.patch.object(smoke_module, "_source_binding", side_effect=observed):
            result = self.execute_smoke(self.backend())
        self.assertEqual("STOPPED_AFTER_ONE_TASK", result["status"])
        self.assertEqual(2, calls)

    def test_post_attempt_pre_backend_selection_failure_gets_terminal_outcome(self) -> None:
        import article_loop.m6_smoke as smoke_module
        original = smoke_module._load_selection
        calls = 0

        def change_after_attempt(*args, **kwargs):  # type: ignore[no-untyped-def]
            nonlocal calls
            calls += 1
            if calls == 2:
                raise M6SmokeError("selection changed while the smoke was prepared")
            return original(*args, **kwargs)

        backend = self.backend()
        with mock.patch.object(smoke_module, "_load_selection", side_effect=change_after_attempt):
            result = self.execute_smoke(backend)
        self.assertEqual("FAILED_CLOSED", result["status"])
        self.assertEqual([], backend.calls)
        self.assertTrue((self.attempt / "outcome.json").is_file())
        self.assertEqual(0, result["calls"])

    def test_pre_send_failure_has_no_receipt_or_confirmed_spend(self) -> None:
        backend = self.backend(failure="pre_send_failure")
        result = self.execute_smoke(backend)
        self.assertEqual("FAILED_PRE_SEND", result["status"])
        self.assertFalse(result["receipt_created"])
        receipts = self.attempt / "state/inference" / result["run_id"] / "receipts"
        self.assertEqual([], list(receipts.glob("*.json")))
        events = _budget_events(self.attempt, str(result["run_id"]))
        confirmed_cost = sum(
            int(event["payload"].get("cost_microunits") or 0)  # type: ignore[union-attr]
            for event in events if event["event_type"] == "RECONCILED"
        )
        self.assertEqual(0, confirmed_cost)
        self.assertEqual(1, len(backend.calls))

    def test_post_send_ambiguity_stays_uncertain_without_retry_or_refund(self) -> None:
        backend = self.backend(failure="timeout")
        result = self.execute_smoke(backend)
        self.assertEqual("UNCERTAIN", result["status"])
        events = _budget_events(self.attempt, str(result["run_id"]))
        self.assertEqual("UNCERTAIN", [event["event_type"] for event in events if event["event_type"] in {"RECONCILED", "RELEASED", "UNCERTAIN"}][-1])
        self.assertEqual(1, len(backend.calls))
        kinds = [event["event_type"] for event in events]
        self.assertNotIn("RELEASED", kinds)
        self.assertFalse(result["retry_performed"])
        self.assertFalse(result["refund_performed"])

    def test_existing_attempt_and_m3_evidence_are_not_modified(self) -> None:
        existing = self.attempt_parent / "attempt-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        existing.mkdir(); (existing / "marker").write_text("preserve", encoding="utf-8")
        before_existing = _tree_hash(existing)
        before_m3 = _tree_hash(self.m3)
        self.execute_smoke(self.backend())
        completed = _tree_hash(self.attempt)
        with self.assertRaisesRegex(M6SmokeError, "already exists"):
            self.execute_smoke(self.backend())
        self.assertEqual(before_existing, _tree_hash(existing))
        self.assertEqual(before_m3, _tree_hash(self.m3))
        self.assertEqual(completed, _tree_hash(self.attempt))


if __name__ == "__main__":
    unittest.main()
