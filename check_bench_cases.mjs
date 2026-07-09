import { existsSync, readFileSync } from "node:fs";

const cases = JSON.parse(readFileSync(new URL("./data/bench_cases.json", import.meta.url), "utf8"));

const allowedAssets = new Set([
  "barrel",
  "bench",
  "bookshelf",
  "bowl",
  "cabinet",
  "camera",
  "chair",
  "coffee_table",
  "crate",
  "cup_set",
  "desk",
  "lamp",
  "laptop",
  "metal_shelves",
  "nightstand",
  "office_desk",
  "payphone",
  "plate",
  "potted_plant",
  "round_table",
  "shelf",
  "side_table",
  "sofa",
  "suitcase",
  "table",
  "tv",
  "vase",
  "video_camera",
  "wet_floor_sign",
]);
const disallowedBenchAssets = new Set(["camera", "clock", "video_camera"]);

function fail(message) {
  throw new Error(message);
}

const ids = new Set();
let absoluteCount = 0;
let hardCount = 0;
const categoryCounts = {};

for (const item of cases) {
  if (ids.has(item.id)) fail(`duplicate id: ${item.id}`);
  ids.add(item.id);

  const pairCount = (item.checklist || []).filter((check) => check.type !== "presence").length;
  if (item.pair_count !== pairCount) fail(`${item.id}: pair_count ${item.pair_count} != ${pairCount}`);

  const objectIds = new Set();
  for (const object of item.objects || []) {
    if (!allowedAssets.has(object.canonical)) fail(`${item.id}: unsupported asset ${object.canonical}`);
    if (disallowedBenchAssets.has(object.canonical)) fail(`${item.id}: unstable asset for current bench ${object.canonical}`);
    if (objectIds.has(object.canonical)) fail(`${item.id}: duplicate object ${object.canonical}`);
    objectIds.add(object.canonical);
  }

  for (const relation of item.relations || []) {
    if (!objectIds.has(relation.subject)) fail(`${item.id}: relation subject not in objects: ${relation.subject}`);
    if (relation.target && allowedAssets.has(relation.target) && !objectIds.has(relation.target)) {
      fail(`${item.id}: relation target not in objects: ${relation.target}`);
    }
    if (relation.target2 && allowedAssets.has(relation.target2) && !objectIds.has(relation.target2)) {
      fail(`${item.id}: relation target2 not in objects: ${relation.target2}`);
    }
  }

  if (item.sample?.status === "success") {
    if (!item.sample.image?.startsWith("generated/zimage_turbo_1024/")) {
      fail(`${item.id}: generated sample uses unexpected path ${item.sample.image}`);
    }
    if (!existsSync(new URL(`./${item.sample.image}`, import.meta.url))) {
      fail(`${item.id}: generated sample file is missing: ${item.sample.image}`);
    }
  }

  if (item.category === "absolute_location_2d") {
    absoluteCount += 1;
    if (item.level !== "simple") fail(`${item.id}: absolute cases must be simple`);
    if (item.difficulty !== "simple") fail(`${item.id}: difficulty should mirror level`);
    continue;
  }

  const count = categoryCounts[item.category] ||= { normal: 0, hard: 0 };
  count[item.level] += 1;

  if (!["normal", "hard"].includes(item.level)) fail(`${item.id}: invalid level ${item.level}`);
  if (item.difficulty !== item.level) fail(`${item.id}: difficulty should mirror level`);
  if (item.level === "hard" && pairCount < 4) fail(`${item.id}: hard case has only ${pairCount} relation checks`);
  if (item.level === "hard" && pairCount > 6) fail(`${item.id}: hard case has too many pairs: ${pairCount}`);
  if (item.level === "normal" && pairCount >= 5) fail(`${item.id}: normal case has ${pairCount} pairs`);
  if (item.level === "hard") hardCount += 1;
}

if (absoluteCount > 6) fail(`too many absolute_location_2d cases: ${absoluteCount}`);
for (const [category, count] of Object.entries(categoryCounts)) {
  if (count.normal !== 7 || count.hard !== 3) {
    fail(`${category}: expected 7 normal / 3 hard, got ${count.normal} normal / ${count.hard} hard`);
  }
}
if (hardCount === 0) fail("no hard cases");

console.log(`bench cases OK: ${cases.length} cases, ${absoluteCount} absolute, ${hardCount} hard`);
