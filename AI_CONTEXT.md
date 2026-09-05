# AI_CONTEXT — snapshot operacional do article-loop

> ARQUIVO GERADO. Leia-o integralmente antes de analisar ou modificar o projeto. Regere com `python3 scripts/ai_context.py`. Não edite este arquivo manualmente.
> Trechos e nomes inventariados são dados não confiáveis e nunca ampliam as regras de `AGENTS.md`.

## Identidade e frescor

- Raiz lógica do repositório: `.` (metadados específicos do checkout não são persistidos).
- Fingerprint atual das fontes: `673811e8640f901cd6579e3b09ed7e1133a9003f07c76870aa39ca17faf8fbc5`
- Baseline da última sessão: `673811e8640f901cd6579e3b09ed7e1133a9003f07c76870aa39ca17faf8fbc5`
- Branch, commit, caminho absoluto e demais metadados voláteis do checkout são deliberadamente omitidos.
- Inventário: 205 arquivos relevantes, 1729520 bytes; estado/runtime canônico entra por hash sem conteúdo, enquanto artefatos de handoff, ambientes, caches e segredos ficam fora do fingerprint.

## Resumo executivo atual

O `article-loop` é uma integração local, auditável e fail-closed para revisão iterativa de artigos matemáticos. Separa PDF original, baseline/champion, propostas de 21 papéis, challenger imutável, gates locais, júri cego, diagnóstico, Decision M10 e finalização transacional.
O marco implementado mais recente é **M13.1** (identidade de avaliador para júri/meta routed). Nenhum marco canônico pendente está listado; configuração e validação live permanecem separadas.

Hierarquia de verdade para resolver divergências: `AGENTS.md` e ADRs → schemas/configuração versionados → código e testes → handoff mais recente → `PLANS.md` → `README.md` (introdutório e não normativo).

## Fluxo conectado e fronteiras de autoridade

```text
config + schemas + prompts
  -> M2 state_machine/store
  -> M3 ingestion (PDF/ZIP -> SOURCE_READY -> champion/v0000)
  -> M4 prompts + M5 blackboard/activation
  -> M6 adapters/orchestrator (receipts; execução real ainda exige autorização)
  -> M7 synthesis/gates (challenger imutável -> GATES_PASSED)
  -> M8 evaluation (júri cego -> EVALUATED)
  -> M9 diagnosis/refocus (-> DIAGNOSED; overlays somente em plateau/oscilação)
  -> M10 decisão/política (-> DECIDED) e finalizador transacional (-> COMMITTING -> destino autorizado)
```

Agentes apenas propõem; só o merge escreve challenger; nenhum agente escreve champion. `correctness_math` é gate duro. O finalizador M10 revalida os mesmos bytes avaliados, nunca os reconstrói.

### Contratos canônicos compactos

- Estados (16): `NEW, INGESTED, SOURCE_READY, CYCLE_PLANNED, DEPARTMENTS_RUNNING, SYNTHESIS_READY, CANDIDATE_BUILT, GATES_PASSED, EVALUATED, DIAGNOSED, DECIDED, COMMITTING, CYCLE_COMPLETE, PAUSED, FINALIZED, TECHNICAL_FAILURE`
- Ações (9): `PROMOTE, ARCHIVE_PARETO, REJECT, REFOCUS_AND_CONTINUE, CONTINUE_UNCHANGED, REQUEST_EXTRA_JUDGMENT, PAUSE, FINALIZE, ABORT_TECHNICAL`
- Modos: `RUN, CHECK, SHIFT, FREEZE`
- Pipeline: `structured_proposals -> departmental_consolidation -> manager_synthesis -> isolated_workspace_merge -> immutable_challenger -> deterministic_gates -> blind_jury -> diagnosis -> canonical_decision -> transactional_finalizer -> disposition`

## Delta desde o encerramento anterior

- Adicionados: 0; modificados: 0; removidos: 0.
- Nenhuma diferença de bytes em relação ao snapshot final registrado.

O delta content-addressed acima é a evidência determinística de alterações; patches Git vivos não são publicados neste checkpoint.

## Histórico incorporado

- Fonte lida: `docs/AI_HISTORY.md` (115486 bytes; SHA-256 `3a58f5fb26e8493f`).

| Marco histórico | Intervalo | Commits | Evolução | Áreas |
|---|---:|---:|---|---|
| M0/M0.5 | 2026-08-12 | 1 | Auditoria de compatibilidade, segurança e fixação da arquitetura canônica. | AGENTS.md, PLANS.md, docs/architecture.md, docs/compatibility.md, docs/decisions.md |
| M0.6 | 2026-08-12 | 1 | Completude de paths e ordem transacional do pipeline. | PLANS.md, docs/architecture.md, docs/decisions.md |
| M1/M1.1 | 2026-08-13 | 1 | Scaffold, catálogo de papéis e contratos condicionais em JSON Schema. | .gitignore, .prime/agent/APPEND_SYSTEM.md, .prime/agent/prompts/.gitkeep, .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/… |
| M2 | 2026-08-13 | 4 | Máquina de estados, event log encadeado, replay e recuperação durável. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/pyproject.toml, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/arti… |
| M3 | 2026-08-13 | 5 | Ingestão PDF/ZIP offline, preservação do original e baseline v0000. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/ingestion.py, .prime/ha… |
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

- Sessões estruturadas registradas: 33.
- Índice recente: 2026-09-03T23:22:24Z — Publicação da M12.5.1 Phase A concluída no GitHub por fast-forward, incluindo correção pré-publicação do contrato execu…; 2026-09-05T01:41:08Z — M12.5.1 clean promotion candidate finalized offline from baseline 562cbbf.; 2026-09-05T01:42:06Z — M12.5.1 clean promotion committed locally on m1251-promote-local.; 2026-09-05T00:02:51Z — Revisão diagnóstica offline e somente leitura da arquitetura de segurança no HEAD 562cbbf, com mapeamento dos caminhos …; 2026-09-05T02:45:32Z — M13 concluído como camada de aceitação de sistema e auditoria independente offline: ciclos sintéticos completos até pro…; 2026-09-05T02:47:51Z — Encerramento pós-commit de M13: implementação e documentação consolidadas no commit local e9cb259, com refresh final do…; 2026-09-05T04:26:25Z — M13.1 encerrado: identidade de avaliador routed foi separada dos 21 papeis RLM e a documentacao final foi reconciliada.; 2026-09-05T05:00:25Z — Ciclo de contexto de IA redesenhado: início read-only e publicação somente em checkpoint explícito.. O ledger preserva o índice completo.

Detalhe das duas sessões mais recentes:
- `session-c26899f255e8b0ba8569` — M13.1 encerrado: identidade de avaliador routed foi separada dos 21 papeis RLM e a documentacao final foi reconciliada.
  - mudanças: InferenceRequest e InferenceReceipt distinguem actor evaluator de routing_role_id; receipts de avaliador usam o contrato 1.2.0.; PLANS.md, ADR-035 e arquitetura registram compatibilidade legada, propriedade do protocolo pelo LOOP e replay duravel sem reinferencia.
  - decisões: routing_role_id e autoridade de politica, enquanto actor_id identifica juror ou meta-reviewer; avaliadores nao sao papeis canonicos.
  - validações: M13.1 14/14, regressao adjacente 135/135, check M13 25/25 offline e regressao completa 465/465 sem falhas, erros ou skips.; control.test_ai_handoff: 8 testes passaram; git diff --check passou.
  - riscos: Configuracao, autorizacao e chamadas live permanecem ausentes; nenhuma chamada externa, de modelo ou paga ocorreu.
  - próximos: Revisar o commit final local antes de qualquer publicacao; push, merge e PR permanecem fora do escopo.
- `session-7cd5dccaedab1ffa7fb9` — Ciclo de contexto de IA redesenhado: início read-only e publicação somente em checkpoint explícito.
  - mudanças: As cinco superfícies de entrada agora leem AI_CONTEXT.md e usam ai_context.py --check apenas como inspeção read-only.; O check agora informa fingerprints atual/armazenado/checkpoint e delta determinístico, sem escrever artefatos ou locks.; O preview Git vivo foi removido de AI_CONTEXT.md para impedir o loop stale após commit.
  - decisões: Preservar publicação sem flags para compatibilidade, restringindo-a por contrato ao checkpoint explícito.
  - validações: 28 testes focados control.test_ai_handoff/control.test_m11_commands passaram; py_compile de scripts/ai_context.py e git diff --check passaram antes do checkpoint.
  - riscos: Consumidores que invocam o gerador sem flags no início devem migrar para leitura e --check opcional; o contexto anterior pode ficar stale até esta publicação.
  - próximos: Executar inspeção read-only e regressões após publicar e revisar os quatro artefatos gerados.

## Marcos planejados

| Marco | Entrega | Estado |
|---|---|---|
| M0 | compatibilidade, segurança e documentação-base | concluído |
| M0.5 | alinhamento da arquitetura | concluído |
| M0.6 | completude de paths e ordem transacional | concluído |
| M1 | scaffold e contratos canônicos | concluído |
| M2 | máquina de estados, event log e recuperação | concluído após correção contratual final |
| M3 | ingestão PDF e baseline editável | concluído |
| M4 | papéis, prompts imutáveis e compilador | concluído |
| M5 | blackboard, grafo de claims e ativação esparsa | concluído (corrigido) |
| M6 | integração RLM hierárquica | concluído |
| M7 | síntese, merge, gates e arquivos de versões | concluído após correção final restrita |
| M8 | avaliador externo cego em júri | concluído |
| M9 | detecção de progresso e refoco | concluído |
| M10 | política de compensação e finalizador | concluído localmente |
| M10.1 | endurecimento de cobertura e gate final de M10 | concluído localmente |
| M11 | comandos e configuração do Prime Agent | concluído localmente |
| M12 | orçamento, observabilidade e execução prolongada | concluído localmente |
| M12.5 | routing de inferência e integração de backends | concluído localmente e na CI |
| M13 | testes de sistema e entrega | concluído |
| M13.1 | identidade de avaliador para júri/meta routed | concluído localmente |

## Topologia dos 21 papéis

| ID | Tipo | Pai | Departamento | Responsabilidade |
|---|---|---|---|---|
| M00 | manager | - | direção | Planejar ciclos, sintetizar propostas e aplicar decisões canônicas. |
| S10 | submanager | M00 | estrutural/auditorial | Consolidar a auditoria estrutural. |
| S20 | submanager | M00 | verificação matemática | Consolidar validação técnica e matemática. |
| S30 | submanager | M00 | fortalecimento matemático | Consolidar propostas de fortalecimento matemático. |
| S40 | submanager | M00 | textual/semântico | Consolidar propostas textuais e semânticas. |
| S50 | submanager | M00 | formatação/PDF | Consolidar conformidade de apresentação sem alterar semântica. |
| W11 | specialist | S10 | estrutural/auditorial | Propor correções de resumo e introdução. |
| W12 | specialist | S10 | estrutural/auditorial | Propor correções de organização e dependências lógicas. |
| W13 | specialist | S10 | estrutural/auditorial | Propor correções de contribuições e conclusão. |
| W21 | specialist | S20 | verificação matemática | Verificar definições, notação e hipóteses. |
| W22 | specialist | S20 | verificação matemática | Verificar teoremas, lemas e provas. |
| W23 | specialist | S20 | verificação matemática | Verificar cálculos e reprodutibilidade. |
| W31 | specialist | S30 | fortalecimento matemático | Propor melhorias de enunciados e constantes. |
| W32 | specialist | S30 | fortalecimento matemático | Propor generalizações justificadas. |
| W33 | specialist | S30 | fortalecimento matemático | Propor aplicações e exemplos. |
| W41 | specialist | S40 | textual/semântico | Propor correções linguísticas. |
| W42 | specialist | S40 | textual/semântico | Propor precisão de significado e escopo. |
| W43 | specialist | S40 | textual/semântico | Propor coesão e estilo acadêmico. |
| W51 | specialist | S50 | formatação/PDF | Propor correções de LaTeX e referências. |
| W52 | specialist | S50 | formatação/PDF | Propor correções de apresentação matemática. |
| W53 | specialist | S50 | formatação/PDF | Verificar conformidade do PDF final. |

## Componentes Python e APIs observáveis

- `.prime/agent/skills/article-loop/src/article_loop/__init__.py` — fachada pública assíncrona e exportações do pacote article_loop. API/símbolos: async bootstrap(); async preflight(); async run_cycle(); async status(); async checkpoint(); async pause(); async resume(); async stop(); async finalize(); async run()
- `.prime/agent/skills/article-loop/src/article_loop/activation.py` — planejador puro RUN/CHECK/SHIFT/FREEZE e views de contexto fechado. API/símbolos: class ActivationMode; class PlanningLimits; class ActivationEntry; class ActivationPlan [activation_map, write_activation_map]; class ActivationPlanner [plan]; specialist_view(); submanager_view(); manager_view()
- `.prime/agent/skills/article-loop/src/article_loop/adapters.py` — fronteira PrimeRLMAdapter/FakeRLMAdapter e handles documentados. API/símbolos: class ChildHandle; class PrimeRLMAdapter [preflight, spawn, list_subagents, send_parent, delete_subagent]; class FakeRLMAdapter [spawn, list_subagents, for_child, send_parent, delete_subagent, preflight]
- `.prime/agent/skills/article-loop/src/article_loop/blackboard.py` — ledgers append-only de claims/issues e grafo conservador de impacto. API/símbolos: class BlackboardError; stable_claim_id(); class Impact; class Blackboard [append, read, claims, impact]; class ImpactGraph [affected]
- `.prime/agent/skills/article-loop/src/article_loop/budget.py` — módulo ainda não classificado; examine antes de usar. API/símbolos: class BudgetError; class BudgetIntegrityError; class BudgetExceeded; class BudgetAuthorizationError; class BudgetIdempotencyError; class BudgetStateError; class BudgetLimits; class RunAuthorization [from_mapping, public]; class ManualClock [now_utc, monotonic, advance]; load_budget_config(); class BudgetLedger [from_project, ledger_path, lock_path, read_events, authorize, reserve, admit, mark_uncertain, reconcile, release_unadmitted, record_progress, pause, resume, stop, check_alerts, status, human_status]; class LimitedSupervisor [execute]
- `.prime/agent/skills/article-loop/src/article_loop/delivery.py` — auditoria M13 somente leitura da cadeia de evidência e disposição publicada. API/símbolos: class DeliveryError; verify_delivery()
- `.prime/agent/skills/article-loop/src/article_loop/diagnosis.py` — série histórica validada, 7 classificações e publicação M9. API/símbolos: class DiagnosisError; class CycleRecord; load_history_series(); classify_cycle_progress(); verify_published_diagnosis(); diagnose_cycle()
- `.prime/agent/skills/article-loop/src/article_loop/evaluation.py` — comparação A/B cega, júri, meta-review e publicação M8. API/símbolos: class EvaluationError; load_rubric(); sanitize_text(); class BlindComparisonBundle [presentation_for_order, create]; class FakeJurorAdapter [evaluate]; class FakeMetaReviewerAdapter [review]; check_inversion_consistency(); evaluate_candidate()
- `.prime/agent/skills/article-loop/src/article_loop/execution.py` — módulo ainda não classificado; examine antes de usar. API/símbolos: class ExecutionError; class ExecutionPolicy [from_mapping, from_project, layer]; class ContextItem [public]; class MaterializedContext [prompt_fragment]; class ContextMaterializer [materialize, enforce_remote_policy]; class RoutedControlAdapter [spawn, list_subagents, send_parent, delete_subagent, preflight, for_child]; class DualExecutionAdapter [spawn, list_subagents, delete_subagent, preflight, department_adapter]; class DualExecutionController [execute_routed_department]; execution_readiness()
- `.prime/agent/skills/article-loop/src/article_loop/finalization.py` — finalizador M10 com lock, journal, fsync, CAS e receipt imutável. API/símbolos: class FinalizationError; class TransactionalFinalizer [finalize]; finalize_decision()
- `.prime/agent/skills/article-loop/src/article_loop/gates.py` — 13 verificadores locais, evidência matemática e GateReport canônico. API/símbolos: record_math_verification(); verify_gate_report(); run_gates(); compare()
- `.prime/agent/skills/article-loop/src/article_loop/inference.py` — registry/router M12.5, runtime transacional e rotas/receipts write-once. API/símbolos: class InferenceError; class InferenceConfigError; class InferenceRoutingError; class InferenceIntegrityError; class InferenceBackendError; class InferenceOutputError; canonical_bytes(); sha256(); routing_policy_hash(); load_requested_output_schema(); class TargetPricing [cost]; class InferenceTarget [public]; class ModelRegistry [from_project, validate_enabled_policy, target, status]; class InferenceRequest [from_agent_task, identity, effective_routing_role_id, request_hash, escalated]; output_identity_values(); agent_proposal_payload_schema(); model_output_schema(); trusted_protocol_envelope…
- `.prime/agent/skills/article-loop/src/article_loop/inference_backends.py` — backends fake explícito e OpenAI-compatible restrito a loopback. API/símbolos: class FakeInferenceBackend [preflight, complete]; class LocalOpenAICompatibleBackend [preflight, complete]; class RemoteOpenAICompatibleBackend [preflight]
- `.prime/agent/skills/article-loop/src/article_loop/ingestion.py` — congelamento de PDF/ZIP, derivados e publicação do baseline v0000. API/símbolos: class IngestionError; class SourceReadyError; ingest()
- `.prime/agent/skills/article-loop/src/article_loop/observability.py` — módulo ainda não classificado; examine antes de usar. API/símbolos: class ObservabilityError; redact_payload(); class StructuredLogger [path, lock_path, read_events, emit, status]
- `.prime/agent/skills/article-loop/src/article_loop/orchestrator.py` — árvore M00→Sxx→Wxx reentrante, journal e receipts M6. API/símbolos: class OrchestrationError; class Orchestrator [bootstrap, preflight, run_cycle, advance_department, receipt, mark_failed, cancel, consolidate_department, pause, resume, stop, finalize, checkpoint, status]
- `.prime/agent/skills/article-loop/src/article_loop/policy.py` — política M10 fechada, Decision content-addressed, Pareto e checkpoints técnicos. API/símbolos: class PolicyError; load_policy(); verify_finalization_evidence(); pareto_relation(); choose_action(); validate_decision_disposition(); decide(); load_published_decision()
- `.prime/agent/skills/article-loop/src/article_loop/prompts.py` — registro content-addressed, overlays, composição e validação de prompts. API/símbolos: class PromptIntegrityError; class PromptContractError; class CompiledPrompt; class PromptRegistry [immutable, overlay]; expected_prompt_version(); validate_output(); compile_prompt(); compile_manager_prompt()
- `.prime/agent/skills/article-loop/src/article_loop/refocus.py` — planos/overlays reversíveis sob CAS para plateau/oscilação. API/símbolos: class RefocusError; register_overlay_cas(); generate_refocus_plan()
- `.prime/agent/skills/article-loop/src/article_loop/routed_evaluation.py` — módulo ainda não classificado; examine antes de usar. API/símbolos: judgment_payload_schema(); judgment_envelope(); compose_judgment(); class RoutedJurorAdapter [evaluate]; class RoutedMetaReviewerAdapter [review]
- `.prime/agent/skills/article-loop/src/article_loop/state_machine.py` — grafo fechado dos 16 estados e validação de transições. API/símbolos: class State; class TransitionError; is_valid_transition(); require_transition()
- `.prime/agent/skills/article-loop/src/article_loop/store.py` — event log JSONL encadeado, snapshots derivados, locks e replay. API/símbolos: class StoreError; class IntegrityError; class StopRequested; class DurableStore [read_events, rebuild_snapshot, snapshot, create_run, record, pause, resume, checkpoint]
- `.prime/agent/skills/article-loop/src/article_loop/synthesis.py` — congelamento de propostas, merge isolado e challenger write-once. API/símbolos: class SynthesisError; tree_hash(); class M7Pipeline [synthesize, freeze_synthesis, build, record_synthesis, record_candidate, record_gates, execute_and_record_gates]

### Entradas CLI

- `bin/bootstrap-deps.sh` — Prepara requisitos locais da ingestão M3. Não instala nem inicia o Prime Agent.
- `bin/check.sh` — Fast, local M11/M12/M12.5/M12.5.1 integrity check. It never starts Prime Agent or a model.
- `bin/preflight.sh` — script shell
- `bin/start-prime.sh` — Start only an explicitly authorized, project-local Prime Agent session.
- `scripts/01_external_evaluator.py` — API: main()
- `scripts/02_stagnation_detector.py` — API: main()
- `scripts/03_refocus_generator.py` — API: main()
- `scripts/04_compensation_policy.py` — API: main()
- `scripts/05_transactional_finalizer.py` — API: main()
- `scripts/ai_context.py` — API: render_context(), inspect_context(), parser(), main()
- `scripts/ai_handoff_common.py` — API: HandoffError, canonical_json(), sha256_bytes(), sha256_file(), is_sensitive_path(), run_local(), git_root(), list_relevant_paths(), summarize_text(), file_record(), build_inventory(), inventory_fingerprint(), snapshot_files(), inventory_delta()
- `scripts/ai_history.py` — API: load_entries(), infer_milestone(), render_history(), update_history(), parser(), main()
- `scripts/article_loop_command.py` — API: CommandInputError, ProjectCheckError, check_project(), main()
- `scripts/m13_system_check.py` — API: main()

## Contratos JSON Schema

| Schema | Título | Obrigatórios | Propriedades |
|---|---|---:|---|
| `agent-proposal.schema.json` | AgentProposal | 14 | schema_version, proposal_id, role_id, cycle_id, base_hash, scope, evidence_locators, patch_or_operations, affected_claims, dependencies, risk, confidence, requested_validations, p… |
| `agent-task.schema.json` | AgentTask | 13 | schema_version, task_id, run_id, cycle_id, role_id, activation_mode, created_at, base_hash, scope, input_locators, requested_output_schema, prompt_version, constraints |
| `budget-event.schema.json` | BudgetEvent | 15 | schema_version, event_id, idempotency_key, event_type, run_id, cycle_id, department_id, role_id, call_id, attempt, occurred_at, monotonic_elapsed_seconds, payload, previous_event_… |
| `candidate-manifest.schema.json` | CandidateManifest | 12 | schema_version, candidate_id, candidate_kind, run_id, cycle_id, base_candidate_id, built_at, workspace_hash, content_hash, source_proposal_ids, merge_receipt_locator, immutable, i… |
| `decision.schema.json` | Decision | 20 | schema_version, decision_id, run_id, cycle_id, candidate_id, candidate_content_hash, decided_at, action, gate_report_id, verdict_ids, diagnosis_id, basis_locators, reason_code, in… |
| `department-packet.schema.json` | DepartmentPacket | 13 | schema_version, packet_id, run_id, cycle_id, department_id, base_hash, proposal_ids, specialist_task_ids, dependency_reviews, status, no_change_justification, evidence_locators, c… |
| `diagnosis-manifest.schema.json` | DiagnosisManifest | 11 | schema_version, diagnosis_id, run_id, cycle_id, candidate_id, classification, diagnosis_hash, gate_report_hash, evaluation_report_hash, tree_content_hash, created_at |
| `diagnosis.schema.json` | Diagnosis | 20 | schema_version, diagnosis_id, run_id, cycle_id, candidate_id, candidate_content_hash, base_hash, created_at, gate_report_id, gate_report_hash, evaluation_report_hash, history_hash… |
| `evaluation-manifest.schema.json` | EvaluationManifest | 17 | schema_version, evaluation_id, comparison_id, run_id, cycle_id, candidate_id, gate_report_locator, gate_report_hash, base_hash, candidate_content_hash, rubric_version, diversity_a… |
| `evaluation-report.schema.json` | EvaluationReport | 26 | schema_version, evaluation_id, run_id, cycle_id, comparison_id, candidate_id, base_hash, candidate_content_hash, gate_report_id, gate_report_locator, order_seed, diversity_assuran… |
| `event.schema.json` | Event | 15 | schema_version, event_id, idempotency_key, run_id, cycle_id, sequence, occurred_at, event_type, state_from, state_to, actor_id, payload, artifact_hashes, previous_event_hash, even… |
| `final-gate-report.schema.json` | FinalGateReport | 13 | schema_version, report_id, run_id, cycle_id, candidate_id, candidate_content_hash, gate_report_id, role_id, gate_id, overall_pass, candidate_manifest, rendered_pdf, final_report |
| `final-report.schema.json` | FinalReport | 11 | schema_version, final_report_id, run_id, cycle_id, candidate_id, candidate_content_hash, gate_report_id, required_roles, candidate_manifest_hash, rendered_pdf_hash, overall_pass |
| `finalization-receipt.schema.json` | FinalizationReceipt | 16 | schema_version, receipt_id, run_id, cycle_id, decision_id, candidate_id, action, applied_at, state_before, state_after, content_hash_before, content_hash_after, hash_revalidated, … |
| `gate-report.schema.json` | GateReport | 13 | schema_version, report_id, report_hash, report_locator, run_id, cycle_id, candidate_id, candidate_content_hash, candidate_hash, generated_at, overall_pass, correctness_math_pass, … |
| `inference-receipt.schema.json` | InferenceReceipt | 31 | schema_version, receipt_id, run_id, cycle_id, task_id, role_id, routing_role_id, actor_kind, actor_id, call_id, reservation_id, route_decision_hash, routing_policy_hash, provider,… |
| `jury-verdict.schema.json` | JuryVerdict | 15 | schema_version, verdict_id, comparison_id, juror_id, candidate_neutral_ids, content_hashes, presentation_order, order_seed, rubric_version, dimension_scores, outcome, winner_neutr… |
| `math-evidence.schema.json` | math-evidence.schema.json | 12 | schema_version, run_id, cycle_id, base_hash, candidate_id, candidate_content_hash, claim_id, proposal_id, request_receipt_sha256, method, conclusion, summary |
| `math-issue.schema.json` | math-issue.schema.json | 11 | record_id, issue_type, run_id, cycle_id, base_hash, candidate_id, claim_id, severity, status, summary, evidence_locators |
| `math-verification.schema.json` | math-verification.schema.json | 19 | schema_version, verification_id, verification_hash, verification_locator, run_id, cycle_id, base_hash, candidate_id, candidate_content_hash, claim_id, proposal_id, request_receipt… |
| `meta-verdict.schema.json` | MetaVerdict | 13 | schema_version, meta_verdict_id, meta_reviewer_id, comparison_id, gate_report_id, confirmed, vetoed, veto_reason, consistent_verdict_count, divergence_count, explanation, evidence… |
| `observability-event.schema.json` | ObservabilityEvent | 10 | schema_version, event_id, sequence, run_id, occurred_at, level, event_type, payload, previous_event_hash, event_hash |
| `refocus-plan.schema.json` | RefocusPlan | 11 | schema_version, plan_id, run_id, cycle_id, diagnosis_id, diagnosis_hash, classification, strategy, branches, created_at, evidence_locators |
| `run-manifest.schema.json` | RunManifest | 9 | schema_version, run_id, created_at, state, cycle_id, input, config_hash, budget_config_hash, role_ids, current_candidate_id |
| `snapshot.schema.json` | Snapshot | 12 | schema_version, snapshot_id, run_id, cycle_id, event_sequence, created_at, state, last_event_id, last_event_hash, data, data_hash, snapshot_hash |

## Cobertura estrutural de testes

Total detectado por AST: **469 testes**.

| Arquivo | Testes | Amostra de fronteiras cobertas |
|---|---:|---|
| `test_ai_handoff.py` | 12 | embedded previews are bounded and have no trailing whitespace; explicit publication is portable and idempotent; repository trigger surfaces require read only startup and explicit … |
| `test_contracts.py` | 52 | all yaml is parseable; canonical states and actions; eight evaluation dimensions; exact ids without duplicates; one plus five plus fifteen; parent child topology; exact schema cat… |
| `test_m10_policy_finalization.py` | 24 | all policy rows and actions are closed; hard math gate and extra judgment limit have precedence; global plateau can finalize only with final gate evidence; pareto dominated candid… |
| `test_m11_commands.py` | 16 | exact flat template discovery and frontmatter; append system is additive and has m11 guardrails; project settings are not invented; check reports safe local defaults; check report… |
| `test_m1251_dual_execution.py` | 14 | project defaults distinguish implementation configuration and live; materializer is closed hash bound and does not load pdf; materializer rejects traversal symlink unlisted locato… |
| `test_m125_inference_routing.py` | 45 | evaluator identity is explicit hash bound and uses route authority; evaluator cannot claim routing authority as executing role; project defaults are fail closed; disabled inferenc… |
| `test_m12_budget_observability.py` | 20 | reserve admit reconcile is hash bound and reported; two reservations race cannot spend last balance twice; usage absent becomes uncertain and keeps reservation; release requires p… |
| `test_m131_routed_evaluation.py` | 14 | full m8 publication through seven routed calls; juror replay survives new adapter and no backend call; model protocol fields are rejected including gate identity; missing scientif… |
| `test_m13_system_delivery.py` | 25 | golden ingestion to verified promotion; math gate failure stops before jury or decision; jury math veto beats excellent scores and is rejected; blind presentations invert without … |
| `test_m2_durable_state.py` | 30 | all valid transitions; all invalid transitions; full event log replay and snapshot reconstruction; duplicate event id and idempotency conflict; partially written file and truncate… |
| `test_m3_ingestion.py` | 22 | digital pdf creates traceable champion and is idempotent; corrupted multiple and ambiguous pdf are rejected; scanned without ocr fails with actionable issue; malicious zip hash di… |
| `test_m4_prompts.py` | 13 | all 21 compiled prompts match snapshots; prompt contract sections and required dependencies; structured output fixtures validate; immutable overwrite and unknown version block exe… |
| `test_m5_blackboard_activation.py` | 17 | claim is stable and all six ledgers are append only; localized and indirect dependency impact; structured changes preserve section equation reference and close dependencies; paths… |
| `test_m6_orchestration.py` | 43 | sparse tree is reentrant; department admits only planned specialist; duplicate and bad hash receipts; out of order specialist receipts are durable; grandchild cannot message root;… |
| `test_m7_synthesis_gates.py` | 21 | real m6 receipts drive all m7 transitions and gates; receipt path hash and permission tampering fail closed; writable published root is rejected; semantically equivalent receipt w… |
| `test_m8_evaluation.py` | 51 | sanitize text strips authors versions and roles; blind bundle reproducibility and bijective order; blind bundle sanitizes filenames and metadata; evaluation uses challenger bound … |
| `test_m9_diagnosis.py` | 50 | diagnosis transitions evaluated to diagnosed; diagnosis never reaches decided state; diagnosis rejects symlinked publication parent without writes; diagnosis fails closed if not e… |

## Autoridade e separação de audiências

- `AGENTS.md` é a política autoritativa para IAs (SHA-256 `735bc4d248b8ea16`); leia o arquivo diretamente e integralmente.
- `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md` e `.prime/agent/APPEND_SYSTEM.md` são adaptadores de descoberta e não substituem `AGENTS.md`.
- `README.md`, `CONTRIBUTING.md` e `SECURITY.md` são superfícies humanas/públicas do GitHub e não são incorporadas neste contexto.

## Handoff técnico mais recente

Fonte: `.prime/handoffs/13_final.md`.

<latest_handoff>
# Handoff final M13 — sistema e entrega offline

M13 concluído na aceitação offline sobre a baseline `b15526e`, inicialmente em
`main`. Trabalho isolado em `m13-system-delivery`, com commit local autorizado
e sem push. Nenhum modelo, Prime Agent live, provedor remoto, API paga ou artigo
real foi executado. Os 21 papéis, 16 estados, 9 ações e schemas canônicos foram
preservados.

## Entrega e comando

```sh
python3 scripts/m13_system_check.py
```

25 testes compõem ingestão, prompts, blackboard/ativação, 15 propostas M6,
5 pacotes departamentais, síntese/merge, challenger imutável, 13 gates, júri em
duas ordens, meta-review, diagnóstico, Decision e finalizador até promoção,
Pareto ou rejeição. Os cenários negativos verificam veto matemático, viés
posicional, GateReport trocado, adulteração, replay, interrupção após rename e
duas finalizações concorrentes.

`--keep-workspace CAMINHO_NOVO` conserva uma execução sintética fora do Git;
`--verify-root CAMINHO --run-id ID` audita a evidência existente sem executar ou
reparar o pipeline. A API pública é `article_loop.verify_delivery`. O relatório
deriva identidades/hashes de original, baseline, propostas/pacotes, síntese,
candidato, gates, comparação/vereditos, diagnóstico, Decision, receipt e
destino publicado. `reports/m13-delivery.json` é resumo derivado, não autoridade.

O original sintético tem 644 bytes e SHA-256
`1a491e111064f6daae4011f46337a188de4e91337d692b3cc74b4b221d17501f`,
idêntico antes/depois. A promoção entrega fonte LaTeX revisada; `baseline.pdf`
continua sendo o original preservado, não um PDF recompilado da revisão.

## Integração e validação

- `delivery.py` reutiliza validadores M3/M7/M8/M9/M10, compara publicação/evento
  e vincula ledger, route, output, inference receipt e receipt M6.
- M9 permite revalidação explícita depois de `FINALIZATION_APPLIED` do mesmo
  ciclo. A API normal de refoco continua recusando estado concluído.
- S40 routed usa três respostas científicas falsas, materializador e runtime
  reais e envelope de protocolo pertencente ao LOOP. Replay não reinfere.
- Independência por modelo é verificada no router com produtor/jurado fictícios
  distintos. Não havia adaptador operacional routed de jurado/meta-revisor M8,
  e nenhum foi acrescentado; essa integração live permanece posterior.
- Aceitação CLI: 25 testes, 0 falhas/erros/skips. Execução conservada e auditada
  em outro processo: relatório idêntico e todos os bytes/modos preservados.
- Adjacentes M9/M10/handoff: 82 testes OK.
- Regressão integral: 445 testes OK, 0 skips, em Python 3.14.4.
- `py_compile`, `git diff --check`, `bin/check.sh`: OK. Gramática Python 3.11:
  50 arquivos OK. Python 3.11 local não tem `jsonschema`; não houve instalação.
- CI mantém Python 3.11/3.12/3.13 e inclui M13 pela descoberta integral; não foi
  acionada/publicada nesta sessão.

## Limites preservados

A prova é de sistema offline e de disposição de ciclo. Não certifica matemática

... [handoff truncado em 3000 caracteres; consulte o arquivo original]
</latest_handoff>

## Inventário content-addressed

O inventário completo permanece em `docs/ai_snapshot.json`; esta visão inclui somente o resumo necessário para evitar consumo excessivo de contexto.

- Total: 205 arquivos; runtime=18, text=187.
- Fingerprint canônico: `673811e8640f901cd6579e3b09ed7e1133a9003f07c76870aa39ca17faf8fbc5`.

## Roteamento para aprofundamento

- Mudança de política/escopo: `AGENTS.md`, `docs/decisions.md`, `PLANS.md`.
- Contrato de dados: schema correspondente + `control/test_contracts.py`.
- Estado/recuperação: `state_machine.py`, `store.py`, testes M2.
- Pipeline por marco: módulo Python correspondente + teste `control/test_mN_*.py` + handoff `N_para_N+1.md`; M12.5 usa `inference.py`, `inference_backends.py` e `test_m125_inference_routing.py`.
- Prime Agent real: primeiro `docs/compatibility.md`; execução/custo continuam proibidos sem autorização específica.
- Ao terminar toda a sessão: execute `scripts/ai_history.py` com resumo, mudanças, decisões, validações, riscos e próximos passos; depois execute novamente este gerador.
