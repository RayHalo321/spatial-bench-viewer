from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from continuous_yaw_v32 import (  # noqa: E402
    build_yaw_judge_prompt,
    build_reference_card,
    expected_yaw_bin,
    normalized_bbox,
    score_yaw_prediction,
    validate_continuous_yaw_case,
)


def case(degrees: int = 30, direction: str = "right") -> dict:
    return {
        "id": "YAW32-D01",
        "prompt_en": f"A television faces mostly toward the viewer and turns {degrees} degrees {direction}.",
        "objects": [{"id": "television_1", "canonical": "tv", "mention": "television"}],
        "relations": [
            {
                "id": "r1",
                "type": "face_angle",
                "subject": "television_1",
                "primary": True,
                "frame": "image",
                "angle_reference": "facing_viewer",
                "direction": direction,
                "angle_degrees": degrees,
                "tolerance_deg": 15,
                "facing_part": "screen_side",
            }
        ],
    }


class ContinuousYawV32Tests(unittest.TestCase):
    def test_only_three_bins_are_supported(self) -> None:
        self.assertEqual(expected_yaw_bin(30), "slight")
        self.assertEqual(expected_yaw_bin(60), "diagonal")
        self.assertEqual(expected_yaw_bin(90), "side")
        with self.assertRaises(ValueError):
            expected_yaw_bin(45)

    def test_joint_requires_readable_part_direction_and_bin(self) -> None:
        relation = case()["relations"][0]
        passed = score_yaw_prediction(
            relation,
            {
                "subject_visible": True,
                "front_part_visible": True,
                "turn_direction": "right",
                "yaw_bin": "slight",
            },
        )
        self.assertTrue(passed["direction_pass"])
        self.assertTrue(passed["magnitude_bin_pass"])
        self.assertTrue(passed["joint_pass"])

        unclear = score_yaw_prediction(
            relation,
            {
                "subject_visible": True,
                "front_part_visible": False,
                "turn_direction": "right",
                "yaw_bin": "slight",
            },
        )
        self.assertFalse(unclear["direction_pass"])
        self.assertFalse(unclear["magnitude_bin_pass"])
        self.assertTrue(unclear["unclear"])

    def test_prompt_is_method_blind_and_uses_visual_bins(self) -> None:
        item = case(60, "left")
        prompt = build_yaw_judge_prompt(item, item["relations"][0])
        self.assertIn("Image 1 is the complete final RGB image", prompt)
        self.assertIn("slight=15-45", prompt)
        self.assertIn("diagonal=45-75", prompt)
        self.assertNotIn("Blender", prompt)
        self.assertNotIn("MUSES", prompt)

    def test_bbox_is_clamped_and_invalid_box_is_rejected(self) -> None:
        self.assertEqual(normalized_bbox({"subject_visible": True, "bbox_2d": [-10, 100, 1100, 900]}, 100, 200), (0, 20, 100, 180))
        self.assertIsNone(normalized_bbox({"subject_visible": False, "bbox_2d": [0, 0, 1000, 1000]}, 100, 100))

    def test_validator_rejects_45_degree_case(self) -> None:
        self.assertEqual(validate_continuous_yaw_case(case()), [])
        errors = validate_continuous_yaw_case(case(45))
        self.assertTrue(any("only 30, 60, or 90" in error for error in errors))

    def test_reference_card_shows_both_directions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = build_reference_card(Path(directory) / "reference.png")
            with Image.open(output) as image:
                self.assertEqual(image.size, (1750, 500))


if __name__ == "__main__":
    unittest.main()
