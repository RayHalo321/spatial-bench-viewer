#!/usr/bin/env python3
"""Shared protocol helpers for the Spatial Bench v3.2 continuous-yaw extension."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ANGLE_TO_BIN = {30: "slight", 60: "diagonal", 90: "side"}
DIRECTIONS = {"left", "right", "front", "back", "unclear"}
YAW_BINS = {"front", "slight", "diagonal", "side", "back", "unclear"}
FACING_PART_LABELS = {
    "front_side": "functional front side",
    "screen_side": "screen side",
    "lens_side": "lens side",
    "emitting_side": "light-emitting side",
}


def continuous_yaw_relations(case: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        relation
        for relation in case.get("relations", [])
        if relation.get("type") == "face_angle"
        and relation.get("angle_reference") == "facing_viewer"
        and relation.get("frame") == "image"
    ]


def expected_yaw_bin(degrees: object) -> str:
    try:
        angle = int(float(degrees))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid continuous-yaw angle: {degrees!r}") from exc
    if angle not in ANGLE_TO_BIN:
        raise ValueError(f"Continuous yaw supports only 30, 60, or 90 degrees, got {angle}")
    return ANGLE_TO_BIN[angle]


def validate_continuous_yaw_case(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    objects = {item.get("id") for item in case.get("objects", [])}
    relations = continuous_yaw_relations(case)
    if not relations:
        errors.append(f"{case.get('id', '<unknown>')}: no camera-relative continuous-yaw relation")
    for relation in relations:
        relation_id = relation.get("id", "<unknown>")
        if relation.get("subject") not in objects:
            errors.append(f"{relation_id}: subject is not declared in objects")
        if relation.get("direction") not in {"left", "right"}:
            errors.append(f"{relation_id}: direction must be left or right")
        try:
            expected_yaw_bin(relation.get("angle_degrees"))
        except ValueError as exc:
            errors.append(f"{relation_id}: {exc}")
        if relation.get("facing_part") not in FACING_PART_LABELS:
            errors.append(f"{relation_id}: facing_part must name a visually readable functional side")
    return errors


def build_localization_prompt(mention: str) -> str:
    return (
        f"Locate the single {mention} that is the subject of the spatial request. "
        "Use only visible image evidence. Return JSON only with "
        '{"subject_visible":true|false,"bbox_2d":[x1,y1,x2,y2],"reason":"short reason"}. '
        "bbox_2d uses integer coordinates from 0 to 1000, with (0,0) at image top-left. "
        "If the subject is absent or cannot be uniquely identified, set subject_visible=false and bbox_2d=null."
    )


def normalized_bbox(payload: dict[str, Any], width: int, height: int) -> tuple[int, int, int, int] | None:
    if payload.get("subject_visible") is not True:
        return None
    raw = payload.get("bbox_2d")
    if not isinstance(raw, list) or len(raw) != 4:
        return None
    try:
        x1, y1, x2, y2 = [float(value) for value in raw]
    except (TypeError, ValueError):
        return None
    x1, x2 = sorted((max(0.0, min(1000.0, x1)), max(0.0, min(1000.0, x2))))
    y1, y2 = sorted((max(0.0, min(1000.0, y1)), max(0.0, min(1000.0, y2))))
    if x2 - x1 < 5 or y2 - y1 < 5:
        return None
    return (
        int(x1 * width / 1000),
        int(y1 * height / 1000),
        max(1, int(x2 * width / 1000)),
        max(1, int(y2 * height / 1000)),
    )


def crop_subject(image_path: Path, bbox: tuple[int, int, int, int], output_path: Path) -> Path:
    image = Image.open(image_path).convert("RGB")
    x1, y1, x2, y2 = bbox
    pad = max(12, int(max(x2 - x1, y2 - y1) * 0.18))
    crop = image.crop((max(0, x1 - pad), max(0, y1 - pad), min(image.width, x2 + pad), min(image.height, y2 + pad)))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    crop.save(output_path)
    return output_path


def build_yaw_judge_prompt(case: dict[str, Any], relation: dict[str, Any]) -> str:
    objects = {item["id"]: item for item in case.get("objects", [])}
    subject = objects[relation["subject"]]
    mention = subject.get("mention") or subject.get("canonical") or relation["subject"]
    part = FACING_PART_LABELS[relation["facing_part"]]
    return (
        "Judge one continuous-yaw request using only the three supplied images. "
        "Image 1 is the complete final RGB image, Image 2 is a crop of the requested subject, "
        "and Image 3 is the fixed yaw-bin reference card. The method identity is unknown.\n"
        f"Prompt: {case['prompt_en']}\n"
        f"Subject: {mention}. Named front part: {part}.\n"
        "The reference pose is the named front part facing the camera. Left and right are image coordinates. "
        "Classify the horizontal turn of that part's outward direction, not the nearer side edge and not the shadow.\n"
        "Yaw bins are fixed: front=0-15 degrees, slight=15-45, diagonal=45-75, side=75-105, and back=>105. "
        "At slight or diagonal yaw, front_part_visible is true only when the named front surface is visibly readable. "
        "At side yaw, it may also be true when a narrow edge and object shape are sufficient to determine the named part's outward direction. "
        "If the subject, named part, turn direction, or magnitude is ambiguous, use unclear rather than guessing.\n"
        "Return JSON only with: "
        '{"subject_visible":true|false,"front_part_visible":true|false,'
        '"turn_direction":"left|right|front|back|unclear",'
        '"yaw_bin":"front|slight|diagonal|side|back|unclear",'
        '"confidence":0.0,"reason":"short visual reason"}.'
    )


def score_yaw_prediction(relation: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    direction = str(payload.get("turn_direction") or "unclear").strip().lower()
    yaw_bin = str(payload.get("yaw_bin") or "unclear").strip().lower()
    if direction not in DIRECTIONS:
        direction = "unclear"
    if yaw_bin not in YAW_BINS:
        yaw_bin = "unclear"
    subject_visible = payload.get("subject_visible") is True
    front_visible = payload.get("front_part_visible") is True
    readable = subject_visible and front_visible and direction != "unclear" and yaw_bin != "unclear"
    direction_pass = readable and direction == relation["direction"]
    magnitude_pass = readable and yaw_bin == expected_yaw_bin(relation["angle_degrees"])
    return {
        "subject_visible": subject_visible,
        "front_part_visible": front_visible,
        "expected_direction": relation["direction"],
        "predicted_direction": direction,
        "expected_yaw_bin": expected_yaw_bin(relation["angle_degrees"]),
        "predicted_yaw_bin": yaw_bin,
        "direction_pass": bool(direction_pass),
        "magnitude_bin_pass": bool(magnitude_pass),
        "joint_pass": bool(direction_pass and magnitude_pass),
        "unclear": not readable,
        "confidence": payload.get("confidence", 0),
        "reason": str(payload.get("reason") or ""),
    }


def build_reference_card(output_path: Path) -> Path:
    import math

    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1750, 500
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 34)
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 24)
    except OSError:
        title_font = font = ImageFont.load_default()
    draw.text((30, 18), "Camera-relative yaw bins (top view)", fill="black", font=title_font)
    draw.text((30, 60), "Red edge = functional front. Blue arrow = outward facing direction.", fill=(55, 55, 55), font=font)
    cells = [
        (-90, "side", "LEFT"),
        (-60, "diagonal", "LEFT"),
        (-30, "slight", "LEFT"),
        (0, "front", "FRONT"),
        (30, "slight", "RIGHT"),
        (60, "diagonal", "RIGHT"),
        (90, "side", "RIGHT"),
    ]
    for index, (degrees, label, direction) in enumerate(cells):
        x0 = 20 + index * 247
        y0 = 100
        draw.rounded_rectangle((x0, y0, x0 + 228, y0 + 370), radius=8, outline=(190, 190, 190), width=2)
        cx, cy = x0 + 114, y0 + 170
        angle = math.radians(degrees)
        forward = (math.sin(angle), -math.cos(angle))
        side = (math.cos(angle), math.sin(angle))
        half_w, half_h = 62, 38
        corners = []
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            corners.append((cx + sx * half_w * side[0] + sy * half_h * forward[0], cy + sx * half_w * side[1] + sy * half_h * forward[1]))
        draw.polygon(corners, fill=(222, 228, 235), outline=(55, 65, 80))
        draw.line((corners[0], corners[1]), fill=(220, 45, 45), width=9)
        arrow_end = (cx + forward[0] * 92, cy + forward[1] * 92)
        draw.line((cx, cy, *arrow_end), fill=(35, 95, 190), width=6)
        draw.ellipse((arrow_end[0] - 7, arrow_end[1] - 7, arrow_end[0] + 7, arrow_end[1] + 7), fill=(35, 95, 190))
        angle_text = "0 deg" if degrees == 0 else f"{abs(degrees)} deg {direction}"
        draw.text((x0 + 16, y0 + 286), angle_text, fill="black", font=font)
        draw.text((x0 + 16, y0 + 326), label.upper(), fill=(35, 95, 190), font=font)
    image.save(output_path)
    return output_path
