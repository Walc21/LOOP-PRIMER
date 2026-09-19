# Equipe efêmera de manutenção

Esta equipe operacional é separada dos 21 papéis científicos. Ela não usa
`PrimeRLMAdapter`, não altera autoridade científica e não cria estado durável
além de documentação, código e handoffs já autorizados.

## Topologia por tarefa

A sessão raiz atua como `maint-coordinator`. Cada rodada tem exatamente um
filho escritor, com nome `maint-implementer-*`. Quando ele encerra e entrega o
handoff, o coordenador o remove e cria um novo `maint-verifier-*` somente
leitura. Filhos são folhas. Não há netos, dois escritores simultâneos, roster
permanente, daemon ou configuração global.

O coordenador usa somente `rlm.spawn`, o handle de admissão,
`rlm.list_subagents`, `rlm.delete_subagent` e `agent_message.send`. Um handle
confirma admissão, não conclusão nem resposta. Resultados chegam por handoff
explícito. Nenhuma outra API deve ser presumida.

## Autorização e isolamento

Cada tarefa precisa de autorização humana explícita, escopo, allowlist de paths
e limites. Uma autorização de manutenção não autoriza rede, download, Prime
live, modelo, endpoint, autonomia ou ciclo científico. A profundidade 2 é um
override apenas da sessão raiz quando autorizado; nunca use `--global`.

Os papéis `maint-*` não acessam `config/roles/`, champion, challenger, Pareto,
PDF, estado de execução ou evidência salvo quando uma tarefa específica de
inspeção somente leitura autorizar isso. O implementador preserva arquivos
preexistentes. O verificador não corrige o diff.

## Fluxo fail-closed

1. O coordenador registra tarefa, paths, proibições e critérios.
2. Confirma por `rlm.list_subagents()` que não existe escritor ativo.
3. Admite um único `maint-implementer-*` com pedido autocontido.
4. Recebe handoff `version=1` e remove o implementador encerrado.
5. Admite um `maint-verifier-*` novo e somente leitura.
6. Recebe o handoff do verificador e classifica a tarefa.
7. Uma correção exige nova rodada com novo implementador único.

Todo handoff inclui `version`, `task`, `role`, `phase`, `state`, `files`,
`commands`, `risks` e `next`. `state` é exatamente `PASS`, `BLOCKED` ou
`UNCERTAIN`. Não se envia cadeia de raciocínio privada nem segredo. O contrato
operacional completo está em
`.prime/agent/skills/repo-maintenance/references/roles.md`.
