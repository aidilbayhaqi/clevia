from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.agent.router import route_intent
from app.services.safety import classify_risk


DATASET = Path(__file__).parent / "datasets" / "golden_v1.jsonl"


def load_cases() -> list[dict]:
    cases: list[dict] = []
    with DATASET.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                cases.append(json.loads(line))
    return cases


def evaluate_offline() -> tuple[int, int, list[dict]]:
    passed = 0
    failures: list[dict] = []
    cases = load_cases()
    for case in cases:
        actual_risk = classify_risk(case["message"])
        actual_intent = route_intent(case["message"]).value
        expected = case["expected"]
        ok = (
            actual_risk == expected.get("risk", "normal")
            and actual_intent == expected["intent"]
        )
        if ok:
            passed += 1
        else:
            failures.append(
                {
                    "id": case["id"],
                    "expected": expected,
                    "actual": {"risk": actual_risk, "intent": actual_intent},
                }
            )
    return passed, len(cases), failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Clevia baseline evaluation runner")
    parser.add_argument("--offline", action="store_true", help="Run deterministic offline gates")
    parser.parse_args()

    passed, total, failures = evaluate_offline()
    print(json.dumps({"passed": passed, "total": total, "failures": failures}, indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
