"""Public API."""
from .state_machine import State, TransitionError
from .store import DurableStore, IntegrityError, StopRequested, StoreError
from .ingestion import IngestionError, SourceReadyError, ingest
__version__ = "0.2.0"
async def run(*args, **kwargs):
    raise RuntimeError("article-loop orchestration is not implemented before M6")
__all__ = ["DurableStore", "IngestionError", "IntegrityError", "SourceReadyError", "State", "StopRequested", "StoreError", "TransitionError", "ingest", "run"]
