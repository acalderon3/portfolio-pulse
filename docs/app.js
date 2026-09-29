/* Portfolio Pulse demo. Static: reads the recorded snapshot in data/ and makes no API calls. */
(() => {
"use strict";

const S = { data: null, evalr: null, preread: "", check: null, log: "", reg: { q: "", team: "", health: "", gap: false, t1: false, sort: "sev", dir: 1 }, graphMode: "all", riskRule: "" };
const $ = (sel, el = document) => el.querySelector(sel);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const SEV = { red: 0, amber: 1, green: 2, done: 3 };
const LABEL = { green: "Green", amber: "Amber", red: "Red", done: "Done" };
const RULE = { past_due: "Past due", blocker_age: "Blocked", dependency_late: "Dependency lands late", slip: "Slipped",
  upstream_red: "Upstream is Red", in_freeze: "In change freeze", conflicting_signal: "Conflicting signal",
  stale: "Stale update", missing_basics: "Missing owner or date" };
const SOURCE = { jira: "Jira epic export", sheet: "Tracker spreadsheet", confluence: "Confluence pages", status_doc: "Weekly status doc", slack: "Slack channels", steering: "Steering-committee notes" };
const FIELD = { owner: "Owner", self_status: "Reported status", target: "Target date", baseline: "Baseline date", last_update: "Last update", blocker: "Blocker", depends_on: "Dependencies", why: "Why it matters" };
const repoUrl = (() => { const h = location.hostname; if (!h.endsWith("github.io")) return "https://github.com/acalderon3/portfolio-pulse"; const r = location.pathname.split("/").filter(Boolean)[0]; return r ? `https://github.com/${h.split(".")[0]}/${r}` : null; })();
const codeLink = path => repoUrl ? `<a href="${repoUrl}/blob/main/${path}" target="_blank" rel="noopener"><code>${esc(path)}</code></a>` : `<code>${esc(path)}</code>`;

/* ---------- small helpers */
function icon(h, size = 10) {
  const s = size, c = s / 2;
  if (h === "green") return `<svg width="${s}" height="${s}" aria-hidden="true"><circle cx="${c}" cy="${c}" r="${c}" fill="var(--good)"/></svg>`;
  if (h === "amber") return `<svg width="${s + 1}" height="${s}" aria-hidden="true"><path d="M${(s + 1) / 2} 0 L${s + 1} ${s} L0 ${s} Z" fill="var(--warn)"/></svg>`;
  if (h === "red") return `<svg width="${s}" height="${s}" aria-hidden="true"><rect width="${s}" height="${s}" rx="2" fill="var(--crit)"/></svg>`;
  if (h === "done") return `<svg width="${s}" height="${s}" aria-hidden="true"><path d="M1 ${c} L${c - 1} ${s - 1.5} L${s - 1} 1.5" stroke="var(--done)" stroke-width="2" fill="none"/></svg>`;
  return `<svg width="${s}" height="${s}" aria-hidden="true"><rect y="${c - 1}" width="${s}" height="2" fill="var(--text-3)"/></svg>`;
}
const st = h => h ? `<span class="st">${icon(h)}${LABEL[h]}</span>` : `<span class="st none">${icon(null)}Not stated</span>`;
const P = id => S.data.programs.find(p => p.id === id);
const pill = id => { const p = P(id); return p ? `<span class="pill" data-open="${id}" title="${esc(p.name)}">${icon(p.health, 9)}${id}</span>` : esc(id); };
const fmt = d => d ? new Date(d + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "None";
const fmtShort = d => d ? new Date(d + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "None";
const addDays = (d, n) => { const x = new Date(d + "T12:00:00"); x.setDate(x.getDate() + n); return x.toISOString().slice(0, 10); };
const active = () => S.data.programs.filter(p => p.health !== "done");

const tip = $("#tip");
function showTip(html, e) { tip.innerHTML = html; tip.style.display = "block"; moveTip(e); }
function moveTip(e) { const w = tip.offsetWidth, h = tip.offsetHeight; let x = e.clientX + 14, y = e.clientY + 14; if (x + w > innerWidth - 8) x = e.clientX - w - 14; if (y + h > innerHeight - 8) y = e.clientY - h - 14; tip.style.left = x + "px"; tip.style.top = y + "px"; }
function hideTip() { tip.style.display = "none"; }

/* ---------- tiny markdown (headings, lists, bold, italic, code, links, program IDs) */
function inline(s) {
  s = esc(s);
  const codes = [];
  s = s.replace(/`([^`]+)`/g, (_, c) => { codes.push(c); return `\u0000${codes.length - 1}\u0000`; });
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
       .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
       .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>")
       .replace(/\b((?:ERP|SCT|COM|CX|WPT|EAI)-\d\d)\b/g, '<span class="pid" data-open="$1">$1</span>');
  return s.replace(/\u0000(\d+)\u0000/g, (_, i) => `<code>${codes[i]}</code>`);
}
function md(src) {
  let out = "", list = false, para = [];
  const flush = () => { if (para.length) { out += `<p>${inline(para.join(" "))}</p>`; para = []; } };
  for (const line of src.split("\n")) {
    const h = line.match(/^(#{1,3}) (.*)/);
    if (h) { flush(); if (list) { out += "</ul>"; list = false; } out += `<h${h[1].length}>${inline(h[2])}</h${h[1].length}>`; continue; }
    if (/^- /.test(line)) { flush(); if (!list) { out += "<ul>"; list = true; } out += `<li>${inline(line.slice(2))}</li>`; continue; }
    if (!line.trim()) { flush(); if (list) { out += "</ul>"; list = false; } continue; }
    if (list) { out += "</ul>"; list = false; }
    para.push(line);
  }
  flush(); if (list) out += "</ul>";
  return out;
}

/* ---------- drawer */
function openProgram(id) {
  const p = P(id); if (!p) return;
  const ev = Object.entries(p.evidence).map(([f, e]) => `
    <div class="receipt"><div class="meta"><strong>${FIELD[f] || f}</strong>
      <span class="badge ${e.by === "model" ? "model" : ""}">${e.by === "model" ? "extracted by Claude, quote verified" : "parsed"}</span>
      <a href="data/sources/${esc(e.source)}" target="_blank" rel="noopener">${esc(e.source)}</a><span>${esc(e.locator)}</span></div>
      <div class="q">${esc(e.quote) || "<em>(empty)</em>"}</div></div>`).join("");
  const rules = p.reasons.length ? p.reasons.map(r => `<div class="rule-row">${icon(r.level)}<div><strong>${RULE[r.rule]}</strong><div class="muted small">${inline(r.detail)}</div></div></div>`).join("")
    : `<div class="muted small">${p.health === "done" ? "Program is complete." : "No rule fired, so it's Green on the evidence."}</div>`;
  const notes = p.notes.length ? `<h3 class="section">Signals from chat and notes</h3>` + p.notes.map(n => `<div class="receipt"><div class="meta"><strong>${n.kind === "contradicts_reported_status" ? "Contradicts reported status" : "Schedule risk"}</strong><span class="badge model">extracted by Claude</span><span>${esc(n.locator)}</span></div><div class="small" style="margin-top:4px">${esc(n.summary)}</div><div class="q">“${esc(n.quote)}”</div></div>`).join("") : "";
  $("#drawer").innerHTML = `
    <button class="close" id="dclose" type="button">Close</button>
    <div class="tiny">${esc(p.id)} · ${esc(p.team_name)} · Tier ${p.tier}</div>
    <h2>${esc(p.name)}</h2>
    <div class="muted small">${esc(p.why || "Why it matters: not stated in the source.")}</div>
    <dl class="kv">
      <dt>Evidence</dt><dd>${st(p.health)} ${p.status_gap ? `<span class="gapmark">· reported ${LABEL[p.self_status]}</span>` : ""}</dd>
      <dt>Reported</dt><dd>${st(p.self_status)}</dd>
      <dt>Owner</dt><dd>${esc(p.owner) || '<span class="gapmark">No owner</span>'}</dd>
      <dt>Target</dt><dd>${fmt(p.target)}${p.baseline && p.baseline !== p.target ? ` <span class="muted">(baseline ${fmtShort(p.baseline)})</span>` : ""}</dd>
      <dt>Forecast</dt><dd>${fmt(p.forecast)}${p.forecast && p.target && p.forecast > p.target ? ' <span class="gapmark">late on dependencies</span>' : ""}</dd>
      <dt>Last update</dt><dd>${fmt(p.last_update)}</dd>
      <dt>Blocker</dt><dd>${p.blocker_text ? esc(p.blocker_text) + (p.blocker_since ? ` <span class="muted">since ${fmtShort(p.blocker_since)}</span>` : "") : '<span class="muted">None</span>'}</dd>
      <dt>Depends on</dt><dd>${p.upstream.map(pill).join(" ") || '<span class="muted">Nothing</span>'}</dd>
      <dt>Feeds</dt><dd>${p.downstream.map(pill).join(" ") || '<span class="muted">Nothing</span>'}</dd>
    </dl>
    <h3 class="section">Why it's ${p.health === "done" ? "done" : LABEL[p.health]}</h3>${rules}
    ${notes}
    <h3 class="section">Receipts</h3>
    <p class="tiny" style="margin-top:-4px">Every field links back to the team's own artifact. Nobody filled in a separate report.</p>${ev}`;
  $("#drawer").classList.add("open"); $("#scrim").classList.add("open");
  $("#dclose").onclick = closeDrawer; $("#drawer").scrollTop = 0;
}
function closeDrawer() { $("#drawer").classList.remove("open"); $("#scrim").classList.remove("open"); }
$("#scrim").onclick = closeDrawer;
addEventListener("keydown", e => { if (e.key === "Escape") closeDrawer(); });
document.addEventListener("click", e => { const t = e.target.closest("[data-open]"); if (t) { e.preventDefault(); openProgram(t.dataset.open); } });

/* ---------- views */
function overview() {
  const d = S.data, sum = d.summary, h = sum.health;
  const cols = ["green", "amber", "red"], rows = ["green", "amber", "red", "None"];
  const cnt = {}; active().forEach(p => { const k = (p.self_status || "None") + "|" + p.health; cnt[k] = (cnt[k] || 0) + 1; });
  const max = Math.max(...Object.values(cnt));
  const matrix = `<table class="matrix"><thead><tr><th></th>${cols.map(c => `<th>${st(c)}</th>`).join("")}</tr></thead><tbody>
    ${rows.map(r => `<tr><th class="row">${r === "None" ? "Not stated" : LABEL[r]}</th>${cols.map(c => {
      const n = cnt[r + "|" + c] || 0, pct = n ? Math.round(12 + 70 * n / max) : 0, gap = r !== "None" && SEV[c] < SEV[r];
      return `<td class="${gap && n ? "gap" : ""}" style="background:${n ? `color-mix(in srgb, var(--accent) ${pct}%, var(--surface))` : "var(--surface-2)"};color:${pct > 50 ? "#fff" : "var(--text)"}" title="Reported ${r === "None" ? "nothing" : LABEL[r]}, evidence says ${LABEL[c]}: ${n}">${n || ""}</td>`; }).join("")}</tr>`).join("")}
    </tbody></table>
    <div class="legend"><span>Rows: what the team reports. Columns: what the evidence says.</span><span><span style="display:inline-block;width:12px;height:12px;border:2px solid var(--crit);border-radius:3px;vertical-align:-2px"></span> Reported better than the evidence</span></div>`;

  const bars = d.teams.map(t => {
    const segs = ["green", "amber", "red", "done"].filter(k => t.health[k]).map(k => `<span data-tip="${esc(t.team_name)}: ${t.health[k]} ${LABEL[k]}" style="flex:${t.health[k]};background:var(--${{ green: "good", amber: "warn", red: "crit", done: "done" }[k]})"></span>`).join("");
    return `<div class="tbar"><div class="name">${esc(t.team_name)}<small>from ${SOURCE[t.source]}</small></div><div class="stack">${segs}</div><div class="count">${t.health.red || 0} R · ${t.health.amber || 0} A</div></div>`;
  }).join("");

  const chains = d.chains.map(c => {
    const r = P(c.root), why = r.reasons.filter(x => !["upstream_red", "dependency_late"].includes(x.rule)).map(x => x.detail.replace(/\.$/, "")).join(". ") + ".";
    return `<div class="card"><div class="tiny">Root cause · ${c.affected.length} programs downstream · across ${c.teams.length} teams</div>
      <div class="chain-root" style="margin-top:6px">${pill(c.root)}<div><div class="big">${esc(r.name)}</div><div class="muted small">${esc(why)}</div></div></div>
      <div class="chain-list">${c.affected.map(pill).join("")}</div>
      <div class="tiny" style="margin-top:8px">${c.red.length} of these are Red because they can't finish before ${esc(c.root)} does. ${c.affected.filter(i => P(i).self_status === "green").length} of them report Green.</div></div>`;
  }).join("");

  return `<div class="banner">Synthetic demo: <strong>Kestrel Health</strong> is a fictional wearables company. It has 100 IT programs across six teams, and each team tracks status in a different place. Snapshot as of Monday, ${fmt(d.as_of)}.</div>
  <h2 class="view-title">This week at a glance</h2>
  <p class="lede">Health comes from evidence (dates, blockers, dependencies, freshness), not from what teams say. One rubric applies to every team, and every Amber or Red traces back to a fact in the team's own artifact.</p>
  <div class="grid g4">
    <div class="card kpi"><div class="st">${icon("red")}Red</div><div class="n">${h.red}</div><div class="l">need a decision or an unblock</div></div>
    <div class="card kpi"><div class="st">${icon("amber")}Amber</div><div class="n">${h.amber}</div><div class="l">at risk or can't be verified</div></div>
    <div class="card kpi"><div class="n">${sum.status_gaps}</div><div class="l">programs <strong>report better than their evidence</strong>, mostly Green that is really Amber or Red</div></div>
    <div class="card kpi"><div class="n">${sum.hidden_dependencies}</div><div class="l">cross-team dependencies that exist <strong>only in chat or meeting notes</strong>, found by Claude</div></div>
  </div>
  <h3 class="section" style="margin-top:26px">Two blockers explain most of the Red</h3>
  <div class="grid g2">${chains}</div>
  <div class="grid g2 section" style="margin-top:16px">
    <div class="card"><h3>Reported status vs evidence</h3>${matrix}</div>
    <div class="card"><h3>Health by team</h3>${bars}
      <div class="legend">${["green", "amber", "red", "done"].map(k => `<span class="st">${icon(k)}${LABEL[k]}</span>`).join("")}</div></div>
  </div>`;
}

function register() {
  const f = S.reg;
  const teams = S.data.teams.map(t => `<option value="${t.team}" ${f.team === t.team ? "selected" : ""}>${esc(t.team_name)}</option>`).join("");
  return `<h2 class="view-title">Program register</h2>
  <p class="lede">All 100 programs in one table, with the same fields for every team. Click a row to see the receipts: the exact file, row or message each value came from.</p>
  <div class="filters">
    <input type="search" id="rq" placeholder="Search program, owner, ID…" value="${esc(f.q)}" aria-label="Search">
    <select id="rteam" aria-label="Team"><option value="">All teams</option>${teams}</select>
    <select id="rhealth" aria-label="Health"><option value="">Any health</option>${["red", "amber", "green", "done"].map(h => `<option value="${h}" ${f.health === h ? "selected" : ""}>${LABEL[h]}</option>`).join("")}</select>
    <label><input type="checkbox" id="rgap" ${f.gap ? "checked" : ""}> Reported better than evidence</label>
    <label><input type="checkbox" id="rt1" ${f.t1 ? "checked" : ""}> Tier 1 only</label>
    <span class="tiny" id="rcount"></span>
  </div>
  <div class="table-wrap"><table class="reg"><thead><tr>
    ${[["id", "ID"], ["name", "Program"], ["team", "Team"], ["owner", "Owner"], ["self", "Reported"], ["sev", "Evidence"], ["target", "Target → forecast"], ["last", "Last update"], ["reason", "Main reason"]].map(([k, l]) => `<th data-sort="${k}">${l}${f.sort === k ? (f.dir > 0 ? " ↑" : " ↓") : ""}</th>`).join("")}
  </tr></thead><tbody id="rbody"></tbody></table></div>`;
}
function fillRegister() {
  const f = S.reg, q = f.q.toLowerCase();
  let rows = S.data.programs.filter(p => (!f.team || p.team === f.team) && (!f.health || p.health === f.health) && (!f.gap || p.status_gap) && (!f.t1 || p.tier === 1)
    && (!q || [p.id, p.name, p.owner, p.team_name].join(" ").toLowerCase().includes(q)));
  const key = { id: p => p.id, name: p => p.name, team: p => p.team, owner: p => p.owner || "~", self: p => SEV[p.self_status] ?? 9, sev: p => SEV[p.health] * 10 + p.tier, target: p => p.target || "9", last: p => p.last_update || "", reason: p => p.reasons[0]?.rule || "~" }[f.sort];
  rows.sort((a, b) => (key(a) > key(b) ? 1 : key(a) < key(b) ? -1 : 0) * f.dir);
  $("#rbody").innerHTML = rows.map(p => {
    const top = [...p.reasons].sort((a, b) => SEV[a.level] - SEV[b.level])[0];
    const late = p.forecast && p.target && p.forecast > p.target;
    return `<tr data-open="${p.id}"><td class="mono">${p.id}</td>
      <td><div class="pname">${esc(p.name)}</div><div class="why-line">${esc(p.why || "")}</div></td>
      <td class="small">${esc(p.team)}</td><td class="small">${esc(p.owner) || '<span class="gapmark">None</span>'}</td>
      <td>${st(p.self_status)}</td>
      <td>${st(p.health)}${p.status_gap ? '<div class="gapmark">↑ gap</div>' : ""}</td>
      <td class="small">${fmtShort(p.target)}${late ? ` → <span class="gapmark">${fmtShort(p.forecast)}</span>` : ""}</td>
      <td class="small">${fmtShort(p.last_update)}</td>
      <td class="reason">${top ? `<strong>${RULE[top.rule]}.</strong> ${esc(top.detail)}${p.reasons.length > 1 ? ` <span class="tiny">+${p.reasons.length - 1} more</span>` : ""}` : ""}</td></tr>`;
  }).join("");
  $("#rcount").textContent = `${rows.length} of ${S.data.programs.length}`;
}
function bindRegister() {
  const f = S.reg, upd = () => fillRegister();
  $("#rq").oninput = e => { f.q = e.target.value; upd(); };
  $("#rteam").onchange = e => { f.team = e.target.value; upd(); };
  $("#rhealth").onchange = e => { f.health = e.target.value; upd(); };
  $("#rgap").onchange = e => { f.gap = e.target.checked; upd(); };
  $("#rt1").onchange = e => { f.t1 = e.target.checked; upd(); };
  document.querySelectorAll("th[data-sort]").forEach(th => th.onclick = () => { const k = th.dataset.sort; f.dir = f.sort === k ? -f.dir : 1; f.sort = k; render(); });
  fillRegister();
}

function dependencies() {
  const d = S.data;
  const hidden = d.edges.filter(e => e.hidden);
  return `<h2 class="view-title">Cross-team dependencies</h2>
  <p class="lede">${d.summary.dependencies} dependencies between ${new Set(d.edges.flatMap(e => [e.upstream, e.downstream])).size} programs. Blue links cross teams and appear only in chat or meeting notes, never in a tracker field. Claude found these by reading the text. Hover over a program to trace its chain, or click it to open it.</p>
  <div class="filters"><div class="seg" id="gmode">
    ${[["all", "All"], ["hidden", "Found only in chat/notes"], ...d.chains.map(c => [c.root, `${c.root} chain`])].map(([k, l]) => `<button type="button" data-mode="${k}" class="${S.graphMode === k ? "on" : ""}">${l}</button>`).join("")}
  </div></div>
  <div class="graph-wrap" id="gwrap"></div>
  <div class="legend">${["green", "amber", "red", "done"].map(k => `<span class="st">${icon(k)}${LABEL[k]}</span>`).join("")}
    <span><svg width="26" height="8"><path d="M0 4H26" stroke="var(--accent)" stroke-width="2"/></svg> In chat or notes only, cross-team</span>
    <span><svg width="26" height="8"><path d="M0 4H26" stroke="var(--edge)" stroke-width="1.5"/></svg> Recorded in a tracker field</span>
    <span>Arrows point from the program that has to finish first to the one that waits.</span></div>
  <div class="card section" style="margin-top:18px"><h3>Found only in chat and meeting notes (${hidden.length})</h3>
  <table class="simple"><thead><tr><th>Waits</th><th>On</th><th>Evidence (verbatim, checked against the source)</th><th>Where</th></tr></thead><tbody>
  ${hidden.map(e => `<tr><td>${pill(e.downstream)}</td><td>${pill(e.upstream)}</td><td class="small">“${esc(e.quote)}”</td><td class="tiny">${esc(e.source)}<br>${esc(e.locator)}</td></tr>`).join("")}
  </tbody></table></div>`;
}
function drawGraph() {
  const d = S.data;
  const teams = ["WPT", "EAI", "ERP", "COM", "SCT", "CX"];  // platforms first, so most links flow left to right
  const ids = [...new Set(d.edges.flatMap(e => [e.upstream, e.downstream]))];
  const colW = 196, rowH = 30, top = 48, left = 16;
  const nb = {}; ids.forEach(i => nb[i] = []);
  d.edges.forEach(e => { nb[e.upstream].push(e.downstream); nb[e.downstream].push(e.upstream); });
  const cols = teams.map(t => ids.filter(i => P(i).team === t).sort((a, b) => SEV[P(a).health] - SEV[P(b).health] || a.localeCompare(b)));
  const pos = {};
  const place = () => cols.forEach((col, ci) => col.forEach((id, ri) => pos[id] = { x: left + ci * colW + 8, y: top + ri * rowH }));
  place();
  for (let it = 0; it < 6; it++) {  // barycentre passes: pull linked programs level with each other
    cols.forEach(col => { const key = id => { const ys = nb[id].filter(n => P(n).team !== P(id).team).map(n => pos[n].y); return ys.length ? ys.reduce((a, b) => a + b) / ys.length : pos[id].y + 1e3; }; const k = {}; col.forEach(id => k[id] = key(id)); col.sort((a, b) => k[a] - k[b]); });
    place();
  }
  const maxRows = Math.max(...cols.map(c => c.length));
  const W = left * 2 + teams.length * colW, H = top + maxRows * rowH + 10;
  const edges = d.edges.map((e, i) => {
    const a = pos[e.upstream], b = pos[e.downstream];
    let path;
    if (Math.abs(a.x - b.x) < 1) { const bend = 26 + Math.min(40, Math.abs(a.y - b.y) / 6); path = `M${a.x - 6} ${a.y} C${a.x - bend} ${a.y}, ${b.x - bend} ${b.y}, ${b.x - 8} ${b.y}`; }
    else { const dir = b.x > a.x ? 1 : -1, sx = dir > 0 ? a.x + colW - 22 : a.x - 8, ex = dir > 0 ? b.x - 9 : b.x + colW - 20, mx = (sx + ex) / 2; path = `M${sx} ${a.y} C${mx} ${a.y}, ${mx} ${b.y}, ${ex} ${b.y}`; }
    return `<path class="edge ${e.hidden ? "hidden" : ""}" data-e="${i}" d="${path}" marker-end="url(#${e.hidden ? "arrH" : "arr"})"/>`;
  }).join("");
  const nodes = ids.map(id => {
    const p = P(id), { x, y } = pos[id], nm = p.name.length > 20 ? p.name.slice(0, 19) + "…" : p.name;
    const shape = { green: `<circle cx="${x}" cy="${y}" r="6" fill="var(--good)"/>`, amber: `<path d="M${x} ${y - 6.5} L${x + 7} ${y + 5.5} L${x - 7} ${y + 5.5} Z" fill="var(--warn)"/>`,
      red: `<rect x="${x - 6}" y="${y - 6}" width="12" height="12" rx="2" fill="var(--crit)"/>`, done: `<circle cx="${x}" cy="${y}" r="6" fill="var(--done)"/>` }[p.health];
    return `<g class="node" data-id="${id}"><rect x="${x - 10}" y="${y - 11}" width="${colW - 12}" height="22" fill="transparent" stroke="none"/>${shape}<text x="${x + 12}" y="${y + 4}" style="paint-order:stroke;stroke:var(--surface);stroke-width:3px"><tspan font-weight="600">${id}</tspan> ${esc(nm)}</text></g>`;
  }).join("");
  const heads = teams.map((t, ci) => `<text class="colhead" x="${left + ci * colW}" y="22">${esc(d.teams.find(x => x.team === t).team_name.replace("Enterprise Architecture", "Ent. Architecture"))}</text>`).join("");
  $("#gwrap").innerHTML = `<svg class="graph" id="graph" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="Dependency graph">
    <defs><marker id="arr" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="var(--edge)"/></marker>
    <marker id="arrH" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="var(--accent)"/></marker></defs>
    ${heads}<g>${edges}</g><g>${nodes}</g></svg>`;

  const svg = $("#graph");
  const reach = id => { const on = new Set([id]); const walk = (k, dir) => d.edges.forEach(e => { const [f, t] = dir ? [e.upstream, e.downstream] : [e.downstream, e.upstream]; if (f === k && !on.has(t)) { on.add(t); walk(t, dir); } }); walk(id, true); walk(id, false); return on; };
  function focus(set, edgeFilter) {
    svg.classList.toggle("focus", !!set);
    svg.querySelectorAll(".node").forEach(n => n.classList.toggle("on", !!set && set.has(n.dataset.id)));
    svg.querySelectorAll(".edge").forEach(p => { const e = d.edges[p.dataset.e]; p.classList.toggle("on", !!set && (edgeFilter ? edgeFilter(e) : set.has(e.upstream) && set.has(e.downstream))); });
  }
  function modeFocus() {
    const m = S.graphMode;
    if (m === "all") return focus(null);
    if (m === "hidden") { const h = d.edges.filter(e => e.hidden); return focus(new Set(h.flatMap(e => [e.upstream, e.downstream])), e => e.hidden); }
    const c = d.chains.find(c => c.root === m); focus(new Set([c.root, ...c.affected]));
  }
  svg.querySelectorAll(".node").forEach(n => {
    const id = n.dataset.id, p = P(id);
    n.onmouseenter = e => { focus(reach(id)); showTip(`<strong>${id} · ${esc(p.name)}</strong><br>${st(p.health)} · target ${fmtShort(p.target)}${p.forecast > p.target ? `, forecast <span class="gapmark">${fmtShort(p.forecast)}</span>` : ""}<br><span class="muted">${p.upstream.length} upstream · ${p.downstream.length} downstream</span>`, e); };
    n.onmousemove = moveTip;
    n.onmouseleave = () => { hideTip(); modeFocus(); };
    n.onclick = () => openProgram(id);
  });
  document.querySelectorAll("#gmode button").forEach(b => b.onclick = () => { S.graphMode = b.dataset.mode; document.querySelectorAll("#gmode button").forEach(x => x.classList.toggle("on", x === b)); modeFocus(); });
  modeFocus();
}

function risks() {
  const items = active().flatMap(p => p.reasons.map(r => ({ ...r, p })));
  const counts = {}; items.forEach(i => counts[i.rule] = (counts[i.rule] || 0) + 1);
  const shown = items.filter(i => !S.riskRule || i.rule === S.riskRule).sort((a, b) => SEV[a.level] - SEV[b.level] || a.p.tier - b.p.tier || a.p.id.localeCompare(b.p.id));
  const notes = S.data.programs.flatMap(p => p.notes.filter(n => n.kind === "schedule_risk").map(n => ({ ...n, p })));
  return `<h2 class="view-title">Risk flags</h2>
  <p class="lede">Every rule that fired, most severe first. These are leading indicators like stale updates, aging blockers, freeze collisions and dependencies that will land late. Most of them turn up before a team would call the program at risk.</p>
  <div class="chips"><button class="chip ${!S.riskRule ? "on" : ""}" data-rule="">All (${items.length})</button>
    ${Object.keys(RULE).filter(k => counts[k]).map(k => `<button class="chip ${S.riskRule === k ? "on" : ""}" data-rule="${k}">${RULE[k]} (${counts[k]})</button>`).join("")}</div>
  <div class="card">${shown.map(i => `<div class="risk"><div>${st(i.level)}<div class="tiny">${RULE[i.rule]}</div></div>
    <div>${pill(i.p.id)} <strong>${esc(i.p.name)}</strong><div class="muted small" style="margin-top:2px">${esc(i.detail)}</div></div>
    <div class="small muted">${esc(i.p.owner || "No owner")}<div class="tiny">${esc(i.p.team_name)} · Tier ${i.p.tier}</div></div></div>`).join("")}</div>
  <div class="card section" style="margin-top:18px"><h3>Schedule signals from chat and notes (shown here, not scored)</h3>
  <p class="tiny" style="margin-top:-4px">Claude flags these for a person to follow up. They don't change health by themselves. Only a direct contradiction of the reported status does that.</p>
  ${notes.map(n => `<div class="risk"><div><span class="badge model">Claude</span></div><div>${pill(n.p.id)} ${esc(n.summary)}<div class="tiny" style="margin-top:3px">“${esc(n.quote)}”</div></div><div class="tiny">${esc(n.locator)}</div></div>`).join("")}</div>`;
}

function preread() {
  const c = S.check;
  return `<h2 class="view-title">Weekly pre-read</h2>
  <p class="lede">The one-pager for Monday's portfolio review. Claude drafts it from the snapshot, a script checks it against the data, and a person edits it and sends it. It leads with decisions, not status.</p>
  <div class="two-col">
    <div class="card prose">${md(S.preread)}</div>
    <div class="grid">
      <div class="card"><h3>${c.passed ? "All checks pass" : "Checks failing"}</h3>
        ${c.checks.map(x => `<div class="check"><span class="${x.pass ? "ok" : "bad"}">${x.pass ? "✓" : "✗"}</span><div>${esc(x.check)}<div class="tiny">${esc(x.detail)}</div></div></div>`).join("")}
        <p class="tiny" style="margin:8px 0 0">${codeLink("pipeline/verify_preread.py")}</p></div>
      <div class="card small"><h3>How this page was made</h3>
        <p style="margin:0 0 8px">1. Claude drafted it from <code>portfolio.json</code> using ${codeLink("prompts/weekly_preread.md")}.</p>
        <p style="margin:0 0 8px">2. The checker caught stale headline counts in the first draft. It had been written before a parser fix changed the numbers.</p>
        <p style="margin:0 0 8px">3. A human read found two things a script can't: a miscounted "four teams", and a deadline the model invented inside a recommendation.</p>
        <p style="margin:0" class="muted">Details are in the verification log under How it works.</p></div>
      <div class="card"><button class="btn ghost" id="copymd" type="button">Copy as Markdown</button></div>
    </div>
  </div>`;
}

const PLATFORMS = [["EAI-01", "Integrations through the iPaaS"], ["WPT-01", "Employee accounts and provisioning (JML)"], ["EAI-08", "SSO for tier-1 apps"],
  ["ERP-01", "The new ERP ledger"], ["EAI-02", "Enterprise data warehouse"], ["EAI-04", "AI gateway (any LLM use)"], ["EAI-06", "Order event bus"], ["COM-03", "E-commerce checkout"]];
function intake() {
  const teams = S.data.teams.map(t => `<option value="${t.team}" ${t.team === "SCT" ? "selected" : ""}>${esc(t.team_name)}</option>`).join("");
  return `<h2 class="view-title">Intake triage</h2>
  <p class="lede">Every new request gets a real answer within a week. Before anyone says yes, the triage checks the request against live portfolio data: platform readiness, freezes, team load, and what would have to give.</p>
  <div class="two-col" style="grid-template-columns:minmax(0,380px) minmax(0,1fr)">
    <form class="card intake" id="iform">
      <label>Request<input name="title" value="Carrier claims automation" required></label>
      <label>Requested by<input name="by" value="Logistics (Ops)"></label>
      <label>IT team that would build it<select name="team">${teams}</select></label>
      <div class="grid g2" style="gap:12px">
        <label>Size<select name="size"><option value="2">S · about 2 weeks</option><option value="6" selected>M · about 6 weeks</option><option value="12">L · 12+ weeks</option></select></label>
        <label>Needed by<input type="date" name="need" value="2026-11-30" required></label>
      </div>
      <label>Business tier<select name="tier"><option value="1">1 · business-critical</option><option value="2" selected>2 · important</option><option value="3">3 · discretionary</option></select></label>
      <div><div class="small muted" style="margin-bottom:6px">Shared platforms it depends on</div>
        <div class="checks">${PLATFORMS.map(([id, l]) => `<label><input type="checkbox" name="plat" value="${id}" ${["EAI-01", "EAI-04"].includes(id) ? "checked" : ""}>${esc(l)}</label>`).join("")}</div></div>
      <div><button class="btn" type="submit">Assess request</button></div>
    </form>
    <div class="card" id="iout"></div>
  </div>`;
}
function assessIntake() {
  const f = new FormData($("#iform")), d = S.data, asOf = d.as_of;
  const team = f.get("team"), weeks = +f.get("size"), need = f.get("need"), tier = +f.get("tier"), plats = f.getAll("plat");
  const tname = d.teams.find(t => t.team === team).team_name;
  const friday = s => { const x = new Date(s + "T12:00:00"); x.setDate(x.getDate() + ((5 - x.getDay() + 7) % 7)); return x.toISOString().slice(0, 10); };
  const readiness = plats.map(id => { const p = P(id); const ready = p.health === "done" ? asOf : (p.forecast || p.target); return { p, ready }; });
  const gating = readiness.filter(r => r.ready && r.ready > asOf).sort((a, b) => b.ready.localeCompare(a.ready))[0];
  const earliest = friday([addDays(asOf, weeks * 7), gating ? addDays(gating.ready, 14) : asOf].sort().pop());
  const freeze = d.freezes.find(z => z.team === team && need >= z.start && need <= z.end);
  const act = d.programs.filter(p => p.team === team && p.health !== "done");
  const risky = act.filter(p => p.health !== "green"), t1 = act.filter(p => p.tier === 1);
  const defer = act.filter(p => p.tier === 3 && p.health !== "red").sort((a, b) => (b.target || "").localeCompare(a.target || "")).slice(0, 2);
  const redPlat = readiness.filter(r => r.p.health === "red");
  let verdict, cls;
  if (need < earliest) { verdict = `Not by ${fmtShort(need)}. Realistic date: ${fmt(earliest)}.`; cls = "red"; }
  else if (freeze) { verdict = `Yes, if the date moves out of the ${freeze.name}.`; cls = "amber"; }
  else if (weeks >= 12 || risky.length / act.length >= 0.4 || (tier === 3 && weeks >= 6)) { verdict = "Yes, if we defer something to make room."; cls = "amber"; }
  else { verdict = "Yes. It fits."; cls = "green"; }
  const due = (() => { let x = asOf, n = 0; while (n < 5) { x = addDays(x, 1); const w = new Date(x + "T12:00:00").getDay(); if (w && w < 6) n++; } return x; })();
  const reply = [
    `Re: ${f.get("title")} (from ${f.get("by")})`, "",
    `Answer: ${verdict}`, "",
    need < earliest ? `Why: ${gating ? `it depends on ${gating.p.name} (${gating.p.id}), which is ${LABEL[gating.p.health]} and forecast for ${fmt(gating.ready)}. With integration and testing, the earliest finish is ${fmt(earliest)}.` : `at ${weeks} weeks of work, the earliest finish is ${fmt(earliest)}.`}` : `Why: the shared platforms it needs are ready in time, and ${tname} can start.`,
    freeze ? `The ${fmtShort(need)} date falls inside the ${freeze.name} (${fmtShort(freeze.start)} to ${fmtShort(freeze.end)}).` : "",
    `${tname} is carrying ${act.length} active programs. ${risky.length} of them are Amber or Red, and ${t1.length} are Tier 1.`,
    defer.length && cls !== "green" ? `If this goes ahead, candidates to defer are ${defer.map(p => `${p.name} (${p.id}, Tier 3)`).join(" or ")}.` : "",
    "", "Next step: confirm the trade-off at Monday's portfolio review.",
  ].filter((l, i, a) => l !== "" || a[i - 1] !== "").join("\n");
  $("#iout").innerHTML = `<div class="tiny">Answer due by ${fmt(due)} (5 business days)</div>
    <div class="verdict">${st(cls)} ${esc(verdict)}</div>
    <table class="simple" style="margin:10px 0 14px"><thead><tr><th>Check</th><th>Finding</th></tr></thead><tbody>
      <tr><td>Platform readiness</td><td>${readiness.length ? readiness.map(r => `${pill(r.p.id)} ${esc(r.p.name)}: ${st(r.p.health)}, ready ${fmtShort(r.ready)}`).join("<br>") : '<span class="muted">No shared platforms selected</span>'}</td></tr>
      <tr><td>Earliest realistic finish</td><td>${fmt(earliest)} <span class="tiny">(${weeks} weeks of work${gating ? `, after ${gating.p.id} plus 2 weeks to integrate` : ""})</span></td></tr>
      <tr><td>Change freeze</td><td>${freeze ? `${st("amber")} The requested date is inside the ${esc(freeze.name)}` : '<span class="muted">No conflict</span>'}</td></tr>
      <tr><td>${esc(tname)} load</td><td>${act.length} active · ${risky.length} Amber or Red · ${t1.length} Tier 1</td></tr>
      <tr><td>What would give</td><td>${defer.length ? defer.map(p => `${pill(p.id)} ${esc(p.name)}`).join("<br>") : '<span class="muted">No Tier-3 candidates</span>'}</td></tr>
      ${redPlat.length ? `<tr><td>Upstream risk</td><td>${redPlat.map(r => `${r.p.id} is Red: ${esc(r.p.reasons[0].detail)}`).join("<br>")}</td></tr>` : ""}
    </tbody></table>
    <h3>Draft reply</h3><div class="reply" id="ireply">${esc(reply)}</div>
    <div style="margin-top:10px;display:flex;gap:8px;align-items:center;flex-wrap:wrap"><button class="btn ghost" type="button" id="icopy">Copy reply</button>
    <span class="tiny">This demo uses rules, so it costs nothing to run. In production, Claude writes the reply from these same facts (${codeLink("prompts/intake_triage.md")}) and a person sends it.</span></div>`;
  $("#icopy").onclick = () => navigator.clipboard?.writeText(reply).catch(() => {});
}

function method() {
  const d = S.data, e = S.evalr, runs = Object.entries(d.extraction.runs);
  const pct = x => x == null ? "n/a" : Math.round(x * 100) + "%";
  return `<h2 class="view-title">How it works</h2>
  <p class="lede">Code does what is deterministic, Claude reads what only a reader can, and a person makes every call that matters. Every AI output passes a mechanical check before anyone relies on it.</p>
  <div class="flow">
    <div class="step"><b>1 · Six sources, as-is</b>Jira CSV, a spreadsheet, Confluence pages, a status doc, Slack, steering notes. Teams keep working where they already work.<div class="who"><span class="badge">no new reporting</span></div></div>
    <div class="step"><b>2a · Parse the structured ones</b>Four sources have fields, so plain code reads them. It's cheaper, exact and repeatable.<div class="who"><span class="badge">code</span></div></div>
    <div class="step"><b>2b · Extract the unstructured ones</b>Chat and meeting notes use nicknames and hide dependencies. Claude turns them into records and quotes its source for every field.<div class="who"><span class="badge model">Claude</span></div></div>
    <div class="step"><b>3 · Grounding check</b>Each quote has to exist verbatim in the source, and each date has to appear in its quote. If not, the value is dropped.<div class="who"><span class="badge">code</span></div></div>
    <div class="step"><b>4 · One rubric</b>The same evidence rules score every team, dependency lateness propagates, and every Amber or Red cites its fact.<div class="who"><span class="badge">code</span></div></div>
    <div class="step"><b>5 · Pre-read and intake</b>Claude drafts, a checker verifies the facts, and a person edits, decides and sends.<div class="who"><span class="badge model">Claude</span> <span class="badge">code</span> <span class="badge">person</span></div></div>
  </div>

  <div class="grid g2 section" style="margin-top:18px">
    <div class="card"><h3>Who does what</h3><table class="simple"><thead><tr><th>Work</th><th>Done by</th><th>Why</th></tr></thead><tbody>
      <tr><td>Reading CSV columns and page tables</td><td>Code</td><td>Deterministic, so a model adds cost and risk and nothing else</td></tr>
      <tr><td>Reading chat and notes, resolving "JML" to WPT-01, spotting coupling</td><td>Claude</td><td>Needs language and context</td></tr>
      <tr><td>Checking the model's work</td><td>Code</td><td>Quotes and dates are verifiable, so they get verified</td></tr>
      <tr><td>Scoring health</td><td>Code (rubric)</td><td>Has to be identical across teams and explainable</td></tr>
      <tr><td>Drafting the pre-read and intake replies</td><td>Claude</td><td>Compression and first drafts</td></tr>
      <tr><td>The final health call, escalations, trade-offs, anything political</td><td>A person</td><td>Accountability can't be delegated</td></tr>
    </tbody></table></div>
    <div class="card"><h3>The shared health definition</h3><table class="simple"><thead><tr><th>Level</th><th>Rule</th></tr></thead><tbody>
      ${d.rubric.rules.map(r => `<tr><td>${st(r.level)}</td><td>${esc(r.definition)}</td></tr>`).join("")}
      <tr><td>${st("green")}</td><td>No rule fired.</td></tr></tbody></table>
      <p class="tiny" style="margin:8px 0 0">The thresholds live in one file (${codeLink("pipeline/rubric.py")}), so changing them is a reviewed decision.</p></div>
  </div>

  <div class="card section" style="margin-top:18px"><h3>Scored against ground truth</h3>
    <p class="small muted" style="margin-top:-4px">The generator knows the real facts behind every messy artifact, and ${codeLink("pipeline/eval.py")} scores the pipeline field by field. Caveat: templated synthetic text is easier than real chat, so treat these numbers as proof that the checks work, not as a real-world accuracy claim. The eval's real value was catching a parser bug (see the log below).</p>
    <div class="grid g2">
      <table class="simple"><thead><tr><th>Source</th><th>Read by</th><th class="num">Owner</th><th class="num">Dates</th><th class="num">Blocker</th><th class="num">All fields</th></tr></thead><tbody>
        ${e.fields.map(r => `<tr><td>${SOURCE[r.source]}</td><td>${r.method === "model" ? '<span class="badge model">Claude</span>' : '<span class="badge">parser</span>'}</td><td class="num">${pct(r.owner)}</td><td class="num">${pct((r.target + r.baseline + r.last_update) / 3)}</td><td class="num">${pct(r.blocker_text)}</td><td class="num">${pct(r.overall)}</td></tr>`).join("")}
      </tbody></table>
      <div>
        <div class="check"><span class="ok">✓</span><div>Health matches ground truth for <strong>${pct(e.health.agreement)}</strong> of programs</div></div>
        <div class="check"><span class="ok">✓</span><div>Dependencies: precision ${pct(e.dependencies.precision)}, recall ${pct(e.dependencies.recall)}. Chat-and-notes-only links: recall ${pct(e.dependencies.chat_and_notes_only_recall)}</div></div>
        <div class="check"><span class="${e.grounding.failures.length ? "bad" : "ok"}">${e.grounding.failures.length ? "✗" : "✓"}</span><div>${e.grounding.model_fields_checked} model-extracted fields grounded, ${e.grounding.failures.length} rejected. Invented quotes and mismatched dates are rejected in ${codeLink("tests/test_pipeline.py")}</div></div>
        <h3 style="margin-top:12px">Planted scenarios detected</h3>
        ${e.planted.map(p => `<div class="check"><span class="${p.detected ? "ok" : "bad"}">${p.detected ? "✓" : "✗"}</span><div class="small">${esc(p.scenario)}</div></div>`).join("")}
      </div>
    </div></div>

  <div class="grid g2 section" style="margin-top:18px">
    <div class="card prose small">${md(S.log)}</div>
    <div class="card"><h3>Model runs behind this snapshot</h3>
      ${runs.map(([k, m]) => `<div class="receipt"><div class="meta"><strong>${esc(k)}</strong><span class="badge model">${esc(m.model)}</span>${m.stale && m.stale.length ? '<span class="badge">stale</span>' : ""}</div>
        <div class="small" style="margin-top:4px">${esc(m.recorded_via)}</div><div class="tiny">prompt ${esc(m.prompt_sha)} · source ${esc(m.source_sha)} · ${esc(m.recorded_at)}</div></div>`).join("")}
      <p class="small muted">The demo replays recorded model output, so viewing it is free and needs no API key. Every recording is pinned to hashes of its prompt and source files, and the build warns if either one changes. To re-run live: <code>python -m pipeline.build --backend claude</code>.</p></div>
  </div>`;
}

/* ---------- router */
const VIEWS = { overview, register, dependencies, risks, preread, intake, method };
function render() {
  const v = (location.hash.slice(1) || "overview");
  const name = VIEWS[v] ? v : "overview";
  document.querySelectorAll("#tabs a").forEach(a => a.classList.toggle("active", a.getAttribute("href") === "#" + name));
  $("#view").innerHTML = VIEWS[name]();
  if (name === "register") bindRegister();
  if (name === "dependencies") drawGraph();
  if (name === "risks") document.querySelectorAll(".chip").forEach(c => c.onclick = () => { S.riskRule = c.dataset.rule; render(); });
  if (name === "preread") $("#copymd").onclick = () => navigator.clipboard?.writeText(S.preread).catch(() => {});
  if (name === "intake") { $("#iform").onsubmit = ev => { ev.preventDefault(); assessIntake(); }; assessIntake(); }
  document.querySelectorAll("[data-tip]").forEach(el => { el.onmouseenter = e => showTip(esc(el.dataset.tip), e); el.onmousemove = moveTip; el.onmouseleave = hideTip; });
}
addEventListener("hashchange", () => { render(); scrollTo(0, 0); });
$("#theme").onclick = () => {
  const cur = document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const next = cur === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem("pp-theme", next); } catch (e) {}
  render();
};

Promise.all([
  fetch("data/portfolio.json").then(r => r.json()), fetch("data/eval.json").then(r => r.json()),
  fetch("data/preread.md").then(r => r.text()), fetch("data/preread_check.json").then(r => r.json()),
  fetch("data/verification_log.md").then(r => r.text()),
]).then(([d, e, pr, c, log]) => { Object.assign(S, { data: d, evalr: e, preread: pr, check: c, log }); render(); })
  .catch(err => { $("#view").innerHTML = `<div class="card">Couldn't load the snapshot (${esc(err.message)}). If you opened index.html straight from disk, serve the folder instead: <code>python -m http.server -d docs</code>.</div>`; });
})();
