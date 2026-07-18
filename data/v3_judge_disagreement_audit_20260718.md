# Visual adjudication vs Qwen32 disagreement audit

- Headline winner changes: 3/8
- Original-category winner changes: 7/8
- Review case entries: 37
- Method-case judge disagreements: 65
- Atomic answer disagreements: 164

## Headline metrics

| Metric | Visual leader | Qwen32 leader | Ours visual | Ours Qwen32 | Rank |
|---|---|---|---:|---:|---:|
| Presence | T2I-Blender + Qwen I2I | FLUX.1-schnell | 98.5% | 97.0% | 1 -> 2 |
| Cardinality | T2I-Blender + Qwen I2I | T2I-Blender + Qwen I2I | 97.0% | 95.9% | 1 -> 1 |
| 2D Layout | T2I-Blender + Qwen I2I | MUSES-Qwen RGB | 96.2% | 85.9% | 1 -> 5 |
| Depth / Contact / Occlusion | T2I-Blender + Qwen I2I | FLUX.1-schnell | 95.6% | 88.1% | 1 -> 2 |
| Orientation / Yaw | MUSES-Qwen RGB + Qwen I2I | MUSES-Qwen RGB + Qwen I2I | 80.4% | 80.7% | 3 -> 2 |
| Multi-Relation | T2I-Blender + Qwen I2I | T2I-Blender + Qwen I2I | 97.7% | 95.3% | 1 -> 1 |
| Spatial Macro | T2I-Blender + Qwen I2I | T2I-Blender + Qwen I2I | 92.2% | 86.6% | 1 -> 1 |
| Case Exact | T2I-Blender + Qwen I2I | T2I-Blender + Qwen I2I | 82.8% | 76.3% | 1 -> 1 |

## Original categories

- **Absolute Location**: ours 100.0% (visual rank 1) vs 83.3% (Qwen32 rank 6); review cases: ABS-D01, ABS-D02, ABS-D04.
- **Relative Position**: ours 92.3% (visual rank 2) vs 88.5% (Qwen32 rank 2); review cases: REL-N02, REL-D03, REL-N03, REL-H01, REL-H03, PILOTREL-H01.
- **Depth / Front-Back**: ours 95.0% (visual rank 2) vs 85.0% (Qwen32 rank 1); review cases: DEP-D04, DEP-D05, DEP-D07, DEP-H02, DEP-H03, PILOTDEP-H01.
- **Occlusion / Visibility**: ours 91.7% (visual rank 3) vs 83.3% (Qwen32 rank 3); review cases: OCC-D02, OCC-D07, OCC-H01, PILOTOCC-H01.
- **Support / Contact**: ours 100.0% (visual rank 1) vs 95.8% (Qwen32 rank 2); review cases: SUP-H01, SUP-H02, PILOTSUP-N02, PILOTSUP-H01.
- **Orientation / Facing**: ours 85.7% (visual rank 5) vs 71.4% (Qwen32 rank 6); review cases: ORI-N01, ORI-H01, ORI-H02, ORI-H03, PILOTORI-N01, PILOTORI-H01.
- **Yaw Direction**: ours 75.0% (visual rank 2) vs 90.0% (Qwen32 rank 1); review cases: YAW-D01, YAW-D03, YAW-D07, YAW-H01, YAW-H03, PILOTYAW-N02, PILOTYAW-H01.
- **Multi-Relation Composition**: ours 97.7% (visual rank 1) vs 95.3% (Qwen32 rank 1); review cases: MUL-H01.
