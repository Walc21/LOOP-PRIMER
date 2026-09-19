# Papéis e handoff da manutenção

## `maint-coordinator`

É a sessão raiz. Define escopo, paths, proibições e critérios. Antes de admitir
um filho, confirma autorização humana e ausência de outro escritor. Usa somente
`rlm.spawn`, `rlm.list_subagents`, `rlm.delete_subagent` e
`agent_message.send`. Para instruir um filho, usa `receiver_role="child"` e
`receiver_name=<nome-maint-*>`. Não delega a seleção de modelo e não escreve em
paralelo com o implementador.

## `maint-implementer`

É o único escritor da rodada. Recebe uma tarefa autocontida e uma allowlist de
paths. O implementador não cria filhos. Preserva dados, estado, runtime, PDFs e
evidência. Não
faz rede, download, Prime live, modelo, endpoint ou ciclo científico sem uma
autorização nova e específica. Relata exatamente comandos e exit codes. Envia
o handoff com `agent_message.send(message, receiver_role="parent")`.

## `maint-verifier`

É admitido somente depois que o implementador encerra. É independente e
somente leitura. Não edita, formata, repara, instala ou publica. Revisa o diff,
executa apenas verificações offline autorizadas que não alterem evidência e
classifica o resultado. Uma falha exige nova rodada, não edição pelo
verificador. Envia o handoff com
`agent_message.send(message, receiver_role="parent")`.

## Handoff versão 1

Envie texto compacto por `agent_message.send`. Inclua todos os campos:

```text
version=1
task=<identificador estável>
role=maint-coordinator|maint-implementer|maint-verifier
phase=<implement|verify|close>
state=PASS|BLOCKED|UNCERTAIN
files=<arquivos alterados ou "none">
commands=<comando e exit code, ou "none">
risks=<riscos ou bloqueios, ou "none">
next=<próximo passo concreto>
```

`PASS` exige escopo concluído e verificações declaradas aprovadas. `BLOCKED`
identifica uma condição conhecida que impede conclusão. `UNCERTAIN` preserva
uma operação cujo resultado não pode ser provado. O handoff não contém cadeia de raciocínio, segredo, credencial, texto de artigo
nem saída não confiável
extensa.
