---
name: article-loop
description: Núcleo local do article-loop; stub de contrato do Marco 1.
---

# article-loop

Esta skill será o núcleo executável da integração. No Marco 1 ela documenta
somente a superfície assíncrona `run()` e falha de forma explícita se chamada.
Não inicia agentes, modelos, rede ou operações de runtime.

Os marcos futuros devem preservar os contratos em `config/schemas/` e só podem
ativar integração Prime Agent após o preflight previsto em
`docs/compatibility.md`.
