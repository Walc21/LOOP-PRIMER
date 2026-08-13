"""Canonical deterministic state transitions."""
from enum import StrEnum
class State(StrEnum):
 NEW="NEW"; INGESTED="INGESTED"; SOURCE_READY="SOURCE_READY"; CYCLE_PLANNED="CYCLE_PLANNED"; DEPARTMENTS_RUNNING="DEPARTMENTS_RUNNING"; SYNTHESIS_READY="SYNTHESIS_READY"; CANDIDATE_BUILT="CANDIDATE_BUILT"; GATES_PASSED="GATES_PASSED"; EVALUATED="EVALUATED"; DIAGNOSED="DIAGNOSED"; DECIDED="DECIDED"; COMMITTING="COMMITTING"; CYCLE_COMPLETE="CYCLE_COMPLETE"; PAUSED="PAUSED"; FINALIZED="FINALIZED"; TECHNICAL_FAILURE="TECHNICAL_FAILURE"
class TransitionError(ValueError): pass
_FORWARD={State.NEW:State.INGESTED,State.INGESTED:State.SOURCE_READY,State.SOURCE_READY:State.CYCLE_PLANNED,State.CYCLE_PLANNED:State.DEPARTMENTS_RUNNING,State.DEPARTMENTS_RUNNING:State.SYNTHESIS_READY,State.SYNTHESIS_READY:State.CANDIDATE_BUILT,State.CANDIDATE_BUILT:State.GATES_PASSED,State.GATES_PASSED:State.EVALUATED,State.EVALUATED:State.DIAGNOSED,State.DIAGNOSED:State.DECIDED,State.DECIDED:State.COMMITTING,State.COMMITTING:State.CYCLE_COMPLETE}
def is_valid_transition(current:State,target:State,*,resume_to:State|None=None)->bool:
 if current is State.PAUSED:return resume_to is not None and target is resume_to
 if current in {State.FINALIZED,State.TECHNICAL_FAILURE}:return False
 if target in {State.PAUSED,State.TECHNICAL_FAILURE}:return True
 if current is State.CYCLE_COMPLETE:return target in {State.CYCLE_PLANNED,State.FINALIZED}
 return _FORWARD.get(current) is target
def require_transition(current:State,target:State,*,resume_to:State|None=None)->None:
 if not is_valid_transition(current,target,resume_to=resume_to):raise TransitionError(f"invalid transition: {current} -> {target}")
