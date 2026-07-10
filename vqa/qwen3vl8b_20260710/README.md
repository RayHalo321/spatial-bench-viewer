# Qwen3-VL-8B Judge Records

- Judge: `Qwen3-VL-8B-Instruct`, served locally with vLLM on one A100 80GB.
- Date: 2026-07-10.
- Scope: 76 cases, 214 presence checks, 174 spatial relation checks per image model.
- Protocol: opaque question IDs, presence gating, positive/negative relation questions, and direct ternary `between` questions.
- Scoring: relation scores are normalized within each case; `combined = 0.2 * presence + 0.8 * relation`.

Each model directory contains the complete `vqa_results.jsonl`, a standardized `summary.json`, and the evaluation log when available. Every result row keeps the question answers, confidence, short reason, raw response, relation details, and error field.

FLUX `OCC09` initially produced malformed JSON. Its original row and log are retained; `retry_OCC09.jsonl` records the structure-constrained retry used in the final merged results.

Evaluator SHA-256: `42b042862db2fdd10b25d86ef2f7776ba6e1568d61705a9577b1b1c92f955e9a`

Cases SHA-256: `321f2bd4d1f95145734531a0cc0707a034f5c7523434801511e2cf90c5c9b36a`
