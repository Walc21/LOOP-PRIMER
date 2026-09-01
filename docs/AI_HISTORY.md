# Histórico evolutivo e atualizações de sessão — article-loop

> Gerado por `scripts/ai_history.py`. O histórico Git e os ADRs são reconstruídos; as atualizações de sessão vêm do ledger append-only `docs/ai_sessions.jsonl`.

## Baseline registrado

- Fingerprint das fontes: `790634e49232fc6bf5ef4ed3e0536f1426a4d7c3ab1c36eec14468754572b721`
- Registrado em: `2026-09-01T09:48:32Z`
- Git: branch `master`, HEAD `907af5057315`
- Arquivos relevantes: 151

## Evolução reconstruída do versionamento

| Marco | Intervalo | Commits | Evolução inferida | Áreas tocadas |
|---|---:|---:|---|---|
| M0/M0.5 | 2026-08-12 | 1 | Auditoria de compatibilidade, segurança e fixação da arquitetura canônica. | AGENTS.md, PLANS.md, docs/architecture.md, docs/compatibility.md, docs/decisions.md |
| M0.6 | 2026-08-12 | 1 | Completude de paths e ordem transacional do pipeline. | PLANS.md, docs/architecture.md, docs/decisions.md |
| M1/M1.1 | 2026-08-13 | 1 | Scaffold, catálogo de papéis e contratos condicionais em JSON Schema. | .gitignore, .prime/agent/APPEND_SYSTEM.md, .prime/agent/prompts/.gitkeep, .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/… |
| M2 | 2026-08-13 | 4 | Máquina de estados, event log encadeado, replay e recuperação durável. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/arti… |
| M3 | 2026-08-13 | 5 | Ingestão PDF/ZIP offline, preservação do original e baseline v0000. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/ingestion.py, .prime/ha… |
| sem marco explícito | 2026-08-13 | 1 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | .prime/agent/skills/article-loop/src/article_loop/ingestion.py, .prime/handoffs/03_para_04.md, PLANS.md, control/test_m3_ingestion.py |
| M4 | 2026-08-13 | 3 | Prompts imutáveis, overlays e compilação content-addressed dos 21 papéis. | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/prompts.py, .prime/handoffs/04_para_05.md, PLANS.md, control/fixtu… |
| M5 | 2026-08-13..2026-08-14 | 4 | Blackboard, grafo de impacto, views fechadas e ativação esparsa. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/arti… |
| M6 | 2026-08-14 | 7 | Orquestração RLM hierárquica reentrante por receipts duráveis. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/adapters.py, .prime/age… |
| M7 | 2026-08-14 | 5 | Síntese, merge isolado, challenger write-once e 13 gates locais. | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/gates.py, .prime/agent/skills/article-loop/src/article_loop/synthe… |
| M8 | 2026-08-27 | 1 | Júri externo cego, inversão consistente e meta-revisão. | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/evaluation.py, .prime/handoffs/08_para_09.md, PLANS.md, control/te… |
| M9 | 2026-08-28 | 2 | Diagnóstico determinístico de progresso e refoco reversível. | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/diagnosis.py, .prime/agent/skills/article-loop/src/article_loop/ev… |

### Commits exatos

| Commit | Data | Marco | Assunto | Arquivos principais |
|---|---:|---|---|---|
| `cd508338e` | 2026-08-12 | M0/M0.5 | docs: checkpoint Marco 0 e 0.5 | AGENTS.md, PLANS.md, docs/architecture.md, docs/compatibility.md, docs/decisions.md |
| `e52a76dc0` | 2026-08-12 | M0.6 | docs: checkpoint Marco 0.6 | PLANS.md, docs/architecture.md, docs/decisions.md |
| `cf364b0b4` | 2026-08-13 | M1/M1.1 | feat: checkpoint M1 and M1.1 | .gitignore, .prime/agent/APPEND_SYSTEM.md, .prime/agent/prompts/.gitkeep, .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/… |
| `dcdde49a2` | 2026-08-13 | M2 | feat: add durable state core for M2 | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/state_machine.py, .prime/agent/skills/article-loop/src/article_loo… |
| `3d2120be3` | 2026-08-13 | M2 | fix: complete M2 durable state recovery | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/skills/article-loop/src/article_loop/state_machine.py, .prime/agent/skills… |
| `f2d84a43b` | 2026-08-13 | M2 | fix: harden M2 replay and event commits | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/store.py, .prime/handoffs/02_para_03.md, PLANS.md, control/test_m2_durable_state.py, d… |
| `fce02113e` | 2026-08-13 | M2 | fix: enforce M2 event schema contract | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/store.py, .prime/handoffs/02_para_03.md, PLANS.md, control/test_m2_durable_state.py, d… |
| `5786c542b` | 2026-08-13 | M3 | feat: implement M3 PDF ingestion baseline | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/ingestion.py, .prime/ha… |
| `a8f44959f` | 2026-08-13 | M3 | fix: harden m3 ingestion recovery | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/ingestion.py, .prime/handoffs/03_para_04.md, PLANS.md, README.md, config/gates.yaml |
| `804258504` | 2026-08-13 | M3 | fix: finalize M3 ingestion durability | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/ingestion.py, .prime/handoffs/03_para_04.md, PLANS.md, control/test_m3_ingestion.py, d… |
| `246c93164` | 2026-08-13 | M3 | fix: bind source zip to M3 identity | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/ingestion.py, .prime/handoffs/03_para_04.md, PLANS.md, control/test_m3_ingestion.py, d… |
| `bdc766cc4` | 2026-08-13 | sem marco explícito | fix: preserve rejected source zip provenance | .prime/agent/skills/article-loop/src/article_loop/ingestion.py, .prime/handoffs/03_para_04.md, PLANS.md, control/test_m3_ingestion.py |
| `9c35b37b7` | 2026-08-13 | M3 | Add local environment bootstrap | PLANS.md, README.md, bin/bootstrap-deps.sh, docs/decisions.md |
| `31d71caab` | 2026-08-13 | M4 | feat: implement M4 prompt contracts | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/prompts.py, .prime/handoffs/04_para_05.md, PLANS.md, control/fixtu… |
| `644d85983` | 2026-08-13 | M4 | fix: harden M4 prompt contracts | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/prompts.py, .prime/handoffs/04_para_05.md, PLANS.md, control/fixtu… |
| `de3da679a` | 2026-08-13 | M4 | fix: contain M4 schema paths | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/prompts.py, .prime/handoffs/04_para_05.md, PLANS.md, control/test_… |
| `4fde20a67` | 2026-08-13 | M5 | feat: implement M5 operational planner | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/arti… |
| `a35abecf0` | 2026-08-13 | M5 | fix: harden M5 operational planner | .prime/agent/skills/article-loop/src/article_loop/activation.py, .prime/agent/skills/article-loop/src/article_loop/blackboard.py, .prime/handoffs/05_para_06.md, PLANS.md, control/… |
| `72bec3424` | 2026-08-14 | M5 | fix: restore canonical M5 packet planning | .prime/agent/skills/article-loop/src/article_loop/activation.py, .prime/handoffs/05_para_06.md, PLANS.md, control/test_m5_blackboard_activation.py, docs/decisions.md |
| `d141f8e65` | 2026-08-14 | M5 | fix: preserve M5 cycle-zero critical coverage | .prime/agent/skills/article-loop/src/article_loop/activation.py, .prime/handoffs/05_para_06.md, PLANS.md, control/test_m5_blackboard_activation.py, docs/decisions.md |
| `ec1d8573e` | 2026-08-14 | M6 | feat: implement M6 RLM orchestration | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/adapters.py, .prime/age… |
| `43b1a6d6c` | 2026-08-14 | M6 | fix: harden M6 durable orchestration | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/adapters.py, .prime/age… |
| `17dda2af9` | 2026-08-14 | M6 | fix: close M6 orchestration invariants | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/adapters.py, .prime/agent/skills/article-loop/src/article_loop/orchestrator.py, .prime… |
| `325a47271` | 2026-08-14 | M6 | fix(m6): reconcile frozen receipts and canonical transitions | .prime/agent/skills/article-loop/src/article_loop/orchestrator.py, .prime/handoffs/06_para_07.md, PLANS.md, control/test_m6_orchestration.py |
| `d4e1d141a` | 2026-08-14 | M6 | fix(m6): validate checkpoints and frozen retries | .prime/agent/skills/article-loop/src/article_loop/orchestrator.py, .prime/handoffs/06_para_07.md, PLANS.md, control/test_m6_orchestration.py, docs/decisions.md |
| `d31838d7b` | 2026-08-14 | M6 | fix(m6): close activation plan validation | .prime/agent/skills/article-loop/src/article_loop/orchestrator.py, .prime/handoffs/06_para_07.md, PLANS.md, control/test_m6_orchestration.py, docs/decisions.md |
| `f5ec8ae58` | 2026-08-14 | M6 | fix(m6): accept impact-only W53 checkpoints | .prime/agent/skills/article-loop/src/article_loop/orchestrator.py, .prime/handoffs/06_para_07.md, PLANS.md, control/test_m6_orchestration.py, docs/decisions.md |
| `6f9e8b294` | 2026-08-14 | M7 | feat(m7): add local synthesis merge and gates | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/gates.py, .prime/agent/skills/article-loop/src/article_loop/synthe… |
| `e619f8616` | 2026-08-14 | M7 | fix(m7): harden synthesis manifests and gates | .prime/agent/skills/article-loop/src/article_loop/gates.py, .prime/agent/skills/article-loop/src/article_loop/synthesis.py, .prime/handoffs/07_para_08.md, PLANS.md, config/schemas… |
| `39d2e5a3d` | 2026-08-14 | M7 | fix(m7): close synthesis and gate integrity gaps | .prime/agent/skills/article-loop/src/article_loop/gates.py, .prime/agent/skills/article-loop/src/article_loop/synthesis.py, .prime/handoffs/07_para_08.md, PLANS.md, control/test_m… |
| `a571d4a16` | 2026-08-14 | M7 | fix(m7): enforce canonical receipts and gates | .prime/agent/skills/article-loop/src/article_loop/gates.py, .prime/agent/skills/article-loop/src/article_loop/synthesis.py, 07_para_08.md, PLANS.md, config/gates.yaml, config/sche… |
| `eec32aa19` | 2026-08-14 | M7 | fix(m7): close final gate and publication gaps | .prime/agent/skills/article-loop/src/article_loop/gates.py, .prime/agent/skills/article-loop/src/article_loop/synthesis.py, .prime/handoffs/07_para_08.md, 07_para_08.md, PLANS.md,… |
| `f8264d61a` | 2026-08-27 | M8 | feat(m8): implement blind external jury evaluation and meta-review | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/evaluation.py, .prime/handoffs/08_para_09.md, PLANS.md, control/te… |
| `765aac3e4` | 2026-08-28 | M9 | feat(m9): implement diagnosis and harden evaluation | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/diagnosis.py, .prime/agent/skills/article-loop/src/article_loop/ev… |
| `907af5057` | 2026-08-28 | M9 | fix(m9): recompute published diagnosis semantics | .prime/agent/skills/article-loop/src/article_loop/diagnosis.py, .prime/handoffs/08_para_09.md, .prime/handoffs/09_para_10.md, PLANS.md, control/test_m9_diagnosis.py, docs/decision… |

## Decisões arquiteturais

- ADR-001 — O repositório possui estado durável próprio
- ADR-002 — Topologia lógica 1 + 5 + 15 e profundidade RLM 2
- ADR-003 — Mensagem curta, arquivo canônico
- ADR-004 — Júri cego separado de autoria e promoção
- ADR-005 — Gates determinísticos locais antes de autonomia
- ADR-006 — Sem chamadas pagas, dependências ou runtime nesta fase
- ADR-007 — Arquitetura canônica dos Prompts 01–13
- ADR-008 — Ordem transacional do pipeline
- ADR-009 — Contratos declarativos e validação local do Marco 1
- ADR-010 — Contratos condicionais antes do estado durável
- ADR-011 — Log encadeado e snapshot derivado para o estado durável
- ADR-012 — Recuperação conservadora e identificadores de execução seguros
- ADR-013 — Replay semântico e commit transacional do event log
- ADR-014 — Validação estrutural integral do evento antes de commit e no replay
- ADR-015 — Ingestão M3 conservadora, offline e versionada
- ADR-016 — Correção final de integridade e recuperação da ingestão M3
- ADR-017 — Limites de escrita e ordem de evidência da ingestão M3
- ADR-018 — Identidade completa de `source.zip` na execução M3
- ADR-019 — Bootstrap portátil limitado ao ambiente local de ingestão
- ADR-020 — Prompts M4 imutáveis, content-addressed e compostos localmente
- ADR-021 — Blackboard append-only e planejamento determinístico de M5
- ADR-022 — Orquestração RLM por receipts duráveis no M6
- ADR-023 — M7: síntese congelada e challenger write-once
- ADR-024 — M8: Júri Externo Cego, Inversão Consistente e Meta-Review
- ADR-025 — M9: Detecção Determinística de Estagnação, Diagnóstico Canônico e Refoco Reversível
- ADR-026 — Handoff compacto e histórico de sessões para agentes de IA

## Atualizações de sessão

### 2026-09-01T09:19:46Z — Implementado o handoff automático e compacto para novas sessões de IA, com contexto atual content-addressed, histórico evolutivo e protocolo obrigatório de início e encerramento.

- Session ID: `session-35ff672e405b8ae45f46`
- Fingerprint final: `7342646896943b59286c34a66b5d4c09dae9770e0d829e0a9fd659f9a1ea9aa4`
- Git final: `907af5057315`; status relevante: 12 item(ns)
- Delta factual: 0 adicionados, 0 modificados, 0 removidos
- Esta sessão inicializou o primeiro baseline; a evolução anterior é reconstruída do Git/ADRs, não tratada como adição de todos os arquivos.

**Mudanças**

- Analisados e conectados 151 arquivos relevantes do repositório, o histórico de 35 commits, 26 ADRs, os marcos M0–M9, 21 papéis, 20 schemas e 303 testes detectados por AST.
- Adicionados scripts/ai_context.py, scripts/ai_history.py e scripts/ai_handoff_common.py com publicação atômica, idempotência, inventário completo e ausência de rede/modelos/dependências novas.
- Adicionados gatilhos auto-descobertos em AGENTS.md, CLAUDE.md e .prime/agent/APPEND_SYSTEM.md; o README aponta para o contexto atual.
- Adicionado control/test_ai_handoff.py e documentados ADR-026, arquitetura auxiliar e progresso em PLANS.md.

**Decisões**

- O fingerprint exclui os próprios artefatos gerados, ambientes, caches e conteúdo sensível; inclui por hash o estado/runtime científico ignorado pelo Git, sem incorporar seu conteúdo.
- O histórico combina evolução factual reconstruída de Git/ADRs com um resumo semântico estruturado obrigatório ao fim de cada sessão.
- O registrador de histórico nunca roda no início; após o encerramento, o contexto é regenerado para incorporar o novo baseline.

**Validações**

- python3 -m py_compile nos três utilitários e no novo teste: aprovado.
- python3 -m unittest -q control.test_ai_handoff control.test_contracts: 56 testes aprovados.
- Segunda geração de AI_CONTEXT.md e --check: idempotência aprovada antes do encerramento.
- Regressão integral iniciou 303 testes e encerrou com 12 falhas e 181 erros ambientais, todos convergindo para ausência do executável pdflatex; nenhuma dependência foi instalada.
- git diff --check: aprovado.

**Riscos/limites**

- pdflatex não está instalado; por isso a regressão que depende da ingestão M3 não pôde ser validada integralmente nesta máquina.
- Nenhum arquivo pode obrigar um cliente de IA que ignore deliberadamente instruções auto-descobertas; AGENTS.md, CLAUDE.md e APPEND_SYSTEM.md cobrem os runtimes previstos pelo projeto.
- Mudanças de bytes são detectadas automaticamente, mas intenção e decisões semânticas ainda exigem um resumo honesto da IA no encerramento.

**Próximos passos**

- M10 continua pendente e não foi iniciado; implementar política de compensação, decisão canônica e finalizador somente em sessão autorizada e separada.

### 2026-09-01T09:20:21Z — Corrigida a incorporação do histórico no contexto para não repetir a linha de cabeçalho da tabela de marcos.

- Session ID: `session-349098e294a13203aa59`
- Fingerprint final: `790634e49232fc6bf5ef4ed3e0536f1426a4d7c3ab1c36eec14468754572b721`
- Git final: `907af5057315`; status relevante: 12 item(ns)
- Delta factual: 0 adicionados, 2 modificados, 0 removidos

**Mudanças**

- scripts/ai_context.py agora seleciona somente linhas de marcos M0–M13, excluindo o cabeçalho genérico da tabela.
- control/test_ai_handoff.py ganhou regressão que proíbe o cabeçalho duplicado.

**Decisões**

- O ledger anterior permaneceu append-only; a correção pós-encerramento foi registrada em nova entrada em vez de reescrever a sessão anterior.

**Validações**

- python3 -m py_compile scripts/ai_context.py control/test_ai_handoff.py: aprovado.
- python3 -m unittest -q control.test_ai_handoff control.test_contracts: 56 testes aprovados.
- git diff --check: aprovado.

**Riscos/limites**

- Permanece o bloqueio ambiental de pdflatex já registrado na sessão anterior.

**Próximos passos**

- Regenerar AI_CONTEXT.md e confirmar baseline, ausência de delta e idempotência.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `control/test_ai_handoff.py` | `97665823ebd9` | `b660fd15651b` |
| modified | `scripts/ai_context.py` | `2445867b9d90` | `4009029f532f` |

### 2026-09-01T09:48:32Z — Reexecutada com sucesso a regressão integral após a instalação local do pdflatex pelo usuário; o bloqueio ambiental anterior foi resolvido.

- Session ID: `session-2e596a2acf9f4bb2beb3`
- Fingerprint final: `790634e49232fc6bf5ef4ed3e0536f1426a4d7c3ab1c36eec14468754572b721`
- Git final: `907af5057315`; status relevante: 12 item(ns)
- Delta factual: 0 adicionados, 0 modificados, 0 removidos

**Mudanças**

- Nenhum arquivo-fonte foi alterado nesta sessão; foi realizada somente validação do ambiente e da suíte completa.

**Decisões**

- A instalação do pdflatex é agora suficiente para atravessar a ingestão M3 e validar a regressão M0–M9 nesta máquina.

**Validações**

- command -v pdflatex: /usr/bin/pdflatex; pdfTeX 3.141592653-2.6-1.40.28, TeX Live 2025/Debian.
- python3 -m unittest discover -s control -p 'test_*.py' -q: 303 testes executados em 244.057s, resultado OK, código de saída 0.

**Riscos/limites**

- Permaneceu somente o aviso esperado da fixture negativa M3: Duplicate name: a.tex; não houve falha ou erro.

**Próximos passos**

- M10 permanece pendente; a suíte integral atual está verde para servir de baseline antes de qualquer implementação futura.
