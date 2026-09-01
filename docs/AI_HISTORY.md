# Histórico evolutivo e atualizações de sessão — article-loop

> Gerado por `scripts/ai_history.py`. O histórico Git e os ADRs são reconstruídos; as atualizações de sessão vêm do ledger append-only `docs/ai_sessions.jsonl`.

## Baseline registrado

- Fingerprint das fontes: `6f2971f08a5feaa6c15b713cedfa0dc50a255fd5378145820f6c83a17f5bd51c`
- Registrado em: `2026-09-01T12:40:48Z`
- Git: branch `main`, HEAD `ff09de79c972`
- Arquivos relevantes: 158

## Evolução reconstruída do versionamento

| Marco | Intervalo | Commits | Evolução inferida | Áreas tocadas |
|---|---:|---:|---|---|
| M0/M0.5 | 2026-08-12 | 1 | Auditoria de compatibilidade, segurança e fixação da arquitetura canônica. | AGENTS.md, PLANS.md, docs/architecture.md, docs/compatibility.md, docs/decisions.md |
| M0.6 | 2026-08-12 | 1 | Completude de paths e ordem transacional do pipeline. | PLANS.md, docs/architecture.md, docs/decisions.md |
| M1/M1.1 | 2026-08-13 | 1 | Scaffold, catálogo de papéis e contratos condicionais em JSON Schema. | .gitignore, .prime/agent/APPEND_SYSTEM.md, .prime/agent/prompts/.gitkeep, .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/… |
| M2 | 2026-08-13 | 4 | Máquina de estados, event log encadeado, replay e recuperação durável. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/arti… |
| M3 | 2026-08-13 | 5 | Ingestão PDF/ZIP offline, preservação do original e baseline v0000. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/ingestion.py, .prime/ha… |
| sem marco explícito | 2026-08-13..2026-09-01 | 26 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | .github/ISSUE_TEMPLATE/bug_report.md, .github/ISSUE_TEMPLATE/feature_request.md, .github/pull_request_template.md, .github/workflows/ci.yml, .gitignore, .prime/agent/APPEND_SYSTEM… |
| M4 | 2026-08-13 | 3 | Prompts imutáveis, overlays e compilação content-addressed dos 21 papéis. | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/prompts.py, .prime/handoffs/04_para_05.md, PLANS.md, control/fixtu… |
| M5 | 2026-08-13..2026-08-14 | 4 | Blackboard, grafo de impacto, views fechadas e ativação esparsa. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/arti… |
| M6 | 2026-08-14..2026-09-01 | 8 | Orquestração RLM hierárquica reentrante por receipts duráveis. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/adapters.py, .prime/age… |
| M7 | 2026-08-14..2026-09-01 | 6 | Síntese, merge isolado, challenger write-once e 13 gates locais. | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/gates.py, .prime/agent/skills/article-loop/src/article_loop/synthe… |
| M8 | 2026-08-27..2026-09-01 | 3 | Júri externo cego, inversão consistente e meta-revisão. | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/evaluation.py, .prime/handoffs/08_para_09.md, PLANS.md, control/te… |
| M9 | 2026-08-28..2026-09-01 | 5 | Diagnóstico determinístico de progresso e refoco reversível. | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/diagnosis.py, .prime/agent/skills/article-loop/src/article_loop/ev… |
| M8/M9 | 2026-09-01 | 1 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | bin/bootstrap-deps.sh, bin/check.sh, bin/preflight.sh, bin/start-prime.sh, scripts/01_external_evaluator.py, scripts/02_stagnation_detector.py, scripts/03_refocus_generator.py |
| M0 | 2026-09-01 | 1 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | config/roles/M00.yaml, config/roles/S10.yaml, config/roles/S20.yaml, config/roles/S30.yaml, config/roles/S40.yaml, config/roles/S50.yaml, config/roles/W11.yaml |
| M2/M3 | 2026-09-01 | 1 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | control/test_m2_durable_state.py, control/test_m3_ingestion.py |
| M4/M5 | 2026-09-01 | 1 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | control/test_m4_prompts.py, control/test_m5_blackboard_activation.py |

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
| `f9111838d` | 2026-09-01 | sem marco explícito | feat: initialize LOOP-PRIMER with CI workflows, community standards, and AI context layer | .github/ISSUE_TEMPLATE/bug_report.md, .github/ISSUE_TEMPLATE/feature_request.md, .github/pull_request_template.md, .github/workflows/ci.yml, .gitignore, .prime/agent/APPEND_SYSTEM… |
| `d1c6e571b` | 2026-09-01 | sem marco explícito | feat: initialize repository with README.md | README.md |
| `cf8b5845f` | 2026-09-01 | sem marco explícito | feat: add community standards, CI workflow, and initial project configuration | .github/ISSUE_TEMPLATE/bug_report.md, .github/ISSUE_TEMPLATE/feature_request.md, .github/pull_request_template.md, .github/workflows/ci.yml, .gitignore, CLAUDE.md |
| `947ee3a68` | 2026-09-01 | sem marco explícito | chore: initialize workspace and runtime directory sentinels | artifacts/extracted/.gitkeep, artifacts/original/.gitkeep, artifacts/rendered/.gitkeep, input/inbox/.gitkeep, logs/.gitkeep, prompts/immutable/.gitkeep |
| `327588161` | 2026-09-01 | sem marco explícito | feat(prompts): add immutable system prompts and role overlays | prompts/immutable/M00.md, prompts/immutable/S10.md, prompts/immutable/S20.md, prompts/immutable/S30.md, prompts/immutable/S40.md, prompts/immutable/S50.md |
| `06fce0af9` | 2026-09-01 | M8/M9 | feat(scripts): add M8-M9 CLI tools, finalizer, and preflight entrypoints | bin/bootstrap-deps.sh, bin/check.sh, bin/preflight.sh, bin/start-prime.sh, scripts/01_external_evaluator.py, scripts/02_stagnation_detector.py |
| `530e77df8` | 2026-09-01 | sem marco explícito | feat(ai): add deterministic AI context and history handoff utilities | scripts/ai_context.py, scripts/ai_handoff_common.py, scripts/ai_history.py |
| `87994b367` | 2026-09-01 | sem marco explícito | feat(config): add system, budgets, gates, and evaluation rubrics configuration | config/budgets.yaml, config/gates.yaml, config/rubrics/evaluation.yaml, config/system.yaml |
| `c7d5c2741` | 2026-09-01 | M0 | feat(config): add 21 specialized role definitions for M00, S10-S50, W11-W53 | config/roles/M00.yaml, config/roles/S10.yaml, config/roles/S20.yaml, config/roles/S30.yaml, config/roles/S40.yaml, config/roles/S50.yaml |
| `ae6986c08` | 2026-09-01 | sem marco explícito | feat(schemas): add JSON schemas for agent proposals, tasks, candidates, and decisions | config/schemas/agent-proposal.schema.json, config/schemas/agent-task.schema.json, config/schemas/candidate-manifest.schema.json, config/schemas/decision.schema.json, config/schema… |
| `1dc5ef4d9` | 2026-09-01 | sem marco explícito | feat(schemas): add JSON schemas for verdicts, math verifications, and finalization receipts | config/schemas/finalization-receipt.schema.json, config/schemas/gate-report.schema.json, config/schemas/jury-verdict.schema.json, config/schemas/math-evidence.schema.json, config/… |
| `850ada2d5` | 2026-09-01 | sem marco explícito | feat(core): add state_machine, store, and ingestion modules | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/ingestion.py, .prime/agent/skills/article-loop/src/article_loop/st… |
| `7af5f15d6` | 2026-09-01 | sem marco explícito | feat(core): add prompts, blackboard, activation, and adapters modules | .prime/agent/skills/article-loop/src/article_loop/activation.py, .prime/agent/skills/article-loop/src/article_loop/adapters.py, .prime/agent/skills/article-loop/src/article_loop/b… |
| `8ba877668` | 2026-09-01 | sem marco explícito | feat(core): add synthesis merge and 13 deterministic gates verifiers | .prime/agent/skills/article-loop/src/article_loop/gates.py, .prime/agent/skills/article-loop/src/article_loop/synthesis.py |
| `ab0ae8ddc` | 2026-09-01 | sem marco explícito | feat(core): add hierarchical RLM orchestrator with durable receipts | .prime/agent/skills/article-loop/src/article_loop/orchestrator.py |
| `c7c8ea368` | 2026-09-01 | M8 | feat(core): add M8 external blind evaluation engine | .prime/agent/skills/article-loop/src/article_loop/evaluation.py |
| `6114bf52f` | 2026-09-01 | M9 | feat(core): add M9 deterministic stagnation diagnosis engine | .prime/agent/skills/article-loop/src/article_loop/diagnosis.py |
| `6d4a905cf` | 2026-09-01 | M9 | feat(core): add M9 reversible CAS prompt refocus generator | .prime/agent/skills/article-loop/src/article_loop/refocus.py |
| `a2eae2076` | 2026-09-01 | sem marco explícito | docs(prime): add skill definitions and technical handoff milestones | .prime/agent/APPEND_SYSTEM.md, .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/handoffs/02_para_03.md, .prime/handoffs/03_para_0… |
| `b74ba4c44` | 2026-09-01 | sem marco explícito | test(control): add fixtures and AI handoff verification tests | control/__init__.py, control/fixtures/m4/agent_proposal.json, control/fixtures/m4/agent_task.json, control/fixtures/m4/department_packet.json, control/fixtures/m4/prompt-snapshots… |
| `1573b6edf` | 2026-09-01 | sem marco explícito | test(control): add 20 schema contracts and state transition test suite | control/test_contracts.py |
| `aa15902f2` | 2026-09-01 | sem marco explícito | fix(scripts): remove stray backslash in ai_context.py test parser | scripts/ai_context.py |
| `ceb5ff7a6` | 2026-09-01 | M2/M3 | test(control): add M2 durable state and M3 ingestion test suites | control/test_m2_durable_state.py, control/test_m3_ingestion.py |
| `f5983ab2b` | 2026-09-01 | M4/M5 | test(control): add M4 prompt compilation and M5 activation test suites | control/test_m4_prompts.py, control/test_m5_blackboard_activation.py |
| `99b9bbf3c` | 2026-09-01 | M6 | test(control): add M6 orchestration and durable journal test suite | control/test_m6_orchestration.py |
| `440941468` | 2026-09-01 | M7 | test(control): add M7 synthesis merge and gates validation test suite | control/test_m7_synthesis_gates.py |
| `7a3e2e452` | 2026-09-01 | M8 | test(control): add M8 external blind evaluation test suite | control/test_m8_evaluation.py |
| `97a7b4a47` | 2026-09-01 | M9 | test(control): add M9 deterministic stagnation diagnosis test suite | control/test_m9_diagnosis.py |
| `4a588d729` | 2026-09-01 | sem marco explícito | docs(core): add architecture overview and Prime compatibility guides | docs/architecture.md, docs/compatibility.md |
| `48d518601` | 2026-09-01 | sem marco explícito | docs(adrs): add comprehensive architectural decision records (ADRs 001-024) | docs/decisions.md |
| `1ba3e0e33` | 2026-09-01 | sem marco explícito | docs(ai): add AI session history, jsonl ledger, and snapshot | docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| `a3ffaa9d5` | 2026-09-01 | sem marco explícito | docs(spec): add AGENTS operational policy and PLANS milestone roadmap | AGENTS.md, PLANS.md |
| `af1b3d264` | 2026-09-01 | sem marco explícito | docs(ai): add consolidated AI_CONTEXT snapshot | AI_CONTEXT.md |
| `bb04d9803` | 2026-09-01 | sem marco explícito | fix(ai): reconcile tracked context with GitHub publication | .github/workflows/ci.yml, AI_CONTEXT.md, PLANS.md, README.md, control/test_ai_handoff.py, docs/AI_HISTORY.md |
| `f6bb6259a` | 2026-09-01 | sem marco explícito | chore(git): reconcile local and GitHub histories |  |
| `ff09de79c` | 2026-09-01 | sem marco explícito | docs(ai): record GitHub publication handoff | AI_CONTEXT.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |

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
