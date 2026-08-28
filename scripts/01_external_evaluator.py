#!/usr/bin/env python3
"""Thin CLI wrapper for M8 external blind evaluation (JSON-in / JSON-out)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure article_loop is importable from standard local locations
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime/agent/skills/article-loop/src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop.evaluation import EvaluationError, evaluate_candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="M8 External Blind Evaluator CLI")
    parser.add_argument("--root", type=str, default=str(ROOT), help="Project root directory")
    parser.add_argument("--run-id", type=str, help="Canonical run identifier")
    parser.add_argument("--cycle-id", type=int, default=None, help="Cycle number (0-indexed)")
    parser.add_argument("--candidate-id", type=str, default=None, help="Candidate ID (e.g. v0001)")
    parser.add_argument("--gate-report-locator", type=str, default=None, help="Relative path to GateReport")
    parser.add_argument("--order-seed", type=int, default=413, help="Seed for candidate presentation")
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
        except Exception as exc:
            err = {"status": "error", "error_type": "input_parsing_error", "message": str(exc)}
            sys.stderr.write(json.dumps(err, indent=2) + "\n")
            return 1

    root = Path(params.get("root", args.root)).resolve()
    run_id = params.get("run_id", args.run_id)
    cycle_id = params.get("cycle_id", args.cycle_id)
    candidate_id = params.get("candidate_id", args.candidate_id)
    gate_report_locator = params.get("gate_report_locator", args.gate_report_locator)
    order_seed = params.get("order_seed", args.order_seed)

    if not run_id:
        err = {"status": "error", "error_type": "missing_parameter", "message": "--run-id is required"}
        sys.stderr.write(json.dumps(err, indent=2) + "\n")
        return 1

    try:
        report = evaluate_candidate(
            root=root,
            run_id=run_id,
            cycle_id=cycle_id,
            candidate_id=candidate_id,
            gate_report_locator=gate_report_locator,
            order_seed=order_seed,
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
