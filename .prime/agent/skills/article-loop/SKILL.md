---
name: article-loop
description: Núcleo local de estado durável do article-loop, sem runtime Prime Agent.
---

# article-loop

No Marco 6, a skill acrescenta uma orquestração por receipts. A prova local usa
`FakeRLMAdapter`; importar a skill não inicia Prime Agent, agentes, modelos ou rede.

## API pública

`DurableStore(root, *, fault=None)` mantém um JSONL encadeado por `run_id`
seguro e snapshots derivados. Seus métodos públicos são:

- `create_run(run_id, *, actor_id="system", event_id=None)`;
- `record(run_id, target, *, event_id, idempotency_key, actor_id, ...)`;
- `read_events(run_id)`, `snapshot(run_id)`,
  `rebuild_snapshot(run_id, *, persist=True)` e `checkpoint(run_id)`;
- `pause(run_id, **kwargs)` e `resume(run_id, **kwargs)`.

`State`, `TransitionError`, `StoreError`, `IntegrityError` e `StopRequested`
também são exportados. O log é a fonte de verdade: linhas parciais, JSON
inválido, IDs repetidos, hash/encadeamento divergentes e replay que viole a
máquina de estados levantam `IntegrityError`; o store não os repara
silenciosamente. Um append prepara a versão integral do JSONL em temporário no
mesmo filesystem, aplica `fsync` e `os.replace`, sincroniza o diretório quando
suportado e verifica o resultado. Temporários órfãos não alteram o replay.
`control/STOP` bloqueia operações novas depois da aquisição do lock.

Antes do lock/commit, `record()` rejeita os parâmetros estruturais inválidos:
IDs e tipo de evento vazios, chave de idempotência vazia ou maior que 256,
`run_id` inseguro, payload não objeto e hashes de artefato não únicos ou fora
do SHA-256 hexadecimal minúsculo. Durante o replay, o mesmo contrato fechado
de `event.schema.json` é aplicado integralmente, incluindo versão `1.1.0`,
inteiros não booleanos, data ISO 8601 com fuso e hashes por posição no log.

`ingest(root, *, fault=None)` é o preflight M3. Ele congela exatamente o PDF
regular `input/inbox/artigo.pdf` (e o ZIP opcional) antes de qualquer leitura,
preserva os bytes congelados por SHA-256 em
`artifacts/original/<sha256>/document.pdf` e registra `INGESTED` com caminho,
tamanho, hash e modo de fonte antes de extração, renderização ou gate. Só então
usa Poppler local e, após o gate local `SOURCE_READY`, publica
`versions/champion/v0000`; os IDs NEW → INGESTED → SOURCE_READY são
determinísticos. A identidade imutável registrada nos dois eventos e no
`ingestion-manifest` inclui SHA-256 do PDF, presença de `source.zip`, seu
SHA-256/tamanho quando presente e o `source_mode`; retomada e idempotência
rejeitam ZIP adicionado, removido ou alterado. Antes de qualquer escrita, os oito diretórios gerenciados são
validados sem symlinks e dentro da raiz; cada árvore em staging sincroniza
todos os arquivos e diretórios antes do rename. Um `source.zip` só é usado se
todos os membros `.tex` que seriam copiados tiverem LaTeX UTF-8 com chaves,
ambientes e um único `document` estruturalmente válidos; em dúvida, a execução
usa `PDF_ONLY_RECONSTRUCTION` e registra issue.
O retorno informa `created` ou `idempotent` somente após revalidar artefatos,
manifests, hashes e árvores sem symlink. PDFs sem texto recebem classificação
escaneada e issue de OCR desligado; nenhuma fórmula ou símbolo é inferido. A
reconstrução LaTeX escapa toda extração não confiável e é compilada em diretório
isolado com `-no-shell-escape`. `IngestionError` e `SourceReadyError` explicam
entradas inseguras ou baseline insuficiente.

## API pública M6--M10

Todas as funções abaixo são assíncronas: `await bootstrap(pdf_path, root=".")`,
`await preflight(root=".")`, `await run_cycle(root=".", cycle_id=None,
dry_run=False)`, `await status(root=".")`, `await checkpoint(root=".")`,
`await pause(root=".")`, `await resume(root=".")`, `await stop(root=".")` e
`await finalize(root=".")`. `run()` permanece um alias de `run_cycle()`.

M10 também expõe `decide(root, run_id, cycle_id=...)`,
`finalize_decision(root, run_id, cycle_id=...)`, `pareto_relation(...)` e
`TransactionalFinalizer`. `finalize()` não usa mais o atalho histórico de M6:
ele exige uma `Decision` M10 ativa e delega ao finalizador que revalida hashes,
diagnóstico e precondições antes de qualquer efeito. Para `FINALIZE`, as
precondições incluem relatórios imutáveis de W22/W51/W53 vinculados por SHA-256
ao manifesto completo, PDF renderizado e relatório final; uma retomada após o
receipt só conclui o evento/checkpoint que faltava. A política é local e não
inicia Prime Agent, modelos ou um artigo real.

`PrimeRLMAdapter` encapsula somente a API instalada: admissão por
`await rlm(prompt, name=...)`, mensagens sem `mode` e remoção pelo pai. Antes
de uma execução autorizada, a sessão raiz deve consultar e executar
`/rlm-max-depth 2` (sem `--global`). `FakeRLMAdapter` permite validar a árvore,
duplicatas, recibos e retomada sem runtime real.

`Orchestrator` nunca faz fan-in por `gather()`: a admissão retorna somente o
handle, e cada conclusão é uma nova passagem curta que relê o journal. M6 usa
exclusivamente o `ingest-<sha256>` de M3, já em `SOURCE_READY`, depois de
revalidar PDF congelado, manifesto de ingestão e champion `v0000`; o
`base_hash` é o `content_hash` daquele champion. O plano M5 validado e
content-addressed é persistido antes da primeira admissão; plano pausado e
entradas `FREEZE` não criam filhos.

O journal complementar em `state/orchestration/<run>/journal.jsonl` é
append-only, encadeado por hash, bloqueado por execução e sincronizado; o
snapshot é apenas projeção atômica. Tarefa, view e prompt compilado são
content-addressed no workspace isolado antes do spawn. Em queda entre spawn e
persistência, a retomada reconcilia `list_subagents()` pelo nome determinístico.
M00 admite somente S10--S50, e cada Sxx, em seu próprio contexto de sessão,
admite apenas Wxx--Wxx+2; folhas não admitem filhos.

Os especialistas escrevem em `workspaces/<run>/cycle-<n>/<papel>/`; o receipt
contém somente caminho, SHA-256 e versão. Sob o mesmo lock, o pai verifica
matriz W→S/S→M, identidade, ciclo, base, schema, hash e workspace sem symlink.
Uma repetição byte-idêntica é idempotente; conteúdo diverso para o mesmo
emissor/ciclo é conflito. Só `DepartmentPacket` validado sobe de `Sxx` para
`M00`; a raiz não fala com netos. Pausa, parada e finalização bloqueiam
mutações; cancelamento é journalizado antes da remoção. A API pública live não
seleciona o fake: sem `PrimeRLMAdapter` explicitamente injetado ela falha
fechada, e `dry_run` grava somente preview separado.

## Memória e ativação M5

`Blackboard(root)` mantém ledgers JSONL append-only, separados por execução,
para claims, issues, tasks, dependencies, evidence e decisions. `append()`
rejeita conflito de identificador; `claims()` projeta a revisão mais recente
sem apagar a trilha; `impact()` produz claims, objetos documentais e papéis
afetados. Claims exigem texto, tipo, localização, dependências, evidências,
status, severidade, SHA-256 de fonte e ciclo da última validação; seu ID é
determinístico.

`ActivationPlanner(limits).plan(...)` é puro e retorna `ActivationPlan`, sem
disparar papel algum. Ele emite entradas RUN/CHECK/SHIFT/FREEZE, checkpoint de
pausa se algum limite for excedido e um `activation_map.json` recusando
sobrescrita. `specialist_view`, `submanager_view` e `manager_view` expõem,
respectivamente, apenas dados locais, propostas dos filhos e cinco pacotes
departamentais. A integração M6 deverá respeitar `paused` e nunca criar tarefa
ou chamada para entradas FREEZE.

Os marcos futuros devem preservar os contratos em `config/schemas/` e só podem
executar integração Prime Agent após o preflight previsto em
`docs/compatibility.md`.

## Comandos locais M11

`scripts/article_loop_command.py` é uma ponte fina JSON-in/JSON-out para as
APIs públicas existentes: `bootstrap`, `preflight`, `run`, `status`,
`checkpoint`, `pause`, `resume`, `stop` e `finalize`. Ela valida a raiz, IDs,
tipos e campos permitidos, rejeita `settings.json` não confirmado e nunca
seleciona `FakeRLMAdapter` a partir de entrada externa. `run` é dry-run por
default; um processo fora de uma sessão Prime não pode fabricar o
`PrimeRLMAdapter`, portanto uma execução live sem adaptador explícito falha
fechada como definido no M6.

Os templates são arquivos diretos em `.prime/agent/prompts/`, com frontmatter
limitado a `description` e `argument-hint`. `bin/check.sh` valida localmente
essas superfícies, os contratos de profundidade e os defaults de orçamento sem
rede. `bin/start-prime.sh` roda o check e só pode encaminhar as flags
confirmadas `--skill` e `--prompt-template` ao executável Prime Agent depois de
autorização explícita, STOP ausente, configuração live e preflight aprovados;
se o binário ou alguma precondição faltar, falha sem iniciar sessão. Nenhum
template faz polling infinito: admissão/espera é reportada por receipt e o
turno termina.

## Complemento corretivo M6 (segundo)

O adaptador Prime só aceita handles documentados com `rlm_child_id`, `name`,
`session_dir` e `model`; `preflight()` apenas verifica superfícies e informa
`/rlm-max-depth 2`, sem executar sessão. Cada PLAN M5 é imutável por ciclo e
um ciclo seguinte exige `CYCLE_COMPLETE` no `DurableStore`. `SPAWN_INTENT` é o
token de proprietário da admissão e a recuperação consulta somente os filhos
diretos pelo nome determinístico. Todo receipt é copiado por SHA-256 para área
imutável antes de consumo; mudança no arquivo original rejeita consolidação.
S30/S40 técnicos precisam de review S20 canônico do mesmo ciclo/base/proposta.
M6 permanece offline e não inicia M7.

## Operação limitada M12

`BudgetLedger` e `StructuredLogger` são as superfícies locais de orçamento e
observabilidade. O ledger é por `run_id`, append-only, content-addressed e
protegido por lock; `reserve()` deve preceder qualquer operação consumidora,
`admit()` registra a fronteira atômica, `reconcile()` registra tokens
input/output/cache e `mark_uncertain()` conserva saldo quando o resultado não
é conhecido. `release_unadmitted()` exige prova explícita de não admissão.

Limites usam tokens inteiros não negativos e podem ser hierárquicos por ciclo,
departamento, papel e modelo, além de chamadas, filhos concorrentes, retries,
wall time, ciclos e julgamentos extras. Excesso reconciliado bloqueia novas
reservas. `status()` e `human_status()` expõem uso confirmado/reservado,
comprometido e saldo por limite, reservas, última melhoria, diagnóstico,
próxima ação, alertas e `assurance`.

Os perfis `calibration` e `overnight` são tetos opt-in, mas permanecem
desabilitados em `config/budgets.yaml`; M12 não liga modelo, Prime Agent, rede,
APIs pagas ou execução prolongada. `live=True` exige autorização explícita no
mesmo run, hash de configuração/perfil, provider/modelo, teto e timestamp.
`STOP` bloqueia novas reservas e `PAUSE` preserva o ledger e reservas abertas.

Logs estruturados aceitam apenas campos de allowlist, rotacionam sem apagar
evidência e sincronizam writes com fsync. Não registrar credenciais, cookies,
auth, prompts completos, artigo integral ou mensagens privadas. Depois de
crash, reabrir o ledger, verificar a cadeia e reconciliar receipts/handles;
nunca devolver saldo por suposição nem usar loop textual infinito.

## Routing de inferência M12.5

`ModelRegistry` carrega e valida a seção `inference` de
`config/budgets.yaml`; `ModelRouter` é puro e escolhe targets por papel,
capacidade, limite, fallback e independência. `InferenceRuntime` aceita somente
um `AgentTask` já validado e executa a sequência fechada `route -> reserve ->
admit -> backend -> receipt -> reconcile`. Ele não substitui o orchestrator M6,
não cria filhos e não altera `PrimeRLMAdapter.spawn(prompt, name)`.

Decisões ficam em `state/inference/<run>/routes/` e receipts operacionais em
`state/inference/<run>/receipts/`, ambos write-once, hash-bound e sem prompt ou
resposta integral. Repetir a mesma chamada depois de crash reconcilia o receipt
existente sem reinferência; ausência de receipt após admissão fica `UNCERTAIN`.
`FREEZE` não reserva nem chama backend. Escalation requer reason code fechado,
tentativa limitada e nova decisão persistida; nunca faça retry silencioso.

O fake exige `allow_test_doubles=True` estritamente booleano e é recusado com
`live=True`. O backend OpenAI-compatible local aceita só loopback explícito,
timeout e resposta limitada, sem proxies ou redirects. A configuração
versionada mantém inferência e permissões desabilitadas. Uma autorização
roteada usa provider/model nulos e `routing_policy_hash`; qualquer drift
invalida a autorização.

## Execução dual M12.5.1 Phase A

`ExecutionPolicy` valida as seções top-level `execution` e `privacy`.
`DualExecutionAdapter` escolhe `prime` ou `routed` somente por Sxx. O caminho
Prime delega sem mudar `PrimeRLMAdapter.spawn(prompt, name)`; o caminho routed
persiste um handle de controle local e mantém a mesma admissão Wxx de M6.
`DualExecutionController.execute_routed_department()` materializa a tarefa,
chama `InferenceRuntime`, copia os bytes científicos duráveis para
`agent-proposal.json`, usa `Orchestrator.receipt()` e chama a consolidação M6.

`ContextMaterializer` só lê texto autorizado pela AgentTask/view, rejeita
travessia e symlink, omite o PDF binário, registra proveniência/hash e falha se
contexto + output excederem o target. `deny_remote` é o default; os modos
remotos não autorizam conteúdo fora dos locators. Outputs ficam write-once sob
`state/inference/<run>/outputs/` e sustentam retomada sem reinferência.

O ledger reserva e reporta custo inteiro. O teto versionado é 10.000.000
microunits USD; preços são inteiros por milhão de tokens, usage conhecido é
recalculado e usage desconhecido mantém a reserva. `PAID_RUNTIME_READY` descreve
a capacidade do código, não autorização: `execution.enabled`, inferência,
targets, rotas e paid/live continuam desabilitados. `execution_readiness()`
separa `implementation_ready`, `configuration_ready` e `live_ready` sem ler
credenciais.
