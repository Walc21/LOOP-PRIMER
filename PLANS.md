# ExecPlan vivo — article-loop

## Objetivo

Construir uma integração verificável para revisão iterativa de artigo matemático
sem alterar o núcleo do Prime Agent. A arquitetura canônica possui 21 papéis,
execução esparsa, estado durável próprio, júri cego, gates determinísticos,
champion, challengers e arquivo Pareto.

A fonte normativa de arquitetura é `docs/architecture.md`; a autoridade da
integração Prime Agent continua sendo `docs/compatibility.md`.

## Estado atual

- M13.1 concluído e validado no checkpoint local `ac49084`:
  adaptadores routed de júri e meta-review usam o runtime existente sem criar
  papéis RLM. Avaliadores têm `role_id: null`, identidade explícita de ator e
  `routing_role_id` como autoridade de política; o payload científico continua
  pertencendo ao modelo e o protocolo ao LOOP (ADR-035). Receipts de
  avaliador usam o contrato fechado 1.2.0; 1.0/1.1 e suas identidades legadas
  permanecem byte-compatíveis. Replay durável não reinfere. Validação offline:
  14 testes dedicados, 135 adjacentes, check M13 com 25 testes e regressão
  completa com 465 testes, sem falhas, erros ou skips.
- Atualizado em 2026-09-05.
- M13 concluído na aceitação offline: 25 testes de sistema, 82 testes adjacentes
  de M9/M10/handoff e 445 testes na regressão completa passaram sem skips em
  Python 3.14.4. A CLI conservou uma execução sintética e a auditoria independente
  confirmou a mesma entrega sem modificar seus arquivos. Provedores live e júri
  routed operacional permanecem separados desta aceitação.
- M0 — compatibilidade, segurança e documentação-base: concluído.
- M0.5 — alinhamento da arquitetura canônica: concluído.
- M2 — máquina de estados, event log e recuperação: concluído após correção contratual final.
- M0.6 — completude de caminhos e ordem transacional: concluído nesta etapa.
- M1 — scaffold e contratos canônicos: concluído.
- M1.1 — correção dos contratos condicionais: concluído; 46 testes cobrem
  exemplos positivos e negativos dos 12 schemas e invariantes de M00.
- Não houve instalação de dependências, início do Prime Agent, subagente,
  `/autonomous`, `/refine` ou chamada de modelo.
- Versão instalada auditada: `prime-agent 0.7.1`.
- M3 correção final de identidade concluída: vincula `source.zip` aos eventos,
  à recuperação e ao champion; M4 concluído, sujeito a endurecimento
  contratual pontual.
- M4 concluído: contratos de prompt content-addressed, overlays versionados e
  compilação local cobrem os 21 papéis sem iniciar agentes nem alterar o catálogo.
- M5 corrigido cirurgicamente: memória operacional append-only, grafo de impacto, views
  fechadas e planejador determinístico foram validados sem chamada a agentes ou
  modelos.
- M9 concluído; M10.1 concluído localmente como endurecimento de cobertura de
  M10. A rodada valida os nove efeitos da tabela fechada, todas as fases de
  recuperação, concorrência real, Pareto completo e o gate de finalização
  vinculado a PDF, manifesto, hashes e relatório final. M11--M13 permanecem
  fora de escopo.
- M11 concluído localmente nesta sessão: ponte CLI JSON-in/JSON-out para as
  nove APIs existentes, nove templates planos descobríveis, guardrails
  aditivos, `check.sh`, launcher dry-run por padrão e runbook. O launcher live
  exige autorização/configuração fail-closed, preflight M3 e `prime-agent` no
  `PATH`; como o binário não foi encontrado e o orçamento atual é zero, nenhum
  processo Prime foi iniciado. M12--M13 permanecem fora de escopo.
- M12 concluído e publicado no checkpoint de referência `e5eb78f`. M12.5 está
  concluído como camada aditiva de routing/backend entre tarefas canônicas e o
  ledger, sem alterar M6, estados, ações, papéis ou iniciar M13. O fixture HTTP
  loopback real passou na matriz GitHub Actions Python 3.11–3.13.
- M12.5.1 Phase A concluída localmente sobre o checkpoint inicial `ba316b5`:
  execução dual por departamento converge no contrato M6, contexto autorizado
  é materializado e hash-bound, saída científica precede o receipt, privacidade
  é vinculada ao run e o ledger impõe teto inteiro de USD 10. A promoção limpa
  mantém o modelo restrito ao payload científico e o LOOP como único emissor do
  envelope de protocolo/identidade antes da validação canônica; o W41 foi
  aceito por M6 e o S40 consolidado no caminho local comprovado. A configuração
  final permanece desabilitada, sem targets, rotas, modelos ou credenciais;
  configuração humana e qualquer smoke live continuam fora desta fase.
- Ferramentas auxiliares de handoff para IA concluídas: um gerador local de
  contexto compacto e um registrador local de histórico de sessões. Elas não
  alteram a máquina de estados, candidatos, gates ou a autoridade dos scripts
  científicos M0--M13.
- Reparo de integração Git/GitHub e separação de audiências documentais
  concluído: a árvore validada foi preservada, o merge artificial entre
  históricos independentes saiu de `main`, a branch ficou como descendente
  linear de `origin/main` e o protocolo de IA saiu do `README.md` público.

## Contratos já decididos

- O catálogo de 21 papéis, os caminhos canônicos, os estados, as ações e as
  dimensões de avaliação já são definidos em `docs/architecture.md`; M1 não
  inventará nem renomeará esses contratos.
- A hierarquia RLM autorizada no futuro é profundidade 2: M00 na profundidade
  0, S10–S50 na 1 e W11–W53 na 2. A sessão raiz deverá usar
  `/rlm-max-depth 2`, sem `--global`, somente após autorização específica.
- `rlm(...)` devolve apenas handle de admissão. Propostas detalhadas chegam por
  arquivo canônico e resumo ou referência por `agent_message` compatível.
- Agentes propõem; somente o merge escreve no challenger; nenhum agente escreve
  diretamente no champion.
- O pipeline canônico é: propostas estruturadas → consolidação departamental →
  síntese do gerente → merge em workspace isolado → challenger imutável → gates
  determinísticos → júri cego → diagnóstico → decisão canônica → finalizador
  transacional → promoção, arquivo Pareto ou rejeição. A decisão só opera sobre
  candidato construído e avaliado.
- O finalizador apenas revalida hashes e aplica atomicamente ação autorizada;
  não reconstrói nem modifica o conteúdo avaliado. `SHIFT` explora uma
  alternativa motivada por plateau, oscilação ou diagnóstico e não é mera
  repetição de `RUN`.
- Dependências futuras só podem ser locais, declaradas pelo projeto, necessárias
  ao marco corrente e registradas neste plano. Instalações globais são proibidas.
- O bootstrap de ambiente para a ingestão M3 cobre somente Debian/Ubuntu:
  instala ferramentas locais de sistema quando ausentes e cria `.venv` no
  repositório. O Prime Agent permanece uma dependência opcional externa e não
  é instalado por esse mecanismo.

## Marcos canônicos

| Marco | Entrega | Estado | Critério de aceitação |
|---|---|---|---|
| M0 | compatibilidade, segurança e documentação-base | concluído | versão, superfícies e incompatibilidades registradas sem runtime |
| M0.5 | alinhamento da arquitetura | concluído | catálogo, estados, ações, dimensões, scripts e árvore canônica verificados |
| M0.6 | completude de paths e ordem transacional | concluído | caminhos adicionais, ordem merge → gates → júri → decisão → finalizador e SHIFT verificados |
| M1 | scaffold e contratos canônicos | concluído | árvore materializada, 21 papéis, 8 dimensões e 12 schemas validados localmente |
| M2 | máquina de estados, event log e recuperação | concluído após correção contratual final | API e replay aplicam integralmente `event.schema.json`; 30 testes M2 e 76 testes locais aprovados |
| M3 | ingestão PDF e baseline editável | concluído | original publicado e registrado em `INGESTED` antes das derivações; PDF, presença/hash/tamanho de ZIP e modo de fonte são imutáveis até `v0000`, com contenção de caminhos e falha fechada |
| M4 | papéis, prompts imutáveis e compilador | concluído | os 21 papéis canônicos compilam deterministicamente a partir de núcleos verificados, contexto fechado, overlay registrado e schema de saída |
| M5 | blackboard, grafo de claims e ativação esparsa | concluído (corrigido) | localizadores estruturados, lock, limites e regras de ativação corrigidos; M6 permanece não iniciado |
| M6 | integração RLM hierárquica | concluído | adapters Prime/Fake, receipts validados, árvore esparsa e retomada local aprovados sem modelo |
| M7 | síntese, merge, gates e arquivos de versões | concluído após correção final restrita | publica um único challenger integralmente read-only, verifica o `GateReport` canônico persistido antes de `GATES_PASSED` e executa os 13 gates locais de modo fail-closed; júri, decisão e M8 continuam fora do escopo |
| M8 | avaliador externo cego em júri | concluído | avaliação cega externa por júri e meta-revisão com separação de test doubles e publicação transacional write-once |
| M9 | detecção de progresso e refoco | concluído | diagnóstico determinístico em 7 classificações canônicas, transição EVALUATED -> DIAGNOSED e refoco reversível com overlays imutáveis sob CAS |
| M10 | política de compensação e finalizador | concluído localmente | política pura emite uma `Decision` fechada; finalizador revalida hashes e aplica a disposição atômica sem modificar o challenger avaliado |
| M10.1 | endurecimento de cobertura e gate final de M10 | concluído localmente | pacote final hash-bound, rederivação de decisão, recuperação por fase, concorrência e Pareto verificados sem iniciar M11 |
| M11 | comandos e configuração do Prime Agent | concluído localmente | ponte CLI, templates planos, guardrails aditivos, runbook e launcher fail-closed; `settings.json` omitido sem schema instalado confirmado |
| M12 | orçamento, observabilidade e execução prolongada | concluído localmente | ledger hash-bound, reservas atômicas, reconciliação conservadora, perfis opt-in, status/logs/alertas e retomada fail-closed; sem modelo, rede ou execução real |
| M12.5 | routing de inferência e integração de backends | concluído localmente e na CI | registry/router determinísticos, política hash-bound, autorização multi-target compatível, receipts write-once e backend loopback validado na matriz Python 3.11–3.13, sem bypass de M6 nem target pago implícito |
| M12.5.1 | ligação end-to-end de execução dual — Phase A | concluído localmente | seleção Prime/Routed por departamento, ator de controle routed persistente, contexto mínimo hash-bound, privacidade fail-closed, teto monetário inteiro, saída científica durável e retomada sem reinferência; defaults disabled e nenhum smoke live |
| M13 | testes de sistema e entrega | concluído | 25 testes offline cobrem A–T: ingestão até promoção/Pareto/rejeição, original imutável, cadeia auditável, veto, cegueira, replay, recuperação e auditoria independente; regressão de 445 testes sem skips |
| M13.1 | identidade de avaliador para júri/meta routed | concluído localmente | identidade de avaliador separada dos 21 papéis RLM, autoridade explícita de routing, receipt 1.2.0 fechado e replay durável sem reinferência; 14 testes dedicados, 135 adjacentes, check M13 de 25 testes e regressão completa de 465 testes aprovados offline |

### Aceitação M13

Compor APIs reais M2–M12.5.1 em fixtures temporárias; dublês somente nas
fronteiras Prime, inferência e júri. Acrescentar auditoria local da entrega,
veto matemático, cegueira/inversão, adulteração, replay e recuperação concorrente.
Nenhuma dependência nova, relaxamento de schema ou configuração live.
O adaptador operacional routed M8 permanece posterior; a independência por
modelo foi testada no router e o júri offline nas interfaces M8 existentes.

Aceitação executada por `python3 scripts/m13_system_check.py`; matriz e limites
em `docs/m13-system-acceptance.md`. `--verify-root` recompõe a evidência local
de uma disposição concluída. O pacote promovido contém a fonte revisada e
preserva `baseline.pdf` como proveniência; não substitui o pacote terminal
`FINALIZE` de M10.1. Nenhuma dependência foi instalada, nenhum modelo foi
chamado e nenhum push foi realizado. A matriz CI 3.11–3.13 fica configurada
para a futura publicação; somente a gramática 3.11 foi verificada adicionalmente
no host, pois esse interpretador não tem `jsonschema` instalado.

## Sequência canônica dos Prompts 01–13

1. M1 materializa o scaffold e os contratos canônicos já documentados.
2. M2 implementa a máquina de estados, o event log e a recuperação.
3. M3 processa a entrada canônica e produz baseline editável com preservação do
   PDF original.
4. M4 introduz papéis, prompts imutáveis e compilador, sem mudar seu catálogo.
5. M5 implementa blackboard, grafo de claims e ativação esparsa.
6. M6 integra a hierarquia RLM somente em execução autorizada.
7. M7 constrói síntese, merge, gates e arquivos de versões.
8. M8 integra o avaliador externo cego como júri.
9. M9 integra detecção de progresso e refoco.
10. M10 integra compensação e finalização transacional.
11. M11 configura comandos e recursos locais do Prime Agent.
12. M12 acrescenta orçamento, observabilidade e execução prolongada autorizada.
13. M13 executa testes sistêmicos e prepara a entrega.

M12.5 e M12.5.1 são hardenings aditivos surgidos depois de M12 e antes de M13;
eles não renumeram nem substituem nenhum dos Prompts canônicos 01--13. A Phase
A de M12.5.1 entrega código e validação offline; configuração humana e smoke
live exigem uma fase posterior e autorização específica.

## Critérios de aceitação do produto

- Há exatamente 21 papéis lógicos com os IDs canônicos e a execução nunca
  ultrapassa profundidade RLM 2.
- O gerente geral executa sempre; o primeiro ciclo auditável envolve os cinco
  departamentos; ciclos posteriores obedecem ao grafo de impacto.
- Os 16 estados e as 9 ações canônicas são persistidos e as transições são
  recuperáveis por event log.
- `correctness_math` é gate duro e não pode ser compensado por clareza, estilo
  ou outra dimensão.
- O PDF em `input/inbox/artigo.pdf` é preservado por SHA-256; `source.zip`, se
  existente e aprovado em inspeção segura, é a fonte preferencial.
- Apenas merge escreve challenger e nenhuma rotina de agente escreve champion.
- Merge constrói challenger imutável antes de gates e julgamento cego; decisão e
  finalização só ocorrem após essa avaliação e deixam evidência suficiente para
  reconstituir champion, challengers, rejeitados e fronteira Pareto.
- O projeto não altera instalação/configuração global do Prime Agent e não faz
  chamadas pagas sem autorização específica.

## Riscos e bloqueadores

| Risco ou bloqueador | Mitigação/decisão |
|---|---|
| versão instalada `0.7.1` diverge de exemplos em `main` | adaptador usa somente contratos registrados em `docs/compatibility.md` |
| contrato de `agent_message.mode` é conflitante | não usar `mode`; persistir resultado canônico em arquivo |
| PDF e `source.zip` reais não foram fornecidos | M3 usa fixture local nos testes; uma execução real exige entrada do usuário |
| runtime Prime Agent pode gerar custo | M6 e M11 requerem autorização específica de provedor e orçamento |
| ativação excessiva multiplica custo/ruído | grafo de impacto e FREEZE impedem chamadas não justificadas |

## Registro de progresso

- 2026-09-03 — A validação pré-publicação da M12.5.1 revelou uma
  divergência de contrato: a Phase A e a CI executam literalmente
  `bin/check.sh`, portanto o arquivo precisa ser executável, mas o teste de
  scaffold M1 ainda exigia bit executável ausente para `check.sh`. A correção
  planejada é atualizar somente essa asserção legada, preservando
  `start-prime.sh` não executável e `preflight.sh` executável, e repetir a
  regressão integral antes de qualquer commit ou push.

- 2026-09-03 — M12.5.1 Phase A concluída localmente. A prova end-to-end usa
  S10 routed com W11 local, W12 remoto simulado e W13 local, publica outputs
  científicos duráveis, chama receipts M6 e reutiliza a consolidação
  `DepartmentPacket`; S20 permanece no caminho Prime simulado. Cobertura
  dedicada validou privacidade `deny_remote`/`scoped_remote`/`full_remote`,
  marcador de não exfiltração, contenção/symlink/overflow, preço inteiro, teto
  exato de 10.000.000 microunits e rejeição de +1, concorrência, autorização,
  independência por modelo, backend HTTPS mockado sem proxy/redirect e todos os
  cortes de recuperação sem chamada adicional. As suítes dedicadas executaram
  63 testes com sucesso e 1 skip histórico; a regressão integral final executou
  410 testes com sucesso em 268,029 s e 1 skip histórico do fixture loopback.
  `py_compile`, `bash -n`, `git diff --check` e o check JSON passaram. A
  configuração final reporta `implementation_ready=true`,
  `configuration_ready=false`, `live_ready=false`, sem targets/rotas e com
  `deny_remote`; nenhum Prime Agent, modelo, rede real, API paga, credencial,
  artigo real, instalação, M13, commit ou push foi executado.

- 2026-09-03 — M12.5.1 Phase A iniciada sobre HEAD limpo
  `ba316b50a707d490348192d528046b6eec567250`. A decisão é preservar
  `PrimeRLMAdapter.spawn(prompt, name)` e adicionar seleção por departamento:
  departamentos Prime mantêm a hierarquia M6, enquanto departamentos routed
  usam um ator de controle local persistente e trabalhadores via
  `InferenceRuntime`, sempre publicando o mesmo `agent-proposal.json` e usando
  `Orchestrator.receipt()`. O contexto virá apenas de locators autorizados e
  texto M3, com contenção/symlink checks, hash e limite fail-closed. A política
  de privacidade por run inicia em `deny_remote`; o teto monetário será
  10.000.000 microunits USD, com reserva antes da chamada e reconciliação
  conservadora. Incertezas explícitas: a instalação observada hoje informa
  somente `prime-agent 0.9.1`, portanto seleção de modelo por filho é
  `unknown_on_current_version`; não há configuração real de target, preço,
  rota, modelo ou credencial. Não haverá Prime Agent, modelo, rede, API paga,
  artigo real, instalação, M13, commit ou push nesta fase.

- 2026-09-03 — Correção CI M12.5 confirmada no GitHub Actions pelo run
  `33807419247` do commit `49fad01`: os três jobs passaram, cada um com 399
  testes (`3.11`: 213.130s; `3.12`: 248.472s; `3.13`: 233.922s). O fixture
  loopback real cobriu o caso de conexão fechada e encerrou o critério J sem
  ativar modelo, target pago, Prime Agent ou M13.

- 2026-09-03 — Correção local da CI M12.5 concluída. O backend passou a
  normalizar `RemoteDisconnected`, `ConnectionResetError` e `BrokenPipeError`
  diretos como `BACKEND_FAILURE` pós-envio; o runtime continua marcando a
  reserva `UNCERTAIN`. O teste socketless reproduz exatamente a exceção dos
  runners, e o check M11 agora testa deterministicamente Prime presente e
  ausente sem depender do host. A suíte completa executou 396 testes com
  sucesso e 1 skip local do fixture loopback; as suítes M12.5/M12/M11/
  contratos executaram 117 testes com sucesso e 1 skip. A revalidação foi
  posteriormente concluída no run `33807419247` da matriz Python 3.11–3.13.

- 2026-09-03 — Correção CI M12.5 iniciada após os runs GitHub Actions
  `33802406129`, `33802521340` e `33802584988` falharem igualmente em Python
  3.11, 3.12 e 3.13. A causa observada é
  `http.client.RemoteDisconnected` escapar do backend local no caso de conexão
  fechada sem resposta. A menor correção deve normalizar essa falha pós-envio
  como `BACKEND_FAILURE`, adicionar reprodução socketless e preservar
  `UNCERTAIN`, sem ampliar rede, targets, custo, M13 ou contrato M6.
  A validação local também encontrou `prime-agent 0.9.1` no PATH; o teste M11
  será isolado do estado do host e verificará presença/ausência simuladas sem
  iniciar sessão ou adotar APIs novas.

- 2026-09-03 — A implementação M12.5 foi commitada como `dbf411c`
  (`feat(m12.5): add deterministic inference routing`) e publicada por
  fast-forward em `origin/main` (`e5eb78f..dbf411c`). O status técnico não foi
  inflado: o critério J continua pendente por bloqueio de socket loopback, M13
  não foi iniciado e inferência/targets pagos continuam desabilitados.

- 2026-09-03 — M12.5 implementado e validado localmente, exceto pelo smoke
  HTTP real do fixture loopback: o sandbox recusou a abertura do socket e a
  tentativa de elevação foi negada, portanto o critério J permanece
  explicitamente não provado. A suíte completa executou 395 testes com sucesso
  e 1 skip; as suítes dedicadas M12.5/M12/M11/contratos executaram 116 testes
  com sucesso e 1 skip. `py_compile`, `bash -n`, `bin/check.sh` e
  `git diff --check` passaram; `shellcheck` não está instalado. Foram
  preservados defaults fechados, M6 e autorização legacy. Não houve Prime
  Agent, modelo, rede externa, segredo, instalação, M13, commit ou push.

- 2026-09-03 — M12.5 iniciado sobre o checkpoint M12 `e5eb78f`. O escopo é a
  menor camada project-local e content-addressed que transforma `AgentTask` em
  pedido de inferência, escolhe target deterministicamente e obriga a ordem
  route → reserve → admit → backend → receipt → reconcile. A autorização M12
  ganhará modo routed sem invalidar ledgers legacy. A auditoria estática não
  encontrou o executável/pacote Prime anteriormente registrado, portanto a
  seleção de modelo per-child fica `unsupported_verified` e
  `PrimeRLMAdapter.spawn()` permanece inalterado. Targets pagos ficarão
  bloqueados porque os tetos monetários atuais não têm enforcement no ledger.
  Não haverá Prime Agent, modelo, rede externa, segredo, instalação, M13,
  commit ou push nesta sessão.

- 2026-09-03 — M11 planejado para esta sessão sobre árvore limpa e checkpoint
  M10 ancestral. O escopo é estritamente expor as APIs locais existentes por
  uma ponte JSON-in/JSON-out, nove templates Markdown planos, `check.sh`, um
  `start-prime.sh` fail-closed, guardrails aditivos e runbook. A configuração
  `.prime/agent/settings.json` será omitida porque o executável Prime Agent não
  está disponível nesta sessão e `docs/compatibility.md` não confirma o
  formato/chaves instalados. Não haverá sessão Prime, modelo, rede, segredo,
  instalação, commit ou publicação. O `README.md` será apenas sincronizado
  com o status e a referência dos comandos M11.

- 2026-09-03 — M11 concluído localmente sem iniciar Prime Agent, modelo, rede,
  credencial, instalação, commit ou publicação. A ponte
  `scripts/article_loop_command.py` valida envelopes e IDs, rejeita campos de
  test double, e delega bootstrap/preflight/run/status/checkpoint/pause/resume/
  stop/finalize às APIs existentes; `run` permanece dry-run por padrão. Os
  nove templates planos foram descobertos e validados por frontmatter; o
  launcher verifica STOP, profundidade 2, configuração/orçamento e
  autorização antes de encaminhar somente `--skill` e `--prompt-template`.
  `bin/check.sh` e o launcher dry-run passaram; o caminho live parou no
  orçamento fail-closed antes do binário ausente. Passaram `python3 -m
  unittest -q control.test_m11_commands` (15 testes), `python3 -m unittest -q
  control.test_ai_handoff control.test_m11_commands` (23 testes),
  `python3 -m unittest discover -s control -q` (346 testes em 249.459s),
  `python3 -m py_compile scripts/article_loop_command.py
  control/test_m11_commands.py`, `bash -n` nos dois scripts e `git diff
  --check`. `shellcheck` não está disponível nesta máquina. O formato de
  `.prime/agent/settings.json` continua deliberadamente não inventado; smoke
  test live permanece pendente até uma instalação compatível e autorização
  separada.

- 2026-09-03 — M12 iniciado sobre a base M11 validada. O escopo é somente
  orçamento durável, observabilidade e operação prolongada limitada, com
  `BudgetLedger` append-only/content-addressed, reservas atômicas,
  reconciliação conservadora, perfis opt-in e status/logs/alertas redigidos.
  Os defaults de modelo, API paga, rede e execução live permanecem
  desabilitados; não haverá M13, Prime Agent ou modelo nesta sessão.

- 2026-09-03 — M12 concluído localmente. `BudgetLedger` e
  `StructuredLogger` passaram a cobrir reserva sob lock, reconciliação
  idempotente, `UNCERTAIN`, limites hierárquicos, binding de configuração,
  deadlines/duração retomáveis, status por limite, alertas idempotentes e
  redaction/rotação com fsync. Foram adicionados os schemas M12, testes
  adversariais e o handoff `12_para_13.md`. A suíte dedicada M12/M11/contratos
  aprovou 87 testes; a regressão integral aprovou 366 testes em 246.975s, com
  apenas o warning esperado do fixture negativo de ZIP. A configuração live e
  os perfis continuam desabilitados; não houve commit, publicação ou M13.

- 2026-09-03 — M10.1 concluído localmente. Foram adicionados os schemas de
  relatório de gate final e relatório final; `FINALIZE` agora exige as
  atestações imutáveis W22/W51/W53, GateReport vigente, manifesto completo,
  PDF em `artifacts/rendered/` e relatório final, todos vinculados por SHA-256.
  O finalizador rederiva a disposição fechada e, se a queda ocorre depois do
  recibo, revalida o recibo antes de registrar somente o evento/checkpoint
  pendente. A cobertura inclui Pareto real, rejeição, refoco, julgamento extra,
  pausa, promoção, finalização, nove fronteiras de crash/retry, CAS adversarial
  e duas finalizações concorrentes. `python3 -m unittest discover -s control
  -q` aprovou 331 testes em 245.441s; o único aviso foi `Duplicate name:
  'a.tex'` da fixture negativa. Não houve artigo, modelo, Prime Agent, rede,
  instalação, commit ou GitHub; M11--M13 continuam fora de escopo.

- 2026-09-02 — M10.1 iniciado sobre árvore limpa e checkpoint M9 ancestral.
  A regressão integral pré-alteração foi executada localmente, sem artigo,
  modelo, Prime Agent, rede, instalação ou GitHub. O escopo é estritamente
  complementar a M10: validar os nove efeitos, cada fase transacional e a
  recuperação idempotente, concorrência por processo, CAS adversarial, Pareto
  em fluxo real, limites de julgamento/técnicos/orçamento e o pacote completo
  de evidência para `FINALIZE`. M11--M13 continuam explicitamente excluídos.

- 2026-09-02 — M10 concluído localmente: `policy.py` revalida os artefatos
  M7--M9 e deriva uma `Decision` content-addressed com tabela fechada em
  `config/decision-policy.yaml`; `finalization.py` aplica a ação sob lock,
  journal persistido, `fsync`, rename atômico e CAS do pointer de champion.
  Promoção cria um novo envelope de champion para os mesmos bytes avaliados;
  Pareto e rejected preservam referências imutáveis. Foram adicionadas as CLIs
  JSON-in/JSON-out 04 e 05, testes de tabela, idempotência, mutação e crashes
  antes/depois do pointer. A regressão completa aprovou 316 testes em 214.956s.
  Não houve modelo, rede, execução do artigo, instalação, commit ou GitHub;
  M11--M13 não foram iniciados.

- 2026-09-02 — Revisão pré-publicação de M10 identificou três lacunas de
  integração a corrigir antes do commit: a disposição Pareto deve comparar a
  fronteira já publicada e tornar essa relação verificável pelo finalizador;
  o limite técnico configurado precisa produzir checkpoint/contador durável;
  e `article_loop.finalize()` deve delegar ao finalizador M10, não ao atalho
  histórico do `Orchestrator`. A atualização também sincronizará README,
  arquitetura, skill e snapshot de contexto. Nenhum runtime Prime, artigo ou
  modelo será iniciado.

- 2026-09-02 — M10 iniciado após contexto obrigatório atual, árvore Git limpa,
  validação local do checkpoint M9 `fd23224` como ancestral de `HEAD` e suíte
  integral M0--M9 aprovada (307 testes). O escopo autorizado é estritamente a
  política de decisão determinística, publicação de `Decision`, journal de
  finalização e disposições transacionais para champion, Pareto e rejected.
  Não haverá execução do artigo, modelo, rede, instalação, commit ou acesso ao
  GitHub; M11--M13 não seriam iniciados sem nova autorização.

- 2026-09-02 — Concluído reparo estritamente infraestrutural da integração
  Git/GitHub e das superfícies Markdown. Foram diagnosticados dois diretórios
  `.git` aninhados, um merge `ours` entre históricos sem ancestral comum e um
  `AI_CONTEXT.md` que incorporava caminho absoluto/HEAD do checkout. A mudança
  preservou um backup local, manteve a árvore funcional, tornou `main`
  publicável por fast-forward e separou o `README.md` humano dos gatilhos
  auto-descobertos em `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, instruções do
  GitHub Copilot e integração Prime. Nenhum marco M10+ será iniciado.

- 2026-09-01 — Reconciliação da camada de handoff com a publicação no GitHub
  concluída. Os sete arquivos comunitários foram preservados; o README mantém a
  apresentação nova, mas recupera o gatilho obrigatório e declara M10 como
  pendente. O gerador agora limita o README extenso, normaliza previews e exclui
  seus quatro artefatos gerados do diff, permanecendo idempotente mesmo quando
  `AI_CONTEXT.md` é rastreado. O CI instala TeX/Poppler e executa a descoberta
  integral. Passaram 59 testes direcionados/contratuais e 306 testes completos,
  além de `py_compile`, duas gerações idênticas e `git diff --check`.

- 2026-09-01 — Iniciada a reconciliação da camada de handoff para IA com o
  commit posterior de publicação no GitHub. O snapshot content-addressed da
  sessão original comprovou que os três utilitários, os gatilhos, os testes e a
  documentação normativa permaneceram byte a byte; a mudança posterior
  acrescentou sete arquivos comunitários e substituiu somente `README.md`.
  Serão preservadas as adições do GitHub, restaurado o aviso obrigatório de
  entrada para IAs e corrigidas descrições/CI que antecipam M10 como concluído.

- 2026-09-01 — Camada auxiliar de contexto/handoff concluída. O gerador
  content-addressed inventaria fontes e estado/runtime canônico (este último
  somente por metadata/hash), extrai arquitetura/APIs/schemas/testes, incorpora
  o histórico e publica `AI_CONTEXT.md` idempotentemente. O registrador
  reconstrói 35 commits e 26 ADRs, recebe resumo estruturado de encerramento,
  mantém ledger/snapshot e renderiza `docs/AI_HISTORY.md`. Gatilhos foram
  adicionados a `AGENTS.md`, `CLAUDE.md` e `APPEND_SYSTEM.md`. Passaram 4 testes
  novos e os 52 testes contratuais existentes, além de `py_compile` e
  `git diff --check`. A regressão integral iniciou 303 testes, mas terminou com
  12 falhas e 181 erros ambientais porque `pdflatex` não está instalado;
  nenhuma dependência global foi instalada e esse limite foi registrado sem
  atribuí-lo às ferramentas novas.

- 2026-09-01 — Iniciada a camada auxiliar de contexto/handoff para IA. A
  hipótese é que inventário content-addressed, introspecção estrutural,
  histórico Git/ADR e deltas desde a última sessão fornecem contexto suficiente
  sem concatenar aproximadamente 0,9 MB de fontes e testes. A incerteza
  inevitável é semântica: nenhuma ferramenta determinística consegue substituir
  uma descrição humana de decisões; por isso o encerramento de sessão exigirá
  resumo estruturado da IA e manterá um fallback automático apenas factual.
  Não haverá rede, chamada de modelo, alteração do Prime Agent global nem
  execução do pipeline científico.

- 2026-08-14 — Correção final restrita de M7 concluída: publicação atômica
  integralmente read-only, verificação canônica do `GateReport`, contratos de
  evidência matemática e os 13 gates locais foram cobertos por ataques e pela
  suíte completa de 192 testes. Champion, Pareto e rejected foram conferidos
  por hash e permaneceram inalterados; M8 não foi iniciado.

- 2026-08-14 — Correção final restrita de M7 iniciada: o mesmo verificador
  operacional do `GateReport` será aplicado após a execução e imediatamente
  antes da transição; a publicação não fará `chmod` após o `rename`; evidência
  matemática será um contrato canônico ligado a run/ciclo/base/candidato,
  claim e receipt; e os gates reconstruirão estado, proveniência,
  dependências, assets, referências e entrypoint LaTeX. Hipóteses: contratos
  locais fechados podem representar aprovação matemática auditável sem chamar
  modelos; ausência ou ambiguidade de evidência reprova. Incerteza: ferramentas
  LaTeX locais podem faltar, caso em que o gate falha fechadamente. M8,
  champion, Pareto e rejected não serão alterados.

- 2026-08-14 — Correção final de M7 em curso: a hipótese de trabalho é que o
  contrato publicado por M6 (recibo absoluto em
  `state/orchestration/<run>/receipts/<sha256>/artifact.json`, inclusive bytes
  com quebra final) é a única origem aceitável para pacotes e propostas. A
  incerteza remanescente é a disponibilidade dos executáveis locais de
  compilação/renderização; sua ausência deverá reprovar o gate, nunca ser
  mascarada por adapter. O escopo não inclui M8, promoção, Pareto persistido ou
  disposição de versões.

- 2026-08-14 — Correção cirúrgica de M7 iniciada sobre `6f9e8b2`, após
  precheck limpo, leitura dos handoffs M6/M7 e suíte local. O escopo corrige
  somente integridade da árvore, receipts/síntese, publicação write-once,
  gates locais e a ponte mínima de estado; nenhum trabalho de M8 é autorizado.
- 2026-08-14 — Complemento corretivo de M7: a síntese agora exige os bytes
  canônicos das propostas aceitas e os compromete (hash, dependências,
  validações e ordem) no recibo congelado. A inspeção/cópia de árvore aceita
  diretórios reais e alvos aninhados, mas recusa raiz ou componente symlink,
  hardlink, FIFO, tipos especiais e colisões normalizadas. Gates recusam
  evidência por link, timeout/duração inválida e saída excessiva. Foram
  adicionadas regressões locais para essas fronteiras; M8 não foi iniciado.
- 2026-08-14 — Fechamento da correção M7: dependências precisam pertencer ao
  conjunto aceito, o recibo de síntese é relido por contenção antes de um retry
  e fault injection cobre as fronteiras antes/depois do rename. A verificação
  local segmentada executou 183 testes M0–M7 sem skips novos; M8 permanece
  fora de escopo.

- 2026-08-14 — M7 iniciado após precheck limpo do checkpoint M6 `f5ec8ae`,
  seu ancestralidade em `HEAD` e suíte local aprovada. O escopo é estritamente
  síntese dos cinco pacotes, merge isolado, challenger write-once e gates
  locais; não inclui júri, diagnóstico, decisão ou disposição de versões.
- 2026-08-14 — M7 concluído: `M7Pipeline` congela cinco pacotes canônicos,
  constrói challenger isolado por operações estruturadas e publica somente em
  `versions/challengers/`; `run_gates` revalida a árvore e mantém matemática
  inconclusiva sem evidência. Champion, Pareto e rejected não são escritores
  M7.

- 2026-08-12 — M0: diretório validado, Git inicializado, versão e superfícies
  públicas do Prime Agent auditadas sem credenciais ou runtime.
- 2026-08-12 — M0.5 iniciado: documentação integralmente relida e comparada à
  sequência canônica dos Prompts 01–13.
- 2026-08-12 — M0.5 concluído: arquitetura, marcos, decisões e política de
  dependências alinhados; verificações textuais de cardinalidade registradas.
- 2026-08-12 — M0.6 concluído: paths canônicos completados, ordem merge → gates
  → júri → decisão → finalizador fixada e `SHIFT` diferenciado de `RUN`; nenhum
  artefato de implementação foi criado.
- 2026-08-12 — M1 iniciado: adotados YAML declarativo para configuração, JSON
  Schema Draft 2020-12 para contratos de dados e testes locais sem rede ou
  chamadas de modelo.
- 2026-08-12 — M1 concluído: scaffold canônico materializado; configurações,
  papéis, rubrica e schemas validados; 12 testes locais passaram sem rede,
  instalação, Prime Agent ou chamadas de modelo.
- 2026-08-13 — M2 corretivo iniciado: a implementação parcial será auditada
  contra recuperação, atomicidade, locks, integridade e contenção; nenhum
  marco posterior será iniciado.
- 2026-08-13 — M1.1 iniciado: revisão contratual anterior ao estado durável,
  sem implementar transições, ingestão, orquestração, merge ou júri.
- 2026-08-13 — M1.1 concluído: M00 fixado em `RUN`; contratos condicionais de
  tarefas, candidatos, departamentos, diagnóstico, júri, decisão, run, evento e
  snapshot validados com 46 testes no `.venv/bin/python`.
- 2026-08-13 — M2 iniciado: será implementado exclusivamente o núcleo local de
  estado durável, sem chamadas de modelo, agentes, rede ou dependências novas.
- 2026-08-13 — M2 concluído: log JSONL append-only encadeado, snapshots
  derivados, checkpoint, lock por execução, STOP, recuperação conservadora e
  idempotência foram validados por 13 testes dedicados e 59 testes locais no
  total; M3 não foi iniciado.
- 2026-08-13 — M2 correção final iniciada: auditoria encontrou replay
  semântico incompleto e append direto não recuperável; a correção permanece
  limitada ao M2, sem iniciar M3.
- 2026-08-13 — M2 correção final concluída: replay reaplica as regras de
  transição, ciclo, pausa e terminalidade; o JSONL usa commit por temporário,
  `fsync`, rename, sincronização de diretório quando suportada e verificação.
  Os 46 testes contratuais, 18 testes M2 e 64 testes locais passaram; M3 não
  foi iniciado.
- 2026-08-13 — M2 correção contratual final iniciada: a auditoria demonstrou
  que a API aceitava campos estruturais inválidos e que replay aceitava versão
  de schema forjada. A correção validará integralmente o evento antes do
  commit e durante replay, sem dependência nova e sem iniciar M3.
- 2026-08-13 — M2 correção contratual final concluída: `record()` rejeita
  parâmetros inválidos antes do lock/commit, e replay aplica todos os campos
  fechados e limites de `event.schema.json` mesmo para cadeias recalculadas.
  Os 46 testes contratuais, 30 testes M2 e 76 testes locais passaram; M3 não
  foi iniciado.
- 2026-08-13 — M3 concluído: preflight offline valida entrada e ZIP seguro,
  preserva o original por SHA-256, extrai baseline rastreável e publica v0000
  só após `SOURCE_READY`. Cinco testes M3 usam fixture local e a suíte completa
  passou com 81 testes; sem rede, modelo, OCR automático, dependência nova ou
  Prime Agent.
- 2026-08-13 — M3 correção final iniciada: auditoria independente demonstrou
  TOCTOU de PDF/ZIP, publicação parcialmente irrecuperável, idempotência sem
  verificação de integridade, ausência de transições M2 e métricas SOURCE_READY
  tautológicas. A correção fica estritamente no M3, com staging congelado,
  recuperação conservadora, event log canônico e testes adversariais locais;
  M4 continua bloqueado.
- 2026-08-13 — M3 correção final concluída: PDF e ZIP são congelados e
  revalidados antes de qualquer ferramenta; publicação por estágio/rename é
  recuperável e o log registra NEW → INGESTED → SOURCE_READY com chaves
  determinísticas. Idempotência agora revalida árvores, manifests, hashes e
  ausência de symlinks. SOURCE_READY mede cobertura, inventários e amostra
  visual; LaTeX reconstruído é escapado e compilado isoladamente. M4 não foi
  iniciado.
- 2026-08-13 — M3 correção cirúrgica anterior concluída: o manifesto de `v0000`
  satisfaz o schema de candidato; o original é publicado e o evento `INGESTED`
  é persistido antes de extração, renderização e gate. Todos os oito diretórios
  gerenciados rejeitam symlinks, LaTeX só é aceito após inspeção estática
  conservadora, e cada árvore de staging sofre `fsync` integral antes do
  rename. Passaram 46 testes contratuais, 30 testes M2, 14 testes M3 e 90 na
  suíte completa; M4 não foi iniciado.
- 2026-08-13 — M3 correção final de identidade iniciada: a identidade imutável
  passará a incluir PDF, presença/ausência e hash/tamanho de `source.zip`, e o
  modo de fonte. Eventos, retomada, retorno idempotente e champion serão
  confrontados contra essa mesma identidade; ZIP com qualquer `.tex` truncado
  cairá em `PDF_ONLY_RECONSTRUCTION`. A contagem final será registrada após a
  suíte completa; M4 não será iniciado.
- 2026-08-13 — M3 correção final de identidade concluída: `INGESTED` e
  `SOURCE_READY` registram a identidade integral; toda retomada, idempotência e
  champion a confere. Inclusão, remoção ou troca de `source.zip` falha fechada,
  e qualquer membro `.tex` inválido impede `SOURCE_ZIP`. Passaram 46 testes de
  contratos, 30 de M2 e 22 de M3: 98 na suíte completa; M4 não foi iniciado.
- 2026-08-13 — M3 correção de proveniência de fallback concluída: quando LaTeX
  inválido força `PDF_ONLY_RECONSTRUCTION`, o `ingestion-manifest.json` ainda
  preserva SHA-256 e tamanho do `source.zip` recebido, sem publicar
  `latex-source`. A suíte completa manteve 98 testes aprovados; M4 não foi
  iniciado.
- 2026-08-13 — Portabilidade M3: será incluído um bootstrap explícito para
  Debian/Ubuntu que verifica Python 3.11+, Poppler e LaTeX, instala somente os
  pacotes de sistema ausentes mediante `sudo`, e cria o ambiente virtual local
  com as versões de `requirements-dev.txt`. Prime Agent continua fora do
  escopo, por ser opcional e uma instalação global.
- 2026-08-13 — M4 concluído: os 21 prompts compilam deterministicamente de
  núcleos Markdown verificados por SHA-256; contexto é fechado pelo
  `AgentTask`, overlay YAML é versionado e registrado, e `AgentProposal` e
  `DepartmentPacket` são validados pelos schemas existentes. Seis testes M4 e
  a suíte completa de 104 testes passaram localmente, sem modelos, Prime
  Agent, rede ou dependências novas.
- 2026-08-13 — Correção contratual M4 concluída: catálogo, caminho e papel
  são vinculados rigidamente; overlays têm escopo contido, grafo acíclico e
  listas válidas; `prompt_version` identifica o conteúdo composto; e schemas
  validam formatos. Onze testes M4 e a suíte completa de 109 testes passaram,
  sem modelos, Prime Agent, rede ou dependências novas.
- 2026-08-13 — Correção contratual M4 adicional concluída: a API pública de
  identidade aceita apenas schemas de saída canônicos e rejeita escapes,
  aliases e symlinks nas raízes e arquivos de prompts e schemas. Treze testes
  M4 e a suíte completa de 111 testes passaram localmente.
- 2026-08-13 — M5 concluído: blackboard JSONL append-only com claims
  content-addressed, grafo de impacto e planejador puro de RUN/CHECK/SHIFT/
  FREEZE foram implementados. Cobertura obrigatória para prova (W22),
  finalização (W51/W53), dependências envelhecidas e checkpoint de orçamento
  são locais e determinísticos. Oito testes M5 e 119 testes na suíte completa
  passaram, sem rede, modelos, Prime Agent ou dependências novas.
- 2026-08-14 — Segunda correção cirúrgica de M5 concluída: `manager_view`
  aceita exclusivamente os cinco `DepartmentPacket` canônicos, em ordem,
  validados integralmente pelo schema com `FormatChecker`; W22 só é coberto
  quando o impacto matemático o exigir; e o ciclo 0 mantém gerentes e focais
  em `RUN`, preservando verificadores críticos em `CHECK`. Os 15 testes M5 e
  os 126 testes da suíte completa passaram localmente, sem dependências novas,
  chamadas a modelos, Prime Agent, rede ou início de M6.
- 2026-08-14 — Terceira correção cirúrgica de M5 concluída: o ciclo 0 une
  impactos e cobertura obrigatória aos focais mínimos, preservando W22/W51/W53
  e demais trabalhadores atingidos; verificadores críticos têm precedência
  sobre o fallback `RUN`; checkpoints declaram obrigatórios ausentes; e M00
  recusa DepartmentPackets de execução, ciclo, base ou `packet_id`
  incompatíveis. Os 17 testes M5 e os 128 testes da suíte completa passaram
  localmente, sem dependências novas, chamadas a modelos, Prime Agent, rede ou
  início de M6.
- 2026-08-14 — M6 iniciado: a integração será limitada a adaptadores locais e
  simulação determinística. O adaptador real somente encapsula as superfícies
  documentadas (`rlm`, `agent_message` e profundidade por sessão); nenhum
  runtime, modelo ou agente real será iniciado nesta etapa.
- 2026-08-14 — M6 concluído: a prova offline cobriu admissão idempotente,
  receipts fora de ordem/duplicados, falha, silêncio, cancelamento, isolamento
  raiz/neto e consolidação de `DepartmentPacket`; a suíte completa aprovou 136
  testes.
- 2026-08-14 — Correção cirúrgica de M6 iniciada: a integração será vinculada
  exclusivamente ao `ingest-<sha256>` canônico em `SOURCE_READY`. O plano M5
  content-addressed, journal append-only por execução, workspaces sem symlink,
  contexto RLM por ator e receipts com matriz de parentesco serão a única fonte
  de continuidade. Não haverá chamadas ao Prime Agent, modelos ou M7.
- 2026-08-14 — Correção cirúrgica de M6 concluída localmente: bootstrap
  revalida o baseline M3 e usa o hash do champion; o journal M6 encadeado
  projeta snapshots por ciclo; a árvore M00→Sxx→Wxx é contextual e reentrante;
  planos, tarefas, views, prompts e receipts são validados e duráveis. A
  cobertura adversarial permanece offline; M7 não foi iniciado.
- 2026-08-14 — Segunda correção cirúrgica de M6 iniciada: corrigir contratos
  Prime, ciclo/PLAN particionado, pausa/stop canônicos, receipts imutáveis,
  dependência S20, contexto real e admissão concorrente; M7 permanece fora de
  escopo e não haverá runtime, rede ou chamadas de modelo.
- 2026-08-14 — Segunda correção cirúrgica de M6 concluída: handles Prime são
  estritamente `rlm_child_id`/`name`/`session_dir`/`model`; PLAN, activation e
  projeções são imutáveis e particionados por ciclo; intent de spawn é
  journalizado antes da admissão. Receipts congelam bytes content-addressed e
  pacotes departamentais são write-once/reenviáveis. Pausa/retomada têm IDs de
  passagem, stop cancela antes de remover, e S30/S40 técnicos ficam bloqueados
  sem revisão S20 válida. Passaram 24 testes M6 locais e 152 testes na suíte
  completa; M7 não foi iniciado.
- 2026-08-14 — Terceira correção cirúrgica de M6 concluída: o checkpoint
  pausado do M5 é aceito somente no formato fechado realmente emitido pelo
  planejador, sem admissão de filhos; `receipt()` faz uma única leitura dos
  bytes, valida e congela exatamente essa leitura antes de journalizar, e toda
  consolidação usa exclusivamente a cópia imutável verificada. Transições de
  pausa, retomada, parada e ciclo confirmam primeiro o DurableStore canônico e
  reconciliam retries sem eventos duplicados. Passaram 31 testes M6 e 159 na
  suíte completa com `jsonschema` real, além de `py_compile`; M7 não foi
  iniciado.
- 2026-08-14 — Quarta e última correção cirúrgica de M6 iniciada: validar o
  checkpoint pausado por recálculo exato das constraints M5 e tornar retries
  de receipts e `DepartmentPacket` independentes do workspace mutável, sempre
  a partir da cópia congelada autoritativa. Não haverá Prime, modelos, rede ou
  trabalho de M7.
- 2026-08-14 — Quarta e última correção cirúrgica de M6 concluída: o
  checkpoint pausado recalcula e compara exatamente as sete constraints e o
  `reason` do M5; retries de receipt e `DepartmentPacket` validam e restauram
  somente bytes congelados autoritativos. Passaram 34 testes M6, 162 na suíte
  completa com `jsonschema` real e `py_compile` em `src` e `control`; M7 não
  foi iniciado.
- 2026-08-14 — Quinta correção cirúrgica de M6 iniciada: fechar antes de toda
  persistência ou admissão a validação do `ActivationPlan` contra o subconjunto
  exato emitível pelo planejador M5, incluindo ordem, entradas, custos, saídas,
  modos, cobertura obrigatória e checkpoints pausados. Runtime, receipts,
  retries, reconciliação e `DurableStore` permanecem fora de escopo; M7 não
  será iniciado.
- 2026-08-14 — Quinta correção cirúrgica de M6 concluída: `_plan()` agora
  aceita apenas a forma canônica publicamente emitível pelo M5, antes de
  `PLAN`, DurableStore, workspace ou spawn: 21 papéis ordenados, entradas
  compartilhadas e determinísticas, custos/saídas/modos emitidos e os únicos
  grupos obrigatórios válidos. Planos pausados são recalculados sem permitir
  ausência obrigatória inventada. Passaram 36 testes M6 e 164 na suíte
  completa com `jsonschema` real, além de `py_compile`; M7 não foi iniciado.
- 2026-08-14 — Sexta correção cirúrgica de M6 concluída: a validação do
  checkpoint pausado não infere finalização apenas porque W53 está ativo; o
  artefato M5 permanece o vínculo de proveniência. W22 continua exigindo o
  grupo de prova, e os únicos grupos declarados continuam vazio, prova,
  finalização ou união. A matriz pública M5 aprovou 966 planos (ciclos 0/1/3,
  todos os papéis, combinações críticas, ambos estados de finalização e todos
  os limites restritivos). Passaram 43 testes M6 e 171 na suíte completa com
  `jsonschema` real, além de `py_compile`; M7 não foi iniciado.
- 2026-08-28 — Milestone 08 (M8) concluído e endurecido com sucesso:
  avaliação cega externa por júri e meta-revisão implementadas com estrita
  separação operacional (adapters de teste `FakeJurorAdapter` e `FakeMetaReviewerAdapter`
  declarados `is_test_double=True`, e `evaluate_candidate()` impondo
  `allow_test_doubles=False` por padrão, falhando fechado com `EvaluationError`
  caso dublês de teste sejam injetados sem autorização explícita; CLI
  `scripts/01_external_evaluator.py` repassa autorização somente via `--test-mode`),
  vinculação semântica estrita dos vereditos à apresentação enviada (anti-replay,
  ordem bijetiva, matching de `comparison_id`, `order_seed`, `rubric_version` e
  `content_hashes`), verificação canônica de `GateReport` (`verify_gate_report`) e
  vinculação estrita com o evento ativo `GATES_PASSED` (exigindo `candidate_hash`
  idêntico sem fallback), publicação transacional write-once em staging com fsync
  individual de arquivos e diretórios antes e após `_harden_read_only`, rename atômico,
  fsync pós-rename do diretório pai, limpeza segura de staging read-only (`_cleanup_staging`),
  recuperação auditável preservando todos os 9 hashes de evidência, e manifesto de
  avaliação (`manifest.json`) com inventário de hashes. Novos schemas Draft 2020-12
  formalizados (`meta-verdict.schema.json`, `evaluation-report.schema.json`,
  `evaluation-manifest.schema.json`). Aprovados testes em `control/test_m8_evaluation.py`,
  `control/test_contracts.py` e na suíte de regressão (M0–M8) com 100% de sucesso.

- 2026-08-28 — Milestone 09 (M9) concluído com sucesso:
  detecção determinística de estagnação e refoco implementados através de módulos puros
  `article_loop.diagnosis` e `article_loop.refocus`, e CLIs finas `scripts/02_stagnation_detector.py`
  e `scripts/03_refocus_generator.py` (JSON-in / JSON-out).
  Reconstituição de séries históricas exclusivamente com ciclos fechados e artefatos válidos
  (GateReport, EvaluationReport, manifestos, claims e issues), com isolamento estrito anti-lookahead
  e verificação de integridade de hashes.
  Classificação determinística sob 7 estados canônicos (`EVOLVING`, `LOCAL_PLATEAU`, `GLOBAL_PLATEAU`,
  `OSCILLATING`, `REGRESSING`, `INCONCLUSIVE`, `TECHNICAL_FAILURE`) com precedência fechada,
  precedência intransponível do hard gate matemático (`correctness_math_pass == False`), janela móvel
  configurável (default 3 ciclos; janelas incompletas nunca inventam plateau) e normalização de papéis
  em `FREEZE` via denominador do activation map.
  Publicação transacional write-once de `Diagnosis` content-addressed (`diag-<sha256>`) em
  `state/diagnosis/<run_id>/c<cycle:04d>/` com permissões `0444`/`0555` e sincronização `fsync`.
  Transição de estado durável exclusivamente de `EVALUATED -> DIAGNOSED` registrada no `DurableStore`.
  Refoco autorizado exclusivamente para `LOCAL_PLATEAU`, `GLOBAL_PLATEAU` e `OSCILLATING`, gerando
  overlays filhos imutáveis e acíclicos em `prompts/overlays/<role_id>/<new_version>.yaml` e `RefocusPlan`
  em `state/refocus/<run_id>/c<cycle:04d>/`. No plateau global, são gerados exatamente dois ramos
  distintos (`exploitation` e `exploration`) com orçamentos e critérios de falsificação.
  Gravação atômica em `prompts/registry.json` com lock exclusivo de arquivo (`prompts/.registry.lock`),
  CAS, fsync e validação de grafo `PromptRegistry`. Proibição absoluta de edição de prompts imutáveis,
  overlays de `M00` ou ampliação de privilégios.
  Novos schemas Draft 2020-12 formalizados (`diagnosis-manifest.schema.json`, `refocus-plan.schema.json`).
  Aprovados 50 testes em `control/test_m9_diagnosis.py`, 51 testes M8, 52 testes
  de contrato e 299 testes na suíte integral de regressão (M0–M9), executada
  em 566.531s. O verificador M9 recompõe a classificação a partir do histórico
  comprometido e rejeita diagnósticos semanticamente forjados mesmo quando
  artefato, manifesto e evento são re-hashados. M10 permanece não iniciado.
