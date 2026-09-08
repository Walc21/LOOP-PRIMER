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
`text.txt` possui 316.739 bytes. A admissão não usa mais apenas bytes do prompt:
ela constrói o corpo HTTP estruturado completo e aplica o teto conservador
`ceil(bytes_do_corpo / 4 * 2) + saída_reservada + 512`. O multiplicador é uma
margem explícita, porque não foi provada equivalência entre a contagem local e
o tokenizer do runner. Aumentar o limite apenas deslocaria a fronteira e não
registraria por que determinado conteúdo foi escolhido. O smoke também não
trunca texto, escolhe primeiras páginas, usa OCR ou inventa fallback.

Antes do preflight, o operador precisa decidir quais páginas integrais ou quais
segmentos de linhas canônicas já registrados em `normalized.json` são
pertinentes. Não existe seleção default, e a ferramenta não toma essa decisão
científica. Ela é inerte sem `--create`; com a flag, cria uma única vez um
manifesto `selection-UUID.json` sob a raiz allowlisted, sem modificar M3.

Seleção histórica por página integral:

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

Seleção nova por segmentos inclusivos de linhas:

```bash
python3 scripts/m6_context_selection.py \
  --m3-root 'runtime/m3-real-attempts/attempt-<UUID>' \
  --m3-run-id 'ingest-<sha256-do-pdf>' \
  --output 'runtime/m6-context-selections/selection-<UUID>.json' \
  --segment '<pagina>:<linha-inicial>:<linha-final>' \
  --create
```

`--segment` pode ser repetido, mas não pode ser misturado com `--page`.
Página e linhas são identificadores numéricos canônicos do M3; os limites são
inclusivos e as linhas são os índices globais que `normalized.json` associa à
página. Segmento de uma linha, como `1:17:17`, é válido. Intervalo invertido,
vazio, fora da página, inexistente, duplicado ou sobreposto é recusado. A ordem
persistida é sempre `(página, linha inicial, linha final)`. Segmentos
adjacentes continuam distintos: não existe merge, expansão, preenchimento de
lacuna ou contexto adicional implícito.

O manifesto de página inteira mantém a versão `1.0.0` e continua legível
exatamente como foi criado. Ele não é reescrito, migrado ou reinterpretado.
O manifesto de segmentos usa `2.0.0`, `selection_kind=line_segments` e cada
unidade contém `unit_id`, locator, página, limites, tamanho e SHA-256 dos
bytes reconstruídos. O topo vincula run, binding M3, artefato extraído e
`normalized.json`, além do tamanho e SHA-256 do agregado canônico ordenado
dos fragmentos. `selection_hash` vincula o manifesto inteiro sem seu próprio
campo de hash.

A CLI de criação aceita somente paths relativos contidos nas raízes runtime
allowlisted. Path absoluto, travessia, barra invertida, symlink, arquivo não
regular, raiz externa ou destino existente falha fechado. A API interna recebe
as allowlists explicitamente e aplica a mesma contenção. O operador nunca
fornece texto do artigo, bytes, hash, prompt, path de conteúdo, intervalo por
byte nem consulta semântica.

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
  --structured-output-dialect openai_chat_completions_json_schema \
  --deadline-utc '<data-hora-UTC-absoluta>' \
  --timeout-seconds '<segundos>' \
  --context-limit '<tokens>' \
  --max-output-tokens 2048
```

Esse exemplo não executa nada porque omite deliberadamente `--execute` e
`--human-authorized`. Adicionar ambos é uma decisão operacional futura e exige
modelo, endpoint e deadline atuais confirmados pelo operador.

Antes dessa decisão, acrescente somente `--preflight-only`. Esse modo relê M3 e
o manifesto, reconstrói os fragmentos, valida task/schema e compila o prompt
final com wrapper. A resposta `READY` informa, sem conteúdo científico, hashes
e tamanhos do prompt, mensagens, schema científico, `response_format`,
envelope e corpo HTTP, além do teto conservador de entrada, saída reservada,
margem e total. Também informa versão/tipo da seleção, segmentos, páginas,
limites, hashes, tamanhos dos fragmentos e do contexto materializado e
`headroom_tokens`. Em overflow, `BLOCKED` inclui a mesma decomposição, com
headroom negativo e o motivo, sem expor texto, prompt completo, PDF, resposta,
segredo ou credencial. Uso reportado por uma chamada anterior nunca ajusta essa
admissão. Ele não exige autorização live, não cria a tentativa e não chama
endpoint. Uma falha prevista responde JSON `BLOCKED` com exit 2 e sem
traceback.

O dialeto é obrigatório e único: `openai_chat_completions_json_schema`, com
path exato `/v1/chat/completions`, `temperature=0` e
`response_format.type=json_schema`, `strict=true`. Antes de admitir, o comando
verifica offline que o executável Ollama corresponde ao perfil local auditado
por SHA-256, versão vinculada ao hash e marcadores estáticos da rota e dos
campos OpenAI. Essa
verificação não inicia servidor, não consulta endpoint e não prova que o modelo
obedecerá ao schema; uma resposta fora do contrato ainda termina
`FAILED_OUTPUT`. Binário ausente, atualizado ou divergente exige nova auditoria
e bloqueia antes da tentativa. Não existe API nativa ou fallback automático de
dialeto.

Os limites não são opções ajustáveis: `max_calls=1`, `max_concurrency=1`,
`max_retries=0`, `max_cycles=1`, custo máximo zero, `deny_remote=true`, target
único e nenhum fallback. O endpoint aceita somente HTTP com host textual exato
`127.0.0.1` e porta explícita. `localhost`, IPv6, `0.0.0.0`, interface LAN,
URL remota e `file://` são recusados.

Para W11, 2.048 tokens são o teto recomendado para a próxima smoke e o mínimo
aceito pelo contrato oficial. `context_limit` continua 8.192. Se a requisição
com 2.048 tokens não comportar a seleção existente das páginas 1 e 3, o
operador precisará escolher e criar, sob nova decisão, outro manifesto M3
create-only mais compacto. O smoke não altera nem substitui seleções existentes.

No preflight offline de 2026-09-08, a seleção existente das páginas 1 e 3 foi
recusada antes de criar a tentativa: 12.010 tokens conservadores de entrada,
2.048 de saída e 512 de margem totalizaram 14.570 para um limite de 8.192. Esse
resultado não escolhe automaticamente outra evidência e não autoriza nova run.

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
inference receipt e outcome. `inputs/request-manifest.json` vincula dialeto,
endpoint, formato, prova de compatibilidade, hashes e tamanhos da requisição.
M3 e seleção são revalidados uma segunda vez
imediatamente antes de route/reserve/backend. A ordem operacional permanece
`route -> reserve -> admit -> backend -> receipt -> reconcile -> stop`.
Ambiguidade pós-envio permanece `UNCERTAIN`, sem release, refund ou retry.

Esta superfície é preparação operacional. Sua presença no repositório não
autoriza modelo, servidor local, rede, Prime Agent nem execução científica.
