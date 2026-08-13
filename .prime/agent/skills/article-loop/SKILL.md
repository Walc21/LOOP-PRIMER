---
name: article-loop
description: Núcleo local de estado durável do article-loop, sem runtime Prime Agent.
---

# article-loop

No Marco 2, esta skill fornece somente persistência local, offline e
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

A função assíncrona `run(*args, **kwargs)` permanece deliberadamente
indisponível e levanta `RuntimeError` até a integração autorizada do Marco 6.

Os marcos futuros devem preservar os contratos em `config/schemas/` e só podem
ativar integração Prime Agent após o preflight previsto em
`docs/compatibility.md`.
