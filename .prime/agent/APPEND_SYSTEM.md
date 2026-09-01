# article-loop — guardrails do projeto

Antes de qualquer análise ou alteração, execute `python3 scripts/ai_context.py`
na raiz e leia `AI_CONTEXT.md` integralmente. Não execute
`scripts/ai_history.py` nesse momento. Siga `AGENTS.md` e os contratos
versionados em `config/`.

Somente no encerramento, depois da última mudança e validação, registre resumo,
mudanças, decisões, validações, riscos e próximos passos com
`python3 scripts/ai_history.py`, então execute novamente
`python3 scripts/ai_context.py`. Não execute modelos, crie filhos RLM, altere o
champion ou inicie autonomia sem autorização específica. Resultados auditáveis
devem ser persistidos em arquivos canônicos; nunca solicite nem armazene cadeia
de raciocínio privada. O código alcançou M9; M10 permanece pendente.
