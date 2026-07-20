from __future__ import annotations

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from v3_common import (  # noqa: E402
    match_extraction,
    materialize_case,
    strict_score_case,
    validate_adapter,
    validate_case,
)


def obj(object_id: str, canonical: str, mention: str) -> dict:
    return {"id": object_id, "canonical": canonical, "mention": mention}


def rel(relation_id: str, kind: str, subject: str, target: str = "", *, primary: bool, **extra) -> dict:
    payload = {"id": relation_id, "type": kind, "subject": subject, "primary": primary, **extra}
    if target:
        payload["target"] = target
    return payload


def normal_orientation_case() -> dict:
    return {
        "schema_version": "spatial_bench_v3",
        "id": "ORI-N01",
        "subset": "compositional",
        "difficulty": "normal",
        "focus_capability": "orientation_facing",
        "prompt_en": "A television sits on a cabinet. A sofa stands in front of the cabinet and faces the television.",
        "prompt_zh": "电视放在柜子上。沙发位于柜子前方，并朝向电视。",
        "objects": [
            obj("television_1", "tv", "television"),
            obj("cabinet_1", "cabinet", "cabinet"),
            obj("sofa_1", "sofa", "sofa"),
        ],
        "relations": [
            rel("r1", "on_top", "television_1", "cabinet_1", primary=False, frame="support"),
            rel("r2", "in_front", "sofa_1", "cabinet_1", primary=False, frame="camera"),
            rel(
                "r3",
                "face",
                "sofa_1",
                "television_1",
                primary=True,
                frame="object_target",
                facing_intent="toward_target",
                facing_part="front_side",
            ),
        ],
    }


class SchemaTests(unittest.TestCase):
    def test_json_schema_is_valid_json(self) -> None:
        with (ROOT / "schema" / "core_case.schema.json").open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
        self.assertEqual(
            schema["$defs"]["relation"]["properties"]["facing_part"]["enum"],
            ["front_side", "screen_side", "lens_side", "emitting_side"],
        )

        with (ROOT / "schema" / "t2i_blender_adapter.schema.json").open("r", encoding="utf-8") as handle:
            adapter_schema = json.load(handle)
        orientation = adapter_schema["$defs"]["orientation_profile"]
        self.assertEqual(orientation["properties"]["human_review"]["enum"], ["pending", "accepted", "rejected"])
        self.assertEqual(set(orientation["properties"]["view_hashes"]["required"]), {"+X", "-X", "+Y", "-Y", "+Z", "-Z"})

    def test_normal_orientation_case_is_valid(self) -> None:
        self.assertEqual(validate_case(normal_orientation_case(), profile="pilot"), [])

    def test_spatial_answer_in_instance_id_is_rejected(self) -> None:
        case = normal_orientation_case()
        case["objects"][2]["id"] = "sofa_left_1"
        case["relations"][1]["subject"] = "sofa_left_1"
        case["relations"][2]["subject"] = "sofa_left_1"
        self.assertTrue(any("encodes a spatial answer" in item for item in validate_case(case, profile="pilot")))

    def test_duplicate_canonical_is_supported_by_schema_but_rejected_by_pilot(self) -> None:
        case = normal_orientation_case()
        case["objects"][2] = obj("television_2", "tv", "second television")
        errors = validate_case(case, profile="pilot")
        self.assertTrue(any("may not repeat a canonical" in item for item in errors))

    def test_bare_between_is_rejected(self) -> None:
        case = normal_orientation_case()
        case["relations"] = [rel("r1", "between", "sofa_1", "television_1", primary=True)]
        self.assertTrue(any("bare between" in item for item in validate_case(case)))

    def test_derived_fields_and_asset_ids_are_rejected_from_core(self) -> None:
        case = normal_orientation_case()
        case["pair_count"] = 3
        case["objects"][0]["asset_id"] = "ext_tv_example"
        errors = validate_case(case, profile="pilot")
        self.assertTrue(any("unknown core fields" in item for item in errors))
        self.assertTrue(any("forbidden object fields" in item for item in errors))

    def test_registered_ordered_between_is_valid(self) -> None:
        case = {
            "schema_version": "spatial_bench_v3",
            "id": "REL-N01",
            "subset": "compositional",
            "difficulty": "normal",
            "focus_capability": "relative_position_2d",
            "registered_pattern": "ordered_between",
            "prompt_en": "A sofa is on the left, a coffee table is on the right, and a vase stands between them.",
            "prompt_zh": "沙发在左侧，茶几在右侧，花瓶位于二者之间。",
            "objects": [obj("sofa_1", "sofa", "sofa"), obj("coffee_table_1", "coffee_table", "coffee table"), obj("vase_1", "vase", "vase")],
            "relations": [
                rel("r1", "right_of", "vase_1", "sofa_1", primary=True, frame="image"),
                rel("r2", "left_of", "vase_1", "coffee_table_1", primary=True, frame="image"),
            ],
        }
        self.assertEqual(validate_case(case, profile="pilot"), [])

    def test_image_facing_does_not_require_target(self) -> None:
        case = {
            "schema_version": "spatial_bench_v3",
            "id": "YAW-D01",
            "subset": "diagnostic",
            "difficulty": None,
            "focus_capability": "yaw_direction",
            "prompt_en": "A television screen faces the right side of the image.",
            "prompt_zh": "电视屏幕朝向画面右侧。",
            "objects": [obj("television_1", "tv", "television")],
            "relations": [
                rel(
                    "r1",
                    "face",
                    "television_1",
                    primary=True,
                    frame="image",
                    facing_intent="right",
                    facing_part="screen_side",
                )
            ],
        }
        self.assertEqual(validate_case(case, profile="pilot"), [])

    def test_camera_relative_face_angle_is_compositional(self) -> None:
        case = {
            "schema_version": "spatial_bench_v3",
            "id": "CYAW-N01",
            "subset": "compositional",
            "difficulty": "normal",
            "focus_capability": "continuous_yaw",
            "prompt_en": "A television rests on a cabinet. Its screen starts facing the viewer and turns 30 degrees toward image right.",
            "prompt_zh": "电视放在柜子上。屏幕从正对观察者开始，向画面右侧转动30度。",
            "objects": [obj("television_1", "tv", "television"), obj("cabinet_1", "cabinet", "cabinet")],
            "relations": [
                rel("r1", "on_top", "television_1", "cabinet_1", primary=False, frame="support"),
                rel(
                    "r2",
                    "face_angle",
                    "television_1",
                    primary=True,
                    frame="image",
                    direction="right",
                    angle_degrees=30,
                    angle_reference="facing_viewer",
                    tolerance_deg=15,
                    facing_part="screen_side",
                ),
            ],
        }
        self.assertEqual(validate_case(case), [])
        materialized = materialize_case(case)
        yaw_check = materialized["evaluation"]["relation_checks"][1]
        self.assertIn("slightly", yaw_check["positive"]["question"])
        self.assertIn("continuous_yaw", materialized["derived"]["relation_families"])


class MaterializerTests(unittest.TestCase):
    def test_counts_and_questions_are_derived(self) -> None:
        materialized = materialize_case(normal_orientation_case())
        self.assertEqual(materialized["derived"]["object_count"], 3)
        self.assertEqual(materialized["derived"]["constraint_count"], 3)
        self.assertEqual(materialized["derived"]["family_count"], 3)
        self.assertEqual(len(materialized["evaluation"]["presence_checks"]), 3)
        self.assertEqual(len(materialized["evaluation"]["cardinality_checks"]), 3)
        self.assertEqual(len(materialized["evaluation"]["relation_checks"]), 3)
        face = materialized["evaluation"]["relation_checks"][2]
        self.assertIn("front side", face["positive"]["question"])
        self.assertEqual(face["inverse"]["expected_answer"], "no")

    def test_strict_score_rejects_unclear_and_requires_extraction(self) -> None:
        materialized = materialize_case(normal_orientation_case())
        answers = {}
        for check in materialized["evaluation"]["presence_checks"] + materialized["evaluation"]["cardinality_checks"]:
            answers[check["id"]] = "yes"
        for check in materialized["evaluation"]["relation_checks"]:
            answers[check["positive"]["id"]] = "yes"
            if check["inverse"]:
                answers[check["inverse"]["id"]] = "no"
        score = strict_score_case(materialized, answers, extraction_exact=False)
        self.assertTrue(score["relation_all"])
        self.assertEqual(score["primary_relation_score"], 1.0)
        self.assertEqual(
            [(item["relation_family"], item["primary"]) for item in score["relation_rows"]],
            [("support_contact", False), ("depth_front_back", False), ("orientation_facing", True)],
        )
        self.assertFalse(score["case_exact"])
        answers["r3:inverse"] = "unclear"
        score = strict_score_case(materialized, answers, extraction_exact=True)
        self.assertFalse(score["relation_all"])
        self.assertEqual(score["primary_relation_score"], 0.0)
        self.assertFalse(score["case_exact"])


class ExtractionMatcherTests(unittest.TestCase):
    def test_descriptive_potted_plant_alias_matches(self) -> None:
        case = {
            "schema_version": "spatial_bench_v3",
            "id": "OCC-D01",
            "subset": "diagnostic",
            "difficulty": None,
            "focus_capability": "occlusion_visibility",
            "prompt_en": "A tall potted plant partially occludes a cabinet.",
            "prompt_zh": "一盆高大的盆栽部分遮挡柜子。",
            "objects": [
                obj("potted_plant_1", "potted_plant", "potted plant"),
                obj("cabinet_1", "cabinet", "cabinet"),
            ],
            "relations": [
                rel("r1", "partially_occludes", "potted_plant_1", "cabinet_1", primary=True)
            ],
        }
        extracted = {
            "objects": [
                {
                    "id": "tall_potted_plant",
                    "canonical": "tall_potted_plant",
                    "provenance": "prompt_explicit",
                },
                {"id": "cabinet", "canonical": "cabinet", "provenance": "prompt_explicit"},
            ],
            "relations": [
                {
                    "type": "occlude",
                    "subject": "tall_potted_plant",
                    "target": "cabinet",
                    "provenance": "prompt_explicit",
                }
            ],
        }

        self.assertTrue(match_extraction(case, extracted)["extraction_exact"])

    def test_office_desk_truth_matches_desk_alias(self) -> None:
        case = {
            "schema_version": "spatial_bench_v3",
            "id": "REL-D02",
            "subset": "diagnostic",
            "difficulty": None,
            "focus_capability": "relative_position_2d",
            "prompt_en": "A chair is left of an office desk.",
            "prompt_zh": "椅子在办公桌左侧。",
            "objects": [obj("chair_1", "chair", "chair"), obj("desk_1", "office_desk", "office desk")],
            "relations": [rel("r1", "left_of", "chair_1", "desk_1", primary=True, frame="image")],
        }
        extracted = {
            "objects": [
                {"id": "chair", "canonical": "chair", "provenance": "prompt_explicit"},
                {"id": "desk", "canonical": "desk", "provenance": "prompt_explicit"},
            ],
            "relations": [
                {"type": "left_of", "subject": "chair", "target": "desk", "provenance": "prompt_explicit"}
            ],
        }

        self.assertTrue(match_extraction(case, extracted)["extraction_exact"])

    def test_inverse_equivalent_relation_matches(self) -> None:
        case = {
            "schema_version": "spatial_bench_v3",
            "id": "REL-D01",
            "subset": "diagnostic",
            "difficulty": None,
            "focus_capability": "relative_position_2d",
            "prompt_en": "A chair is left of a table.",
            "prompt_zh": "椅子在桌子左侧。",
            "objects": [obj("chair_1", "chair", "chair"), obj("table_1", "table", "table")],
            "relations": [rel("r1", "left_of", "chair_1", "table_1", primary=True, frame="image")],
        }
        extracted = {
            "objects": [
                {"id": "chair", "canonical": "chair", "provenance": "prompt_explicit"},
                {"id": "table", "canonical": "table", "provenance": "prompt_explicit"},
            ],
            "relations": [
                {"type": "right_of", "subject": "table", "target": "chair", "provenance": "prompt_explicit"}
            ],
        }
        report = match_extraction(case, extracted)
        self.assertTrue(report["extraction_exact"])
        self.assertEqual(report["invented_relation_count"], 0)

    def test_system_defaults_are_not_invented_and_inferred_contradictions_are_counted(self) -> None:
        case = {
            "schema_version": "spatial_bench_v3",
            "id": "REL-D01",
            "subset": "diagnostic",
            "difficulty": None,
            "focus_capability": "relative_position_2d",
            "prompt_en": "A chair is left of a table.",
            "prompt_zh": "椅子在桌子左侧。",
            "objects": [obj("chair_1", "chair", "chair"), obj("table_1", "table", "table")],
            "relations": [rel("r1", "left_of", "chair_1", "table_1", primary=True, frame="image")],
        }
        extracted = {
            "objects": [
                {"id": "chair", "canonical": "chair", "provenance": "prompt_explicit"},
                {"id": "table", "canonical": "table", "provenance": "prompt_explicit"},
                {"id": "floor", "canonical": "floor", "provenance": "system_default"},
            ],
            "relations": [
                {"type": "left_of", "subject": "chair", "target": "table", "provenance": "prompt_explicit"},
                {"type": "right_of", "subject": "chair", "target": "table", "provenance": "inferred"},
                {"type": "on_top", "subject": "chair", "target": "floor", "provenance": "system_default"},
            ],
        }
        report = match_extraction(case, extracted)
        self.assertEqual(report["invented_object_count"], 0)
        self.assertEqual(report["invented_relation_count"], 0)
        self.assertEqual(report["contradictory_inferred_relation_count"], 1)
        self.assertFalse(report["extraction_exact"])


class AdapterTests(unittest.TestCase):
    def adapter(self) -> dict:
        digest = "a" * 64
        return {
            "schema_version": "spatial_bench_v3",
            "adapter_version": "pilot-1",
            "registry_path": "assets/external_assets_registry.json",
            "registry_sha256": digest,
            "profiles": [
                {
                    "canonical": "tv",
                    "asset_id": "ext_tv_example",
                    "task_profiles": ["orientation_subject", "support_subject"],
                    "measured_dimensions_m": [1.2, 0.1, 0.7],
                    "orientation_profile": {
                        "canonical_front_axis": "-Y",
                        "front_confidence": 0.9,
                        "has_distinct_front": True,
                        "yaw_symmetry_order": 1,
                        "profiler_model": "vlm-example",
                        "profiler_version": "1",
                        "view_hashes": {axis: digest for axis in ("+X", "-X", "+Y", "-Y", "+Z", "-Z")},
                        "vlm_raw_output": {"front_axis": "-Y"},
                        "raw_output_sha256": digest,
                        "human_review": "accepted",
                        "profile_version": "1",
                    },
                }
            ],
        }

    def test_strict_orientation_adapter_is_valid(self) -> None:
        self.assertEqual(validate_adapter(self.adapter()), [])

    def test_orientation_subject_without_profile_is_rejected(self) -> None:
        adapter = self.adapter()
        del adapter["profiles"][0]["orientation_profile"]
        self.assertTrue(any("requires an orientation_profile" in item for item in validate_adapter(adapter)))

    def test_invalid_orientation_numbers_report_errors(self) -> None:
        adapter = self.adapter()
        adapter["profiles"][0]["orientation_profile"]["front_confidence"] = "high"
        errors = validate_adapter(adapter)
        self.assertTrue(any("invalid front_confidence" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
