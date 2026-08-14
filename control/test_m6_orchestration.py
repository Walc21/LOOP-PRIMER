import asyncio, hashlib, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))
from article_loop import FakeRLMAdapter, Orchestrator, OrchestrationError, ingest, run_cycle


class M6OrchestrationTests(unittest.TestCase):
    """The original eight scenarios, now against the real M3 baseline."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        for relative in ("input/inbox", "artifacts/original", "artifacts/extracted", "artifacts/rendered", "versions/champion", "workspaces", "state"):
            (self.root / relative).mkdir(parents=True, exist_ok=True)
        shutil.copytree(ROOT / "config", self.root / "config", dirs_exist_ok=True)
        shutil.copytree(ROOT / "prompts", self.root / "prompts")
        ps = self.root / "fixture.ps"; ps.write_text("%!PS\n/Courier findfont 18 scalefont setfont 72 700 moveto (Fixture x = 1 [1]) show showpage\n")
        self.pdf = self.root / "input/inbox/artigo.pdf"
        subprocess.run(["gs", "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", f"-sOutputFile={self.pdf}", str(ps)], check=True)
        ingest(self.root)
        self.fake = FakeRLMAdapter(); self.o = Orchestrator(self.root, self.fake)
        self.state = asyncio.run(self.o.bootstrap(self.pdf)); self.run = self.state["run_id"]
        roles = ["M00", *[f"S{i}0" for i in range(1, 6)], *[f"W{i}{j}" for i in range(1, 6) for j in range(1, 4)]]
        self.plan = {"cycle_id": 0, "paused": False, "checkpoint": None, "budget": {}, "roles": [{"role_id": role, "mode": "RUN"} for role in roles]}
    def tearDown(self): self.temp.cleanup()
    def cycle(self): return asyncio.run(self.o.run_cycle(run_id=self.run, plan=self.plan))
    def manager(self, department):
        child = asyncio.run(self.o.status(self.run))["children"][department]
        return self.fake.for_child(child["child_id"], actor_role=department)
    def proposal(self, role):
        return {"schema_version":"1.1.0","proposal_id":f"p-{role}","role_id":role,"cycle_id":0,
                "base_hash":self.state["base_hash"],"scope":["proof"],"evidence_locators":["page:1"],
                "patch_or_operations":{"kind":"operations","operations":[{"op":"annotate","target":"proof","value":"note"}]},
                "affected_claims":[],"dependencies":[],"risk":{"level":"low","factors":[],"technical_effect_possible":False},
                "confidence":1,"requested_validations":[],"prompt_version":"test"}
    def write_proposal(self, role):
        path = self.root / "workspaces" / self.run / "cycle-0000" / role / "receipt.json"
        path.write_text(json.dumps(self.proposal(role)), encoding="utf-8")
        return path, hashlib.sha256(path.read_bytes()).hexdigest()
    def admit_workers(self, department):
        return asyncio.run(self.o.advance_department(self.run, department, adapter=self.manager(department)))
    def test_sparse_tree_is_reentrant(self):
        first = self.cycle(); again = self.cycle()
        self.assertEqual(len(first["children"]), 5); self.assertEqual(len(again["children"]), 5); self.assertEqual(len(self.fake.calls), 5)
        self.assertEqual({c["depth"] for c in self.fake.calls}, {0})
    def test_department_admits_only_planned_specialist(self):
        self.cycle(); state = self.admit_workers("S20"); self.assertTrue({"W21", "W22", "W23"} <= set(state["children"]))
        self.assertTrue(all(c["parent_id"] == state["children"]["S20"]["child_id"] for c in self.fake.calls if c["actor_role"] == "S20"))
    def test_duplicate_and_bad_hash_receipts(self):
        self.cycle(); self.admit_workers("S10"); out, digest = self.write_proposal("W11")
        state=asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="S10",path=out,sha256=digest)); duplicate=asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="S10",path=out,sha256=digest))
        self.assertEqual(len(state["receipts"]),len(duplicate["receipts"]))
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="S10",path=out,sha256="0"*64))
    def test_out_of_order_specialist_receipts_are_durable(self):
        self.cycle(); self.admit_workers("S10"); self.admit_workers("S20")
        out20, digest20 = self.write_proposal("W21"); asyncio.run(self.o.receipt(self.run,sender_role="W21",parent_role="S20",path=out20,sha256=digest20))
        out10, digest10 = self.write_proposal("W11"); state = asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="S10",path=out10,sha256=digest10))
        self.assertEqual(set(state["receipts"]), {"W11", "W21"})
    def test_grandchild_cannot_message_root(self):
        self.cycle(); self.admit_workers("S10"); out, digest = self.write_proposal("W11")
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="M00",path=out,sha256=digest))
    def test_silent_failed_and_restart_are_durable(self):
        self.cycle(); fresh=Orchestrator(self.root,self.fake); state=asyncio.run(fresh.status(self.run)); self.assertEqual(state["children"]["S10"]["status"],"ADMITTED")
        state=asyncio.run(fresh.mark_failed(self.run, "S20", "simulated")); self.assertEqual(state["children"]["S20"]["status"], "FAILED")
        state=asyncio.run(fresh.stop(self.run)); self.assertTrue(state["stopped"])
    def test_consolidates_only_department_packet_for_root(self):
        self.cycle(); self.admit_workers("S10")
        for role in ("W11", "W12", "W13"):
            out, digest = self.write_proposal(role); asyncio.run(self.o.receipt(self.run, sender_role=role, parent_role="S10", path=out, sha256=digest))
        state = asyncio.run(self.o.consolidate_department(self.run, "S10", adapter=self.manager("S10")))
        self.assertEqual(state["receipts"]["S10"]["parent_role"], "M00")
    def test_pause_resume_and_preflight(self):
        self.assertEqual(asyncio.run(self.o.preflight())["adapter"], "fake")
        asyncio.run(self.o.pause(self.run)); self.assertTrue(asyncio.run(self.o.status(self.run))["paused"]); asyncio.run(self.o.resume(self.run)); self.assertFalse(asyncio.run(self.o.status(self.run))["paused"])

    def test_run_identity_and_source_ready_are_closed(self):
        for bad in ("../x", "/tmp/x", "ingest-x/../y"):
            with self.assertRaises(OrchestrationError): self.o._run(bad)
        other = Path(tempfile.mkdtemp())
        try:
            (other / "input/inbox").mkdir(parents=True); copy = other / "input/inbox/artigo.pdf"; copy.write_bytes(self.pdf.read_bytes())
            with self.assertRaises(OrchestrationError): asyncio.run(Orchestrator(other).bootstrap(copy))
        finally: shutil.rmtree(other)

    def test_bootstrap_rejects_changed_champion_and_uses_champion_hash(self):
        manifest = json.loads((self.root / "versions/champion/v0000/manifest.json").read_text())
        self.assertEqual(self.state["base_hash"], manifest["content_hash"])
        (self.root / "versions/champion/v0000/baseline.pdf").write_bytes(b"changed")
        with self.assertRaises(OrchestrationError): asyncio.run(Orchestrator(self.root, self.fake).bootstrap(self.pdf))

    def test_paused_freeze_and_dry_run_never_admit(self):
        frozen = {**self.plan, "roles":[{**entry, "mode":"FREEZE" if entry["role_id"] == "S10" else entry["mode"]} for entry in self.plan["roles"]]}
        asyncio.run(self.o.run_cycle(run_id=self.run, plan=frozen, dry_run=True)); self.assertEqual(self.fake.calls, [])
        paused = {**self.plan, "paused": True}
        asyncio.run(self.o.run_cycle(run_id=self.run, plan=paused)); self.assertEqual(self.fake.calls, [])

    def test_dry_run_then_live_and_next_cycle_have_distinct_identities(self):
        asyncio.run(self.o.run_cycle(run_id=self.run, plan=self.plan, dry_run=True)); self.assertEqual(self.fake.calls, [])
        self.cycle(); self.assertEqual(len(self.fake.calls), 5)
        next_plan = {**self.plan, "cycle_id": 1}
        asyncio.run(self.o.run_cycle(run_id=self.run, plan=next_plan)); self.assertEqual(len(self.fake.calls), 10)
        self.assertEqual(len({x["name"] for x in self.fake.calls}), 10)

    def test_actor_topology_depth_and_reconciliation(self):
        self.cycle(); s10 = asyncio.run(self.o.status(self.run))["children"]["S10"]
        with self.assertRaises(OrchestrationError): asyncio.run(self.o._admit(self.run, 0, "W11", self.fake))
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.advance_department(self.run, "S20", adapter=self.manager("S10")))
        self.admit_workers("S10")
        workers = [x for x in self.fake.calls if x["actor_role"] == "S10"]
        self.assertEqual({x["depth"] for x in workers}, {1}); self.assertTrue(all(x["parent_id"] == s10["child_id"] for x in workers))

    def test_receipt_parentage_identity_workspace_and_conflict(self):
        self.cycle(); self.admit_workers("S10"); out, digest = self.write_proposal("W11")
        for parent in ("S20", "M00"):
            with self.assertRaises(OrchestrationError): asyncio.run(self.o.receipt(self.run, sender_role="W11", parent_role=parent, path=out, sha256=digest))
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.receipt(self.run, sender_role="S10", parent_role="S20", path=out, sha256=digest))
        other = out.parent.parent / "W12" / "receipt.json"; other.write_bytes(out.read_bytes())
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.receipt(self.run, sender_role="W11", parent_role="S10", path=other, sha256=hashlib.sha256(other.read_bytes()).hexdigest()))
        asyncio.run(self.o.receipt(self.run, sender_role="W11", parent_role="S10", path=out, sha256=digest))
        conflicting = out.parent / "second.json"; proposal = self.proposal("W11"); proposal["proposal_id"] = "conflict"; conflicting.write_text(json.dumps(proposal))
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.receipt(self.run, sender_role="W11", parent_role="S10", path=conflicting, sha256=hashlib.sha256(conflicting.read_bytes()).hexdigest()))

    def test_receipt_cycle_base_and_symlink_are_rejected(self):
        self.cycle(); self.admit_workers("S10"); out, digest = self.write_proposal("W11")
        changed = self.proposal("W11"); changed["cycle_id"] = 9; out.write_text(json.dumps(changed)); digest = hashlib.sha256(out.read_bytes()).hexdigest()
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.receipt(self.run, sender_role="W11", parent_role="S10", path=out, sha256=digest))
        out.unlink(); out.symlink_to(self.pdf)
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.receipt(self.run, sender_role="W11", parent_role="S10", path=out, sha256="0" * 64))

    def test_task_prompt_and_journal_integrity_are_checked(self):
        self.cycle(); child = asyncio.run(self.o.status(self.run))["children"]["S10"]
        task = Path(child["workspace"]) / "task.json"; self.assertEqual(child["task_hash"], hashlib.sha256(task.read_bytes()).hexdigest())
        self.assertTrue((Path(child["workspace"]) / "prompt.txt").read_text())
        journal = self.root / "state/orchestration" / self.run / "journal.jsonl"; journal.write_bytes(journal.read_bytes() + b'{')
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.status(self.run))

    def test_terminal_states_and_cancel_are_durable(self):
        self.cycle(); child = asyncio.run(self.o.status(self.run))["children"]["S10"]
        asyncio.run(self.o.cancel(self.run, "S10")); self.assertIn(child["child_id"], self.fake.cancelled)
        events = self.o._events(self.run); self.assertEqual(events[-1]["event_type"], "CANCELLED")
        asyncio.run(self.o.pause(self.run))
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.mark_failed(self.run, "S20", "late"))
        asyncio.run(self.o.resume(self.run)); asyncio.run(self.o.stop(self.run))
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.resume(self.run))
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.advance_department(self.run, "S20", adapter=self.manager("S20")))

    def test_public_live_requires_explicit_real_adapter(self):
        self.cycle()
        with self.assertRaises(OrchestrationError): asyncio.run(run_cycle(root=self.root, cycle_id=0))
