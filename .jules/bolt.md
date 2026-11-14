## 2024-10-23 - JSON Schema Validator Caching
**Learning:** `jsonschema.Draft202012Validator` initialization is relatively expensive (around 0.2ms - 3ms depending on schema complexity). It is used heavily in `article-loop` (22 instances), and because it takes an arbitrary dictionary (which isn't directly hashable in Python), caching is missed.
**Action:** When working with JSON schema validations that happen in loops or hot paths, cache the validator instances using `functools.lru_cache` and `json.dumps(schema, sort_keys=True)`. Using an object ID (`id(schema)`) lookup table in combination with the string hash cache makes it exponentially faster for identical dictionary instances.

## 2024-10-26 - Immutable cache keys for JSON schema
**Learning:** Do not cache mutable unhashable objects (like dictionary schemas) using `id()` or object identity (`is`). Because dictionaries are mutable, in-place modifications retain the same `id` and reference, causing stale cache hits. Instead, serialize the dictionary to a deterministic string (e.g., `json.dumps(schema, sort_keys=True)`) and use `@lru_cache`.
**Action:** Always prefer stable serializations for cache keys over instance mapping caching when data is inherently mutable to prevent hard-to-debug data staleness, even when it sacrifices a tiny amount of micro-performance.
