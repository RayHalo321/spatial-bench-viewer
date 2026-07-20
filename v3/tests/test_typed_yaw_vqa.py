from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

try:
    import openai  # noqa: F401
except ModuleNotFoundError:
    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = object
    sys.modules["openai"] = openai_stub

from evaluate_images_vqa import build_typed_yaw_prompt, typed_yaw_answers  # noqa: E402
from v3_common import materialize_case  # noqa: E402


def yaw_case(canonical: str, facing_part: str, facing_intent: str = "left") -> dict:
    subject = f"{canonical}_1"
    return materialize_case(
        {
            "schema_version": "spatial_bench_v3",
            "id": "YAW-TEST",
            "subset": "diagnostic",
            "difficulty": None,
            "focus_capability": "yaw_direction",
            "prompt_en": f"A {canonical} faces {facing_intent}.",
            "prompt_zh": "测试。",
            "objects": [{"id": subject, "canonical": canonical, "mention": canonical}],
            "relations": [
                {
                    "id": "r1",
                    "type": "face",
                    "subject": subject,
                    "facing_intent": facing_intent,
                    "facing_part": facing_part,
                    "frame": "image",
                    "primary": True,
                }
            ],
        }
    )


class TypedYawTests(unittest.TestCase):
    def test_seating_prompt_defines_open_seat_direction(self) -> None:
        case = yaw_case("chair", "front_side")
        prompt = build_typed_yaw_prompt(case, case["relations"][0])
        self.assertIn("open front edge", prompt)
        self.assertIn("open_seat_side", prompt)
        self.assertNotIn(case["prompt_en"], prompt)

    def test_matching_direction_passes_positive_and_rejects_inverse(self) -> None:
        case = yaw_case("chair", "front_side", "left")
        answers = typed_yaw_answers(
            case,
            case["relations"][0],
            {"part_visible": True, "open_seat_side": "image_left", "reason": "open seat points left"},
        )
        self.assertEqual(answers["r1:positive"]["answer"], "yes")
        self.assertEqual(answers["r1:inverse"]["answer"], "no")

    def test_visible_opposite_direction_fails_without_contradiction(self) -> None:
        case = yaw_case("tv", "screen_side", "right")
        answers = typed_yaw_answers(
            case,
            case["relations"][0],
            {"part_visible": True, "direction": "image_left"},
        )
        self.assertEqual(answers["r1:positive"]["answer"], "no")
        self.assertEqual(answers["r1:inverse"]["answer"], "yes")

    def test_hidden_named_part_is_unclear(self) -> None:
        case = yaw_case("tv", "screen_side", "left")
        answers = typed_yaw_answers(
            case,
            case["relations"][0],
            {"part_visible": False, "direction": "image_left"},
        )
        self.assertEqual(answers["r1:positive"]["answer"], "unclear")
        self.assertEqual(answers["r1:inverse"]["answer"], "unclear")


if __name__ == "__main__":
    unittest.main()
