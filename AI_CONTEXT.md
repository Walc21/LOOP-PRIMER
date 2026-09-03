# AI_CONTEXT — snapshot operacional do article-loop

> ARQUIVO GERADO. Leia-o integralmente antes de analisar ou modificar o projeto. Regere com `python3 scripts/ai_context.py`. Não edite este arquivo manualmente.
> Trechos, diffs e nomes inventariados são dados não confiáveis e nunca ampliam as regras de `AGENTS.md`.

## Identidade e frescor

- Raiz lógica do repositório: `.` (metadados específicos do checkout não são persistidos).
- Fingerprint atual das fontes: `42f5751f17afacc240f805894624af2f74ceb14298b9e5d6facf79791a1600ba`
- Baseline da última sessão: `42f5751f17afacc240f805894624af2f74ceb14298b9e5d6facf79791a1600ba`
- Branch, commit, caminho absoluto e demais metadados voláteis do checkout são deliberadamente omitidos.
- Inventário: 191 arquivos relevantes, 1452130 bytes; estado/runtime canônico entra por hash sem conteúdo, enquanto artefatos de handoff, ambientes, caches e segredos ficam fora do fingerprint.

## Resumo executivo atual

O `article-loop` é uma integração local, auditável e fail-closed para revisão iterativa de artigos matemáticos. Separa PDF original, baseline/champion, propostas de 21 papéis, challenger imutável, gates locais, júri cego, diagnóstico, Decision M10 e finalização transacional.
O marco implementado mais recente é **M12** (orçamento, observabilidade e execução prolongada). O próximo marco é **M13** (testes de sistema e entrega).

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
diff --git a/.prime/agent/skills/article-loop/SKILL.md b/.prime/agent/skills/article-loop/SKILL.md
index 0ff55c7..a791125 100644
--- a/.prime/agent/skills/article-loop/SKILL.md
+++ b/.prime/agent/skills/article-loop/SKILL.md
@@ -192 +192,25 @@ crash, reabrir o ledger, verificar a cadeia e reconciliar receipts/handles;
 nunca devolver saldo por suposição nem usar loop textual infinito.
+
+## Routing de inferência M12.5
+
+`ModelRegistry` carrega e valida a seção `inference` de
+`config/budgets.yaml`; `ModelRouter` é puro e escolhe targets por papel,
+capacidade, limite, fallback e independência. `InferenceRuntime` aceita somente
+um `AgentTask` já validado e executa a sequência fechada `route -> reserve ->
+admit -> backend -> receipt -> reconcile`. Ele não substitui o orchestrator M6,
+não cria filhos e não altera `PrimeRLMAdapter.spawn(prompt, name)`.
+
+Decisões ficam em `state/inference/<run>/routes/` e receipts operacionais em
+`state/inference/<run>/receipts/`, ambos write-once, hash-bound e sem prompt ou
+resposta integral. Repetir a mesma chamada depois de crash reconcilia o receipt
+existente sem reinferência; ausência de receipt após admissão fica `UNCERTAIN`.
+`FREEZE` não reserva nem chama backend. Escalation requer reason code fechado,
+tentativa limitada e nova decisão persistida; nunca faça retry silencioso.
+
+O fake exige `allow_test_doubles=True` estritamente booleano e é recusado com
+`live=True`. O backend OpenAI-compatible local aceita só loopback explícito,
+timeout e resposta limitada, sem proxies ou redirects. A configuração
+versionada mantém inferência e permissões desabilitadas. Targets pagos são
+recusados porque ainda não existe enforcement monetário duro pré-chamada. Uma
+autorização roteada usa provider/model nulos e `routing_policy_hash`; qualquer
+drift invalida a autorização.
diff --git a/.prime/agent/skills/article-loop/src/article_loop/__init__.py b/.prime/agent/skills/article-loop/src/article_loop/__init__.py
index 77a5e55..6be5a37 100644
--- a/.prime/agent/skills/article-loop/src/article_loop/__init__.py
+++ b/.prime/agent/skills/article-loop/src/article_loop/__init__.py
@@ -40,4 +40,12 @@ from .budget import (
 from .observability import ObservabilityError, StructuredLogger, redact_payload
+from .inference import (
+    InferenceBackend, InferenceBackendError, InferenceConfigError, InferenceError,
+    InferenceIntegrityError, InferenceOutputError, InferenceReceipt,
+    InferenceRequest, InferenceResult, InferenceRuntime, InferenceStore,
+    InferenceTarget, ModelRegistry, ModelRouter, RouteDecision,
+    inference_preflight, routing_policy_hash,
+)
+from .inference_backends import FakeInferenceBackend, LocalOpenAICompatibleBackend

-__version__ = "0.6.0"
+__version__ = "0.7.0"

@@ -71,2 +79,9 @@ __all__ = [
     "StructuredLogger", "redact_payload",
+    "InferenceBackend", "InferenceBackendError", "InferenceConfigError",
+    "InferenceError", "InferenceIntegrityError", "InferenceOutputError",
+    "InferenceReceipt", "InferenceRequest", "InferenceResult",
+    "InferenceRuntime", "InferenceStore", "InferenceTarget", "ModelRegistry",
+    "ModelRouter", "RouteDecision", "FakeInferenceBackend",
+    "LocalOpenAICompatibleBackend", "inference_preflight",
+    "routing_policy_hash",
     "check_inversion_consistency", "classify_cycle_progress", "compare",
diff --git a/.prime/agent/skills/article-loop/src/article_loop/budget.py b/.prime/agent/skills/article-loop/src/article_loop/budget.py
index bd623d0..ce0dddf 100644
--- a/.prime/agent/skills/article-loop/src/article_loop/budget.py
+++ b/.prime/agent/skills/article-loop/src/article_loop/budget.py
@@ -29,2 +29,32 @@ except ImportError:  # pragma: no cover - project environments already use PyYAM

+
+if yaml is not None:
+    class _UniqueSafeLoader(yaml.SafeLoader):
+        """Safe YAML loader which rejects duplicate mapping keys."""
+
+    def _construct_unique_mapping(loader, node, deep=False):  # noqa: ANN001, ANN202
+        loader.flatten_mapping(node)
+        mapping = {}
+        for key_node, value_node in node.value:
+            key = loader.construct_object(key_node, deep=deep)
+            try:
+                duplicate = key in mapping
+            except TypeError as error:
+                raise yaml.constructor.ConstructorError(
+                    "while constructing a mapping", node.start_mark,
+                    "found an unhashable mapping key", key_node.start_mark,
+                ) from error
+            if duplicate:
+                raise yaml.constructor.ConstructorError(
+                    "while constructing a mapping", node.start_mark,
+                    f"found duplicate key: {key!r}", key_node.start_mark,
+                )
+            mapping[key] = loader.construct_object(value_node, deep=deep)
+        return mapping
+
+    _UniqueSafeLoader.add_constructor(
+        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
+        _construct_unique_mapping,
+    )
+
 from .observability import StructuredLogger
@@ -178,2 +208,3 @@ class RunAuthorization:
     approval_reference: str
+    routing_policy_hash: str | None = None

@@ -195,6 +226,14 @@ class RunAuthorization:
             raise BudgetAuthorizationError("authorization.approval_reference is invalid")
-        return cls(run_id, profile, config_hash, provider, model, token_limit, approved_at, reference.strip())
+        routing_policy_hash = value.get("routing_policy_hash")
+        if routing_policy_hash is not None and (
+            not isinstance(routing_policy_hash, str) or _SHA.fullmatch(routing_policy_hash) is None
+        ):
+            raise BudgetAuthorizationError("authorization.routing_policy_hash is invalid")
+        return cls(
+            run_id, profile, config_hash, provider, model, token_limit,
+            approved_at, reference.strip(), routing_policy_hash,
+        )

     def public(self) -> dict[str, Any]:
-        return {
+        result = {
             "run_id": self.run_id,
@@ -208,2 +247,7 @@ class RunAuthorization:
         }
+        # Preserve the historical event bytes and fixtures for legacy
+        # single-target authorizations.
+        if self.routing_policy_hash is not None:
+            result["routing_policy_hash"] = self.routing_policy_hash
+        return result

@@ -255,3 +299,3 @@ def load_budget_config(root: str | Path) -> Mapping[str, Any]:
     try:
-        value = yaml.safe_load(path.read_text(encoding="utf-8"))
+        value = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueSafeLoader)
     except (OSError, UnicodeError, yaml.YAMLError) as error:
@@ -281,2 +325,4 @@ class BudgetLedger:
         logger: StructuredLogger | None = None,
+        inference_policy: Mapping[str, Any] | None = None,
+        routing_policy_hash: str | None = None,
     ):
@@ -301,2 +347,13 @@ class BudgetLedger:
         self.config_hash = config_hash
+        self.inference_policy = dict(inference_policy) if isinstance(inference_policy, Mapping) else None
+        computed_routing_hash = (
+            _hash(_canonical(self.inference_policy)) if self.inference_policy is not None else None
+        )
+        if routing_policy_hash is not None and (
+            not isinstance(routing_policy_hash, str) or _SHA.fullmatch(routing_policy_hash) is None
+        ):
+            raise BudgetError("routing_policy_hash is invalid")
+        if routing_policy_hash is not None and routing_policy_hash != computed_routing_hash:
+            raise BudgetIntegrityError("routing policy hash differs from configured policy")
+        self.routing_policy_hash = routing_policy_hash or computed_routing_hash
         if currency is not None:
@@ -385,2 +442,5 @@ class BudgetLedger:
         )
+        inference = config.get("inference")
+        if not isinstance(inference, Mapping):
+            raise BudgetError("inference configuration is invalid")
         return cls(
@@ -397,2 +457,4 @@ class BudgetLedger:
... [diff truncado em 8000 caracteres; consulte somente o arquivo necessário]
```

## Histórico incorporado

- Fonte lida: `docs/AI_HISTORY.md` (78561 bytes; SHA-256 `3a8aff95ad30c7fc`).

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

- Sessões estruturadas registradas: 20.
- Índice recente: 2026-09-03T04:11:47Z — Concluído o endurecimento M10.1 local: pacote final hash-bound, rederivação da Decision, recuperação pós-recibo e cober…; 2026-09-03T04:19:31Z — Publicado M10.1 no GitHub após commit e fast-forward normais em origin/main; nenhum código adicional foi alterado nesta…; 2026-09-03T05:00:04Z — Implementação local do M11 concluída: a camada operacional agora expõe as APIs existentes por uma ponte JSON-in/JSON-ou…; 2026-09-03T05:04:53Z — Commit e publicação da implementação local da M11 concluídos no repositório LOOP-PRIMER; a integração de comandos, temp…; 2026-09-03T05:18:47Z — Avaliada a prontidão para iniciar M12 após a publicação da M11; nenhum código, configuração, execução live, modelo, Pri…; 2026-09-03T06:08:39Z — M12 implementado localmente sobre a base M11: ledger de orçamento durável, observabilidade estruturada redigida, perfis…; 2026-09-03T19:09:00Z — Avaliação diagnóstica do estado atual após a publicação do M12: integridade local e regressão completa aprovadas, branc…; 2026-09-03T20:22:56Z — M12.5 implementado como camada aditiva de routing de inferência governada pelo BudgetLedger M12, sem alterar M6 e sem i…. O ledger preserva o índice completo.

Detalhe das duas sessões mais recentes:
- `session-m12-evaluation-20260903` — Avaliação diagnóstica do estado atual após a publicação do M12: integridade local e regressão completa aprovadas, branch main alinhada ao origin/main, M13 ainda pendente e execução live corretamente bloqueada.
  - mudanças: Nenhum arquivo de produto, contrato, configuração, código ou marco foi alterado; somente o registro obrigatório desta sessão diagnóstica e o contexto gerado foram atualizados.
  - decisões: Considerar o M12 tecnicamente saudável para avançar ao planejamento do M13, preservando os defaults fail-closed e sem autorizar Prime Agent, modelos, rede ou APIs pagas.
  - validações: bash bin/check.sh: status success; live_ready=false; model_execution_enabled=false; paid_apis_enabled=false; perfis calibration e overnight desabilitados; prime_agent_discovered=false.; python3 -m unittest discover -s control -q: 366 testes aprovados em 231.770s; único warning conhecido Duplicate name: a.tex no fixture adversarial de ZIP.; git rev-list --left-right --count HEAD...origin/main retornou 0 0; HEAD e origin/main apontam para e5eb78f feat(m12): add durable budget observability.
  - riscos: O handoff 12_para_13.md ainda descreve corretamente a sessão de implementação pré-commit, mas sua frase de que não houve commit/publicação está desatualizada em relação ao estado atual e pode confundir o próximo operador.; M13 possui objetivo geral, mas ainda carece de um plano detalhado e critérios sistêmicos específicos antes da implementação.
  - próximos: Se autorizado, planejar M13 em PLANS.md e docs/decisions.md, corrigir a superfície de handoff/publicação e então implementar testes sistêmicos e empacotamento sem executar o artigo real.
- `session-2dffb2bba91ea37f3f05` — M12.5 implementado como camada aditiva de routing de inferência governada pelo BudgetLedger M12, sem alterar M6 e sem iniciar M13; aceitação integral permanece aberta somente pelo smoke HTTP loopback bloqueado pelo sandbox.
  - mudanças: Adicionados registry, router, request/result/receipt, store write-once e runtime transacional em inference.py.; Adicionados fake determinístico e backend local OpenAI-compatible limitado a loopback em inference_backends.py, além do schema de receipt.; Estendidos autorização routed hash-bound, status, preflight/check, observabilidade, documentação, testes e handoff 12_5_para_13.
  - decisões: PrimeRLMAdapter.spawn(prompt, name) permaneceu intacto; seleção de modelo por filho foi registrada como unsupported_verified porque o Prime Agent não está instalado neste host.; Targets pagos permanecem recusados porque M12 não possui enforcement monetário duro pré-chamada; defaults inference/local/remote/paid permanecem falsos.; M12.5 não é executor de papel RLM: opera apenas pedidos derivados de AgentTask sem substituir handles, receipts ou hierarquia M6.
  - validações: python3 -m unittest discover -s control -q: 395 testes aprovados, 1 skip do fixture HTTP loopback.; Suítes M12.5, M12, M11 e contratos: 116 testes aprovados, 1 skip do fixture HTTP loopback.; py_compile dos Python alterados/criados, bash -n bin/check.sh, bin/check.sh, json.tool do schema e git diff --check: aprovados.; bin/check.sh confirmou inference desabilitada, zero targets, paid_runtime_ready false, Prime não descoberto e policy hash estável.
  - riscos: O sandbox recusou socket loopback e a elevação foi negada; o critério J não foi provado e M12.5 não foi marcado como integralmente aceito.; shellcheck não está instalado; não houve instalação global.
  - próximos: Antes de M13, executar control.test_m125_inference_routing.M125LoopbackBackendTests em ambiente que permita socket local e confirmar todos os cenários HTTP.; Manter Prime, modelos, rede remota e targets pagos desabilitados até nova autorização específica.

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
| M12.5 | routing de inferência e integração de backends | implementado; aceitação loopback bloqueada pelo sandbox |
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
- `.prime/agent/skills/article-loop/src/article_loop/finalization.py` — finalizador M10 com lock, journal, fsync, CAS e receipt imutável. API/símbolos: class FinalizationError; class TransactionalFinalizer [finalize]; finalize_decision()
- `.prime/agent/skills/article-loop/src/article_loop/gates.py` — 13 verificadores locais, evidência matemática e GateReport canônico. API/símbolos: record_math_verification(); verify_gate_report(); run_gates(); compare()
- `.prime/agent/skills/article-loop/src/article_loop/inference.py` — registry/router M12.5, runtime transacional e rotas/receipts write-once. API/símbolos: class InferenceError; class InferenceConfigError; class InferenceRoutingError; class InferenceIntegrityError; class InferenceBackendError; class InferenceOutputError; canonical_bytes(); sha256(); routing_policy_hash(); class InferenceTarget [public]; class ModelRegistry [from_project, validate_enabled_policy, target, status]; class InferenceRequest [from_agent_task, identity, request_hash, escalated]; class RouteDecision [identity, decision_hash]; class ModelRouter [route]; class InferenceResult; class InferenceBackend [preflight, complete]; class InferenceReceipt [public]; class InferenceSto…
- `.prime/agent/skills/article-loop/src/article_loop/inference_backends.py` — backends fake explícito e OpenAI-compatible restrito a loopback. API/símbolos: class FakeInferenceBackend [preflight, complete]; class LocalOpenAICompatibleBackend [preflight, complete]
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
- `bin/check.sh` — Fast, local M11/M12/M12.5 integrity check. It never starts Prime Agent or a model.
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

Total detectado por AST: **398 testes**.

| Arquivo | Testes | Amostra de fronteiras cobertas |
|---|---:|---|
| `test_ai_handoff.py` | 8 | embedded previews are bounded and have no trailing whitespace; tracked generated context is portable and idempotent; repository trigger surfaces preserve start and end protocol; c… |
| `test_contracts.py` | 52 | all yaml is parseable; canonical states and actions; eight evaluation dimensions; exact ids without duplicates; one plus five plus fifteen; parent child topology; exact schema cat… |
| `test_m10_policy_finalization.py` | 24 | all policy rows and actions are closed; hard math gate and extra judgment limit have precedence; global plateau can finalize only with final gate evidence; pareto dominated candid… |
| `test_m11_commands.py` | 15 | exact flat template discovery and frontmatter; append system is additive and has m11 guardrails; project settings are not invented; check reports safe local defaults; require live… |
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

M12.5 foi implementado sobre o checkpoint M12 `e5eb78f`, sem commit ou push.
A camada é aditiva: não muda os 21 papéis, 16 estados, 9 ações, profundidade
RLM, gates, júri, Decision, finalizador, champion ou autoridade de merge. M13
não foi iniciado.

A aceitação integral de M12.5 continua aberta somente no critério J. O teste
com `ThreadingHTTPServer` foi implementado, mas este sandbox recusou a abertura
de socket loopback; uma tentativa de executar fora do sandbox foi negada. O
teste fica como skip explícito, sem alegar smoke real.

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

A auditoria não encontrou binário ou pacote Prime Agent neste host. Observar o
modelo no handle histórico não prova seleção: `prime_child_model_routing` é
`unsupported_verified`; `PrimeRLMAdapter.spawn(prompt, name)` ficou intacto.
O runtime de inferência não finge ser um filho RLM nem substitui M6.

## Validação

- `python3 -m unittest discover -s control -q`: 395 testes OK, 1 skip loopback.
- M12.5 + M12 + M11 + contratos: 116 testes OK, 1 skip loopback.
- `python3 -m py_compile ...`: OK.
- `bash -n bin/check.sh`: OK.
- `bin/check.sh`: OK; inference desabilitada, zero targets, paid false.
- `git diff --check`: OK.
- `shellcheck`: ausente; não instalado.

## Próximo passo permitido

Antes de iniciar M13, executar somente o fixture loopback em ambiente que
autorize socket local e confirmar sucesso, erro HTTP, malformed, resposta
grande, conexão fechada, timeout, redirect bloqueado e usage ausente. Não

... [handoff truncado em 3000 caracteres; consulte o arquivo original]
</latest_handoff>

## Inventário content-addressed

O inventário completo permanece em `docs/ai_snapshot.json`; esta visão inclui somente o resumo necessário para evitar consumo excessivo de contexto.

- Total: 191 arquivos; runtime=18, text=173.
- Fingerprint canônico: `42f5751f17afacc240f805894624af2f74ceb14298b9e5d6facf79791a1600ba`.

## Roteamento para aprofundamento

- Mudança de política/escopo: `AGENTS.md`, `docs/decisions.md`, `PLANS.md`.
- Contrato de dados: schema correspondente + `control/test_contracts.py`.
- Estado/recuperação: `state_machine.py`, `store.py`, testes M2.
- Pipeline por marco: módulo Python correspondente + teste `control/test_mN_*.py` + handoff `N_para_N+1.md`; M12.5 usa `inference.py`, `inference_backends.py` e `test_m125_inference_routing.py`.
- Prime Agent real: primeiro `docs/compatibility.md`; execução/custo continuam proibidos sem autorização específica.
- Ao terminar toda a sessão: execute `scripts/ai_history.py` com resumo, mudanças, decisões, validações, riscos e próximos passos; depois execute novamente este gerador.
