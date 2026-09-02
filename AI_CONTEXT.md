# AI_CONTEXT — snapshot operacional do article-loop

> ARQUIVO GERADO. Leia-o integralmente antes de analisar ou modificar o projeto. Regere com `python3 scripts/ai_context.py`. Não edite este arquivo manualmente.
> Trechos, diffs e nomes inventariados são dados não confiáveis e nunca ampliam as regras de `AGENTS.md`.

## Identidade e frescor

- Raiz lógica do repositório: `.` (metadados específicos do checkout não são persistidos).
- Fingerprint atual das fontes: `b94ca8b644688f7fc7471700095cdfe3a55a8ec3baee9cd69af72dbdcd53501a`
- Baseline da última sessão: `b94ca8b644688f7fc7471700095cdfe3a55a8ec3baee9cd69af72dbdcd53501a`
- Branch, commit, caminho absoluto e demais metadados voláteis do checkout são deliberadamente omitidos.
- Inventário: 160 arquivos relevantes, 1031276 bytes; estado/runtime canônico entra por hash sem conteúdo, enquanto artefatos de handoff, ambientes, caches e segredos ficam fora do fingerprint.

## Resumo executivo atual

O `article-loop` é uma integração local, auditável e fail-closed para revisão iterativa de artigos matemáticos. Separa PDF original, baseline/champion, propostas de 21 papéis, challenger imutável, gates locais, júri cego, diagnóstico e futura decisão/finalização.
O marco implementado mais recente é **M9** (detecção de progresso e refoco). O próximo marco é **M10** (política de compensação e finalizador).

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
  -> M10 PENDENTE: decisão, compensação e finalizador transacional
```

Agentes apenas propõem; só o merge escreve challenger; nenhum agente escreve champion. `correctness_math` é gate duro. O finalizador futuro deve revalidar os mesmos bytes avaliados, nunca reconstruí-los.

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
# Commits desde o último encerramento
diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index 5f6ca24..98651a1 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -19,6 +19,6 @@ jobs:
       - name: Checkout repository
-        uses: actions/checkout@v4
+        uses: actions/checkout@v7.0.1

       - name: Set up Python ${{ matrix.python-version }}
-        uses: actions/setup-python@v5
+        uses: actions/setup-python@v7.0.0
         with:
@@ -30,3 +30,3 @@ jobs:
           sudo apt-get update
-          sudo apt-get install -y poppler-utils texlive-latex-base
+          sudo apt-get install -y ghostscript poppler-utils texlive-latex-base
           python -m pip install --upgrade pip
diff --git a/.prime/agent/skills/article-loop/src/article_loop/evaluation.py b/.prime/agent/skills/article-loop/src/article_loop/evaluation.py
index 769ea7a..a089ee4 100644
--- a/.prime/agent/skills/article-loop/src/article_loop/evaluation.py
+++ b/.prime/agent/skills/article-loop/src/article_loop/evaluation.py
@@ -842,3 +842,3 @@ def _revalidate_published_evaluation(

-    expected_comparison_id = f"cmp-{_sha(_json({
+    expected_comparison_payload = {
         'candidate_hashes': [champion_hash, challenger_hash],
@@ -846,7 +846,9 @@ def _revalidate_published_evaluation(
         'order_seed': eval_report['order_seed'],
-    }))}"
-    expected_evaluation_id = f"eval-{_sha(_json({
+    }
+    expected_comparison_id = f"cmp-{_sha(_json(expected_comparison_payload))}"
+    expected_evaluation_payload = {
         'comparison_id': expected_comparison_id,
         'candidate_id': expected_candidate_id,
-    }))[:32]}"
+    }
+    expected_evaluation_id = f"eval-{_sha(_json(expected_evaluation_payload))[:32]}"
     if (
```

## Histórico incorporado

- Fonte lida: `docs/AI_HISTORY.md` (46888 bytes; SHA-256 `8f4ae3274c143eb4`).

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

- Sessões estruturadas registradas: 10.
- Índice completo: 2026-09-01T09:19:46Z — Implementado o handoff automático e compacto para novas sessões de IA, com contexto atual content-addressed, histórico evolutivo e protocolo obrigatório de início e encerramento.; 2026-09-01T09:20:21Z — Corrigida a incorporação do histórico no contexto para não repetir a linha de cabeçalho da tabela de marcos.; 2026-09-01T09:48:32Z — Reexecutada com sucesso a regressão integral após a instalação local do pdflatex pelo usuário; o bloqueio ambiental anterior foi resolvido.; 2026-09-01T11:38:01Z — Precheck do M10 interrompido antes da implementação porque a árvore Git já continha AI_CONTEXT.md modificado; nenhum código, contrato científico, plano, ADR, estado ou versão do M10 foi alterado.; 2026-09-01T11:52:21Z — Reconciliada a implementação de contexto/histórico para IA com o commit posterior de publicação no GitHub, preservando as adições comunitárias e restaurando o comportamento perdido.; 2026-09-01T12:18:53Z — Preparada a publicação da reconciliação no GitHub e preservados os históricos local e remoto; o push não foi aplicado porque a máquina não possui credencial HTTPS, GitHub CLI ou chave SSH autorizada.; 2026-09-02T17:07:54Z — Reparada a integração local com Git/GitHub e separadas as superfícies Markdown humanas das entradas para IAs, preservando integralmente a árvore funcional e sem iniciar M10, modelos ou o pipeline científico.; 2026-09-02T17:16:51Z — Explicado como autorizar publicação no GitHub a partir do Codex local; nenhuma fonte, configuração ou contrato do projeto foi alterado.; 2026-09-02T17:23:25Z — Autenticação do GitHub validada e publicação preparada por reconciliação segura sobre o remoto atualizado, deixando main em condição fast-forward sem force-push.; 2026-09-02T17:30:21Z — Falhas da CI publicada foram diagnosticadas e corrigidas para restaurar a matriz GitHub Actions em Python 3.11, 3.12 e 3.13..

Detalhe das três sessões mais recentes:
- `session-github-publish-auth-guidance-20260902` — Explicado como autorizar publicação no GitHub a partir do Codex local; nenhuma fonte, configuração ou contrato do projeto foi alterado.
  - mudanças: Nenhuma alteração funcional ou documental foi realizada; somente o handoff diagnóstico obrigatório foi registrado.
  - decisões: Recomendada autenticação interativa do GitHub CLI via navegador, sem fornecer senha ou token ao agente.
  - validações: Inspeção local confirmou origin HTTPS, branch main um commit à frente, GitHub CLI ausente e nenhum credential.helper configurado.
  - riscos: A publicação continua indisponível até o usuário concluir pessoalmente a autenticação do GitHub nesta máquina.
  - próximos: Instalar o GitHub CLI, concluir gh auth login via navegador, executar gh auth setup-git e então autorizar explicitamente o push.
- `session-github-publish-20260902` — Autenticação do GitHub validada e publicação preparada por reconciliação segura sobre o remoto atualizado, deixando main em condição fast-forward sem force-push.
  - mudanças: Após o fetch revelar 55 commits no remoto, o commit local corrigido foi preservado em backup/pre-publish-rebase-20260902 e reaplicado sobre origin/main mantendo exatamente a mesma árvore de conteúdo.
  - decisões: Preservar integralmente o histórico remoto e recusar push divergente; publicar somente por fast-forward, sem force-push.
  - validações: gh api user confirmou a conta autenticada Walc21 sem exibir credenciais.; Após a reconciliação, origin/main...main apresentou 0 commits somente no remoto e 1 somente no local; origin/main é ancestral de main.; A árvore antes e depois da reconciliação permaneceu idêntica no hash 1040b4e2d8690c32345a0d4d61cefe8151477a2f.; Foram aprovados 60 testes direcionados, compilação dos arquivos Python versionados, git diff --check e verificação de atualidade do AI_CONTEXT.md.
  - riscos: A execução de CI do GitHub só poderá ser confirmada depois do push.
  - próximos: Executar git push origin main e verificar a igualdade entre os SHAs local e remoto e o resultado do CI.
- `session-github-ci-repair-20260902` — Falhas da CI publicada foram diagnosticadas e corrigidas para restaurar a matriz GitHub Actions em Python 3.11, 3.12 e 3.13.
  - mudanças: O workflow passou a instalar ghostscript, dependência do comando gs usado pelos testes de ingestão, síntese, avaliação e diagnóstico.; A reconstrução de IDs em evaluation.py foi refatorada para evitar expressão multilinha dentro de f-string e manter compatibilidade sintática com Python 3.11 sem alterar o conteúdo calculado.; actions/checkout e actions/setup-python foram atualizadas para as releases oficiais atuais v7.0.1 e v7.0.0, eliminando o runtime Node.js obsoleto indicado pelo GitHub.
  - decisões: Corrigir a infraestrutura e a incompatibilidade declarada pela matriz em vez de remover testes ou abandonar o Python 3.11.
  - validações: O log da CI 33660817044 mostrou FileNotFoundError para gs em Python 3.12 e 3.13 e SyntaxError na f-string de evaluation.py em Python 3.11.; A gramática Python 3.11 foi validada com ast.parse feature_version 3.11; todos os arquivos Python compilam no runtime local.; O YAML do workflow foi analisado com sucesso e git diff --check não apontou erros.; A suíte completa local aprovou 307 de 307 testes em 216.078 segundos.
  - riscos: O resultado da nova matriz remota só será conhecido após publicar o commit de correção.
  - próximos: Criar e publicar o commit de correção de CI e acompanhar a nova execução do GitHub Actions até a conclusão.

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
| M10 | política de compensação e finalizador | pendente; não iniciado |
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
- `.prime/agent/skills/article-loop/src/article_loop/gates.py` — 13 verificadores locais, evidência matemática e GateReport canônico. API/símbolos: record_math_verification(); verify_gate_report(); run_gates(); compare()
- `.prime/agent/skills/article-loop/src/article_loop/ingestion.py` — congelamento de PDF/ZIP, derivados e publicação do baseline v0000. API/símbolos: class IngestionError; class SourceReadyError; ingest()
- `.prime/agent/skills/article-loop/src/article_loop/orchestrator.py` — árvore M00→Sxx→Wxx reentrante, journal e receipts M6. API/símbolos: class OrchestrationError; class Orchestrator [bootstrap, preflight, run_cycle, advance_department, receipt, mark_failed, cancel, consolidate_department, pause, resume, stop, finalize, checkpoint, status]
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
- `scripts/04_compensation_policy.py` — módulo Python interno
- `scripts/05_transactional_finalizer.py` — módulo Python interno
- `scripts/ai_context.py` — API: render_context(), parser(), main()
- `scripts/ai_handoff_common.py` — API: HandoffError, canonical_json(), sha256_bytes(), sha256_file(), is_sensitive_path(), run_local(), git_root(), list_relevant_paths(), summarize_text(), file_record(), build_inventory(), inventory_fingerprint(), snapshot_files(), inventory_delta()
- `scripts/ai_history.py` — API: load_entries(), infer_milestone(), render_history(), update_history(), parser(), main()

## Contratos JSON Schema

| Schema | Título | Obrigatórios | Propriedades |
|---|---|---:|---|
| `agent-proposal.schema.json` | AgentProposal | 14 | schema_version, proposal_id, role_id, cycle_id, base_hash, scope, evidence_locators, patch_or_operations, affected_claims, dependencies, risk, confidence, requested_validations, prompt_version |
| `agent-task.schema.json` | AgentTask | 13 | schema_version, task_id, run_id, cycle_id, role_id, activation_mode, created_at, base_hash, scope, input_locators, requested_output_schema, prompt_version, constraints |
| `candidate-manifest.schema.json` | CandidateManifest | 12 | schema_version, candidate_id, candidate_kind, run_id, cycle_id, base_candidate_id, built_at, workspace_hash, content_hash, source_proposal_ids, merge_receipt_locator, immutable, inventory, merge_receipt, base_hash, synthesis_hash, proposal… |
| `decision.schema.json` | Decision | 17 | schema_version, decision_id, run_id, cycle_id, candidate_id, candidate_content_hash, decided_at, action, gate_report_id, verdict_ids, diagnosis_id, basis_locators, reason_code, inconclusive_evaluation_id, final_gate_report_ids, content_mod… |
| `department-packet.schema.json` | DepartmentPacket | 13 | schema_version, packet_id, run_id, cycle_id, department_id, base_hash, proposal_ids, specialist_task_ids, dependency_reviews, status, no_change_justification, evidence_locators, created_at |
| `diagnosis-manifest.schema.json` | DiagnosisManifest | 11 | schema_version, diagnosis_id, run_id, cycle_id, candidate_id, classification, diagnosis_hash, gate_report_hash, evaluation_report_hash, tree_content_hash, created_at |
| `diagnosis.schema.json` | Diagnosis | 20 | schema_version, diagnosis_id, run_id, cycle_id, candidate_id, candidate_content_hash, base_hash, created_at, gate_report_id, gate_report_hash, evaluation_report_hash, history_hash, verdict_ids, window_size, mde, classification, signals, re… |
| `evaluation-manifest.schema.json` | EvaluationManifest | 17 | schema_version, evaluation_id, comparison_id, run_id, cycle_id, candidate_id, gate_report_locator, gate_report_hash, base_hash, candidate_content_hash, rubric_version, diversity_assurance, verdict_hashes, meta_verdict_hash, evaluation_repo… |
| `evaluation-report.schema.json` | EvaluationReport | 26 | schema_version, evaluation_id, run_id, cycle_id, comparison_id, candidate_id, base_hash, candidate_content_hash, gate_report_id, gate_report_locator, order_seed, diversity_assurance, total_jurors, consistent_jurors, divergent_jurors, chall… |
| `event.schema.json` | Event | 15 | schema_version, event_id, idempotency_key, run_id, cycle_id, sequence, occurred_at, event_type, state_from, state_to, actor_id, payload, artifact_hashes, previous_event_hash, event_hash |
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

Total detectado por AST: **307 testes**.

| Arquivo | Testes | Amostra de fronteiras cobertas |
|---|---:|---|
| `test_ai_handoff.py` | 8 | embedded previews are bounded and have no trailing whitespace; tracked generated context is portable and idempotent; repository trigger surfaces preserve start and end protocol; context points to ai sources without embedding human docs or … |
| `test_contracts.py` | 52 | all yaml is parseable; canonical states and actions; eight evaluation dimensions; exact ids without duplicates; one plus five plus fifteen; parent child topology; exact schema catalog and meta validation; agent proposal required fields and… |
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

Fonte: `.prime/handoffs/09_para_10.md`.

<latest_handoff>
# Handoff: Milestone 09 (M9) -> Milestone 10 (M10)

**Data:** 2026-08-28
**Status do Marco M9:** CONCLUÍDO E APROVADO
**Próximo Marco:** M10 (Política de Compensação, Decisão Canônica e Finalizador)

---

## 1. Resumo Executivo da Entrega M9

O Milestone 09 (M9) implementou a detecção determinística de estagnação, diagnóstico canônico estruturado e geração controlada e reversível de planos de refoco e overlays de prompt. O módulo opera estritamente na transição de estados `EVALUATED -> DIAGNOSED`.

Todas as operações foram realizadas de modo puramente determinístico, offline e sem chamadas a modelos reais, garantindo a preservação absoluta de todos os artefatos históricos, candidatos, vereditos e prompts imutáveis dos marcos M0–M8.

---

## 2. Componentes Entregues

### 2.1 Módulos Puros
- `article_loop.diagnosis` (`.prime/agent/skills/article-loop/src/article_loop/diagnosis.py`):
  - `load_history_series()`: Reconstituição rigorosa da série histórica $c_0 \dots c_N$ a partir de ciclos fechados e artefatos íntegros, com isolamento anti-lookahead e rejeição fail-closed de mistura de runs ou lacunas.
  - `classify_cycle_progress()`: Motor determinístico em 7 estados; perda do hard gate matemático produz `REGRESSING` antes de qualquer conclusão de júri inconclusivo.
  - A verificação de um diagnóstico publicado recompõe `classification`, `signals`, `recommended_mode` e `focus` a partir do histórico comprometido, `window_size` e `mde`; re-hash de um resultado semanticamente forjado não é aceito.
  - Normalização de papéis em `FREEZE` via denominador extraído de `activation_map`.
  - Prevalência intransponível do hard gate matemático (`correctness_math_pass == False`).
  - `diagnose_cycle()`: Executa o diagnóstico, valida contra schema Draft 2020-12, publica transacionalmente em staging com permissões `0444`/`0555`, sincronização `fsync`, substituição atômica em `state/diagnosis/<run_id>/c<cycle:04d>/` e registra o evento `DIAGNOSED` no `DurableStore`.

- `article_loop.refocus` (`.prime/agent/skills/article-loop/src/article_loop/refocus.py`):
  - `generate_refocus_plan()`: Gera `RefocusPlan` exclusivamente para `LOCAL_PLATEAU`, `GLOBAL_PLATEAU` ou `OSCILLATING`. Recusa (`RefocusError`) execuções para `EVOLVING`, `REGRESSING`, `INCONCLUSIVE` e `TECHNICAL_FAILURE`.
  - Em `GLOBAL_PLATEAU`, gera no máximo dois ramos distintos (`exploitation` e `exploration`), com orçamentos e critérios de falsificação objetivos.
  - `register_overlay_cas()`: Cria novos arquivos YAML imutáveis em `prompts/overlays/<role_id>/<version>.yaml` e atualiza `prompts/registry.json` sob lock exclusivo de arquivo (`prompts/.registry.lock`), CAS, fsync e validação de grafo `PromptRegistry`. M00 nunca recebe overlay e os núcleos em `prompts/immutable/` nunca são modificados.

### 2.2 Utilitários CLI (JSON-in / JSON-out)
- `scripts/02_stagnation_detector.py`: Wrapper CLI fino para diagnóstico determinístico.
- `scripts/03_refocus_generator.py`: Wrapper CLI fino para geração de refoco e overlays.

### 2.3 Contratos e Schemas JSON (Draft 2020-12)
- `config/schemas/diagnosis-manifest.schema.json`: Schema do manifesto de integridade da publicação do diagnóstico.
- `config/schemas/refocus-plan.schema.json`: Schema do plano de refoco e ramificações.
- Total de schemas formais no repositório: 20 schemas validados em `control/test_contracts.py`.

---

## 3. Verificação e Testes

- **Suíte de Testes M9 (`control/test_m9_diagnosis.py`):**
  - 50 testes unitários e de integração cobrindo todas as 7 classificações, recomposição semântica contra ataques re-hashados, invariância de ordem, limiares exatos MDE, rejeição de melhorias falsas, isolamento anti-lookahead, papéis `FREEZE`, bloqueio de ampliação de privilégios de overlay, idempotência, recuperação de falhas com injeção de erros e imutabilidade byte a byte de campeão, challenger e vereditos.
  - Resultado: **50/50 aprovados** em 148.650s.

- **Suíte Integral de Contratos (`control/test_contracts.py`):**
  - 52 testes validando 20 schemas canônicos.
  - Resultado: **52/52 aprovados**.

- **Suíte Completa de Regressão (M0–M9):**
  - Execução: `python3 -m unittest discover -s control -q`
  - Resultado: **299 testes aprovados** com 100% de sucesso em 566.531s.

---

## 4. Fronteiras e Regras Estritas para o M10

1. **Estado de Entrada do M10:**
   - O M10 deve receber a execução no estado `DIAGNOSED`.
   - O M10 é o único responsável pela transição para `DECIDED` e `FINALIZED`.
2. **Imutabilidade e Preservação:**
   - O M10 não deve modificar o conteúdo dos challengers gerados no M7 nem os vereditos do M8 nem o diagnóstico do M9.
   - A promoção de challenger para campeão (`versions/champion/v<next>`) ou retenção/rollback deve ser atômica e estritamente auditada via `DurableStore`.
3. **Overlays e Prompt Registry:**
   - Se o plano de refoco gerou novos overlays e foi aprovado, o M10 pode acionar o próximo ciclo aplicando os ponteiros de overlay correspondentes ao ramo selecionado.
4. **Sem Chamadas Reais de Modelo:**
   - Manter a separação estrita de test doubles e a proibição de chamadas a provedores externos de LLM até a autorização de marcos específicos.
</latest_handoff>

## Inventário content-addressed

O inventário completo permanece em `docs/ai_snapshot.json`; esta visão inclui somente o resumo necessário para evitar consumo excessivo de contexto.

- Total: 160 arquivos; runtime=18, text=142.
- Fingerprint canônico: `b94ca8b644688f7fc7471700095cdfe3a55a8ec3baee9cd69af72dbdcd53501a`.

## Roteamento para aprofundamento

- Mudança de política/escopo: `AGENTS.md`, `docs/decisions.md`, `PLANS.md`.
- Contrato de dados: schema correspondente + `control/test_contracts.py`.
- Estado/recuperação: `state_machine.py`, `store.py`, testes M2.
- Pipeline por marco: módulo Python correspondente + teste `control/test_mN_*.py` + handoff `N_para_N+1.md`.
- Prime Agent real: primeiro `docs/compatibility.md`; execução/custo continuam proibidos sem autorização específica.
- Ao terminar toda a sessão: execute `scripts/ai_history.py` com resumo, mudanças, decisões, validações, riscos e próximos passos; depois execute novamente este gerador.
