#!/usr/bin/env python3
"""Build the 90-case Spatial Bench v3.2 core manifest."""

from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from v3_common import validate_cases


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "data/full_93_v31_candidate_core_cases.jsonl"
OUT_PATH = ROOT / "data/full_90_v32_core_cases.jsonl"
MIGRATION_PATH = ROOT / "data/full_90_v32_migration_map.json"
PROMPTS_PATH = ROOT / "data/full_90_v32_prompts.md"
RERUN_PATH = ROOT / "data/full_90_v32_rerun_prompt_manifest.jsonl"
RERUN_IDS_PATH = ROOT / "data/full_90_v32_rerun_ids.txt"


def obj(object_id: str, canonical: str, mention: str) -> dict[str, Any]:
    return {"id": object_id, "canonical": canonical, "mention": mention}


def rel(kind: str, subject: str, target: str | None = None, *, primary: bool, frame: str, **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {"type": kind, "subject": subject, "frame": frame, "primary": primary}
    if target:
        row["target"] = target
    row.update(extra)
    return row


def semantic_hash(case: dict[str, Any]) -> str:
    payload = copy.deepcopy(case)
    payload.pop("id", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    base_rows = [json.loads(line) for line in BASE_PATH.read_text().splitlines() if line.strip()]
    base = {row["id"]: row for row in base_rows}
    cases: list[dict[str, Any]] = []
    migration: list[dict[str, Any]] = []

    def clone(source_id: str, new_id: str) -> None:
        row = copy.deepcopy(base[source_id])
        row["id"] = new_id
        cases.append(row)
        migration.append({
            "new_id": new_id,
            "source_id": source_id,
            "reuse_old_artifacts": True,
            "semantic_sha256": semantic_hash(row),
        })

    def add(
        case_id: str,
        capability: str,
        difficulty: str,
        prompt_en: str,
        prompt_zh: str,
        objects: list[dict[str, Any]],
        relations: list[dict[str, Any]],
        *,
        source_id: str | None = None,
        registered_pattern: str | None = None,
    ) -> None:
        for index, relation in enumerate(relations, 1):
            relation["id"] = f"r{index}"
        row: dict[str, Any] = {
            "schema_version": "spatial_bench_v3",
            "id": case_id,
            "subset": "compositional",
            "difficulty": difficulty,
            "focus_capability": capability,
            "prompt_en": prompt_en,
            "prompt_zh": prompt_zh,
            "objects": objects,
            "relations": relations,
        }
        if registered_pattern:
            row["registered_pattern"] = registered_pattern
        cases.append(row)
        migration.append({
            "new_id": case_id,
            "source_id": source_id,
            "reuse_old_artifacts": False,
            "semantic_sha256": semantic_hash(row),
        })

    # Absolute-location sanity checks remain unchanged.
    for index in range(1, 7):
        clone(f"ABS-D{index:02d}", f"ABS-D{index:02d}")

    # Relative position: 7 Normal + 5 Hard.
    for source, target in (
        ("REL-N01", "REL-N01"), ("REL-N02", "REL-N02"), ("REL-N03", "REL-N03"),
        ("PILOTREL-N01", "REL-N04"), ("PILOTREL-N02", "REL-N05"),
    ):
        clone(source, target)
    add(
        "REL-N06", "relative_position_2d", "normal",
        "A chair stands to the left of a table, and a vase rests on the table.",
        "一把椅子位于桌子左侧，一个花瓶放在桌面上。",
        [obj("chair_1", "chair", "chair"), obj("table_1", "table", "table"), obj("vase_1", "vase", "vase")],
        [rel("left_of", "chair_1", "table_1", primary=True, frame="image"), rel("on_top", "vase_1", "table_1", primary=False, frame="support")],
        source_id="REL-D01",
    )
    add(
        "REL-N07", "relative_position_2d", "normal",
        "A sofa stands to the right of a bookshelf, and a coffee table is in front of the sofa.",
        "一张沙发位于书架右侧，一张茶几位于沙发前方。",
        [obj("sofa_1", "sofa", "sofa"), obj("bookshelf_1", "bookshelf", "bookshelf"), obj("coffee_table_1", "coffee_table", "coffee table")],
        [rel("right_of", "sofa_1", "bookshelf_1", primary=True, frame="image"), rel("in_front", "coffee_table_1", "sofa_1", primary=False, frame="camera")],
        source_id="REL-D02",
    )
    for source, target in (("REL-H02", "REL-H01"), ("REL-H03", "REL-H02"), ("PILOTREL-H01", "REL-H03")):
        clone(source, target)
    add(
        "REL-H04", "relative_position_2d", "hard",
        "A coffee table stands between a sofa on its left and an armchair on its right. A cabinet is behind the coffee table, with a bookshelf to the cabinet's left and a potted plant to the cabinet's right.",
        "茶几位于左侧的沙发与右侧的扶手椅之间。柜子位于茶几后方，书架位于柜子左侧，盆栽位于柜子右侧。",
        [obj("sofa_1", "sofa", "sofa"), obj("coffee_table_1", "coffee_table", "coffee table"), obj("armchair_1", "armchair", "armchair"), obj("cabinet_1", "cabinet", "cabinet"), obj("bookshelf_1", "bookshelf", "bookshelf"), obj("plant_1", "potted_plant", "potted plant")],
        [rel("left_of", "sofa_1", "coffee_table_1", primary=True, frame="image"), rel("right_of", "armchair_1", "coffee_table_1", primary=True, frame="image"), rel("behind", "cabinet_1", "coffee_table_1", primary=False, frame="camera"), rel("left_of", "bookshelf_1", "cabinet_1", primary=True, frame="image"), rel("right_of", "plant_1", "cabinet_1", primary=True, frame="image")],
    )
    add(
        "REL-H05", "relative_position_2d", "hard",
        "On an office desk, a laptop is left of a desk lamp and a vase is right of the laptop. All three rest on the desk. A chair is in front of the office desk, and a bookshelf is behind the office desk.",
        "办公桌上，笔记本电脑位于台灯左侧，花瓶位于笔记本电脑右侧，三者都放在桌面上。椅子位于办公桌前方，书架位于办公桌后方。",
        [obj("office_desk_1", "office_desk", "office desk"), obj("laptop_1", "laptop", "laptop"), obj("lamp_1", "lamp", "desk lamp"), obj("vase_1", "vase", "vase"), obj("chair_1", "chair", "chair"), obj("bookshelf_1", "bookshelf", "bookshelf")],
        [rel("on_top", "laptop_1", "office_desk_1", primary=False, frame="support"), rel("on_top", "lamp_1", "office_desk_1", primary=False, frame="support"), rel("on_top", "vase_1", "office_desk_1", primary=False, frame="support"), rel("left_of", "laptop_1", "lamp_1", primary=True, frame="image"), rel("right_of", "vase_1", "laptop_1", primary=True, frame="image"), rel("in_front", "chair_1", "office_desk_1", primary=False, frame="camera"), rel("behind", "bookshelf_1", "office_desk_1", primary=False, frame="camera")],
    )

    # Depth/front-back: 7 Normal + 5 Hard.
    clone("PILOTDEP-N01", "DEP-N01")
    clone("PILOTDEP-N02", "DEP-N02")
    depth_normals = [
        ("DEP-N03", "DEP-D01", "A chair is in front of a sofa, and a side table is to the right of the sofa.", "一把椅子位于沙发前方，一张边桌位于沙发右侧。", [obj("chair_1", "chair", "chair"), obj("sofa_1", "sofa", "sofa"), obj("side_table_1", "side_table", "side table")], [rel("in_front", "chair_1", "sofa_1", primary=True, frame="camera"), rel("right_of", "side_table_1", "sofa_1", primary=False, frame="image")]),
        ("DEP-N04", "DEP-D02", "A coffee table is in front of a sofa, and a potted plant is to the left of the sofa.", "一张茶几位于沙发前方，一盆盆栽位于沙发左侧。", [obj("coffee_table_1", "coffee_table", "coffee table"), obj("sofa_1", "sofa", "sofa"), obj("plant_1", "potted_plant", "potted plant")], [rel("in_front", "coffee_table_1", "sofa_1", primary=True, frame="camera"), rel("left_of", "plant_1", "sofa_1", primary=False, frame="image")]),
        ("DEP-N05", "DEP-D03", "A suitcase is in front of a cabinet, and a chair is to the right of the suitcase.", "一个行李箱位于柜子前方，一把椅子位于行李箱右侧。", [obj("suitcase_1", "suitcase", "suitcase"), obj("cabinet_1", "cabinet", "cabinet"), obj("chair_1", "chair", "chair")], [rel("in_front", "suitcase_1", "cabinet_1", primary=True, frame="camera"), rel("right_of", "chair_1", "suitcase_1", primary=False, frame="image")]),
        ("DEP-N06", "DEP-D04", "A barrel is behind a crate, and a bench is to the left of the crate.", "一个木桶位于木箱后方，一张长凳位于木箱左侧。", [obj("barrel_1", "barrel", "barrel"), obj("crate_1", "crate", "crate"), obj("bench_1", "bench", "bench")], [rel("behind", "barrel_1", "crate_1", primary=True, frame="camera"), rel("left_of", "bench_1", "crate_1", primary=False, frame="image")]),
        ("DEP-N07", "DEP-D06", "A table is behind a chair, and a lamp rests on the table.", "一张桌子位于椅子后方，一盏灯放在桌面上。", [obj("table_1", "table", "table"), obj("chair_1", "chair", "chair"), obj("lamp_1", "lamp", "lamp")], [rel("behind", "table_1", "chair_1", primary=True, frame="camera"), rel("on_top", "lamp_1", "table_1", primary=False, frame="support")]),
    ]
    for case_id, source_id, en, zh, objects, relations in depth_normals:
        add(case_id, "depth_front_back", "normal", en, zh, objects, relations, source_id=source_id)
    add(
        "DEP-H01", "depth_front_back", "hard",
        "A coffee table and a chair are in front of a sofa, with the coffee table to the chair's left. Behind the sofa, a cabinet is on the left and a bookshelf is on the right.",
        "茶几和椅子位于沙发前方，茶几位于椅子左侧。柜子和书架位于沙发后方，柜子在左，书架在右。",
        [obj("coffee_table_1", "coffee_table", "coffee table"), obj("chair_1", "chair", "chair"), obj("sofa_1", "sofa", "sofa"), obj("cabinet_1", "cabinet", "cabinet"), obj("bookshelf_1", "bookshelf", "bookshelf")],
        [rel("in_front", "coffee_table_1", "sofa_1", primary=True, frame="camera"), rel("in_front", "chair_1", "sofa_1", primary=True, frame="camera"), rel("left_of", "coffee_table_1", "chair_1", primary=False, frame="image"), rel("behind", "cabinet_1", "sofa_1", primary=True, frame="camera"), rel("behind", "bookshelf_1", "sofa_1", primary=True, frame="camera"), rel("left_of", "cabinet_1", "bookshelf_1", primary=False, frame="image")],
        source_id="DEP-H02",
    )
    clone("DEP-H03", "DEP-H02")
    clone("PILOTDEP-H01", "DEP-H03")
    add(
        "DEP-H04", "depth_front_back", "hard",
        "In an office lounge, a desk and a chair are in front of a sofa, with the chair to the desk's right. A bookshelf is behind the sofa, and a suitcase is in front of the desk.",
        "在办公休息区，书桌和椅子位于沙发前方，椅子位于书桌右侧。书架位于沙发后方，行李箱位于书桌前方。",
        [obj("office_desk_1", "office_desk", "office desk"), obj("chair_1", "chair", "chair"), obj("sofa_1", "sofa", "sofa"), obj("bookshelf_1", "bookshelf", "bookshelf"), obj("suitcase_1", "suitcase", "suitcase")],
        [rel("in_front", "office_desk_1", "sofa_1", primary=True, frame="camera"), rel("in_front", "chair_1", "sofa_1", primary=True, frame="camera"), rel("right_of", "chair_1", "office_desk_1", primary=False, frame="image"), rel("behind", "bookshelf_1", "sofa_1", primary=True, frame="camera"), rel("in_front", "suitcase_1", "office_desk_1", primary=True, frame="camera")],
    )
    add(
        "DEP-H05", "depth_front_back", "hard",
        "In a reading room, an armchair and a side table are in front of a bookshelf, with the side table to the armchair's right. A suitcase is behind the armchair, and a potted plant is to the bookshelf's left.",
        "在阅读室中，扶手椅和边桌位于书架前方，边桌位于扶手椅右侧。行李箱位于扶手椅后方，盆栽位于书架左侧。",
        [obj("armchair_1", "armchair", "armchair"), obj("side_table_1", "side_table", "side table"), obj("bookshelf_1", "bookshelf", "bookshelf"), obj("suitcase_1", "suitcase", "suitcase"), obj("plant_1", "potted_plant", "potted plant")],
        [rel("in_front", "armchair_1", "bookshelf_1", primary=True, frame="camera"), rel("in_front", "side_table_1", "bookshelf_1", primary=True, frame="camera"), rel("right_of", "side_table_1", "armchair_1", primary=False, frame="image"), rel("behind", "suitcase_1", "armchair_1", primary=True, frame="camera"), rel("left_of", "plant_1", "bookshelf_1", primary=False, frame="image")],
    )

    # Occlusion: one readable primary overlap per Hard case.
    clone("PILOTOCC-N01", "OCC-N01")
    clone("PILOTOCC-N02", "OCC-N02")
    occ_normals = [
        ("OCC-N03", "OCC-D01", "A tall potted plant stands to the left of a cabinet and partially occludes it, while the cabinet remains recognizable. A side table is to the cabinet's right.", "一盆较高的盆栽位于柜子左侧并部分遮挡柜子，但柜子仍可辨认。边桌位于柜子右侧。", [obj("plant_1", "potted_plant", "tall potted plant"), obj("cabinet_1", "cabinet", "cabinet"), obj("side_table_1", "side_table", "side table")], [rel("left_of", "plant_1", "cabinet_1", primary=False, frame="image"), rel("partially_occludes", "plant_1", "cabinet_1", primary=True, frame="camera", occlusion_policy="partial"), rel("right_of", "side_table_1", "cabinet_1", primary=False, frame="image")]),
        ("OCC-N04", "OCC-D03", "A bench partially occludes the lower part of a bookshelf while the bookshelf remains recognizable, and a suitcase is to the bench's right.", "一张长凳部分遮挡书架下部，但书架仍可辨认；一个行李箱位于长凳右侧。", [obj("bench_1", "bench", "bench"), obj("bookshelf_1", "bookshelf", "bookshelf"), obj("suitcase_1", "suitcase", "suitcase")], [rel("partially_occludes", "bench_1", "bookshelf_1", primary=True, frame="camera", occlusion_policy="partial"), rel("right_of", "suitcase_1", "bench_1", primary=False, frame="image")]),
        ("OCC-N05", "OCC-D04", "A crate partially occludes a barrel while the barrel remains recognizable, and a bench is to the barrel's left.", "一个木箱部分遮挡木桶，但木桶仍可辨认；一张长凳位于木桶左侧。", [obj("crate_1", "crate", "crate"), obj("barrel_1", "barrel", "barrel"), obj("bench_1", "bench", "bench")], [rel("partially_occludes", "crate_1", "barrel_1", primary=True, frame="camera", occlusion_policy="partial"), rel("left_of", "bench_1", "barrel_1", primary=False, frame="image")]),
        ("OCC-N06", "OCC-D06", "A suitcase partially occludes a cabinet while the cabinet remains recognizable, and a side table is to the cabinet's left.", "一个行李箱部分遮挡柜子，但柜子仍可辨认；一张边桌位于柜子左侧。", [obj("suitcase_1", "suitcase", "suitcase"), obj("cabinet_1", "cabinet", "cabinet"), obj("side_table_1", "side_table", "side table")], [rel("partially_occludes", "suitcase_1", "cabinet_1", primary=True, frame="camera", occlusion_policy="partial"), rel("left_of", "side_table_1", "cabinet_1", primary=False, frame="image")]),
        ("OCC-N07", None, "A coffee table partially occludes the lower part of a sofa while the sofa remains recognizable, and a chair is to the sofa's right.", "一张茶几部分遮挡沙发下部，但沙发仍可辨认；一把椅子位于沙发右侧。", [obj("coffee_table_1", "coffee_table", "coffee table"), obj("sofa_1", "sofa", "sofa"), obj("chair_1", "chair", "chair")], [rel("partially_occludes", "coffee_table_1", "sofa_1", primary=True, frame="camera", occlusion_policy="partial"), rel("right_of", "chair_1", "sofa_1", primary=False, frame="image")]),
    ]
    for case_id, source_id, en, zh, objects, relations in occ_normals:
        add(case_id, "occlusion_visibility", "normal", en, zh, objects, relations, source_id=source_id)
    occ_hards = [
        ("OCC-H01", "A television rests on a cabinet. A sofa is in front of the cabinet, and a coffee table is in front of the sofa and partially occludes its lower part while the sofa remains recognizable. A chair is to the sofa's right.", "电视放在柜子上。沙发位于柜子前方，茶几位于沙发前方并部分遮挡沙发下部，但沙发仍可辨认。椅子位于沙发右侧。", [obj("tv_1", "tv", "television"), obj("cabinet_1", "cabinet", "cabinet"), obj("sofa_1", "sofa", "sofa"), obj("coffee_table_1", "coffee_table", "coffee table"), obj("chair_1", "chair", "chair")], [rel("on_top", "tv_1", "cabinet_1", primary=False, frame="support"), rel("in_front", "sofa_1", "cabinet_1", primary=False, frame="camera"), rel("in_front", "coffee_table_1", "sofa_1", primary=False, frame="camera"), rel("partially_occludes", "coffee_table_1", "sofa_1", primary=True, frame="camera", occlusion_policy="partial"), rel("right_of", "chair_1", "sofa_1", primary=False, frame="image")]),
        ("OCC-H02", "A bench is in front of a bookshelf and partially occludes its lower shelves while the bookshelf remains recognizable. A suitcase is to the bench's right, a chair is to the bench's left, and a potted plant is to the bookshelf's left.", "长凳位于书架前方并部分遮挡书架下层，但书架仍可辨认。行李箱位于长凳右侧，椅子位于长凳左侧，盆栽位于书架左侧。", [obj("bench_1", "bench", "bench"), obj("bookshelf_1", "bookshelf", "bookshelf"), obj("suitcase_1", "suitcase", "suitcase"), obj("chair_1", "chair", "chair"), obj("plant_1", "potted_plant", "potted plant")], [rel("in_front", "bench_1", "bookshelf_1", primary=False, frame="camera"), rel("partially_occludes", "bench_1", "bookshelf_1", primary=True, frame="camera", occlusion_policy="partial"), rel("right_of", "suitcase_1", "bench_1", primary=False, frame="image"), rel("left_of", "chair_1", "bench_1", primary=False, frame="image"), rel("left_of", "plant_1", "bookshelf_1", primary=False, frame="image")]),
        ("OCC-H03", "A chair stands in front of a cabinet and partially occludes the cabinet while the cabinet remains recognizable. A television rests on the cabinet, a sofa is to the cabinet's left, a side table is to the cabinet's right, and a coffee table is in front of the sofa.", "椅子位于柜子前方并部分遮挡柜子，但柜子仍可辨认。电视放在柜子上，沙发位于柜子左侧，边桌位于柜子右侧，茶几位于沙发前方。", [obj("chair_1", "chair", "chair"), obj("cabinet_1", "cabinet", "cabinet"), obj("tv_1", "tv", "television"), obj("sofa_1", "sofa", "sofa"), obj("side_table_1", "side_table", "side table"), obj("coffee_table_1", "coffee_table", "coffee table")], [rel("in_front", "chair_1", "cabinet_1", primary=False, frame="camera"), rel("partially_occludes", "chair_1", "cabinet_1", primary=True, frame="camera", occlusion_policy="partial"), rel("on_top", "tv_1", "cabinet_1", primary=False, frame="support"), rel("left_of", "sofa_1", "cabinet_1", primary=False, frame="image"), rel("right_of", "side_table_1", "cabinet_1", primary=False, frame="image"), rel("in_front", "coffee_table_1", "sofa_1", primary=False, frame="camera")]),
        ("OCC-H04", "In a storage room, a crate is in front of a barrel and partially occludes it while the barrel remains recognizable. A suitcase is to the crate's left, a shelf is behind the barrel, and a potted plant is to the shelf's right.", "在储藏室中，木箱位于木桶前方并部分遮挡木桶，但木桶仍可辨认。行李箱位于木箱左侧，货架位于木桶后方，盆栽位于货架右侧。", [obj("crate_1", "crate", "crate"), obj("barrel_1", "barrel", "barrel"), obj("suitcase_1", "suitcase", "suitcase"), obj("shelf_1", "metal_shelves", "shelf"), obj("plant_1", "potted_plant", "potted plant")], [rel("in_front", "crate_1", "barrel_1", primary=False, frame="camera"), rel("partially_occludes", "crate_1", "barrel_1", primary=True, frame="camera", occlusion_policy="partial"), rel("left_of", "suitcase_1", "crate_1", primary=False, frame="image"), rel("behind", "shelf_1", "barrel_1", primary=False, frame="camera"), rel("right_of", "plant_1", "shelf_1", primary=False, frame="image")]),
        ("OCC-H05", "An armchair partially occludes a side table while the table remains recognizable. A lamp rests on the side table, a sofa is behind the armchair, a coffee table is in front of the sofa, and a vase rests on the coffee table.", "扶手椅部分遮挡边桌，但边桌仍可辨认。灯放在边桌上，沙发位于扶手椅后方，茶几位于沙发前方，花瓶放在茶几上。", [obj("armchair_1", "armchair", "armchair"), obj("side_table_1", "side_table", "side table"), obj("lamp_1", "lamp", "lamp"), obj("sofa_1", "sofa", "sofa"), obj("coffee_table_1", "coffee_table", "coffee table"), obj("vase_1", "vase", "vase")], [rel("partially_occludes", "armchair_1", "side_table_1", primary=True, frame="camera", occlusion_policy="partial"), rel("on_top", "lamp_1", "side_table_1", primary=False, frame="support"), rel("behind", "sofa_1", "armchair_1", primary=False, frame="camera"), rel("in_front", "coffee_table_1", "sofa_1", primary=False, frame="camera"), rel("on_top", "vase_1", "coffee_table_1", primary=False, frame="support")]),
    ]
    for case_id, en, zh, objects, relations in occ_hards:
        add(case_id, "occlusion_visibility", "hard", en, zh, objects, relations)

    # Support/contact: 7 Normal + 5 Hard.
    clone("PILOTSUP-N01", "SUP-N01")
    clone("PILOTSUP-N02", "SUP-N02")
    support_normals = [
        ("SUP-N03", "SUP-D01", "A book set rests on a bench, and a suitcase stands to the right of the bench.", "一套书放在长凳上，一个行李箱位于长凳右侧。", [obj("book_set_1", "book_set", "book set"), obj("bench_1", "bench", "bench"), obj("suitcase_1", "suitcase", "suitcase")], [rel("on_top", "book_set_1", "bench_1", primary=True, frame="support"), rel("right_of", "suitcase_1", "bench_1", primary=False, frame="image")]),
        ("SUP-N04", "SUP-D02", "A laptop and a desk lamp rest on an office desk, with the desk lamp to the laptop's right.", "一台笔记本电脑和一盏台灯放在办公桌上，台灯位于笔记本电脑右侧。", [obj("laptop_1", "laptop", "laptop"), obj("office_desk_1", "office_desk", "office desk"), obj("lamp_1", "lamp", "desk lamp")], [rel("on_top", "laptop_1", "office_desk_1", primary=True, frame="support"), rel("on_top", "lamp_1", "office_desk_1", primary=True, frame="support"), rel("right_of", "lamp_1", "laptop_1", primary=False, frame="image")]),
        ("SUP-N05", "SUP-D03", "A lantern rests on a side table, and a chair stands to the side table's left.", "一盏灯笼放在边桌上，一把椅子位于边桌左侧。", [obj("lantern_1", "lantern", "lantern"), obj("side_table_1", "side_table", "side table"), obj("chair_1", "chair", "chair")], [rel("on_top", "lantern_1", "side_table_1", primary=True, frame="support"), rel("left_of", "chair_1", "side_table_1", primary=False, frame="image")]),
        ("SUP-N06", "SUP-D04", "A lamp rests on a nightstand, and a suitcase stands to the nightstand's right.", "一盏灯放在床头柜上，一个行李箱位于床头柜右侧。", [obj("lamp_1", "lamp", "lamp"), obj("nightstand_1", "nightstand", "nightstand"), obj("suitcase_1", "suitcase", "suitcase")], [rel("on_top", "lamp_1", "nightstand_1", primary=True, frame="support"), rel("right_of", "suitcase_1", "nightstand_1", primary=False, frame="image")]),
        ("SUP-N07", "SUP-D05", "A television rests on a cabinet, and a bookshelf stands to the cabinet's left.", "一台电视放在柜子上，一个书架位于柜子左侧。", [obj("tv_1", "tv", "television"), obj("cabinet_1", "cabinet", "cabinet"), obj("bookshelf_1", "bookshelf", "bookshelf")], [rel("on_top", "tv_1", "cabinet_1", primary=True, frame="support"), rel("left_of", "bookshelf_1", "cabinet_1", primary=False, frame="image")]),
    ]
    for case_id, source_id, en, zh, objects, relations in support_normals:
        add(case_id, "support_contact", "normal", en, zh, objects, relations, source_id=source_id)
    clone("SUP-H02", "SUP-H01")
    clone("PILOTSUP-H01", "SUP-H02")
    add(
        "SUP-H03", "support_contact", "hard",
        "A laptop and a desk lamp rest on an office desk. A chair is in front of the desk, a bookshelf is behind the office desk, and a suitcase is to the bookshelf's left.",
        "笔记本电脑和台灯放在办公桌上。椅子位于桌子前方，书架位于办公桌后方，行李箱位于书架左侧。",
        [obj("laptop_1", "laptop", "laptop"), obj("lamp_1", "lamp", "desk lamp"), obj("office_desk_1", "office_desk", "office desk"), obj("chair_1", "chair", "chair"), obj("bookshelf_1", "bookshelf", "bookshelf"), obj("suitcase_1", "suitcase", "suitcase")],
        [rel("on_top", "laptop_1", "office_desk_1", primary=True, frame="support"), rel("on_top", "lamp_1", "office_desk_1", primary=True, frame="support"), rel("in_front", "chair_1", "office_desk_1", primary=False, frame="camera"), rel("behind", "bookshelf_1", "office_desk_1", primary=False, frame="camera"), rel("left_of", "suitcase_1", "bookshelf_1", primary=False, frame="image")],
    )
    add(
        "SUP-H04", "support_contact", "hard",
        "A lamp and an alarm clock rest on a nightstand to the right of a bed. A suitcase is in front of the bed, and a chair is to the bed's left.",
        "灯和闹钟放在床右侧的床头柜上。行李箱位于床前方，椅子位于床左侧。",
        [obj("lamp_1", "lamp", "lamp"), obj("clock_1", "clock", "alarm clock"), obj("nightstand_1", "nightstand", "nightstand"), obj("bed_1", "bed", "bed"), obj("suitcase_1", "suitcase", "suitcase"), obj("chair_1", "chair", "chair")],
        [rel("on_top", "lamp_1", "nightstand_1", primary=True, frame="support"), rel("on_top", "clock_1", "nightstand_1", primary=True, frame="support"), rel("right_of", "nightstand_1", "bed_1", primary=False, frame="image"), rel("in_front", "suitcase_1", "bed_1", primary=False, frame="camera"), rel("left_of", "chair_1", "bed_1", primary=False, frame="image")],
    )
    add(
        "SUP-H05", "support_contact", "hard",
        "A lamp and a vase rest on a side table. The side table is to the right of a sofa, a suitcase is to the sofa's left, and a coffee table is in front of the sofa.",
        "灯和花瓶放在边桌上。边桌位于沙发右侧，行李箱位于沙发左侧，茶几位于沙发前方。",
        [obj("lamp_1", "lamp", "lamp"), obj("vase_1", "vase", "vase"), obj("side_table_1", "side_table", "side table"), obj("sofa_1", "sofa", "sofa"), obj("suitcase_1", "suitcase", "suitcase"), obj("coffee_table_1", "coffee_table", "coffee table")],
        [rel("on_top", "lamp_1", "side_table_1", primary=True, frame="support"), rel("on_top", "vase_1", "side_table_1", primary=True, frame="support"), rel("right_of", "side_table_1", "sofa_1", primary=False, frame="image"), rel("left_of", "suitcase_1", "sofa_1", primary=False, frame="image"), rel("in_front", "coffee_table_1", "sofa_1", primary=False, frame="camera")],
    )

    # Orientation/facing: retain valid difficult failures.
    for source, target in (("ORI-N01", "ORI-N01"), ("PILOTORI-N01", "ORI-N02"), ("PILOTORI-N02", "ORI-N03")):
        clone(source, target)
    add(
        "ORI-N04", "orientation_facing", "normal",
        "A television rests on a cabinet with its screen facing the camera and clearly visible.",
        "一台电视放在柜子上，屏幕朝向相机并清晰可见。",
        [obj("tv_1", "tv", "television"), obj("cabinet_1", "cabinet", "cabinet")],
        [rel("on_top", "tv_1", "cabinet_1", primary=False, frame="support"), rel("face", "tv_1", primary=True, frame="camera", facing_intent="toward_camera", facing_part="screen_side")],
        source_id="ORI-D01",
    )
    add(
        "ORI-N05", "orientation_facing", "normal",
        "A cabinet faces the camera with its front clearly visible, and a side table stands to the cabinet's left.",
        "柜子的正面朝向相机并清晰可见，一张边桌位于柜子左侧。",
        [obj("cabinet_1", "cabinet", "cabinet"), obj("side_table_1", "side_table", "side table")],
        [rel("face", "cabinet_1", primary=True, frame="camera", facing_intent="toward_camera", facing_part="front_side"), rel("left_of", "side_table_1", "cabinet_1", primary=False, frame="image")],
        source_id="ORI-D02",
    )
    add(
        "ORI-N06", "orientation_facing", "normal",
        "A bookshelf faces the camera with its open front clearly visible, and a chair stands to its left.",
        "书架的开放正面朝向相机并清晰可见，一把椅子位于书架左侧。",
        [obj("bookshelf_1", "bookshelf", "bookshelf"), obj("chair_1", "chair", "chair")],
        [rel("face", "bookshelf_1", primary=True, frame="camera", facing_intent="toward_camera", facing_part="front_side"), rel("left_of", "chair_1", "bookshelf_1", primary=False, frame="image")],
        source_id="ORI-D03",
    )
    add(
        "ORI-N07", "orientation_facing", "normal",
        "A desktop monitor and a laptop rest on an office desk, and the monitor screen faces the laptop.",
        "台式显示器和笔记本电脑放在办公桌上，显示器屏幕朝向笔记本电脑。",
        [obj("monitor_1", "computer_monitor", "desktop monitor"), obj("laptop_1", "laptop", "laptop"), obj("office_desk_1", "office_desk", "office desk")],
        [rel("on_top", "monitor_1", "office_desk_1", primary=False, frame="support"), rel("on_top", "laptop_1", "office_desk_1", primary=False, frame="support"), rel("face", "monitor_1", "laptop_1", primary=True, frame="object_target", facing_intent="toward_target", facing_part="screen_side")],
    )
    for source, target in (("ORI-H01", "ORI-H01"), ("ORI-H02", "ORI-H02"), ("ORI-H03", "ORI-H03"), ("PILOTORI-H01", "ORI-H04")):
        clone(source, target)
    add(
        "ORI-H05", "orientation_facing", "hard",
        "An open laptop rests on an office desk, and a television rests on a cabinet to the desk's right. The laptop screen faces the television. A chair in front of the desk faces the laptop.",
        "打开的笔记本电脑放在办公桌上，电视放在桌子右侧的柜子上。笔记本电脑屏幕朝向电视。椅子位于桌子前方并朝向笔记本电脑。",
        [obj("laptop_1", "laptop", "open laptop"), obj("office_desk_1", "office_desk", "office desk"), obj("tv_1", "tv", "television"), obj("cabinet_1", "cabinet", "cabinet"), obj("chair_1", "chair", "chair")],
        [rel("on_top", "laptop_1", "office_desk_1", primary=False, frame="support"), rel("on_top", "tv_1", "cabinet_1", primary=False, frame="support"), rel("right_of", "cabinet_1", "office_desk_1", primary=False, frame="image"), rel("face", "laptop_1", "tv_1", primary=True, frame="object_target", facing_intent="toward_target", facing_part="screen_side"), rel("in_front", "chair_1", "office_desk_1", primary=False, frame="camera"), rel("face", "chair_1", "laptop_1", primary=True, frame="object_target", facing_intent="toward_target", facing_part="front_side")],
    )

    # Continuous yaw: 7 Normal + 5 Hard, VLM-bin evaluation only.
    yaw_normals = [
        ("YAW-N01", "A television rests on a cabinet. From facing the viewer, its screen turns 30 degrees toward image right while most of the screen remains visible.", "电视放在柜子上。屏幕从正对观察者的位置向画面右侧转动30度，同时大部分屏幕仍然可见。", [obj("tv_1", "tv", "television"), obj("cabinet_1", "cabinet", "cabinet")], [rel("on_top", "tv_1", "cabinet_1", primary=False, frame="support"), rel("face_angle", "tv_1", primary=True, frame="image", direction="right", angle_degrees=30, angle_reference="facing_viewer", tolerance_deg=15, facing_part="screen_side")]),
        ("YAW-N02", "An open laptop rests on an office desk. From facing the viewer, its screen turns 60 degrees toward image left, forming a diagonal view with part of the screen visible.", "打开的笔记本电脑放在办公桌上。屏幕从正对观察者的位置向画面左侧转动60度，形成仍可见部分屏幕的斜向视图。", [obj("laptop_1", "laptop", "open laptop"), obj("office_desk_1", "office_desk", "office desk")], [rel("on_top", "laptop_1", "office_desk_1", primary=False, frame="support"), rel("face_angle", "laptop_1", primary=True, frame="image", direction="left", angle_degrees=60, angle_reference="facing_viewer", tolerance_deg=15, facing_part="screen_side")]),
        ("YAW-N03", "A chair stands to the right of a coffee table. From facing the viewer, the chair's front turns 90 degrees toward image right, forming a side view.", "一把椅子位于茶几右侧。椅子正面从正对观察者的位置向画面右侧转动90度，形成侧视图。", [obj("chair_1", "chair", "chair"), obj("coffee_table_1", "coffee_table", "coffee table")], [rel("right_of", "chair_1", "coffee_table_1", primary=False, frame="image"), rel("face_angle", "chair_1", primary=True, frame="image", direction="right", angle_degrees=90, angle_reference="facing_viewer", tolerance_deg=15, facing_part="front_side")]),
        ("YAW-N04", "A sofa stands behind a coffee table. From facing the viewer, the sofa's open seating side turns 30 degrees toward image left while most of it remains visible.", "沙发位于茶几后方。沙发的开放座面从正对观察者的位置向画面左侧转动30度，同时大部分座面仍然可见。", [obj("sofa_1", "sofa", "sofa"), obj("coffee_table_1", "coffee_table", "coffee table")], [rel("behind", "sofa_1", "coffee_table_1", primary=False, frame="camera"), rel("face_angle", "sofa_1", primary=True, frame="image", direction="left", angle_degrees=30, angle_reference="facing_viewer", tolerance_deg=15, facing_part="front_side")]),
        ("YAW-N05", "A cabinet stands to the left of a bookshelf. From facing the viewer, the cabinet front turns 60 degrees toward image right in a diagonal view.", "柜子位于书架左侧。柜子正面从正对观察者的位置向画面右侧转动60度，形成斜向视图。", [obj("cabinet_1", "cabinet", "cabinet"), obj("bookshelf_1", "bookshelf", "bookshelf")], [rel("left_of", "cabinet_1", "bookshelf_1", primary=False, frame="image"), rel("face_angle", "cabinet_1", primary=True, frame="image", direction="right", angle_degrees=60, angle_reference="facing_viewer", tolerance_deg=15, facing_part="front_side")]),
        ("YAW-N06", "A bookshelf stands behind a chair. From facing the viewer, the bookshelf's open front turns 60 degrees toward image left in a diagonal view.", "书架位于椅子后方。书架的开放正面从正对观察者的位置向画面左侧转动60度，形成斜向视图。", [obj("bookshelf_1", "bookshelf", "bookshelf"), obj("chair_1", "chair", "chair")], [rel("behind", "bookshelf_1", "chair_1", primary=False, frame="camera"), rel("face_angle", "bookshelf_1", primary=True, frame="image", direction="left", angle_degrees=60, angle_reference="facing_viewer", tolerance_deg=15, facing_part="front_side")]),
        ("YAW-N07", "A refrigerator stands to the right of a side table. From facing the viewer, its door front turns 30 degrees toward image left while most of the doors remain visible.", "冰箱位于边桌右侧。冰箱门正面从正对观察者的位置向画面左侧转动30度，同时大部分柜门仍然可见。", [obj("refrigerator_1", "refrigerator", "refrigerator"), obj("side_table_1", "side_table", "side table")], [rel("right_of", "refrigerator_1", "side_table_1", primary=False, frame="image"), rel("face_angle", "refrigerator_1", primary=True, frame="image", direction="left", angle_degrees=30, angle_reference="facing_viewer", tolerance_deg=15, facing_part="front_side")]),
    ]
    for case_id, en, zh, objects, relations in yaw_normals:
        add(case_id, "continuous_yaw", "normal", en, zh, objects, relations)
    yaw_hards = [
        ("YAW-H01", "On an office desk, an open laptop is left of a desktop monitor, and a chair stands in front of the desk. Starting from directly facing the viewer, the laptop screen turns 30 degrees toward image right and the monitor screen turns 60 degrees toward image left.", "办公桌上，打开的笔记本电脑位于显示器左侧，椅子位于桌子前方。笔记本屏幕和显示器屏幕都从正对观察者的位置开始，笔记本屏幕向画面右侧转动30度，显示器屏幕向画面左侧转动60度。", [obj("laptop_1", "laptop", "open laptop"), obj("monitor_1", "computer_monitor", "desktop monitor"), obj("office_desk_1", "office_desk", "office desk"), obj("chair_1", "chair", "chair")], [rel("on_top", "laptop_1", "office_desk_1", primary=False, frame="support"), rel("on_top", "monitor_1", "office_desk_1", primary=False, frame="support"), rel("left_of", "laptop_1", "monitor_1", primary=False, frame="image"), rel("in_front", "chair_1", "office_desk_1", primary=False, frame="camera"), rel("face_angle", "laptop_1", primary=True, frame="image", direction="right", angle_degrees=30, angle_reference="facing_viewer", tolerance_deg=15, facing_part="screen_side"), rel("face_angle", "monitor_1", primary=True, frame="image", direction="left", angle_degrees=60, angle_reference="facing_viewer", tolerance_deg=15, facing_part="screen_side")]),
        ("YAW-H02", "A sofa is left of a coffee table, and a chair is right of the coffee table. A cabinet stands behind the coffee table with a television on top. Starting from directly facing the viewer, the sofa front turns 30 degrees toward image left and the chair front turns 60 degrees toward image right.", "沙发位于茶几左侧，椅子位于茶几右侧。柜子位于茶几后方，电视放在柜子上。沙发和椅子都从正对观察者的位置开始，沙发正面向画面左侧转动30度，椅子正面向画面右侧转动60度。", [obj("sofa_1", "sofa", "sofa"), obj("coffee_table_1", "coffee_table", "coffee table"), obj("chair_1", "chair", "chair"), obj("cabinet_1", "cabinet", "cabinet"), obj("tv_1", "tv", "television")], [rel("left_of", "sofa_1", "coffee_table_1", primary=False, frame="image"), rel("right_of", "chair_1", "coffee_table_1", primary=False, frame="image"), rel("behind", "cabinet_1", "coffee_table_1", primary=False, frame="camera"), rel("on_top", "tv_1", "cabinet_1", primary=False, frame="support"), rel("face_angle", "sofa_1", primary=True, frame="image", direction="left", angle_degrees=30, angle_reference="facing_viewer", tolerance_deg=15, facing_part="front_side"), rel("face_angle", "chair_1", primary=True, frame="image", direction="right", angle_degrees=60, angle_reference="facing_viewer", tolerance_deg=15, facing_part="front_side")]),
        ("YAW-H03", "A television rests on a cabinet, an armchair is in front of the cabinet, a coffee table is in front of the armchair, and a potted plant is to the cabinet's right. Starting from directly facing the viewer, the TV screen turns 30 degrees toward image right and the armchair front turns 60 degrees toward image left.", "电视放在柜子上，扶手椅位于柜子前方，茶几位于扶手椅前方，盆栽位于柜子右侧。电视和扶手椅都从正对观察者的位置开始，电视屏幕向画面右侧转动30度，扶手椅正面向画面左侧转动60度。", [obj("tv_1", "tv", "television"), obj("cabinet_1", "cabinet", "cabinet"), obj("armchair_1", "armchair", "armchair"), obj("coffee_table_1", "coffee_table", "coffee table"), obj("plant_1", "potted_plant", "potted plant")], [rel("on_top", "tv_1", "cabinet_1", primary=False, frame="support"), rel("in_front", "armchair_1", "cabinet_1", primary=False, frame="camera"), rel("in_front", "coffee_table_1", "armchair_1", primary=False, frame="camera"), rel("right_of", "plant_1", "cabinet_1", primary=False, frame="image"), rel("face_angle", "tv_1", primary=True, frame="image", direction="right", angle_degrees=30, angle_reference="facing_viewer", tolerance_deg=15, facing_part="screen_side"), rel("face_angle", "armchair_1", primary=True, frame="image", direction="left", angle_degrees=60, angle_reference="facing_viewer", tolerance_deg=15, facing_part="front_side")]),
        ("YAW-H04", "A chair is in front of an office desk, a sofa is behind the chair, and a laptop and desk lamp rest on the desk, with the lamp to the laptop's right. Starting from directly facing the viewer, the chair front turns 90 degrees toward image right and the sofa front turns 30 degrees toward image left.", "椅子位于办公桌前方，沙发位于椅子后方，笔记本电脑和台灯放在桌面上，台灯位于笔记本电脑右侧。椅子和沙发都从正对观察者的位置开始，椅子正面向画面右侧转动90度，沙发正面向画面左侧转动30度。", [obj("chair_1", "chair", "chair"), obj("office_desk_1", "office_desk", "office desk"), obj("sofa_1", "sofa", "sofa"), obj("laptop_1", "laptop", "laptop"), obj("lamp_1", "lamp", "desk lamp")], [rel("in_front", "chair_1", "office_desk_1", primary=False, frame="camera"), rel("behind", "sofa_1", "chair_1", primary=False, frame="camera"), rel("on_top", "laptop_1", "office_desk_1", primary=False, frame="support"), rel("on_top", "lamp_1", "office_desk_1", primary=False, frame="support"), rel("right_of", "lamp_1", "laptop_1", primary=False, frame="image"), rel("face_angle", "chair_1", primary=True, frame="image", direction="right", angle_degrees=90, angle_reference="facing_viewer", tolerance_deg=15, facing_part="front_side"), rel("face_angle", "sofa_1", primary=True, frame="image", direction="left", angle_degrees=30, angle_reference="facing_viewer", tolerance_deg=15, facing_part="front_side")]),
        ("YAW-H05", "A cabinet is left of a bookshelf, a bench is in front of the bookshelf, a suitcase is left of the bench, and a potted plant is right of the cabinet. Starting from directly facing the viewer, the cabinet front turns 60 degrees toward image right and the bookshelf's open front turns 30 degrees toward image left.", "柜子位于书架左侧，长凳位于书架前方，行李箱位于长凳左侧，盆栽位于柜子右侧。柜子和书架都从正对观察者的位置开始，柜子正面向画面右侧转动60度，书架开放正面向画面左侧转动30度。", [obj("cabinet_1", "cabinet", "cabinet"), obj("bookshelf_1", "bookshelf", "bookshelf"), obj("bench_1", "bench", "bench"), obj("suitcase_1", "suitcase", "suitcase"), obj("plant_1", "potted_plant", "potted plant")], [rel("left_of", "cabinet_1", "bookshelf_1", primary=False, frame="image"), rel("in_front", "bench_1", "bookshelf_1", primary=False, frame="camera"), rel("left_of", "suitcase_1", "bench_1", primary=False, frame="image"), rel("right_of", "plant_1", "cabinet_1", primary=False, frame="image"), rel("face_angle", "cabinet_1", primary=True, frame="image", direction="right", angle_degrees=60, angle_reference="facing_viewer", tolerance_deg=15, facing_part="front_side"), rel("face_angle", "bookshelf_1", primary=True, frame="image", direction="left", angle_degrees=30, angle_reference="facing_viewer", tolerance_deg=15, facing_part="front_side")]),
    ]
    for case_id, en, zh, objects, relations in yaw_hards:
        add(case_id, "continuous_yaw", "hard", en, zh, objects, relations)

    # Multi-relation composition: 7 Normal + 5 Hard.
    for source, target in (
        ("MUL-N01", "MUL-N01"), ("MUL-N02", "MUL-N02"), ("MUL-N03", "MUL-N03"),
        ("MUL-N04", "MUL-N04"), ("MUL-N05", "MUL-N05"), ("MUL-N06", "MUL-N06"),
        ("PILOTMUL-N02", "MUL-N07"),
    ):
        clone(source, target)
    clone("MUL-H03", "MUL-H01")
    clone("PILOTMUL-H01", "MUL-H02")
    add(
        "MUL-H03", "multi_relation_composition", "hard",
        "A television rests on a cabinet. A vase rests on a coffee table in front of a sofa. A chair is to the sofa's right and faces the television.",
        "电视放在柜子上。花瓶放在茶几上，茶几位于沙发前方。椅子位于沙发右侧并朝向电视。",
        [obj("tv_1", "tv", "television"), obj("cabinet_1", "cabinet", "cabinet"), obj("vase_1", "vase", "vase"), obj("coffee_table_1", "coffee_table", "coffee table"), obj("sofa_1", "sofa", "sofa"), obj("chair_1", "chair", "chair")],
        [rel("on_top", "tv_1", "cabinet_1", primary=True, frame="support"), rel("on_top", "vase_1", "coffee_table_1", primary=True, frame="support"), rel("in_front", "coffee_table_1", "sofa_1", primary=True, frame="camera"), rel("right_of", "chair_1", "sofa_1", primary=True, frame="image"), rel("face", "chair_1", "tv_1", primary=True, frame="object_target", facing_intent="toward_target", facing_part="front_side")],
    )
    add(
        "MUL-H04", "multi_relation_composition", "hard",
        "A vase rests on a coffee table in front of a sofa. A potted plant is to the sofa's left, and a chair is to the sofa's right and faces the coffee table.",
        "花瓶放在茶几上，茶几位于沙发前方。盆栽位于沙发左侧，椅子位于沙发右侧并朝向茶几。",
        [obj("vase_1", "vase", "vase"), obj("coffee_table_1", "coffee_table", "coffee table"), obj("sofa_1", "sofa", "sofa"), obj("plant_1", "potted_plant", "potted plant"), obj("chair_1", "chair", "chair")],
        [rel("on_top", "vase_1", "coffee_table_1", primary=True, frame="support"), rel("in_front", "coffee_table_1", "sofa_1", primary=True, frame="camera"), rel("left_of", "plant_1", "sofa_1", primary=True, frame="image"), rel("right_of", "chair_1", "sofa_1", primary=True, frame="image"), rel("face", "chair_1", "coffee_table_1", primary=True, frame="object_target", facing_intent="toward_target", facing_part="front_side")],
    )
    add(
        "MUL-H05", "multi_relation_composition", "hard",
        "A television rests on a cabinet. A vase rests on a coffee table in front of a sofa. An armchair is to the sofa's right and partially occludes the cabinet while the cabinet remains recognizable.",
        "电视放在柜子上。花瓶放在茶几上，茶几位于沙发前方。扶手椅位于沙发右侧并部分遮挡柜子，但柜子仍可辨认。",
        [obj("tv_1", "tv", "television"), obj("cabinet_1", "cabinet", "cabinet"), obj("vase_1", "vase", "vase"), obj("coffee_table_1", "coffee_table", "coffee table"), obj("sofa_1", "sofa", "sofa"), obj("armchair_1", "armchair", "armchair")],
        [rel("on_top", "tv_1", "cabinet_1", primary=True, frame="support"), rel("on_top", "vase_1", "coffee_table_1", primary=True, frame="support"), rel("in_front", "coffee_table_1", "sofa_1", primary=True, frame="camera"), rel("right_of", "armchair_1", "sofa_1", primary=True, frame="image"), rel("partially_occludes", "armchair_1", "cabinet_1", primary=True, frame="camera", occlusion_policy="partial")],
    )

    errors = validate_cases(cases, profile="v32")
    if errors:
        raise SystemExit("\n".join(errors))

    OUT_PATH.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in cases), encoding="utf-8")
    MIGRATION_PATH.write_text(json.dumps({
        "schema_version": "spatial_bench_v3.2_migration",
        "source_manifest": BASE_PATH.name,
        "target_manifest": OUT_PATH.name,
        "counts": {
            "total": len(cases),
            "reusable": sum(row["reuse_old_artifacts"] for row in migration),
            "rerun": sum(not row["reuse_old_artifacts"] for row in migration),
        },
        "cases": migration,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    migration_by_id = {row["new_id"]: row for row in migration}
    markdown = [
        "# Spatial Bench v3.2 Prompts (90 Cases)", "",
        "`reuse` means the v3.1 image and visual judgment may be migrated after hash verification.", "",
    ]
    current = None
    for row in cases:
        capability = row["focus_capability"]
        if capability != current:
            current = capability
            markdown.extend((f"## {capability}", ""))
        state = "reuse" if migration_by_id[row["id"]]["reuse_old_artifacts"] else "rerun"
        difficulty = row["difficulty"] or "diagnostic"
        markdown.extend((
            f"### {row['id']} | {difficulty} | {state}", "",
            row["prompt_en"], "", row["prompt_zh"], "",
        ))
    PROMPTS_PATH.write_text("\n".join(markdown), encoding="utf-8")

    rerun_rows = []
    for row in cases:
        migration_row = migration_by_id[row["id"]]
        if migration_row["reuse_old_artifacts"]:
            continue
        rerun_rows.append({
            "prompt_id": row["id"],
            "prompt": row["prompt_en"],
            "prompt_zh": row["prompt_zh"],
            "category": row["focus_capability"],
            "difficulty": row["difficulty"],
            "source_id": migration_row["source_id"],
        })
    RERUN_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rerun_rows),
        encoding="utf-8",
    )
    RERUN_IDS_PATH.write_text("\n".join(row["prompt_id"] for row in rerun_rows) + "\n", encoding="utf-8")

    counts = Counter((row["focus_capability"], row["difficulty"]) for row in cases)
    print(f"wrote {len(cases)} cases to {OUT_PATH}")
    print(f"reuse={sum(row['reuse_old_artifacts'] for row in migration)} rerun={sum(not row['reuse_old_artifacts'] for row in migration)}")
    print(f"wrote {len(rerun_rows)} rerun prompts to {RERUN_PATH}")
    for key in sorted(counts, key=str):
        print(key, counts[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
