import { existsSync, readFileSync, writeFileSync } from "node:fs";

const sampleDir = "generated/zimage_turbo_1024";
const samples = loadSamples(new URL(`./${sampleDir}/samples_manifest.jsonl`, import.meta.url));

const aliases = {
  barrel: "barrel",
  bench: "bench",
  bookshelf: "bookshelf",
  bowl: "bowl",
  cabinet: "cabinet",
  camera: "camera",
  chair: "chair",
  coffee_table: "coffee table",
  crate: "crate",
  cup_set: "cup set",
  desk: "desk",
  lamp: "lamp",
  laptop: "laptop",
  metal_shelves: "metal shelves",
  nightstand: "nightstand",
  office_desk: "office desk",
  payphone: "payphone",
  plate: "plate",
  potted_plant: "potted plant",
  round_table: "round table",
  shelf: "shelf",
  side_table: "side table",
  sofa: "sofa",
  suitcase: "suitcase",
  table: "table",
  tv: "television",
  vase: "vase",
  video_camera: "video camera",
  wet_floor_sign: "wet floor sign",
};

const aliasesZh = {
  barrel: "木桶",
  bench: "长凳",
  bookshelf: "书架",
  bowl: "碗",
  cabinet: "柜子",
  camera: "相机",
  chair: "椅子",
  coffee_table: "茶几",
  crate: "木箱",
  cup_set: "杯具",
  desk: "书桌",
  lamp: "台灯",
  laptop: "笔记本电脑",
  metal_shelves: "金属货架",
  nightstand: "床头柜",
  office_desk: "办公桌",
  payphone: "公用电话",
  plate: "盘子",
  potted_plant: "盆栽",
  round_table: "圆桌",
  shelf: "架子",
  side_table: "边几",
  sofa: "沙发",
  suitcase: "行李箱",
  table: "桌子",
  tv: "电视",
  vase: "花瓶",
  video_camera: "摄像机",
  wet_floor_sign: "小心地滑标志",
};

const promptZh = {
  ABS01: "一把椅子放在空房间的左侧。",
  ABS02: "一张沙发放在空房间的右侧。",
  ABS03: "一台电视放在空房间的中央。",
  ABS04: "一张茶几放在空房间的中央。",
  ABS05: "一个书架放在空房间的左侧。",
  ABS06: "一个行李箱放在空房间的右侧。",
  REL01: "一把椅子在一张桌子的左侧。",
  REL02: "一张沙发在一个书架的右侧。",
  REL03: "在办公桌上，一台笔记本电脑放在一盏台灯的左侧。",
  REL04: "一个花瓶放在沙发和茶几之间。",
  REL05: "一台电视在一个柜子的右侧。",
  REL06: "一个行李箱在长凳左侧，一盆盆栽在长凳右侧。",
  REL07: "一张边几在沙发右侧。",
  REL08: "沙发在茶几左侧，椅子在茶几右侧，行李箱在沙发左侧，柜子在椅子右侧，书架在柜子右侧。",
  REL09: "在办公桌上，笔记本电脑位于左侧台灯和右侧花瓶之间，一把椅子放在桌子前方。",
  REL10: "柜子位于左侧书架和右侧椅子之间；行李箱在书架和柜子的左侧，盆栽在椅子右侧。",
  DEP01: "一把椅子在沙发前方。",
  DEP02: "一张茶几在沙发前方。",
  DEP03: "一个行李箱在柜子前方。",
  DEP04: "一个木桶在木箱后方。",
  DEP05: "一盆盆栽在长凳后方。",
  DEP06: "一张桌子在椅子后方。",
  DEP07: "一个木箱在金属货架前方。",
  DEP08: "椅子在茶几前方，椅子和茶几都在沙发前方，沙发在柜子和书架前方。",
  DEP09: "木箱和行李箱在长凳前方，木桶在长凳后方，金属货架在木桶后方。",
  DEP10: "行李箱和椅子在桌子前方，沙发和柜子在桌子后方。",
  OCC01: "一盆较高的盆栽部分遮挡住一个柜子。",
  OCC02: "一个行李箱部分遮挡住一张沙发。",
  OCC03: "一张长凳部分遮挡住一个书架。",
  OCC04: "一个木箱部分遮挡住一个木桶。",
  OCC05: "一把椅子部分遮挡住一张茶几。",
  OCC06: "一个行李箱部分遮挡住一个柜子。",
  OCC07: "一盆盆栽部分遮挡住一个书架。",
  OCC08: "一盆盆栽部分遮挡住柜子；行李箱在柜子前方，沙发在柜子左侧且位于行李箱后方，椅子在柜子右侧。",
  OCC09: "一个木箱部分遮挡住木桶；行李箱在木箱左侧，长凳在木箱右侧，金属货架在木桶后方。",
  OCC10: "一把椅子部分遮挡住茶几；沙发在茶几后方，行李箱在椅子左侧，柜子在椅子右侧。",
  SUP01: "一个花瓶放在茶几上。",
  SUP02: "一台笔记本电脑放在办公桌上。",
  SUP03: "一个碗放在边几上。",
  SUP04: "一盏台灯放在床头柜上。",
  SUP05: "一台电视放在柜子上。",
  SUP06: "一个盘子放在桌子上。",
  SUP07: "一套杯具放在圆桌上。",
  SUP08: "在同一张办公桌上，笔记本电脑、台灯、花瓶、杯具和盘子都放在桌面上。",
  SUP09: "花瓶在茶几上，台灯在床头柜上，电视在柜子上，笔记本电脑在办公桌上，碗在边几上。",
  SUP10: "在同一张桌子上，笔记本电脑、台灯、花瓶、碗和盘子都放在桌面上。",
  ORI01: "一台电视正面朝向画面，屏幕清晰可见。",
  ORI02: "一个柜子正面朝向画面，柜门清晰可见。",
  ORI03: "一盏台灯朝向画面左侧。",
  ORI04: "一台打开的笔记本电脑放在书桌上，屏幕清晰可见。",
  ORI05: "一把椅子朝画面左侧倾斜摆放。",
  ORI06: "一张沙发朝画面右侧倾斜摆放。",
  ORI07: "一个书架正面朝向画面，开放的正面清晰可见。",
  ORI08: "在办公桌上，一台打开的笔记本电脑屏幕清晰可见；台灯在笔记本右侧，椅子在桌子前方，沙发在椅子后方。",
  ORI09: "一台电视放在柜子上，屏幕清晰可见；沙发在柜子左侧，椅子在柜子右侧，茶几在柜子前方。",
  ORI10: "一个书架正面清晰可见；柜子在书架右侧，椅子在柜子前方，行李箱在椅子左侧，盆栽在柜子右侧。",
  ROT01: "一台电视在画面中向左旋转约 30 度。",
  ROT02: "一把椅子在画面中向右旋转约 45 度。",
  ROT03: "一台放在书桌上的笔记本电脑顺时针旋转约 90 度。",
  ROT04: "一张沙发在画面中略微向左旋转。",
  ROT05: "一个柜子在画面中向右旋转约 30 度。",
  ROT06: "一个书架在画面中向左旋转约 45 度。",
  ROT07: "一张长凳在画面中向左旋转约 45 度。",
  ROT08: "在办公桌上，笔记本电脑顺时针旋转约 90 度；台灯在笔记本右侧，花瓶在笔记本前方。",
  ROT09: "一把椅子向右旋转约 45 度，一张沙发略微向左旋转；茶几位于它们之间，行李箱在椅子前方。",
  ROT10: "一台电视向左旋转约 45 度并放在柜子上；椅子在柜子前方，沙发在柜子左侧，行李箱在柜子右侧。",
  MUL01: "一个花瓶放在茶几上，茶几在沙发前方。",
  MUL02: "一张长凳在书架前方，一个行李箱在长凳右侧。",
  MUL03: "在办公桌上，一套杯具放在笔记本电脑前方。",
  MUL04: "一台电视放在柜子上，屏幕清晰可见；一把椅子在柜子前方。",
  MUL05: "一个碗放在边几上，一盏台灯在边几左侧。",
  MUL06: "一台电视放在柜子上，屏幕清晰可见。",
  MUL07: "一个行李箱在长凳前方，一盆盆栽在长凳右侧。",
  MUL08: "沙发在茶几后方，椅子在茶几左侧，行李箱在茶几右侧；屏幕可见的电视在沙发后方，盆栽部分遮挡住电视。",
  MUL09: "木箱在木桶前方，柜子在木桶后方；行李箱在木箱左侧，长凳在木箱右侧，盆栽部分遮挡住柜子。",
  MUL10: "在办公桌上，打开的笔记本电脑屏幕清晰可见；花瓶在笔记本右侧，台灯在笔记本左侧，椅子在桌子前方。",
};

const relationText = {
  absolute_location: "located at",
  above: "above",
  below: "below",
  behind: "behind",
  face: "facing",
  in_front: "in front of",
  inside: "inside",
  left_of: "left of",
  on_top: "on top of",
  partially_occludes: "partially occluding",
  right_of: "right of",
  rotate_yaw: "rotated as requested",
  same_surface: "on the same surface as",
  under: "under",
};

const zhRelationText = {
  absolute_location: "位于",
  above: "在上方",
  below: "在下方",
  behind: "在后方",
  face: "朝向",
  in_front: "在前方",
  inside: "在内部",
  left_of: "在左侧",
  on_top: "在上面",
  partially_occludes: "部分遮挡",
  right_of: "在右侧",
  rotate_yaw: "按要求旋转",
  same_surface: "在同一表面",
  under: "在下方",
};

const checkTypeByRelation = {
  absolute_location: "absolute_location",
  behind: "depth",
  face: "orientation",
  in_front: "depth",
  inside: "support",
  on_top: "support",
  partially_occludes: "occlusion",
  rotate_yaw: "rotation",
  same_surface: "support",
  under: "support",
};

const cases = [
  c("ABS01", "absolute_location_2d", "simple", "simple_left", "A chair is placed on the left side of a plain room.", [
    o("chair", "subject"),
  ], [r("chair", "absolute_location", "", "left side")]),
  c("ABS02", "absolute_location_2d", "simple", "simple_right", "A sofa is placed on the right side of a plain room.", [
    o("sofa", "subject"),
  ], [r("sofa", "absolute_location", "", "right side")]),
  c("ABS03", "absolute_location_2d", "simple", "simple_center", "A television is centered in a plain room.", [
    o("tv", "subject"),
  ], [r("tv", "absolute_location", "", "center")]),
  c("ABS04", "absolute_location_2d", "simple", "simple_center_table", "A coffee table is centered in a plain room.", [
    o("coffee_table", "subject"),
  ], [r("coffee_table", "absolute_location", "", "center")]),
  c("ABS05", "absolute_location_2d", "simple", "simple_left_bookshelf", "A bookshelf is placed on the left side of a plain room.", [
    o("bookshelf", "subject"),
  ], [r("bookshelf", "absolute_location", "", "left side")]),
  c("ABS06", "absolute_location_2d", "simple", "simple_right_suitcase", "A suitcase is placed on the right side of a plain room.", [
    o("suitcase", "subject"),
  ], [r("suitcase", "absolute_location", "", "right side")]),

  c("REL01", "relative_position_2d", "normal", "large_pair_left_right", "A chair is to the left of a table.", [
    o("chair", "subject"),
    o("table", "object"),
  ], [r("chair", "left_of", "table")]),
  c("REL02", "relative_position_2d", "normal", "large_pair_left_right", "A sofa is to the right of a bookshelf.", [
    o("sofa", "subject"),
    o("bookshelf", "object"),
  ], [r("sofa", "right_of", "bookshelf")]),
  c("REL03", "relative_position_2d", "normal", "small_objects_on_surface", "On an office desk, a laptop is to the left of a lamp.", [
    o("office_desk", "support"),
    o("laptop", "subject"),
    o("lamp", "object"),
  ], [r("laptop", "on_top", "office_desk"), r("lamp", "on_top", "office_desk"), r("laptop", "left_of", "lamp")]),
  c("REL04", "relative_position_2d", "normal", "object_between_large_anchors", "A vase is between a sofa and a coffee table.", [
    o("vase", "subject"),
    o("sofa", "object"),
    o("coffee_table", "object"),
  ], [r("sofa", "left_of", "vase"), r("coffee_table", "right_of", "vase")]),
  c("REL05", "relative_position_2d", "normal", "large_pair_left_right", "A television is to the right of a cabinet.", [
    o("tv", "subject"),
    o("cabinet", "object"),
  ], [r("tv", "right_of", "cabinet")]),
  c("REL06", "relative_position_2d", "normal", "two_side_anchors", "A suitcase is to the left of a bench, and a potted plant is to the right of the bench.", [
    o("suitcase", "subject"),
    o("bench", "object"),
    o("potted_plant", "object"),
  ], [r("suitcase", "left_of", "bench"), r("potted_plant", "right_of", "bench")]),
  c("REL07", "relative_position_2d", "normal", "side_table_pair", "A side table is to the right of a sofa.", [
    o("side_table", "subject"),
    o("sofa", "object"),
  ], [r("side_table", "right_of", "sofa")]),
  c("REL08", "relative_position_2d", "hard", "five_pair_room_layout", "A sofa is left of a coffee table, a chair is right of the coffee table, a suitcase is left of the sofa, a cabinet is right of the chair, and a bookshelf is right of the cabinet.", [
    o("sofa", "subject"),
    o("coffee_table", "object"),
    o("chair", "object"),
    o("suitcase", "object"),
    o("cabinet", "object"),
    o("bookshelf", "object"),
  ], [r("sofa", "left_of", "coffee_table"), r("chair", "right_of", "coffee_table"), r("suitcase", "left_of", "sofa"), r("cabinet", "right_of", "chair"), r("bookshelf", "right_of", "cabinet")]),
  c("REL09", "relative_position_2d", "hard", "desk_grid_layout", "On an office desk, a laptop is between a lamp on the left and a vase on the right, and a chair is in front of the desk.", [
    o("office_desk", "support"),
    o("laptop", "subject"),
    o("lamp", "object"),
    o("vase", "object"),
    o("chair", "object"),
  ], [r("laptop", "on_top", "office_desk"), r("lamp", "on_top", "office_desk"), r("vase", "on_top", "office_desk"), r("lamp", "left_of", "laptop"), r("vase", "right_of", "laptop"), r("chair", "in_front", "office_desk")]),
  c("REL10", "relative_position_2d", "hard", "wall_furniture_layout", "A cabinet is between a bookshelf on the left and a chair on the right, a suitcase is left of the bookshelf and the cabinet, and a potted plant is right of the chair.", [
    o("cabinet", "subject"),
    o("bookshelf", "object"),
    o("chair", "object"),
    o("suitcase", "object"),
    o("potted_plant", "object"),
  ], [r("bookshelf", "left_of", "cabinet"), r("chair", "right_of", "cabinet"), r("suitcase", "left_of", "bookshelf"), r("potted_plant", "right_of", "chair"), r("suitcase", "left_of", "cabinet")]),

  c("DEP01", "depth_front_back", "normal", "large_depth_pair", "A chair is in front of a sofa.", [
    o("chair", "subject"),
    o("sofa", "object"),
  ], [r("chair", "in_front", "sofa")]),
  c("DEP02", "depth_front_back", "normal", "large_depth_pair", "A coffee table is in front of a sofa.", [
    o("coffee_table", "subject"),
    o("sofa", "object"),
  ], [r("coffee_table", "in_front", "sofa")]),
  c("DEP03", "depth_front_back", "normal", "large_depth_pair", "A suitcase is in front of a cabinet.", [
    o("suitcase", "subject"),
    o("cabinet", "object"),
  ], [r("suitcase", "in_front", "cabinet")]),
  c("DEP04", "depth_front_back", "normal", "container_depth_pair", "A barrel is behind a crate.", [
    o("barrel", "subject"),
    o("crate", "object"),
  ], [r("barrel", "behind", "crate")]),
  c("DEP05", "depth_front_back", "normal", "large_depth_pair", "A potted plant is behind a bench.", [
    o("potted_plant", "subject"),
    o("bench", "object"),
  ], [r("potted_plant", "behind", "bench")]),
  c("DEP06", "depth_front_back", "normal", "large_depth_pair", "A table is behind a chair.", [
    o("table", "subject"),
    o("chair", "object"),
  ], [r("table", "behind", "chair")]),
  c("DEP07", "depth_front_back", "normal", "storage_depth_pair", "A crate is in front of metal shelves.", [
    o("crate", "subject"),
    o("metal_shelves", "object"),
  ], [r("crate", "in_front", "metal_shelves")]),
  c("DEP08", "depth_front_back", "hard", "room_depth_layers", "A chair is in front of a coffee table, both are in front of a sofa, and the sofa is in front of a cabinet and a bookshelf.", [
    o("chair", "subject"),
    o("coffee_table", "object"),
    o("sofa", "object"),
    o("cabinet", "object"),
    o("bookshelf", "object"),
  ], [r("chair", "in_front", "coffee_table"), r("chair", "in_front", "sofa"), r("coffee_table", "in_front", "sofa"), r("sofa", "in_front", "cabinet"), r("sofa", "in_front", "bookshelf")]),
  c("DEP09", "depth_front_back", "hard", "storage_depth_layers", "A crate and a suitcase are in front of a bench, while a barrel is behind the bench and metal shelves are behind the barrel.", [
    o("crate", "subject"),
    o("suitcase", "object"),
    o("bench", "object"),
    o("barrel", "object"),
    o("metal_shelves", "object"),
  ], [r("crate", "in_front", "bench"), r("suitcase", "in_front", "bench"), r("barrel", "behind", "bench"), r("metal_shelves", "behind", "barrel"), r("bench", "in_front", "metal_shelves")]),
  c("DEP10", "depth_front_back", "hard", "living_room_depth_layers", "A suitcase and a chair are in front of a table, while a sofa and a cabinet are behind the table.", [
    o("suitcase", "subject"),
    o("chair", "object"),
    o("table", "object"),
    o("sofa", "object"),
    o("cabinet", "object"),
  ], [r("suitcase", "in_front", "table"), r("chair", "in_front", "table"), r("sofa", "behind", "table"), r("cabinet", "behind", "table"), r("table", "in_front", "sofa")]),

  c("OCC01", "occlusion_visibility", "normal", "large_occlusion", "A tall potted plant partially occludes a cabinet.", [
    o("potted_plant", "subject"),
    o("cabinet", "object"),
  ], [r("potted_plant", "partially_occludes", "cabinet")]),
  c("OCC02", "occlusion_visibility", "normal", "large_occlusion", "A suitcase partially occludes a sofa.", [
    o("suitcase", "subject"),
    o("sofa", "object"),
  ], [r("suitcase", "partially_occludes", "sofa")]),
  c("OCC03", "occlusion_visibility", "normal", "large_occlusion", "A bench partially occludes a bookshelf.", [
    o("bench", "subject"),
    o("bookshelf", "object"),
  ], [r("bench", "partially_occludes", "bookshelf")]),
  c("OCC04", "occlusion_visibility", "normal", "container_occlusion", "A crate partially occludes a barrel.", [
    o("crate", "subject"),
    o("barrel", "object"),
  ], [r("crate", "partially_occludes", "barrel")]),
  c("OCC05", "occlusion_visibility", "normal", "large_occlusion", "A chair partially occludes a coffee table.", [
    o("chair", "subject"),
    o("coffee_table", "object"),
  ], [r("chair", "partially_occludes", "coffee_table")]),
  c("OCC06", "occlusion_visibility", "normal", "large_occlusion", "A suitcase partially occludes a cabinet.", [
    o("suitcase", "subject"),
    o("cabinet", "object"),
  ], [r("suitcase", "partially_occludes", "cabinet")]),
  c("OCC07", "occlusion_visibility", "normal", "plant_bookshelf_occlusion", "A potted plant partially occludes a bookshelf.", [
    o("potted_plant", "subject"),
    o("bookshelf", "object"),
  ], [r("potted_plant", "partially_occludes", "bookshelf")]),
  c("OCC08", "occlusion_visibility", "hard", "room_occlusion_layout", "A potted plant partially occludes a cabinet, a suitcase is in front of the cabinet, a sofa is left of the cabinet and behind the suitcase, and a chair is right of the cabinet.", [
    o("potted_plant", "subject"),
    o("cabinet", "object"),
    o("suitcase", "object"),
    o("sofa", "object"),
    o("chair", "object"),
  ], [r("potted_plant", "partially_occludes", "cabinet"), r("suitcase", "in_front", "cabinet"), r("sofa", "left_of", "cabinet"), r("sofa", "behind", "suitcase"), r("chair", "right_of", "cabinet")]),
  c("OCC09", "occlusion_visibility", "hard", "storage_occlusion_layout", "A crate partially occludes a barrel, a suitcase is left of the crate, a bench is right of the crate, and metal shelves are behind the barrel.", [
    o("crate", "subject"),
    o("barrel", "object"),
    o("suitcase", "object"),
    o("bench", "object"),
    o("metal_shelves", "object"),
  ], [r("crate", "partially_occludes", "barrel"), r("suitcase", "left_of", "crate"), r("bench", "right_of", "crate"), r("metal_shelves", "behind", "barrel"), r("barrel", "in_front", "metal_shelves")]),
  c("OCC10", "occlusion_visibility", "hard", "furniture_occlusion_layout", "A chair partially occludes a coffee table, a sofa is behind the coffee table, a suitcase is left of the chair, and a cabinet is right of the chair.", [
    o("chair", "subject"),
    o("coffee_table", "object"),
    o("sofa", "object"),
    o("suitcase", "object"),
    o("cabinet", "object"),
  ], [r("chair", "partially_occludes", "coffee_table"), r("sofa", "behind", "coffee_table"), r("suitcase", "left_of", "chair"), r("cabinet", "right_of", "chair"), r("coffee_table", "in_front", "sofa")]),

  c("SUP01", "support_contact", "normal", "large_support", "A vase sits on top of a coffee table.", [
    o("vase", "subject"),
    o("coffee_table", "support"),
  ], [r("vase", "on_top", "coffee_table")]),
  c("SUP02", "support_contact", "normal", "small_support", "A laptop rests on top of an office desk.", [
    o("laptop", "subject"),
    o("office_desk", "support"),
  ], [r("laptop", "on_top", "office_desk")]),
  c("SUP03", "support_contact", "normal", "small_support", "A bowl sits on top of a side table.", [
    o("bowl", "subject"),
    o("side_table", "support"),
  ], [r("bowl", "on_top", "side_table")]),
  c("SUP04", "support_contact", "normal", "small_support", "A lamp sits on top of a nightstand.", [
    o("lamp", "subject"),
    o("nightstand", "support"),
  ], [r("lamp", "on_top", "nightstand")]),
  c("SUP05", "support_contact", "normal", "large_support", "A television sits on top of a cabinet.", [
    o("tv", "subject"),
    o("cabinet", "support"),
  ], [r("tv", "on_top", "cabinet")]),
  c("SUP06", "support_contact", "normal", "small_support", "A plate sits on top of a table.", [
    o("plate", "subject"),
    o("table", "support"),
  ], [r("plate", "on_top", "table")]),
  c("SUP07", "support_contact", "normal", "small_support", "A cup set sits on top of a round table.", [
    o("cup_set", "subject"),
    o("round_table", "support"),
  ], [r("cup_set", "on_top", "round_table")]),
  c("SUP08", "support_contact", "hard", "shared_desk_support", "On one office desk, a laptop, a lamp, a vase, a cup set, and a plate all sit on top of the desk.", [
    o("office_desk", "support"),
    o("laptop", "subject"),
    o("lamp", "object"),
    o("vase", "object"),
    o("cup_set", "object"),
    o("plate", "object"),
  ], [r("laptop", "on_top", "office_desk"), r("lamp", "on_top", "office_desk"), r("vase", "on_top", "office_desk"), r("cup_set", "on_top", "office_desk"), r("plate", "on_top", "office_desk")]),
  c("SUP09", "support_contact", "hard", "multiple_surface_support", "A vase is on a coffee table, a lamp is on a nightstand, a television is on a cabinet, a laptop is on an office desk, and a bowl is on a side table.", [
    o("vase", "subject"),
    o("coffee_table", "support"),
    o("lamp", "object"),
    o("nightstand", "support"),
    o("tv", "object"),
    o("cabinet", "support"),
    o("laptop", "object"),
    o("office_desk", "support"),
    o("bowl", "object"),
    o("side_table", "support"),
  ], [r("vase", "on_top", "coffee_table"), r("lamp", "on_top", "nightstand"), r("tv", "on_top", "cabinet"), r("laptop", "on_top", "office_desk"), r("bowl", "on_top", "side_table")]),
  c("SUP10", "support_contact", "hard", "shared_table_support", "On one table, a laptop, a lamp, a vase, a bowl, and a plate all sit on top of the table.", [
    o("table", "support"),
    o("laptop", "subject"),
    o("lamp", "object"),
    o("vase", "object"),
    o("bowl", "object"),
    o("plate", "object"),
  ], [r("laptop", "on_top", "table"), r("lamp", "on_top", "table"), r("vase", "on_top", "table"), r("bowl", "on_top", "table"), r("plate", "on_top", "table")]),

  c("ORI01", "orientation_facing", "normal", "tv_front_visible", "A television is shown front-facing with its screen clearly visible.", [
    o("tv", "subject"),
  ], [r("tv", "face", "", "front-facing", { question: "Is the television shown front-facing with its screen visible?" })]),
  c("ORI02", "orientation_facing", "normal", "cabinet_front_visible", "A cabinet is shown front-facing with its doors clearly visible.", [
    o("cabinet", "subject"),
  ], [r("cabinet", "face", "", "front-facing", { question: "Is the cabinet shown front-facing with its doors clearly visible?" })]),
  c("ORI03", "orientation_facing", "normal", "lamp_points_left", "A desk lamp points to the left side of the image.", [
    o("lamp", "subject"),
  ], [r("lamp", "face", "left_side", "points to the left side", { question: "Is the desk lamp pointing to the left side of the image?" })]),
  c("ORI04", "orientation_facing", "normal", "laptop_screen_visible", "A laptop is open on a desk with its screen clearly visible.", [
    o("laptop", "subject"),
    o("desk", "support"),
  ], [r("laptop", "on_top", "desk"), r("laptop", "face", "", "screen visible", { question: "Is the laptop open with its screen clearly visible?" })]),
  c("ORI05", "orientation_facing", "normal", "single_chair_left", "A chair is angled toward the left side of the image.", [
    o("chair", "subject"),
  ], [r("chair", "face", "left_side", "angled toward the left side", { question: "Is the chair angled toward the left side of the image?" })]),
  c("ORI06", "orientation_facing", "normal", "single_sofa_right", "A sofa is angled toward the right side of the image.", [
    o("sofa", "subject"),
  ], [r("sofa", "face", "right_side", "angled toward the right side", { question: "Is the sofa angled toward the right side of the image?" })]),
  c("ORI07", "orientation_facing", "normal", "bookshelf_front_visible", "A bookshelf is shown with its open front clearly visible.", [
    o("bookshelf", "subject"),
  ], [r("bookshelf", "face", "", "open front visible", { question: "Is the bookshelf open front clearly visible?" })]),
  c("ORI08", "orientation_facing", "hard", "desk_orientation_bundle", "On an office desk, a laptop is open with its screen clearly visible, a lamp is to the right of the laptop, a chair is in front of the desk, and a sofa is behind the chair.", [
    o("office_desk", "support"),
    o("laptop", "subject"),
    o("lamp", "object"),
    o("chair", "object"),
    o("sofa", "object"),
  ], [r("laptop", "on_top", "office_desk"), r("lamp", "on_top", "office_desk"), r("laptop", "face", "", "screen visible", { question: "Is the laptop open with its screen clearly visible?" }), r("lamp", "right_of", "laptop"), r("chair", "in_front", "office_desk"), r("sofa", "behind", "chair")]),
  c("ORI09", "orientation_facing", "hard", "tv_orientation_bundle", "A television is on a cabinet with its screen clearly visible, a sofa is left of the cabinet, a chair is right of the cabinet, and a coffee table is in front of the cabinet.", [
    o("tv", "subject"),
    o("cabinet", "support"),
    o("sofa", "object"),
    o("chair", "object"),
    o("coffee_table", "object"),
  ], [r("tv", "on_top", "cabinet"), r("tv", "face", "", "screen visible", { question: "Is the television screen clearly visible?" }), r("sofa", "left_of", "cabinet"), r("chair", "right_of", "cabinet"), r("coffee_table", "in_front", "cabinet")]),
  c("ORI10", "orientation_facing", "hard", "bookshelf_orientation_bundle", "A bookshelf is shown with its open front clearly visible, a cabinet is right of the bookshelf, a chair is in front of the cabinet, a suitcase is left of the chair, and a potted plant is right of the cabinet.", [
    o("bookshelf", "subject"),
    o("cabinet", "support"),
    o("chair", "object"),
    o("suitcase", "object"),
    o("potted_plant", "object"),
  ], [r("bookshelf", "face", "", "open front visible", { question: "Is the bookshelf open front clearly visible?" }), r("cabinet", "right_of", "bookshelf"), r("chair", "in_front", "cabinet"), r("suitcase", "left_of", "chair"), r("potted_plant", "right_of", "cabinet")]),

  c("ROT01", "rotation_yaw", "normal", "large_yaw", "A television is rotated 30 degrees to the left in the image.", [
    o("tv", "subject"),
  ], [r("tv", "rotate_yaw", "", "30 degrees to the left", { question: "Is the television rotated 30 degrees to the left in the image?" })]),
  c("ROT02", "rotation_yaw", "normal", "chair_yaw", "A chair is rotated 45 degrees to the right in the image.", [
    o("chair", "subject"),
  ], [r("chair", "rotate_yaw", "", "45 degrees to the right", { question: "Is the chair rotated 45 degrees to the right in the image?" })]),
  c("ROT03", "rotation_yaw", "normal", "small_surface_rotation", "A laptop on a desk is rotated 90 degrees clockwise in the image.", [
    o("laptop", "subject"),
    o("desk", "support"),
  ], [r("laptop", "on_top", "desk"), r("laptop", "rotate_yaw", "", "90 degrees clockwise", { question: "Is the laptop rotated 90 degrees clockwise on the desk?" })]),
  c("ROT04", "rotation_yaw", "normal", "sofa_yaw", "A sofa is rotated slightly to the left in the image.", [
    o("sofa", "subject"),
  ], [r("sofa", "rotate_yaw", "", "slightly to the left", { question: "Is the sofa rotated slightly to the left in the image?" })]),
  c("ROT05", "rotation_yaw", "normal", "cabinet_yaw", "A cabinet is rotated 30 degrees to the right in the image.", [
    o("cabinet", "subject"),
  ], [r("cabinet", "rotate_yaw", "", "30 degrees to the right", { question: "Is the cabinet rotated 30 degrees to the right in the image?" })]),
  c("ROT06", "rotation_yaw", "normal", "bookshelf_yaw", "A bookshelf is rotated 45 degrees to the left in the image.", [
    o("bookshelf", "subject"),
  ], [r("bookshelf", "rotate_yaw", "", "45 degrees to the left", { question: "Is the bookshelf rotated 45 degrees to the left in the image?" })]),
  c("ROT07", "rotation_yaw", "normal", "bench_yaw", "A bench is rotated 45 degrees to the left in the image.", [
    o("bench", "subject"),
  ], [r("bench", "rotate_yaw", "", "45 degrees to the left", { question: "Is the bench rotated 45 degrees to the left in the image?" })]),
  c("ROT08", "rotation_yaw", "hard", "desk_rotation_bundle", "On an office desk, a laptop is rotated 90 degrees clockwise, a lamp is to the right of the laptop, and a vase is in front of the laptop.", [
    o("office_desk", "support"),
    o("laptop", "subject"),
    o("lamp", "object"),
    o("vase", "object"),
  ], [r("laptop", "on_top", "office_desk"), r("lamp", "on_top", "office_desk"), r("laptop", "rotate_yaw", "", "90 degrees clockwise", { question: "Is the laptop rotated 90 degrees clockwise?" }), r("lamp", "right_of", "laptop"), r("vase", "in_front", "laptop")]),
  c("ROT09", "rotation_yaw", "hard", "furniture_rotation_bundle", "A chair is rotated 45 degrees to the right, a sofa is rotated slightly to the left, a coffee table sits between them, and a suitcase is in front of the chair.", [
    o("chair", "subject"),
    o("sofa", "object"),
    o("coffee_table", "object"),
    o("suitcase", "object"),
  ], [r("chair", "rotate_yaw", "", "45 degrees to the right", { question: "Is the chair rotated 45 degrees to the right in the image?" }), r("sofa", "rotate_yaw", "", "slightly to the left", { question: "Is the sofa rotated slightly to the left in the image?" }), r("chair", "left_of", "coffee_table"), r("sofa", "right_of", "coffee_table"), r("suitcase", "in_front", "chair")]),
  c("ROT10", "rotation_yaw", "hard", "tv_rotation_bundle", "A television is rotated 45 degrees to the left, the television sits on a cabinet, a chair is in front of the cabinet, a sofa is left of the cabinet, and a suitcase is right of the cabinet.", [
    o("tv", "subject"),
    o("cabinet", "support"),
    o("chair", "object"),
    o("sofa", "object"),
    o("suitcase", "object"),
  ], [r("tv", "rotate_yaw", "", "45 degrees to the left", { question: "Is the television rotated 45 degrees to the left in the image?" }), r("tv", "on_top", "cabinet"), r("chair", "in_front", "cabinet"), r("sofa", "left_of", "cabinet"), r("suitcase", "right_of", "cabinet")]),

  c("MUL01", "multi_relation_composition", "normal", "support_plus_depth", "A vase is on a coffee table in front of a sofa.", [
    o("vase", "subject"),
    o("coffee_table", "support"),
    o("sofa", "object"),
  ], [r("vase", "on_top", "coffee_table"), r("coffee_table", "in_front", "sofa")]),
  c("MUL02", "multi_relation_composition", "normal", "depth_plus_side", "A bench is in front of a bookshelf, and a suitcase is to the right of the bench.", [
    o("bench", "subject"),
    o("bookshelf", "object"),
    o("suitcase", "object"),
  ], [r("bench", "in_front", "bookshelf"), r("suitcase", "right_of", "bench")]),
  c("MUL03", "multi_relation_composition", "normal", "small_shared_support", "On an office desk, a cup set is in front of a laptop.", [
    o("office_desk", "support"),
    o("laptop", "subject"),
    o("cup_set", "object"),
  ], [r("laptop", "on_top", "office_desk"), r("cup_set", "on_top", "office_desk"), r("cup_set", "in_front", "laptop")]),
  c("MUL04", "multi_relation_composition", "normal", "orientation_plus_depth", "A television is on a cabinet with its screen clearly visible, and a chair is in front of the cabinet.", [
    o("tv", "subject"),
    o("cabinet", "support"),
    o("chair", "object"),
  ], [r("tv", "on_top", "cabinet"), r("tv", "face", "", "screen visible", { question: "Is the television screen clearly visible?" }), r("chair", "in_front", "cabinet")]),
  c("MUL05", "multi_relation_composition", "normal", "support_plus_side", "A bowl is on a side table, and a lamp is to the left of the side table.", [
    o("bowl", "subject"),
    o("side_table", "support"),
    o("lamp", "object"),
  ], [r("bowl", "on_top", "side_table"), r("lamp", "left_of", "side_table")]),
  c("MUL06", "multi_relation_composition", "normal", "screen_plus_support", "A television sits on a cabinet with its screen clearly visible.", [
    o("tv", "subject"),
    o("cabinet", "support"),
  ], [r("tv", "face", "", "screen visible", { question: "Is the television screen clearly visible?" }), r("tv", "on_top", "cabinet")]),
  c("MUL07", "multi_relation_composition", "normal", "depth_plus_side_simple", "A suitcase is in front of a bench, and a potted plant is to the right of the bench.", [
    o("suitcase", "subject"),
    o("bench", "object"),
    o("potted_plant", "object"),
  ], [r("suitcase", "in_front", "bench"), r("potted_plant", "right_of", "bench")]),
  c("MUL08", "multi_relation_composition", "hard", "large_room_composition", "A sofa is behind a coffee table, a chair is left of the coffee table, a suitcase is right of the coffee table, a television with its screen visible is behind the sofa, and a potted plant partially occludes the television.", [
    o("sofa", "subject"),
    o("coffee_table", "object"),
    o("chair", "object"),
    o("suitcase", "object"),
    o("tv", "object"),
    o("potted_plant", "object"),
  ], [r("sofa", "behind", "coffee_table"), r("chair", "left_of", "coffee_table"), r("suitcase", "right_of", "coffee_table"), r("tv", "face", "", "screen visible", { question: "Is the television screen clearly visible?" }), r("tv", "behind", "sofa"), r("potted_plant", "partially_occludes", "tv")]),
  c("MUL09", "multi_relation_composition", "hard", "storage_composition", "A crate is in front of a barrel, a cabinet stands behind the barrel, a suitcase is left of the crate, a bench is right of the crate, and a potted plant partially occludes the cabinet.", [
    o("crate", "subject"),
    o("barrel", "object"),
    o("cabinet", "object"),
    o("suitcase", "object"),
    o("bench", "object"),
    o("potted_plant", "object"),
  ], [r("crate", "in_front", "barrel"), r("cabinet", "behind", "barrel"), r("suitcase", "left_of", "crate"), r("bench", "right_of", "crate"), r("potted_plant", "partially_occludes", "cabinet")]),
  c("MUL10", "multi_relation_composition", "hard", "desk_composition", "On an office desk, a laptop is open with its screen visible, a vase is right of the laptop, a lamp is left of the laptop, and a chair is in front of the desk.", [
    o("office_desk", "support"),
    o("laptop", "subject"),
    o("vase", "object"),
    o("lamp", "object"),
    o("chair", "object"),
  ], [r("laptop", "on_top", "office_desk"), r("laptop", "face", "", "screen visible", { question: "Is the laptop open with its screen visible?" }), r("vase", "right_of", "laptop"), r("lamp", "left_of", "laptop"), r("chair", "in_front", "office_desk")]),
];

writeFileSync(new URL("./data/bench_cases.json", import.meta.url), JSON.stringify(cases, null, 2) + "\n");

const indexUrl = new URL("./index.html", import.meta.url);
const index = readFileSync(indexUrl, "utf8");
const updated = index.replace(
  /const CASES = .*?;\n    let filtered/s,
  `const CASES = ${JSON.stringify(cases)};\n    let filtered`,
);
if (updated === index) {
  throw new Error("Could not replace inline CASES in index.html");
}
writeFileSync(indexUrl, updated);

console.log(`wrote ${cases.length} bench cases`);

function c(id, category, level, subtype, prompt, objects, relations) {
  const checklist = [
    ...objects.map((object) => ({
      check_id: `presence:${object.canonical}`,
      type: "presence",
      subject: object.canonical,
      relation: "presence",
      target: "",
      label_zh: `图中是否出现${object.alias_zh}？`,
      label_en: `Does the image contain ${object.alias}?`,
      vqa_question: `Does the image contain ${object.alias}?`,
      vqa_question_zh: `图中是否出现${object.alias_zh}？`,
      expected_answer: "yes",
    })),
    ...relations.map(checkForRelation),
  ];
  return {
    id,
    benchmark: "spatial_prompts_v2",
    category,
    level,
    difficulty: level,
    pair_count: relations.length,
    subtype,
    prompt,
    prompt_zh: promptZh[id] || prompt,
    objects,
    relations: relations.map(relationEntry),
    checklist,
    sample: sampleFor(id, prompt),
  };
}

function sampleFor(id, prompt) {
  const record = samples.get(id);
  if (!record || record.status !== "success" || record.prompt !== prompt) {
    return {
      status: "pending",
      image: "",
      image_path: "",
      model: "",
      seed: null,
      error: record ? "sample manifest prompt mismatch; regenerate for v2 prompt" : "sample needs regeneration for v2 prompt",
    };
  }

  const relPath = `${sampleDir}/${record.image_rel_path || `${id}.png`}`;
  return {
    status: "success",
    image: relPath,
    image_path: relPath,
    model: record.model || "",
    seed: record.seed ?? null,
    error: "",
  };
}

function loadSamples(manifestUrl) {
  const out = new Map();
  if (!existsSync(manifestUrl)) return out;
  for (const line of readFileSync(manifestUrl, "utf8").split(/\n+/)) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const record = JSON.parse(trimmed);
    if (record.prompt_id) out.set(record.prompt_id, record);
  }
  return out;
}

function o(canonical, role = "object") {
  return { alias: aliases[canonical], alias_zh: aliasesZh[canonical] || aliases[canonical], canonical, role };
}

function r(subject, relation, target = "", text = relationText[relation], extra = {}) {
  return { subject, relation, target, text, ...extra };
}

function checkForRelation(rel) {
  const subject = aliases[rel.subject] || rel.subject;
  const subjectZh = aliasesZh[rel.subject] || subject;
  const target = aliases[rel.target] || rel.target || rel.text;
  const targetZh = rel.target ? (aliasesZh[rel.target] || target) : zhRegion(rel.text);
  const question = rel.question || relationQuestionEn(rel, subject, target);
  const questionZh = relationQuestionZh(rel, subjectZh, targetZh);
  return {
    check_id: `${rel.relation}:${rel.subject}:${rel.target || slug(rel.text)}`,
    type: checkTypeByRelation[rel.relation] || "relation",
    subject: rel.subject,
    relation: rel.relation,
    target: rel.target || "",
    label_zh: questionZh,
    pair_zh: relationPhraseZh(rel, subjectZh, targetZh),
    label_en: question,
    vqa_question: question,
    vqa_question_zh: questionZh,
    expected_answer: "yes",
    source: "prompt_relation",
  };
}

function relationQuestionEn(rel, subject, target) {
  const s = withArticle(subject);
  const t = withArticle(target);
  switch (rel.relation) {
    case "absolute_location":
      return `Is ${s} ${target === "center" ? "in the center of" : `on the ${target} of`} the image?`;
    case "left_of":
      return `Is ${s} to the left of ${t}?`;
    case "right_of":
      return `Is ${s} to the right of ${t}?`;
    case "in_front":
      return `Is ${s} in front of ${t}?`;
    case "behind":
      return `Is ${s} behind ${t}?`;
    case "on_top":
      return `Is ${s} on top of ${t}?`;
    case "partially_occludes":
      return `Is ${s} partially blocking ${t}?`;
    case "same_surface":
      return `Is ${s} on the same surface as ${t}?`;
    case "inside":
      return `Is ${s} inside ${t}?`;
    case "under":
      return `Is ${s} under ${t}?`;
    case "rotate_yaw":
    case "face":
      return `Is ${s} ${relationText[rel.relation]} ${target}?`;
    default:
      return `Is ${s} ${relationText[rel.relation] || rel.relation} ${t}?`;
  }
}

function relationQuestionZh(rel, subject, target) {
  switch (rel.relation) {
    case "absolute_location":
      return `${subject}是否位于画面${target}？`;
    case "left_of":
      return `${subject}是否在${target}的左侧？`;
    case "right_of":
      return `${subject}是否在${target}的右侧？`;
    case "in_front":
      return `${subject}是否在${target}的前方？`;
    case "behind":
      return `${subject}是否在${target}的后方？`;
    case "on_top":
      return `${subject}是否放在${target}上？`;
    case "partially_occludes":
      return `${subject}是否部分遮挡住${target}？`;
    case "face":
      return faceQuestionZh(rel, subject);
    case "rotate_yaw":
      return `${subject}是否${zhRegion(rel.text)}？`;
    case "same_surface":
      return `${subject}是否和${target}在同一表面上？`;
    case "inside":
      return `${subject}是否在${target}里面？`;
    case "under":
      return `${subject}是否在${target}下方？`;
    default:
      return `${subject}是否满足关系：${rel.relation} ${target}？`;
  }
}

function relationPhraseZh(rel, subject, target) {
  switch (rel.relation) {
    case "absolute_location":
      return `${subject}位于画面${target}`;
    case "left_of":
      return `${subject}在${target}左侧`;
    case "right_of":
      return `${subject}在${target}右侧`;
    case "in_front":
      return `${subject}在${target}前方`;
    case "behind":
      return `${subject}在${target}后方`;
    case "on_top":
      return `${subject}放在${target}上`;
    case "partially_occludes":
      return `${subject}部分遮挡${target}`;
    case "face":
      return facePhraseZh(rel, subject);
    case "rotate_yaw":
      return `${subject}${zhRegion(rel.text)}`;
    default:
      return `${subject} ${rel.relation} ${target}`;
  }
}

function faceQuestionZh(rel, subject) {
  if (rel.text.includes("screen visible")) return `${subject}的屏幕是否清晰可见？`;
  if (rel.text.includes("doors clearly visible")) return `${subject}的正面柜门是否清晰可见？`;
  if (rel.text.includes("open front")) return `${subject}的开放正面是否清晰可见？`;
  if (rel.text.includes("left side")) return `${subject}是否朝向画面左侧？`;
  if (rel.text.includes("right side")) return `${subject}是否朝向画面右侧？`;
  if (rel.text.includes("front-facing")) return `${subject}是否正面朝向画面？`;
  return `${subject}的朝向是否符合 prompt 要求？`;
}

function facePhraseZh(rel, subject) {
  if (rel.text.includes("screen visible")) return `${subject}屏幕可见`;
  if (rel.text.includes("doors clearly visible")) return `${subject}正面柜门可见`;
  if (rel.text.includes("open front")) return `${subject}开放正面可见`;
  if (rel.text.includes("left side")) return `${subject}朝向画面左侧`;
  if (rel.text.includes("right side")) return `${subject}朝向画面右侧`;
  if (rel.text.includes("front-facing")) return `${subject}正面朝向画面`;
  return `${subject}朝向符合要求`;
}

function zhRegion(value) {
  const normalized = String(value || "").replace(/_/g, " ");
  const map = {
    center: "中央",
    "left side": "左侧",
    "right side": "右侧",
    "left_side": "左侧",
    "right_side": "右侧",
    "30 degrees to the left": "向左旋转约 30 度",
    "45 degrees to the left": "向左旋转约 45 度",
    "30 degrees to the right": "向右旋转约 30 度",
    "45 degrees to the right": "向右旋转约 45 度",
    "90 degrees clockwise": "顺时针旋转约 90 度",
    "slightly to the left": "略微向左旋转",
  };
  return map[value] || map[normalized] || normalized;
}

function withArticle(name) {
  if (!name || ["left side", "right side", "center"].includes(name)) return name;
  if (name === "metal shelves") return "the metal shelves";
  return `the ${name}`;
}

function relationEntry(rel) {
  const out = {
    subject: rel.subject,
    text_span: rel.text,
    type: rel.relation,
  };
  if (rel.target) out.target = rel.target;
  if (rel.relation === "face") {
    out.type = "face";
    out.relation = "orientation";
    out.facing_intent = rel.target ? "toward_target" : "front_visible";
  }
  if (rel.relation === "rotate_yaw") {
    out.type = "rotation_yaw";
  }
  return out;
}

function slug(value) {
  return String(value || "scene").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
}
