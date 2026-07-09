import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

const [resultPath, summaryPath, outPath = "vqa_report.html", ...manualPaths] = process.argv.slice(2);
if (!resultPath || !summaryPath) {
  console.error("usage: node build_vqa_report.mjs <vqa_results.jsonl> <summary.json> [out.html]");
  process.exit(1);
}

const cases = JSON.parse(readFileSync("data/bench_cases.json", "utf8"));
const caseById = new Map(cases.map((c) => [c.id, c]));
const rows = resultPath === "-"
  ? []
  : readFileSync(resultPath, "utf8").trim().split(/\n+/).filter(Boolean).map((line) => JSON.parse(line));
const summary = summaryPath === "-"
  ? { model: "qwen3-vl-plus", overall: pack([]), by_category: {}, by_level: {} }
  : JSON.parse(readFileSync(summaryPath, "utf8"));
const manualRows = manualPaths.flatMap((path) =>
  readFileSync(path, "utf8").trim().split(/\n+/).filter(Boolean).map((line) => JSON.parse(line))
);

function esc(x) {
  return String(x ?? "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch]);
}

function pct(x) {
  return `${(Number(x || 0) * 100).toFixed(1)}%`;
}

function inverseQuestion(check) {
  const q = check.vqa_question || check.label_en || "";
  const subject = (check.subject || "").replaceAll("_", " ");
  const target = (check.target || "").replaceAll("_", " ");
  switch (check.relation) {
    case "left_of": return q.replace(" to the left of ", " to the right of ");
    case "right_of": return q.replace(" to the right of ", " to the left of ");
    case "in_front": return q.replace(" in front of ", " behind ");
    case "behind": return q.replace(" behind ", " in front of ");
    case "on_top": return subject && target ? `Is the ${subject} under the ${target}?` : "";
    case "partially_occludes": return subject && target ? `Does the ${target} partially block the ${subject}?` : "";
    case "face": return subject && target ? `Is the ${subject} facing away from the ${target}?` : "";
    case "rotate_yaw":
      if (/\bleft\b/i.test(q)) return q.replace(/left/ig, "right");
      if (/\bright\b/i.test(q)) return q.replace(/right/ig, "left");
      return "";
    default:
      return "";
  }
}

function questionMap(c) {
  const map = new Map();
  for (const check of c.checklist || []) {
    const q = check.vqa_question || check.label_en || "";
    if (check.type === "presence") {
      map.set(check.check_id, q);
    } else {
      map.set(`${check.check_id}|pos`, q);
      const neg = inverseQuestion(check);
      if (neg) map.set(`${check.check_id}|neg`, neg);
    }
  }
  return map;
}

function metricCards(data) {
  return `
    <div class="cards">
      <div><b>${esc(data.cases)}</b><span>cases</span></div>
      <div><b>${pct(data.presence_score)}</b><span>presence</span></div>
      <div><b>${pct(data.relation_score)}</b><span>relation</span></div>
      <div><b>${pct(data.combined_score)}</b><span>combined</span></div>
    </div>`;
}

function groupTable(title, data) {
  const body = Object.entries(data || {}).map(([name, x]) => `
    <tr><td>${esc(name)}</td><td>${x.cases}</td><td>${pct(x.presence_score)}</td><td>${pct(x.relation_score)}</td><td>${pct(x.combined_score)}</td></tr>
  `).join("");
  return `<section><h2>${esc(title)}</h2><table><thead><tr><th>group</th><th>cases</th><th>presence</th><th>relation</th><th>combined</th></tr></thead><tbody>${body}</tbody></table></section>`;
}

function errorTable(errors) {
  if (!errors?.length) return "";
  const body = errors.map((x) => `
    <tr><td>${esc(x.id)}</td><td>${esc(x.category)}</td><td>${esc(x.level)}</td><td>${esc(x.error)}</td></tr>
  `).join("");
  return `<section><h2>Run Errors</h2><table><thead><tr><th>case</th><th>category</th><th>level</th><th>error</th></tr></thead><tbody>${body}</tbody></table></section>`;
}

function pack(rows) {
  const avg = (xs) => xs.length ? xs.reduce((a, b) => a + Number(b || 0), 0) / xs.length : 0;
  return {
    cases: rows.length,
    presence_score: avg(rows.map((r) => r.presence_score)),
    relation_score: avg(rows.map((r) => r.relation_score)),
    combined_score: avg(rows.map((r) => r.combined_score)),
  };
}

function summarize(rows) {
  const byCategory = {};
  const byLevel = {};
  for (const row of rows) {
    const c = caseById.get(row.id) || {};
    const category = row.category || c.category || "unknown";
    const level = row.level || c.level || "unknown";
    (byCategory[category] ||= []).push(row);
    (byLevel[level] ||= []).push(row);
  }
  return {
    overall: pack(rows),
    by_category: Object.fromEntries(Object.entries(byCategory).sort().map(([k, v]) => [k, pack(v)])),
    by_level: Object.fromEntries(Object.entries(byLevel).sort().map(([k, v]) => [k, pack(v)])),
  };
}

function caseDetails(row) {
  const c = caseById.get(row.id) || {};
  const qmap = questionMap(c);
  const answers = Object.entries(row.answers || {}).map(([id, ans]) => `
    <tr>
      <td><code>${esc(id)}</code></td>
      <td>${esc(qmap.get(id) || "")}</td>
      <td><span class="pill ${esc(ans.answer)}">${esc(ans.answer)}</span></td>
      <td>${esc(ans.reason || "")}</td>
    </tr>
  `).join("");
  return `
    <details>
      <summary>
        <b>${esc(row.id)}</b>
        <span>${esc(row.category || c.category)} / ${esc(row.level || c.level)}</span>
        <span>presence ${pct(row.presence_score)}</span>
        <span>relation ${pct(row.relation_score)}</span>
        <span>combined ${pct(row.combined_score)}</span>
      </summary>
      <p class="prompt">${esc(c.prompt_zh || "")}<br>${esc(c.prompt || "")}</p>
      <img src="${esc(c.sample?.image || "")}" alt="${esc(row.id)} sample">
      <table><thead><tr><th>id</th><th>question</th><th>answer</th><th>reason</th></tr></thead><tbody>${answers}</tbody></table>
    </details>`;
}

const now = new Date().toLocaleString("zh-CN", { hour12: false });
const manualSummary = manualRows.length ? summarize(manualRows) : null;
const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Qwen3-VL VQA Report</title>
  <style>
    :root { --bg:#f7f3ea; --panel:#fffdf8; --text:#2f2a24; --muted:#756f66; --line:#e7ded2; --accent:#b85c38; --ok:#46784e; --fail:#a6463c; --unclear:#8a6b22; }
    * { box-sizing: border-box; }
    body { margin:0; background:var(--bg); color:var(--text); font:14px/1.45 ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    header, main { max-width:1180px; margin:auto; padding:22px; }
    h1, h2 { font-family:ui-serif,Georgia,Cambria,"Times New Roman",serif; margin:0 0 12px; }
    a { color:var(--accent); text-decoration:none; }
    section, details { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px; margin:14px 0; }
    .muted, summary span { color:var(--muted); }
    .cards { display:grid; grid-template-columns:repeat(4,minmax(120px,1fr)); gap:10px; }
    .cards div { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:12px; }
    .cards b { display:block; font-size:24px; }
    .cards span { color:var(--muted); }
    table { width:100%; border-collapse:collapse; }
    th, td { border-bottom:1px solid var(--line); padding:8px; text-align:left; vertical-align:top; }
    th { color:var(--muted); font-size:12px; }
    summary { cursor:pointer; display:flex; gap:14px; flex-wrap:wrap; align-items:center; }
    img { width:220px; max-width:100%; border-radius:10px; border:1px solid var(--line); margin:12px 0; }
    code { white-space:nowrap; }
    .prompt { font-size:16px; }
    .pill { border:1px solid var(--line); border-radius:999px; padding:2px 8px; font-weight:700; }
    .yes { color:var(--ok); }
    .no { color:var(--fail); }
    .unclear { color:var(--unclear); }
    @media (max-width: 720px) { .cards { grid-template-columns:1fr 1fr; } summary { display:block; } }
  </style>
</head>
<body>
  <header>
    <h1>Qwen3-VL VQA Report</h1>
    <p class="muted">model: ${esc(summary.model)} · generated: ${esc(now)} · <a href="index.html">back to viewer</a></p>
    ${rows.length ? `<h2>Qwen3-VL</h2>${metricCards(summary.overall)}` : `<h2>Qwen3-VL</h2><p class="muted">pending remote result import</p>`}
  </header>
  <main>
    ${rows.length ? `${groupTable("By Category", summary.by_category)}${groupTable("By Level", summary.by_level)}` : ""}
    ${errorTable(summary.errors)}
    ${manualSummary ? `
      <section>
        <h2>Manual-Agent</h2>
        ${metricCards(manualSummary.overall)}
      </section>
      ${groupTable("Manual By Category", manualSummary.by_category)}
      ${groupTable("Manual By Level", manualSummary.by_level)}
    ` : ""}
    ${rows.length ? `<section>
      <h2>Qwen3-VL Cases</h2>
      ${rows.map(caseDetails).join("")}
    </section>` : ""}
    ${manualRows.length ? `<section><h2>Manual-Agent Cases</h2>${manualRows.map(caseDetails).join("")}</section>` : ""}
  </main>
</body>
</html>`;

mkdirSync(dirname(outPath), { recursive: true });
writeFileSync(outPath, html, "utf8");
console.log(`wrote ${join(process.cwd(), outPath)}`);
