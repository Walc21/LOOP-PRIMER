"""Project-local Prime Agent skill scaffold.

The orchestration contract is intentionally deferred to M6. This module never
starts agents or models in M1.
"""

__version__ = "0.1.0"


async def run() -> None:
    """Refuse execution until the orchestration milestone is implemented."""
    raise RuntimeError("article-loop orchestration is not implemented before M6")
