---
name: repo-maintenance
description: Equipe efêmera e fail-closed para manutenção offline deste repositório.
---

# repo-maintenance

Use esta skill somente após autorização humana explícita para uma tarefa de
manutenção com paths e limites definidos. Leia `AGENTS.md`, `AI_CONTEXT.md`, a
seção aplicável de `PLANS.md`, o ADR aplicável e
`docs/maintenance-agents.md` antes de admitir um filho.

## Contrato fechado

- A sessão raiz é `maint-coordinator`.
- Os nomes de todos os filhos começam com `maint-`.
- Cada rodada possui exatamente um `maint-implementer`. Ele é o único escritor
  e só altera os paths permitidos no pedido.
- Após o escritor terminar, o coordenador cria um `maint-verifier` novo. O
  verificador é somente leitura e não corrige o trabalho.
- Filhos são folhas. Eles não criam filhos nem usam netos.
- A equipe não acessa os 21 papéis científicos, champion, challengers, Pareto,
  estado de execução, PDF ou evidência.
- Rede, downloads, Prime live, modelo, endpoint e ciclo científico continuam
  proibidos sem autorização separada e explícita.

## Superfícies permitidas

A coordenação usa somente as superfícies locais confirmadas:

1. `rlm.spawn(prompt, name=...)`, que devolve um handle de admissão e nunca a
   resposta do filho;
2. `rlm.list_subagents()` para recuperar filhos diretos;
3. `rlm.delete_subagent(child)` para remover um filho direto encerrado;
4. `agent_message.send(...)` para handoffs e instruções explícitas.

Não invente APIs, manifestos, rosters, daemons, `.prime/agent/agents/`,
`team.yaml`, estado paralelo ou seleção implícita de modelo. Use profundidade 2
somente na sessão raiz autorizada e nunca `--global`.

## Sequência da rodada

1. O coordenador fixa tarefa, autorização, allowed paths e comandos proibidos.
2. Ele confirma que não existe outro escritor e admite um único
   `maint-implementer`.
3. O implementador inspeciona, edita, valida offline e envia um handoff.
4. O coordenador encerra/remove o implementador antes da verificação.
5. Ele admite um `maint-verifier` novo, somente leitura.
6. O verificador revisa diff e comandos permitidos, então envia um handoff.
7. O coordenador decide encerrar, bloquear ou abrir uma nova rodada com novo
   implementador. Nunca há dois escritores simultâneos.

O formato dos papéis e do handoff está em `references/roles.md`.
