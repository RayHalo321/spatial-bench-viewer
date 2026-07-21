#!/usr/bin/env python3
"""Build the v3.2 result tables from complete 90-case visual audits."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


METHODS = (
    "flux",
    "sdxl",
    "gligen",
    "lmd_plus",
    "boxdiff_xl",
    "muses_qwen_rgb",
    "muses_qwen_sdxl",
    "muses_qwen_rgb_qwen_i2i",
    "t2i_blender_rgb",
    "t2i_blender_qwen",
)

GROUPS = {
    "layout_2d": ("absolute_location_2d", "relative_position_2d"),
    "depth_contact_occlusion": (
        "depth_front_back",
        "support_contact",
        "occlusion_visibility",
    ),
    "orientation_yaw": ("orientation_facing", "continuous_yaw"),
    "composition": ("multi_relation_composition",),
}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values)


def bucket(cases: list[dict], decisions: dict[str, dict]) -> dict:
    totals = defaultdict(int)
    for case in cases:
        row = decisions[case["id"]]
        objects = row["objects"]
        cardinality = row["cardinality"]
        relations = row["relations"]
        primary_ids = {relation["id"] for relation in case["relations"] if relation["primary"]}
        totals["cases"] += 1
        totals["presence_pass"] += sum(objects.values())
        totals["presence_total"] += len(objects)
        totals["cardinality_pass"] += sum(cardinality.values())
        totals["cardinality_total"] += len(cardinality)
        totals["relation_pass"] += sum(relations.values())
        totals["relation_total"] += len(relations)
        totals["primary_pass"] += sum(relations[relation_id] for relation_id in primary_ids)
        totals["primary_total"] += len(primary_ids)
        totals["exact_pass"] += bool(row["exact"])
    return {
        **totals,
        "presence_micro": totals["presence_pass"] / totals["presence_total"],
        "cardinality_micro": totals["cardinality_pass"] / totals["cardinality_total"],
        "strict_relation_micro": totals["relation_pass"] / totals["relation_total"],
        "primary_relation_micro": totals["primary_pass"] / totals["primary_total"],
        "exact_case_rate": totals["exact_pass"] / totals["cases"],
    }


def validate_decisions(cases: list[dict], rows: list[dict], method: str) -> dict[str, dict]:
    if len(rows) != len(cases):
        raise ValueError(f"{method}: expected {len(cases)} rows, got {len(rows)}")
    by_id = {}
    truth_ids = {case["id"] for case in cases}
    for row in rows:
        case_id = row["case_id"]
        if case_id in by_id:
            raise ValueError(f"{method}: duplicate row {case_id}")
        if row["method"] != method:
            raise ValueError(f"{case_id}: expected method {method}, got {row['method']}")
        by_id[case_id] = row
    if set(by_id) != truth_ids:
        raise ValueError(f"{method}: case ids do not match the core manifest")
    for case in cases:
        row = by_id[case["id"]]
        decision = row["decision"]
        expected_objects = {obj["id"] for obj in case["objects"]}
        expected_cardinality = {obj["canonical"] for obj in case["objects"]}
        expected_relations = {relation["id"] for relation in case["relations"]}
        actual = (
            set(decision["objects"]),
            set(decision["cardinality"]),
            set(decision["relations"]),
        )
        expected = (expected_objects, expected_cardinality, expected_relations)
        if actual != expected:
            raise ValueError(f"{method} {case['id']}: decision keys do not match truth")
        values = [
            *decision["objects"].values(),
            *decision["cardinality"].values(),
            *decision["relations"].values(),
        ]
        if bool(row["exact"]) != all(values):
            raise ValueError(f"{method} {case['id']}: inconsistent exact flag")
    return {
        case_id: {**row["decision"], "exact": bool(row["exact"])}
        for case_id, row in by_id.items()
    }


def qwen_decisions(cases: list[dict], rows: list[dict], method: str) -> dict[str, dict]:
    if len(rows) != len(cases):
        raise ValueError(f"{method}: expected {len(cases)} Qwen rows, got {len(rows)}")
    by_id = {row["id"]: row for row in rows}
    if len(by_id) != len(rows) or set(by_id) != {case["id"] for case in cases}:
        raise ValueError(f"{method}: Qwen case ids do not match the core manifest")
    decisions = {}
    for case in cases:
        row = by_id[case["id"]]
        answers = row["answers"]
        objects = {
            obj["id"]: answers.get(f"presence:{obj['id']}", {}).get("answer") == "yes"
            for obj in case["objects"]
        }
        cardinality = {
            answer_id.removeprefix("cardinality:"): answer.get("answer") == "yes"
            for answer_id, answer in answers.items()
            if answer_id.startswith("cardinality:")
        }
        expected_cardinality_count = len({obj["canonical"] for obj in case["objects"]})
        if len(cardinality) != expected_cardinality_count:
            raise ValueError(
                f"{method} {case['id']}: Qwen cardinality count does not match truth"
            )
        relations = {relation["relation_id"]: bool(relation["pass"]) for relation in row["relation_rows"]}
        expected_relations = {relation["id"] for relation in case["relations"]}
        if set(relations) != expected_relations:
            raise ValueError(f"{method} {case['id']}: Qwen relation ids do not match truth")
        values = [*objects.values(), *cardinality.values(), *relations.values()]
        decisions[case["id"]] = {
            "objects": objects,
            "cardinality": cardinality,
            "relations": relations,
            "exact": all(values),
        }
    return decisions


def summary(cases: list[dict], decisions: dict[str, dict]) -> dict:
    categories = sorted({case["focus_capability"] for case in cases})
    difficulties = ("diagnostic", "normal", "hard")
    return {
        "overall": bucket(cases, decisions),
        "by_capability": {
            category: bucket(
                [case for case in cases if case["focus_capability"] == category], decisions
            )
            for category in categories
        },
        "by_difficulty": {
            difficulty: bucket(
                [
                    case
                    for case in cases
                    if (case["difficulty"] or "diagnostic") == difficulty
                ],
                decisions,
            )
            for difficulty in difficulties
        },
    }


def paper_row(method: str, result: dict) -> dict:
    primary = {
        category: values["primary_relation_micro"]
        for category, values in result["by_capability"].items()
    }
    return {
        "method": method,
        "presence": result["overall"]["presence_micro"],
        "cardinality": result["overall"]["cardinality_micro"],
        **{
            group: mean(primary[category] for category in categories)
            for group, categories in GROUPS.items()
        },
        "spatial_macro": mean(primary.values()),
        "case_exact": result["overall"]["exact_case_rate"],
        "diagnostic_exact": result["by_difficulty"]["diagnostic"]["exact_case_rate"],
        "normal_exact": result["by_difficulty"]["normal"]["exact_case_rate"],
        "hard_exact": result["by_difficulty"]["hard"]["exact_case_rate"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--visual-dir", type=Path, required=True)
    parser.add_argument("--qwen-dir", type=Path, required=True)
    parser.add_argument("--qwen38-dir", type=Path)
    parser.add_argument("--gpt56-dir", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    cases = load_jsonl(args.core)
    if len(cases) != 90:
        raise ValueError(f"expected frozen 90-case core, got {len(cases)}")
    results = {"visual": {}, "qwen32_diagnostic": {}}
    if args.qwen38_dir:
        results["qwen38_diagnostic"] = {}
    if args.gpt56_dir:
        results["gpt56_diagnostic"] = {}
    case_rows = {}
    for method in METHODS:
        visual_rows = load_jsonl(args.visual_dir / f"{method}_full90_final.jsonl")
        direct = validate_decisions(cases, visual_rows, method)
        qwen = qwen_decisions(
            cases, load_jsonl(args.qwen_dir / method / "vqa_results.jsonl"), method
        )
        results["visual"][method] = summary(cases, direct)
        results["qwen32_diagnostic"][method] = summary(cases, qwen)
        qwen38 = None
        if args.qwen38_dir:
            qwen38 = qwen_decisions(
                cases,
                load_jsonl(args.qwen38_dir / method / "vqa_results.jsonl"),
                method,
            )
            results["qwen38_diagnostic"][method] = summary(cases, qwen38)
        gpt56 = None
        if args.gpt56_dir:
            gpt56 = qwen_decisions(
                cases,
                load_jsonl(args.gpt56_dir / method / "vqa_results.jsonl"),
                method,
            )
            results["gpt56_diagnostic"][method] = summary(cases, gpt56)
        for case in cases:
            case_rows.setdefault(case["id"], {})[method] = {
                "visual": direct[case["id"]],
                "qwen32": qwen[case["id"]],
                **({"qwen38": qwen38[case["id"]]} if qwen38 else {}),
                **({"gpt56": gpt56[case["id"]]} if gpt56 else {}),
            }

    output = {
        "schema_version": "spatial_bench_v3_2_results",
        "case_count": len(cases),
        "definitions": {
            "spatial_macro": "Macro average of primary relation accuracy over all eight capabilities.",
            "case_exact": "All required objects, cardinalities, and explicit relations pass.",
            "qwen32_diagnostic": "Diagnostic only; direct visual adjudication is the headline judge.",
            "qwen38_diagnostic": "Diagnostic only; Qwen3.8-Max Preview does not replace direct visual adjudication.",
            "gpt56_diagnostic": "Diagnostic only; GPT-5.6 SOL xhigh does not replace direct visual adjudication.",
        },
        "judges": {
            "visual": {"role": "headline", "protocol": "blind multi-reviewer adjudication"},
            "qwen32_diagnostic": {
                "role": "diagnostic",
                "model": "Qwen3-VL-32B-Instruct",
            },
            **(
                {
                    "qwen38_diagnostic": {
                        "role": "diagnostic",
                        "model": "qwen3.8-max-preview",
                        "provider": "Alibaba Cloud Model Studio Token Plan",
                        "base_url": "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
                    }
                }
                if args.qwen38_dir
                else {}
            ),
            **(
                {
                    "gpt56_diagnostic": {
                        "role": "diagnostic",
                        "model": "gpt-5.6-sol",
                        "reasoning_effort": "xhigh",
                        "provider": "Right Code",
                        "base_url": "https://www.right.codes/codex/v1",
                    }
                }
                if args.gpt56_dir
                else {}
            ),
        },
        **{
            judge: {
                "rows": [paper_row(method, values[method]) for method in METHODS],
                "summary": values,
            }
            for judge, values in results.items()
        },
        "cases": [
            {
                "id": case["id"],
                "prompt_en": case["prompt_en"],
                "prompt_zh": case["prompt_zh"],
                "category": case["focus_capability"],
                "difficulty": case["difficulty"] or "diagnostic",
                "results": case_rows[case["id"]],
            }
            for case in cases
        ],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    with args.output_csv.open("w", newline="") as handle:
        fieldnames = ["judge", *output["visual"]["rows"][0]]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for judge in results:
            for row in output[judge]["rows"]:
                writer.writerow({"judge": judge, **row})
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_csv}")


if __name__ == "__main__":
    main()
