# Inventário de superfícies model-driven — M12.5.1

Este inventário separa claramente código determinístico de pontos que podem
consumir um modelo. Ele não é autorização de execução.

| Superfície | Entrada autorizada | Saída contratual | Camada e estado Phase A |
|---|---|---|---|
| Filhos Prime M6 | `AgentTask`, view fechada, prompt compilado e workspace isolado | handle; depois `agent-proposal.json` ou `department-packet.json` por receipt | `prime`; API preservada como `spawn(prompt, name)`; live não executado |
| Trabalhadores routed M12.5.1 | mesma `AgentTask`/view M6, contexto textual materializado e hash-bound | JSON científico validado, output durável e receipt M6 | `routed`; ligação implementada; sem target/configuração live |
| Router/backend M12.5 | metadados da tarefa, capacidades, política, contexto hash e prompt filtrado | inference result e receipt operacional | determinístico até a chamada; backend real desabilitado |
| Júri cego M8 | bundle anonimizado de candidato/champion e rubric | `JuryReport` | interface `JurorAdapter.evaluate()` existente; não é contornada pelo routed controller |
| Meta-review M8 | relatórios cegos validados | `MetaReview`/avaliação consolidada | interface existente; nenhuma ligação nova nesta Phase A |

M3, M5, M7, gates, M9, política M10 e finalizador são determinísticos e não
chamam modelo. O ator de controle Sxx routed também não é modelo: ele persiste
handles/admissões e conduz workers pelo runtime.

## Fronteira M8

M12.5.1 não substitui `JurorAdapter` nem injeta `InferenceRuntime` diretamente
no avaliador. A interface M8 continua sendo o ponto obrigatório para blindagem,
randomização, inversão, validação de schema e meta-review. A política de modelo
do router pode expressar independência por `model`, mas uma futura ligação M8
precisará entrar por essa interface, preservar o bundle cego e ter testes
próprios. Nesta Phase A, documentar essa fronteira é mais seguro do que criar
um segundo caminho de júri.

## Conteúdo que nunca é metadado operacional

Prompt completo, contexto materializado, artigo, saída científica, mensagens
privadas e credenciais não pertencem a logs, route decisions ou inference
receipts. A saída científica existe somente no store de outputs e na cópia
exata recepcionada por M6. O receipt contém hashes e locators.
