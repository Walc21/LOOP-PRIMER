# Protocolo de entrada e saída para agentes

Leia e cumpra `AGENTS.md` integralmente.

Antes de analisar, planejar ou alterar o repositório, leia `AI_CONTEXT.md`
integralmente como o último checkpoint publicado. Opcionalmente, na raiz,
execute a inspeção read-only:

```bash
python3 scripts/ai_context.py --check
```

Exit `1` significa apenas checkpoint stale, não falha de execução nem
autorização para regenerar. Nunca execute o gerador sem flags no início ou
durante o trabalho; não execute `scripts/ai_history.py` no começo.

Somente em um checkpoint explícito, depois de toda edição e validação, execute
`scripts/ai_history.py` com resumo estruturado e factual da sessão, conforme o
protocolo de `AGENTS.md`, depois publique `AI_CONTEXT.md` uma vez com o comando
sem flags. O commit dos artefatos gerados também é explícito.
