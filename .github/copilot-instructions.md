# Instruções do repositório para GitHub Copilot

`AGENTS.md` é a política canônica para agentes e deve ser lido integralmente.
Antes de analisar ou alterar o projeto, leia `AI_CONTEXT.md` integralmente como
o último checkpoint publicado. A inspeção opcional na raiz é read-only:

```bash
python3 scripts/ai_context.py --check
```

Exit `1` significa apenas checkpoint stale, não falha nem autorização para
regenerar. Nunca execute o gerador sem flags no início ou durante o trabalho;
histórico, publicação de contexto e commit dos artefatos gerados pertencem a
checkpoint explícito. Não execute modelos, rede, Prime Agent ou o pipeline
científico sem a autorização específica exigida por `AGENTS.md`.
