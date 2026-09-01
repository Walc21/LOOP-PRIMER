"""Canonical, provenance-bound and crash-recoverable prompt refocus for M9."""
from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Generator, Mapping, Sequence

import yaml

from .diagnosis import DiagnosisError, verify_published_diagnosis
from .evaluation import EvaluationError, _validate_schema
from .prompts import OVERLAY_ROLE_IDS, PromptIntegrityError, PromptRegistry
from .store import DurableStore
from .synthesis import _contained, _fsync, _fsync_tree_dirs, _json, _regular, _sha, _walk

SCHEMA_VERSION = "1.1.0"
REFOCUS_PLAN_SCHEMA = "refocus-plan.schema.json"

ALLOWED_REFOCUS_CLASSIFICATIONS = frozenset({
    "LOCAL_PLATEAU",
    "GLOBAL_PLATEAU",
    "OSCILLATING",
})

FORBIDDEN_REFOCUS_CLASSIFICATIONS = frozenset({
    "REGRESSING",
    "INCONCLUSIVE",
    "TECHNICAL_FAILURE",
    "EVOLVING",
})

_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
_OVERLAY_FIELDS = {
    "parent_version",
    "diagnostic",
    "author",
    "evidence",
    "scope",
    "hash",
    "rollback",
    "instructions",
}


class RefocusError(RuntimeError):
    """Raised when provenance, publication, or overlay invariants fail."""


def _read_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        _regular(path)
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise RefocusError(f"cannot read canonical JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise RefocusError(f"canonical JSON must be an object: {path.name}")
    return value, raw


def _write_synced_file(path: Path, data: bytes) -> None:
    with path.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _harden_read_only(tree: Path) -> None:
    for _, path, sinfo in _walk(tree):
        if stat.S_ISDIR(sinfo.st_mode):
            os.chmod(path, 0o555)
        elif stat.S_ISREG(sinfo.st_mode):
            os.chmod(path, 0o444)
    os.chmod(tree, 0o555)


def _cleanup_staging(staging_path: Path) -> None:
    if not staging_path.exists():
        return
    for root_dir, dirs, files in os.walk(staging_path, topdown=False):
        for name in files:
            try:
                os.chmod(Path(root_dir) / name, 0o600)
            except OSError:
                pass
        for name in dirs:
            try:
                os.chmod(Path(root_dir) / name, 0o700)
            except OSError:
                pass
    try:
        os.chmod(staging_path, 0o700)
    except OSError:
        pass
    shutil.rmtree(staging_path)


def _managed_directory(root: Path, relative: str, *, create: bool) -> Path:
    """Return a canonical real output directory without traversing symlinks."""
    try:
        path = _contained(root, relative)
        if path.exists() or path.is_symlink():
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                raise RefocusError("managed refocus directory is not a real directory")
        elif create:
            path.mkdir(parents=True)
        if path.exists() and path.resolve().relative_to(root) != Path(relative):
            raise RefocusError("managed refocus directory is not canonical")
        return path
    except RefocusError:
        raise
    except Exception as exc:
        raise RefocusError("managed refocus directory is unsafe") from exc


@contextmanager
def _locked_registry(prompts_dir: Path) -> Generator[None, None, None]:
    if prompts_dir.is_symlink() or not prompts_dir.is_dir():
        raise RefocusError("prompts directory is not a safe managed directory")
    lock_path = prompts_dir / ".registry.lock"
    if lock_path.is_symlink():
        raise RefocusError("prompt registry lock may not be a symlink")
    flags = os.O_RDWR | os.O_CREAT | os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except OSError as exc:
        raise RefocusError("prompt registry lock cannot be opened safely") from exc
    info = os.fstat(descriptor)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        os.close(descriptor)
        raise RefocusError("prompt registry lock must be a unique regular file")
    with os.fdopen(descriptor, "a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _safe_overlay_directory(prompts_dir: Path, role_id: str, *, create: bool) -> Path:
    overlays_root = prompts_dir / "overlays"
    if overlays_root.is_symlink() or not overlays_root.is_dir():
        raise RefocusError("prompt overlays root is not a safe managed directory")
    if overlays_root.resolve().parent != prompts_dir.resolve():
        raise RefocusError("prompt overlays root escapes prompts directory")
    role_dir = overlays_root / role_id
    if role_dir.exists() or role_dir.is_symlink():
        if role_dir.is_symlink() or not role_dir.is_dir() or role_dir.resolve().parent != overlays_root.resolve():
            raise RefocusError("overlay role directory is not a safe managed directory")
    elif create:
        role_dir.mkdir()
        _fsync(overlays_root)
    return role_dir


def _compute_overlay_hash(document: Mapping[str, Any]) -> str:
    body = {key: value for key, value in document.items() if key != "hash"}
    return hashlib.sha256(_json(body)).hexdigest()


def _validate_version(version: Any, *, field: str = "overlay version") -> str:
    if not isinstance(version, str) or not _VERSION.fullmatch(version) or version in {".", ".."}:
        raise RefocusError(f"{field} is not a safe canonical identifier")
    return version


def _normalize_overlay_document(document: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(document, Mapping) or set(document) != _OVERLAY_FIELDS:
        raise RefocusError("overlay document has invalid fields")
    normalized = copy.deepcopy(dict(document))
    for field in ("diagnostic", "author", "instructions"):
        if not isinstance(normalized[field], str) or not normalized[field].strip():
            raise RefocusError(f"overlay {field} must be a non-empty string")
    for field in ("evidence", "scope"):
        values = normalized[field]
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not value.strip() for value in values)
            or len(values) != len(set(values))
        ):
            raise RefocusError(f"overlay {field} must contain unique non-empty strings")
    for locator in normalized["evidence"]:
        if Path(locator).is_absolute() or ".." in Path(locator).parts:
            raise RefocusError("overlay evidence locator is unsafe")
    for field in ("parent_version", "rollback"):
        reference = normalized[field]
        if reference is not None:
            normalized[field] = _validate_version(reference, field=f"overlay {field}")
    supplied_hash = normalized.get("hash")
    expected_hash = _compute_overlay_hash(normalized)
    if supplied_hash not in {"", expected_hash}:
        raise RefocusError("overlay supplied hash differs from canonical content")
    normalized["hash"] = expected_hash
    return normalized


def _validated_registry(root: Path) -> PromptRegistry:
    try:
        registry = PromptRegistry(root)
        for role_id, versions in registry.registry.get("overlays", {}).items():
            for version in versions:
                registry.overlay(role_id, version)
        return registry
    except PromptIntegrityError as exc:
        raise RefocusError(f"prompt registry integrity validation failed: {exc}") from exc


def _validate_overlay_graph(documents: Mapping[str, Mapping[str, Mapping[str, Any]]]) -> None:
    for role_id, versions in documents.items():
        graph: dict[str, tuple[str, ...]] = {}
        for version, document in versions.items():
            references = tuple(
                reference
                for reference in (document["parent_version"], document["rollback"])
                if reference is not None
            )
            if any(reference not in versions for reference in references):
                raise RefocusError(f"overlay {role_id}/{version} references an unknown version")
            if version in references:
                raise RefocusError(f"overlay {role_id}/{version} is self-referential")
            graph[version] = references
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(version: str) -> None:
            if version in visiting:
                raise RefocusError(f"overlay graph for {role_id} is cyclic")
            if version in visited:
                return
            visiting.add(version)
            for reference in graph[version]:
                visit(reference)
            visiting.remove(version)
            visited.add(version)

        for version in graph:
            visit(version)


def _registry_bytes(registry_data: Mapping[str, Any]) -> bytes:
    return (json.dumps(registry_data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _replace_registry(prompts_dir: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".registry_new_", dir=prompts_dir)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, prompts_dir / "registry.json")
        _fsync(prompts_dir)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _register_overlays_cas(
    root: Path,
    overlays: Sequence[tuple[str, str, Mapping[str, Any]]],
) -> dict[tuple[str, str], str]:
    """Register one complete overlay batch with one registry commit."""
    root = Path(root).resolve()
    prompts_dir = root / "prompts"
    registry_path = prompts_dir / "registry.json"
    requested: dict[tuple[str, str], dict[str, Any]] = {}
    for role_id, version, document in overlays:
        if not isinstance(role_id, str) or role_id not in OVERLAY_ROLE_IDS:
            raise RefocusError(f"cannot register overlay for forbidden role: {role_id}")
        safe_version = _validate_version(version)
        key = (role_id, safe_version)
        normalized = _normalize_overlay_document(document)
        if key in requested and requested[key] != normalized:
            raise RefocusError("overlay batch contains a conflicting duplicate")
        requested[key] = normalized
    if not requested:
        return {}

    with _locked_registry(prompts_dir):
        registry = _validated_registry(root)
        registry_data = copy.deepcopy(registry.registry)
        original_registry_raw = registry_path.read_bytes()
        documents: dict[str, dict[str, dict[str, Any]]] = {}
        for role_id, versions in registry.registry.get("overlays", {}).items():
            documents[role_id] = {}
            for version in versions:
                _, existing = registry.overlay(role_id, version)
                documents[role_id][version] = dict(existing)

        publish: list[tuple[Path, dict[str, Any]]] = []
        result: dict[tuple[str, str], str] = {}
        catalog = registry_data.setdefault("overlays", {})
        for (role_id, version), document in requested.items():
            overlay_dir = _safe_overlay_directory(prompts_dir, role_id, create=False)
            overlay_file = overlay_dir / f"{version}.yaml"
            role_catalog = catalog.setdefault(role_id, {})
            existing_entry = role_catalog.get(version)
            if existing_entry is not None:
                _, existing_document = registry.overlay(role_id, version)
                if dict(existing_document) != document or existing_entry.get("hash") != document["hash"]:
                    raise RefocusError(f"overlay version '{version}' already exists for role '{role_id}' with different content")
            else:
                if overlay_file.exists() or overlay_file.is_symlink():
                    if overlay_file.is_symlink() or not overlay_file.is_file():
                        raise RefocusError("orphan overlay is not a safe regular file")
                    try:
                        orphan = yaml.safe_load(overlay_file.read_text(encoding="utf-8"))
                    except (OSError, yaml.YAMLError) as exc:
                        raise RefocusError("orphan overlay is unreadable") from exc
                    if orphan != document:
                        raise RefocusError("refusing to overwrite a conflicting orphan overlay")
                else:
                    publish.append((overlay_file, document))
                role_catalog[version] = {
                    "path": f"overlays/{role_id}/{version}.yaml",
                    "hash": document["hash"],
                }
            documents.setdefault(role_id, {})[version] = document
            result[(role_id, version)] = document["hash"]

        _validate_overlay_graph(documents)
        if registry_data == registry.registry:
            return result

        staged_files: list[tuple[str, Path]] = []
        registry_committed = False
        try:
            for overlay_file, document in publish:
                _safe_overlay_directory(prompts_dir, overlay_file.parent.name, create=True)
                descriptor, temporary = tempfile.mkstemp(prefix=".overlay_stage_", dir=overlay_file.parent)
                with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                    yaml.safe_dump(document, stream, sort_keys=True, allow_unicode=True)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temporary, 0o444)
                staged_files.append((temporary, overlay_file))

            for temporary, overlay_file in staged_files:
                if overlay_file.exists():
                    existing = yaml.safe_load(overlay_file.read_text(encoding="utf-8"))
                    expected = requested[(overlay_file.parent.name, overlay_file.stem)]
                    if existing != expected:
                        raise RefocusError("concurrent conflicting overlay publication detected")
                else:
                    os.link(temporary, overlay_file)
                    _fsync(overlay_file.parent)

            _replace_registry(prompts_dir, _registry_bytes(registry_data))
            registry_committed = True
            _validated_registry(root)
        except Exception:
            if registry_committed:
                _replace_registry(prompts_dir, original_registry_raw)
            raise
        finally:
            for temporary, _ in staged_files:
                if os.path.exists(temporary):
                    # ``temporary`` may be a hard link to the published
                    # overlay.  chmod would mutate that shared inode and turn
                    # the just-published immutable overlay back into 0600.
                    # Unlinking the staging name is sufficient cleanup.
                    os.unlink(temporary)
        return result


def register_overlay_cas(
    root: Path,
    role_id: str,
    version: str,
    overlay_document: Mapping[str, Any],
) -> str:
    """Create or idempotently recover one immutable registered overlay."""
    return _register_overlays_cas(Path(root), [(role_id, version, overlay_document)])[(role_id, version)]


def _latest_overlay_version(root: Path, role_id: str, *, exclude: str | None = None) -> str | None:
    registry = _validated_registry(root)
    versions = registry.registry.get("overlays", {}).get(role_id, {})
    candidates = sorted(version for version in versions if version != exclude)
    return candidates[-1] if candidates else None


def _overlay_document(
    *,
    root: Path,
    role_id: str,
    version: str,
    diagnostic: str,
    evidence: str,
    scope: str,
    instructions: str,
) -> dict[str, Any]:
    parent = _latest_overlay_version(root, role_id, exclude=version)
    return {
        "parent_version": parent,
        "diagnostic": diagnostic,
        "author": "m9-refocus-generator",
        "evidence": [evidence],
        "scope": [scope],
        "hash": "",
        "rollback": parent,
        "instructions": instructions,
    }


def _plan_id_for(plan: Mapping[str, Any]) -> str:
    body = dict(plan)
    body.pop("plan_id", None)
    return f"plan-{_sha(_json(body))}"


def _revalidate_published_refocus(
    root: Path,
    refocus_dir: Path,
    *,
    expected: Mapping[str, Any],
) -> dict[str, Any]:
    canonical_dir = f"state/refocus/{expected['run_id']}/c{expected['cycle_id']:04d}"
    try:
        relative = refocus_dir.resolve().relative_to(root).as_posix()
    except (OSError, ValueError) as exc:
        raise RefocusError("published refocus directory escapes project root") from exc
    if relative != canonical_dir:
        raise RefocusError("published refocus directory is not canonical")
    _contained(root, canonical_dir, True)
    entries = _walk(refocus_dir)
    if [relative_path for relative_path, _, _ in entries] != ["refocus-plan.json"]:
        raise RefocusError("published refocus directory has unexpected artifacts")
    if (
        stat.S_IMODE(refocus_dir.lstat().st_mode) != 0o555
        or stat.S_IMODE(entries[0][2].st_mode) != 0o444
    ):
        raise RefocusError("published refocus plan permissions are not immutable")
    plan, raw = _read_json(refocus_dir / "refocus-plan.json")
    try:
        _validate_schema(root, REFOCUS_PLAN_SCHEMA, plan)
    except EvaluationError as exc:
        raise RefocusError("published refocus plan schema validation failed") from exc
    if raw != _json(plan) or plan.get("plan_id") != _plan_id_for(plan):
        raise RefocusError("published refocus plan is not canonical content-addressed JSON")
    if plan != dict(expected):
        raise RefocusError("published refocus plan conflicts with canonical diagnosis")
    registry = _validated_registry(root)
    for branch in plan["branches"]:
        for role_id, version in branch["overlay_versions"].items():
            _, document = registry.overlay(role_id, version)
            if branch["overlay_hashes"].get(role_id) != document.get("hash"):
                raise RefocusError("refocus plan overlay hash binding differs from registry")
            entry = registry.registry["overlays"][role_id][version]
            overlay_path = root / "prompts" / entry["path"]
            info = overlay_path.lstat()
            if stat.S_IMODE(info.st_mode) != 0o444 or info.st_nlink != 1:
                raise RefocusError("generated refocus overlay is not immutable")
    return plan


def generate_refocus_plan(
    root: Path | str,
    run_id: str,
    cycle_id: int,
    diagnosis: Mapping[str, Any],
    *,
    store: DurableStore | None = None,
    fault: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Generate an authorized, idempotent RefocusPlan from canonical M9 evidence."""
    if isinstance(cycle_id, bool) or not isinstance(cycle_id, int) or cycle_id < 0:
        raise RefocusError("cycle_id must be a non-negative integer")
    if not isinstance(run_id, str) or not run_id:
        raise RefocusError("run_id must be a non-empty string")
    if not isinstance(diagnosis, Mapping):
        raise RefocusError("diagnosis must be an object")
    root_path = Path(root).resolve()
    try:
        canonical_diagnosis, _ = verify_published_diagnosis(root_path, run_id, cycle_id, store=store)
    except DiagnosisError as exc:
        raise RefocusError(f"canonical diagnosis verification failed: {exc}") from exc
    if dict(diagnosis) != canonical_diagnosis:
        raise RefocusError("supplied diagnosis differs from canonical published diagnosis")

    classification = canonical_diagnosis["classification"]
    if classification in FORBIDDEN_REFOCUS_CLASSIFICATIONS:
        raise RefocusError(
            f"refocus overlay generation is forbidden for classification '{classification}'; must proceed to M10 directly without overlays"
        )
    if classification not in ALLOWED_REFOCUS_CLASSIFICATIONS:
        raise RefocusError(f"unknown classification for refocus: {classification}")

    diagnosis_locator = f"state/diagnosis/{run_id}/c{cycle_id:04d}/diagnosis.json"
    diagnosis_hash = _sha(_json(canonical_diagnosis))
    focus = list(canonical_diagnosis["focus"])
    run_tag = _sha(run_id.encode("utf-8"))[:12]
    requested_overlays: list[tuple[str, str, dict[str, Any]]] = []
    branches: list[dict[str, Any]] = []

    def add_branch(
        *,
        branch_id: str,
        kind: str,
        role_id: str,
        suffix: str,
        hypothesis: str,
        falsification: list[str],
        scope: str,
        instructions: str,
    ) -> None:
        version = f"m9-{run_tag}-c{cycle_id:04d}-{suffix}"
        expected_document = _overlay_document(
            root=root_path,
            role_id=role_id,
            version=version,
            diagnostic=f"Refocus M9 {classification} for {role_id} in cycle {cycle_id}.",
            evidence=diagnosis_locator,
            scope=scope,
            instructions=instructions,
        )
        expected_normalized = _normalize_overlay_document(expected_document)
        current_registry = _validated_registry(root_path)
        existing_entry = current_registry.registry.get("overlays", {}).get(role_id, {}).get(version)
        if existing_entry is not None:
            _, existing_document = current_registry.overlay(role_id, version)
            if dict(existing_document) != expected_normalized:
                raise RefocusError("existing generated overlay conflicts with canonical refocus content")
            document = expected_normalized
        else:
            document = expected_normalized
        normalized = _normalize_overlay_document(document)
        requested_overlays.append((role_id, version, normalized))
        branches.append({
            "branch_id": branch_id,
            "kind": kind,
            "hypothesis": hypothesis,
            "falsification_criteria": falsification,
            "target_roles": [role_id],
            "budget_limit": {"max_tokens": 0, "max_cost": 0.0, "max_cycles": 1},
            "overlay_versions": {role_id: version},
            "overlay_hashes": {role_id: normalized["hash"]},
        })

    if classification == "LOCAL_PLATEAU":
        target_role = next((item for item in focus if item in OVERLAY_ROLE_IDS and item.startswith("W")), "W22")
        add_branch(
            branch_id="branch-targeted-bottleneck",
            kind="targeted",
            role_id=target_role,
            suffix="bottleneck",
            hypothesis=f"Mitigate local stagnation bottleneck in role {target_role}",
            falsification=[f"dimension_delta:{target_role} <= 0.0", "correctness_math_pass == False"],
            scope="proof" if target_role in {"W21", "W22", "W23"} else "structure",
            instructions=f"Resolve only the diagnosed bottleneck in {target_role}; preserve validated claims and provide explicit evidence locators.",
        )
    elif classification == "GLOBAL_PLATEAU":
        add_branch(
            branch_id="branch-exploitation",
            kind="exploitation",
            role_id="W22",
            suffix="exploit",
            hypothesis="Deepen lemma verification in the core proof to break stagnation",
            falsification=["proof_completeness_gain < 0.2", "correctness_math_pass == False"],
            scope="proof",
            instructions="Refine core proof steps with granular lemmas while preserving global definitions and all validated claims.",
        )
        add_branch(
            branch_id="branch-exploration",
            kind="exploration",
            role_id="W31",
            suffix="explore",
            hypothesis="Explore an equivalent bound formulation to unlock the global plateau",
            falsification=["scientific_contribution_gain < 0.2", "correctness_math_pass == False"],
            scope="constants",
            instructions="Explore an equivalent formulation of hypotheses and bounds without weakening validated mathematical obligations.",
        )
    else:
        add_branch(
            branch_id="branch-stabilization",
            kind="stabilization",
            role_id="W12",
            suffix="stabilize",
            hypothesis="Stabilize oscillating dimension trade-offs",
            falsification=["dimension_reversals_detected > 0", "correctness_math_pass == False"],
            scope="structure",
            instructions="Enforce convergence constraints and preserve all previously validated terms without reversing accepted edits.",
        )

    strategy = {
        "LOCAL_PLATEAU": "targeted_bottleneck",
        "GLOBAL_PLATEAU": "dual_branch",
        "OSCILLATING": "stabilization",
    }[classification]
    plan_without_id = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "cycle_id": cycle_id,
        "diagnosis_id": canonical_diagnosis["diagnosis_id"],
        "diagnosis_hash": diagnosis_hash,
        "classification": classification,
        "strategy": strategy,
        "branches": branches,
        "created_at": canonical_diagnosis["created_at"],
        "evidence_locators": [diagnosis_locator],
    }
    refocus_plan = {"plan_id": _plan_id_for(plan_without_id), **plan_without_id}
    try:
        _validate_schema(root_path, REFOCUS_PLAN_SCHEMA, refocus_plan)
    except EvaluationError as exc:
        raise RefocusError("generated refocus plan does not satisfy its schema") from exc

    refocus_parent = _managed_directory(root_path, f"state/refocus/{run_id}", create=False)
    refocus_dir = refocus_parent / f"c{cycle_id:04d}"
    if refocus_dir.exists():
        return _revalidate_published_refocus(root_path, refocus_dir, expected=refocus_plan)

    _register_overlays_cas(root_path, requested_overlays)
    if fault:
        fault("after_overlays_registered")

    refocus_parent = _managed_directory(root_path, f"state/refocus/{run_id}", create=True)
    staging_path = Path(tempfile.mkdtemp(prefix=f".staging_refocus_c{cycle_id:04d}_", dir=refocus_parent))
    try:
        _write_synced_file(staging_path / "refocus-plan.json", _json(refocus_plan))
        _fsync_tree_dirs(staging_path)
        _harden_read_only(staging_path)
        _fsync_tree_dirs(staging_path)
        if fault:
            fault("before_refocus_plan_published")
        if refocus_dir.exists():
            _cleanup_staging(staging_path)
            return _revalidate_published_refocus(root_path, refocus_dir, expected=refocus_plan)
        os.replace(staging_path, refocus_dir)
        _fsync(refocus_parent)
    except Exception:
        _cleanup_staging(staging_path)
        raise
    return _revalidate_published_refocus(root_path, refocus_dir, expected=refocus_plan)
