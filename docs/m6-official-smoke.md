# Smoke oficial M6 de uma tarefa

Esta entrada prepara uma futura prova operacional mínima do caminho routed. Ela
executa no máximo uma `AgentTask`, para `S10` ou `W11`, e termina sem iniciar
M7, síntese, júri, novo ciclo, continuação ou retry.

O comando é inerte por padrão. Sem `--execute`, ele valida a forma dos
argumentos, responde `DISABLED` e não cria a tentativa. Uma execução real exige
também `--human-authorized`; os dois booleanos valem somente para a invocação
corrente. Arquivo JSON, configuração persistida e variável de ambiente não
substituem essa autorização. A CLI não oferece opção para autorizar doubles.

## Seleção M3 explícita

O agregado M3 não é um contexto padrão. Na evidência de 77 páginas,
`text.txt` possui 316.739 bytes; com `context_limit=8192`, saída reservada de
512 tokens e overhead de 512 tokens, restam aproximadamente 28.672 bytes para
a materialização preliminar. Aumentar o limite apenas desloca essa fronteira e
não registra por que determinado conteúdo foi escolhido. O smoke também não
trunca texto, escolhe primeiras páginas, usa OCR ou inventa fallback.

Antes do preflight, o operador precisa decidir quais blocos integrais de página
já registrados em `normalized.json` são pertinentes. Não existe seleção
default. A ferramenta abaixo é inerte sem `--create`; com a flag, cria uma única
vez um manifesto `selection-UUID.json` sob a raiz allowlisted, sem modificar M3:

```bash
python3 scripts/m6_context_selection.py \
  --m3-root '<raiz-direta-runtime/m3-real-attempts/attempt-UUID>' \
  --m3-run-id 'ingest-<sha256-do-pdf>' \
  --output 'runtime/m6-context-selections/selection-<UUID>.json' \
  --page '<pagina-explicitamente-escolhida>' \
  --create
```

`--page` pode ser repetido. A ferramenta ordena os blocos e rejeita duplicatas,
página inexistente, path fora da raiz, symlink e destino preexistente. O
manifesto não contém texto livre nem path de conteúdo fornecido pelo operador:
ele registra locators estruturais, intervalos integrais de linhas, tamanhos e
hashes derivados de M3, além dos hashes do binding, do artefato extraído e de
`normalized.json`.

## Contrato do comando

```bash
python3 scripts/m6_official_smoke.py \
  --m3-root '<raiz-direta-runtime/m3-real-attempts/attempt-UUID>' \
  --m3-run-id 'ingest-<sha256-do-pdf>' \
  --attempt-root '<raiz-direta-runtime/m6-official-smokes/attempt-UUID-novo>' \
  --selection-manifest 'runtime/m6-context-selections/selection-<UUID>.json' \
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

Antes dessa decisão, acrescente somente `--preflight-only`. Esse modo relê M3 e
o manifesto, reconstrói os fragmentos, valida task/schema e compila o prompt
final com wrapper. A resposta `READY` informa, sem conteúdo científico, bytes
do prompt/contexto, estimativa de entrada, saída reservada, overhead e total.
Ele não exige autorização live, não cria a tentativa e não chama endpoint. Uma
falha prevista responde JSON `BLOCKED` com exit 2 e sem traceback.

Os limites não são opções ajustáveis: `max_calls=1`, `max_concurrency=1`,
`max_retries=0`, `max_cycles=1`, custo máximo zero, `deny_remote=true`, target
único e nenhum fallback. O endpoint aceita somente HTTP com host textual exato
`127.0.0.1` e porta explícita. `localhost`, IPv6, `0.0.0.0`, interface LAN,
URL remota e `file://` são recusados.

## Evidência e parada

A raiz M3 deve ser uma tentativa canônica explícita em `SOURCE_READY`. O fluxo
revalida event log, identidade do PDF, source identity, manifests, hashes das
árvores original/extracted/rendered, champion e gate `SOURCE_READY`; em seguida
revalida o manifesto e reconstrói cada bloco diretamente de `normalized.json`.
Task, view, prompt compilado, wrapper, contexto, saída reservada e overhead
precisam caber antes de a raiz M6 existir. Seleção ausente, incompleta,
adulterada, com locator/hash divergente, symlink, travessia ou overflow retorna
`BLOCKED` sem attempt, route, ledger, reserva, receipt, backend ou custo.

A raiz M3 é somente leitura. A raiz M6 deve não existir e é criada uma única
vez; reentrada, retomada e sobrescrita são recusadas. Ela preserva configuração,
autorização da invocação, binding M3, cópia byte a byte do manifesto de seleção,
task, view, prompt, decomposição da admissão, route, budget events, output,
inference receipt e outcome. M3 e seleção são revalidados uma segunda vez
imediatamente antes de route/reserve/backend. A ordem operacional permanece
`route -> reserve -> admit -> backend -> receipt -> reconcile -> stop`.
Ambiguidade pós-envio permanece `UNCERTAIN`, sem release, refund ou retry.

Esta superfície é preparação operacional. Sua presença no repositório não
autoriza modelo, servidor local, rede, Prime Agent nem execução científica.
