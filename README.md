# Spatial Prompt Bench Viewer

Static viewer for inspecting spatial prompt benchmark cases, generated samples, and scoring checklists.

Serve the folder over HTTP or publish it with GitHub Pages, then open `index.html`.

- `index.html`: inspect all 97 v3 prompts and compare FLUX.1-schnell, SDXL Base 1.0, and LayoutGPT + GLIGEN case by case, including strict local VQA answers.
- `v3_results.html`: strict local Qwen3-VL-8B results for the 97-case v3 suite, plus the separate 21-case T2I-Blender pilot.
- `vqa_report.html`: current unified report for Qwen3-VL-8B, qwen3-vl-plus API, and GPT subagent judgments.
- `our_pipeline_partial_report.html`: 63/76-image partial T2I-Blender run with independent subagent scoring and provisional atomic/compositional grouping.
- `vqa/`: complete JSONL answers, reasons, relation scores, evaluator snapshots, logs, and retry records.

The legacy report uses presence gating, direct `between` questions, positive/inverse checks for other relations, per-case relation normalization, and `20% presence + 80% relation` combined scoring. The v3 page uses strict binary scoring and reports presence, cardinality, relation accuracy, and exact-case pass separately. Previous-protocol files are retained under `vqa/archive_legacy_20260709/`.

T2I-Blender RGB renders and Qwen redraws are intentionally absent from the main viewer until the full v3 run completes.
