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
