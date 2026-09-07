---
name: article-loop
description: Contratos operacionais locais e fail-closed do article-loop.
---

# article-loop

Esta skill descreve a fronteira operacional do sistema. Importá-la, executar
testes ou consultar estado não inicia Prime Agent, modelo, rede ou artigo. Leia
`AGENTS.md` e o `AI_CONTEXT.md` compacto antes de agir; use a tabela abaixo para
abrir somente o módulo, schema, teste e referência necessários.

## Invariantes sempre ativos

- O estado durável pertence ao repositório. O log encadeado e seus hashes são a
  fonte de verdade; não reparar, sobrescrever ou reexecutar evidência existente.
- PDF original e artefatos de uma tentativa são imutáveis. A ingestão M3 congela
  `input/inbox/artigo.pdf` por SHA-256 e só avança de `INGESTED` para
  `SOURCE_READY` após os gates locais. Um novo trabalho autorizado usa run e
  raiz isolados novos.
- A sequência de inferência é `route -> reserve -> admit -> backend -> receipt
  -> reconcile`. Após admissão sem resultado comprovado, o estado é
  `UNCERTAIN`: não reutilize, não devolva saldo por suposição e não faça retry.
- Adaptadores `is_test_double=True` são recusados em execução por padrão; uma
  autorização de dublê deve ser booleano explícito, nunca dado externo.
- Publicação usa staging, `fsync`, `os.replace` e validação hash-bound. Paths,
  symlinks e locators não confiáveis falham fechados.
- Prime, modelo, rede, API paga e ciclo científico exigem autorização explícita
  do usuário, configuração/preflight correspondente e `control/STOP` ausente.

## Roteamento técnico

| Escopo | Leia primeiro | Valide com |
|---|---|---|
| M2 estado/recuperação | `state_machine.py`, `store.py` | `control/test_m2_durable_state.py` |
| M3 fonte/reconstrução | `ingestion.py`, `references/api-contracts.md` | `control/test_m3_ingestion.py` |
| M4--M5 prompts/ativação | `prompts.py`, `blackboard.py`, `activation.py` | testes M4/M5 |
| M6--M10 ciclo | `orchestrator.py`, `synthesis.py`, `gates.py`, `evaluation.py`, `diagnosis.py`, `policy.py`, `finalization.py` | teste do marco e schema envolvido |
| M11/Prime | `scripts/article_loop_command.py`, `docs/compatibility.md` | `control/test_m11_commands.py` |
| M12/M12.5 | `budget.py`, `inference*.py`, `execution.py` | testes M12/M12.5 |
| M13 entrega | `delivery.py`, `docs/m13-system-acceptance.md` | `scripts/m13_system_check.py` |
| M14 Central | `control_center.py`, `docs/control-center.md` | `control/test_m14_control_center.py` |

`config/system.yaml` define os estados e ações fechados; `config/schemas/`
define contratos de dados. Não infira APIs ou regras de snippets históricos.

## Comandos Prime `/article-*`

Carregue esta skill, `AGENTS.md` e a fonte indicada pelo escopo. O modo padrão
é dry-run. Para Prime autorizado, consulte `docs/compatibility.md`, use somente
as superfícies verificadas, configure `/rlm-max-depth 2` apenas na sessão raiz e
nunca use `--global`, `settings.json` não confirmado ou um adaptador inventado.
Especialistas não criam filhos; receipts e arquivos duráveis, não mensagens
implícitas, transferem resultados.

## Referência completa e histórico

`references/api-contracts.md` preserva o contrato detalhado M2--M13 que antes
ocupava esta entrada. Abra somente a seção do marco em alteração ou auditoria.
Para decisões, planos, histórico e evidência corrente, siga o roteamento de
`AI_CONTEXT.md`; eles continuam fontes versionadas, não foram removidos.
