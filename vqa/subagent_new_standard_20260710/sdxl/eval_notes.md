# SDXL Evaluation Notes

- Image model: SDXL
- Judge: GPT-Subagent
- Scope: 76 images in `generated/sdxl_1024`
- Protocol: NEW presence-gated positive/inverse protocol, with direct ternary questions for `between`
- Question handling: visual decisions were recorded in case-local opaque order and mapped to benchmark check IDs only after judging

## Ambiguous cases

- `REL01`: several chairs appear on both sides of the table, so both directional readings are unclear.
- `REL08`: no distinct chair is visible; a small floor object could be luggage, so suitcase presence and its relation are unclear.
- `REL10`: the plant overlaps the chair horizontally, making left/right placement unclear.
- `DEP01`: one seat/loveseat hybrid cannot establish distinct chair and sofa instances; both presences and the depth relation are unclear.
- `DEP05`: one plant is left of the bench and another sits on it; neither a behind nor in-front relation is visibly established.
- `OCC10`: two chairs are visible, so the suitcase's left/right relation to "the chair" is unclear.
- `SUP09`: the stylized scene merges several furniture roles; the far-right surface is not clearly a side table.
- `ORI06`: the sofa is nearly frontal and symmetric, so its slight rightward angle is unclear.
- `ROT02`: stylized ghost geometry makes the chair's 45-degree yaw direction unclear.
- `ROT03`: multiple laptops appear at different angles; none visibly establishes a 90-degree clockwise rotation.
- `ROT07`: the symmetric bench is oblique, but the image does not reliably establish left versus right 45-degree yaw.
- `ROT10`: the cropped blue seat reads as a sofa rather than a distinct chair, and the object atop the cabinet reads as a bag rather than a suitcase.
- `MUL02`: the foreground item merges suitcase and bench cues; both are counted present, but it cannot be right of itself.
- `MUL08`: the partial chair is at the lower right, the suitcase-like item is under/left of the table, and TV-versus-sofa depth is not established by overlap.
- `MUL09`: no distinct crate or suitcase is visible, and the shelf-like structure is not clearly a bench.

## Full-resolution rechecks

Original-detail inspection was used for `REL01`, `REL06`, `REL07`, `REL08`, `REL10`, `DEP01`, `DEP05`, `OCC01`, `OCC05`, `OCC10`, `SUP09`, `ORI06`, `ROT02`, `ROT07`, `ROT10`, and `MUL09`.
