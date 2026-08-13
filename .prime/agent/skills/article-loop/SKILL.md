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
inválido, IDs repetidos e hash/encadeamento divergentes levantam
`IntegrityError`; o store não os repara silenciosamente. `control/STOP`
bloqueia operações novas depois da aquisição do lock.

A função assíncrona `run(*args, **kwargs)` permanece deliberadamente
indisponível e levanta `RuntimeError` até a integração autorizada do Marco 6.

Os marcos futuros devem preservar os contratos em `config/schemas/` e só podem
ativar integração Prime Agent após o preflight previsto em
`docs/compatibility.md`.
