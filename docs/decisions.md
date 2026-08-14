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
somente letras ASCII, algarismos, ponto, hífen e sublinhado, sem `.` ou `..`.
O store verifica o sinal `control/STOP` depois de adquirir o lock. Linhas JSONL
sem terminador, JSON inválido, eventos incompletos e hashes ou encadeamentos
incompatíveis são corrupção e impedem replay ou nova escrita; não há reparo
silencioso do log. Um snapshot parcial nunca é fonte de verdade: um arquivo
temporário abandonado antes do rename é descartável e, após rename, o snapshot
é sempre revalidado e pode ser reconstruído integralmente do JSONL.

**Motivo:** impedir que uma entrada de caminho escape do repositório, que um
STOP concorra com o início de uma operação ou que uma recuperação transforme
perda/corrupção de evidência em histórico aparentemente válido.

## ADR-013 — Replay semântico e commit transacional do event log

**Estado:** aceito em 2026-08-13.

**Decisão:** o replay valida também a máquina de estados: o evento inicial é
exatamente `NEW`, transições posteriores preservam origem, ciclo e regras de
pausa/retomada, e estados terminais não admitem sucessores. Cada append lógico
é preparado como a versão integral do JSONL em arquivo temporário no mesmo
filesystem, com flush e `fsync`, seguido de `os.replace`, `fsync` do diretório
quando disponível e verificação do arquivo final. Temporários órfãos não são
fonte de estado; corrupção do log canônico nunca é reparada silenciosamente.

**Motivo:** hashes válidos provam integridade criptográfica, mas não que a
história representa uma execução autorizada. A substituição atômica evita que
uma queda exponha uma linha parcial como evento commitado e mantém a repetição
idempotente recuperável após falhas antes ou depois do rename.

## ADR-014 — Validação estrutural integral do evento antes de commit e no replay

**Estado:** aceito em 2026-08-13.

**Decisão:** o store implementa localmente, sem dependência de runtime, todos
os invariantes de `config/schemas/event.schema.json` que se aplicam ao evento:
versão `1.1.0`, campos fechados, identificadores não vazios, chave de
idempotência de até 256 caracteres, `run_id` seguro, inteiros não negativos
sem aceitar booleanos, data ISO 8601 com fuso, payload objeto, hashes de
artefatos únicos e SHA-256 hexadecimal minúsculo, e hashes anterior/próprio
conformes à posição no log. A API `record()` valida os parâmetros expostos
antes de adquirir o lock ou alterar o JSONL; o replay reaplica a mesma
validação estrutural além da cadeia criptográfica e da semântica de estados.

**Motivo:** uma cadeia de hashes recalculada só comprova consistência dos bytes;
não torna um evento fora do contrato canônico confiável. Aplicar o schema nos
dois limites impede tanto commits locais inválidos quanto logs forjados.

## ADR-015 — Ingestão M3 conservadora, offline e versionada

**Estado:** aceito em 2026-08-13.

**Decisão:** a ingestão aceita exatamente `input/inbox/artigo.pdf`, sem
symlinks que escapem da raiz, calcula seu SHA-256 e somente produz derivados
em diretórios identificados por esse hash. Poppler fornece metadados, texto,
páginas renderizadas e imagens; a classificação digital/híbrido/escaneado é
heurística documentada no manifest. OCR permanece opcional e explicitamente
desligado por padrão: ausência de texto em PDF escaneado gera issues em vez de
símbolos inferidos. `source.zip` é inspecionado sem extração insegura e só é
preferido se contiver fontes LaTeX regulares válidas.

O gate `SOURCE_READY` compara páginas, cobertura textual, inventários de
equações e referências e uma amostra visual local segundo limites declarados
em `config/gates.yaml`. A promoção para `versions/champion/v0000` ocorre por
publicação atômica somente após o gate; reingestão do mesmo hash é idempotente
e qualquer divergência de artefato já publicado falha fechada.

**Motivo:** a fonte PDF é evidência imutável, enquanto uma reconstrução é
necessariamente incompleta. Separar as duas e registrar lacunas torna a etapa
reproduzível sem fingir que extração/OCR prova equivalência matemática.

## ADR-016 — Correção final de integridade e recuperação da ingestão M3

**Estado:** aceito em 2026-08-13.

**Decisão:** a ingestão congela PDF e `source.zip` em staging antes
de qualquer inspeção ou transformação; SHA-256 e tamanho serão calculados nos
bytes congelados e novamente verificados. Artefatos e champion serão preparados
em staging, publicados por rename com sincronização e verificados depois da
publicação. A retomada só aceitará conjuntos completos, sem symlinks e com
manifests/hashes mutuamente consistentes; qualquer divergência falhará fechada.

O `run_id` é derivado do SHA-256 integral, e o DurableStore registra
idempotentemente NEW → INGESTED → SOURCE_READY. SOURCE_READY só será emitido
após gate calculado por métricas reais e documentadas; LaTeX e ZIP serão
tratados como dados não confiáveis.

O gate mede texto por página, candidatos versus inventários de equações e
referências e uma amostra visual determinística; limites de PDF/ZIP também
são declarados em `gates.yaml`. A reconstrução trata cada linha como texto não
confiável, escapa caracteres LaTeX e compila com `-no-shell-escape` em diretório
isolado.

**Motivo:** impedir que um byte diferente do validado seja publicado, que uma
queda transforme publicação parcial em sucesso implícito, ou que um manifest
autodeclarado substitua evidência verificável.

## ADR-017 — Limites de escrita e ordem de evidência da ingestão M3

**Estado:** aceito em 2026-08-13.

**Decisão:** antes de qualquer escrita, a ingestão valida a raiz e cada
diretório gerenciado, recusando qualquer componente symlink e qualquer destino
resolvido fora da raiz. O original congelado é publicado e sua evidência
(caminho, tamanho, SHA-256 e modo de fonte) é registrada em `INGESTED` antes de
extração, renderização ou gate; uma falha de `SOURCE_READY` portanto preserva
o estado `INGESTED` e o original íntegro. A retomada usa as chaves idempotentes
existentes, sem repetir eventos.

`source.zip` só é preferido quando a fonte LaTeX UTF-8 passa inspeção estática
conservadora: comentários e escapes são respeitados, chaves são balanceadas,
há exatamente um ambiente `document` e a pilha de ambientes fecha sem
truncamento. Se essa confirmação falhar, o ZIP não é fonte e a ingestão usa
`PDF_ONLY_RECONSTRUCTION` com issue explícita. Antes de cada rename de staging,
todos os arquivos regulares e o diretório são sincronizados.

**Motivo:** registrar a evidência imutável antes de qualquer transformação,
impedir escrita por links de diretório, não aceitar TeX estruturalmente
truncado e reduzir a janela de perda após publicação atômica.

## ADR-018 — Identidade completa de `source.zip` na execução M3

**Estado:** aceito em 2026-08-13.

**Decisão:** a identidade imutável de uma ingestão contém SHA-256 do PDF,
presença de `source.zip`, e, quando presente, SHA-256 e tamanho do ZIP, além de
`source_mode`. Embora o `run_id` continue derivado do PDF, os eventos
`INGESTED` e `SOURCE_READY` carregam a identidade completa. Toda retomada e
todo retorno idempotente comparam a entrada atual, os eventos persistidos e o
`ingestion-manifest` do champion; adição, remoção ou alteração do ZIP causa
falha fechada.

Um projeto `SOURCE_ZIP` só pode copiar o ZIP inteiro quando todos os seus
membros `.tex` são UTF-8 e estruturalmente válidos. Se qualquer um não for,
todo o ZIP é tratado como não confirmado e a ingestão usa
`PDF_ONLY_RECONSTRUCTION` com issue explícita.

**Motivo:** impedir que artefatos e eventos de uma entrada sejam combinados com
um ZIP posterior e evitar que um projeto parcialmente truncado seja aceito.

## ADR-019 — Bootstrap portátil limitado ao ambiente local de ingestão

**Estado:** aceito em 2026-08-13.

**Decisão:** `bin/bootstrap-deps.sh` suporta Debian e Ubuntu. Ele detecta os
requisitos da ingestão M3 — Python 3.11+, módulo `venv`, Poppler
(`pdfinfo`, `pdftotext`, `pdftoppm`, `pdfimages`) e `pdflatex` — e solicita
`sudo` apenas se algum pacote de sistema estiver ausente. Em seguida, cria ou
reutiliza `.venv` no próprio repositório e instala as versões fixadas de
`requirements-dev.txt`.

O script não instala nem configura o Prime Agent: ele é opcional nesta etapa,
é global ao dispositivo e exige autorização própria. Sistemas que não sejam
Debian/Ubuntu falham com instruções claras, sem tentar inferir um gerenciador
de pacotes.

**Motivo:** o repositório deve poder ser copiado sem carregar ambientes locais,
mas a automação não pode ocultar instalações globais, variar silenciosamente
por distribuição ou ampliar o escopo da integração Prime Agent.

## ADR-020 — Prompts M4 imutáveis, content-addressed e compostos localmente

**Estado:** aceito em 2026-08-13.

**Decisão:** o núcleo global e os 21 núcleos de papel são arquivos Markdown
imutáveis em `prompts/immutable/`, identificados por SHA-256 no
`prompts/registry.json`. O compilador local verifica todos esses hashes antes
de compor, põe o prefixo estável obrigatoriamente em primeiro lugar e rejeita
papel, versão ou hash desconhecido. Um overlay é YAML versionado em
`prompts/overlays/<role_id>/<version>.yaml`, declara versão-pai, diagnóstico,
autor, evidência, escopo, hash e rollback, e só é aceito se também estiver no
registro e se seu conteúdo conferir. O rollback é um identificador de versão
anterior registrada, nunca uma alteração do núcleo.

O contexto de ciclo é uma lista fechada de campos de `AgentTask`; campos que
não forem explicitamente permitidos são bloqueados antes da composição. A
saída é sempre referenciada pelo schema canônico `AgentProposal` ou
`DepartmentPacket`. Os prompts solicitam conclusão, evidência, objeções e
justificativa concisa, sem cadeia de raciocínio privada. Eles proíbem
autoelogio, texto meta, alegações sem localizador e escrita direta no champion.
S30 e S40 exigem revisão de S20 para os efeitos definidos na arquitetura; S50
não recebe autoridade semântica.

**Complemento corretivo:** o registro é um catálogo fechado: `immutable` deve
conter exatamente `global` e os 21 IDs canônicos, com `global` apenas em
`immutable/global.md` e cada papel apenas em `immutable/<ROLE_ID>.md`.
Caminhos são arquivos regulares dentro da raiz esperada; redirecionar um papel
para o núcleo de outro falha. Overlays só podem existir para IDs canônicos não
gerenciais no caminho `overlays/<ROLE_ID>/<versão>.yaml`.

Antes da composição, `scope` do overlay precisa estar contido no da
`AgentTask`; `scope` e `evidence` são listas não vazias, sem strings vazias ou
duplicadas. M00 não aceita overlay enquanto não houver contrato explícito de
escopo autorizado. As ligações `parent_version` e `rollback` formam grafo
acíclico e falham fechadas.

`prompt_version` é uma identidade `sha256:<hex>` calculada por função pura
com hashes global e do papel, versão e hash do overlay (ou ausência explícita)
e nome e hash do schema de saída. A compilação exige coincidência exata. Toda
validação JSON Schema usa `FormatChecker`, inclusive timestamps.

**Garantia adicional de contenção:** schemas de saída são uma allowlist
explícita e a API pública de identidade os valida antes de construir caminhos.
O carregamento interno aceita apenas essa allowlist mais o schema de tarefa;
nomes com barras, `..`, caminhos absolutos, aliases e outros JSONs são
rejeitados. A raiz, `prompts/`, `prompts/registry.json`, `config/schemas/` e o
schema selecionado devem ser caminhos regulares contidos, sem symlinks.

**Motivo:** separar núcleo auditável, ajuste contextual e envelope de saída
impede deriva silenciosa de instruções, vazamento de contexto ou que uma
proposta seja confundida com alteração de candidato/champion.

## ADR-021 — Blackboard append-only e planejamento determinístico de M5

**Estado:** aceito em 2026-08-13.

**Decisão:** M5 introduz um blackboard local em JSONL, particionado por
execução e por ledger (`claims`, `issues`, `tasks`, `dependencies`, `evidence`
e `decisions`). As linhas nunca são alteradas; a projeção de um claim usa sua
última revisão, preservando todas as anteriores. O `claim_id` é derivado de
texto canônico, tipo, localização e hash da fonte, portanto é estável entre
reexecuções do mesmo snapshot. O grafo de impacto percorre dependências em
ambos os sentidos e traduz tipos/localizadores em seções, equações,
referências e papéis canônicos.

O planejador é uma função pura do snapshot, histórico e limites declarados.
Ele sempre inclui M00, emite exatamente cinco pacotes departamentais canônicos,
nunca cria tarefa para `FREEZE`, impõe cobertura por idade quando dependências
mudaram e reserva W22 somente para impacto que já o alcance (teorema, prova,
lema ou dependência matemática fechada) e W51+W53 para finalização. No ciclo
0, os targets de impacto e cobertura obrigatória são preservados por união;
M00 e os cinco subgerentes estão em `RUN`, e cada departamento sem trabalhador
alcançado recebe somente um focal padrão em `RUN`. Os outros especialistas
permanecem em `FREEZE`. `CHECK` de W22 ativado e W53 na finalização precede o
fallback do primeiro ciclo e não passa a `SHIFT` por sinal global. `SHIFT`
exige exploração ou reformulação explicitamente justificada. Orçamentos
excedidos, ou qualquer papel obrigatório ausente dos ativos, retornam um
checkpoint de pausa explícito com `missing_mandatory`; não há expansão ou
congelamento silencioso. As views removem contexto não necessário: um
especialista vê sua tarefa e evidência local; um subgerente vê propostas dos
filhos; M00 vê somente cinco DepartmentPackets canônicos, validados contra o
schema com `FormatChecker` e coerentes em `run_id`, `cycle_id`, `base_hash` e
`packet_id` único.

**Hipótese/limite:** o mapeamento semântico de alterações é deliberadamente
conservador por palavras-chave e tipos de localização até que M6 forneça
resultados de agentes. M5 não executa agentes, não atualiza a máquina de
estados e não persiste checkpoint no event log; ele apenas o devolve como dado
para a integração futura.

**Motivo:** separar memória auditável, decisão de ativação e execução futura
permite testar economia, cobertura e orçamento sem custo de modelo nem estado
implícito de sessão.

## ADR-022 — Orquestração RLM por receipts duráveis no M6

**Estado:** aceito em 2026-08-14.

**Decisão:** M6 introduz `PrimeRLMAdapter` e `FakeRLMAdapter` e uma
orquestração reentrante. `rlm()` é tratado exclusivamente como admissão: o
handle é persistido antes de qualquer avanço e não existe fan-in por
`gather`. Cada filho escreve em workspace isolado; sua única mensagem ao pai é
um receipt com caminho contido, SHA-256 e versão do schema. O pai valida o
receipt e o arquivo antes de consolidar. Somente o subgerente recebe receipts
dos três especialistas e somente ele envia um `DepartmentPacket` à raiz.

Nomes são determinísticos por execução, ciclo, departamento e papel. A
retomada lê o journal próprio, reaproveita admissões persistidas e cria apenas
filhos ainda ausentes. A profundidade 2 é uma pré-condição do adaptador real:
ela deve ser consultada e configurada pela sessão raiz com
`/rlm-max-depth 2`, sem `--global`, somente em execução autorizada. A prova
M6 usa exclusivamente o fake e importação local da skill.

**Complemento corretivo (2026-08-14):** M6 não cria uma execução paralela:
usa o `ingest-<sha256>` de M3 somente depois de revalidar PDF, manifesto de
ingestão, champion `v0000` e `SOURCE_READY`; `base_hash` é o `content_hash` do
manifest do champion. A projeção M6 vem de journal JSONL encadeado,
append-only, bloqueado por execução, sincronizado e validado; snapshots são
atômicos e derivados. O activation map M5 é copiado com hash antes da primeira
admissão e nunca é recalculado em retomada. M00 admite apenas Sxx, e cada Sxx
em sua própria sessão admite apenas seus Wxx. Handles, tarefa, view e prompt
content-addressed são journalizados antes do spawn seguinte. Receipts são
aceitos uma vez, sob lock, somente da matriz W→S/S→M, no workspace canônico e
com hash, schema, ciclo e base conferidos. A API pública não escolhe o fake:
live sem `PrimeRLMAdapter` explícito falha fechada; dry-run grava só preview.
Pausa, parada e finalização impedem mutações e o cancelamento é persistido
antes da remoção.

**Segundo complemento corretivo (2026-08-14):** a admissão é serializada por
`SPAWN_INTENT` sob o lock do journal; retomada reconcilia intent sem handle
somente entre os filhos diretos pelo nome determinístico. O contrato do handle
Prime exige `rlm_child_id`, `name`, `session_dir` e `model`; handles parciais
falham fechados. PLAN, activation, filhos e receipts são particionados por
ciclo e um novo PLAN só é aceito se a máquina canônica estiver em
`CYCLE_COMPLETE`. Receipts publicam uma cópia content-addressed imutável e a
consolidação relê/verifica esses bytes. Pausa/retomada têm passagens monotônicas
e são espelhadas no `DurableStore`; finalização continua exclusiva de M10.
`DepartmentPacket` é write-once e reenvia seus bytes persistidos depois de
falha de mensagem. Propostas técnicas de S30/S40 exigem revisão aprovada de
S20 no mesmo proposal/ciclo/base; sem ela o pacote é `blocked`. Um departamento
ativo sem trabalhador publica somente `no_change` com justificativa e evidência.
Tasks e views expõem locators imutáveis do baseline, extratos, rubrica e slice
local do blackboard; especialistas não recebem contexto global nem champion
editável. Replay valida tipo e payload de todos os eventos e falha fechado.

**Terceiro complemento corretivo (2026-08-14):** a aceitação de plano pausado
recálcula, na ordem do `ActivationPlanner._within_limits()`, todas as sete
constraints e o `reason` M5 a partir das entradas, orçamento, limites e
cobertura obrigatória; checkpoint meramente bem-formado não basta. Antes de
tocar o workspace, retry de receipt compara o envelope com o receipt já
aceito e valida somente os bytes congelados. Retry de consolidação usa o
packet congelado já aceito, restaura atomicamente o arquivo mutável apenas com
esses bytes quando necessário e reenvia ao pai o caminho e hash previamente
aceitos. Cópias congeladas ausentes, symlinkadas ou corrompidas falham
fechadas.
