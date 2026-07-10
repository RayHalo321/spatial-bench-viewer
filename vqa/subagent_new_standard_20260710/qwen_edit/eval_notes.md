# Qwen-Edit Direct evaluation notes

All 76 source images were inspected individually. Rotation cases and other direction-sensitive images were reopened at original resolution. Questions were judged in per-case opaque order before being mapped back to checklist IDs. The direct `between` questions were evaluated without an inverse.

## Ambiguous or interpretation-sensitive cases

- **REL02:** Two sofas appear on opposite sides of the bookshelf. Both directional questions are therefore `yes`, producing the protocol's inconsistent half-credit outcome.
- **REL04:** Multiple sofas and vases are present. The large foreground vase is on the coffee table rather than geometrically between a sofa and that table, so the direct `between` answer is `no`.
- **DEP08:** Chair versus coffee-table depth is mildly perspective-dependent. The chair appears slightly closer and was judged in front.
- **OCC05 / OCC06:** The visible overlap reverses the requested blocker: the coffee table blocks the chair in OCC05, and the cabinet blocks the suitcase in OCC06.
- **OCC07:** Leaves cross the bookshelf's left edge, which was counted as partial occlusion.
- **SUP09:** The bowl and vase share the low round coffee table. That surface was not counted as a distinct side table, so `presence:side_table` is `no`.
- **ORI05 / ORI06:** Facing direction was inferred from the exposed outer side and which edge appears closest. ORI05 faces left; ORI06 also faces left, contrary to its requested rightward angle.
- **ROT01-ROT10:** Yaw was judged from exposed side faces and receding edges. ROT09's chair and ROT10's television are near frontal, so neither exact 45-degree direction is supported. ROT03 and ROT08 do not show a 90-degree clockwise laptop turn.
- **MUL08:** A sofa-like form is visible only as a television reflection. It was not counted as a physical sofa in the scene.

## Presence-gate cases

The required object is visibly absent in DEP09 (`suitcase`), OCC09 (`barrel`), SUP09 (`side table`), MUL08 (`sofa`), and MUL09 (`crate`). Their dependent relation scores are zero regardless of relation answers. All reviewed ambiguities were resolvable as `yes` or `no`; no `unclear` answer remained after original-image inspection.
