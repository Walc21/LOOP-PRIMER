## 2024-10-23 - JSON Schema Validator Caching
**Learning:** `jsonschema.Draft202012Validator` initialization is relatively expensive (around 0.2ms - 3ms depending on schema complexity). It is used heavily in `article-loop` (22 instances), and because it takes an arbitrary dictionary (which isn't directly hashable in Python), caching is missed.
**Action:** When working with JSON schema validations that happen in loops or hot paths, cache the validator instances using `functools.lru_cache` and `json.dumps(schema, sort_keys=True)`. Using an object ID (`id(schema)`) lookup table in combination with the string hash cache makes it exponentially faster for identical dictionary instances.

## 2026-10-27 - Memoize JSON Schema Validator Initialization
**Learning:** Instantiating `jsonschema.Draft202012Validator` involves expensive internal compilation steps for each schema.
**Action:** When a project repeatedly validates payloads against the same set of schema dictionaries, use `@lru_cache` to memoize the validator creation. Serialize the dictionary to a string (`json.dumps(schema, sort_keys=True)`) to serve as a hashable cache key.
