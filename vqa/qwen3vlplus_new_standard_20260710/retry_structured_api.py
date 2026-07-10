#!/usr/bin/env python3
import argparse
import importlib.util
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-root", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--model", default="qwen3-vl-plus")
    args = parser.parse_args()

    module_path = args.eval_root / "evaluator.py"
    spec = importlib.util.spec_from_file_location("evaluator", module_path)
    evaluator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluator)
    evaluator.load_env(evaluator.REPO / ".env")

    cases = json.loads((args.eval_root / "data/cases.json").read_text(encoding="utf-8"))
    case = next(item for item in cases if item["id"] == args.case_id)
    questions = evaluator.build_questions(case)
    aliases = {f"q{index + 1:03d}": question["id"] for index, question in enumerate(questions)}
    question_text = "\n".join(
        f"{index + 1}. id=q{index + 1:03d} question={question['question']}"
        for index, question in enumerate(questions)
    )
    prompt = (
        "Answer each visual yes/no question using only yes, no, or unclear. "
        "Return one answer for every id. Do not include explanations.\n"
        '{"answers":[{"id":"q001","answer":"yes"}]}\n\n'
        f"Questions:\n{question_text}"
    )
    image_path = Path(case["sample"].get("image_path") or case["sample"]["image"])
    client, http_client = evaluator.create_dashscope_client(timeout=180)
    try:
        response = client.chat.completions.create(
            model=args.model,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": evaluator.image_data_url(image_path)}},
            ]}],
            temperature=0,
            max_tokens=1024,
            response_format={"type": "json_object"},
            timeout=180,
        )
    finally:
        http_client.close()

    raw = response.choices[0].message.content or ""
    parsed = evaluator.extract_json(raw)
    for answer in parsed.get("answers", []):
        if answer.get("id") in aliases:
            answer["id"] = aliases[answer["id"]]
        answer.setdefault("confidence", None)
        answer.setdefault("reason", "Recovered with constrained JSON retry.")
    scored = evaluator.score_case(case, questions, parsed)
    row = {
        "id": case["id"],
        "category": case["category"],
        "level": case["level"],
        "model": args.model,
        "image": str(image_path),
        "question_count": len(questions),
        **scored,
        "raw_response": raw,
        "error": "",
    }
    out_dir = args.eval_root / f"retry_structured_{args.case_id}"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "vqa_results.jsonl").write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "raw_response.txt").write_text(raw, encoding="utf-8")
    print(json.dumps({"id": case["id"], "questions": len(questions), "relation": row["relation_score"]}))


if __name__ == "__main__":
    main()
