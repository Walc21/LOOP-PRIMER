# article-loop

Integração auditável do Prime Agent para revisão iterativa de
artigos matemáticos. O projeto separa entrada imutável, propostas de 21 papéis,
challengers, gates determinísticos, júri cego, decisão e finalização
transacional.

O Marco 3 acrescenta ingestão local e offline: coloque exatamente um PDF
regular em `input/inbox/artigo.pdf` e execute `bin/preflight.sh`. O comando
preserva o original em `artifacts/original/<sha256>/`, extrai derivados locais
e publica `versions/champion/v0000` somente depois do gate `SOURCE_READY`.
Reexecutar o mesmo PDF é idempotente somente depois de revalidar hashes,
manifests e árvores sem symlink; qualquer arquivo ambíguo ou existente
divergente falha sem sobrescrever evidência. PDF e `source.zip` são congelados
em staging antes da inspeção. `source.zip` é aceito apenas após inspeção UTF-8,
anti-traversal, anti-duplicidade/criptografia/symlink e com estrutura LaTeX
confirmada. O log durável registra `NEW → INGESTED → SOURCE_READY`.

PDF escaneado sem OCR não recebe texto inventado: o manifest contém issues e o
gate falha por falta de cobertura textual. Nenhum comando inicia o Prime Agent,
modelo, rede ou API paga.

## Validação local

Crie um ambiente virtual local e instale somente as dependências declaradas:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest -v control.test_contracts
```

Não instale essas dependências globalmente. O teste é offline depois que o
ambiente local contém as versões fixadas em `requirements-dev.txt`.

## Comandos

- `bin/preflight.sh` — ingestão e gate local `SOURCE_READY`;
- `bin/check.sh` — futura entrada única de verificações;
- `bin/start-prime.sh` — futuro início explicitamente autorizado do Prime Agent.

Não execute o Prime Agent, modelos ou APIs pagas durante a construção sem
autorização específica.
