# Spatial Prompt Benchmark v2 Design Table

Total: 62 prompts, 150 spatial relation pairs. Difficulty is defined by relation-pair count: `simple` is used only for lightweight absolute-location sanity checks, `normal` has fewer than 5 spatial pairs, and `hard` has 5 or more spatial pairs.

| Category | 对应空间能力 | 主要评估点 | 当前数量 | 难度设计 | Simple example | Normal example | Hard example |
|---|---|---|---:|---|---|---|---|
| `absolute_location_2d` | Object location in image regions | 物体是否出现在图像指定区域，如 left/right/center/foreground/background | 6 cases / 6 pairs | 只保留 `simple`，暂不做 hard；作为 sanity check | A chair is placed on the left side of a plain room. | - | - |
| `relative_position_2d` | 2D relative position | 两个物体在图像平面中的 left/right/above/below/between 是否正确 | 6 cases / 17 pairs | `normal`: 1-4 pairs；`hard`: >=5 pairs | - | A chair is to the left of a table. | A sofa is left of a coffee table, a chair is right of the coffee table, a suitcase is in front of the sofa, a potted plant is behind the chair, and a bookshelf is behind the coffee table. |
| `depth_front_back` | Depth, front/back | 前后关系、靠近/远离 viewer 的深度关系是否成立 | 6 cases / 14 pairs | `normal`: 单一深度关系；`hard`: 多物体深度链或混合 side/depth | - | A chair is in front of a sofa. | A bench is in front of a bookshelf, a suitcase is in front of the bench, a sofa is behind the bookshelf, a coffee table is in front of the sofa, and a chair is behind the suitcase. |
| `occlusion_visibility` | Occlusion and visibility | 遮挡主体、被遮挡物体、部分可见性是否符合 prompt | 6 cases / 16 pairs | `normal`: 单一遮挡；`hard`: 多遮挡关系并混入 depth/side relation | - | A tall potted plant partially occludes a cabinet. | A potted plant partially occludes a cabinet, a chair partially occludes a coffee table, a suitcase is in front of the chair, a bookshelf stands behind the cabinet, and a sofa is left of the coffee table. |
| `support_contact` | Support, contact, containment | on top / inside / under / same surface 等支撑与容器关系是否成立 | 6 cases / 14 pairs | `normal`: 单一 support/contact；`hard`: 多物体共享支撑面或多个支撑关系 | - | A vase sits on top of a coffee table. | On one large table, a laptop, a lamp, a cup set, a plate, and a clock all sit on top of the table. |
| `orientation_facing` | Orientation and facing direction | 物体正面、屏幕、开口或镜头是否朝向指定方向/目标 | 18 cases / 30 pairs | 重点扩充 `normal` 单物体朝向；`hard`: 朝向与位置/支撑组合 | - | A television faces the viewer. | On an office desk, a video camera faces a television, the television faces the viewer, a laptop is left of the video camera, and a lamp is right of the video camera. |
| `rotation_yaw` | Rotation and yaw angle | 物体是否按 prompt 发生水平旋转、转向或角度变化 | 6 cases / 18 pairs | `normal`: 单物体旋转；`hard`: 旋转 + 朝向 + 支撑/相对位置组合 | - | A television is rotated 30 degrees toward the left side of the room. | On an office desk, a television is rotated 90 degrees to face left, a video camera is angled toward the television, and a laptop is to the right of the video camera. |
| `multi_relation_composition` | Compositional spatial understanding | 多种空间关系是否能在同一场景中同时满足 | 8 cases / 35 pairs | `normal`: 2-3 pairs；`hard`: >=5 pairs，混合 support/depth/side/orientation/occlusion | - | A vase is on a coffee table in front of a sofa. | A sofa is behind a coffee table, a chair is left of the coffee table, a suitcase is right of the coffee table, a television faces the viewer behind the sofa, and a potted plant partially occludes the television. |

## Scoring Columns

| Score field | Meaning | Suggested aggregation |
|---|---|---|
| `presence` | Required object appears in the image | Presence pass rate |
| relation pair | One atomic spatial relation is satisfied | Pair pass rate |
| `Case Soft Score` | Average over relation pairs in one case | Good for hard cases and diagnosis |
| `Case Strict Score` | All required objects and relation pairs pass | Good for headline pass/fail |
| `Category Score` | Average case or pair score within one category | Compare spatial abilities |
| `unclear` | Ambiguous image or hard-to-judge relation | Keep separate for review; do not silently count as pass |

## Notes For Discussion

- The current prompts are enough for a pilot, but the language should be cleaned before final evaluation.
- Use one coordinate convention in v3, preferably viewer/image based wording such as "from the viewer's perspective" or "the left side of the image".
- Generation prompts can be natural, while scoring questions should stay atomic and explicit.
