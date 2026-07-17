# Spatial Prompt Bench Viewer

Static viewer for inspecting spatial prompt benchmark cases, generated samples, and scoring checklists.

Serve the folder over HTTP or publish it with GitHub Pages, then open `index.html`.

- `index.html`: inspect the curated 93-case v3 suite and compare FLUX.1-schnell, SDXL Base 1.0, LayoutGPT + GLIGEN, T2I-Blender RGB, and Qwen-refined T2I-Blender outputs case by case.
- `v3_results.html`: frozen multi-reviewer visual adjudication for the four scored methods on the same 93 cases, 269 object instances, and 243 explicit relations.
- `vqa_report.html`: current unified report for Qwen3-VL-8B, qwen3-vl-plus API, and GPT subagent judgments.
- `our_pipeline_partial_report.html`: 63/76-image partial T2I-Blender run with independent subagent scoring and provisional atomic/compositional grouping.
- `vqa/`: complete JSONL answers, reasons, relation scores, evaluator snapshots, logs, and retry records.

The legacy report uses presence gating, direct `between` questions, positive/inverse checks for other relations, per-case relation normalization, and `20% presence + 80% relation` combined scoring. The active v3 page uses strict adjudicated scoring and reports presence, relation accuracy, primary-relation accuracy, and exact-case pass separately. Previous-protocol files are retained under `vqa/archive_legacy_20260709/`.

The original 97-case data and old 8B scores remain archived. The active viewer excludes four visually invalid occlusion/depth renders and includes all 93 Qwen-refined outputs. Those Qwen-refined images are deliberately unscored until they receive the same separate visual audit.
