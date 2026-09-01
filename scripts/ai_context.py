#!/usr/bin/env python3
"""Gera um documento único, compacto e atual para iniciar uma sessão de IA."""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from ai_handoff_common import (
    HandoffError,
    atomic_write,
    build_inventory,
    git_state,
    inventory_delta,
    inventory_fingerprint,
    load_json,
    markdown_cell,
    run_local,
    sha256_bytes,
)
from ai_history import LEDGER_RELATIVE, SNAPSHOT_RELATIVE, load_entries


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE = Path("AI_CONTEXT.md")
HISTORY_RELATIVE = Path("docs/AI_HISTORY.md")

MODULE_PURPOSES = {
    "state_machine.py": "grafo fechado dos 16 estados e validação de transições",
    "store.py": "event log JSONL encadeado, snapshots derivados, locks e replay",
    "ingestion.py": "congelamento de PDF/ZIP, derivados e publicação do baseline v0000",
    "prompts.py": "registro content-addressed, overlays, composição e validação de prompts",
    "blackboard.py": "ledgers append-only de claims/issues e grafo conservador de impacto",
    "activation.py": "planejador puro RUN/CHECK/SHIFT/FREEZE e views de contexto fechado",
    "adapters.py": "fronteira PrimeRLMAdapter/FakeRLMAdapter e handles documentados",
    "orchestrator.py": "árvore M00→Sxx→Wxx reentrante, journal e receipts M6",
    "synthesis.py": "congelamento de propostas, merge isolado e challenger write-once",
    "gates.py": "13 verificadores locais, evidência matemática e GateReport canônico",
    "evaluation.py": "comparação A/B cega, júri, meta-review e publicação M8",
    "diagnosis.py": "série histórica validada, 7 classificações e publicação M9",
    "refocus.py": "planos/overlays reversíveis sob CAS para plateau/oscilação",
    "__init__.py": "fachada pública assíncrona e exportações do pacote article_loop",
}


def _read(root: Path, relative: str, default: str = "") -> str:
    path = root / relative
    if not path.exists():
        return default
    if path.is_symlink() or not path.is_file():
        raise HandoffError(f"documento esperado não é arquivo regular: {relative}")
    return path.read_text("utf-8")


def _section(text: str, heading: str, *, level: int = 2) -> str:
    marker = "#" * level + " " + heading
    start = text.find(marker)
    if start < 0:
        return ""
    rest = text[start:]
    match = re.search(rf"\n#{{1,{level}}}\s+", rest[len(marker) :])
    end = len(marker) + match.start() if match else len(rest)
    return rest[:end].strip()


def _milestones(plans: str) -> list[dict[str, str]]:
    result = []
    for line in plans.splitlines():
        match = re.match(r"^\|\s*(M\d+(?:\.\d+)?)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|$", line)
        if match:
            result.append({"id": match.group(1).strip(), "delivery": match.group(2).strip(), "status": match.group(3).strip(), "acceptance": match.group(4).strip()})
    return result


def _yaml_list(text: str, key: str) -> list[str]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line == f"{key}:":
            values = []
            for following in lines[index + 1 :]:
                match = re.match(r"^  -\s+(.+)$", following)
                if match:
                    values.append(match.group(1).strip())
                elif following.strip() and not following.startswith(" "):
                    break
            return values
    return []


def _yaml_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.*?)\s*$", text, re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip().strip('"\'')
    return None if value in {"", "null", "~"} else value


def _roles(root: Path) -> list[dict[str, Any]]:
    result = []
    for path in sorted((root / "config/roles").glob("*.yaml")) if (root / "config/roles").is_dir() else []:
        text = path.read_text("utf-8")
        result.append({key: _yaml_scalar(text, key) for key in ("id", "name", "kind", "department", "rlm_depth", "parent_id", "responsibility")})
    return sorted(result, key=lambda item: str(item.get("id")))


def _schemas(root: Path) -> list[dict[str, Any]]:
    result = []
    directory = root / "config/schemas"
    if not directory.is_dir():
        return result
    for path in sorted(directory.glob("*.json")):
        try:
            value = json.loads(path.read_text("utf-8"))
        except json.JSONDecodeError:
            result.append({"name": path.name, "title": "JSON inválido", "required": [], "properties": []})
            continue
        result.append({
            "name": path.name,
            "title": value.get("title") or value.get("$id") or "sem título",
            "required": value.get("required", []),
            "properties": list(value.get("properties", {})),
        })
    return result


def _python_api(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text("utf-8"))
    except (OSError, SyntaxError) as exc:
        return [f"erro de parsing: {exc}"]
    result = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            methods = [child.name for child in node.body if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and not child.name.startswith("_")]
            result.append(f"class {node.name}" + (f" [{', '.join(methods)}]" if methods else ""))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            result.append(("async " if isinstance(node, ast.AsyncFunctionDef) else "") + node.name + "()")
    return result


def _tests(root: Path) -> list[dict[str, Any]]:
    result = []
    directory = root / "control"
    if not directory.is_dir():
        return result
    for path in sorted(directory.glob("test_*.py")):
        try:
            tree = ast.parse(path.read_text("utf-8"))
        except SyntaxError:
            result.append({"name": path.name, "count": 0, "topics": ["Python inválido"]})
            continue
        names = [node.name.removeprefix("test_").replace("_", " ") for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")]
        result.append({"name": path.name, "count": len(names), "topics": names[:8]})
    return result


def _history_digest(root: Path, history_text: str) -> list[str]:
    lines = [f"- Fonte lida: `docs/AI_HISTORY.md` ({len(history_text.encode('utf-8'))} bytes; SHA-256 `{sha256_bytes(history_text.encode('utf-8'))[:16]}`)."]
    if not history_text:
        lines.append("- Histórico ainda não existe; o encerramento desta sessão deve criá-lo com `scripts/ai_history.py`.")
        return lines
    evolution = history_text.split("## Atualizações de sessão", 1)[0]
    milestone_rows = [line for line in evolution.splitlines() if re.match(r"^\|\s*M\d", line)]
    if milestone_rows:
        lines.extend(["", "| Marco histórico | Intervalo | Commits | Evolução | Áreas |", "|---|---:|---:|---|---|"])
        lines.extend(milestone_rows)
    entries = load_entries(root / LEDGER_RELATIVE)
    lines.extend(["", f"- Sessões estruturadas registradas: {len(entries)}."])
    if entries:
        lines.append("- Índice completo: " + "; ".join(f"{entry.get('recorded_at')} — {entry.get('summary')}" for entry in entries) + ".")
        lines.extend(["", "Detalhe das três sessões mais recentes:"])
        for entry in entries[-3:]:
            lines.append(f"- `{entry.get('session_id')}` — {entry.get('summary')}")
            for key, label in (("changes", "mudanças"), ("decisions", "decisões"), ("validations", "validações"), ("risks", "riscos"), ("next_steps", "próximos")):
                values = entry.get(key, [])
                if values:
                    lines.append(f"  - {label}: " + "; ".join(values))
    return lines


def _diff_preview(root: Path, snapshot: Mapping[str, Any], limit: int) -> str:
    git = git_state(root)
    if not git.get("available"):
        return "Git indisponível; use o delta content-addressed acima."
    pieces = []
    previous_head = snapshot.get("git", {}).get("head") if isinstance(snapshot.get("git"), dict) else None
    current_head = git.get("head")
    if isinstance(previous_head, str) and re.fullmatch(r"[0-9a-f]{40}", previous_head) and previous_head != current_head:
        committed = run_local(["git", "diff", "--no-ext-diff", "--unified=1", f"{previous_head}..{current_head}", "--"], cwd=root, timeout=30)
        if committed.stdout:
            pieces.append("# Commits desde o último encerramento\n" + committed.stdout)
    working = run_local(["git", "diff", "--no-ext-diff", "--unified=1", "HEAD", "--"], cwd=root, timeout=30)
    if working.stdout:
        pieces.append("# Alterações não commitadas\n" + working.stdout)
    text = "\n".join(pieces)
    if not text:
        return "Nenhuma alteração Git detectada em relação ao encerramento registrado."
    if len(text.encode("utf-8")) > limit:
        return text[:limit] + f"\n\n... [diff truncado para respeitar o limite de {limit} bytes]"
    return text


def render_context(root: Path, *, diff_limit: int = 16384) -> str:
    root = root.resolve()
    readme = _read(root, "README.md")
    agents = _read(root, "AGENTS.md")
    plans = _read(root, "PLANS.md")
    decisions = _read(root, "docs/decisions.md")
    system_yaml = _read(root, "config/system.yaml")
    gates_yaml = _read(root, "config/gates.yaml")
    budgets_yaml = _read(root, "config/budgets.yaml")
    history_text = _read(root, "docs/AI_HISTORY.md")
    snapshot = load_json(root / SNAPSHOT_RELATIVE, default={})
    previous_inventory = snapshot.get("files", {}) if isinstance(snapshot.get("files"), dict) else {}
    current_inventory = build_inventory(root)
    delta = inventory_delta(previous_inventory, current_inventory)

    sections = ["# AI_CONTEXT — Contexto Consolidado para Sessões de IA", ""]
    sections.append("> Documento gerado deterministicamente por `scripts/ai_context.py`.\n> Fonte única de verdade consolidada para evitar leitura fragmentada no início da sessão.")
    sections.append("")

    sections.append("## 1. Missão e Arquitetura Executiva")
    sections.append(_section(readme, "Missão", level=2) or _section(readme, "Arquitetura", level=2) or "Refinamento iterativo e auditável de artigos científicos com isolamento estrito.")
    sections.append("")

    sections.append("## 2. Guardrails Críticos e Comportamentais (AGENTS.md)")
    sections.append(agents or "Siga estritamente as regras de isolamento, contratos imutáveis e execução local.")
    sections.append("")

    sections.append("## 3. Estado Atual dos Marcos (PLANS.md)")
    milestones = _milestones(plans)
    if milestones:
        sections.append("| Marco | Entrega | Estado | Critério de Aceitação |")
        sections.append("|---|---|---|---|")
        for item in milestones:
            sections.append(f"| {markdown_cell(item['id'])} | {markdown_cell(item['delivery'])} | {markdown_cell(item['status'])} | {markdown_cell(item['acceptance'])} |")
    else:
        sections.append("Tabela de marcos não encontrada em `PLANS.md`.")
    sections.append("")

    sections.append("## 4. Contratos do Sistema (config/system.yaml, gates, budgets)")
    states = _yaml_list(system_yaml, "states")
    actions = _yaml_list(system_yaml, "actions")
    sections.append(f"- **Estados canônicos ({len(states)}):** {', '.join(states) if states else 'não listados'}")
    sections.append(f"- **Ações canônicas ({len(actions)}):** {', '.join(actions) if actions else 'não listadas'}")
    sections.append(f"- **Gates ({gates_yaml.count('gate_id:')}):** configurados em `config/gates.yaml`.")
    sections.append(f"- **Orçamentos:** configurados em `config/budgets.yaml`.")
    sections.append("")

    sections.append("## 5. Catálogo de Papéis Especializados (config/roles)")
    roles = _roles(root)
    if roles:
        sections.append("| ID | Nome | Tipo | Depto | Depth | Pai | Responsabilidade |")
        sections.append("|---|---|---|---|---:|---|---|")
        for r in roles:
            sections.append(f"| {markdown_cell(r.get('id'))} | {markdown_cell(r.get('name'))} | {markdown_cell(r.get('kind'))} | {markdown_cell(r.get('department'))} | {r.get('rlm_depth') or '-'} | {markdown_cell(r.get('parent_id'))} | {markdown_cell(r.get('responsibility'))} |")
    sections.append("")

    sections.append("## 6. Schemas e Contratos Estruturados (config/schemas)")
    schemas = _schemas(root)
    if schemas:
        sections.append("| Schema | Título | Campos Obrigatórios |")
        sections.append("|---|---|---|")
        for s in schemas:
            sections.append(f"| `{s['name']}` | {markdown_cell(s['title'])} | `{', '.join(s['required'][:6]) + ('...' if len(s['required']) > 6 else '')}` |")
    sections.append("")

    sections.append("## 7. Módulos Core do Pacote `article_loop` (.prime/.../src/article_loop)")
    src_dir = root / ".prime/agent/skills/article-loop/src/article_loop"
    if src_dir.is_dir():
        sections.append("| Módulo | Propósito Canônico | Símbolos Públicos Exportados |")
        sections.append("|---|---|---|")
        for path in sorted(src_dir.glob("*.py")):
            purpose = MODULE_PURPOSES.get(path.name, "módulo do sistema")
            api = _python_api(path)
            sections.append(f"| `{path.name}` | {purpose} | `{', '.join(api[:5]) + ('...' if len(api) > 5 else '')}` |")
    sections.append("")

    sections.append("## 8. Cobertura da Suíte de Testes (control/)")
    tests = _tests(root)
    if tests:
        sections.append("| Arquivo de Teste | Quantidade de Casos | Tópicos Cobertos |")
        sections.append("|---|---:|---|")
        for t in tests:
            sections.append(f"| `{t['name']}` | {t['count']} | {', '.join(t['topics'][:4]) + ('...' if len(t['topics']) > 4 else '')} |")
    sections.append("")

    sections.append("## 9. Histórico de Sessões Anteriores (docs/AI_HISTORY.md)")
    sections.extend(_history_digest(root, history_text))
    sections.append("")

    sections.append("## 10. Delta e Integridade do Workspace")
    sections.append(f"- **Fingerprint atual do inventário:** `{inventory_fingerprint(current_inventory)}`")
    sections.append(f"- **Arquivos adicionados desde o último fechamento:** {len(delta['added'])}")
    sections.append(f"- **Arquivos modificados:** {len(delta['modified'])}")
    sections.append(f"- **Arquivos deletados:** {len(delta['deleted'])}")
    sections.append("")
    sections.append("### Prévia de Diferenças (Git diff)")
    sections.append("```diff")
    sections.append(_diff_preview(root, snapshot, diff_limit))
    sections.append("```")
    sections.append("")

    return "\n".join(sections)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera AI_CONTEXT.md determinístico.")
    parser.add_argument("--root", default=".", help="Raiz do repositório")
    parser.add_argument("--check", action="store_true", help="Verifica se AI_CONTEXT.md está atualizado sem sobrescrever")
    parser.add_argument("--diff-limit", type=int, default=16384, help="Limite em bytes do preview de diff")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    content = render_context(root, diff_limit=args.diff_limit)
    target = root / OUTPUT_RELATIVE

    if args.check:
        if not target.exists():
            sys.stderr.write("AI_CONTEXT.md não existe.\n")
            return 1
        existing = target.read_text("utf-8")
        if existing != content:
            sys.stderr.write("AI_CONTEXT.md desatualizado em relação ao estado atual.\n")
            return 1
        print(json.dumps({"status": "up_to_date", "fingerprint": sha256_bytes(content.encode("utf-8"))}))
        return 0

    atomic_write(target, content.encode("utf-8"))
    print(json.dumps({
        "status": "updated",
        "output": str(OUTPUT_RELATIVE),
        "bytes": len(content.encode("utf-8")),
        "estimated_tokens": len(content) // 4,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
