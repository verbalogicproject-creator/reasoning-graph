const $ = (selector) => document.querySelector(selector);
let csrfToken = "";
const api = async (url, options = {}) => {
  const requestOptions = {...options, headers: {...(options.headers || {})}};
  if (String(requestOptions.method || "GET").toUpperCase() !== "GET") {
    requestOptions.headers["X-CSRF-Token"] = csrfToken;
  }
  const response = await fetch(url, requestOptions);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
};
const esc = (value) => String(value ?? "").replace(/[&<>\"]/g, (c) => ({"&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;"}[c]));
function notice(selector, text) { $(selector).textContent = text; }

function renderGraph(path) {
  const host = $("#path-graph");
  host.replaceChildren();
  if (!path?.length) { host.textContent = "No traversable declared path was returned."; return; }
  const nodes = [...new Set(path.flatMap((edge) => [edge.source, edge.target]))];
  const elements = [
    ...nodes.map((id) => ({data: {id, label: id}})),
    ...path.map((edge, index) => ({data: {id: `edge-${index}`, source: edge.source, target: edge.target, label: edge.edge_type}})),
  ];
  cytoscape({
    container: host,
    elements,
    layout: {name: "breadthfirst", directed: true, padding: 20, spacingFactor: 1.25},
    style: [
      {selector: "node", style: {"background-color": "#1769d2", label: "data(label)", color: "#152033", "font-family": "monospace", "font-size": 10, "text-wrap": "wrap", "text-max-width": 110, "text-valign": "bottom", "text-margin-y": 6}},
      {selector: "edge", style: {width: 2, "line-color": "#1769d2", "target-arrow-color": "#1769d2", "target-arrow-shape": "triangle", "curve-style": "bezier", label: "data(label)", color: "#627087", "font-family": "monospace", "font-size": 9, "text-rotation": "autorotate"}},
    ],
  });
}
function renderProvenance(items) {
  $("#provenance").innerHTML = (items || []).map((item) => `<li><code>${esc(item.source)} to ${esc(item.target)} (${esc(item.edge_type)})</code><br><span>${esc(item.confidence_basis)} · ${esc(item.support_kind)}</span></li>`).join("") || "<li>No provenance was returned.</li>";
}
async function resolveQuery(event) {
  event.preventDefault();
  const query = $("#query").value.trim();
  $("#resolve-result").hidden = true;
  notice("#resolve-state", "Resolving against the bound graph...");
  try {
    const data = await api(`/api/resolve?text=${encodeURIComponent(query)}&weighted=${$("#weighted").checked}&include_dormant=${$("#dormant").checked}`);
    $("#answer-status").textContent = data.status;
    $("#answer-confidence").textContent = data.confidence == null ? "no confidence" : `${data.confidence} ${data.confidence_kind || ""}`;
    $("#answer-kind").textContent = [data.path_class, data.support_kind].filter(Boolean).join(" · ");
    $("#answer-text").textContent = data.answer || data.refusal?.reason || "No answer text returned.";
    renderGraph(data.path); renderProvenance(data.provenance);
    $("#resolve-result").hidden = false;
    notice("#resolve-state", data.status === "REFUSE" ? "The graph refused to make an unsupported claim." : "Resolved from declared graph evidence.");
  } catch (error) { notice("#resolve-state", error.message); }
}
function keyValues(host, object) {
  $(host).innerHTML = Object.entries(object || {}).map(([key, value]) => `<div><strong>${esc(key.replaceAll("_", " "))}</strong><span>${esc(typeof value === "object" ? JSON.stringify(value) : value)}</span></div>`).join("") || "<div>No entries.</div>";
}
function renderObservations(entries) {
  $("#observation-list").innerHTML = (entries || []).slice().reverse().map((item) => `<li><code>${esc(item.event_id)}</code> · ${esc(item.resolution_status)} / ${esc(item.outcome)}<br>${esc(item.query)}</li>`).join("") || "<li>No observations recorded.</li>";
}
function renderMemory(entries) {
  $("#memory-list").innerHTML = (entries || []).map((item) => {
    const approve = item.status === "reviewable" ? `<button type="button" data-memory-id="${esc(item.memory_id)}">Review and approve</button>` : "";
    return `<li><code>${esc(item.kind)}</code> · ${esc(item.status)}<br>${esc(item.content)}${approve}</li>`;
  }).join("") || "<li>No memory candidates await review.</li>";
  document.querySelectorAll("[data-memory-id]").forEach((button) => {
    button.onclick = async () => {
      const memoryId = button.dataset.memoryId;
      const confirmation = window.prompt(`Type APPROVE MEMORY ${memoryId} to activate this entry.`) || "";
      try {
        await api("/api/memory/approve", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({approve:true, memory_id:memoryId, confirmation})});
        notice("#memory-state", "Memory activated after explicit confirmation.");
        renderMemory((await api("/api/memory/review")).review);
      } catch (error) { notice("#memory-state", error.message); }
    };
  });
}
async function load() {
  try {
    const [overview, gaps, candidates, observations, memories] = await Promise.all([api("/api/overview"), api("/api/gaps"), api("/api/candidates"), api("/api/observations"), api("/api/memory/review")]);
    $("#instance-label").textContent = overview.instance;
    $("#count-value").textContent = `${overview.integrity.counts.nodes} / ${overview.integrity.counts.edges}`;
    $("#integrity-value").textContent = overview.integrity.ok ? "PASS" : "ATTENTION";
    $("#frontier-value").textContent = overview.gap_count;
    $("#observations-value").textContent = overview.observation_count;
    keyValues("#integrity-detail", Object.fromEntries(Object.entries(overview.integrity).filter(([, value]) => Array.isArray(value)).map(([key, value]) => [key, value.length])));
    keyValues("#frontier-detail", overview.frontier);
    $("#gap-list").innerHTML = gaps.entries.map((entry) => `<li><code>${esc(entry.id)}</code> · ${esc(entry.status)}<br>${esc(entry.title || entry.gap_shape || "untitled")}</li>`).join("") || "<li>No frontier entries.</li>";
    $("#candidate-list").innerHTML = candidates.entries.map((entry) => `<div><strong>${esc(entry.name)}</strong><span>${esc(entry.bytes)} bytes · staged</span></div>`).join("") || "<div>No staged candidates.</div>";
    renderObservations(observations.entries);
    renderMemory(memories.review);
  } catch (error) { notice("#resolve-state", `Workbench data unavailable: ${error.message}`); }
}
$("#resolve-form").addEventListener("submit", resolveQuery);
$("#observation-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const data = Object.fromEntries(new FormData(event.target));
  try { await api("/api/observations", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(data)}); notice("#observation-state", "Observation appended. Active graph rules were not changed."); event.target.reset(); renderObservations((await api("/api/observations")).entries); } catch (error) { notice("#observation-state", error.message); }
});
$("#memory-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  data.agent_acknowledged = data.agent_acknowledged === "on";
  if (data.evidence) {
    try { data.evidence = JSON.parse(data.evidence); }
    catch { notice("#memory-state", "Evidence must be valid JSON."); return; }
  } else {
    delete data.evidence;
  }
  if (!data.validation) delete data.validation;
  if (!data.agreement) delete data.agreement;
  try {
    await api("/api/memory", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(data)});
    notice("#memory-state", "Memory proposed. Activation still requires review and typed confirmation.");
    event.target.reset();
    renderMemory((await api("/api/memory/review")).review);
  } catch (error) { notice("#memory-state", error.message); }
});
async function action(path, body) {
  try { const result = await api(path, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({...body, approve:true})}); notice("#approval-state", JSON.stringify(result)); load(); } catch (error) { notice("#approval-state", error.message); }
}
$("#verify-button").onclick = () => action("/api/actions/verify", {staged_path: $("#freeze-file").value});
$("#freeze-button").onclick = () => action("/api/actions/freeze", {staged_path: $("#freeze-file").value, confirmation: $("#freeze-confirmation").value});
$("#retire-button").onclick = () => action("/api/actions/retire", {confirmation: $("#retire-confirmation").value});
async function initialize() {
  const session = await api("/api/session");
  csrfToken = session.csrf_token;
  await load();
}
initialize().catch((error) => notice("#resolve-state", `Workbench data unavailable: ${error.message}`));
