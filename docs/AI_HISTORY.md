# Histórico evolutivo e atualizações de sessão — article-loop

> Gerado por `scripts/ai_history.py`. O histórico Git e os ADRs são reconstruídos; as atualizações de sessão vêm do ledger append-only `docs/ai_sessions.jsonl`.

## Baseline registrado

- Fingerprint das fontes: `b94ca8b644688f7fc7471700095cdfe3a55a8ec3baee9cd69af72dbdcd53501a`
- Registrado em: `2026-09-02T17:30:21Z`
- Git: branch `main`, HEAD `35e2f80bea39`
- Arquivos relevantes: 160

## Evolução reconstruída do versionamento

| Marco | Intervalo | Commits | Evolução inferida | Áreas tocadas |
|---|---:|---:|---|---|
| M0/M0.5 | 2026-08-12 | 1 | Auditoria de compatibilidade, segurança e fixação da arquitetura canônica. | AGENTS.md, PLANS.md, docs/architecture.md, docs/compatibility.md, docs/decisions.md |
| M0.6 | 2026-08-12 | 1 | Completude de paths e ordem transacional do pipeline. | PLANS.md, docs/architecture.md, docs/decisions.md |
| M1/M1.1 | 2026-08-13 | 1 | Scaffold, catálogo de papéis e contratos condicionais em JSON Schema. | .gitignore, .prime/agent/APPEND_SYSTEM.md, .prime/agent/prompts/.gitkeep, .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/… |
| M2 | 2026-08-13 | 4 | Máquina de estados, event log encadeado, replay e recuperação durável. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/arti… |
| M3 | 2026-08-13 | 5 | Ingestão PDF/ZIP offline, preservação do original e baseline v0000. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/ingestion.py, .prime/ha… |
| sem marco explícito | 2026-08-13..2026-09-02 | 43 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | .github/ISSUE_TEMPLATE/bug_report.md, .github/ISSUE_TEMPLATE/feature_request.md, .github/copilot-instructions.md, .github/pull_request_template.md, .github/workflows/ci.yml, .giti… |
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
