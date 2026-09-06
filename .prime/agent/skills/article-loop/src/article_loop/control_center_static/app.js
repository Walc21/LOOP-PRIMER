(() => {
  "use strict";
  const api = "/api/v1";
  const view = document.querySelector("#view");
  const notice = document.querySelector("#notice");
  const connection = document.querySelector("#connection-state");
  let currentView = "overview";
  let eventCursor = null;
  let activeRun = null;
  let pollTimer = null;

  const esc = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[char]));
  const pretty = (value) => esc(JSON.stringify(value, null, 2));
  const hash = (value) => value ? `<code class="hash">${esc(value)}</code>` : "—";
  const state = (value) => `<span class="status" data-state="${esc(String(value).toLowerCase())}">${esc(value ?? "unknown")}</span>`;
  const key = () => crypto.randomUUID();
  const showNotice = (text, bad = false) => { notice.hidden = false; notice.className = `notice${bad ? " danger-text" : ""}`; notice.textContent = text; };
  const clearNotice = () => { notice.hidden = true; notice.textContent = ""; };

  async function request(path, options = {}) {
    const response = await fetch(api + path, {cache: "no-store", ...options});
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload?.error?.message || `Erro HTTP ${response.status}`);
    return payload;
  }

  async function post(path, body) {
    return request(path, {method: "POST", headers: {"Content-Type": "application/json", "Idempotency-Key": key()}, body: JSON.stringify(body)});
  }

  function setConnection(text) { connection.textContent = text; }

  function cards(items) {
    return `<div class="grid">${items.map(([label, value, detail]) => `<article class="card"><p class="muted">${esc(label)}</p><p class="metric">${value}</p>${detail ? `<p class="small muted">${detail}</p>` : ""}</article>`).join("")}</div>`;
  }

  async function overview() {
    const data = await request("/system/status");
    const run = data.runs.runs.find((item) => item.active) || data.runs.runs[0];
    activeRun = run?.run_id || null;
    view.innerHTML = `<h2>Visão geral</h2>
      <p class="muted">A Central mostra apenas snapshots e eventos duráveis já confirmados. Nenhum controle desta tela inicia uma inferência.</p>
      ${cards([
        ["Execuções", esc(data.runs.total), data.active_runs.length ? `${data.active_runs.length} ativa(s)` : "sem execução ativa"],
        ["Execução / inferência", state(data.execution.live_ready ? "enabled" : "disabled"), data.execution.live_ready ? "ainda requer autorização de run" : "HUMAN CONFIGURATION REQUIRED"],
        ["Preflight", state(data.preflight.configured === true), esc(data.preflight.reason || "verificado localmente")],
        ["Configuração ativa", hash(data.configuration_hash), "hash das superfícies versionadas"]
      ])}
      <section class="panel"><h3>Saúde de armazenamento</h3><ul>${data.health.storage.map((item) => `<li>${esc(item.path)}: ${item.safe ? "presente e seguro" : "ausente ou requer atenção"}</li>`).join("")}</ul></section>
      <section class="panel"><h3>Controle permitido</h3><p>Preflight é uma consulta canônica auditada. Pausar, retomar, checkpoint, stop e finalize só aparecem para uma execução existente e sempre exigem confirmação, hash atual e chave de idempotência.</p>
      <button class="button secondary" id="preflight" data-hash="${esc(data.configuration_hash)}">Executar preflight local auditado</button></section>`;
    document.querySelector("#preflight")?.addEventListener("click", async (event) => {
      if (!confirm("Executar o preflight local? Isto não inicia Prime Agent nem inferência.")) return;
      try { const result = await post("/preflight", {confirmed: true, expected_hash: event.currentTarget.dataset.hash}); showNotice(`Preflight concluído: ${JSON.stringify(result.result)}`); }
      catch (error) { showNotice(error.message, true); }
    });
  }

  function runControls(run) {
    if (!run) return "<p class=\"empty\">Não há execução selecionada.</p>";
    const names = run.orchestration ? [["checkpoint", "Checkpoint", "secondary"], ["pause", "Pausar", "secondary"], ["resume", "Retomar", "secondary"], ["stop", "Stop", "danger"], ["finalize", "Finalizar", "danger"]] : [["finalize", "Finalizar", "danger"]];
    return `<div class="toolbar">${names.map(([action, label, klass]) => `<button class="button ${klass}" data-run-action="${action}" data-run="${esc(run.run_id)}" data-hash="${esc(run.version_hash)}">${label}</button>`).join("")}</div>`;
  }

  async function runs() {
    const data = await request("/runs?limit=100");
    if (!data.runs.length) { view.innerHTML = "<h2>Execuções</h2><p class=\"empty\">Sem execução durável. A Central não oferece ação para criar ou iniciar uma execução.</p>"; return; }
    activeRun = activeRun || data.runs[0].run_id;
    view.innerHTML = `<h2>Execuções</h2><div class="table-wrap"><table><thead><tr><th>Run</th><th>Estado</th><th>Ciclo</th><th>Snapshot</th><th>Ativa</th></tr></thead><tbody>${data.runs.map((run) => `<tr><td><button class="button secondary small" data-select-run="${esc(run.run_id)}">${esc(run.run_id)}</button></td><td>${state(run.state)}</td><td>${esc(run.cycle_id)}</td><td>${hash(run.version_hash)}</td><td>${run.active ? "sim" : "não"}</td></tr>`).join("")}</tbody></table></div><div id="run-detail" class="panel"></div>`;
    document.querySelectorAll("[data-select-run]").forEach((button) => button.addEventListener("click", () => { activeRun = button.dataset.selectRun; renderRunDetail(); }));
    document.querySelectorAll("[data-run-action]").forEach((button) => button.addEventListener("click", controlRun));
    await renderRunDetail();
  }

  async function renderRunDetail() {
    if (!activeRun || !document.querySelector("#run-detail")) return;
    const run = await request(`/runs/${encodeURIComponent(activeRun)}`);
    const detail = document.querySelector("#run-detail");
    const artifacts = await request(`/runs/${encodeURIComponent(activeRun)}/artifacts`);
    detail.innerHTML = `<h3>${esc(run.run_id)}</h3><p>Estado ${state(run.state)} · ciclo ${esc(run.cycle_id)} · versão ${hash(run.version_hash)}</p>${runControls(run)}<details><summary>Snapshot confirmado</summary><pre>${pretty(run.snapshot)}</pre></details><details><summary>Orquestração e activity</summary><pre>${pretty(run.orchestration)}</pre></details><details><summary>Artefatos aprovados</summary>${artifacts.artifacts.length ? `<ul>${artifacts.artifacts.map((artifact) => `<li><a href="${esc(artifact.href)}">${hash(artifact.sha256)}</a> <span class="small muted">metadados allowlisted</span></li>`).join("")}</ul>` : "<p class=\"small muted\">Nenhum artefato aprovado no journal.</p>"}</details><p class="small muted">Os links exibem somente metadados de um hash já comprometido no journal; não existe download de caminhos arbitrários. Stop preserva reservas, receipts e evidência. Finalize mantém todas as pré-condições M10; a UI não pode ignorar gates.</p>`;
    detail.querySelectorAll("[data-run-action]").forEach((button) => button.addEventListener("click", controlRun));
  }

  async function controlRun(event) {
    const button = event.currentTarget;
    const action = button.dataset.runAction;
    const labels = {checkpoint: "criar um checkpoint", pause: "pausar", resume: "retomar", stop: "parar preservando evidências", finalize: "finalizar somente se as pré-condições canônicas passarem"};
    if (!confirm(`Confirma ${labels[action]} a execução ${button.dataset.run}?`)) return;
    try { const result = await post(`/runs/${encodeURIComponent(button.dataset.run)}/${action}`, {confirmed: true, expected_hash: button.dataset.hash}); showNotice(`Ação ${action} registrada: ${JSON.stringify(result.result)}`); await runs(); }
    catch (error) { showNotice(error.message, true); }
  }

  async function topology() {
    const query = activeRun ? `?run_id=${encodeURIComponent(activeRun)}` : "";
    const data = await request(`/runs${query}`).catch(() => null);
    let topology;
    if (activeRun) topology = await request(`/runs/${encodeURIComponent(activeRun)}/topology`);
    else {
      const system = await request("/system/status");
      if (system.runs.runs[0]) { activeRun = system.runs.runs[0].run_id; topology = await request(`/runs/${encodeURIComponent(activeRun)}/topology`); }
      else { view.innerHTML = "<h2>Topologia e atividade</h2><p class=\"empty\">A árvore lógica existe, mas não há execução para exibir atividade.</p>"; return; }
    }
    view.innerHTML = `<h2>Topologia e atividade dos 21 papéis</h2><p class="muted">A topologia exibe atividade operacional. Ela nunca liga um candidato da avaliação cega à autoria de um papel.</p><div class="role-tree">${topology.roles.map((role) => `<article class="role" data-kind="${esc(role.kind)}"><strong>${esc(role.role_id)}</strong><span>${esc(role.department)}</span><span>${state(role.state)}</span><span>${esc(role.activation_mode || "sem ativação")}<br><small class="muted">Receipt: ${hash(role.receipt)}</small></span></article>`).join("")}</div>`;
    void data;
  }

  async function evidence() {
    const system = await request("/system/status");
    activeRun = activeRun || system.runs.runs[0]?.run_id;
    if (!activeRun) { view.innerHTML = "<h2>Gates, júri, diagnóstico e decisões</h2><p class=\"empty\">Sem execução durável para projetar evidência.</p>"; return; }
    const data = await request(`/runs/${encodeURIComponent(activeRun)}/evidence`);
    view.innerHTML = `<h2>Gates, júri, diagnóstico e decisões</h2><p class="muted">A apresentação mantém a cegueira do júri: não há autoria, ordem de criação nem metadados de champion em uma avaliação em curso.</p><section class="panel"><h3>Gates determinísticos</h3><div class="table-wrap"><table><thead><tr><th>Gate</th><th>Resultado</th><th>Verificador</th><th>Duração</th><th>Hash de entrada</th></tr></thead><tbody>${data.gates.map((gate) => `<tr><td>${esc(gate.gate_id)}${gate.gate_id === "correctness_math" ? " · hard gate" : ""}</td><td>${state(gate.passed)}</td><td>${esc(gate.command)}<br><small>${esc(gate.verifier_version)}</small></td><td>${esc(gate.duration_ms)} ms</td><td>${hash(gate.input_hash)}</td></tr>`).join("") || "<tr><td colspan=\"5\">Ainda não há GateReport confirmado.</td></tr>"}</tbody></table></div></section><section class="grid"><article class="panel"><h3>Júri cego</h3><pre>${pretty(data.jury)}</pre></article><article class="panel"><h3>Diagnóstico</h3><pre>${pretty(data.diagnosis)}</pre></article><article class="panel"><h3>Decisão e Pareto</h3><pre>${pretty(data.decision)}</pre></article><article class="panel"><h3>Finalização</h3><pre>${pretty(data.finalization)}</pre></article></section><p class="small muted">O gate <code>correctness_math</code> continua duro; este painel não transforma aprovação visual em autorização de finalização.</p>`;
  }

  async function budget() {
    const data = await request("/budget");
    view.innerHTML = `<h2>Orçamento e custo</h2><p class="muted">Valores monetários usam microunits inteiros; custo incerto permanece separado de custo reconciliado.</p>${data.budgets.length ? data.budgets.map((budget) => `<section class="panel"><h3>${esc(budget.run_id)}</h3><p>Estado ${state(budget.state)} · assurance ${esc(budget.assurance)}</p>${cards([["Teto configurado", esc(budget.usage?.by_limit?.max_run_cost_microunits?.limit ?? "—")], ["Custo reconciliado", esc(budget.usage?.confirmed_cost_microunits ?? "0")], ["Reserva", esc(budget.usage?.reserved_cost_microunits ?? "0")], ["Saldo", esc(budget.available?.cost_microunits ?? "—")]])}<details><summary>Reservas, admissão e alertas</summary><pre>${pretty({reservations: budget.reservations, alerts: budget.alerts, authorization: budget.authorization})}</pre></details></section>`).join("") : "<p class=\"empty\">Não há ledger de orçamento para projetar.</p>"}`;
  }

  function defaultFor(schema) {
    if (!schema) return "";
    if (Object.prototype.hasOwnProperty.call(schema, "const")) return schema.const;
    const type = Array.isArray(schema.type) ? schema.type[0] : schema.type;
    if (type === "object") return Object.fromEntries(Object.entries(schema.properties || {}).map(([name, child]) => [name, defaultFor(child)]));
    if (type === "array") return [];
    if (type === "boolean") return false;
    if (type === "integer" || type === "number") return 0;
    return "";
  }

  function renderTyped(value, schema, label = "configuração", path = "root") {
    const id = `field-${crypto.randomUUID()}`;
    if (Array.isArray(value)) {
      return `<fieldset class="fieldset"><legend>${esc(label)}</legend>${value.map((item, index) => renderTyped(item, schema?.items, `${label} ${index + 1}`, `${path}.${index}`)).join("") || "<p class=\"small muted\">Lista vazia. Campos canônicos não são criados por texto livre.</p>"}</fieldset>`;
    }
    if (value && typeof value === "object") {
      const extra = schema?.additionalProperties;
      const add = extra && extra !== true ? `<div class="toolbar small"><label for="${id}">Nova chave</label><input id="${id}" data-map-key="${esc(path)}" pattern="[A-Za-z0-9_.-]+"><button class="button secondary" type="button" data-add-map="${esc(path)}">Adicionar campo tipado</button></div>` : "";
      return `<fieldset class="fieldset"><legend>${esc(label)}</legend>${Object.keys(value).map((name) => renderTyped(value[name], schema?.properties?.[name] || extra, name, `${path}.${name}`)).join("")}${add}</fieldset>`;
    }
    if (typeof value === "boolean") return `<div class="field"><label for="${id}">${esc(label)}</label><select id="${id}" data-editor-value data-type="boolean"><option value="true" ${value ? "selected" : ""}>true</option><option value="false" ${!value ? "selected" : ""}>false</option></select></div>`;
    if (typeof value === "number") return `<div class="field"><label for="${id}">${esc(label)}</label><input id="${id}" data-editor-value data-type="number" type="number" min="0" value="${esc(value)}"></div>`;
    const protectedValue = value === "[REDACTED]";
    const enumOptions = schema?.enum ? schema.enum.map((item) => `<option value="${esc(item)}" ${item === value ? "selected" : ""}>${esc(item)}</option>`).join("") : null;
    return `<div class="field"><label for="${id}">${esc(label)}</label>${enumOptions ? `<select id="${id}" data-editor-value data-type="string">${enumOptions}</select>` : `<input id="${id}" data-editor-value data-type="string" value="${esc(value ?? "")}" ${protectedValue ? "disabled aria-describedby=\"redacted-note\"" : ""}>`}</div>`;
  }

  function bindTypedForm(container, source) {
    const inputs = container.querySelectorAll("[data-editor-value]");
    inputs.forEach((input) => input.addEventListener("change", () => {
      // A full rerender maps field order to the typed source recursively. This
      // avoids accepting YAML or a raw JSON editing surface.
      const all = [...container.querySelectorAll("[data-editor-value]")];
      let pointer = 0;
      const hydrate = (value) => {
        if (Array.isArray(value)) return value.map(hydrate);
        if (value && typeof value === "object") { Object.keys(value).forEach((name) => { value[name] = hydrate(value[name]); }); return value; }
        const element = all[pointer++];
        if (!element || element.disabled) return value;
        if (typeof value === "boolean") return element.value === "true";
        if (typeof value === "number") return Number(element.value);
        return element.value;
      };
      hydrate(source);
    }));
  }

  async function config() {
    const data = await request("/config");
    view.innerHTML = `<h2>Configuração</h2><p class="muted">Cada superfície versionada tem origem, hash e formulário tipado. Não há editor YAML, terminal nem edição de arquivos arbitrários. Mudanças ficam em rascunho e só valem para execuções futuras.</p><div class="toolbar"><label for="config-select">Superfície</label><select id="config-select"><option value="">Selecione uma configuração</option>${data.configuration.map((item, index) => `<option value="${index}">${esc(item.category)} · ${esc(item.path)}</option>`).join("")}</select></div><section id="config-editor" class="panel"><p class="empty">Selecione uma configuração para criar um rascunho tipado.</p></section>`;
    document.querySelector("#config-select").addEventListener("change", () => {
      const item = data.configuration[Number(document.querySelector("#config-select").value)];
      if (!item) return;
      const value = structuredClone(item.value);
      const editor = document.querySelector("#config-editor");
      const renderEditor = () => {
        editor.innerHTML = `<h3>${esc(item.path)}</h3><p class="small">Hash atual: ${hash(item.hash)} · impacto: ${esc(item.impact)}</p><p id="redacted-note" class="small muted">Campos redigidos nunca são devolvidos pela API nem gravados no log da Central.</p><form id="config-form">${renderTyped(value, item.schema, "valor")}<div class="toolbar"><button class="button" type="submit">Criar e validar rascunho</button></div></form><div id="draft-result"></div>`;
        bindTypedForm(editor, value);
        editor.querySelectorAll("[data-add-map]").forEach((button) => button.addEventListener("click", () => {
          const path = button.dataset.addMap;
          const input = editor.querySelector(`[data-map-key="${CSS.escape(path)}"]`);
          const name = input?.value?.trim();
          if (!name || !/^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(name)) { showNotice("A nova chave deve ser um identificador seguro.", true); return; }
          const target = path.split(".").slice(1).reduce((current, part) => current?.[part], value);
          const schema = path.split(".").slice(1).reduce((current, part) => current?.properties?.[part] || current?.additionalProperties, item.schema);
          if (!target || typeof target !== "object" || Object.prototype.hasOwnProperty.call(target, name)) { showNotice("A chave já existe ou o mapa não é editável.", true); return; }
          target[name] = defaultFor(schema);
          renderEditor();
        }));
        editor.querySelector("#config-form").addEventListener("submit", submitDraft);
      };
      const submitDraft = async (event) => {
        event.preventDefault();
        if (!confirm(`Criar rascunho tipado para ${item.path}?`)) return;
        try {
          const draft = await post("/config/drafts", {confirmed: true, config_path: item.path, base_hash: item.hash, value});
          const validate = await post(`/config/drafts/${draft.result.draft_id}/validate`, {confirmed: true, expected_hash: draft.result.candidate_hash});
          document.querySelector("#draft-result").innerHTML = `<p>Rascunho validado: ${hash(validate.result.candidate_hash)}</p><details open><summary>Diff antes/depois</summary><pre>${pretty(validate.result.diff)}</pre></details><button class="button danger" id="apply-draft">Aplicar para futuras execuções</button>`;
          document.querySelector("#apply-draft").addEventListener("click", async () => {
            if (!confirm("Aplicar esta configuração? A aplicação falhará se houver execução ativa ou versão stale.")) return;
            try { const applied = await post(`/config/drafts/${validate.result.draft_id}/apply`, {confirmed: true, expected_hash: validate.result.candidate_hash}); showNotice(`Configuração aplicada: ${applied.result.applied_hash}`); await config(); }
            catch (error) { showNotice(error.message, true); }
          });
        } catch (error) { showNotice(error.message, true); }
      };
      renderEditor();
    });
  }

  async function audit() {
    const [auditData, errorData] = await Promise.all([request("/audit"), request("/errors?limit=100")]);
    view.innerHTML = `<h2>Auditoria e erros</h2><p class="muted">Ações de operador são mantidas em um ledger separado, hash-encadeado, sem alterar o journal científico.</p><section class="panel"><h3>Ledger de ações</h3><div class="table-wrap"><table><thead><tr><th>Sequência</th><th>Ação</th><th>Resultado</th><th>Antes</th><th>Depois</th></tr></thead><tbody>${auditData.events.map((item) => `<tr><td>${esc(item.sequence)}</td><td>${esc(item.action)}</td><td>${esc(item.outcome)}</td><td>${hash(item.before_hash)}</td><td>${hash(item.after_hash)}</td></tr>`).join("") || "<tr><td colspan=\"5\">Nenhuma ação de operador.</td></tr>"}</tbody></table></div></section><section class="panel"><h3>Warnings e erros operacionais</h3><pre>${pretty(errorData.errors)}</pre></section>`;
  }

  const renderers = {overview, runs, topology, evidence, budget, config, audit};
  async function render() {
    clearNotice();
    try { await renderers[currentView](); }
    catch (error) { view.innerHTML = `<h2>Informação indisponível</h2><p class="danger-text">${esc(error.message)}</p>`; }
  }

  function startEvents() {
    const stream = new EventSource(`${api}/events/stream${eventCursor ? `?cursor=${encodeURIComponent(eventCursor)}` : ""}`);
    setConnection("Ao vivo — aguardando eventos duráveis confirmados.");
    stream.addEventListener("durable", (event) => { eventCursor = event.lastEventId || eventCursor; setConnection("Ao vivo — atualização confirmada."); if (currentView !== "config") render(); });
    stream.onerror = () => {
      stream.close();
      setConnection("Reconectando — usando atualização somente leitura enquanto o stream retorna.");
      if (pollTimer) clearInterval(pollTimer);
      pollTimer = setInterval(async () => {
        try { const data = await request(`/events${eventCursor ? `?cursor=${encodeURIComponent(eventCursor)}` : ""}`); eventCursor = data.next_cursor || eventCursor; if (data.events.length) await render(); setConnection("Atualização atrasada — polling local ativo."); }
        catch { setConnection("Sem execução ativa ou conexão local indisponível."); }
      }, 4000);
      setTimeout(() => { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } startEvents(); }, 6000);
    };
  }

  document.querySelectorAll(".nav-button").forEach((button) => button.addEventListener("click", async () => {
    document.querySelectorAll(".nav-button").forEach((item) => item.classList.remove("active"));
    button.classList.add("active"); currentView = button.dataset.view; await render();
  }));
  render().then(startEvents);
})();
