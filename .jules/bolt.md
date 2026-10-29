## 2024-10-23 - JSON Schema Validator Caching
**Learning:** `jsonschema.Draft202012Validator` initialization is relatively expensive (around 0.2ms - 3ms depending on schema complexity). It is used heavily in `article-loop` (22 instances), and because it takes an arbitrary dictionary (which isn't directly hashable in Python), caching is missed.
**Action:** When working with JSON schema validations that happen in loops or hot paths, cache the validator instances using `functools.lru_cache` and `json.dumps(schema, sort_keys=True)`. Using an object ID (`id(schema)`) lookup table in combination with the string hash cache makes it exponentially faster for identical dictionary instances.

## 2024-11-20 - Safe JSON Schema Validator Caching
**Learning:** `jsonschema.Draft202012Validator` initialization is a CPU-intensive operation involving rule compilation and reference resolution. However, dictionary-based schemas can't be safely cached using `id()` (due to Python recycling memory addresses of garbage-collected objects).
**Action:** Safely cache dictionary-based validators using an `lru_cache` and by serializing the schema dict to a stable JSON string (`json.dumps(schema, sort_keys=True)`) to use as the cache key. A `TypeError` fallback ensures objects that aren't JSON-serializable don't break existing functionality.
