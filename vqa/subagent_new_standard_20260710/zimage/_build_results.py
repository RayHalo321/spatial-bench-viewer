import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


OVERRIDES = {
    "ABS02": {
        "absolute_location:sofa:right_side|pos": ("no", "The sofa spans nearly the full width and is centered rather than confined to the right side."),
        "absolute_location:sofa:right_side|neg": ("no", "The sofa is also not confined to the left side; it spans the center."),
    },
    "ABS06": {
        "absolute_location:suitcase:right_side|pos": ("no", "The suitcase is centered in the frame rather than placed on the right side."),
        "absolute_location:suitcase:right_side|neg": ("no", "The centered suitcase is not on the left side either."),
    },
    "REL04": {
        "presence:sofa": ("no", "The image shows two single-seat armchairs, not a sofa."),
        "between:vase:sofa:coffee_table|pos": ("no", "The vase is between the two armchairs, while the coffee table is in the foreground."),
    },
    "REL05": {
        "right_of:tv:cabinet|pos": ("no", "The television is centered directly over the cabinet, not clearly to its right."),
        "right_of:tv:cabinet|neg": ("no", "The television is not clearly to the cabinet's left either; their centers align."),
    },
    "REL08": {
        "right_of:cabinet:chair|pos": ("no", "The cabinet is visibly behind and to the left of the chair."),
        "right_of:cabinet:chair|neg": ("yes", "The cabinet is visibly to the left of the chair."),
    },
    "REL10": {
        "left_of:suitcase:bookshelf|pos": ("no", "The suitcase overlaps the lower bookshelf and has nearly the same horizontal center."),
        "left_of:suitcase:bookshelf|neg": ("no", "The suitcase is not clearly to the right of the bookshelf either."),
        "right_of:potted_plant:chair|pos": ("no", "The plant trunk is behind and almost horizontally aligned with the chair."),
        "right_of:potted_plant:chair|neg": ("no", "The plant is not clearly to the left of the chair either."),
    },
    "DEP05": {
        "presence:bench": ("unclear", "Only a cropped wooden support surface is visible, so it could be a bench or a table."),
        "behind:potted_plant:bench|pos": ("no", "The plant is resting on the wooden surface, not visibly behind it."),
        "behind:potted_plant:bench|neg": ("no", "The plant is not clearly in front of the support; it is on top of it."),
    },
    "DEP06": {
        "behind:table:chair|pos": ("unclear", "One chair is in front of the table and another is behind it, making the singular reference ambiguous."),
        "behind:table:chair|neg": ("unclear", "The table is in front of one visible chair but behind the other."),
    },
    "OCC01": {
        "partially_occludes:potted_plant:cabinet|pos": ("no", "The plant stands beside the cabinet without a clear overlapping silhouette."),
        "partially_occludes:potted_plant:cabinet|neg": ("no", "The cabinet also does not overlap or block the plant."),
    },
    "ORI05": {
        "face:chair:left_side|pos": ("no", "The chair's seat projects to the right, so it is angled toward the right side."),
        "face:chair:left_side|neg": ("yes", "The chair is visibly facing away from the left side and toward the right."),
    },
    "ORI06": {
        "face:sofa:right_side|pos": ("no", "The sofa remains essentially front-facing rather than angled toward the right."),
        "face:sofa:right_side|neg": ("no", "The sofa is not clearly facing away toward the left; it is front-facing."),
    },
    "ORI08": {
        "presence:sofa": ("no", "The background seating is a single-seat armchair rather than a sofa."),
        "behind:sofa:chair|pos": ("no", "No sofa is visible behind the foreground chair; the background seat is an armchair."),
        "behind:sofa:chair|neg": ("no", "No sofa is visible in front of the chair either."),
    },
    "ORI10": {
        "right_of:cabinet:bookshelf|pos": ("unclear", "The bookshelf and cabinet appear merged into one open storage unit, so separate centers are not well defined."),
        "right_of:cabinet:bookshelf|neg": ("unclear", "The merged storage unit also prevents a clear inverse left-of judgment."),
    },
    "ROT02": {
        "rotate_yaw:chair:45_degrees_to_the_right|pos": ("no", "The chair is shown in left-facing side profile, not rotated 45 degrees to the right."),
        "rotate_yaw:chair:45_degrees_to_the_right|neg": ("yes", "The visible chair orientation is toward the left side."),
    },
    "ROT03": {
        "rotate_yaw:laptop:90_degrees_clockwise|pos": ("no", "The laptop still faces the viewer and is not turned sideways by 90 degrees."),
    },
    "ROT05": {
        "rotate_yaw:cabinet:30_degrees_to_the_right|pos": ("no", "The visible right side panel indicates the cabinet face is turned toward the left."),
        "rotate_yaw:cabinet:30_degrees_to_the_right|neg": ("yes", "The cabinet is visibly angled toward the left."),
    },
    "ROT08": {
        "rotate_yaw:laptop:90_degrees_clockwise|pos": ("no", "The laptop remains front-facing rather than rotated sideways by 90 degrees."),
        "in_front:vase:laptop|pos": ("no", "The vase sits to the left and slightly behind the laptop's front edge."),
        "in_front:vase:laptop|neg": ("yes", "The vase is visibly farther back on the desk than the laptop's front edge."),
    },
    "ROT09": {
        "rotate_yaw:chair:45_degrees_to_the_right|pos": ("no", "The chair opens toward the left side rather than being rotated to the right."),
        "rotate_yaw:chair:45_degrees_to_the_right|neg": ("yes", "The chair is visibly angled toward the left."),
    },
    "ROT10": {
        "rotate_yaw:tv:45_degrees_to_the_left|pos": ("no", "The television is nearly front-facing, not rotated 45 degrees to the left."),
        "rotate_yaw:tv:45_degrees_to_the_left|neg": ("no", "The television is not rotated 45 degrees to the right either."),
    },
    "MUL03": {
        "presence:cup_set": ("no", "Only one mug is visible, not a cup set."),
        "on_top:cup_set:office_desk|pos": ("no", "A single mug is on the desk, but no cup set is visible."),
        "on_top:cup_set:office_desk|neg": ("no", "There is no cup set under the desk; only one mug is visible on top."),
        "in_front:cup_set:laptop|pos": ("no", "A single mug is in front of the laptop, but no cup set is present."),
        "in_front:cup_set:laptop|neg": ("no", "No cup set is visible behind the laptop either."),
    },
    "MUL09": {
        "behind:cabinet:barrel|pos": ("no", "The cabinet rests directly above the barrel rather than behind it in depth."),
        "behind:cabinet:barrel|neg": ("no", "The cabinet is not clearly in front of the barrel either; it is stacked on it."),
        "partially_occludes:potted_plant:cabinet|pos": ("no", "The plant is behind and beside the cabinet rather than blocking its front."),
        "partially_occludes:potted_plant:cabinet|neg": ("yes", "The cabinet hides part of the plant on its right side."),
    },
}


NOTES = """# Z-Image Turbo evaluation notes

All 76 original images were inspected. Answers were judged from the natural-language questions using opaque internal question numbers; output `|pos` and `|neg` keys are schema labels only.

- **ABS01:** The chair is visibly left of image center, although it is not pushed to the far edge; counted as left-side (`yes`).
- **REL04 / ORI08:** Single-seat armchairs were not counted as sofas. Their sofa presence checks are `no`, so dependent relations fail the presence gate.
- **REL10:** The suitcase overlaps the bookshelf, and the plant is almost horizontally aligned with the chair; neither requested left/right relation is visually established.
- **DEP05:** The wooden support is too cropped to distinguish a bench from a table, so bench presence is `unclear` and the relation is gated to zero.
- **DEP06:** Two chairs appear on opposite sides of the table. Both the positive and inverse depth questions are `unclear`, producing a 0.5 relation score.
- **OCC07:** The plant was counted as partially blocking the bookshelf because its leaves obscure the shelf interior and books, even though the outer frame remains visible.
- **SUP06 / SUP08:** A visible tabletop was accepted as a table; cup saucers were accepted as small plates because the presence question asks only whether a plate is visible.
- **ORI10:** The bookshelf and cabinet are fused into one open storage unit. Both direction questions are `unclear`, producing a 0.5 relation score.
- **ROT06 / ROT07:** The strong diagonal orientations were accepted as left rotations. ROT02, ROT05, ROT08, and ROT10 visibly fail their requested rotation direction or magnitude.
- **MUL03:** One mug is not a cup set; cup-set presence is `no` and its two dependent relations are gated to zero.
- **MUL09:** The cabinet is stacked above the barrel, not behind it. The plant is behind the cabinet, so the visible occlusion direction is the inverse of the requested one.
"""


def label(value):
    return str(value or "").replace("_", " ").strip()


def inverse_question(check):
    relation = check.get("relation")
    q = str(check.get("vqa_question") or check.get("label_en") or "").strip()
    subject = label(check.get("subject"))
    target = label(check.get("target"))
    if relation == "left_of":
        return q.replace(" to the left of ", " to the right of ")
    if relation == "right_of":
        return q.replace(" to the right of ", " to the left of ")
    if relation == "in_front":
        return q.replace(" in front of ", " behind ")
    if relation == "behind":
        return q.replace(" behind ", " in front of ")
    if relation == "on_top" and subject and target:
        return f"Is the {subject} under the {target}?"
    if relation == "partially_occludes" and subject and target:
        return f"Does the {target} partially block the {subject}?"
    if relation == "face" and subject and target:
        return f"Is the {subject} facing away from the {target}?"
    if relation == "rotate_yaw":
        if " left " in f" {q.lower()} ":
            return re.sub("left", "right", q, flags=re.I)
        if " right " in f" {q.lower()} ":
            return re.sub("right", "left", q, flags=re.I)
    if relation == "absolute_location":
        if "left side" in q:
            return q.replace("left side", "right side")
        if "right side" in q:
            return q.replace("right side", "left side")
    return None


def questions_for(case):
    questions = []
    for check in case["checklist"]:
        if check["type"] == "presence":
            questions.append((check["check_id"], check, "presence"))
            continue
        questions.append((check["check_id"] + "|pos", check, "positive"))
        inverse = inverse_question(check)
        if inverse:
            questions.append((check["check_id"] + "|neg", check, "inverse"))
    return [(f"q{i:03d}", answer_id, check, kind) for i, (answer_id, check, kind) in enumerate(questions, 1)]


def default_reason(check, kind, answer):
    subject = label(check.get("subject"))
    target = label(check.get("target"))
    relation = check.get("relation")
    if kind == "presence":
        return f"The {subject} is clearly visible in the image."
    if kind == "inverse":
        if relation in {"left_of", "right_of", "absolute_location"}:
            return f"The visible position of the {subject} supports the requested side, not the inverse side."
        if relation in {"in_front", "behind"}:
            return f"Visible depth and overlap place the {subject} on the requested side of the {target}, not the inverse."
        if relation == "on_top":
            return f"The {subject} rests on top of the {target}, not underneath it."
        if relation == "partially_occludes":
            return f"The {subject} is the foreground blocker; the {target} does not block it."
        return f"The visible orientation supports the requested direction, not the inverse direction."
    if relation == "left_of":
        return f"The {subject} is visibly to the left of the {target}."
    if relation == "right_of":
        return f"The {subject} is visibly to the right of the {target}."
    if relation == "in_front":
        return f"The {subject} is visibly nearer than and in front of the {target}."
    if relation == "behind":
        return f"The {subject} is visibly farther back than the {target}."
    if relation == "on_top":
        return f"The {subject} visibly rests on the top surface of the {target}."
    if relation == "partially_occludes":
        return f"The {subject} overlaps and hides part of the {target}."
    if relation == "between":
        return f"The {subject} is visibly positioned between the two target objects."
    if relation == "absolute_location":
        return f"The {subject} visibly occupies the requested image region."
    if relation == "face":
        return f"The visible orientation of the {subject} matches the stated facing condition."
    if relation == "rotate_yaw":
        return f"The visible angle of the {subject} matches the stated rotation."
    return f"The visible placement of the {subject} matches the stated relation."


def score_case(case, answers):
    presence = {}
    for check in case["checklist"]:
        if check["type"] == "presence":
            presence[check["subject"]] = answers[check["check_id"]]["answer"]

    presence_values = [1.0 if value == "yes" else 0.5 if value == "unclear" else 0.0 for value in presence.values()]
    object_names = {obj.get("canonical") for obj in case.get("objects", [])}
    details = []
    for check in case["checklist"]:
        if check["type"] == "presence":
            continue
        required = [check.get("subject")]
        if check.get("target") in object_names:
            required.append(check.get("target"))
        if check.get("target2") in object_names:
            required.append(check.get("target2"))
        if any(presence.get(obj) != "yes" for obj in required if obj):
            score = 0.0
            reason = "presence_gate_failed"
        else:
            pos = answers[check["check_id"] + "|pos"]["answer"]
            neg_key = check["check_id"] + "|neg"
            if neg_key in answers:
                neg = answers[neg_key]["answer"]
                if pos == "yes" and neg == "no":
                    score, reason = 1.0, "positive_yes_negative_no"
                elif pos == "no":
                    score, reason = 0.0, f"positive_no_negative_{neg}"
                else:
                    score, reason = 0.5, f"inconsistent_or_unclear_pos_{pos}_neg_{neg}"
            else:
                score = 1.0 if pos == "yes" else 0.5 if pos == "unclear" else 0.0
                reason = f"positive_only_{pos}"
        details.append({"check_id": check["check_id"], "type": check.get("type"), "score": score, "reason": reason})

    presence_score = sum(presence_values) / len(presence_values)
    relation_score = sum(item["score"] for item in details) / len(details)
    return presence_score, relation_score, 0.2 * presence_score + 0.8 * relation_score, details


def pack(rows):
    relation_details = [detail for row in rows for detail in row["relation_details"]]
    return {
        "cases": len(rows),
        "relations": len(relation_details),
        "presence_macro": sum(row["presence_score"] for row in rows) / len(rows),
        "relation_case_macro": sum(row["relation_score"] for row in rows) / len(rows),
        "relation_micro": sum(detail["score"] for detail in relation_details) / len(relation_details),
        "exact_case_pass_rate": sum(row["presence_score"] == 1.0 and row["relation_score"] == 1.0 for row in rows) / len(rows),
        "errors": sum(bool(row["error"]) for row in rows),
    }


def main():
    cases = json.loads((ROOT / "vqa/qwen3vl8b_20260710/bench_cases.json").read_text())
    old_rows = [json.loads(line) for line in (ROOT / "vqa/qwen3vl8b_20260710/zimage/vqa_results.jsonl").read_text().splitlines()]
    image_by_id = {row["id"]: row["image"] for row in old_rows}
    rows = []

    for case in cases:
        answers = {}
        for opaque_id, answer_id, check, kind in questions_for(case):
            del opaque_id
            answer = "yes" if kind != "inverse" else "no"
            reason = default_reason(check, kind, answer)
            if answer_id in OVERRIDES.get(case["id"], {}):
                answer, reason = OVERRIDES[case["id"]][answer_id]
            confidence = 0.5 if answer == "unclear" else 0.98
            answers[answer_id] = {"answer": answer, "confidence": confidence, "reason": reason}

        presence_score, relation_score, combined_score, details = score_case(case, answers)
        rows.append({
            "id": case["id"],
            "category": case["category"],
            "level": case["level"],
            "model": "GPT-Subagent",
            "image": image_by_id[case["id"]],
            "question_count": len(answers),
            "presence_score": presence_score,
            "relation_score": relation_score,
            "combined_score": combined_score,
            "relation_details": details,
            "answers": answers,
            "raw_response": "",
            "error": "",
        })

    by_category = defaultdict(list)
    by_level = defaultdict(list)
    for row in rows:
        by_category[row["category"]].append(row)
        by_level[row["level"]].append(row)
    summary = {
        "overall": pack(rows),
        "by_category": {key: pack(value) for key, value in by_category.items()},
        "by_level": {key: pack(value) for key, value in by_level.items()},
    }

    (OUT / "vqa_results.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    (OUT / "eval_notes.md").write_text(NOTES)


if __name__ == "__main__":
    main()
