#!/usr/bin/env python3
"""Merge blind visual audits and build the frozen ten-method result tables."""

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


METHODS = [
    "flux",
    "sdxl",
    "gligen",
    "lmd_plus",
    "boxdiff_xl",
    "muses_qwen_rgb",
    "muses_qwen_sdxl",
    "muses_qwen_rgb_qwen_i2i",
    "t2i_blender",
    "t2i_blender_qwen",
]

CATEGORY_GROUPS = {
    "layout_2d": ["absolute_location_2d", "relative_position_2d"],
    "depth_contact_occlusion": ["depth_front_back", "support_contact", "occlusion_visibility"],
    "orientation_yaw": ["orientation_facing", "yaw_direction"],
    "multi_relation": ["multi_relation_composition"],
}


def load_jsonl(path):
    with path.open() as handle:
        return [json.loads(line) for line in handle if line.strip()]


def audit_path(audit_dir, stem):
    final = audit_dir / f"{stem}_final.jsonl"
    return final if final.exists() else audit_dir / f"{stem}_agent.jsonl"


def strict_relation_pass(answers, relation_id, has_inverse):
    positive = answers.get(f"{relation_id}:positive", {}).get("answer") == "yes"
    inverse_id = f"{relation_id}:inverse"
    if not has_inverse or inverse_id not in answers:
        return positive
    return positive and answers[inverse_id].get("answer") == "no"


def mean(values):
    values = [value for value in values if value is not None]
    return sum(values) / len(values) if values else None


def score_bucket(cases, method_id, field="direct"):
    totals = defaultdict(int)
    for case in cases:
        result = case["results"][method_id]
        score = result if field == "direct" else result["qwen32"]
        object_count = len(case["objects"])
        cardinality_count = sum(check["kind"] == "cardinality" for check in case["checks"])
        relation_count = len(case["relations"])
        primary_count = sum(bool(relation.get("primary")) for relation in case["relations"])
        totals["cases"] += 1
        totals["presence_total"] += object_count
        totals["cardinality_total"] += cardinality_count
        totals["relation_total"] += relation_count
        totals["primary_total"] += primary_count
        totals["presence_pass"] += round(score["presence"] * object_count)
        totals["cardinality_pass"] += round(score["cardinality"] * cardinality_count)
        totals["relation_pass"] += round(score["relation"] * relation_count)
        totals["primary_pass"] += round(score["primary_relation"] * primary_count)
        totals["exact_pass"] += bool(score["exact"])
    out = dict(totals)
    for name in ("presence", "cardinality", "relation", "primary"):
        out[f"{name}_micro"] = totals[f"{name}_pass"] / totals[f"{name}_total"]
    out["strict_relation_micro"] = out.pop("relation_micro")
    out["primary_relation_micro"] = out.pop("primary_micro")
    out["exact_case_rate"] = totals["exact_pass"] / totals["cases"]
    return out


def build_summary(cases, field="direct"):
    summary = {"overall": {}, "by_capability": {}, "by_difficulty": {}}
    categories = sorted({case["category"] for case in cases})
    difficulties = sorted({case["difficulty"] for case in cases})
    for method_id in METHODS:
        summary["overall"][method_id] = score_bucket(cases, method_id, field)
    for category in categories:
        rows = [case for case in cases if case["category"] == category]
        summary["by_capability"][category] = {
            method_id: score_bucket(rows, method_id, field) for method_id in METHODS
        }
    for difficulty in difficulties:
        rows = [case for case in cases if case["difficulty"] == difficulty]
        summary["by_difficulty"][difficulty] = {
            method_id: score_bucket(rows, method_id, field) for method_id in METHODS
        }
    return summary


def paper_rows(summary):
    rows = []
    for method_id in METHODS:
        overall = summary["overall"][method_id]
        by_category = summary["by_capability"]
        primary = {
            category: by_category[category][method_id]["primary_relation_micro"]
            for category in by_category
        }
        row = {
            "method": method_id,
            "presence": overall["presence_micro"],
            "cardinality": overall["cardinality_micro"],
            "layout_2d": mean(primary[name] for name in CATEGORY_GROUPS["layout_2d"]),
            "depth_contact_occlusion": mean(primary[name] for name in CATEGORY_GROUPS["depth_contact_occlusion"]),
            "orientation_yaw": mean(primary[name] for name in CATEGORY_GROUPS["orientation_yaw"]),
            "multi_relation": primary["multi_relation_composition"],
            "spatial_macro": mean(primary.values()),
            "case_exact": overall["exact_case_rate"],
            "diagnostic_exact": summary["by_difficulty"]["diagnostic"][method_id]["exact_case_rate"],
            "normal_exact": summary["by_difficulty"]["normal"][method_id]["exact_case_rate"],
            "hard_exact": summary["by_difficulty"]["hard"][method_id]["exact_case_rate"],
        }
        rows.append(row)
    return rows


def merge_cardinality(viewer, audit_dir):
    sources = [
        ("card_flux_sdxl", ["flux", "sdxl"]),
        ("card_gligen_lmd", ["gligen", "lmd_plus"]),
        ("card_boxdiff_blender", ["boxdiff_xl", "t2i_blender"]),
    ]
    cases = {case["id"]: case for case in viewer["cases"]}
    for stem, methods in sources:
        rows = load_jsonl(audit_path(audit_dir, stem))
        if len(rows) != len(cases):
            raise ValueError(f"{stem}: expected {len(cases)} rows, got {len(rows)}")
        for row in rows:
            case = cases[row["id"]]
            expected = {check["id"] for check in case["checks"] if check["kind"] == "cardinality"}
            for method_id in methods:
                result = case["results"][method_id]
                decisions = row["methods"][method_id]["cardinality"]
                if set(decisions) != expected:
                    raise ValueError(f"{row['id']} {method_id}: cardinality ids do not match truth")
                for check_id, decision in decisions.items():
                    result["answers"][check_id] = decision
                result["cardinality"] = sum(
                    decision["answer"] == "yes" for decision in decisions.values()
                ) / len(decisions)
                result["exact"] = bool(
                    result["presence"] == 1 and result["cardinality"] == 1 and result["relation"] == 1
                )
                result["judge"] = "direct_visual_subagent_adjudication_v2"


def merge_blender_qwen(viewer, audit_dir):
    rows = load_jsonl(audit_path(audit_dir, "full_blender_qwen"))
    cases = {case["id"]: case for case in viewer["cases"]}
    if len(rows) != len(cases):
        raise ValueError(f"full_blender_qwen: expected {len(cases)} rows, got {len(rows)}")
    for row in rows:
        case = cases[row["id"]]
        answers = {}
        for decision in row["presence"] + row["cardinality"]:
            answers[decision["check_id"]] = {
                "answer": decision["answer"],
                "confidence": row["confidence"],
                "reason": decision["reason"],
            }
        relation_results = {}
        for decision in row["relations"]:
            relation_id = decision["relation_id"]
            relation_results[relation_id] = bool(decision["strict_pass"])
            answers[f"{relation_id}:positive"] = {
                "answer": decision["positive_answer"],
                "confidence": row["confidence"],
                "reason": decision["reason"],
            }
            if decision.get("inverse_answer") is not None:
                answers[f"{relation_id}:inverse"] = {
                    "answer": decision["inverse_answer"],
                    "confidence": row["confidence"],
                    "reason": decision["reason"],
                }
        relation_ids = {relation["id"] for relation in case["relations"]}
        if set(relation_results) != relation_ids:
            raise ValueError(f"{row['id']}: relation ids do not match truth")
        presence = sum(item["answer"] == "yes" for item in row["presence"]) / len(row["presence"])
        cardinality = sum(item["answer"] == "yes" for item in row["cardinality"]) / len(row["cardinality"])
        relation = sum(relation_results.values()) / len(relation_results)
        primary = [relation_results[item["id"]] for item in case["relations"] if item.get("primary")]
        result = case["results"]["t2i_blender_qwen"]
        result.update({
            "presence": presence,
            "cardinality": cardinality,
            "relation": relation,
            "primary_relation": sum(primary) / len(primary),
            "exact": bool(presence == 1 and cardinality == 1 and relation == 1),
            "error": "",
            "answers": answers,
            "judged": True,
            "judge": "direct_visual_subagent_adjudication_v2",
            "audit_notes": row["summary"],
            "audit_confidence": row["confidence"],
            "adjudicated": audit_path(audit_dir, "full_blender_qwen").name.endswith("_final.jsonl"),
        })


def recompute_direct_exact(viewer):
    for case in viewer["cases"]:
        for method_id in METHODS:
            result = case["results"][method_id]
            result["exact"] = bool(
                result["presence"] == 1 and result["cardinality"] == 1 and result["relation"] == 1
            )


def audit_rows(viewer):
    rows = []
    for case in viewer["cases"]:
        methods = {}
        inverse_ids = {check["relation_id"] for check in case["checks"] if check["kind"] == "inverse"}
        for method_id in METHODS:
            result = case["results"][method_id]
            methods[method_id] = {
                "presence": {
                    obj["id"]: "pass" if result["answers"].get(f"presence:{obj['id']}", {}).get("answer") == "yes" else "fail"
                    for obj in case["objects"]
                },
                "cardinality": {
                    check["id"]: "pass" if result["answers"].get(check["id"], {}).get("answer") == "yes" else "fail"
                    for check in case["checks"] if check["kind"] == "cardinality"
                },
                "relations": {
                    relation["id"]: "pass" if strict_relation_pass(result["answers"], relation["id"], relation["id"] in inverse_ids) else "fail"
                    for relation in case["relations"]
                },
                "exact": bool(result["exact"]),
                "notes": result.get("audit_notes", ""),
            }
        rows.append({"case_id": case["id"], "prompt": case["prompt_en"], "methods": methods})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-dir", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    viewer_path = args.repo / "data/v3_viewer_cases.json"
    viewer = json.loads(viewer_path.read_text())
    merge_cardinality(viewer, args.audit_dir)
    merge_blender_qwen(viewer, args.audit_dir)
    recompute_direct_exact(viewer)
    viewer["schema_version"] = "spatial_bench_v3_viewer_ten_method_adjudicated"
    viewer["generated_at"] = datetime.now(timezone.utc).isoformat()
    viewer["judge"] = "Direct visual subagent adjudication with strict cardinality"
    viewer_path.write_text(json.dumps(viewer, ensure_ascii=False, indent=2) + "\n")

    visual = build_summary(viewer["cases"])
    qwen32 = build_summary(viewer["cases"], "qwen32")
    summary = {
        "schema_version": "subagent_visual_audit_v3_ten_method_adjudicated",
        "judge": "blind direct visual subagents plus independent disagreement adjudication; strict unclear=fail",
        "all_93": visual,
    }
    summary_path = args.repo / "data/v3_visual_audit_20260718_ten_method_adjudicated_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")

    case_path = args.repo / "data/v3_visual_audit_20260718_ten_method_adjudicated.jsonl"
    with case_path.open("w") as handle:
        for row in audit_rows(viewer):
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    final = {
        "schema_version": "spatial_bench_v3_final_paper_table",
        "definitions": {
            "spatial_macro": "Macro average of primary relation accuracy over the eight original categories.",
            "case_exact": "All required object instances, cardinalities, and explicit relations pass.",
        },
        "visual": {"rows": paper_rows(visual), "summary": visual},
        "qwen32_diagnostic": {"rows": paper_rows(qwen32), "summary": qwen32},
    }
    final_path = args.repo / "data/v3_final_paper_table_20260718.json"
    final_path.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n")
    csv_path = args.repo / "data/v3_final_paper_table_20260718.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["judge"] + list(final["visual"]["rows"][0]))
        writer.writeheader()
        for judge in ("visual", "qwen32_diagnostic"):
            for row in final[judge]["rows"]:
                writer.writerow({"judge": judge, **row})

    print(f"wrote {viewer_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {case_path}")
    print(f"wrote {final_path}")
    print(f"wrote {csv_path}")


if __name__ == "__main__":
    main()
