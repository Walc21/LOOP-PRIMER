# Demonstração do LOOP-PRIMER com inferência local

O ciclo terminou em `CYCLE_COMPLETE` em **2 min 32 s**. O sistema aplicou
`REJECT` à revisão e a auditoria independente confirmou a entrega. O
produtor e o júri usaram o Ollama local, com janela de 16.384 tokens. A run
reconciliou as **12 chamadas reais**, que somaram **28.360 tokens**, a custo
externo zero. [Resultado da execução](evidence/local-qwen-mvp/outcome.json)

## O que mostrar

1. Abra o [PDF original](evidence/local-qwen-mvp/artigo-original.pdf).
   O artigo sintético tem uma página e prova que, se \(x=1\), então \(x+x=2\).
2. Compare a [fonte original](evidence/local-qwen-mvp/original.tex)
   e a [fonte revisada](evidence/local-qwen-mvp/revisado.tex).
   A alteração explicita a substituição \(x+x=1+1=2\). Cinco propostas do produtor chegaram à síntese.
3. Mostre o [resumo dos 13 gates](evidence/local-qwen-mvp/gate-summary.json).
   Todos passaram, inclusive a verificação aritmética independente da afirmação sintética.
4. Abra a [avaliação cega](evidence/local-qwen-mvp/evaluation.json).
   O Qwen2.5 1.5B produziu os seis pareceres e a meta-revisão. Dois pares foram
   consistentes na inversão A/B, ambos com empate. O terceiro divergiu.
   Os pareceres consistentes marcaram a matemática do candidato como não
   aprovada pelo júri. Os três papéis usam o mesmo modelo, com garantia de
   diversidade reduzida registrada na avaliação.
5. Mostre a [decisão registrada](evidence/local-qwen-mvp/decision.json)
   e a [rejeição publicada](evidence/local-qwen-mvp/rejection-reference.json).
   O critério de matemática do júri levou a `GATE_FAILED` na decisão. A
   confirmação da meta-revisão não substituiu esse critério. O PDF original
   foi preservado e a revisão ficou rastreável.

## Consultar ou repetir a auditoria

A [auditoria publicada](evidence/local-qwen-mvp/audit.json) saiu de um
processo separado e devolveu o mesmo resultado da CLI, incluindo `status: pass`.
Os [registros públicos](evidence/local-qwen-mvp/README.md) permitem conferir os
recibos, a linha do tempo e os hashes. Na máquina com a raiz da execução
original, o comando abaixo revalida o ciclo sem fazer inferência.

```bash
python3 scripts/m13_system_check.py \
  --verify-root runtime/local-full-cycle/attempt-d45eb426-2b1b-4a4b-837f-26d631cf0573 \
  --run-id ingest-4d07d27bcd2e2a85ab58dca0ad4ad60a9dd193fc90ddb4a29eaa9e3847f3bb46
```

## Repetir a demonstração ao vivo

Com o mesmo artigo sintético na caixa de entrada e os aliases no Ollama
local, prepare uma nova tentativa. Uma execução nova pode chegar a uma
decisão diferente, porque os pareceres são gerados de novo.

```bash
set -eu
loop_demo_plan=$(python3 scripts/local_loopback_full_cycle.py prepare \
  --producer-model loop-primer-producer:16k \
  --producer-context-32k-model loop-primer-producer:32k \
  --juror-model loop-primer-juror-qwen25:16k \
  --juror-context-32k-model loop-primer-juror-qwen25:32k)
loop_demo_attempt=$(printf '%s\n' "$loop_demo_plan" | python3 -c 'import json, sys; print(json.load(sys.stdin)["attempt_id"])')
python3 scripts/local_loopback_full_cycle.py preflight --attempt-id "$loop_demo_attempt"
loop_demo_deadline=$(date -u -d '+60 minutes' +%FT%TZ)
python3 scripts/local_loopback_full_cycle.py run --attempt-id "$loop_demo_attempt" \
  --human-authorized --deadline-utc "$loop_demo_deadline" --synthetic-article
```
