"""Synthetic system fixture. Only external execution/judgment is simulated."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".prime/agent/skills/article-loop/src"))

from article_loop import FakeRLMAdapter, Orchestrator, ingest
from article_loop.activation import ActivationPlanner
from article_loop.blackboard import Blackboard, Impact
from article_loop.evaluation import FakeJurorAdapter, FakeMetaReviewerAdapter, evaluate_candidate
from article_loop.gates import record_math_verification, run_gates
from article_loop.diagnosis import diagnose_cycle
from article_loop.policy import decide
from article_loop.finalization import TransactionalFinalizer
from article_loop.store import DurableStore
from article_loop.synthesis import M7Pipeline


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def synthetic_pdf():
    """A fixed, valid one-page PDF; no clock, user input, or generator dependency."""
    stream = b"BT /F1 12 Tf 72 720 Td (Synthetic lemma: if x = 1, then x + x = 2. Proof: substitute 1.) Tj ET\n"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"endstream",
    ]
    data = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data += f"{number} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(data)
    data += b"xref\n0 6\n0000000000 65535 f \n"
    data += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    return data + f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()


BASE_TEX = "\\documentclass{article}\n\\begin{document}\nIf $x=1$, then $x+x=2$. Proof: substitute.\\label{lemma}\n\\end{document}\n"
BETTER_TEX = BASE_TEX.replace("Proof: substitute.", "Proof: substituting $x=1$ gives $x+x=1+1=2$.")
DEPARTMENTS = ("S10", "S20", "S30", "S40", "S50")


def remove_fixture(root):
    """Restore write permission only inside a disposable fixture before cleanup."""
    for base, dirs, files in os.walk(root, topdown=False, followlinks=False):
        for name in files + dirs:
            path = Path(base) / name
            if not path.is_symlink():
                path.chmod(0o700 if path.is_dir() else 0o600)
    Path(root).chmod(0o700)
    shutil.rmtree(root)


class RecordingJuror(FakeJurorAdapter):
    def __init__(self, *, score_override=None, **kwargs):
        super().__init__(**kwargs)
        self.presentations = []
        self.score_override = score_override or {}

    def evaluate(self, presentation):
        self.presentations.append(json.loads(json.dumps(presentation)))
        verdict = super().evaluate(presentation)
        verdict["dimension_scores"][1].update(self.score_override)
        return verdict


class SyntheticCycle:
    """Compose the public stages; never assign a state snapshot or gate result."""

    def __init__(self, root, *, routed=False, inference_policy=None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=False)
        for relative in ("input/inbox", "artifacts/original", "artifacts/extracted", "artifacts/rendered", "versions/champion", "workspaces", "state", "reports"):
            (self.root / relative).mkdir(parents=True, exist_ok=True)
        shutil.copytree(ROOT / "config", self.root / "config")
        shutil.copytree(ROOT / "prompts", self.root / "prompts")
        if routed:
            from dataclasses import asdict
            import yaml
            from article_loop.budget import BudgetLimits
            path = self.root / "config/budgets.yaml"
            config = yaml.safe_load(path.read_text())
            config["inference"] = inference_policy if inference_policy is not None else fake_policy()
            config["execution"].update(enabled=True, departments={d: ("routed" if d == "S40" else "prime") for d in DEPARTMENTS})
            config["budget"]["limits"] = asdict(BudgetLimits(total_tokens=1000000, max_calls=20))
            path.write_text(yaml.safe_dump(config), encoding="utf-8")
        self.pdf = self.root / "input/inbox/artigo.pdf"
        self.pdf.write_bytes(synthetic_pdf())
        self.pre_hash, self.pre_size, self.pre_mode = digest(self.pdf), self.pdf.stat().st_size, self.pdf.stat().st_mode
        with zipfile.ZipFile(self.root / "input/inbox/source.zip", "w") as archive:
            archive.writestr(zipfile.ZipInfo("paper.tex", (2026, 1, 1, 0, 0, 0)), BASE_TEX)
        self.ingested = ingest(self.root)
        self.run_id = self.ingested["run_id"]
        self.fake = FakeRLMAdapter()
        self.routed = routed
        adapter = self.fake
        if routed:
            from article_loop.execution import DualExecutionAdapter, ExecutionPolicy
            self.execution = ExecutionPolicy.from_project(self.root)
            adapter = DualExecutionAdapter(self.root, self.run_id, self.execution, prime_adapter=self.fake)
        self.adapter = adapter
        self.orchestrator = Orchestrator(self.root, adapter)
        self.initial = asyncio.run(self.orchestrator.bootstrap(self.pdf))
        self.store = DurableStore(self.root)
        self.base_hash = self.initial["base_hash"]
        claim = Blackboard(self.root).append(self.run_id, "claims", {
            "text": "If x=1, then x+x=2", "type": "theorem", "location": {"page": 1, "section": "proof"},
            "dependencies": [], "evidence": ["page:1"], "status": "active", "severity": 10,
            "source_hash": self.base_hash, "last_validated_cycle": 0,
        })
        self.claim_id = claim["claim_id"]
        impact = Impact((self.claim_id,), ("section:proof",), ("equation:1",), ("reference:1",), tuple(f"W{i}{j}" for i in range(1, 6) for j in range(1, 4)), 10)
        self.plan = ActivationPlanner().plan(cycle_id=0, impact=impact).activation_map()
        board = self.root / "state/blackboard" / self.run_id
        for filename in ("activation-c0000.json", "activation_map.json"):
            (board / filename).write_bytes(canonical(self.plan))
        self.pipe = M7Pipeline(self.root)

    def proposal(self, role):
        operation = {"op": "add", "target": f"evidence/{role.lower()}.txt", "value": "Synthetic lemma checked: 1+1=2.\n"}
        if role == "W41":
            operation = {"op": "replace", "target": "latex-source/paper.tex", "value": BETTER_TEX}
        return {
            "schema_version": "1.1.0", "proposal_id": f"p-{role}", "role_id": role, "cycle_id": 0,
            "base_hash": self.base_hash, "scope": ["proof"], "evidence_locators": ["page:1"],
            "patch_or_operations": {"kind": "operations", "operations": [operation]},
            "affected_claims": [self.claim_id] if role == "W22" else [], "dependencies": [],
            "risk": {"level": "low", "factors": [], "technical_effect_possible": False}, "confidence": 1,
            "requested_validations": ["correctness_math"] if role == "W22" else [], "prompt_version": "m13-fixture",
        }

    def manager(self, department):
        child = asyncio.run(self.orchestrator.status(self.run_id))["children"][department]
        return self.adapter.department_adapter(child) if self.routed and department == "S40" else self.fake.for_child(child["child_id"], actor_role=department)

    def workers(self):
        asyncio.run(self.orchestrator.run_cycle(
            run_id=self.run_id, plan=self.plan, allow_test_doubles=True,
        ))
        for department in DEPARTMENTS:
            if self.routed and department == "S40":
                continue
            manager = self.manager(department)
            asyncio.run(self.orchestrator.advance_department(self.run_id, department, adapter=manager))
            for suffix in (1, 2, 3):
                role = f"W{department[1]}{suffix}"
                workspace = self.root / "workspaces" / self.run_id / "cycle-0000" / role
                proposal = self.proposal(role)
                # The fixture owns external output, but receives real M4 identity.
                task = json.loads((workspace / "task.json").read_bytes())
                proposal["prompt_version"] = task["prompt_version"]
                path = workspace / "receipt.json"
                path.write_bytes(canonical(proposal))
                asyncio.run(self.orchestrator.receipt(self.run_id, sender_role=role, parent_role=department, path=path, sha256=digest(path)))
            asyncio.run(self.orchestrator.consolidate_department(self.run_id, department, adapter=manager))
        if self.routed:
            self.routed_workers()
        self.m6 = asyncio.run(self.orchestrator.status(self.run_id))
        return self.m6

    def routed_workers(self):
        from article_loop.budget import BudgetLedger, BudgetLimits
        from article_loop.execution import DualExecutionController
        from article_loop.inference import InferenceRuntime, ModelRegistry
        self.registry = ModelRegistry.from_project(self.root)
        self.ledger = BudgetLedger.from_project(self.root, self.run_id)
        self.backend = PayloadBackend(self)
        self.runtime = InferenceRuntime(self.root, self.ledger, self.registry, {"fake": self.backend})
        self.controller = DualExecutionController(self.root, self.execution, self.registry)
        return asyncio.run(self.controller.execute_routed_department(self.orchestrator, self.run_id, "S40", self.manager("S40"), self.runtime, allow_test_doubles=True))

    def candidate(self, *, approve_math=True):
        self.workers()
        self.synthesis = self.pipe.synthesize(self.m6["receipts"], run_id=self.run_id)
        self.pipe.record_synthesis(self.store, self.synthesis)
        self.manifest = self.pipe.build(self.synthesis, self.root / "versions/champion/v0000")
        self.pipe.record_candidate(self.store, self.manifest)
        self.candidate_dir = self.root / "versions/challengers" / self.manifest["candidate_id"]
        if approve_math:
            # A known synthetic identity, not evidence for arbitrary mathematics.
            if 1 + 1 != 2:
                raise RuntimeError("synthetic arithmetic verifier failed")
            record_math_verification(self.candidate_dir, claim_id=self.claim_id, proposal_id="p-W22", verifier_id="m13-synthetic-arithmetic", verifier_version="1.0.0", method="manual-proof-check", summary="For the synthetic fixture only: substitution x=1 gives 1+1=2.")
        return self.manifest

    def gates(self):
        self.gate_report = self.pipe.execute_and_record_gates(self.store, self.candidate_dir)
        return self.gate_report

    def evaluate(self, *, math_pass=True, positional_bias=None, meta=None, scores=(3, 5), winner="B", score_override=None):
        self.jurors = {name: RecordingJuror(juror_id=name, specialty=specialty, model_family=f"synthetic-judge-{index}", preferred_winner=winner, math_pass=(True, math_pass), positional_bias=positional_bias, base_scores=scores, score_override=score_override) for index, (name, specialty) in enumerate((("juror-math", "correctness_math"), ("juror-contrib", "scientific_contribution"), ("juror-clarity", "clarity")))}
        self.evaluation = evaluate_candidate(self.root, self.run_id, cycle_id=0, candidate_id=self.manifest["candidate_id"], gate_report_locator=self.gate_report["report_locator"], juror_adapters=self.jurors, meta_adapter=meta or FakeMetaReviewerAdapter(), allow_test_doubles=True)
        return self.evaluation

    def diagnose(self):
        self.diagnosis = diagnose_cycle(self.root, self.run_id, cycle_id=0, candidate_id=self.manifest["candidate_id"], window_size=1)
        return self.diagnosis

    def decide(self):
        self.decision = decide(self.root, self.run_id, cycle_id=0)
        return self.decision

    def finalize(self, **kwargs):
        self.receipt = TransactionalFinalizer(self.root, **kwargs).finalize(self.run_id, cycle_id=0)
        return self.receipt

    def run(self):
        self.candidate()
        self.gates()
        self.evaluate()
        self.diagnose()
        self.decide()
        return self.finalize()


def fake_policy():
    targets = {}
    for name, model in (("producer", "synthetic-producer"), ("judge", "synthetic-judge")):
        targets[name] = {"target_id": name, "provider": "synthetic", "model": model, "backend_type": "fake", "enabled": True, "local": True, "paid": False, "tier": "mid", "capabilities": ["language", "structured_output", "math_high_assurance"], "context_limit": 1000000, "max_output_tokens": 1000, "independence_group": name, "endpoint": None, "api_key_env": None, "timeout_seconds": 1, "fallback_target": None, "pricing": None}
    return {"schema_version": "1.0.0", "enabled": True, "allow_local": True, "allow_remote": False, "allow_paid": False, "routing_mode": "deterministic", "targets": targets, "role_routes": {role: {"targets": ["producer", "judge"], "required_capabilities": ["language", "structured_output"]} for role in ("W41", "W42", "W43")}, "escalation": {"enabled": False, "max_route_attempts": 1}, "independence": {"jury_must_differ_from_producer_group": True, "mode": "model"}}


class PayloadBackend:
    is_test_double = True

    def __init__(self, fixture):
        self.fixture = fixture
        self.calls = []

    def preflight(self, target):
        return {"ready": True, "test_double": True, "network": False}

    def complete(self, request, target):
        from article_loop.inference import InferenceResult
        self.calls.append(request)
        proposal = self.fixture.proposal(request.role_id)
        for field in ("schema_version", "proposal_id", "role_id", "cycle_id", "base_hash", "prompt_version"):
            proposal.pop(field)
        return InferenceResult(canonical(proposal).decode(), 10, 5, 0, True, wall_time_seconds=0, finish_reason="stop")
