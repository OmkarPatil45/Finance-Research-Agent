
import json
import math
import sys
import time
from datetime import date
from pathlib import Path

from sqlalchemy import select

from app.db.models import Transaction, Fund
from app.db.session import SessionLocal
from app.tools.transactions import (
    calculate_spending,
    spending_by_category,
    spending_by_merchant,
)
from app.tools.funds import (
    calculate_fund_return,
    calculate_holding_returns,
)

BACKEND_DIR = Path(__file__).resolve().parents[1]
CASES_FILE = BACKEND_DIR / "evals" / "evaluation_cases.json"

OPERATIONS = {
    "calculate_spending": calculate_spending,
    "spending_by_category": spending_by_category,
    "spending_by_merchant": spending_by_merchant,
    "calculate_fund_return": calculate_fund_return,
    "calculate_holding_returns": calculate_holding_returns,
}

DATE_FIELDS = {"start_date", "end_date", "as_of_date"}


def resolve_path(result, path):
    """Resolve simple dictionary paths such as return_percentage."""
    value = result
    for part in path.split("."):
        value = value[part]
    return value


def check_result(result, check):
    if check.get("type") == "list_item":
        items = resolve_path(result, check["path"])
        matches = [
            item
            for item in items
            if item.get(check["match_field"]) == check["match_value"]
        ]

        if not matches:
            return False, (
                f"No item found where {check['match_field']}="
                f"{check['match_value']!r}"
            )

        actual = matches[0].get(check["field"])
    else:
        actual = resolve_path(result, check["path"])

    expected = check["expected"]

    if (
        isinstance(actual, (int, float))
        and not isinstance(actual, bool)
        and isinstance(expected, (int, float))
        and not isinstance(expected, bool)
    ):
        passed = math.isclose(
            actual, expected, rel_tol=0, abs_tol=0.01
        )
    else:
        passed = actual == expected

    return passed, f"expected={expected!r}, actual={actual!r}"


def run_case(db, case):
    started = time.perf_counter()
    expected_error = case.get("expected_error")

    try:
        params = dict(case["params"])

        for field in DATE_FIELDS:
            if field in params:
                params[field] = date.fromisoformat(params[field])

        result = OPERATIONS[case["operation"]](db=db, **params)

        if expected_error:
            return {
                "id": case["id"],
                "name": case["name"],
                "status": "FAIL",
                "duration_ms": round(
                    (time.perf_counter() - started) * 1000, 2
                ),
                "details": "Expected an error, but the operation succeeded.",
            }

        failures = []
        for check in case.get("checks", []):
            try:
                passed, details = check_result(result, check)
            except (KeyError, IndexError, TypeError) as exc:
                passed = False
                details = f"Invalid result path: {exc}"

            if not passed:
                failures.append(details)

        return {
            "id": case["id"],
            "name": case["name"],
            "status": "PASS" if not failures else "FAIL",
            "duration_ms": round(
                (time.perf_counter() - started) * 1000, 2
            ),
            "details": "; ".join(failures) if failures else "All checks passed.",
        }

    except (ValueError, TypeError) as exc:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)

        if expected_error and expected_error.lower() in str(exc).lower():
            return {
                "id": case["id"],
                "name": case["name"],
                "status": "PASS",
                "duration_ms": duration_ms,
                "details": "Expected error was raised.",
            }

        return {
            "id": case["id"],
            "name": case["name"],
            "status": "FAIL",
            "duration_ms": duration_ms,
            "details": (
                f"Unexpected error: {type(exc).__name__}: {exc}"
            ),
        }

    except Exception as exc:
        return {
            "id": case["id"],
            "name": case["name"],
            "status": "ERROR",
            "duration_ms": round(
                (time.perf_counter() - started) * 1000, 2
            ),
            "details": f"{type(exc).__name__}: {exc}",
        }


def main():
    if not CASES_FILE.exists():
        print(f"Evaluation file not found: {CASES_FILE}")
        return 2

    with CASES_FILE.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    if not isinstance(cases, list) or not cases:
        print("Evaluation cases must be a non-empty JSON array.")
        return 2

    seen_ids = set()
    for case in cases:
        if case.get("id") in seen_ids:
            print(f"Duplicate evaluation ID: {case.get('id')}")
            return 2
        seen_ids.add(case.get("id"))

        if case.get("operation") not in OPERATIONS:
            print(f"Unsupported operation in {case.get('id')}")
            return 2

    results = []

    with SessionLocal() as db:
        for case in cases:
            result = run_case(db, case)
            results.append(result)

            print(
                f"[{result['status']}] {result['id']} - "
                f"{result['name']} ({result['duration_ms']} ms)"
            )
            if result["status"] != "PASS":
                print(f"       {result['details']}")

    passed = sum(item["status"] == "PASS" for item in results)
    failed = sum(item["status"] == "FAIL" for item in results)
    errors = sum(item["status"] == "ERROR" for item in results)

    report = {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "results": results,
    }

    report_path = BACKEND_DIR / "evals" / "evaluation_report.json"
    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\n--- Evaluation Summary ---")
    print(f"Total:  {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    print(f"Report: {report_path}")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
