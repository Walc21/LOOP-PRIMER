# Evidência do MVP local com Qwen2.5

A tentativa `attempt-a4a07eb4-c74f-4b19-b7d8-94a3e14df238` processou o artigo
sintético de uma página. O produtor local registrou cinco propostas válidas,
o candidato passou nos 13 gates e o Qwen2.5 1.5B Instruct produziu os seis
pareceres válidos do júri cego. A meta-revisão foi rejeitada como
`schema_invalid` após três segundos. O último estado canônico foi
`GATES_PASSED`, sem decisão aplicada nem auditoria final. As 12 chamadas
foram reconciliadas, com 28.505 tokens contabilizados, custo externo zero
e nenhuma reserva `UNCERTAIN`.

O manifesto do modelo base do júri é `65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b`.
Todas as chamadas usaram as variantes de 16.384 tokens. As de 32.768 tokens
constavam no plano. Os recibos do júri registraram de 208 a 346 tokens de
saída por parecer. A meta-revisão registrou 536 tokens de entrada e 87 de
saída. A resposta rejeitada foi identificada por hash, sem cópia de seu
texto, de modo que a regra específica que falhou segue indeterminada.

| Artefato local preservado | SHA-256 |
| --- | --- |
| PDF sintético de entrada | `4d07d27bcd2e2a85ab58dca0ad4ad60a9dd193fc90ddb4a29eaa9e3847f3bb46` |
| ZIP LaTeX de entrada | `bd7940fcadece9ca609408a4d59351a069d7093c14146359e414ea9c581589cd` |
| `run-plan.json` | `fe142b85afd6f732cffcad34dd8b339c7cf0c9400fe6eff79c96a1d611b02f5b` |
| `outcome.json` | `165990fca577f7e6078fd4a648e97f8fba04efcb7a2012ffadc92b3ae9a236bc` |
| Eventos de estado | `6ca7739e3f35d625f42495f3a31ebe03e285ba0a2600058312a0747cf0ca7aaf` |
| Eventos do orçamento | `5198f8c1def68d9679414be863d7e1c1d3c15bdfe4bcf2bb0bfc902a5fe6c79a` |
| Relatório dos gates | `896c9c55da074fe695de395110c5db4b07bdcd906afd9b47ed85351c35fc424e` |

Após essa tentativa, o adaptador ganhou um prompt próprio para a meta-revisão
e o log passou a identificar a categoria de rejeição. Os testes com dublês
chegaram a `CYCLE_COMPLETE` com disposição auditada. A validação da
meta-revisão com inferência real permanece pendente.

Veja o [plano do MVP](../PLANS.md#proposta-de-mvp-local--2026-11-17) e a
[decisão sobre o júri](decisions.md#júri-pequeno-para-o-artigo-sintético).
