"""Project-owned JSON Schema validation with strict RFC 3339 dates.

The checker is registered locally so validation does not depend on the optional
``jsonschema[format]`` extras installed in a particular environment.
"""
from __future__ import annotations

from datetime import date, datetime
import functools
import json
import re
from typing import Any, Mapping

import jsonschema


_RFC3339_DATE_TIME = re.compile(
    r"^(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})"
    r"[Tt](?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?P<fraction>\.[0-9]+)?"
    r"(?P<offset>[Zz]|[+-][0-9]{2}:[0-9]{2})$"
)


def is_rfc3339_datetime(value: object) -> bool:
    """Return whether *value* is a complete RFC 3339 date-time string."""
    if not isinstance(value, str):
        return False
    match = _RFC3339_DATE_TIME.fullmatch(value)
    if match is None:
        return False
    try:
        date.fromisoformat(match.group("date"))
    except ValueError:
        return False
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    second = int(match.group("second"))
    if hour > 23 or minute > 59 or second > 60:
        return False
    offset = match.group("offset")
    if offset not in {"Z", "z"}:
        offset_hour = int(offset[1:3])
        offset_minute = int(offset[4:6])
        if offset_hour > 23 or offset_minute > 59:
            return False
    try:
        normalized = value[:-1] + "+00:00" if value[-1] in "Zz" else value
        # Python rejects leap second 60, which RFC 3339 explicitly permits.
        parseable = normalized[:17] + "59" + normalized[19:] if second == 60 else normalized
        parsed = datetime.fromisoformat(parseable)
    except ValueError:
        return False
    return parsed.tzinfo is not None


STRICT_FORMAT_CHECKER = jsonschema.FormatChecker()
STRICT_FORMAT_CHECKER.checks("date-time")(is_rfc3339_datetime)


@functools.lru_cache(maxsize=128)
def _get_validator(schema_str: str) -> jsonschema.Draft202012Validator:
    schema = json.loads(schema_str)
    return jsonschema.Draft202012Validator(
        schema, format_checker=STRICT_FORMAT_CHECKER,
    )


import collections


class _IDCache:
    def __init__(self, maxsize: int = 128) -> None:
        self.cache: collections.OrderedDict[int, tuple[Mapping[str, Any], jsonschema.Draft202012Validator]] = collections.OrderedDict()
        self.maxsize = maxsize

    def get(self, schema_id: int, schema: Mapping[str, Any]) -> jsonschema.Draft202012Validator | None:
        if schema_id in self.cache:
            cached_schema, validator_instance = self.cache[schema_id]
            if cached_schema is schema:
                self.cache.move_to_end(schema_id)
                return validator_instance
        return None

    def set(self, schema_id: int, schema: Mapping[str, Any], validator_instance: jsonschema.Draft202012Validator) -> None:
        self.cache[schema_id] = (schema, validator_instance)
        if len(self.cache) > self.maxsize:
            self.cache.popitem(last=False)


_ID_CACHE = _IDCache(maxsize=128)


def validator(schema: Mapping[str, Any]) -> jsonschema.Draft202012Validator:
    """Build the only Draft 2020-12 instance validator used by the package."""
    schema_id = id(schema)
    validator_instance = _ID_CACHE.get(schema_id, schema)
    if validator_instance is not None:
        return validator_instance

    schema_str = json.dumps(schema, sort_keys=True)
    validator_instance = _get_validator(schema_str)
    _ID_CACHE.set(schema_id, schema, validator_instance)
    return validator_instance
