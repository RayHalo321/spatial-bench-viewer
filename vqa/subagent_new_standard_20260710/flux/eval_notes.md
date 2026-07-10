# FLUX Visual Evaluation Notes

## Scope and protocol

- Image model: FLUX.
- Judge: GPT-Subagent, independent visual inspection of all 76 images.
- Each image was reviewed in an ordered category sheet; ambiguous cases were reopened at original 1024 x 1024 resolution.
- Natural-language questions were judged under opaque per-case IDs (`q001`, `q002`, ...). Schema answer keys were restored only after judging.
- Presence gating and positive/inverse scoring follow the requested new protocol exactly. `between` checks use a direct positive-only ternary question.

## Ambiguous and noteworthy cases

- `ABS05`: The bookshelf center is around the left third of the frame, so left-side placement is `yes`.
- `REL02`: Two sofas are visible; the gray sofa is clearly right of the central bookshelf, so the existential relation is `yes` despite the tan sofa on the left.
- `REL04`: The vase is visibly supported by the coffee table in front of the sofa, not between two separate objects; the direct `between` answer is `no`.
- `REL08`: The cabinet is clearly left of the chair, while the cropped foreground suitcase still has its center left of the sofa.
- `DEP08`: Original-resolution review confirms the foreground chair, then coffee table, sofa, and rear cabinet/bookshelf depth ordering.
- `DEP04`: The barrel is centered slightly behind the front edges of the flanking crates, so barrel-behind-crate is `yes`.
- `DEP10`: The sofa is heavily occluded by the chairs and table but remains identifiable from its continuous upholstered back and seat, so presence is `yes`.
- `OCC04`: The crate frame encloses and hides parts of the barrel; the barrel does not hide the crate frame.
- `OCC05`: The foreground coffee table hides the chair's lower-right area, reversing the requested occluder.
- `OCC10`: The chair hides part of the rear tabletop while the table's front edge also hides the chair's lower portion. Positive and inverse are both `yes`, yielding `0.5`.
- `SUP08`: The large white plate beneath the foreground cup is visibly distinct from the smaller saucer, so plate presence is `yes`.
- `SUP09`: No nightstand is visible, and the lamp is a floor lamp. The laptop is visible at the cropped right edge, but its office desk is not identifiable, so office-desk presence and laptop-on-desk are `unclear`; both gated relations score `0`.
- `ORI05`: The chair's front is shifted left relative to its back, supporting a leftward angle.
- `ORI06`: The sectional's open seating direction points toward the left foreground, not the right.
- `ORI08`: The lamp is right of the laptop but stands on the floor behind the desk, so lamp-on-desk is `no`.
- `ROT01`: The television's right casing is visible, supporting an approximately 30-degree left yaw.
- `ROT02`: The chair is nearly side-on and faces left, not right.
- `ROT04`: A small amount of the sofa's right exterior side is visible, supporting a slight left yaw.
- `ROT07`: The bench's right end face is visible and its long axis recedes leftward, supporting the requested left yaw.
- `ROT09`: The chair faces left. The sofa is too close to frontal to distinguish slight-left from slight-right yaw, so both sofa yaw questions are `unclear`.
- `ROT10`: The television is effectively front-facing; neither 45-degree left nor right yaw is visible.
- `MUL09`: The bench is cropped at the right edge, but its arm, seat, and continuing frame are sufficient for presence `yes` and right-of-crate `yes`.
