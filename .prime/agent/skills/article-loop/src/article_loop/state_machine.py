"""Canonical deterministic state transitions for the local event log."""

from enum import StrEnum


class State(StrEnum):
    NEW = "NEW"
    INGESTED = "INGESTED"
    SOURCE_READY = "SOURCE_READY"
    CYCLE_PLANNED = "CYCLE_PLANNED"
    DEPARTMENTS_RUNNING = "DEPARTMENTS_RUNNING"
    SYNTHESIS_READY = "SYNTHESIS_READY"
    CANDIDATE_BUILT = "CANDIDATE_BUILT"
    GATES_PASSED = "GATES_PASSED"
    EVALUATED = "EVALUATED"
    DIAGNOSED = "DIAGNOSED"
    DECIDED = "DECIDED"
    COMMITTING = "COMMITTING"
    CYCLE_COMPLETE = "CYCLE_COMPLETE"
    PAUSED = "PAUSED"
    FINALIZED = "FINALIZED"
    TECHNICAL_FAILURE = "TECHNICAL_FAILURE"


class TransitionError(ValueError):
    """Raised when an event does not follow the canonical state graph."""


_FORWARD = {
    State.NEW: State.INGESTED,
    State.INGESTED: State.SOURCE_READY,
    State.SOURCE_READY: State.CYCLE_PLANNED,
    State.CYCLE_PLANNED: State.DEPARTMENTS_RUNNING,
    State.DEPARTMENTS_RUNNING: State.SYNTHESIS_READY,
    State.SYNTHESIS_READY: State.CANDIDATE_BUILT,
    State.CANDIDATE_BUILT: State.GATES_PASSED,
    State.GATES_PASSED: State.EVALUATED,
    State.EVALUATED: State.DIAGNOSED,
    State.DIAGNOSED: State.DECIDED,
    State.DECIDED: State.COMMITTING,
    # M10 may complete a normal disposition, or directly freeze a fully
    # revalidated final version.  Both paths are explicit and replayable.
    State.COMMITTING: State.CYCLE_COMPLETE,
}
_TERMINAL = {State.FINALIZED, State.TECHNICAL_FAILURE}


def is_valid_transition(
    current: State, target: State, *, resume_to: State | None = None
) -> bool:
    """Return whether ``target`` may follow ``current``.

    A technical failure is a safe exit from every non-terminal state, including
    a pause.  A pause preserves one exact resumable state and cannot be used to
    bypass the forward graph.
    """
    if current in _TERMINAL:
        return False
    if target is State.TECHNICAL_FAILURE:
        return True
    if current is State.PAUSED:
        return resume_to is not None and target is resume_to
    if target is State.PAUSED:
        return True
    if current is State.COMMITTING and target is State.FINALIZED:
        return True
    if current is State.CYCLE_COMPLETE:
        return target in {State.CYCLE_PLANNED, State.FINALIZED}
    return _FORWARD.get(current) is target


def require_transition(
    current: State, target: State, *, resume_to: State | None = None
) -> None:
    if not is_valid_transition(current, target, resume_to=resume_to):
        raise TransitionError(f"invalid transition: {current} -> {target}")
