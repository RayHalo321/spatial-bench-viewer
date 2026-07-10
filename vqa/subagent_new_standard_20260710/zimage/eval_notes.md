# Z-Image Turbo evaluation notes

All 76 original images were inspected. Answers were judged from the natural-language questions using opaque internal question numbers; output `|pos` and `|neg` keys are schema labels only.

- **ABS01:** The chair is visibly left of image center, although it is not pushed to the far edge; counted as left-side (`yes`).
- **REL04 / ORI08:** Single-seat armchairs were not counted as sofas. Their sofa presence checks are `no`, so dependent relations fail the presence gate.
- **REL10:** The suitcase overlaps the bookshelf, and the plant is almost horizontally aligned with the chair; neither requested left/right relation is visually established.
- **DEP05:** The wooden support is too cropped to distinguish a bench from a table, so bench presence is `unclear` and the relation is gated to zero.
- **DEP06:** Two chairs appear on opposite sides of the table. Both the positive and inverse depth questions are `unclear`, producing a 0.5 relation score.
- **OCC07:** The plant was counted as partially blocking the bookshelf because its leaves obscure the shelf interior and books, even though the outer frame remains visible.
- **SUP06 / SUP08:** A visible tabletop was accepted as a table; cup saucers were accepted as small plates because the presence question asks only whether a plate is visible.
- **ORI10:** The bookshelf and cabinet are fused into one open storage unit. Both direction questions are `unclear`, producing a 0.5 relation score.
- **ROT06 / ROT07:** The strong diagonal orientations were accepted as left rotations. ROT02, ROT05, ROT08, and ROT10 visibly fail their requested rotation direction or magnitude.
- **MUL03:** One mug is not a cup set; cup-set presence is `no` and its two dependent relations are gated to zero.
- **MUL09:** The cabinet is stacked above the barrel, not behind it. The plant is behind the cabinet, so the visible occlusion direction is the inverse of the requested one.
