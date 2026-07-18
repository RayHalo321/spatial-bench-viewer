# Cardinality audit validation summary

- Input rows: 93
- Output rows: 93
- Cardinality checks per method: 269
- Total method-check judgments: 538
- Input/output case order: exact match
- Check coverage: every input cardinality check appears exactly once for each method
- Duplicate or extra check keys: none
- Allowed answers: yes/no only
- Policy: blind direct-visual inspection; strict unclear=fail; no prior/Qwen/API scores used

## Results

| Method | Passed checks | Check accuracy | All-cardinality cases | Case accuracy |
|---|---:|---:|---:|---:|
| boxdiff_xl | 171/269 | 63.6% | 38/93 | 40.9% |
| t2i_blender | 259/269 | 96.3% | 85/93 | 91.4% |

## Failed cases

- **boxdiff_xl (55)**: ABS-D03, REL-D01, REL-D04, REL-H01, REL-H02, REL-H03, DEP-D01, DEP-D02, DEP-D03, DEP-D04, DEP-D05, DEP-D06, DEP-H03, OCC-D01, OCC-D02, OCC-D03, OCC-D04, OCC-D06, OCC-D07, OCC-H01, SUP-D01, SUP-D05, SUP-D07, SUP-H01, SUP-H02, SUP-H03, YAW-D01, ORI-H01, ORI-H02, ORI-H03, YAW-D09, YAW-H02, YAW-H03, MUL-N04, MUL-N05, MUL-N06, MUL-N07, MUL-H01, MUL-H02, MUL-H03, PILOTREL-N02, PILOTREL-H01, PILOTDEP-N01, PILOTDEP-N02, PILOTDEP-H01, PILOTOCC-H01, PILOTSUP-N01, PILOTSUP-N02, PILOTSUP-H01, PILOTORI-N02, PILOTORI-H01, PILOTYAW-N01, PILOTYAW-N02, PILOTYAW-H01, PILOTMUL-H01
- **t2i_blender (8)**: ABS-D01, YAW-D04, YAW-D07, YAW-D08, MUL-H01, MUL-H03, PILOTREL-H01, PILOTYAW-H01
