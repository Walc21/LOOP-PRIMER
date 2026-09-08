#!/usr/bin/env python3
"""Create a canonical, explicit M3 block selection for the official M6 smoke."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime" / "agent" / "skills" / "article-loop" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop.m6_smoke import M6SmokeError, create_context_selection


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3-root", required=True)
    parser.add_argument("--m3-run-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--page", action="append", type=int, default=[])
    parser.add_argument(
        "--create", action="store_true",
        help="perform the create-only manifest publication; false by default",
    )
    args = parser.parse_args(argv)
    if not args.create:
        print(json.dumps({"status": "DISABLED", "created": False}, sort_keys=True))
        return 0
    try:
        result = create_context_selection(
            ROOT, args.m3_root, args.m3_run_id, args.output, args.page,
            allowed_m3_parent=ROOT / "runtime" / "m3-real-attempts",
            allowed_selection_parent=ROOT / "runtime" / "m6-context-selections",
        )
    except M6SmokeError as error:
        print(json.dumps({"status": "BLOCKED", "cause": str(error)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
