"""Deterministic, local and fail-closed M7 gates."""
from __future__ import annotations

import json, shutil, subprocess, tempfile, time
from pathlib import Path
from typing import Any, Mapping

import yaml

from .synthesis import IntegrityError, SynthesisError, _atomic, _contained, _inventory, _json, _m6_receipt, _regular, _sha, tree_hash

REQUIRED_GATES = ("contracts_state", "source_provenance", "latex_compile_safe", "render", "pdf_valid", "references_labels", "asset_inventory", "claim_dependencies", "math_critical_issues", "forbidden_metatext", "local_budget", "manifest_integrity", "correctness_math")

def _config(root: Path) -> dict[str, dict[str, Any]]:
    try:
        value=yaml.safe_load((root/"config/gates.yaml").read_text(encoding="utf-8"))
        items=value["m7_gates"]
    except (OSError, TypeError, KeyError, yaml.YAMLError) as e:
        raise IntegrityError("M7 gate configuration is unavailable") from e
    if not isinstance(items,list) or [x.get("id") for x in items if isinstance(x,dict)] != list(REQUIRED_GATES):
        raise IntegrityError("M7 gate configuration is missing or unknown")
    result={}
    for item in items:
        if not isinstance(item,dict) or set(item)!={"id","command","verifier_version","timeout_seconds"} or not isinstance(item["command"],str) or not isinstance(item["verifier_version"],str) or type(item["timeout_seconds"]) is not int or item["timeout_seconds"] < 1:
            raise IntegrityError("M7 gate configuration is malformed")
        result[item["id"]]=item
    return result

def _manifest(candidate: Path) -> dict[str, Any]:
    _regular(candidate/"manifest.json")
    try: m=json.loads((candidate/"manifest.json").read_bytes())
    except (OSError,json.JSONDecodeError) as e: raise IntegrityError("invalid manifest") from e
    if m.get("content_hash") != tree_hash(candidate,exclude={"manifest.json"}) or m.get("inventory") != _inventory(candidate,{"manifest.json"}): raise IntegrityError("manifest integrity failure")
    return m

def _run(command: str, args: list[str], *, cwd: Path, timeout: int) -> tuple[bool,int,str,int]:
    executable=shutil.which(command)
    if executable is None: return False,127,"required executable is unavailable",0
    started=time.monotonic()
    try:
        done=subprocess.run([executable,*args], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout, check=False)
        return done.returncode==0,done.returncode,done.stdout[:4096],int((time.monotonic()-started)*1000)
    except subprocess.TimeoutExpired: return False,124,"local verifier timed out",int((time.monotonic()-started)*1000)
    except OSError as e: return False,126,str(e)[:4096],int((time.monotonic()-started)*1000)

def _math_evidence(root: Path, manifest: Mapping[str,Any]) -> tuple[bool,str,list[str]]:
    """Require canonical M6 S20/W22 receipts, not a file named after either role."""
    merge=manifest.get("merge_receipt")
    if not isinstance(merge,dict): return False,"candidate lacks closed merge receipt",[]
    synthesis_hash=merge.get("synthesis_hash")
    if not isinstance(synthesis_hash,str): return False,"candidate has no frozen synthesis hash",[]
    synthesis_path=root/"state/synthesis"/synthesis_hash/"synthesis.json"
    try:
        _regular(synthesis_path); raw=synthesis_path.read_bytes(); synthesis=json.loads(raw)
    except (OSError,json.JSONDecodeError,SynthesisError): return False,"frozen synthesis is unavailable",[]
    if _sha(raw)!=synthesis_hash or synthesis.get("run_id")!=manifest.get("run_id") or synthesis.get("cycle_id")!=manifest.get("cycle_id") or synthesis.get("base_hash")!=manifest.get("base_hash"): return False,"frozen synthesis identity differs",[]
    decision=synthesis.get("decision",{}); packet_receipts=decision.get("packet_receipts",{}); proposal_receipts=decision.get("proposal_receipts",{})
    try:
        s20,s20_raw=_m6_receipt(root,manifest["run_id"],packet_receipts["S20"],"department-packet.schema.json",sender="S20")
        w22_id=next(pid for pid,p in proposal_receipts.items() if p.get("sender_role")=="W22")
        w22,w22_raw=_m6_receipt(root,manifest["run_id"],proposal_receipts[w22_id],"agent-proposal.schema.json",sender="W22")
    except (KeyError,StopIteration,SynthesisError): return False,"canonical S20/W22 M6 receipts are unavailable",[]
    if decision.get("packet_hashes",{}).get("S20")!=_sha(s20_raw) or decision.get("proposal_hashes",{}).get(w22_id)!=_sha(w22_raw): return False,"canonical M6 receipt hashes differ",[]
    # The canonical receipt location binds both payloads to manifest.run_id;
    # packets/proposals bind cycle/base before this M7 candidate exists.
    if any(x.get(k)!=manifest.get(k) for x in (s20,w22) for k in ("cycle_id","base_hash")): return False,"mathematical receipt identity differs",[]
    if not isinstance(manifest.get("candidate_id"),str) or not manifest["candidate_id"]: return False,"candidate identity unavailable",[]
    if s20.get("status")!="complete" or w22_id not in s20.get("proposal_ids",[]) or not w22.get("affected_claims") or "correctness_math" not in w22.get("requested_validations",[]): return False,"S20 did not explicitly approve a claim-bearing W22 correctness check",[]
    if any(str(issue.get("severity","")).upper()=="CRITICAL" for issue in w22.get("issues",[]) if isinstance(issue,dict)): return False,"W22 records an unresolved critical issue",[]
    return True,"canonical S20/W22 approval verified",[packet_receipts["S20"]["immutable_path"],proposal_receipts[w22_id]["immutable_path"]]

def _check(gate: str, candidate: Path, root: Path, manifest: Mapping[str,Any], context: dict[str,Any], timeout: int) -> tuple[bool,str,str,int,list[str],int]:
    """Returns pass, class, output, code, evidence, duration. No adapter decides a result."""
    if gate in {"contracts_state","manifest_integrity"}:
        _manifest(candidate); return True,"technical","manifest and immutable publication verified",0,["manifest.json"],0
    if gate == "source_provenance":
        p=_contained(root,str(manifest.get("merge_receipt_locator","")),True)
        try: _regular(p); ok=_sha(p.read_bytes())==manifest.get("synthesis_hash")
        except (OSError,SynthesisError): ok=False
        return ok,"technical","frozen synthesis verified" if ok else "frozen synthesis missing or altered",0 if ok else 1,[str(manifest.get("merge_receipt_locator",""))] if ok else [],0
    if gate in {"latex_compile_safe","render","pdf_valid"}:
        pdf=context.get("pdf")
        if gate=="latex_compile_safe":
            tex=sorted(candidate.glob("*.tex"))
            if len(tex)!=1: return False,"technical","exactly one root TeX source is required",1,[],0
            work=Path(tempfile.mkdtemp(prefix="m7-latex-"))
            ok,code,out,duration=_run("pdflatex",["-no-shell-escape","-interaction=nonstopmode","-halt-on-error",f"-output-directory={work}",str(tex[0])],cwd=candidate,timeout=timeout)
            candidate_pdf=work/(tex[0].stem+".pdf")
            if not ok or not candidate_pdf.is_file(): shutil.rmtree(work,ignore_errors=True); return False,"technical",out,code,[],duration
            context["work"]=work; context["pdf"]=candidate_pdf; return True,"technical",out or "pdflatex completed",0,[tex[0].name],duration
        if not isinstance(pdf,Path) or not pdf.is_file(): return False,"technical","compiler did not produce a PDF",1,[],0
        if gate=="render":
            output=Path(context["work"])/"render"; output.mkdir(exist_ok=True)
            ok,code,out,duration=_run("pdftoppm",["-png","-f","1","-singlefile",str(pdf),str(output/"page")],cwd=candidate,timeout=timeout)
            return ok,"technical",out or ("first page rendered" if ok else "render failed"),code,["manifest.json"] if ok else [],duration
        if pdf.stat().st_size == 0: return False,"technical","compiler produced an empty PDF",1,[],0
        ok,code,out,duration=_run("pdfinfo",[str(pdf)],cwd=candidate,timeout=timeout)
        return ok,"technical",out or ("pdfinfo accepted output" if ok else "PDF invalid"),code,["manifest.json"] if ok else [],duration
    if gate=="references_labels":
        text="\n".join(x.read_text(encoding="utf-8",errors="replace") for x in candidate.rglob("*.tex")); labels=[]; refs=[]
        import re
        labels=re.findall(r"\\label\{([^}]+)\}",text); refs=re.findall(r"\\(?:ref|eqref)\{([^}]+)\}",text)
        ok=len(labels)==len(set(labels)) and set(refs).issubset(labels)
        return ok,"technical","labels and references verified" if ok else "duplicate or unresolved label",0 if ok else 1,["manifest.json"],0
    if gate=="asset_inventory":
        _manifest(candidate)
        import re
        source="\n".join(x.read_text(encoding="utf-8",errors="replace") for x in candidate.rglob("*.tex"))
        equations=len(re.findall(r"\\\\(?:begin\{equation\*?\}|\[)",source))
        figures=len(re.findall(r"\\\\begin\{figure\*?\}",source))
        tables=len(re.findall(r"\\\\begin\{table\*?\}",source))
        return True,"technical",f"asset inventory verified: equations={equations}, figures={figures}, tables={tables}",0,["manifest.json"],0
    if gate=="claim_dependencies":
        try:
            synthesis_path=_contained(root,str(manifest["merge_receipt_locator"]),True)
            _regular(synthesis_path)
            syn=json.loads(synthesis_path.read_bytes()); proposals=syn["decision"]["proposal_receipts"]
            for receipt in proposals.values(): _m6_receipt(root,manifest["run_id"],receipt,"agent-proposal.schema.json")
            ok=True
        except (KeyError,OSError,json.JSONDecodeError,SynthesisError): ok=False
        return ok,"technical","proposal dependency receipts verified" if ok else "proposal dependency receipt failed",0 if ok else 1,[str(manifest.get("merge_receipt_locator",""))] if ok else [],0
    if gate in {"math_critical_issues","correctness_math"}:
        ok,out,evidence=_math_evidence(root,manifest)
        return ok,"scientific",out,0 if ok else 1,evidence,0
    if gate=="forbidden_metatext":
        forbidden=("as an ai","language model","ignore previous instructions")
        found=any(word in "\n".join(x.read_text(encoding="utf-8",errors="replace") for x in candidate.rglob("*.tex")).casefold() for word in forbidden)
        return not found,"technical","no forbidden metatext" if not found else "forbidden metatext detected",0 if not found else 1,["manifest.json"],0
    if gate=="local_budget":
        items=_inventory(candidate,{"manifest.json"}); ok=len(items)<=1000 and sum(x["size"] for x in items)<=50*1024*1024
        return ok,"technical","local size budget verified" if ok else "local size budget exceeded",0 if ok else 1,["manifest.json"],0
    return False,"inconclusive","unknown local verifier",1,[],0

def run_gates(candidate: str|Path, *, adapter: Any|None=None, required=REQUIRED_GATES) -> dict[str,Any]:
    """Adapter is intentionally ignored: it may schedule this function, never declare a pass."""
    candidate=Path(candidate).resolve(); root=candidate.parents[2]
    if candidate.parent != root/"versions/challengers": raise IntegrityError("candidate is outside challenger publication tree")
    if tuple(required)!=REQUIRED_GATES or len(set(required))!=len(required): raise IntegrityError("required M7 gate set differs")
    config=_config(root); manifest=_manifest(candidate); frozen=tree_hash(candidate); context={}; report=[]
    try:
        for gate in REQUIRED_GATES:
            before=tree_hash(candidate)
            if before!=frozen: raise IntegrityError("candidate mutated before gate")
            entry=config[gate]; ok,classification,output,code,evidence,duration=_check(gate,candidate,root,manifest,context,entry["timeout_seconds"])
            after=tree_hash(candidate)
            if after!=before: ok=False; classification="technical"; code=1; output="candidate mutated during gate"; evidence=[]
            report.append({"gate_id":gate,"command":entry["command"],"verifier_version":entry["verifier_version"],"timeout_seconds":entry["timeout_seconds"],"input_hash":before,"input_hash_after":after,"exit_code":code,"duration_ms":duration,"output":str(output)[:4096],"passed":bool(ok),"classification":classification,"evidence_locators":evidence})
    finally:
        work=context.get("work")
        if isinstance(work,Path): shutil.rmtree(work,ignore_errors=True)
    body={"schema_version":"1.1.0","run_id":manifest["run_id"],"cycle_id":manifest["cycle_id"],"candidate_id":manifest["candidate_id"],"candidate_content_hash":manifest["content_hash"],"candidate_hash":frozen,"generated_at":"1970-01-01T00:00:00Z","gates":report}
    body["correctness_math_pass"]=next(x["passed"] for x in report if x["gate_id"]=="correctness_math"); body["overall_pass"]=all(x["passed"] for x in report)
    body["report_hash"]=_sha(_json(body)); body["report_id"]="g-"+body["report_hash"][:32]
    path=root/"state/gates"/manifest["candidate_id"]/(body["report_hash"]+".json"); path.parent.mkdir(parents=True,exist_ok=True); body["report_locator"]=path.relative_to(root).as_posix(); raw=_json(body)
    if path.exists():
        if path.read_bytes()!=raw: raise IntegrityError("gate report collision")
    else: _atomic(path,raw)
    return body

def compare(left: Mapping[str,Any],right: Mapping[str,Any],*,cost_tiebreak=True):
    """Eight fixed finite dimensions; cost only breaks an otherwise equal vector."""
    def vector(x):
        values=x.get("pareto_vector")
        if not isinstance(values,(list,tuple)) or len(values)!=8 or any(type(v) not in (int,float) or not float("-inf")<float(v)<float("inf") for v in values): raise ValueError("pareto_vector must contain eight finite numeric dimensions")
        critical=sum(1 for issue in x.get("issues",[]) if isinstance(issue,Mapping) and str(issue.get("severity","")).upper()=="CRITICAL")
        severity=sum({"CRITICAL":4,"HIGH":3,"MEDIUM":2,"LOW":1}.get(str(i.get("severity","")).upper(),4) for i in x.get("issues",[]) if isinstance(i,Mapping))
        return tuple(map(float,values)), (int(bool(x.get("correctness_math_pass")) and not critical), -critical, -severity)
    a,a_priority=vector(left); b,b_priority=vector(right)
    # The scientific admission priorities are resolved before the eight
    # componentwise dimensions; the dimensions themselves are never scored.
    if a_priority != b_priority:
        ge_priority=all(x>=y for x,y in zip(a_priority,b_priority))
        le_priority=all(x<=y for x,y in zip(a_priority,b_priority))
        relation="left_dominates" if ge_priority else "right_dominates" if le_priority else "incomparable"
        return {"relation":relation,"left_vector":a,"right_vector":b,"promotion_authorized":False}
    ge=all(x>=y for x,y in zip(a,b)); le=all(x<=y for x,y in zip(a,b))
    relation="equal" if a==b else "left_dominates" if ge else "right_dominates" if le else "incomparable"
    if relation=="equal" and cost_tiebreak and left.get("cost")!=right.get("cost"): relation="left_dominates" if left.get("cost",float("inf"))<right.get("cost",float("inf")) else "right_dominates"
    return {"relation":relation,"left_vector":a,"right_vector":b,"promotion_authorized":False}
