#!/usr/bin/env python3
from __future__ import annotations

import argparse

from v3_common import load_cases, validate_cases


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Spatial Bench v3 core cases.")
    parser.add_argument("cases")
    parser.add_argument("--profile", choices=("", "pilot", "v32"), default="")
    args = parser.parse_args()
    cases = load_cases(args.cases)
    errors = validate_cases(cases, profile=args.profile)
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Spatial Bench v3 validation passed: {len(cases)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
