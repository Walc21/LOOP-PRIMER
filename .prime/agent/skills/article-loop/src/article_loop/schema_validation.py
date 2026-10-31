"""Project-owned JSON Schema validation with strict RFC 3339 dates.

The checker is registered locally so validation does not depend on the optional
``jsonschema[format]`` extras installed in a particular environment.
"""
from __future__ import annotations

import collections
import functools
import json
from datetime import date, datetime
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


# Cache by object ID to avoid hashing dictionaries (unhashable) in the fast path.
_schema_cache_by_id: collections.OrderedDict[int, tuple[Any, jsonschema.Draft202012Validator]] = collections.OrderedDict()
MAX_CACHE_SIZE = 128

@functools.lru_cache(maxsize=MAX_CACHE_SIZE)
def _validator_from_json(schema_json: str) -> jsonschema.Draft202012Validator:
    """Fallback cache using canonical JSON string for structurally identical schemas."""
    schema = json.loads(schema_json)
    return jsonschema.Draft202012Validator(
        schema, format_checker=STRICT_FORMAT_CHECKER,
    )


def validator(schema: Mapping[str, Any]) -> jsonschema.Draft202012Validator:
    """Build the only Draft 2020-12 instance validator used by the package.

    Optimized: Draft202012Validator initialization is expensive (~0.2ms - 3ms).
    This caches instances to prevent redundant initializations in hot loops.

    WARNING: This cache assumes `schema` objects are immutable throughout their lifecycle.
    Mutating a cached schema dictionary will result in validation against the old state.
    """
    schema_id = id(schema)

    # Fast path: check if the exact same dictionary object was already seen.
    # The identity check `cached_schema is schema` prevents collisions if Python reuses memory addresses.
    if schema_id in _schema_cache_by_id:
        cached_schema, cached_validator = _schema_cache_by_id[schema_id]
        if cached_schema is schema:
            _schema_cache_by_id.move_to_end(schema_id)
            return cached_validator

    # Slow path / fallback: serialize schema to a canonical JSON string to use as cache key for identical values
    try:
        schema_json = json.dumps(schema, sort_keys=True)
    except TypeError:
        # Fallback if the schema contains un-serializable objects (e.g. custom types)
        return jsonschema.Draft202012Validator(
            schema, format_checker=STRICT_FORMAT_CHECKER,
        )

    val = _validator_from_json(schema_json)

    # Update object ID cache
    _schema_cache_by_id[schema_id] = (schema, val)
    if len(_schema_cache_by_id) > MAX_CACHE_SIZE:
        _schema_cache_by_id.popitem(last=False)

    return val
