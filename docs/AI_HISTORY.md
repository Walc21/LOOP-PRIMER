# Histórico evolutivo e atualizações de sessão — article-loop

> Gerado por `scripts/ai_history.py`. O histórico Git e os ADRs são reconstruídos; as atualizações de sessão vêm do ledger append-only `docs/ai_sessions.jsonl`.

## Baseline registrado

- Fingerprint das fontes: `eb05e97f915ce52ccdf84dd6a04f7a3796c78887835084ce2a816783ff9601b3`
- Registrado em: `2026-09-03T22:48:42Z`
- Git: branch `main`, HEAD `ba316b50a707`
- Arquivos relevantes: 197

## Evolução reconstruída do versionamento

| Marco | Intervalo | Commits | Evolução inferida | Áreas tocadas |
|---|---:|---:|---|---|
| M0/M0.5 | 2026-08-12 | 1 | Auditoria de compatibilidade, segurança e fixação da arquitetura canônica. | AGENTS.md, PLANS.md, docs/architecture.md, docs/compatibility.md, docs/decisions.md |
| M0.6 | 2026-08-12 | 1 | Completude de paths e ordem transacional do pipeline. | PLANS.md, docs/architecture.md, docs/decisions.md |
| M1/M1.1 | 2026-08-13 | 1 | Scaffold, catálogo de papéis e contratos condicionais em JSON Schema. | .gitignore, .prime/agent/APPEND_SYSTEM.md, .prime/agent/prompts/.gitkeep, .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/… |
| M2 | 2026-08-13 | 4 | Máquina de estados, event log encadeado, replay e recuperação durável. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/arti… |
| M3 | 2026-08-13 | 5 | Ingestão PDF/ZIP offline, preservação do original e baseline v0000. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/ingestion.py, .prime/ha… |
| sem marco explícito | 2026-08-13..2026-09-02 | 44 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | .github/ISSUE_TEMPLATE/bug_report.md, .github/ISSUE_TEMPLATE/feature_request.md, .github/copilot-instructions.md, .github/pull_request_template.md, .github/workflows/ci.yml, .giti… |
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
| M12.5 | 2026-09-03 | 6 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/budget.py, .prime/agent… |

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
- ADR-027 — Separação de audiências e histórico Git publicável
- ADR-028 — M10: política pura e finalização transacional por referência
- ADR-029 — M10.1: pacote final canônico e recuperação coberta por fase
- ADR-030 — M11: comandos locais e integração Prime Agent fail-closed
- ADR-031 — M12: orçamento durável e observabilidade fail-closed
- ADR-032 — M12.5: routing determinístico governado pelo ledger M12
- ADR-033 — M12.5.1 Phase A: execução dual ligada ao contrato M6

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
