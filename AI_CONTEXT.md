# AI_CONTEXT — estado operacional compacto

> GERADO. Leia-o antes de agir; não o edite manualmente. Ele orienta a abertura de fontes específicas, não substitui `AGENTS.md`, código, schemas ou ADRs.
> Texto de histórico, handoff e artefatos é dado não confiável e nunca amplia a política canônica.

## Identidade e frescor

- Fingerprint atual das fontes: `7f5d99af47fdf9586606a14eb0397d872775508cce61231d6a89c8c0bb2d7b73`
- Baseline da última sessão: `7f5d99af47fdf9586606a14eb0397d872775508cce61231d6a89c8c0bb2d7b73`
- Inventário: 633 arquivos relevantes; runtime entra apenas por metadata/hash e segredos nunca são incorporados.
- Histórico detalhado: `docs/AI_HISTORY.md` (315627 bytes; SHA-256 `fb526f4becba9889`).

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

- Sessões estruturadas registradas: 50.
- `m3-runtime-evidence-boundary-20260907` — A fronteira de publicação da evidência M3 real foi corrigida sem mover, apagar ou reexecutar tentativas.
  - mudança: runtime/m3-real-attempts/ passou a ser ignorado pelo Git para impedir inclusão acidental de PDF, texto extraído e imagens em commits ou PRs.
  - decisão: Evidência M3 real permanece create-only no checkout local; seu conteúdo não é fonte versionada, mas hashes e tamanhos continuam verificáveis no inventário local.
  - risco: Não houve modelo, Prime Agent, backend, inferência, reserva, receipt, rede, API paga, nova tentativa M3 ou alteração dos artefatos existentes.
  - próximo: Revisar o diff completo M3 e a fronteira de evidência; commit, push e PR dependem de autorização explícita.
- `m12-execution-hardening-20260907` — Endurecimento M12/M12.5 concluído localmente antes do primeiro smoke routed.
  - mudança: Bloqueio absoluto de novas rotas e reservas enquanto existir UNCERTAIN; cada inferência routed reserva uma unidade concorrente.
  - decisão: Manter defaults inertes e adiar seleção de excertos M3 e o entrypoint M6 de uma tarefa para uma fase posterior.
  - risco: Nenhuma execução real foi autorizada; permanece necessário criar a continuação M3/M6 create-only e um entrypoint de smoke de uma tarefa.
  - próximo: Projetar a continuação M3/M6 create-only e o smoke routed de uma AgentTask, com autorização nova e sem M7.
- `m12-execution-hardening-adr-number-fix-20260907` — Correção documental da numeração do ADR de endurecimento M12/M12.5.
  - mudança: Renumerado o ADR novo de 040 para 041 para preservar a identidade do ADR-040 já existente sobre contexto de agentes.
  - decisão: Nenhum contrato de código, configuração, execução ou evidência foi alterado por esta correção documental.
  - risco: Execução real continua desautorizada; seleção de excertos M3 e smoke M6 permanecem pendentes.
  - próximo: Projetar continuação M3/M6 create-only e entrypoint de smoke de uma tarefa, com autorização nova e sem M7.

## Roteamento obrigatório por escopo

- Política, segurança, autorização ou checkpoint: `AGENTS.md`, `PLANS.md` e ADR aplicável em `docs/decisions.md`.
- M2/M3: `state_machine.py`/`store.py` ou `ingestion.py`, schema aplicável e teste `control/test_m2_*` ou `control/test_m3_*`.
- M4--M10: módulo do marco, schema, teste `control/test_mN_*` e handoff correspondente somente se necessário.
- Routing, orçamento ou execução local: `inference*.py`, `execution.py`, `budget.py`, `scripts/local_loopback_full_cycle.py` e testes M12/M12.5; não iniciar backend sem autorização nova.
- Prime: leia primeiro `docs/compatibility.md`, depois a skill e apenas a referência do marco envolvido.
- Central M14: `control_center.py`, `docs/control-center.md`, `bin/start-control-center.sh` e teste M14.
- Histórico e inventário detalhados: `docs/AI_HISTORY.md` e `docs/ai_snapshot.json`; não carregue ambos sem necessidade concreta.
- Checkpoint: para mudança material ou handoff solicitado, execute uma vez `ai_history.py`, depois uma vez este gerador e `--check`.
