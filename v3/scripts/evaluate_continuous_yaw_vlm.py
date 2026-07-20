#!/usr/bin/env python3
"""Evaluate v3.2 camera-relative continuous yaw using only final-image VLM evidence."""

from __future__ import annotations

import argparse
import base64
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from PIL import Image

from continuous_yaw_v32 import (
    build_localization_prompt,
    build_reference_card,
    build_yaw_judge_prompt,
    continuous_yaw_relations,
    crop_subject,
    normalized_bbox,
    score_yaw_prediction,
    validate_continuous_yaw_case,
)
from v3_common import load_cases


def image_data_url(path: Path) -> str:
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def extract_json(text: str) -> dict[str, Any]:
    stripped = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.I).strip()
    try:
        return json.loads(stripped, strict=False)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0), strict=False)


def index_images(root: Path, subdir: str) -> dict[str, str]:
    indexed: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        if subdir and path.parent.name != subdir:
            continue
        case_id = re.sub(r"_0$", "", path.stem)
        if case_id in indexed:
            raise ValueError(f"Duplicate image for {case_id}: {indexed[case_id]} and {path}")
        indexed[case_id] = str(path)
    return indexed


def index_manifest(path: Path) -> dict[str, str]:
    images: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        case_id = str(row.get("id") or row.get("prompt_id") or row.get("semantic_id") or "")
        image = next(
            (row.get(key) for key in ("final_image_path", "qwen_output_path", "final_rgb_path", "image_path", "image") if row.get(key)),
            "",
        )
        if case_id and image:
            images[case_id] = str(image)
    return images


def call_json(client: Any, model: str, text: str, images: list[Path], timeout: float) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": text}]
    content.extend({"type": "image_url", "image_url": {"url": image_data_url(path)}} for path in images)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": content}],
        temperature=0,
        max_tokens=512,
        timeout=timeout,
        response_format={"type": "json_object"},
    )
    return extract_json(response.choices[0].message.content or "")


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def pack(items: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(items)
        return {
            "relations": total,
            "direction_accuracy": sum(item["direction_pass"] for item in items) / total if total else 0.0,
            "magnitude_bin_accuracy": sum(item["magnitude_bin_pass"] for item in items) / total if total else 0.0,
            "joint_accuracy": sum(item["joint_pass"] for item in items) / total if total else 0.0,
            "unclear_rate": sum(item["unclear"] for item in items) / total if total else 0.0,
        }

    by_angle: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_direction: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_angle[str(row["angle_degrees"])].append(row)
        by_direction[row["expected_direction"]].append(row)
    return {
        "protocol": "continuous_yaw_v3.2_vlm_only",
        "overall": pack(rows),
        "by_angle": {key: pack(value) for key, value in sorted(by_angle.items())},
        "by_direction": {key: pack(value) for key, value in sorted(by_direction.items())},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--images-root", type=Path)
    source.add_argument("--image-manifest", type=Path)
    parser.add_argument("--image-subdir", default="")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--model", default="Qwen3-VL-32B-Instruct")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001/v1")
    parser.add_argument("--api-key", default="EMPTY")
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cases = load_cases(args.cases)
    if args.case_id:
        selected = set(args.case_id)
        cases = [case for case in cases if case["id"] in selected]
    errors = [error for case in cases for error in validate_continuous_yaw_case(case)]
    if errors:
        raise SystemExit("\n".join(errors))
    images = index_manifest(args.image_manifest) if args.image_manifest else index_images(args.images_root, args.image_subdir)
    missing = sorted(case["id"] for case in cases if case["id"] not in images)
    if missing:
        raise SystemExit(f"Missing images: {missing}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    reference_path = build_reference_card(args.out_dir / "yaw_reference_bins.png")
    if args.dry_run:
        print(json.dumps({"cases": len(cases), "relations": sum(len(continuous_yaw_relations(case)) for case in cases), "reference": str(reference_path)}))
        return 0

    from openai import OpenAI

    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    rows: list[dict[str, Any]] = []
    for case in cases:
        object_map = {item["id"]: item for item in case["objects"]}
        image_path = Path(images[case["id"]])
        with Image.open(image_path) as image:
            width, height = image.size
        crop_cache: dict[str, Path] = {}
        for relation in continuous_yaw_relations(case):
            subject_id = relation["subject"]
            subject = object_map[subject_id]
            if subject_id not in crop_cache:
                localization = call_json(
                    client,
                    args.model,
                    build_localization_prompt(subject.get("mention") or subject.get("canonical") or subject_id),
                    [image_path],
                    args.timeout,
                )
                bbox = normalized_bbox(localization, width, height)
                crop_cache[subject_id] = (
                    crop_subject(image_path, bbox, args.out_dir / "crops" / case["id"] / f"{subject_id}.png")
                    if bbox
                    else image_path
                )
            prediction = call_json(
                client,
                args.model,
                build_yaw_judge_prompt(case, relation),
                [image_path, crop_cache[subject_id], reference_path],
                args.timeout,
            )
            scored = score_yaw_prediction(relation, prediction)
            rows.append(
                {
                    "case_id": case["id"],
                    "relation_id": relation["id"],
                    "subject": subject_id,
                    "angle_degrees": int(float(relation["angle_degrees"])),
                    "image_path": str(image_path),
                    "subject_crop_path": str(crop_cache[subject_id]),
                    **scored,
                    "raw_prediction": prediction,
                }
            )

    results_path = args.out_dir / "continuous_yaw_results.jsonl"
    results_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    (args.out_dir / "summary.json").write_text(json.dumps(summarize(rows), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summarize(rows)["overall"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
