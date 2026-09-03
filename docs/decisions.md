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

**Quarto complemento corretivo (2026-08-14):** antes de persistir `PLAN`,
alterar o `DurableStore`, criar workspace ou admitir filho, M6 aceita somente
o `activation_map()` que o `ActivationPlanner` M5 público pode emitir: os 21
papéis vêm uma vez na ordem canônica, campos de trabalho são tipados e não
vazios, entradas ativas são a mesma lista determinística e custos/saídas são
os fixos do papel. `FREEZE` continua integralmente vazio, M00 é `RUN`, e um
departamento não congela enquanto houver trabalhador ativo. A validação de
modo reconstitui regras do ciclo 0 que independem de histórico, inclusive
W22/W53 como `CHECK`. Cobertura obrigatória só admite os conjuntos M5 de
prova, finalização ou sua união; cada obrigatório deve estar ativo, e o
checkpoint pausado só pode declarar a saída efetivamente produzível pelo
planejador, impedindo que uma ausência inventada converta plano normal em
pausa.

**Quinto complemento corretivo (2026-08-14):** `activation_map()` não expõe
`finalization_requested`; portanto M6 não o infere de W53 ativo. No checkpoint
pausado, a presença de W53 por `Impact.roles` é compatível com
`mandatory_roles=[]`, enquanto um grupo de finalização declarado continua
exigindo S50, W51 e W53 ativos. A regra independente de W22 permanece: W22
ativo exige o grupo S20/W22. A proveniência permanece vinculada ao hash do
artefato M5 persistido, e os únicos grupos declarados aceitos são vazio,
prova, finalização e sua união.

## ADR-023 — M7: síntese congelada e challenger write-once

**Decisão:** M7 aceita exatamente cinco `DepartmentPacket` canônicos com
identidade comum, congela seus bytes e opera sobre cópia regular do champion.
Operações estruturadas usam paths contidos; links e arquivos especiais falham
fechados. Gates conferem a árvore antes/depois; `correctness_math` fica
inconclusivo sem evidência canônica. M7 não muda champion nem aplica decisão.

**Complemento corretivo (2026-08-14):** a identidade de síntese passa a
comprometer os bytes congelados e receipts dos cinco pacotes, a decisão
estruturada e os hashes integrais das propostas aceitas. A cópia preserva
diretórios normais e recusa links, hardlinks e arquivos especiais; staging,
inventário, manifest e publicação são verificados write-once. Gates locais
configurados são fail-closed, registram entrada/saída limitada e não aceitam
booleano para `correctness_math`. A única ponte de estado M7 é
`DEPARTMENTS_RUNNING → SYNTHESIS_READY → CANDIDATE_BUILT → GATES_PASSED`.

**Segundo complemento corretivo (2026-08-14):** `synthesize()` recebe os
bytes canônicos das propostas aceitas e falha se o conjunto não for exatamente
o declarado pelos cinco pacotes. O recibo congelado passa a comprometer os
hashes integrais, dependências, validações, reviews S20 aplicáveis e ordem de
aplicação. A árvore usa `lstat` sem seguir links, inclui diretórios no hash e
inventário determinísticos e normaliza nomes para detectar colisões; gates não
truncam uma saída excessiva para aprová-la e aceitam localizadores somente para
arquivos regulares contidos no candidato. Esses controles continuam locais e
não adicionam avaliação, júri, promoção ou qualquer estado M8.

**Verificação da correção:** dependências declaradas precisam pertencer ao
conjunto aceito; o retry relê o recibo congelado por contenção; e falhas
injetadas antes/depois do `rename` recuperam de forma idempotente. A suíte
local M0–M7 foi executada em módulos por limite de tempo do ambiente (183
testes, sem skips novos); M8 não foi iniciado.

**Terceiro complemento corretivo (2026-08-14, em implementação):** M7 deixa
de aceitar dicionários/fixtures como evidência de pacote ou proposta. Antes de
decodificar JSON, ele resolve o caminho absoluto canônico do receipt M6 pelo
par `(run_id, sha256)`, confirma contenção, faz `lstat`, lê os bytes uma única
vez e confere o SHA-256 exato. As transições M7 passam a ser operações com
pós-condições verificadas sobre artefatos congelados/publicados, e os gates
são verificadores locais configurados que falham fechados. Esta decisão não
introduz júri, avaliação externa, promoção ou qualquer estado M8.

**Quarto complemento corretivo (2026-08-14, correção final restrita):** o
artefato que autoriza `GATES_PASSED` é exclusivamente o `GateReport` canônico,
serializado e persistido no localizador derivado do próprio hash. Um único
verificador relê seus bytes, valida schema, identidade, configuração dos 13
gates, relações operacionais, hashes, localização, árvore atual do candidato
e estado `CANDIDATE_BUILT`; ele é reutilizado após `run_gates()` e
imediatamente antes da transição. `record_gates()` não aceita `Mapping` como
prova. Relatórios inconclusivos, forjados, internamente contraditórios ou
divergentes da configuração falham fechados.

A publicação finaliza, sincroniza e torna staging, descendentes e raiz
read-only antes do `rename`; depois dele há somente sincronização do pai e
revalidação, nunca um `chmod` tardio. `correctness_math` separa solicitação de
validação, evidência e aprovação: a aprovação é um contrato fechado persistido
e ligado a run, ciclo, base, candidato, claim, receipt e hashes. Os gates de
estado, proveniência M3, grafo de claims, assets, referências e LaTeX
reconstroem suas evidências locais; exceções viram resultados reprovados com
classificação e código de saída. O entrypoint LaTeX segue a regra determinista
`article.tex`, `paper.tex`, `latex-source/paper.tex`, preservando o diretório
de trabalho dos includes. Esta decisão termina no M7 e não autoriza júri,
promoção, Pareto, rejected nem M8.

## ADR-024 — M8: Júri Externo Cego, Inversão Consistente e Meta-Review

**Data:** 2026-08-27
**Status:** Aceito

### Contexto
O marco M8 é responsável pela avaliação cega, determinística e reproduzível do
candidato challenger em relação ao champion atual, após a aprovação de todos os
gates determinísticos do M7 (`GATES_PASSED`). A avaliação deve prevenir
vazamento de identidade/autoria e viés de posição (1ª vs 2ª apresentação),
garantindo que qualquer decisão de avanço seja auditável, imutável e vinculada
aos hashes de conteúdo avaliados.

### Decisão
1. **Blind Comparison Bundle & Sanitização**:
   - O `BlindComparisonBundle` extrai o conteúdo do champion e challenger,
     sanitiza menções a papéis (`M00`, `S10-S50`, `W11-W53`), versões (`v0000`,
     `v0001`, etc.) e rótulos (`champion`, `challenger`), associando-os aos
     identificadores neutros `"A"` e `"B"`.
   - Gera apresentações bijetivas nas ordens `["A", "B"]` e `["B", "A"]` com
     `order_seed` determinístico.

2. **Inversão Consistente e Detecção de Viés**:
   - Cada jurado avalia ambas as ordens de apresentação.
   - `check_inversion_consistency()` detecta viés de 1ª ou 2ª posição, drift de
     notas por dimensão acima da tolerância, e inconsistências na verificação
     matemática (`correctness_math_pass`).
   - Apenas jurados consistentes em ambas as apresentações são contabilizados
     no veredito final.

3. **Especialidades e Diversidade do Júri**:
   - Três especialidades canônicas: `juror-math` (foco em correção matemática),
     `juror-contrib` (foco em contribuição científica) e `juror-clarity` (foco em
     clareza e estilo).
   - Avaliação de diversidade de famílias de modelos (`full_diversity` vs
     `reduced_diversity_assurance`).

4. **Meta-Review e Veto Fail-Closed**:
   - O Meta-Revisor valida a consistência do júri contra o `GateReport` canônico.
   - Veto de meta-revisão ou reprovação em `correctness_math` por qualquer jurado
     consistente torna o resultado estritamente não-elegível (`challenger_eligible = False`).

5. **Imutabilidade e Transição de Estado**:
   - Todos os vereditos individuais e o relatório final de avaliação são
     persistidos de forma atômica e imutável em
     `state/evaluations/<run_id>/c<cycle_id:04d>/`.
   - Hashes da árvore do champion e challenger são verificados antes e depois
     da avaliação, garantindo zero mutação.
   - A única transição de estado permitida e executada é `GATES_PASSED → EVALUATED`.
   - M8 não altera o champion, não escreve em `versions/pareto/` ou `versions/rejected/`,
     e não realiza transição para `DIAGNOSED`, `DECIDED`, `COMMITTING`, `CYCLE_COMPLETE` ou `FINALIZED`.

### Consequências
- A avaliação de artigos opera de forma 100% reproduzível, auditável e imutável.
- Falhas de consistência, viés posicional ou veto matemático são tratadas de forma
  estritamente fail-closed.
- A máquina de estados preserva a separação de autoridade entre avaliação (M8) e
  decisão/diagnóstico/promoção (M9+).

**Complemento corretivo de endurecimento (2026-08-28):**
1. **Separação de Adapters Operacionais vs Teste**:
   - `FakeJurorAdapter` e `FakeMetaReviewerAdapter` são declarados restritos a teste (`test_only`).
   - O caminho operacional (`evaluate_candidate` e o CLI `scripts/01_external_evaluator.py`)
     falha fechado (`EvaluationError`) caso não haja adapters operacionais explicitamente configurados.
   - Proibido qualquer fallback padrão silencioso que favoreça o challenger.
2. **Vinculação Semântica Estrita dos Vereditos**:
   - Cada resposta do jurado é validada não apenas contra o schema sintático, mas
     contra a apresentação exata enviada: `comparison_id`, `juror_id`, `candidate_neutral_ids == ["A", "B"]`,
     `presentation_order`, `order_seed`, `rubric_version`, `content_hashes` fixos na ordem neutra `[hash_A, hash_B]`.
   - Vereditos duplicados, ordens repetidas (`A/B` retornado duas vezes), hashes trocados ou `verdict_id` reutilizado
     são rejeitados antes de qualquer persistência.
3. **Reuso do Verificador Canônico de GateReport**:
   - M8 reutiliza `article_loop.gates.verify_gate_report` para validar o `GateReport` contra o candidato atual.
   - Exige que o último evento do store seja estritamente `GATES_PASSED` e vincula `run_id`, `cycle_id`, `candidate_id`,
     `candidate_hash` e `report_locator` ao evento ativo.
   - Qualquer discrepância em `cycle_id`, `candidate_id` ou `gate_report_locator` falha fechada.
4. **Publicação Transacional Write-Once em Staging**:
   - A avaliação prepara toda a árvore em diretório temporário de staging no mesmo filesystem.
   - Gera e valida `manifest.json` da avaliação comprometendo todos os hashes (GateReport, champion, challenger, apresentações, vereditos, meta-veredicto e relatório).
   - Torna arquivos `0444` e diretórios `0555` antes do `rename` atômico para `state/evaluations/<run_id>/c<cycle_id:04d>`.
   - Caso o diretório de destino já exista, ele é revalidado integralmente; se idêntico, é aceito como replay idempotente; se divergente, rejeita por colisão.
   - Replay após falha entre publicação e evento revalida e reutiliza a árvore existente sem reescrevê-la.
5. **Sanitização Integral e Blinding de Caminhos**:
   - Nomes de arquivo, diretórios e metadados entregues aos jurados são mapeados para identificadores neutros,
     impedindo vazamento de roles (`M00`, `S10-S50`, `W11-W53`), versões (`v0000`, `v0001`), labels (`champion`, `challenger`)
     ou identificadores de ciclo/run.
6. **Durabilidade Estrita Pré-Rename (`fsync`)**:
   - Cada arquivo (`verdicts/*.json`, `meta-verdict.json`, `evaluation.json`, `manifest.json`) é gravado em bytes canônicos
     com `fsync` individual do descritor de arquivo.
   - Sincronização explícita dos diretórios do staging (`_fsync_tree_dirs`) antes e após a alteração de permissões (`_harden_read_only`),
     antes de `os.replace`.
   - Sincronização do diretório-pai após o rename.
7. **Limpeza Confiável de Staging Read-Only (`_cleanup_staging`)**:
   - Falha ou interrupção durante a montagem do staging limpa recursivamente o diretório temporário após restaurar permissões
     de escrita (`0o700` dirs, `0o600` files), sem suprimir erros (`ignore_errors=False`), impedindo arquivos órfãos em
     `state/evaluations/<run_id>/`.
8. **Preservação de Evidências em Recuperação**:
   - O caminho de recuperação do evento `EVALUATED` revalida e obtém os hashes diretamente da árvore publicada
     (`evaluation.json`, `meta-verdict.json`, `manifest.json` e os 6 `verdicts/*.json`), registrando exatamente a mesma lista
     canônica de 9 hashes que o caminho normal.
9. **Vinculação Estrita de `candidate_hash`**:
   - O payload do evento `GATES_PASSED` deve conter obrigatoriamente `candidate_hash` e este deve ser igual a
     `gate_report["candidate_hash"]` (sem fallback para `candidate_content_hash`), falhando fechado com `EvaluationError`
     antes de qualquer execução de jurados.
10. **Imposição Ativa de Fronteira de Test Doubles (`allow_test_doubles`)**:
    - `evaluate_candidate()` valida estritamente `allow_test_doubles` como tipo booleano (`isinstance(..., bool)`),
      recusando valores truthy ou não-booleanos (e.g. `"false"`, `1`, `{}`) com `EvaluationError`.
    - Por padrão (`allow_test_doubles=False`), inspeciona se qualquer adaptador de jurado ou meta-revisor possui
      `is_test_double=True` e falha fechado antes de produzir ou publicar qualquer artefato.
    - O CLI `scripts/01_external_evaluator.py` aceita a habilitação de dublês estritamente via flag CLI `--test-mode`,
      ignorando qualquer chave `test_mode` inserida no payload JSON de `--input`.
    - A separação entre adapters operacionais e dublês de teste passa a ser estritamente ativa e garantida em tempo de execução.

## ADR-025 — M9: Detecção Determinística de Estagnação, Diagnóstico Canônico e Refoco Reversível

**Data:** 2026-08-28
**Status:** Aceito

### Contexto
O Milestone 09 (M9) é responsável por processar o histórico validado de ciclos fechados a partir do estado `EVALUATED`,
gerando um `Diagnosis` determinístico, estruturado e content-addressed, e, exclusivamente quando diagnosticada
estagnação ou oscilação (`LOCAL_PLATEAU`, `GLOBAL_PLATEAU`, `OSCILLATING`), gerar um `RefocusPlan` com overlays de
prompt filhos imutáveis, reversíveis e sem ampliação de privilégios.

### Decisão
1. **Reconstituição Rigorosa e Isolamento Histórico**:
   - `load_history_series()` carrega exclusivamente ciclos fechados anteriores `c0..cN`, revalidando schemas,
     integridade criptográfica e hashes de `GateReport`, `evaluation.json` e manifestos.
   - Proibido qualquer look-ahead: artefatos ou eventos de ciclos futuros `> cN` são ignorados ou rejeitados.
   - Mistura de `run_id`, quebra de continuidade de sequência ou candidatos órfãos falham fechados (`DiagnosisError`).

2. **Motor de Classificação Puro e Precedência Fechada**:
   - Implementação estrita das 7 classificações canônicas: `EVOLVING`, `LOCAL_PLATEAU`, `GLOBAL_PLATEAU`,
     `OSCILLATING`, `REGRESSING`, `INCONCLUSIVE`, `TECHNICAL_FAILURE`.
   - Precedência determinística:
     1. `TECHNICAL_FAILURE`: falhas técnicas de compilação LaTeX, renderização ou gates determinísticos;
     2. `REGRESSING`: perda de hard gate matemático (`correctness_math_pass == False`), que não pode ser mascarada por júri inconclusivo;
     3. `INCONCLUSIVE`: divergência do júri ou todas as dimensões especializadas congeladas;
     4. `REGRESSING`: queda de notas centrais ou aumento material de severidade de issues;
     5. `OSCILLATING`: reversões materiais entre ciclos na janela ou reabertura de issues;
     6. `EVOLVING`: ganho global validado $\ge MDE$, challenger elegível e aprovação matemática integral;
     7. `LOCAL_PLATEAU`: janela completa com ganhos globais abaixo do MDE (`Minimum Detectable Effect`) e gargalo localizado em departamento/papel específico;
     8. `GLOBAL_PLATEAU`: janela completa sem ganho material nem direção segura em todos os departamentos;
     9. `INCONCLUSIVE`: fallback para janela insuficiente ou direção não validada por M8.
   - Melhorias cosméticas (clareza/estilo/economia de custo) jamais compensam perda matemática.

3. **Janela Móvel Parametrizada e FREEZE Normalizado**:
   - Janela deslizante default de 3 ciclos. Janela incompleta nunca inventa plateau.
   - O denominador de progresso departamental considera exclusivamente papéis ativos no `activation_map`,
     desconsiderando papéis em `FREEZE` legítimo.

4. **Publicação Transacional Write-Once e Transição de Estado**:
   - `Diagnosis` content-addressed (`diag-<sha256>`) validado contra `diagnosis.schema.json`.
   - Publicação em staging com permissões `0444`/`0555`, sincronização `fsync` de descritores e `os.replace` em
     `state/diagnosis/<run_id>/c<cycle:04d>/`.
   - Transição durável exclusivamente para `State.DIAGNOSED` (`EVALUATED -> DIAGNOSED`).
   - M9 nunca realiza transição para `DECIDED`, não promove candidatos e não modifica o conteúdo do artigo.

5. **Refoco Autorizado e Overlays Imutáveis**:
   - Refoco executa exclusivamente para `LOCAL_PLATEAU`, `GLOBAL_PLATEAU` e `OSCILLATING`. Para `EVOLVING`, `REGRESSING`,
     `INCONCLUSIVE` e `TECHNICAL_FAILURE`, a geração de overlays é proibida, seguindo diretamente para o M10.
   - Overlays são gerados como novos arquivos YAML imutáveis em `prompts/overlays/<role_id>/<new_ver>.yaml`,
     vinculados por `parent_version`, `rollback` acíclico e escopo contido.
   - Modificação de núcleos `prompts/immutable/`, overlays para `M00` ou ampliação de orçamento/autonomia são bloqueados.
   - No plateau global, são gerados no máximo 2 ramos: `exploitation` (refinamento matemático/estrutural) e `exploration` (reformulação alternativa de hipóteses).

6. **Transacionalidade e CAS no Registry**:
   - Gravações em `prompts/registry.json` utilizam lock exclusivo de arquivo (`prompts/.registry.lock`),
     validação de grafo `PromptRegistry`, escrita via arquivo temporário com `fsync` e substituição atômica.
   - Concorrência de múltiplos writers é serializada sob lock sem corrupção de ponteiros.

### Consequências
- A identificação de causas de estagnação torna-se 100% determinística, auditável e rastreável.
- Ajustes de contexto via prompt overlays tornam-se reversíveis, contidos e sem ampliação de privilégios.
- O pipeline respeita estritamente a fronteira entre diagnóstico (M9) e decisão/finalização (M10).

**Complemento corretivo de verificação semântica (2026-08-28):**

- A validade do `diagnosis_id`, dos hashes do manifesto e do evento é necessária,
  mas não suficiente: `verify_published_diagnosis()` recompõe classificação,
  sinais, modo recomendado e foco com o histórico revalidado e os parâmetros
  `window_size`/`mde` comprometidos.
- O evento `DIAGNOSED` deve vincular explicitamente `candidate_content_hash` ao
  ciclo avaliado; ausência ou divergência falha fechado.
- Um invasor que reescreva diagnosis, manifesto e evento com hashes internos
  coerentes não pode substituir o resultado do classificador determinístico.

## ADR-026 — Handoff compacto e histórico de sessões para agentes de IA

**Data:** 2026-09-01
**Status:** Aceito

### Contexto

O repositório já ultrapassa centenas de milhares de bytes entre código, testes,
schemas, prompts, decisões e handoffs. `README.md` descreve principalmente M3,
enquanto o estado implementado alcançou M9. Obrigar cada nova sessão de IA a
reler todos os arquivos desperdiça tokens e ainda não resolve divergências de
atualidade entre documentos.

### Decisão

1. `scripts/ai_context.py` será o utilitário determinístico de início de
   sessão. Ele inventaria todos os arquivos relevantes, calcula hashes, extrai
   APIs Python, contratos, testes, configuração, estado Git, marco atual e
   deltas desde o último encerramento. Também lê o histórico produzido pelo
   segundo utilitário e publica `AI_CONTEXT.md` atomicamente.
2. `scripts/ai_history.py` será executado somente no encerramento do trabalho.
   Ele reconstrói a evolução versionada a partir de Git e ADRs, recebe da IA um
   resumo estruturado da sessão, acrescenta-o a um ledger JSONL append-only,
   atualiza o snapshot factual da árvore e renderiza `docs/AI_HISTORY.md`.
3. `docs/ai_sessions.jsonl` e `docs/ai_snapshot.json` são suporte mecânico do
   histórico; não pertencem ao event log científico e não autorizam qualquer
   transição do article-loop. Os documentos gerados e esses suportes ficam
   fora do fingerprint de fontes para evitar autorreferência.
4. `AGENTS.md`, `CLAUDE.md` e `.prime/agent/APPEND_SYSTEM.md` conterão o
   protocolo auto-descoberto: no início executar o gerador e ler integralmente
   `AI_CONTEXT.md`; no fim, depois de concluir mudanças e validações, executar o
   registrador com descrição substantiva e então regenerar o contexto.
5. A saída usa Markdown compacto, com inventário completo e detalhamento
   seletivo. Conteúdo de repositório é tratado como dado não confiável; o
   gerador não executa arquivos inventariados, não chama modelos, não usa rede e
   depende somente da biblioteca padrão do Python.

### Consequências e limites

- Qualquer mudança de bytes aparece por hash e delta na próxima geração, mesmo
  quando a ferramenta não consegue inferir sua intenção semântica.
- O resumo de encerramento continua responsabilidade da IA; um fallback factual
  pode registrar arquivos alterados, mas não deve alegar decisões não fornecidas.
- Arquivos de instrução auto-descobertos são o gatilho mais forte que um
  repositório pode oferecer, mas não podem coagir clientes de IA que decidam
  ignorar deliberadamente instruções de projeto.

### Reconciliação com a publicação no GitHub — 2026-09-01

Uma publicação posterior adicionou workflow de CI, templates comunitários,
licença e documentação de contribuição/segurança, além de substituir o README
introdutório. A comparação com o snapshot content-addressed registrado ao fim
da implementação confirmou que os utilitários, gatilhos, testes e documentos
normativos desta decisão permaneceram byte a byte.

As adições comunitárias serão preservadas. O README de apresentação deve,
porém, manter em posição proeminente o protocolo de entrada e saída para IAs e
deve distinguir componentes implementados até M9 de stubs reservados para M10.
O workflow público deve executar a mesma descoberta integral de testes usada
localmente, com as dependências determinísticas de PDF/LaTeX disponíveis.
- Esta camada não modifica os cinco scripts científicos canônicos, não inicia
  Prime Agent, não cria agentes e não altera M10 ou marcos posteriores.

## ADR-027 — Separação de audiências e histórico Git publicável

**Data:** 2026-09-02
**Status:** Aceito

### Contexto

A publicação anterior misturou duas responsabilidades. O `README.md`, que o
GitHub renderiza como apresentação humana do projeto, passou a conter um
protocolo obrigatório de sessão para IAs. Ao mesmo tempo, o contexto gerado para
agentes incorporava caminho absoluto, branch e HEAD do checkout, portanto uma
cópia idêntica do repositório podia ficar modificada apenas por executar o
gerador exigido. O documento ainda duplicava integralmente `AGENTS.md`, um
trecho extenso do README e todo o inventário, elevando desnecessariamente o
custo de contexto para clientes de IA.

No Git, a pasta de trabalho continha um repositório vazio na raiz e outro
repositório funcional em `EXECLOOP/`. A branch funcional havia sido unida a
`origin/main` por um merge com estratégia `ours` entre históricos sem ancestral
comum, deixando dezenas de commits locais artificiais para uma futura
publicação.

### Decisão

1. `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, templates e workflow serão
   superfícies humanas/públicas do GitHub. O README não imporá protocolo de
   agente nem será incorporado ao contexto operacional de IA.
2. `AGENTS.md` será a entrada canônica para agentes genéricos/Codex.
   `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md` e
   `.prime/agent/APPEND_SYSTEM.md` serão adaptadores curtos que encaminham ao
   contrato canônico, sem duplicar a política inteira.
3. `AI_CONTEXT.md` continuará versionado para consumidores que leem o
   repositório sem executar ferramentas, mas sua renderização será portável:
   sem caminho absoluto, nome de branch, commit ou status volátil do checkout.
   Ele manterá fingerprint, delta, resumo operacional, handoff e roteamento,
   mas apontará para `AGENTS.md`, `README.md` e `docs/ai_snapshot.json` em vez
   de copiá-los integralmente.
4. A árvore validada será preservada e reaplicada como um único commit
   descendente de `origin/main`, com uma branch de backup para o grafo anterior.
   Isso permite publicação normal por fast-forward e proíbe force-push como
   parte deste reparo.
5. Haverá um único repositório Git na raiz efetiva do projeto. O `.git` vazio
   da pasta-pai será movido para um backup recuperável antes de elevar o
   conteúdo de `EXECLOOP/` para essa raiz.

### Consequências e limites

- Visitantes do GitHub recebem uma apresentação do produto sem instruções de
  controle de agente no topo da página.
- Codex, Claude, Gemini, GitHub Copilot e Prime Agent recebem pontos de entrada
  próprios que convergem para a mesma política.
- Clonar, copiar ou commitar o projeto não altera `AI_CONTEXT.md` somente por
  mudar caminho, branch ou SHA do checkout.
- A autenticação do GitHub continua sendo uma fronteira externa: o reparo
  prepara um fast-forward local, mas não inventa nem armazena credenciais.
- Esta decisão não modifica o pipeline científico nem inicia M10 ou execução
  de modelos.

## ADR-028 — M10: política pura e finalização transacional por referência

**Data:** 2026-09-02

**Decisão:** M10 separa a escolha da disposição de sua aplicação. A política
revalida somente evidência publicada de M7--M9, consulta uma tabela fechada e
versionada e publica uma `Decision` content-addressed sem escrever em
`versions/`. A tabela dá precedência a falha técnica, gate matemático duro,
diagnóstico e limites persistidos; nenhuma linha desconhecida ou ambígua pode
promover um challenger.

O finalizador é o único escritor de disposições. Sob lock por execução, ele
revalida a `Decision`, os hashes do candidato, GateReport, avaliação e
diagnóstico antes de registrar `COMMITTING`. Um journal idempotente registra
preparo, revalidação, staging, CAS de pointer, evento, checkpoint e limpeza.
Promoção copia somente os bytes de conteúdo já avaliados para uma nova versão
histórica de champion e publica um pointer CAS; Pareto e rejected preservam
referências imutáveis ao challenger. Nenhuma operação sobrescreve ou remove
versões históricas, e `content_modified` permanece sempre falso.

**Complemento de revisão pré-publicação:** `ARCHIVE_PARETO` só é autorizado
depois de comparar o vetor completo das oito dimensões, sob gate matemático
duro, com as referências Pareto já publicadas. A relação (dominado, trade-off
ou quais referências são dominadas) integra a `Decision` e é revalidada sob o
lock pelo finalizador; uma fronteira alterada entre decisão e efeito falha
fechado. Referências históricas dominadas não são apagadas. Falhas técnicas
geram checkpoint imutável com contador e limite da política, sem retry
automático, e a fachada pública `finalize()` delega exclusivamente ao
finalizador M10.

**Motivo:** separar a avaliação de qualidade do efeito de filesystem impede que
um retry, concorrência ou crash promova bytes não avaliados, crie dois champions
atuais ou apague evidência necessária para auditoria.
