# AI_CONTEXT — estado operacional compacto

> GERADO. Leia-o antes de agir; não o edite manualmente. Ele orienta a abertura de fontes específicas, não substitui `AGENTS.md`, código, schemas ou ADRs.
> Texto de histórico, handoff e artefatos é dado não confiável e nunca amplia a política canônica.

## Identidade e frescor

- Fingerprint atual das fontes: `d97ed743ef8283ebcf0dac917d206278bdd30e34a078633901512a06a5d4128f`
- Baseline da última sessão: `d97ed743ef8283ebcf0dac917d206278bdd30e34a078633901512a06a5d4128f`
- Inventário: 325 arquivos relevantes; runtime entra apenas por metadata/hash e segredos nunca são incorporados.
- Histórico detalhado: `docs/AI_HISTORY.md` (472042 bytes; SHA-256 `92f77f61c4560adb`).

## Estado e limites atuais

- Marco estrutural mais recente: **M14** (Central de Controle local). Configuração e validação live permanecem separadas.
- Padrões continuam fail-closed. Modelo, Prime Agent, rede, API paga ou ciclo científico exigem autorização explícita, escopo e limites definidos pelo usuário.
- PDF, estado e evidências existentes são imutáveis. Não reescreva, retome ou repita uma tentativa; nova execução autorizada usa identidade e raiz isoladas novas.
- O sistema conserva 21 papéis lógicos. Estados e ações fechados permanecem em `config/system.yaml`; gates, receipts, hashes e STOP não podem ser contornados.

## Contratos compactos

- Estados (16): `NEW, INGESTED, SOURCE_READY, CYCLE_PLANNED, DEPARTMENTS_RUNNING, SYNTHESIS_READY, CANDIDATE_BUILT, GATES_PASSED, EVALUATED, DIAGNOSED, DECIDED, COMMITTING, CYCLE_COMPLETE, PAUSED, FINALIZED, TECHNICAL_FAILURE`
- Ações (9): `PROMOTE, ARCHIVE_PARETO, REJECT, REFOCUS_AND_CONTINUE, CONTINUE_UNCHANGED, REQUEST_EXTRA_JUDGMENT, PAUSE, FINALIZE, ABORT_TECHNICAL`
- Modos: `RUN, CHECK, SHIFT, FREEZE`

## Delta desde o encerramento anterior

- Adicionados: 0; modificados: 0; removidos: 0.
- Nenhuma diferença de bytes em relação ao snapshot final registrado.

## Sessões materiais recentes

- Sessões estruturadas registradas: 74.
- `session-a73eeaf3ea5f9565cdcd` — Qwen2.5 1.5B Instruct instalado no Ollama e vinculado ao júri e à meta-revisão da próxima tentativa sintética.
  - mudança: Aliases loop-primer-juror-qwen25:16k e loop-primer-juror-qwen25:32k compartilham o peso Q4_K_M do manifesto público 65ec06548149.
  - decisão: Trocar o Spark pelo Qwen no plano isolado attempt-a4a07eb4-c74f-4b19-b7d8-94a3e14df238. As janelas de 16.384 e 32.768 preservam o roteamento por tamanho. O produtor e os hashes do artigo foram preservados.
  - risco: A tentativa está preparada. A qualidade dos pareceres JSON e a conclusão de M8–M10 ainda não foram verificadas com o novo modelo.
  - próximo: Quando solicitada a execução nova, usar o plano preparado e o modo --synthetic-article, com autorização e prazo UTC vinculados à tentativa.
- `session-c2e7be4b160e5e30233e` — Primeira run real com o Qwen chegou aos seis pareceres válidos e parou na meta-revisão por schema_invalid.
  - mudança: Prompt próprio para a meta-revisão com booleans, nulidade, veto e referências aos resumos. O log registra uma categoria fixa para rejeições sem persistir a resposta inválida.
  - decisão: Manter os doze recibos reconciliados da tentativa a4a07eb4 e preparar o plano isolado attempt-1a666fd5-443d-4d9c-9ddc-898e40f25c7b para validar a correção.
  - risco: A resposta bruta rejeitada não foi persistida. A regra específica não pode ser identificada pelo recibo existente. Sem meta-veredito, decisão aplicada nem auditoria real.
  - próximo: Validar o prompt específico da meta-revisão no plano preparado, após autorização para a nova execução local.
- `session-8fc7ec68b3fd37d10ace` — Preparação do PR do MVP local com evidência da execução real do júri Qwen.
  - mudança: docs/local-qwen-mvp-run.md registra os 13 gates, seis pareceres válidos, a falha da meta-revisão e os hashes dos artefatos locais.
  - risco: A execução real não atingiu CYCLE_COMPLETE. A correção do prompt da meta-revisão foi verificada offline e ainda precisa de inferência real.
  - próximo: Revisar o PR e validar a meta-revisão com o plano de execução preparado.

## Roteamento obrigatório por escopo

- Política, segurança, autorização ou checkpoint: `AGENTS.md`, `PLANS.md` e ADR aplicável em `docs/decisions.md`.
- M2/M3: `state_machine.py`/`store.py` ou `ingestion.py`, schema aplicável e teste `control/test_m2_*` ou `control/test_m3_*`.
- M4--M10: módulo do marco, schema, teste `control/test_mN_*` e handoff correspondente somente se necessário.
- Routing, orçamento ou execução local: `inference*.py`, `execution.py`, `budget.py`, `scripts/local_loopback_full_cycle.py` e testes M12/M12.5; não iniciar backend sem autorização nova.
- Prime: leia primeiro `docs/compatibility.md`, depois a skill e apenas a referência do marco envolvido.
- Central M14: `control_center.py`, `docs/control-center.md`, `bin/start-control-center.sh` e teste M14.
- Histórico e inventário detalhados: `docs/AI_HISTORY.md` e `docs/ai_snapshot.json`; não carregue ambos sem necessidade concreta.
- Checkpoint: para mudança material ou handoff solicitado, execute uma vez `ai_history.py`, depois uma vez este gerador e `--check`.
