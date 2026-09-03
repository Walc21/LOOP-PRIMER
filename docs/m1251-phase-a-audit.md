# M12.5.1 Phase A — auditoria de ligação

Baseline auditado: `ba316b50a707d490348192d528046b6eec567250`, árvore limpa
no início. Prompt externo preservado em
`/home/victor/Downloads/LOOP_PRIMER_M12_5_1_PHASE_A_PROMPT.md`, SHA-256
`01c9de81d08deb436446c913a7410e457c54efaba0342a8db953c52dc28eb41b`.

## Mapa end-to-end

| Etapa | Autoridade existente | Ligação Phase A |
|---|---|---|
| `AgentTask` e locators | `orchestrator.py::_task`, schema `agent-task` | preservada; entrada única do materializer |
| Prompt e workspace | `compile_prompt`, `_admit`, `workspaces/<run>/cycle-*/<role>` | preservados; prompt recebe somente fragmento autorizado |
| Spawn/handle | `PrimeRLMAdapter.spawn(prompt, name)`, journal M6 | Prime inalterado; routed usa handle local persistente |
| Inferência Wxx | M12.5 `InferenceRuntime` | selecionada apenas para departamentos routed |
| Output científico | schema pedido pela `AgentTask` | validado e publicado antes do receipt operacional |
| Receipt do backend | `InferenceReceipt` | ganhou output/context/privacy hashes e locator |
| Receipt científico | `Orchestrator.receipt()` | recebe bytes exatos do output durável |
| Packet Sxx | `consolidate_department()` | reutilizado sem bifurcação |
| Síntese/gates/júri | M7/M8 | inalterados; M8 mantém sua interface de adapter |
| Diagnóstico/decisão/finalização | M9/M10/M10.1 | inalterados |

## Lacunas encontradas e fechamento

- M12.5 terminava no receipt operacional e descartava os bytes da resposta:
  agora há output store write-once e rematerialização M6.
- O ledger registrava custo, mas não reservava um teto pré-chamada: agora
  reserva, saldo, autorização, reconciliação e overrun usam microunits inteiros.
- Não havia privacidade por run nem contexto mínimo: agora modo, provenance,
  hash, contenção e limite são verificáveis.
- Não havia seleção Prime/Routed por departamento: agora o adapter dual escolhe
  Sxx, sem mistura interna do caminho Prime.
- A independência de júri era somente por grupo: o modo legacy permanece e o
  modo recomendado compara `model` exato.
- Só a versão Prime 0.9.1 foi observada nesta fase; por isso model routing por
  filho é `unknown_on_current_version`, não “suportado” nem “incompatível”.

## Invariantes preservados

Permanecem exatamente 21 papéis, 16 estados e 9 ações. Não houve mudança no
catálogo, máquina de estados, critérios científicos, gates, síntese, blindagem,
Decision, finalizador ou `PrimeRLMAdapter.spawn()`. A Phase A não iniciou Prime,
modelo, rede, API paga, artigo real ou M13.
