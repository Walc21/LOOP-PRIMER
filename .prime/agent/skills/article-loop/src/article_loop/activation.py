"""Pure sparse activation planner; M5 does not execute any role."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .blackboard import Impact
from .prompts import PromptContractError, validate_output


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
    max_active_per_role: int = 1
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
    """Plans all roles deterministically from impact, history, and hard limits."""

    def __init__(self, limits: PlanningLimits = PlanningLimits()):
        self.limits = limits

    def plan(self, *, cycle_id: int, impact: Impact, history: Mapping[str, Mapping[str, Any]] | None = None, finalization_requested: bool = False, plateau: bool = False, oscillation: bool = False, diagnostic: bool = False) -> ActivationPlan:
        if cycle_id < 0:
            raise ValueError("cycle_id must be non-negative")
        history = history or {}
        targets = set(impact.roles)
        mandatory: set[str] = set()
        if finalization_requested:
            mandatory.update(("S50", "W51", "W53")); targets.update(mandatory)
        # S20 also owns notation and equations.  Only an impact that already
        # reaches the proof verifier is evidence that a theorem/proof check is
        # required; do not infer it merely from S20 being active.
        if "W22" in targets:
            mandatory.update(("S20", "W22")); targets.update(mandatory)
        if cycle_id == 0:
            # Preserve impact and mandatory coverage.  Add a single default
            # focal only where the department has no worker already targeted.
            targets.update(DEPARTMENTS)
            for department, children in CHILDREN.items():
                if not targets.intersection(children):
                    targets.add(children[0])
        for department in DEPARTMENTS:
            item = history.get(department, {})
            age = cycle_id - int(item.get("last_checked_cycle", cycle_id))
            if item.get("dependencies_changed") and age >= self.limits.freeze_dependency_cycles:
                targets.add(department); targets.add(CHILDREN[department][0])
        for department, children in CHILDREN.items():
            if targets.intersection(children): targets.add(department)
        entries = [self._entry("M00", ActivationMode.RUN, "gerente geral obrigatório", impact)]
        for department in DEPARTMENTS:
            entries.extend(self._department_entries(department, targets, impact, history, plateau, oscillation, diagnostic, first_cycle=cycle_id == 0))
        return self._within_limits(cycle_id, entries, mandatory)

    def _within_limits(self, cycle_id: int, entries: list[ActivationEntry], mandatory: set[str]) -> ActivationPlan:
        active = [entry for entry in entries if entry.mode is not ActivationMode.FREEZE]
        counts = {department: sum(entry.mode is not ActivationMode.FREEZE for entry in entries if entry.role_id == department or entry.role_id in CHILDREN[department]) for department in DEPARTMENTS}
        children = {department: sum(entry.mode is not ActivationMode.FREEZE for entry in entries if entry.role_id in CHILDREN[department]) for department in DEPARTMENTS}
        tokens = sum(entry.estimated_tokens for entry in active); wall = sum(entry.wall_time_seconds for entry in active)
        active_roles = {entry.role_id for entry in active}
        missing_mandatory = sorted(mandatory - active_roles)
        reasons = []
        if missing_mandatory: reasons.append("missing_mandatory")
        if len(active) > self.limits.max_active_per_cycle: reasons.append("cycle_limit")
        if tokens > self.limits.max_estimated_tokens: reasons.append("token_limit")
        if wall > self.limits.max_wall_time_seconds: reasons.append("wall_time_limit")
        if any(value > self.limits.max_active_per_department for value in counts.values()): reasons.append("department_limit")
        if any(value > self.limits.max_children_per_manager for value in children.values()): reasons.append("children_limit")
        if self.limits.max_active_per_role < 1 and active: reasons.append("role_limit")
        if reasons:
            reason = "mandatory_coverage_missing" if missing_mandatory else ("mandatory_coverage_exceeds_limits" if mandatory else ("department_limit_exhausted" if reasons == ["department_limit"] else "budget_exhausted"))
            checkpoint = {"reason": reason, "constraints": reasons, "mandatory_roles": sorted(mandatory), "missing_mandatory": missing_mandatory, "active_roles": len(active), "estimated_tokens": tokens, "wall_time_seconds": wall, "limits": asdict(self.limits)}
            return ActivationPlan(cycle_id, tuple(entries), True, checkpoint, self.limits)
        return ActivationPlan(cycle_id, tuple(entries), False, None, self.limits)

    def _department_entries(self, department: str, targets: set[str], impact: Impact, history: Mapping[str, Mapping[str, Any]], plateau: bool, oscillation: bool, diagnostic: bool, *, first_cycle: bool) -> list[ActivationEntry]:
        children = CHILDREN[department]
        department_active = department in targets or bool(targets.intersection(children))
        result = [self._entry(department, self._mode(department, department_active, impact, history, plateau, oscillation, diagnostic, first_cycle=first_cycle), "impacto, cobertura ou finalização" if department_active else "sem impacto no ciclo", impact)]
        for role in children:
            active = role in targets
            result.append(self._entry(role, self._mode(role, active, impact, history, plateau, oscillation, diagnostic, first_cycle=first_cycle), "dependência crítica" if role in {"W22", "W51", "W53"} else "impacto focal", impact))
        return result

    @staticmethod
    def _mode(role: str, active: bool, impact: Impact, history: Mapping[str, Mapping[str, Any]], plateau: bool, oscillation: bool, diagnostic: bool, *, first_cycle: bool) -> ActivationMode:
        if not active: return ActivationMode.FREEZE
        # These roles verify an already-defined mathematical or finalization
        # obligation, including in the first cycle.  A global exploration
        # signal cannot replace that check.
        if role in {"W22", "W53"}: return ActivationMode.CHECK
        if first_cycle: return ActivationMode.RUN
        item = history.get(role, {})
        shift = plateau or oscillation or diagnostic or bool(item.get("plateau")) or bool(item.get("oscillation")) or bool(item.get("diagnosis_required")) or int(item.get("failure_count", 0)) >= 2
        if shift: return ActivationMode.SHIFT
        if role == "W22" or impact.severity < 50 or int(item.get("failure_count", 0)) == 1: return ActivationMode.CHECK
        return ActivationMode.RUN

    @staticmethod
    def _entry(role: str, mode: ActivationMode, justification: str, impact: Impact) -> ActivationEntry:
        if mode is ActivationMode.FREEZE:
            return ActivationEntry(role, mode, justification, 0, 0, (), ())
        manager = role.startswith("S") or role == "M00"
        expected = ("department-packet.schema.json",) if role.startswith("S") else (("activation_map.json",) if role == "M00" else ("agent-proposal.schema.json",))
        inputs = tuple(sorted(set(impact.claims + impact.sections + impact.equations + impact.references))) or ("snapshot",)
        return ActivationEntry(role, mode, justification, 500 if manager else 900, 60 if manager else 120, inputs, expected)


def specialist_view(task: Mapping[str, Any], *, excerpts: Sequence[str], dependent_claims: Sequence[Mapping[str, Any]], rubric: Mapping[str, Any], local_history: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {"task": dict(task), "excerpts": list(excerpts), "dependent_claims": [dict(claim) for claim in dependent_claims], "rubric": dict(rubric), "local_history": [dict(item) for item in local_history]}


def submanager_view(task: Mapping[str, Any], child_proposals: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {"task": dict(task), "child_proposals": [dict(proposal) for proposal in child_proposals]}


def manager_view(project_root: str | Path, packets: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Expose only the five schema-valid canonical DepartmentPackets to M00."""
    if len(packets) != len(DEPARTMENTS): raise ValueError("M00 must receive exactly five packets")
    for expected, packet in zip(DEPARTMENTS, packets):
        if not isinstance(packet, Mapping) or packet.get("department_id") != expected: raise ValueError("packets must be canonical, unique, and ordered")
        try:
            validate_output(project_root, "department-packet.schema.json", packet)
        except PromptContractError as error:
            raise ValueError("DepartmentPacket must satisfy its canonical schema") from error
    run_ids = {packet["run_id"] for packet in packets}
    cycle_ids = {packet["cycle_id"] for packet in packets}
    base_hashes = {packet["base_hash"] for packet in packets}
    packet_ids = [packet["packet_id"] for packet in packets]
    if len(run_ids) != 1 or len(cycle_ids) != 1 or len(base_hashes) != 1:
        raise ValueError("DepartmentPackets must share run_id, cycle_id, and base_hash")
    if any(not packet_id.strip() for packet_id in packet_ids) or len(set(packet_ids)) != len(packet_ids):
        raise ValueError("DepartmentPacket packet_id values must be non-empty and unique")
    return {"department_packets": list(packets)}
