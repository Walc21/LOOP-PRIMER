# Plano de Desenvolvimento — Marcos e Entregáveis

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
