# T2I-Blender + Qwen Direct Visual Audit

- Protocol: blind inspection of the supplied images and frozen prompt/truth only; strict unclear = fail.
- Coverage: 93/93 cases in frozen input order.
- No prior Qwen32, API, or repository scores were used.

## Validation

- Presence checks: 269/269 emitted exactly once; 266/269 passed (98.9%).
- Cardinality checks: 269/269 emitted exactly once; 262/269 passed (97.4%).
- Relation IDs: 243/243 emitted exactly once; 232/243 strict-passed (95.5%).
- Case exact: 80/93 (86.0%).
- Failed exact cases (13): REL-N02, REL-H01, DEP-H02, OCC-H01, YAW-D03, YAW-D07, YAW-H03, MUL-H03, PILOTREL-H01, PILOTOCC-H01, PILOTORI-H01, PILOTYAW-N02, PILOTYAW-H01

## Category Summary

| Category | Exact | Relation strict pass |
|---|---:|---:|
| absolute_location_2d | 6/6 (100.0%) | 6/6 (100.0%) |
| depth_front_back | 11/12 (91.7%) | 26/26 (100.0%) |
| multi_relation_composition | 12/13 (92.3%) | 42/43 (97.7%) |
| occlusion_visibility | 8/10 (80.0%) | 20/21 (95.2%) |
| orientation_facing | 9/10 (90.0%) | 36/37 (97.3%) |
| relative_position_2d | 10/13 (76.9%) | 36/38 (94.7%) |
| support_contact | 13/13 (100.0%) | 33/33 (100.0%) |
| yaw_direction | 11/16 (68.8%) | 33/39 (84.6%) |

## Difficulty Summary

| Difficulty | Exact |
|---|---:|
| diagnostic | 40/42 (95.2%) |
| normal | 24/26 (92.3%) |
| hard | 16/25 (64.0%) |
