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
