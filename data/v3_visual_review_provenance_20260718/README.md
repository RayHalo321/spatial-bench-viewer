# Visual review provenance

These files preserve the blind direct-visual judgments used to complete the
ten-method Spatial Bench v3 table.

- `card_*_agent.jsonl`: first-pass cardinality judgments for the six methods
  whose older audits did not score object counts separately.
- `full_blender_qwen_agent.jsonl`: first-pass presence, cardinality, and
  relation judgments for T2I-Blender + Qwen I2I.
- `cardinality_adjudicate_*_output.jsonl` and
  `blender_qwen_adjudicate_output.jsonl`: independent blind reviews of every
  first-pass/Qwen3-VL-32B disagreement.

The headline table uses the independent adjudication on disputed cells and the
first pass elsewhere. Qwen3-VL-32B is retained as a separate diagnostic judge;
it never directly replaces a visual reviewer decision.
