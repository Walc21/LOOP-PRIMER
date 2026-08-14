# ExecPlan vivo — article-loop

## Objetivo

Construir uma integração verificável para revisão iterativa de artigo matemático
sem alterar o núcleo do Prime Agent. A arquitetura canônica possui 21 papéis,
execução esparsa, estado durável próprio, júri cego, gates determinísticos,
champion, challengers e arquivo Pareto.

A fonte normativa de arquitetura é `docs/architecture.md`; a autoridade da
integração Prime Agent continua sendo `docs/compatibility.md`.

## Estado atual

- Atualizado em 2026-08-14.
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
| M8 | avaliador externo cego em júri | pendente | rubrica cega não expõe autoria, ordem ou status de champion |
| M9 | detecção de progresso e refoco | pendente | estagnação e refoco são produzidos pelos scripts canônicos |
| M10 | política de compensação e finalizador | pendente | finalizador revalida hashes e aplica ações atômicas sem modificar o challenger avaliado |
| M11 | comandos e configuração do Prime Agent | pendente | recursos `.prime/agent/` seguem a compatibilidade instalada |
| M12 | orçamento, observabilidade e execução prolongada | pendente | limites, custos e recuperação são observáveis sem alterar globais |
| M13 | testes de sistema e entrega | pendente | sistema é reproduzível, auditável e entrega sem alterar o PDF original |

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
