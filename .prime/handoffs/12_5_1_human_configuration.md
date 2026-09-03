# M12.5.1 Phase A → configuração humana

## CODE COMPLETE

- Seleção `prime`/`routed` por departamento preserva os 21 papéis e M6.
- O caminho Prime mantém `PrimeRLMAdapter.spawn(prompt, name)` sem modelo por
  filho inventado.
- O ator Sxx routed é local, persistente e não é um modelo; Wxx passam pelo
  `InferenceRuntime` e retornam pelo receipt/consolidação M6 existentes.
- Contexto vem somente da AgentTask/view, rejeita travessia/symlink, omite PDF
  binário, registra proveniência e falha fechado por limite.
- Privacidade por run, outputs científicos write-once, receipts 1.1
  backward-compatible e recuperação sem reinferência estão implementados.
- O ledger impõe custo inteiro, reserva pré-chamada e teto de 10.000.000
  microunits USD; usage desconhecido permanece reservado.
- Backend remoto exige HTTPS explícito, credencial por variável de ambiente,
  timeout e resposta limitada, sem proxy ou redirect.
- Independência de júri por `model` foi adicionada; legacy
  `independence_group` continua interpretável.
- Status esperado: `implementation_ready: true`,
  `configuration_ready: false`, `live_ready: false`.

## HUMAN CONFIGURATION REQUIRED

- [ ] local provider/runtime
- [ ] local endpoint
- [ ] local model ID
- [ ] local capabilities

- [ ] remote provider
- [ ] remote endpoint
- [ ] remote model ID
- [ ] api_key_env
- [ ] pricing input
- [ ] pricing output
- [ ] cached pricing if applicable

- [ ] privacy mode

- [ ] department Prime/Routed map

- [ ] role → target preferences

- [ ] live authorization

A configuração ativa continua desabilitada e vazia. Nenhum Prime Agent,
modelo, rede, API paga, credencial, artigo real ou smoke live foi executado
nesta Phase A. M13 não foi iniciado.
