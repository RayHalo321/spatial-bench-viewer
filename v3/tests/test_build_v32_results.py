from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_v32_results import bucket, qwen_decisions, validate_decisions  # noqa: E402


class BuildV32ResultsTests(unittest.TestCase):
    def setUp(self):
        self.cases = [
            {
                "id": "X-N01",
                "objects": [{"id": "chair_1", "canonical": "chair"}],
                "relations": [{"id": "r1", "primary": True}],
            }
        ]

    def test_bucket_uses_frozen_object_and_relation_denominators(self):
        result = bucket(
            self.cases,
            {
                "X-N01": {
                    "objects": {"chair_1": True},
                    "cardinality": {"chair": True},
                    "relations": {"r1": False},
                    "exact": False,
                }
            },
        )
        self.assertEqual(result["presence_micro"], 1)
        self.assertEqual(result["strict_relation_micro"], 0)
        self.assertEqual(result["exact_case_rate"], 0)

    def test_visual_review_keys_must_match_truth(self):
        rows = [
            {
                "case_id": "X-N01",
                "method": "flux",
                "decision": {
                    "objects": {"chair_1": True},
                    "cardinality": {"canonical": True},
                    "relations": {"r1": True},
                },
                "exact": True,
            }
        ]
        with self.assertRaisesRegex(ValueError, "decision keys do not match truth"):
            validate_decisions(self.cases, rows, "flux")

    def test_qwen_uses_materialized_cardinality_alias(self):
        rows = [
            {
                "id": "X-N01",
                "answers": {
                    "presence:chair_1": {"answer": "yes"},
                    "cardinality:seat": {"answer": "yes"},
                },
                "relation_rows": [{"relation_id": "r1", "pass": True}],
            }
        ]
        result = qwen_decisions(self.cases, rows, "flux")["X-N01"]
        self.assertEqual(result["cardinality"], {"seat": True})
        self.assertTrue(result["exact"])


if __name__ == "__main__":
    unittest.main()
