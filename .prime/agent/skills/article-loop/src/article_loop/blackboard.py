"""Append-only operational memory and deterministic impact projection for M5."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


LEDGERS = ("claims", "issues", "tasks", "dependencies", "evidence", "decisions")


class BlackboardError(ValueError):
    """Raised for malformed or conflicting append-only records."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_claim_id(*, text: str, claim_type: str, location: Mapping[str, Any], source_hash: str) -> str:
    """Return an input-addressed claim identifier, independent of cycle order."""
    if not all(isinstance(value, str) and value.strip() for value in (text, claim_type, source_hash)):
        raise BlackboardError("claim text, type and source_hash must be non-empty strings")
    return "clm-" + sha256(_canonical({"text": text.strip(), "type": claim_type, "location": location, "source_hash": source_hash}).encode()).hexdigest()[:24]


@dataclass(frozen=True)
class Impact:
    claims: tuple[str, ...]
    sections: tuple[str, ...]
    equations: tuple[str, ...]
    references: tuple[str, ...]
    roles: tuple[str, ...]


class Blackboard:
    """Run-partitioned JSONL ledgers. Existing lines are never rewritten."""

    def __init__(self, root: Path | str):
        self.root = Path(root)

    def _path(self, run_id: str, ledger: str) -> Path:
        if ledger not in LEDGERS or not run_id or "/" in run_id or "\\" in run_id or run_id in {".", ".."}:
            raise BlackboardError("unsafe run_id or unknown ledger")
        return self.root / "state" / "blackboard" / run_id / f"{ledger}.jsonl"

    def append(self, run_id: str, ledger: str, record: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(record, Mapping):
            raise BlackboardError("ledger record must be an object")
        value = dict(record)
        if ledger == "claims":
            value = self._claim(value)
        identifier = value.get("record_id") or value.get("claim_id")
        if not isinstance(identifier, str) or not identifier:
            raise BlackboardError("record_id (or claim_id) is required")
        path = self._path(run_id, ledger)
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized = _canonical(value)
        if path.exists():
            for prior in self.read(run_id, ledger):
                prior_id = prior.get("record_id") or prior.get("claim_id")
                if prior_id == identifier:
                    if _canonical(prior) == serialized:
                        return prior
                    if ledger != "claims":
                        raise BlackboardError(f"conflicting append for {identifier}")
        with path.open("a", encoding="utf-8") as stream:
            stream.write(serialized + "\n")
        return value

    def _claim(self, claim: dict[str, Any]) -> dict[str, Any]:
        required = ("text", "type", "location", "dependencies", "evidence", "status", "severity", "source_hash", "last_validated_cycle")
        missing = [key for key in required if key not in claim]
        if missing or not isinstance(claim["location"], Mapping):
            raise BlackboardError(f"claim missing required fields: {', '.join(missing)}")
        if not isinstance(claim["dependencies"], list) or not isinstance(claim["evidence"], list):
            raise BlackboardError("claim dependencies and evidence must be lists")
        if not isinstance(claim["severity"], int) or isinstance(claim["severity"], bool) or not 0 <= claim["severity"] <= 100:
            raise BlackboardError("claim severity must be an integer from 0 to 100")
        if not isinstance(claim["last_validated_cycle"], int) or isinstance(claim["last_validated_cycle"], bool):
            raise BlackboardError("last_validated_cycle must be an integer")
        if not isinstance(claim["source_hash"], str) or not re.fullmatch(
            r"[a-f0-9]{64}", claim["source_hash"]
        ):
            raise BlackboardError("source_hash must be a lowercase SHA-256")
        expected = stable_claim_id(text=claim["text"], claim_type=claim["type"], location=claim["location"], source_hash=claim["source_hash"])
        if "claim_id" in claim and claim["claim_id"] != expected:
            raise BlackboardError("claim_id does not match canonical claim identity")
        claim["claim_id"] = expected
        return claim

    def read(self, run_id: str, ledger: str) -> list[dict[str, Any]]:
        path = self._path(run_id, ledger)
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                item = json.loads(line)
            except json.JSONDecodeError as error:
                raise BlackboardError(f"invalid {ledger} JSONL line {number}") from error
            if not isinstance(item, dict):
                raise BlackboardError(f"invalid {ledger} record {number}")
            records.append(item)
        return records

    def claims(self, run_id: str) -> dict[str, dict[str, Any]]:
        """Return the latest revision of each claim while retaining ledger history."""
        current: dict[str, dict[str, Any]] = {}
        for claim in self.read(run_id, "claims"):
            current[claim["claim_id"]] = claim
        return current

    def impact(self, run_id: str, changes: Iterable[Mapping[str, Any] | str]) -> Impact:
        return ImpactGraph(self.claims(run_id)).affected(changes)


class ImpactGraph:
    """Closed, conservative graph from claims to document objects and roles."""

    def __init__(self, claims: Mapping[str, Mapping[str, Any]]):
        self.claims = {key: dict(value) for key, value in claims.items()}

    def affected(self, changes: Iterable[Mapping[str, Any] | str]) -> Impact:
        tokens = {self._token(change) for change in changes}
        selected = {claim_id for claim_id, claim in self.claims.items() if self._matches(claim, tokens)}
        # Dependencies can be stated in either direction, so close the graph both ways.
        changed = True
        while changed:
            changed = False
            for claim_id, claim in self.claims.items():
                deps = set(claim.get("dependencies", []))
                if claim_id in selected or deps & selected:
                    if claim_id not in selected:
                        selected.add(claim_id); changed = True
                    for dependency in deps:
                        if dependency in self.claims and dependency not in selected:
                            selected.add(dependency); changed = True
        sections: set[str] = set(); equations: set[str] = set(); references: set[str] = set(); roles: set[str] = set()
        for claim_id in selected:
            claim = self.claims[claim_id]
            location = claim.get("location", {})
            for key, target in (("section", sections), ("equation", equations), ("reference", references)):
                value = location.get(key)
                if isinstance(value, str) and value:
                    target.add(value)
            roles.update(_roles_for(claim, tokens))
        # A newly detected change may precede claim extraction; preserve critical
        # coverage instead of waiting for a future ledger append.
        roles.update(_roles_for({"type": " ".join(tokens), "text": "", "location": {}}, tokens))
        return Impact(tuple(sorted(selected)), tuple(sorted(sections)), tuple(sorted(equations)), tuple(sorted(references)), tuple(sorted(roles)))

    @staticmethod
    def _token(change: Mapping[str, Any] | str) -> str:
        if isinstance(change, str):
            return change
        if not isinstance(change, Mapping):
            raise BlackboardError("changes must be strings or objects")
        return str(change.get("id") or change.get("kind") or change.get("location") or "")

    def _matches(self, claim: Mapping[str, Any], tokens: set[str]) -> bool:
        location = claim.get("location", {})
        values = {str(claim.get("claim_id", "")), str(claim.get("type", "")), *(str(value) for value in location.values())}
        return bool(values & tokens)


def _roles_for(claim: Mapping[str, Any], tokens: set[str]) -> set[str]:
    text = " ".join((str(claim.get("type", "")), str(claim.get("text", "")), *tokens)).lower()
    location = claim.get("location", {})
    roles: set[str] = set()
    if any(word in text for word in ("theorem", "theorema", "proof", "prova", "lemma", "lema")):
        roles.update(("S20", "W22"))
    if any(word in text for word in ("notation", "notação", "definition", "definição", "hypothesis", "hipótese")):
        roles.update(("S20", "W21", "S40", "W42"))
    if location.get("equation") or any(word in text for word in ("equation", "equação", "calculation", "cálculo")):
        roles.update(("S20", "W23", "S50", "W52"))
    if location.get("reference") or "reference" in text or "referência" in text:
        roles.update(("S50", "W51"))
    if any(word in text for word in ("style", "estilo", "grammar", "gramática")):
        roles.update(("S40", "W41", "W43"))
    return roles
