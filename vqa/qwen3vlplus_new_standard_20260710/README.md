# qwen3-vl-plus API Judge Records

- Judge: `qwen3-vl-plus` through the remote DashScope-compatible API.
- Date: 2026-07-10.
- Scope: four image models, 76 cases each, 214 presence checks and 174 spatial relation checks per image model.
- Protocol: opaque question IDs, presence gating, positive/inverse relation questions, and direct ternary `between` questions.
- Scoring: each case normalizes by relation count; `combined = 0.2 * presence + 0.8 * relation`.

The root keeps one evaluator and case snapshot. Each image-model directory contains the final `vqa_results.jsonl`, standardized `summary.json`, original full-run output, logs, and retry evidence. The final four files contain 76 unique case IDs, 174 relation details, and no errors.

Nine first-pass responses contained malformed JSON. Six were recovered by a regular single-case retry; three used the recorded constrained-JSON retry. The failed first-pass rows remain in `vqa_results_raw.jsonl` and the replacement rows remain in their `retry_*` directories.
