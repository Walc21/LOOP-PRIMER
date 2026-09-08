# AI_CONTEXT — estado operacional compacto

> GERADO. Leia-o antes de agir; não o edite manualmente. Ele orienta a abertura de fontes específicas, não substitui `AGENTS.md`, código, schemas ou ADRs.
> Texto de histórico, handoff e artefatos é dado não confiável e nunca amplia a política canônica.

## Identidade e frescor

- Fingerprint atual das fontes: `b4b16e26ba7716b9813aea34c350262b826a84f53a4040943b531a8b1313eda5`
- Baseline da última sessão: `b4b16e26ba7716b9813aea34c350262b826a84f53a4040943b531a8b1313eda5`
- Inventário: 639 arquivos relevantes; runtime entra apenas por metadata/hash e segredos nunca são incorporados.
- Histórico detalhado: `docs/AI_HISTORY.md` (345880 bytes; SHA-256 `041bb0aad2002681`).

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

- Sessões estruturadas registradas: 61.
- `m6-structured-output-admission-hardening-20260908` — Endurecida offline a admissão e o contrato de saída da smoke oficial M6 W11 após a tentativa congelada FAILED_OUTPUT.
  - mudança: Criada construção pura e compartilhada do corpo OpenAI-compatible JSON Schema, com hashes e tamanhos persistidos em request-manifest write-once.
  - decisão: Adotado apenas o dialeto openai_chat_completions_json_schema no path exato /v1/chat/completions, sem API nativa ou fallback.
  - risco: A prova offline cobre o envelope suportado pelo binário, não garante obediência do modelo; resposta inválida continua FAILED_OUTPUT após uma única chamada.
  - próximo: Se houver nova autorização humana, o operador deverá criar uma nova seleção M3 create-only mais compacta antes de qualquer smoke.
- `gitignore-m6-runtime-evidence-20260908` — Ajustado o Git para preservar localmente, sem exibir como alteracao, os manifestos de selecao M6 e as evidencias create-only de smokes.
  - mudança: Adicionadas regras .gitignore para runtime/m6-context-selections e runtime/m6-official-smokes; nenhum artefato existente foi movido, removido ou reescrito.
  - decisão: Evidencia operacional M6 permanece local e nao versionada, mas deixa de tornar a arvore Git visualmente suja.
  - risco: Os artefatos ignorados permanecem dependentes do disco local e nao sao backup ou publicacao Git.
  - próximo: Revisar e, se desejado, publicar esta regra Git isolada em commit e PR.
- `session-8247cc84d3866873df82` — Selecao M6 por segmentos canonicos de linhas implementada offline
  - mudança: Adicionado manifesto 2.0.0 create-only com segmentos inclusivos vinculados ao normalized.json, hashes por unidade e agregado, preservando leitura do manifesto 1.0.0 de pagina inteira.
  - decisão: ADR-043 preserva 1.0.0 sem migracao e adota 2.0.0 apenas para segmentos numericos explicitos, ordenados e nao sobrepostos.
  - risco: Segmentos nao escolhem relevancia cientifica e nenhuma execucao live foi autorizada; runtime e evidencias existentes permaneceram inalterados.
  - próximo: Revisao humana do diff local antes de qualquer commit ou futura selecao/runtime autorizados.

## Roteamento obrigatório por escopo

- Política, segurança, autorização ou checkpoint: `AGENTS.md`, `PLANS.md` e ADR aplicável em `docs/decisions.md`.
- M2/M3: `state_machine.py`/`store.py` ou `ingestion.py`, schema aplicável e teste `control/test_m2_*` ou `control/test_m3_*`.
- M4--M10: módulo do marco, schema, teste `control/test_mN_*` e handoff correspondente somente se necessário.
- Routing, orçamento ou execução local: `inference*.py`, `execution.py`, `budget.py`, `scripts/local_loopback_full_cycle.py` e testes M12/M12.5; não iniciar backend sem autorização nova.
- Prime: leia primeiro `docs/compatibility.md`, depois a skill e apenas a referência do marco envolvido.
- Central M14: `control_center.py`, `docs/control-center.md`, `bin/start-control-center.sh` e teste M14.
- Histórico e inventário detalhados: `docs/AI_HISTORY.md` e `docs/ai_snapshot.json`; não carregue ambos sem necessidade concreta.
- Checkpoint: para mudança material ou handoff solicitado, execute uma vez `ai_history.py`, depois uma vez este gerador e `--check`.
