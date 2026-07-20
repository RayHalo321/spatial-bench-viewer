# Spatial Bench v3.2 Prompts (90 Cases)

`reuse` means the v3.1 image and visual judgment may be migrated after hash verification.

## absolute_location_2d

### ABS-D01 | diagnostic | reuse

A chair is positioned in the left side of the image.

一把椅子放在空房间的左侧。

### ABS-D02 | diagnostic | reuse

A sofa is positioned in the right side of the image.

一张沙发放在空房间的右侧。

### ABS-D03 | diagnostic | reuse

A television is positioned in the center of the image.

一台电视放在空房间的中央。

### ABS-D04 | diagnostic | reuse

A coffee table is positioned in the center of the image.

一张茶几放在空房间的中央。

### ABS-D05 | diagnostic | reuse

A bookshelf is positioned in the left side of the image.

一个书架放在空房间的左侧。

### ABS-D06 | diagnostic | reuse

A suitcase is positioned in the right side of the image.

一个行李箱放在空房间的右侧。

## relative_position_2d

### REL-N01 | normal | reuse

A laptop and a lamp both rest on an office desk, with the laptop to the left of the lamp.

笔记本电脑和台灯都放在办公桌上，笔记本电脑位于台灯左侧。

### REL-N02 | normal | reuse

A vase is to the right of a sofa and to the left of a coffee table.

花瓶位于沙发右侧，同时位于茶几左侧。

### REL-N03 | normal | reuse

A suitcase is to the left of a bench, and a potted plant is to the right of and behind the bench.

行李箱位于长凳左侧，盆栽位于长凳右侧并在长凳后方。

### REL-N04 | normal | reuse

A chair is to the left of a coffee table, and the coffee table is in front of a sofa.

一把椅子位于茶几左侧，茶几位于沙发前方。

### REL-N05 | normal | reuse

A laptop rests on an office desk, and a lamp stands to the right of the laptop.

一台笔记本电脑放在办公桌上，一盏灯位于笔记本电脑右侧。

### REL-N06 | normal | rerun

A chair stands to the left of a table, and a vase rests on the table.

一把椅子位于桌子左侧，一个花瓶放在桌面上。

### REL-N07 | normal | rerun

A sofa stands to the right of a bookshelf, and a coffee table is in front of the sofa.

一张沙发位于书架右侧，一张茶几位于沙发前方。

### REL-H01 | hard | reuse

On an office desk, a lamp is to the left of a laptop, and a vase is to the right of the laptop. All three rest on the desk, and a chair stands in front of the desk.

办公桌上，台灯位于笔记本电脑左侧，花瓶位于笔记本电脑右侧。三者都放在桌面上，椅子位于办公桌前方。

### REL-H02 | hard | reuse

A cabinet is to the right of a bookshelf and to the left of a chair. A suitcase is left of the bookshelf, and a potted plant is right of the chair. The cabinet is in front of the bookshelf.

柜子位于书架右侧并位于椅子左侧。行李箱位于书架左侧，盆栽位于椅子右侧。柜子位于书架前方。

### REL-H03 | hard | reuse

A sofa is to the left of a coffee table, and an armchair is to the right of the coffee table. A cabinet stands behind the coffee table, a bookshelf is to the left of the cabinet, and a potted plant is to the right of the cabinet.

一张沙发位于茶几左侧，一把扶手椅位于茶几右侧。一个柜子位于茶几后方，书架位于柜子左侧，盆栽位于柜子右侧。

### REL-H04 | hard | rerun

A coffee table stands between a sofa on its left and an armchair on its right. A cabinet is behind the coffee table, with a bookshelf to the cabinet's left and a potted plant to the cabinet's right.

茶几位于左侧的沙发与右侧的扶手椅之间。柜子位于茶几后方，书架位于柜子左侧，盆栽位于柜子右侧。

### REL-H05 | hard | rerun

On an office desk, a laptop is left of a desk lamp and a vase is right of the laptop. All three rest on the desk. A chair is in front of the office desk, and a bookshelf is behind the office desk.

办公桌上，笔记本电脑位于台灯左侧，花瓶位于笔记本电脑右侧，三者都放在桌面上。椅子位于办公桌前方，书架位于办公桌后方。

## depth_front_back

### DEP-N01 | normal | reuse

A coffee table is in front of a sofa, and a chair is to the right of the sofa.

一张茶几位于沙发前方，一把椅子位于沙发右侧。

### DEP-N02 | normal | reuse

A suitcase stands in front of and to the left of a cabinet.

一个行李箱位于柜子前方偏左的位置。

### DEP-N03 | normal | rerun

A chair is in front of a sofa, and a side table is to the right of the sofa.

一把椅子位于沙发前方，一张边桌位于沙发右侧。

### DEP-N04 | normal | rerun

A coffee table is in front of a sofa, and a potted plant is to the left of the sofa.

一张茶几位于沙发前方，一盆盆栽位于沙发左侧。

### DEP-N05 | normal | rerun

A suitcase is in front of a cabinet, and a chair is to the right of the suitcase.

一个行李箱位于柜子前方，一把椅子位于行李箱右侧。

### DEP-N06 | normal | rerun

A barrel is behind a crate, and a bench is to the left of the crate.

一个木桶位于木箱后方，一张长凳位于木箱左侧。

### DEP-N07 | normal | rerun

A table is behind a chair, and a lamp rests on the table.

一张桌子位于椅子后方，一盏灯放在桌面上。

### DEP-H01 | hard | rerun

A coffee table and a chair are in front of a sofa, with the coffee table to the chair's left. Behind the sofa, a cabinet is on the left and a bookshelf is on the right.

茶几和椅子位于沙发前方，茶几位于椅子左侧。柜子和书架位于沙发后方，柜子在左，书架在右。

### DEP-H02 | hard | reuse

A suitcase and a chair are in front of a table, with the suitcase to the left of the chair. A sofa and a cabinet are behind the table.

行李箱和椅子位于桌子前方，行李箱在椅子左侧。沙发和柜子位于桌子后方。

### DEP-H03 | hard | reuse

A sofa stands in the room. A coffee table is in front of the sofa. A chair is to the right of the coffee table and also in front of the sofa. A bookshelf stands behind the sofa, with a potted plant to the left of the bookshelf.

一张沙发位于房间内。茶几位于沙发前方。椅子位于茶几右侧，同时也位于沙发前方。书架位于沙发后方，盆栽位于书架左侧。

### DEP-H04 | hard | rerun

In an office lounge, a desk and a chair are in front of a sofa, with the chair to the desk's right. A bookshelf is behind the sofa, and a suitcase is in front of the desk.

在办公休息区，书桌和椅子位于沙发前方，椅子位于书桌右侧。书架位于沙发后方，行李箱位于书桌前方。

### DEP-H05 | hard | rerun

In a reading room, an armchair and a side table are in front of a bookshelf, with the side table to the armchair's right. A suitcase is behind the armchair, and a potted plant is to the bookshelf's left.

在阅读室中，扶手椅和边桌位于书架前方，边桌位于扶手椅右侧。行李箱位于扶手椅后方，盆栽位于书架左侧。

## occlusion_visibility

### OCC-N01 | normal | reuse

A potted plant stands to the left of a cabinet and partially blocks the cabinet, while the cabinet remains recognizable.

一盆盆栽位于柜子左侧，并部分遮挡柜子，但柜子仍可辨认。

### OCC-N02 | normal | reuse

A suitcase stands to the right of a refrigerator and partially blocks the refrigerator, while the refrigerator remains recognizable.

一个行李箱位于冰箱右侧，并部分遮挡冰箱，但冰箱仍可辨认。

### OCC-N03 | normal | rerun

A tall potted plant stands to the left of a cabinet and partially occludes it, while the cabinet remains recognizable. A side table is to the cabinet's right.

一盆较高的盆栽位于柜子左侧并部分遮挡柜子，但柜子仍可辨认。边桌位于柜子右侧。

### OCC-N04 | normal | rerun

A bench partially occludes the lower part of a bookshelf while the bookshelf remains recognizable, and a suitcase is to the bench's right.

一张长凳部分遮挡书架下部，但书架仍可辨认；一个行李箱位于长凳右侧。

### OCC-N05 | normal | rerun

A crate partially occludes a barrel while the barrel remains recognizable, and a bench is to the barrel's left.

一个木箱部分遮挡木桶，但木桶仍可辨认；一张长凳位于木桶左侧。

### OCC-N06 | normal | rerun

A suitcase partially occludes a cabinet while the cabinet remains recognizable, and a side table is to the cabinet's left.

一个行李箱部分遮挡柜子，但柜子仍可辨认；一张边桌位于柜子左侧。

### OCC-N07 | normal | rerun

A coffee table partially occludes the lower part of a sofa while the sofa remains recognizable, and a chair is to the sofa's right.

一张茶几部分遮挡沙发下部，但沙发仍可辨认；一把椅子位于沙发右侧。

### OCC-H01 | hard | rerun

A television rests on a cabinet. A sofa is in front of the cabinet, and a coffee table is in front of the sofa and partially occludes its lower part while the sofa remains recognizable. A chair is to the sofa's right.

电视放在柜子上。沙发位于柜子前方，茶几位于沙发前方并部分遮挡沙发下部，但沙发仍可辨认。椅子位于沙发右侧。

### OCC-H02 | hard | rerun

A bench is in front of a bookshelf and partially occludes its lower shelves while the bookshelf remains recognizable. A suitcase is to the bench's right, a chair is to the bench's left, and a potted plant is to the bookshelf's left.

长凳位于书架前方并部分遮挡书架下层，但书架仍可辨认。行李箱位于长凳右侧，椅子位于长凳左侧，盆栽位于书架左侧。

### OCC-H03 | hard | rerun

A chair stands in front of a cabinet and partially occludes the cabinet while the cabinet remains recognizable. A television rests on the cabinet, a sofa is to the cabinet's left, a side table is to the cabinet's right, and a coffee table is in front of the sofa.

椅子位于柜子前方并部分遮挡柜子，但柜子仍可辨认。电视放在柜子上，沙发位于柜子左侧，边桌位于柜子右侧，茶几位于沙发前方。

### OCC-H04 | hard | rerun

In a storage room, a crate is in front of a barrel and partially occludes it while the barrel remains recognizable. A suitcase is to the crate's left, a shelf is behind the barrel, and a potted plant is to the shelf's right.

在储藏室中，木箱位于木桶前方并部分遮挡木桶，但木桶仍可辨认。行李箱位于木箱左侧，货架位于木桶后方，盆栽位于货架右侧。

### OCC-H05 | hard | rerun

An armchair partially occludes a side table while the table remains recognizable. A lamp rests on the side table, a sofa is behind the armchair, a coffee table is in front of the sofa, and a vase rests on the coffee table.

扶手椅部分遮挡边桌，但边桌仍可辨认。灯放在边桌上，沙发位于扶手椅后方，茶几位于沙发前方，花瓶放在茶几上。

## support_contact

### SUP-N01 | normal | reuse

A vase rests on a side table, and a chair stands to the left of the side table.

一个花瓶放在边桌上，一把椅子位于边桌左侧。

### SUP-N02 | normal | reuse

A television sits on a cabinet, and an armchair stands in front of the cabinet.

一台电视放在柜子上，一把扶手椅位于柜子前方。

### SUP-N03 | normal | rerun

A book set rests on a bench, and a suitcase stands to the right of the bench.

一套书放在长凳上，一个行李箱位于长凳右侧。

### SUP-N04 | normal | rerun

A laptop and a desk lamp rest on an office desk, with the desk lamp to the laptop's right.

一台笔记本电脑和一盏台灯放在办公桌上，台灯位于笔记本电脑右侧。

### SUP-N05 | normal | rerun

A lantern rests on a side table, and a chair stands to the side table's left.

一盏灯笼放在边桌上，一把椅子位于边桌左侧。

### SUP-N06 | normal | rerun

A lamp rests on a nightstand, and a suitcase stands to the nightstand's right.

一盏灯放在床头柜上，一个行李箱位于床头柜右侧。

### SUP-N07 | normal | rerun

A television rests on a cabinet, and a bookshelf stands to the cabinet's left.

一台电视放在柜子上，一个书架位于柜子左侧。

### SUP-H01 | hard | reuse

A television, a vase, and a lamp rest on top of a cabinet. A sofa stands in front of the cabinet, and a chair is to the right of the sofa.

电视、花瓶和台灯放在一个柜子上。沙发位于柜子前方，椅子位于沙发右侧。

### SUP-H02 | hard | reuse

A television sits on a cabinet, and a vase rests on the flat surface of a side table. The side table is to the left of the cabinet, a sofa stands in front of the cabinet, and a bookshelf stands behind the sofa.

一台电视放在柜子上，一个花瓶放在边桌的平整桌面上。边桌位于柜子左侧，沙发位于柜子前方，书架位于沙发后方。

### SUP-H03 | hard | rerun

A laptop and a desk lamp rest on an office desk. A chair is in front of the desk, a bookshelf is behind the office desk, and a suitcase is to the bookshelf's left.

笔记本电脑和台灯放在办公桌上。椅子位于桌子前方，书架位于办公桌后方，行李箱位于书架左侧。

### SUP-H04 | hard | rerun

A lamp and an alarm clock rest on a nightstand to the right of a bed. A suitcase is in front of the bed, and a chair is to the bed's left.

灯和闹钟放在床右侧的床头柜上。行李箱位于床前方，椅子位于床左侧。

### SUP-H05 | hard | rerun

A lamp and a vase rest on a side table. The side table is to the right of a sofa, a suitcase is to the sofa's left, and a coffee table is in front of the sofa.

灯和花瓶放在边桌上。边桌位于沙发右侧，行李箱位于沙发左侧，茶几位于沙发前方。

## orientation_facing

### ORI-N01 | normal | reuse

A laptop is open on a desk with its screen side facing the camera.

一台打开的笔记本电脑放在书桌上，屏幕清晰可见。

### ORI-N02 | normal | reuse

A television sits on a cabinet, and a sofa stands in front of the cabinet facing the television.

一台电视放在柜子上，一张沙发位于柜子前方，并朝向电视。

### ORI-N03 | normal | reuse

A laptop rests on a desk with its screen facing the camera, and a lamp stands to the right of the laptop.

一台笔记本电脑放在书桌上，屏幕朝向镜头；一盏灯位于笔记本电脑右侧。

### ORI-N04 | normal | rerun

A television rests on a cabinet with its screen facing the camera and clearly visible.

一台电视放在柜子上，屏幕朝向相机并清晰可见。

### ORI-N05 | normal | rerun

A cabinet faces the camera with its front clearly visible, and a side table stands to the cabinet's left.

柜子的正面朝向相机并清晰可见，一张边桌位于柜子左侧。

### ORI-N06 | normal | rerun

A bookshelf faces the camera with its open front clearly visible, and a chair stands to its left.

书架的开放正面朝向相机并清晰可见，一把椅子位于书架左侧。

### ORI-N07 | normal | rerun

A desktop monitor and a laptop rest on an office desk, and the monitor screen faces the laptop.

台式显示器和笔记本电脑放在办公桌上，显示器屏幕朝向笔记本电脑。

### ORI-H01 | hard | reuse

A laptop and a lamp both rest on an office desk. The laptop's screen side faces the camera, and the lamp is to its right. A chair stands in front of the desk and faces the desk, while a sofa is behind the chair.

笔记本电脑和台灯都放在办公桌上。笔记本电脑的屏幕面朝向相机，台灯位于其右侧。椅子位于办公桌前方并朝向办公桌，沙发位于椅子后方。

### ORI-H02 | hard | reuse

A television rests on a cabinet. A sofa is left of the cabinet and faces the television, a chair is right of the cabinet and also faces the television, and a coffee table is in front of the cabinet.

电视放在柜子上。沙发位于柜子左侧并朝向电视，椅子位于柜子右侧且同样朝向电视，茶几位于柜子前方。

### ORI-H03 | hard | reuse

A bookshelf has its open front facing the camera. A cabinet is right of it, and a chair in front of the cabinet faces the cabinet. A suitcase is left of the chair, and a potted plant is right of the cabinet.

书架的开放正面朝向相机。柜子位于书架右侧，柜子前方的椅子朝向柜子。行李箱位于椅子左侧，盆栽位于柜子右侧。

### ORI-H04 | hard | reuse

A television sits on a cabinet. A sofa stands in front of the cabinet and faces the television. A chair is to the right of the sofa and faces away from the television. A coffee table is in front of the sofa, and a bookshelf stands to the left of the cabinet.

一台电视放在柜子上。沙发位于柜子前方并朝向电视。椅子位于沙发右侧，且背向电视。茶几位于沙发前方，书架位于柜子左侧。

### ORI-H05 | hard | rerun

An open laptop rests on an office desk, and a television rests on a cabinet to the desk's right. The laptop screen faces the television. A chair in front of the desk faces the laptop.

打开的笔记本电脑放在办公桌上，电视放在桌子右侧的柜子上。笔记本电脑屏幕朝向电视。椅子位于桌子前方并朝向笔记本电脑。

## continuous_yaw

### YAW-N01 | normal | rerun

A television rests on a cabinet. From facing the viewer, its screen turns 30 degrees toward image right while most of the screen remains visible.

电视放在柜子上。屏幕从正对观察者的位置向画面右侧转动30度，同时大部分屏幕仍然可见。

### YAW-N02 | normal | rerun

An open laptop rests on an office desk. From facing the viewer, its screen turns 60 degrees toward image left, forming a diagonal view with part of the screen visible.

打开的笔记本电脑放在办公桌上。屏幕从正对观察者的位置向画面左侧转动60度，形成仍可见部分屏幕的斜向视图。

### YAW-N03 | normal | rerun

A chair stands to the right of a coffee table. From facing the viewer, the chair's front turns 90 degrees toward image right, forming a side view.

一把椅子位于茶几右侧。椅子正面从正对观察者的位置向画面右侧转动90度，形成侧视图。

### YAW-N04 | normal | rerun

A sofa stands behind a coffee table. From facing the viewer, the sofa's open seating side turns 30 degrees toward image left while most of it remains visible.

沙发位于茶几后方。沙发的开放座面从正对观察者的位置向画面左侧转动30度，同时大部分座面仍然可见。

### YAW-N05 | normal | rerun

A cabinet stands to the left of a bookshelf. From facing the viewer, the cabinet front turns 60 degrees toward image right in a diagonal view.

柜子位于书架左侧。柜子正面从正对观察者的位置向画面右侧转动60度，形成斜向视图。

### YAW-N06 | normal | rerun

A bookshelf stands behind a chair. From facing the viewer, the bookshelf's open front turns 60 degrees toward image left in a diagonal view.

书架位于椅子后方。书架的开放正面从正对观察者的位置向画面左侧转动60度，形成斜向视图。

### YAW-N07 | normal | rerun

A refrigerator stands to the right of a side table. From facing the viewer, its door front turns 30 degrees toward image left while most of the doors remain visible.

冰箱位于边桌右侧。冰箱门正面从正对观察者的位置向画面左侧转动30度，同时大部分柜门仍然可见。

### YAW-H01 | hard | rerun

On an office desk, an open laptop is left of a desktop monitor, and a chair stands in front of the desk. Starting from directly facing the viewer, the laptop screen turns 30 degrees toward image right and the monitor screen turns 60 degrees toward image left.

办公桌上，打开的笔记本电脑位于显示器左侧，椅子位于桌子前方。笔记本屏幕和显示器屏幕都从正对观察者的位置开始，笔记本屏幕向画面右侧转动30度，显示器屏幕向画面左侧转动60度。

### YAW-H02 | hard | rerun

A sofa is left of a coffee table, and a chair is right of the coffee table. A cabinet stands behind the coffee table with a television on top. Starting from directly facing the viewer, the sofa front turns 30 degrees toward image left and the chair front turns 60 degrees toward image right.

沙发位于茶几左侧，椅子位于茶几右侧。柜子位于茶几后方，电视放在柜子上。沙发和椅子都从正对观察者的位置开始，沙发正面向画面左侧转动30度，椅子正面向画面右侧转动60度。

### YAW-H03 | hard | rerun

A television rests on a cabinet, an armchair is in front of the cabinet, a coffee table is in front of the armchair, and a potted plant is to the cabinet's right. Starting from directly facing the viewer, the TV screen turns 30 degrees toward image right and the armchair front turns 60 degrees toward image left.

电视放在柜子上，扶手椅位于柜子前方，茶几位于扶手椅前方，盆栽位于柜子右侧。电视和扶手椅都从正对观察者的位置开始，电视屏幕向画面右侧转动30度，扶手椅正面向画面左侧转动60度。

### YAW-H04 | hard | rerun

A chair is in front of an office desk, a sofa is behind the chair, and a laptop and desk lamp rest on the desk, with the lamp to the laptop's right. Starting from directly facing the viewer, the chair front turns 90 degrees toward image right and the sofa front turns 30 degrees toward image left.

椅子位于办公桌前方，沙发位于椅子后方，笔记本电脑和台灯放在桌面上，台灯位于笔记本电脑右侧。椅子和沙发都从正对观察者的位置开始，椅子正面向画面右侧转动90度，沙发正面向画面左侧转动30度。

### YAW-H05 | hard | rerun

A cabinet is left of a bookshelf, a bench is in front of the bookshelf, a suitcase is left of the bench, and a potted plant is right of the cabinet. Starting from directly facing the viewer, the cabinet front turns 60 degrees toward image right and the bookshelf's open front turns 30 degrees toward image left.

柜子位于书架左侧，长凳位于书架前方，行李箱位于长凳左侧，盆栽位于柜子右侧。柜子和书架都从正对观察者的位置开始，柜子正面向画面右侧转动60度，书架开放正面向画面左侧转动30度。

## multi_relation_composition

### MUL-N01 | normal | reuse

A vase rests on a coffee table. The coffee table is in front of a sofa.

花瓶放在茶几上。茶几位于沙发前方。

### MUL-N02 | normal | reuse

A bench is in front of a bookshelf, and a suitcase is to the right of the bench.

一张长凳在书架前方，一个行李箱在长凳右侧。

### MUL-N03 | normal | reuse

A laptop and a mug rest on an office desk, with the mug in front of the laptop.

笔记本电脑和马克杯放在办公桌上，马克杯位于笔记本电脑前方。

### MUL-N04 | normal | reuse

A television rests on a cabinet. A chair stands in front of the cabinet and faces the television.

电视放在柜子上。椅子位于柜子前方并朝向电视。

### MUL-N05 | normal | reuse

A bowl is on a side table, and a lamp is to the left of the side table.

一个碗放在边几上，一盏台灯在边几左侧。

### MUL-N06 | normal | reuse

A television rests on a cabinet. A sofa stands in front of the cabinet and faces the television.

电视放在柜子上。沙发位于柜子前方并朝向电视。

### MUL-N07 | normal | reuse

A chair stands to the left of a bookshelf and faces the bookshelf.

一把椅子位于书架左侧，并朝向书架。

### MUL-H01 | hard | reuse

On an office desk, a laptop is open with its screen side facing the camera, a vase is right of the laptop, a lamp is left of the laptop, and a chair is in front of the desk.

在办公桌上，打开的笔记本电脑屏幕清晰可见；花瓶在笔记本右侧，台灯在笔记本左侧，椅子在桌子前方。

### MUL-H02 | hard | reuse

A laptop rests on an office desk with its screen facing the camera. A lamp stands to the right of the laptop, a chair stands in front of the desk, a bookshelf stands behind the chair, and a suitcase is to the left of the bookshelf.

一台笔记本电脑放在办公桌上，屏幕朝向镜头。一盏灯位于笔记本电脑右侧，一把椅子位于办公桌前方，一个书架位于椅子后方，一个行李箱位于书架左侧。

### MUL-H03 | hard | rerun

A television rests on a cabinet. A vase rests on a coffee table in front of a sofa. A chair is to the sofa's right and faces the television.

电视放在柜子上。花瓶放在茶几上，茶几位于沙发前方。椅子位于沙发右侧并朝向电视。

### MUL-H04 | hard | rerun

A vase rests on a coffee table in front of a sofa. A potted plant is to the sofa's left, and a chair is to the sofa's right and faces the coffee table.

花瓶放在茶几上，茶几位于沙发前方。盆栽位于沙发左侧，椅子位于沙发右侧并朝向茶几。

### MUL-H05 | hard | rerun

A television rests on a cabinet. A vase rests on a coffee table in front of a sofa. An armchair is to the sofa's right and partially occludes the cabinet while the cabinet remains recognizable.

电视放在柜子上。花瓶放在茶几上，茶几位于沙发前方。扶手椅位于沙发右侧并部分遮挡柜子，但柜子仍可辨认。
