#!/usr/bin/env python3
"""Build the v3.2 case viewer payload and method contact sheets."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


MODELS = (
    ("flux", "FLUX.1-schnell"),
    ("sdxl", "SDXL Base 1.0"),
    ("gligen", "LayoutGPT + GLIGEN"),
    ("lmd_plus", "LMD+"),
    ("boxdiff_xl", "LayoutGPT + BoxDiff-XL"),
    ("muses_qwen_rgb", "MUSES-Qwen RGB"),
    ("muses_qwen_sdxl", "MUSES-Qwen + SDXL"),
    ("muses_qwen_rgb_qwen_i2i", "MUSES-Qwen RGB + Qwen I2I"),
    ("t2i_blender_rgb", "T2I-Blender RGB"),
    ("t2i_blender_qwen", "T2I-Blender + Qwen I2I"),
)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def flatten_checks(case: dict) -> list[dict]:
    evaluation = case["evaluation"]
    checks = [
        {
            "kind": "presence",
            "id": item["id"],
            "question": item["question"],
            "expected": item["expected_answer"],
        }
        for item in evaluation["presence_checks"]
    ]
    checks.extend(
        {
            "kind": "cardinality",
            "id": item["id"],
            "question": item["question"],
            "expected": item["expected_answer"],
        }
        for item in evaluation["cardinality_checks"]
    )
    for item in evaluation["relation_checks"]:
        checks.append(
            {
                "kind": "relation",
                "id": item["positive"]["id"],
                "question": item["positive"]["question"],
                "expected": item["positive"]["expected_answer"],
            }
        )
        if item.get("inverse"):
            checks.append(
                {
                    "kind": "inverse",
                    "id": item["inverse"]["id"],
                    "question": item["inverse"]["question"],
                    "expected": item["inverse"]["expected_answer"],
                }
            )
    return checks


def visual_result(case: dict, row: dict, image: str) -> dict:
    decision = row["decision"]
    reason = row.get("notes", "Direct visual review.")
    answers = {
        f"presence:{object_id}": {
            "answer": "yes" if passed else "no",
            "reason": reason,
        }
        for object_id, passed in decision["objects"].items()
    }
    answers.update(
        {
            f"cardinality:{canonical}": {
                "answer": "yes" if passed else "no",
                "reason": reason,
            }
            for canonical, passed in decision["cardinality"].items()
        }
    )
    evaluation = case["evaluation"]
    for item in evaluation["relation_checks"]:
        relation_id = item["relation_id"]
        passed = decision["relations"][relation_id]
        answers[item["positive"]["id"]] = {
            "answer": "yes" if passed else "no",
            "reason": reason,
        }
        if item.get("inverse"):
            answers[item["inverse"]["id"]] = {
                "answer": "no" if passed else "unclear",
                "reason": reason,
            }
    primary_ids = {relation["id"] for relation in case["relations"] if relation["primary"]}
    return {
        "image": image,
        "presence": sum(decision["objects"].values()) / len(decision["objects"]),
        "cardinality": sum(decision["cardinality"].values()) / len(decision["cardinality"]),
        "relation": sum(decision["relations"].values()) / len(decision["relations"]),
        "primary_relation": sum(decision["relations"][key] for key in primary_ids)
        / len(primary_ids),
        "exact": bool(row["exact"]),
        "error": "",
        "answers": answers,
        "judged": True,
        "judge": "Direct visual multi-reviewer adjudication",
        "audit_notes": reason,
        "audit_confidence": row.get("confidence", ""),
        "adjudicated": bool(row.get("adjudicated", False)),
    }


def qwen_result(row: dict) -> dict:
    return {
        "presence": row["presence_score"],
        "cardinality": row["cardinality_score"],
        "relation": row["strict_relation_score"],
        "primary_relation": row["primary_relation_score"],
        "exact": bool(row["case_exact"]),
        "error": row.get("error", ""),
        "answers": row["answers"],
        "judged": not bool(row.get("error")),
        "judge": "Qwen3-VL-32B-Instruct",
    }


def contact_sheet(paths: list[Path], labels: list[str], output: Path) -> None:
    columns = 6
    tile_width = 190
    image_size = 180
    tile_height = 207
    sheet = Image.new(
        "RGB",
        (columns * tile_width, math.ceil(len(paths) / columns) * tile_height),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, (path, label) in enumerate(zip(paths, labels)):
        x = index % columns * tile_width + 5
        y = index // columns * tile_height + 5
        with Image.open(path) as image:
            thumb = ImageOps.fit(
                image.convert("RGB"),
                (image_size, image_size),
                method=Image.Resampling.LANCZOS,
            )
        sheet.paste(thumb, (x, y))
        draw.text((x, y + image_size + 5), label, fill="#20252d", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, "JPEG", quality=88, optimize=True)


def convert_web_image(source: Path, output: Path) -> None:
    if output.is_file() and output.stat().st_mtime_ns >= source.stat().st_mtime_ns:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.save(output, "WEBP", quality=86, method=6)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--viewer-root", type=Path, required=True)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--materialized", type=Path, required=True)
    parser.add_argument("--visual-dir", type=Path, required=True)
    parser.add_argument("--qwen-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    core = load_jsonl(args.core)
    materialized = {row["id"]: row for row in json.loads(args.materialized.read_text())}
    case_ids = [row["id"] for row in core]
    if len(case_ids) != 90 or set(case_ids) != set(materialized):
        raise ValueError("core and materialized manifests must contain the same 90 cases")

    visual = {}
    qwen = {}
    for method, _ in MODELS:
        visual_rows = load_jsonl(args.visual_dir / f"{method}_full90_final.jsonl")
        qwen_rows = load_jsonl(args.qwen_dir / method / "vqa_results.jsonl")
        visual[method] = {row["case_id"]: row for row in visual_rows}
        qwen[method] = {row["id"]: row for row in qwen_rows}
        if set(visual[method]) != set(case_ids) or set(qwen[method]) != set(case_ids):
            raise ValueError(f"{method}: incomplete visual or Qwen32 coverage")

    cases = []
    image_root = args.viewer_root / "generated/v3_full90_v32"
    for core_case in core:
        case_id = core_case["id"]
        case = materialized[case_id]
        results = {}
        for method, _ in MODELS:
            source_image = image_root / method / "images" / f"{case_id}.png"
            if not source_image.is_file():
                raise FileNotFoundError(source_image)
            image = image_root / method / "web" / f"{case_id}.webp"
            convert_web_image(source_image, image)
            relative = str(image.relative_to(args.viewer_root))
            result = visual_result(case, visual[method][case_id], relative)
            result["qwen32"] = qwen_result(qwen[method][case_id])
            results[method] = result
        cases.append(
            {
                "id": case_id,
                "subset": core_case["subset"],
                "difficulty": core_case["difficulty"] or "diagnostic",
                "category": core_case["focus_capability"],
                "prompt_en": core_case["prompt_en"],
                "prompt_zh": core_case["prompt_zh"],
                "derived": case["derived"],
                "objects": core_case["objects"],
                "relations": core_case["relations"],
                "checks": flatten_checks(case),
                "results": results,
            }
        )

    output = {
        "schema_version": "spatial_bench_v3_2_viewer",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "judge": "Direct visual multi-reviewer adjudication",
        "models": [{"id": method, "label": label} for method, label in MODELS],
        "pipeline": {
            "case_count": 90,
            "note": "v3.2: six absolute-location diagnostics plus twelve cases per remaining capability.",
        },
        "judges": [
            {
                "id": "visual",
                "label": "Visual adjudication",
                "description": "Blind direct image review with independent failed-case adjudication.",
            },
            {
                "id": "qwen32",
                "label": "Qwen3-VL-32B",
                "description": "Secondary diagnostic judge using the same atomic checklist.",
            },
        ],
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")

    for method, _ in MODELS:
        paths = [image_root / method / "images" / f"{case_id}.png" for case_id in case_ids]
        contact_sheet(paths, case_ids, image_root / f"{method}_contact_sheet.jpg")
    print(f"built viewer cases={len(cases)} methods={len(MODELS)} output={args.output}")


if __name__ == "__main__":
    main()
