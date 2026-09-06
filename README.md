# LOOP-PRIMER

LOOP-PRIMER é um sistema local, auditável e *fail-closed* para a revisão iterativa de artigos matemáticos. Ele organiza propostas de revisão, evidências e decisões em contratos duráveis: os agentes propõem; o LOOP preserva o estado, aplica gates, conduz o júri cego, registra a decisão e finaliza somente o que foi validado.

Não é um chatbot que edita PDFs diretamente. O PDF de entrada é preservado, e qualquer futura alteração percorre uma cadeia verificável de candidatos, evidências e decisões antes de poder ser promovida.

## Estado atual

Os marcos M0 a M14 estão implementados estruturalmente e validados localmente. Isso significa que os contratos, a persistência, os controles e as validações offline existem no repositório. Não significa que uma revisão científica real esteja autorizada, configurada ou tenha sido executada.

| Marcos | Entrega estrutural |
|---|---|
| M0–M1 | Compatibilidade, arquitetura, catálogo de papéis e contratos versionados. |
| M2–M3 | Máquina de estados, log encadeado, recuperação e ingestão que preserva o original. |
| M4–M5 | Prompts imutáveis, contexto fechado, blackboard, grafo de impacto e ativação esparsa. |
| M6–M7 | Orquestração por receipts, síntese isolada, challenger imutável e gates locais. |
| M8–M10.1 | Júri cego, diagnóstico, refoco, decisão canônica e finalização transacional. |
| M11–M12.5.1 | Comandos locais fail-closed, orçamento, observabilidade, routing e ligação estrutural de execução. |
| M13–M13.2 | Aceitação de sistema offline, auditoria de entrega e endurecimento das fronteiras de execução e anonimização. |
| M14 | Central de Controle local para observação, timeline, topologia, evidências, orçamento, configuração tipada e auditoria. |

A Central de Controle é uma camada local sobre as fontes de verdade existentes; ela não cria um segundo estado científico. Ela projeta status, execuções, evidências, orçamento e auditoria, e encaminha somente controles canônicos com confirmação, hash esperado e idempotência.

Execução científica real continua fora do escopo padrão: requer autorização humana explícita e as pré-condições contratuais aplicáveis, inclusive configuração, orçamento, política de conteúdo e preflight. A presença do código ou da interface não concede essa autorização.

## Arquitetura

O fluxo canônico é deliberadamente simples de inspecionar:

```text
configuração → estado durável → ingestão → papéis → síntese → gates
→ júri cego → diagnóstico → decisão → finalização
```

Há 21 papéis lógicos: um gerente geral, cinco subgerentes e até três especialistas por subgerente. A topologia tem profundidade máxima de dois e a ativação é esparsa: um papel só participa quando o estado, o impacto e o gate do ciclo exigem trabalho. Isso evita tratar a hierarquia como uma autorização para iniciar todos os papéis.

- **Champion e challenger:** o champion é a versão de referência; o challenger é um candidato novo, isolado e imutável. Agentes não escrevem diretamente no champion.
- **Gates determinísticos:** verificações locais e reproduzíveis que aceitam ou rejeitam uma etapa segundo contratos definidos. Um gate aprovado só atesta o que ele efetivamente verifica.
- **Receipts:** registros duráveis, vinculados por hashes, que conectam uma operação à sua evidência e permitem auditoria e retomada sem assumir que uma sessão externa terminou.
- **Orçamento:** um ledger hash-bound controla admissão, reserva e reconciliação de recursos; ausência de informação suficiente conserva a incerteza em vez de liberar gasto automaticamente.
- **Fail-closed:** dados, autorização, configuração ou evidência ausentes não são preenchidos por suposição; a operação é bloqueada com um diagnóstico.

## Segurança e limites

- Não há execução automática de modelo, Prime Agent, provedor remoto, API paga ou pipeline científico. Cada execução real exige autorização humana explícita e condições verificáveis no momento da operação.
- PDFs de entrada são imutáveis: não são sobrescritos, anotados, recomprimidos ou substituídos. Antes de derivações futuras, o sistema registra a identidade do original no estado durável.
- Estado científico, eventos e artefatos permanecem nos contratos canônicos do projeto. A Central de Controle possui projeções e um ledger de auditoria separado; ela não é um editor arbitrário de arquivos, terminal ou executor de inferência.
- Configuração tipada não substitui autorização: mesmo habilitar um valor não autoriza modelo, provedor, orçamento ou execução científica.

## Uso local seguro

Use os comandos abaixo a partir da raiz do repositório e somente em um ambiente local que já possua as dependências declaradas pelo projeto.

### Verificação padrão

```sh
bash bin/check.sh
```

Esse check local verifica a superfície de comandos e a prontidão fail-closed. No checkout atual, ele reporta que a execução live, a execução de modelos e as APIs pagas estão desabilitadas. Ele não inicia Prime Agent nem modelo.

Para a regressão estrutural offline completa, o comando aceito pelo projeto é:

```sh
python3 -m unittest discover -s control -q
```

Para a aceitação de sistema sintética e a auditoria independente de entrega, consulte a documentação M13 antes de usar:

```sh
python3 scripts/m13_system_check.py
```

Essas verificações exercitam contratos e fixtures locais; não equivalem a uma execução científica real nem a uma validação matemática de um artigo concreto.

### Central de Controle local

Inicie-a exclusivamente pelo launcher oficial:

```sh
bash bin/start-control-center.sh
```

Com a porta padrão, abra `http://127.0.0.1:8765` no mesmo computador. Para usar outra porta local entre 1024 e 65535, por exemplo:

```sh
bash bin/start-control-center.sh --port 8766
```

Nesse caso, abra `http://127.0.0.1:8766`. A Central deve ser acessada pelo endereço `http://127.0.0.1:...` do servidor local, nunca abrindo `index.html` por `file://`: esse modo não fornece os assets nem a API `/api/v1` da Central. O launcher fixa o bind em loopback; para encerrar o servidor, mantenha o terminal em primeiro plano e use `Ctrl-C`.

## Qualidade e testes

A estratégia de qualidade é offline e orientada a contratos. As suítes em `control/` verificam schemas, transições, persistência e recuperação, imutabilidade de entrada, gates, cegueira do júri, decisões, receipts, orçamento, fronteiras de test doubles e a Central de Controle em loopback. A Central também é exercitada com servidor local em porta efêmera, inclusive para assets, API, cursor de eventos, idempotência e rejeição de bind não-loopback.

O CI e as suítes estruturais fornecem evidência sobre esses contratos. Não substituem uma autorização humana, não chamam um provedor por si só e não provam correção científica de um manuscrito.

## Onde começar

- [Arquitetura canônica](docs/architecture.md)
- [Decisões arquiteturais](docs/decisions.md)
- [Central de Controle local](docs/control-center.md)
- [Plano e marcos](PLANS.md)
- [Política operacional para agentes](AGENTS.md)
- [Aceitação de sistema M13](docs/m13-system-acceptance.md)
- [Compatibilidade com o Prime Agent](docs/compatibility.md)

## Contribuição e licença

Consulte [CONTRIBUTING.md](CONTRIBUTING.md) e [SECURITY.md](SECURITY.md) antes de contribuir. O projeto é distribuído sob a [licença MIT](LICENSE).

Autor: Victor Gabriel de Oliveira ([@Walc21](https://github.com/Walc21)).
