#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

from openai import OpenAI

REPO = Path(os.environ.get("T2I_BLENDER_REPO", "/T2I-Blender/code"))
sys.path.insert(0, str(REPO / "src"))

from common.openai_client import create_dashscope_client, summarize_remote_api_error  # noqa: E402


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def image_data_url(path: Path) -> str:
    suffix = path.suffix.lower()
    mime = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def extract_json(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped, flags=re.I).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        return json.loads(stripped, strict=False)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.S)
        if match:
            return json.loads(match.group(0), strict=False)
        raise


def norm_answer(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"yes", "no", "unclear"}:
        return text
    if any(x in text for x in ["unclear", "not sure", "cannot determine", "can't determine", "unknown"]):
        return "unclear"
    if re.search(r"\byes\b", text):
        return "yes"
    if re.search(r"\bno\b", text):
        return "no"
    return "unclear"


def label(name: str) -> str:
    return (name or "").replace("_", " ").strip()


def inverse_question(check: dict) -> str | None:
    relation = check.get("relation")
    q = str(check.get("vqa_question") or check.get("label_en") or "").strip()
    subject = label(check.get("subject", ""))
    target = label(check.get("target", ""))
    if not q:
        return None
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
        return None
    if relation == "absolute_location":
        if "left side" in q:
            return q.replace("left side", "right side")
        if "right side" in q:
            return q.replace("right side", "left side")
    return None


def build_questions(case: dict) -> list[dict]:
    questions = []
    for check in case.get("checklist", []):
        q = str(check.get("vqa_question") or check.get("label_en") or "").strip()
        if not q:
            continue
        if check.get("type") == "presence":
            questions.append({"id": check["check_id"], "check_id": check["check_id"], "kind": "presence", "question": q})
            continue
        questions.append({"id": check["check_id"] + "|pos", "check_id": check["check_id"], "kind": "relation_pos", "question": q})
        neg = inverse_question(check)
        if neg:
            questions.append({"id": check["check_id"] + "|neg", "check_id": check["check_id"], "kind": "relation_neg", "question": neg})
    return questions


def call_vqa(client, model: str, image_path: Path, questions: list[dict], timeout: float) -> tuple[dict, str]:
    aliases = {f"q{idx + 1:03d}": q["id"] for idx, q in enumerate(questions)}
    qtext = "\n".join(
        f"{idx + 1}. id=q{idx + 1:03d} question={q['question']}"
        for idx, q in enumerate(questions)
    )
    prompt = (
        "You are a strict visual question answering judge. Answer only from visible image evidence. "
        "For each yes/no question, answer exactly one of: yes, no, unclear. "
        "Use unclear when the image is too ambiguous, cropped, tiny, or occluded to judge.\n\n"
        "Return strict JSON only in this format:\n"
        '{"answers":[{"id":"...","answer":"yes|no|unclear","confidence":0.0,"reason":"short reason"}]}\n\n'
        "Questions:\n"
        f"{qtext}"
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
        max_tokens=2048,
        timeout=timeout,
    )
    raw = response.choices[0].message.content or ""
    parsed = extract_json(raw)
    for answer in parsed.get("answers", []):
        if isinstance(answer, dict) and answer.get("id") in aliases:
            answer["id"] = aliases[answer["id"]]
    return parsed, raw


def score_case(case: dict, questions: list[dict], parsed: dict) -> dict:
    answers = parsed.get("answers", [])
    by_id = {}
    if isinstance(answers, list):
        for item in answers:
            if isinstance(item, dict) and item.get("id"):
                by_id[str(item["id"])] = {
                    "answer": norm_answer(item.get("answer")),
                    "confidence": item.get("confidence"),
                    "reason": item.get("reason", ""),
                }

    for q in questions:
        by_id.setdefault(q["id"], {"answer": "unclear", "confidence": 0, "reason": "missing model answer"})

    object_names = {o.get("canonical") for o in case.get("objects", [])}
    presence = {}
    for check in case.get("checklist", []):
        if check.get("type") == "presence":
            presence[check.get("subject")] = by_id.get(check["check_id"], {}).get("answer", "unclear")

    presence_scores = [1.0 if ans == "yes" else 0.5 if ans == "unclear" else 0.0 for ans in presence.values()]
    relation_scores = []
    relation_details = []
    for check in case.get("checklist", []):
        if check.get("type") == "presence":
            continue
        required = [check.get("subject")]
        target = check.get("target")
        if target in object_names:
            required.append(target)
        target2 = check.get("target2")
        if target2 in object_names:
            required.append(target2)
        if any(presence.get(obj) != "yes" for obj in required if obj):
            score = 0.0
            reason = "presence_gate_failed"
        else:
            pos = by_id.get(check["check_id"] + "|pos", {}).get("answer", "unclear")
            neg_item = by_id.get(check["check_id"] + "|neg")
            if neg_item:
                neg = neg_item.get("answer", "unclear")
                if pos == "yes" and neg == "no":
                    score = 1.0
                    reason = "positive_yes_negative_no"
                elif pos == "no":
                    score = 0.0
                    reason = f"positive_no_negative_{neg}"
                else:
                    score = 0.5
                    reason = f"inconsistent_or_unclear_pos_{pos}_neg_{neg}"
            else:
                pos = by_id.get(check["check_id"] + "|pos", {}).get("answer", "unclear")
                score = 1.0 if pos == "yes" else 0.5 if pos == "unclear" else 0.0
                reason = f"positive_only_{pos}"
        relation_scores.append(score)
        relation_details.append({"check_id": check["check_id"], "type": check.get("type"), "score": score, "reason": reason})

    presence_score = sum(presence_scores) / len(presence_scores) if presence_scores else 0.0
    relation_score = sum(relation_scores) / len(relation_scores) if relation_scores else 0.0
    return {
        "presence_score": presence_score,
        "relation_score": relation_score,
        "combined_score": 0.2 * presence_score + 0.8 * relation_score,
        "relation_details": relation_details,
        "answers": by_id,
    }


def avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bench-root", default="/NAS/liox/hsr/spatial-bench-viewer")
    parser.add_argument("--cases", default="data/bench_cases.json")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--model", default=os.environ.get("T2I_VQA_MODEL") or os.environ.get("T2I_VLM_MODEL") or "qwen3-vl-plus")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--api-key", default="EMPTY")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    load_env(REPO / ".env")
    bench_root = Path(args.bench_root)
    cases = json.loads((bench_root / args.cases).read_text(encoding="utf-8"))
    if args.case_id:
        wanted = set(args.case_id)
        cases = [c for c in cases if c.get("id") in wanted]
    if args.limit:
        cases = cases[: args.limit]

    stamp = time.strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir or (REPO / "benchmarks" / f"spatial_qwen_vqa_{stamp}"))
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "vqa_results.jsonl"
    summary_path = out_dir / "summary.json"

    if args.base_url:
        client = OpenAI(api_key=args.api_key, base_url=args.base_url, timeout=args.timeout)
        http_client = None
    else:
        client, http_client = create_dashscope_client(timeout=args.timeout)
    rows = []
    try:
        with result_path.open("w", encoding="utf-8") as f:
            for idx, case in enumerate(cases, 1):
                image_rel = case.get("sample", {}).get("image_path") or case.get("sample", {}).get("image")
                image_path = bench_root / image_rel
                questions = build_questions(case)
                row = {
                    "id": case.get("id"),
                    "category": case.get("category"),
                    "level": case.get("level"),
                    "model": args.model,
                    "image": str(image_path),
                    "question_count": len(questions),
                }
                try:
                    parsed, raw = call_vqa(client, args.model, image_path, questions, args.timeout)
                    row.update(score_case(case, questions, parsed))
                    row["raw_response"] = raw
                    row["error"] = ""
                except Exception as exc:
                    row.update({"presence_score": 0.0, "relation_score": 0.0, "combined_score": 0.0})
                    row["raw_response"] = ""
                    row["error"] = summarize_remote_api_error(exc)
                rows.append(row)
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
                print(f"[{idx}/{len(cases)}] {row['id']} relation={row['relation_score']:.3f} presence={row['presence_score']:.3f} err={row['error']}")
    finally:
        if http_client is not None:
            http_client.close()
        else:
            client.close()

    by_category = defaultdict(list)
    by_level = defaultdict(list)
    by_category_level = defaultdict(list)
    for row in rows:
        by_category[row["category"]].append(row)
        by_level[row["level"]].append(row)
        by_category_level[f"{row['category']}::{row['level']}"].append(row)

    def pack(group_rows: list[dict]) -> dict:
        return {
            "cases": len(group_rows),
            "presence_score": avg([r["presence_score"] for r in group_rows]),
            "relation_score": avg([r["relation_score"] for r in group_rows]),
            "combined_score": avg([r["combined_score"] for r in group_rows]),
        }

    summary = {
        "model": args.model,
        "cases": len(rows),
        "result_path": str(result_path),
        "summary_path": str(summary_path),
        "overall": pack(rows),
        "by_category": {k: pack(v) for k, v in sorted(by_category.items())},
        "by_level": {k: pack(v) for k, v in sorted(by_level.items())},
        "by_category_level": {k: pack(v) for k, v in sorted(by_category_level.items())},
        "errors": [r for r in rows if r.get("error")],
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary["overall"], ensure_ascii=False, indent=2))
    print(f"wrote {result_path}")
    print(f"wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
