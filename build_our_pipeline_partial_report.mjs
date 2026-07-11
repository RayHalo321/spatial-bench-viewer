import { readFileSync, writeFileSync } from "node:fs";

const manifest = JSON.parse(readFileSync("data/our_pipeline_partial_20260711.json", "utf8"));
const cases = JSON.parse(readFileSync("data/bench_cases.json", "utf8"));
const resultPath = "vqa/our_pipeline_partial_subagent_20260711/vqa_results.jsonl";
const outPath = process.argv[2] || "our_pipeline_partial_report.html";
const rows = readFileSync(resultPath, "utf8").trim().split(/\n+/).filter(Boolean).map((line) => JSON.parse(line));
const availableIds = new Set(manifest.items.filter((item) => item.available).map((item) => item.id));

if (rows.length !== manifest.available || new Set(rows.map((row) => row.id)).size !== manifest.available) {
  throw new Error(`expected ${manifest.available} unique judge rows, got ${rows.length}`);
}
if (rows.some((row) => !availableIds.has(row.id) || row.error)) {
  throw new Error("judge rows contain unavailable cases or errors");
}
const relationCount = rows.reduce((sum, row) => sum + (row.relation_details || []).length, 0);
if (relationCount !== 126) throw new Error(`expected 126 relation details, got ${relationCount}`);

const rowById = new Map(rows.map((row) => [row.id, row]));
const caseById = new Map(cases.map((item) => [item.id, item]));

function provisionalClass(constraintCount) {
  if (constraintCount === 1) return "atomic_diagnostic";
  if (constraintCount <= 3) return "compositional_normal";
  if (constraintCount === 4) return "needs_revision_4_constraints";
  return "compositional_hard";
}

function average(values) {
  return values.length ? values.reduce((sum, value) => sum + Number(value || 0), 0) / values.length : 0;
}

function pack(groupRows) {
  const relations = groupRows.flatMap((row) => row.relation_details || []);
  return {
    cases: groupRows.length,
    relations: relations.length,
    presence: average(groupRows.map((row) => row.presence_score)),
    relationCase: average(groupRows.map((row) => row.relation_score)),
    relationMicro: average(relations.map((item) => item.score)),
    combined: average(groupRows.map((row) => 0.2 * row.presence_score + 0.8 * row.relation_score)),
    exact: average(groupRows.map((row) => Number(row.relation_score === 1))),
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
      questions.push({ id: check.check_id, type: "presence", question });
      continue;
    }
    questions.push({ id: `${check.check_id}|pos`, type: "positive", question });
    const inverse = inverseQuestion(check);
    if (inverse) questions.push({ id: `${check.check_id}|neg`, type: "inverse", question: inverse });
  }
  return questions;
}

const items = manifest.items.map((item) => {
  const c = caseById.get(item.id);
  const row = rowById.get(item.id) || null;
  return {
    ...item,
    provisional_class: provisionalClass(item.constraint_count),
    prompt: c.prompt,
    prompt_zh: c.prompt_zh,
    questions: questionsForCase(c),
    score: row ? {
      presence: row.presence_score,
      relation: row.relation_score,
      combined: 0.2 * row.presence_score + 0.8 * row.relation_score,
      answers: row.answers || {},
      relationDetails: row.relation_details || [],
    } : null,
  };
});

const overall = pack(rows);
const categories = [...new Set(items.map((item) => item.category))];
const coverageRows = categories.map((category) => {
  const group = items.filter((item) => item.category === category);
  const evaluated = rows.filter((row) => (caseById.get(row.id) || {}).category === category);
  const metrics = pack(evaluated);
  return {
    category,
    expected: group.length,
    available: group.filter((item) => item.available).length,
    missing: group.filter((item) => !item.available).length,
    ...metrics,
  };
});
const subsetRows = [...new Set(items.map((item) => item.provisional_class))].map((name) => {
  const group = items.filter((item) => item.provisional_class === name);
  const evaluated = rows.filter((row) => group.some((item) => item.id === row.id));
  return {
    name,
    expected: group.length,
    available: group.filter((item) => item.available).length,
    missing: group.filter((item) => !item.available).length,
    ...pack(evaluated),
  };
});

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch]);
}

function pct(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

const serialized = JSON.stringify({ manifest: { ...manifest, items: undefined }, items, overall, coverageRows, subsetRows })
  .replaceAll("<", "\\u003c");

const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>T2I-Blender Partial Bench Report</title>
  <style>
    :root { --bg:#f7f3ea; --panel:#fffdf8; --text:#2f2a24; --muted:#756e64; --line:#e5dbce; --accent:#b95735; --accent-soft:#f8e8dc; --ok:#42764b; --bad:#a8483d; --warn:#89681e; }
    * { box-sizing:border-box; }
    body { margin:0; color:var(--text); background:var(--bg); font:14px/1.5 ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    h1,h2,h3 { font-family:ui-serif,Georgia,Cambria,"Times New Roman",serif; letter-spacing:0; }
    a { color:var(--accent); text-decoration:none; }
    header { position:sticky; top:0; z-index:10; display:flex; justify-content:space-between; align-items:center; gap:12px; padding:12px max(16px,calc((100vw - 1500px)/2)); border-bottom:1px solid var(--line); background:rgba(255,253,248,.96); }
    header h1 { margin:0; font-size:20px; }
    nav { display:flex; gap:8px; flex-wrap:wrap; }
    nav a { padding:5px 9px; border:1px solid var(--line); border-radius:6px; color:var(--text); background:var(--panel); }
    main { max-width:1500px; margin:auto; padding:22px 16px 60px; }
    .hero { display:grid; grid-template-columns:minmax(0,1.4fr) minmax(300px,.6fr); gap:18px; align-items:start; }
    .hero h2 { margin:0; font-size:34px; }
    .hero p { color:var(--muted); max-width:900px; }
    .warning { padding:14px 16px; border-left:4px solid var(--warn); background:#fff8e8; }
    .metrics { display:grid; grid-template-columns:repeat(6,minmax(130px,1fr)); gap:9px; margin:18px 0; }
    .metric { min-height:92px; padding:13px; border:1px solid var(--line); border-radius:7px; background:var(--panel); }
    .metric b { display:block; font-size:24px; }
    .metric span { color:var(--muted); }
    section { margin:22px 0; }
    section h2 { margin:0 0 10px; }
    .panel { padding:14px; border:1px solid var(--line); border-radius:8px; background:var(--panel); }
    .table-wrap { overflow:auto; }
    table { width:100%; border-collapse:collapse; }
    th,td { padding:8px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
    th { color:var(--muted); font-size:12px; white-space:nowrap; }
    tbody tr:last-child td { border-bottom:0; }
    .filters { display:grid; grid-template-columns:2fr repeat(4,minmax(145px,1fr)); gap:9px; margin-bottom:12px; }
    input,select { width:100%; min-height:38px; padding:7px 9px; border:1px solid var(--line); border-radius:6px; color:var(--text); background:var(--panel); }
    .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(330px,1fr)); gap:12px; }
    article { overflow:hidden; border:1px solid var(--line); border-radius:8px; background:var(--panel); }
    article.missing { background:#fbf7f0; }
    article img,.missing-media { display:block; width:100%; aspect-ratio:1; object-fit:contain; background:#ece7de; border-bottom:1px solid var(--line); }
    .missing-media { display:grid; place-items:center; color:var(--muted); font-size:16px; }
    .card-body { padding:13px; }
    .case-head { display:flex; justify-content:space-between; gap:8px; align-items:start; }
    .case-head h3 { margin:0; font-size:18px; }
    .tags,.score-row { display:flex; gap:6px; flex-wrap:wrap; }
    .tag { padding:2px 7px; border:1px solid var(--line); border-radius:999px; color:var(--muted); font-size:12px; }
    .score-row { margin:10px 0; }
    .score-row span { padding:5px 8px; border-radius:5px; background:var(--accent-soft); }
    .prompt { min-height:86px; margin:10px 0; }
    .prompt span { display:block; margin-top:4px; color:var(--muted); }
    details { border-top:1px solid var(--line); padding-top:9px; }
    summary { cursor:pointer; color:var(--accent); }
    details table { margin-top:8px; font-size:12px; }
    code { font:11px/1.35 ui-monospace,SFMono-Regular,Menlo,monospace; overflow-wrap:anywhere; }
    .answer { font-weight:700; }.yes { color:var(--ok); }.no { color:var(--bad); }.unclear { color:var(--warn); }
    .empty { padding:34px; text-align:center; color:var(--muted); }
    @media(max-width:1000px) { .hero { grid-template-columns:1fr; } .metrics { grid-template-columns:repeat(3,1fr); } }
    @media(max-width:680px) { header { align-items:flex-start; } header h1 { font-size:17px; } main { padding:16px 10px 40px; } .hero h2 { font-size:28px; } .metrics { grid-template-columns:1fr 1fr; } .filters { grid-template-columns:1fr; } .grid { grid-template-columns:1fr; } }
  </style>
</head>
<body>
  <header><h1>T2I-Blender Partial Bench</h1><nav><a href="index.html">样例浏览器</a><a href="vqa_report.html">Direct T2I VQA</a><a href="${esc(resultPath)}">Judge JSONL</a></nav></header>
  <main>
    <div class="hero">
      <div><h2>当前不完整版本成果汇总</h2><p>Run <code>${esc(manifest.run_id)}</code>。这里展示 T2I-Blender 完成场景构建后，再经过 Qwen-Edit 输出的成果图，并由独立视觉 subagent 按当前 soft-score checklist 协议评分。</p></div>
      <div class="warning"><b>Partial run，不用于最终模型排名</b><br>当前只有 ${manifest.available}/${manifest.expected} 张图。缺失样本在 hard 和 orientation 类别中更集中，因此下方均值只代表已完成子集。</div>
    </div>
    <div class="metrics">
      <div class="metric"><b>${pct(manifest.available / manifest.expected)}</b><span>image coverage · ${manifest.available}/${manifest.expected}</span></div>
      <div class="metric"><b>${pct(overall.presence)}</b><span>presence macro</span></div>
      <div class="metric"><b>${pct(overall.relationCase)}</b><span>relation case macro</span></div>
      <div class="metric"><b>${pct(overall.relationMicro)}</b><span>relation micro · ${overall.relations} checks</span></div>
      <div class="metric"><b>${pct(overall.exact)}</b><span>exact case pass</span></div>
      <div class="metric"><b>${pct(overall.combined)}</b><span>combined · 20/80</span></div>
    </div>
    <section><h2>Category Coverage</h2><div class="panel table-wrap"><table><thead><tr><th>Category</th><th>Available</th><th>Missing</th><th>Presence</th><th>Relation case</th><th>Relation micro</th><th>Exact</th></tr></thead><tbody>${coverageRows.map((x) => `<tr><td><b>${esc(x.category)}</b></td><td>${x.available}/${x.expected}</td><td>${x.missing}</td><td>${pct(x.presence)}</td><td>${pct(x.relationCase)}</td><td>${pct(x.relationMicro)}</td><td>${pct(x.exact)}</td></tr>`).join("")}</tbody></table></div></section>
    <section><h2>Provisional Subsets</h2><div class="warning">这里按正在讨论的新规则临时重分组：1 constraint 为 atomic；2–3 为 compositional normal；5–6 为 compositional hard；4 constraints 单独标记待修订。原始 case 数据尚未正式迁移。</div><div class="panel table-wrap"><table><thead><tr><th>Provisional subset</th><th>Available</th><th>Missing</th><th>Presence</th><th>Relation case</th><th>Relation micro</th><th>Exact</th></tr></thead><tbody>${subsetRows.map((x) => `<tr><td><b>${esc(x.name)}</b></td><td>${x.available}/${x.expected}</td><td>${x.missing}</td><td>${pct(x.presence)}</td><td>${pct(x.relationCase)}</td><td>${pct(x.relationMicro)}</td><td>${pct(x.exact)}</td></tr>`).join("")}</tbody></table></div></section>
    <section>
      <h2>Cases</h2>
      <div class="filters panel"><input id="search" placeholder="搜索 case ID 或 prompt"><select id="category"><option value="">全部 category</option>${categories.map((x) => `<option>${esc(x)}</option>`).join("")}</select><select id="level"><option value="">全部旧 difficulty</option><option>simple</option><option>normal</option><option>hard</option></select><select id="provisional"><option value="">全部 provisional subset</option>${subsetRows.map((x) => `<option>${esc(x.name)}</option>`).join("")}</select><select id="status"><option value="">全部状态</option><option value="available">已生成并评分</option><option value="missing">未完成</option></select></div>
      <div class="grid" id="caseGrid"></div>
    </section>
  </main>
  <script>
    const DATA=${serialized};
    const h=(value)=>String(value??"").replace(/[&<>"']/g,(ch)=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
    const pct=(value)=>(Number(value||0)*100).toFixed(1)+"%";
    function card(item){
      const media=item.available?'<img loading="lazy" src="'+h(item.image)+'" alt="'+h(item.id)+'">':'<div class="missing-media">No completed image</div>';
      const scores=item.score?'<div class="score-row"><span>presence '+pct(item.score.presence)+'</span><span>relation '+pct(item.score.relation)+'</span><span>combined '+pct(item.score.combined)+'</span></div>':'<div class="score-row"><span>scene incomplete</span></div>';
      const answerRows=item.score?item.questions.map((q)=>{const a=item.score.answers[q.id]||{answer:'unclear',reason:'missing answer'};return '<tr><td><code>'+h(q.id)+'</code></td><td>'+h(q.question)+'</td><td class="answer '+h(a.answer)+'">'+h(a.answer)+'</td><td>'+h(a.reason||'')+'</td></tr>';}).join(''):'';
      const details=item.score?'<details><summary>逐问题 Judge 记录</summary><div class="table-wrap"><table><thead><tr><th>ID</th><th>Question</th><th>Answer</th><th>Reason</th></tr></thead><tbody>'+answerRows+'</tbody></table></div></details>':'<details><summary>未完成原因</summary><p>'+h(item.run_status)+' · '+h(item.termination_reason||item.failure_class||'scene_incomplete')+'</p></details>';
      return '<article class="'+(item.available?'':'missing')+'">'+media+'<div class="card-body"><div class="case-head"><h3>'+h(item.id)+'</h3><div class="tags"><span class="tag">'+h(item.category)+'</span><span class="tag">'+h(item.provisional_class)+'</span><span class="tag">'+item.constraint_count+' constraints</span></div></div>'+scores+'<p class="prompt">'+h(item.prompt_zh||'')+'<span>'+h(item.prompt)+'</span></p>'+details+'</div></article>';
    }
    function render(){
      const query=document.querySelector('#search').value.trim().toLowerCase();const category=document.querySelector('#category').value;const level=document.querySelector('#level').value;const provisional=document.querySelector('#provisional').value;const status=document.querySelector('#status').value;
      const filtered=DATA.items.filter((item)=>(!query||(item.id+' '+item.prompt+' '+(item.prompt_zh||'')).toLowerCase().includes(query))&&(!category||item.category===category)&&(!level||item.level===level)&&(!provisional||item.provisional_class===provisional)&&(!status||(status==='available')===item.available));
      document.querySelector('#caseGrid').innerHTML=filtered.length?filtered.map(card).join(''):'<div class="empty">没有符合当前筛选的 case</div>';
    }
    ['search','category','level','provisional','status'].forEach((id)=>document.querySelector('#'+id).addEventListener(id==='search'?'input':'change',render));render();
  </script>
</body>
</html>`;

writeFileSync(outPath, html, "utf8");
console.log(`wrote ${outPath}`);
