# Decisões arquiteturais

## ADR-001 — O repositório possui estado durável próprio

**Estado:** aceito em 2026-08-12.

Sessões, JSONL e artefatos do Prime Agent ajudam a executar e retomar trabalho,
mas não são a fonte de verdade do produto. O article-loop persistirá seus
próprios registros de execução, candidatos, evidências, votos cegos, gates,
promoções e fronteira Pareto em formato versionado e validado.

**Motivo:** sessões podem compactar, expirar, ser retomadas em outro contexto ou
não existir em uma reexecução local. Uma decisão científica precisa de trilha
de auditoria independente do fornecedor/runtime.

## ADR-002 — Topologia lógica 1 + 5 + 15 e profundidade RLM 2

**Estado:** aceito em 2026-08-12.

O gerente geral é a raiz na profundidade 0. Cinco subgerentes são filhos diretos
na profundidade 1. Cada subgerente pode criar no máximo três especialistas na
profundidade 2. A agenda é esparsa e pode executar somente um subconjunto.

**Motivo:** o limite instalado permite criação quando `depth < maxDepth`; definir
o máximo por sessão como 2 representa a topologia inteira e bloqueia uma camada
não solicitada. A configuração global fica proibida.

## ADR-003 — Mensagem curta, arquivo canônico

**Estado:** aceito em 2026-08-12.

Filhos retornam resumo e referência por `agent_message` compatível; análise,
evidência e recomendações completas vivem em arquivo imutável e schema-validado
do projeto.

**Motivo:** o retorno de `rlm()` é só handle e a semântica de `agent_message.mode`
é incompatível entre a documentação principal e o contrato empacotado. Arquivos
canônicos tornam a recuperação e a auditoria independentes da fila de mensagens.

## ADR-004 — Júri cego separado de autoria e promoção

**Estado:** aceito em 2026-08-12.

O júri recebe versões neutras de candidatos, sem identificação do papel autor,
ordem de criação ou status de champion. Votos e rubricas são gravados antes da
decisão de promoção. O gerente geral aplica a regra de decisão após verificar
o gate.

**Motivo:** evitar que a autoridade aparente do papel ou a incumbência do
champion contamine a avaliação.

## ADR-005 — Gates determinísticos locais antes de autonomia

**Estado:** aceito em 2026-08-12.

O produto terá verificadores locais, determinísticos e versionados. Gatilhos
`--autonomous-gate` do Prime Agent, se usados no futuro, apenas invocarão esses
verificadores já definidos e nunca substituirão o registro de gates do produto.

**Motivo:** autonomia e compactação são políticas de continuidade, não prova de
correção. A decisão mantém os testes reproduzíveis e limita custo.

## ADR-006 — Sem chamadas pagas, dependências ou runtime nesta fase

**Estado:** aceito em 2026-08-12.

Esta fase fica limitada a auditoria estática, documentação e inicialização Git.
Não haverá instalação, `/autonomous`, `/refine`, filho RLM, login, leitura de
credenciais ou chamada de modelo.

**Motivo:** requisito explícito de segurança, custo e preservação da instalação.

## ADR-007 — Arquitetura canônica dos Prompts 01–13

**Estado:** aceito em 2026-08-12.

O projeto fixa no Marco 0.5 os 21 papéis identificados, a ativação
RUN/CHECK/SHIFT/FREEZE, os 16 estados, as 9 ações de decisão, as 8 dimensões de
avaliação, os cinco scripts externos e a árvore de paths canônicos documentada
em `docs/architecture.md`.

**Decisão:** M1 e os marcos posteriores devem implementar esses contratos sem
renomeá-los ou deslocá-los. `PDF_ONLY_RECONSTRUCTION` é regime de ingestão, não
novo estado. `correctness_math` é gate duro não compensável. Agentes somente
propõem; merge é a única autoridade de escrita do challenger e nenhum agente
escreve diretamente no champion.

**Motivo:** a sequência dos Prompts 01–13 exige que a estrutura de coordenação,
recuperação, avaliação e finalização seja conhecida antes de existir código. A
decisão reduz ambiguidade entre departamentos, impede deriva de paths e mantém
as garantias de auditoria e custo da arquitetura esparsa.

## ADR-008 — Ordem transacional do pipeline

**Estado:** aceito em 2026-08-12.

**Decisão:** o pipeline segue obrigatoriamente propostas estruturadas,
consolidação departamental, síntese do gerente, merge em workspace isolado,
challenger imutável, gates determinísticos, júri cego, diagnóstico, decisão
canônica, finalizador transacional e destino de promoção, arquivo Pareto ou
rejeição. Merge é o único escritor do challenger e ocorre antes de gates e
júri. A decisão opera apenas sobre um challenger construído e avaliado.
`scripts/05_transactional_finalizer.py` não reconstrói nem modifica conteúdo:
revalida hashes e aplica atomicamente `PROMOTE`, `ARCHIVE_PARETO`, `REJECT`,
`FINALIZE` ou outra ação autorizada. Alterar conteúdo depois do júri exige nova
avaliação.

**Motivo:** separar construção, avaliação e commit impede promover bytes ou
conteúdo diferentes dos avaliados, preservando rastreabilidade e recuperação
atômica do ciclo.

## ADR-009 — Contratos declarativos e validação local do Marco 1

**Estado:** aceito em 2026-08-12.

**Decisão:** configurações e papéis são YAML; envelopes persistidos usam JSON
validado por JSON Schema Draft 2020-12. Cada schema é fechado a propriedades
desconhecidas, identifica sua versão e referencia contratos compartilhados
somente por caminhos relativos versionados. Os testes do scaffold usam apenas
validadores locais já disponíveis e não importam nem iniciam o Prime Agent.

AgentProposal registra evidências, operações, dependências, riscos e versão do
prompt, mas proíbe campos destinados a cadeia de raciocínio privada. A trilha
auditável guarda resultados e justificativas verificáveis, não deliberação
interna de modelos.

**Motivo:** contratos fechados detectam deriva cedo, referências relativas
mantêm o repositório reproduzível e a separação entre evidência e raciocínio
privado reduz risco de retenção indevida sem prejudicar auditoria.

## ADR-010 — Contratos condicionais antes do estado durável

**Estado:** aceito em 2026-08-13.

**Correção cirúrgica (2026-08-13):** alterações estruturadas são normalizadas
sem escolher entre `id`, `kind` e `location`: todos os valores escalares de
cada campo participam da correspondência. Assim, seção, equação e referência
são preservadas inclusive quando `kind` e `location` coexistem. O fecho de
dependências continua bidirecional e transitivo.

O blackboard aceita somente `run_id` simples (`[A-Za-z0-9][A-Za-z0-9_.-]*`),
confina cada componente de `state/blackboard/<run_id>` à raiz resolvida e
rejeita qualquer symlink nesses caminhos gerenciados. A leitura rejeita linha
sem newline ou JSON inválido. Por execução, um lock exclusivo envolve a leitura
de idempotência/conflito e o append; a linha é escrita completa, recebe
`flush`/`fsync` e o diretório é sincronizado. Linhas anteriores jamais são
reescritas.

O planejador usa severidade máxima do impacto, idade, alterações de
dependência, falhas e sinais de plateau/oscilação/diagnóstico como entradas
determinísticas. `RUN` é trabalho novo ou severidade alta; `CHECK` é validação
de prova/teorema, severidade baixa ou primeira falha; `SHIFT` tem precedência
para plateau, oscilação, diagnóstico solicitado ou falhas repetidas; `FREEZE`
significa ausência de chamada e tem tokens, tempo e saídas esperadas vazios.
W22 é obrigatório para teorema/prova e W51+W53 para finalização. Não há
truncamento: se qualquer limite por ciclo, departamento, gerente, papel,
tokens ou tempo impedir cobertura obrigatória, o plano é `paused` com
checkpoint explícito. A seleção e a serialização do mapa são canônicas.

`manager_view` aceita exatamente os cinco pacotes, na ordem `S10`, `S20`,
`S30`, `S40`, `S50`, uma vez cada. Cada item é integralmente um
`DepartmentPacket` válido; `no_change` é seu status canônico, nunca um envelope
alternativo.

**Decisão:** tarefas distinguem subgerentes de especialistas; manifests de
baseline e challenger têm invariantes diferentes; vereditos representam uma
única apresentação cega entre exatamente dois candidatos; e cada ação de
decisão exige sua evidência própria. RunManifest, Event e Snapshot expressam
somente invariantes estruturais necessárias ao Prompt 02, sem antecipar regras
de transição.

M00 permanece sempre em `RUN` e não é destinatário de AgentTask. Contratos
fechados rejeitam campos que revelem champion, autoria ou equipe no júri.

**Motivo:** impedir estados impossíveis e combinações ambíguas antes que sejam
persistidos, mantendo a implementação futura de transições separada dos
formatos canônicos.

## ADR-011 — Log encadeado e snapshot derivado para o estado durável

**Estado:** aceito em 2026-08-13.

**Decisão:** M2 usa um JSONL append-only por `run_id`, com sequência, hash do
evento anterior e hash canônico do próprio evento. O snapshot é derivado do
log, nunca a fonte de verdade, e é reconstituível após interrupção. A escrita
de snapshot/checkpoint usa arquivo temporário no mesmo filesystem, `flush`,
`fsync`, `rename` e nova verificação de hash; o log é protegido por lock
exclusivo por execução. A chave idempotente é única por log e uma repetição com
o mesmo conteúdo devolve o evento existente.

`PAUSED` guarda o estado de retomada e retorna somente a ele; `FINALIZED` e
`TECHNICAL_FAILURE` são terminais. O arquivo `control/STOP` bloqueia o começo
de novas operações, mas não interrompe uma operação que já adquiriu o lock,
preservando sua atomicidade.

## ADR-012 — Recuperação conservadora e identificadores de execução seguros

**Estado:** aceito em 2026-08-13.

**Decisão:** o `run_id` é um identificador simples, não um caminho: aceita
apenas caracteres alfanuméricos, hífen, sublinhado e ponto, recusando
`..`, `/`, `\`, caracteres nulos ou espaços. Qualquer arquivo ou diretório de
estado (`state/events/<run_id>.jsonl`, `state/snapshots/<run_id>/`,
`state/checkpoints/<run_id>/`, `state/locks/<run_id>.lock`) é estritamente
confinado à raiz do repositório; symlinks nesses caminhos gerenciados são
proibidos e rejeitados.

Se o event log estiver ausente, a recuperação falha; se estiver vazio, devolve
`NEW`; se a cadeia de hashes estiver corrompida, truncada ou ilegível, falha de
modo explícito e auditável, sem criar eventos fictícios nem tentar adivinhar o
estado. O lock exclusivo é liberado em qualquer terminação normal ou excepcional
e uma execução que encontre lock ativo falha fechada com erro de concorrência.

**Motivo:** evitar travessia de diretórios, sobrescrita acidental fora da árvore
gerenciada e corrupção silenciosa do estado por processos concorrentes ou dados
malformados.

## ADR-013 — Ingestão PDF offline, identificação imutável e publicação atômica do Marco 3

**Estado:** aceito em 2026-08-13.

**Decisão:** M3 preserva o PDF de entrada como leitura imutável e identifica o
candidato inicial exclusivamente por SHA-256 do arquivo original. A publicação
usa `artifacts/original/<sha256>/artigo.pdf`, com modo `0444`, `fsync` e
`os.replace`. O extraction manifest registra tamanho, hash, páginas, modo de
fonte e hashes derivados; a transição do estado durável registra `INGESTED` e,
após a compilação/validação do baseline, `SOURCE_READY`.

Se `source.zip` estiver presente e passar por inspeção segura (sem symlinks, sem
travessia `..`, sem arquivos executáveis ou absolutos), ele é a fonte prioritária
(`SOURCE_ZIP`). Caso contrário, a execução opera em `PDF_ONLY_RECONSTRUCTION`
gerando baseline estruturado a partir do texto extraído.

**Motivo:** garantir reproducibilidade criptográfica e auditabilidade desde o
primeiro byte, impedindo mutação in-place do artigo de entrada.

## ADR-014 — Identidade composta de ingestão e contenção rígida

**Estado:** aceito em 2026-08-13.

**Decisão:** a identidade de ingestão vincula PDF, presença/ausência, tamanho e
SHA-256 de `source.zip`, modo de fonte e baseline. Qualquer alteração ou troca
de `source.zip` durante uma mesma execução falha fechada. Todos os diretórios de
ingestão rejeitam symlinks, exigem caminhos normalizados e sincronizam metadados
antes de emitir `SOURCE_READY`.

## ADR-015 — Compilação determinística de prompts e isolamento de overlays do Marco 4

**Estado:** aceito em 2026-08-13.

**Decisão:** M4 compila os 21 prompts canônicos a partir de templates Markdown
imutáveis em `prompts/immutable/`, context-bound via `AgentTask` e overlays YAML
registrados em `prompts/overlays/`. Cada overlay é identificado por SHA-256 no
`prompts/registry.json`, possui escopo fechado e grafo acíclico de versões.

A compilação é determinística, offline e não executa código arbitrário nem
expande variáveis fora do contexto tipado. M00 não aceita overlays que ampliem
sua autoridade.

## ADR-016 — Blackboard append-only, grafo de impacto e ativação pura do Marco 5

**Estado:** aceito em 2026-08-13.

**Decisão:** M5 implementa a memória de trabalho do ciclo como um log JSONL
append-only em `state/blackboard/<run_id>/claims.jsonl`, indexando afirmações
científicas por `claim_id` content-addressed (`claim-<sha256>`).

O planejador de ativação calcula deterministicamente o grafo de impacto
(seções, equações, referências, severidade e dependências) e emite a matriz de
modos `RUN`/`CHECK`/`SHIFT`/`FREEZE`. W22 é obrigatório quando há impacto em
teoremas/provas; W51+W53 são obrigatórios para finalização. Se o orçamento ou
tempo impedir a cobertura obrigatória, o ciclo emite plano pausado com
checkpoint explícito.

## ADR-017 — Hierarquia RLM offline, journals encadeados e receipts do Marco 6

**Estado:** aceito em 2026-08-14.

**Decisão:** M6 encapsula a hierarquia RLM em adaptadores (`PrimeRLMAdapter` e
`FakeRLMAdapter`), permitindo testes e simulações completamente determinísticos
sem chamadas de modelo ou rede. O orquestrador emite intenções de spawn em
journal encadeado por ciclo (`state/orchestration/<run_id>/journal.jsonl`),
confinando workspaces em `workspaces/<run_id>/cycle-XXXX/<role_id>/`.

Propostas de especialistas chegam via receipts assinados com SHA-256 e são
consolidadas pelos subgerentes em `DepartmentPacket` imutáveis. S30 e S40 com
impacto técnico exigem revisão prévia de S20.

## ADR-018 — Síntese atômica, isolamento de merge e 13 gates determinísticos do Marco 7

**Estado:** aceito em 2026-08-14.

**Decisão:** M7 constrói um único challenger por ciclo em workspace isolado,
aplicando atomicamente as operações aceitas na síntese do gerente geral. O
challenger é publicado de forma estritamente read-only (`0444`/`0555`) em
`versions/challengers/<candidate_id>/`.

Treze gates determinísticos locais são executados de forma fail-closed:
`latex_compiles`, `bibtex_valid`, `math_correctness`, `references_resolved`,
`layout_margins`, `proof_integrity`, `claim_coverage`, etc. O gate
`correctness_math` é duro e sua reprovação impede a promoção do challenger.
Nenhuma escrita em `versions/champion/` ou `versions/pareto/` ocorre no M7.

## ADR-019 — Verificação canônica do GateReport e evidência matemática estrita

**Estado:** aceito em 2026-08-14.

**Decisão:** `GateReport` é persistido antes do evento `GATES_PASSED`, contendo o
inventário completo de gates, saídas, tempos, hashes de entrada e códigos de
saída. A evidência matemática requer vínculo criptográfico com o `claim_id`,
`proposal_id`, método de prova e verificação auditável.

## ADR-020 — Isolamento de avaliação cega em júri e meta-revisão do Marco 8

**Estado:** aceito em 2026-08-28.

**Decisão:** M8 avalia o challenger aprovado nos gates comparando-o contra o
champion atual em apresentações cegas pareadas (ordem A/B e B/A) distribuídas a
um júri de 3 jurados especializados (`juror-math`, `juror-contrib`, `juror-clarity`).

Cada jurado emite dois vereditos cegos independentes. A consistência de
inversão (ausência de viés posicional) e a meta-revisão são calculadas
deterministicamente. Se houver divergência ou veto do meta-revisor, o
resultado é inconclusivo e o challenger não se torna elegível para promoção.

## ADR-021 — Transacionalidade de avaliação e proteção contra dublês

**Estado:** aceito em 2026-08-28.

**Decisão:** A avaliação é publicada atomicamente em
`state/evaluations/<run_id>/cXXXX/` com permissões `0444`/`0555` e `fsync`. O
evento durável `EVALUATED` vincula os 9 hashes dos artefatos produzidos.

Adaptadores com `is_test_double=True` falham fechados em modo operacional
(`allow_test_doubles=False`), garantindo que dublês de teste nunca sejam
usados silenciosamente em produção.

## ADR-022 — Detecção de estagnação e 7 classificações de progresso do Marco 9

**Estado:** aceito em 2026-08-28.

**Decisão:** M9 analisa a série histórica de ciclos fechados e classifica o
progresso em uma de 7 categorias canônicas: `EVOLVING`, `LOCAL_PLATEAU`,
`GLOBAL_PLATEAU`, `OSCILLATING`, `REGRESSING`, `INCONCLUSIVE` e `TECHNICAL_FAILURE`.

A classificação é pura, determinística e anti-lookahead. A perda de hard gate
matemático gera `REGRESSING` imediato. Janelas incompletas nunca inventam
plateau.

## ADR-023 — Refoco adaptativo e CAS no registry de overlays

**Estado:** aceito em 2026-08-28.

**Decisão:** Refoco é autorizado exclusivamente para `LOCAL_PLATEAU`,
`GLOBAL_PLATEAU` e `OSCILLATING`. O refoco gera novos overlays YAML acíclicos em
`prompts/overlays/<role_id>/<new_ver>.yaml` com instruções focais e links de
rollback.

A gravação no `prompts/registry.json` utiliza lock exclusivo
(`prompts/.registry.lock`), atomicidade via arquivo temporário e validação de
grafo. Modificar prompts imutáveis ou criar overlays para M00 é estritamente
proibido.

## ADR-024 — Transição de estado de diagnóstico e isolamento do M10

**Estado:** aceito em 2026-08-28.

**Decisão:** M9 realiza exclusivamente a transição durável `EVALUATED -> DIAGNOSED`.
Nenhuma decisão de promoção (`PROMOTE`), arquivamento (`ARCHIVE_PARETO`) ou
rejeição (`REJECT`) é tomada no M9; essa autoridade pertence exclusivamente à
política de compensação e finalizador transacional do Marco 10.

## ADR-025 — Verificação semântica estrita do diagnóstico

**Estado:** aceito em 2026-08-28.

**Decisão:** `verify_published_diagnosis()` recalcula a classificação a partir
do histórico comprometido e dos parâmetros `window_size` e `mde`. Diagnósticos
forjados ou adulterados falham fechados mesmo que seus hashes internos tenham
sido recalculados.

## ADR-026 — Protocolo determinístico de contexto e histórico para IAs

**Estado:** aceito em 2026-09-01.

**Decisão:** `scripts/ai_context.py` publica o snapshot de contexto `AI_CONTEXT.md`
no início de cada sessão de IA. `scripts/ai_history.py` mantém o ledger
`docs/ai_sessions.jsonl` e o histórico `docs/AI_HISTORY.md` no encerramento da
sessão.

Os artefatos de IA não pertencem à máquina de estados científicos, não alteram
candidatos, gates ou decisões e operam de forma 100% offline, determinística e
sem dependências externas.
