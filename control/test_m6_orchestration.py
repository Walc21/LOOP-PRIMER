import asyncio, hashlib, json, shutil, subprocess, sys, tempfile, unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))
from article_loop import ChildHandle, FakeRLMAdapter, Orchestrator, OrchestrationError, PrimeRLMAdapter, ingest, run_cycle
from article_loop.store import DurableStore, StoreError
from article_loop.activation import ActivationPlanner, PlanningLimits
from article_loop.blackboard import Impact


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
        impact = Impact(claims=("claim:fixture",), sections=("section:proof",), equations=("equation:1",), references=("reference:1",), roles=tuple(f"W{i}{j}" for i in range(1, 6) for j in range(1, 4)), severity=10)
        self.plan = ActivationPlanner().plan(cycle_id=0, impact=impact).activation_map()
        self.persist_plan(self.plan)
    def tearDown(self): self.temp.cleanup()
    def persist_plan(self, plan):
        directory=self.root / "state/blackboard" / self.run; directory.mkdir(parents=True, exist_ok=True)
        encoded=json.dumps(plan, sort_keys=True, separators=(",", ":"))
        (directory / f"activation-c{plan['cycle_id']:04d}.json").write_text(encoded)
        if plan["cycle_id"] == 0: (directory / "activation_map.json").write_text(encoded)
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

    def test_forged_freeze_and_dry_run_never_admit(self):
        frozen = {**self.plan, "roles":[{**entry, "mode":"FREEZE" if entry["role_id"] == "S10" else entry["mode"]} for entry in self.plan["roles"]]}
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.run_cycle(run_id=self.run, plan=frozen, dry_run=True))
        asyncio.run(self.o.run_cycle(run_id=self.run, plan=self.plan, dry_run=True)); self.assertEqual(self.fake.calls, [])

    def test_dry_run_then_live_and_next_cycle_is_blocked_until_complete(self):
        asyncio.run(self.o.run_cycle(run_id=self.run, plan=self.plan, dry_run=True)); self.assertEqual(self.fake.calls, [])
        self.cycle(); self.assertEqual(len(self.fake.calls), 5)
        next_plan = ActivationPlanner().plan(cycle_id=1, impact=Impact((), (), (), (), ("W11",), 1)).activation_map(); self.persist_plan(next_plan)
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.run_cycle(run_id=self.run, plan=next_plan))

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
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.advance_department(self.run, "S20", adapter=self.fake))

    def test_public_live_requires_explicit_real_adapter(self):
        self.cycle()
        with self.assertRaises(OrchestrationError): asyncio.run(run_cycle(root=self.root, cycle_id=0))

    def test_prime_documented_handle_and_preflight_are_closed(self):
        class Handle:
            rlm_child_id="prime-1"; name="named"; session_dir="/session"; model="model"
        class API:
            async def __call__(self, prompt, *, name): return Handle()
            async def list_subagents(self): return [Handle()]
            async def delete_subagent(self, child): self.deleted=child
        class Message:
            async def send(self, message, *, receiver_role): pass
        api=API(); prime=PrimeRLMAdapter(api, Message(), actor_role="M00", actor_id="root", depth=0)
        self.assertEqual(asyncio.run(prime.preflight())["required_session_command"], "/rlm-max-depth 2")
        child=asyncio.run(prime.spawn("p",name="named")); self.assertEqual((child.child_id,child.name,child.session_dir,child.model),("prime-1","named","/session","model"))
        asyncio.run(prime.delete_subagent("prime-1")); self.assertEqual(api.deleted,"prime-1")
        class Bad: name="named"; session_dir="/session"; model="model"
        async def bad_list(): return [Bad()]
        api.list_subagents = bad_list
        with self.assertRaises(ValueError): asyncio.run(prime.list_subagents())

    def test_pause_resume_pause_stop_and_finalize_are_canonical(self):
        self.cycle(); asyncio.run(self.o.pause(self.run)); first=asyncio.run(self.o.status(self.run))["pause_id"]
        events=len(self.o._events(self.run)); asyncio.run(self.o.pause(self.run)); self.assertEqual(len(self.o._events(self.run)),events)
        asyncio.run(self.o.resume(self.run)); asyncio.run(self.o.pause(self.run)); state=asyncio.run(self.o.status(self.run))
        self.assertTrue(state["paused"]); self.assertNotEqual(first,state["pause_id"]); self.assertEqual(DurableStore(self.root).snapshot(self.run)["state"],"PAUSED")
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.finalize(self.run))
        asyncio.run(self.o.stop(self.run)); stopped=asyncio.run(self.o.status(self.run)); self.assertTrue(stopped["stopped"])
        self.assertTrue(all(child["status"] == "CANCELLED" for child in stopped["children"].values()))
        cancelled=[i for i,e in enumerate(self.o._events(self.run)) if e["event_type"] == "CANCELLED"]
        self.assertLess(max(cancelled), next(i for i,e in enumerate(self.o._events(self.run)) if e["event_type"] == "STOPPED"))

    def test_receipt_freeze_and_packet_publication_are_immutable(self):
        self.cycle(); self.admit_workers("S10")
        for role in ("W11","W12","W13"):
            path,digest=self.write_proposal(role); asyncio.run(self.o.receipt(self.run,sender_role=role,parent_role="S10",path=path,sha256=digest))
        path=self.root / "workspaces" / self.run / "cycle-0000" / "W11" / "receipt.json"; path.unlink()
        (self.root / "workspaces" / self.run / "cycle-0000" / "W12" / "receipt.json").write_text("{}")
        # Accepted receipts are now exclusively represented by their frozen
        # content-addressed bytes, so mutable workspaces may disappear.
        state=asyncio.run(self.o.consolidate_department(self.run,"S10",adapter=self.manager("S10")))
        packet=Path(state["receipts"]["S10"]["path"]); before=packet.read_bytes()
        asyncio.run(self.o.consolidate_department(self.run,"S10",adapter=self.manager("S10"))); self.assertEqual(before,packet.read_bytes())

    def test_s20_dependency_reviews_gate_technical_departments(self):
        self.cycle(); self.admit_workers("S30")
        for role in ("W31","W32","W33"):
            p=self.proposal(role); p["risk"]["technical_effect_possible"]=True
            path=self.root / "workspaces" / self.run / "cycle-0000" / role / "receipt.json"; path.write_text(json.dumps(p)); asyncio.run(self.o.receipt(self.run,sender_role=role,parent_role="S30",path=path,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        state=asyncio.run(self.o.consolidate_department(self.run,"S30",adapter=self.manager("S30")))
        packet=json.loads(Path(state["receipts"]["S30"]["path"]).read_text()); self.assertEqual(packet["status"],"blocked"); self.assertEqual(packet["dependency_reviews"],[])

    def test_real_m5_map_budget_freeze_and_views_are_checked(self):
        forged=json.loads(json.dumps(self.plan)); forged["budget"]["estimated_tokens"] += 1
        with self.assertRaises(OrchestrationError): self.o._plan(forged)
        frozen=json.loads(json.dumps(self.plan)); entry=next(x for x in frozen["roles"] if x["role_id"]=="W11"); entry["mode"]="FREEZE"; entry["estimated_tokens"]=1
        with self.assertRaises(OrchestrationError): self.o._plan(frozen)
        self.cycle(); self.admit_workers("S10"); child=asyncio.run(self.o.status(self.run))["children"]["W11"]
        view=json.loads((Path(child["workspace"])/"view.json").read_text()); self.assertTrue(view["excerpts"] and view["rubric"]["locator"].endswith("evaluation.yaml"))

    def test_intent_reconciliation_concurrency_and_closed_replay(self):
        self.cycle(); manager=self.manager("S10")
        async def concurrent_admission():
            return await asyncio.gather(self.o._admit(self.run,0,"W11",manager),self.o._admit(self.run,0,"W11",manager))
        asyncio.run(concurrent_admission())
        self.assertEqual(len([x for x in self.fake.calls if x["name"].endswith("-w11")]),1)
        with self.assertRaises(OrchestrationError): self.o._append(self.run,"UNKNOWN","unknown",{})
        with self.assertRaises(OrchestrationError): self.o._append(self.run,"HANDLE","bad",{"role_id":"W12"})

    def test_real_paused_m5_checkpoint_is_accepted_without_spawn(self):
        impact=Impact((),(),(),(),("W11",),1)
        paused=ActivationPlanner(limits=PlanningLimits(max_estimated_tokens=1)).plan(cycle_id=0,impact=impact).activation_map()
        self.assertTrue(paused["paused"]); self.assertIsInstance(paused["checkpoint"],dict)
        self.persist_plan(paused)
        state=asyncio.run(self.o.run_cycle(run_id=self.run,plan=paused))
        self.assertTrue(state["paused"]); self.assertEqual(state["children"],{}); self.assertEqual(self.fake.calls,[])

    def test_paused_checkpoint_is_closed_against_forgery(self):
        paused=ActivationPlanner(limits=PlanningLimits(max_estimated_tokens=1)).plan(cycle_id=0,impact=Impact((),(),(),(),("W11",),1)).activation_map()
        variants=[]
        missing=json.loads(json.dumps(paused)); del missing["checkpoint"]["reason"]; variants.append(missing)
        extra=json.loads(json.dumps(paused)); extra["checkpoint"]["extra"]=True; variants.append(extra)
        wrong=json.loads(json.dumps(paused)); wrong["checkpoint"]["estimated_tokens"]="1"; variants.append(wrong)
        mismatch=json.loads(json.dumps(paused)); mismatch["checkpoint"]["reason"]="department_limit_exhausted"; variants.append(mismatch)
        for forged in variants:
            with self.subTest(forged=forged["checkpoint"]):
                with self.assertRaises(OrchestrationError): self.o._plan(forged)

    def test_paused_checkpoint_recalculates_every_m5_constraint(self):
        normal=json.loads(json.dumps(self.plan)); self.assertFalse(normal["paused"])
        def forged(constraint):
            plan=json.loads(json.dumps(normal)); plan["paused"]=True
            plan["checkpoint"]={"reason":"budget_exhausted","constraints":[constraint],
                "mandatory_roles":[],"missing_mandatory":[],
                "active_roles":sum(role["mode"] != "FREEZE" for role in plan["roles"]),
                "estimated_tokens":plan["budget"]["estimated_tokens"],
                "wall_time_seconds":plan["budget"]["wall_time_seconds"],
                "limits":dict(plan["budget"]["limits"])}
            return plan
        for constraint in ("token_limit", "cycle_limit", "wall_time_limit", "department_limit", "children_limit", "role_limit"):
            with self.subTest(constraint=constraint):
                with self.assertRaises(OrchestrationError): self.o._plan(forged(constraint))

    def test_receipt_retry_uses_frozen_copy_before_workspace(self):
        self.cycle(); self.admit_workers("S10"); path,digest=self.write_proposal("W11")
        asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="S10",path=path,sha256=digest))
        receipt_events=lambda: len([event for event in self.o._events(self.run) if event["event_type"] == "RECEIPT"])
        accepted=asyncio.run(self.o.status(self.run))["receipts"]["W11"]; events=receipt_events()
        path.unlink()
        asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="S10",path=path,sha256=digest))
        path.write_text("{}")
        asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="S10",path=path,sha256=digest))
        self.assertEqual(receipt_events(),events)
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="S10",path=path.with_name("other.json"),sha256=digest))
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="S10",path=path,sha256="0"*64))
        Path(accepted["immutable_path"]).write_bytes(b"{}")
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="S10",path=path,sha256=digest))

    def test_department_packet_retry_restores_frozen_bytes_and_envelope(self):
        self.cycle(); self.admit_workers("S10")
        for role in ("W11", "W12", "W13"):
            path,digest=self.write_proposal(role); asyncio.run(self.o.receipt(self.run,sender_role=role,parent_role="S10",path=path,sha256=digest))
        manager=self.manager("S10"); state=asyncio.run(self.o.consolidate_department(self.run,"S10",adapter=manager))
        accepted=state["receipts"]["S10"]; packet=Path(accepted["path"]); frozen=Path(accepted["immutable_path"])
        original=packet.read_bytes(); created_at=json.loads(original)["created_at"]; events=len([e for e in self.o._events(self.run) if e["event_type"]=="RECEIPT"])
        packet.unlink(); asyncio.run(self.o.consolidate_department(self.run,"S10",adapter=manager))
        self.assertEqual(packet.read_bytes(),original)
        packet.write_bytes(b"{}"); asyncio.run(self.o.consolidate_department(self.run,"S10",adapter=manager))
        self.assertEqual(packet.read_bytes(),original); self.assertEqual(json.loads(packet.read_bytes())["created_at"],created_at)
        self.assertEqual(hashlib.sha256(packet.read_bytes()).hexdigest(),accepted["sha256"])
        self.assertEqual(len([e for e in self.o._events(self.run) if e["event_type"]=="RECEIPT"]),events)
        envelope=json.loads(manager.messages[-1]["message"]); self.assertEqual(envelope["sha256"],accepted["sha256"]); self.assertEqual(envelope["path"],accepted["path"])
        frozen.write_bytes(b"{}")
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.consolidate_department(self.run,"S10",adapter=manager))

    def test_receipt_is_read_once_and_frozen_copy_corruption_fails_closed(self):
        self.cycle(); self.admit_workers("S10"); path,digest=self.write_proposal("W11")
        original=Path.read_bytes; reads=[]
        def counted(item, *args, **kwargs):
            if item == path: reads.append(item)
            return original(item,*args,**kwargs)
        with mock.patch.object(Path,"read_bytes",counted):
            asyncio.run(self.o.receipt(self.run,sender_role="W11",parent_role="S10",path=path,sha256=digest))
        self.assertEqual(reads,[path])
        for role in ("W12","W13"):
            proposal,proposal_hash=self.write_proposal(role)
            asyncio.run(self.o.receipt(self.run,sender_role=role,parent_role="S10",path=proposal,sha256=proposal_hash))
        frozen=Path(asyncio.run(self.o.status(self.run))["receipts"]["W11"]["immutable_path"]); frozen.write_bytes(b"{}")
        with self.assertRaises(OrchestrationError): asyncio.run(self.o.consolidate_department(self.run,"S10"))

    def test_pause_failure_does_not_publish_local_pause_and_retry_is_idempotent(self):
        self.cycle()
        def failed_store(_root): return DurableStore(_root,fault=lambda _stage: (_ for _ in ()).throw(StoreError("injected")))
        with mock.patch("article_loop.orchestrator.DurableStore",side_effect=failed_store):
            with self.assertRaises(OrchestrationError): asyncio.run(self.o.pause(self.run))
        self.assertFalse(asyncio.run(self.o.status(self.run))["paused"]); self.assertEqual(DurableStore(self.root).snapshot(self.run)["state"],"DEPARTMENTS_RUNNING")
        asyncio.run(self.o.pause(self.run)); asyncio.run(self.o.pause(self.run))
        self.assertEqual(len([e for e in self.o._events(self.run) if e["event_type"]=="PAUSED"]),1)

    def test_resume_and_stop_failures_do_not_publish_local_terminal_events(self):
        self.cycle(); asyncio.run(self.o.pause(self.run))
        def failed_store(_root): return DurableStore(_root,fault=lambda _stage: (_ for _ in ()).throw(StoreError("injected")))
        with mock.patch("article_loop.orchestrator.DurableStore",side_effect=failed_store):
            with self.assertRaises(OrchestrationError): asyncio.run(self.o.resume(self.run))
        self.assertTrue(asyncio.run(self.o.status(self.run))["paused"]); self.assertEqual(DurableStore(self.root).snapshot(self.run)["state"],"PAUSED")
        asyncio.run(self.o.resume(self.run))
        with mock.patch("article_loop.orchestrator.DurableStore",side_effect=failed_store):
            with self.assertRaises(OrchestrationError): asyncio.run(self.o.stop(self.run))
        self.assertFalse(asyncio.run(self.o.status(self.run))["stopped"]); self.assertEqual(DurableStore(self.root).snapshot(self.run)["state"],"DEPARTMENTS_RUNNING")
        asyncio.run(self.o.stop(self.run)); asyncio.run(self.o.stop(self.run))
        events=self.o._events(self.run)
        self.assertEqual(len([e for e in events if e["event_type"]=="RESUMED"]),1)
        self.assertEqual(len([e for e in events if e["event_type"]=="STOPPED"]),1)

    def test_retry_after_canonical_commit_before_journal_reconciles_once(self):
        self.cycle(); original=self.o._append; raised=False
        def interrupted(run,event,key,payload):
            nonlocal raised
            if event == "PAUSED" and not raised:
                raised=True; raise RuntimeError("interrupted after canonical commit")
            return original(run,event,key,payload)
        with mock.patch.object(self.o,"_append",side_effect=interrupted):
            with self.assertRaises(RuntimeError): asyncio.run(self.o.pause(self.run))
        self.assertFalse(asyncio.run(self.o.status(self.run))["paused"]); self.assertEqual(DurableStore(self.root).snapshot(self.run)["state"],"PAUSED")
        asyncio.run(self.o.pause(self.run))
        self.assertEqual(len([e for e in self.o._events(self.run) if e["event_type"]=="PAUSED"]),1)

    def test_cycle_mirror_retry_after_canonical_commit_reconciles_once(self):
        original=self.o._append; raised=False
        def interrupted(run,event,key,payload):
            nonlocal raised
            if event == "PLAN" and not raised:
                raised=True; raise RuntimeError("interrupted after canonical cycle commit")
            return original(run,event,key,payload)
        with mock.patch.object(self.o,"_append",side_effect=interrupted):
            with self.assertRaises(RuntimeError): self.cycle()
        self.assertEqual(DurableStore(self.root).snapshot(self.run)["state"],"CYCLE_PLANNED")
        self.cycle()
        self.assertEqual(len([e for e in self.o._events(self.run) if e["event_type"]=="PLAN"]),1)
