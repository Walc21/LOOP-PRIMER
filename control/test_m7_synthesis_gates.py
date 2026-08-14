import json, os, shutil, sys, tempfile, unittest, jsonschema
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]/".prime/agent/skills/article-loop/src"))
from article_loop import DurableStore, M7Pipeline, State, SynthesisError, compare, run_gates, tree_hash
ROOT=Path(__file__).parents[1]; ROLES=("S10","S20","S30","S40","S50")
def packet(role,n,h,**kw):
 d={"schema_version":"1.1.0","packet_id":f"p{n}","run_id":"r","cycle_id":0,"department_id":role,"base_hash":h,"proposal_ids":["x1"] if role=="S10" else [],"specialist_task_ids":[],"dependency_reviews":[],"status":"complete" if role=="S10" else "no_change","no_change_justification":None if role=="S10" else "documented no-change rationale","evidence_locators":["e"],"created_at":"1970-01-01T00:00:00Z"}; d.update(kw); return d
def proposal(h,op=None,**kw):
 d={"schema_version":"1.1.0","proposal_id":"x1","role_id":"W11","cycle_id":0,"base_hash":h,"scope":["a.tex"],"evidence_locators":["e"],"patch_or_operations":{"kind":"operations","operations":[op or {"op":"replace","target":"a.tex","value":"new"}]},"affected_claims":[],"dependencies":[],"risk":{"level":"low","factors":[],"technical_effect_possible":False},"confidence":1,"requested_validations":[],"prompt_version":"v"}; d.update(kw); return d
class Adapter:
 def __init__(self,fail=(),mutate=False): self.fail=set(fail); self.mutate=mutate
 def verify(self,gate,candidate,manifest):
  if self.mutate and gate=="render": (candidate/"a.tex").write_text("changed")
  before=tree_hash(candidate)
  return {"command":f"article-loop-local-{gate}","verifier_version":"m7.2","input_hash":before,"classification":"scientific" if gate=="correctness_math" else "technical","output":"fixture","exit_code":0 if gate not in self.fail else 1,"evidence_locators":["proof/S20-W22.json"]}
class M7Tests(unittest.TestCase):
 def setUp(self):
  self.temp=Path(tempfile.mkdtemp()); shutil.copytree(ROOT/"config",self.temp/"config"); (self.temp/"versions/challengers").mkdir(parents=True); (self.temp/"workspaces").mkdir(); self.base=self.temp/"base"; (self.base/"proof").mkdir(parents=True); (self.base/"a.tex").write_text("old"); (self.base/"proof/S20-W22.json").write_text("fixture"); h=tree_hash(self.base); (self.base/"manifest.json").write_text(json.dumps({"candidate_id":"v0000","content_hash":h})); self.packets=[packet(r,i,h) for i,r in enumerate(ROLES,1)]; self.receipts={}
  for p in self.packets:
   path=self.temp/"state/receipts"/(p["department_id"]+".json"); path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()); self.receipts[p["department_id"]]={"immutable_path":path.relative_to(self.temp).as_posix(),"sha256":__import__("hashlib").sha256(path.read_bytes()).hexdigest()}
 def tearDown(self): shutil.rmtree(self.temp)
 def syn(self): return M7Pipeline(self.temp).synthesize(self.packets,receipts=self.receipts,proposals=[proposal(tree_hash(self.base,exclude={"manifest.json"}))])
 def candidate(self):
  s=self.syn(); m=M7Pipeline(self.temp).build(s,[proposal(s["base_hash"])],self.base); return self.temp/"versions/challengers"/m["candidate_id"],m
 def test_exact_five_identity_receipts_and_freeze(self):
  s=self.syn(); self.assertEqual(M7Pipeline(self.temp).freeze_synthesis(s).read_bytes(),s["frozen_bytes"])
  for bad in (self.packets[:4],self.packets+[self.packets[0]],self.packets[:4]+[self.packets[0]]):
   with self.assertRaises(SynthesisError): M7Pipeline(self.temp).synthesize(bad,receipts=self.receipts,proposals=[proposal(tree_hash(self.base,exclude={"manifest.json"}))])
  x=list(self.packets); x[1]=dict(x[1],run_id="other")
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).synthesize(x,receipts=self.receipts,proposals=[proposal(tree_hash(self.base,exclude={"manifest.json"}))])
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).synthesize(self.packets)
  (self.temp/self.receipts["S10"]["immutable_path"]).write_text("tampered")
  with self.assertRaises(SynthesisError): self.syn()
 def test_blocked_and_no_change_are_fail_closed(self):
  x=list(self.packets); x[2]=dict(x[2],status="blocked",no_change_justification=None)
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).synthesize(x,receipts=self.receipts,proposals=[proposal(tree_hash(self.base,exclude={"manifest.json"}))])
  x=list(self.packets); x[1]=dict(x[1],no_change_justification="")
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).synthesize(x,receipts=self.receipts,proposals=[proposal(tree_hash(self.base,exclude={"manifest.json"}))])
 def test_manifest_write_once_and_champion_unchanged(self):
  c,m=self.candidate(); jsonschema.validate(m,json.loads((self.temp/"config/schemas/candidate-manifest.schema.json").read_text())); self.assertEqual((self.base/"a.tex").read_text(),"old"); self.assertEqual((c/"a.tex").read_text(),"new"); self.assertEqual(M7Pipeline(self.temp).build(self.syn(),[proposal(self.syn()["base_hash"])],self.base)["candidate_id"],m["candidate_id"])
 def test_rejects_traversal_overlap_stale_circular_and_links(self):
  s=self.syn(); p=proposal(s["base_hash"],{"op":"replace","target":"../bad","value":"x"})
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).build(s,[p],self.base)
  p=proposal(s["base_hash"],{"op":"replace","target":"a.tex","value":"x"}); p["patch_or_operations"]["operations"].append({"op":"replace","target":"a.tex","value":"y"})
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).build(s,[p],self.base)
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).build(s,[proposal("0"*64)],self.base)
  p=proposal(s["base_hash"],dependencies=["unaccepted"])
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).synthesize(self.packets,receipts=self.receipts,proposals=[p])
  (self.base/"link").symlink_to(self.base/"a.tex")
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).build(s,[proposal(s["base_hash"])],self.base)
 def test_gates_report_and_mutation_detection(self):
  c,_=self.candidate(); r=run_gates(c,adapter=Adapter()); jsonschema.validate(r,json.loads((self.temp/"config/schemas/gate-report.schema.json").read_text())); self.assertTrue(r["overall_pass"]); self.assertTrue((self.temp/r["report_locator"]).is_file())
  with self.assertRaises(TypeError): run_gates(c,math_evidence=True)
  with self.assertRaises(Exception): run_gates(c,adapter=Adapter(mutate=True))
 def test_gate_failures_and_pure_comparison(self):
  c,_=self.candidate(); r=run_gates(c,adapter=Adapter({"latex_compile_safe"})); self.assertFalse(r["overall_pass"]); self.assertFalse(run_gates(c)["overall_pass"])
  out=compare({"correctness_math_pass":False,"issues":[],"pareto_vector":[9]}, {"correctness_math_pass":True,"issues":[],"pareto_vector":[0]}); self.assertEqual(out["winner"],"right"); self.assertFalse(out["promotion_authorized"])
 def test_real_champion_tree_and_nested_target(self):
  (self.base/"source").mkdir(); (self.base/"latex-source").mkdir(); (self.base/"source/data.txt").write_text("data"); (self.base/"latex-source/paper.tex").write_text("old paper")
  h=tree_hash(self.base,exclude={"manifest.json"}); self.packets=[packet(r,i,h) for i,r in enumerate(ROLES,1)]
  for p in self.packets:
   path=self.temp/"state/receipts"/(p["department_id"]+".json"); path.write_bytes(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()); self.receipts[p["department_id"]]["sha256"]=__import__("hashlib").sha256(path.read_bytes()).hexdigest()
  p=proposal(h,{"op":"replace","target":"latex-source/paper.tex","value":"new paper"}); s=M7Pipeline(self.temp).synthesize(self.packets,receipts=self.receipts,proposals=[p]); m=M7Pipeline(self.temp).build(s,[p],self.base)
  self.assertEqual((self.temp/"versions/challengers"/m["candidate_id"]/"latex-source/paper.tex").read_text(),"new paper")
  self.assertEqual((self.base/"latex-source/paper.tex").read_text(),"old paper")
 def test_rejects_intermediate_link_hardlink_and_special_file(self):
  s=self.syn(); (self.base/"nested").mkdir(); (self.base/"nested/link").symlink_to(self.base/"proof")
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).build(s,[proposal(s["base_hash"],{"op":"add","target":"nested/link/x.tex","value":"x"})],self.base)
  (self.base/"nested/link").unlink(); os.link(self.base/"a.tex",self.base/"nested/copy.tex")
  with self.assertRaises(SynthesisError): tree_hash(self.base)
  (self.base/"nested/copy.tex").unlink(); os.mkfifo(self.base/"nested/pipe")
  with self.assertRaises(SynthesisError): tree_hash(self.base)
 def test_frozen_proposal_bytes_and_existing_candidate_are_revalidated(self):
  s=self.syn(); changed=proposal(s["base_hash"],{"op":"replace","target":"a.tex","value":"different"})
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).build(s,[changed],self.base)
  c,m=self.candidate(); (c/"a.tex").write_text("tampered")
  with self.assertRaises(Exception): M7Pipeline(self.temp).build(s,[proposal(s["base_hash"])],self.base)
  self.assertEqual(m["candidate_id"],c.name)
 def test_gate_rejects_timeout_excess_output_and_linked_evidence(self):
  c,_=self.candidate()
  class Bad(Adapter):
   def verify(self,gate,candidate,manifest): return {"command":f"article-loop-local-{gate}","verifier_version":"m7.2","input_hash":tree_hash(candidate),"classification":"scientific","exit_code":0,"duration_ms":1001,"output":"x"*5000,"evidence_locators":["proof/S20-W22.json"]}
  self.assertFalse(run_gates(c,adapter=Bad())["overall_pass"])
  (c/"proof/linked.json").symlink_to(c/"proof/S20-W22.json")
  class Linked(Adapter):
   def verify(self,gate,candidate,manifest): return {"command":f"article-loop-local-{gate}","verifier_version":"m7.2","input_hash":tree_hash(candidate),"classification":"scientific","exit_code":0,"evidence_locators":["proof/linked.json"]}
  with self.assertRaises(Exception): run_gates(c,adapter=Linked())
 def test_m7_records_only_the_three_forward_states(self):
  store=DurableStore(self.temp); store.create_run("r",actor_id="test")
  for n,state in enumerate((State.INGESTED,State.SOURCE_READY,State.CYCLE_PLANNED,State.DEPARTMENTS_RUNNING),1): store.record("r",state,event_id=f"pre-{n}",idempotency_key=f"pre-{n}",actor_id="test")
  pipe=M7Pipeline(self.temp)
  for n,state in enumerate((State.SYNTHESIS_READY,State.CANDIDATE_BUILT,State.GATES_PASSED),1):
   event=pipe.record_state(store,"r",state,"a"*63+str(n)); self.assertEqual(event["state_to"],state)
  with self.assertRaises(SynthesisError): pipe.record_state(store,"r",State.EVALUATED,"b"*64)
 def test_recovery_at_publication_rename_boundaries(self):
  for point in ("before_rename","after_rename"):
   with self.subTest(point=point):
    p=proposal(tree_hash(self.base,exclude={"manifest.json"}),{"op":"replace","target":"a.tex","value":point})
    s=M7Pipeline(self.temp).synthesize(self.packets,receipts=self.receipts,proposals=[p])
    def fault(name):
     if name == point: raise RuntimeError(point)
    with self.assertRaises(RuntimeError): M7Pipeline(self.temp,fault=fault).build(s,[p],self.base)
    manifest=M7Pipeline(self.temp).build(s,[p],self.base)
    self.assertTrue((self.temp/"versions/challengers"/manifest["candidate_id"]/"manifest.json").is_file())
  self.assertFalse(any((self.temp/"workspaces").iterdir()))
