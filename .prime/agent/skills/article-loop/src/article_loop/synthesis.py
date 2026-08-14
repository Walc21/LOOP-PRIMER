"""M7 local synthesis and isolated, write-once challenger construction."""
from __future__ import annotations
import hashlib, json, os, shutil, stat, tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence
from .activation import DEPARTMENTS
from .prompts import PromptContractError, validate_output

class SynthesisError(RuntimeError): pass
def _json(v: Any) -> bytes: return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
def _sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def _contained(root: Path, name: str) -> Path:
    p=root/name
    if not name or Path(name).is_absolute() or ".." in Path(name).parts or p.resolve().parent != root.resolve(): raise SynthesisError("unsafe target")
    return p
def tree_hash(root: Path, *, exclude: set[str]=set()) -> str:
    entries=[]
    for p in sorted(root.rglob("*")):
        rel=p.relative_to(root).as_posix()
        if rel in exclude: continue
        s=p.lstat()
        if stat.S_ISLNK(s.st_mode) or not stat.S_ISREG(s.st_mode): raise SynthesisError("tree contains link or special file")
        entries.append([rel,s.st_size,_sha(p.read_bytes())])
    return _sha(_json(entries))
def _fsync(path: Path) -> None:
    fd=os.open(path, os.O_RDONLY); os.fsync(fd); os.close(fd)

class M7Pipeline:
    """Purely local M7 authority; it never changes champion/Pareto/rejected."""
    def __init__(self, root: str|Path): self.root=Path(root).resolve()
    def synthesize(self, packets: Sequence[Mapping[str,Any]]) -> dict[str,Any]:
        if len(packets)!=5: raise SynthesisError("exactly five DepartmentPackets required")
        ordered=[]
        for role, packet in zip(DEPARTMENTS, packets):
            if packet.get("department_id") != role: raise SynthesisError("packets must be canonical and unique")
            try: validate_output(self.root,"department-packet.schema.json",packet)
            except PromptContractError as e: raise SynthesisError("invalid DepartmentPacket") from e
            if packet["status"] == "no_change" and not packet.get("no_change_justification"): raise SynthesisError("no_change requires justification")
            if packet["status"] == "blocked" and role in {"S30","S40"}: raise SynthesisError("technical blocked packet prevents merge")
            ordered.append(packet)
        identity={(p["run_id"],p["cycle_id"],p["base_hash"],p["schema_version"]) for p in ordered}
        if len(identity)!=1: raise SynthesisError("packet identities differ")
        frozen=_json(ordered); h=_sha(frozen)
        return {"schema_version":"1.1.0","run_id":ordered[0]["run_id"],"cycle_id":ordered[0]["cycle_id"],"base_hash":ordered[0]["base_hash"],"packet_hashes":[_sha(_json(x)) for x in ordered],"synthesis_hash":h,"frozen_bytes":frozen,"decisions":[{"proposal_id":pid,"outcome":"deferred" if p["status"]=="blocked" else "accepted","reason":"department packet status","evidence":p["evidence_locators"]} for p in ordered for pid in p["proposal_ids"]]}
    def freeze_synthesis(self, synthesis: Mapping[str,Any]) -> Path:
        path=self.root/"state"/"synthesis"/str(synthesis["synthesis_hash"])/"synthesis.json"; path.parent.mkdir(parents=True,exist_ok=True)
        raw=synthesis["frozen_bytes"]
        if path.exists() and path.read_bytes()!=raw: raise SynthesisError("synthesis hash collision")
        if not path.exists(): path.write_bytes(raw); _fsync(path); _fsync(path.parent)
        return path
    def build(self, synthesis: Mapping[str,Any], proposals: Sequence[Mapping[str,Any]], champion: str|Path) -> dict[str,Any]:
        base=Path(champion).resolve(); manifest=json.loads((base/"manifest.json").read_text())
        if manifest.get("content_hash")!=synthesis["base_hash"]: raise SynthesisError("obsolete base")
        ids=set(); ops=[]
        for x in proposals:
            try: validate_output(self.root,"agent-proposal.schema.json",x)
            except PromptContractError as e: raise SynthesisError("invalid proposal") from e
            if x["proposal_id"] in ids or x["base_hash"]!=synthesis["base_hash"]: raise SynthesisError("duplicate or obsolete proposal")
            ids.add(x["proposal_id"]); ops.extend((x["proposal_id"],o) for o in x["patch_or_operations"].get("operations",[]))
            if x["patch_or_operations"]["kind"]!="operations": raise SynthesisError("text patches require an audited adapter")
        targets=[o[1]["target"] for o in ops]
        if len(targets)!=len(set(targets)): raise SynthesisError("overlapping operations")
        candidate_id="c-"+_sha(_json({"base":synthesis["base_hash"],"synthesis":synthesis["synthesis_hash"],"proposals":sorted(ids)}))[:24]
        destination=self.root/"versions"/"challengers"/candidate_id
        if destination.exists():
            existing=json.loads((destination/"manifest.json").read_text())
            if existing.get("base_candidate_id")==manifest.get("candidate_id"): return existing
            raise SynthesisError("divergent write-once challenger")
        staging=Path(tempfile.mkdtemp(prefix="m7-",dir=self.root/"workspaces"))
        try:
            for p in base.rglob("*"):
                if p.name=="manifest.json": continue
                rel=p.relative_to(base); q=staging/rel
                if p.is_symlink() or not p.is_file(): raise SynthesisError("unsafe champion tree")
                q.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,q)
            for _,op in sorted(ops,key=lambda z:(z[1]["target"],z[0])):
                target=_contained(staging,op["target"])
                if op["op"]=="add" and target.exists(): raise SynthesisError("add target exists")
                if op["op"] in {"replace","remove","annotate"} and not target.exists(): raise SynthesisError("target absent")
                if op["op"]=="remove": target.unlink()
                else: target.parent.mkdir(parents=True,exist_ok=True); target.write_text(op["value"] or "",encoding="utf-8")
            inventory=[]
            for p in sorted(staging.rglob("*")):
                if not p.is_file() or p.is_symlink(): raise SynthesisError("unsafe staged file")
                inventory.append({"path":p.relative_to(staging).as_posix(),"sha256":_sha(p.read_bytes()),"size":p.stat().st_size})
                _fsync(p)
            content=tree_hash(staging)
            receipt={"synthesis_hash":synthesis["synthesis_hash"],"source_proposal_ids":sorted(ids),"operations":len(ops)}
            out={"schema_version":"1.1.0","candidate_id":candidate_id,"candidate_kind":"challenger","run_id":synthesis["run_id"],"cycle_id":synthesis["cycle_id"],"base_candidate_id":manifest["candidate_id"],"built_at":"1970-01-01T00:00:00Z","workspace_hash":content,"content_hash":content,"source_proposal_ids":sorted(ids),"merge_receipt_locator":"manifest.json","immutable":True,"inventory":inventory,"merge_receipt":receipt}
            (staging/"manifest.json").write_bytes(_json(out)); _fsync(staging/"manifest.json"); _fsync(staging)
            destination.parent.mkdir(parents=True,exist_ok=True); os.replace(staging,destination); _fsync(destination.parent)
            return out
        except Exception:
            shutil.rmtree(staging,ignore_errors=True); raise
