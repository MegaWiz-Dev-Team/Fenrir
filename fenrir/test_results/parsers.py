"""Parsers for test result formats (JUnit XML, coverage JSON)."""

import json
import logging
import xml.etree.ElementTree as ET
from typing import Optional

from fenrir.test_results.models import TestResultCreate, TestResultType

logger = logging.getLogger("fenrir.test_results.parsers")


def parse_junit_xml(
    xml_content: str,
    service: str,
    test_type: TestResultType = TestResultType.UNIT,
) -> TestResultCreate:
    """Parse JUnit XML format into TestResultCreate.

    Supports output from: cargo test, pytest --junitxml, jest, etc.
    """
    root = ET.fromstring(xml_content)

    # Handle both <testsuites> and <testsuite> root
    if root.tag == "testsuites":
        suites = root.findall("testsuite")
    else:
        suites = [root]

    total = 0
    passed = 0
    failed = 0
    skipped = 0
    errors = 0
    duration_ms = 0
    suite_name = None
    test_cases = []

    for suite in suites:
        if suite_name is None:
            suite_name = suite.get("name", "unknown")

        s_total = int(suite.get("tests", 0))
        s_failures = int(suite.get("failures", 0))
        s_errors = int(suite.get("errors", 0))
        s_skipped = int(suite.get("skipped", 0))
        s_time = float(suite.get("time", 0))

        total += s_total
        failed += s_failures
        errors += s_errors
        skipped += s_skipped
        duration_ms += int(s_time * 1000)

        # Parse individual test cases
        for tc in suite.findall("testcase"):
            tc_name = tc.get("name", "unknown")
            tc_class = tc.get("classname", "")
            tc_time = float(tc.get("time", 0))

            tc_status = "passed"
            tc_message = None

            failure = tc.find("failure")
            error = tc.find("error")
            skip = tc.find("skipped")

            if failure is not None:
                tc_status = "failed"
                tc_message = failure.get("message", failure.text or "")
            elif error is not None:
                tc_status = "error"
                tc_message = error.get("message", error.text or "")
            elif skip is not None:
                tc_status = "skipped"
                tc_message = skip.get("message", "")

            test_cases.append({
                "name": tc_name,
                "classname": tc_class,
                "status": tc_status,
                "duration_ms": int(tc_time * 1000),
                "message": tc_message,
            })

    passed = total - failed - errors - skipped

    return TestResultCreate(
        service=service,
        test_type=test_type,
        suite_name=suite_name,
        total=total,
        passed=max(0, passed),
        failed=failed,
        skipped=skipped,
        errors=errors,
        duration_ms=duration_ms,
        raw_output=xml_content[:10000],
        test_cases=test_cases,
    )


def parse_coverage_json(
    json_content: str,
    result: TestResultCreate,
) -> TestResultCreate:
    """Parse coverage JSON and merge into TestResultCreate.

    Supports formats:
    - Python coverage.json (coverage.py)
    - cargo-llvm-cov JSON
    - Simple {"coverage_pct": 78.5} format
    """
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError:
        logger.warning("Invalid coverage JSON")
        return result

    # Simple format: {"coverage_pct": 78.5}
    if "coverage_pct" in data:
        result.coverage_pct = data["coverage_pct"]
        result.coverage_lines_total = data.get("lines_total")
        result.coverage_lines_covered = data.get("lines_covered")
        return result

    # Python coverage.py format
    if "totals" in data:
        totals = data["totals"]
        result.coverage_pct = totals.get("percent_covered", 0)
        result.coverage_lines_total = totals.get("num_statements", 0)
        result.coverage_lines_covered = totals.get("covered_lines", 0)
        result.coverage_branches_total = totals.get("num_branches")
        result.coverage_branches_covered = totals.get("covered_branches")
        return result

    # cargo-llvm-cov format
    if "data" in data and isinstance(data["data"], list):
        for entry in data["data"]:
            totals = entry.get("totals", {})
            lines = totals.get("lines", {})
            branches = totals.get("branches", {})

            if lines:
                covered = lines.get("covered", 0)
                total = lines.get("count", 1)
                result.coverage_pct = round(covered / total * 100, 2) if total > 0 else 0
                result.coverage_lines_total = total
                result.coverage_lines_covered = covered

            if branches:
                result.coverage_branches_total = branches.get("count")
                result.coverage_branches_covered = branches.get("covered")

            break  # Only use first data entry

    return result


def parse_cargo_test_output(
    output: str,
    service: str,
) -> TestResultCreate:
    """Parse `cargo test` stdout into TestResultCreate.

    Looks for: 'test result: ok. 60 passed; 0 failed; 0 ignored; ...'
    """
    total = 0
    passed = 0
    failed = 0
    skipped = 0

    for line in output.splitlines():
        if line.strip().startswith("test result:"):
            parts = line.split(".")
            if len(parts) >= 2:
                stats = parts[1].strip()
                for token in stats.split(";"):
                    token = token.strip()
                    if "passed" in token:
                        passed = int(token.split()[0])
                    elif "failed" in token:
                        failed = int(token.split()[0])
                    elif "ignored" in token:
                        skipped = int(token.split()[0])

    total = passed + failed + skipped

    return TestResultCreate(
        service=service,
        test_type=TestResultType.UNIT,
        suite_name="cargo test",
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        raw_output=output[:10000],
    )
