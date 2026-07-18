#!/usr/bin/env python3
"""Build the visual-adjudication vs Qwen32 manual audit payload."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from math import isclose
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VIEWER_PATH = ROOT / "data/v3_viewer_cases.json"
TABLE_PATH = ROOT / "data/v3_final_paper_table_20260718.json"
OUTPUT_PATH = ROOT / "data/v3_judge_disagreement_audit_20260718.json"
SUMMARY_PATH = ROOT / "data/v3_judge_disagreement_audit_20260718.md"
OURS = "t2i_blender_qwen"

HEADLINE_METRICS = {
    "presence": "Presence",
    "cardinality": "Cardinality",
    "layout_2d": "2D Layout",
    "depth_contact_occlusion": "Depth / Contact / Occlusion",
    "orientation_yaw": "Orientation / Yaw",
    "multi_relation": "Multi-Relation",
    "spatial_macro": "Spatial Macro",
    "case_exact": "Case Exact",
}

CATEGORY_LABELS = {
    "absolute_location_2d": "Absolute Location",
    "relative_position_2d": "Relative Position",
    "depth_front_back": "Depth / Front-Back",
    "occlusion_visibility": "Occlusion / Visibility",
    "support_contact": "Support / Contact",
    "orientation_facing": "Orientation / Facing",
    "yaw_direction": "Yaw Direction",
    "multi_relation_composition": "Multi-Relation Composition",
}

AGGREGATE_FIELDS = ("presence", "cardinality", "relation", "primary_relation", "exact")


def ranked_block(rows: dict[str, dict], metric: str, method_order: list[str]) -> dict:
    best = max(row[metric] for row in rows.values())
    winners = [method for method in method_order if isclose(rows[method][metric], best, abs_tol=1e-12)]
    ours = rows[OURS][metric]
    return {
        "best_score": best,
        "winner_ids": winners,
        "ours_score": ours,
        "ours_rank": 1 + sum(row[metric] > ours + 1e-12 for row in rows.values()),
    }


def headline_block(rows: list[dict], metric: str, method_order: list[str]) -> dict:
    return ranked_block({row["method"]: row for row in rows}, metric, method_order)


def compact_answer(answer: dict | None) -> dict | None:
    if not answer:
        return None
    return {
        key: answer[key]
        for key in ("answer", "confidence", "reason", "votes")
        if key in answer
    }


def compact_result(case: dict, method_id: str) -> dict:
    result = case["results"][method_id]
    qwen = result["qwen32"]
    relation_primary = {relation["id"]: bool(relation.get("primary")) for relation in case["relations"]}
    checks = []
    for check in case["checks"]:
        direct_answer = result.get("answers", {}).get(check["id"])
        qwen_answer = qwen.get("answers", {}).get(check["id"])
        direct_value = direct_answer.get("answer") if direct_answer else None
        qwen_value = qwen_answer.get("answer") if qwen_answer else None
        relation_id = check.get("relation_id")
        checks.append(
            {
                "id": check["id"],
                "kind": check["kind"],
                "question": check["question"],
                "expected": check["expected"],
                "primary": bool(relation_id and relation_primary.get(relation_id)),
                "direct": compact_answer(direct_answer),
                "qwen32": compact_answer(qwen_answer),
                "answer_mismatch": direct_value is not None and qwen_value is not None and direct_value != qwen_value,
            }
        )
    visual_scores = {field: result[field] for field in AGGREGATE_FIELDS}
    qwen_scores = {field: qwen[field] for field in AGGREGATE_FIELDS}
    aggregate_mismatches = [field for field in AGGREGATE_FIELDS if visual_scores[field] != qwen_scores[field]]
    return {
        "image": result["image"],
        "visual": visual_scores,
        "qwen32": qwen_scores,
        "aggregate_mismatches": aggregate_mismatches,
        "checks": checks,
        "atomic_mismatch_count": sum(check["answer_mismatch"] for check in checks),
    }


def main() -> None:
    viewer = json.loads(VIEWER_PATH.read_text())
    table = json.loads(TABLE_PATH.read_text())
    method_order = [method["id"] for method in viewer["models"]]
    method_labels = {method["id"]: method["label"] for method in viewer["models"]}

    headline = []
    for metric, label in HEADLINE_METRICS.items():
        visual = headline_block(table["visual"]["rows"], metric, method_order)
        qwen = headline_block(table["qwen32_diagnostic"]["rows"], metric, method_order)
        headline.append(
            {
                "metric": metric,
                "label": label,
                "visual": visual,
                "qwen32": qwen,
                "winner_changed": set(visual["winner_ids"]) != set(qwen["winner_ids"]),
                "ours_rank_changed": visual["ours_rank"] != qwen["ours_rank"],
                "ours_score_delta": qwen["ours_score"] - visual["ours_score"],
            }
        )

    categories = []
    total_review_cases = 0
    total_method_case_disagreements = 0
    for category, label in CATEGORY_LABELS.items():
        visual_rows = table["visual"]["summary"]["by_capability"][category]
        qwen_rows = table["qwen32_diagnostic"]["summary"]["by_capability"][category]
        visual = ranked_block(visual_rows, "primary_relation_micro", method_order)
        qwen = ranked_block(qwen_rows, "primary_relation_micro", method_order)
        selected_methods = [
            method
            for method in method_order
            if method in set(visual["winner_ids"] + qwen["winner_ids"] + [OURS])
        ]

        review_cases = []
        category_cases = [case for case in viewer["cases"] if case["category"] == category]
        for case in category_cases:
            compact = {method: compact_result(case, method) for method in selected_methods}
            judge_mismatch_methods = [
                method for method, result in compact.items() if result["aggregate_mismatches"]
            ]
            qwen_gap_methods = [
                method
                for method in qwen["winner_ids"]
                if case["results"][method]["qwen32"]["primary_relation"]
                != case["results"][OURS]["qwen32"]["primary_relation"]
            ]
            visual_gap_methods = [
                method
                for method in visual["winner_ids"]
                if case["results"][method]["primary_relation"]
                != case["results"][OURS]["primary_relation"]
            ]
            if not judge_mismatch_methods and not qwen_gap_methods and not visual_gap_methods:
                continue
            review_cases.append(
                {
                    "id": case["id"],
                    "difficulty": case["difficulty"],
                    "prompt_en": case["prompt_en"],
                    "prompt_zh": case.get("prompt_zh", ""),
                    "relations": case["relations"],
                    "judge_mismatch_methods": judge_mismatch_methods,
                    "qwen_leader_vs_ours_gap_methods": qwen_gap_methods,
                    "visual_leader_vs_ours_gap_methods": visual_gap_methods,
                    "methods": compact,
                }
            )
            total_method_case_disagreements += len(judge_mismatch_methods)

        total_review_cases += len(review_cases)
        categories.append(
            {
                "category": category,
                "label": label,
                "case_count": len(category_cases),
                "visual": visual,
                "qwen32": qwen,
                "winner_changed": set(visual["winner_ids"]) != set(qwen["winner_ids"]),
                "ours_rank_changed": visual["ours_rank"] != qwen["ours_rank"],
                "ours_score_delta": qwen["ours_score"] - visual["ours_score"],
                "selected_method_ids": selected_methods,
                "review_case_count": len(review_cases),
                "review_cases": review_cases,
            }
        )

    payload = {
        "schema_version": "spatial_bench_v3_judge_disagreement_audit",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ours_method_id": OURS,
        "methods": viewer["models"],
        "protocols": {
            "visual": "Direct visual subagent review with independent adjudication; headline protocol.",
            "qwen32": "Qwen3-VL-32B-Instruct, three votes per atomic question; diagnostic protocol.",
        },
        "headline": headline,
        "categories": categories,
        "totals": {
            "headline_winner_changes": sum(row["winner_changed"] for row in headline),
            "headline_ours_rank_changes": sum(row["ours_rank_changed"] for row in headline),
            "category_winner_changes": sum(row["winner_changed"] for row in categories),
            "category_ours_rank_changes": sum(row["ours_rank_changed"] for row in categories),
            "review_case_entries": total_review_cases,
            "method_case_judge_disagreements": total_method_case_disagreements,
            "atomic_answer_disagreements": sum(
                result["atomic_mismatch_count"]
                for category in categories
                for case in category["review_cases"]
                for result in case["methods"].values()
            ),
        },
    }
    assert len(headline) == 8 and len(categories) == 8
    for category in categories:
        for case in category["review_cases"]:
            for result in case["methods"].values():
                assert (ROOT / result["image"]).is_file(), result["image"]
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    lines = [
        "# Visual adjudication vs Qwen32 disagreement audit",
        "",
        f"- Headline winner changes: {payload['totals']['headline_winner_changes']}/8",
        f"- Original-category winner changes: {payload['totals']['category_winner_changes']}/8",
        f"- Review case entries: {total_review_cases}",
        f"- Method-case judge disagreements: {total_method_case_disagreements}",
        f"- Atomic answer disagreements: {payload['totals']['atomic_answer_disagreements']}",
        "",
        "## Headline metrics",
        "",
        "| Metric | Visual leader | Qwen32 leader | Ours visual | Ours Qwen32 | Rank |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in headline:
        visual_names = ", ".join(method_labels[method] for method in row["visual"]["winner_ids"])
        qwen_names = ", ".join(method_labels[method] for method in row["qwen32"]["winner_ids"])
        lines.append(
            f"| {row['label']} | {visual_names} | {qwen_names} | "
            f"{row['visual']['ours_score']:.1%} | {row['qwen32']['ours_score']:.1%} | "
            f"{row['visual']['ours_rank']} -> {row['qwen32']['ours_rank']} |"
        )
    lines.extend(["", "## Original categories", ""])
    for row in categories:
        lines.append(
            f"- **{row['label']}**: ours {row['visual']['ours_score']:.1%} (visual rank {row['visual']['ours_rank']}) "
            f"vs {row['qwen32']['ours_score']:.1%} (Qwen32 rank {row['qwen32']['ours_rank']}); "
            f"review cases: {', '.join(case['id'] for case in row['review_cases']) or 'none'}."
        )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
