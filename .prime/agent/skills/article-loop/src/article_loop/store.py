"""Append-only local durable state with replay, locks and atomic snapshots."""
from __future__ import annotations
import fcntl,hashlib,json,os,tempfile
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from typing import Any,Mapping,Callable
from .state_machine import State,TransitionError,require_transition
SCHEMA_VERSION="1.1.0"
class StoreError(RuntimeError):pass
class IntegrityError(StoreError):pass
class StopRequested(StoreError):pass
def _bytes(v:Mapping[str,Any])->bytes:return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def _hash(v:bytes)->str:return hashlib.sha256(v).hexdigest()
def _now()->str:return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
class DurableStore:
 """Filesystem-only store rooted at an existing validated project directory."""
 def __init__(self,root:str|Path,*,fault:Callable[[str],None]|None=None):
  self.root=Path(root).resolve();self.fault=fault
  if not self.root.is_dir():raise StoreError("root must be an existing directory")
  for x in ("state/events","state/snapshots","state/checkpoints","state/locks"):(self.root/x).mkdir(parents=True,exist_ok=True)
 def _p(self,x:str)->Path:
  p=(self.root/x).resolve()
  if self.root not in p.parents:return (_ for _ in ()).throw(StoreError("path escapes validated root"))
  return p
 def _log(self,r):return self._p(f"state/events/{r}.jsonl")
 def _snap(self,r):return self._p(f"state/snapshots/{r}.json")
 @contextmanager
 def _lock(self,r):
  with self._p(f"state/locks/{r}.lock").open("a+") as f:
   fcntl.flock(f,fcntl.LOCK_EX)
   try:yield
   finally:fcntl.flock(f,fcntl.LOCK_UN)
 def _ehash(self,e):
  d=dict(e);d.pop("event_hash",None);return _hash(_bytes(d))
 def _atomic(self,p:Path,v:Mapping[str,Any]):
  data=_bytes(v);fd,n=tempfile.mkstemp(prefix=".tmp-",dir=p.parent);t=Path(n)
  try:
   with os.fdopen(fd,"wb") as f:f.write(data);f.flush();os.fsync(f.fileno())
   if self.fault:self.fault("before_rename")
   os.replace(t,p)
   if self.fault:self.fault("after_rename")
   if _hash(p.read_bytes())!=_hash(data):raise IntegrityError("atomic hash verification failed")
  finally:
   if t.exists():t.unlink()
 def read_events(self,r:str)->list[dict[str,Any]]:
  p=self._log(r)
  if not p.exists():return []
  out=[];lines=p.read_bytes().splitlines(keepends=True)
  for i,line in enumerate(lines):
   if not line.endswith(b"\n"):
    if i==len(lines)-1:break
    raise IntegrityError("partial event line")
   try:e=json.loads(line)
   except json.JSONDecodeError as x:raise IntegrityError("invalid event JSON") from x
   if e.get("event_hash")!=self._ehash(e):raise IntegrityError("event hash mismatch")
   if e.get("sequence")!=len(out) or e.get("previous_event_hash")!=(out[-1]["event_hash"] if out else None):raise IntegrityError("event chain mismatch")
   out.append(e)
  return out
 def _snapshot(self,r,es):
  if es:last=es[-1];state=last["state_to"];seq=last["sequence"];cycle=last["cycle_id"];lid=last["event_id"];lh=last["event_hash"];resume=last["payload"].get("resume_state") if state=="PAUSED" else None
  else:state="NEW";seq=-1;cycle=0;lid=lh=resume=None
  data={"resume_state":resume};d={"schema_version":SCHEMA_VERSION,"snapshot_id":f"{r}:{seq}","run_id":r,"cycle_id":cycle,"event_sequence":seq,"created_at":_now(),"state":state,"last_event_id":lid,"last_event_hash":lh,"data":data,"data_hash":_hash(_bytes(data))};d["snapshot_hash"]=_hash(_bytes(d));return d
 def rebuild_snapshot(self,r:str,*,persist=True):
  d=self._snapshot(r,self.read_events(r))
  if persist:self._atomic(self._snap(r),d)
  return d
 def snapshot(self,r):return self.rebuild_snapshot(r,persist=False)
 def create_run(self,r:str,*,actor_id="system",event_id=None):return self.record(r,State.NEW,event_id=event_id or r+":created",idempotency_key=r+":created",actor_id=actor_id,event_type="RUN_CREATED",initial=True)
 def record(self,r:str,target:State,*,event_id:str,idempotency_key:str,actor_id:str,event_type="STATE_RECORDED",payload:Mapping[str,Any]|None=None,artifact_hashes:list[str]|None=None,initial=False):
  if self._p("control/STOP").is_file():raise StopRequested("control/STOP blocks new operations")
  with self._lock(r):
   es=self.read_events(r)
   for e in es:
    if e["event_id"]==event_id or e["idempotency_key"]==idempotency_key:
     if e["event_id"]==event_id and e["idempotency_key"]==idempotency_key and e["state_to"]==target.value:return e
     raise StoreError("idempotency conflict")
   if not es:
    if not initial or target is not State.NEW:raise TransitionError("run must begin at NEW")
    current=State.NEW;frm=None;cycle=0
   else:
    current=State(es[-1]["state_to"]);frm=current.value;resume=State(es[-1]["payload"]["resume_state"]) if current is State.PAUSED else None;require_transition(current,target,resume_to=resume);cycle=es[-1]["cycle_id"]+(current is State.CYCLE_COMPLETE and target is State.CYCLE_PLANNED)
   pay=dict(payload or {})
   if target is State.PAUSED:pay["resume_state"]=current.value
   e={"schema_version":SCHEMA_VERSION,"event_id":event_id,"idempotency_key":idempotency_key,"run_id":r,"cycle_id":cycle,"sequence":len(es),"occurred_at":_now(),"event_type":event_type,"state_from":frm,"state_to":target.value,"actor_id":actor_id,"payload":pay,"artifact_hashes":sorted(set(artifact_hashes or [])),"previous_event_hash":es[-1]["event_hash"] if es else None};e["event_hash"]=self._ehash(e)
   with self._log(r).open("ab") as f:f.write(_bytes(e)+b"\n");f.flush();os.fsync(f.fileno())
   self.rebuild_snapshot(r,persist=True);return e
 def pause(self,r:str,**kw):return self.record(r,State.PAUSED,**kw)
 def resume(self,r:str,**kw):
  s=self.snapshot(r)["data"]["resume_state"]
  if not s:raise TransitionError("run is not paused")
  return self.record(r,State(s),**kw)
 def checkpoint(self,r:str):
  with self._lock(r):
   s=self.rebuild_snapshot(r,persist=True);self._atomic(self._p(f"state/checkpoints/{r}-{s['event_sequence']}.json"),s);return s
