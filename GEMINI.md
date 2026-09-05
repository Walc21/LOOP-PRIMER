# Protocolo para Gemini

Leia e cumpra `AGENTS.md` integralmente; ele é a política canônica deste
repositório.

Antes de analisar, planejar ou alterar arquivos, leia `AI_CONTEXT.md`
integralmente como o último checkpoint publicado. A inspeção opcional na raiz é
estritamente read-only:

```bash
python3 scripts/ai_context.py --check
```

Exit `1` significa somente checkpoint stale, não falha nem autorização para
regenerar. Nunca execute o gerador sem flags no início ou durante o trabalho.
Registre histórico, publique contexto e faça commit dos artefatos gerados
somente em checkpoint explícito após a última edição e validação, conforme
`AGENTS.md`.
