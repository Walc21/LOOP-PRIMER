"""Deterministic M7 gates over a frozen challenger."""
from __future__ import annotations
import json, time
from pathlib import Path
from typing import Any, Mapping
from .synthesis import SynthesisError, _json, _sha, tree_hash
REQUIRED=("manifest_integrity","correctness_math")
def run_gates(candidate: str|Path, *, math_evidence: bool=False) -> dict[str,Any]:
    root=Path(candidate); manifest=json.loads((root/"manifest.json").read_text()); before=tree_hash(root,exclude={"manifest.json"})
    if before!=manifest.get("content_hash"): raise SynthesisError("candidate hash mismatch")
    gates=[]
    gates.append({"gate_id":"manifest_integrity","verifier_version":"m7.1","classification":"technical","passed":True,"command":"internal","timeout_seconds":0,"input_hash":before,"exit_code":0,"duration_ms":0,"output":"manifest/tree verified","evidence_locators":[]})
    gates.append({"gate_id":"correctness_math","verifier_version":"m7.1","classification":"scientific" if math_evidence else "inconclusive","passed":bool(math_evidence),"command":"canonical evidence only","timeout_seconds":0,"input_hash":before,"exit_code":0 if math_evidence else 1,"duration_ms":0,"output":"evidence present" if math_evidence else "canonical mathematical evidence absent","evidence_locators":[]})
    after=tree_hash(root,exclude={"manifest.json"})
    if after!=before: raise SynthesisError("candidate mutated during gates")
    overall=all(x["passed"] for x in gates) and {x["gate_id"] for x in gates}==set(REQUIRED)
    report={"schema_version":"1.1.0","report_id":"g-"+_sha(_json(gates))[:24],"candidate_id":manifest["candidate_id"],"candidate_content_hash":before,"generated_at":"1970-01-01T00:00:00Z","overall_pass":overall,"correctness_math_pass":bool(math_evidence),"gates":gates}
    return report
def compare(left: Mapping[str,Any], right: Mapping[str,Any]) -> Mapping[str,Any]:
    """Evidence-only ranking: mathematical hard gate, critical issues, Pareto, cost."""
    if bool(left.get("correctness_math_pass")) != bool(right.get("correctness_math_pass")): return {"winner":"left" if left.get("correctness_math_pass") else "right","reason":"correctness_math"}
    return {"winner":None,"reason":"pareto_evidence_required"}
