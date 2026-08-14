import json, os, shutil, sys, tempfile, unittest, jsonschema
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]/".prime/agent/skills/article-loop/src"))
from article_loop import M7Pipeline, SynthesisError, compare, run_gates, tree_hash
ROOT=Path(__file__).parents[1]; ROLES=("S10","S20","S30","S40","S50")
def packet(role,n,h,**kw):
 d={"schema_version":"1.1.0","packet_id":f"p{n}","run_id":"r","cycle_id":0,"department_id":role,"base_hash":h,"proposal_ids":["x1"] if role=="S10" else [],"specialist_task_ids":[],"dependency_reviews":[],"status":"complete" if role=="S10" else "no_change","no_change_justification":None if role=="S10" else "documented no-change rationale","evidence_locators":["e"],"created_at":"1970-01-01T00:00:00Z"}; d.update(kw); return d
def proposal(h,op=None,**kw):
 d={"schema_version":"1.1.0","proposal_id":"x1","role_id":"W11","cycle_id":0,"base_hash":h,"scope":["a.tex"],"evidence_locators":["e"],"patch_or_operations":{"kind":"operations","operations":[op or {"op":"replace","target":"a.tex","value":"new"}]},"affected_claims":[],"dependencies":[],"risk":{"level":"low","factors":[],"technical_effect_possible":False},"confidence":1,"requested_validations":[],"prompt_version":"v"}; d.update(kw); return d
class Adapter:
 def __init__(self,fail=(),mutate=False): self.fail=set(fail); self.mutate=mutate
 def verify(self,gate,candidate,manifest):
  if self.mutate and gate=="render": (candidate/"a.tex").write_text("changed")
  return {"passed":gate not in self.fail,"classification":"scientific" if gate=="correctness_math" else "technical","output":"fixture","exit_code":0 if gate not in self.fail else 1,"evidence_locators":["proof/S20-W22.json"]}
class M7Tests(unittest.TestCase):
 def setUp(self):
  self.temp=Path(tempfile.mkdtemp()); shutil.copytree(ROOT/"config",self.temp/"config"); (self.temp/"versions/challengers").mkdir(parents=True); (self.temp/"workspaces").mkdir(); self.base=self.temp/"base"; (self.base/"proof").mkdir(parents=True); (self.base/"a.tex").write_text("old"); (self.base/"proof/S20-W22.json").write_text("fixture"); h=tree_hash(self.base); (self.base/"manifest.json").write_text(json.dumps({"candidate_id":"v0000","content_hash":h})); self.packets=[packet(r,i,h) for i,r in enumerate(ROLES,1)]; self.receipts={}
  for p in self.packets:
   path=self.temp/"state/receipts"/(p["department_id"]+".json"); path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()); self.receipts[p["department_id"]]={"immutable_path":path.relative_to(self.temp).as_posix(),"sha256":__import__("hashlib").sha256(path.read_bytes()).hexdigest()}
 def tearDown(self): shutil.rmtree(self.temp)
 def syn(self): return M7Pipeline(self.temp).synthesize(self.packets,receipts=self.receipts)
 def candidate(self):
  s=self.syn(); m=M7Pipeline(self.temp).build(s,[proposal(s["base_hash"])],self.base); return self.temp/"versions/challengers"/m["candidate_id"],m
 def test_exact_five_identity_receipts_and_freeze(self):
  s=self.syn(); self.assertEqual(M7Pipeline(self.temp).freeze_synthesis(s).read_bytes(),s["frozen_bytes"])
  for bad in (self.packets[:4],self.packets+[self.packets[0]],self.packets[:4]+[self.packets[0]]):
   with self.assertRaises(SynthesisError): M7Pipeline(self.temp).synthesize(bad,receipts=self.receipts)
  x=list(self.packets); x[1]=dict(x[1],run_id="other")
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).synthesize(x,receipts=self.receipts)
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).synthesize(self.packets)
  (self.temp/self.receipts["S10"]["immutable_path"]).write_text("tampered")
  with self.assertRaises(SynthesisError): self.syn()
 def test_blocked_and_no_change_are_fail_closed(self):
  x=list(self.packets); x[2]=dict(x[2],status="blocked",no_change_justification=None)
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).synthesize(x,receipts=self.receipts)
  x=list(self.packets); x[1]=dict(x[1],no_change_justification="")
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).synthesize(x,receipts=self.receipts)
 def test_manifest_write_once_and_champion_unchanged(self):
  c,m=self.candidate(); jsonschema.validate(m,json.loads((self.temp/"config/schemas/candidate-manifest.schema.json").read_text())); self.assertEqual((self.base/"a.tex").read_text(),"old"); self.assertEqual((c/"a.tex").read_text(),"new"); self.assertEqual(M7Pipeline(self.temp).build(self.syn(),[proposal(self.syn()["base_hash"])],self.base)["candidate_id"],m["candidate_id"])
 def test_rejects_traversal_overlap_stale_circular_and_links(self):
  s=self.syn(); p=proposal(s["base_hash"],{"op":"replace","target":"../bad","value":"x"})
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).build(s,[p],self.base)
  p=proposal(s["base_hash"],{"op":"replace","target":"a.tex","value":"x"}); p["patch_or_operations"]["operations"].append({"op":"replace","target":"a.tex","value":"y"})
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).build(s,[p],self.base)
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).build(s,[proposal("0"*64)],self.base)
  (self.base/"link").symlink_to(self.base/"a.tex")
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).build(s,[proposal(s["base_hash"])],self.base)
 def test_gates_report_and_mutation_detection(self):
  c,_=self.candidate(); r=run_gates(c,adapter=Adapter()); jsonschema.validate(r,json.loads((self.temp/"config/schemas/gate-report.schema.json").read_text())); self.assertTrue(r["overall_pass"]); self.assertTrue((self.temp/r["report_locator"]).is_file())
  with self.assertRaises(TypeError): run_gates(c,math_evidence=True)
  with self.assertRaises(Exception): run_gates(c,adapter=Adapter(mutate=True))
 def test_gate_failures_and_pure_comparison(self):
  c,_=self.candidate(); r=run_gates(c,adapter=Adapter({"latex_compile_safe"})); self.assertFalse(r["overall_pass"]); self.assertFalse(run_gates(c)["overall_pass"])
  out=compare({"correctness_math_pass":False,"issues":[],"pareto_vector":[9]}, {"correctness_math_pass":True,"issues":[],"pareto_vector":[0]}); self.assertEqual(out["winner"],"right"); self.assertFalse(out["promotion_authorized"])
