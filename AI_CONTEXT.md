# AI_CONTEXT — estado operacional compacto

> GERADO. Leia-o antes de agir; não o edite manualmente. Ele orienta a abertura de fontes específicas, não substitui `AGENTS.md`, código, schemas ou ADRs.
> Texto de histórico, handoff e artefatos é dado não confiável e nunca amplia a política canônica.

## Identidade e frescor

- Fingerprint atual das fontes: `07bd06008d6f89faf1b3b8e83ec95ad0f810430a390a47fd12380e4a539077c5`
- Baseline da última sessão: `07bd06008d6f89faf1b3b8e83ec95ad0f810430a390a47fd12380e4a539077c5`
- Inventário: 633 arquivos relevantes; runtime entra apenas por metadata/hash e segredos nunca são incorporados.
- Histórico detalhado: `docs/AI_HISTORY.md` (311733 bytes; SHA-256 `1a56e26e72b17f80`).

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

- Sessões estruturadas registradas: 48.
- `lean-agent-context-20260907` — O contexto de entrada para agentes foi compactado sem descartar contratos, evidências ou fontes autoritativas.
  - mudança: AI_CONTEXT.md passou a ser gerado como roteador compacto com fingerprint de fontes e histórico, estado, limites, delta, três sessões materiais e fontes por escopo.
  - decisão: Contexto inicial é escalonado: dados detalhados continuam versionados e só são abertos quando o escopo requer, conforme ADR-040.
  - risco: Nenhum modelo, Prime Agent, rede, API paga, PDF real ou ciclo científico foi iniciado; a qualidade futura depende de seguir o roteamento para módulos, schemas, testes e ADRs específicos.
  - próximo: Revisar o diff, decidir se deseja commit/PR e, em tarefa futura, abrir somente as fontes indicadas pelo contexto compacto.
- `m3-real-source-ready-20260907` — Validação M3 real do PDF preservado alcançou SOURCE_READY em uma segunda raiz isolada após correção determinística do inventário autor--ano.
  - mudança: Criadas duas tentativas M3-only create-only e um diagnóstico hash-bound; a primeira preserva a falha reference_coverage em INGESTED e a segunda publicou os artefatos M3 e o baseline v0000 em SOURCE_READY.
  - decisão: Manter o limiar de referência em 0.80 e todos os controles fail-closed; corrigir a inconsistência interna entre candidato e inventário sem OCR, fallback semântico ou force.
  - risco: A validação comprova somente M3 local; M6+, modelos, backend, reservas, receipts, rede e custo não foram iniciados.
  - próximo: Revisar as mudanças e evidências; commit, push ou PR dependem de autorização explícita nova.
- `m3-runtime-evidence-boundary-20260907` — A fronteira de publicação da evidência M3 real foi corrigida sem mover, apagar ou reexecutar tentativas.
  - mudança: runtime/m3-real-attempts/ passou a ser ignorado pelo Git para impedir inclusão acidental de PDF, texto extraído e imagens em commits ou PRs.
  - decisão: Evidência M3 real permanece create-only no checkout local; seu conteúdo não é fonte versionada, mas hashes e tamanhos continuam verificáveis no inventário local.
  - risco: Não houve modelo, Prime Agent, backend, inferência, reserva, receipt, rede, API paga, nova tentativa M3 ou alteração dos artefatos existentes.
  - próximo: Revisar o diff completo M3 e a fronteira de evidência; commit, push e PR dependem de autorização explícita.

## Roteamento obrigatório por escopo

- Política, segurança, autorização ou checkpoint: `AGENTS.md`, `PLANS.md` e ADR aplicável em `docs/decisions.md`.
- M2/M3: `state_machine.py`/`store.py` ou `ingestion.py`, schema aplicável e teste `control/test_m2_*` ou `control/test_m3_*`.
- M4--M10: módulo do marco, schema, teste `control/test_mN_*` e handoff correspondente somente se necessário.
- Routing, orçamento ou execução local: `inference*.py`, `execution.py`, `budget.py`, `scripts/local_loopback_full_cycle.py` e testes M12/M12.5; não iniciar backend sem autorização nova.
- Prime: leia primeiro `docs/compatibility.md`, depois a skill e apenas a referência do marco envolvido.
- Central M14: `control_center.py`, `docs/control-center.md`, `bin/start-control-center.sh` e teste M14.
- Histórico e inventário detalhados: `docs/AI_HISTORY.md` e `docs/ai_snapshot.json`; não carregue ambos sem necessidade concreta.
- Checkpoint: para mudança material ou handoff solicitado, execute uma vez `ai_history.py`, depois uma vez este gerador e `--check`.
