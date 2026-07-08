# Spatial Bench Prompt Inventory - Reworked Chinese Summary

Generated: 2026-07-05

This file summarizes the current active bench prompts after the wording cleanup.

## Changes Applied

- Rewrote `ABS04-ABS06` to use clear image coordinates: bottom center, top center, lower left.
- Rewrote `DEP05-DEP06` as explicit front-to-back rows instead of awkward chained depth sentences.
- Removed `SUP03`, `SUP04`, and `SUP06` because `under` and `inside` are hard for the current bbox/placement system.
- Reworked orientation prompts to use front-facing / screen-visible wording and reduce camera-heavy cases.
- Reworked rotation prompts to say objects are rotated left/right/clockwise in the image.
- Reworked multi-relation prompts that used unnatural front-facing wording.

## Current Counts

| Category | Cases |
| --- | ---: |
| absolute_location_2d | 6 |
| relative_position_2d | 6 |
| depth_front_back | 6 |
| occlusion_visibility | 6 |
| support_contact | 3 |
| orientation_facing | 18 |
| rotation_yaw | 6 |
| multi_relation_composition | 8 |
| Total | 59 |

## Prompt List

### absolute_location_2d

| ID | Level | English prompt | 中文翻译 |
| --- | --- | --- | --- |
| ABS01 | simple | A chair is placed on the left side of a plain room. | 一把椅子放在空房间左侧。 |
| ABS02 | simple | A sofa is placed on the right side of a plain room. | 一张沙发放在空房间右侧。 |
| ABS03 | simple | A television is centered in a plain room. | 一台电视放在空房间中央。 |
| ABS04 | simple | A coffee table is near the bottom center of the image. | 一张咖啡桌位于图像下方中间附近。 |
| ABS05 | simple | A bookshelf is near the top center of the image. | 一个书架位于图像上方中间附近。 |
| ABS06 | simple | A suitcase is in the lower left corner of the image. | 一个行李箱位于图像左下角。 |

### relative_position_2d

| ID | Level | English prompt | 中文翻译 |
| --- | --- | --- | --- |
| REL01 | normal | A chair is to the left of a table. | 一把椅子在一张桌子的左侧。 |
| REL02 | normal | A sofa is to the right of a bookshelf. | 一张沙发在一个书架的右侧。 |
| REL03 | normal | On an office desk, a laptop is to the left of a lamp. | 在办公桌上，一台笔记本电脑在一盏灯的左侧。 |
| REL04 | normal | A vase is between a sofa and a coffee table. | 一个花瓶位于一张沙发和一张咖啡桌之间。 |
| REL05 | hard | A sofa is left of a coffee table, a chair is right of the coffee table, a suitcase is in front of the sofa, a potted plant is behind the chair, and a bookshelf is behind the coffee table. | 一张沙发在咖啡桌左侧，一把椅子在咖啡桌右侧，一个行李箱在沙发前方，一盆植物在椅子后方，一个书架在咖啡桌后方。 |
| REL06 | hard | A coffee table is between a sofa on the left and a chair on the right; a suitcase is left of the sofa, a cabinet is right of the chair, and a television is above the cabinet. | 一张咖啡桌位于左侧沙发和右侧椅子之间，一个行李箱在沙发左侧，一个柜子在椅子右侧，一台电视在柜子上方。 |

### depth_front_back

| ID | Level | English prompt | 中文翻译 |
| --- | --- | --- | --- |
| DEP01 | normal | A chair is in front of a sofa. | 一把椅子在沙发前方。 |
| DEP02 | normal | A coffee table is in front of a sofa. | 一张咖啡桌在沙发前方。 |
| DEP03 | normal | A suitcase is in front of a cabinet. | 一个行李箱在柜子前方。 |
| DEP04 | normal | A barrel is behind a crate. | 一个桶在一个木箱后方。 |
| DEP05 | hard | From front to back, the objects are a suitcase, a chair, a coffee table, a sofa, a bookshelf, and a cabinet. | 从前到后依次是：行李箱、椅子、咖啡桌、沙发、书架和柜子。 |
| DEP06 | hard | From front to back, the objects are a crate, a barrel, a bench, a suitcase, a potted plant, and a cabinet. | 从前到后依次是：木箱、桶、长凳、行李箱、盆栽植物和柜子。 |

### occlusion_visibility

| ID | Level | English prompt | 中文翻译 |
| --- | --- | --- | --- |
| OCC01 | normal | A tall potted plant partially occludes a cabinet. | 一盆高大的植物部分遮挡一个柜子。 |
| OCC02 | normal | A suitcase partially occludes a sofa. | 一个行李箱部分遮挡一张沙发。 |
| OCC03 | normal | On a desk, a lamp partially occludes a laptop. | 在桌子上，一盏灯部分遮挡一台笔记本电脑。 |
| OCC04 | normal | A crate partially occludes a barrel. | 一个木箱部分遮挡一个桶。 |
| OCC05 | hard | A potted plant partially occludes a cabinet, a chair partially occludes a coffee table, a suitcase is in front of the chair, a bookshelf stands behind the cabinet, and a sofa is left of the coffee table. | 一盆植物部分遮挡一个柜子，一把椅子部分遮挡一张咖啡桌，一个行李箱在椅子前方，一个书架位于柜子后方，一张沙发在咖啡桌左侧。 |
| OCC06 | hard | A crate partially occludes a barrel, a suitcase partially occludes a bench, a cabinet is behind the barrel, a chair is right of the bench, and a potted plant is left of the cabinet. | 一个木箱部分遮挡一个桶，一个行李箱部分遮挡一张长凳，一个柜子在桶后方，一把椅子在长凳右侧，一盆植物在柜子左侧。 |

### support_contact

| ID | Level | English prompt | 中文翻译 |
| --- | --- | --- | --- |
| SUP01 | normal | A vase sits on top of a coffee table. | 一个花瓶放在咖啡桌上。 |
| SUP02 | normal | A laptop rests on top of an office desk. | 一台笔记本电脑放在办公桌上。 |
| SUP05 | hard | On one large table, a laptop, a lamp, a cup set, a plate, and a clock all sit on top of the table. | 在一张大桌子上，一台笔记本电脑、一盏灯、一组杯子、一个盘子和一个钟都放在桌面上。 |

### orientation_facing

| ID | Level | English prompt | 中文翻译 |
| --- | --- | --- | --- |
| ORI01 | normal | A television is shown front-facing with its screen clearly visible. | 一台电视正面朝外，屏幕清楚可见。 |
| ORI02 | normal | A chair faces a television. | 一把椅子朝向一台电视。 |
| ORI03 | normal | A desk lamp points to the left side of the image. | 一盏台灯指向图像左侧。 |
| ORI04 | normal | A laptop is open on a desk with its screen clearly visible. | 一台笔记本电脑打开并放在桌上，屏幕清楚可见。 |
| ORI07 | normal | A chair is angled toward the left side of the image. | 一把椅子转向图像左侧。 |
| ORI08 | normal | A chair is angled toward the right side of the image. | 一把椅子转向图像右侧。 |
| ORI09 | normal | A sofa is angled toward the left side of the image. | 一张沙发转向图像左侧。 |
| ORI10 | normal | A sofa is angled toward the right side of the image. | 一张沙发转向图像右侧。 |
| ORI11 | normal | A cabinet is angled left, with its front doors visible from the left side. | 一个柜子向左转，柜门正面从左侧方向可见。 |
| ORI12 | normal | A cabinet is angled right, with its front doors visible from the right side. | 一个柜子向右转，柜门正面从右侧方向可见。 |
| ORI13 | normal | A bookshelf is angled left, with its open front visible from the left side. | 一个书架向左转，开放正面从左侧方向可见。 |
| ORI14 | normal | A bookshelf is angled right, with its open front visible from the right side. | 一个书架向右转，开放正面从右侧方向可见。 |
| ORI15 | normal | A television screen is angled toward the left side of the image. | 一台电视屏幕转向图像左侧。 |
| ORI16 | normal | A television screen is angled toward the right side of the image. | 一台电视屏幕转向图像右侧。 |
| ORI17 | normal | A laptop screen is angled toward the left side of the image. | 一台笔记本电脑屏幕转向图像左侧。 |
| ORI18 | normal | A laptop screen is angled toward the right side of the image. | 一台笔记本电脑屏幕转向图像右侧。 |
| ORI05 | hard | On an office desk, a laptop screen is angled toward the left side of the image, a lamp is to the right of the laptop, a chair is in front of the desk, and a sofa is behind the chair. | 在办公桌上，一台笔记本电脑屏幕转向图像左侧，一盏灯在笔记本电脑右侧，一把椅子在桌子前方，一张沙发在椅子后方。 |
| ORI06 | hard | A sofa faces a television, a chair also faces the television, the television is on top of a cabinet, a lamp is left of the cabinet, and a bookshelf is behind the cabinet. | 一张沙发朝向一台电视，一把椅子也朝向这台电视，电视放在柜子上，一盏灯在柜子左侧，一个书架在柜子后方。 |

### rotation_yaw

| ID | Level | English prompt | 中文翻译 |
| --- | --- | --- | --- |
| ROT01 | normal | A television is rotated 30 degrees to the left in the image. | 一台电视在图像中向左旋转 30 度。 |
| ROT02 | normal | A chair is rotated 45 degrees to the right in the image. | 一把椅子在图像中向右旋转 45 度。 |
| ROT03 | normal | A laptop on a desk is rotated 90 degrees clockwise in the image. | 桌上的一台笔记本电脑在图像中顺时针旋转 90 度。 |
| ROT04 | normal | A sofa is rotated slightly to the left in the image. | 一张沙发在图像中略微向左旋转。 |
| ROT05 | hard | On an office desk, a television is rotated 90 degrees to the left in the image, a laptop is rotated 90 degrees clockwise, and a lamp is to the right of the laptop. | 在办公桌上，一台电视在图像中向左旋转 90 度，一台笔记本电脑顺时针旋转 90 度，一盏灯在笔记本电脑右侧。 |
| ROT06 | hard | On a desk, a laptop is rotated 90 degrees clockwise in the image, a lamp is turned toward the laptop, and a clock is to the left of the laptop. | 在桌子上，一台笔记本电脑在图像中顺时针旋转 90 度，一盏灯转向笔记本电脑，一个钟在笔记本电脑左侧。 |

### multi_relation_composition

| ID | Level | English prompt | 中文翻译 |
| --- | --- | --- | --- |
| MUL01 | normal | A vase is on a coffee table in front of a sofa. | 一个花瓶放在沙发前方的咖啡桌上。 |
| MUL02 | normal | A bench is in front of a bookshelf, and a suitcase is to the right of the bench. | 一张长凳在书架前方，一个行李箱在长凳右侧。 |
| MUL03 | normal | On an office desk, a cup set is in front of a laptop. | 在办公桌上，一组杯子在笔记本电脑前方。 |
| MUL04 | normal | A television is on a cabinet with its screen clearly visible, and a chair is in front of the cabinet. | 一台电视放在柜子上，屏幕清楚可见，一把椅子在柜子前方。 |
| MUL05 | hard | A sofa is behind a coffee table, a chair is left of the coffee table, a suitcase is right of the coffee table, a television with its screen visible is behind the sofa, and a potted plant partially occludes the television. | 一张沙发在咖啡桌后方，一把椅子在咖啡桌左侧，一个行李箱在咖啡桌右侧，一台屏幕可见的电视在沙发后方，一盆植物部分遮挡电视。 |
| MUL06 | hard | A crate is in front of a barrel, a cabinet stands behind the barrel, a suitcase is left of the crate, a bench is right of the crate, and a potted plant partially occludes the cabinet. | 一个木箱在桶前方，一个柜子立在桶后方，一个行李箱在木箱左侧，一张长凳在木箱右侧，一盆植物部分遮挡柜子。 |
| MUL07 | hard | On an office desk, a laptop is open with its screen visible, a camera is right of the laptop, a lamp is left of the laptop, a cup set is in front of the laptop, and a television is behind the desk. | 在办公桌上，一台笔记本电脑打开且屏幕可见，一台相机在笔记本电脑右侧，一盏灯在笔记本电脑左侧，一组杯子在笔记本电脑前方，一台电视在桌子后方。 |
| MUL08 | hard | A video camera faces a television, both are on an office desk, a chair is in front of the desk, a cabinet is behind the television, and a suitcase is to the right of the chair. | 一台摄像机朝向一台电视，两者都在办公桌上，一把椅子在桌子前方，一个柜子在电视后方，一个行李箱在椅子右侧。 |
