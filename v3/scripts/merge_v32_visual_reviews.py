#!/usr/bin/env python3
"""Merge first-pass, failed-case review, and disputed-case tie-break rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_jsonl(paths: list[Path]) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for path in paths:
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            case_id = row.get("case_id") or row.get("id")
            if not case_id:
                raise ValueError(f"missing case identifier in {path}")
            row["case_id"] = case_id
            if "decision" not in row and "object_presence" in row:
                row["decision"] = {
                    "objects": row["object_presence"],
                    "cardinality": row["cardinality"],
                    "relations": row["relations"],
                }
            if case_id in rows:
                raise ValueError(f"duplicate case {case_id} across {paths}")
            rows[case_id] = row
    return rows


def normalize_and_validate(rows: dict[str, dict], cases: dict[str, dict]) -> None:
    for case_id, row in rows.items():
        case = cases[case_id]
        object_to_canonical = {item["id"]: item["canonical"] for item in case["objects"]}
        cardinality = row["decision"]["cardinality"]
        expected_cardinality = {item["canonical"] for item in case["objects"]}
        if set(cardinality) == {"canonical"}:
            cardinality = {key: cardinality["canonical"] for key in expected_cardinality}
        normalized: dict[str, bool] = {}
        for key, value in cardinality.items():
            canonical = object_to_canonical.get(key, key)
            if canonical in normalized and normalized[canonical] != value:
                raise ValueError(f"{case_id}: conflicting cardinality judgments for {canonical}")
            normalized[canonical] = value
        row["decision"]["cardinality"] = normalized

        expected = {
            "objects": {item["id"] for item in case["objects"]},
            "cardinality": expected_cardinality,
            "relations": {item["id"] for item in case["relations"]},
        }
        for group, keys in expected.items():
            actual = set(row["decision"][group])
            if actual != keys:
                raise ValueError(
                    f"{case_id} {group}: expected {sorted(keys)}, got {sorted(actual)}"
                )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--first", type=Path, nargs="+", required=True)
    parser.add_argument("--second", type=Path, nargs="+", required=True)
    parser.add_argument("--third", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    cases = {
        row["id"]: row
        for row in (
            json.loads(line) for line in args.cases.read_text().splitlines() if line.strip()
        )
    }
    first = load_jsonl(args.first)
    second = load_jsonl(args.second)
    third = load_jsonl([args.third])
    normalize_and_validate(first, cases)
    normalize_and_validate(second, cases)
    normalize_and_validate(third, cases)
    output = []
    for case_id, initial in first.items():
        if initial["method"] != args.method:
            raise ValueError(f"{case_id}: expected method {args.method}")
        followup = second.get(case_id)
        if followup is None:
            selected = initial
            review_count = 1
            adjudicated = False
        elif initial["decision"] == followup["decision"]:
            selected = initial
            review_count = 2
            adjudicated = False
        else:
            selected = third.get(case_id)
            if selected is None:
                raise ValueError(f"missing tie-break row for {case_id}")
            review_count = 3
            adjudicated = True
        values = [
            *selected["decision"]["objects"].values(),
            *selected["decision"]["cardinality"].values(),
            *selected["decision"]["relations"].values(),
        ]
        output.append(
            {
                **selected,
                "case_id": case_id,
                "method": args.method,
                "exact": all(values),
                "review_count": review_count,
                "adjudicated": adjudicated,
                "first_pass_exact": bool(initial["exact"]),
            }
        )

    extra_second = set(second) - set(first)
    extra_third = set(third) - set(first)
    if extra_second or extra_third:
        raise ValueError(f"review rows outside first pass: second={extra_second}, third={extra_third}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in output)
    )
    print(
        f"method={args.method} rows={len(output)} exact={sum(row['exact'] for row in output)} "
        f"adjudicated={sum(row['adjudicated'] for row in output)}"
    )


if __name__ == "__main__":
    main()
