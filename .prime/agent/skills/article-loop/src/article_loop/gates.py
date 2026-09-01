"""Deterministic, local, fail-closed M7 gates and canonical evidence."""
from __future__ import annotations

import json
import re
import shutil
import stat
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping

import yaml

from .blackboard import Blackboard
from .ingestion import _directory_hash
from .state_machine import State
from .store import DurableStore
from .synthesis import (
    IntegrityError, M7Pipeline, SynthesisError, _atomic, _contained,
    _inventory, _json, _m6_receipt, _regular, _sha, _validate_schema,
    _walk, tree_hash,
)

REQUIRED_GATES = (
    "contracts_state", "source_provenance", "latex_compile_safe", "render",
    "pdf_valid", "references_labels", "asset_inventory", "claim_dependencies",
    "math_critical_issues", "forbidden_metatext", "local_budget",
    "manifest_integrity", "correctness_math",
)
_HEX = re.compile(r"[a-f0-9]{64}\Z")


def _config(root: Path) -> dict[str, dict[str, Any]]:
    try:
        value = yaml.safe_load((root / "config/gates.yaml").read_text(encoding="utf-8"))
        items = value["m7_gates"]
    except (OSError, TypeError, KeyError, yaml.YAMLError) as exc:
        raise IntegrityError("M7 gate configuration is unavailable") from exc
    if not isinstance(items, list) or [x.get("id") for x in items if isinstance(x, dict)] != list(REQUIRED_GATES):
        raise IntegrityError("M7 gate configuration is missing, duplicated, reordered, or unknown")
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if (not isinstance(item, dict) or set(item) != {"id", "command", "verifier_version", "timeout_seconds"}
                or not isinstance(item["command"], str) or not item["command"]
                or not isinstance(item["verifier_version"], str) or not item["verifier_version"]
                or type(item["timeout_seconds"]) is not int or item["timeout_seconds"] < 1):
            raise IntegrityError("M7 gate configuration is malformed")
        result[item["id"]] = dict(item)
    return result


def _read_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        _regular(path)
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError, SynthesisError) as exc:
        raise IntegrityError(f"invalid canonical JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise IntegrityError("canonical JSON must be an object")
    return value, raw


def _manifest(root: Path, candidate: Path) -> dict[str, Any]:
    manifest, _ = _read_json(candidate / "manifest.json")
    try:
        _validate_schema(root, "candidate-manifest.schema.json", manifest)
    except SynthesisError as exc:
        raise IntegrityError("candidate manifest schema failed") from exc
    if (manifest.get("candidate_kind") != "challenger"
            or manifest.get("candidate_id") != candidate.name
            or manifest.get("content_hash") != tree_hash(candidate, exclude={"manifest.json"})
            or manifest.get("workspace_hash") != manifest.get("content_hash")
            or manifest.get("inventory") != _inventory(candidate, {"manifest.json"})):
        raise IntegrityError("candidate manifest/content relation failed")
    for _, _, info in _walk(candidate):
        if stat.S_IMODE(info.st_mode) & 0o222:
            raise IntegrityError("candidate publication is writable")
    if stat.S_IMODE(candidate.lstat().st_mode) & 0o222:
        raise IntegrityError("candidate publication root is writable")
    return manifest


def _synthesis(root: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    expected = f"state/synthesis/{manifest.get('synthesis_hash')}/synthesis.json"
    if manifest.get("merge_receipt_locator") != expected:
        raise IntegrityError("synthesis locator is not canonical")
    path = _contained(root, expected, True)
    synthesis, raw = _read_json(path)
    if _sha(raw) != manifest.get("synthesis_hash") or raw != _json(synthesis):
        raise IntegrityError("frozen synthesis bytes/hash failed")
    try:
        rebuilt = M7Pipeline(root)._validated_synthesis({"synthesis_hash": _sha(raw), "frozen_bytes": raw})
    except SynthesisError as exc:
        raise IntegrityError("frozen synthesis cannot be rebuilt") from exc
    if raw != rebuilt["frozen_bytes"]:
        raise IntegrityError("frozen synthesis rebuild differs")
    if any(synthesis.get(key) != manifest.get(key) for key in ("run_id", "cycle_id", "base_hash")):
        raise IntegrityError("synthesis/candidate identity differs")
    decision = synthesis.get("decision", {})
    if (decision.get("application_order") != manifest.get("proposal_ids")
            or decision.get("application_order") != manifest.get("source_proposal_ids")
            or decision.get("proposal_hashes") != manifest.get("proposal_hashes")
            or manifest.get("merge_receipt", {}).get("synthesis_hash") != manifest.get("synthesis_hash")
            or manifest.get("merge_receipt", {}).get("proposal_hashes") != decision.get("proposal_hashes")
            or manifest.get("merge_receipt", {}).get("proposal_receipts") != decision.get("proposal_receipts")
            or manifest.get("merge_receipt", {}).get("base_hash") != manifest.get("base_hash")):
        raise IntegrityError("candidate merge receipt differs from frozen decision")
    return synthesis


def _proposals(root: Path, manifest: Mapping[str, Any], synthesis: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    receipts = synthesis["decision"]["proposal_receipts"]
    for proposal_id in synthesis["decision"]["application_order"]:
        try:
            proposal, raw = _m6_receipt(root, manifest["run_id"], receipts[proposal_id], "agent-proposal.schema.json")
        except (KeyError, SynthesisError) as exc:
            raise IntegrityError("proposal receipt unavailable") from exc
        if (_sha(raw) != synthesis["decision"]["proposal_hashes"].get(proposal_id)
                or proposal.get("proposal_id") != proposal_id
                or proposal.get("cycle_id") != manifest.get("cycle_id")
                or proposal.get("base_hash") != manifest.get("base_hash")):
            raise IntegrityError("proposal receipt identity/hash differs")
        result[proposal_id] = proposal
    return result


def _source_provenance(root: Path, candidate: Path, manifest: Mapping[str, Any], synthesis: Mapping[str, Any]) -> list[str]:
    base = root / "versions/champion" / str(manifest.get("base_candidate_id"))
    base_manifest, base_raw = _read_json(base / "manifest.json")
    try:
        _validate_schema(root, "candidate-manifest.schema.json", base_manifest)
    except SynthesisError as exc:
        raise IntegrityError("base manifest schema failed") from exc
    if (base_manifest.get("candidate_id") != manifest.get("base_candidate_id")
            or base_manifest.get("content_hash") != manifest.get("base_hash")
            # M3's baseline manifest is bound with its file-only directory hash;
            # challengers use M7's stricter tree hash.  Verify each artifact with
            # the algorithm declared by the milestone that published it.
            or _directory_hash(base, exclude={"manifest.json"}) != manifest.get("base_hash")):
        raise IntegrityError("base champion identity/content differs")
    ingestion, _ = _read_json(base / "ingestion-manifest.json")
    baseline = base / "baseline.pdf"
    _regular(baseline)
    if _sha(baseline.read_bytes()) != ingestion.get("input_sha256"):
        raise IntegrityError("baseline PDF hash differs from ingestion provenance")
    identity = ingestion.get("source_identity")
    if (not isinstance(identity, dict) or identity.get("input_sha256") != ingestion.get("input_sha256")
            or identity.get("source_mode") != ingestion.get("source_mode")):
        raise IntegrityError("ingestion source identity differs")
    proposals = _proposals(root, manifest, synthesis)
    touched = {
        operation["target"]
        for proposal in proposals.values()
        for operation in proposal["patch_or_operations"]["operations"]
    }
    base_files = {r: p for r, p, s in _walk(base, {"manifest.json"}) if stat.S_ISREG(s.st_mode)}
    candidate_files = {r: p for r, p, s in _walk(candidate, {"manifest.json"}) if stat.S_ISREG(s.st_mode)}
    for rel, path in base_files.items():
        if rel not in touched:
            other = candidate_files.get(rel)
            if other is None or _sha(path.read_bytes()) != _sha(other.read_bytes()):
                raise IntegrityError(f"unchanged base artifact diverged: {rel}")
    for protected in ("baseline.pdf", "ingestion-manifest.json"):
        if protected in touched:
            raise IntegrityError("proposal attempts to alter ingestion provenance")
    return ["versions/champion/%s/manifest.json" % manifest["base_candidate_id"], "ingestion-manifest.json", "baseline.pdf"]


def _entrypoint(candidate: Path) -> Path:
    alternatives = (candidate / "article.tex", candidate / "paper.tex", candidate / "latex-source/paper.tex")
    present = [path for path in alternatives if path.exists()]
    if len(present) != 1:
        raise IntegrityError("exactly one validated LaTeX entrypoint is required")
    _regular(present[0])
    return present[0]


def _run(command: str, args: list[str], *, cwd: Path, timeout: int) -> tuple[bool, int, str, int]:
    executable = shutil.which(command)
    if executable is None:
        return False, 127, "required executable is unavailable", 0
    started = time.monotonic()
    try:
        done = subprocess.run([executable, *args], cwd=cwd, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, timeout=timeout, check=False)
        return done.returncode == 0, done.returncode, done.stdout[:4096], int((time.monotonic() - started) * 1000)
    except subprocess.TimeoutExpired:
        return False, 124, "local verifier timed out", int((time.monotonic() - started) * 1000)
    except OSError as exc:
        return False, 126, str(exc)[:4096], int((time.monotonic() - started) * 1000)


def _claims(root: Path, manifest: Mapping[str, Any], proposals: Mapping[str, Mapping[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    claims = Blackboard(root).claims(manifest["run_id"])
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(claim_id: str) -> None:
        if claim_id in done:
            return
        if claim_id in visiting or claim_id not in claims:
            raise IntegrityError("claim dependency is missing or cyclic")
        visiting.add(claim_id)
        claim = claims[claim_id]
        if claim.get("source_hash") != manifest.get("base_hash") or claim.get("last_validated_cycle", -1) < manifest.get("cycle_id", 0):
            raise IntegrityError("claim is stale relative to frozen decision")
        for dependency in claim.get("dependencies", []):
            visit(dependency)
        visiting.remove(claim_id)
        done.add(claim_id)

    affected = sorted({claim for proposal in proposals.values() for claim in proposal.get("affected_claims", [])})
    for claim_id in affected:
        visit(claim_id)
    return claims, affected


def _math_requests(proposals: Mapping[str, Mapping[str, Any]]) -> dict[tuple[str, str], Mapping[str, Any]]:
    requests: dict[tuple[str, str], Mapping[str, Any]] = {}
    for proposal_id, proposal in proposals.items():
        if "correctness_math" not in proposal.get("requested_validations", []):
            continue
        if proposal.get("role_id") != "W22" or not proposal.get("affected_claims"):
            raise IntegrityError("mathematical request is not a claim-bearing W22 request")
        for claim_id in proposal["affected_claims"]:
            requests[(proposal_id, claim_id)] = proposal
    if not requests:
        raise IntegrityError("no canonical mathematical verification request")
    return requests


def record_math_verification(candidate: str | Path, *, claim_id: str, proposal_id: str,
                             verifier_id: str, verifier_version: str, method: str,
                             summary: str) -> dict[str, Any]:
    """Persist a separate canonical approval; a request can never approve itself."""
    candidate = Path(candidate).resolve()
    root = candidate.parents[2]
    manifest = _manifest(root, candidate)
    synthesis = _synthesis(root, manifest)
    proposals = _proposals(root, manifest, synthesis)
    requests = _math_requests(proposals)
    if (proposal_id, claim_id) not in requests:
        raise SynthesisError("verification has no matching canonical request")
    receipt = synthesis["decision"]["proposal_receipts"][proposal_id]
    evidence_body = {
        "schema_version": "1.0.0", "run_id": manifest["run_id"], "cycle_id": manifest["cycle_id"],
        "base_hash": manifest["base_hash"], "candidate_id": manifest["candidate_id"],
        "candidate_content_hash": manifest["content_hash"], "claim_id": claim_id,
        "proposal_id": proposal_id, "request_receipt_sha256": receipt["sha256"],
        "method": method, "conclusion": "valid", "summary": summary,
    }
    _validate_schema(root, "math-evidence.schema.json", evidence_body)
    evidence_raw = _json(evidence_body)
    evidence_hash = _sha(evidence_raw)
    evidence_path = root / "state/math-evidence" / manifest["candidate_id"] / f"{evidence_hash}.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    if evidence_path.exists() and evidence_path.read_bytes() != evidence_raw:
        raise IntegrityError("mathematical evidence collision")
    if not evidence_path.exists():
        _atomic(evidence_path, evidence_raw)
    body = {
        "schema_version": "1.0.0", "run_id": manifest["run_id"], "cycle_id": manifest["cycle_id"],
        "base_hash": manifest["base_hash"], "candidate_id": manifest["candidate_id"],
        "candidate_content_hash": manifest["content_hash"], "claim_id": claim_id,
        "proposal_id": proposal_id, "request_receipt_locator": receipt["immutable_path"],
        "request_receipt_sha256": receipt["sha256"],
        "evidence_locator": evidence_path.relative_to(root).as_posix(), "evidence_hash": evidence_hash,
        "verdict": "approved", "verifier_id": verifier_id,
        "verifier_version": verifier_version, "issued_at": "1970-01-01T00:00:00Z",
    }
    digest = _sha(_json(body))
    body["verification_hash"] = digest
    body["verification_id"] = "mv-" + digest[:32]
    path = root / "state/math-verifications" / manifest["candidate_id"] / f"{digest}.json"
    body["verification_locator"] = path.relative_to(root).as_posix()
    _validate_schema(root, "math-verification.schema.json", body)
    raw = _json(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != raw:
        raise IntegrityError("mathematical verification collision")
    if not path.exists():
        _atomic(path, raw)
    return body


def _math_approvals(root: Path, manifest: Mapping[str, Any], synthesis: Mapping[str, Any], proposals: Mapping[str, Mapping[str, Any]]) -> list[str]:
    requests = _math_requests(proposals)
    directory = root / "state/math-verifications" / manifest["candidate_id"]
    if not directory.is_dir():
        raise IntegrityError("mathematical requests have no independent approvals")
    approved: set[tuple[str, str]] = set()
    locators: list[str] = []
    for path in sorted(directory.iterdir()):
        verification, raw = _read_json(path)
        try:
            _validate_schema(root, "math-verification.schema.json", verification)
        except SynthesisError as exc:
            raise IntegrityError("mathematical verification schema failed") from exc
        digest = verification.get("verification_hash")
        body = dict(verification)
        for field in ("verification_hash", "verification_id", "verification_locator"):
            body.pop(field, None)
        canonical = f"state/math-verifications/{manifest['candidate_id']}/{digest}.json"
        if (raw != _json(verification) or digest != _sha(_json(body)) or path.name != f"{digest}.json"
                or verification.get("verification_id") != "mv-" + str(digest)[:32]
                or verification.get("verification_locator") != canonical):
            raise IntegrityError("mathematical verification hash/locator failed")
        if (any(verification.get(key) != manifest.get(key) for key in ("run_id", "cycle_id", "base_hash", "candidate_id"))
                or verification.get("candidate_content_hash") != manifest.get("content_hash")):
            raise IntegrityError("mathematical verification identity differs")
        key = (verification["proposal_id"], verification["claim_id"])
        if key not in requests or verification.get("verdict") != "approved":
            raise IntegrityError("mathematical approval does not match a request")
        receipt = synthesis["decision"]["proposal_receipts"][key[0]]
        if (verification.get("request_receipt_locator") != receipt["immutable_path"]
                or verification.get("request_receipt_sha256") != receipt["sha256"]):
            raise IntegrityError("mathematical request receipt differs")
        evidence_path = _contained(root, verification["evidence_locator"], True)
        evidence, evidence_raw = _read_json(evidence_path)
        try:
            _validate_schema(root, "math-evidence.schema.json", evidence)
        except SynthesisError as exc:
            raise IntegrityError("mathematical evidence schema failed") from exc
        if (_sha(evidence_raw) != verification["evidence_hash"] or evidence_raw != _json(evidence)
                or evidence_path != root / "state/math-evidence" / manifest["candidate_id"] / f"{verification['evidence_hash']}.json"
                or any(evidence.get(k) != manifest.get(k) for k in ("run_id", "cycle_id", "base_hash", "candidate_id"))
                or evidence.get("candidate_content_hash") != manifest.get("content_hash")
                or evidence.get("proposal_id") != key[0] or evidence.get("claim_id") != key[1]
                or evidence.get("request_receipt_sha256") != receipt["sha256"]
                or evidence.get("conclusion") != "valid"):
            raise IntegrityError("mathematical evidence identity/hash/locator failed")
        if key in approved:
            raise IntegrityError("duplicate mathematical approval")
        approved.add(key)
        locators.extend([verification["verification_locator"], verification["evidence_locator"]])
    if approved != set(requests):
        raise IntegrityError("not every affected claim has an approval")
    return locators


def _critical_issues(root: Path, manifest: Mapping[str, Any], affected: list[str]) -> list[str]:
    evidence: list[str] = []
    for issue in Blackboard(root).read(manifest["run_id"], "issues"):
        if str(issue.get("severity", "")).upper() == "CRITICAL" and issue.get("status") != "resolved":
            raise IntegrityError("unresolved persisted CRITICAL issue")
        if issue.get("issue_type") == "math":
            try:
                _validate_schema(root, "math-issue.schema.json", issue)
            except SynthesisError as exc:
                raise IntegrityError("mathematical issue schema failed") from exc
            if (any(issue.get(k) != manifest.get(k) for k in ("run_id", "cycle_id", "base_hash", "candidate_id"))
                    or issue.get("claim_id") not in affected):
                raise IntegrityError("mathematical issue identity differs")
        evidence.append(f"state/blackboard/{manifest['run_id']}/issues.jsonl")
    return sorted(set(evidence))


def _all_tex(candidate: Path) -> list[Path]:
    return sorted(path for path in candidate.rglob("*.tex") if path.is_file())


def _candidate_built_binding(store: DurableStore, manifest: Mapping[str, Any],
                             error_type: type[Exception] = IntegrityError) -> None:
    snapshot = store.snapshot(str(manifest["run_id"]))
    events = store.read_events(str(manifest["run_id"]))
    expected_payload = {
        "candidate_id": manifest["candidate_id"],
        "candidate_hash": manifest["content_hash"],
    }
    if (snapshot.get("state") != State.CANDIDATE_BUILT.value
            or snapshot.get("cycle_id") != manifest.get("cycle_id")
            or not events
            or events[-1].get("state_to") != State.CANDIDATE_BUILT.value
            or events[-1].get("cycle_id") != manifest.get("cycle_id")
            or events[-1].get("payload") != expected_payload
            or events[-1].get("artifact_hashes") != [manifest["content_hash"]]):
        raise error_type("run is not bound to this candidate at CANDIDATE_BUILT")


def _check(gate: str, candidate: Path, root: Path, manifest: Mapping[str, Any],
           context: dict[str, Any], timeout: int) -> tuple[bool, str, str, int, list[str], int]:
    if gate == "contracts_state":
        _manifest(root, candidate)
        synthesis = _synthesis(root, manifest)
        store = DurableStore(root)
        _candidate_built_binding(store, manifest)
        context["synthesis"] = synthesis
        context["proposals"] = _proposals(root, manifest, synthesis)
        return True, "technical", "schemas, frozen decision, and CANDIDATE_BUILT verified", 0, ["manifest.json", manifest["merge_receipt_locator"]], 0
    if gate == "source_provenance":
        evidence = _source_provenance(root, candidate, manifest, context["synthesis"])
        return True, "technical", "source identity, baseline, and unchanged artifacts verified", 0, evidence, 0
    if gate in {"latex_compile_safe", "render", "pdf_valid"}:
        if gate == "latex_compile_safe":
            entry = _entrypoint(candidate)
            work = Path(tempfile.mkdtemp(prefix="m7-latex-"))
            ok, code, output, duration = _run(
                "pdflatex", ["-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error",
                             f"-output-directory={work}", entry.name],
                cwd=entry.parent, timeout=timeout,
            )
            pdf = work / f"{entry.stem}.pdf"
            if not ok or not pdf.is_file():
                shutil.rmtree(work, ignore_errors=True)
                return False, "technical", output or "LaTeX compilation failed", code, [], duration
            context["work"] = work
            context["pdf"] = pdf
            context["latex_output"] = output
            return True, "technical", output or "pdflatex completed", 0, [entry.relative_to(candidate).as_posix()], duration
        pdf = context.get("pdf")
        if not isinstance(pdf, Path) or not pdf.is_file():
            return False, "technical", "compiler did not produce a PDF", 1, [], 0
        if gate == "render":
            output = Path(context["work"]) / "render"
            output.mkdir(exist_ok=True)
            ok, code, text, duration = _run("pdftoppm", ["-png", "-f", "1", "-singlefile", str(pdf), str(output / "page")], cwd=candidate, timeout=timeout)
            return ok, "technical", text or ("first page rendered" if ok else "render failed"), code, ["manifest.json"] if ok else [], duration
        if pdf.stat().st_size == 0:
            return False, "technical", "compiler produced an empty PDF", 1, [], 0
        ok, code, output, duration = _run("pdfinfo", [str(pdf)], cwd=candidate, timeout=timeout)
        return ok, "technical", output or ("pdfinfo accepted output" if ok else "PDF invalid"), code, ["manifest.json"] if ok else [], duration
    if gate == "references_labels":
        text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in _all_tex(candidate))
        labels = re.findall(r"\\label\{([^}]+)\}", text)
        refs = re.findall(r"\\(?:ref|eqref|pageref)\{([^}]+)\}", text)
        cites = [key.strip() for group in re.findall(r"\\cite(?:\[[^]]*\])?\{([^}]+)\}", text) for key in group.split(",")]
        bibitems = set(re.findall(r"\\bibitem(?:\[[^]]*\])?\{([^}]+)\}", text))
        bibkeys = set()
        for bib in candidate.rglob("*.bib"):
            bibkeys.update(re.findall(r"@[A-Za-z]+\s*\{\s*([^,\s]+)", bib.read_text(encoding="utf-8", errors="replace")))
        log = str(context.get("latex_output", ""))
        bad_log = bool(re.search(r"undefined references|undefined citations|multiply defined", log, re.I))
        ok = len(labels) == len(set(labels)) and set(refs).issubset(labels) and set(cites).issubset(bibitems | bibkeys) and not bad_log
        return ok, "technical", "references, citations, and compiler log verified" if ok else "duplicate/unresolved reference or citation", 0 if ok else 1, ["manifest.json"], 0
    if gate == "asset_inventory":
        text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in _all_tex(candidate))
        equations = len(re.findall(r"\\begin\{(?:equation|align|gather|multline)\*?\}|\\\[", text))
        figures = len(re.findall(r"\\begin\{figure\*?\}", text))
        tables = len(re.findall(r"\\begin\{table\*?\}", text))
        graphics = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", text)
        for graphic in graphics:
            options = [candidate / graphic] + [candidate / f"{graphic}{suffix}" for suffix in (".pdf", ".png", ".jpg", ".jpeg", ".eps")]
            if not any(path.is_file() for path in options):
                raise IntegrityError("referenced graphic is absent")
        _manifest(root, candidate)
        return True, "technical", f"actual asset inventory: equations={equations}, figures={figures}, tables={tables}, graphics={len(graphics)}", 0, ["manifest.json"], 0
    if gate == "claim_dependencies":
        _, affected = _claims(root, manifest, context["proposals"])
        context["affected"] = affected
        return True, "technical", f"claim graph rebuilt for {len(affected)} affected claims", 0, [f"state/blackboard/{manifest['run_id']}/claims.jsonl"], 0
    if gate == "math_critical_issues":
        evidence = _critical_issues(root, manifest, context["affected"])
        return True, "scientific", "no unresolved persisted CRITICAL mathematical issue", 0, evidence, 0
    if gate == "forbidden_metatext":
        text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in _all_tex(candidate)).casefold()
        found = any(word in text for word in ("as an ai", "language model", "ignore previous instructions"))
        return not found, "technical", "no forbidden metatext" if not found else "forbidden metatext detected", 0 if not found else 1, ["manifest.json"], 0
    if gate == "local_budget":
        items = _inventory(candidate, {"manifest.json"})
        ok = len(items) <= 1000 and sum(item["size"] for item in items) <= 50 * 1024 * 1024
        return ok, "technical", "local size budget verified" if ok else "local size budget exceeded", 0 if ok else 1, ["manifest.json"], 0
    if gate == "manifest_integrity":
        _manifest(root, candidate)
        return True, "technical", "manifest, inventory, modes, and publication hash verified", 0, ["manifest.json"], 0
    if gate == "correctness_math":
        evidence = _math_approvals(root, manifest, context["synthesis"], context["proposals"])
        return True, "scientific", "independent claim-bound mathematical approvals verified", 0, evidence, 0
    raise IntegrityError("unknown local verifier")


def _report_body_hash(report: Mapping[str, Any]) -> str:
    body = dict(report)
    for field in ("report_hash", "report_id", "report_locator"):
        body.pop(field, None)
    return _sha(_json(body))


def verify_gate_report(root: str | Path, report_locator: str | Path, *,
                       store: DurableStore | None = None,
                       require_candidate_built: bool = False) -> dict[str, Any]:
    """Rebuild every operational relation before a report can change state."""
    if isinstance(report_locator, Mapping):
        raise SynthesisError("an arbitrary mapping is not canonical gate evidence")
    root = Path(root).resolve()
    locator = Path(report_locator).as_posix()
    path = _contained(root, locator, True)
    report, raw = _read_json(path)
    try:
        _validate_schema(root, "gate-report.schema.json", report)
    except SynthesisError as exc:
        raise SynthesisError("gate report schema failed") from exc
    if raw != _json(report):
        raise SynthesisError("gate report bytes are not canonical")
    gates = report.get("gates", [])
    if [gate.get("gate_id") for gate in gates] != list(REQUIRED_GATES):
        raise SynthesisError("gate identifiers are missing, duplicated, reordered, or unknown")
    config = _config(root)
    candidate = root / "versions/challengers" / str(report.get("candidate_id"))
    manifest = _manifest(root, candidate)
    current_hash = tree_hash(candidate)
    if (report.get("run_id") != manifest.get("run_id") or report.get("cycle_id") != manifest.get("cycle_id")
            or report.get("candidate_content_hash") != manifest.get("content_hash")
            or report.get("candidate_hash") != current_hash):
        raise SynthesisError("gate report/candidate identity or content differs")
    for gate in gates:
        expected = config[gate["gate_id"]]
        if any(gate.get(key) != expected[key] for key in ("command", "verifier_version", "timeout_seconds")):
            raise SynthesisError("gate operational configuration differs")
        if gate.get("input_hash") != current_hash or gate.get("input_hash_after") != current_hash:
            raise SynthesisError("gate input hashes do not match current candidate")
        if gate.get("passed") and (gate.get("exit_code") != 0 or gate.get("classification") == "inconclusive"):
            raise SynthesisError("a passed gate has invalid exit/classification semantics")
    correctness = gates[REQUIRED_GATES.index("correctness_math")]["passed"]
    if report.get("correctness_math_pass") is not correctness or report.get("overall_pass") is not all(gate["passed"] for gate in gates):
        raise SynthesisError("gate report aggregates differ from gate results")
    digest = _report_body_hash(report)
    canonical = f"state/gates/{manifest['candidate_id']}/{digest}.json"
    if (report.get("report_hash") != digest or report.get("report_id") != "g-" + digest[:32]
            or report.get("report_locator") != canonical or locator != canonical
            or path != root / canonical):
        raise SynthesisError("gate report hash/id/locator is not canonical")
    if require_candidate_built:
        active_store = store or DurableStore(root)
        _candidate_built_binding(active_store, manifest, SynthesisError)
    return report


def run_gates(candidate: str | Path, *, adapter: Any | None = None,
              required=REQUIRED_GATES) -> dict[str, Any]:
    """Execute the exact local set. Adapters may schedule, never decide."""
    candidate = Path(candidate).resolve()
    root = candidate.parents[2]
    if candidate.parent != root / "versions/challengers":
        raise IntegrityError("candidate is outside challenger publication tree")
    if tuple(required) != REQUIRED_GATES or len(set(required)) != len(required):
        raise IntegrityError("required M7 gate set differs")
    config = _config(root)
    manifest = _manifest(root, candidate)
    frozen = tree_hash(candidate)
    context: dict[str, Any] = {}
    gates: list[dict[str, Any]] = []
    try:
        for gate_id in REQUIRED_GATES:
            before = tree_hash(candidate)
            if before != frozen:
                raise IntegrityError("candidate mutated before gate")
            entry = config[gate_id]
            try:
                ok, classification, output, code, evidence, duration = _check(
                    gate_id, candidate, root, manifest, context, entry["timeout_seconds"])
            except IntegrityError as exc:
                ok, classification, output, code, evidence, duration = False, "technical", str(exc), 70, [], 0
            except Exception as exc:  # verifier failure is evidence, not an absent report
                ok, classification, output, code, evidence, duration = False, "technical", f"verifier exception: {type(exc).__name__}: {exc}", 70, [], 0
            after = tree_hash(candidate)
            if after != before:
                ok, classification, output, code, evidence = False, "technical", "candidate mutated during gate", 70, []
            gates.append({
                "gate_id": gate_id, "command": entry["command"],
                "verifier_version": entry["verifier_version"], "timeout_seconds": entry["timeout_seconds"],
                "input_hash": before, "input_hash_after": after, "exit_code": code,
                "duration_ms": duration, "output": str(output)[:4096], "passed": bool(ok),
                "classification": classification, "evidence_locators": evidence,
            })
    finally:
        work = context.get("work")
        if isinstance(work, Path):
            shutil.rmtree(work, ignore_errors=True)
    body = {
        "schema_version": "1.1.0", "run_id": manifest["run_id"], "cycle_id": manifest["cycle_id"],
        "candidate_id": manifest["candidate_id"], "candidate_content_hash": manifest["content_hash"],
        "candidate_hash": frozen, "generated_at": "1970-01-01T00:00:00Z", "gates": gates,
        "correctness_math_pass": gates[REQUIRED_GATES.index("correctness_math")]["passed"],
        "overall_pass": all(gate["passed"] for gate in gates),
    }
    digest = _sha(_json(body))
    body["report_hash"] = digest
    body["report_id"] = "g-" + digest[:32]
    path = root / "state/gates" / manifest["candidate_id"] / f"{digest}.json"
    body["report_locator"] = path.relative_to(root).as_posix()
    raw = _json(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != raw:
        raise IntegrityError("gate report collision")
    if not path.exists():
        _atomic(path, raw)
    return verify_gate_report(root, body["report_locator"])


def compare(left: Mapping[str, Any], right: Mapping[str, Any], *, cost_tiebreak=True):
    """Eight fixed finite dimensions; cost only breaks an otherwise equal vector."""
    def vector(value):
        values = value.get("pareto_vector")
        if (not isinstance(values, (list, tuple)) or len(values) != 8
                or any(type(item) not in (int, float) or not float("-inf") < float(item) < float("inf") for item in values)):
            raise ValueError("pareto_vector must contain eight finite numeric dimensions")
        critical = sum(1 for issue in value.get("issues", []) if isinstance(issue, Mapping) and str(issue.get("severity", "")).upper() == "CRITICAL")
        severity = sum({"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(str(issue.get("severity", "")).upper(), 4) for issue in value.get("issues", []) if isinstance(issue, Mapping))
        return tuple(map(float, values)), (int(bool(value.get("correctness_math_pass")) and not critical), -critical, -severity)
    a, a_priority = vector(left)
    b, b_priority = vector(right)
    if a_priority != b_priority:
        ge_priority = all(x >= y for x, y in zip(a_priority, b_priority))
        le_priority = all(x <= y for x, y in zip(a_priority, b_priority))
        relation = "left_dominates" if ge_priority else "right_dominates" if le_priority else "incomparable"
        return {"relation": relation, "left_vector": a, "right_vector": b, "promotion_authorized": False}
    ge = all(x >= y for x, y in zip(a, b))
    le = all(x <= y for x, y in zip(a, b))
    relation = "equal" if a == b else "left_dominates" if ge else "right_dominates" if le else "incomparable"
    if relation == "equal" and cost_tiebreak and left.get("cost") != right.get("cost"):
        relation = "left_dominates" if left.get("cost", float("inf")) < right.get("cost", float("inf")) else "right_dominates"
    return {"relation": relation, "left_vector": a, "right_vector": b, "promotion_authorized": False}
