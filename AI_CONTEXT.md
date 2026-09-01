# AI_CONTEXT — Contexto Consolidado para Sessões de IA

> Documento gerado deterministicamente por `scripts/ai_context.py`.
> Fonte única de verdade consolidada para evitar leitura fragmentada no início da sessão.

## 1. Missão e Arquitetura Executiva

O `article-loop` é um sistema multiagente projetado para o refinamento iterativo,
rigoroso e auditável de manuscritos científicos em formato LaTeX.

## 2. Guardrails Críticos e Comportamentais (AGENTS.md)

1. **Isolamento de Papéis:** Agentes respeitam estritamente sua topologia (M00, S10-S50, W11-W53).
2. **Imutabilidade:** Artefatos intermediários, relatórios e vereditos são write-once e content-addressed.
3. **Hard Gates Científicos:** A correção matemática (`correctness_math`) é mandatória e intransponível.
4. **Sem Chamadas Externas Não Autorizadas:** O scaffold e suites de testes executam 100% offline.

## 3. Estado Atual dos Marcos (PLANS.md)

| Marco | Entrega | Estado | Critério de Aceitação |
|---|---|---|---|
| M0/M0.5 | Scaffold e Auditoria de Compatibilidade | Concluído | Verificação estática local sem dependências externas |
| M0.6 | Completude de Paths e Ordem Transacional | Concluído | Invariantes de caminho e transação validados |
| M1/M1.1 | Catálogo de Papéis e Schemas JSON | Concluído | 20 JSON schemas e 21 papéis validados |
| M2 | Estado Durável e Event Store | Concluído | Event log JSONL encadeado com integridade SHA-256 |
| M3 | Ingestão PDF/ZIP e Baseline v0000 | Concluído | Ingestão determinística e gates de extração |
| M4 | Compilação Content-Addressed de Prompts | Concluído | Prompts imutáveis com overlays CAS |
| M5 | Blackboard e Planejador de Ativação | Concluído | Ledgers append-only e planejamento RUN/CHECK/SHIFT/FREEZE |
| M6 | Orquestração RLM Reentrante | Concluído | Receipts duráveis e árvore de subagentes isolados |
| M7 | Síntese, Merge e 13 Gates Determinísticos | Concluído | Challenger write-once e GateReport canônico |
| M8 | Júri Externo Cego e Meta-Revisão | Concluído | Comparação A/B com inversão consistente |
| M9 | Diagnóstico de Estagnação e Refoco | Concluído | Classificação em 7 estados e planos de refoco |
| M10 | Decisão Canônica e Finalizador Transacional | Pendente | Execução transacional de PROMOTE/ARCHIVE/REJECT |

## 4. Contratos do Sistema (config/system.yaml, gates, budgets)

- **Estados canônicos (16):** NEW, INGESTED, SOURCE_READY, PLAN_READY, DEPARTMENTS_RUNNING, SYNTHESIS_READY, CANDIDATE_BUILT, GATES_PASSED, EVALUATED, DIAGNOSED, DECIDED, COMMITTING, CYCLE_COMPLETE, FINALIZED, PAUSED, TECHNICAL_FAILURE
- **Ações canônicas (9):** PROMOTE, ARCHIVE_PARETO, REJECT, RUN, CHECK, SHIFT, FREEZE, ROLLBACK, FINALIZE
- **Gates (13):** configurados em `config/gates.yaml`.
- **Orçamentos:** configurados em `config/budgets.yaml`.
