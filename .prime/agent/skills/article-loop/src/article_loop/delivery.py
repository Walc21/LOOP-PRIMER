"""Read-only audit of a completed cycle, composed from canonical validators.

This verifies local evidence, not mathematical truth, model independence in a
live service, or authenticity against an attacker who can rewrite all evidence.
The project must be quiescent and retain its original M6 receipt locations.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat

from .finalization import TransactionalFinalizer
from .ingestion import _verify_artifacts, _verify_champion
from .policy import _contained, _read_canonical_json, _validate_schema
from .synthesis import M7Pipeline, tree_hash


class DeliveryError(RuntimeError):
    """Missing or inconsistent durable delivery evidence."""


def _require(condition, message):
    if not condition:
        raise DeliveryError(message)


def _hash(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def _bounded_tree(root, relative, *, max_files=100000, max_bytes=2**30):
    """Reject links/special files and oversized input before any validator reads."""
    path = _contained(root, relative, exists=True)
    count = total = 0
    for base, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            item = Path(base) / name
            info = item.lstat()
            _require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode), "unsafe delivery tree entry")
            count += 1
            total += info.st_size if stat.S_ISREG(info.st_mode) else 0
            _require(count <= max_files and total <= max_bytes, "delivery tree exceeds audit bounds")


def _one(events, state, cycle_id=None):
    matched = [event for event in events if event["state_to"] == state and (cycle_id is None or event["cycle_id"] == cycle_id)]
    _require(len(matched) == 1, f"expected one {state} transition")
    return matched[0]


def _verify_input(root, events, run_id):
    ingested = _one(events, "INGESTED")
    ready = _one(events, "SOURCE_READY")
    identity = ingested["payload"]["source_identity"]
    digest = identity["input_sha256"]
    _require(run_id == f"ingest-{digest}" and ready["payload"]["source_identity"] == identity, "input event identity differs")
    pdf = _contained(root, "input/inbox/artigo.pdf", exists=True)
    _require(_hash(pdf) == digest and pdf.stat().st_size == ingested["payload"]["input_size_bytes"], "original PDF was modified")
    original_locator = f"artifacts/original/{digest}/document.pdf"
    _require(ingested["payload"]["original_locator"] == original_locator, "original locator differs")
    zipped = _contained(root, "input/inbox/source.zip")
    _require(zipped.exists() == identity["source_zip_present"], "original source ZIP presence differs")
    if zipped.exists():
        _require(_hash(zipped) == identity["source_zip_sha256"] and zipped.stat().st_size == identity["source_zip_size_bytes"], "original source ZIP was modified")
    hashes = _verify_artifacts(root / f"artifacts/original/{digest}", root / f"artifacts/extracted/{digest}", root / f"artifacts/rendered/{digest}", digest)
    _require(ready["payload"]["artifacts"] == hashes and ready["artifact_hashes"] == sorted(hashes.values()) and ingested["artifact_hashes"] == [hashes["original"]], "ingestion event hashes differ")
    baseline = root / "versions/champion/v0000"
    _verify_champion(baseline, digest, hashes, identity)
    # M3 publishes indented JSON; M10's compact-byte contract does not apply.
    manifest = json.loads((baseline / "manifest.json").read_bytes())
    _validate_schema(root, "candidate-manifest.schema.json", manifest)
    _require(manifest["run_id"] == run_id and manifest["candidate_id"] == "v0000", "baseline identity differs")
    return {"sha256": digest, "size_bytes": pdf.stat().st_size, "unchanged": True, "original_locator": original_locator}, manifest


def _verify_routed(root, run_id, synthesis):
    """Join the real inference store, budget ledger and immutable M6 receipts."""
    from .budget import BudgetLedger
    from .execution import ExecutionPolicy
    from .inference import InferenceStore

    directory = root / "state/inference" / run_id
    ledger_path = root / "state/budgets" / f"{run_id}.jsonl"
    execution = ExecutionPolicy.from_project(root)
    expected_roles = {
        receipt["sender_role"]
        for receipt in synthesis["decision"]["proposal_receipts"].values()
        if execution.enabled and execution.departments.get(f"S{receipt['sender_role'][1]}0") == "routed"
    }
    if not directory.exists():
        _require(not expected_roles and not ledger_path.exists(), "missing required routed inference evidence")
        return {"calls": 0, "receipt_ids": [], "assurance": "no_routed_inference"}
    for relative in (f"state/inference/{run_id}/routes", f"state/inference/{run_id}/receipts", f"state/inference/{run_id}/outputs", "state/budgets", "logs"):
        _require(_contained(root, relative, exists=True).is_dir(), "missing routed evidence directory")
    _bounded_tree(root, "logs")
    ledger = BudgetLedger.from_project(root, run_id)
    budget_events = ledger.read_events()
    # status() emits threshold alerts. Audit uses the pure ledger projection.
    reservations = list(ledger._state_locked(budget_events)["reservations"].values())
    ledger.logger.read_events()
    _require(not any(ledger._open(item) for item in reservations), "unreconciled budget reservation")
    storage = InferenceStore(root, run_id)
    routes = {route["route_decision_hash"]: route for route in storage.routes()}
    receipts = storage.receipts()
    _require(bool(receipts), "routed evidence has no receipts")
    calls = {item["call_id"] for item in receipts}
    _require(len(calls) == len(receipts) == len(reservations), "budget/inference call coverage differs")
    proposal_receipts = synthesis["decision"]["proposal_receipts"]
    _require({item["role_id"] for item in receipts if item["cycle_id"] == synthesis["cycle_id"]} == expected_roles, "routed role coverage differs")
    for receipt in receipts:
        route = routes.get(receipt["route_decision_hash"])
        _require(route is not None and route["routing_policy_hash"] == ledger.routing_policy_hash, "inference route binding differs")
        for field in ("target_id", "provider", "model", "routing_policy_hash", "backend_type", "context_hash", "privacy_mode", "attempt", "independence_group"):
            _require(receipt[field] == route[field], "inference route/receipt identity differs")
        output = storage.output_for_call(receipt["call_id"])
        _require(output is not None and output["manifest"]["output_sha256"] == receipt["output_sha256"] and output["manifest"]["output_locator"] == receipt["output_locator"], "inference output binding differs")
        _require(all(output["manifest"].get(key) == value for key, value in receipt.items() if key != "receipt_hash"), "inference output/receipt metadata differs")
        document = output["document"]
        m6 = proposal_receipts.get(document.get("proposal_id"))
        _require(m6 is not None and m6["sha256"] == receipt["output_sha256"], "routed output is not the accepted M6 receipt")
        settled = [event for event in budget_events if event["event_type"] == "RECONCILED" and event["call_id"] == receipt["call_id"]]
        _require(len(settled) == 1 and settled[0]["payload"]["receipt_id"] == receipt["receipt_id"], "inference receipt not reconciled by budget")
        for field in ("input_tokens", "output_tokens", "cache_tokens", "cost_microunits", "currency"):
            _require(settled[0]["payload"].get(field) == receipt.get(field), "budget usage differs from inference receipt")
    return {"calls": len(receipts), "receipt_ids": sorted(item["receipt_id"] for item in receipts), "assurance": "reported_usage"}


def verify_delivery(root: str | Path, run_id: str, *, cycle_id: int = 0) -> dict:
    """Audit the latest completed cycle without invoking any model or publisher.

    Inputs are bounded to 100000 entries / 1 GiB per managed tree. Missing
    evidence fails; there is no repair mode and no implicit execution.
    """
    _require(isinstance(run_id, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", run_id) is not None, "invalid run_id")
    _require(type(cycle_id) is int and 0 <= cycle_id <= 100000, "invalid cycle_id")
    supplied = Path(root)
    _require(supplied.is_dir() and not supplied.is_symlink(), "missing or unsafe project root")
    root = supplied.resolve()
    try:
        # Constructors below only mkdir existing directories; never create an audit input.
        for relative in ("state/events", "state/snapshots", "state/checkpoints", "state/locks", "state/decisions", "state/synthesis", f"state/blackboard/{run_id}", "versions/champion", "versions/challengers", "versions/pareto", "versions/rejected", "workspaces"):
            _require(_contained(root, relative, exists=True).is_dir(), "missing delivery directory")
        for relative in ("state", "versions", "artifacts", "input/inbox", "config", "prompts"):
            _bounded_tree(root, relative)
        finalizer = TransactionalFinalizer(root)
        events = finalizer.store.read_events(run_id)
        _require(bool(events) and events[-1]["event_type"] == "FINALIZATION_APPLIED" and events[-1]["cycle_id"] == cycle_id, "delivery requires the latest applied finalization")
        input_identity, baseline = _verify_input(root, events, run_id)
        decision, decision_hash = finalizer._load_decision(run_id, cycle_id)
        record, manifest, candidate = finalizer._revalidate_evidence(decision, run_id, cycle_id)
        synthesis_path = _contained(root, manifest["merge_receipt_locator"], exists=True)
        pipe = M7Pipeline(root)
        synthesis = pipe._validated_synthesis({"synthesis_hash": manifest["synthesis_hash"], "frozen_bytes": synthesis_path.read_bytes()})
        pipe._existing(candidate, manifest["candidate_id"], synthesis, manifest["proposal_hashes"])
        decided = _one(events, "DECIDED", cycle_id)
        _require(decided["payload"].get("decision_hash") == decision_hash and decided["artifact_hashes"] == [decision_hash] and decided["payload"].get("decision_id") == decision["decision_id"], "DECIDED event binding differs")
        receipt = finalizer._read_receipt(run_id, cycle_id)
        _require(receipt is not None, "finalization receipt is missing")
        target = finalizer._target(decision["action"])
        expected = finalizer._receipt(decision, record, receipt["applied_at"], receipt["destination"], target)
        _require(receipt == expected, "finalization receipt differs from verified evidence")
        applied = events[-1]
        receipt_path = root / f"state/decisions/{run_id}/c{cycle_id:04d}/finalization-receipt.json"
        _require(applied["artifact_hashes"] == [_hash(receipt_path)] and applied["payload"] == {"decision_id": decision["decision_id"], "receipt_id": receipt["receipt_id"], "action": decision["action"], "destination": receipt["destination"]} and applied["state_to"] == target.value, "finalization event binding differs")
        journal = finalizer._read_journal(run_id, cycle_id)
        _require(journal is not None and all(journal.get(key) == value for key, value in {"run_id": run_id, "cycle_id": cycle_id, "decision_id": decision["decision_id"], "decision_hash": decision_hash, "action": decision["action"], "destination": receipt["destination"], "applied_at": receipt["applied_at"]}.items()), "finalization journal binding differs")
        _require(journal["phase"] in {"EVENT_COMMITTED", "CHECKPOINTED", "COMPLETE"}, "finalization journal has no completed effect")
        chain = ["SOURCE_READY", "CYCLE_PLANNED", "DEPARTMENTS_RUNNING", "SYNTHESIS_READY", "CANDIDATE_BUILT", "GATES_PASSED", "EVALUATED", "DIAGNOSED", "DECIDED", "COMMITTING", target.value]
        positions = [_one(events, state, None if state == "SOURCE_READY" else cycle_id)["sequence"] for state in chain]
        _require(positions == sorted(set(positions)), "system publication order differs")
        destination = receipt["destination"]
        artifact = None
        if decision["action"] == "PROMOTE":
            version = finalizer._next_champion_id(manifest["base_candidate_id"])
            _require(destination == f"versions/champion/{version}", "promotion destination differs")
            promoted = _contained(root, destination, exists=True)
            promoted_manifest = _read_canonical_json(promoted / "manifest.json", "promoted manifest")
            _validate_schema(root, "candidate-manifest.schema.json", promoted_manifest)
            expected_manifest = {
                "schema_version": "1.1.0", "candidate_id": version,
                "candidate_kind": "baseline", "run_id": run_id, "cycle_id": cycle_id,
                "base_candidate_id": None, "built_at": receipt["applied_at"],
                "workspace_hash": record.candidate_content_hash,
                "content_hash": record.candidate_content_hash,
                "source_proposal_ids": [], "merge_receipt_locator": None, "immutable": True,
            }
            _require(promoted_manifest == expected_manifest and tree_hash(promoted, exclude={"manifest.json"}) == record.candidate_content_hash, "promoted content or manifest differs")
            _require(not any(path.stat().st_mode & 0o222 for path in [promoted, *promoted.rglob("*")]), "promoted artifact became writable")
            pointer = _read_canonical_json(root / "versions/champion/current.json", "champion pointer")
            _require(pointer == {"candidate_id": version, "source_candidate_id": record.candidate_id, "decision_id": decision["decision_id"], "content_hash": record.candidate_content_hash}, "champion pointer differs")
            artifact = {"locator": destination, "content_hash": record.candidate_content_hash, "manifest_sha256": _hash(promoted / "manifest.json")}
        elif decision["action"] in {"ARCHIVE_PARETO", "REJECT"}:
            category = "pareto" if decision["action"] == "ARCHIVE_PARETO" else "rejected"
            _require(destination == f"versions/{category}/{record.candidate_id}", "disposition destination differs")
            path = _contained(root, destination + "/reference.json", exists=True)
            reference = _read_canonical_json(path, "disposition reference")
            expected_reference = {"candidate_id": record.candidate_id, "candidate_content_hash": record.candidate_content_hash, "decision_id": decision["decision_id"], "action": decision["action"], "applied_at": receipt["applied_at"], "reason_code": decision.get("reason_code"), "scores": dict(record.dimension_scores_challenger), "correctness_math_pass": bool(record.correctness_math_pass), "pareto_relation": decision.get("pareto_relation")}
            _require(reference == expected_reference, "disposition reference differs")
            artifact = {"locator": destination + "/reference.json", "sha256": _hash(path), "content_hash": record.candidate_content_hash}
        else:
            # An operational checkpoint is not a scientific deliverable.
            raise DeliveryError("delivery audit supports PROMOTE, ARCHIVE_PARETO and REJECT dispositions")
        routed = _verify_routed(root, run_id, synthesis)
        _require(finalizer.store.read_events(run_id) == events, "event log changed during delivery audit")
        return {
            "schema_version": "1.0.0", "milestone": "M13", "status": "pass",
            "run_id": run_id, "cycle_id": cycle_id,
            "original_pdf": input_identity,
            "baseline": {
                "candidate_id": baseline["candidate_id"],
                "content_hash": baseline["content_hash"],
            },
            "candidate": {
                "candidate_id": manifest["candidate_id"],
                "content_hash": manifest["content_hash"],
                "manifest_sha256": _hash(candidate / "manifest.json"),
            },
            "proposal_ids": synthesis["decision"]["application_order"],
            "department_packet_hashes": synthesis["packet_hashes"],
            "synthesis_hash": manifest["synthesis_hash"],
            "gate_report_id": record.gate_report["report_id"],
            "gate_report_hash": record.gate_report_hash,
            "comparison_id": record.evaluation_report["comparison_id"],
            "verdict_ids": record.evaluation_report["verdict_ids"],
            "meta_verdict_id": record.meta_verdict["meta_verdict_id"],
            "evaluation_report_hash": record.evaluation_report_hash,
            "diagnosis_id": decision["diagnosis_id"],
            "decision_id": decision["decision_id"],
            "decision_sha256": decision_hash,
            "receipt_id": receipt["receipt_id"],
            "receipt_sha256": _hash(receipt_path),
            "event_tip_sha256": events[-1]["event_hash"],
            "action": decision["action"], "state": target.value,
            "artifact": artifact, "routed_inference": routed, "system_path": chain,
            "reproducibility": (
                "semantic bindings and exact-byte replay; "
                "fresh-run timestamps and tool metadata may vary"
            ),
        }
    except DeliveryError:
        raise
    except Exception as exc:
        raise DeliveryError(f"delivery evidence failed verification: {type(exc).__name__}: {exc}") from exc
