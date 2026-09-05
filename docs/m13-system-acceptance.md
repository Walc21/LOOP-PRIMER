# M13 — aceitação offline e auditoria de entrega

## Comando de aceitação

```sh
python3 scripts/m13_system_check.py
```

Executa `control.test_m13_system_delivery` e emite JSON com resultado e contagens.
Qualquer falha, erro ou skip impede `status: pass` e retorna código 1. Requer
somente as dependências locais já declaradas pelo projeto (Python, PyYAML,
jsonschema, Poppler e LaTeX). Não instala pacotes nem exige Internet, Prime,
Ollama, API key, provedor ou manuscrito do usuário. A fixture PDF é gerada
diretamente com bytes fixos e texto sintético; não depende de Ghostscript.
Os outros testes legados ainda usam Ghostscript conforme `requirements`/CI.

Para conservar uma execução sintética routed após a aceitação, use um caminho
novo, fora da árvore Git:

```sh
python3 scripts/m13_system_check.py --keep-workspace /tmp/m13-evidence-new
```

O comando recusa um caminho existente. Cada teste usa diretório temporário
independente; o workspace solicitado é preservado para auditoria. Configuração
fake habilitada existe somente nessa cópia sintética. Defaults do repositório
permanecem fechados.

## Auditoria independente

```sh
python3 scripts/m13_system_check.py \
  --verify-root /tmp/m13-evidence-new \
  --run-id ingest-1a491e111064f6daae4011f46337a188de4e91337d692b3cc74b4b221d17501f
```

Essa modalidade só lê evidência existente; não invoca orquestradores,
compiladores, backends ou publicadores. A API é
`article_loop.verify_delivery(root, run_id, cycle_id=0)`. Ausência, symlink,
arquivo especial, divergência, ciclo ainda aberto ou reserva não reconciliada
falham fechados. Entradas são limitadas a 100000 itens e 1 GiB por árvore
gerenciada. O workspace deve estar quiescente durante a auditoria.

O verificador cobre entregas de ciclo `PROMOTE`, `ARCHIVE_PARETO` e `REJECT`.
Checkpoints operacionais (`PAUSE`, novo julgamento etc.) não são entregas
científicas. A publicação de um artigo terminal por `FINALIZE` continua regida
pelo pacote W22/W51/W53 de M10.1 e seus testes; M13 não fabrica esse pacote.

`reports/m13-delivery.json` é uma visão derivada conveniente da execução
conservada. A auditoria recalcula o resultado a partir da evidência e não confia
nesse resumo. O artefato entregue na promoção é o diretório `v0001`: fonte
LaTeX revisada, arquivos de evidência e manifesto. `baseline.pdf` conserva a
entrada como proveniência; ele não é apresentado como PDF recompilado da revisão.

## Composição e cadeia de evidência

```text
PDF/ZIP sintéticos -> ingest() -> v0000 / SOURCE_READY
-> prompts M4 / Blackboard / ActivationPlanner
-> Orchestrator / 15 AgentProposals / 5 DepartmentPackets
-> M7Pipeline.synthesize -> merge isolado -> challenger imutável
-> 13 gates -> BlindComparisonBundle / 6 vereditos em duas ordens
-> meta-review -> EVALUATED -> diagnose_cycle -> DIAGNOSED
-> decide -> DECIDED -> TransactionalFinalizer -> COMMITTING
-> PROMOTE / ARCHIVE_PARETO / REJECT -> CYCLE_COMPLETE
-> verify_delivery
```

O relatório deriva identidades de entrada/baseline/candidato, hashes dos cinco
pacotes, propostas aceitas, hash da síntese, GateReport, comparação, seis
vereditos, meta-veredito, avaliação, diagnóstico, Decision, receipt final,
hash do último evento e artefato/disposição. Os validadores originais M3/M7/M8/
M9/M10 são reutilizados. O auditor também compara o manifesto promovido ao
envelope exato que o finalizador pode emitir, o ponteiro champion ao receipt
e as reservas/receipts/outputs routed às propostas recebidas por M6.

O PDF sintético tem SHA-256 fixo
`1a491e111064f6daae4011f46337a188de4e91337d692b3cc74b4b221d17501f`.
O teste compara seus bytes/hash, tamanho e modo antes e depois. A melhoria
esperada explicita a substituição `x=1` na prova de `x+x=2` na fonte derivada.
A validação aritmética desta fixture não é uma prova automática de matemática
arbitrária; as avaliações excelentes são saídas determinísticas de teste.

## Critérios A–T e testes

Nomes abaixo pertencem a `control.test_m13_system_delivery`; todo critério é
exercitado offline. O estado de aceitação é produzido pelo comando, não por
esta tabela estática.

| Critério | Evidência executável |
|---|---|
| A — ciclo completo | `test_golden_ingestion_to_verified_promotion` |
| B — original imutável | `test_golden_ingestion_to_verified_promotion` |
| C — cadeia vinculada | `test_golden_ingestion_to_verified_promotion`, `test_routed_fake_payload_rejoins_complete_pipeline_and_audit` |
| D — candidato antes de gates/júri/decisão | `test_golden_ingestion_to_verified_promotion` / ordem de eventos auditada |
| E — júri cego | `test_blind_presentations_invert_without_identity_leak` |
| F — rejeição de viés posicional | `test_positional_inconsistency_cannot_promote` |
| G — veto matemático | `test_math_gate_failure_stops_before_jury_or_decision`, `test_jury_math_veto_beats_excellent_scores_and_is_rejected` |
| H — meta-review vinculado ao gate | `test_meta_cannot_substitute_gate_identity` |
| I — avaliação válida antes de diagnóstico/decisão | `test_corrupted_evaluation_blocks_diagnosis_and_decision` |
| J — finalizador preserva challenger | `test_replay_each_authoritative_stage_has_no_duplicate_effect`, `test_mutated_challenger_blocks_finalization` |
| K — replay sem duplicação | `test_replay_each_authoritative_stage_has_no_duplicate_effect` |
| L — interrupção recuperável | `test_finalizer_interruption_recovers_one_champion` |
| M — adulteração detectada | `test_tampered_durable_artifacts_fail_independent_audit`, `test_forged_final_receipt_with_new_hash_is_not_authoritative`, `test_routed_artifact_tamper_and_missing_budget_fail_closed` |
| N — concorrência sem divergência | `test_concurrent_finalization_has_one_published_truth` |
| O — defaults desabilitados | `test_versioned_defaults_disable_all_model_execution` |
| P — fronteira de dublês | `test_test_doubles_require_explicit_boolean_and_cannot_run_live` |
| Q — sem dependência de rede/modelo | bloqueio de `socket.connect` em todos os testes de ciclo; `test_routed_fake_payload_rejoins_complete_pipeline_and_audit` |
| R — verificação por comando independente | `test_delivery_cli_verifies_in_an_independent_process` |
| S — reconstrução reproduzível da disposição | `test_fresh_runs_reproduce_semantics_and_replay_exact_bytes`, `test_tradeoff_is_archived_with_verified_pareto_reference` |
| T — nenhum runtime/segredo rastreado | `test_git_tracks_no_runtime_credentials_or_test_outputs` |

Também são testados inputs inválidos sem criação de estado, preservação de
saída existente, GateReport ausente e tentativa de fuga por symlink.

## M12.5.1 e fronteira M8

S40 usa `DualExecutionController` e backend falso; os demais departamentos usam
`FakeRLMAdapter`. Registry, router, materializador, runtime, ledger, publicação
de output, envelope confiável e recepção M6 são reais. O modelo simulado emite
somente os oito campos científicos; LOOP determina os seis campos de protocolo.
Replay recupera os mesmos outputs sem reinferir.

M8 não tinha adaptadores operacionais `RoutedJurorAdapter`/
`RoutedMetaReviewerAdapter`; M13 não acrescenta esse caminho live. O júri usa
as interfaces M8 reais com saídas fictícias. Independência por modelo é testada
na política M12.5.1: o target `synthetic-judge` difere de
`synthetic-producer`; igualdade é rejeitada mesmo com grupos distintos.
Isso prova o router offline, não uma sessão de júri live roteada.

## Reprodutibilidade e limites

Os bytes da entrada sintética são fixos. Dentro de uma execução, replay preserva
IDs, conteúdo, hashes e ações. Execuções novas reproduzem a disposição,
melhoria textual, resultados dos gates e conclusões das avaliações fictícias.
Datas e metadados de ferramentas variam; não se promete igualdade de todos os
hashes entre execuções/hosts. Receipts M6 contêm locators absolutos pelo contrato
existente: conserve o workspace no caminho original. A cópia para outro caminho
não é uma migração de evidência validada.

A auditoria não autentica evidência contra quem pode reescrever conjuntamente
toda a raiz confiável e seus hashes, não certifica matemática geral, não mede
qualidade de modelos e não substitui validação separada de provedor remoto,
pagamento, credencial, serviço local ou Prime Agent. Nenhum artigo real é usado.
