"""Public API."""
from .state_machine import State, TransitionError
from .store import DurableStore, IntegrityError, StopRequested, StoreError
__version__ = "0.2.0"
async def run(*args, **kwargs):
    raise RuntimeError("article-loop orchestration is not implemented before M6")
__all__ = ["DurableStore", "IntegrityError", "State", "StopRequested", "StoreError", "TransitionError", "run"]
