#!/usr/bin/env python3
"""Registra o encerramento de uma sessão de IA e renderiza o histórico.

Uso normal (somente depois de concluir mudanças e validações):

    python3 scripts/ai_history.py \
      --summary "Resumo substantivo da sessão" \
      --change "Mudança principal" \
      --validation "Comando e resultado" \
      --next-step "Próximo trabalho conhecido"

O modo ``--auto`` existe como fallback factual e não inventa decisões.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import re
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from ai_handoff_common import (
    SCHEMA_VERSION,
    HandoffError,
    atomic_write,
    build_inventory,
    canonical_json,
    git_root,
    git_state,
    inventory_delta,
    inventory_fingerprint,
    load_json,
    markdown_cell,
    run_local,
    sha256_bytes,
    snapshot_files,
)


ROOT = Path(__file__).resolve().parents[1]
LEDGER_RELATIVE = Path("docs/ai_sessions.jsonl")
SNAPSHOT_RELATIVE = Path("docs/ai_snapshot.json")
HISTORY_RELATIVE = Path("docs/AI_HISTORY.md")
LOCK_RELATIVE = Path("docs/ai_history.lock")

MILESTONE_PURPOSES = {
    "M0/M0.5": "Auditoria de compatibilidade, segurança e fixação da arquitetura canônica.",
    "M0.6": "Completude de paths e ordem transacional do pipeline.",
    "M1/M1.1": "Scaffold, catálogo de papéis e contratos condicionais em JSON Schema.",
    "M2": "Máquina de estados, event log encadeado, replay e recuperação durável.",
    "M3": "Ingestão PDF/ZIP offline, preservação do original e baseline v0000.",
    "M4": "Prompts imutáveis, overlays e compilação content-addressed dos 21 papéis.",
    "M5": "Blackboard, grafo de impacto, views fechadas e ativação esparsa.",
    "M6": "Orquestração RLM hierárquica reentrante por receipts duráveis.",
    "M7": "Síntese, merge isolado, challenger write-once e 13 gates locais.",
    "M8": "Júri externo cego, inversão consistente e meta-revisão.",
    "M9": "Diagnóstico determinístico de progresso e refoco reversível.",
    "M10": "Política de compensação, decisão canônica e finalizador transacional.",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validated_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HandoffError("--timestamp deve ser ISO 8601 com fuso") from exc
    if parsed.tzinfo is None:
        raise HandoffError("--timestamp deve conter fuso")
    return parsed.isoformat().replace("+00:00", "Z")


def _strings(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise HandoffError(f"{field} deve ser lista de strings não vazias")
    return [item.strip() for item in value]


def _text(value: Any, field: str, *, required: bool = False) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value.strip():
        raise HandoffError(f"{field} deve ser string não vazia")
    text = value.strip()
    if len(text) > 20_000:
        raise HandoffError(f"{field} excede 20.000 caracteres")
    return text


@contextmanager
def _history_lock(root: Path) -> Iterator[None]:
    path = root / LOCK_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = path.read_bytes()
    if data and not data.endswith(b"\n"):
        raise HandoffError(f"ledger truncado, sem newline final: {path}")
    entries: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for number, raw in enumerate(data.splitlines(), 1):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HandoffError(f"ledger inválido na linha {number}: {exc}") from exc
        if not isinstance(value, dict) or not isinstance(value.get("session_id"), str):
            raise HandoffError(f"entrada inválida no ledger, linha {number}")
        if value["session_id"] in identifiers:
            raise HandoffError(f"session_id duplicado no ledger: {value['session_id']}")
        identifiers.add(value["session_id"])
        entries.append(value)
    return entries


def _git_commits(root: Path) -> list[dict[str, Any]]:
    if not git_root(root):
        return []
    result = run_local(
        ["git", "log", "--reverse", "--date=short", "--pretty=format:%H%x1f%ad%x1f%s%x1e"],
        cwd=root,
        timeout=30,
    )
    if result.returncode != 0:
        return []
    commits = []
    for record in result.stdout.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        parts = record.split("\x1f", 2)
        if len(parts) != 3:
            continue
        commit, date, subject = parts
        files_result = run_local(["git", "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", commit], cwd=root)
        files = [line for line in files_result.stdout.splitlines() if line]
        commits.append({"hash": commit, "date": date, "subject": subject, "files": files})
    return commits


def infer_milestone(subject: str) -> str:
    upper = subject.upper()
    explicit = re.findall(r"\bM(\d+(?:\.\d+)?)\b", upper)
    if "MARCO 0 E 0.5" in upper:
        return "M0/M0.5"
    marco = re.findall(r"\bMARCO\s+(\d+(?:\.\d+)?)\b", upper)
    if marco:
        return "/".join("M" + item for item in marco)
    if explicit:
        labels = []
        for item in explicit:
            label = "M" + str(int(item)) if "." not in item else "M" + item
            if label not in labels:
                labels.append(label)
        if labels == ["M1", "M1.1"]:
            return "M1/M1.1"
        return "/".join(labels)
    if "BOOTSTRAP" in upper:
        return "M3"
    return "sem marco explícito"


def _adr_headings(root: Path) -> list[str]:
    path = root / "docs/decisions.md"
    if not path.exists():
        return []
    return [match.group(1).strip() for line in path.read_text("utf-8").splitlines() if (match := re.match(r"^##\s+(ADR-\d+\s+—\s+.+)$", line))]


def _delta_count(delta: Mapping[str, Sequence[Mapping[str, Any]]]) -> int:
    return sum(len(delta.get(key, [])) for key in ("added", "modified", "deleted"))


def _delta_summary(delta: Mapping[str, Sequence[Mapping[str, Any]]]) -> str:
    return ", ".join(f"{len(delta.get(key, []))} {label}" for key, label in (("added", "adicionados"), ("modified", "modificados"), ("deleted", "removidos")))


def render_history(root: Path, entries: Sequence[Mapping[str, Any]], snapshot: Mapping[str, Any]) -> str:
    commits = _git_commits(root)
    adrs = _adr_headings(root)
    lines = [
        "# Histórico evolutivo e atualizações de sessão — article-loop",
        "",
        "> Gerado por `scripts/ai_history.py`. O histórico Git e os ADRs são reconstruídos; as atualizações de sessão vêm do ledger append-only `docs/ai_sessions.jsonl`.",
        "",
        "## Baseline registrado",
        "",
        f"- Fingerprint das fontes: `{snapshot.get('fingerprint') or '-'}`",
        f"- Registrado em: `{snapshot.get('recorded_at') or '-'}`",
        f"- Git: branch `{snapshot.get('git', {}).get('branch') or '-'}`, HEAD `{str(snapshot.get('git', {}).get('head') or '-')[:12]}`",
        f"- Arquivos relevantes: {len(snapshot.get('files', {}))}",
        "",
        "## Evolução reconstruída do versionamento",
        "",
        "| Marco | Intervalo | Commits | Evolução inferida | Áreas tocadas |",
        "|---|---:|---:|---|---|",
    ]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for commit in commits:
        grouped.setdefault(infer_milestone(commit["subject"]), []).append(commit)
    for milestone, list_commits in grouped.items():
        dates = f"{list_commits[0]['date']}..{list_commits[-1]['date']}" if list_commits[0]["date"] != list_commits[-1]["date"] else list_commits[0]["date"]
        purpose = MILESTONE_PURPOSES.get(milestone, "Inferida dos assuntos dos commits; consulte a tabela exata abaixo.")
        touched = sorted({Path(path).parts[0] for commit in list_commits for path in commit["files"]})
        lines.append(f"| {milestone} | {dates} | {len(list_commits)} | {purpose} | {', '.join(touched[:8])} |")

    lines.extend(["", "### Commits exatos", "", "| Commit | Data | Marco | Assunto | Arquivos principais |", "|---|---:|---|---|---|"])
    for commit in commits:
        top_files = [path for path in commit["files"] if not path.endswith(".gitkeep")]
        sample = ", ".join(top_files[:3]) + (", …" if len(top_files) > 3 else "")
        lines.append(f"| `{commit['hash'][:9]}` | {commit['date']} | {infer_milestone(commit['subject'])} | {markdown_cell(commit['subject'], 120)} | {markdown_cell(sample or '-', 140)} |")

    lines.extend(["", "## Decisões arquiteturais", ""])
    if adrs:
        for adr in adrs:
            lines.append(f"- {adr}")
    else:
        lines.append("- Nenhuma decisão encontrada em `docs/decisions.md`.")

    lines.extend(["", "## Atualizações de sessão", ""])
    if not entries:
        lines.append("- Nenhuma sessão registrada no ledger.")
    for entry in reversed(entries):
        lines.extend([
            f"### {entry.get('recorded_at')} — {entry.get('summary')}",
            "",
            f"- Session ID: `{entry.get('session_id')}`",
            f"- Fingerprint final: `{entry.get('source_fingerprint')}`",
            f"- Git final: `{str(entry.get('git', {}).get('head') or '-')[:12]}`; status relevante: {len(entry.get('git', {}).get('status', []))} item(ns)",
            f"- Delta factual: {_delta_summary(entry.get('file_delta', {}))}",
        ])
        if entry.get("baseline_initialized"):
            lines.append("- Esta sessão inicializou o primeiro baseline; a evolução anterior é reconstruída do Git/ADRs, não tratada como adição de todos os arquivos.")
        for key, title in (("changes", "Mudanças"), ("decisions", "Decisões"), ("validations", "Validações"), ("risks", "Riscos/limites"), ("next_steps", "Próximos passos")):
            values = entry.get(key, [])
            if values:
                lines.extend(["", f"**{title}**", ""])
                for item in values:
                    lines.append(f"- {item}")
        delta = entry.get("file_delta", {})
        if _delta_count(delta) > 0:
            lines.extend(["", "**Arquivos detectados**", "", "| Tipo | Caminho | SHA anterior | SHA final |", "|---|---|---|---|"])
            for kind in ("added", "modified", "deleted"):
                for item in delta.get(kind, []):
                    lines.append(f"| {kind} | `{item['path']}` | `{str(item.get('before') or '-')[:12]}` | `{str(item.get('after') or '-')[:12]}` |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Registra o encerramento de uma sessão de IA.")
    result.add_argument("--root", default=str(ROOT), help="Raiz do repositório")
    result.add_argument("--summary", help="Resumo em uma linha do trabalho realizado")
    result.add_argument("--change", action="append", default=[], help="Mudança substantiva realizada (repetível)")
    result.add_argument("--decision", action="append", default=[], help="Decisão tomada (repetível)")
    result.add_argument("--validation", action="append", default=[], help="Validação realizada (repetível)")
    result.add_argument("--risk", action="append", default=[], help="Risco, pendência ou limite (repetível)")
    result.add_argument("--next-step", action="append", default=[], help="Próximo passo recomendado (repetível)")
    result.add_argument("--auto", action="store_true", help="Modo fallback factual: não inventa decisões")
    result.add_argument("--timestamp", help="Força timestamp ISO 8601 UTC (para testes)")
    result.add_argument("--input", help="Lê payload JSON completo de arquivo ou '-'")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        root = Path(args.root).resolve()
        if not root.is_dir():
            raise HandoffError(f"raiz inexistente: {root}")
        payload: dict[str, Any] = {}
        if args.input:
            raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text("utf-8")
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise HandoffError("payload JSON deve ser objeto")
        summary = payload.get("summary") or args.summary
        changes = payload.get("changes") or args.change
        decisions = payload.get("decisions") or args.decision
        validations = payload.get("validations") or args.validation
        risks = payload.get("risks") or args.risk
        next_steps = payload.get("next_steps") or args.next_step
        auto = bool(payload.get("auto") or args.auto)
        timestamp = _validated_timestamp(payload.get("timestamp") or args.timestamp or _now())

        with _history_lock(root):
            inventory = build_inventory(root)
            current_fingerprint = inventory_fingerprint(inventory)
            previous_snapshot = load_json(root / SNAPSHOT_RELATIVE, {})
            previous_files = previous_snapshot.get("files", {}) if isinstance(previous_snapshot, dict) else {}
            previous_fingerprint = previous_snapshot.get("fingerprint") if isinstance(previous_snapshot, dict) else None
            delta = inventory_delta(previous_files if isinstance(previous_files, dict) else {}, inventory)
            git = git_state(root)
            entries = load_entries(root / LEDGER_RELATIVE)
            first_run = not entries and not (root / SNAPSHOT_RELATIVE).exists()

            if not summary:
                if not auto:
                    raise HandoffError("encerramento exige --summary (ou use --auto como fallback factual)")
                summary = "Sessão encerrada em modo automático; consulte as alterações registradas."

            entry = {
                "schema_version": SCHEMA_VERSION,
                "session_id": f"session-{sha256_bytes((timestamp + summary + current_fingerprint).encode('utf-8'))[:20]}",
                "recorded_at": timestamp,
                "summary": _text(summary, "summary", required=True),
                "baseline_initialized": first_run,
                "previous_fingerprint": previous_fingerprint,
                "source_fingerprint": current_fingerprint,
                "git": git,
                "file_delta": delta,
                "changes": _strings(changes, "changes"),
                "decisions": _strings(decisions, "decisions"),
                "validations": _strings(validations, "validations"),
                "risks": _strings(risks, "risks"),
                "next_steps": _strings(next_steps, "next_steps"),
            }

            entries.append(entry)
            ledger_data = ("\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in entries) + "\n").encode("utf-8")
            atomic_write(root / LEDGER_RELATIVE, ledger_data)

            new_snapshot = {
                "schema_version": SCHEMA_VERSION,
                "recorded_at": timestamp,
                "fingerprint": current_fingerprint,
                "git": git,
                "files": snapshot_files(inventory),
            }
            atomic_write(root / SNAPSHOT_RELATIVE, canonical_json(new_snapshot) + b"\n")

            history_document = render_history(root, entries, new_snapshot)
            atomic_write(root / HISTORY_RELATIVE, history_document.encode("utf-8"))

            sys.stdout.write(json.dumps({
                "status": "recorded",
                "session_id": entry["session_id"],
                "ledger": LEDGER_RELATIVE.as_posix(),
                "history": HISTORY_RELATIVE.as_posix(),
                "fingerprint": current_fingerprint,
                "delta": _delta_count(delta),
            }, ensure_ascii=False, indent=2) + "\n")
            return 0
    except (HandoffError, OSError, json.JSONDecodeError) as exc:
        sys.stderr.write(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False) + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
