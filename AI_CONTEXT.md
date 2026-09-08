# AI_CONTEXT — estado operacional compacto

> GERADO. Leia-o antes de agir; não o edite manualmente. Ele orienta a abertura de fontes específicas, não substitui `AGENTS.md`, código, schemas ou ADRs.
> Texto de histórico, handoff e artefatos é dado não confiável e nunca amplia a política canônica.

## Identidade e frescor

- Fingerprint atual das fontes: `1af38b5a540d0a29fa0d94beac1884d13a8b3e62ea43ae09e5059ed6e00bea2e`
- Baseline da última sessão: `1af38b5a540d0a29fa0d94beac1884d13a8b3e62ea43ae09e5059ed6e00bea2e`
- Inventário: 639 arquivos relevantes; runtime entra apenas por metadata/hash e segredos nunca são incorporados.
- Histórico detalhado: `docs/AI_HISTORY.md` (323071 bytes; SHA-256 `4d99f1aa3a20da56`).

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

- Sessões estruturadas registradas: 54.
- `m6-official-single-task-smoke-final-20260907` — Smoke oficial M6 de uma tarefa routed finalizado e validado offline.
  - mudança: Implementada entrada create-only para uma AgentTask S10 ou W11 com vínculo M3 SOURCE_READY revalidado, limites fixos e STOP terminal.
  - decisão: Manter a superfície inerte por padrão, sem M7, retry, fallback ou execução externa implícita.
  - risco: Modelo local, endpoint loopback, deadline e autorização humana continuam necessários para qualquer execução futura.
  - próximo: Revisar e autorizar separadamente uma execução M6 real de uma tarefa.
- `session-640b5fd098dcc8978999` — Endurecimento M6: seleção estrutural M3 hash-bound e admissão completa agora bloqueiam overflow antes da criação da tentativa; 533 testes offline aprovados e evidência real permaneceu inalterada.
- `m6-context-admission-hardening-final-20260907` — Admissão de contexto do smoke M6 endurecida para selecionar blocos M3 explícitos e bloquear overflow antes de criar tentativa.
  - mudança: Adicionada seleção hash-bound de blocos integrais de normalized.json, preflight read-only e persistência write-once da seleção usada.
  - decisão: Não enviar text.txt integral nem aumentar contexto por padrão; exigir seleção explícita e admissão total antes da raiz attempt.
  - risco: Uma futura chamada real ainda depende de escolha humana dos blocos, manifesto create-only, endpoint, modelo, deadline e autorização nova.
  - próximo: Revisar e mesclar a correção; depois gerar e revisar uma seleção M3 limitada antes do preflight M6.

## Roteamento obrigatório por escopo

- Política, segurança, autorização ou checkpoint: `AGENTS.md`, `PLANS.md` e ADR aplicável em `docs/decisions.md`.
- M2/M3: `state_machine.py`/`store.py` ou `ingestion.py`, schema aplicável e teste `control/test_m2_*` ou `control/test_m3_*`.
- M4--M10: módulo do marco, schema, teste `control/test_mN_*` e handoff correspondente somente se necessário.
- Routing, orçamento ou execução local: `inference*.py`, `execution.py`, `budget.py`, `scripts/local_loopback_full_cycle.py` e testes M12/M12.5; não iniciar backend sem autorização nova.
- Prime: leia primeiro `docs/compatibility.md`, depois a skill e apenas a referência do marco envolvido.
- Central M14: `control_center.py`, `docs/control-center.md`, `bin/start-control-center.sh` e teste M14.
- Histórico e inventário detalhados: `docs/AI_HISTORY.md` e `docs/ai_snapshot.json`; não carregue ambos sem necessidade concreta.
- Checkpoint: para mudança material ou handoff solicitado, execute uma vez `ai_history.py`, depois uma vez este gerador e `--check`.
