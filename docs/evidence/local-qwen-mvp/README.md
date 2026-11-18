# Registros do MVP local com Qwen2.5

O LOOP-PRIMER concluiu uma execução com **inferência real de ponta a ponta**.
A tentativa `attempt-d45eb426-2b1b-4a4b-837f-26d631cf0573` chegou a
`CYCLE_COMPLETE`, aplicou `REJECT` e teve a auditoria M13 aprovada. O auditor
confirmou o PDF original, a avaliação, a decisão e os 12 recibos reconciliados.

| Registro | Arquivo |
|---|---|
| Artigo sintético e edição | [PDF original](artigo-original.pdf), [LaTeX original](original.tex), [LaTeX revisado](revisado.tex) |
| Gates e avaliação cega | [Resumo dos 13 gates](gate-summary.json), [avaliação com meta-parecer](evaluation.json) |
| Decisão aplicada | [Decisão](decision.json), [referência de rejeição](rejection-reference.json), [recibo de finalização](finalization-receipt.json) |
| Resultado e verificação independente | [Resultado da CLI](outcome.json), [auditoria M13](audit.json) |
| Histórico e dados completos do recorte público | [Linha do tempo](timeline.json), [arquivo de registros](registros-qwen.zip), [SHA-256](SHA256SUMS) |

## Linha do tempo

| Tentativa | Resultado registrado |
|---|---|
| `a4a07eb4` | 13 gates aprovados e seis pareceres válidos. A meta-revisão retornou `schema_invalid`. |
| `1a666fd5` | O diagnóstico confirmou `OUTPUT_SCHEMA_INVALID` no JSON da meta-revisão. |
| `11eafb0d` | Meta-parecer válido. O ciclo registrou `REQUEST_EXTRA_JUDGMENT`, com auditoria desse pedido em modo separado. |
| `d45eb426` | Entrega de ponta a ponta auditada. A política aplicou `REJECT` após o júri reprovar o candidato no critério matemático. |

O ZIP contém os quatro planos, eventos, registros de orçamento, rotas e
recibos, saídas válidas de inferência, diagnósticos, decisões e auditorias
quando disponíveis. Inclui os arquivos sintéticos de entrada e as versões
LaTeX. Cada entrada consta do `SHA256SUMS` interno. Os arquivos vinculados a
caminhos da máquina original estão representados em
`local-path-bound-sha256.json`, junto aos resumos públicos por tentativa.

O arquivo é um exporte documental. A reexecução do auditor M13 sobre a
evidência original exige a raiz de trabalho em que o ciclo foi executado.
O [roteiro da demonstração](../../demo-mvp-local.md) mostra como rodar um
ciclo novo e como consultar a auditoria já concluída.
