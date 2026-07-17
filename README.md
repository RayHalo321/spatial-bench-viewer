# Spatial Prompt Bench Viewer

Static viewer for inspecting spatial prompt benchmark cases, generated samples, and scoring checklists.

Serve the folder over HTTP or publish it with GitHub Pages, then open `index.html`.

- `index.html`: inspect the curated 93-case v3 suite and compare FLUX.1-schnell, SDXL Base 1.0, LayoutGPT + GLIGEN, and T2I-Blender RGB case by case.
- `v3_results.html`: uniform strict local Qwen3-VL-8B results for all four methods on the same 93 cases and 947 atomic questions.
- `vqa_report.html`: current unified report for Qwen3-VL-8B, qwen3-vl-plus API, and GPT subagent judgments.
- `our_pipeline_partial_report.html`: 63/76-image partial T2I-Blender run with independent subagent scoring and provisional atomic/compositional grouping.
- `vqa/`: complete JSONL answers, reasons, relation scores, evaluator snapshots, logs, and retry records.

The legacy report uses presence gating, direct `between` questions, positive/inverse checks for other relations, per-case relation normalization, and `20% presence + 80% relation` combined scoring. The v3 page uses strict binary scoring and reports presence, cardinality, relation accuracy, and exact-case pass separately. Previous-protocol files are retained under `vqa/archive_legacy_20260709/`.

The original 97-case data and scores remain archived. The active viewer excludes four human-confirmed invalid occlusion/depth renders and includes T2I-Blender RGB outputs; full-suite Qwen redraws remain a separate follow-up.
