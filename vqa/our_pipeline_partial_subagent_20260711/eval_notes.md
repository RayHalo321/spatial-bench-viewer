# T2I-Blender partial run independent visual evaluation

This evaluation covers only the 63 images marked `available=true` in `our_pipeline_partial_20260711.json`. It is a partial run: coverage is 63/76 (82.89%). The 13 unavailable cases receive no rows and no fabricated scores.

## Protocol

Each image was inspected directly. Presence is judged per canonical object. Every relation uses the canonical positive question and the inverse construction from `run_spatial_bench_qwen_vqa_local.py`; `between` uses only its direct ternary question. Relation scoring applies the presence gate, then scores positive=yes/inverse=no as 1, positive=no as 0, other inverse conflicts or unclear results as 0.5, and positive-only yes/unclear/no as 1/0.5/0. Case relations are averaged over relation checks and combined score is `0.2 * presence + 0.8 * relation`.

Opaque IDs (`q001`, `q002`, ...) were assigned within each case while judging so semantic check IDs did not reveal expected answers. The output maps them back to canonical answer keys for report compatibility and retains each opaque ID in the answer record.

## Observed failure modes

- Duplicate instances sometimes make both a positive and inverse question visibly true: ABS06 has suitcases on both sides; REL08 has chairs on both sides of queried objects; REL09 has one chair in front of and another behind the desk; ROT08 contains vases at different depths. These are scored 0.5 when the presence gate passes.
- Several requested spatial constraints are visibly reversed or absent: REL04 does not place the vase as a distinct object between sofa and coffee table; REL10 places the plant left of the chair; ROT05 yaws the cabinet in the opposite direction; MUL08 leaves a gap between plant and television.
- Some generated geometry undermines support or recognition: MUL03 puts the cup set floating below the desktop; OCC03's occluded tall wooden form lacks visible shelf features, so bookshelf presence is unclear and the relation fails the presence gate.
- Orientation and exact yaw remain difficult from a single view. ORI04 shows the laptop screen nearly edge-on; ROT03 and ROT08 are not close to 90 degrees; ROT07 is only slightly angled, so the 45-degree claim is unclear; ROT10 is visibly front-facing rather than yawed 45 degrees.
- SUP09 omits the laptop and office desk, so their support relation is forced to zero by the presence gate.

## Partial-run bias

The missing IDs are: DEP08, DEP10, OCC08, SUP05, SUP08, ORI03, ORI06, ORI08, ORI09, ROT09, MUL04, MUL06, MUL09. Missing samples are not random across the benchmark: all 6 simple cases are present, while all 13 missing samples are normal/hard cases, including multiple orientation and multi-relation cases. Consequently, the reported macro scores describe the completed 63-case subset and likely overstate full-run performance if unavailable cases are systematically harder. They must not be used as a 76-case score or for final model ranking.

## Key metrics on the available subset

- Presence macro: 99.29%
- Relation case macro: 88.81%
- Relation micro: 87.70%
- Exact case pass rate: 74.60%
- Combined macro: 90.90%

Validation: 63 rows, 63 unique IDs, 164 presence checks, 126 relation details, 0 errors; every case relation average and `0.2/0.8` combined formula were recomputed.
