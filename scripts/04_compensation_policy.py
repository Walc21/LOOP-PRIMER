#!/usr/bin/env python3
"""Thin JSON-in / JSON-out CLI for the deterministic M10 policy."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime/agent/skills/article-loop/src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop.policy import PolicyError, decide


def _params(input_path: str | None) -> dict[str, Any]:
    if input_path is None:
        return {}
    raw = sys.stdin.read() if input_path == "-" else Path(input_path).read_text(encoding="utf-8")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("input JSON must be an object")
    if set(value) - {"root", "run_id", "cycle_id"}:
        raise ValueError("input JSON has unsupported parameters")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="M10 deterministic compensation policy")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--run-id")
    parser.add_argument("--cycle-id", type=int, default=None)
    parser.add_argument("--input", default=None, help="JSON file or '-' for stdin")
    args = parser.parse_args()
    try:
        params = _params(args.input)
        root_value = params.get("root", args.root)
        run_id = params.get("run_id", args.run_id)
        cycle_id = params.get("cycle_id", args.cycle_id)
        if not isinstance(root_value, str) or not root_value:
            raise ValueError("root must be a non-empty string")
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("run_id is required")
        if cycle_id is not None and (isinstance(cycle_id, bool) or not isinstance(cycle_id, int) or cycle_id < 0):
            raise ValueError("cycle_id must be a non-negative integer")
        decision = decide(Path(root_value).resolve(), run_id, cycle_id=cycle_id)
        sys.stdout.write(json.dumps({"status": "success", "decision": decision}, indent=2) + "\n")
        return 0
    except ValueError as exc:
        sys.stderr.write(json.dumps({"status": "error", "error_type": "input_error", "message": str(exc)}) + "\n")
        return 1
    except PolicyError as exc:
        sys.stderr.write(json.dumps({"status": "error", "error_type": "policy_error", "message": str(exc)}) + "\n")
        return 2
    except Exception as exc:
        sys.stderr.write(json.dumps({"status": "error", "error_type": "unexpected_error", "message": str(exc)}) + "\n")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
