"""Local fail-closed M7 gates and a pure comparison function."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping
from .synthesis import IntegrityError, SynthesisError, _atomic, _contained, _json, _regular, _sha, _inventory, tree_hash
REQUIRED_GATES=("contracts_state","source_provenance","latex_compile_safe","render","pdf_valid","references_labels","asset_inventory","claim_dependencies","math_critical_issues","forbidden_metatext","local_budget","manifest_integrity","correctness_math")
LOCAL_VERIFIERS={gate:(f"article-loop-local-{gate}","m7.2") for gate in REQUIRED_GATES}
def _result(gate, before, passed=False, classification="inconclusive", output="evidence absent", code=1, evidence=(), *, command=None, verifier_version=None, duration_ms=0):
    command,verifier_version=LOCAL_VERIFIERS[gate] if command is None else (command,verifier_version)
    return {"gate_id":gate,"command":command,"verifier_version":verifier_version,"timeout_seconds":1,"input_hash":before,"exit_code":code,"duration_ms":duration_ms,"output":output[:4096],"passed":bool(passed),"classification":classification,"evidence_locators":list(evidence)}
def _manifest(candidate):
    _regular(candidate / "manifest.json")
    path=candidate/"manifest.json"
    try: m=json.loads(path.read_text())
    except Exception as e: raise IntegrityError("invalid manifest") from e
    if m.get("content_hash")!=tree_hash(candidate,exclude={"manifest.json"}) or m.get("inventory")!=_inventory(candidate,{"manifest.json"}): raise IntegrityError("manifest integrity failure")
    return m
def run_gates(candidate: str|Path, *, adapter: Any|None=None, required=REQUIRED_GATES) -> dict[str,Any]:
    """Run only named local adapters. Missing adapters never pass a gate."""
    candidate=Path(candidate)
    # This lstat-backed walk also rejects a symlinked candidate root before the
    # manifest lookup can traverse it.
    tree_hash(candidate)
    if candidate.parent.name != "challengers" or candidate.parent.parent.name != "versions":
        raise IntegrityError("candidate is outside the challenger publication tree")
    manifest=_manifest(candidate)
    if tuple(required)!=REQUIRED_GATES or len(set(required))!=len(required): raise IntegrityError("unknown or missing required gate")
    report=[]; frozen=tree_hash(candidate)
    for gate in REQUIRED_GATES:
        before=tree_hash(candidate)
        duration=0
        if before!=frozen: raise IntegrityError("candidate mutated before gate")
        if gate=="manifest_integrity":
            passed=True; classification="technical"; output="manifest/inventory verified"; code=0; evidence=["manifest.json"]
        elif adapter is None:
            passed=False; classification="inconclusive"; output="no local verifier configured"; code=1; evidence=[]
        else:
            value=adapter.verify(gate,candidate,manifest) if hasattr(adapter,"verify") else None
            if not isinstance(value,Mapping): value={}
            classification=value.get("classification","inconclusive")
            command,version=LOCAL_VERIFIERS[gate]
            output=str(value.get("output","adapter evidence absent")); evidence=value.get("evidence_locators",[])
            raw_code=value.get("exit_code")
            code=raw_code if isinstance(raw_code,int) and not isinstance(raw_code,bool) else 1
            passed=code==0
            if value.get("command")!=command or value.get("verifier_version")!=version or value.get("input_hash")!=before:
                passed=False; output="unallowlisted or stale verifier result"; code=1
            if classification not in {"scientific","technical","inconclusive"}: passed=False; classification="inconclusive"
            duration=value.get("duration_ms",0)
            if not isinstance(duration,int) or isinstance(duration,bool) or duration < 0 or duration > 1000 or value.get("timed_out") is True:
                passed=False; output="gate timeout or invalid duration"; code=1; duration=0
            if len(output.encode()) > 4096:
                passed=False; output="gate output exceeded limit"; code=1
            try:
                valid_evidence=isinstance(evidence,list) and all(isinstance(x,str) and _regular(_contained(candidate,x,True)) for x in evidence)
            except (SynthesisError, OSError): valid_evidence=False
            if not valid_evidence: passed=False; evidence=[]; output="invalid evidence locator"; code=1
            if gate=="correctness_math" and not (passed and classification=="scientific" and any("S20" in x or "W22" in x for x in evidence)):
                passed=False; classification="inconclusive"; output="canonical S20/W22 mathematical evidence absent"; code=1
        after=tree_hash(candidate)
        item=_result(gate,before,passed,classification,output,code,evidence, duration_ms=duration); item["input_hash_after"]=after
        if after!=before: item.update(passed=False,classification="technical",exit_code=1,output="candidate mutated during gate")
        report.append(item)
    body={"schema_version":"1.1.0","candidate_id":manifest["candidate_id"],"candidate_content_hash":manifest["content_hash"],"candidate_hash":frozen,"generated_at":"1970-01-01T00:00:00Z","gates":report}
    body["correctness_math_pass"]=next(x["passed"] for x in report if x["gate_id"]=="correctness_math")
    body["overall_pass"]=all(x["passed"] for x in report) and body["correctness_math_pass"]
    body["report_hash"]=_sha(_json(body)); body["report_id"]="g-"+body["report_hash"][:32]
    root=candidate.parents[2]; path=root/"state/gates"/manifest["candidate_id"]/(body["report_hash"]+".json")
    path.parent.mkdir(parents=True,exist_ok=True); raw=_json(body)
    if path.exists():
        if path.read_bytes()!=raw: raise IntegrityError("gate report collision")
    else: _atomic(path,raw)
    body["report_locator"]=path.relative_to(root).as_posix()
    return body
def compare(left: Mapping[str,Any],right: Mapping[str,Any],*,cost_tiebreak=True):
    """Pure evidence ordering; it cannot publish, reject, archive or promote."""
    def key(x):
        math=bool(x.get("correctness_math_pass")); critical=sum(1 for i in x.get("issues",[]) if i.get("severity")=="CRITICAL")
        severe=sum({"CRITICAL":4,"HIGH":3,"MEDIUM":2,"LOW":1}.get(i.get("severity"),4) for i in x.get("issues",[]))
        vector=tuple(x.get("pareto_vector",[]))
        cost=x.get("cost",0) if cost_tiebreak else 0
        return (math and not critical,-critical,-severe,vector,-cost)
    a,b=key(left),key(right); return {"winner":"left" if a>b else "right" if b>a else "tie","left_key":a,"right_key":b,"promotion_authorized":False}
