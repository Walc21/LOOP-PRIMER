"""M7 deterministic synthesis and isolated write-once challenger creation."""
from __future__ import annotations
import hashlib, json, os, shutil, stat, tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence
from .activation import DEPARTMENTS
from .prompts import PromptContractError, validate_output
from .store import DurableStore, IntegrityError
from .state_machine import State
class SynthesisError(RuntimeError): pass
def _json(v: Any) -> bytes: return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
def _sha(v: bytes) -> str: return hashlib.sha256(v).hexdigest()
def _rel(name: str) -> PurePosixPath:
    p=PurePosixPath(name) if isinstance(name,str) else None
    if not p or not name or "\x00" in name or p.is_absolute() or any(x in {"",".",".."} for x in p.parts): raise SynthesisError("unsafe target")
    return p
def _contained(root: Path,name: str,exists=False) -> Path:
    root=root.resolve(); p=_rel(name); current=root
    for part in p.parts[:-1]:
        current/=part
        if current.exists() or current.is_symlink():
            s=current.lstat()
            if stat.S_ISLNK(s.st_mode) or not stat.S_ISDIR(s.st_mode): raise SynthesisError("unsafe intermediate target")
    target=root.joinpath(*p.parts)
    try: target.resolve(strict=False).relative_to(root)
    except ValueError as e: raise SynthesisError("target escapes staging") from e
    if exists and not target.exists(): raise SynthesisError("target does not exist")
    return target
def _regular(path: Path) -> os.stat_result:
    s=path.lstat()
    if stat.S_ISLNK(s.st_mode) or not stat.S_ISREG(s.st_mode): raise SynthesisError("link or special file")
    return s
def _walk(root: Path,exclude: set[str]|None=None):
    root=root.resolve(); exclude=exclude or set()
    if not root.is_dir(): raise SynthesisError("tree root is not a directory")
    out=[]; seen=set(); inodes=set()
    for base,dirs,files in os.walk(root,topdown=True,followlinks=False):
        dirs.sort(); files.sort(); here=Path(base)
        for name in list(dirs)+files:
            path=here/name; rel=path.relative_to(root).as_posix()
            if rel in exclude:
                if name in dirs: dirs.remove(name)
                continue
            s=path.lstat()
            if stat.S_ISLNK(s.st_mode): raise SynthesisError("tree contains symlink")
            if not(stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode)): raise SynthesisError("tree contains special file")
            if rel.casefold() in seen: raise SynthesisError("case collision")
            seen.add(rel.casefold())
            if stat.S_ISREG(s.st_mode):
                inode=(s.st_dev,s.st_ino)
                if s.st_nlink != 1 or inode in inodes: raise SynthesisError("hardlink in immutable tree")
                inodes.add(inode)
            out.append((rel,path,s))
    return out
def tree_hash(root: Path, *, exclude: set[str]|None=None) -> str:
    return _sha(_json([["d",r] if stat.S_ISDIR(s.st_mode) else ["f",r,s.st_size,_sha(p.read_bytes())] for r,p,s in _walk(root,exclude)]))
def _inventory(root: Path,exclude: set[str]|None=None):
    return [{"path":r,"sha256":_sha(p.read_bytes()),"size":s.st_size} for r,p,s in _walk(root,exclude) if stat.S_ISREG(s.st_mode)]
def _fsync(path: Path):
    fd=os.open(path,os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)
def _atomic(path: Path,data: bytes):
    fd,tmp=tempfile.mkstemp(prefix=".m7-",dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path); _fsync(path.parent)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def _copy(source: Path,dest: Path,exclude: set[str]|None=None):
    dest.mkdir(exist_ok=True)
    for rel,path,s in _walk(source,exclude):
        target=dest/rel
        if stat.S_ISDIR(s.st_mode): target.mkdir()
        else:
            target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,target); os.chmod(target,stat.S_IMODE(s.st_mode)); _fsync(target)
    _fsync(dest)
class M7Pipeline:
    """Only this merge writes a challenger; no M8 disposition is available."""
    def __init__(self,root: str|Path,*,fault=None):
        self.root=Path(root).resolve(); self.fault=fault
        for x in ("state/synthesis","versions/challengers","workspaces"): (self.root/x).mkdir(parents=True,exist_ok=True)
    def _hit(self,name):
        if self.fault: self.fault(name)
    def synthesize(self,packets: Sequence[Mapping[str,Any]],*,receipts: Mapping[str,Mapping[str,Any]]|None=None):
        if len(packets)!=5: raise SynthesisError("requires exactly five packets")
        if receipts is None: raise SynthesisError("immutable receipts are required")
        by={p.get("department_id"):dict(p) for p in packets}
        if len(by)!=5 or tuple(by)!=DEPARTMENTS: raise SynthesisError("departments must be canonical and unique")
        packets=[by[x] for x in DEPARTMENTS]; ident=[(p.get("run_id"),p.get("cycle_id"),p.get("base_hash"),p.get("schema_version")) for p in packets]
        if len(set(ident))!=1: raise SynthesisError("packet identity mismatch")
        hashes={}; accepted=[]
        for p in packets:
            try: validate_output(self.root,"department-packet.schema.json",p)
            except PromptContractError as e: raise SynthesisError("invalid packet") from e
            role=p["department_id"]; raw=_json(p); hashes[role]=_sha(raw)
            r=receipts.get(role); frozen=r.get("immutable_path") if isinstance(r,Mapping) else None
            if not isinstance(r,Mapping) or r.get("sha256")!=hashes[role] or not isinstance(frozen,str): raise SynthesisError("missing receipt")
            f=_contained(self.root,frozen,True); _regular(f)
            if f.read_bytes()!=raw: raise SynthesisError("packet receipt diverges")
            if p["status"]=="blocked" and role in {"S30","S40"}: raise SynthesisError("technical department blocked")
            if p["status"]=="no_change" and (not p["no_change_justification"] or not p["evidence_locators"]): raise SynthesisError("unjustified no_change")
            if p["status"]=="complete": accepted += p["proposal_ids"]
        if len(accepted)!=len(set(accepted)): raise SynthesisError("duplicate proposal")
        decision={"accepted":sorted(accepted),"rejected":[],"deferred":[],"conflicts":[],"justifications":{x:"accepted departmental proposal" for x in accepted},"packet_hashes":hashes,"proposal_hashes":{},"application_order":[],"dependencies":{},"validations":{}}
        body={"schema_version":"1.1.0","run_id":ident[0][0],"cycle_id":ident[0][1],"base_hash":ident[0][2],"packets":packets,"packet_hashes":hashes,"decision":decision}
        raw=_json(body); body["synthesis_hash"]=_sha(raw); body["frozen_bytes"]=raw; return body
    def freeze_synthesis(self,synthesis):
        raw=synthesis.get("frozen_bytes")
        if not isinstance(raw,bytes) or _sha(raw)!=synthesis.get("synthesis_hash"): raise SynthesisError("invalid frozen synthesis")
        path=self.root/"state/synthesis"/synthesis["synthesis_hash"]/"synthesis.json"; path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            if path.read_bytes()!=raw: raise IntegrityError("synthesis collision")
        else: _atomic(path,raw)
        return path
    def _proposals(self,syn,proposals):
        got={p.get("proposal_id"):dict(p) for p in proposals}; accepted=syn["decision"]["accepted"]
        if len(got)!=len(proposals) or set(got)!=set(accepted): raise SynthesisError("proposal set diverges")
        hashes={}
        for i,p in got.items():
            try: validate_output(self.root,"agent-proposal.schema.json",p)
            except PromptContractError as e: raise SynthesisError("invalid proposal") from e
            if p["cycle_id"]!=syn["cycle_id"] or p["base_hash"]!=syn["base_hash"]: raise SynthesisError("stale proposal")
            hashes[i]=_sha(_json(p))
        deps={x:[d for d in got[x]["dependencies"] if d in got] for x in got}; order=[]; todo=set(got)
        while todo:
            ready=sorted(x for x in todo if not set(deps[x])&todo)
            if not ready: raise SynthesisError("circular dependencies")
            order+=ready; todo.difference_update(ready)
        return [got[x] for x in order],hashes,order
    def _apply(self,stage,proposals):
        touched=set()
        for p in proposals:
            change=p["patch_or_operations"]
            if change.get("kind")!="operations": raise SynthesisError("text patch needs audited adapter")
            for op in change.get("operations",[]):
                if set(op)-{"op","target","value"} or op.get("op") not in {"add","replace","remove","annotate"}: raise SynthesisError("operation not allowlisted")
                target=_contained(stage,op.get("target"),op["op"] in {"replace","remove","annotate"}); key=_rel(op["target"]).as_posix().casefold()
                if key in touched: raise SynthesisError("overlapping operation")
                touched.add(key)
                if op["op"]=="remove": target.unlink(); continue
                if not isinstance(op.get("value"),str): raise SynthesisError("operation value must be text")
                target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists(): _regular(target)
                with target.open("w",encoding="utf-8",newline="") as f: f.write(op["value"]); f.flush(); os.fsync(f.fileno())
    def _existing(self,path,cid,syn,hashes):
        manifest=path/"manifest.json"; _regular(manifest)
        try: m=json.loads(manifest.read_text())
        except Exception as e: raise IntegrityError("invalid manifest") from e
        if m.get("candidate_id")!=cid or m.get("synthesis_hash")!=syn["synthesis_hash"] or m.get("proposal_hashes")!=hashes: raise IntegrityError("candidate identity diverges")
        if m.get("content_hash")!=tree_hash(path,exclude={"manifest.json"}) or m.get("inventory")!=_inventory(path,{"manifest.json"}): raise IntegrityError("candidate content diverges")
        return m
    def build(self,synthesis,proposals,champion):
        if _sha(synthesis.get("frozen_bytes",b""))!=synthesis.get("synthesis_hash"): raise SynthesisError("unfrozen synthesis")
        self.freeze_synthesis(synthesis); source=Path(champion).resolve()
        if tree_hash(source,exclude={"manifest.json"})!=synthesis["base_hash"]: raise SynthesisError("wrong base")
        ordered,hashes,order=self._proposals(synthesis,proposals)
        cid="c-"+_sha(_json({"run":synthesis["run_id"],"cycle":synthesis["cycle_id"],"base":synthesis["base_hash"],"synthesis":synthesis["synthesis_hash"],"hashes":hashes,"order":order}))[:32]
        published=self.root/"versions/challengers"/cid
        if published.exists(): return self._existing(published,cid,synthesis,hashes)
        stage=Path(tempfile.mkdtemp(prefix=cid+"-",dir=self.root/"workspaces"))
        try:
            self._hit("before_staging"); _copy(source,stage,{"manifest.json"}); self._hit("after_copy"); self._apply(stage,ordered); self._hit("after_apply")
            content=tree_hash(stage)
            base_manifest=source/"manifest.json"
            try: base_id=json.loads(base_manifest.read_text()).get("candidate_id","v0000")
            except Exception: base_id="v0000"
            m={"schema_version":"1.1.0","candidate_id":cid,"candidate_kind":"challenger","run_id":synthesis["run_id"],"cycle_id":synthesis["cycle_id"],"base_candidate_id":base_id,"base_hash":synthesis["base_hash"],"workspace_hash":content,"content_hash":content,"immutable":True,"source_proposal_ids":order,"proposal_ids":order,"prompt_versions":sorted({p["prompt_version"] for p in ordered}),"built_at":"1970-01-01T00:00:00Z","inventory":_inventory(stage),"merge_receipt_locator":f"state/synthesis/{synthesis['synthesis_hash']}/synthesis.json","merge_receipt":{"synthesis_hash":synthesis["synthesis_hash"],"proposal_hashes":hashes},"synthesis_hash":synthesis["synthesis_hash"],"proposal_hashes":hashes}
            _atomic(stage/"manifest.json",_json(m)); self._hit("after_manifest"); self._existing(stage,cid,synthesis,hashes); _fsync(stage); self._hit("before_rename")
            try: os.rename(stage,published)
            except FileExistsError: return self._existing(published,cid,synthesis,hashes)
            _fsync(published.parent); self._hit("after_rename"); return self._existing(published,cid,synthesis,hashes)
        finally:
            if stage.exists(): shutil.rmtree(stage)

    def record_state(self, store: DurableStore, run_id: str, state: State, artifact_hash: str):
        """Persist only the three M7 forward states, with idempotent event IDs."""
        if state not in {State.SYNTHESIS_READY,State.CANDIDATE_BUILT,State.GATES_PASSED}: raise SynthesisError("M7 state outside authority")
        key=f"m7:{run_id}:{state}:{artifact_hash}"
        return store.record(run_id,state,event_id=key,idempotency_key=key,actor_id="M7",event_type=state,payload={"artifact_hash":artifact_hash},artifact_hashes=[artifact_hash])
