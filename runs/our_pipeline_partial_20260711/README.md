# T2I-Blender Partial Bench Run

- Remote run: `current_20260708_full_qwen_20260710`
- Pipeline: T2I-Blender scene construction followed by Qwen-Edit image output
- Expected cases: 76
- Completed images: 63
- Scene-incomplete or non-exported cases: 13
- Coverage: 82.9%

This is an incomplete diagnostic snapshot, not a final benchmark result. The missing cases are not scored as zero in the partial report because missingness is concentrated in hard and orientation-heavy prompts. `DEP08` is a confirmed `relation_not_visually_readable` contract failure, `DEP10` stopped during verifier execution, and the other 11 cases have no preserved run or log artifact and are treated as coverage gaps rather than semantic failures.

Missing cases:

- `DEP08`, `DEP10`
- `OCC08`
- `SUP05`, `SUP08`
- `ORI03`, `ORI06`, `ORI08`, `ORI09`
- `ROT09`
- `MUL04`, `MUL06`, `MUL09`

The directory retains the remote `results.jsonl` and completion audits. Web previews are stored under `generated/our_pipeline_partial_20260711/`; independent visual-judge records are stored under `vqa/our_pipeline_partial_subagent_20260711/`.
