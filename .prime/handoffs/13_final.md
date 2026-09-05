# Handoff final M13 — sistema e entrega offline

M13 concluído na aceitação offline sobre a baseline `b15526e`, inicialmente em
`main`. Trabalho isolado em `m13-system-delivery`, com commit local autorizado
e sem push. Nenhum modelo, Prime Agent live, provedor remoto, API paga ou artigo
real foi executado. Os 21 papéis, 16 estados, 9 ações e schemas canônicos foram
preservados.

## Entrega e comando

```sh
python3 scripts/m13_system_check.py
```

25 testes compõem ingestão, prompts, blackboard/ativação, 15 propostas M6,
5 pacotes departamentais, síntese/merge, challenger imutável, 13 gates, júri em
duas ordens, meta-review, diagnóstico, Decision e finalizador até promoção,
Pareto ou rejeição. Os cenários negativos verificam veto matemático, viés
posicional, GateReport trocado, adulteração, replay, interrupção após rename e
duas finalizações concorrentes.

`--keep-workspace CAMINHO_NOVO` conserva uma execução sintética fora do Git;
`--verify-root CAMINHO --run-id ID` audita a evidência existente sem executar ou
reparar o pipeline. A API pública é `article_loop.verify_delivery`. O relatório
deriva identidades/hashes de original, baseline, propostas/pacotes, síntese,
candidato, gates, comparação/vereditos, diagnóstico, Decision, receipt e
destino publicado. `reports/m13-delivery.json` é resumo derivado, não autoridade.

O original sintético tem 644 bytes e SHA-256
`1a491e111064f6daae4011f46337a188de4e91337d692b3cc74b4b221d17501f`,
idêntico antes/depois. A promoção entrega fonte LaTeX revisada; `baseline.pdf`
continua sendo o original preservado, não um PDF recompilado da revisão.

## Integração e validação

- `delivery.py` reutiliza validadores M3/M7/M8/M9/M10, compara publicação/evento
  e vincula ledger, route, output, inference receipt e receipt M6.
- M9 permite revalidação explícita depois de `FINALIZATION_APPLIED` do mesmo
  ciclo. A API normal de refoco continua recusando estado concluído.
- S40 routed usa três respostas científicas falsas, materializador e runtime
  reais e envelope de protocolo pertencente ao LOOP. Replay não reinfere.
- Independência por modelo é verificada no router com produtor/jurado fictícios
  distintos. Não havia adaptador operacional routed de jurado/meta-revisor M8,
  e nenhum foi acrescentado; essa integração live permanece posterior.
- Aceitação CLI: 25 testes, 0 falhas/erros/skips. Execução conservada e auditada
  em outro processo: relatório idêntico e todos os bytes/modos preservados.
- Adjacentes M9/M10/handoff: 82 testes OK.
- Regressão integral: 445 testes OK, 0 skips, em Python 3.14.4.
- `py_compile`, `git diff --check`, `bin/check.sh`: OK. Gramática Python 3.11:
  50 arquivos OK. Python 3.11 local não tem `jsonschema`; não houve instalação.
- CI mantém Python 3.11/3.12/3.13 e inclui M13 pela descoberta integral; não foi
  acionada/publicada nesta sessão.

## Limites preservados

A prova é de sistema offline e de disposição de ciclo. Não certifica matemática
arbitrária, qualidade de modelo, júri routed live, provedor/pagamento nem artigo
terminal por `FINALIZE`. Este último mantém a evidência W22/W51/W53 e testes
M10.1. O verificador de M13 cobre promoção/Pareto/rejeição, exige workspace
quiescente e conserva locators M6 originais; cópia para outro caminho não é
uma migração validada. Timestamps/metadados variam entre execuções; replay na
mesma execução preserva bytes/IDs. Auditoria não protege contra reescrita
conjunta de toda a raiz confiável e seus hashes.

Matriz A–T e instruções completas: `docs/m13-system-acceptance.md`.
Configuração versionada permanece disabled, sem targets, rotas ou credenciais.
