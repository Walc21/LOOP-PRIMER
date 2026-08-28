#!/usr/bin/env python3
"""Thin CLI wrapper for M9 deterministic stagnation detection (JSON-in / JSON-out)."""
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

from article_loop.diagnosis import DiagnosisError, diagnose_cycle


def main() -> int:
    parser = argparse.ArgumentParser(description="M9 Stagnation Detector CLI")
    parser.add_argument("--root", type=str, default=str(ROOT), help="Project root directory")
    parser.add_argument("--run-id", type=str, help="Canonical run identifier")
    parser.add_argument("--cycle-id", type=int, default=None, help="Cycle number (0-indexed)")
    parser.add_argument("--candidate-id", type=str, default=None, help="Candidate ID (e.g. v0001)")
    parser.add_argument("--window-size", type=int, default=3, help="Sliding window size")
    parser.add_argument("--mde", type=float, default=0.25, help="Minimum Detectable Effect threshold")
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
    candidate_id = params.get("candidate_id", args.candidate_id)
    window_size = params.get("window_size", args.window_size)
    mde = params.get("mde", args.mde)

    if not isinstance(run_id, str) or not run_id:
        err = {"status": "error", "error_type": "missing_parameter", "message": "--run-id is required"}
        sys.stderr.write(json.dumps(err, indent=2) + "\n")
        return 1

    try:
        diagnosis = diagnose_cycle(
            root=root,
            run_id=run_id,
            cycle_id=cycle_id,
            candidate_id=candidate_id,
            window_size=window_size,
            mde=mde,
        )
        sys.stdout.write(json.dumps({"status": "success", "diagnosis": diagnosis}, indent=2) + "\n")
        return 0
    except DiagnosisError as exc:
        err = {"status": "error", "error_type": "diagnosis_error", "message": str(exc)}
        sys.stderr.write(json.dumps(err, indent=2) + "\n")
        return 2
    except Exception as exc:
        err = {"status": "error", "error_type": "unexpected_error", "message": str(exc)}
        sys.stderr.write(json.dumps(err, indent=2) + "\n")
        return 3


if __name__ == "__main__":
    sys.exit(main())
