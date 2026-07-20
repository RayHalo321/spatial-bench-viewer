#!/usr/bin/env python3
from __future__ import annotations

import argparse

from v3_common import load_cases, materialize_case, validate_cases, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize derived evaluation data from Spatial Bench v3 core cases.")
    parser.add_argument("cases")
    parser.add_argument("output")
    parser.add_argument("--profile", choices=("", "pilot"), default="")
    args = parser.parse_args()
    cases = load_cases(args.cases)
    errors = validate_cases(cases, profile=args.profile)
    if errors:
        print("\n".join(errors))
        return 1
    write_json(args.output, [materialize_case(case) for case in cases])
    print(f"Materialized {len(cases)} cases -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
