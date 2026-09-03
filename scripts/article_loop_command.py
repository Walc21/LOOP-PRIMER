#!/usr/bin/env python3
"""Project-local, fail-closed command bridge for the article-loop skill.

This module is intentionally a thin adapter around the APIs that already
exist in ``article_loop``.  It never selects a fake adapter, starts a Prime
session, reads credentials, or contacts a network service.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping

try:
    import yaml
except ImportError as error:  # pragma: no cover - the project declares PyYAML
    raise SystemExit("PyYAML is required for the local command bridge") from error

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".prime/agent/skills/article-loop/src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from article_loop import (  # noqa: E402
    bootstrap,
    checkpoint,
    finalize,
    pause,
    preflight,
    resume,
    run_cycle,
    status,
    stop,
)
from article_loop.finalization import finalize_decision  # noqa: E402
from article_loop.budget import BudgetError, BudgetLedger  # noqa: E402
from article_loop.orchestrator import Orchestrator  # noqa: E402
from article_loop.inference import (  # noqa: E402
    InferenceConfigError,
    InferenceRuntime,
    ModelRegistry,
    inference_preflight,
)


COMMANDS = (
    "bootstrap",
    "preflight",
    "run",
    "status",
    "checkpoint",
    "pause",
    "resume",
    "stop",
    "finalize",
)
TEMPLATE_NAMES = tuple(f"article-{name}" for name in COMMANDS)
TEMPLATE_DIR = ROOT / ".prime/agent/prompts"
MAX_INPUT_BYTES = 1_048_576
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class CommandInputError(ValueError):
    """The caller supplied an unsupported or malformed command envelope."""


class ProjectCheckError(RuntimeError):
    """The project cannot safely satisfy a local command precondition."""


def _read_json_input(path_value: str | None) -> dict[str, Any]:
    if path_value is None:
        return {}
    if path_value == "-":
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    else:
        path = Path(path_value)
        if path.is_symlink() or not path.is_file():
            raise CommandInputError("input must be a regular, non-symlink file")
        if path.stat().st_size > MAX_INPUT_BYTES:
            raise CommandInputError("input JSON exceeds the local size limit")
        raw = path.read_bytes()
    if len(raw) > MAX_INPUT_BYTES:
        raise CommandInputError("input JSON exceeds the local size limit")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CommandInputError("input must be valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise CommandInputError("input JSON must be an object")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local JSON-in/JSON-out command bridge for article-loop"
    )
    parser.add_argument("command", choices=COMMANDS + ("check",))
    parser.add_argument("--root", default=None, help="project root (default: this checkout)")
    parser.add_argument("--input", default=None, help="JSON file or '-' for stdin")
    parser.add_argument("--pdf", default=None, help="regular PDF path for bootstrap")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--cycle-id", type=int, default=None)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", dest="dry_run", action="store_true", default=None)
    mode.add_argument("--live", dest="dry_run", action="store_false", default=None)
    parser.add_argument(
        "--require-live",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser


def _safe_root(value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CommandInputError("root must be a non-empty string")
    raw = Path(value)
    if raw.is_symlink():
        raise CommandInputError("root must not be a symlink")
    try:
        root = raw.resolve(strict=True)
    except OSError as error:
        raise CommandInputError("root must be an existing directory") from error
    if not root.is_dir():
        raise CommandInputError("root must be an existing directory")
    return root


def _safe_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise CommandInputError(f"{label} must be a safe non-empty identifier")
    return value


def _cycle(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CommandInputError("cycle_id must be a non-negative integer")
    return value


def _merge_parameters(command: str, args: argparse.Namespace) -> dict[str, Any]:
    incoming = _read_json_input(args.input)
    allowed = {
        "bootstrap": {"root", "pdf"},
        "preflight": {"root"},
        "run": {"root", "run_id", "cycle_id", "dry_run"},
        "status": {"root", "run_id", "cycle_id"},
        "checkpoint": {"root", "run_id"},
        "pause": {"root", "run_id"},
        "resume": {"root", "run_id"},
        "stop": {"root", "run_id"},
        "finalize": {"root", "run_id", "cycle_id"},
        "check": {"root"},
    }[command]
    unknown = set(incoming) - allowed
    if unknown:
        raise CommandInputError(
            "input JSON has unsupported parameters: " + ", ".join(sorted(unknown))
        )
    if args.require_live and command != "check":
        raise CommandInputError("--require-live is accepted only by check")

    cli_values = {
        "root": args.root,
        "pdf": args.pdf,
        "run_id": args.run_id,
        "cycle_id": args.cycle_id,
        "dry_run": args.dry_run,
    }
    for key, value in cli_values.items():
        if value is not None and key not in allowed:
            raise CommandInputError(f"{key} is not accepted by /{command}")
    for key, value in cli_values.items():
        if value is None:
            continue
        if key in incoming and incoming[key] != value:
            raise CommandInputError(f"conflicting values for {key}")
        incoming[key] = value

    incoming["root"] = _safe_root(incoming.get("root", str(ROOT)))
    if command == "bootstrap":
        pdf = incoming.get("pdf")
        if not isinstance(pdf, str) or not pdf.strip():
            raise CommandInputError("bootstrap requires one PDF path")
        pdf_path = Path(pdf)
        if pdf_path.is_symlink() or not pdf_path.is_file():
            raise CommandInputError("bootstrap PDF must be a regular, non-symlink file")
        incoming["pdf"] = pdf
    if "run_id" in incoming and incoming["run_id"] is not None:
        incoming["run_id"] = _safe_id(incoming["run_id"], "run_id")
    if "cycle_id" in incoming:
        incoming["cycle_id"] = _cycle(incoming["cycle_id"])
    if command == "run":
        dry_run = incoming.get("dry_run", True)
        if type(dry_run) is not bool:
            raise CommandInputError("dry_run must be a boolean")
        incoming["dry_run"] = dry_run
    return incoming


def _load_yaml(path: Path) -> Mapping[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ProjectCheckError(f"cannot read project configuration: {path.name}") from error
    if not isinstance(value, Mapping):
        raise ProjectCheckError(f"project configuration is not an object: {path.name}")
    return value


def _check_template(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ProjectCheckError(f"template is unreadable: {path.name}") from error
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ProjectCheckError(f"template lacks YAML frontmatter: {path.name}")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ProjectCheckError(f"template frontmatter is not closed: {path.name}") from error
    try:
        metadata = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as error:
        raise ProjectCheckError(f"template frontmatter is invalid: {path.name}") from error
    if not isinstance(metadata, Mapping) or not metadata:
        raise ProjectCheckError(f"template frontmatter is empty: {path.name}")
    if set(metadata) - {"description", "argument-hint"}:
        raise ProjectCheckError(f"template uses unsupported frontmatter: {path.name}")
    if not isinstance(metadata.get("description"), str) or not metadata["description"].strip():
        raise ProjectCheckError(f"template description is invalid: {path.name}")
    hint = metadata.get("argument-hint")
    if hint is not None and not isinstance(hint, str):
        raise ProjectCheckError(f"template argument-hint is invalid: {path.name}")
    if not "article_loop" in "\n".join(lines[end + 1 :]):
        raise ProjectCheckError(f"template does not name an article_loop API: {path.name}")


def _validate_fail_closed_budget(config: Mapping[str, Any], *, require_live: bool) -> dict[str, Any]:
    execution = config.get("model_execution")
    rlm = config.get("rlm")
    authorization = config.get("authorization")
    if not all(isinstance(item, Mapping) for item in (execution, rlm, authorization)):
        raise ProjectCheckError("config/budgets.yaml lacks closed execution sections")
    if rlm.get("max_depth") != 2 or rlm.get("sparse_activation_required") is not True:
        raise ProjectCheckError("RLM depth/sparse activation is not the canonical value")
    if type(execution.get("enabled")) is not bool or type(execution.get("paid_apis_enabled")) is not bool:
        raise ProjectCheckError("model execution flags are invalid")
    if type(authorization.get("required_for_model_calls")) is not bool or authorization.get("required_for_model_calls") is not True:
        raise ProjectCheckError("model-call authorization must be required")
    limits = ("total_cost_limit", "per_cycle_cost_limit", "max_model_calls", "max_concurrent_children")
    for key in limits:
        value = execution.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ProjectCheckError(f"invalid model execution limit: {key}")
    for key in ("max_model_calls", "max_concurrent_children"):
        value = execution.get(key)
        if type(value) is not int:
            raise ProjectCheckError(f"invalid integer model execution limit: {key}")
    if execution.get("paid_apis_enabled"):
        raise ProjectCheckError("paid APIs are not permitted by M11")
    live_ready = (
        execution.get("enabled") is True
        and execution.get("max_model_calls", 0) > 0
        and execution.get("max_concurrent_children", 0) > 0
        and isinstance(authorization.get("approval_reference"), str)
        and bool(authorization.get("approval_reference").strip())
    )
    if require_live and not live_ready:
        raise ProjectCheckError("live execution is not explicitly enabled and authorized")
    return {
        "model_execution_enabled": execution.get("enabled") is True,
        "live_ready": live_ready,
        "paid_apis_enabled": False,
        "rlm_max_depth": 2,
    }


def _validate_m12_budget(config: Mapping[str, Any]) -> dict[str, Any]:
    """Validate M12 declarations without enabling any consumer."""
    section = config.get("budget")
    if not isinstance(section, Mapping) or section.get("schema_version") != "1.0.0":
        raise ProjectCheckError("config/budgets.yaml lacks the M12 budget section")
    if section.get("unit") != "tokens":
        raise ProjectCheckError("M12 budget unit must be tokens")
    if section.get("default_profile") is not None:
        raise ProjectCheckError("M12 default_profile must remain disabled")
    maximum = section.get("max_integer")
    if type(maximum) is not int or maximum < 1 or maximum > 2**63 - 1:
        raise ProjectCheckError("M12 budget max_integer is invalid")
    limits = section.get("limits")
    if not isinstance(limits, Mapping):
        raise ProjectCheckError("M12 budget limits are invalid")
    required_limits = {
        "total_tokens", "per_cycle_tokens", "per_department_tokens", "per_role_tokens",
        "per_model_tokens", "max_calls", "max_concurrent_children", "max_retries",
        "max_wall_time_seconds", "max_cycles", "max_cycles_without_improvement",
        "max_extra_judgments",
    }
    if set(limits) != required_limits:
        raise ProjectCheckError("M12 budget limits are not the canonical set")
    for name, value in limits.items():
        if type(value) is not int or value < 0 or value > maximum:
            raise ProjectCheckError(f"invalid M12 budget limit: {name}")
    profiles = section.get("profiles")
    if not isinstance(profiles, Mapping) or set(profiles) != {"calibration", "overnight"}:
        raise ProjectCheckError("M12 budget profiles are invalid")
    expected_profiles = {
        "calibration": {
            "total_tokens": 250000, "max_cycles": 1,
            "max_concurrent_children": 5, "max_wall_time_seconds": 5400,
            "max_retries": 0, "max_extra_judgments": 0,
        },
        "overnight": {
            "total_tokens": 1500000, "max_cycles": 6,
            "max_wall_time_seconds": 28800,
            "max_cycles_without_improvement": 2, "max_extra_judgments": 1,
            "max_retries": 0,
        },
    }
    for name, profile in profiles.items():
        if not isinstance(profile, Mapping) or type(profile.get("enabled")) is not bool or profile.get("enabled") is not False:
            raise ProjectCheckError(f"M12 profile is invalid: {name}")
        profile_limits = profile.get("limits")
        if not isinstance(profile_limits, Mapping) or dict(profile_limits) != expected_profiles[name]:
            raise ProjectCheckError(f"M12 profile limits are invalid: {name}")
        for key, value in profile_limits.items():
            if type(value) is not int or value < 0 or value > maximum:
                raise ProjectCheckError(f"invalid M12 profile limit: {name}.{key}")
    observability = config.get("observability")
    if not isinstance(observability, Mapping) or observability.get("schema_version") != "1.0.0":
        raise ProjectCheckError("M12 observability configuration is invalid")
    if type(observability.get("max_log_bytes")) is not int or observability["max_log_bytes"] < 1024:
        raise ProjectCheckError("M12 log size limit is invalid")
    if observability.get("redaction") != "allowlist":
        raise ProjectCheckError("M12 log redaction must use an allowlist")
    thresholds = observability.get("alert_thresholds")
    if thresholds != [50, 80, 95, 100]:
        raise ProjectCheckError("M12 alert thresholds are invalid")
    return {"unit": "tokens", "profiles": {name: profile["enabled"] for name, profile in profiles.items()}, "max_log_bytes": observability["max_log_bytes"]}


def _validate_m125_inference(root: Path) -> dict[str, Any]:
    """Validate routing declarations without starting a backend or model."""
    try:
        return inference_preflight(root)
    except InferenceConfigError as error:
        raise ProjectCheckError("M12.5 inference configuration is invalid") from error


def check_project(root: str | Path, *, require_live: bool = False) -> dict[str, Any]:
    """Validate only local M11 surfaces and fail closed on unsafe drift."""
    project = _safe_root(str(root))
    required_files = (
        "AGENTS.md",
        "AI_CONTEXT.md",
        ".prime/agent/APPEND_SYSTEM.md",
        ".prime/agent/skills/article-loop/SKILL.md",
        "config/budgets.yaml",
        "config/schemas/inference-receipt.schema.json",
        "config/system.yaml",
        "scripts/article_loop_command.py",
        "bin/check.sh",
        "bin/start-prime.sh",
    )
    for relative in required_files:
        path = project / relative
        if path.is_symlink() or not path.is_file():
            raise ProjectCheckError(f"required project file is unsafe or missing: {relative}")
    for relative in (".prime/agent/prompts", "control", "input/inbox"):
        path = project / relative
        if path.is_symlink() or not path.is_dir():
            raise ProjectCheckError(f"required project directory is unsafe or missing: {relative}")
    append = (project / ".prime/agent/APPEND_SYSTEM.md").read_text(encoding="utf-8")
    for marker in ("AGENTS.md", "article-loop/SKILL.md", "FINALIZED"):
        if marker not in append:
            raise ProjectCheckError("APPEND_SYSTEM.md is missing a required guardrail")
    stop_path = project / "control/STOP"
    if stop_path.exists() or stop_path.is_symlink():
        raise ProjectCheckError("control/STOP blocks new operations")
    settings = project / ".prime/agent/settings.json"
    if settings.exists() or settings.is_symlink():
        raise ProjectCheckError("unverified project settings.json is not accepted")

    prompt_dir = project / ".prime/agent/prompts"
    discovered = tuple(sorted(path.stem for path in prompt_dir.glob("*.md")))
    if discovered != tuple(sorted(TEMPLATE_NAMES)):
        raise ProjectCheckError("prompt template discovery is not the canonical M11 set")
    for name in TEMPLATE_NAMES:
        template = prompt_dir / f"{name}.md"
        if template.is_symlink():
            raise ProjectCheckError(f"symlinked prompt template: {template.name}")
        _check_template(template)

    budgets = _load_yaml(project / "config/budgets.yaml")
    execution = _validate_fail_closed_budget(budgets, require_live=require_live)
    m12 = _validate_m12_budget(budgets)
    m125 = _validate_m125_inference(project)
    system = _load_yaml(project / "config/system.yaml")
    project_config = system.get("project")
    if not isinstance(project_config, Mapping) or project_config.get("rlm_max_depth") != 2:
        raise ProjectCheckError("config/system.yaml has an invalid project depth")
    prime_path = shutil.which("prime-agent")
    return {
        "root": str(project),
        "status": "ok",
        "prompt_templates": list(sorted(TEMPLATE_NAMES)),
        "settings": "omitted_unconfirmed",
        "prime_agent_discovered": prime_path is not None,
        "execution": execution,
        "m12": m12,
        "m125": m125,
        "stop_present": False,
    }


def _run_command(command: str, params: Mapping[str, Any]) -> Any:
    root = params["root"]
    run_id = params.get("run_id")
    cycle_id = params.get("cycle_id")
    if command == "bootstrap":
        return asyncio.run(bootstrap(params["pdf"], root=root))
    if command == "preflight":
        result = asyncio.run(preflight(root=root))
        return {**dict(result), "inference": _validate_m125_inference(root)}
    if command == "run":
        return asyncio.run(
            run_cycle(
                root=root,
                cycle_id=cycle_id,
                dry_run=params["dry_run"],
            )
        )
    if command == "status":
        if run_id is None:
            return asyncio.run(status(root=root))
        result = asyncio.run(Orchestrator(root).status(run_id))
        try:
            ledger = BudgetLedger.from_project(root, run_id)
            registry = ModelRegistry.from_project(root)
            result = {
                **result,
                "budget": ledger.status(current_cycle=cycle_id),
                "inference": InferenceRuntime(root, ledger, registry, {}).status(),
            }
        except BudgetError as error:
            raise RuntimeError("budget status is unavailable") from error
        return result
    if command == "checkpoint":
        if run_id is None:
            return asyncio.run(checkpoint(root=root))
        return asyncio.run(Orchestrator(root).checkpoint(run_id))
    if command == "pause":
        if run_id is None:
            return asyncio.run(pause(root=root))
        return asyncio.run(Orchestrator(root).pause(run_id))
    if command == "resume":
        if run_id is None:
            return asyncio.run(resume(root=root))
        return asyncio.run(Orchestrator(root).resume(run_id))
    if command == "stop":
        if run_id is None:
            return asyncio.run(stop(root=root))
        return asyncio.run(Orchestrator(root).stop(run_id))
    if command == "finalize":
        if run_id is None:
            return asyncio.run(finalize(root=root))
        return finalize_decision(root, run_id, cycle_id=cycle_id)
    raise CommandInputError(f"unsupported command: {command}")


def _result(value: Any) -> Any:
    if isinstance(value, Mapping):
        return dict(value)
    return value


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        params = _merge_parameters(args.command, args)
        if args.command == "check":
            value = check_project(params["root"], require_live=args.require_live)
        else:
            value = _run_command(args.command, params)
        sys.stdout.write(
            json.dumps(
                {"status": "success", "command": args.command, "result": _result(value)},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0
    except CommandInputError as error:
        sys.stderr.write(json.dumps({"status": "error", "error_type": "input_error", "message": str(error)}) + "\n")
        return 2
    except (ProjectCheckError, OSError, RuntimeError, ValueError) as error:
        sys.stderr.write(json.dumps({"status": "error", "error_type": "operation_error", "message": str(error)}) + "\n")
        return 3
    except Exception as error:  # pragma: no cover - defensive fail-closed boundary
        sys.stderr.write(json.dumps({"status": "error", "error_type": "unexpected_error", "message": str(error)}) + "\n")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
