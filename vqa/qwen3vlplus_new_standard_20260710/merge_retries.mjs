import { readFileSync, writeFileSync } from "node:fs";

const configs = {
  zimage: ["retry_structured_ORI09/vqa_results.jsonl"],
  sdxl: [
    "retry_failed/vqa_results.jsonl",
    "retry_structured_MUL04/vqa_results.jsonl",
    "retry_structured_MUL05/vqa_results.jsonl",
  ],
  flux: ["retry_failed/vqa_results.jsonl", "retry_ORI04/vqa_results.jsonl"],
  qwen_edit: ["retry_failed/vqa_results.jsonl", "retry_OCC10/vqa_results.jsonl"],
};

for (const [model, retryPaths] of Object.entries(configs)) {
  const rawPath = `${model}/results/vqa_results.jsonl`;
  const rawRows = readJsonl(rawPath);
  writeFileSync(`${model}/vqa_results_raw.jsonl`, lines(rawRows));
  const byId = new Map(rawRows.map((row) => [row.id, row]));
  for (const retryPath of retryPaths) {
    for (const row of readJsonl(`${model}/${retryPath}`)) {
      if (!row.error) byId.set(row.id, row);
    }
  }
  const rows = rawRows.map((row) => byId.get(row.id));
  const relations = rows.reduce((count, row) => count + (row.relation_details || []).length, 0);
  const errors = rows.filter((row) => row.error);
  if (rows.length !== 76 || new Set(rows.map((row) => row.id)).size !== 76 || relations !== 174 || errors.length) {
    throw new Error(`${model}: rows=${rows.length}, relations=${relations}, errors=${errors.map((row) => row.id)}`);
  }
  writeFileSync(`${model}/vqa_results.jsonl`, lines(rows));
  writeFileSync(`${model}/summary.json`, JSON.stringify(summarize(rows), null, 2) + "\n");
  console.log(`${model}: 76 cases, 174 relations, 0 errors`);
}

function readJsonl(path) {
  return readFileSync(path, "utf8").split("\n").filter(Boolean).map((line) => JSON.parse(line));
}

function lines(rows) {
  return rows.map((row) => JSON.stringify(row)).join("\n") + "\n";
}

function summarize(rows) {
  return {
    overall: pack(rows),
    by_category: groups(rows, (row) => row.category),
    by_level: groups(rows, (row) => row.level),
  };
}

function groups(rows, keyOf) {
  const grouped = new Map();
  for (const row of rows) {
    const key = keyOf(row);
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key).push(row);
  }
  return Object.fromEntries([...grouped].map(([key, values]) => [key, pack(values)]));
}

function pack(rows) {
  const relations = rows.flatMap((row) => row.relation_details || []);
  return {
    cases: rows.length,
    relations: relations.length,
    presence_macro: average(rows.map((row) => row.presence_score)),
    relation_case_macro: average(rows.map((row) => row.relation_score)),
    relation_micro: average(relations.map((detail) => detail.score)),
    exact_case_pass_rate: average(rows.map((row) => Number(row.relation_score === 1))),
    combined_macro: average(rows.map((row) => 0.2 * row.presence_score + 0.8 * row.relation_score)),
    errors: rows.filter((row) => row.error).length,
  };
}

function average(values) {
  return values.length ? values.reduce((sum, value) => sum + Number(value || 0), 0) / values.length : 0;
}
