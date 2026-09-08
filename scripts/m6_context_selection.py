#!/usr/bin/env python3
"""Create a canonical explicit M3 page or line-segment selection for M6."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime" / "agent" / "skills" / "article-loop" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop.m6_smoke import M6SmokeError, create_context_selection


_SEGMENT = re.compile(r"([1-9][0-9]{0,3}):([0-9]{1,6}):([0-9]{1,6})\Z")


def _segment(value: str) -> tuple[int, int, int]:
    match = _SEGMENT.fullmatch(value)
    if match is None:
        raise M6SmokeError("segment must use numeric PAGE:LINE_START:LINE_END")
    return tuple(int(number) for number in match.groups())  # type: ignore[return-value]


def _relative_cli_path(value: str, *, label: str) -> None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value:
        raise M6SmokeError(f"{label} must be a contained relative path")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3-root", required=True)
    parser.add_argument("--m3-run-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--page", action="append", type=int, default=[])
    parser.add_argument(
        "--segment", action="append", default=[],
        metavar="PAGE:LINE_START:LINE_END",
        help="inclusive canonical M3 line segment; repeat for multiple segments",
    )
    parser.add_argument(
        "--create", action="store_true",
        help="perform the create-only manifest publication; false by default",
    )
    args = parser.parse_args(argv)
    if not args.create:
        print(json.dumps({"status": "DISABLED", "created": False}, sort_keys=True))
        return 0
    try:
        _relative_cli_path(args.m3_root, label="M3 root")
        _relative_cli_path(args.output, label="selection output")
        segments = [_segment(value) for value in args.segment]
        result = create_context_selection(
            ROOT, args.m3_root, args.m3_run_id, args.output, args.page,
            segments=segments,
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
