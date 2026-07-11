# Spatial Prompt Bench Viewer

Static viewer for inspecting spatial prompt benchmark cases, generated samples, and scoring checklists.

Open `index.html` locally or publish this folder with GitHub Pages.

- `index.html`: compare Z-Image Turbo, SDXL, FLUX, and Qwen-Edit Direct images case by case.
- `vqa_report.html`: current unified report for Qwen3-VL-8B, qwen3-vl-plus API, and GPT subagent judgments.
- `our_pipeline_partial_report.html`: 63/76-image partial T2I-Blender run with independent subagent scoring and provisional atomic/compositional grouping.
- `vqa/`: complete JSONL answers, reasons, relation scores, evaluator snapshots, logs, and retry records.

The current scoring protocol uses presence gating, direct `between` questions, positive/inverse checks for other relations, per-case relation normalization, and `20% presence + 80% relation` combined scoring. Previous-protocol files are retained under `vqa/archive_legacy_20260709/` and are not used by the public report.
