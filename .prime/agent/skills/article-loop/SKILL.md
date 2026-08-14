---
name: article-loop
description: Núcleo local de estado durável do article-loop, sem runtime Prime Agent.
---

# article-loop

Até o Marco 5, esta skill fornece persistência, ingestão e planejamento local, offline e
determinística. Não inicia agentes, modelos, rede ou operações de runtime.

## API pública

`DurableStore(root, *, fault=None)` mantém um JSONL encadeado por `run_id`
seguro e snapshots derivados. Seus métodos públicos são:

- `create_run(run_id, *, actor_id="system", event_id=None)`;
- `record(run_id, target, *, event_id, idempotency_key, actor_id, ...)`;
- `read_events(run_id)`, `snapshot(run_id)`,
  `rebuild_snapshot(run_id, *, persist=True)` e `checkpoint(run_id)`;
- `pause(run_id, **kwargs)` e `resume(run_id, **kwargs)`.

`State`, `TransitionError`, `StoreError`, `IntegrityError` e `StopRequested`
também são exportados. O log é a fonte de verdade: linhas parciais, JSON
inválido, IDs repetidos, hash/encadeamento divergentes e replay que viole a
máquina de estados levantam `IntegrityError`; o store não os repara
silenciosamente. Um append prepara a versão integral do JSONL em temporário no
mesmo filesystem, aplica `fsync` e `os.replace`, sincroniza o diretório quando
suportado e verifica o resultado. Temporários órfãos não alteram o replay.
`control/STOP` bloqueia operações novas depois da aquisição do lock.

Antes do lock/commit, `record()` rejeita os parâmetros estruturais inválidos:
IDs e tipo de evento vazios, chave de idempotência vazia ou maior que 256,
`run_id` inseguro, payload não objeto e hashes de artefato não únicos ou fora
do SHA-256 hexadecimal minúsculo. Durante o replay, o mesmo contrato fechado
de `event.schema.json` é aplicado integralmente, incluindo versão `1.1.0`,
inteiros não booleanos, data ISO 8601 com fuso e hashes por posição no log.

`ingest(root, *, fault=None)` é o preflight M3. Ele congela exatamente o PDF
regular `input/inbox/artigo.pdf` (e o ZIP opcional) antes de qualquer leitura,
preserva os bytes congelados por SHA-256 em
`artifacts/original/<sha256>/document.pdf` e registra `INGESTED` com caminho,
tamanho, hash e modo de fonte antes de extração, renderização ou gate. Só então
usa Poppler local e, após o gate local `SOURCE_READY`, publica
`versions/champion/v0000`; os IDs NEW → INGESTED → SOURCE_READY são
determinísticos. A identidade imutável registrada nos dois eventos e no
`ingestion-manifest` inclui SHA-256 do PDF, presença de `source.zip`, seu
SHA-256/tamanho quando presente e o `source_mode`; retomada e idempotência
rejeitam ZIP adicionado, removido ou alterado. Antes de qualquer escrita, os oito diretórios gerenciados são
validados sem symlinks e dentro da raiz; cada árvore em staging sincroniza
todos os arquivos e diretórios antes do rename. Um `source.zip` só é usado se
todos os membros `.tex` que seriam copiados tiverem LaTeX UTF-8 com chaves,
ambientes e um único `document` estruturalmente válidos; em dúvida, a execução
usa `PDF_ONLY_RECONSTRUCTION` e registra issue.
O retorno informa `created` ou `idempotent` somente após revalidar artefatos,
manifests, hashes e árvores sem symlink. PDFs sem texto recebem classificação
escaneada e issue de OCR desligado; nenhuma fórmula ou símbolo é inferido. A
reconstrução LaTeX escapa toda extração não confiável e é compilada em diretório
isolado com `-no-shell-escape`. `IngestionError` e `SourceReadyError` explicam
entradas inseguras ou baseline insuficiente.

A função assíncrona `run(*args, **kwargs)` permanece deliberadamente
indisponível e levanta `RuntimeError` até a integração autorizada do Marco 6.

## Memória e ativação M5

`Blackboard(root)` mantém ledgers JSONL append-only, separados por execução,
para claims, issues, tasks, dependencies, evidence e decisions. `append()`
rejeita conflito de identificador; `claims()` projeta a revisão mais recente
sem apagar a trilha; `impact()` produz claims, objetos documentais e papéis
afetados. Claims exigem texto, tipo, localização, dependências, evidências,
status, severidade, SHA-256 de fonte e ciclo da última validação; seu ID é
determinístico.

`ActivationPlanner(limits).plan(...)` é puro e retorna `ActivationPlan`, sem
disparar papel algum. Ele emite entradas RUN/CHECK/SHIFT/FREEZE, checkpoint de
pausa se algum limite for excedido e um `activation_map.json` recusando
sobrescrita. `specialist_view`, `submanager_view` e `manager_view` expõem,
respectivamente, apenas dados locais, propostas dos filhos e cinco pacotes
departamentais. A integração M6 deverá respeitar `paused` e nunca criar tarefa
ou chamada para entradas FREEZE.

Os marcos futuros devem preservar os contratos em `config/schemas/` e só podem
ativar integração Prime Agent após o preflight previsto em
`docs/compatibility.md`.
