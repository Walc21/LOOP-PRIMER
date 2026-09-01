#!/usr/bin/env python3
"""Thin CLI wrapper for M8 external blind evaluation (JSON-in / JSON-out)."""
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

from article_loop.evaluation import (
    EvaluationError,
    FakeJurorAdapter,
    FakeMetaReviewerAdapter,
    evaluate_candidate,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="M8 External Blind Evaluator CLI")
    parser.add_argument("--root", type=str, default=str(ROOT), help="Project root directory")
    parser.add_argument("--run-id", type=str, help="Canonical run identifier")
    parser.add_argument("--cycle-id", type=int, default=None, help="Cycle number (0-indexed)")
    parser.add_argument("--candidate-id", type=str, default=None, help="Candidate ID (e.g. v0001)")
    parser.add_argument("--gate-report-locator", type=str, default=None, help="Relative path to GateReport")
    parser.add_argument("--order-seed", type=int, default=413, help="Seed for candidate presentation")
    parser.add_argument("--test-mode", action="store_true", help="Enable test harness mode with controlled test adapters")
    parser.add_argument("--test-winner", type=str, default=None, choices=["A", "B", "tie", "inconclusive"], help="Preferred winner for test mode")
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
    gate_report_locator = params.get("gate_report_locator", args.gate_report_locator)
    order_seed = params.get("order_seed", args.order_seed)
    test_mode = args.test_mode
    test_winner = args.test_winner

    if not isinstance(run_id, str) or not run_id:
        err = {"status": "error", "error_type": "missing_parameter", "message": "--run-id is required"}
        sys.stderr.write(json.dumps(err, indent=2) + "\n")
        return 1

    juror_adapters = None
    meta_adapter = None
    if test_mode:
        juror_adapters = {
            "juror-math": FakeJurorAdapter(juror_id="juror-math", specialty="correctness_math", preferred_winner=test_winner),
            "juror-contrib": FakeJurorAdapter(juror_id="juror-contrib", specialty="scientific_contribution", preferred_winner=test_winner),
            "juror-clarity": FakeJurorAdapter(juror_id="juror-clarity", specialty="clarity", preferred_winner=test_winner),
        }
        meta_adapter = FakeMetaReviewerAdapter()

    try:
        report = evaluate_candidate(
            root=root,
            run_id=run_id,
            cycle_id=cycle_id,
            candidate_id=candidate_id,
            gate_report_locator=gate_report_locator,
            order_seed=order_seed,
            juror_adapters=juror_adapters,
            meta_adapter=meta_adapter,
            allow_test_doubles=test_mode,
        )
        sys.stdout.write(json.dumps({"status": "success", "report": report}, indent=2) + "\n")
        return 0
    except EvaluationError as exc:
        err = {"status": "error", "error_type": "evaluation_error", "message": str(exc)}
        sys.stderr.write(json.dumps(err, indent=2) + "\n")
        return 2
    except Exception as exc:
        err = {"status": "error", "error_type": "unexpected_error", "message": str(exc)}
        sys.stderr.write(json.dumps(err, indent=2) + "\n")
        return 3


if __name__ == "__main__":
    sys.exit(main())
