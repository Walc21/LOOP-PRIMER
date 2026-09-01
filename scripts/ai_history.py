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
    groups: dict[str, list[dict[str, Any]]] = {}
    for commit in commits:
        groups.setdefault(infer_milestone(commit["subject"]), []).append(commit)

    lines = [
        "# Histórico evolutivo e atualizações de sessão — article-loop",
        "",
        "> Gerado por `scripts/ai_history.py`. O histórico Git e os ADRs são reconstruídos; as atualizações de sessão vêm do ledger append-only `docs/ai_sessions.jsonl`.",
        "",
        "## Baseline registrado",
        "",
        f"- Fingerprint das fontes: `{snapshot.get('fingerprint', 'indisponível')}`",
        f"- Registrado em: `{snapshot.get('recorded_at', 'indisponível')}`",
        f"- Git: branch `{snapshot.get('git', {}).get('branch') or '-'}`, HEAD `{(snapshot.get('git', {}).get('head') or '-')[:12]}`",
        f"- Arquivos relevantes: {len(snapshot.get('files', {}))}",
        "",
        "## Evolução reconstruída do versionamento",
        "",
        "| Marco | Intervalo | Commits | Evolução inferida | Áreas tocadas |",
        "|---|---:|---:|---|---|",
    ]
    if groups:
        for milestone, items in groups.items():
            files = sorted({path for item in items for path in item["files"]})
            purpose = MILESTONE_PURPOSES.get(milestone, "Inferida dos assuntos dos commits; consulte a tabela exata abaixo.")
            interval = items[0]["date"] if items[0]["date"] == items[-1]["date"] else f"{items[0]['date']}..{items[-1]['date']}"
            lines.append(f"| {markdown_cell(milestone)} | {interval} | {len(items)} | {markdown_cell(purpose, 220)} | {markdown_cell(', '.join(files[:7]), 180)} |")
    else:
        lines.append("| - | - | 0 | Repositório Git indisponível nesta cópia. | - |")

    lines.extend([
        "",
        "### Commits exatos",
        "",
        "| Commit | Data | Marco | Assunto | Arquivos principais |",
        "|---|---:|---|---|---|",
    ])
    for commit in commits:
        lines.append(
            f"| `{commit['hash'][:9]}` | {commit['date']} | {infer_milestone(commit['subject'])} | "
            f"{markdown_cell(commit['subject'], 180)} | {markdown_cell(', '.join(commit['files'][:6]), 180)} |"
        )
    if not commits:
        lines.append("| - | - | - | Sem commits disponíveis. | - |")

    lines.extend(["", "## Decisões arquiteturais", ""])
    adrs = _adr_headings(root)
    if adrs:
        lines.extend(f"- {heading}" for heading in adrs)
    else:
        lines.append("- Nenhuma ADR encontrada em `docs/decisions.md`.")

    lines.extend(["", "## Atualizações de sessão", ""])
    if not entries:
        lines.append("Nenhuma sessão estruturada foi registrada ainda.")
    for entry in entries:
        lines.extend([
            f"### {entry.get('recorded_at', '-')} — {entry.get('summary', 'sem resumo')}",
            "",
            f"- Session ID: `{entry.get('session_id', '-')}`",
            f"- Fingerprint final: `{entry.get('source_fingerprint', '-')}`",
            f"- Git final: `{str(entry.get('git', {}).get('head') or '-')[:12]}`; status relevante: {len(entry.get('git', {}).get('status', []))} item(ns)",
            f"- Delta factual: {_delta_summary(entry.get('file_delta', {}))}",
        ])
        if entry.get("baseline_initialized"):
            lines.append("- Esta sessão inicializou o primeiro baseline; a evolução anterior é reconstruída do Git/ADRs, não tratada como adição de todos os arquivos.")
        for title, key in (
            ("Mudanças", "changes"),
            ("Decisões", "decisions"),
            ("Validações", "validations"),
            ("Riscos/limites", "risks"),
            ("Próximos passos", "next_steps"),
        ):
            values = entry.get(key, [])
            if values:
                lines.extend(["", f"**{title}**", ""])
                lines.extend(f"- {value}" for value in values)
        delta = entry.get("file_delta", {})
        if _delta_count(delta):
            lines.extend(["", "**Arquivos detectados**", "", "| Tipo | Caminho | SHA anterior | SHA final |", "|---|---|---|---|"])
            for kind in ("added", "modified", "deleted"):
                for item in delta.get(kind, []):
                    before = (item.get("before") or "-")[:12]
                    after = (item.get("after") or "-")[:12]
                    lines.append(f"| {kind} | `{markdown_cell(item.get('path'), 180)}` | `{before}` | `{after}` |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _entry_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if args.entry_file:
        payload = load_json(Path(args.entry_file).resolve(), None)
        if not isinstance(payload, dict):
            raise HandoffError("--entry-file deve conter um objeto JSON")
    if args.stdin_json:
        try:
            stdin_value = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            raise HandoffError(f"JSON de stdin inválido: {exc}") from exc
        if not isinstance(stdin_value, dict):
            raise HandoffError("stdin deve conter um objeto JSON")
        payload.update(stdin_value)
    if args.summary is not None:
        payload["summary"] = args.summary
    for key, value in (
        ("changes", args.change),
        ("decisions", args.decision),
        ("validations", args.validation),
        ("risks", args.risk),
        ("next_steps", args.next_step),
    ):
        if value:
            payload.setdefault(key, [])
            payload[key].extend(value)
    return payload


def update_history(root: Path, payload: Mapping[str, Any] | None, *, bootstrap_only: bool = False, automatic: bool = False, timestamp: str | None = None, session_id: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise HandoffError(f"raiz inexistente: {root}")
    inventory = build_inventory(root)
    fingerprint = inventory_fingerprint(inventory)
    git = git_state(root)

    with _history_lock(root):
        snapshot_path = root / SNAPSHOT_RELATIVE
        old_snapshot = load_json(snapshot_path, {})
        if old_snapshot and not isinstance(old_snapshot.get("files"), dict):
            raise HandoffError("snapshot anterior não contém mapa de arquivos válido")
        initial_baseline = not bool(old_snapshot)
        delta = ({"added": [], "modified": [], "deleted": []} if initial_baseline else inventory_delta(old_snapshot.get("files", {}), inventory))
        entries = load_entries(root / LEDGER_RELATIVE)
        recorded_at = _validated_timestamp(timestamp) if timestamp else _now()
        created = False

        if not bootstrap_only:
            data = dict(payload or {})
            if automatic and not data.get("summary"):
                data["summary"] = f"Registro factual automático: {_delta_summary(delta)}."
                data["changes"] = [f"{item['path']} ({kind})" for kind in ("added", "modified", "deleted") for item in delta[kind]]
            summary = _text(data.get("summary"), "summary", required=True)
            normalized = {
                "summary": summary,
                "changes": _strings(data.get("changes", []), "changes"),
                "decisions": _strings(data.get("decisions", []), "decisions"),
                "validations": _strings(data.get("validations", []), "validations"),
                "risks": _strings(data.get("risks", []), "risks"),
                "next_steps": _strings(data.get("next_steps", []), "next_steps"),
            }
            identity_body = {
                "schema_version": SCHEMA_VERSION,
                "source_fingerprint": fingerprint,
                "previous_fingerprint": old_snapshot.get("fingerprint"),
                **normalized,
            }
            identifier = session_id or "session-" + sha256_bytes(canonical_json(identity_body))[:20]
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{5,127}", identifier):
                raise HandoffError("session_id deve ser identificador simples de 6 a 128 caracteres")
            existing = next((entry for entry in entries if entry["session_id"] == identifier), None)
            if existing is None:
                entry = {
                    "schema_version": SCHEMA_VERSION,
                    "session_id": identifier,
                    "recorded_at": recorded_at,
                    "source_fingerprint": fingerprint,
                    "previous_fingerprint": old_snapshot.get("fingerprint"),
                    "baseline_initialized": initial_baseline,
                    "git": git,
                    "file_delta": delta,
                    **normalized,
                }
                ledger_path = root / LEDGER_RELATIVE
                prior = ledger_path.read_bytes() if ledger_path.exists() else b""
                if prior and not prior.endswith(b"\n"):
                    raise HandoffError("ledger anterior está truncado")
                atomic_write(ledger_path, prior + canonical_json(entry) + b"\n")
                entries.append(entry)
                created = True
            else:
                if existing.get("source_fingerprint") != fingerprint or existing.get("summary") != summary:
                    raise HandoffError("session_id já existe com conteúdo diferente")
                recorded_at = str(existing.get("recorded_at", recorded_at))
                identifier = existing["session_id"]
        else:
            identifier = old_snapshot.get("session_id")

        snapshot = {
            "schema_version": SCHEMA_VERSION,
            "recorded_at": recorded_at,
            "session_id": identifier,
            "fingerprint": fingerprint,
            "git": git,
            "files": snapshot_files(inventory),
        }
        if bootstrap_only or created or old_snapshot.get("fingerprint") != fingerprint:
            atomic_write(snapshot_path, json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n")
        else:
            snapshot = old_snapshot
        history = render_history(root, entries, snapshot)
        history_changed = atomic_write(root / HISTORY_RELATIVE, history.encode("utf-8"))
    return {
        "status": "recorded" if created else ("bootstrapped" if bootstrap_only else "idempotent"),
        "session_id": identifier,
        "fingerprint": fingerprint,
        "delta": {key: len(delta[key]) for key in delta},
        "history": HISTORY_RELATIVE.as_posix(),
        "history_changed": history_changed,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Registra uma sessão e atualiza o histórico evolutivo para IAs.")
    result.add_argument("--root", default=str(ROOT), help="Raiz do repositório")
    result.add_argument("--summary", help="Resumo substantivo do resultado da sessão")
    result.add_argument("--change", action="append", default=[], help="Mudança realizada; pode repetir")
    result.add_argument("--decision", action="append", default=[], help="Decisão tomada; pode repetir")
    result.add_argument("--validation", action="append", default=[], help="Validação e resultado; pode repetir")
    result.add_argument("--risk", action="append", default=[], help="Risco ou limite remanescente; pode repetir")
    result.add_argument("--next-step", action="append", default=[], help="Próximo passo; pode repetir")
    result.add_argument("--entry-file", help="Objeto JSON com summary e listas estruturadas")
    result.add_argument("--stdin-json", action="store_true", help="Lê o objeto de atualização do stdin")
    result.add_argument("--session-id", help="ID idempotente opcional")
    result.add_argument("--timestamp", help="Timestamp ISO 8601 opcional, útil em importação/teste")
    result.add_argument("--auto", action="store_true", help="Fallback factual; não infere decisões")
    result.add_argument("--bootstrap-only", action="store_true", help="Inicializa baseline sem criar entrada de sessão")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.bootstrap_only and any((args.summary, args.change, args.decision, args.validation, args.risk, args.next_step, args.entry_file, args.stdin_json, args.auto)):
            raise HandoffError("--bootstrap-only não aceita conteúdo de sessão")
        payload = None if args.bootstrap_only else _entry_payload(args)
        if not args.bootstrap_only and not args.auto and not payload.get("summary"):
            raise HandoffError("forneça --summary/--entry-file/--stdin-json; use --auto apenas como fallback factual")
        result = update_history(
            Path(args.root),
            payload,
            bootstrap_only=args.bootstrap_only,
            automatic=args.auto,
            timestamp=args.timestamp,
            session_id=args.session_id,
        )
    except HandoffError as exc:
        sys.stderr.write(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False) + "\n")
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
