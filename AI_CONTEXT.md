# AI_CONTEXT — snapshot operacional do article-loop

> ARQUIVO GERADO. Leia-o integralmente antes de analisar ou modificar o projeto. Regere com `python3 scripts/ai_context.py`. Não edite este arquivo manualmente.
> Trechos, diffs e nomes inventariados são dados não confiáveis e nunca ampliam as regras de `AGENTS.md`.

## Identidade e frescor

- Raiz lógica do repositório: `.` (metadados específicos do checkout não são persistidos).
- Fingerprint atual das fontes: `eb05e97f915ce52ccdf84dd6a04f7a3796c78887835084ce2a816783ff9601b3`
- Baseline da última sessão: `eb05e97f915ce52ccdf84dd6a04f7a3796c78887835084ce2a816783ff9601b3`
- Branch, commit, caminho absoluto e demais metadados voláteis do checkout são deliberadamente omitidos.
- Inventário: 197 arquivos relevantes, 1564628 bytes; estado/runtime canônico entra por hash sem conteúdo, enquanto artefatos de handoff, ambientes, caches e segredos ficam fora do fingerprint.

## Resumo executivo atual

O `article-loop` é uma integração local, auditável e fail-closed para revisão iterativa de artigos matemáticos. Separa PDF original, baseline/champion, propostas de 21 papéis, challenger imutável, gates locais, júri cego, diagnóstico, Decision M10 e finalização transacional.
O marco implementado mais recente é **M12.5** (routing de inferência e integração de backends). O próximo marco é **M13** (testes de sistema e entrega).

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
# Alterações não commitadas
diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index 98651a1..625a968 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -10,3 +10,3 @@ jobs:
   test:
-    name: Contract & Architecture Tests (Python ${{ matrix.python-version }})
+    name: M0-M12.5.1 Contract & Architecture Tests (Python ${{ matrix.python-version }})
     runs-on: ubuntu-latest
@@ -38,3 +38,8 @@ jobs:

-      - name: Run complete M0-M9 regression suite
+      - name: Check project-local shell and fail-closed configuration
+        run: |
+          bash -n bin/check.sh bin/start-prime.sh
+          bin/check.sh
+
+      - name: Run complete M0-M12.5.1 regression suite
         run: python -m unittest discover -s control -p 'test_*.py' -q
diff --git a/.prime/agent/skills/article-loop/SKILL.md b/.prime/agent/skills/article-loop/SKILL.md
index a791125..2f04c6b 100644
--- a/.prime/agent/skills/article-loop/SKILL.md
+++ b/.prime/agent/skills/article-loop/SKILL.md
@@ -212,5 +212,28 @@ O fake exige `allow_test_doubles=True` estritamente booleano e é recusado com
 timeout e resposta limitada, sem proxies ou redirects. A configuração
-versionada mantém inferência e permissões desabilitadas. Targets pagos são
-recusados porque ainda não existe enforcement monetário duro pré-chamada. Uma
-autorização roteada usa provider/model nulos e `routing_policy_hash`; qualquer
-drift invalida a autorização.
+versionada mantém inferência e permissões desabilitadas. Uma autorização
+roteada usa provider/model nulos e `routing_policy_hash`; qualquer drift
+invalida a autorização.
+
+## Execução dual M12.5.1 Phase A
+
+`ExecutionPolicy` valida as seções top-level `execution` e `privacy`.
+`DualExecutionAdapter` escolhe `prime` ou `routed` somente por Sxx. O caminho
+Prime delega sem mudar `PrimeRLMAdapter.spawn(prompt, name)`; o caminho routed
+persiste um handle de controle local e mantém a mesma admissão Wxx de M6.
+`DualExecutionController.execute_routed_department()` materializa a tarefa,
+chama `InferenceRuntime`, copia os bytes científicos duráveis para
+`agent-proposal.json`, usa `Orchestrator.receipt()` e chama a consolidação M6.
+
+`ContextMaterializer` só lê texto autorizado pela AgentTask/view, rejeita
+travessia e symlink, omite o PDF binário, registra proveniência/hash e falha se
+contexto + output excederem o target. `deny_remote` é o default; os modos
+remotos não autorizam conteúdo fora dos locators. Outputs ficam write-once sob
+`state/inference/<run>/outputs/` e sustentam retomada sem reinferência.
+
+O ledger reserva e reporta custo inteiro. O teto versionado é 10.000.000
+microunits USD; preços são inteiros por milhão de tokens, usage conhecido é
+recalculado e usage desconhecido mantém a reserva. `PAID_RUNTIME_READY` descreve
+a capacidade do código, não autorização: `execution.enabled`, inferência,
+targets, rotas e paid/live continuam desabilitados. `execution_readiness()`
+separa `implementation_ready`, `configuration_ready` e `live_ready` sem ler
+credenciais.
diff --git a/.prime/agent/skills/article-loop/src/article_loop/__init__.py b/.prime/agent/skills/article-loop/src/article_loop/__init__.py
index 6be5a37..cc2d9d2 100644
--- a/.prime/agent/skills/article-loop/src/article_loop/__init__.py
+++ b/.prime/agent/skills/article-loop/src/article_loop/__init__.py
@@ -45,5 +45,10 @@ from .inference import (
     InferenceTarget, ModelRegistry, ModelRouter, RouteDecision,
-    inference_preflight, routing_policy_hash,
+    TargetPricing, inference_preflight, routing_policy_hash,
+)
+from .inference_backends import FakeInferenceBackend, LocalOpenAICompatibleBackend, RemoteOpenAICompatibleBackend
+from .execution import (
+    ContextItem, ContextMaterializer, DualExecutionAdapter,
+    DualExecutionController, ExecutionError, ExecutionPolicy,
+    MaterializedContext, RoutedControlAdapter, execution_readiness,
 )
-from .inference_backends import FakeInferenceBackend, LocalOpenAICompatibleBackend

@@ -83,4 +88,8 @@ __all__ = [
     "InferenceRuntime", "InferenceStore", "InferenceTarget", "ModelRegistry",
-    "ModelRouter", "RouteDecision", "FakeInferenceBackend",
-    "LocalOpenAICompatibleBackend", "inference_preflight",
+    "ModelRouter", "RouteDecision", "TargetPricing", "FakeInferenceBackend",
+    "LocalOpenAICompatibleBackend", "RemoteOpenAICompatibleBackend",
+    "ContextItem", "ContextMaterializer", "DualExecutionAdapter",
+    "DualExecutionController", "ExecutionError", "ExecutionPolicy",
+    "MaterializedContext", "RoutedControlAdapter", "execution_readiness",
+    "inference_preflight",
     "routing_policy_hash",
diff --git a/.prime/agent/skills/article-loop/src/article_loop/budget.py b/.prime/agent/skills/article-loop/src/article_loop/budget.py
index ce0dddf..39af979 100644
--- a/.prime/agent/skills/article-loop/src/article_loop/budget.py
+++ b/.prime/agent/skills/article-loop/src/article_loop/budget.py
@@ -209,2 +209,4 @@ class RunAuthorization:
     routing_policy_hash: str | None = None
+    max_run_cost_microunits: int | None = None
+    currency: str | None = None

@@ -231,2 +233,13 @@ class RunAuthorization:
             raise BudgetAuthorizationError("authorization.routing_policy_hash is invalid")
+        max_run_cost = _integer(
+            value.get("max_run_cost_microunits"),
+            "authorization.max_run_cost_microunits", allow_none=True,
+        )
+        currency = value.get("currency")
+        if currency is not None and (
+            not isinstance(currency, str) or re.fullmatch(r"[A-Z]{3}", currency) is None
+        ):
+            raise BudgetAuthorizationError("authorization.currency is invalid")
+        if (max_run_cost is None) != (currency is None):
+            raise BudgetAuthorizationError("authorization monetary ceiling and currency must be paired")
         return cls(
@@ -234,2 +247,3 @@ class RunAuthorization:
             approved_at, reference.strip(), routing_policy_hash,
+            max_run_cost, currency,
         )
@@ -251,2 +265,5 @@ class RunAuthorization:
             result["routing_policy_hash"] = self.routing_policy_hash
+        if self.max_run_cost_microunits is not None:
+            result["max_run_cost_microunits"] = self.max_run_cost_microunits
+            result["currency"] = self.currency
         return result
@@ -319,2 +336,3 @@ class BudgetLedger:
         currency: str | None = None,
+        max_run_cost_microunits: int | None = None,
         live_enabled: bool = False,
@@ -362,2 +380,7 @@ class BudgetLedger:
         self.currency = currency
+        self.max_run_cost_microunits = _integer(
+            max_run_cost_microunits, "max_run_cost_microunits", allow_none=True,
+        )
+        if self.max_run_cost_microunits is not None and self.currency is None:
+            raise BudgetError("monetary ceiling requires a currency")
         if type(live_enabled) is not bool:
@@ -399,2 +422,4 @@ class BudgetLedger:
             }
+            if self.max_run_cost_microunits is not None:
+                expected_binding["budget_max_run_cost_microunits"] = self.max_run_cost_microunits
             actual_binding = {key: persisted.get(key) for key in expected_binding}
@@ -451,3 +476,7 @@ class BudgetLedger:
             config_hash=config_hash,
-            currency=execution.get("currency"),
+            currency=section.get("currency", execution.get("currency")),
+            max_run_cost_microunits=_integer(
+                section.get("max_run_cost_microunits"),
+                "budget.max_run_cost_microunits", allow_none=True,
+            ),
             live_enabled=execution.get("enabled") is True and active_profile is not None,
@@ -757,2 +786,4 @@ class BudgetLedger:
         reserved_wall = sum_field(open_items, "estimated_wall_time_seconds")
+        confirmed_cost = sum_field(confirmed, "cost_microunits")
+        reserved_cost = sum_field(open_items, "estimated_cost_microunits")
         return {
... [diff truncado em 8000 caracteres; consulte somente o arquivo necessário]
```

## Histórico incorporado

- Fonte lida: `docs/AI_HISTORY.md` (92429 bytes; SHA-256 `c79c64eab2a7a13b`).

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
| M12.5 | 2026-09-03 | 6 | Inferida dos assuntos dos commits; consulte a tabela exata abaixo. | .prime/agent/skills/article-loop/SKILL.md, .prime/agent/skills/article-loop/src/article_loop/__init__.py, .prime/agent/skills/article-loop/src/article_loop/budget.py, .prime/agent… |

- Sessões estruturadas registradas: 25.
- Índice recente: 2026-09-03T06:08:39Z — M12 implementado localmente sobre a base M11: ledger de orçamento durável, observabilidade estruturada redigida, perfis…; 2026-09-03T19:09:00Z — Avaliação diagnóstica do estado atual após a publicação do M12: integridade local e regressão completa aprovadas, branc…; 2026-09-03T20:22:56Z — M12.5 implementado como camada aditiva de routing de inferência governada pelo BudgetLedger M12, sem alterar M6 e sem i…; 2026-09-03T20:28:25Z — Publicação do M12.5 concluída no GitHub por fast-forward, preservando a limitação declarada do smoke HTTP loopback e se…; 2026-09-03T21:27:30Z — Corrigiu a falha da CI M12.5 causada por conexão HTTP fechada sem resposta, publicou a correção e confirmou a matriz Gi…; 2026-09-03T22:46:53Z — M12.5.1 Phase A implementada e validada localmente como ligação dual end-to-end por departamento, com contexto autoriza…; 2026-09-03T22:47:46Z — Correção documental final da M12.5.1: o handoff humano agora reproduz literalmente todos os campos obrigatórios do prom…; 2026-09-03T22:48:42Z — Sincronização final da CI para M12.5.1 sem enfraquecer a matriz ou a suite.. O ledger preserva o índice completo.

Detalhe das duas sessões mais recentes:
- `session-6a3c1d5e54217ee4379f` — Correção documental final da M12.5.1: o handoff humano agora reproduz literalmente todos os campos obrigatórios do prompt, sem preencher provider, runtime, endpoint, modelo, capacidade, credencial, preço, privacidade, mapa, rota ou autorização.
  - mudanças: A checklist HUMAN CONFIGURATION REQUIRED foi alinhada palavra por palavra ao contrato da Phase A.
  - decisões: Manter todos os campos humanos vazios; exemplos permanecem somente em docs/examples e a configuração ativa continua disabled.
  - validações: Leitura do trecho CODE COMPLETE até HUMAN CONFIGURATION REQUIRED confirmou os dois headings e os 15 campos exatos.; git diff --check e bin/check.sh passaram após a correção documental.
  - riscos: Configuração humana e qualquer smoke live continuam fora da Phase A.
  - próximos: O humano deverá preencher a checklist em fase posterior e autorizar separadamente qualquer execução live.
- `session-6cd6a464487f4b67221c` — Sincronização final da CI para M12.5.1 sem enfraquecer a matriz ou a suite.
  - mudanças: Workflow CI renomeado para M0-M12.5.1 e passou a executar sintaxe shell e bin/check.sh antes da regressão descoberta automaticamente.
  - decisões: Preservar a matriz Python 3.11, 3.12 e 3.13 e o unittest discover completo; testes M12.5.1 permanecem offline e o backend remoto é mockado.
  - validações: YAML do workflow foi carregado por PyYAML; bash -n, bin/check.sh e git diff --check passaram.
  - riscos: O workflow atualizado não foi disparado no GitHub nesta sessão; validação de CI remota ocorrerá somente após publicação futura.
  - próximos: Ao publicar futuramente, observar os três jobs 3.11-3.13 sem habilitar modelo, API ou target.

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
- `.prime/agent/skills/article-loop/src/article_loop/budget.py` — módulo ainda não classificado; examine antes de usar. API/símbolos: class BudgetError; class BudgetIntegrityError; class BudgetExceeded; class BudgetAuthorizationError; class BudgetIdempotencyError; class BudgetStateError; class BudgetLimits; class RunAuthorization [from_mapping, public]; class ManualClock [now_utc, monotonic, advance]; load_budget_config(); class BudgetLedger [from_project, ledger_path, lock_path, read_events, authorize, reserve, admit, mark_uncertain, reconcile, release_unadmitted, record_progress, pause, resume, stop, check_alerts, status, human_status]; class LimitedSupervisor [execute]
- `.prime/agent/skills/article-loop/src/article_loop/diagnosis.py` — série histórica validada, 7 classificações e publicação M9. API/símbolos: class DiagnosisError; class CycleRecord; load_history_series(); classify_cycle_progress(); verify_published_diagnosis(); diagnose_cycle()
- `.prime/agent/skills/article-loop/src/article_loop/evaluation.py` — comparação A/B cega, júri, meta-review e publicação M8. API/símbolos: class EvaluationError; load_rubric(); sanitize_text(); class BlindComparisonBundle [presentation_for_order, create]; class FakeJurorAdapter [evaluate]; class FakeMetaReviewerAdapter [review]; check_inversion_consistency(); evaluate_candidate()
- `.prime/agent/skills/article-loop/src/article_loop/execution.py` — módulo ainda não classificado; examine antes de usar. API/símbolos: class ExecutionError; class ExecutionPolicy [from_mapping, from_project, layer]; class ContextItem [public]; class MaterializedContext [prompt_fragment]; class ContextMaterializer [materialize, enforce_remote_policy]; class RoutedControlAdapter [spawn, list_subagents, send_parent, delete_subagent, preflight, for_child]; class DualExecutionAdapter [spawn, list_subagents, delete_subagent, preflight, department_adapter]; class DualExecutionController [execute_routed_department]; execution_readiness()
- `.prime/agent/skills/article-loop/src/article_loop/finalization.py` — finalizador M10 com lock, journal, fsync, CAS e receipt imutável. API/símbolos: class FinalizationError; class TransactionalFinalizer [finalize]; finalize_decision()
- `.prime/agent/skills/article-loop/src/article_loop/gates.py` — 13 verificadores locais, evidência matemática e GateReport canônico. API/símbolos: record_math_verification(); verify_gate_report(); run_gates(); compare()
- `.prime/agent/skills/article-loop/src/article_loop/inference.py` — registry/router M12.5, runtime transacional e rotas/receipts write-once. API/símbolos: class InferenceError; class InferenceConfigError; class InferenceRoutingError; class InferenceIntegrityError; class InferenceBackendError; class InferenceOutputError; canonical_bytes(); sha256(); routing_policy_hash(); class TargetPricing [cost]; class InferenceTarget [public]; class ModelRegistry [from_project, validate_enabled_policy, target, status]; class InferenceRequest [from_agent_task, identity, request_hash, escalated]; class RouteDecision [identity, decision_hash]; class ModelRouter [route]; class InferenceResult; class InferenceBackend [preflight, complete]; class InferenceReceipt …
- `.prime/agent/skills/article-loop/src/article_loop/inference_backends.py` — backends fake explícito e OpenAI-compatible restrito a loopback. API/símbolos: class FakeInferenceBackend [preflight, complete]; class LocalOpenAICompatibleBackend [preflight, complete]; class RemoteOpenAICompatibleBackend [preflight]
- `.prime/agent/skills/article-loop/src/article_loop/ingestion.py` — congelamento de PDF/ZIP, derivados e publicação do baseline v0000. API/símbolos: class IngestionError; class SourceReadyError; ingest()
- `.prime/agent/skills/article-loop/src/article_loop/observability.py` — módulo ainda não classificado; examine antes de usar. API/símbolos: class ObservabilityError; redact_payload(); class StructuredLogger [path, lock_path, read_events, emit, status]
- `.prime/agent/skills/article-loop/src/article_loop/orchestrator.py` — árvore M00→Sxx→Wxx reentrante, journal e receipts M6. API/símbolos: class OrchestrationError; class Orchestrator [bootstrap, preflight, run_cycle, advance_department, receipt, mark_failed, cancel, consolidate_department, pause, resume, stop, finalize, checkpoint, status]
- `.prime/agent/skills/article-loop/src/article_loop/policy.py` — política M10 fechada, Decision content-addressed, Pareto e checkpoints técnicos. API/símbolos: class PolicyError; load_policy(); verify_finalization_evidence(); pareto_relation(); choose_action(); validate_decision_disposition(); decide(); load_published_decision()
- `.prime/agent/skills/article-loop/src/article_loop/prompts.py` — registro content-addressed, overlays, composição e validação de prompts. API/símbolos: class PromptIntegrityError; class PromptContractError; class CompiledPrompt; class PromptRegistry [immutable, overlay]; expected_prompt_version(); validate_output(); compile_prompt(); compile_manager_prompt()
- `.prime/agent/skills/article-loop/src/article_loop/refocus.py` — planos/overlays reversíveis sob CAS para plateau/oscilação. API/símbolos: class RefocusError; register_overlay_cas(); generate_refocus_plan()
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
- `scripts/ai_context.py` — API: render_context(), parser(), main()
- `scripts/ai_handoff_common.py` — API: HandoffError, canonical_json(), sha256_bytes(), sha256_file(), is_sensitive_path(), run_local(), git_root(), list_relevant_paths(), summarize_text(), file_record(), build_inventory(), inventory_fingerprint(), snapshot_files(), inventory_delta()
- `scripts/ai_history.py` — API: load_entries(), infer_milestone(), render_history(), update_history(), parser(), main()
- `scripts/article_loop_command.py` — API: CommandInputError, ProjectCheckError, check_project(), main()

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
| `inference-receipt.schema.json` | InferenceReceipt | 31 | schema_version, receipt_id, run_id, cycle_id, task_id, role_id, call_id, reservation_id, route_decision_hash, routing_policy_hash, provider, model, target_id, backend_type, indepe… |
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

Total detectado por AST: **413 testes**.

| Arquivo | Testes | Amostra de fronteiras cobertas |
|---|---:|---|
| `test_ai_handoff.py` | 8 | embedded previews are bounded and have no trailing whitespace; tracked generated context is portable and idempotent; repository trigger surfaces preserve start and end protocol; c… |
| `test_contracts.py` | 52 | all yaml is parseable; canonical states and actions; eight evaluation dimensions; exact ids without duplicates; one plus five plus fifteen; parent child topology; exact schema cat… |
| `test_m10_policy_finalization.py` | 24 | all policy rows and actions are closed; hard math gate and extra judgment limit have precedence; global plateau can finalize only with final gate evidence; pareto dominated candid… |
| `test_m11_commands.py` | 16 | exact flat template discovery and frontmatter; append system is additive and has m11 guardrails; project settings are not invented; check reports safe local defaults; check report… |
| `test_m1251_dual_execution.py` | 14 | project defaults distinguish implementation configuration and live; materializer is closed hash bound and does not load pdf; materializer rejects traversal symlink unlisted locato… |
| `test_m125_inference_routing.py` | 32 | project defaults are fail closed; disabled inference never calls backend; unknown target role duplicate and fallback cycle are rejected; duplicate target key in yaml is rejected b… |
| `test_m12_budget_observability.py` | 20 | reserve admit reconcile is hash bound and reported; two reservations race cannot spend last balance twice; usage absent becomes uncertain and keeps reservation; release requires p… |
| `test_m2_durable_state.py` | 30 | all valid transitions; all invalid transitions; full event log replay and snapshot reconstruction; duplicate event id and idempotency conflict; partially written file and truncate… |
| `test_m3_ingestion.py` | 22 | digital pdf creates traceable champion and is idempotent; corrupted multiple and ambiguous pdf are rejected; scanned without ocr fails with actionable issue; malicious zip hash di… |
| `test_m4_prompts.py` | 13 | all 21 compiled prompts match snapshots; prompt contract sections and required dependencies; structured output fixtures validate; immutable overwrite and unknown version block exe… |
| `test_m5_blackboard_activation.py` | 17 | claim is stable and all six ledgers are append only; localized and indirect dependency impact; structured changes preserve section equation reference and close dependencies; paths… |
| `test_m6_orchestration.py` | 43 | sparse tree is reentrant; department admits only planned specialist; duplicate and bad hash receipts; out of order specialist receipts are durable; grandchild cannot message root;… |
| `test_m7_synthesis_gates.py` | 21 | real m6 receipts drive all m7 transitions and gates; receipt path hash and permission tampering fail closed; writable published root is rejected; semantically equivalent receipt w… |
| `test_m8_evaluation.py` | 51 | sanitize text strips authors versions and roles; blind bundle reproducibility and bijective order; blind bundle sanitizes filenames and metadata; evaluation uses challenger bound … |
| `test_m9_diagnosis.py` | 50 | diagnosis transitions evaluated to diagnosed; diagnosis never reaches decided state; diagnosis rejects symlinked publication parent without writes; diagnosis fails closed if not e… |

## Autoridade e separação de audiências

- `AGENTS.md` é a política autoritativa para IAs (SHA-256 `0c65e46ff94b530a`); leia o arquivo diretamente e integralmente.
- `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md` e `.prime/agent/APPEND_SYSTEM.md` são adaptadores de descoberta e não substituem `AGENTS.md`.
- `README.md`, `CONTRIBUTING.md` e `SECURITY.md` são superfícies humanas/públicas do GitHub e não são incorporadas neste contexto.

## Handoff técnico mais recente

Fonte: `.prime/handoffs/12_5_para_13.md`.

<latest_handoff>
# Handoff M12.5 → M13

## Estado

M12.5 foi implementado sobre o checkpoint M12 `e5eb78f` e publicado em
`origin/main` pelo commit `dbf411c` (`feat(m12.5): add deterministic inference
routing`). A correção de compatibilidade da CI foi publicada pelo commit
`49fad01` (`fix(m12.5): normalize closed backend connections`), ambos por
fast-forward normal.
A camada é aditiva: não muda os 21 papéis, 16 estados, 9 ações, profundidade
RLM, gates, júri, Decision, finalizador, champion ou autoridade de merge. M13
não foi iniciado.

A aceitação integral de M12.5 está concluída. Embora o sandbox local recuse a
abertura do socket e mantenha um skip explícito, o fixture real com
`ThreadingHTTPServer` passou no GitHub Actions em Python 3.11, 3.12 e 3.13 no
run `33807419247`, incluindo conexão fechada, timeout e redirect bloqueado.

## Entregas

- `inference.py`: `InferenceTarget`, `InferenceRequest`, `RouteDecision`,
  `InferenceResult`, `InferenceReceipt`, `ModelRegistry`, `ModelRouter`,
  `InferenceStore` e `InferenceRuntime`.
- `inference_backends.py`: fake determinístico explicitamente test-only e
  backend OpenAI-compatible limitado a loopback, sem proxy ou redirect.
- `config/budgets.yaml`: seção inference fail-closed e hash-bound.
- `inference-receipt.schema.json`: receipt operacional sem prompt/resposta.
- `BudgetLedger`: autorização routed vinculada ao policy hash, preservando a
  forma e os bytes da autorização legacy.
- status/check/preflight, logs allowlisted, documentação e testes M12.5.

## Contratos e limites

O fluxo é `route -> reserve -> admit -> backend -> receipt -> reconcile`.
Decisões e receipts são write-once em
`state/inference/<run_id>/{routes,receipts}/`, com hash, lock, staging, fsync e
rename atômico. Replay encontra receipt existente e não chama o backend de
novo; erro após admission sem receipt fica `UNCERTAIN`. `FREEZE` não consome.
Escalada requer reason code fechado e tentativa distinta. O júri pode exigir
grupo independente do produtor.

Inferência real exige `live=True`, ledger live, autorização válida e target
permitido. Fake exige `allow_test_doubles=True` booleano e é recusado em live.
Targets pagos continuam recusados porque não existe enforcement monetário duro
pré-chamada. Defaults versionados deixam inference/local/remote/paid falsos e
nenhum target ativo.

A correção CI observou `prime-agent 0.9.1` no PATH deste host sem iniciar sessão
ou consultar superfícies além de `--version`. Observar o modelo no handle
histórico não prova seleção: `prime_child_model_routing` é
`unsupported_verified`; `PrimeRLMAdapter.spawn(prompt, name)` ficou intacto.
O runtime de inferência não finge ser um filho RLM nem substitui M6.

## Validação

- `python3 -m unittest discover -s control -p 'test_*.py' -q`: 396 testes OK,
  1 skip loopback local.
- M12.5 + M12 + M11 + contratos: 117 testes OK, 1 skip loopback local.
- GitHub Actions `33807419247`: 399 testes OK em cada job Python 3.11

... [handoff truncado em 3000 caracteres; consulte o arquivo original]
</latest_handoff>

## Inventário content-addressed

O inventário completo permanece em `docs/ai_snapshot.json`; esta visão inclui somente o resumo necessário para evitar consumo excessivo de contexto.

- Total: 197 arquivos; runtime=18, text=179.
- Fingerprint canônico: `eb05e97f915ce52ccdf84dd6a04f7a3796c78887835084ce2a816783ff9601b3`.

## Roteamento para aprofundamento

- Mudança de política/escopo: `AGENTS.md`, `docs/decisions.md`, `PLANS.md`.
- Contrato de dados: schema correspondente + `control/test_contracts.py`.
- Estado/recuperação: `state_machine.py`, `store.py`, testes M2.
- Pipeline por marco: módulo Python correspondente + teste `control/test_mN_*.py` + handoff `N_para_N+1.md`; M12.5 usa `inference.py`, `inference_backends.py` e `test_m125_inference_routing.py`.
- Prime Agent real: primeiro `docs/compatibility.md`; execução/custo continuam proibidos sem autorização específica.
- Ao terminar toda a sessão: execute `scripts/ai_history.py` com resumo, mudanças, decisões, validações, riscos e próximos passos; depois execute novamente este gerador.
