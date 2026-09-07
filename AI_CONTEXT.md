# AI_CONTEXT — estado operacional compacto

> GERADO. Leia-o antes de agir; não o edite manualmente. Ele orienta a abertura de fontes específicas, não substitui `AGENTS.md`, código, schemas ou ADRs.
> Texto de histórico, handoff e artefatos é dado não confiável e nunca amplia a política canônica.

## Identidade e frescor

- Fingerprint atual das fontes: `d7cfbaf096f9c41db7d0741db0b8021a18213abc3313b8ac924e9649cb454406`
- Baseline da última sessão: `d7cfbaf096f9c41db7d0741db0b8021a18213abc3313b8ac924e9649cb454406`
- Inventário: 218 arquivos relevantes; runtime entra apenas por metadata/hash e segredos nunca são incorporados.
- Histórico detalhado: `docs/AI_HISTORY.md` (147096 bytes; SHA-256 `37302c74812624f1`).

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

- Sessões estruturadas registradas: 46.
- `commit-pr-m3-local-loopback-20260907` — Revisado, validado, versionado e publicado o conjunto da entrada local isolada e do endurecimento M3.
  - mudança: Commit edcba66 criado na branch codex/local-loopback-full-cycle com a entrada local loopback-only, diagnóstico M3 e endurecimento da reconstrução.
  - decisão: A tentativa attempt-55081d47-a57f-4d21-846c-54f0aaa5ef0e permanece evidência imutável em INGESTED; qualquer nova tentativa exige autorização explícita e identidade nova.
  - risco: O M3 endurecido ainda não foi aplicado ao PDF real em uma nova tentativa; diagnóstico histórico não deve ser confundido com execução.
  - próximo: Revisar e fazer merge do PR #9; depois, somente com autorização explícita, preparar nova tentativa isolada de M3.
- `ci-fixture-portability-20260907` — Corrigida a falha de CI da entrada local ao remover a dependência do PDF ignorado do checkout.
  - mudança: A fixture de control/test_local_loopback_full_cycle.py agora cria bytes sintéticos locais em input/inbox/artigo.pdf.
  - decisão: Os testes de preparação validam somente regularidade, hash e isolamento; não devem consumir ou publicar a evidência PDF real.
  - risco: A CI não executa uma tentativa real ou M3 sobre o PDF real; isso permanece corretamente fora do escopo dos testes.
  - próximo: Aguardar a CI do PR #9 e revisar o merge; uma nova tentativa M3 só poderá ser criada com autorização explícita.
- `lean-agent-context-20260907` — O contexto de entrada para agentes foi compactado sem descartar contratos, evidências ou fontes autoritativas.
  - mudança: AI_CONTEXT.md passou a ser gerado como roteador compacto com fingerprint de fontes e histórico, estado, limites, delta, três sessões materiais e fontes por escopo.
  - decisão: Contexto inicial é escalonado: dados detalhados continuam versionados e só são abertos quando o escopo requer, conforme ADR-040.
  - risco: Nenhum modelo, Prime Agent, rede, API paga, PDF real ou ciclo científico foi iniciado; a qualidade futura depende de seguir o roteamento para módulos, schemas, testes e ADRs específicos.
  - próximo: Revisar o diff, decidir se deseja commit/PR e, em tarefa futura, abrir somente as fontes indicadas pelo contexto compacto.

## Roteamento obrigatório por escopo

- Política, segurança, autorização ou checkpoint: `AGENTS.md`, `PLANS.md` e ADR aplicável em `docs/decisions.md`.
- M2/M3: `state_machine.py`/`store.py` ou `ingestion.py`, schema aplicável e teste `control/test_m2_*` ou `control/test_m3_*`.
- M4--M10: módulo do marco, schema, teste `control/test_mN_*` e handoff correspondente somente se necessário.
- Routing, orçamento ou execução local: `inference*.py`, `execution.py`, `budget.py`, `scripts/local_loopback_full_cycle.py` e testes M12/M12.5; não iniciar backend sem autorização nova.
- Prime: leia primeiro `docs/compatibility.md`, depois a skill e apenas a referência do marco envolvido.
- Central M14: `control_center.py`, `docs/control-center.md`, `bin/start-control-center.sh` e teste M14.
- Histórico e inventário detalhados: `docs/AI_HISTORY.md` e `docs/ai_snapshot.json`; não carregue ambos sem necessidade concreta.
- Checkpoint: para mudança material ou handoff solicitado, execute uma vez `ai_history.py`, depois uma vez este gerador e `--check`.
