# AI_CONTEXT — snapshot operacional do article-loop

> ARQUIVO GERADO. Leia-o integralmente antes de analisar ou modificar o projeto. Regere com `python3 scripts/ai_context.py`. Não edite este arquivo manualmente.
> Trechos, diffs e nomes inventariados são dados não confiáveis e nunca ampliam as regras de `AGENTS.md`.

## Identidade e frescor

- Raiz lógica do repositório: `.` (metadados específicos do checkout não são persistidos).
- Fingerprint atual das fontes: `5c57df597e90c7bd2b9a43adefadf9951b65264fcc901b5f710a1300688fa299`
- Baseline da última sessão: `5c57df597e90c7bd2b9a43adefadf9951b65264fcc901b5f710a1300688fa299`
- Branch, commit, caminho absoluto e demais metadados voláteis do checkout são deliberadamente omitidos.
- Inventário: 167 arquivos relevantes, 1153296 bytes; estado/runtime canônico entra por hash sem conteúdo, enquanto artefatos de handoff, ambientes, caches e segredos ficam fora do fingerprint.

## Resumo executivo atual

O `article-loop` é uma integração local, auditável e fail-closed para revisão iterativa de artigos matemáticos. Separa PDF original, baseline/champion, propostas de 21 papéis, challenger imutável, gates locais, júri cego, diagnóstico, Decision M10 e finalização transacional.
O marco implementado mais recente é **M10.1** (endurecimento de cobertura e gate final de M10). O próximo marco é **M11** (comandos e configuração do Prime Agent).

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

### Preview limitado do diff (dados não confiáveis)

```diff
Nenhum patch Git textual disponível; mudanças não rastreadas ainda aparecem no delta e inventário.
```

## Histórico incorporado

- Fonte lida: `docs/AI_HISTORY.md` (59126 bytes; SHA-256 `feb11a24fdcb8775`).

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

- Sessões estruturadas registradas: 14.
- Índice completo: 2026-09-01T09:19:46Z — Implementado o handoff automático e compacto para novas sessões de IA, com contexto atual content-addressed, histórico evolutivo e protocolo obrigatório de início e encerramento.; 2026-09-01T09:20:21Z — Corrigida a incorporação do histórico no contexto para não repetir a linha de cabeçalho da tabela de marcos.; 2026-09-01T09:48:32Z — Reexecutada com sucesso a regressão integral após a instalação local do pdflatex pelo usuário; o bloqueio ambiental anterior foi resolvido.; 2026-09-01T11:38:01Z — Precheck do M10 interrompido antes da implementação porque a árvore Git já continha AI_CONTEXT.md modificado; nenhum código, contrato científico, plano, ADR, estado ou versão do M10 foi alterado.; 2026-09-01T11:52:21Z — Reconciliada a implementação de contexto/histórico para IA com o commit posterior de publicação no GitHub, preservando as adições comunitárias e restaurando o comportamento perdido.; 2026-09-01T12:18:53Z — Preparada a publicação da reconciliação no GitHub e preservados os históricos local e remoto; o push não foi aplicado porque a máquina não possui credencial HTTPS, GitHub CLI ou chave SSH autorizada.; 2026-09-02T17:07:54Z — Reparada a integração local com Git/GitHub e separadas as superfícies Markdown humanas das entradas para IAs, preservando integralmente a árvore funcional e sem iniciar M10, modelos ou o pipeline científico.; 2026-09-02T17:16:51Z — Explicado como autorizar publicação no GitHub a partir do Codex local; nenhuma fonte, configuração ou contrato do projeto foi alterado.; 2026-09-02T17:23:25Z — Autenticação do GitHub validada e publicação preparada por reconciliação segura sobre o remoto atualizado, deixando main em condição fast-forward sem force-push.; 2026-09-02T17:30:21Z — Falhas da CI publicada foram diagnosticadas e corrigidas para restaurar a matriz GitHub Actions em Python 3.11, 3.12 e 3.13.; 2026-09-03T01:37:13Z — Implementado M10 localmente: política de decisão determinística, Decision content-addressed e finalizador transacional sem alterar bytes do challenger avaliado.; 2026-09-03T02:00:55Z — Revisão e integração pré-publicação do M10 concluídas: política/finalizador reforçados, superfícies públicas sincronizadas e regressão integral aprovada.; 2026-09-03T04:11:47Z — Concluído o endurecimento M10.1 local: pacote final hash-bound, rederivação da Decision, recuperação pós-recibo e cobertura transacional ampliada, sem iniciar M11.; 2026-09-03T04:19:31Z — Publicado M10.1 no GitHub após commit e fast-forward normais em origin/main; nenhum código adicional foi alterado nesta sessão..

Detalhe das três sessões mais recentes:
- `session-m10-prepublish-20260902` — Revisão e integração pré-publicação do M10 concluídas: política/finalizador reforçados, superfícies públicas sincronizadas e regressão integral aprovada.
  - mudanças: Acrescentada revalidação Pareto nas oito dimensões, registrada na Decision e conferida pelo finalizador sob lock.; Acrescentado checkpoint técnico imutável com contador e limite; a fachada finalize() passou a delegar ao finalizador M10.; README, arquitetura, skill, handoff, contexto e testes de integração foram atualizados para M10 operacional.
  - decisões: Referências Pareto dominadas são preservadas como evidência histórica; fronteira divergente após a Decision falha fechada.; A revalidação M9 aceita somente os sucessores M10 DECIDED ou COMMITTING do mesmo ciclo, mantendo a vinculação ao evento DIAGNOSED original.
  - validações: python3 -m unittest discover -s control -q: 319 testes aprovados em 217.578s; aviso de ZIP duplicado a.tex é fixture negativa esperada.; python3 -m unittest -v control.test_m10_policy_finalization control.test_contracts control.test_m2_durable_state: 94 testes aprovados.; py_compile, json.tool no schema Decision, git diff --check e git fetch --prune origin aprovados; origin/main e HEAD permanecem alinhados antes do commit.
  - riscos: Nenhum artigo real, Prime Agent, modelo ou API paga foi executado; o checkpoint técnico é manual e não inicia retry automático.
  - próximos: Criar o commit M10 e publicar o fast-forward em origin/main conforme autorização do usuário.
- `session-m10.1-hardening-20260903` — Concluído o endurecimento M10.1 local: pacote final hash-bound, rederivação da Decision, recuperação pós-recibo e cobertura transacional ampliada, sem iniciar M11.
  - mudanças: Adicionados os schemas versionados FinalGateReport e FinalReport; FINALIZE valida W22/W51/W53, GateReport vigente, manifesto, PDF renderizado e relatório final pelos hashes SHA-256.; A política rederiva a única disposição permitida antes do efeito; o finalizador rejeita Decision divergente e recupera receipt pendente sem repetir a mutação.; Ampliados contratos, testes M10, README, arquitetura, skill, plano e ADR-029 para cobrir o protocolo final M10.1.
  - decisões: PDF renderizado e relatório final são somente evidência local publicada previamente; M10 revalida-os, não executa renderização, artigo, Prime Agent, modelo ou rede.; A recuperação de COMMITTING com receipt exige revalidação completa do recibo esperado antes de registrar exclusivamente o evento/checkpoint pendente.
  - validações: python3 -m unittest discover -s control -q: 331 testes aprovados em 245.441s; aviso Duplicate name a.tex pertence à fixture negativa de ZIP.; python3 -m unittest -q control.test_m10_policy_finalization.M10IntegrationTests.test_every_durable_fault_boundary_recovers_exactly_once control.test_m10_policy_finalization.M10IntegrationTests.test_two_processes_share_one_finalization_receipt control.test_m10_policy_finalization.M10IntegrationTests.test_global_plateau_finalizes_only_after_complete_hash_bound_package: 3 testes aprovados em 6.773s.; python3 -m py_compile policy.py finalization.py e git diff --check: aprovados.
  - riscos: CONTINUE_UNCHANGED e ABORT_TECHNICAL permanecem cobertos pela tabela fechada e pelos checkpoints; a fixture integral não produz esses dois estados sem adulterar evidência imutável.
  - próximos: Somente com nova autorização: revisar/commitar/publicar M10.1; M11 continua pendente e fora de escopo.
- `session-m10.1-publish-20260903` — Publicado M10.1 no GitHub após commit e fast-forward normais em origin/main; nenhum código adicional foi alterado nesta sessão.
  - mudanças: Commit 9c598ba reuniu o endurecimento M10.1, schemas finais, testes, documentação pública e artefatos de handoff já validados.
  - decisões: A publicação usou push normal de main, sem force-push, rebase, reset ou alteração de histórico remoto.
  - validações: git fetch --prune origin confirmou HEAD e origin/main alinhados antes do commit (0 e 0); git diff --check aprovado; git push origin main publicou 35c1fa6..9c598ba.
  - riscos: M11--M13 continuam pendentes; não houve execução de artigo, Prime Agent, modelo, API paga ou instalação.
  - próximos: Nenhum passo pendente para M10.1; iniciar M11 somente sob autorização específica e com nova árvore limpa.

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
| M11 | comandos e configuração do Prime Agent | pendente |
| M12 | orçamento, observabilidade e execução prolongada | pendente |
| M13 | testes de sistema e entrega | pendente |

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
- `.prime/agent/skills/article-loop/src/article_loop/diagnosis.py` — série histórica validada, 7 classificações e publicação M9. API/símbolos: class DiagnosisError; class CycleRecord; load_history_series(); classify_cycle_progress(); verify_published_diagnosis(); diagnose_cycle()
- `.prime/agent/skills/article-loop/src/article_loop/evaluation.py` — comparação A/B cega, júri, meta-review e publicação M8. API/símbolos: class EvaluationError; load_rubric(); sanitize_text(); class BlindComparisonBundle [presentation_for_order, create]; class FakeJurorAdapter [evaluate]; class FakeMetaReviewerAdapter [review]; check_inversion_consistency(); evaluate_candidate()
- `.prime/agent/skills/article-loop/src/article_loop/finalization.py` — finalizador M10 com lock, journal, fsync, CAS e receipt imutável. API/símbolos: class FinalizationError; class TransactionalFinalizer [finalize]; finalize_decision()
- `.prime/agent/skills/article-loop/src/article_loop/gates.py` — 13 verificadores locais, evidência matemática e GateReport canônico. API/símbolos: record_math_verification(); verify_gate_report(); run_gates(); compare()
- `.prime/agent/skills/article-loop/src/article_loop/ingestion.py` — congelamento de PDF/ZIP, derivados e publicação do baseline v0000. API/símbolos: class IngestionError; class SourceReadyError; ingest()
- `.prime/agent/skills/article-loop/src/article_loop/orchestrator.py` — árvore M00→Sxx→Wxx reentrante, journal e receipts M6. API/símbolos: class OrchestrationError; class Orchestrator [bootstrap, preflight, run_cycle, advance_department, receipt, mark_failed, cancel, consolidate_department, pause, resume, stop, finalize, checkpoint, status]
- `.prime/agent/skills/article-loop/src/article_loop/policy.py` — política M10 fechada, Decision content-addressed, Pareto e checkpoints técnicos. API/símbolos: class PolicyError; load_policy(); verify_finalization_evidence(); pareto_relation(); choose_action(); validate_decision_disposition(); decide(); load_published_decision()
- `.prime/agent/skills/article-loop/src/article_loop/prompts.py` — registro content-addressed, overlays, composição e validação de prompts. API/símbolos: class PromptIntegrityError; class PromptContractError; class CompiledPrompt; class PromptRegistry [immutable, overlay]; expected_prompt_version(); validate_output(); compile_prompt(); compile_manager_prompt()
- `.prime/agent/skills/article-loop/src/article_loop/refocus.py` — planos/overlays reversíveis sob CAS para plateau/oscilação. API/símbolos: class RefocusError; register_overlay_cas(); generate_refocus_plan()
- `.prime/agent/skills/article-loop/src/article_loop/state_machine.py` — grafo fechado dos 16 estados e validação de transições. API/símbolos: class State; class TransitionError; is_valid_transition(); require_transition()
- `.prime/agent/skills/article-loop/src/article_loop/store.py` — event log JSONL encadeado, snapshots derivados, locks e replay. API/símbolos: class StoreError; class IntegrityError; class StopRequested; class DurableStore [read_events, rebuild_snapshot, snapshot, create_run, record, pause, resume, checkpoint]
- `.prime/agent/skills/article-loop/src/article_loop/synthesis.py` — congelamento de propostas, merge isolado e challenger write-once. API/símbolos: class SynthesisError; tree_hash(); class M7Pipeline [synthesize, freeze_synthesis, build, record_synthesis, record_candidate, record_gates, execute_and_record_gates]

### Entradas CLI

- `bin/bootstrap-deps.sh` — Prepara requisitos locais da ingestão M3. Não instala nem inicia o Prime Agent.
- `bin/check.sh` — Reserved for M11. Intentionally non-executable and operationally inert in M1.
- `bin/preflight.sh` — script shell
- `bin/start-prime.sh` — Reserved for M11. Intentionally non-executable and operationally inert in M1.
- `scripts/01_external_evaluator.py` — API: main()
- `scripts/02_stagnation_detector.py` — API: main()
- `scripts/03_refocus_generator.py` — API: main()
- `scripts/04_compensation_policy.py` — API: main()
- `scripts/05_transactional_finalizer.py` — API: main()
- `scripts/ai_context.py` — API: render_context(), parser(), main()
- `scripts/ai_handoff_common.py` — API: HandoffError, canonical_json(), sha256_bytes(), sha256_file(), is_sensitive_path(), run_local(), git_root(), list_relevant_paths(), summarize_text(), file_record(), build_inventory(), inventory_fingerprint(), snapshot_files(), inventory_delta()
- `scripts/ai_history.py` — API: load_entries(), infer_milestone(), render_history(), update_history(), parser(), main()

## Contratos JSON Schema

| Schema | Título | Obrigatórios | Propriedades |
|---|---|---:|---|
| `agent-proposal.schema.json` | AgentProposal | 14 | schema_version, proposal_id, role_id, cycle_id, base_hash, scope, evidence_locators, patch_or_operations, affected_claims, dependencies, risk, confidence, requested_validations, prompt_version |
| `agent-task.schema.json` | AgentTask | 13 | schema_version, task_id, run_id, cycle_id, role_id, activation_mode, created_at, base_hash, scope, input_locators, requested_output_schema, prompt_version, constraints |
| `candidate-manifest.schema.json` | CandidateManifest | 12 | schema_version, candidate_id, candidate_kind, run_id, cycle_id, base_candidate_id, built_at, workspace_hash, content_hash, source_proposal_ids, merge_receipt_locator, immutable, inventory, merge_receipt, base_hash, synthesis_hash, proposal… |
| `decision.schema.json` | Decision | 20 | schema_version, decision_id, run_id, cycle_id, candidate_id, candidate_content_hash, decided_at, action, gate_report_id, verdict_ids, diagnosis_id, basis_locators, reason_code, inconclusive_evaluation_id, final_gate_report_ids, content_mod… |
| `department-packet.schema.json` | DepartmentPacket | 13 | schema_version, packet_id, run_id, cycle_id, department_id, base_hash, proposal_ids, specialist_task_ids, dependency_reviews, status, no_change_justification, evidence_locators, created_at |
| `diagnosis-manifest.schema.json` | DiagnosisManifest | 11 | schema_version, diagnosis_id, run_id, cycle_id, candidate_id, classification, diagnosis_hash, gate_report_hash, evaluation_report_hash, tree_content_hash, created_at |
| `diagnosis.schema.json` | Diagnosis | 20 | schema_version, diagnosis_id, run_id, cycle_id, candidate_id, candidate_content_hash, base_hash, created_at, gate_report_id, gate_report_hash, evaluation_report_hash, history_hash, verdict_ids, window_size, mde, classification, signals, re… |
| `evaluation-manifest.schema.json` | EvaluationManifest | 17 | schema_version, evaluation_id, comparison_id, run_id, cycle_id, candidate_id, gate_report_locator, gate_report_hash, base_hash, candidate_content_hash, rubric_version, diversity_assurance, verdict_hashes, meta_verdict_hash, evaluation_repo… |
| `evaluation-report.schema.json` | EvaluationReport | 26 | schema_version, evaluation_id, run_id, cycle_id, comparison_id, candidate_id, base_hash, candidate_content_hash, gate_report_id, gate_report_locator, order_seed, diversity_assurance, total_jurors, consistent_jurors, divergent_jurors, chall… |
| `event.schema.json` | Event | 15 | schema_version, event_id, idempotency_key, run_id, cycle_id, sequence, occurred_at, event_type, state_from, state_to, actor_id, payload, artifact_hashes, previous_event_hash, event_hash |
| `final-gate-report.schema.json` | FinalGateReport | 13 | schema_version, report_id, run_id, cycle_id, candidate_id, candidate_content_hash, gate_report_id, role_id, gate_id, overall_pass, candidate_manifest, rendered_pdf, final_report |
| `final-report.schema.json` | FinalReport | 11 | schema_version, final_report_id, run_id, cycle_id, candidate_id, candidate_content_hash, gate_report_id, required_roles, candidate_manifest_hash, rendered_pdf_hash, overall_pass |
| `finalization-receipt.schema.json` | FinalizationReceipt | 16 | schema_version, receipt_id, run_id, cycle_id, decision_id, candidate_id, action, applied_at, state_before, state_after, content_hash_before, content_hash_after, hash_revalidated, atomic, content_modified, destination |
| `gate-report.schema.json` | GateReport | 13 | schema_version, report_id, report_hash, report_locator, run_id, cycle_id, candidate_id, candidate_content_hash, candidate_hash, generated_at, overall_pass, correctness_math_pass, gates |
| `jury-verdict.schema.json` | JuryVerdict | 15 | schema_version, verdict_id, comparison_id, juror_id, candidate_neutral_ids, content_hashes, presentation_order, order_seed, rubric_version, dimension_scores, outcome, winner_neutral_id, correctness_math_pass, evidence_locators, submitted_at |
| `math-evidence.schema.json` | math-evidence.schema.json | 12 | schema_version, run_id, cycle_id, base_hash, candidate_id, candidate_content_hash, claim_id, proposal_id, request_receipt_sha256, method, conclusion, summary |
| `math-issue.schema.json` | math-issue.schema.json | 11 | record_id, issue_type, run_id, cycle_id, base_hash, candidate_id, claim_id, severity, status, summary, evidence_locators |
| `math-verification.schema.json` | math-verification.schema.json | 19 | schema_version, verification_id, verification_hash, verification_locator, run_id, cycle_id, base_hash, candidate_id, candidate_content_hash, claim_id, proposal_id, request_receipt_locator, request_receipt_sha256, evidence_locator, evidence… |
| `meta-verdict.schema.json` | MetaVerdict | 13 | schema_version, meta_verdict_id, meta_reviewer_id, comparison_id, gate_report_id, confirmed, vetoed, veto_reason, consistent_verdict_count, divergence_count, explanation, evidence_locators, reviewed_at |
| `refocus-plan.schema.json` | RefocusPlan | 11 | schema_version, plan_id, run_id, cycle_id, diagnosis_id, diagnosis_hash, classification, strategy, branches, created_at, evidence_locators |
| `run-manifest.schema.json` | RunManifest | 9 | schema_version, run_id, created_at, state, cycle_id, input, config_hash, budget_config_hash, role_ids, current_candidate_id |
| `snapshot.schema.json` | Snapshot | 12 | schema_version, snapshot_id, run_id, cycle_id, event_sequence, created_at, state, last_event_id, last_event_hash, data, data_hash, snapshot_hash |

## Cobertura estrutural de testes

Total detectado por AST: **331 testes**.

| Arquivo | Testes | Amostra de fronteiras cobertas |
|---|---:|---|
| `test_ai_handoff.py` | 8 | embedded previews are bounded and have no trailing whitespace; tracked generated context is portable and idempotent; repository trigger surfaces preserve start and end protocol; context points to ai sources without embedding human docs or … |
| `test_contracts.py` | 52 | all yaml is parseable; canonical states and actions; eight evaluation dimensions; exact ids without duplicates; one plus five plus fifteen; parent child topology; exact schema catalog and meta validation; agent proposal required fields and… |
| `test_m10_policy_finalization.py` | 24 | all policy rows and actions are closed; hard math gate and extra judgment limit have precedence; global plateau can finalize only with final gate evidence; pareto dominated candidate is rejected by the closed table; budget limit is safe at… |
| `test_m2_durable_state.py` | 30 | all valid transitions; all invalid transitions; full event log replay and snapshot reconstruction; duplicate event id and idempotency conflict; partially written file and truncated jsonl are rejected; corrupted jsonl is rejected; crash bef… |
| `test_m3_ingestion.py` | 22 | digital pdf creates traceable champion and is idempotent; corrupted multiple and ambiguous pdf are rejected; scanned without ocr fails with actionable issue; malicious zip hash divergence and publish failure are safe; valid source zip is p… |
| `test_m4_prompts.py` | 13 | all 21 compiled prompts match snapshots; prompt contract sections and required dependencies; structured output fixtures validate; immutable overwrite and unknown version block execution; invalid overlay and unknown rollback block execution… |
| `test_m5_blackboard_activation.py` | 17 | claim is stable and all six ledgers are append only; localized and indirect dependency impact; structured changes preserve section equation reference and close dependencies; paths partial lines and concurrent writers are safe; run and ledg… |
| `test_m6_orchestration.py` | 43 | sparse tree is reentrant; department admits only planned specialist; duplicate and bad hash receipts; out of order specialist receipts are durable; grandchild cannot message root; silent failed and restart are durable; consolidates only de… |
| `test_m7_synthesis_gates.py` | 21 | real m6 receipts drive all m7 transitions and gates; receipt path hash and permission tampering fail closed; writable published root is rejected; semantically equivalent receipt with different bytes is rejected; missing or swapped worker r… |
| `test_m8_evaluation.py` | 51 | sanitize text strips authors versions and roles; blind bundle reproducibility and bijective order; blind bundle sanitizes filenames and metadata; evaluation uses challenger bound champion not v0000; evaluation rejects invalid order seed an… |
| `test_m9_diagnosis.py` | 50 | diagnosis transitions evaluated to diagnosed; diagnosis never reaches decided state; diagnosis rejects symlinked publication parent without writes; diagnosis fails closed if not evaluated state; classification evolving; classification regr… |

## Autoridade e separação de audiências

- `AGENTS.md` é a política autoritativa para IAs (SHA-256 `0c65e46ff94b530a`); leia o arquivo diretamente e integralmente.
- `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md` e `.prime/agent/APPEND_SYSTEM.md` são adaptadores de descoberta e não substituem `AGENTS.md`.
- `README.md`, `CONTRIBUTING.md` e `SECURITY.md` são superfícies humanas/públicas do GitHub e não são incorporadas neste contexto.

## Handoff técnico mais recente

Fonte: `.prime/handoffs/10_para_11.md`.

<latest_handoff>
# Handoff canônico M10 → M11

## Limite alcançado

M10 foi concluído exclusivamente com lógica local e determinística. Ele
implementa `DIAGNOSED -> DECIDED -> COMMITTING` e, conforme a ação, encerra em
`CYCLE_COMPLETE`, `PAUSED`, `FINALIZED` ou `TECHNICAL_FAILURE`. Não iniciou M11
e não executou o artigo real, Prime Agent, modelos ou rede.

## Política de decisão

`article_loop.policy` consome somente a evidência M7--M9 revalidada: árvore e
manifest do challenger, GateReport, avaliação cega, diagnóstico e event log.
`config/decision-policy.yaml` fixa em bytes versionados a precedência de falha
técnica, gate matemático duro, diagnóstico, julgamento inconclusivo e candidato
avaliado. Configuração, hash, estado ou identidade divergentes falham fechados;
nenhuma condição desconhecida pode promover um candidato.

`decide()` publica em
`state/decisions/<run_id>/c<cycle>/decision.json` uma `Decision` canônica,
imutável e content-addressed, vinculada ao hash da configuração. Em seguida
registra exatamente o evento `DECIDED`. Retentativa no mesmo estado retorna os
mesmos bytes sem evento duplicado. A política não escreve em `versions/`.

Antes de `ARCHIVE_PARETO`, a política compara o vetor das oito dimensões com
cada referência Pareto vigente sob `correctness_math=true`. A `Decision`
registra a relação explícita `dominated_by`/`dominates`; um candidato dominado
segue para `REJECT` com motivo fechado, sem apagar a referência histórica. Para
`ABORT_TECHNICAL`, ela também registra contador, limite e checkpoint de retry
manual; não existe retry automático ou sleep oculto.

## Finalizador transacional

`TransactionalFinalizer` é o único escritor de disposições. Ele toma lock por
execução, revalida novamente candidate, GateReport, avaliação, diagnóstico e
Decision, e persiste as fases `PREPARED`, `HASHES_REVALIDATED`,
`DESTINATION_STAGED`/`POINTER_SWAPPED`, `EVENT_COMMITTED`, `CHECKPOINTED` e
`COMPLETE` em `transaction.json`.

- `PROMOTE` copia somente os bytes de conteúdo já avaliados para a próxima
  versão histórica de champion, com manifest novo e pointer CAS em
  `versions/champion/current.json`.
- `ARCHIVE_PARETO` e `REJECT` preservam referência imutável à identidade do
  challenger; não removem seu diretório. O finalizador recalcula a relação
  Pareto sob lock e para se a fronteira mudou após a `Decision`.
- `REFOCUS_AND_CONTINUE`, `CONTINUE_UNCHANGED` e `REQUEST_EXTRA_JUDGMENT`
  publicam somente preparação/solicitação local, sem iniciar agentes.
- `PAUSE`, `ABORT_TECHNICAL` e `FINALIZE` permanecem conservadores;
  `ABORT_TECHNICAL` publica checkpoint imutável limitado e `FINALIZE` exige
  reports finais locais aprovados contendo W22, W51 e W53.

O receipt final é imutável e validado contra
`finalization-receipt.schema.json`; afirma `hash_revalidated=true`,
`atomic=true` e `content_modified=false`. Crash durante rename ou depois do
pointer é retomado pelo mesmo destino determinístico, sem segundo champion ou
remoção de histórico.

## Contratos e superfícies

- Adicionados: `article_loop.policy`, `article_loop.finalization`,
  `config/decision-policy.yaml`, `control/test_m10_policy_finalization.py`.
- Ativadas as CLIs JSON-in/JSON-out `scripts/04_compensation_policy.py` e
  `scripts/05_transactional_finalizer.py`.
- `Decision` agora exige `policy_config_hash`, `pareto_relation` e
  `technical_checkpoint`; `PAUSE` aceita o motivo fechado
  `INCONCLUSIVE_LIMIT_REACHED` após o único pedido de julgamento permitido.
- A máquina de estados permite explicitamente `COMMITTING -> FINALIZED` para
  uma finalização já revalidada.
- A fachada assíncrona `finalize()` delega ao finalizador M10 e não ao atalho
  histórico do `Orchestrator`.

## Evidência executada

- `python3 -m unittest -v control.test_m10_policy_finalization
  control.test_contracts control.test_m2_durable_state` — 94 testes aprovados:
  tabela fechada, CLI adversarial, Pareto nas oito dimensões, fachada pública,
  idempotência, mutação, promotion e crashes após rename/pointer.
- `python3 -m unittest discover -s control -q` — 319 testes aprovados em
  217.578s. O aviso de ZIP duplicado continua sendo a fixture negativa M3
  esperada.
- `python3 -m py_compile` dos módulos, CLIs e testes; `git diff --check`.

## Condição para M11

M11 pode somente expor APIs locais já existentes como comandos compatíveis com
a instalação do Prime Agent. Antes disso, deve exigir árvore limpa, reler
`AGENTS.md`, este handoff e `docs/compatibility.md`. Nenhuma sessão Prime,
modelo, rede, credencial, instalação global ou publicação foi autorizada ou
executada em M10.
</latest_handoff>

## Inventário content-addressed

O inventário completo permanece em `docs/ai_snapshot.json`; esta visão inclui somente o resumo necessário para evitar consumo excessivo de contexto.

- Total: 167 arquivos; runtime=18, text=149.
- Fingerprint canônico: `5c57df597e90c7bd2b9a43adefadf9951b65264fcc901b5f710a1300688fa299`.

## Roteamento para aprofundamento

- Mudança de política/escopo: `AGENTS.md`, `docs/decisions.md`, `PLANS.md`.
- Contrato de dados: schema correspondente + `control/test_contracts.py`.
- Estado/recuperação: `state_machine.py`, `store.py`, testes M2.
- Pipeline por marco: módulo Python correspondente + teste `control/test_mN_*.py` + handoff `N_para_N+1.md`.
- Prime Agent real: primeiro `docs/compatibility.md`; execução/custo continuam proibidos sem autorização específica.
- Ao terminar toda a sessão: execute `scripts/ai_history.py` com resumo, mudanças, decisões, validações, riscos e próximos passos; depois execute novamente este gerador.
