# Compatibilidade do Prime Agent

## Escopo e autoridade

Auditoria realizada em 2026-08-12, no diretório do projeto
`/home/victor/EXECLOOP`. Nenhuma sessão, agente filho, modelo, `/autonomous` ou
`/refine` foi iniciado. Não foram lidos arquivos de autenticação nem outras
credenciais.

Regra deste projeto: o comportamento observado na instalação `0.7.1` é a
autoridade de execução. A documentação de `main` foi conferida como referência
atual, mas não autoriza código que a instalação não exponha.

## Evidência da instalação

| Item | Resultado observado |
|---|---|
| Executável | `/home/victor/.nvm/versions/node/v24.19.0/bin/prime-agent` |
| `prime-agent --version` | `0.7.1` |
| Pacote | `prime-agent` `0.7.1`, com `piConfig.configDir: .prime/agent` |
| Node exigido pelo pacote | `>=22.8.0` |
| Git do projeto | inexistente antes da auditoria; inicializado sem commit/push |

### Saída útil de `prime-agent --help` (resumo sanitizado)

O CLI instalado expõe os modos `text`, `json`, `rpc`, `acp` e `daemon`; opções
de sessão `--continue`, `--resume`, `--fork`, `--session-dir`, `--no-session` e
`--goal`; carregadores `--skill`, `--prompt-template`, `--no-skills`,
`--no-prompt-templates` e `--no-context-files`; e as opções autônomas
`--autonomous`, `--autonomous-gate`, `--autonomous-gate-retries`,
`--autonomous-gate-timeout-ms`, limites de continuações, turnos, tokens e tempo.

Subcomandos listados: `help`, `agents`, `list`, `attach`, `stop`, `rename`,
`send`, `schedule`, `status`, `doctor`, `shutdown`, `package`, `update`,
`model`, `session` e `config`.

Foram ainda verificados:

- `session export <file> [output]`;
- `send [--from <agent>] <agent> <message>` com `--steer`, `--follow-up` e
  `--json`;
- `package <install|remove|list|update>`;
- `schedule <list|add|cancel>`;
- `list [--all] [--json]`, `attach <agent>`, `stop <agent> [--json]` e
  `doctor [--fix] [--json]`.

Nenhum desses subcomandos foi executado além de `help`.

### Revalidação operacional M11 — 2026-09-03

O caminho absoluto registrado acima e o comando `prime-agent` não estão
disponíveis nesta sessão (`command -v prime-agent` não encontrou executável).
A tabela histórica de superfícies continua sendo a referência compatível, mas
não houve smoke test live, `/reload`, sessão Prime ou leitura de settings.
M11, portanto, não cria `.prime/agent/settings.json` nem presume chaves da
documentação de `main`; o launcher falha fechado até que uma instalação
compatível seja encontrada e uma autorização separada exista.

### Auditoria estática M12.5 — 2026-09-03

A nova verificação repetiu `command -v prime-agent`, consultou o caminho
absoluto histórico e procurou o pacote instalado sem iniciar sessão: nenhum
executável ou pacote Prime Agent estava disponível neste host. Assim, três
capacidades permanecem deliberadamente separadas:

- observar o modelo retornado no `ChildHandle` histórico é suportado;
- escolher um modelo para a sessão raiz não foi verificado nesta instalação;
- escolher provider/modelo por chamada `rlm(...)` ou por filho é
  `unsupported_verified` no ambiente atual.

M12.5 não acrescenta argumentos a `PrimeRLMAdapter.spawn(prompt, name)` e não
usa configuração de `main` como substituto de evidência local. Seu routing
backend-aware vale somente para a nova fronteira de inferência explícita; não
altera a topologia, profundidade ou lifecycle dos filhos M6.

## Documentação oficial consultada

O repositório oficial é
[`PrimeIntellect-ai/prime-agent`](https://github.com/PrimeIntellect-ai/prime-agent).
Foram consultadas as versões atuais de `main` e as cópias empacotadas pela
instalação local:

- [quickstart.md](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/quickstart.md)
- [usage.md](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/usage.md)
- [settings.md](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/settings.md)
- [prompt-templates.md](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/prompt-templates.md)
- [skills.md](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/skills.md)
- [rlm.md](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/rlm.md)
- [long-running-agents.md](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/long-running-agents.md)

Também foram examinados, somente para esclarecer contrato já instalado, os arquivos públicos empacotados `dist/skills/{agent-message,goal,compact,refine}/SKILL.md` e o código distribuído do comando `/rlm-max-depth`.

## Superfícies verificadas

| Superfície | Contrato confirmado para o projeto | Status |
|---|---|---|
| Contexto de projeto | `AGENTS.md`/`CLAUDE.md` são descobertos em ancestrais e no cwd; `AGENTS.md` é adequado para regras duráveis. | suportada |
| Apêndice do sistema | A documentação instalada declara `.prime/agent/APPEND_SYSTEM.md` como apêndice ao prompt padrão, sem substituí-lo. | suportada documentalmente; smoke test futuro |
| Templates | `.prime/agent/prompts/*.md`, não recursivo; frontmatter YAML opcional com `description` e `argument-hint`; nome do arquivo vira `/nome`; suporta `$1`, `$@`, `$ARGUMENTS` e cortes de argumentos. | suportada |
| Local de skills | Skill de projeto em `.prime/agent/skills/`; diretórios com `SKILL.md` são descobertos recursivamente. | suportada |
| Skill Python | Requer `SKILL.md`, `pyproject.toml`, `src/<nome_com_underscore>/__init__.py`; hífens do nome viram underscores no import. `run()` torna o módulo chamável assíncrono. | suportada; não instalar nesta fase |
| `rlm(...)` | `await rlm(prompt, name=...)` devolve imediatamente handle de admissão com `rlm_child_id`, `name`, `session_dir`, `model`; nunca devolve resposta do filho. | suportada |
| Seleção de modelo | O handle permite observar `model`; seleção de sessão não foi revalidada e seleção provider/model por filho/chamada não está exposta no contrato confirmado. | sessão: não verificada; por filho: `unsupported_verified` |
| Resultados de filhos | Chegam por `agent_message` explícito ou arquivos; `rlm.list_subagents()` recupera filhos diretos; `rlm.delete_subagent(...)` os remove quando não necessários. | suportada |
| `agent_message` | `list_agents()` é restrito à família. Assinatura segura: `send(message, receiver_role="parent"|"sibling"|"child", receiver_name=...)`; pai não recebe nome, irmãos/filhos exigem nome. | suportada com ressalva abaixo |
| `/goal` | Cria/meta persistentemente objetivo explícito; possui status, pause, resume, clear e orçamento. No kernel, `goal.get()`, `goal.create()` e `goal.complete()`. | suportada; proibida nesta fase |
| `/autonomous` | `on`, `off`, `status`; no CLI possui gates e limites. | suportada; proibida nesta fase |
| Gates autônomos | `--autonomous-gate <command>` é repetível; padrão de 3 tentativas por gate e timeout de 300000 ms por gate. Gate falho alimenta nova tentativa e o runtime evita repetir o mesmo gate sem mudança de workspace. | suportada; não ativar agora |
| `/compact` | Resume mensagens antigas; kernel persiste. No kernel, `compact.status()` e `compact.run(instructions=None)` agendam ao fim do turno. | suportada; não ativar agora |
| `/refine` | Refina estado suplementar da harness após o turno; `refine.status()` e `refine.run(...)`. Não altera o prompt-base imutável, mas pode requerer modelo. | suportada; proibida nesta fase |
| `/rlm-max-depth` | Comando interativo aceita consulta ou `/rlm-max-depth <inteiro não negativo> [--global]`. A instalação resolve, em ordem, override persistido no chat, valor herdado, configuração global, `RLM_MAX_DEPTH`, depois padrão 1. | suportada; usar somente override de chat 2 |
| Sessões por projeto | JSONL é salvo por padrão em `~/.prime/agent/sessions/`; o cabeçalho registra cwd e o seletor usa essa informação para visão por projeto. `sessionDir` pode ser configurado, mas o produto manterá estado próprio. | suportada |

## Estratégia de compatibilidade para profundidade 2

Antes de uma execução autorizada, o adaptador deverá consultar
`/rlm-max-depth`. Em seguida, na sessão raiz, aplicará exatamente
`/rlm-max-depth 2`, sem `--global`. A implementação instalada permite uma nova
chamada a `rlm` somente quando `RLM_DEPTH < RLM_MAX_DEPTH`; logo, os níveis 0,
1 e 2 atendem gerente geral, subgerentes e especialistas respectivamente.

Se o comando não estiver disponível na UI da versão efetivamente executada, o
adaptador deve interromper a sessão antes de criar qualquer subgerente e emitir
um erro de compatibilidade. Não deve escrever `RLM_MAX_DEPTH` em configuração
global, iniciar profundidade 1 esperando recursão, ou simular filhos com uma API
não documentada.

## Incompatibilidades e adaptador obrigatório

1. **Defasagem de versão:** o executável é `0.7.1`; a documentação `main` de
   configurações contém exemplo de manifesto `0.73.1`. Não se presume que todo
   exemplo de `main` exista no binário. O adaptador usa apenas a tabela acima.
2. **Profundidade padrão:** a instalação padrão é 1, enquanto a arquitetura
   exige 2. O adaptador faz preflight por sessão e configura 2 localmente; falha
   de forma explícita se não conseguir.
3. **`agent_message.mode`:** `long-running-agents.md` de `main` mostra
   `mode="auto"|"steer"|"follow_up"`, mas a `SKILL.md` embutida na instalação
   documenta uma assinatura sem `mode` e o handler distribuído não encaminha
   esse campo. O adaptador não passa `mode` nem promete semântica de fila além
   do receipt observado. Use a assinatura mínima acima e artefatos duráveis.
4. **`/rlm-max-depth` não é flag CLI:** foi confirmado como comando interativo,
   não como `prime-agent --rlm-max-depth`. Nunca inventar essa flag.
5. **Descoberta de templates não é recursiva:** comandos necessários ao produto
   devem ser arquivos diretos de `.prime/agent/prompts/` ou ser carregados
   explicitamente por configuração futura validada.
6. **Skill Python instala no kernel quando uma sessão é iniciada:** criar ou
   alterar `pyproject.toml` pode disparar instalação/recriação do ambiente do
   kernel. Nesta fase a skill é apenas planejada; testes de importação ficam
   bloqueados até autorização para dependências e sessão.
7. **Refinamento e autonomia são superfícies de execução, não provas de
   correção:** gates aprovados cobrem somente seus verificadores. A promoção de
   candidato continuará dependente do estado próprio, júri e gates locais.

## Regras do adaptador

- Centralizar essas operações em uma única camada do projeto; não espalhar
  strings de API de Prime Agent pelos papéis.
- Persistir envelopes de pedido/resultado antes de atualizar champion,
  challenger ou Pareto.
- Usar `await rlm(prompt, name=...)`, guardar o handle e terminar o turno; não
  fazer polling fictício nem esperar uma resposta como retorno.
- Para mensagens, usar somente `receiver_role` e `receiver_name` conforme a
  assinatura mínima. Para informação longa, escrever arquivo imutável e enviar
  apenas referência/identificador por mensagem.
- Tratar indisponibilidade de mensagem, sessão, skill ou profundidade como
  estado recuperável e visível, nunca como sucesso silencioso.
- Validar dinamicamente as superfícies, em modo offline e sem modelo quando isso
  for possível, antes do primeiro uso com um provedor autorizado.
