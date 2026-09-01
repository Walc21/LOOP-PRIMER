# Guia de Compatibilidade com Runtime Prime Agent

Este documento estabelece as regras de interface e isolamento necessárias para
execução no ecossistema Prime Agent.

## 1. Topologia e Isolamento de Sessões

- O `PrimeRLMAdapter` requer que a profundidade máxima seja configurada via `/rlm-max-depth 2`.
- Sessões são isoladas por workspace e comunicam-se exclusivamente através de recibos e journals estruturados.
- Em ambiente de testes, o `FakeRLMAdapter` emula perfeitamente o ciclo de vida sem executar chamadas remotas.
