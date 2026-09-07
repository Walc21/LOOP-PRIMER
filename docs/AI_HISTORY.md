# Histórico evolutivo e atualizações de sessão — article-loop

> Gerado por `scripts/ai_history.py`. O histórico Git e os ADRs são reconstruídos; as atualizações de sessão vêm do ledger append-only `docs/ai_sessions.jsonl`.

## Baseline registrado

- Fingerprint das fontes: `07bd06008d6f89faf1b3b8e83ec95ad0f810430a390a47fd12380e4a539077c5`
- Registrado em: `2026-09-07T04:57:09Z`
- Git: branch `codex/m3-real-source-ready`, HEAD `2ff020dfe869`
- Arquivos relevantes: 633

## Evolução reconstruída do versionamento

| Marco | Intervalo | Commits | Evolução inferida | Áreas tocadas |
|---|---:|---:|---|---|
| M0/M0.5 | 2026-08-12 | 1 | Auditoria de compatibilidade, segurança e fixação da arquitetura canônica. | AGENTS.md, PLANS.md, docs/architecture.md, docs/compatibility.md, docs/decisions.md |
| M0.6 | 2026-08-12 | 1 | Completude de paths e ordem transacional do pipeline. | PLANS.md, docs/architecture.md, docs/decisions.md |
| M1/M1.1 | 2026-08-13 | 1 | Scaffold, catálogo de papéis e contratos condicionais em JSON Schema. | .gitignore, .prime/agent/APPEND_SYSTEM.md, .prime/agent/prompts/.gitkeep, .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/… |
| M2 | 2026-08-13 | 4 | Máquina de estados, event log encadeado, replay e recuperação durável. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/arti… |
| M3 | 2026-08-13..2026-09-06 | 6 | Ingestão PDF/ZIP offline, preservação do original e baseline v0000. | .gitignore, .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/ingestion.p… |
| sem marco explícito | 2026-08-13..2026-09-07 | 57 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | .github/ISSUE_TEMPLATE/bug_report.md, .github/ISSUE_TEMPLATE/feature_request.md, .github/copilot-instructions.md, .github/pull_request_template.md, .github/workflows/ci.yml, .giti… |
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
| M10 | 2026-09-02..2026-09-03 | 2 | Política de compensação, decisão canônica e finalizador transacional. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/diagnosis.py, .prime/ag… |
| M10.1 | 2026-09-03 | 1 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | AI_CONTEXT.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| M11 | 2026-09-03 | 2 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | .prime/agent/APPEND_SYSTEM.md, .prime/agent/prompts/article-bootstrap.md, .prime/agent/prompts/article-checkpoint.md, .prime/agent/prompts/article-finalize.md, .prime/agent/prompt… |
| M12 | 2026-09-03 | 1 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/budget.py, .prime/agent… |
| M12.5 | 2026-09-03..2026-09-04 | 9 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | .github/workflows/ci.yml, .gitignore, .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/sr… |
| M13 | 2026-09-04..2026-09-05 | 4 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | .github/workflows/ci.yml, .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_lo… |
| M13.1 | 2026-09-05 | 3 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/budget.py, .prime/agent/skills/article-loop/src/article_loop/evalu… |
| M13.2 | 2026-09-06 | 4 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | .prime/agent/skills/article-loop/src/article_loop/adapters.py, .prime/agent/skills/article-loop/src/article_loop/evaluation.py, .prime/agent/skills/article-loop/src/article_loop/e… |
| M14 | 2026-09-06 | 2 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | .gitignore, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/budget.py, .prime/agent/skills/article-loop/src/articl… |

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
| `42ac80fa9` | 2026-09-01 | sem marco explícito | chore: sync CI workflows, schemas, requirements, and runtime sentinels | .github/workflows/ci.yml, .prime/agent/prompts/.gitkeep, bin/preflight.sh, config/schemas/decision.schema.json, requirements-dev.txt |
| `18773d774` | 2026-09-01 | sem marco explícito | feat(scripts): sync deterministic AI context and history handoff utilities | scripts/ai_context.py, scripts/ai_handoff_common.py, scripts/ai_history.py |
| `dd70d1179` | 2026-09-01 | sem marco explícito | feat(core): sync ingestion, activation, and adapters modules | .prime/agent/skills/article-loop/src/article_loop/activation.py, .prime/agent/skills/article-loop/src/article_loop/adapters.py, .prime/agent/skills/article-loop/src/article_loop/i… |
| `998f5c41f` | 2026-09-01 | sem marco explícito | feat(core): sync synthesis, gates, and refocus modules | .prime/agent/skills/article-loop/src/article_loop/gates.py, .prime/agent/skills/article-loop/src/article_loop/refocus.py, .prime/agent/skills/article-loop/src/article_loop/synthes… |
| `00dbd9ad0` | 2026-09-01 | sem marco explícito | feat(core): sync hierarchical RLM orchestrator | .prime/agent/skills/article-loop/src/article_loop/orchestrator.py |
| `586ddcad9` | 2026-09-01 | sem marco explícito | feat(core): sync blind evaluation and meta-review engine | .prime/agent/skills/article-loop/src/article_loop/evaluation.py |
| `fd23224d1` | 2026-09-01 | sem marco explícito | feat(core): sync stagnation diagnosis engine | .prime/agent/skills/article-loop/src/article_loop/diagnosis.py |
| `f2bbcf3aa` | 2026-09-01 | sem marco explícito | test(control): sync tests for handoff, durable state, ingestion, prompts | control/test_ai_handoff.py, control/test_m2_durable_state.py, control/test_m3_ingestion.py, control/test_m4_prompts.py |
| `e3df0df8c` | 2026-09-01 | sem marco explícito | test(control): sync tests for activation, orchestration, synthesis/gates | control/test_m5_blackboard_activation.py, control/test_m6_orchestration.py, control/test_m7_synthesis_gates.py |
| `74ff710f6` | 2026-09-01 | sem marco explícito | test(control): sync test suite for blind evaluation | control/test_m8_evaluation.py |
| `e8eecce95` | 2026-09-01 | sem marco explícito | test(control): sync test suite for stagnation diagnosis | control/test_m9_diagnosis.py |
| `80ae9c8fd` | 2026-09-01 | sem marco explícito | docs(spec): sync AGENTS, CLAUDE, PLANS, and README | AGENTS.md, CLAUDE.md, PLANS.md, README.md |
| `7a6312210` | 2026-09-01 | sem marco explícito | docs(arch): sync architecture overview, compatibility, and ADRs | docs/architecture.md, docs/compatibility.md, docs/decisions.md |
| `b0600ac1e` | 2026-09-01 | sem marco explícito | docs(ai): sync session ledger, history and snapshot handoff | docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| `fae5d251d` | 2026-09-01 | sem marco explícito | docs(ai): sync AI context snapshot | AI_CONTEXT.md |
| `929ad97f2` | 2026-09-02 | sem marco explícito | chore(git): publish local updates to GitHub repository |  |
| `35e2f80be` | 2026-09-02 | sem marco explícito | fix(repo): separate GitHub and AI integration | .github/copilot-instructions.md, AI_CONTEXT.md, GEMINI.md, PLANS.md, README.md, control/test_ai_handoff.py |
| `051f969db` | 2026-09-02 | sem marco explícito | fix(ci): restore GitHub Actions matrix | .github/workflows/ci.yml, .prime/agent/skills/article-loop/src/article_loop/evaluation.py, AI_CONTEXT.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| `35c1fa6f8` | 2026-09-02 | M10 | feat(m10): add deterministic decision finalizer | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/diagnosis.py, .prime/ag… |
| `9c598ba8a` | 2026-09-03 | M10 | feat(m10): harden finalization evidence and recovery | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/finalization.py, .prime/agent/skills/article-loop/src/article_loop/policy.py, AI_CONTE… |
| `1fec40893` | 2026-09-03 | M10.1 | chore(history): record M10.1 publication | AI_CONTEXT.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| `87c26ae37` | 2026-09-03 | M11 | feat(m11): add local Prime Agent command integration | .prime/agent/APPEND_SYSTEM.md, .prime/agent/prompts/article-bootstrap.md, .prime/agent/prompts/article-checkpoint.md, .prime/agent/prompts/article-finalize.md, .prime/agent/prompt… |
| `af08c798d` | 2026-09-03 | M11 | chore(history): record M11 publication | AI_CONTEXT.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| `e5eb78fbc` | 2026-09-03 | M12 | feat(m12): add durable budget observability | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/budget.py, .prime/agent… |
| `dbf411c80` | 2026-09-03 | M12.5 | feat(m12.5): add deterministic inference routing | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/budget.py, .prime/agent… |
| `4961907ae` | 2026-09-03 | M12.5 | chore(history): record M12.5 publication | .prime/handoffs/12_5_para_13.md, AI_CONTEXT.md, PLANS.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| `3858f0b94` | 2026-09-03 | M12.5 | chore(context): refresh M12.5 publication snapshot | AI_CONTEXT.md |
| `49fad01ca` | 2026-09-03 | M12.5 | fix(m12.5): normalize closed backend connections | .prime/agent/skills/article-loop/src/article_loop/inference_backends.py, .prime/handoffs/12_5_para_13.md, PLANS.md, control/test_m11_commands.py, control/test_m125_inference_routi… |
| `90c1e27b7` | 2026-09-03 | M12.5 | docs(m12.5): record green CI validation | .prime/handoffs/12_5_para_13.md, AI_CONTEXT.md, PLANS.md, README.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl |
| `ba316b50a` | 2026-09-03 | M12.5 | chore(context): refresh M12.5 CI snapshot | AI_CONTEXT.md |
| `e238b8891` | 2026-09-03 | M12.5 | feat(m12.5.1): add dual execution phase A | .github/workflows/ci.yml, .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_lo… |
| `562cbbf28` | 2026-09-03 | M12.5 | chore(history): record M12.5.1 publication | AI_CONTEXT.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| `007edeee5` | 2026-09-04 | M12.5 | feat(m12.5.1): promote proven routed inference path | .gitignore, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/execution.py, .prime/agent/skills/article-loop/src/art… |
| `b15526ef4` | 2026-09-04 | sem marco explícito | docs(ai): restore omitted security review session | AI_CONTEXT.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| `e9cb259b5` | 2026-09-04 | M13 | feat(m13): prove offline system and delivery path | .github/workflows/ci.yml, .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_lo… |
| `13fefd702` | 2026-09-04 | M13 | chore(context): finalize M13 local handoff | AI_CONTEXT.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| `3d298da4a` | 2026-09-05 | M13 | Merge pull request #2 from Walc21/m13-system-delivery |  |
| `cadfafb88` | 2026-09-05 | M13.1 | wip(m13.1): preserve routed jury integration | .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/evaluation.py, .prime/agent/skills/article-loop/src/article_loop/i… |
| `ac49084f1` | 2026-09-05 | M13.1 | feat(m13.1): separate evaluator inference identity | .prime/agent/skills/article-loop/src/article_loop/budget.py, .prime/agent/skills/article-loop/src/article_loop/inference.py, .prime/agent/skills/article-loop/src/article_loop/rout… |
| `f08e1d2dc` | 2026-09-05 | M13.1 | docs(m13.1): close routed jury integration | AI_CONTEXT.md, PLANS.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json, docs/architecture.md |
| `ea2057cca` | 2026-09-05 | M13 | Merge pull request #3 from Walc21/m13-routed-jury-hardening |  |
| `27b836586` | 2026-09-05 | sem marco explícito | fix(ai-context): make session startup read-only | .github/copilot-instructions.md, .prime/agent/APPEND_SYSTEM.md, AGENTS.md, CLAUDE.md, GEMINI.md, PLANS.md |
| `f6c6b0562` | 2026-09-05 | sem marco explícito | docs(ai-context): publish read-only lifecycle checkpoint | AI_CONTEXT.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| `67910ec79` | 2026-09-05 | sem marco explícito | Merge pull request #4 from Walc21/chore/ai-context-lifecycle |  |
| `c7fee6b6b` | 2026-09-06 | M13.2 | feat(m13.2): harden structural execution boundaries | .prime/agent/skills/article-loop/src/article_loop/adapters.py, .prime/agent/skills/article-loop/src/article_loop/evaluation.py, .prime/agent/skills/article-loop/src/article_loop/e… |
| `de9253491` | 2026-09-06 | M13.2 | Merge pull request #5 from Walc21/codex/m13.2-structural-hardening |  |
| `9176655e1` | 2026-09-06 | M13.2 | docs(m13.2): publish structural hardening checkpoint | AI_CONTEXT.md, PLANS.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json, docs/decisions.md |
| `816634ea4` | 2026-09-06 | M13.2 | Merge pull request #6 from Walc21/codex/m13.2.1-handoff |  |
| `e1daf66e9` | 2026-09-06 | M14 | feat(m14): add local control center | .gitignore, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/budget.py, .prime/agent/skills/article-loop/src/articl… |
| `fce6dfc0e` | 2026-09-06 | sem marco explícito | Merge pull request #7 from Walc21/codex/control-center |  |
| `9faed3499` | 2026-09-06 | sem marco explícito | Clarify canonical local control-center startup | .prime/agent/skills/article-loop/src/article_loop/control_center_static/index.html, .prime/agent/skills/article-loop/src/article_loop/control_center_static/styles.css, AI_CONTEXT.… |
| `ef39df85f` | 2026-09-06 | M14 | docs(readme): refresh M14 project overview | AI_CONTEXT.md, README.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| `b406a9ded` | 2026-09-06 | sem marco explícito | fix(readme): retain handoff contract markers | AI_CONTEXT.md, README.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| `ba90b7847` | 2026-09-06 | sem marco explícito | Merge pull request #8 from Walc21/codex/control-center-launcher |  |
| `edcba666e` | 2026-09-06 | M3 | feat(local): add isolated full-cycle entry and harden M3 | .gitignore, .prime/agent/skills/article-loop/src/article_loop/ingestion.py, AI_CONTEXT.md, PLANS.md, control/test_local_loopback_full_cycle.py, control/test_m3_ingestion.py |
| `6ac799fac` | 2026-09-06 | sem marco explícito | docs(ai): checkpoint commit and PR publication | AI_CONTEXT.md, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| `6753f0cd6` | 2026-09-06 | sem marco explícito | test(ci): make local cycle fixture self-contained | AI_CONTEXT.md, PLANS.md, control/test_local_loopback_full_cycle.py, docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json |
| `3ae6ab7a6` | 2026-09-06 | sem marco explícito | Merge pull request #9 from Walc21/codex/local-loopback-full-cycle |  |
| `b16fb5205` | 2026-09-07 | sem marco explícito | docs: compact agent context routing | .github/copilot-instructions.md, .prime/agent/APPEND_SYSTEM.md, .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/references/api-contracts.md, AGENTS.md,… |
| `2ff020dfe` | 2026-09-07 | sem marco explícito | Merge pull request #10 from Walc21/codex/lean-agent-context |  |

## Decisões arquiteturais

- ADR-040 — Contexto escalonado para agentes sem perda de autoridade
- ADR-039 — Ciclo local autorizado por composição das APIs canônicas
- ADR-038 — M14: inicialização exclusivamente pelo servidor local canônico
- ADR-037 — M14: Central de Controle local como camada de projeção e comando canônico
- ADR-036 — M13.2: hardening estrutural de fronteiras de execução e júri
- ADR-035 — M13.1: julgamento routed com identidade de avaliador separada
- ADR-034 — M13: aceitação offline e auditoria independente da entrega
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
- ADR-027 — Separação de audiências e histórico Git publicável
- ADR-028 — M10: política pura e finalização transacional por referência
- ADR-029 — M10.1: pacote final canônico e recuperação coberta por fase
- ADR-030 — M11: comandos locais e integração Prime Agent fail-closed
- ADR-031 — M12: orçamento durável e observabilidade fail-closed
- ADR-032 — M12.5: routing determinístico governado pelo ledger M12
- ADR-033 — M12.5.1 Phase A: execução dual ligada ao contrato M6
- ADR-034 — Ciclo de contexto de IA: início read-only e checkpoint explícito

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

### 2026-09-01T11:38:01Z — Precheck do M10 interrompido antes da implementação porque a árvore Git já continha AI_CONTEXT.md modificado; nenhum código, contrato científico, plano, ADR, estado ou versão do M10 foi alterado.

- Session ID: `session-b623adc6ee93e8333134`
- Fingerprint final: `b179c30014db09573fa09040ceb77f26251c885e51a06f99839bef6cf578d8f0`
- Git final: `f9111838d8dc`; status relevante: 0 item(ns)
- Delta factual: 7 adicionados, 1 modificados, 0 removidos

**Mudanças**

- Nenhuma mudança funcional do M10 foi realizada; somente o snapshot inicial obrigatório foi regenerado e esta conclusão diagnóstica foi registrada conforme AGENTS.md.

**Decisões**

- Aplicado fail-closed ao requisito de árvore Git limpa; M10 não foi iniciado.

**Validações**

- python3 scripts/ai_context.py: status current; AI_CONTEXT.md regenerado com sucesso.
- git status --porcelain=v1: M AI_CONTEXT.md antes da implementação.
- git merge-base --is-ancestor 907af50 HEAD e 765aac3 HEAD: ambos retornaram sucesso; checkpoints M9 são ancestrais do HEAD f911183.

**Riscos/limites**

- A árvore permanece divergente e não pode receber o commit único do M10 sem uma decisão explícita sobre o AI_CONTEXT.md gerado.

**Próximos passos**

- Limpar ou autorizar a incorporação do AI_CONTEXT.md atual em um baseline separado; então reiniciar o precheck completo do M10.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `.github/ISSUE_TEMPLATE/bug_report.md` | `-` | `6e7f0c070911` |
| added | `.github/ISSUE_TEMPLATE/feature_request.md` | `-` | `bf3b8ec7c497` |
| added | `.github/pull_request_template.md` | `-` | `42ee22ace252` |
| added | `.github/workflows/ci.yml` | `-` | `fa6e9e693cbe` |
| added | `CONTRIBUTING.md` | `-` | `88dd6a0e2eb0` |
| added | `LICENSE` | `-` | `0d0db335dda4` |
| added | `SECURITY.md` | `-` | `1adf19468e39` |
| modified | `README.md` | `73b055ebb203` | `767c7f78d10c` |

### 2026-09-01T11:52:21Z — Reconciliada a implementação de contexto/histórico para IA com o commit posterior de publicação no GitHub, preservando as adições comunitárias e restaurando o comportamento perdido.

- Session ID: `session-97c4dfa331be26096a7e`
- Fingerprint final: `6f2971f08a5feaa6c15b713cedfa0dc50a255fd5378145820f6c83a17f5bd51c`
- Git final: `f9111838d8dc`; status relevante: 6 item(ns)
- Delta factual: 0 adicionados, 6 modificados, 0 removidos

**Mudanças**

- A comparação content-addressed comprovou que scripts, gatilhos, testes, plano, arquitetura e ADR originais sobreviveram byte a byte; o commit posterior adicionou sete arquivos e substituiu somente README.md.
- O README de apresentação do GitHub foi preservado, recebeu novamente o gatilho obrigatório para IAs e passou a declarar corretamente que M10 e os scripts 04/05 continuam pendentes e inertes.
- scripts/ai_context.py agora limita o README incorporado, normaliza espaços finais de previews e exclui AI_CONTEXT.md, AI_HISTORY.md, ai_sessions.jsonl e ai_snapshot.json do preview Git para impedir autorreferência.
- O workflow de CI passou a instalar TeX/Poppler e executar a descoberta integral M0-M9; control/test_ai_handoff.py cobre as quatro superfícies de gatilho, preview limitado e idempotência com AI_CONTEXT.md rastreado.

**Decisões**

- As sete adições comunitárias da sessão do GitHub foram mantidas; nenhuma versão, candidato, estado científico ou componente M10 foi alterado.
- Artefatos gerados permanecem rastreados, mas são excluídos do próprio preview Git; mudanças de fontes continuam aparecendo no fingerprint e no delta.

**Validações**

- Comparação do snapshot original contra a árvore posterior: 7 arquivos adicionados, 1 modificado (README.md), 0 removidos; 11 arquivos centrais conferidos por SHA-256 e idênticos.
- python3 -m unittest -q control.test_ai_handoff control.test_contracts: 59 testes aprovados.
- python3 -m unittest discover -s control -p 'test_*.py' -q: 306 testes aprovados em 178.248s.
- python3 -m py_compile dos utilitários/teste, duas gerações idempotentes de AI_CONTEXT.md e git diff --check: aprovados.

**Riscos/limites**

- AI_CONTEXT.md é um artefato gerado rastreado e pode mudar após novos commits ou fontes; execute o gerador no início e novamente no encerramento conforme AGENTS.md.

**Próximos passos**

- M10 permanece pendente e deve ser iniciado somente em uma sessão separada e autorizada; esta reconciliação não executou artigo, modelos ou rede.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `.github/workflows/ci.yml` | `fa6e9e693cbe` | `ab1a06f9a6af` |
| modified | `PLANS.md` | `287b35b3576f` | `e5fdc5c8c8d1` |
| modified | `README.md` | `767c7f78d10c` | `c4b17d42beac` |
| modified | `control/test_ai_handoff.py` | `b660fd15651b` | `9de410fac395` |
| modified | `docs/decisions.md` | `6526bb3da3fd` | `276e9d1c0e9e` |
| modified | `scripts/ai_context.py` | `4009029f532f` | `43b8ac9858f5` |

### 2026-09-01T12:18:53Z — Preparada a publicação da reconciliação no GitHub e preservados os históricos local e remoto; o push não foi aplicado porque a máquina não possui credencial HTTPS, GitHub CLI ou chave SSH autorizada.

- Session ID: `session-af3c5e022c055dd4c430`
- Fingerprint final: `6f2971f08a5feaa6c15b713cedfa0dc50a255fd5378145820f6c83a17f5bd51c`
- Git final: `f6bb6259a874`; status relevante: 0 item(ns)
- Delta factual: 0 adicionados, 0 modificados, 0 removidos

**Mudanças**

- Criado o commit bb04d98 com a reconciliação validada do contexto, README, testes e CI.
- Os históricos sem ancestral comum foram unidos pelo merge f6bb625 com origin/main como segundo pai e árvore idêntica à versão local validada; a branch local foi renomeada de master para main.

**Decisões**

- Foi recusado force-push. Como o remoto tinha zero arquivos exclusivos ausentes localmente, o merge de preservação manteve todos os commits remotos no grafo e exatamente a árvore local validada.

**Validações**

- git fetch --prune origin confirmou main como branch padrão e origin/master removida.
- Comparação de árvores: remote_only_count=0, local_only_count=1; tree antes e depois do merge f6bb625 permaneceu a89f954bea809c2b427ac7f768737590ecfe805c.
- git push --set-upstream origin main foi recusado antes de qualquer atualização remota com could not read Username; gh ausente e SSH respondeu Permission denied (publickey).

**Riscos/limites**

- Os commits estão somente na máquina local até o usuário autenticar HTTPS ou SSH para github.com.

**Próximos passos**

- Após autenticação do GitHub nesta máquina, repetir git push --set-upstream origin main e verificar o SHA remoto.

### 2026-09-02T17:07:54Z — Reparada a integração local com Git/GitHub e separadas as superfícies Markdown humanas das entradas para IAs, preservando integralmente a árvore funcional e sem iniciar M10, modelos ou o pipeline científico.

- Session ID: `session-github-ai-repair-20260902`
- Fingerprint final: `458c1f41f6f40316728d43cafff1963444cb4dd292577c91fea20e12280db1bf`
- Git final: `8f6f59e95746`; status relevante: 3 item(ns)
- Delta factual: 2 adicionados, 6 modificados, 0 removidos

**Mudanças**

- A raiz efetiva do projeto foi elevada de EXECLOOP/ para a pasta de trabalho; o repositório Git vazio da pasta-pai foi movido para backup recuperável e restou um único .git na raiz.
- O merge artificial de históricos independentes saiu de main; o grafo anterior foi preservado em backup/pre-github-repair-20260902 e a árvore final foi condensada em um único commit descendente de origin/main.
- README.md ficou dedicado à apresentação pública; GEMINI.md e .github/copilot-instructions.md foram adicionados, convergindo com AGENTS.md, CLAUDE.md e a integração Prime para a política canônica de IA.
- AI_CONTEXT.md deixou de persistir caminho absoluto, branch e HEAD, deixou de incorporar README/AGENTS/inventário completo e ganhou truncamento de diff em limite de linha; a saída aponta ao snapshot detalhado.
- Os launchers e scripts de ativação da .venv local foram corrigidos para a raiz atual, sem rede ou instalação de dependências.

**Decisões**

- Preservar AI_CONTEXT.md versionado para leitores remotos, mas torná-lo portátil e compacto; manter README.md humano e usar adaptadores específicos para descoberta por IA.
- Não usar force-push nem alterar o remoto durante o reparo; preparar main para publicação normal por fast-forward e conservar backups locais.

**Validações**

- python3 -m unittest discover -s control -p 'test_*.py' -q após elevar a raiz: 307 testes aprovados em 222.705s.
- python3 -m unittest -q control.test_ai_handoff control.test_contracts: 60 testes aprovados; python3 -m py_compile nas fontes/scripts/testes: aprovado.
- Validador local leu 48 arquivos Markdown em UTF-8 e encontrou zero links relativos quebrados; git diff --check passou após corrigir o truncamento em meio de linha.
- git rev-list --left-right --count origin/main...main retornou 0 1 e git merge-base --is-ancestor origin/main main retornou sucesso; main possui um único commit local de pai único.
- Ativação da .venv, import de jsonschema/PyYAML, pip 25.1.1 e jsonschema CLI 4.10.3 funcionaram na nova raiz.

**Riscos/limites**

- git fetch/push via HTTPS continua bloqueado por ausência de credencial; origin/main é a última referência remota disponível localmente e nenhuma publicação foi alegada.
- O grafo anterior permanece somente na branch local de backup e o .git vazio anterior permanece em backup fora da raiz; não devem ser publicados.

**Próximos passos**

- Autenticar o GitHub nesta máquina, executar git fetch origin, confirmar novamente o fast-forward e então git push origin main; verificar o SHA e a CI no remoto.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `.github/copilot-instructions.md` | `-` | `c72d16e8330e` |
| added | `GEMINI.md` | `-` | `e2cbfe965d39` |
| modified | `PLANS.md` | `e5fdc5c8c8d1` | `3a87aa4bac8d` |
| modified | `README.md` | `c4b17d42beac` | `5602c8f20915` |
| modified | `control/test_ai_handoff.py` | `9de410fac395` | `8a96f1d415b2` |
| modified | `docs/architecture.md` | `15c0171b2569` | `45f6cf230dd1` |
| modified | `docs/decisions.md` | `276e9d1c0e9e` | `452734f3f329` |
| modified | `scripts/ai_context.py` | `43b8ac9858f5` | `26aa077994cc` |

### 2026-09-02T17:16:51Z — Explicado como autorizar publicação no GitHub a partir do Codex local; nenhuma fonte, configuração ou contrato do projeto foi alterado.

- Session ID: `session-github-publish-auth-guidance-20260902`
- Fingerprint final: `458c1f41f6f40316728d43cafff1963444cb4dd292577c91fea20e12280db1bf`
- Git final: `f831dece33fb`; status relevante: 0 item(ns)
- Delta factual: 0 adicionados, 0 modificados, 0 removidos

**Mudanças**

- Nenhuma alteração funcional ou documental foi realizada; somente o handoff diagnóstico obrigatório foi registrado.

**Decisões**

- Recomendada autenticação interativa do GitHub CLI via navegador, sem fornecer senha ou token ao agente.

**Validações**

- Inspeção local confirmou origin HTTPS, branch main um commit à frente, GitHub CLI ausente e nenhum credential.helper configurado.

**Riscos/limites**

- A publicação continua indisponível até o usuário concluir pessoalmente a autenticação do GitHub nesta máquina.

**Próximos passos**

- Instalar o GitHub CLI, concluir gh auth login via navegador, executar gh auth setup-git e então autorizar explicitamente o push.

### 2026-09-02T17:23:25Z — Autenticação do GitHub validada e publicação preparada por reconciliação segura sobre o remoto atualizado, deixando main em condição fast-forward sem force-push.

- Session ID: `session-github-publish-20260902`
- Fingerprint final: `458c1f41f6f40316728d43cafff1963444cb4dd292577c91fea20e12280db1bf`
- Git final: `fc295e4363c4`; status relevante: 0 item(ns)
- Delta factual: 0 adicionados, 0 modificados, 0 removidos

**Mudanças**

- Após o fetch revelar 55 commits no remoto, o commit local corrigido foi preservado em backup/pre-publish-rebase-20260902 e reaplicado sobre origin/main mantendo exatamente a mesma árvore de conteúdo.

**Decisões**

- Preservar integralmente o histórico remoto e recusar push divergente; publicar somente por fast-forward, sem force-push.

**Validações**

- gh api user confirmou a conta autenticada Walc21 sem exibir credenciais.
- Após a reconciliação, origin/main...main apresentou 0 commits somente no remoto e 1 somente no local; origin/main é ancestral de main.
- A árvore antes e depois da reconciliação permaneceu idêntica no hash 1040b4e2d8690c32345a0d4d61cefe8151477a2f.
- Foram aprovados 60 testes direcionados, compilação dos arquivos Python versionados, git diff --check e verificação de atualidade do AI_CONTEXT.md.

**Riscos/limites**

- A execução de CI do GitHub só poderá ser confirmada depois do push.

**Próximos passos**

- Executar git push origin main e verificar a igualdade entre os SHAs local e remoto e o resultado do CI.

### 2026-09-02T17:30:21Z — Falhas da CI publicada foram diagnosticadas e corrigidas para restaurar a matriz GitHub Actions em Python 3.11, 3.12 e 3.13.

- Session ID: `session-github-ci-repair-20260902`
- Fingerprint final: `b94ca8b644688f7fc7471700095cdfe3a55a8ec3baee9cd69af72dbdcd53501a`
- Git final: `35e2f80bea39`; status relevante: 2 item(ns)
- Delta factual: 0 adicionados, 2 modificados, 0 removidos

**Mudanças**

- O workflow passou a instalar ghostscript, dependência do comando gs usado pelos testes de ingestão, síntese, avaliação e diagnóstico.
- A reconstrução de IDs em evaluation.py foi refatorada para evitar expressão multilinha dentro de f-string e manter compatibilidade sintática com Python 3.11 sem alterar o conteúdo calculado.
- actions/checkout e actions/setup-python foram atualizadas para as releases oficiais atuais v7.0.1 e v7.0.0, eliminando o runtime Node.js obsoleto indicado pelo GitHub.

**Decisões**

- Corrigir a infraestrutura e a incompatibilidade declarada pela matriz em vez de remover testes ou abandonar o Python 3.11.

**Validações**

- O log da CI 33660817044 mostrou FileNotFoundError para gs em Python 3.12 e 3.13 e SyntaxError na f-string de evaluation.py em Python 3.11.
- A gramática Python 3.11 foi validada com ast.parse feature_version 3.11; todos os arquivos Python compilam no runtime local.
- O YAML do workflow foi analisado com sucesso e git diff --check não apontou erros.
- A suíte completa local aprovou 307 de 307 testes em 216.078 segundos.

**Riscos/limites**

- O resultado da nova matriz remota só será conhecido após publicar o commit de correção.

**Próximos passos**

- Criar e publicar o commit de correção de CI e acompanhar a nova execução do GitHub Actions até a conclusão.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `.github/workflows/ci.yml` | `ab1a06f9a6af` | `fe0474481ca7` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/evaluation.py` | `023e6a921488` | `8babd430c3b6` |

### 2026-09-03T01:37:13Z — Implementado M10 localmente: política de decisão determinística, Decision content-addressed e finalizador transacional sem alterar bytes do challenger avaliado.

- Session ID: `session-m10-local-20260902`
- Fingerprint final: `16226d96eedb3e09ea014422a6ea373666ea247a741fe1851601cd07e963f861`
- Git final: `051f969db75b`; status relevante: 14 item(ns)
- Delta factual: 5 adicionados, 9 modificados, 0 removidos

**Mudanças**

- Adicionados policy.py e finalization.py, a tabela fechada config/decision-policy.yaml, as CLIs 04/05 e a suíte control/test_m10_policy_finalization.py.
- A promoção cria versão histórica de champion com os mesmos bytes avaliados; Pareto e rejected recebem referências imutáveis; journal, fsync, rename e CAS protegem recuperação.
- Decision passou a exigir policy_config_hash; COMMITTING pode alcançar FINALIZED após revalidação; PLANS, ADR-028 e handoff 10_para_11 foram atualizados.

**Decisões**

- Nenhuma conexão, atualização ou commit no GitHub foi realizada; M11--M13, Prime Agent, modelos, rede e artigo real ficaram fora do escopo.
- A política usa a precedência fechada técnica, hard gate matemático, diagnóstico, julgamento inconclusivo e candidato avaliado; ambiguidade falha fechada.

**Validações**

- python3 -m unittest discover -s control -q: 316 testes aprovados em 214.956s; aviso Duplicate name a.tex pertence à fixture negativa M3.
- python3 -m unittest -q control.test_m10_policy_finalization control.test_contracts control.test_m2_durable_state: 91 testes aprovados em 11.927s.
- python3 -m py_compile dos módulos, CLIs e teste M10; git diff --check: aprovados.

**Riscos/limites**

- FINALIZE permanece fail-closed até reports finais locais aprovados para W22, W51 e W53; uma operação real continua requerendo autorização futura.

**Próximos passos**

- M11, se autorizado, deve começar com árvore limpa, AGENTS.md, docs/compatibility.md e .prime/handoffs/10_para_11.md, sem iniciar sessão Prime sem autorização específica.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `.prime/agent/skills/article-loop/src/article_loop/finalization.py` | `-` | `7c7378019bd2` |
| added | `.prime/agent/skills/article-loop/src/article_loop/policy.py` | `-` | `051c4c6b8824` |
| added | `.prime/handoffs/10_para_11.md` | `-` | `490423c2a9dd` |
| added | `config/decision-policy.yaml` | `-` | `461def203733` |
| added | `control/test_m10_policy_finalization.py` | `-` | `53ba08cd6f50` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/__init__.py` | `da6ca10075ff` | `fafdc5caf46a` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/state_machine.py` | `22268554a056` | `7f8ee90f7496` |
| modified | `PLANS.md` | `3a87aa4bac8d` | `71404a465d0f` |
| modified | `config/schemas/decision.schema.json` | `563503d4f74d` | `bbe604ff6464` |
| modified | `control/test_contracts.py` | `3c538170db94` | `6f5d25abde8c` |
| modified | `control/test_m2_durable_state.py` | `4b328ee7fc6a` | `ec7af622272b` |
| modified | `docs/decisions.md` | `452734f3f329` | `a869cadf7e11` |
| modified | `scripts/04_compensation_policy.py` | `7330a3953b54` | `7215917a1b87` |
| modified | `scripts/05_transactional_finalizer.py` | `9446896eae0b` | `6d379c3173b9` |

### 2026-09-03T02:00:55Z — Revisão e integração pré-publicação do M10 concluídas: política/finalizador reforçados, superfícies públicas sincronizadas e regressão integral aprovada.

- Session ID: `session-m10-prepublish-20260902`
- Fingerprint final: `921c248a2e2a15ed25f7429f73926349014d146386d22ad2e188e94e321b364c`
- Git final: `051f969db75b`; status relevante: 20 item(ns)
- Delta factual: 0 adicionados, 15 modificados, 0 removidos

**Mudanças**

- Acrescentada revalidação Pareto nas oito dimensões, registrada na Decision e conferida pelo finalizador sob lock.
- Acrescentado checkpoint técnico imutável com contador e limite; a fachada finalize() passou a delegar ao finalizador M10.
- README, arquitetura, skill, handoff, contexto e testes de integração foram atualizados para M10 operacional.

**Decisões**

- Referências Pareto dominadas são preservadas como evidência histórica; fronteira divergente após a Decision falha fechada.
- A revalidação M9 aceita somente os sucessores M10 DECIDED ou COMMITTING do mesmo ciclo, mantendo a vinculação ao evento DIAGNOSED original.

**Validações**

- python3 -m unittest discover -s control -q: 319 testes aprovados em 217.578s; aviso de ZIP duplicado a.tex é fixture negativa esperada.
- python3 -m unittest -v control.test_m10_policy_finalization control.test_contracts control.test_m2_durable_state: 94 testes aprovados.
- py_compile, json.tool no schema Decision, git diff --check e git fetch --prune origin aprovados; origin/main e HEAD permanecem alinhados antes do commit.

**Riscos/limites**

- Nenhum artigo real, Prime Agent, modelo ou API paga foi executado; o checkpoint técnico é manual e não inicia retry automático.

**Próximos passos**

- Criar o commit M10 e publicar o fast-forward em origin/main conforme autorização do usuário.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `.prime/agent/skills/article-loop/SKILL.md` | `31e949e57dc8` | `a008817e7381` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/__init__.py` | `fafdc5caf46a` | `7687ae22a123` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/diagnosis.py` | `17a74d7bfd39` | `5c60264a38c7` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/finalization.py` | `7c7378019bd2` | `5ee4a6f5f90e` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/policy.py` | `051c4c6b8824` | `086d71ecf13b` |
| modified | `.prime/handoffs/10_para_11.md` | `490423c2a9dd` | `780be8a5c4d1` |
| modified | `PLANS.md` | `71404a465d0f` | `d92a85224cd5` |
| modified | `README.md` | `5602c8f20915` | `355f4a13d8af` |
| modified | `config/schemas/decision.schema.json` | `bbe604ff6464` | `285c0e47f450` |
| modified | `control/test_ai_handoff.py` | `8a96f1d415b2` | `7eeb838fe65e` |
| modified | `control/test_contracts.py` | `6f5d25abde8c` | `273fe28e215e` |
| modified | `control/test_m10_policy_finalization.py` | `53ba08cd6f50` | `6bd8ac5a32e6` |
| modified | `docs/architecture.md` | `45f6cf230dd1` | `d6942938ab13` |
| modified | `docs/decisions.md` | `a869cadf7e11` | `38c2a4b299e0` |
| modified | `scripts/ai_context.py` | `26aa077994cc` | `3f7517e51d98` |

### 2026-09-03T04:11:47Z — Concluído o endurecimento M10.1 local: pacote final hash-bound, rederivação da Decision, recuperação pós-recibo e cobertura transacional ampliada, sem iniciar M11.

- Session ID: `session-m10.1-hardening-20260903`
- Fingerprint final: `5c57df597e90c7bd2b9a43adefadf9951b65264fcc901b5f710a1300688fa299`
- Git final: `35c1fa6f879e`; status relevante: 11 item(ns)
- Delta factual: 2 adicionados, 9 modificados, 0 removidos

**Mudanças**

- Adicionados os schemas versionados FinalGateReport e FinalReport; FINALIZE valida W22/W51/W53, GateReport vigente, manifesto, PDF renderizado e relatório final pelos hashes SHA-256.
- A política rederiva a única disposição permitida antes do efeito; o finalizador rejeita Decision divergente e recupera receipt pendente sem repetir a mutação.
- Ampliados contratos, testes M10, README, arquitetura, skill, plano e ADR-029 para cobrir o protocolo final M10.1.

**Decisões**

- PDF renderizado e relatório final são somente evidência local publicada previamente; M10 revalida-os, não executa renderização, artigo, Prime Agent, modelo ou rede.
- A recuperação de COMMITTING com receipt exige revalidação completa do recibo esperado antes de registrar exclusivamente o evento/checkpoint pendente.

**Validações**

- python3 -m unittest discover -s control -q: 331 testes aprovados em 245.441s; aviso Duplicate name a.tex pertence à fixture negativa de ZIP.
- python3 -m unittest -q control.test_m10_policy_finalization.M10IntegrationTests.test_every_durable_fault_boundary_recovers_exactly_once control.test_m10_policy_finalization.M10IntegrationTests.test_two_processes_share_one_finalization_receipt control.test_m10_policy_finalization.M10IntegrationTests.test_global_plateau_finalizes_only_after_complete_hash_bound_package: 3 testes aprovados em 6.773s.
- python3 -m py_compile policy.py finalization.py e git diff --check: aprovados.

**Riscos/limites**

- CONTINUE_UNCHANGED e ABORT_TECHNICAL permanecem cobertos pela tabela fechada e pelos checkpoints; a fixture integral não produz esses dois estados sem adulterar evidência imutável.

**Próximos passos**

- Somente com nova autorização: revisar/commitar/publicar M10.1; M11 continua pendente e fora de escopo.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `config/schemas/final-gate-report.schema.json` | `-` | `ede3c466919b` |
| added | `config/schemas/final-report.schema.json` | `-` | `dd19b7227a10` |
| modified | `.prime/agent/skills/article-loop/SKILL.md` | `a008817e7381` | `2daf907bd773` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/finalization.py` | `5ee4a6f5f90e` | `0a7f109e9e2e` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/policy.py` | `086d71ecf13b` | `cda534151c1c` |
| modified | `PLANS.md` | `d92a85224cd5` | `ce451c209d1c` |
| modified | `README.md` | `355f4a13d8af` | `44c335cc2acd` |
| modified | `control/test_contracts.py` | `273fe28e215e` | `e14816e0f348` |
| modified | `control/test_m10_policy_finalization.py` | `6bd8ac5a32e6` | `3084e0cf69b9` |
| modified | `docs/architecture.md` | `d6942938ab13` | `71e182c75e53` |
| modified | `docs/decisions.md` | `38c2a4b299e0` | `540ce5851b09` |

### 2026-09-03T04:19:31Z — Publicado M10.1 no GitHub após commit e fast-forward normais em origin/main; nenhum código adicional foi alterado nesta sessão.

- Session ID: `session-m10.1-publish-20260903`
- Fingerprint final: `5c57df597e90c7bd2b9a43adefadf9951b65264fcc901b5f710a1300688fa299`
- Git final: `9c598ba8a373`; status relevante: 0 item(ns)
- Delta factual: 0 adicionados, 0 modificados, 0 removidos

**Mudanças**

- Commit 9c598ba reuniu o endurecimento M10.1, schemas finais, testes, documentação pública e artefatos de handoff já validados.

**Decisões**

- A publicação usou push normal de main, sem force-push, rebase, reset ou alteração de histórico remoto.

**Validações**

- git fetch --prune origin confirmou HEAD e origin/main alinhados antes do commit (0 e 0); git diff --check aprovado; git push origin main publicou 35c1fa6..9c598ba.

**Riscos/limites**

- M11--M13 continuam pendentes; não houve execução de artigo, Prime Agent, modelo, API paga ou instalação.

**Próximos passos**

- Nenhum passo pendente para M10.1; iniciar M11 somente sob autorização específica e com nova árvore limpa.

### 2026-09-03T05:00:04Z — Implementação local do M11 concluída: a camada operacional agora expõe as APIs existentes por uma ponte JSON-in/JSON-out, nove templates planos, check local e launcher Prime fail-closed; documentação, runbook, compatibilidade e handoff foram sincronizados sem iniciar M12.

- Session ID: `session-m11-local-20260903`
- Fingerprint final: `769f42631f2e59ed03609f618d6a2a3713c2f4e640d109ce57d98ed945e37dde`
- Git final: `1fec40893496`; status relevante: 22 item(ns)
- Delta factual: 13 adicionados, 9 modificados, 0 removidos

**Mudanças**

- Adicionada scripts/article_loop_command.py como ponte única para bootstrap, preflight, run, status, checkpoint, pause, resume, stop e finalize, com validação de raiz/IDs/envelopes e dry-run padrão.
- Adicionados nove templates diretamente em .prime/agent/prompts/, guardrails M11 aditivos no APPEND_SYSTEM.md, check.sh, start-prime.sh e docs/runbook.md.
- Atualizados skill, arquitetura, compatibilidade, README, PLANS, ADR-030, testes M11 e handoff 11_para_12; settings.json foi deliberadamente omitido por ausência de schema confirmado.

**Decisões**

- O launcher só encaminha --skill e --prompt-template, após autorização/configuração explícitas, STOP ausente, preflight M3 e orçamento aprovados; defaults atuais continuam sem modelo e sem API paga.
- A ausência local do binário prime-agent não é compensada por instalação, opção global, sessão fake, credencial, rede, autonomous ou refine; o smoke test live fica pendente.

**Validações**

- python3 -m unittest discover -s control -q: 346 testes aprovados em 267.946s; o único aviso foi Duplicate name: a.tex da fixture negativa M3.
- python3 -m unittest -q control.test_contracts control.test_ai_handoff control.test_m11_commands: 75 testes aprovados.
- python3 -m py_compile scripts/article_loop_command.py control/test_m11_commands.py; bash -n bin/check.sh bin/start-prime.sh; git diff --check: aprovados.
- bash bin/check.sh e bash bin/start-prime.sh --dry-run --template article-run: aprovados, com prime_started=false e model_called=false; caminho live parou no orçamento fail-closed.
- HEAD permaneceu 1fec408934962f87bdedc3fce05e263a8f7c9f76 e não houve commit ou publicação.

**Riscos/limites**

- prime-agent não foi encontrado no PATH nem no caminho histórico documentado; shellcheck também não está disponível, portanto o smoke test real e essa análise permanecem pendentes.
- A integração live continua exigindo sessão Prime autorizada, PrimeRLMAdapter explícito, /rlm-max-depth 2 por sessão e configuração de orçamento/autorização futura.

**Próximos passos**

- Manter M12 e qualquer execução live fora desta árvore até nova autorização específica; quando houver instalação compatível, fazer somente o smoke test operacional autorizado.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `.prime/agent/prompts/article-bootstrap.md` | `-` | `e2c6a78b7ba5` |
| added | `.prime/agent/prompts/article-checkpoint.md` | `-` | `6281a032e06a` |
| added | `.prime/agent/prompts/article-finalize.md` | `-` | `4809390c52a0` |
| added | `.prime/agent/prompts/article-pause.md` | `-` | `48e6bd2a31e3` |
| added | `.prime/agent/prompts/article-preflight.md` | `-` | `17cdeb2c563e` |
| added | `.prime/agent/prompts/article-resume.md` | `-` | `933189537ff5` |
| added | `.prime/agent/prompts/article-run.md` | `-` | `2c71b663c2f5` |
| added | `.prime/agent/prompts/article-status.md` | `-` | `7e8853e4e29f` |
| added | `.prime/agent/prompts/article-stop.md` | `-` | `7d9a74a1302a` |
| added | `.prime/handoffs/11_para_12.md` | `-` | `3d11ea0dd239` |
| added | `control/test_m11_commands.py` | `-` | `041e9cc2ebf9` |
| added | `docs/runbook.md` | `-` | `081ced68a389` |
| added | `scripts/article_loop_command.py` | `-` | `626e29247e77` |
| modified | `.prime/agent/APPEND_SYSTEM.md` | `09f65d8308cc` | `00651a431820` |
| modified | `.prime/agent/skills/article-loop/SKILL.md` | `2daf907bd773` | `030bc8b30701` |
| modified | `PLANS.md` | `ce451c209d1c` | `8ffcb5c9ec6c` |
| modified | `README.md` | `44c335cc2acd` | `9319ca1f60dd` |
| modified | `bin/check.sh` | `cebf4561239f` | `53cf8c2e4765` |
| modified | `bin/start-prime.sh` | `cebf4561239f` | `5805e1b6f491` |
| modified | `docs/architecture.md` | `71e182c75e53` | `5cdd7fde951e` |
| modified | `docs/compatibility.md` | `03174c609124` | `545e2ce3590f` |
| modified | `docs/decisions.md` | `540ce5851b09` | `bc0718acbe4e` |

### 2026-09-03T05:04:53Z — Commit e publicação da implementação local da M11 concluídos no repositório LOOP-PRIMER; a integração de comandos, templates, runbook, testes e guardrails foi enviada para origin/main sem iniciar execução científica, Prime Agent ou modelos.

- Session ID: `session-m11-publish-20260903`
- Fingerprint final: `769f42631f2e59ed03609f618d6a2a3713c2f4e640d109ce57d98ed945e37dde`
- Git final: `87c26ae37330`; status relevante: 0 item(ns)
- Delta factual: 0 adicionados, 0 modificados, 0 removidos

**Mudanças**

- Criado o commit 87c26ae (feat(m11): add local Prime Agent command integration) com os 26 arquivos preparados da M11.
- Publicado main para https://github.com/Walc21/LOOP-PRIMER.git via git push origin main, sem force push.

**Decisões**

- Manter o histórico de encerramento e o snapshot AI versionados junto do trabalho, conforme AGENTS.md, e registrar a publicação em uma sessão própria.

**Validações**

- git fetch --prune origin concluído; git rev-list --left-right --count HEAD...origin/main retornou 0 0 após o push; HEAD e origin/main apontam para 87c26ae.
- As validações locais da M11 permanecem registradas na sessão anterior: regressão completa 346 testes OK, testes dedicados 15/15 OK, py_compile, bash -n, git diff --check e smoke checks locais.

**Riscos/limites**

- A execução live permanece bloqueada por padrão e não foi iniciada; Prime Agent, modelos, APIs pagas e rede de execução científica não foram usados.

**Próximos passos**

- M12 permanece como próximo marco, sem ação adicional nesta sessão.

### 2026-09-03T05:18:47Z — Avaliada a prontidão para iniciar M12 após a publicação da M11; nenhum código, configuração, execução live, modelo, Prime Agent ou rede foi iniciado nesta sessão. O M12 permanece pendente e seu escopo foi separado das instruções de execução real.

- Session ID: `session-m12-readiness-20260903`
- Fingerprint final: `769f42631f2e59ed03609f618d6a2a3713c2f4e640d109ce57d98ed945e37dde`
- Git final: `af08c798df37`; status relevante: 0 item(ns)
- Delta factual: 0 adicionados, 0 modificados, 0 removidos

**Mudanças**

- Nenhum arquivo de produto ou contrato M0--M11 foi alterado; somente o registro obrigatório desta sessão diagnóstica foi acrescentado.

**Decisões**

- Para iniciar M12, preservar defaults fail-closed e executar apenas implementação offline de orçamento durável, observabilidade e operação prolongada limitada; perfis e execução live continuam opt-in por run.

**Validações**

- Estado observado: main limpa e alinhada com origin/main antes do diagnóstico; M11 publicado em af08c79, com implementação em 87c26ae; a evidência da regressão M11 de 346 testes permanece no handoff 11_para_12.md.

**Riscos/limites**

- O binário Prime Agent não está disponível nesta sessão e a operação live real continua bloqueada; nenhum custo, modelo, credencial ou rede deve ser introduzido para começar o código M12.

**Próximos passos**

- Sob autorização explícita para implementar somente M12, repetir o precheck com suíte completa, inventariar fronteiras consumidoras e definir os contratos do BudgetLedger/observabilidade antes de editar.

### 2026-09-03T06:08:39Z — M12 implementado localmente sobre a base M11: ledger de orçamento durável, observabilidade estruturada redigida, perfis opt-in e status operacional; execução real permanece desabilitada e M13 não foi iniciado.

- Session ID: `session-8285cd8003cfdf5a27bb`
- Fingerprint final: `7580bfaf8dc057fa94fbb59c0b688b1f799b4c873a6647eacd838bb83ec692d2`
- Git final: `af08c798df37`; status relevante: 18 item(ns)
- Delta factual: 6 adicionados, 12 modificados, 0 removidos

**Mudanças**

- Adicionados BudgetLedger e StructuredLogger com eventos append-only/content-addressed, lock, reservas atômicas, reconciliação idempotente, UNCERTAIN, deadlines retomáveis, binding monotônico de configuração e status humano/JSON por limite.
- Adicionados schemas M12, configuração fail-closed, integração de status na ponte local e handoff .prime/handoffs/12_para_13.md; documentação e testes atualizados.

**Decisões**

- Preservar model_execution, APIs pagas, rede, perfis e dry-run desabilitados; live exige autorização explícita vinculada a run, perfil, hash, provider/modelo, teto e timestamp.
- Não alterar orchestrator, state machine, critérios científicos, gates ou conteúdo; não fazer commit/publicação nesta sessão.

**Validações**

- python3 -m unittest control.test_m12_budget_observability control.test_m11_commands control.test_contracts -q: 87 testes aprovados.
- python3 -m unittest discover -s control -q: 366 testes aprovados em 246.975s; somente warning esperado Duplicate name: a.tex no fixture negativo de ZIP.
- python3 -m py_compile nos módulos M12 e scripts/article_loop_command.py: OK; bash bin/check.sh: OK, prime_agent_discovered=false, model_execution_enabled=false, perfis desabilitados.

**Riscos/limites**

- Prime Agent não está disponível nesta máquina; nenhum smoke test live, modelo, rede ou operação prolongada real foi executado. Commit e publicação GitHub permanecem pendentes de autorização explícita.

**Próximos passos**

- Antes de M13, validar a árvore/histórico M12 e decidir explicitamente se deve haver commit; qualquer operação live exige nova configuração versionada e autorização específica por run.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `.prime/agent/skills/article-loop/src/article_loop/budget.py` | `-` | `79e089767cc0` |
| added | `.prime/agent/skills/article-loop/src/article_loop/observability.py` | `-` | `843fb7b0eca7` |
| added | `.prime/handoffs/12_para_13.md` | `-` | `6b6381b53320` |
| added | `config/schemas/budget-event.schema.json` | `-` | `50a2c40ab3ad` |
| added | `config/schemas/observability-event.schema.json` | `-` | `e4d1ac474059` |
| added | `control/test_m12_budget_observability.py` | `-` | `4c18cab99ae3` |
| modified | `.prime/agent/skills/article-loop/SKILL.md` | `030bc8b30701` | `e2400db7b022` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/__init__.py` | `7687ae22a123` | `14d02ad12848` |
| modified | `PLANS.md` | `8ffcb5c9ec6c` | `3e2b5a9540fa` |
| modified | `README.md` | `9319ca1f60dd` | `e3177b62485f` |
| modified | `bin/check.sh` | `53cf8c2e4765` | `7da00cfe872e` |
| modified | `config/budgets.yaml` | `3c70f903c84d` | `6000c58d4ea4` |
| modified | `control/test_contracts.py` | `e14816e0f348` | `feb03d159a19` |
| modified | `control/test_m11_commands.py` | `041e9cc2ebf9` | `344693b92f05` |
| modified | `docs/architecture.md` | `5cdd7fde951e` | `756dc8e755cb` |
| modified | `docs/decisions.md` | `bc0718acbe4e` | `aa038a86a30e` |
| modified | `docs/runbook.md` | `081ced68a389` | `f067531f3d3d` |
| modified | `scripts/article_loop_command.py` | `626e29247e77` | `09b6ae4eafc7` |

### 2026-09-03T19:09:00Z — Avaliação diagnóstica do estado atual após a publicação do M12: integridade local e regressão completa aprovadas, branch main alinhada ao origin/main, M13 ainda pendente e execução live corretamente bloqueada.

- Session ID: `session-m12-evaluation-20260903`
- Fingerprint final: `7580bfaf8dc057fa94fbb59c0b688b1f799b4c873a6647eacd838bb83ec692d2`
- Git final: `e5eb78fbce40`; status relevante: 0 item(ns)
- Delta factual: 0 adicionados, 0 modificados, 0 removidos

**Mudanças**

- Nenhum arquivo de produto, contrato, configuração, código ou marco foi alterado; somente o registro obrigatório desta sessão diagnóstica e o contexto gerado foram atualizados.

**Decisões**

- Considerar o M12 tecnicamente saudável para avançar ao planejamento do M13, preservando os defaults fail-closed e sem autorizar Prime Agent, modelos, rede ou APIs pagas.

**Validações**

- bash bin/check.sh: status success; live_ready=false; model_execution_enabled=false; paid_apis_enabled=false; perfis calibration e overnight desabilitados; prime_agent_discovered=false.
- python3 -m unittest discover -s control -q: 366 testes aprovados em 231.770s; único warning conhecido Duplicate name: a.tex no fixture adversarial de ZIP.
- git rev-list --left-right --count HEAD...origin/main retornou 0 0; HEAD e origin/main apontam para e5eb78f feat(m12): add durable budget observability.

**Riscos/limites**

- O handoff 12_para_13.md ainda descreve corretamente a sessão de implementação pré-commit, mas sua frase de que não houve commit/publicação está desatualizada em relação ao estado atual e pode confundir o próximo operador.
- M13 possui objetivo geral, mas ainda carece de um plano detalhado e critérios sistêmicos específicos antes da implementação.

**Próximos passos**

- Se autorizado, planejar M13 em PLANS.md e docs/decisions.md, corrigir a superfície de handoff/publicação e então implementar testes sistêmicos e empacotamento sem executar o artigo real.

### 2026-09-03T20:22:56Z — M12.5 implementado como camada aditiva de routing de inferência governada pelo BudgetLedger M12, sem alterar M6 e sem iniciar M13; aceitação integral permanece aberta somente pelo smoke HTTP loopback bloqueado pelo sandbox.

- Session ID: `session-2dffb2bba91ea37f3f05`
- Fingerprint final: `42f5751f17afacc240f805894624af2f74ceb14298b9e5d6facf79791a1600ba`
- Git final: `e5eb78fbce40`; status relevante: 20 item(ns)
- Delta factual: 5 adicionados, 15 modificados, 0 removidos

**Mudanças**

- Adicionados registry, router, request/result/receipt, store write-once e runtime transacional em inference.py.
- Adicionados fake determinístico e backend local OpenAI-compatible limitado a loopback em inference_backends.py, além do schema de receipt.
- Estendidos autorização routed hash-bound, status, preflight/check, observabilidade, documentação, testes e handoff 12_5_para_13.

**Decisões**

- PrimeRLMAdapter.spawn(prompt, name) permaneceu intacto; seleção de modelo por filho foi registrada como unsupported_verified porque o Prime Agent não está instalado neste host.
- Targets pagos permanecem recusados porque M12 não possui enforcement monetário duro pré-chamada; defaults inference/local/remote/paid permanecem falsos.
- M12.5 não é executor de papel RLM: opera apenas pedidos derivados de AgentTask sem substituir handles, receipts ou hierarquia M6.

**Validações**

- python3 -m unittest discover -s control -q: 395 testes aprovados, 1 skip do fixture HTTP loopback.
- Suítes M12.5, M12, M11 e contratos: 116 testes aprovados, 1 skip do fixture HTTP loopback.
- py_compile dos Python alterados/criados, bash -n bin/check.sh, bin/check.sh, json.tool do schema e git diff --check: aprovados.
- bin/check.sh confirmou inference desabilitada, zero targets, paid_runtime_ready false, Prime não descoberto e policy hash estável.

**Riscos/limites**

- O sandbox recusou socket loopback e a elevação foi negada; o critério J não foi provado e M12.5 não foi marcado como integralmente aceito.
- shellcheck não está instalado; não houve instalação global.

**Próximos passos**

- Antes de M13, executar control.test_m125_inference_routing.M125LoopbackBackendTests em ambiente que permita socket local e confirmar todos os cenários HTTP.
- Manter Prime, modelos, rede remota e targets pagos desabilitados até nova autorização específica.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `.prime/agent/skills/article-loop/src/article_loop/inference.py` | `-` | `2b6a50fad3ad` |
| added | `.prime/agent/skills/article-loop/src/article_loop/inference_backends.py` | `-` | `7158723dfaa6` |
| added | `.prime/handoffs/12_5_para_13.md` | `-` | `e73540e766e6` |
| added | `config/schemas/inference-receipt.schema.json` | `-` | `21ae25d44751` |
| added | `control/test_m125_inference_routing.py` | `-` | `a580527f775b` |
| modified | `.prime/agent/skills/article-loop/SKILL.md` | `e2400db7b022` | `e222eb98ae1c` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/__init__.py` | `14d02ad12848` | `09902d2c1a1f` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/budget.py` | `79e089767cc0` | `b0f41c695b43` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/observability.py` | `843fb7b0eca7` | `bb380abefcb5` |
| modified | `PLANS.md` | `3e2b5a9540fa` | `f29dacfae80c` |
| modified | `README.md` | `e3177b62485f` | `99310c8e1ff7` |
| modified | `bin/check.sh` | `7da00cfe872e` | `811b45294a81` |
| modified | `config/budgets.yaml` | `6000c58d4ea4` | `bc9498cc9e79` |
| modified | `control/test_contracts.py` | `feb03d159a19` | `00fa5c6c2444` |
| modified | `docs/architecture.md` | `756dc8e755cb` | `5dd2e60cd660` |
| modified | `docs/compatibility.md` | `545e2ce3590f` | `0d9cefb2b755` |
| modified | `docs/decisions.md` | `aa038a86a30e` | `eb992674718f` |
| modified | `docs/runbook.md` | `f067531f3d3d` | `77c793dce656` |
| modified | `scripts/ai_context.py` | `3f7517e51d98` | `030ac491a33d` |
| modified | `scripts/article_loop_command.py` | `09b6ae4eafc7` | `fdd07a8a61cd` |

### 2026-09-03T20:28:25Z — Publicação do M12.5 concluída no GitHub por fast-forward, preservando a limitação declarada do smoke HTTP loopback e sem iniciar M13.

- Session ID: `session-8099f5a97e6e063424d5`
- Fingerprint final: `686362339e8f53fe7142b94031908e3133136fe3b8aadf602bdc362c273fa1f6`
- Git final: `dbf411c80ae0`; status relevante: 2 item(ns)
- Delta factual: 0 adicionados, 2 modificados, 0 removidos

**Mudanças**

- Atualizados PLANS.md e o handoff 12_5_para_13.md com o commit e a publicação efetivamente observados.

**Decisões**

- A implementação e o registro de publicação permanecem em commits separados para que o histórico final reflita fatos já confirmados.
- Nenhum force-push, rebase, modelo, Prime Agent, target pago ou M13 foi executado.

**Validações**

- git fetch --prune origin e git rev-list confirmaram HEAD...origin/main em 0 0 antes do commit.
- bin/check.sh passou e as suítes M12.5/M12/M11/contratos executaram 116 testes com sucesso e 1 skip de loopback antes da publicação.
- Commit dbf411c publicado com sucesso: e5eb78f..dbf411c main -> main.

**Riscos/limites**

- O critério J do M12.5 continua pendente porque o sandbox não permite abrir o fixture HTTP loopback.

**Próximos passos**

- Executar o fixture loopback em ambiente permitido antes de declarar aceitação integral do M12.5 ou iniciar M13.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `.prime/handoffs/12_5_para_13.md` | `e73540e766e6` | `d1b564d69d81` |
| modified | `PLANS.md` | `f29dacfae80c` | `3d5999659a31` |

### 2026-09-03T21:27:30Z — Corrigiu a falha da CI M12.5 causada por conexão HTTP fechada sem resposta, publicou a correção e confirmou a matriz GitHub Actions Python 3.11–3.13 integralmente verde.

- Session ID: `session-87ecd36b0d1ddca820bd`
- Fingerprint final: `c2a68d3819a2b48ec4e0c3ef4fe42fd337ec12dc6baef2f17ebdc48632fb61e8`
- Git final: `49fad01ca1a0`; status relevante: 3 item(ns)
- Delta factual: 0 adicionados, 8 modificados, 0 removidos

**Mudanças**

- Inference backend agora normaliza RemoteDisconnected, ConnectionResetError e BrokenPipeError diretos como BACKEND_FAILURE pós-envio.
- Cobertura socketless reproduz a exceção exata e testes M11 deixaram de depender da presença real do binário Prime no host.
- README, PLANS, ADR-032, compatibilidade e handoff M12.5 foram sincronizados com a correção e a evidência da CI.

**Decisões**

- Falhas de transporte após envio preservam sent=True e levam a reserva para UNCERTAIN; não há retry implícito nem ampliação de rede ou custo.
- A presença de prime-agent no PATH é diagnóstico, não autorização para sessão, modelo ou API.

**Validações**

- Suíte local completa: 396 testes passaram em 280.579s, com 1 skip explícito do fixture loopback bloqueado pelo sandbox.
- Subconjunto M12.5/M12/M11/contratos: 117 testes passaram, com 1 skip local.
- bin/check.sh passou com inference, execução de modelo e targets pagos desabilitados.
- GitHub Actions run 33807419247 passou em Python 3.11, 3.12 e 3.13; 399 testes por job em 213.130s, 248.472s e 233.922s, respectivamente.
- git diff --check passou após a sincronização documental.

**Riscos/limites**

- shellcheck permanece indisponível localmente e não foi instalado; o sandbox local continua sem socket loopback, mitigado pela matriz CI real.

**Próximos passos**

- M13 permanece não iniciado e requer solicitação própria; Prime Agent, modelo e targets pagos exigem autorização específica.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `.prime/agent/skills/article-loop/src/article_loop/inference_backends.py` | `7158723dfaa6` | `65c9818e9c4e` |
| modified | `.prime/handoffs/12_5_para_13.md` | `d1b564d69d81` | `87908f4d39d0` |
| modified | `PLANS.md` | `3d5999659a31` | `3debcefda243` |
| modified | `README.md` | `99310c8e1ff7` | `1471a09b2065` |
| modified | `control/test_m11_commands.py` | `344693b92f05` | `bccd8c0c2165` |
| modified | `control/test_m125_inference_routing.py` | `a580527f775b` | `175fbc5fd342` |
| modified | `docs/compatibility.md` | `0d9cefb2b755` | `f532eaf0a54a` |
| modified | `docs/decisions.md` | `eb992674718f` | `b8a1c20354ac` |

### 2026-09-03T22:46:53Z — M12.5.1 Phase A implementada e validada localmente como ligação dual end-to-end por departamento, com contexto autorizado, privacidade por run, output científico durável, teto monetário inteiro e recovery sem reinferência; configuração e live permanecem deliberadamente inativos e M13 não foi iniciado.

- Session ID: `session-6c69bb7f70ed5c903379`
- Fingerprint final: `1e80fe6ddcc01dc9f783314b6f6795f52ea1ac71c946108a5bfea483e18b30fd`
- Git final: `ba316b50a707`; status relevante: 22 item(ns)
- Delta factual: 6 adicionados, 16 modificados, 0 removidos

**Mudanças**

- Adicionado execution.py com ExecutionPolicy, ContextMaterializer, RoutedControlAdapter, DualExecutionAdapter, DualExecutionController e readiness em três níveis.
- InferenceRuntime agora vincula context_hash e privacy_mode, publica output científico write-once antes do receipt, recupera crashes sem nova chamada e suporta pricing canônico e backend remoto HTTPS sem proxy ou redirect.
- BudgetLedger agora reserva, reconcilia e reporta custo inteiro sob teto de 10000000 microunits USD; autorização vincula teto e moeda, usage desconhecido conserva reserva e overrun bloqueia novas chamadas.
- Configuração ativa ganhou execution disabled, mapa vazio e privacy deny_remote; schema, CLI check/status, documentação, exemplo humano, inventário model-driven e handoff M12.5.1 foram sincronizados.
- Cobertura offline M12.5.1 adicionada para S10 routed e S20 Prime simulado, privacidade, contexto, custo, júri por model, backend remoto mockado, concorrência e recuperação.

**Decisões**

- Seleção ocorre apenas por departamento: Prime preserva spawn prompt/name e routed usa controle local persistente para Sxx com workers no InferenceRuntime, convergindo no receipt e DepartmentPacket M6.
- A capacidade monetária paid_runtime_ready é verdadeira no código, mas execution, inference, targets, routes, allow_paid e live continuam desabilitados até configuração e autorização humanas.
- Independência de júri recomenda comparação por model; independence_group legacy permanece interpretável.
- Prime 0.9.1 foi observado apenas por versão, portanto seleção de modelo por filho permanece unknown_on_current_version.

**Validações**

- python3 -m unittest discover -s control -q: 410 testes aprovados em 268.029s, com 1 skip histórico do fixture loopback.
- Suítes M12.5.1, M12.5 e M12 dedicadas: 63 testes aprovados, com 1 skip histórico.
- py_compile dos módulos Python alterados/criados e do teste M12.5.1: aprovado.
- git diff --check e bash -n bin/check.sh bin/start-prime.sh: aprovados.
- bin/check.sh: aprovado; implementation_ready=true, configuration_ready=false, live_ready=false, zero targets/rotas, deny_remote, teto 10000000 USD.

**Riscos/limites**

- Nenhum smoke Prime, modelo local/remoto, rede real, API paga, credencial ou artigo real foi executado; configuração humana permanece obrigatória.
- A seleção Prime de modelo por filho em 0.9.1 não foi auditada além da versão e permanece unknown_on_current_version.
- A matriz GitHub Actions Python 3.11-3.13 não foi disparada nesta sessão; o workflow existente executará os novos testes offline quando publicado.

**Próximos passos**

- Configuração humana futura deve escolher mapa S10-S50, targets e modelos, endpoints, preços, rotas, privacy mode e autorização de run sem gravar segredo.
- Qualquer smoke live precisa de pedido e autorização separados; M13 continua pendente.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `.prime/agent/skills/article-loop/src/article_loop/execution.py` | `-` | `6f8d86ccf803` |
| added | `.prime/handoffs/12_5_1_human_configuration.md` | `-` | `c679cec819ee` |
| added | `control/test_m1251_dual_execution.py` | `-` | `35ee4e9c290a` |
| added | `docs/examples/m1251-human-configuration.yaml` | `-` | `26746a614b84` |
| added | `docs/m1251-phase-a-audit.md` | `-` | `81596d449460` |
| added | `docs/model-driven-surfaces.md` | `-` | `d1fb59e1b2b6` |
| modified | `.prime/agent/skills/article-loop/SKILL.md` | `e222eb98ae1c` | `cf254794a433` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/__init__.py` | `09902d2c1a1f` | `36a0327810c3` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/budget.py` | `b0f41c695b43` | `f4fc7767d6ba` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/inference.py` | `2b6a50fad3ad` | `5cfc2e6cd444` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/inference_backends.py` | `65c9818e9c4e` | `395c005c5cb7` |
| modified | `PLANS.md` | `3debcefda243` | `cfc7ee23f0f9` |
| modified | `README.md` | `1471a09b2065` | `d796aa3ec6e7` |
| modified | `bin/check.sh` | `811b45294a81` | `275ae836c32f` |
| modified | `config/budgets.yaml` | `bc9498cc9e79` | `dc93a24029f2` |
| modified | `config/schemas/inference-receipt.schema.json` | `21ae25d44751` | `76f33221f512` |
| modified | `control/test_m125_inference_routing.py` | `175fbc5fd342` | `d6c8ab02fb27` |
| modified | `docs/architecture.md` | `5dd2e60cd660` | `018f518aebba` |
| modified | `docs/compatibility.md` | `f532eaf0a54a` | `be929550d830` |
| modified | `docs/decisions.md` | `b8a1c20354ac` | `5f708176ecd7` |
| modified | `docs/runbook.md` | `77c793dce656` | `881f74e79ed6` |
| modified | `scripts/article_loop_command.py` | `fdd07a8a61cd` | `0699196206ee` |

### 2026-09-03T22:47:46Z — Correção documental final da M12.5.1: o handoff humano agora reproduz literalmente todos os campos obrigatórios do prompt, sem preencher provider, runtime, endpoint, modelo, capacidade, credencial, preço, privacidade, mapa, rota ou autorização.

- Session ID: `session-6a3c1d5e54217ee4379f`
- Fingerprint final: `0b054cba462067ce0b3592858ffda29ff3d7071c517e66f3707fe23f32db4770`
- Git final: `ba316b50a707`; status relevante: 22 item(ns)
- Delta factual: 0 adicionados, 1 modificados, 0 removidos

**Mudanças**

- A checklist HUMAN CONFIGURATION REQUIRED foi alinhada palavra por palavra ao contrato da Phase A.

**Decisões**

- Manter todos os campos humanos vazios; exemplos permanecem somente em docs/examples e a configuração ativa continua disabled.

**Validações**

- Leitura do trecho CODE COMPLETE até HUMAN CONFIGURATION REQUIRED confirmou os dois headings e os 15 campos exatos.
- git diff --check e bin/check.sh passaram após a correção documental.

**Riscos/limites**

- Configuração humana e qualquer smoke live continuam fora da Phase A.

**Próximos passos**

- O humano deverá preencher a checklist em fase posterior e autorizar separadamente qualquer execução live.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `.prime/handoffs/12_5_1_human_configuration.md` | `c679cec819ee` | `72b1a756244d` |

### 2026-09-03T22:48:42Z — Sincronização final da CI para M12.5.1 sem enfraquecer a matriz ou a suite.

- Session ID: `session-6cd6a464487f4b67221c`
- Fingerprint final: `eb05e97f915ce52ccdf84dd6a04f7a3796c78887835084ce2a816783ff9601b3`
- Git final: `ba316b50a707`; status relevante: 23 item(ns)
- Delta factual: 0 adicionados, 1 modificados, 0 removidos

**Mudanças**

- Workflow CI renomeado para M0-M12.5.1 e passou a executar sintaxe shell e bin/check.sh antes da regressão descoberta automaticamente.

**Decisões**

- Preservar a matriz Python 3.11, 3.12 e 3.13 e o unittest discover completo; testes M12.5.1 permanecem offline e o backend remoto é mockado.

**Validações**

- YAML do workflow foi carregado por PyYAML; bash -n, bin/check.sh e git diff --check passaram.

**Riscos/limites**

- O workflow atualizado não foi disparado no GitHub nesta sessão; validação de CI remota ocorrerá somente após publicação futura.

**Próximos passos**

- Ao publicar futuramente, observar os três jobs 3.11-3.13 sem habilitar modelo, API ou target.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `.github/workflows/ci.yml` | `fe0474481ca7` | `61350e140d71` |

### 2026-09-03T23:22:24Z — Publicação da M12.5.1 Phase A concluída no GitHub por fast-forward, incluindo correção pré-publicação do contrato executável de bin/check.sh e validação local/remota integral.

- Session ID: `session-709c7c983dca0c4e1fcc`
- Fingerprint final: `8126b4d30eb36acca6affdaa8c270321c31ba9c2c75ba77befd116ed0340f766`
- Git final: `e238b8891baa`; status relevante: 0 item(ns)
- Delta factual: 0 adicionados, 3 modificados, 0 removidos

**Mudanças**

- Commit e238b88 (feat(m12.5.1): add dual execution phase A) publicou os 28 arquivos de implementação, contratos, testes, documentação e handoff em origin/main.
- O teste de scaffold passou a exigir bin/check.sh executável, preservando bin/start-prime.sh não executável e bin/preflight.sh executável, conforme a invocação literal da Phase A e da CI.

**Decisões**

- Publicar somente por push normal fast-forward, sem force-push ou reescrita; manter execução, modelos, targets remotos e APIs pagas desabilitados.

**Validações**

- git fetch --prune origin e git rev-list --left-right --count HEAD...origin/main confirmaram alinhamento 0 0 antes da publicação.
- python3 -m unittest discover -s control -p test_*.py -q passou com 410 testes e 1 skip em 255.130 s após a correção contratual.
- py_compile dos Python alterados, git diff --check, bash -n bin/check.sh bin/start-prime.sh, bin/check.sh e varredura de padrões óbvios de credenciais passaram.
- GitHub Actions run 33816899914 concluiu com sucesso a matriz Python 3.11, 3.12 e 3.13 para o commit e238b88.

**Riscos/limites**

- Configuração humana, endpoints, modelos, preços, credencial via ambiente e autorização live continuam ausentes; configuration_ready e live_ready permanecem false.

**Próximos passos**

- Preencher .prime/handoffs/12_5_1_human_configuration.md em uma fase humana posterior antes de qualquer smoke live; M13 permanece não iniciado.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `PLANS.md` | `cfc7ee23f0f9` | `c5f7127e3b7d` |
| modified | `control/test_contracts.py` | `00fa5c6c2444` | `aa3d80791b67` |
| modified | `docs/decisions.md` | `5f708176ecd7` | `83b3f1f550c5` |

### 2026-09-05T01:41:08Z — M12.5.1 clean promotion candidate finalized offline from baseline 562cbbf.

- Session ID: `session-3ec0ef358b1a25a76f99`
- Fingerprint final: `6312949b3a5dc49eb7a85f20f7dddf5b430c000a16b25b9e25be917cc663b8c7`
- Git final: `562cbbf28447`; status relevante: 10 item(ns)
- Delta factual: 0 adicionados, 10 modificados, 0 removidos

**Mudanças**

- Promoted the final model-scientific-payload and LOOP-trusted-envelope composition with generic structured output and canonical downstream AgentProposal validation.
- Excluded the B1 branch-bound live smoke harness from the promotion because it was not a reusable fail-closed diagnostic.
- Updated PLANS.md and ADR-033 with the promoted ownership boundary and configuration limits.

**Decisões**

- Keep canonical AgentTask and AgentProposal schemas, M6 receipt identity validation, and inert budgets configuration unchanged.
- Do not retain an alternate model-supplied identity-constant path or an implicit-live diagnostic harness.

**Validações**

- Focused tests passed: test_m125_inference_routing 36 tests with 1 loopback skip; test_m1251_dual_execution 14; test_m6_orchestration 43.
- Full regression passed: python3 -m unittest discover -s control -q, 417 tests with 1 loopback skip.
- py_compile, git diff --check, bin/check.sh, schema/config diff, and tracked-artifact scan passed.

**Riscos/limites**

- No live model, provider, network call, remote target, paid API, or M13 execution occurred; human configuration is still required for any future live smoke.

**Próximos passos**

- Review and merge this one promotion commit only after separate authorization; do not configure or execute inference.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `.gitignore` | `1d23a95bcdb4` | `293dc90f4e63` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/__init__.py` | `36a0327810c3` | `186ba528897d` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/execution.py` | `6f8d86ccf803` | `c777f1e7d74f` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/inference.py` | `5cfc2e6cd444` | `ab4a01e90de4` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/inference_backends.py` | `395c005c5cb7` | `a538afb419e9` |
| modified | `PLANS.md` | `c5f7127e3b7d` | `bf3ba60f6e1a` |
| modified | `control/test_m1251_dual_execution.py` | `35ee4e9c290a` | `4a4206f336c4` |
| modified | `control/test_m125_inference_routing.py` | `d6c8ab02fb27` | `2a700ab8ead2` |
| modified | `control/test_m6_orchestration.py` | `748aab32dc74` | `c8a90dee0e45` |
| modified | `docs/decisions.md` | `83b3f1f550c5` | `7c9ca1da4295` |

### 2026-09-05T01:42:06Z — M12.5.1 clean promotion committed locally on m1251-promote-local.

- Session ID: `session-f63fe2314358a393aae7`
- Fingerprint final: `6312949b3a5dc49eb7a85f20f7dddf5b430c000a16b25b9e25be917cc663b8c7`
- Git final: `973d0d46e74f`; status relevante: 0 item(ns)
- Delta factual: 0 adicionados, 0 modificados, 0 removidos

**Mudanças**

- Created the single clean promotion commit 973d0d46e74fc9a9110669fab86ff3a5e89bc43e from baseline 562cbbf.

**Decisões**

- Keep the promotion local only: no push, no merge to main, no live configuration.

**Validações**

- Post-commit working tree was clean; the committed candidate had already passed focused tests, full 417-test regression, py_compile, git diff --check, bin/check.sh, schema/config invariants, and artifact scan.

**Riscos/limites**

- Remote providers, paid inference, and live smoke remain disabled; M13 remains unstarted.

**Próximos passos**

- A separately authorized reviewer may inspect or merge the single promotion commit; do not run inference without explicit human configuration and authorization.

### 2026-09-05T00:02:51Z — Revisão diagnóstica offline e somente leitura da arquitetura de segurança no HEAD 562cbbf, com mapeamento dos caminhos Prime e routed, recursos efetivos, fluxos privilegiados e controles por componente.

- Session ID: `session-5bc7ce151a9d498d5175`
- Fingerprint final: `8126b4d30eb36acca6affdaa8c270321c31ba9c2c75ba77befd116ed0340f766`
- Git final: `562cbbf28447`; status relevante: 0 item(ns)
- Delta factual: 0 adicionados, 0 modificados, 0 removidos

**Mudanças**

- Nenhum código-fonte, configuração ou artefato científico foi alterado; somente o histórico/contexto obrigatório de handoff foi atualizado.

**Decisões**

- Manter separados os caminhos Prime, inferência local e inferência remota, além das autoridades independentes de ingestão, estado, síntese, júri e finalização.

**Validações**

- Inspeção estática offline com rg, nl e sed; HEAD confirmado como 562cbbf28447b6c4b3a4002aabedfd0a22a4bdcf; nenhum código da aplicação, modelo, Prime Agent ou serviço externo foi executado.

**Riscos/limites**

- Implementação externa do Prime Agent, permissões efetivas do host e serviço remoto/TLS não estão no repositório e permanecem pré-requisitos não verificados.

**Próximos passos**

- O agente principal deve verificar os fatos materiais e incorporar o threatModel e as divergências documentais ao resultado da varredura.

### 2026-09-05T02:45:32Z — M13 concluído como camada de aceitação de sistema e auditoria independente offline: ciclos sintéticos completos até promoção, Pareto e rejeição, com preservação do PDF original e checkpoint local revisável sobre b15526e.

- Session ID: `session-89af3d3114afa07a3873`
- Fingerprint final: `d935abdefc074d8bf3c6a6eaa9c67f0f0d51ca454592bc74a3d358e607f11879`
- Git final: `b15526ef4aca`; status relevante: 16 item(ns)
- Delta factual: 6 adicionados, 10 modificados, 0 removidos

**Mudanças**

- Adicionados control/m13_fixture.py, control/test_m13_system_delivery.py e scripts/m13_system_check.py: 25 cenários de aceitação e CLI com conservação opcional de evidência ou auditoria somente leitura.
- Adicionado article_loop.delivery.verify_delivery, exportado pela fachada: revalidação composta M3/M7/M8/M9/M10, manifesto/ponteiro/receipt/evento final e cadeia budget/route/output/inference receipt/M6.
- Estendida somente a revalidação explícita M9 para FINALIZATION_APPLIED do mesmo ciclo, sem autorizar refoco normal depois de conclusão.
- Atualizados PLANS, ADR-034, arquitetura, README, runbook, skill, handoff 13_final, descoberta do handoff final no gerador de contexto e rótulos da CI para M13.

**Decisões**

- Manter os schemas, 21 papéis, 16 estados e 9 ações intactos. Nenhuma dependência nova, configuração live, modelo, Prime Agent ou provedor remoto executado.
- Usar dublês apenas nas fronteiras externas e modelos fictícios distintos para provar independência no router. Adaptadores operacionais routed de júri/meta-review M8 permanecem posteriores.
- Auditoria cobre disposições PROMOTE/ARCHIVE_PARETO/REJECT em workspace quiescente e no caminho original; não fabrica o pacote terminal FINALIZE de M10.1.
- Encerrar com um único commit local na branch m13-system-delivery, sem push nem merge para main.

**Validações**

- python3 -m unittest control.test_m13_system_delivery -q: 25 testes OK, 0 skips.
- python3 scripts/m13_system_check.py --keep-workspace (novo caminho externo): PASS, 25 testes, 0 erros/falhas/skips, seguido de ciclo routed conservado com 3 chamadas fake reconciliadas.
- CLI --verify-root em processo independente: relatório idêntico ao conservado e inventário completo de bytes/modos inalterado.
- python3 -m unittest control.test_m9_diagnosis control.test_m10_policy_finalization control.test_ai_handoff -q: 82 testes OK em 141.514s.
- python3 -m unittest discover -s control -q: 445 testes OK, 0 skips, em 362.995s no Python 3.14.4; apenas fixtures HTTP loopback legados, sem rede externa.
- python3 -m unittest control.test_ai_handoff -q depois da sincronização documental: 8 testes OK.
- python3 -m py_compile scripts/*.py control/*.py .prime/agent/skills/article-loop/src/article_loop/*.py: OK. AST com feature_version=(3,11): 50 arquivos OK.
- git diff --check, git diff --cached --check e bin/check.sh: OK. Configuração segue execution/inference/local/remote/paid desabilitada e sem targets.
- git diff b15526e em config/system.yaml, budgets.yaml, schemas e roles: nenhum delta. Auditoria dos caminhos runtime rastreados encontrou somente .gitkeep; pesquisa contextual de segredos novos encontrou apenas api_key_env=None e nomes de arquivos proibidos em testes.
- PDF sintético original: 644 bytes; SHA-256 antes/depois 1a491e111064f6daae4011f46337a188de4e91337d692b3cc74b4b221d17501f, com modo e tamanho preservados.

**Riscos/limites**

- Aceitação offline não prova qualidade científica geral, júri routed live, Prime Agent live, provedor remoto ou pagamento. Nenhum artigo real executado.
- Python 3.11 local não possui jsonschema; nenhuma instalação foi feita. A matriz CI 3.11/3.12/3.13 não foi executada nesta sessão sem publicação.
- Receipts M6 preservam locators absolutos pelo contrato existente; não se promete migração por cópia nem igualdade byte a byte entre hosts. Relatório m13-delivery.json é derivado e a CLI recompõe a evidência autoritativa.

**Próximos passos**

- Revisar o commit local e executar a matriz CI somente quando houver autorização para publicação.
- Configuração de provedor, inferência live e adaptadores routed de júri/meta-review exigem trabalho e autorização separados.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `.prime/agent/skills/article-loop/src/article_loop/delivery.py` | `-` | `a02991dcb9ea` |
| added | `.prime/handoffs/13_final.md` | `-` | `7f905635a87c` |
| added | `control/m13_fixture.py` | `-` | `ae2eb464e2f7` |
| added | `control/test_m13_system_delivery.py` | `-` | `4da13c01f8dd` |
| added | `docs/m13-system-acceptance.md` | `-` | `da913ee40db2` |
| added | `scripts/m13_system_check.py` | `-` | `5522dba9bbd4` |
| modified | `.github/workflows/ci.yml` | `61350e140d71` | `bf1d737ea098` |
| modified | `.prime/agent/skills/article-loop/SKILL.md` | `cf254794a433` | `7177a152fcde` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/__init__.py` | `186ba528897d` | `2aa366464002` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/diagnosis.py` | `5c60264a38c7` | `fcb74adb4501` |
| modified | `PLANS.md` | `bf3ba60f6e1a` | `9308c5ab2da1` |
| modified | `README.md` | `d796aa3ec6e7` | `bf2c1e350275` |
| modified | `docs/architecture.md` | `018f518aebba` | `95593b17c02d` |
| modified | `docs/decisions.md` | `7c9ca1da4295` | `ac0e6d647793` |
| modified | `docs/runbook.md` | `881f74e79ed6` | `36e8d856a1aa` |
| modified | `scripts/ai_context.py` | `030ac491a33d` | `49f09af19c29` |

### 2026-09-05T02:47:51Z — Encerramento pós-commit de M13: implementação e documentação consolidadas no commit local e9cb259, com refresh final dos artefatos gerados de handoff.

- Session ID: `session-00f1ff5cffdb3d788812`
- Fingerprint final: `d935abdefc074d8bf3c6a6eaa9c67f0f0d51ca454592bc74a3d358e607f11879`
- Git final: `e9cb259b5325`; status relevante: 0 item(ns)
- Delta factual: 0 adicionados, 0 modificados, 0 removidos

**Mudanças**

- O commit e9cb259 (feat(m13): prove offline system and delivery path) preservou a implementação validada e os 20 arquivos da entrega; nenhum código ou configuração de produto foi alterado depois dele.
- Atualização somente de docs/AI_HISTORY.md, docs/ai_sessions.jsonl, docs/ai_snapshot.json e AI_CONTEXT.md para incorporar o checkpoint Git real.

**Decisões**

- Usar um segundo commit exclusivamente de histórico/contexto: a verificação pós-commit confirmou que o preview Git gerado torna o snapshot textual anterior stale. Isso mantém o handoff atual sem reescrever ou emendar commits.
- Preservar main/origin/main em b15526e; nenhum push, merge para main ou execução live.

**Validações**

- Após e9cb259, git status --short estava vazio.
- python3 scripts/ai_context.py --check após o commit identificou stale no preview Git; fontes e fingerprint científico permaneceram os mesmos.
- Validação consolidada do código de e9cb259: aceitação M13 25 testes, adjacentes 82 testes, regressão completa 445 testes, 0 skips; py_compile, diff checks e bin/check.sh OK.
- Auditoria independente da evidência externa preservada: relatório idêntico e bytes/modos inalterados; PDF sintético de 644 bytes mantém SHA-256 1a491e111064f6daae4011f46337a188de4e91337d692b3cc74b4b221d17501f.

**Riscos/limites**

- Validação live e matriz CI remota permanecem não executadas; o checkpoint é exclusivamente local.

**Próximos passos**

- Revisar o checkpoint local. Publicação e validação live dependem de autorização separada.

### 2026-09-05T04:26:25Z — M13.1 encerrado: identidade de avaliador routed foi separada dos 21 papeis RLM e a documentacao final foi reconciliada.

- Session ID: `session-c26899f255e8b0ba8569`
- Fingerprint final: `954acc19950ddfe231af20e9534569f91156c9ba3dcf5728c1255d81abaf3062`
- Git final: `ac49084f1fe0`; status relevante: 3 item(ns)
- Delta factual: 2 adicionados, 10 modificados, 0 removidos

**Mudanças**

- InferenceRequest e InferenceReceipt distinguem actor evaluator de routing_role_id; receipts de avaliador usam o contrato 1.2.0.
- PLANS.md, ADR-035 e arquitetura registram compatibilidade legada, propriedade do protocolo pelo LOOP e replay duravel sem reinferencia.

**Decisões**

- routing_role_id e autoridade de politica, enquanto actor_id identifica juror ou meta-reviewer; avaliadores nao sao papeis canonicos.

**Validações**

- M13.1 14/14, regressao adjacente 135/135, check M13 25/25 offline e regressao completa 465/465 sem falhas, erros ou skips.
- control.test_ai_handoff: 8 testes passaram; git diff --check passou.

**Riscos/limites**

- Configuracao, autorizacao e chamadas live permanecem ausentes; nenhuma chamada externa, de modelo ou paga ocorreu.

**Próximos passos**

- Revisar o commit final local antes de qualquer publicacao; push, merge e PR permanecem fora do escopo.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `.prime/agent/skills/article-loop/src/article_loop/routed_evaluation.py` | `-` | `6e0534886bc9` |
| added | `control/test_m131_routed_evaluation.py` | `-` | `3cf7058ec230` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/__init__.py` | `2aa366464002` | `aec1d2b67a19` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/budget.py` | `f4fc7767d6ba` | `1fa4c6dfc435` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/evaluation.py` | `8babd430c3b6` | `1c2da4a593f4` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/inference.py` | `ab4a01e90de4` | `7eb77ab24667` |
| modified | `PLANS.md` | `9308c5ab2da1` | `04b1bef26303` |
| modified | `config/schemas/inference-receipt.schema.json` | `76f33221f512` | `04326435eee4` |
| modified | `control/m13_fixture.py` | `ae2eb464e2f7` | `da4d3cd326d8` |
| modified | `control/test_m125_inference_routing.py` | `2a700ab8ead2` | `d8430f7f3acf` |
| modified | `docs/architecture.md` | `95593b17c02d` | `a68d45758893` |
| modified | `docs/decisions.md` | `ac0e6d647793` | `550ec38b4882` |

### 2026-09-05T05:00:25Z — Ciclo de contexto de IA redesenhado: início read-only e publicação somente em checkpoint explícito.

- Session ID: `session-7cd5dccaedab1ffa7fb9`
- Fingerprint final: `673811e8640f901cd6579e3b09ed7e1133a9003f07c76870aa39ca17faf8fbc5`
- Git final: `27b83658659e`; status relevante: 0 item(ns)
- Delta factual: 0 adicionados, 11 modificados, 0 removidos

**Mudanças**

- As cinco superfícies de entrada agora leem AI_CONTEXT.md e usam ai_context.py --check apenas como inspeção read-only.
- O check agora informa fingerprints atual/armazenado/checkpoint e delta determinístico, sem escrever artefatos ou locks.
- O preview Git vivo foi removido de AI_CONTEXT.md para impedir o loop stale após commit.

**Decisões**

- Preservar publicação sem flags para compatibilidade, restringindo-a por contrato ao checkpoint explícito.

**Validações**

- 28 testes focados control.test_ai_handoff/control.test_m11_commands passaram; py_compile de scripts/ai_context.py e git diff --check passaram antes do checkpoint.

**Riscos/limites**

- Consumidores que invocam o gerador sem flags no início devem migrar para leitura e --check opcional; o contexto anterior pode ficar stale até esta publicação.

**Próximos passos**

- Executar inspeção read-only e regressões após publicar e revisar os quatro artefatos gerados.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `.github/copilot-instructions.md` | `c72d16e8330e` | `e330cf49a962` |
| modified | `.prime/agent/APPEND_SYSTEM.md` | `00651a431820` | `42fa8e1fbf01` |
| modified | `AGENTS.md` | `0c65e46ff94b` | `735bc4d248b8` |
| modified | `CLAUDE.md` | `277d35ab7a04` | `2eb0ae4ce37a` |
| modified | `GEMINI.md` | `e2cbfe965d39` | `058ce9fdb605` |
| modified | `PLANS.md` | `04b1bef26303` | `a11255b690d3` |
| modified | `control/test_ai_handoff.py` | `7eeb838fe65e` | `406f7e0298ef` |
| modified | `control/test_m11_commands.py` | `bccd8c0c2165` | `2d3fae206b85` |
| modified | `docs/architecture.md` | `a68d45758893` | `4b52226603de` |
| modified | `docs/decisions.md` | `550ec38b4882` | `96a76105f4e3` |
| modified | `scripts/ai_context.py` | `49f09af19c29` | `827ba6692584` |

### 2026-09-06T04:12:37Z — M13.2.1 encerra documentalmente a M13.2 após o merge do PR #5: corrige a evidência da regressão final de 473 para 474 testes e publica o checkpoint atual.

- Session ID: `session-893d2e53b9018274e0f2`
- Fingerprint final: `99e18d3743a22283e304aca2cc36576423144a99365d5201734d9bc0e7181a24`
- Git final: `de9253491876`; status relevante: 2 item(ns)
- Delta factual: 0 adicionados, 14 modificados, 0 removidos

**Mudanças**

- PLANS.md e ADR-036 agora registram a contagem correta: 474 testes, 1 skip.
- O histórico e o contexto gerado são publicados somente neste checkpoint explícito posterior ao merge.

**Decisões**

- M13.2 permanece o último marco estrutural; M13.2.1 é uma correção de evidência e handoff, sem mudança funcional.

**Validações**

- python3 -m unittest -q control.test_ai_handoff control.test_m11_commands: 28 testes aprovados.
- git diff --check: aprovado antes da publicação dos artefatos gerados.

**Riscos/limites**

- Execução live, configuração de provedor e M14 continuam deliberadamente fora do escopo.

**Próximos passos**

- Antes de qualquer M14, obter autorização específica de escopo, provedor, orçamento e execução.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `.prime/agent/skills/article-loop/src/article_loop/adapters.py` | `0967056aa010` | `69abdcbb18f7` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/evaluation.py` | `1c2da4a593f4` | `0ef24de6bb89` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/execution.py` | `c777f1e7d74f` | `2f89f04e9f5f` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/orchestrator.py` | `88cb3a511c69` | `4a7859229859` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/store.py` | `847aa3bbf8e4` | `0f0e0177405c` |
| modified | `PLANS.md` | `a11255b690d3` | `fdc9f8d10d6c` |
| modified | `control/m13_fixture.py` | `da4d3cd326d8` | `d0bf339d2921` |
| modified | `control/test_m1251_dual_execution.py` | `4a4206f336c4` | `41cd66c9796e` |
| modified | `control/test_m2_durable_state.py` | `ec7af622272b` | `60f39319fab2` |
| modified | `control/test_m6_orchestration.py` | `c8a90dee0e45` | `0c698839b4ef` |
| modified | `control/test_m7_synthesis_gates.py` | `aedbad3eee58` | `8e3955770c4b` |
| modified | `control/test_m8_evaluation.py` | `dd6e1969557c` | `7217301cb474` |
| modified | `control/test_m9_diagnosis.py` | `0de4b64409e0` | `fc822010cc37` |
| modified | `docs/decisions.md` | `96a76105f4e3` | `31cb5575e735` |

### 2026-09-06T05:36:44Z — M14 entregue: Central de Controle local para observação e comandos canônicos, sem iniciar Prime Agent, inferência, modelos, provedores, pipeline científico ou rede externa.

- Session ID: `session-09c1da6074805018e076`
- Fingerprint final: `7065aca4e586ddb7d5b0f2e4183b641544d5af3733e3d2c8cb3ec2ff010cfc2e`
- Git final: `816634ea4cb3`; status relevante: 18 item(ns)
- Delta factual: 9 adicionados, 9 modificados, 0 removidos

**Mudanças**

- Adicionado control plane Python em /api/v1 estritamente 127.0.0.1, com Host/Origin same-origin, POSTs confirmados/idempotentes e ledger de auditoria separado.
- Adicionada UI estática local e responsiva com SSE cursorizado, polling de contingência, topologia de 21 papéis, evidências cegas, orçamento read-only, configuração tipada e links de metadados allowlisted.
- Leitores canônicos receberam variantes read-only para store, logger e orçamento; controles M6 passaram hash esperado no lock canônico.

**Decisões**

- Aplicação de rascunho permanece bloqueada durante qualquer run não terminal porque snapshots legados não vinculam hash global de configuração.
- Links de artefato expõem somente metadados de hashes já presentes no journal; não há leitor HTTP de caminho ou conteúdo arbitrário.

**Validações**

- Suites focadas M14/M6/M2/M12/contratos: 167 testes aprovados em 33.904 s.
- Regressão integral: 495 testes aprovados em 414.383 s; avisos conhecidos apenas de fixtures HTTP/ZIP temporárias.
- bin/check.sh aprovou com live_ready=false, modelos/APIs pagas/routing/targets desabilitados; py_compile, node --check e git diff --check aprovados.

**Riscos/limites**

- Execução live continua fail-closed e requer futura autorização explícita de escopo, provedor, orçamento e run; a Central não fornece endpoint de start ou inferência.

**Próximos passos**

- Se houver autorização futura, iniciar a Central somente em 127.0.0.1 e realizar preflight local auditado antes de qualquer operação permitida.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `.prime/agent/skills/article-loop/src/article_loop/control_center.py` | `-` | `f62fe85c3f35` |
| added | `.prime/agent/skills/article-loop/src/article_loop/control_center_static/app.js` | `-` | `b4a87c04ad50` |
| added | `.prime/agent/skills/article-loop/src/article_loop/control_center_static/index.html` | `-` | `c0f9a056a206` |
| added | `.prime/agent/skills/article-loop/src/article_loop/control_center_static/styles.css` | `-` | `65b8fdf75739` |
| added | `config/schemas/control-center-audit.schema.json` | `-` | `235dd80de607` |
| added | `config/schemas/control-center-draft.schema.json` | `-` | `61190b3c62b5` |
| added | `control/test_m14_control_center.py` | `-` | `d116fa2dc642` |
| added | `docs/control-center.md` | `-` | `784d05166c0c` |
| added | `state/control-center/.gitkeep` | `-` | `01ba4719c80b` |
| modified | `.gitignore` | `293dc90f4e63` | `35a6d1a41539` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/__init__.py` | `aec1d2b67a19` | `90b65b60309b` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/budget.py` | `1fa4c6dfc435` | `936a9a9e30ff` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/observability.py` | `bb380abefcb5` | `6c4cb2259d89` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/orchestrator.py` | `4a7859229859` | `9c13c891f0d1` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/store.py` | `0f0e0177405c` | `a23cf5cd9304` |
| modified | `PLANS.md` | `fdc9f8d10d6c` | `5d98c2fdd324` |
| modified | `control/test_contracts.py` | `aa3d80791b67` | `481cd98e5807` |
| modified | `docs/decisions.md` | `31cb5575e735` | `b870c9794a18` |

### 2026-09-06T06:07:24Z — M14 control-center hardening repaired the known concurrent configuration-apply and idempotency races, plus dynamic map defaults in the offline UI.

- Session ID: `session-19361425ab71b858f229`
- Fingerprint final: `39c79953b9385996475e7a13b0962243b16fbbe6c1ff15610f80ab0b90ad0b20`
- Git final: `816634ea4cb3`; status relevante: 18 item(ns)
- Delta factual: 0 adicionados, 5 modificados, 0 removidos

**Mudanças**

- Serialized configuration apply with a dedicated interprocess lock across active-run check, hash revalidation, write, and draft state publication.
- Serialized control mutations with a dedicated interprocess idempotency lock from lookup through canonical operation and persisted response.
- Corrected dynamic map creation to initialize values from the resolved item schema.

**Decisões**

- Concurrent drafts with the same base hash must have one winner and all same-key requests must replay one persisted canonical result.

**Validações**

- Focused M14: 20 tests OK; full control regression: 497 tests OK in 431.752s; bin/check.sh, py_compile, node --check, and git diff --check OK.

**Riscos/limites**

- No model, Prime Agent, endpoint, provider, or live pipeline was run; no commit or push was made.

**Próximos passos**

- Review the uncommitted M14 control-center branch changes, then commit and open a PR only with explicit authorization.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `.prime/agent/skills/article-loop/src/article_loop/control_center.py` | `f62fe85c3f35` | `a91cb370be06` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/control_center_static/app.js` | `b4a87c04ad50` | `f20913c8a3fa` |
| modified | `PLANS.md` | `5d98c2fdd324` | `d3355968a55e` |
| modified | `control/test_m14_control_center.py` | `d116fa2dc642` | `815a9e6023f4` |
| modified | `docs/decisions.md` | `b870c9794a18` | `387a596451a0` |

### 2026-09-06T07:01:49Z — Ajuste M14 concluído: a Central de Controle agora tem uma inicialização local oficial e verificável, sem tentar suportar file:// ou criar uma variante standalone.

- Session ID: `session-f5f4c080e2d7ea248fba`
- Fingerprint final: `b9ccf46018d73fd0c8c0c1b6aa226279dac15bf873432ee3e348dc630b67b19f`
- Git final: `fce6dfc0ed14`; status relevante: 7 item(ns)
- Delta factual: 1 adicionados, 6 modificados, 0 removidos

**Mudanças**

- Adicionado bin/start-control-center.sh, que exige a raiz article-loop válida, aceita somente --port de 1024 a 65535 e executa exclusivamente o módulo article_loop.control_center em 127.0.0.1 com PYTHONPATH local.
- A interface declara discretamente que file:// não é suportado; docs/control-center.md documenta comando, URL, troca segura de porta e encerramento; PLANS.md e ADR-038 registram a decisão.
- Os testes M14 agora verificam HTML, CSS e JavaScript pelo LocalControlHTTPServer em porta efêmera, ausência de URLs externas, rejeição loopback e restrições estáticas do launcher.

**Decisões**

- Mantido um único caminho oficial de abertura: o LocalControlHTTPServer canônico. URLs absolutas /assets e /api/v1 permanecem intencionais e file:// é explicitamente não operacional.

**Validações**

- python3 -m unittest control.test_m14_control_center -v: 21 testes aprovados em 2.028 s, incluindo servidor loopback real em porta efêmera.
- python3 -m unittest discover -s control -q: 498 testes aprovados em 320.803 s; apenas avisos conhecidos de fixtures HTTP/ZIP temporárias.
- bash bin/check.sh aprovou com live_ready=false; bash -n do launcher, py_compile do módulo/teste, node --check do app.js, git diff --check e --help do launcher aprovaram.

**Riscos/limites**

- file:// continua deliberadamente não suportado porque não oferece a origem HTTP nem a API /api/v1; não há servidor alternativo, modelo, Prime Agent, inferência, rede externa ou pipeline científico.

**Próximos passos**

- Revisar o diff na branch local codex/control-center-launcher; commit, push e PR permanecem fora do escopo até autorização explícita.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `bin/start-control-center.sh` | `-` | `7a0e4871790b` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/control_center_static/index.html` | `c0f9a056a206` | `2f775a29f11a` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/control_center_static/styles.css` | `65b8fdf75739` | `bf08db5bcb11` |
| modified | `PLANS.md` | `d3355968a55e` | `32816308cbda` |
| modified | `control/test_m14_control_center.py` | `815a9e6023f4` | `2e0376925305` |
| modified | `docs/control-center.md` | `784d05166c0c` | `2eb9ab85bd98` |
| modified | `docs/decisions.md` | `387a596451a0` | `63ccee46aa6f` |

### 2026-09-06T07:29:57Z — README atualizado para apresentar o LOOP-PRIMER em portugues como sistema local, auditavel e fail-closed, com estado estrutural ate M14 e fronteiras explicitas contra execucao cientifica nao autorizada.

- Session ID: `session-5ac7252fb3aa584776cf`
- Fingerprint final: `79ef00da29c7fda60bd10d70f933e3b960af8a813e91402a0fb7eeb376ae59bd`
- Git final: `fce6dfc0ed14`; status relevante: 8 item(ns)
- Delta factual: 0 adicionados, 1 modificados, 0 removidos

**Mudanças**

- Substituido o README desatualizado por uma apresentacao orientada a contratos, fluxo canônico, topologia de 21 papeis, conceitos de champion, challenger, gates, receipts, orcamento e fail-closed.
- Documentados somente os comandos locais verificados: bin/check.sh, a regressao unittest, a aceitacao M13 e o launcher bin/start-control-center.sh com URL loopback e porta padrao ou escolhida.

**Decisões**

- O README separa implementacao estrutural concluida de execucao cientifica real, que continua condicionada a autorizacao humana e pre-condicoes fail-closed.

**Validações**

- git diff --check aprovou; todos os links relativos do README foram verificados como existentes; bash bin/start-control-center.sh --help aprovou.
- bash bin/check.sh aprovou e reportou live_ready=false, model_execution_enabled=false e paid_apis_enabled=false.

**Riscos/limites**

- Nenhum modelo, Prime Agent, provedor remoto, API paga, pipeline cientifico ou servidor persistente foi iniciado; a suite integral nao foi reexecutada nesta tarefa documental.

**Próximos passos**

- Revisar o diff local; commit, push ou PR permanecem fora do escopo e exigem autorizacao explicita.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `README.md` | `bf2c1e350275` | `7d19d69de938` |

### 2026-09-06T07:55:00Z — Restored README.md exactly to the version before the rejected update and removed its unresolved merge-conflict markers.

- Session ID: `session-b6f24eee458186e7c9d9`
- Fingerprint final: `b9ccf46018d73fd0c8c0c1b6aa226279dac15bf873432ee3e348dc630b67b19f`
- Git final: `9faed3499bcf`; status relevante: 1 item(ns)
- Delta factual: 0 adicionados, 1 modificados, 0 removidos

**Mudanças**

- Replaced README.md with the exact parent revision blob 4df86adcba1d020b26314e365ac1e948eb47cad5.

**Decisões**

- Preserve the historical README bytes, including its pre-existing trailing whitespace, rather than silently reformatting the restored version.

**Validações**

- Working-tree README hash equals HEAD^:README.md; unresolved conflict markers were removed.

**Riscos/limites**

- The restored historical README still contains outdated claims and seven pre-existing trailing-whitespace warnings; no other project source was changed.

**Próximos passos**

- Review the restored README separately before any new documentation rewrite; commit this restoration only with explicit authorization.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `README.md` | `7d19d69de938` | `bf2c1e350275` |

### 2026-09-06T07:59:33Z — Updated the restored README in place while preserving its original badges, table of contents, diagrams, role matrix, quick-start, CLI, repository-tree and ADR-table structure.

- Session ID: `session-07dd42119cf2d761e4df`
- Fingerprint final: `13aad049b10453e81d5f97fc5f6291786ed7c79a9dca739d34d010426c4d0cb1`
- Git final: `9faed3499bcf`; status relevante: 1 item(ns)
- Delta factual: 0 adicionados, 1 modificados, 0 removidos

**Mudanças**

- Updated milestone, security, test, command, repository-layout and ADR references through M14 and the canonical local Control Center launcher.

**Decisões**

- Keep the legacy README presentation and links; correct claims in place instead of replacing it with a new document structure.

**Validações**

- Verified all documented local files and command entrypoints exist; git diff --check passed; no source or runtime behavior was changed.

**Riscos/limites**

- README documents structural readiness only; live models, Prime Agent, providers, paid APIs and scientific runs remain unauthorized and disabled by default.

**Próximos passos**

- Review the uncommitted documentation and checkpoint changes, then commit only with explicit authorization.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `README.md` | `bf2c1e350275` | `6b14a95fb275` |

### 2026-09-06T08:13:25Z — Restored the two README compatibility markers required by the AI handoff contract after the documentation refresh caused CI to fail.

- Session ID: `session-d74de28a5971446dc7ab`
- Fingerprint final: `d1725eef78664024039b83230a62dd4daba5bf09fe7a4d095d47df45c15d96d2`
- Git final: `ef39df85f67f`; status relevante: 1 item(ns)
- Delta factual: 0 adicionados, 1 modificados, 0 removidos

**Mudanças**

- Added the literal M10 Decision and operational CLI statements back to the README status block without changing its structure.

**Decisões**

- README compatibility markers asserted by control/test_ai_handoff remain stable wording contracts and must be preserved during documentation updates.

**Validações**

- python3 -m unittest control.test_ai_handoff -q: 12 tests OK; git diff --check OK.

**Riscos/limites**

- This is documentation-only; no model, Prime Agent, provider, API, or scientific pipeline was run.

**Próximos passos**

- Push the CI repair commit and wait for the refreshed PR checks.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `README.md` | `6b14a95fb275` | `9db883c90233` |

### 2026-09-07T00:34:13Z — Implementada a entrada local restrita para ciclo routed e executada uma única tentativa real autorizada.

- Session ID: `local-loopback-full-cycle-20260906`
- Fingerprint final: `301d487c0165b513b335f06e43448099fa7188c50281a3f256275ec167832fc0`
- Git final: `ba90b7847d13`; status relevante: 5 item(ns)
- Delta factual: 3 adicionados, 3 modificados, 0 removidos

**Mudanças**

- Adicionados scripts/local_loopback_full_cycle.py e control/test_local_loopback_full_cycle.py; a CLI cria tentativa isolada, valida loopback literal, configura dois modelos distintos e preserva estado canônico.
- Atualizados PLANS.md, ADR-039 e .gitignore para registrar configuração local isolada e o bloqueio factual da tentativa.

**Decisões**

- A falha de reconstrução LaTeX M3 permanece em INGESTED e bloqueia M6--M10; não houve retry, reparo de PDF, inferência ou atestação matemática.

**Validações**

- 503 testes control passaram em 371.356s; bin/check.sh, py_compile e git diff --check passaram. Após ajuste de status, os 5 testes da nova entrada passaram.
- Preflight local confirmou os dois modelos e endpoint loopback; a inspeção canônica confirmou PDF congelado e estado INGESTED.

**Riscos/limites**

- M3 falhou porque reconstructed.tex não compilou com segurança. A tentativa não alcançou SOURCE_READY; não há receipts, gates, júri, decisão ou custo externo.

**Próximos passos**

- Inspecionar ou corrigir a política de reconstrução M3 em trabalho autorizado separado antes de criar qualquer nova tentativa.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `control/test_local_loopback_full_cycle.py` | `-` | `b724647f293c` |
| added | `input/inbox/artigo.pdf` | `-` | `7a888ab15668` |
| added | `scripts/local_loopback_full_cycle.py` | `-` | `efce1c57e60b` |
| modified | `.gitignore` | `35a6d1a41539` | `61498d27e2e2` |
| modified | `PLANS.md` | `32816308cbda` | `7c8139dfdf11` |
| modified | `docs/decisions.md` | `63ccee46aa6f` | `6d0ebcacf4a0` |

### 2026-09-07T01:09:49Z — Correção estrutural M3 concluída sem retomar a tentativa congelada: a reconstrução auxiliar passou a ser ASCII-safe, limitada e diagnosticável offline.

- Session ID: `m3-reconstruction-hardening-20260907`
- Fingerprint final: `c84a15e353707886cacadfd20fcea2418e27040f55233fc5b9031d8ae762d109`
- Git final: `ba90b7847d13`; status relevante: 8 item(ns)
- Delta factual: 1 adicionados, 7 modificados, 0 removidos

**Mudanças**

- Endurecida a reconstrução LaTeX com escape de metacaracteres, marcadores ASCII determinísticos para Unicode e controles, segmentação de linhas e primitivas fixas que evitam avisos de caixa em massa.
- Adicionado scripts/m3_reconstruction_diagnostic.py, create-only e hash-bound, e status da entrada loopback agora expõe canonical_run_id derivado dos journals.
- Adicionada cobertura M3 para Unicode, controles, metacaracteres, linhas longas, falha limitada em INGESTED e diagnóstico; adicionada cobertura de status com outcome histórico sem run_id.

**Decisões**

- normalized.json preserva a transcrição exata; reconstructed.tex é somente representação auxiliar sem comandos derivados do PDF, shell-escape, pacotes ou leitura dinâmica.
- O diagnóstico registra somente identificador, hashes, retorno, duração, tamanho e hash da saída e classificação; nenhum texto extraído foi publicado.

**Validações**

- python3 -m unittest control.test_m3_ingestion control.test_local_loopback_full_cycle -v: 31 testes OK.
- python3 -m unittest discover -s control -p test_*.py: 507 testes OK em 348.030 s.
- bin/check.sh: status success; py_compile dos módulos alterados e git diff --check: OK.
- Diagnóstico único hash-bound do PDF allowlisted: diagnostic-8962e107-cdf5-4862-8f2e-d7202d9c239c, LATEX_OUTPUT_TOO_LARGE, retorno -9, 65536 bytes, sem conteúdo de artigo.

**Riscos/limites**

- A evidência congelada não foi alterada e o diagnóstico único anterior à supressão de avisos confirmou saturação da saída; uma nova tentativa M3 requer autorização explícita e não foi criada.

**Próximos passos**

- Com autorização explícita, criar nova tentativa isolada para validar o M3 endurecido contra o PDF preservado; nunca retomar ou reescrever a tentativa congelada.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `scripts/m3_reconstruction_diagnostic.py` | `-` | `5861d2384b71` |
| modified | `.gitignore` | `61498d27e2e2` | `7e4121d14965` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/ingestion.py` | `e33ca846c9cc` | `55c34b3b03a2` |
| modified | `PLANS.md` | `7c8139dfdf11` | `8831f830600e` |
| modified | `control/test_local_loopback_full_cycle.py` | `b724647f293c` | `36dbf8b9a9a0` |
| modified | `control/test_m3_ingestion.py` | `bd9d67d994e4` | `5d9df83c5971` |
| modified | `docs/decisions.md` | `6d0ebcacf4a0` | `0978281b1043` |
| modified | `scripts/local_loopback_full_cycle.py` | `efce1c57e60b` | `2c661369433b` |

### 2026-09-07T01:21:13Z — Revisado, validado, versionado e publicado o conjunto da entrada local isolada e do endurecimento M3.

- Session ID: `commit-pr-m3-local-loopback-20260907`
- Fingerprint final: `c84a15e353707886cacadfd20fcea2418e27040f55233fc5b9031d8ae762d109`
- Git final: `edcba666eb1c`; status relevante: 0 item(ns)
- Delta factual: 0 adicionados, 0 modificados, 0 removidos

**Mudanças**

- Commit edcba66 criado na branch codex/local-loopback-full-cycle com a entrada local loopback-only, diagnóstico M3 e endurecimento da reconstrução.
- PR #9 aberto contra main; nenhum artefato da tentativa congelada foi versionado.

**Decisões**

- A tentativa attempt-55081d47-a57f-4d21-846c-54f0aaa5ef0e permanece evidência imutável em INGESTED; qualquer nova tentativa exige autorização explícita e identidade nova.

**Validações**

- 31 testes focados, regressão completa de 507 testes, bin/check.sh, py_compile e git diff --check passaram nesta sessão.

**Riscos/limites**

- O M3 endurecido ainda não foi aplicado ao PDF real em uma nova tentativa; diagnóstico histórico não deve ser confundido com execução.

**Próximos passos**

- Revisar e fazer merge do PR #9; depois, somente com autorização explícita, preparar nova tentativa isolada de M3.

### 2026-09-07T01:39:39Z — Corrigida a falha de CI da entrada local ao remover a dependência do PDF ignorado do checkout.

- Session ID: `ci-fixture-portability-20260907`
- Fingerprint final: `0c2ecddf458ea660521359c04d808331c3f053a87d0a47fd391548d3e0af81a6`
- Git final: `6ac799fac683`; status relevante: 3 item(ns)
- Delta factual: 0 adicionados, 3 modificados, 0 removidos

**Mudanças**

- A fixture de control/test_local_loopback_full_cycle.py agora cria bytes sintéticos locais em input/inbox/artigo.pdf.
- PLANS.md e ADR-039 registram que a aceitação de preparação é independente do PDF real.

**Decisões**

- Os testes de preparação validam somente regularidade, hash e isolamento; não devem consumir ou publicar a evidência PDF real.

**Validações**

- python3 -m unittest control.test_local_loopback_full_cycle -v: 6 testes OK; python3 -m unittest discover -s control -p test_*.py -q: 507 testes OK em 381.789s; git diff --check: OK.

**Riscos/limites**

- A CI não executa uma tentativa real ou M3 sobre o PDF real; isso permanece corretamente fora do escopo dos testes.

**Próximos passos**

- Aguardar a CI do PR #9 e revisar o merge; uma nova tentativa M3 só poderá ser criada com autorização explícita.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| modified | `PLANS.md` | `8831f830600e` | `17f01d5969b0` |
| modified | `control/test_local_loopback_full_cycle.py` | `36dbf8b9a9a0` | `3497ecd554b8` |
| modified | `docs/decisions.md` | `0978281b1043` | `c68d840cb18e` |

### 2026-09-07T03:22:59Z — O contexto de entrada para agentes foi compactado sem descartar contratos, evidências ou fontes autoritativas.

- Session ID: `lean-agent-context-20260907`
- Fingerprint final: `d7cfbaf096f9c41db7d0741db0b8021a18213abc3313b8ac924e9649cb454406`
- Git final: `3ae6ab7a60d0`; status relevante: 14 item(ns)
- Delta factual: 1 adicionados, 11 modificados, 2 removidos

**Mudanças**

- AI_CONTEXT.md passou a ser gerado como roteador compacto com fingerprint de fontes e histórico, estado, limites, delta, três sessões materiais e fontes por escopo.
- AGENTS.md, a skill article-loop e os adaptadores Prime/Copilot foram reduzidos a regras transversais e encaminhamento; o contrato detalhado da skill foi preservado em references/api-contracts.md.
- CLAUDE.md e GEMINI.md foram removidos por não serem superfícies usadas; diretórios vazios .agents e .codex sem arquivos nem rastreamento foram removidos.

**Decisões**

- Contexto inicial é escalonado: dados detalhados continuam versionados e só são abertos quando o escopo requer, conforme ADR-040.

**Validações**

- 29 testes focados de handoff e M11 passaram; py_compile dos scripts alterados e article_loop_command.py check passaram; git diff --check e git diff --cached --check passaram.
- A regressão integral control foi executada localmente e concluída OK, conforme confirmação do operador; a repetição rastreável posterior foi interrompida deliberadamente e não é contada como validação.

**Riscos/limites**

- Nenhum modelo, Prime Agent, rede, API paga, PDF real ou ciclo científico foi iniciado; a qualidade futura depende de seguir o roteamento para módulos, schemas, testes e ADRs específicos.

**Próximos passos**

- Revisar o diff, decidir se deseja commit/PR e, em tarefa futura, abrir somente as fontes indicadas pelo contexto compacto.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `.prime/agent/skills/article-loop/references/api-contracts.md` | `-` | `7177a152fcde` |
| modified | `.github/copilot-instructions.md` | `e330cf49a962` | `776217ed4380` |
| modified | `.prime/agent/APPEND_SYSTEM.md` | `42fa8e1fbf01` | `aec816192e5e` |
| modified | `.prime/agent/skills/article-loop/SKILL.md` | `7177a152fcde` | `8f1e7d84bb88` |
| modified | `AGENTS.md` | `735bc4d248b8` | `bcce634f6952` |
| modified | `PLANS.md` | `17f01d5969b0` | `a835f54a4020` |
| modified | `control/test_ai_handoff.py` | `406f7e0298ef` | `aad996d05dc8` |
| modified | `control/test_m11_commands.py` | `2d3fae206b85` | `cebe422d7122` |
| modified | `docs/architecture.md` | `4b52226603de` | `ca96280f20f5` |
| modified | `docs/decisions.md` | `c68d840cb18e` | `e4da251c4de0` |
| modified | `scripts/ai_context.py` | `827ba6692584` | `f977db70f0ff` |
| modified | `scripts/article_loop_command.py` | `0699196206ee` | `f847bdc092e9` |
| deleted | `CLAUDE.md` | `2eb0ae4ce37a` | `-` |
| deleted | `GEMINI.md` | `058ce9fdb605` | `-` |

### 2026-09-07T04:41:44Z — Validação M3 real do PDF preservado alcançou SOURCE_READY em uma segunda raiz isolada após correção determinística do inventário autor--ano.

- Session ID: `m3-real-source-ready-20260907`
- Fingerprint final: `04d597be5f85d9712100d709a862e50a8ad94ad2b22e6843f3454553248ca301`
- Git final: `2ff020dfe869`; status relevante: 414 item(ns)
- Delta factual: 410 adicionados, 4 modificados, 0 removidos

**Mudanças**

- Criadas duas tentativas M3-only create-only e um diagnóstico hash-bound; a primeira preserva a falha reference_coverage em INGESTED e a segunda publicou os artefatos M3 e o baseline v0000 em SOURCE_READY.
- Corrigido o classificador M3 para inventariar referências autor--ano capitalizadas e restringir case-insensitive aos marcadores explícitos DOI/arXiv.
- Adicionada regressão que cobre autor--ano, rejeita falso candidato minúsculo e comprova SOURCE_READY no fluxo de ingestão.

**Decisões**

- Manter o limiar de referência em 0.80 e todos os controles fail-closed; corrigir a inconsistência interna entre candidato e inventário sem OCR, fallback semântico ou force.

**Validações**

- 32 testes M3/entrada local passaram; regressão integral passou fora do sandbox com 509 testes; py_compile, bin/check.sh e git diff --check passaram.
- PDF, original publicado e baseline têm SHA-256 7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d; journal válido NEW->INGESTED->SOURCE_READY e schemas event/snapshot/candidate-manifest aprovados.

**Riscos/limites**

- A validação comprova somente M3 local; M6+, modelos, backend, reservas, receipts, rede e custo não foram iniciados.

**Próximos passos**

- Revisar as mudanças e evidências; commit, push ou PR dependem de autorização explícita nova.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `runtime/m3-real-attempts/attempt-c133a0f9-2ada-4717-87c7-b4103f79fc74/artifacts/original/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/manifest.json` | `-` | `8d3064e2d549` |
| added | `runtime/m3-real-attempts/attempt-c133a0f9-2ada-4717-87c7-b4103f79fc74/config/gates.yaml` | `-` | `2ee0a93dee8e` |
| added | `runtime/m3-real-attempts/attempt-c133a0f9-2ada-4717-87c7-b4103f79fc74/state/events/ingest-7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d.jsonl` | `-` | `31ec00c53e9f` |
| added | `runtime/m3-real-attempts/attempt-c133a0f9-2ada-4717-87c7-b4103f79fc74/state/locks/ingest-7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d.lock` | `-` | `e3b0c44298fc` |
| added | `runtime/m3-real-attempts/attempt-c133a0f9-2ada-4717-87c7-b4103f79fc74/state/snapshots/ingest-7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d.json` | `-` | `df5c2209ad9a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/coordinates.html` | `-` | `f3dfb58dd0c2` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/manifest.json` | `-` | `1597152b815f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/normalized.json` | `-` | `7ceba5b337e9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-01.png` | `-` | `5164607c0873` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-02.png` | `-` | `7f2ca5e57f40` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-03.png` | `-` | `48467c667d58` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-04.png` | `-` | `e74ced835f8d` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-05.png` | `-` | `ecbc55b4e74b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-06.png` | `-` | `936ebc1f1a40` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-07.png` | `-` | `f0149c6908bc` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-08.png` | `-` | `ced0ce2331de` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-09.png` | `-` | `3d17ee571b21` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-10.png` | `-` | `f3b3afe0cc5b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-11.png` | `-` | `1cc658f643c6` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-12.png` | `-` | `aeb2541f8114` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-13.png` | `-` | `558e81573479` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-14.png` | `-` | `514cddd3db59` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-15.png` | `-` | `ab6b76289179` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-16.png` | `-` | `308c7290dcd3` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-17.png` | `-` | `c23d6c61ce81` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-18.png` | `-` | `23d6afb8e50a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-19.png` | `-` | `c37e7719e531` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-20.png` | `-` | `a8bbd768185c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-21.png` | `-` | `219b429b7fb8` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-22.png` | `-` | `f284202648c5` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-23.png` | `-` | `2dc67a648b31` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-24.png` | `-` | `048b8516c292` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-25.png` | `-` | `8e38a57b9a85` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-26.png` | `-` | `f18ad02a4e3f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-27.png` | `-` | `acc74f6e9807` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-28.png` | `-` | `272263eb07a2` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-29.png` | `-` | `df1ac8703fda` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-30.png` | `-` | `eb9ca0cfb635` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-31.png` | `-` | `3cf40ca22df2` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-32.png` | `-` | `debca3459201` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-33.png` | `-` | `aee15b1fe347` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-34.png` | `-` | `923254aaa20c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-35.png` | `-` | `1c48deb53f20` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-36.png` | `-` | `1ec36ea69760` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-37.png` | `-` | `0070a9703a57` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-38.png` | `-` | `d2a4b4466400` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-39.png` | `-` | `e2c02d228eb0` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-40.png` | `-` | `a59779f6410e` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-41.png` | `-` | `787c0d3abba9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-42.png` | `-` | `0b6a12ae228f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-43.png` | `-` | `19120549029c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-44.png` | `-` | `48c9bdc545f8` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-45.png` | `-` | `7c4d8d1e888c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-46.png` | `-` | `b092692f2974` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-47.png` | `-` | `38b31cb00e9c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-48.png` | `-` | `dff92f18a3d5` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-49.png` | `-` | `22e000d1dc90` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-50.png` | `-` | `8c725d21b21a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-51.png` | `-` | `4b38e01262a4` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-52.png` | `-` | `ebae884b77c5` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-53.png` | `-` | `494938cb91c9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-54.png` | `-` | `7b36dadc22bf` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-55.png` | `-` | `c36ce667896c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-56.png` | `-` | `f17416d246b9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-57.png` | `-` | `9164976dfeae` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-58.png` | `-` | `10d5c501d061` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-59.png` | `-` | `dfcb9fd3eb6a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-60.png` | `-` | `1b3fa518e237` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-61.png` | `-` | `f966f211354e` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-62.png` | `-` | `5c8064d7e7ea` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-63.png` | `-` | `f6cc6eec2c04` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-64.png` | `-` | `558c03485dce` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-65.png` | `-` | `d613cade3106` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-66.png` | `-` | `3edc69d16dca` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-67.png` | `-` | `f883b79e525c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-68.png` | `-` | `eeeebcfb20d1` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-69.png` | `-` | `4cab9aa8d996` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-70.png` | `-` | `184971bdba6b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-71.png` | `-` | `5abaf5270764` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-72.png` | `-` | `a4ec57f24c51` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-73.png` | `-` | `8892329413cc` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-74.png` | `-` | `54e1b437c74f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-75.png` | `-` | `5adb10b0fb8f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-76.png` | `-` | `ce5d8af85376` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-77.png` | `-` | `92ca120e6645` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/reconstructed.tex` | `-` | `7be05a737bc9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/source_ready.json` | `-` | `9cba70684b67` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-1.txt` | `-` | `e0a4c94e6763` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-10.txt` | `-` | `f6f190e11565` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-11.txt` | `-` | `ad93e8fcf847` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-12.txt` | `-` | `44fea84eced7` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-13.txt` | `-` | `6dc3a8b6e6ce` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-14.txt` | `-` | `0dd221d7fe42` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-15.txt` | `-` | `05080687a263` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-16.txt` | `-` | `47470f482106` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-17.txt` | `-` | `1c76adaec0f6` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-18.txt` | `-` | `8fbeef1db877` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-19.txt` | `-` | `473c6db146cf` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-2.txt` | `-` | `2ffaebc3222b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-20.txt` | `-` | `75f3002f9ec6` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-21.txt` | `-` | `0a78e85a58e5` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-22.txt` | `-` | `c5ee1e9f8883` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-23.txt` | `-` | `047cee02a21a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-24.txt` | `-` | `ced168acb9ec` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-25.txt` | `-` | `fe2a5885221d` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-26.txt` | `-` | `a096227ca7a6` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-27.txt` | `-` | `ec37f80d8a27` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-28.txt` | `-` | `0b292bfd3cac` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-29.txt` | `-` | `9817fe6f8089` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-3.txt` | `-` | `f0f674fad649` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-30.txt` | `-` | `6fee76cb5a4a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-31.txt` | `-` | `812f9cec95e3` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-32.txt` | `-` | `1e0469003c4f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-33.txt` | `-` | `7ed43e2c3296` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-34.txt` | `-` | `5147fd4160c1` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-35.txt` | `-` | `c3e808b742a6` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-36.txt` | `-` | `79015f2d7951` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-37.txt` | `-` | `0cac1a39aafc` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-38.txt` | `-` | `df38257d6425` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-39.txt` | `-` | `0bc46900550b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-4.txt` | `-` | `26fbd9596e36` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-40.txt` | `-` | `fab97c611e12` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-41.txt` | `-` | `9bbd640966f6` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-42.txt` | `-` | `eecf3a01541e` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-43.txt` | `-` | `1de1f5e98b28` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-44.txt` | `-` | `7aa1d1ae8e83` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-45.txt` | `-` | `043bb47f672e` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-46.txt` | `-` | `cb8764beaafe` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-47.txt` | `-` | `e9056da516d9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-48.txt` | `-` | `f15f3e0a1395` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-49.txt` | `-` | `afde326d5f0f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-5.txt` | `-` | `7d5c97c7d92c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-50.txt` | `-` | `45a12bd8c1f7` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-51.txt` | `-` | `806164829e9b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-52.txt` | `-` | `765e5c57dc63` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-53.txt` | `-` | `9e05cd4bac67` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-54.txt` | `-` | `31b85af43259` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-55.txt` | `-` | `145e109e2b95` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-56.txt` | `-` | `79013fa18602` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-57.txt` | `-` | `66d0f2c0aa1d` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-58.txt` | `-` | `2c83ecb78570` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-59.txt` | `-` | `7ec883e5272a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-6.txt` | `-` | `28e634101375` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-60.txt` | `-` | `4512e64906ed` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-61.txt` | `-` | `d2987d34c3fc` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-62.txt` | `-` | `28fdf1883361` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-63.txt` | `-` | `1d4ac6ce02a2` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-64.txt` | `-` | `c6033665a8b3` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-65.txt` | `-` | `8a44b2b80162` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-66.txt` | `-` | `b8583e033a3a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-67.txt` | `-` | `892d5da1b0d2` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-68.txt` | `-` | `6c881d04085c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-69.txt` | `-` | `435714b6b269` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-7.txt` | `-` | `1b9a70b0e22c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-70.txt` | `-` | `b4917e26c0be` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-71.txt` | `-` | `c433b6d389a7` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-72.txt` | `-` | `42116507a396` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-73.txt` | `-` | `16be43e13a2b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-74.txt` | `-` | `a1f53e0af6d9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-75.txt` | `-` | `a8026361fb9d` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-76.txt` | `-` | `578d7e769981` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-77.txt` | `-` | `7c168201fe02` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-8.txt` | `-` | `8db088f136ac` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-9.txt` | `-` | `f4dc4757dbae` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text.txt` | `-` | `cefcc209f1ac` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/original/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/manifest.json` | `-` | `8d3064e2d549` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/manifest.json` | `-` | `91d527f8f5a5` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-01.png` | `-` | `5164607c0873` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-02.png` | `-` | `7f2ca5e57f40` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-03.png` | `-` | `48467c667d58` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-04.png` | `-` | `e74ced835f8d` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-05.png` | `-` | `ecbc55b4e74b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-06.png` | `-` | `936ebc1f1a40` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-07.png` | `-` | `f0149c6908bc` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-08.png` | `-` | `ced0ce2331de` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-09.png` | `-` | `3d17ee571b21` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-10.png` | `-` | `f3b3afe0cc5b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-11.png` | `-` | `1cc658f643c6` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-12.png` | `-` | `aeb2541f8114` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-13.png` | `-` | `558e81573479` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-14.png` | `-` | `514cddd3db59` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-15.png` | `-` | `ab6b76289179` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-16.png` | `-` | `308c7290dcd3` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-17.png` | `-` | `c23d6c61ce81` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-18.png` | `-` | `23d6afb8e50a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-19.png` | `-` | `c37e7719e531` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-20.png` | `-` | `a8bbd768185c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-21.png` | `-` | `219b429b7fb8` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-22.png` | `-` | `f284202648c5` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-23.png` | `-` | `2dc67a648b31` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-24.png` | `-` | `048b8516c292` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-25.png` | `-` | `8e38a57b9a85` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-26.png` | `-` | `f18ad02a4e3f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-27.png` | `-` | `acc74f6e9807` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-28.png` | `-` | `272263eb07a2` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-29.png` | `-` | `df1ac8703fda` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-30.png` | `-` | `eb9ca0cfb635` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-31.png` | `-` | `3cf40ca22df2` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-32.png` | `-` | `debca3459201` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-33.png` | `-` | `aee15b1fe347` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-34.png` | `-` | `923254aaa20c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-35.png` | `-` | `1c48deb53f20` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-36.png` | `-` | `1ec36ea69760` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-37.png` | `-` | `0070a9703a57` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-38.png` | `-` | `d2a4b4466400` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-39.png` | `-` | `e2c02d228eb0` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-40.png` | `-` | `a59779f6410e` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-41.png` | `-` | `787c0d3abba9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-42.png` | `-` | `0b6a12ae228f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-43.png` | `-` | `19120549029c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-44.png` | `-` | `48c9bdc545f8` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-45.png` | `-` | `7c4d8d1e888c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-46.png` | `-` | `b092692f2974` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-47.png` | `-` | `38b31cb00e9c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-48.png` | `-` | `dff92f18a3d5` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-49.png` | `-` | `22e000d1dc90` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-50.png` | `-` | `8c725d21b21a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-51.png` | `-` | `4b38e01262a4` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-52.png` | `-` | `ebae884b77c5` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-53.png` | `-` | `494938cb91c9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-54.png` | `-` | `7b36dadc22bf` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-55.png` | `-` | `c36ce667896c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-56.png` | `-` | `f17416d246b9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-57.png` | `-` | `9164976dfeae` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-58.png` | `-` | `10d5c501d061` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-59.png` | `-` | `dfcb9fd3eb6a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-60.png` | `-` | `1b3fa518e237` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-61.png` | `-` | `f966f211354e` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-62.png` | `-` | `5c8064d7e7ea` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-63.png` | `-` | `f6cc6eec2c04` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-64.png` | `-` | `558c03485dce` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-65.png` | `-` | `d613cade3106` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-66.png` | `-` | `3edc69d16dca` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-67.png` | `-` | `f883b79e525c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-68.png` | `-` | `eeeebcfb20d1` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-69.png` | `-` | `4cab9aa8d996` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-70.png` | `-` | `184971bdba6b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-71.png` | `-` | `5abaf5270764` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-72.png` | `-` | `a4ec57f24c51` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-73.png` | `-` | `8892329413cc` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-74.png` | `-` | `54e1b437c74f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-75.png` | `-` | `5adb10b0fb8f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-76.png` | `-` | `ce5d8af85376` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-77.png` | `-` | `92ca120e6645` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/config/gates.yaml` | `-` | `2ee0a93dee8e` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/state/events/ingest-7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d.jsonl` | `-` | `c53b3edf94f4` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/state/locks/ingest-7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d.lock` | `-` | `e3b0c44298fc` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/state/snapshots/ingest-7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d.json` | `-` | `c0aced74dc5b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/ingestion-manifest.json` | `-` | `6c3a09e76b94` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/manifest.json` | `-` | `3b8b62f1742a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/coordinates.html` | `-` | `f3dfb58dd0c2` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/manifest.json` | `-` | `1597152b815f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/normalized.json` | `-` | `7ceba5b337e9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-01.png` | `-` | `5164607c0873` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-02.png` | `-` | `7f2ca5e57f40` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-03.png` | `-` | `48467c667d58` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-04.png` | `-` | `e74ced835f8d` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-05.png` | `-` | `ecbc55b4e74b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-06.png` | `-` | `936ebc1f1a40` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-07.png` | `-` | `f0149c6908bc` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-08.png` | `-` | `ced0ce2331de` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-09.png` | `-` | `3d17ee571b21` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-10.png` | `-` | `f3b3afe0cc5b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-11.png` | `-` | `1cc658f643c6` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-12.png` | `-` | `aeb2541f8114` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-13.png` | `-` | `558e81573479` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-14.png` | `-` | `514cddd3db59` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-15.png` | `-` | `ab6b76289179` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-16.png` | `-` | `308c7290dcd3` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-17.png` | `-` | `c23d6c61ce81` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-18.png` | `-` | `23d6afb8e50a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-19.png` | `-` | `c37e7719e531` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-20.png` | `-` | `a8bbd768185c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-21.png` | `-` | `219b429b7fb8` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-22.png` | `-` | `f284202648c5` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-23.png` | `-` | `2dc67a648b31` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-24.png` | `-` | `048b8516c292` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-25.png` | `-` | `8e38a57b9a85` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-26.png` | `-` | `f18ad02a4e3f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-27.png` | `-` | `acc74f6e9807` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-28.png` | `-` | `272263eb07a2` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-29.png` | `-` | `df1ac8703fda` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-30.png` | `-` | `eb9ca0cfb635` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-31.png` | `-` | `3cf40ca22df2` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-32.png` | `-` | `debca3459201` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-33.png` | `-` | `aee15b1fe347` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-34.png` | `-` | `923254aaa20c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-35.png` | `-` | `1c48deb53f20` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-36.png` | `-` | `1ec36ea69760` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-37.png` | `-` | `0070a9703a57` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-38.png` | `-` | `d2a4b4466400` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-39.png` | `-` | `e2c02d228eb0` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-40.png` | `-` | `a59779f6410e` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-41.png` | `-` | `787c0d3abba9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-42.png` | `-` | `0b6a12ae228f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-43.png` | `-` | `19120549029c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-44.png` | `-` | `48c9bdc545f8` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-45.png` | `-` | `7c4d8d1e888c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-46.png` | `-` | `b092692f2974` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-47.png` | `-` | `38b31cb00e9c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-48.png` | `-` | `dff92f18a3d5` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-49.png` | `-` | `22e000d1dc90` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-50.png` | `-` | `8c725d21b21a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-51.png` | `-` | `4b38e01262a4` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-52.png` | `-` | `ebae884b77c5` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-53.png` | `-` | `494938cb91c9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-54.png` | `-` | `7b36dadc22bf` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-55.png` | `-` | `c36ce667896c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-56.png` | `-` | `f17416d246b9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-57.png` | `-` | `9164976dfeae` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-58.png` | `-` | `10d5c501d061` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-59.png` | `-` | `dfcb9fd3eb6a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-60.png` | `-` | `1b3fa518e237` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-61.png` | `-` | `f966f211354e` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-62.png` | `-` | `5c8064d7e7ea` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-63.png` | `-` | `f6cc6eec2c04` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-64.png` | `-` | `558c03485dce` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-65.png` | `-` | `d613cade3106` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-66.png` | `-` | `3edc69d16dca` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-67.png` | `-` | `f883b79e525c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-68.png` | `-` | `eeeebcfb20d1` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-69.png` | `-` | `4cab9aa8d996` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-70.png` | `-` | `184971bdba6b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-71.png` | `-` | `5abaf5270764` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-72.png` | `-` | `a4ec57f24c51` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-73.png` | `-` | `8892329413cc` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-74.png` | `-` | `54e1b437c74f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-75.png` | `-` | `5adb10b0fb8f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-76.png` | `-` | `ce5d8af85376` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-77.png` | `-` | `92ca120e6645` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/reconstructed.tex` | `-` | `7be05a737bc9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/source_ready.json` | `-` | `9cba70684b67` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-1.txt` | `-` | `e0a4c94e6763` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-10.txt` | `-` | `f6f190e11565` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-11.txt` | `-` | `ad93e8fcf847` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-12.txt` | `-` | `44fea84eced7` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-13.txt` | `-` | `6dc3a8b6e6ce` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-14.txt` | `-` | `0dd221d7fe42` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-15.txt` | `-` | `05080687a263` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-16.txt` | `-` | `47470f482106` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-17.txt` | `-` | `1c76adaec0f6` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-18.txt` | `-` | `8fbeef1db877` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-19.txt` | `-` | `473c6db146cf` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-2.txt` | `-` | `2ffaebc3222b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-20.txt` | `-` | `75f3002f9ec6` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-21.txt` | `-` | `0a78e85a58e5` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-22.txt` | `-` | `c5ee1e9f8883` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-23.txt` | `-` | `047cee02a21a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-24.txt` | `-` | `ced168acb9ec` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-25.txt` | `-` | `fe2a5885221d` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-26.txt` | `-` | `a096227ca7a6` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-27.txt` | `-` | `ec37f80d8a27` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-28.txt` | `-` | `0b292bfd3cac` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-29.txt` | `-` | `9817fe6f8089` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-3.txt` | `-` | `f0f674fad649` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-30.txt` | `-` | `6fee76cb5a4a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-31.txt` | `-` | `812f9cec95e3` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-32.txt` | `-` | `1e0469003c4f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-33.txt` | `-` | `7ed43e2c3296` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-34.txt` | `-` | `5147fd4160c1` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-35.txt` | `-` | `c3e808b742a6` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-36.txt` | `-` | `79015f2d7951` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-37.txt` | `-` | `0cac1a39aafc` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-38.txt` | `-` | `df38257d6425` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-39.txt` | `-` | `0bc46900550b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-4.txt` | `-` | `26fbd9596e36` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-40.txt` | `-` | `fab97c611e12` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-41.txt` | `-` | `9bbd640966f6` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-42.txt` | `-` | `eecf3a01541e` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-43.txt` | `-` | `1de1f5e98b28` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-44.txt` | `-` | `7aa1d1ae8e83` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-45.txt` | `-` | `043bb47f672e` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-46.txt` | `-` | `cb8764beaafe` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-47.txt` | `-` | `e9056da516d9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-48.txt` | `-` | `f15f3e0a1395` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-49.txt` | `-` | `afde326d5f0f` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-5.txt` | `-` | `7d5c97c7d92c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-50.txt` | `-` | `45a12bd8c1f7` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-51.txt` | `-` | `806164829e9b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-52.txt` | `-` | `765e5c57dc63` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-53.txt` | `-` | `9e05cd4bac67` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-54.txt` | `-` | `31b85af43259` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-55.txt` | `-` | `145e109e2b95` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-56.txt` | `-` | `79013fa18602` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-57.txt` | `-` | `66d0f2c0aa1d` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-58.txt` | `-` | `2c83ecb78570` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-59.txt` | `-` | `7ec883e5272a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-6.txt` | `-` | `28e634101375` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-60.txt` | `-` | `4512e64906ed` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-61.txt` | `-` | `d2987d34c3fc` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-62.txt` | `-` | `28fdf1883361` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-63.txt` | `-` | `1d4ac6ce02a2` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-64.txt` | `-` | `c6033665a8b3` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-65.txt` | `-` | `8a44b2b80162` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-66.txt` | `-` | `b8583e033a3a` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-67.txt` | `-` | `892d5da1b0d2` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-68.txt` | `-` | `6c881d04085c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-69.txt` | `-` | `435714b6b269` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-7.txt` | `-` | `1b9a70b0e22c` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-70.txt` | `-` | `b4917e26c0be` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-71.txt` | `-` | `c433b6d389a7` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-72.txt` | `-` | `42116507a396` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-73.txt` | `-` | `16be43e13a2b` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-74.txt` | `-` | `a1f53e0af6d9` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-75.txt` | `-` | `a8026361fb9d` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-76.txt` | `-` | `578d7e769981` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-77.txt` | `-` | `7c168201fe02` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-8.txt` | `-` | `8db088f136ac` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-9.txt` | `-` | `f4dc4757dbae` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text.txt` | `-` | `cefcc209f1ac` |
| modified | `.prime/agent/skills/article-loop/src/article_loop/ingestion.py` | `55c34b3b03a2` | `43df1a932fb3` |
| modified | `PLANS.md` | `a835f54a4020` | `abfc292512a8` |
| modified | `control/test_m3_ingestion.py` | `5d9df83c5971` | `b0874f8c8e3b` |
| modified | `docs/decisions.md` | `e4da251c4de0` | `094ae31b875a` |

### 2026-09-07T04:57:09Z — A fronteira de publicação da evidência M3 real foi corrigida sem mover, apagar ou reexecutar tentativas.

- Session ID: `m3-runtime-evidence-boundary-20260907`
- Fingerprint final: `07bd06008d6f89faf1b3b8e83ec95ad0f810430a390a47fd12380e4a539077c5`
- Git final: `2ff020dfe869`; status relevante: 7 item(ns)
- Delta factual: 5 adicionados, 415 modificados, 0 removidos

**Mudanças**

- runtime/m3-real-attempts/ passou a ser ignorado pelo Git para impedir inclusão acidental de PDF, texto extraído e imagens em commits ou PRs.
- O inventário de handoff agora classifica a raiz de tentativas M3 reais como runtime canônico e registra somente hash e tamanho.
- Adicionada regressão para o ignore e para a classificação metadata-only da evidência M3 real.

**Decisões**

- Evidência M3 real permanece create-only no checkout local; seu conteúdo não é fonte versionada, mas hashes e tamanhos continuam verificáveis no inventário local.

**Validações**

- 40 testes focados de handoff e M3 passaram; regressão integral passou com 510 testes; bin/check.sh, py_compile e git diff --check passaram.

**Riscos/limites**

- Não houve modelo, Prime Agent, backend, inferência, reserva, receipt, rede, API paga, nova tentativa M3 ou alteração dos artefatos existentes.

**Próximos passos**

- Revisar o diff completo M3 e a fronteira de evidência; commit, push e PR dependem de autorização explícita.

**Arquivos detectados**

| Tipo | Caminho | SHA anterior | SHA final |
|---|---|---|---|
| added | `runtime/m3-real-attempts/attempt-c133a0f9-2ada-4717-87c7-b4103f79fc74/artifacts/original/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/document.pdf` | `-` | `7a888ab15668` |
| added | `runtime/m3-real-attempts/attempt-c133a0f9-2ada-4717-87c7-b4103f79fc74/input/inbox/artigo.pdf` | `-` | `7a888ab15668` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/original/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/document.pdf` | `-` | `7a888ab15668` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/input/inbox/artigo.pdf` | `-` | `7a888ab15668` |
| added | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/baseline.pdf` | `-` | `7a888ab15668` |
| modified | `.gitignore` | `7e4121d14965` | `5a7c0798e825` |
| modified | `PLANS.md` | `abfc292512a8` | `7b349bcafaa7` |
| modified | `control/test_ai_handoff.py` | `aad996d05dc8` | `599a45af2739` |
| modified | `docs/decisions.md` | `094ae31b875a` | `03ca5c2a8a8c` |
| modified | `runtime/m3-real-attempts/attempt-c133a0f9-2ada-4717-87c7-b4103f79fc74/artifacts/original/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/manifest.json` | `8d3064e2d549` | `8d3064e2d549` |
| modified | `runtime/m3-real-attempts/attempt-c133a0f9-2ada-4717-87c7-b4103f79fc74/config/gates.yaml` | `2ee0a93dee8e` | `2ee0a93dee8e` |
| modified | `runtime/m3-real-attempts/attempt-c133a0f9-2ada-4717-87c7-b4103f79fc74/state/events/ingest-7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d.jsonl` | `31ec00c53e9f` | `31ec00c53e9f` |
| modified | `runtime/m3-real-attempts/attempt-c133a0f9-2ada-4717-87c7-b4103f79fc74/state/locks/ingest-7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d.lock` | `e3b0c44298fc` | `e3b0c44298fc` |
| modified | `runtime/m3-real-attempts/attempt-c133a0f9-2ada-4717-87c7-b4103f79fc74/state/snapshots/ingest-7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d.json` | `df5c2209ad9a` | `df5c2209ad9a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/coordinates.html` | `f3dfb58dd0c2` | `f3dfb58dd0c2` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/manifest.json` | `1597152b815f` | `1597152b815f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/normalized.json` | `7ceba5b337e9` | `7ceba5b337e9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-01.png` | `5164607c0873` | `5164607c0873` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-02.png` | `7f2ca5e57f40` | `7f2ca5e57f40` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-03.png` | `48467c667d58` | `48467c667d58` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-04.png` | `e74ced835f8d` | `e74ced835f8d` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-05.png` | `ecbc55b4e74b` | `ecbc55b4e74b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-06.png` | `936ebc1f1a40` | `936ebc1f1a40` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-07.png` | `f0149c6908bc` | `f0149c6908bc` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-08.png` | `ced0ce2331de` | `ced0ce2331de` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-09.png` | `3d17ee571b21` | `3d17ee571b21` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-10.png` | `f3b3afe0cc5b` | `f3b3afe0cc5b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-11.png` | `1cc658f643c6` | `1cc658f643c6` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-12.png` | `aeb2541f8114` | `aeb2541f8114` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-13.png` | `558e81573479` | `558e81573479` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-14.png` | `514cddd3db59` | `514cddd3db59` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-15.png` | `ab6b76289179` | `ab6b76289179` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-16.png` | `308c7290dcd3` | `308c7290dcd3` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-17.png` | `c23d6c61ce81` | `c23d6c61ce81` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-18.png` | `23d6afb8e50a` | `23d6afb8e50a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-19.png` | `c37e7719e531` | `c37e7719e531` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-20.png` | `a8bbd768185c` | `a8bbd768185c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-21.png` | `219b429b7fb8` | `219b429b7fb8` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-22.png` | `f284202648c5` | `f284202648c5` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-23.png` | `2dc67a648b31` | `2dc67a648b31` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-24.png` | `048b8516c292` | `048b8516c292` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-25.png` | `8e38a57b9a85` | `8e38a57b9a85` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-26.png` | `f18ad02a4e3f` | `f18ad02a4e3f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-27.png` | `acc74f6e9807` | `acc74f6e9807` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-28.png` | `272263eb07a2` | `272263eb07a2` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-29.png` | `df1ac8703fda` | `df1ac8703fda` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-30.png` | `eb9ca0cfb635` | `eb9ca0cfb635` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-31.png` | `3cf40ca22df2` | `3cf40ca22df2` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-32.png` | `debca3459201` | `debca3459201` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-33.png` | `aee15b1fe347` | `aee15b1fe347` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-34.png` | `923254aaa20c` | `923254aaa20c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-35.png` | `1c48deb53f20` | `1c48deb53f20` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-36.png` | `1ec36ea69760` | `1ec36ea69760` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-37.png` | `0070a9703a57` | `0070a9703a57` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-38.png` | `d2a4b4466400` | `d2a4b4466400` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-39.png` | `e2c02d228eb0` | `e2c02d228eb0` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-40.png` | `a59779f6410e` | `a59779f6410e` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-41.png` | `787c0d3abba9` | `787c0d3abba9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-42.png` | `0b6a12ae228f` | `0b6a12ae228f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-43.png` | `19120549029c` | `19120549029c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-44.png` | `48c9bdc545f8` | `48c9bdc545f8` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-45.png` | `7c4d8d1e888c` | `7c4d8d1e888c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-46.png` | `b092692f2974` | `b092692f2974` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-47.png` | `38b31cb00e9c` | `38b31cb00e9c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-48.png` | `dff92f18a3d5` | `dff92f18a3d5` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-49.png` | `22e000d1dc90` | `22e000d1dc90` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-50.png` | `8c725d21b21a` | `8c725d21b21a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-51.png` | `4b38e01262a4` | `4b38e01262a4` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-52.png` | `ebae884b77c5` | `ebae884b77c5` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-53.png` | `494938cb91c9` | `494938cb91c9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-54.png` | `7b36dadc22bf` | `7b36dadc22bf` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-55.png` | `c36ce667896c` | `c36ce667896c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-56.png` | `f17416d246b9` | `f17416d246b9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-57.png` | `9164976dfeae` | `9164976dfeae` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-58.png` | `10d5c501d061` | `10d5c501d061` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-59.png` | `dfcb9fd3eb6a` | `dfcb9fd3eb6a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-60.png` | `1b3fa518e237` | `1b3fa518e237` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-61.png` | `f966f211354e` | `f966f211354e` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-62.png` | `5c8064d7e7ea` | `5c8064d7e7ea` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-63.png` | `f6cc6eec2c04` | `f6cc6eec2c04` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-64.png` | `558c03485dce` | `558c03485dce` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-65.png` | `d613cade3106` | `d613cade3106` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-66.png` | `3edc69d16dca` | `3edc69d16dca` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-67.png` | `f883b79e525c` | `f883b79e525c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-68.png` | `eeeebcfb20d1` | `eeeebcfb20d1` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-69.png` | `4cab9aa8d996` | `4cab9aa8d996` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-70.png` | `184971bdba6b` | `184971bdba6b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-71.png` | `5abaf5270764` | `5abaf5270764` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-72.png` | `a4ec57f24c51` | `a4ec57f24c51` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-73.png` | `8892329413cc` | `8892329413cc` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-74.png` | `54e1b437c74f` | `54e1b437c74f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-75.png` | `5adb10b0fb8f` | `5adb10b0fb8f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-76.png` | `ce5d8af85376` | `ce5d8af85376` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-77.png` | `92ca120e6645` | `92ca120e6645` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/reconstructed.tex` | `7be05a737bc9` | `7be05a737bc9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/source_ready.json` | `9cba70684b67` | `9cba70684b67` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-1.txt` | `e0a4c94e6763` | `e0a4c94e6763` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-10.txt` | `f6f190e11565` | `f6f190e11565` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-11.txt` | `ad93e8fcf847` | `ad93e8fcf847` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-12.txt` | `44fea84eced7` | `44fea84eced7` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-13.txt` | `6dc3a8b6e6ce` | `6dc3a8b6e6ce` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-14.txt` | `0dd221d7fe42` | `0dd221d7fe42` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-15.txt` | `05080687a263` | `05080687a263` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-16.txt` | `47470f482106` | `47470f482106` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-17.txt` | `1c76adaec0f6` | `1c76adaec0f6` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-18.txt` | `8fbeef1db877` | `8fbeef1db877` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-19.txt` | `473c6db146cf` | `473c6db146cf` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-2.txt` | `2ffaebc3222b` | `2ffaebc3222b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-20.txt` | `75f3002f9ec6` | `75f3002f9ec6` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-21.txt` | `0a78e85a58e5` | `0a78e85a58e5` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-22.txt` | `c5ee1e9f8883` | `c5ee1e9f8883` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-23.txt` | `047cee02a21a` | `047cee02a21a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-24.txt` | `ced168acb9ec` | `ced168acb9ec` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-25.txt` | `fe2a5885221d` | `fe2a5885221d` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-26.txt` | `a096227ca7a6` | `a096227ca7a6` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-27.txt` | `ec37f80d8a27` | `ec37f80d8a27` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-28.txt` | `0b292bfd3cac` | `0b292bfd3cac` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-29.txt` | `9817fe6f8089` | `9817fe6f8089` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-3.txt` | `f0f674fad649` | `f0f674fad649` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-30.txt` | `6fee76cb5a4a` | `6fee76cb5a4a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-31.txt` | `812f9cec95e3` | `812f9cec95e3` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-32.txt` | `1e0469003c4f` | `1e0469003c4f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-33.txt` | `7ed43e2c3296` | `7ed43e2c3296` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-34.txt` | `5147fd4160c1` | `5147fd4160c1` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-35.txt` | `c3e808b742a6` | `c3e808b742a6` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-36.txt` | `79015f2d7951` | `79015f2d7951` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-37.txt` | `0cac1a39aafc` | `0cac1a39aafc` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-38.txt` | `df38257d6425` | `df38257d6425` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-39.txt` | `0bc46900550b` | `0bc46900550b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-4.txt` | `26fbd9596e36` | `26fbd9596e36` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-40.txt` | `fab97c611e12` | `fab97c611e12` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-41.txt` | `9bbd640966f6` | `9bbd640966f6` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-42.txt` | `eecf3a01541e` | `eecf3a01541e` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-43.txt` | `1de1f5e98b28` | `1de1f5e98b28` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-44.txt` | `7aa1d1ae8e83` | `7aa1d1ae8e83` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-45.txt` | `043bb47f672e` | `043bb47f672e` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-46.txt` | `cb8764beaafe` | `cb8764beaafe` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-47.txt` | `e9056da516d9` | `e9056da516d9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-48.txt` | `f15f3e0a1395` | `f15f3e0a1395` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-49.txt` | `afde326d5f0f` | `afde326d5f0f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-5.txt` | `7d5c97c7d92c` | `7d5c97c7d92c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-50.txt` | `45a12bd8c1f7` | `45a12bd8c1f7` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-51.txt` | `806164829e9b` | `806164829e9b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-52.txt` | `765e5c57dc63` | `765e5c57dc63` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-53.txt` | `9e05cd4bac67` | `9e05cd4bac67` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-54.txt` | `31b85af43259` | `31b85af43259` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-55.txt` | `145e109e2b95` | `145e109e2b95` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-56.txt` | `79013fa18602` | `79013fa18602` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-57.txt` | `66d0f2c0aa1d` | `66d0f2c0aa1d` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-58.txt` | `2c83ecb78570` | `2c83ecb78570` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-59.txt` | `7ec883e5272a` | `7ec883e5272a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-6.txt` | `28e634101375` | `28e634101375` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-60.txt` | `4512e64906ed` | `4512e64906ed` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-61.txt` | `d2987d34c3fc` | `d2987d34c3fc` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-62.txt` | `28fdf1883361` | `28fdf1883361` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-63.txt` | `1d4ac6ce02a2` | `1d4ac6ce02a2` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-64.txt` | `c6033665a8b3` | `c6033665a8b3` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-65.txt` | `8a44b2b80162` | `8a44b2b80162` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-66.txt` | `b8583e033a3a` | `b8583e033a3a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-67.txt` | `892d5da1b0d2` | `892d5da1b0d2` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-68.txt` | `6c881d04085c` | `6c881d04085c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-69.txt` | `435714b6b269` | `435714b6b269` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-7.txt` | `1b9a70b0e22c` | `1b9a70b0e22c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-70.txt` | `b4917e26c0be` | `b4917e26c0be` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-71.txt` | `c433b6d389a7` | `c433b6d389a7` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-72.txt` | `42116507a396` | `42116507a396` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-73.txt` | `16be43e13a2b` | `16be43e13a2b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-74.txt` | `a1f53e0af6d9` | `a1f53e0af6d9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-75.txt` | `a8026361fb9d` | `a8026361fb9d` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-76.txt` | `578d7e769981` | `578d7e769981` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-77.txt` | `7c168201fe02` | `7c168201fe02` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-8.txt` | `8db088f136ac` | `8db088f136ac` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text-page-9.txt` | `f4dc4757dbae` | `f4dc4757dbae` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/extracted/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/text.txt` | `cefcc209f1ac` | `cefcc209f1ac` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/original/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/manifest.json` | `8d3064e2d549` | `8d3064e2d549` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/manifest.json` | `91d527f8f5a5` | `91d527f8f5a5` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-01.png` | `5164607c0873` | `5164607c0873` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-02.png` | `7f2ca5e57f40` | `7f2ca5e57f40` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-03.png` | `48467c667d58` | `48467c667d58` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-04.png` | `e74ced835f8d` | `e74ced835f8d` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-05.png` | `ecbc55b4e74b` | `ecbc55b4e74b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-06.png` | `936ebc1f1a40` | `936ebc1f1a40` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-07.png` | `f0149c6908bc` | `f0149c6908bc` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-08.png` | `ced0ce2331de` | `ced0ce2331de` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-09.png` | `3d17ee571b21` | `3d17ee571b21` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-10.png` | `f3b3afe0cc5b` | `f3b3afe0cc5b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-11.png` | `1cc658f643c6` | `1cc658f643c6` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-12.png` | `aeb2541f8114` | `aeb2541f8114` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-13.png` | `558e81573479` | `558e81573479` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-14.png` | `514cddd3db59` | `514cddd3db59` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-15.png` | `ab6b76289179` | `ab6b76289179` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-16.png` | `308c7290dcd3` | `308c7290dcd3` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-17.png` | `c23d6c61ce81` | `c23d6c61ce81` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-18.png` | `23d6afb8e50a` | `23d6afb8e50a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-19.png` | `c37e7719e531` | `c37e7719e531` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-20.png` | `a8bbd768185c` | `a8bbd768185c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-21.png` | `219b429b7fb8` | `219b429b7fb8` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-22.png` | `f284202648c5` | `f284202648c5` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-23.png` | `2dc67a648b31` | `2dc67a648b31` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-24.png` | `048b8516c292` | `048b8516c292` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-25.png` | `8e38a57b9a85` | `8e38a57b9a85` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-26.png` | `f18ad02a4e3f` | `f18ad02a4e3f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-27.png` | `acc74f6e9807` | `acc74f6e9807` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-28.png` | `272263eb07a2` | `272263eb07a2` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-29.png` | `df1ac8703fda` | `df1ac8703fda` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-30.png` | `eb9ca0cfb635` | `eb9ca0cfb635` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-31.png` | `3cf40ca22df2` | `3cf40ca22df2` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-32.png` | `debca3459201` | `debca3459201` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-33.png` | `aee15b1fe347` | `aee15b1fe347` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-34.png` | `923254aaa20c` | `923254aaa20c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-35.png` | `1c48deb53f20` | `1c48deb53f20` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-36.png` | `1ec36ea69760` | `1ec36ea69760` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-37.png` | `0070a9703a57` | `0070a9703a57` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-38.png` | `d2a4b4466400` | `d2a4b4466400` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-39.png` | `e2c02d228eb0` | `e2c02d228eb0` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-40.png` | `a59779f6410e` | `a59779f6410e` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-41.png` | `787c0d3abba9` | `787c0d3abba9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-42.png` | `0b6a12ae228f` | `0b6a12ae228f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-43.png` | `19120549029c` | `19120549029c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-44.png` | `48c9bdc545f8` | `48c9bdc545f8` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-45.png` | `7c4d8d1e888c` | `7c4d8d1e888c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-46.png` | `b092692f2974` | `b092692f2974` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-47.png` | `38b31cb00e9c` | `38b31cb00e9c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-48.png` | `dff92f18a3d5` | `dff92f18a3d5` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-49.png` | `22e000d1dc90` | `22e000d1dc90` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-50.png` | `8c725d21b21a` | `8c725d21b21a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-51.png` | `4b38e01262a4` | `4b38e01262a4` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-52.png` | `ebae884b77c5` | `ebae884b77c5` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-53.png` | `494938cb91c9` | `494938cb91c9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-54.png` | `7b36dadc22bf` | `7b36dadc22bf` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-55.png` | `c36ce667896c` | `c36ce667896c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-56.png` | `f17416d246b9` | `f17416d246b9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-57.png` | `9164976dfeae` | `9164976dfeae` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-58.png` | `10d5c501d061` | `10d5c501d061` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-59.png` | `dfcb9fd3eb6a` | `dfcb9fd3eb6a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-60.png` | `1b3fa518e237` | `1b3fa518e237` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-61.png` | `f966f211354e` | `f966f211354e` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-62.png` | `5c8064d7e7ea` | `5c8064d7e7ea` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-63.png` | `f6cc6eec2c04` | `f6cc6eec2c04` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-64.png` | `558c03485dce` | `558c03485dce` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-65.png` | `d613cade3106` | `d613cade3106` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-66.png` | `3edc69d16dca` | `3edc69d16dca` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-67.png` | `f883b79e525c` | `f883b79e525c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-68.png` | `eeeebcfb20d1` | `eeeebcfb20d1` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-69.png` | `4cab9aa8d996` | `4cab9aa8d996` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-70.png` | `184971bdba6b` | `184971bdba6b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-71.png` | `5abaf5270764` | `5abaf5270764` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-72.png` | `a4ec57f24c51` | `a4ec57f24c51` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-73.png` | `8892329413cc` | `8892329413cc` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-74.png` | `54e1b437c74f` | `54e1b437c74f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-75.png` | `5adb10b0fb8f` | `5adb10b0fb8f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-76.png` | `ce5d8af85376` | `ce5d8af85376` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/artifacts/rendered/7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d/pages/page-77.png` | `92ca120e6645` | `92ca120e6645` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/config/gates.yaml` | `2ee0a93dee8e` | `2ee0a93dee8e` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/state/events/ingest-7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d.jsonl` | `c53b3edf94f4` | `c53b3edf94f4` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/state/locks/ingest-7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d.lock` | `e3b0c44298fc` | `e3b0c44298fc` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/state/snapshots/ingest-7a888ab156684c927bd017fd24d4ca28650bedc88f9709b6bae3046593a76d9d.json` | `c0aced74dc5b` | `c0aced74dc5b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/ingestion-manifest.json` | `6c3a09e76b94` | `6c3a09e76b94` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/manifest.json` | `3b8b62f1742a` | `3b8b62f1742a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/coordinates.html` | `f3dfb58dd0c2` | `f3dfb58dd0c2` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/manifest.json` | `1597152b815f` | `1597152b815f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/normalized.json` | `7ceba5b337e9` | `7ceba5b337e9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-01.png` | `5164607c0873` | `5164607c0873` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-02.png` | `7f2ca5e57f40` | `7f2ca5e57f40` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-03.png` | `48467c667d58` | `48467c667d58` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-04.png` | `e74ced835f8d` | `e74ced835f8d` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-05.png` | `ecbc55b4e74b` | `ecbc55b4e74b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-06.png` | `936ebc1f1a40` | `936ebc1f1a40` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-07.png` | `f0149c6908bc` | `f0149c6908bc` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-08.png` | `ced0ce2331de` | `ced0ce2331de` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-09.png` | `3d17ee571b21` | `3d17ee571b21` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-10.png` | `f3b3afe0cc5b` | `f3b3afe0cc5b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-11.png` | `1cc658f643c6` | `1cc658f643c6` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-12.png` | `aeb2541f8114` | `aeb2541f8114` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-13.png` | `558e81573479` | `558e81573479` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-14.png` | `514cddd3db59` | `514cddd3db59` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-15.png` | `ab6b76289179` | `ab6b76289179` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-16.png` | `308c7290dcd3` | `308c7290dcd3` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-17.png` | `c23d6c61ce81` | `c23d6c61ce81` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-18.png` | `23d6afb8e50a` | `23d6afb8e50a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-19.png` | `c37e7719e531` | `c37e7719e531` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-20.png` | `a8bbd768185c` | `a8bbd768185c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-21.png` | `219b429b7fb8` | `219b429b7fb8` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-22.png` | `f284202648c5` | `f284202648c5` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-23.png` | `2dc67a648b31` | `2dc67a648b31` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-24.png` | `048b8516c292` | `048b8516c292` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-25.png` | `8e38a57b9a85` | `8e38a57b9a85` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-26.png` | `f18ad02a4e3f` | `f18ad02a4e3f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-27.png` | `acc74f6e9807` | `acc74f6e9807` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-28.png` | `272263eb07a2` | `272263eb07a2` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-29.png` | `df1ac8703fda` | `df1ac8703fda` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-30.png` | `eb9ca0cfb635` | `eb9ca0cfb635` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-31.png` | `3cf40ca22df2` | `3cf40ca22df2` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-32.png` | `debca3459201` | `debca3459201` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-33.png` | `aee15b1fe347` | `aee15b1fe347` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-34.png` | `923254aaa20c` | `923254aaa20c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-35.png` | `1c48deb53f20` | `1c48deb53f20` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-36.png` | `1ec36ea69760` | `1ec36ea69760` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-37.png` | `0070a9703a57` | `0070a9703a57` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-38.png` | `d2a4b4466400` | `d2a4b4466400` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-39.png` | `e2c02d228eb0` | `e2c02d228eb0` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-40.png` | `a59779f6410e` | `a59779f6410e` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-41.png` | `787c0d3abba9` | `787c0d3abba9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-42.png` | `0b6a12ae228f` | `0b6a12ae228f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-43.png` | `19120549029c` | `19120549029c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-44.png` | `48c9bdc545f8` | `48c9bdc545f8` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-45.png` | `7c4d8d1e888c` | `7c4d8d1e888c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-46.png` | `b092692f2974` | `b092692f2974` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-47.png` | `38b31cb00e9c` | `38b31cb00e9c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-48.png` | `dff92f18a3d5` | `dff92f18a3d5` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-49.png` | `22e000d1dc90` | `22e000d1dc90` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-50.png` | `8c725d21b21a` | `8c725d21b21a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-51.png` | `4b38e01262a4` | `4b38e01262a4` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-52.png` | `ebae884b77c5` | `ebae884b77c5` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-53.png` | `494938cb91c9` | `494938cb91c9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-54.png` | `7b36dadc22bf` | `7b36dadc22bf` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-55.png` | `c36ce667896c` | `c36ce667896c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-56.png` | `f17416d246b9` | `f17416d246b9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-57.png` | `9164976dfeae` | `9164976dfeae` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-58.png` | `10d5c501d061` | `10d5c501d061` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-59.png` | `dfcb9fd3eb6a` | `dfcb9fd3eb6a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-60.png` | `1b3fa518e237` | `1b3fa518e237` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-61.png` | `f966f211354e` | `f966f211354e` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-62.png` | `5c8064d7e7ea` | `5c8064d7e7ea` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-63.png` | `f6cc6eec2c04` | `f6cc6eec2c04` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-64.png` | `558c03485dce` | `558c03485dce` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-65.png` | `d613cade3106` | `d613cade3106` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-66.png` | `3edc69d16dca` | `3edc69d16dca` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-67.png` | `f883b79e525c` | `f883b79e525c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-68.png` | `eeeebcfb20d1` | `eeeebcfb20d1` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-69.png` | `4cab9aa8d996` | `4cab9aa8d996` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-70.png` | `184971bdba6b` | `184971bdba6b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-71.png` | `5abaf5270764` | `5abaf5270764` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-72.png` | `a4ec57f24c51` | `a4ec57f24c51` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-73.png` | `8892329413cc` | `8892329413cc` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-74.png` | `54e1b437c74f` | `54e1b437c74f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-75.png` | `5adb10b0fb8f` | `5adb10b0fb8f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-76.png` | `ce5d8af85376` | `ce5d8af85376` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/pages/page-77.png` | `92ca120e6645` | `92ca120e6645` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/reconstructed.tex` | `7be05a737bc9` | `7be05a737bc9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/source_ready.json` | `9cba70684b67` | `9cba70684b67` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-1.txt` | `e0a4c94e6763` | `e0a4c94e6763` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-10.txt` | `f6f190e11565` | `f6f190e11565` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-11.txt` | `ad93e8fcf847` | `ad93e8fcf847` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-12.txt` | `44fea84eced7` | `44fea84eced7` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-13.txt` | `6dc3a8b6e6ce` | `6dc3a8b6e6ce` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-14.txt` | `0dd221d7fe42` | `0dd221d7fe42` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-15.txt` | `05080687a263` | `05080687a263` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-16.txt` | `47470f482106` | `47470f482106` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-17.txt` | `1c76adaec0f6` | `1c76adaec0f6` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-18.txt` | `8fbeef1db877` | `8fbeef1db877` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-19.txt` | `473c6db146cf` | `473c6db146cf` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-2.txt` | `2ffaebc3222b` | `2ffaebc3222b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-20.txt` | `75f3002f9ec6` | `75f3002f9ec6` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-21.txt` | `0a78e85a58e5` | `0a78e85a58e5` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-22.txt` | `c5ee1e9f8883` | `c5ee1e9f8883` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-23.txt` | `047cee02a21a` | `047cee02a21a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-24.txt` | `ced168acb9ec` | `ced168acb9ec` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-25.txt` | `fe2a5885221d` | `fe2a5885221d` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-26.txt` | `a096227ca7a6` | `a096227ca7a6` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-27.txt` | `ec37f80d8a27` | `ec37f80d8a27` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-28.txt` | `0b292bfd3cac` | `0b292bfd3cac` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-29.txt` | `9817fe6f8089` | `9817fe6f8089` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-3.txt` | `f0f674fad649` | `f0f674fad649` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-30.txt` | `6fee76cb5a4a` | `6fee76cb5a4a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-31.txt` | `812f9cec95e3` | `812f9cec95e3` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-32.txt` | `1e0469003c4f` | `1e0469003c4f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-33.txt` | `7ed43e2c3296` | `7ed43e2c3296` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-34.txt` | `5147fd4160c1` | `5147fd4160c1` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-35.txt` | `c3e808b742a6` | `c3e808b742a6` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-36.txt` | `79015f2d7951` | `79015f2d7951` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-37.txt` | `0cac1a39aafc` | `0cac1a39aafc` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-38.txt` | `df38257d6425` | `df38257d6425` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-39.txt` | `0bc46900550b` | `0bc46900550b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-4.txt` | `26fbd9596e36` | `26fbd9596e36` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-40.txt` | `fab97c611e12` | `fab97c611e12` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-41.txt` | `9bbd640966f6` | `9bbd640966f6` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-42.txt` | `eecf3a01541e` | `eecf3a01541e` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-43.txt` | `1de1f5e98b28` | `1de1f5e98b28` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-44.txt` | `7aa1d1ae8e83` | `7aa1d1ae8e83` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-45.txt` | `043bb47f672e` | `043bb47f672e` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-46.txt` | `cb8764beaafe` | `cb8764beaafe` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-47.txt` | `e9056da516d9` | `e9056da516d9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-48.txt` | `f15f3e0a1395` | `f15f3e0a1395` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-49.txt` | `afde326d5f0f` | `afde326d5f0f` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-5.txt` | `7d5c97c7d92c` | `7d5c97c7d92c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-50.txt` | `45a12bd8c1f7` | `45a12bd8c1f7` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-51.txt` | `806164829e9b` | `806164829e9b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-52.txt` | `765e5c57dc63` | `765e5c57dc63` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-53.txt` | `9e05cd4bac67` | `9e05cd4bac67` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-54.txt` | `31b85af43259` | `31b85af43259` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-55.txt` | `145e109e2b95` | `145e109e2b95` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-56.txt` | `79013fa18602` | `79013fa18602` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-57.txt` | `66d0f2c0aa1d` | `66d0f2c0aa1d` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-58.txt` | `2c83ecb78570` | `2c83ecb78570` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-59.txt` | `7ec883e5272a` | `7ec883e5272a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-6.txt` | `28e634101375` | `28e634101375` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-60.txt` | `4512e64906ed` | `4512e64906ed` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-61.txt` | `d2987d34c3fc` | `d2987d34c3fc` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-62.txt` | `28fdf1883361` | `28fdf1883361` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-63.txt` | `1d4ac6ce02a2` | `1d4ac6ce02a2` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-64.txt` | `c6033665a8b3` | `c6033665a8b3` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-65.txt` | `8a44b2b80162` | `8a44b2b80162` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-66.txt` | `b8583e033a3a` | `b8583e033a3a` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-67.txt` | `892d5da1b0d2` | `892d5da1b0d2` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-68.txt` | `6c881d04085c` | `6c881d04085c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-69.txt` | `435714b6b269` | `435714b6b269` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-7.txt` | `1b9a70b0e22c` | `1b9a70b0e22c` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-70.txt` | `b4917e26c0be` | `b4917e26c0be` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-71.txt` | `c433b6d389a7` | `c433b6d389a7` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-72.txt` | `42116507a396` | `42116507a396` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-73.txt` | `16be43e13a2b` | `16be43e13a2b` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-74.txt` | `a1f53e0af6d9` | `a1f53e0af6d9` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-75.txt` | `a8026361fb9d` | `a8026361fb9d` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-76.txt` | `578d7e769981` | `578d7e769981` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-77.txt` | `7c168201fe02` | `7c168201fe02` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-8.txt` | `8db088f136ac` | `8db088f136ac` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text-page-9.txt` | `f4dc4757dbae` | `f4dc4757dbae` |
| modified | `runtime/m3-real-attempts/attempt-e4686df9-2fbe-49f3-9f4f-f6358adbd211/versions/champion/v0000/source/text.txt` | `cefcc209f1ac` | `cefcc209f1ac` |
| modified | `scripts/ai_handoff_common.py` | `36c5f8907375` | `383b2f011d5c` |
