# Runbook local do article-loop

Este runbook descreve somente a camada operacional M11. O estado durável do
produto continua no repositório; a sessão Prime Agent é apenas um executor
externo. O PDF de entrada e versões publicadas são imutáveis.

## Preparação e verificação

Na raiz do projeto, execute:

```sh
bash bin/check.sh
python3 scripts/article_loop_command.py preflight --root .
```

`check.sh` é local e determinístico: valida os templates planos, os arquivos
canônicos, a profundidade 2 e os defaults de orçamento. `article-preflight` é
read-only quando executado fora de uma sessão Prime e informa que não há
`PrimeRLMAdapter` explícito; isso não é aprovação para execução live.

O formato de `.prime/agent/settings.json` não foi inventado. A configuração
versionada atual mantém chamadas de modelo e APIs pagas desabilitadas, e o
launcher falha fechado enquanto essa condição permanecer.

## Comandos locais

A ponte uniforme retorna JSON em stdout e um erro JSON limitado em stderr. O
modo `run` é dry-run por padrão. Um ID pode ser passado por argumento ou por um
objeto JSON em `--input`; campos desconhecidos são recusados.

```sh
python3 scripts/article_loop_command.py bootstrap --root . --pdf input/inbox/artigo.pdf
python3 scripts/article_loop_command.py status --root . [--run-id RUN_ID]
python3 scripts/article_loop_command.py checkpoint --root . [--run-id RUN_ID]
python3 scripts/article_loop_command.py pause --root . [--run-id RUN_ID]
python3 scripts/article_loop_command.py resume --root . [--run-id RUN_ID]
python3 scripts/article_loop_command.py stop --root . [--run-id RUN_ID]
python3 scripts/article_loop_command.py run --root . [--run-id RUN_ID] [--cycle-id N] [--dry-run]
python3 scripts/article_loop_command.py finalize --root . [--run-id RUN_ID] [--cycle-id N]
```

`bootstrap` pode publicar os artefatos M3 e, por isso, só deve receber um PDF
regular que o operador pretende ingerir. `finalize` chama o finalizador M10 e
nunca contorna Decision, gates, diagnóstico ou hashes. Os comandos de pausa,
retomada, parada e checkpoint delegam à API durável existente; não se deve
editar JSONL, snapshots, manifests ou pointers manualmente.

## Templates Prime Agent

Os comandos `/article-bootstrap`, `/article-preflight`, `/article-run`,
`/article-status`, `/article-checkpoint`, `/article-pause`,
`/article-resume`, `/article-stop` e `/article-finalize` são descobertos
diretamente em `.prime/agent/prompts/`. Cada um chama uma única API existente,
valida seus argumentos e termina o turno quando a API registra admissão ou
espera. Não há polling textual, `gather()` ou criação implícita de filhos.

## Launcher e dry-run

```sh
bash bin/start-prime.sh
bash bin/start-prime.sh --dry-run --template article-status
```

O launcher padrão executa somente `check`, o preflight local e uma confirmação
JSON com `prime_started: false` e `model_called: false`. Ele não inicia um
processo Prime, não altera o estado e não acessa a rede.

Uma execução autorizada futura teria de ser explícita:

```sh
bash bin/start-prime.sh --live --authorize-live --template article-run
```

Antes de encaminhar apenas `--skill article-loop` e
`--prompt-template article-run` ao binário, o launcher exige configuração live
versionada, referência de autorização não vazia, orçamento positivo, ausência
de `control/STOP`, preflight M3 aprovado e `prime-agent` no `PATH`. Atualmente
o orçamento/configuração fail-closed impede essa passagem; nenhum comando
compensa isso com `sudo`, instalação, `--autonomous`, `/refine`, segredo ou
opção global.

Dentro da sessão autorizada, o adaptador real deve ser construído com as
superfícies documentadas de `rlm` e `agent_message`, após consultar e aplicar
`/rlm-max-depth 2` sem `--global`. O retorno de `rlm()` é somente um handle;
resultados detalhados devem ser receipts em arquivos canônicos.

## Comandos de continuidade do Prime Agent

Estas superfícies pertencem à sessão Prime e não substituem o estado durável
do article-loop:

- `/goal` mantém um objetivo explícito da sessão; não autoriza modelo, muda
  `run_id`/`cycle_id` nem prova uma transição científica.
- `/autonomous` é uma política de continuidade supervisionada, com gates e
  limites; não é usado por M11 e não pode ligar execução live ou ignorar STOP.
- `/refine` atua sobre estado suplementar depois de um turno e pode exigir
  modelo; não reescreve prompts imutáveis, não cria autorização e não substitui
  proposta, receipt ou evento canônico.
- `/compact` resume contexto de conversa; a compactação deve preservar, no
  projeto, run/cycle/state, hashes, filhos, issues, orçamento e próxima
  transição. Ela não reconstrói evidência nem altera o event log.

M11 não executa nenhum dos quatro comandos. Uma operação futura deve registrá-
los como ferramentas de sessão, mantendo os mesmos limites e autorizações do
run.

## Estados, pausa e STOP

O caminho inicial esperado é `NEW -> INGESTED -> SOURCE_READY`. Um ciclo
planejado passa por `CYCLE_PLANNED -> DEPARTMENTS_RUNNING`; as etapas M7--M10
continuam responsáveis pelas transições posteriores. `status` é a fonte de
consulta operacional, não uma prova científica.

Para impedir novas mutações, crie o sentinel somente com intenção explícita do
operador:

```sh
touch control/STOP
python3 scripts/article_loop_command.py status --root .
```

Não remova o sentinel durante trabalho ativo. Após a confirmação de parada e
uma decisão operacional documentada, remova-o manualmente e revalide o estado;
o comando `stop` mantém a transição durável e não promete reembolso de trabalho
incerto. `pause` preserva o estado e reservas existentes para retomada.

## Backup e recuperação

Antes de uma operação autorizada, copie para um destino separado os diretórios
de estado e evidência que pretende preservar, sem sobrescrever a origem. Nunca
edite o PDF original. Em crash, reexecute primeiro `check.sh`, consulte
`status`, e deixe as APIs de `DurableStore`/`Orchestrator` reconciliar receipts,
snapshots e locks. Não apague temporários, não reescreva eventos e não use
`git reset`, `git clean` ou `force-push` como recuperação.

## Troubleshooting

- `root must be ...`: execute o comando na raiz correta e não passe um link
  simbólico como raiz.
- `control/STOP blocks new operations`: preserve o sentinel e investigue o
  estado antes de qualquer retomada.
- `live execution is not explicitly enabled and authorized`: comportamento
  esperado com `config/budgets.yaml` fail-closed; M11 não altera esse arquivo.
- `prime-agent is not available in PATH`: a instalação externa não foi
  confirmada; não instale nem substitua o binário dentro deste projeto.
- `live execution requires an explicit PrimeRLMAdapter`: a chamada foi feita
  fora de uma sessão Prime com o adaptador injetado; use dry-run ou uma sessão
  futura explicitamente autorizada.
