import { readFileSync, writeFileSync } from "node:fs";

const root = new URL("./", import.meta.url);
const modelFiles = [
  {
    id: "zimage",
    label: "Z-Image Turbo",
    imageTemplate: "generated/zimage_turbo_1024/{id}.png",
    results: "vqa/qwen3vl8b_20260710/zimage/vqa_results.jsonl",
  },
  {
    id: "sdxl",
    label: "SDXL",
    imageTemplate: "generated/sdxl_1024/{id}.jpg",
    results: "vqa/qwen3vl8b_20260710/sdxl/vqa_results.jsonl",
  },
  {
    id: "flux",
    label: "FLUX",
    imageTemplate: "generated/flux_1024/{id}.jpg",
    results: "vqa/qwen3vl8b_20260710/flux/vqa_results.jsonl",
  },
  {
    id: "qwen_edit",
    label: "Qwen-Edit Direct",
    imageTemplate: "generated/qwen_edit_1024/{id}.jpg",
    results: "vqa/qwen3vl8b_20260710/qwen_edit/vqa_results.jsonl",
  },
];

const models = modelFiles.map((model) => {
  const rows = readJsonl(new URL(model.results, root));
  if (rows.length !== 76 || rows.some((row) => row.error)) {
    throw new Error(`${model.id}: expected 76 successful rows`);
  }
  const summary = summarize(rows);
  writeFileSync(
    new URL(model.results.replace("vqa_results.jsonl", "summary.json"), root),
    JSON.stringify(summary, null, 2) + "\n",
  );
  return {
    ...model,
    summary,
    cases: Object.fromEntries(rows.map((row) => [row.id, {
      presence: row.presence_score,
      relation: row.relation_score,
      combined: row.combined_score,
    }])),
  };
});

const output = {
  judge: {
    model: "Qwen3-VL-8B-Instruct",
    protocol: "neutral question ids; presence gate; positive/negative relation checks",
    generated: "2026-07-10",
  },
  models,
};

writeFileSync(new URL("./data/model_comparison.json", root), JSON.stringify(output, null, 2) + "\n");

const indexUrl = new URL("./index.html", root);
const index = readFileSync(indexUrl, "utf8");
const modelPattern = /const MODEL_DATA = .*?;\n    const CASES/s;
if (!modelPattern.test(index)) throw new Error("Could not find inline MODEL_DATA in index.html");
const updated = index.replace(
  modelPattern,
  `const MODEL_DATA = ${JSON.stringify(output)};\n    const CASES`,
);
writeFileSync(indexUrl, updated);
console.log(`embedded ${models.length} model runs`);

function readJsonl(url) {
  return readFileSync(url, "utf8").split("\n").filter(Boolean).map((line) => JSON.parse(line));
}

function summarize(rows) {
  const byCategory = group(rows, (row) => row.category);
  const byLevel = group(rows, (row) => row.level);
  return {
    overall: pack(rows),
    by_category: Object.fromEntries([...byCategory].map(([key, value]) => [key, pack(value)])),
    by_level: Object.fromEntries([...byLevel].map(([key, value]) => [key, pack(value)])),
  };
}

function group(rows, keyOf) {
  const groups = new Map();
  for (const row of rows) {
    const key = keyOf(row);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  }
  return groups;
}

function pack(rows) {
  const relations = rows.flatMap((row) => row.relation_details || []);
  return {
    cases: rows.length,
    relations: relations.length,
    presence_macro: average(rows.map((row) => row.presence_score)),
    relation_case_macro: average(rows.map((row) => row.relation_score)),
    relation_micro: average(relations.map((item) => item.score)),
    exact_case_pass_rate: average(rows.map((row) => Number(row.relation_score === 1))),
    errors: rows.filter((row) => row.error).length,
  };
}

function average(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
}
