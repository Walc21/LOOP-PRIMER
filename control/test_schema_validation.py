"""Strict, dependency-independent RFC 3339 schema validation tests."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime/agent/skills/article-loop/src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop.schema_validation import is_rfc3339_datetime, validator  # noqa: E402


class StrictSchemaValidationTests(unittest.TestCase):
    def test_accepts_complete_rfc3339_timestamps(self) -> None:
        for value in (
            "2026-09-18T12:34:56Z",
            "2026-09-18t12:34:56.123456+00:00",
            "2024-02-29T23:59:59-03:30",
            "1990-12-31T23:59:60Z",
        ):
            with self.subTest(value=value):
                self.assertTrue(is_rfc3339_datetime(value))

    def test_rejects_invalid_or_incomplete_dates_without_optional_extras(self) -> None:
        schema = {"type": "string", "format": "date-time"}
        for value in (
            "not-a-date",
            "2026-09-18",
            "2026-09-18T12:34:56",
            "2026-02-29T12:34:56Z",
            "2026-09-18 12:34:56Z",
            "2026-09-18T24:00:00Z",
            "2026-09-18T12:34:56+24:00",
        ):
            with self.subTest(value=value):
                with self.assertRaises(jsonschema.ValidationError):
                    validator(schema).validate(value)

    def test_all_schema_boundaries_use_the_common_validator(self) -> None:
        package = SRC / "article_loop"
        for name in (
            "prompts.py", "synthesis.py", "evaluation.py", "execution.py",
            "inference.py", "policy.py", "m6_smoke.py", "routed_evaluation.py",
            "control_center.py", "orchestrator.py",
        ):
            with self.subTest(name=name):
                source = (package / name).read_text(encoding="utf-8")
                self.assertIn("from .schema_validation import", source)
                self.assertNotIn("format_checker=jsonschema.FormatChecker()", source)
                self.assertNotIn("Draft202012Validator(schema).validate", source)


if __name__ == "__main__":
    unittest.main()
