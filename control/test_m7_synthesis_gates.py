import json, shutil, sys, tempfile, unittest, jsonschema
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]/".prime/agent/skills/article-loop/src"))
from article_loop import M7Pipeline, SynthesisError, run_gates, tree_hash
ROOT=Path(__file__).parents[1]
def packet(role, n, h): return {"schema_version":"1.1.0","packet_id":f"p{n}","run_id":"r","cycle_id":0,"department_id":role,"base_hash":h,"proposal_ids":[f"x{n}"],"specialist_task_ids":[],"dependency_reviews":[],"status":"complete","no_change_justification":None,"evidence_locators":["e"],"created_at":"1970-01-01T00:00:00Z"}
class M7Tests(unittest.TestCase):
 def setUp(self):
  self.temp=Path(tempfile.mkdtemp()); shutil.copytree(ROOT/"config",self.temp/"config"); (self.temp/"versions/challengers").mkdir(parents=True); (self.temp/"workspaces").mkdir(); self.base=self.temp/"base"; self.base.mkdir(); (self.base/"a.tex").write_text("old"); h=tree_hash(self.base); self.packets=[packet(r,i,h) for i,r in enumerate(("S10","S20","S30","S40","S50"),1)]; (self.base/"manifest.json").write_text(json.dumps({"candidate_id":"v0000","content_hash":h}))
 def tearDown(self): shutil.rmtree(self.temp)
 def test_exact_identity_and_freeze(self):
  x=M7Pipeline(self.temp).synthesize(self.packets); self.assertEqual(M7Pipeline(self.temp).freeze_synthesis(x).read_bytes(),x["frozen_bytes"])
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).synthesize(self.packets[:4])
  b=list(self.packets); b[1]=dict(b[1],run_id="other")
  with self.assertRaises(SynthesisError): M7Pipeline(self.temp).synthesize(b)
 def test_build_gate_failure_and_idempotency(self):
  pipe=M7Pipeline(self.temp); syn=pipe.synthesize(self.packets); p={"schema_version":"1.1.0","proposal_id":"x1","role_id":"W11","cycle_id":0,"base_hash":syn["base_hash"],"scope":["a"],"evidence_locators":["e"],"patch_or_operations":{"kind":"operations","operations":[{"op":"replace","target":"a.tex","value":"new"}]},"affected_claims":[],"dependencies":[],"risk":{"level":"low","factors":[],"technical_effect_possible":False},"confidence":1,"requested_validations":[],"prompt_version":"v"}; out=pipe.build(syn,[p],self.base); candidate=self.temp/"versions/challengers"/out["candidate_id"]; jsonschema.validate(out,json.loads((self.temp/"config/schemas/candidate-manifest.schema.json").read_text())); report=run_gates(candidate); jsonschema.validate(report,json.loads((self.temp/"config/schemas/gate-report.schema.json").read_text())); self.assertFalse(report["overall_pass"]); self.assertEqual((self.base/"a.tex").read_text(),"old"); self.assertEqual(pipe.build(syn,[p],self.base)["candidate_id"],out["candidate_id"])
 def test_rejects_technical_block_and_traversal(self):
  pipe=M7Pipeline(self.temp); b=list(self.packets); b[2]=dict(b[2],status="blocked",proposal_ids=[])
  with self.assertRaises(SynthesisError): pipe.synthesize(b)
  syn=pipe.synthesize(self.packets); p={"schema_version":"1.1.0","proposal_id":"x1","role_id":"W11","cycle_id":0,"base_hash":syn["base_hash"],"scope":["a"],"evidence_locators":["e"],"patch_or_operations":{"kind":"operations","operations":[{"op":"replace","target":"../bad","value":"x"}]},"affected_claims":[],"dependencies":[],"risk":{"level":"low","factors":[],"technical_effect_possible":False},"confidence":1,"requested_validations":[],"prompt_version":"v"}
  with self.assertRaises(SynthesisError): pipe.build(syn,[p],self.base)
