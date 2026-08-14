import asyncio, hashlib, shutil, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / ".prime/agent/skills/article-loop/src"))
from article_loop import FakeRLMAdapter, Orchestrator

class M6OrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        shutil.copytree(Path(__file__).parents[1] / "config", self.root / "config")
        self.pdf = self.root / "a.pdf"; self.pdf.write_bytes(b"pdf")
        self.fake = FakeRLMAdapter(); self.o = Orchestrator(self.root, self.fake)
        self.state = asyncio.run(self.o.bootstrap(self.pdf)); self.run = self.state["run_id"]
    def tearDown(self): self.temp.cleanup()
    def cycle(self): return asyncio.run(self.o.run_cycle(run_id=self.run))
    def proposal(self, role):
        return {"schema_version":"1.1.0","proposal_id":f"p-{role}","role_id":role,"cycle_id":0,
                "base_hash":self.state["pdf_sha256"],"scope":["proof"],"evidence_locators":["page:1"],
                "patch_or_operations":{"kind":"operations","operations":[{"op":"annotate","target":"proof","value":"note"}]},
                "affected_claims":[],"dependencies":[],"risk":{"level":"low","factors":[],"technical_effect_possible":False},
                "confidence":1,"requested_validations":[],"prompt_version":"test"}
    def write_proposal(self, role):
        path = self.root / "workspaces" / f"{role}.json"; path.parent.mkdir(exist_ok=True)
        path.write_text(__import__("json").dumps(self.proposal(role)))
        return path, hashlib.sha256(path.read_bytes()).hexdigest()
    def test_sparse_tree_is_reentrant(self):
        first = self.cycle(); again = self.cycle()
        self.assertEqual(len(first["children"]), 5); self.assertEqual(len(again["children"]), 5); self.assertEqual(len(self.fake.calls), 5)
        event = next(item for item in first["events"] if item["type"] == "CHILD_ADMITTED")
        self.assertTrue({"child_id", "session_dir", "task_hash", "status"} <= set(event))
    def test_department_admits_only_planned_specialist(self):
        self.cycle(); state = asyncio.run(self.o.advance_department(self.run, "S20")); self.assertTrue("W21" in state["children"]); self.assertFalse("W22" in state["children"])
    def test_duplicate_and_bad_hash_receipts(self):
        self.cycle(); asyncio.run(self.o.advance_department(self.run,"S10")); out, digest = self.write_proposal("W11")
        state=asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="S10",path=out,sha256=digest)); duplicate=asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="S10",path=out,sha256=digest))
        self.assertEqual(len(state["receipts"]),len(duplicate["receipts"]))
        with self.assertRaises(ValueError): asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="S10",path=out,sha256="0"*64))
    def test_out_of_order_specialist_receipts_are_durable(self):
        self.cycle(); asyncio.run(self.o.advance_department(self.run, "S10")); asyncio.run(self.o.advance_department(self.run, "S20"))
        out20, digest20 = self.write_proposal("W21")
        asyncio.run(self.o.receipt(self.run, sender_role="W21", parent_role="S20", path=out20, sha256=digest20))
        out10, digest10 = self.write_proposal("W11")
        state = asyncio.run(self.o.receipt(self.run, sender_role="W11", parent_role="S10", path=out10, sha256=digest10))
        self.assertEqual({item["sender_role"] for item in state["receipts"].values()}, {"W11", "W21"})
    def test_grandchild_cannot_message_root(self):
        self.cycle(); asyncio.run(self.o.advance_department(self.run,"S10")); out, digest = self.write_proposal("W11")
        with self.assertRaises(ValueError): asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="M00",path=out,sha256=digest))
    def test_silent_failed_and_restart_are_durable(self):
        self.cycle(); fresh=Orchestrator(self.root,self.fake); state=asyncio.run(fresh.status(self.run)); self.assertEqual(state["children"]["S10"]["status"],"ADMITTED")
        state=asyncio.run(fresh.mark_failed(self.run, "S20", "simulated")); self.assertEqual(state["children"]["S20"]["status"], "FAILED")
        state=asyncio.run(fresh.stop(self.run)); self.assertTrue(state["stopped"]); self.assertEqual(len(self.fake.cancelled),5)
    def test_consolidates_only_department_packet_for_root(self):
        self.cycle(); asyncio.run(self.o.advance_department(self.run, "S10")); out, digest = self.write_proposal("W11")
        asyncio.run(self.o.receipt(self.run, sender_role="W11", parent_role="S10", path=out, sha256=digest))
        state = asyncio.run(self.o.consolidate_department(self.run, "S10"))
        self.assertTrue(any(item["sender_role"] == "S10" and item["parent_role"] == "M00" for item in state["receipts"].values()))
    def test_pause_resume_and_preflight(self):
        self.assertEqual(asyncio.run(self.o.preflight())["required_command"],"/rlm-max-depth 2")
        asyncio.run(self.o.pause(self.run)); self.assertTrue(asyncio.run(self.o.status(self.run))["paused"]); asyncio.run(self.o.resume(self.run)); self.assertFalse(asyncio.run(self.o.status(self.run))["paused"])
