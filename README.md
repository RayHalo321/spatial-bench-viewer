# Spatial Prompt Bench Viewer

Static viewer for inspecting spatial prompt benchmark cases, generated samples, and scoring checklists.

Serve the folder over HTTP or publish it with GitHub Pages, then open `index.html`.

- `index.html`: inspect the curated 93-case v3 suite and compare all ten generation methods case by case.
- `v3_results.html`: frozen ten-method visual adjudication with Presence, Cardinality, grouped spatial scores, Spatial Macro, strict Case Exact, and difficulty breakdowns.
- `vqa_report.html`: current unified report for Qwen3-VL-8B, qwen3-vl-plus API, and GPT subagent judgments.
- `our_pipeline_partial_report.html`: 63/76-image partial T2I-Blender run with independent subagent scoring and provisional atomic/compositional grouping.
- `vqa/`: complete JSONL answers, reasons, relation scores, evaluator snapshots, logs, and retry records.

The legacy report uses presence gating, direct `between` questions, positive/inverse checks for other relations, per-case relation normalization, and `20% presence + 80% relation` combined scoring. The active v3 page uses strict adjudicated scoring: fail and unclear score zero, while Case Exact requires presence, exact cardinality, and every explicit relation. Previous-protocol files are retained under `vqa/archive_legacy_20260709/`.

The original 97-case data and old 8B scores remain archived. The active viewer excludes four visually invalid occlusion/depth renders and includes complete direct-visual and Qwen3-VL-32B diagnostic results for all ten methods.
