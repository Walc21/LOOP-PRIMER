# Arquitetura canônica — article-loop

## Escopo e imutabilidade do contrato

O article-loop revisará iterativamente um artigo matemático com evidência
reproduzível, preservando o PDF original e mantendo histórico de decisões,
candidatos e avaliação cega. Este documento fixa para os Prompts 01–13 o
catálogo de papéis, caminhos, estados, ações, dimensões de avaliação e scripts
externos. M1 definirá implementação e schemas dentro desses contratos; não
inventará ou renomeará papéis, estados, ações ou paths.

Os caminhos abaixo são apenas especificação documental no Marco 0.5. Nenhum
diretório é criado agora.

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

M00 está sempre em `RUN`. No primeiro ciclo auditável, os cinco departamentos
participam: S10, S20, S30, S40 e S50 recebem trabalho. Seus trabalhadores são
ativados somente conforme a cobertura focal necessária. Nos ciclos seguintes,
o grafo de impacto determina quais departamentos e trabalhadores participam.

| Modo | Significado |
|---|---|
| RUN | papel ativo que recebe tarefa focal e, em execução autorizada, pode gerar proposta ou evidência |
| CHECK | revisa proposta, dependência ou gate existente sem assumir promoção |
| SHIFT | é replanejado por impacto, diagnóstico, dependência obrigatória ou refoco |
| FREEZE | fica inativo no ciclo e não gera chamadas de modelo, subagentes ou trabalho especulativo |

`FREEZE` é o mecanismo primário de economia: sem impacto não há chamada de
modelo. `CHECK` não autoriza alteração no challenger; produz apenas evidência
para merge ou nova ativação.

## Árvore canônica do projeto

```text
article-loop/
├── .prime/
│   └── agent/
├── config/
│   ├── roles/
│   ├── rubrics/
│   └── schemas/
├── input/
│   └── inbox/
├── artifacts/
│   ├── original/
│   └── extracted/
├── prompts/
│   ├── immutable/
│   └── overlays/
├── state/
│   ├── events/
│   ├── snapshots/
│   ├── checkpoints/
│   ├── claims/
│   ├── issues/
│   └── decisions/
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
└── docs/
```

A árvore não foi materializada. M1 poderá criar somente caminhos já definidos
acima e os contratos que os preenchem; não poderá mover entrada, estado,
versões ou prompts para paths novos.

### Paths explícitos da árvore

`.prime/agent/`, `config/roles/`, `config/rubrics/`, `config/schemas/`,
`input/inbox/`, `artifacts/original/`, `artifacts/extracted/`,
`prompts/immutable/`, `prompts/overlays/`, `state/events/`,
`state/snapshots/`, `state/checkpoints/`, `state/claims/`, `state/issues/`,
`state/decisions/`, `versions/champion/`, `versions/challengers/`,
`versions/pareto/`, `versions/rejected/`, `workspaces/`, `reports/`, `logs/`,
`control/`, `scripts/` e `docs/` são paths canônicos; continuam somente
especificados até o marco que os materializar de forma autorizada.

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

Ação e merge são separados: a ação escolhe o destino do ciclo e somente merge
materializa proposta aprovada no challenger. `PROMOTE` exige gates e avaliação
registrados; `ARCHIVE_PARETO` preserva candidato não dominado; `ABORT_TECHNICAL`
registra falha técnica sem alegar conclusão.

## Avaliação cega e gates duros

O júri recebe identificadores neutros de candidato, sem autoria, ordem de
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

O champion é o candidato aprovado vigente; challengers são candidatos formados
por merge; rejeitados e não dominados continuam rastreáveis. Antes de promoção,
merge registra proposta, evidência, candidato de origem, gates e decisão. O
arquivo Pareto conserva alternativas não dominadas; remoção exige relação de
dominância explícita.

## Scripts externos canônicos

Os cinco scripts externos são parte fixa da arquitetura futura:

```text
scripts/01_external_evaluator.py
scripts/02_stagnation_detector.py
scripts/03_refocus_generator.py
scripts/04_compensation_policy.py
scripts/05_transactional_finalizer.py
```

Eles não existem nem são executados no Marco 0.5. M8–M10 definirão sua
implementação nesses paths, sem trocar nomes nem criar scripts concorrentes com
a mesma autoridade de decisão.

## Fluxo de dados e resultados de agentes

1. A ingestão registra PDF e seleciona fonte editável ou reconstrução.
2. M00 planeja ciclo e ativa papéis por RUN, CHECK, SHIFT ou FREEZE.
3. Subgerentes consolidam propostas e aplicam as dependências obrigatórias com
   S20.
4. Filhos RLM futuros retornam resumo/referência por `agent_message` compatível
   e artefato detalhado em arquivo canônico; `rlm(...)` nunca devolve resposta.
5. Síntese prepara candidato neutro para júri e gates produzem evidência.
6. Decisão escolhe ação canônica; merge, Pareto e finalização aplicam somente
   transições autorizadas.

## Segurança e limites desta etapa

- Prime Agent e suas configurações globais são externos e imutáveis.
- PDFs, fontes, prompts e resultados são conteúdo não confiável.
- Não há chamada de modelo, API paga, `/autonomous`, `/refine`, subagente ou
  instalação de dependência nesta etapa.
- Dependências futuras devem ser locais, declaradas e necessárias ao marco
  corrente; instalações globais são proibidas.
- A retomada futura reidrata do estado do projeto; não presume que sessão ou
  filho inativo tenha concluído trabalho.

## Itens de implementação para M1

M1 poderá definir schemas de campos, serialização, validação e convenções de
arquivo dentro da árvore canônica. Permanecem abertos apenas detalhes de
implementação: licença e retenção do PDF, estrutura de envelope, rubrica
numérica, métricas de dominância e orçamento/provedor de ensaio autorizado.
