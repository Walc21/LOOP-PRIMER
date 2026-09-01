"""M7 synthesis from immutable M6 receipts and write-once challengers."""
from __future__ import annotations
import hashlib, json, os, shutil, stat, tempfile, unicodedata
from pathlib import Path, PurePosixPath
from typing import Any, Mapping
from .activation import DEPARTMENTS
import jsonschema
from .prompts import FORMAT_CHECKER, PromptContractError, validate_output
from .store import DurableStore, IntegrityError
from .state_machine import State

class SynthesisError(RuntimeError): pass
def _json(v: Any) -> bytes: return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
def _sha(v: bytes) -> str: return hashlib.sha256(v).hexdigest()
def _validate_schema(root: Path,schema: str,value: Mapping[str,Any]):
    try: definition=json.loads((Path(root)/"config/schemas"/schema).read_text(encoding="utf-8")); jsonschema.Draft202012Validator(definition,format_checker=FORMAT_CHECKER).validate(dict(value))
    except (OSError,json.JSONDecodeError,jsonschema.ValidationError,jsonschema.SchemaError) as exc: raise SynthesisError(f"invalid {schema}") from exc
def _rel(name: str) -> PurePosixPath:
    p=PurePosixPath(name) if isinstance(name,str) else None
    if not p or not name or "\0" in name or p.is_absolute() or any(x in {"", ".", ".."} for x in p.parts): raise SynthesisError("unsafe target")
    if any(unicodedata.normalize("NFC",x)!=x for x in p.parts): raise SynthesisError("non-canonical target")
    return p
def _contained(root: Path,name: str,exists=False) -> Path:
    root=Path(root).resolve(); p=_rel(name); current=root
    for part in p.parts[:-1]:
        current/=part
        if current.exists() or current.is_symlink():
            mode=current.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode): raise SynthesisError("unsafe intermediate target")
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
    root=Path(root); exclude=exclude or set()
    try: s=root.lstat()
    except OSError as e: raise SynthesisError("tree root is unavailable") from e
    if stat.S_ISLNK(s.st_mode) or not stat.S_ISDIR(s.st_mode): raise SynthesisError("tree root is not a real directory")
    out=[]; seen=set(); inodes=set()
    for base,dirs,files in os.walk(root,topdown=True,followlinks=False):
        dirs.sort(); files.sort(); here=Path(base)
        for name in list(dirs)+files:
            path=here/name; rel=path.relative_to(root).as_posix()
            if rel in exclude:
                if name in dirs: dirs.remove(name)
                continue
            info=path.lstat()
            if stat.S_ISLNK(info.st_mode) or not(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)): raise SynthesisError("tree contains link or special file")
            folded=unicodedata.normalize("NFC",rel).casefold()
            if folded in seen: raise SynthesisError("case collision or normalized duplicate")
            seen.add(folded)
            if stat.S_ISREG(info.st_mode):
                inode=(info.st_dev,info.st_ino)
                if info.st_nlink != 1 or inode in inodes: raise SynthesisError("hardlink in immutable tree")
                inodes.add(inode)
            out.append((rel,path,info))
    return out
def tree_hash(root: Path,*,exclude: set[str]|None=None) -> str:
    return _sha(_json([["d",r] if stat.S_ISDIR(s.st_mode) else ["f",r,s.st_size,_sha(p.read_bytes())] for r,p,s in _walk(root,exclude)]))
def _inventory(root: Path,exclude: set[str]|None=None): return [{"path":r,"sha256":_sha(p.read_bytes()),"size":s.st_size} for r,p,s in _walk(root,exclude) if stat.S_ISREG(s.st_mode)]
def _fsync(path: Path):
    fd=os.open(path,os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)
def _fsync_tree_dirs(root: Path):
    for _,path,s in reversed(_walk(root)):
        if stat.S_ISDIR(s.st_mode): _fsync(path)
    _fsync(root)
def _atomic(path: Path,data: bytes):
    fd,temp=tempfile.mkstemp(prefix=".m7-",dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(temp,path); _fsync(path.parent)
    finally:
        if os.path.exists(temp): os.unlink(temp)
def _copy(source: Path,dest: Path,exclude: set[str]|None=None):
    dest.mkdir(exist_ok=True)
    for rel,path,s in _walk(source,exclude):
        target=dest/rel
        if stat.S_ISDIR(s.st_mode): target.mkdir()
        else:
            target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,target); os.chmod(target,stat.S_IMODE(s.st_mode)); _fsync(target)
    _fsync_tree_dirs(dest)
def _readonly(root: Path):
    for _,path,s in _walk(root): os.chmod(path,stat.S_IMODE(s.st_mode)&~0o222)
    s=root.lstat(); os.chmod(root,stat.S_IMODE(s.st_mode)&~0o222); _fsync_tree_dirs(root)
def _discard_stage(root: Path):
    for base,dirs,files in os.walk(root,topdown=False,followlinks=False):
        for name in files: os.chmod(Path(base)/name,0o600)
        for name in dirs: os.chmod(Path(base)/name,0o700)
    os.chmod(root,0o700); shutil.rmtree(root)

def _m6_receipt(root: Path,run_id: str,receipt: Mapping[str,Any],schema: str,*,sender: str|None=None) -> tuple[dict[str,Any],bytes]:
    """Read exact M6 frozen bytes once; parsing happens only after SHA verification."""
    digest=receipt.get("sha256") if isinstance(receipt,Mapping) else None
    if not isinstance(digest,str) or len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest): raise SynthesisError("invalid M6 receipt hash")
    managed=(Path(root).resolve()/"state"/"orchestration"/run_id/"receipts"/digest).resolve()
    try: managed.relative_to(Path(root).resolve())
    except ValueError as e: raise SynthesisError("M6 receipt escapes managed root") from e
    expected=managed/"artifact.json"; advertised=receipt.get("immutable_path")
    if not isinstance(advertised,str) or not Path(advertised).is_absolute() or Path(advertised)!=expected: raise SynthesisError("M6 receipt path is not canonical")
    try: info=expected.lstat()
    except OSError as e: raise SynthesisError("M6 receipt is missing") from e
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode): raise SynthesisError("M6 receipt is not a regular file")
    raw=expected.read_bytes()
    if _sha(raw)!=digest: raise SynthesisError("M6 receipt bytes do not match hash")
    try: value=json.loads(raw); validate_output(root,schema,value)
    except (json.JSONDecodeError,PromptContractError) as e: raise SynthesisError("M6 receipt schema is invalid") from e
    if sender is not None and receipt.get("sender_role")!=sender: raise SynthesisError("M6 receipt sender differs")
    return dict(value),raw

class M7Pipeline:
    """M7 only freezes, publishes, and records evidence; it has no M8 authority."""
    def __init__(self,root: str|Path,*,fault=None):
        self.root=Path(root).resolve(); self.fault=fault
        for item in ("state/synthesis","versions/challengers","workspaces"): (self.root/item).mkdir(parents=True,exist_ok=True)
    def _hit(self,name):
        if self.fault: self.fault(name)
    def _validated_synthesis(self,synthesis: Mapping[str,Any]):
        """Rebuild a frozen decision from the M6 registry before using it."""
        raw=synthesis.get("frozen_bytes")
        if not isinstance(raw,bytes) or _sha(raw)!=synthesis.get("synthesis_hash"):
            raise SynthesisError("invalid frozen synthesis")
        try:
            body=json.loads(raw)
            decision=body["decision"]
            receipts=dict(decision["packet_receipts"])
            for receipt in decision["proposal_receipts"].values():
                role=receipt["sender_role"]
                if role in receipts: raise SynthesisError("duplicate receipt sender")
                receipts[role]=receipt
            rebuilt=self.synthesize(receipts,run_id=body["run_id"])
        except (KeyError,TypeError,json.JSONDecodeError) as exc:
            raise SynthesisError("frozen synthesis is malformed") from exc
        if rebuilt["frozen_bytes"]!=raw or rebuilt["synthesis_hash"]!=synthesis["synthesis_hash"]:
            raise SynthesisError("frozen synthesis does not match canonical M6 receipts")
        return rebuilt
    def synthesize(self,receipts: Mapping[str,Mapping[str,Any]],*,run_id: str):
        """Derive packets and proposals solely from the M6 receipt registry."""
        packets=[]; packet_hashes={}; packet_receipts={}
        for department in DEPARTMENTS:
            packet,raw=_m6_receipt(self.root,run_id,receipts.get(department,{}),"department-packet.schema.json",sender=department)
            if packet.get("run_id")!=run_id or packet.get("department_id")!=department: raise SynthesisError("packet run or department differs")
            packets.append(packet); packet_hashes[department]=_sha(raw); packet_receipts[department]=dict(receipts[department])
        identity={(p["cycle_id"],p["base_hash"],p["schema_version"]) for p in packets}
        if len(identity)!=1: raise SynthesisError("packet identity mismatch")
        cycle_id,base_hash,schema_version=next(iter(identity)); accepted=[]
        for packet in packets:
            if packet["status"]=="blocked": raise SynthesisError("blocked department cannot synthesize")
            if packet["status"]=="no_change" and (not packet["no_change_justification"] or not packet["evidence_locators"]): raise SynthesisError("unjustified no-change")
            if packet["status"]=="complete": accepted.extend(packet["proposal_ids"])
        if len(accepted)!=len(set(accepted)): raise SynthesisError("duplicate proposal")
        proposals={}; hashes={}; proposal_receipts={}
        for role,receipt in receipts.items():
            if not isinstance(role,str) or not role.startswith("W"): continue
            proposal,raw=_m6_receipt(self.root,run_id,receipt,"agent-proposal.schema.json",sender=role); proposal_id=proposal.get("proposal_id")
            if proposal_id in proposals: raise SynthesisError("duplicate M6 proposal id")
            proposals[proposal_id]=proposal; hashes[proposal_id]=_sha(raw); proposal_receipts[proposal_id]=dict(receipt)
        if set(proposals)!=set(accepted): raise SynthesisError("accepted proposals are not exactly M6 receipts")
        for proposal in proposals.values():
            if proposal["cycle_id"]!=cycle_id or proposal["base_hash"]!=base_hash or proposal["schema_version"]!=schema_version: raise SynthesisError("proposal identity differs")
            if any(dep not in proposals for dep in proposal["dependencies"]): raise SynthesisError("proposal dependency is absent")
        todo=set(proposals); order=[]
        while todo:
            ready=sorted(item for item in todo if not(set(proposals[item]["dependencies"])&todo))
            if not ready: raise SynthesisError("cyclic proposal dependencies")
            order.extend(ready); todo.difference_update(ready)
        decision={"accepted":order,"rejected":[],"deferred":[],"conflicts":[],"justifications":{x:"accepted departmental proposal" for x in order},"packet_hashes":packet_hashes,"packet_receipts":packet_receipts,"proposal_hashes":hashes,"proposal_receipts":proposal_receipts,"application_order":order,"dependencies":{x:proposals[x]["dependencies"] for x in order},"validations":{x:proposals[x]["requested_validations"] for x in order},"obsolete_claims":[]}
        body={"schema_version":"1.1.0","run_id":run_id,"cycle_id":cycle_id,"base_hash":base_hash,"packets":packets,"packet_hashes":packet_hashes,"decision":decision}; raw=_json(body)
        return {**body,"synthesis_hash":_sha(raw),"frozen_bytes":raw}
    def freeze_synthesis(self,synthesis: Mapping[str,Any]) -> Path:
        synthesis=self._validated_synthesis(synthesis); raw=synthesis["frozen_bytes"]
        path=self.root/"state/synthesis"/synthesis["synthesis_hash"] / "synthesis.json"; path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            if path.read_bytes()!=raw: raise IntegrityError("synthesis collision")
        else: _atomic(path,raw)
        return path
    def _frozen_proposals(self,synthesis):
        decision=synthesis["decision"]; result=[]
        for proposal_id in decision["application_order"]:
            proposal,raw=_m6_receipt(self.root,synthesis["run_id"],decision["proposal_receipts"].get(proposal_id,{}),"agent-proposal.schema.json")
            if _sha(raw)!=decision["proposal_hashes"].get(proposal_id) or proposal.get("proposal_id")!=proposal_id: raise SynthesisError("frozen proposal diverges")
            if proposal["cycle_id"]!=synthesis["cycle_id"] or proposal["base_hash"]!=synthesis["base_hash"]: raise SynthesisError("stale frozen proposal")
            result.append(proposal)
        return result
    def _apply(self,stage,proposals):
        touched=set()
        for proposal in proposals:
            change=proposal["patch_or_operations"]
            if change.get("kind")!="operations": raise SynthesisError("text patch needs audited adapter")
            for operation in change["operations"]:
                if set(operation)-{"op","target","value"} or operation.get("op") not in {"add","replace","remove","annotate"}: raise SynthesisError("operation not allowlisted")
                target=_contained(stage,operation["target"],operation["op"] in {"replace","remove","annotate"}); key=_rel(operation["target"]).as_posix().casefold()
                if key in touched: raise SynthesisError("overlapping operation")
                touched.add(key)
                if operation["op"]=="remove": target.unlink(); continue
                if not isinstance(operation.get("value"),str): raise SynthesisError("operation value must be text")
                target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists(): _regular(target)
                with target.open("w",encoding="utf-8",newline="") as file: file.write(operation["value"]); file.flush(); os.fsync(file.fileno())
    def _existing(self,path,candidate_id,synthesis,hashes):
        try: root_mode=stat.S_IMODE(Path(path).lstat().st_mode)
        except OSError as e: raise IntegrityError("published challenger is unavailable") from e
        if root_mode&0o222: raise IntegrityError("published challenger root became writable")
        manifest_path=path/"manifest.json"; _regular(manifest_path)
        try: manifest=json.loads(manifest_path.read_text())
        except Exception as e: raise IntegrityError("invalid manifest") from e
        try: _validate_schema(self.root,"candidate-manifest.schema.json",manifest)
        except SynthesisError as e: raise IntegrityError("candidate manifest schema invalid") from e
        if manifest.get("candidate_id")!=candidate_id or manifest.get("synthesis_hash")!=synthesis["synthesis_hash"] or manifest.get("proposal_hashes")!=hashes: raise IntegrityError("candidate identity diverges")
        if manifest.get("content_hash")!=tree_hash(path,exclude={"manifest.json"}) or manifest.get("inventory")!=_inventory(path,{"manifest.json"}): raise IntegrityError("candidate content diverges")
        for _,_,s in _walk(path):
            if stat.S_IMODE(s.st_mode)&0o222: raise IntegrityError("published challenger became writable")
        return manifest
    def build(self,synthesis: Mapping[str,Any],champion: str|Path):
        synthesis=self._validated_synthesis(synthesis); raw=synthesis["frozen_bytes"]
        frozen=self.freeze_synthesis(synthesis)
        if frozen.read_bytes()!=raw: raise IntegrityError("frozen synthesis diverges")
        source=Path(champion); tree_hash(source,exclude={"manifest.json"})
        try: source_manifest=json.loads((source/"manifest.json").read_text(encoding="utf-8")); base_hash=str(source_manifest["content_hash"])
        except (KeyError,OSError,json.JSONDecodeError) as exc: raise SynthesisError("base manifest is invalid") from exc
        if base_hash!=synthesis["base_hash"]: raise SynthesisError("wrong base")
        proposals=self._frozen_proposals(synthesis); hashes=synthesis["decision"]["proposal_hashes"]; order=synthesis["decision"]["application_order"]
        candidate_id="c-"+_sha(_json({"run":synthesis["run_id"],"cycle":synthesis["cycle_id"],"base":base_hash,"synthesis":synthesis["synthesis_hash"],"hashes":hashes,"order":order}))[:32]; published=self.root/"versions/challengers"/candidate_id
        if published.exists(): return self._existing(published,candidate_id,synthesis,hashes)
        stage=Path(tempfile.mkdtemp(prefix=".m7-"+candidate_id+"-",dir=published.parent))
        try:
            self._hit("before_staging"); _copy(source,stage,{"manifest.json"}); self._hit("after_copy"); self._apply(stage,proposals); self._hit("after_apply"); content=tree_hash(stage)
            base_id=str(source_manifest["candidate_id"])
            manifest={"schema_version":"1.1.0","candidate_id":candidate_id,"candidate_kind":"challenger","run_id":synthesis["run_id"],"cycle_id":synthesis["cycle_id"],"base_candidate_id":base_id,"base_hash":base_hash,"workspace_hash":content,"content_hash":content,"immutable":True,"source_proposal_ids":order,"proposal_ids":order,"prompt_versions":sorted({p["prompt_version"] for p in proposals}),"built_at":"1970-01-01T00:00:00Z","inventory":_inventory(stage),"merge_receipt_locator":f"state/synthesis/{synthesis['synthesis_hash']}/synthesis.json","merge_receipt":{"synthesis_hash":synthesis["synthesis_hash"],"proposal_hashes":hashes,"proposal_receipts":synthesis["decision"]["proposal_receipts"],"base_hash":base_hash},"synthesis_hash":synthesis["synthesis_hash"],"proposal_hashes":hashes}
            _atomic(stage/"manifest.json",_json(manifest))
            _readonly(stage)
            self._existing(stage,candidate_id,synthesis,hashes)
            self._hit("before_rename")
            os.rename(stage,published)
            self._hit("after_rename")
            _fsync(published.parent)
            self._hit("after_parent_fsync")
            return self._existing(published,candidate_id,synthesis,hashes)
        finally:
            if stage.exists(): _discard_stage(stage)
    def _record(self,store: DurableStore,run_id: str,target: State,artifact_hash: str,payload: Mapping[str,Any]):
        key=f"m7:{run_id}:{target.value}:{artifact_hash}"; return store.record(run_id,target,event_id=key,idempotency_key=key,actor_id="M7",event_type="M7_ARTIFACT",payload=dict(payload),artifact_hashes=[artifact_hash])
    def record_synthesis(self,store: DurableStore,synthesis: Mapping[str,Any]):
        verified=self._validated_synthesis(synthesis)
        path=self.freeze_synthesis(verified)
        if path.read_bytes()!=verified["frozen_bytes"]: raise IntegrityError("synthesis was not frozen")
        return self._record(store,verified["run_id"],State.SYNTHESIS_READY,verified["synthesis_hash"],{"synthesis_hash":verified["synthesis_hash"]})
    def record_candidate(self,store: DurableStore,manifest: Mapping[str,Any]):
        candidate_id=manifest.get("candidate_id")
        if not isinstance(candidate_id,str) or not candidate_id or "/" in candidate_id or "\\" in candidate_id: raise SynthesisError("candidate identifier is invalid")
        try:
            frozen=(self.root/"state/synthesis"/str(manifest.get("synthesis_hash"))/"synthesis.json").read_bytes()
            synthesis=self._validated_synthesis({"synthesis_hash":manifest.get("synthesis_hash"),"frozen_bytes":frozen})
        except (OSError,SynthesisError) as exc:
            raise SynthesisError("candidate has no valid frozen synthesis") from exc
        path=self.root/"versions/challengers"/candidate_id
        verified=self._existing(path,candidate_id,synthesis,dict(manifest.get("proposal_hashes",{})))
        if verified != dict(manifest) or manifest.get("candidate_kind")!="challenger" or manifest.get("immutable") is not True or not isinstance(manifest.get("content_hash"),str): raise SynthesisError("unpublished challenger")
        self._hit("before_candidate_built_event")
        event=self._record(store,manifest["run_id"],State.CANDIDATE_BUILT,manifest["content_hash"],{"candidate_id":manifest["candidate_id"],"candidate_hash":manifest["content_hash"]})
        self._hit("after_candidate_built_event")
        return event
    def record_gates(self,store: DurableStore,report_locator: str|Path):
        if isinstance(report_locator,Mapping):
            raise SynthesisError("an arbitrary mapping is not gate evidence")
        from .gates import verify_gate_report
        report=verify_gate_report(self.root,report_locator,store=store,require_candidate_built=True)
        if report["overall_pass"] is not True or report["correctness_math_pass"] is not True:
            raise SynthesisError("failed or inconclusive gates cannot advance")
        return self._record(store,report["run_id"],State.GATES_PASSED,report["report_hash"],{"candidate_id":report["candidate_id"],"candidate_hash":report["candidate_hash"],"report_locator":report["report_locator"]})
    def execute_and_record_gates(self,store: DurableStore,candidate: str|Path):
        from .gates import run_gates
        report=run_gates(candidate)
        self.record_gates(store,report["report_locator"])
        return report
