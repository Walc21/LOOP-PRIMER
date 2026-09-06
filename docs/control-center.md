# Central de Controle local

A Central de Controle é uma superfície local sobre as fontes de verdade já
existentes no article-loop. Ela não inicia Prime Agent, inferência, provedores,
rede de modelo, pipeline científico, shell ou edição de arquivo arbitrário.

## Inicialização local oficial

Na raiz do repositório, com o ambiente Python do projeto que já fornece
`PyYAML` e `jsonschema`, use exclusivamente:

```sh
bash bin/start-control-center.sh
```

Abra exatamente `http://127.0.0.1:8765` no mesmo computador. O launcher
resolve a raiz atual, fixa o `PYTHONPATH` do pacote local e inicia somente o
`article_loop.control_center` canônico com bind em `127.0.0.1`. Ele rejeita
argumentos não reconhecidos, raiz inválida e portas inseguras ou inválidas.

Não abra `control_center_static/index.html` diretamente no navegador. O modo
`file://` não é suportado: ele não possui a origem HTTP que serve
`/assets/styles.css` e `/assets/app.js` nem a API canônica `/api/v1`; transformar
os assets em caminhos relativos não resolveria essa ausência e criaria uma UI
standalone incompleta.

Para trocar somente a porta, escolha uma porta local entre 1024 e 65535 e abra
a URL correspondente, por exemplo:

```sh
bash bin/start-control-center.sh --port 8766
```

Depois abra `http://127.0.0.1:8766`. Host, Origin e bind continuam limitados a
loopback. Para encerrar com segurança, mantenha o terminal do launcher em
primeiro plano e pressione `Ctrl-C`; isso para o servidor sem iniciar ou alterar
o pipeline científico.

## Autoridade e proteção

- GETs projetam snapshots, journals e logs canônicos já confirmados. Um leitor
  de orçamento usa a variante read-only e não gera alertas, locks ou logs.
- Artefatos aparecem somente como links de metadados para hashes já publicados
  no journal da run. A Central não oferece download nem leitura por caminho:
  conteúdo continua sujeito ao leitor canônico da etapa que o publicou.
- SSE usa cursor vetorial por fonte durável, com backfill e deduplicação. A UI
  sinaliza texto para ao vivo, reconexão, atualização atrasada e ausência de
  execução, e usa polling somente leitura após queda do stream.
- POSTs exigem `Origin` same-origin, confirmação, `Idempotency-Key` e hash
  esperado. O ledger `state/control-center/audit.jsonl` é separado do journal
  científico, hash-encadeado e escrito com staging, fsync, rename e fsync do
  diretório.
- Os controles são apenas `preflight`, `checkpoint`, `pause`, `resume`,
  `stop` e `finalize`; todos delegam à API canônica. Não há `run`,
  `bootstrap`, inferência, terminal, adaptador ou test double no HTTP público.
- A página do júri não mostra autor de proposta, ordem de criação nem metadados
  que revelem champion durante uma avaliação.

## Configuração

Os únicos arquivos configuráveis são `config/system.yaml`, `config/budgets.yaml`,
`config/gates.yaml`, `config/decision-policy.yaml`, todos os
`config/roles/*.yaml` e `config/rubrics/evaluation.yaml`. A UI usa descritores
tipados e rascunhos com hash-base, validação estrutural/cruzada, diff lógico e
confirmação; ela não aceita YAML arbitrário. Comandos de gates, topologia,
schemas e outros campos canônicos permanecem imutáveis.

Aplicar um rascunho só é permitido sem nenhuma run não terminal. Essa regra é
intencionalmente conservadora porque snapshots legados ainda não associam hash
global de todas as superfícies de configuração a cada run. Uma mudança nunca
é usada por uma run em andamento e configurar `enabled: true` nunca substitui
autorização hash-bound, orçamento, política de conteúdo, provider ou preflight.

## Remoção e retenção

Para remover a superfície de código, reverta exclusivamente os arquivos M14
via fluxo normal do repositório. Antes de descartar `state/control-center/`,
preserve ou exporte o ledger de auditoria conforme a política de evidência do
projeto; ele não deve ser removido como efeito colateral de parar o servidor.
