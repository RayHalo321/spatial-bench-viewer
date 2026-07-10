import { readFileSync, writeFileSync } from "node:fs";

const CASE_PATH = "data/bench_cases.json";
const OUT_PATH = process.argv[2] || "vqa_report.html";
const EXPECTED_CASES = 76;

const IMAGE_MODELS = [
  { id: "zimage", label: "Z-Image Turbo", image: (id, c) => c.sample?.image || `generated/zimage/${id}.png` },
  { id: "sdxl", label: "SDXL", image: (id) => `generated/sdxl_1024/${id}.jpg` },
  { id: "flux", label: "FLUX", image: (id) => `generated/flux_1024/${id}.jpg` },
  { id: "qwen_edit", label: "Qwen-Edit Direct", image: (id) => `generated/qwen_edit_1024/${id}.jpg` },
];

const JUDGES = [
  { id: "qwen8b", label: "Qwen3-VL-8B", root: "vqa/qwen3vl8b_20260710" },
  { id: "api", label: "qwen3-vl-plus API", root: "vqa/qwen3vlplus_new_standard_20260710" },
  { id: "subagent", label: "GPT Subagent", root: "vqa/subagent_new_standard_20260710" },
];

const cases = JSON.parse(readFileSync(CASE_PATH, "utf8"));
const caseById = new Map(cases.map((c) => [c.id, c]));

function readJsonl(path) {
  return readFileSync(path, "utf8").trim().split(/\n+/).filter(Boolean).map((line) => JSON.parse(line));
}

function average(values) {
  return values.length ? values.reduce((sum, value) => sum + Number(value || 0), 0) / values.length : 0;
}

function pack(rows) {
  const relations = rows.flatMap((row) => row.relation_details || []);
  const exactCases = rows.filter((row) => Number(row.relation_score) === 1).length;
  return {
    cases: rows.length,
    relations: relations.length,
    presenceMacro: average(rows.map((row) => row.presence_score)),
    relationCaseMacro: average(rows.map((row) => row.relation_score)),
    relationMicro: average(relations.map((detail) => detail.score)),
    combinedMacro: average(rows.map((row) => 0.2 * Number(row.presence_score || 0) + 0.8 * Number(row.relation_score || 0))),
    exactCasePass: rows.length ? exactCases / rows.length : 0,
    errors: rows.filter((row) => row.error).length,
  };
}

function summarize(rows) {
  const group = (key) => {
    const grouped = new Map();
    for (const row of rows) {
      const c = caseById.get(row.id) || {};
      const name = row[key] || c[key] || "unknown";
      if (!grouped.has(name)) grouped.set(name, []);
      grouped.get(name).push(row);
    }
    return Object.fromEntries([...grouped.entries()].sort().map(([name, values]) => [name, pack(values)]));
  };
  return { overall: pack(rows), byCategory: group("category"), byLevel: group("level") };
}

function publicRow(row) {
  return {
    id: row.id,
    category: row.category,
    level: row.level,
    presence_score: Number(row.presence_score || 0),
    relation_score: Number(row.relation_score || 0),
    combined_score: 0.2 * Number(row.presence_score || 0) + 0.8 * Number(row.relation_score || 0),
    relation_details: row.relation_details || [],
    answers: row.answers || {},
    error: row.error || "",
  };
}

function inverseQuestion(check) {
  const q = check.vqa_question || check.label_en || "";
  const subject = String(check.subject || "").replaceAll("_", " ");
  const target = String(check.target || "").replaceAll("_", " ");
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
    case "absolute_location":
      if (/left side/i.test(q)) return q.replace(/left side/ig, "right side");
      if (/right side/i.test(q)) return q.replace(/right side/ig, "left side");
      return "";
    default: return "";
  }
}

function questionsForCase(c) {
  const questions = [];
  for (const check of c.checklist || []) {
    const question = check.vqa_question || check.label_en || "";
    if (check.type === "presence") {
      questions.push({ id: check.check_id, kind: "presence", question });
      continue;
    }
    questions.push({ id: `${check.check_id}|pos`, kind: "positive", question });
    const inverse = inverseQuestion(check);
    if (inverse) questions.push({ id: `${check.check_id}|neg`, kind: "inverse", question: inverse });
  }
  return questions;
}

const sources = {};
const missing = [];
for (const judge of JUDGES) {
  for (const imageModel of IMAGE_MODELS) {
    const key = `${judge.id}:${imageModel.id}`;
    const path = `${judge.root}/${imageModel.id}/vqa_results.jsonl`;
    try {
      const rows = readJsonl(path);
      if (rows.length !== EXPECTED_CASES) missing.push(`${path}: expected ${EXPECTED_CASES}, got ${rows.length}`);
      sources[key] = { path, rows: rows.map(publicRow), summary: summarize(rows) };
    } catch (error) {
      missing.push(`${path}: ${error.message}`);
    }
  }
}
if (missing.length) {
  console.error("VQA report inputs are incomplete:\n" + missing.map((x) => `- ${x}`).join("\n"));
  process.exit(1);
}

const caseData = cases.map((c) => ({
  id: c.id,
  category: c.category,
  level: c.level,
  prompt: c.prompt,
  prompt_zh: c.prompt_zh,
  images: Object.fromEntries(IMAGE_MODELS.map((m) => [m.id, m.image(c.id, c)])),
  questions: questionsForCase(c),
}));

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch]);
}

function pct(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

const summaryRows = IMAGE_MODELS.flatMap((imageModel) => JUDGES.map((judge) => {
  const source = sources[`${judge.id}:${imageModel.id}`];
  const m = source.summary.overall;
  return `<tr>
    <td><b>${esc(imageModel.label)}</b></td><td>${esc(judge.label)}</td>
    <td>${pct(m.presenceMacro)}</td><td>${pct(m.relationCaseMacro)}</td><td>${pct(m.relationMicro)}</td>
    <td>${pct(m.exactCasePass)}</td><td>${pct(m.combinedMacro)}</td><td>${m.errors}</td>
  </tr>`;
})).join("");

const recordLinks = IMAGE_MODELS.flatMap((imageModel) => JUDGES.map((judge) => {
  const source = sources[`${judge.id}:${imageModel.id}`];
  return `<a href="${esc(source.path)}">${esc(imageModel.label)} · ${esc(judge.label)}</a>`;
})).join("");

const serialized = JSON.stringify({
  cases: caseData,
  models: IMAGE_MODELS.map(({ id, label }) => ({ id, label })),
  judges: JUDGES.map(({ id, label }) => ({ id, label })),
  sources,
}).replaceAll("<", "\\u003c");

const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Spatial Bench VQA Report</title>
  <style>
    :root { --bg:#f7f3ea; --panel:#fffdf8; --text:#2f2a24; --muted:#746d63; --line:#e5dbce; --accent:#b95735; --accent-soft:#f9e9dd; --yes:#3e7749; --no:#a8473c; --unclear:#8a681d; }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--bg); color:var(--text); font:14px/1.5 ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    a { color:var(--accent); text-decoration:none; }
    h1,h2,h3 { margin:0; font-family:ui-serif,Georgia,Cambria,"Times New Roman",serif; letter-spacing:0; }
    header { position:sticky; top:0; z-index:5; display:flex; justify-content:space-between; align-items:center; gap:16px; padding:13px max(18px,calc((100vw - 1460px)/2)); background:rgba(255,253,248,.96); border-bottom:1px solid var(--line); }
    header h1 { font-size:21px; }
    header nav { display:flex; gap:8px; flex-wrap:wrap; }
    header a,.button { display:inline-flex; align-items:center; min-height:32px; padding:5px 10px; border:1px solid var(--line); border-radius:6px; background:var(--panel); color:var(--text); }
    main { max-width:1460px; margin:auto; padding:24px 18px 56px; }
    .hero { display:grid; grid-template-columns:minmax(0,1.5fr) minmax(280px,.7fr); gap:22px; align-items:start; margin-bottom:20px; }
    .hero h2 { font-size:34px; }
    .hero p { color:var(--muted); max-width:820px; }
    .protocol { border-left:4px solid var(--accent); background:var(--panel); padding:13px 16px; }
    .protocol b { display:block; margin-bottom:5px; }
    section { margin:18px 0; }
    .section-head { display:flex; justify-content:space-between; gap:12px; align-items:end; margin-bottom:10px; }
    .section-head p { margin:0; color:var(--muted); }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:15px; }
    .table-wrap { overflow:auto; }
    table { width:100%; border-collapse:collapse; }
    th,td { padding:9px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
    th { color:var(--muted); font-size:12px; white-space:nowrap; }
    tbody tr:last-child td { border-bottom:0; }
    .controls { display:flex; gap:10px; flex-wrap:wrap; align-items:end; margin-bottom:12px; }
    label { display:grid; gap:4px; color:var(--muted); font-size:12px; }
    select { min-height:36px; min-width:220px; padding:6px 30px 6px 9px; border:1px solid var(--line); border-radius:6px; background:var(--panel); color:var(--text); }
    .records { display:grid; grid-template-columns:repeat(3,minmax(200px,1fr)); gap:8px; }
    .records a { padding:9px 10px; border:1px solid var(--line); border-radius:6px; background:var(--panel); }
    .case-layout { display:grid; grid-template-columns:minmax(280px,420px) minmax(0,1fr); gap:16px; align-items:start; }
    .case-image { position:sticky; top:72px; }
    .case-image img { display:block; width:100%; aspect-ratio:1; object-fit:contain; background:#eee9df; border:1px solid var(--line); border-radius:8px; }
    .prompt { margin:12px 0 0; padding:12px; border-left:3px solid var(--accent); background:#fff7ef; font-size:15px; }
    .prompt span { display:block; color:var(--muted); margin-top:5px; }
    .judge-grid { display:grid; gap:12px; }
    .judge-card { background:var(--panel); border:1px solid var(--line); border-radius:8px; overflow:hidden; }
    .judge-head { display:flex; justify-content:space-between; gap:12px; align-items:center; padding:12px 14px; background:#fbf5ec; border-bottom:1px solid var(--line); }
    .metrics { display:flex; gap:12px; flex-wrap:wrap; color:var(--muted); font-size:12px; }
    .judge-card table { font-size:13px; }
    code { font:12px/1.35 ui-monospace,SFMono-Regular,Menlo,monospace; overflow-wrap:anywhere; }
    .pill { display:inline-flex; padding:2px 7px; border:1px solid var(--line); border-radius:999px; font-weight:700; }
    .yes { color:var(--yes); }.no { color:var(--no); }.unclear { color:var(--unclear); }
    .score-1 { color:var(--yes); font-weight:700; }.score-0 { color:var(--no); font-weight:700; }.score-05 { color:var(--unclear); font-weight:700; }
    .note { color:var(--muted); font-size:12px; }
    @media (max-width:900px) { .hero,.case-layout { grid-template-columns:1fr; } .case-image { position:static; } .records { grid-template-columns:1fr 1fr; } }
    @media (max-width:560px) { header { align-items:flex-start; } header h1 { font-size:17px; } main { padding:16px 10px 40px; } .hero h2 { font-size:27px; } .records { grid-template-columns:1fr; } select { min-width:0; width:100%; } label { width:100%; } th,td { padding:8px 7px; } }
  </style>
</head>
<body>
  <header>
    <h1>Spatial Bench VQA Report</h1>
    <nav><a href="index.html">返回样例浏览器</a><a href="#records">原始记录</a></nav>
  </header>
  <main>
    <div class="hero">
      <div>
        <h2>新版统一评分报告</h2>
        <p>同一批 76 个 prompt、四组生成图，分别由本地 Qwen3-VL-8B、qwen3-vl-plus API 和独立 GPT subagent 评判。三方共享完全相同的问题和计分协议，页面不再混用旧版的 50/50 combined 指标。</p>
      </div>
      <div class="protocol">
        <b>当前评分协议</b>
        先检查物体存在性；缺失物体涉及的关系直接记 0。关系正问 yes、反问 no 记 1；正问 no 直接记 0；其余矛盾或不确定组合记 0.5。between 只直接询问，不拆成两个左右关系。case 内按关系数归一化，combined = 20% presence + 80% relation。
      </div>
    </div>

    <section>
      <div class="section-head"><div><h2>总览</h2><p>relation case macro 对每个 case 等权；relation micro 对每条关系等权；exact 要求该 case 的全部 presence-gated relation 满分。</p></div></div>
      <div class="panel table-wrap">
        <table><thead><tr><th>生成模型</th><th>Judge</th><th>Presence macro</th><th>Relation case macro</th><th>Relation micro</th><th>Exact case pass</th><th>Combined macro</th><th>Errors</th></tr></thead><tbody>${summaryRows}</tbody></table>
      </div>
    </section>

    <section>
      <div class="section-head"><div><h2>分类与难度</h2><p>选择任一生成模型和 judge，查看相同协议下的分组结果。</p></div></div>
      <div class="panel">
        <div class="controls">
          <label>生成模型<select id="breakdownModel"></select></label>
          <label>Judge<select id="breakdownJudge"></select></label>
          <label>分组<select id="breakdownGroup"><option value="byCategory">Category</option><option value="byLevel">Difficulty</option></select></label>
        </div>
        <div class="table-wrap"><table><thead><tr><th>Group</th><th>Cases</th><th>Relations</th><th>Presence macro</th><th>Relation case macro</th><th>Relation micro</th><th>Exact case pass</th><th>Combined</th></tr></thead><tbody id="breakdownRows"></tbody></table></div>
      </div>
    </section>

    <section id="records">
      <div class="section-head"><div><h2>原始 Judge 记录</h2><p>每个链接都是 76 条完整 JSONL，含逐问题回答、理由和逐关系得分。</p></div></div>
      <div class="records">${recordLinks}</div>
    </section>

    <section>
      <div class="section-head"><div><h2>逐 Case 对照</h2><p>一张图配同一批问题，三位 judge 的回答并排保留，方便复查。</p></div></div>
      <div class="controls panel">
        <label>生成模型<select id="caseModel"></select></label>
        <label>Case<select id="caseSelect"></select></label>
      </div>
      <div class="case-layout">
        <div class="case-image panel"><img id="caseImage" alt="selected case"><div class="prompt" id="casePrompt"></div></div>
        <div class="judge-grid" id="judgeGrid"></div>
      </div>
    </section>
  </main>
  <script>
    const REPORT = ${serialized};
    const byId = (id) => document.getElementById(id);
    const h = (value) => String(value ?? "").replace(/[&<>"']/g, (ch) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
    const pct = (value) => (Number(value || 0) * 100).toFixed(1) + "%";
    const source = (judge, model) => REPORT.sources[judge + ":" + model];
    const optionHtml = (items) => items.map((item) => '<option value="' + h(item.id) + '">' + h(item.label) + '</option>').join("");
    byId("breakdownModel").innerHTML = optionHtml(REPORT.models);
    byId("caseModel").innerHTML = optionHtml(REPORT.models);
    byId("breakdownJudge").innerHTML = optionHtml(REPORT.judges);
    byId("caseSelect").innerHTML = REPORT.cases.map((c) => '<option value="' + h(c.id) + '">' + h(c.id + " · " + c.category + " · " + c.level) + '</option>').join("");

    function renderBreakdown() {
      const data = source(byId("breakdownJudge").value, byId("breakdownModel").value).summary[byId("breakdownGroup").value];
      byId("breakdownRows").innerHTML = Object.entries(data).map(([name, m]) => '<tr><td><b>' + h(name) + '</b></td><td>' + m.cases + '</td><td>' + m.relations + '</td><td>' + pct(m.presenceMacro) + '</td><td>' + pct(m.relationCaseMacro) + '</td><td>' + pct(m.relationMicro) + '</td><td>' + pct(m.exactCasePass) + '</td><td>' + pct(m.combinedMacro) + '</td></tr>').join("");
    }

    function scoreClass(value) {
      return Number(value) === 1 ? "score-1" : Number(value) === 0 ? "score-0" : "score-05";
    }

    function judgeCard(judge, model, c) {
      const data = source(judge.id, model);
      const row = data.rows.find((item) => item.id === c.id);
      const answers = c.questions.map((question) => {
        const answer = row.answers[question.id] || { answer:"unclear", reason:"missing answer" };
        return '<tr><td><span class="note">' + h(question.kind) + '</span><br><code>' + h(question.id) + '</code></td><td>' + h(question.question) + '</td><td><span class="pill ' + h(answer.answer) + '">' + h(answer.answer) + '</span></td><td>' + h(answer.reason || "") + '</td></tr>';
      }).join("");
      const relationRows = (row.relation_details || []).map((detail) => '<tr><td><code>' + h(detail.check_id) + '</code></td><td class="' + scoreClass(detail.score) + '">' + Number(detail.score).toFixed(1) + '</td><td>' + h(detail.reason) + '</td></tr>').join("");
      return '<article class="judge-card"><div class="judge-head"><h3>' + h(judge.label) + '</h3><div class="metrics"><span>presence ' + pct(row.presence_score) + '</span><span>relation ' + pct(row.relation_score) + '</span><span>combined ' + pct(row.combined_score) + '</span></div></div>' +
        (row.error ? '<p class="panel score-0">' + h(row.error) + '</p>' : '') +
        '<div class="table-wrap"><table><thead><tr><th>问题类型 / ID</th><th>VQA question</th><th>回答</th><th>理由</th></tr></thead><tbody>' + answers + '</tbody></table></div>' +
        '<div class="table-wrap"><table><thead><tr><th>Relation check</th><th>得分</th><th>计分原因</th></tr></thead><tbody>' + relationRows + '</tbody></table></div></article>';
    }

    function renderCase() {
      const model = byId("caseModel").value;
      const c = REPORT.cases.find((item) => item.id === byId("caseSelect").value);
      byId("caseImage").src = c.images[model];
      byId("caseImage").alt = c.id + " " + REPORT.models.find((item) => item.id === model).label;
      byId("casePrompt").innerHTML = '<b>' + h(c.id + " · " + c.category + " · " + c.level) + '</b><br>' + h(c.prompt_zh || "") + '<span>' + h(c.prompt || "") + '</span>';
      byId("judgeGrid").innerHTML = REPORT.judges.map((judge) => judgeCard(judge, model, c)).join("");
    }

    ["breakdownModel","breakdownJudge","breakdownGroup"].forEach((id) => byId(id).addEventListener("change", renderBreakdown));
    ["caseModel","caseSelect"].forEach((id) => byId(id).addEventListener("change", renderCase));
    renderBreakdown();
    renderCase();
  </script>
</body>
</html>`;

writeFileSync(OUT_PATH, html, "utf8");
console.log(`wrote ${OUT_PATH}`);
