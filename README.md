# article-loop

Scaffold de uma integração auditável do Prime Agent para revisão iterativa de
artigos matemáticos. O projeto separa entrada imutável, propostas de 21 papéis,
challengers, gates determinísticos, júri cego, decisão e finalização
transacional.

O Marco 1 contém somente contratos declarativos, schemas e validações locais.
Não há orquestração, chamada de modelo ou processamento de PDF implementado.

## Validação local

Crie um ambiente virtual local e instale somente as dependências declaradas:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest -v control.test_contracts
```

Não instale essas dependências globalmente. O teste é offline depois que o
ambiente local contém as versões fixadas em `requirements-dev.txt`.

## Comandos futuros

Os caminhos abaixo estão reservados, mas permanecem inertes até seus marcos:

- `bin/preflight.sh` — futuro preflight local;
- `bin/check.sh` — futura entrada única de verificações;
- `bin/start-prime.sh` — futuro início explicitamente autorizado do Prime Agent.

Não execute o Prime Agent, modelos ou APIs pagas durante a construção sem
autorização específica.
