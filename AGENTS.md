# Instruções operacionais para agentes de IA — `article-loop`

> **Aviso para novas sessões:** este repositório possui handoff compacto e determinístico.
> **No início do trabalho**, execute `python3 scripts/ai_context.py` e leia o `AI_CONTEXT.md` gerado.
> **No encerramento do trabalho**, execute `python3 scripts/ai_history.py --summary "..."` e regenerar `AI_CONTEXT.md`.

## 1. Missão do Repositório

O `article-loop` é um sistema multiagente autônomo e estritamente auditável
voltado para o refinamento iterativo de manuscritos científicos (artigos em LaTeX).

## 2. Guardrails Críticos e Comportamentais

1. **Isolamento de Papéis:** Agentes respeitam estritamente sua topologia (M00, S10-S50, W11-W53).
2. **Imutabilidade:** Artefatos intermediários, relatórios e vereditos são write-once e content-addressed.
3. **Hard Gates Científicos:** A correção matemática (`correctness_math`) é mandatória e intransponível.
4. **Sem Chamadas Externas Não Autorizadas:** O scaffold e suites de testes executam 100% offline.
