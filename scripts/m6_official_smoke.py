#!/usr/bin/env python3
"""Run one create-only, local, routed M6 task after explicit authorization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime" / "agent" / "skills" / "article-loop" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop.m6_smoke import (
    M6SmokeError, SmokeConfig, preflight_official_smoke, run_official_smoke,
)
from article_loop.inference_backends import OPENAI_CHAT_COMPLETIONS_JSON_SCHEMA


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3-root", required=True)
    parser.add_argument("--m3-run-id", required=True)
    parser.add_argument("--attempt-root", required=True)
    parser.add_argument("--selection-manifest")
    parser.add_argument("--role", choices=("S10", "W11"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument(
        "--structured-output-dialect",
        choices=(OPENAI_CHAT_COMPLETIONS_JSON_SCHEMA,), required=True,
    )
    parser.add_argument("--deadline-utc", required=True)
    parser.add_argument("--timeout-seconds", required=True, type=int)
    parser.add_argument("--context-limit", required=True, type=int)
    parser.add_argument("--max-output-tokens", required=True, type=int)
    parser.add_argument(
        "--execute", action="store_true",
        help="enable this invocation; false by default",
    )
    parser.add_argument(
        "--human-authorized", action="store_true",
        help="fresh boolean authorization for this one invocation",
    )
    parser.add_argument(
        "--preflight-only", action="store_true",
        help="validate exact selection and admission without creating an attempt",
    )
    args = parser.parse_args(argv)
    try:
        config = SmokeConfig.from_mapping({
            "schema_version": "1.1.0", "enabled": args.execute,
            "m3_root": args.m3_root, "m3_run_id": args.m3_run_id,
            "attempt_root": args.attempt_root, "role_id": args.role,
            "selection_manifest": args.selection_manifest,
            "model": args.model, "endpoint": args.endpoint,
            "structured_output_dialect": args.structured_output_dialect,
            "deadline_utc": args.deadline_utc,
            "timeout_seconds": args.timeout_seconds,
            "context_limit": args.context_limit,
            "max_output_tokens": args.max_output_tokens,
            "max_calls": 1, "max_concurrency": 1, "max_retries": 0,
            "max_cycles": 1, "max_cost_microunits": 0,
            "deny_remote": True,
        })
        common = {
            "allowed_m3_parent": ROOT / "runtime" / "m3-real-attempts",
            "allowed_attempt_parent": ROOT / "runtime" / "m6-official-smokes",
            "allowed_selection_parent": ROOT / "runtime" / "m6-context-selections",
        }
        if args.preflight_only:
            result = preflight_official_smoke(ROOT, config, **common)
        else:
            result = run_official_smoke(
                ROOT, config, **common,
                human_authorized=args.human_authorized,
            )
    except M6SmokeError as error:
        print(json.dumps({"status": "BLOCKED", "cause": str(error)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
