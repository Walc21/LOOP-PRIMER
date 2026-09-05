#!/usr/bin/env python3
"""Offline system acceptance, optionally retain or independently audit evidence."""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--keep-workspace", type=Path, help="create a NEW synthetic evidence workspace after acceptance")
    group.add_argument("--verify-root", type=Path, help="read-only audit of an existing completed cycle")
    parser.add_argument("--run-id")
    parser.add_argument("--cycle-id", type=int, default=0)
    args = parser.parse_args(argv)
    if args.verify_root is not None and not args.run_id:
        parser.error("--verify-root requires --run-id")
    if args.verify_root is None and (args.run_id is not None or args.cycle_id != 0):
        parser.error("--run-id/--cycle-id apply only to --verify-root")
    from article_loop.delivery import verify_delivery
    try:
        if args.verify_root is not None:
            print(json.dumps(verify_delivery(args.verify_root, args.run_id, cycle_id=args.cycle_id), sort_keys=True, indent=2))
            return 0
        if args.keep_workspace is not None and (args.keep_workspace.exists() or args.keep_workspace.is_symlink()):
            raise ValueError("--keep-workspace must name a new path; existing output is preserved")
        suite = unittest.defaultTestLoader.loadTestsFromName("control.test_m13_system_delivery")
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        print(stream.getvalue(), file=sys.stderr, end="")
        passed = result.wasSuccessful() and not result.skipped and result.testsRun > 0
        output = {"milestone": "M13", "status": "pass" if passed else "fail", "offline": True, "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped)}
        if passed and args.keep_workspace is not None:
            from control.m13_fixture import SyntheticCycle, canonical
            fixture = SyntheticCycle(args.keep_workspace, routed=True)
            fixture.run()
            report = verify_delivery(fixture.root, fixture.run_id)
            path = fixture.root / "reports/m13-delivery.json"
            with path.open("xb") as file:
                file.write(canonical(report) + b"\n")
                file.flush()
                os.fsync(file.fileno())
            path.chmod(0o444)
            descriptor = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            output["delivery"] = report
            output["workspace"] = str(fixture.root.resolve())
        print(json.dumps(output, sort_keys=True, indent=2))
        return 0 if passed else 1
    except Exception as exc:
        print(json.dumps({"milestone": "M13", "status": "fail", "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
