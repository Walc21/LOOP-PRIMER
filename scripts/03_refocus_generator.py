#!/usr/bin/env python3
"""Thin CLI wrapper for M9 prompt refocus and overlay generation (JSON-in / JSON-out)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Ensure article_loop is importable from standard local locations
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime/agent/skills/article-loop/src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop.refocus import RefocusError, generate_refocus_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="M9 Prompt Refocus Generator CLI")
    parser.add_argument("--root", type=str, default=str(ROOT), help="Project root directory")
    parser.add_argument("--run-id", type=str, help="Canonical run identifier")
    parser.add_argument("--cycle-id", type=int, default=None, help="Cycle number (0-indexed)")
    parser.add_argument("--diagnosis-locator", type=str, default=None, help="Relative path to diagnosis JSON")
    parser.add_argument("--input", type=str, default=None, help="Path to input JSON file or '-' for stdin")

    args = parser.parse_args()

    # If --input is provided, read parameters from JSON
    params: dict[str, Any] = {}
    if args.input:
        try:
            if args.input == "-":
                raw = sys.stdin.read()
            else:
                raw = Path(args.input).read_text(encoding="utf-8")
            params = json.loads(raw)
            if not isinstance(params, dict):
                raise ValueError("input JSON must be an object")
        except Exception as exc:
            err = {"status": "error", "error_type": "input_parsing_error", "message": str(exc)}
            sys.stderr.write(json.dumps(err, indent=2) + "\n")
            return 1

    root_value = params.get("root", args.root)
    if not isinstance(root_value, str) or not root_value:
        err = {"status": "error", "error_type": "invalid_parameter", "message": "root must be a non-empty path string"}
        sys.stderr.write(json.dumps(err, indent=2) + "\n")
        return 1
    root = Path(root_value).resolve()
    run_id = params.get("run_id", args.run_id)
    cycle_id = params.get("cycle_id", args.cycle_id)
    diagnosis_locator = params.get("diagnosis_locator", args.diagnosis_locator)

    if not isinstance(run_id, str) or not run_id:
        err = {"status": "error", "error_type": "missing_parameter", "message": "--run-id is required"}
        sys.stderr.write(json.dumps(err, indent=2) + "\n")
        return 1

    if isinstance(cycle_id, bool) or not isinstance(cycle_id, int) or cycle_id < 0:
        err = {"status": "error", "error_type": "invalid_parameter", "message": "--cycle-id must be a non-negative integer"}
        sys.stderr.write(json.dumps(err, indent=2) + "\n")
        return 1

    canonical_locator = f"state/diagnosis/{run_id}/c{cycle_id:04d}/diagnosis.json"
    diagnosis: dict[str, Any] | None = None
    if diagnosis_locator:
        if diagnosis_locator != canonical_locator:
            err = {"status": "error", "error_type": "invalid_parameter", "message": "--diagnosis-locator must identify the canonical diagnosis for run/cycle"}
            sys.stderr.write(json.dumps(err, indent=2) + "\n")
            return 1
        diag_path = root / canonical_locator
        if not diag_path.exists():
            err = {"status": "error", "error_type": "file_not_found", "message": f"diagnosis file not found: {diagnosis_locator}"}
            sys.stderr.write(json.dumps(err, indent=2) + "\n")
            return 1
        try:
            diagnosis = json.loads(diag_path.read_text(encoding="utf-8"))
        except Exception as exc:
            err = {"status": "error", "error_type": "json_parse_error", "message": str(exc)}
            sys.stderr.write(json.dumps(err, indent=2) + "\n")
            return 1
    else:
        # Default locator
        default_diag_path = root / canonical_locator
        if default_diag_path.exists():
            try:
                diagnosis = json.loads(default_diag_path.read_text(encoding="utf-8"))
            except Exception as exc:
                err = {"status": "error", "error_type": "json_parse_error", "message": str(exc)}
                sys.stderr.write(json.dumps(err, indent=2) + "\n")
                return 1
        else:
            err = {"status": "error", "error_type": "diagnosis_not_found", "message": f"no diagnosis found for cycle {cycle_id}"}
            sys.stderr.write(json.dumps(err, indent=2) + "\n")
            return 1

    try:
        plan = generate_refocus_plan(
            root=root,
            run_id=run_id,
            cycle_id=cycle_id,
            diagnosis=diagnosis,
        )
        sys.stdout.write(json.dumps({"status": "success", "refocus_plan": plan}, indent=2) + "\n")
        return 0
    except RefocusError as exc:
        err = {"status": "error", "error_type": "refocus_error", "message": str(exc)}
        sys.stderr.write(json.dumps(err, indent=2) + "\n")
        return 2
    except Exception as exc:
        err = {"status": "error", "error_type": "unexpected_error", "message": str(exc)}
        sys.stderr.write(json.dumps(err, indent=2) + "\n")
        return 3


if __name__ == "__main__":
    sys.exit(main())
