"""Pure sparse activation planner; M5 does not execute any role."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .blackboard import Impact


DEPARTMENTS = ("S10", "S20", "S30", "S40", "S50")
CHILDREN = {"S10": ("W11", "W12", "W13"), "S20": ("W21", "W22", "W23"), "S30": ("W31", "W32", "W33"), "S40": ("W41", "W42", "W43"), "S50": ("W51", "W52", "W53")}


class ActivationMode(StrEnum):
    RUN = "RUN"
    CHECK = "CHECK"
    SHIFT = "SHIFT"
    FREEZE = "FREEZE"


@dataclass(frozen=True)
class PlanningLimits:
    max_active_per_cycle: int = 21
    max_active_per_department: int = 4
    max_children_per_manager: int = 3
    max_wall_time_seconds: int = 3600
    max_estimated_tokens: int = 20000
    freeze_dependency_cycles: int = 2


@dataclass(frozen=True)
class ActivationEntry:
    role_id: str
    mode: ActivationMode
    justification: str
    estimated_tokens: int
    wall_time_seconds: int
    inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]


@dataclass(frozen=True)
class ActivationPlan:
    cycle_id: int
    entries: tuple[ActivationEntry, ...]
    paused: bool
    checkpoint: Mapping[str, Any] | None
    limits: PlanningLimits

    def activation_map(self) -> dict[str, Any]:
        active = [entry for entry in self.entries if entry.mode is not ActivationMode.FREEZE]
        return {"cycle_id": self.cycle_id, "paused": self.paused, "checkpoint": self.checkpoint, "budget": {"limits": asdict(self.limits), "estimated_tokens": sum(entry.estimated_tokens for entry in active), "wall_time_seconds": sum(entry.wall_time_seconds for entry in active)}, "roles": [asdict(entry) | {"mode": entry.mode.value, "inputs": list(entry.inputs), "expected_outputs": list(entry.expected_outputs)} for entry in self.entries]}

    def write_activation_map(self, path: Path | str) -> Path:
        target = Path(path)
        if target.exists():
            raise FileExistsError(f"refusing to overwrite activation map: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.activation_map(), ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return target


class ActivationPlanner:
    """Plans all roles deterministically from public operational data."""

    def __init__(self, limits: PlanningLimits = PlanningLimits()):
        self.limits = limits

    def plan(self, *, cycle_id: int, impact: Impact, history: Mapping[str, Mapping[str, Any]] | None = None, finalization_requested: bool = False, plateau: bool = False) -> ActivationPlan:
        if cycle_id < 0:
            raise ValueError("cycle_id must be non-negative")
        history = history or {}
        targets = set(impact.roles)
        if finalization_requested:
            targets.update(("S50", "W51", "W53"))
        # First auditable cycle covers every department; one focal worker makes each packet actionable.
        if cycle_id == 0:
            targets.update(DEPARTMENTS)
            targets.update(children[0] for children in CHILDREN.values())
        for department in DEPARTMENTS:
            item = history.get(department, {})
            if item.get("dependencies_changed") and cycle_id - int(item.get("last_checked_cycle", cycle_id)) >= self.limits.freeze_dependency_cycles:
                targets.add(department)
                targets.update(CHILDREN[department][:1])
        # Child involvement implies departmental consolidation.
        for department, children in CHILDREN.items():
            if targets.intersection(children):
                targets.add(department)
        entries = [self._entry("M00", ActivationMode.RUN, "gerente geral obrigatório", impact)]
        for department in DEPARTMENTS:
            entries.extend(self._department_entries(department, targets, impact, history, plateau))
        active = [entry for entry in entries if entry.mode is not ActivationMode.FREEZE]
        tokens = sum(entry.estimated_tokens for entry in active)
        wall = sum(entry.wall_time_seconds for entry in active)
        per_department_excess = any(sum(entry.mode is not ActivationMode.FREEZE for entry in entries if entry.role_id == department or entry.role_id in CHILDREN[department]) > self.limits.max_active_per_department for department in DEPARTMENTS)
        if len(active) > self.limits.max_active_per_cycle or tokens > self.limits.max_estimated_tokens or wall > self.limits.max_wall_time_seconds or per_department_excess:
            checkpoint = {"reason": "budget_exhausted", "active_roles": len(active), "estimated_tokens": tokens, "wall_time_seconds": wall, "limits": asdict(self.limits)}
            if per_department_excess:
                checkpoint = dict(checkpoint, reason="department_limit_exhausted")
            return ActivationPlan(cycle_id, tuple(entries), True, checkpoint, self.limits)
        return ActivationPlan(cycle_id, tuple(entries), False, None, self.limits)

    def _department_entries(self, department: str, targets: set[str], impact: Impact, history: Mapping[str, Mapping[str, Any]], plateau: bool) -> list[ActivationEntry]:
        children = CHILDREN[department]
        active_children = [role for role in children if role in targets]
        if len(active_children) > self.limits.max_children_per_manager:
            active_children = active_children[:self.limits.max_children_per_manager]
        department_active = department in targets or bool(active_children)
        mode = ActivationMode.RUN if department_active else ActivationMode.FREEZE
        if department_active and plateau and department == "S30":
            mode = ActivationMode.SHIFT
        result = [self._entry(department, mode, "impacto, cobertura ou finalização" if department_active else "sem impacto no ciclo", impact)]
        for role in children:
            if role in active_children:
                child_mode = ActivationMode.CHECK if role == "W22" and department != "S20" else ActivationMode.RUN
                result.append(self._entry(role, child_mode, "dependência crítica" if role in {"W22", "W51", "W53"} else "impacto focal", impact))
            else:
                result.append(self._entry(role, ActivationMode.FREEZE, "sem impacto no ciclo", impact))
        return result

    @staticmethod
    def _entry(role: str, mode: ActivationMode, justification: str, impact: Impact) -> ActivationEntry:
        manager = role.startswith("S") or role == "M00"
        expected = ("department-packet.schema.json",) if role.startswith("S") else (("activation_map.json",) if role == "M00" else ("agent-proposal.schema.json",))
        inputs = tuple(sorted(set(impact.claims + impact.sections + impact.equations + impact.references))) or ("snapshot",)
        return ActivationEntry(role, mode, justification, 500 if manager else 900, 60 if manager else 120, inputs, expected)


def specialist_view(task: Mapping[str, Any], *, excerpts: Sequence[str], dependent_claims: Sequence[Mapping[str, Any]], rubric: Mapping[str, Any], local_history: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Closed specialist context: only task-local operational inputs are exposed."""
    return {"task": dict(task), "excerpts": list(excerpts), "dependent_claims": [dict(claim) for claim in dependent_claims], "rubric": dict(rubric), "local_history": [dict(item) for item in local_history]}


def submanager_view(task: Mapping[str, Any], child_proposals: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {"task": dict(task), "child_proposals": [dict(proposal) for proposal in child_proposals]}


def manager_view(packets: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if len(packets) != 5:
        raise ValueError("M00 must receive exactly five DepartmentPackets or NO_CHANGE packets")
    return {"department_packets": [dict(packet) for packet in packets]}
