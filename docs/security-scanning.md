# Alertas de code scanning

Os cinco alertas da captura têm tratamentos diferentes. O encerramento no
GitHub depende da publicação das mudanças e de uma nova análise da branch
`main`; uma execução de workflow com sucesso não prova ausência de alertas.

| Alerta | Evidência e tratamento |
| --- | --- |
| #44 — caminho em `store.py` | Contenção após normalização, rejeição de symlinks, arquivos especiais e entradas JSON malformadas; regressões em `control/test_store_journal_paths.py`. |
| #43 — caminho em `orchestrator.py` | Mesmas barreiras na leitura M6, incluindo rejeição da raiz symlink antes de resolver; regressões em `control/test_orchestrator_journal_paths.py`. |
| #13 — Fuzzing | Alvo Atheris real em `fuzz/fuzz_journals.py`, corpus sintético versionado e workflow `fuzz.yml` para PRs, pushes e execução semanal. |
| #12 — SAST | Workflow `codeql.yml` em PRs/pushes, com consultas `security-extended` para Python. O Scorecard também considera verificações nos PRs históricos; a pontuação precisa ser reavaliada após novas execuções. |
| #11 — CII-Best-Practices | Cadastro e autoavaliação no OpenSSF Best Practices pendentes. Este selo é uma avaliação externa do projeto. |

O SAST Python cobre os módulos em `.prime`, scripts e testes. A cobertura SAST
do JavaScript da interface continua pendente, conforme ADR-045.

## Fuzzing reproduzível

A CI utiliza CPython 3.12 em Linux x86_64, com Atheris fixo por versão e hash.
O alvo grava somente dois arquivos fixos em uma raiz temporária e valida
identificadores sem acessar os paths fornecidos. Cada entrada tem no máximo
4096 bytes; a campanha dura 60 segundos, com timeout de 5 segundos por entrada
e teto de memória de 1024 MiB. Entradas que causarem falha ficam disponíveis
como artefatos da CI por cinco dias.

Para reproduzir localmente com CPython 3.12 disponível, crie um ambiente de
ferramentas dentro da `.venv`, preservando o runtime canônico CPython 3.14:

```sh
python3.12 -m venv .venv/fuzz
.venv/fuzz/bin/python -m pip install --require-hashes -r requirements-ci.txt -r requirements-fuzz.txt
fuzz_corpus="$(mktemp -d)"
cp fuzz/corpus/* "$fuzz_corpus/"
.venv/fuzz/bin/python fuzz/fuzz_journals.py "$fuzz_corpus" -max_total_time=60 -timeout=5 -rss_limit_mb=1024 -max_len=4096 -seed=1 -artifact_prefix="$fuzz_corpus/"
```

As regressões determinísticas continuam na suíte normal, sem exigir Atheris:

```sh
.venv/bin/python -m unittest control.test_store_journal_paths control.test_orchestrator_journal_paths -q
```

## Cadastro CII/OpenSSF

O mantenedor precisa abrir [OpenSSF Best Practices](https://www.bestpractices.dev/),
autenticar sua conta e cadastrar `https://github.com/Walc21/LOOP-PRIMER`.
Depois deve responder à autoavaliação com evidências verificáveis. Fontes
disponíveis para a avaliação incluem:

- [Licença MIT](../LICENSE), [documentação](../README.md) e [contribuição](../CONTRIBUTING.md).
- [Política e canal privado de segurança](../SECURITY.md).
- [Suíte de testes](../.github/workflows/ci.yml), [SAST](../.github/workflows/codeql.yml) e [fuzzing](../.github/workflows/fuzz.yml).
- [Decisões e limites conhecidos](decisions.md).

Critérios sem evidência precisam ser tratados antes da declaração. Após obter
o status e o identificador reais do projeto, o mantenedor pode publicar o badge
correspondente no README e conferir uma nova execução do Scorecard.
