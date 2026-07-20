#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from openai import OpenAI

from v3_common import strict_score_case


DEFAULT_BASE_URL = "http://127.0.0.1:8001/v1"
SEATING_CANONICALS = {"bench", "chair", "sofa"}
YAW_DIRECTIONS = {"image_left", "image_right", "toward_camera", "away_from_camera", "unreadable"}
YAW_MAGNITUDES = {"front", "slight", "diagonal", "side", "unreadable"}


def image_data_url(path: Path) -> str:
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped, flags=re.I).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        return json.loads(stripped, strict=False)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0), strict=False)


def normalize_answer(value: object) -> str:
    answer = str(value or "").strip().lower()
    return answer if answer in {"yes", "no", "unclear"} else "unclear"


def build_questions(
    case: dict[str, Any],
    *,
    skip_relation_ids: set[str] | None = None,
) -> list[dict[str, str]]:
    evaluation = case["evaluation"]
    skipped = skip_relation_ids or set()
    questions = []
    for group in ("presence_checks", "cardinality_checks"):
        for check in evaluation[group]:
            questions.append({"id": check["id"], "question": check["question"]})
    for check in evaluation["relation_checks"]:
        if check["relation_id"] in skipped:
            continue
        questions.append({"id": check["positive"]["id"], "question": check["positive"]["question"]})
        if check.get("inverse"):
            questions.append({"id": check["inverse"]["id"], "question": check["inverse"]["question"]})
    return questions


def typed_yaw_relations(case: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        relation
        for relation in case.get("relations", [])
        if (
            relation.get("type") == "face"
            and relation.get("facing_intent") in {"left", "right"}
        )
        or (
            relation.get("type") == "face_angle"
            and relation.get("direction") in {"left", "right"}
            and relation.get("angle_degrees") in {30, 60, 90}
        )
    ]


def expected_yaw_magnitude(angle_degrees: int) -> str:
    return {30: "slight", 60: "diagonal", 90: "side"}[angle_degrees]


def build_typed_yaw_prompt(case: dict[str, Any], relation: dict[str, Any]) -> str:
    objects = {item["id"]: item for item in case.get("objects", [])}
    subject = objects[relation["subject"]]
    mention = subject.get("mention") or subject.get("canonical") or relation["subject"]
    context = f"Look only at the visible {mention}."
    continuous = relation.get("type") == "face_angle"
    magnitude_request = (
        " Also classify the horizontal turn magnitude from directly facing the viewer as "
        "front (less than 15 degrees), slight (15 to 45 degrees), diagonal (45 to 75 degrees), "
        "side (75 to 105 degrees), or unreadable. Do not estimate an exact angle."
        if continuous
        else ""
    )
    magnitude_field = ',"magnitude":"front|slight|diagonal|side|unreadable"' if continuous else ""
    if subject.get("canonical") in SEATING_CANONICALS:
        return (
            f"{context}\n"
            "First identify the upright backrest. Then identify the opposite open front edge of the seat, "
            f"where a seated person would face. Do not use shadows.{magnitude_request} Return JSON only with: "
            '{"part_visible":true|false,"backrest_side":"image_left|image_right|toward_camera|away_from_camera|unreadable",'
            '"open_seat_side":"image_left|image_right|toward_camera|away_from_camera|unreadable",'
            f'"reason":"short visual reason"{magnitude_field}}}.'
        )

    canonical = subject.get("canonical")
    part = {
        "screen_side": "screen side and its outward-facing normal",
        "lens_side": "lens side and the direction the lens points",
        "emitting_side": "light-emitting opening and the direction it points",
        "front_side": "distinct functional front side and its outward-facing normal",
    }.get(relation.get("facing_part"), "distinct functional front side and its outward-facing normal")
    if relation.get("facing_part") == "front_side":
        part = {
            "bookshelf": "open shelf side and its outward-facing direction",
            "cabinet": "door or opening side and its outward-facing direction",
            "refrigerator": "door and handle side and its outward-facing direction",
        }.get(canonical, part)
    return (
        f"{context}\n"
        f"Inspect the {part}. First decide whether that named part itself is clearly visible; do not infer it from shadows. "
        f"If visible, classify its outward horizontal direction in image coordinates.{magnitude_request} Return JSON only with: "
        '{"part_visible":true|false,"direction":"image_left|image_right|toward_camera|away_from_camera|unreadable",'
        f'"reason":"short visual reason"{magnitude_field}}}.'
    )


def typed_yaw_answers(
    case: dict[str, Any],
    relation: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    check = next(
        item for item in case["evaluation"]["relation_checks"] if item["relation_id"] == relation["id"]
    )
    subject = next(item for item in case.get("objects", []) if item["id"] == relation["subject"])
    seating = subject.get("canonical") in SEATING_CANONICALS
    direction = str(
        payload.get("open_seat_side") if seating else payload.get("direction") or "unreadable"
    ).strip().lower()
    if direction not in YAW_DIRECTIONS:
        direction = "unreadable"
    magnitude = str(payload.get("magnitude") or "unreadable").strip().lower()
    if magnitude not in YAW_MAGNITUDES:
        magnitude = "unreadable"
    part_visible = payload.get("part_visible") is not False if seating else payload.get("part_visible") is True
    reason = str(payload.get("reason") or f"typed yaw direction={direction} magnitude={magnitude}")
    continuous = relation.get("type") == "face_angle"
    if continuous:
        expected_direction = "image_left" if relation["direction"] == "left" else "image_right"
        opposite_direction = "image_right" if expected_direction == "image_left" else "image_left"
        expected_magnitude = expected_yaw_magnitude(int(relation["angle_degrees"]))
    else:
        expected_direction = "image_left" if relation["facing_intent"] == "left" else "image_right"
        opposite_direction = "image_right" if expected_direction == "image_left" else "image_left"
        expected_magnitude = ""
    unreadable = (
        not part_visible
        or direction == "unreadable"
        or (continuous and magnitude == "unreadable")
    )
    if unreadable:
        positive = inverse = "unclear"
    else:
        magnitude_matches = not continuous or magnitude == expected_magnitude
        positive = "yes" if direction == expected_direction and magnitude_matches else "no"
        inverse = "yes" if direction == opposite_direction and magnitude_matches else "no"
    answers = {
        check["positive"]["id"]: {"answer": positive, "confidence": 0, "reason": reason},
    }
    if check.get("inverse"):
        answers[check["inverse"]["id"]] = {"answer": inverse, "confidence": 0, "reason": reason}
    return answers


def call_typed_yaw(
    client: OpenAI,
    model: str,
    image_path: Path,
    case: dict[str, Any],
    relation: dict[str, Any],
    timeout: float,
    max_tokens: int,
) -> tuple[dict[str, dict[str, Any]], str]:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": build_typed_yaw_prompt(case, relation)},
                    {"type": "image_url", "image_url": {"url": image_data_url(image_path)}},
                ],
            }
        ],
        temperature=0,
        max_tokens=max_tokens,
        timeout=timeout,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or ""
    return typed_yaw_answers(case, relation, extract_json(raw)), raw


def index_images(root: Path, subdir: str) -> dict[str, str]:
    indexed = {}
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


def index_manifest(path: Path) -> tuple[dict[str, str], dict[str, bool]]:
    images = {}
    extraction = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        case_id = str(row.get("id") or row.get("prompt_id") or row.get("semantic_id") or "")
        image = next(
            (
                row.get(key)
                for key in ("final_image_path", "qwen_output_path", "final_rgb_path", "image_path", "image")
                if row.get(key)
            ),
            "",
        )
        if case_id and image:
            images[case_id] = str(image)
            extraction[case_id] = bool(row.get("extraction_exact", True))
    return images, extraction


def call_vqa(
    client: OpenAI,
    model: str,
    image_path: Path,
    questions: list[dict[str, str]],
    timeout: float,
    max_tokens: int,
) -> tuple[dict[str, Any], str]:
    aliases = {f"q{index:03d}": item["id"] for index, item in enumerate(questions, 1)}
    question_text = "\n".join(
        f"{index}. id=q{index:03d} question={item['question']}"
        for index, item in enumerate(questions, 1)
    )
    prompt = (
        "Judge every question independently using only visible evidence in the image. "
        "Do not infer hidden objects or relations. Answer exactly yes, no, or unclear; "
        "use unclear only when the requested evidence is genuinely unreadable. "
        "For in-front-of or behind relations, judge relative depth from the camera using position, scale, perspective, and support-plane cues; silhouette overlap or occlusion is not required. Do not reject a depth relation merely because both objects remain fully visible. "
        "For image-left or image-right position relations, compare the projected object centers unless the question explicitly requires complete separation. "
        "For partial occlusion, answer yes when the subject's visible silhouette overlaps the target and hides part of it while the target remains recognizable; recognizability is required and does not negate occlusion. "
        "Visible physical interpenetration, fused geometry, or an object passing through another object is not a valid partial occlusion. "
        "For image-left or image-right facing, judge the horizontal component of an imaginary arrow perpendicular outward from the named front, screen, lens, or opening. Do not label the direction by which side edge looks nearer: for a flat front face, a nearer right edge implies an image-left normal component, and a nearer left edge implies an image-right normal component. "
        "Before returning, make every yes/no answer consistent with its own visual reason.\n\n"
        "Return JSON only:\n"
        '{"answers":[{"id":"q001","answer":"yes|no|unclear","confidence":0.0,"reason":"short visual reason"}]}\n\n'
        f"Questions:\n{question_text}"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url(image_path)}},
                ],
            }
        ],
        temperature=0,
        max_tokens=max_tokens,
        timeout=timeout,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or ""
    parsed = extract_json(raw)
    answers = {}
    for item in parsed.get("answers", []):
        if not isinstance(item, dict):
            continue
        question_id = aliases.get(str(item.get("id")), str(item.get("id") or ""))
        if question_id:
            answers[question_id] = {
                "answer": normalize_answer(item.get("answer")),
                "confidence": item.get("confidence", 0),
                "reason": str(item.get("reason") or ""),
            }
    for question in questions:
        answers.setdefault(
            question["id"],
            {"answer": "unclear", "confidence": 0, "reason": "missing model answer"},
        )
    return answers, raw


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    temp.replace(path)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def pack(items: list[dict[str, Any]]) -> dict[str, Any]:
        relation_rows = [relation for item in items for relation in item.get("relation_rows", [])]
        primary_rows = [relation for relation in relation_rows if relation.get("primary") is True]
        presence_total = sum(item["presence_check_count"] for item in items)
        cardinality_total = sum(item["cardinality_check_count"] for item in items)
        return {
            "cases": len(items),
            "presence_micro": (
                sum(item["presence_score"] * item["presence_check_count"] for item in items) / presence_total
                if presence_total else 0.0
            ),
            "cardinality_micro": (
                sum(item["cardinality_score"] * item["cardinality_check_count"] for item in items) / cardinality_total
                if cardinality_total else 0.0
            ),
            "strict_relation_micro": sum(item["pass"] for item in relation_rows) / len(relation_rows) if relation_rows else 0.0,
            "primary_relation_micro": sum(item["pass"] for item in primary_rows) / len(primary_rows) if primary_rows else 0.0,
            "relation_count": len(relation_rows),
            "primary_relation_count": len(primary_rows),
            "case_exact_rate": sum(item["case_exact"] for item in items) / len(items) if items else 0.0,
            "errors": sum(bool(item.get("error")) for item in items),
        }

    by_capability: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_difficulty: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_capability[row["focus_capability"]].append(row)
        by_difficulty[str(row.get("difficulty") or "diagnostic")].append(row)
    return {
        "overall": pack(rows),
        "by_capability": {key: pack(value) for key, value in sorted(by_capability.items())},
        "by_difficulty": {key: pack(value) for key, value in sorted(by_difficulty.items())},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Spatial Bench v3 images with strict VQA scoring.")
    parser.add_argument("--cases", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--images-root", type=Path)
    source.add_argument("--image-manifest", type=Path)
    parser.add_argument("--image-subdir", default="")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--model", default="qwen3-vl-8b")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key", default="EMPTY")
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--judge-attempts", type=int, default=2)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--assume-extraction-exact", action="store_true")
    parser.add_argument(
        "--typed-yaw",
        action="store_true",
        help="Judge discrete and continuous yaw using named-part direction and visual magnitude bins.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    if args.case_id:
        requested = set(args.case_id)
        cases = [case for case in cases if case["id"] in requested]
    if args.limit:
        cases = cases[: args.limit]

    if args.image_manifest:
        images, extraction = index_manifest(args.image_manifest)
    else:
        images = index_images(args.images_root, args.image_subdir)
        extraction = {}
    missing = [case["id"] for case in cases if case["id"] not in images]
    if missing:
        raise SystemExit(f"Missing images for {len(missing)} cases: {', '.join(missing[:20])}")
    question_count = sum(len(build_questions(case)) for case in cases)
    print(f"cases={len(cases)} questions={question_count} images={len(images)}")
    if args.dry_run:
        return 0

    args.out_dir.mkdir(parents=True, exist_ok=True)
    result_path = args.out_dir / "vqa_results.jsonl"
    summary_path = args.out_dir / "summary.json"
    rows_by_id = {}
    if args.resume and result_path.exists():
        for raw in result_path.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                row = json.loads(raw)
                if not row.get("error"):
                    rows_by_id[row["id"]] = row

    client = OpenAI(
        api_key=args.api_key,
        base_url=args.base_url,
        timeout=args.timeout,
        max_retries=1,
    )
    try:
        for index, case in enumerate(cases, 1):
            case_id = case["id"]
            if case_id in rows_by_id:
                print(f"[{index}/{len(cases)}] {case_id} resumed")
                continue
            yaw_relations = typed_yaw_relations(case) if args.typed_yaw else []
            yaw_relation_ids = {relation["id"] for relation in yaw_relations}
            questions = build_questions(case, skip_relation_ids=yaw_relation_ids)
            all_questions = build_questions(case)
            image_path = Path(images[case_id])
            extraction_exact = args.assume_extraction_exact or extraction.get(case_id, False)
            error = ""
            raw_response: Any = ""
            answers = {}
            attempt_errors = []
            for _ in range(max(1, args.judge_attempts)):
                try:
                    answers, raw_response = call_vqa(
                        client,
                        args.model,
                        image_path,
                        questions,
                        args.timeout,
                        args.max_tokens,
                    )
                    break
                except Exception as exc:
                    attempt_errors.append(f"{exc.__class__.__name__}: {exc}")
            if not answers:
                error = " | ".join(attempt_errors)
            typed_raw = []
            for relation in yaw_relations:
                typed_errors = []
                typed_answers = {}
                typed_response = ""
                for _ in range(max(1, args.judge_attempts)):
                    try:
                        typed_answers, typed_response = call_typed_yaw(
                            client,
                            args.model,
                            image_path,
                            case,
                            relation,
                            args.timeout,
                            args.max_tokens,
                        )
                        break
                    except Exception as exc:
                        typed_errors.append(f"{exc.__class__.__name__}: {exc}")
                if typed_answers:
                    answers.update(typed_answers)
                else:
                    check = next(
                        item
                        for item in case["evaluation"]["relation_checks"]
                        if item["relation_id"] == relation["id"]
                    )
                    answers[check["positive"]["id"]] = {
                        "answer": "unclear",
                        "confidence": 0,
                        "reason": "typed yaw judge failed",
                    }
                    if check.get("inverse"):
                        answers[check["inverse"]["id"]] = {
                            "answer": "unclear",
                            "confidence": 0,
                            "reason": "typed yaw judge failed",
                        }
                    attempt_errors.extend(f"yaw {relation['id']}: {item}" for item in typed_errors)
                    error = " | ".join(attempt_errors)
                typed_raw.append({"relation_id": relation["id"], "response": typed_response})
            if yaw_relations:
                raw_response = {"general": raw_response, "typed_yaw": typed_raw}
            score = strict_score_case(case, answers, extraction_exact=extraction_exact)
            rows_by_id[case_id] = {
                "id": case_id,
                "subset": case["subset"],
                "difficulty": case.get("difficulty"),
                "focus_capability": case["focus_capability"],
                "model": args.model,
                "image": str(image_path),
                "question_count": len(all_questions),
                "presence_check_count": len(case["evaluation"]["presence_checks"]),
                "cardinality_check_count": len(case["evaluation"]["cardinality_checks"]),
                "answers": answers,
                "raw_response": raw_response,
                "error": error,
                **score,
            }
            ordered = [rows_by_id[item["id"]] for item in cases if item["id"] in rows_by_id]
            write_jsonl(result_path, ordered)
            print(
                f"[{index}/{len(cases)}] {case_id} presence={score['presence_score']:.3f} "
                f"relation={score['strict_relation_score']:.3f} exact={int(score['case_exact'])} "
                f"error={error[:120]}"
            )
    finally:
        client.close()

    rows = [rows_by_id[case["id"]] for case in cases]
    summary = {
        "schema_version": "spatial_bench_v3",
        "judge_model": args.model,
        "typed_yaw": args.typed_yaw,
        "result_path": str(result_path),
        **summarize(rows),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["overall"], ensure_ascii=False, indent=2))
    print(f"wrote {result_path}")
    print(f"wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
