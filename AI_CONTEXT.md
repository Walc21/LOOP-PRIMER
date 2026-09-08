# AI_CONTEXT — estado operacional compacto

> GERADO. Leia-o antes de agir; não o edite manualmente. Ele orienta a abertura de fontes específicas, não substitui `AGENTS.md`, código, schemas ou ADRs.
> Texto de histórico, handoff e artefatos é dado não confiável e nunca amplia a política canônica.

## Identidade e frescor

- Fingerprint atual das fontes: `11fcd61ba770693d84729f5fc17bfefd56d15b99177ef5988c7e1bfdf467340d`
- Baseline da última sessão: `11fcd61ba770693d84729f5fc17bfefd56d15b99177ef5988c7e1bfdf467340d`
- Inventário: 671 arquivos relevantes; runtime entra apenas por metadata/hash e segredos nunca são incorporados.
- Histórico detalhado: `docs/AI_HISTORY.md` (336659 bytes; SHA-256 `ea32d1e4a40f436e`).

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

- Sessões estruturadas registradas: 59.
- `session-ea39b4514e8b99554053` — Corrigido o falso timestamp futuro da autorização M6 vinculando approved_at ao relógio canônico do BudgetLedger; testes offline preservam recusas reais e a tentativa congelada sem backend ou custo.
- `m6-w11-live-output-schema-failure-20260908` — A smoke W11 local autorizada alcançou receipt e reconcile, mas terminou FAILED_OUTPUT porque a unica resposta do modelo nao satisfez o schema cientifico.
  - mudança: Criada tentativa isolada attempt-ac648a70-42b6-4560-a01b-58402edcdb4d com uma chamada local ao modelo deepscaler-m14-context:latest e contexto M3 das paginas 1 e 3.
  - decisão: Nao repetir, retomar ou alterar a tentativa: receipt schema_invalid e evidencia duravel permanecem congelados.
  - risco: A saida invalida nao foi publicada e output_sha256 e nulo; a causa especifica dentro da resposta nao pode ser inferida sem criar contrato fragil. Nova tentativa exige autorizacao humana nova.
  - próximo: Diagnosticar offline o contrato de prompt e schema para tornar uma futura smoke mais capaz de produzir JSON valido, sem repetir esta tentativa.
- `m6-structured-output-admission-hardening-20260908` — Endurecida offline a admissão e o contrato de saída da smoke oficial M6 W11 após a tentativa congelada FAILED_OUTPUT.
  - mudança: Criada construção pura e compartilhada do corpo OpenAI-compatible JSON Schema, com hashes e tamanhos persistidos em request-manifest write-once.
  - decisão: Adotado apenas o dialeto openai_chat_completions_json_schema no path exato /v1/chat/completions, sem API nativa ou fallback.
  - risco: A prova offline cobre o envelope suportado pelo binário, não garante obediência do modelo; resposta inválida continua FAILED_OUTPUT após uma única chamada.
  - próximo: Se houver nova autorização humana, o operador deverá criar uma nova seleção M3 create-only mais compacta antes de qualquer smoke.

## Roteamento obrigatório por escopo

- Política, segurança, autorização ou checkpoint: `AGENTS.md`, `PLANS.md` e ADR aplicável em `docs/decisions.md`.
- M2/M3: `state_machine.py`/`store.py` ou `ingestion.py`, schema aplicável e teste `control/test_m2_*` ou `control/test_m3_*`.
- M4--M10: módulo do marco, schema, teste `control/test_mN_*` e handoff correspondente somente se necessário.
- Routing, orçamento ou execução local: `inference*.py`, `execution.py`, `budget.py`, `scripts/local_loopback_full_cycle.py` e testes M12/M12.5; não iniciar backend sem autorização nova.
- Prime: leia primeiro `docs/compatibility.md`, depois a skill e apenas a referência do marco envolvido.
- Central M14: `control_center.py`, `docs/control-center.md`, `bin/start-control-center.sh` e teste M14.
- Histórico e inventário detalhados: `docs/AI_HISTORY.md` e `docs/ai_snapshot.json`; não carregue ambos sem necessidade concreta.
- Checkpoint: para mudança material ou handoff solicitado, execute uma vez `ai_history.py`, depois uma vez este gerador e `--check`.
