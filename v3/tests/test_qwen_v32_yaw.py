import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
openai_stub = types.ModuleType("openai")
openai_stub.OpenAI = object
sys.modules.setdefault("openai", openai_stub)
SPEC = importlib.util.spec_from_file_location(
    "evaluate_images_vqa_v32",
    SCRIPTS / "evaluate_images_vqa_v32.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ContinuousYawJudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cases = json.loads(
            (ROOT / "generated" / "full_90_v32_materialized_eval_cases.json").read_text()
        )
        cls.case = next(case for case in cases if case["id"] == "YAW-N01")
        cls.relation = next(
            relation for relation in cls.case["relations"] if relation["type"] == "face_angle"
        )

    def test_prompt_requests_visual_bin_instead_of_exact_angle(self):
        prompt = MODULE.build_typed_yaw_prompt(self.case, self.relation)
        self.assertIn("slight", prompt)
        self.assertIn("diagonal", prompt)
        self.assertIn("Do not estimate an exact angle", prompt)

    def test_direction_and_magnitude_must_both_match(self):
        answers = MODULE.typed_yaw_answers(
            self.case,
            self.relation,
            {
                "part_visible": True,
                "direction": "image_right",
                "magnitude": "slight",
                "reason": "screen is in a slight right three-quarter view",
            },
        )
        self.assertEqual(answers["r2:positive"]["answer"], "yes")
        self.assertEqual(answers["r2:inverse"]["answer"], "no")

        wrong_bin = MODULE.typed_yaw_answers(
            self.case,
            self.relation,
            {
                "part_visible": True,
                "direction": "image_right",
                "magnitude": "side",
                "reason": "screen is side-on",
            },
        )
        self.assertEqual(wrong_bin["r2:positive"]["answer"], "no")
        self.assertEqual(wrong_bin["r2:inverse"]["answer"], "no")


if __name__ == "__main__":
    unittest.main()
