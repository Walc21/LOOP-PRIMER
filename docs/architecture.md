# Arquitetura canônica — article-loop

## Aceitação de sistema M13

`control/m13_fixture.py` compõe as APIs canônicas em diretórios sintéticos
temporários. Não é um segundo orquestrador de produção. A entrada tem bytes
fixos e só as fronteiras externas Prime/inferência/júri são substituídas.
`control/test_m13_system_delivery.py` cobre a cadeia até disposição, veto duro,
cegueira, recuperação, replay, concorrência e adulteração.

`article_loop.delivery.verify_delivery` é a fronteira independente de auditoria
somente leitura. Reutiliza validadores de ingestão, síntese/receipts, gates,
avaliação, diagnóstico e decisão; confere a publicação do finalizador e a
ligação budget/route/output/receipt M6 quando routed. Não cria decisões nem
reexecuta inferência. A revalidação M9 aceita explicitamente um evento
`FINALIZATION_APPLIED` do mesmo ciclo para essa auditoria; a autorização de
refoco continua limitada a `DIAGNOSED`.

O comando é `python3 scripts/m13_system_check.py`; detalhes, matriz de aceitação
e limites estão em `docs/m13-system-acceptance.md`. Os 21 papéis, 16 estados,
9 ações e schemas científicos permanecem os mesmos.

## Escopo e imutabilidade do contrato

O article-loop revisará iterativamente um artigo matemático com evidência
reproduzível, preservando o PDF original e mantendo histórico de decisões,
candidatos e avaliação cega. Este documento fixa para os Prompts 01–13 o
catálogo de papéis, caminhos, estados, ações, dimensões de avaliação e scripts
externos. M1 materializou configuração e schemas dentro desses contratos sem
inventar ou renomear papéis, estados, ações ou paths. M10 materializou a
política fechada de disposição e o finalizador transacional sem mudar os
artefatos M0--M9.

Os caminhos canônicos foram fixados nos Marcos 0.5 e 0.6 e o scaffold foi
materializado no Marco 1. Diretórios de runtime contêm somente sentinelas
`.gitkeep`; nenhum estado de execução, PDF, segredo ou resultado foi criado.

## Entrada, fontes e preservação

A entrada principal é `input/inbox/artigo.pdf`. Antes de qualquer extração,
reconstrução ou compilação futura, o sistema registra caminho, tamanho e
SHA-256 e conserva o PDF sem sobrescrita, anotação, recompressão ou
substituição.

Se `input/inbox/source.zip` estiver presente, ele é a fonte preferencial após
inspeção segura de conteúdo, licença e integridade. Sem fonte aceita, a execução
opera no regime `PDF_ONLY_RECONSTRUCTION`: ele é modo de ingestão, não estado
canônico. O baseline editável reconstruído deve passar por validação antes de
permitir `SOURCE_READY`; nenhuma melhoria começa antes de `SOURCE_READY`.

## Catálogo exato de 21 papéis

| ID | Papel | Departamento | Profundidade RLM | Responsabilidade focal |
|---|---|---|---:|---|
| M00 | gerente geral | direção | 0 | agenda, impacto, gates, síntese, decisão e ciclo |
| S10 | subgerente estrutural/auditorial | estrutural/auditorial | 1 | consolida a auditoria estrutural |
| W11 | resumo e introdução | estrutural/auditorial | 2 | propõe correções de resumo e introdução |
| W12 | arquitetura lógica | estrutural/auditorial | 2 | propõe correções de organização e dependências lógicas |
| W13 | contribuições e conclusão | estrutural/auditorial | 2 | propõe correções de contribuições e conclusão |
| S20 | subgerente de verificação matemática | verificação matemática | 1 | consolida validação técnica e matemática |
| W21 | definições e hipóteses | verificação matemática | 2 | verifica definições, notação e hipóteses |
| W22 | teoremas e provas | verificação matemática | 2 | verifica teoremas, lemas e provas |
| W23 | cálculos e reprodutibilidade | verificação matemática | 2 | verifica cálculos e reprodutibilidade |
| S30 | subgerente de fortalecimento matemático | fortalecimento matemático | 1 | consolida propostas de fortalecimento |
| W31 | enunciados e constantes | fortalecimento matemático | 2 | propõe melhora de enunciados e constantes |
| W32 | generalizações | fortalecimento matemático | 2 | propõe generalizações justificadas |
| W33 | aplicações e exemplos | fortalecimento matemático | 2 | propõe aplicações e exemplos |
| S40 | subgerente textual/semântico | textual/semântico | 1 | consolida propostas textuais e semânticas |
| W41 | ortografia e gramática | textual/semântico | 2 | propõe correções linguísticas |
| W42 | precisão semântica | textual/semântico | 2 | propõe precisão de significado e escopo |
| W43 | coesão e estilo acadêmico | textual/semântico | 2 | propõe coesão e estilo acadêmico |
| S50 | subgerente de formatação/PDF | formatação/PDF | 1 | consolida conformidade de apresentação |
| W51 | LaTeX e referências | formatação/PDF | 2 | propõe correções de LaTeX e referências |
| W52 | equações, figuras e tabelas | formatação/PDF | 2 | propõe correções de apresentação matemática |
| W53 | conformidade do PDF | formatação/PDF | 2 | verifica conformidade do PDF final |

A profundidade futura máxima é 2: M00 cria os cinco subgerentes; cada
subgerente cria somente seus três trabalhadores; trabalhadores são folhas. A
sessão raiz usará `/rlm-max-depth 2`, sem `--global`, somente após autorização
específica para executar o Prime Agent.

### Dependências obrigatórias e autoridade de escrita

- Alterações matemáticas propostas por S30 retornam para S20 antes de síntese ou
  merge.
- Alterações de S40 com possível efeito técnico retornam para S20 antes de
  síntese ou merge.
- S50 não possui autoridade para introduzir mudança semântica; devolve essa
  necessidade a M00 e ao departamento responsável.
- Agentes produzem propostas e evidência; somente o merge escreve no challenger.
- Nenhum agente escreve diretamente no champion.

## Ativação esparsa

M00 está sempre em `RUN` e não pode receber `CHECK`, `SHIFT` ou `FREEZE`. No
primeiro ciclo auditável, os cinco departamentos
participam: S10, S20, S30, S40 e S50 recebem trabalho. Seus trabalhadores são
ativados somente conforme a cobertura focal necessária. Nos ciclos seguintes,
o grafo de impacto determina quais departamentos e trabalhadores participam.

| Modo | Significado |
|---|---|
| RUN | papel ativo que recebe tarefa focal e, em execução autorizada, pode gerar proposta ou evidência |
| CHECK | revisa proposta, dependência ou gate existente sem assumir promoção |
| SHIFT | exploração limitada de estratégia alternativa, generalização ou reformulação motivada por plateau, oscilação ou diagnóstico; não é apenas reexecutar RUN |
| FREEZE | fica inativo no ciclo e não gera chamadas de modelo, subagentes ou trabalho especulativo |

`FREEZE` é o mecanismo primário de economia: sem impacto não há chamada de
modelo. `CHECK` não autoriza alteração no challenger; produz apenas evidência
para merge ou nova ativação. `SHIFT` é diferente de `RUN`: ele explora de forma
limitada uma alternativa motivada por plateau, oscilação ou diagnóstico, em vez
de repetir a tarefa ativa.

## Árvore canônica do projeto

```text
article-loop/
├── .prime/
│   └── agent/
│       ├── prompts/
│       └── skills/
│           └── article-loop/
├── config/
│   ├── roles/
│   ├── rubrics/
│   └── schemas/
├── input/
│   └── inbox/
├── artifacts/
│   ├── original/
│   ├── extracted/
│   └── rendered/
├── prompts/
│   ├── immutable/
│   ├── overlays/
│   └── registry.json
├── state/
│   ├── events/
│   ├── snapshots/
│   ├── checkpoints/
│   ├── claims/
│   ├── issues/
│   ├── decisions/
│   ├── inference/<run_id>/{routes,receipts}/
│   └── locks/
├── versions/
│   ├── champion/
│   ├── challengers/
│   ├── pareto/
│   └── rejected/
├── workspaces/
├── reports/
├── logs/
├── control/
├── scripts/
├── bin/
│   ├── start-prime.sh
│   ├── preflight.sh
│   └── check.sh
└── docs/
```

A árvore foi materializada no Marco 1. Os caminhos canônicos não podem ser
inventados silenciosamente; cada marco pode criar arquivos dentro dos
diretórios canônicos somente quando for o responsável por eles. M1 criou
configurações, schemas e stubs inertes; não moveu entrada, estado, versões ou
prompts para paths novos.

- `.prime/agent/prompts/` está reservado aos templates Markdown do M4.
- `.prime/agent/skills/article-loop/` contém o scaffold inerte da skill Python.
- `artifacts/rendered/` contém PDFs e páginas renderizadas derivadas.
- `prompts/registry.json` registra hashes e versões dos prompts.
- `state/locks/` contém locks por `run_id`.
- `bin/` contém `bin/start-prime.sh`, `bin/preflight.sh` e `bin/check.sh`.

### Paths explícitos da árvore

`.prime/agent/`, `.prime/agent/prompts/`, `.prime/agent/skills/`,
`.prime/agent/skills/article-loop/`, `config/roles/`, `config/rubrics/`,
`config/schemas/`, `input/inbox/`, `artifacts/original/`,
`artifacts/extracted/`, `artifacts/rendered/`, `prompts/immutable/`,
`prompts/overlays/`, `prompts/registry.json`, `state/events/`,
`state/snapshots/`, `state/checkpoints/`, `state/claims/`, `state/issues/`,
`state/decisions/`, `state/inference/`, `state/locks/`, `versions/champion/`,
`versions/challengers/`, `versions/pareto/`, `versions/rejected/`,
`workspaces/`, `reports/`, `logs/`, `control/`, `scripts/`, `bin/`,
`bin/start-prime.sh`, `bin/preflight.sh`, `bin/check.sh` e `docs/`
são paths canônicos materializados no M1; somente seu conteúdo operacional
permanece reservado aos marcos responsáveis.

## Máquina de estados canônica

Os únicos estados de ciclo são exatamente os 16 abaixo:

```text
NEW
INGESTED
SOURCE_READY
CYCLE_PLANNED
DEPARTMENTS_RUNNING
SYNTHESIS_READY
CANDIDATE_BUILT
GATES_PASSED
EVALUATED
DIAGNOSED
DECIDED
COMMITTING
CYCLE_COMPLETE
PAUSED
FINALIZED
TECHNICAL_FAILURE
```

`PDF_ONLY_RECONSTRUCTION` não adiciona 17º estado. O event log registrará cada
transição, causa, artefatos, versão de entrada e actor responsável. `PAUSED`,
`FINALIZED` e `TECHNICAL_FAILURE` suspendem ou encerram progressão até ação
permitida.

M10 executa somente a sequência `DIAGNOSED -> DECIDED -> COMMITTING`. A ação
autorizada fecha em `CYCLE_COMPLETE`, `PAUSED`, `FINALIZED` ou
`TECHNICAL_FAILURE`. Durante a revalidação M10, o `DIAGNOSED` anterior continua
vinculado por hash; o sucessor só pode ser `DECIDED` ou `COMMITTING` para o
mesmo ciclo.

## Ações canônicas de decisão

As únicas ações de decisão são exatamente as nove abaixo:

```text
PROMOTE
ARCHIVE_PARETO
REJECT
REFOCUS_AND_CONTINUE
CONTINUE_UNCHANGED
REQUEST_EXTRA_JUDGMENT
PAUSE
FINALIZE
ABORT_TECHNICAL
```

Ação e merge são separados: o merge constrói o challenger antes de gates e do
júri; a ação escolhe o destino somente após o challenger estar construído e
avaliado. `PROMOTE` exige gates e avaliação registrados; `ARCHIVE_PARETO`
preserva candidato não dominado; `ABORT_TECHNICAL` registra falha técnica sem
alegar conclusão.

## Avaliação cega e gates duros

Cada `JuryVerdict` compara exatamente dois identificadores neutros em uma única
apresentação A/B ou B/A, sem autoria, ordem de criação ou condição de champion.
A consistência entre apresentações será calculada depois por `comparison_id` e
`juror_id`. As dimensões são exatamente:
criação ou condição de champion. As dimensões são exatamente:

```text
correctness_math
proof_completeness
logical_coherence
scientific_contribution
semantic_precision
clarity
format_integrity
reproducibility
```

`correctness_math` é gate duro: não pode ser compensado por estilo, clareza,
contribuição ou qualquer outra dimensão. Gates locais, determinísticos e
versionados registram entrada, saída, código de saída e evidência. Gate aprovado
não prova propriedade que não verifica.

## Versões, merge e Pareto

O champion é o candidato aprovado vigente; challengers são candidatos imutáveis
construídos pelo merge em workspace isolado; rejeitados e não dominados continuam
rastreáveis. Merge é o único escritor do challenger e ocorre antes de gates e
do júri. A decisão opera exclusivamente sobre um challenger já construído e
avaliado. Antes de `ARCHIVE_PARETO`, M10 compara todas as oito dimensões sob
`correctness_math=true` com cada referência Pareto publicada. A `Decision`
registra quais referências dominam ou são dominadas pelo candidato, e o
finalizador revalida a mesma relação sob lock; evidência histórica não é apagada.

## Scripts externos canônicos

Os cinco scripts externos são parte fixa da arquitetura:

```text
scripts/01_external_evaluator.py
scripts/02_stagnation_detector.py
scripts/03_refocus_generator.py
scripts/04_compensation_policy.py
scripts/05_transactional_finalizer.py
```

M8--M10 implementaram esses paths sem trocar nomes nem criar scripts
concorrentes com a mesma autoridade de decisão. Em especial,
`scripts/05_transactional_finalizer.py` não poderá reconstruir nem modificar o
challenger: apenas revalidará hashes e aplicará atomicamente `PROMOTE`,
`ARCHIVE_PARETO`, `REJECT`, `FINALIZE` ou outra ação autorizada.

`scripts/04_compensation_policy.py` recebe JSON limitado ou argumentos locais,
revalida M7--M9 e publica uma única `Decision` canônica contendo o hash da
política, relação Pareto quando aplicável e checkpoint técnico limitado quando
aplicável. `scripts/05_transactional_finalizer.py` é o único escritor de
disposição: usa lock por execução, journal sincronizado, `fsync`, `os.replace`
e CAS de `versions/champion/current.json` antes de publicar o receipt.

`FINALIZE` é uma exceção deliberadamente mais estrita: além de GateReport,
diagnóstico, candidato e policy hash, exige três `FinalGateReport` imutáveis,
um por W22, W51 e W53. Eles atestam respectivamente `correctness_math`,
`manifest_integrity` e `pdf_valid`, e todos apontam pelos hashes SHA-256 ao
mesmo manifesto de challenger, PDF em `artifacts/rendered/` e `FinalReport`
canônico. A política e o finalizador revalidam esse pacote; evidência ausente,
mutável, não canônica ou divergente bloqueia a finalização. Depois de um crash
após o receipt e antes do evento, a retomada rederiva o mesmo receipt e só
publica evento/checkpoint pendentes, sem reaplicar o efeito.

### Comandos operacionais M11

M11 expõe as APIs locais por uma única ponte
`scripts/article_loop_command.py`, em JSON-in/JSON-out, para bootstrap,
preflight, ciclo, status, checkpoint, pausa, retomada, parada e finalização.
Cada comando aceita somente seus campos fechados, valida raiz e identificadores
e delega a uma API já existente; nenhum payload escolhe `FakeRLMAdapter` ou
altera a configuração global do Prime Agent.

Os nove templates Markdown vivem diretamente em `.prime/agent/prompts/`, pois a
descoberta de templates não é recursiva. `bin/check.sh` valida as superfícies
locais sem rede. `bin/start-prime.sh` é dry-run por padrão; no modo live exige
autorização explícita, configuração/limites locais, ausência de `control/STOP`,
preflight M3 e `prime-agent` no `PATH`, encaminhando somente `--skill` e
`--prompt-template`, opções confirmadas na compatibilidade registrada. Como o
binário não está disponível nesta sessão e o orçamento versionado é
fail-closed, o launcher não inicia Prime Agent nem modelo. Nenhum
`.prime/agent/settings.json` é criado sem confirmação direta do formato da
versão instalada.

### Orçamento e observabilidade M12

M12 adiciona `BudgetLedger`, um ledger local por execução em
`state/budgets/<run_id>.jsonl`. Reservas, admissões, receipts, reconciliações,
incertezas, progresso, alertas e controles são eventos append-only com hash
SHA-256, sequência, idempotência e lock por run. Antes de qualquer fronteira
consumidora, o ledger compromete a estimativa; saldo confirmado e todas as
reservas abertas participam do mesmo check atômico. Resultado desconhecido
permanece reservado como `UNCERTAIN`, e excesso reconciliado bloqueia novas
admissões.

Os limites são expressos em tokens inteiros não negativos e também cobrem ciclo,
departamento, papel, modelo, chamadas, filhos concorrentes, retries, wall time,
ciclos e julgamentos extras. O status JSON/humano expõe uso confirmado,
reservado e comprometido, saldo por limite, reservas, filhos, última melhoria,
diagnóstico, próxima ação, alertas e nível de assurance. Deadlines e duração
monotônica são retomados a partir dos eventos duráveis; `STOP` bloqueia novas
reservas e `PAUSE` conserva as existentes.

`StructuredLogger` grava somente campos operacionais de uma allowlist, com
hash-chain, rotação por tamanho, fsync e rejeição de payload não allowlisted.
Credenciais, cookies, auth, prompts completos, artigo integral e mensagens
privadas ficam fora do log. Os tetos `calibration` e `overnight` permanecem
desabilitados na configuração versionada; perfil e autorização live não são
herdados entre runs. M12 não altera a máquina de estados, critérios
científicos, gates, conteúdo, Prime Agent ou defaults fail-closed de M11.

### Routing de inferência M12.5

M12.5 acrescenta uma camada aditiva entre um `AgentTask` já validado e a
fronteira de consumo. `ModelRegistry` valida o inventário versionado em
`config/budgets.yaml`; `ModelRouter` escolhe deterministicamente um target por
papel, capacidades, limites, fallback e independência; `InferenceRuntime`
coordena a operação. Papel lógico, provider e modelo são identidades distintas.
M6 continua sendo o único dono da topologia RLM, da profundidade e da troca de
mensagens; o adaptador Prime conserva `spawn(prompt, name)` porque seleção de
modelo por filho não foi confirmada na instalação disponível.

A ordem transacional é: decisão de rota write-once, reserva M12, admissão,
chamada única ao backend, receipt operacional sem prompt/resposta integral e
reconciliação. As decisões vivem em
`state/inference/<run_id>/routes/<route_decision_hash>.json`; os receipts, em
`state/inference/<run_id>/receipts/<call_id>.json`. Ambos são vinculados por
hash e publicados atomicamente sob lock por execução. Receipt existente é a
fonte de recuperação: uma retomada reconcilia sem repetir a chamada. Falha após
admissão sem receipt permanece `UNCERTAIN` e não libera saldo automaticamente.

Os defaults são fechados: `inference.enabled`, `allow_local`, `allow_remote` e
`allow_paid` começam falsos e não há targets versionados ativos. O backend local OpenAI-compatible aceita somente
loopback explícito, timeout e resposta limitada, sem redirects ou proxies; o
fake exige autorização booleana de teste e nunca pode executar em modo live.
`FREEZE` não cria rota, reserva, receipt nem chamada. Júri pode exigir grupo de
independência diferente do produtor, e escalation somente ocorre por reason
code fechado, tentativa limitada e nova decisão persistida — nunca por retry
silencioso.

### Ligação end-to-end dual M12.5.1 — Phase A

M12.5.1 introduz uma escolha explícita por departamento, sem criar novos
papéis. Um departamento `prime` segue integralmente o contrato M6 existente.
Um departamento `routed` recebe um Sxx local, determinístico e persistente que
admite os mesmos Wxx no journal M6; somente esses trabalhadores passam por
`InferenceRuntime`. Misturar trabalhadores routed dentro de um departamento
Prime não é permitido. Nos dois caminhos, a convergência é idêntica:

```text
AgentTask + closed M5 view
-> compiled role prompt
-> ContextMaterializer
-> privacy filter
-> ModelRouter
-> monetary/token reservation
-> one backend call
-> validated scientific JSON
-> durable output tree
-> M6 workspace/agent-proposal.json
-> Orchestrator.receipt()
-> existing DepartmentPacket consolidation
-> M7 synthesis, gates, M8 jury and Decision unchanged
```

`ContextMaterializer` aceita apenas locators já presentes na `AgentTask` e na
view fechada. Caminhos precisam permanecer dentro da raiz sem symlinks; árvores
são enumeradas em ordem e só arquivos textuais autorizados entram no contexto.
O PDF binário é deliberadamente omitido: o conteúdo consultável vem do texto
extraído por M3. Cada item registra locator, origem e SHA-256, e o conjunto
produz `context_hash`. O limite do target inclui contexto, overhead e output;
overflow falha antes do router. O conteúdo materializado nunca entra em logs,
route decisions ou inference receipts.

A política por run é `deny_remote`, `scoped_remote` ou `full_remote`.
`deny_remote` elimina targets não locais; os outros modos continuam restritos
a locators explícitos da tarefa — `full_remote` não é autorização para varrer o
repositório. O modo e `context_hash` ficam vinculados à rota, ao output e ao
receipt. Como o hash da configuração integral pertence ao ledger e à
autorização, mudar a política no mesmo run invalida a retomada autorizada.

Saída válida é publicada primeiro em
`state/inference/<run>/outputs/<call_id>/<output_sha256>.json`, acompanhada de
manifesto hash-bound, por staging sincronizado e rename atômico. Só seus bytes
exatos chegam ao workspace M6. Isso permite recuperar quedas entre output,
receipt, reconciliação e receipt M6 sem reinferência; ausência de resultado
conhecido após admissão permanece `UNCERTAIN`, e divergência de hash falha
fechada.

O ledger aplica moeda e custo como inteiros. O teto padrão é 10.000.000
microunits USD por run. Um target pago só é elegível se tiver preços inteiros
por milhão de tokens, `allow_paid`, autorização com o mesmo teto/moeda e
reserva conservadora anterior ao backend. Usage conhecido recalcula o custo a
partir dos tokens; usage desconhecido conserva a reserva. Overrun é registrado
e bloqueia nova admissão. A capacidade está implementada, mas execução,
targets, rotas e paid/live permanecem desabilitados na configuração versionada.

M8 não é contornado por esta camada. Seus jurors e meta-reviewer continuam
entrando pela interface de avaliação já existente. A política de routing passa
a poder exigir independência pelo identificador exato de `model`; o modo
legacy por `independence_group` permanece interpretável. O inventário completo
das superfícies model-driven e da fronteira M8 está em
`docs/model-driven-surfaces.md`.

### M13.1 — Identidade de avaliador routed

Jurors e meta-reviewers routed não são adicionados aos 21 papéis lógicos RLM.
Uma chamada de avaliação usa `role_id: null` e declara
`actor_kind: "evaluator"`, `actor_id` canônico e `routing_role_id` de um papel
existente. `actor_id` identifica quem avalia; `routing_role_id` é somente a
autoridade que seleciona a política e a rota. Assim, a topologia RLM e a conta
por papel não são alteradas, enquanto os limites globais, de ciclo,
departamento, modelo, chamadas, tempo e custo permanecem aplicáveis.

A identidade do avaliador e sua autoridade de routing entram na requisição,
decisão e receipt. Receipts de avaliador seguem o schema fechado `1.2.0`; os
schemas `1.0.0` e `1.1.0` mantêm exatamente a forma legada quando os campos de
avaliador não existem. O modelo emite apenas o payload científico de jury/meta;
o LOOP compõe e valida a identidade e o envelope de protocolo. Output durável
e receipt permitem reexecutar um julgamento já reconciliado sem nova inferência.

### Ferramentas auxiliares de handoff para IA

`scripts/ai_context.py`, `scripts/ai_history.py` e o módulo compartilhado
`scripts/ai_handoff_common.py` são ferramentas de manutenção do repositório,
não scripts científicos externos. Eles não pertencem à máquina de estados, não
emitem ações canônicas e não possuem autoridade sobre PDF, champion,
challengers, gates, júri ou finalização.

O primeiro publica `AI_CONTEXT.md` a partir do inventário atual e do histórico.
O documento é portável entre clones: não persiste caminho absoluto, branch ou
commit do checkout. Ele resume o inventário e referencia
`docs/ai_snapshot.json` para o detalhe content-addressed, sem incorporar o
README público nem duplicar integralmente `AGENTS.md`.
O segundo mantém `docs/AI_HISTORY.md`, apoiado pelo ledger
`docs/ai_sessions.jsonl` e pelo snapshot `docs/ai_snapshot.json`. Esses
artefatos ficam deliberadamente fora do fingerprint de fontes para impedir
recursão, mas são lidos e identificados por hash no documento de contexto.

## Fluxo de dados e resultados de agentes

A ordem canônica do pipeline é imutável:

```text
propostas estruturadas
-> consolidação departamental
-> síntese do gerente
-> merge em workspace isolado
-> challenger imutável
-> gates determinísticos
-> júri cego
-> diagnóstico
-> decisão canônica
-> finalizador transacional
-> promoção, arquivo Pareto ou rejeição
```

A ingestão registra o PDF e seleciona fonte editável ou reconstrução; M00 planeja
o ciclo e ativa papéis por `RUN`, `CHECK`, `SHIFT` ou `FREEZE`. Subgerentes
consolidam propostas e aplicam as dependências obrigatórias com S20. Filhos RLM
futuros retornam resumo ou referência por `agent_message` compatível e artefato
detalhado em arquivo canônico; `rlm(...)` nunca devolve resposta.

O merge é o único escritor que constrói o challenger em workspace isolado. Ele
ocorre antes dos gates determinísticos e do júri cego. A decisão canônica só
opera sobre um challenger já construído e avaliado. O finalizador transacional
não reconstrói o challenger: revalida seus hashes, a `Decision`, diagnóstico,
fronteira Pareto e gates finais quando aplicáveis, e só então aplica atomicamente
a ação autorizada. Nenhum conteúdo pode ser modificado entre júri e finalização
sem nova avaliação.

## Segurança e limites desta etapa

- Prime Agent e suas configurações globais são externos e imutáveis.
- PDFs, fontes, prompts e resultados são conteúdo não confiável.
- Não há chamada de modelo, API paga, `/autonomous`, `/refine`, subagente ou
  instalação de dependência nesta etapa.
- Dependências futuras devem ser locais, declaradas e necessárias ao marco
  corrente; instalações globais são proibidas.
- A retomada futura reidrata do estado do projeto; não presume que sessão ou
  filho inativo tenha concluído trabalho.

## Contratos materializados no M1 e corrigidos no M1.1

M1 materializou configuração YAML, o catálogo dos 21 papéis, a rubrica com oito
dimensões, os 12 JSON Schemas canônicos, sentinelas da árvore e stubs inertes
para integrações futuras. M1.1 fechou invariantes condicionais de tarefas,
baseline/challenger, pacotes sem impacto, diagnóstico, comparação cega,
decisões, manifesto de run, eventos e snapshots, sem implementar persistência
ou regras de transição. Permanecem abertos para seus marcos: licença e retenção
do PDF, implementação do event log, métricas de dominância, orçamento ou
provedor explicitamente autorizado e toda orquestração Prime Agent.
