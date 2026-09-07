# Smoke oficial M6 de uma tarefa

Esta entrada prepara uma futura prova operacional mínima do caminho routed. Ela
executa no máximo uma `AgentTask`, para `S10` ou `W11`, e termina sem iniciar
M7, síntese, júri, novo ciclo, continuação ou retry.

O comando é inerte por padrão. Sem `--execute`, ele valida a forma dos
argumentos, responde `DISABLED` e não cria a tentativa. Uma execução real exige
também `--human-authorized`; os dois booleanos valem somente para a invocação
corrente. Arquivo JSON, configuração persistida e variável de ambiente não
substituem essa autorização. A CLI não oferece opção para autorizar doubles.

## Contrato do comando

```bash
python3 scripts/m6_official_smoke.py \
  --m3-root '<raiz-direta-runtime/m3-real-attempts/attempt-UUID>' \
  --m3-run-id 'ingest-<sha256-do-pdf>' \
  --attempt-root '<raiz-direta-runtime/m6-official-smokes/attempt-UUID-novo>' \
  --role W11 \
  --model '<modelo-local-explicito>' \
  --endpoint 'http://127.0.0.1:<porta>/v1/chat/completions' \
  --deadline-utc '<data-hora-UTC-absoluta>' \
  --timeout-seconds '<segundos>' \
  --context-limit '<tokens>' \
  --max-output-tokens '<tokens>'
```

Esse exemplo não executa nada porque omite deliberadamente `--execute` e
`--human-authorized`. Adicionar ambos é uma decisão operacional futura e exige
modelo, endpoint e deadline atuais confirmados pelo operador.

Os limites não são opções ajustáveis: `max_calls=1`, `max_concurrency=1`,
`max_retries=0`, `max_cycles=1`, custo máximo zero, `deny_remote=true`, target
único e nenhum fallback. O endpoint aceita somente HTTP com host textual exato
`127.0.0.1` e porta explícita. `localhost`, IPv6, `0.0.0.0`, interface LAN,
URL remota e `file://` são recusados.

## Evidência e parada

A raiz M3 deve ser uma tentativa canônica explícita em `SOURCE_READY`. O fluxo
revalida event log, identidade do PDF, source identity, manifests, hashes das
árvores original/extracted/rendered, champion e gate `SOURCE_READY` antes de
materializar contexto e novamente imediatamente antes de route. Symlinks,
travessia, ausência ou divergência interrompem o fluxo sem backend.

A raiz M3 é somente leitura. A raiz M6 deve não existir e é criada uma única
vez; reentrada, retomada e sobrescrita são recusadas. Ela preserva configuração,
autorização da invocação, binding M3, task, view, prompt, route, budget events,
output, inference receipt e outcome. A ordem operacional permanece
`route -> reserve -> admit -> backend -> receipt -> reconcile -> stop`.
Ambiguidade pós-envio permanece `UNCERTAIN`, sem release, refund ou retry.

Esta superfície é preparação operacional. Sua presença no repositório não
autoriza modelo, servidor local, rede, Prime Agent nem execução científica.
