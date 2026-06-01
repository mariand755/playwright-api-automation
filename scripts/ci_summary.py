#!/usr/bin/env python3
"""Parse a JUnit XML report and write a Markdown CI summary to stdout."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def summarize(report_path: str) -> str:
    path = Path(report_path)
    if not path.exists():
        return (
            "## Test Summary\n\n"
            f"> `{report_path}` not found — "
            "JUnit XML was not produced by this run.\n"
        )

    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return (
            "## Test Summary\n\n"
            f"> `{report_path}` could not be parsed as JUnit XML: `{exc}`\n"
        )

    root = tree.getroot()

    # JUnit XML root may be <testsuites> (wrapper) or a single <testsuite>.
    if root.tag == "testsuites":
        suites = root.findall("testsuite")
        if not suites:
            suites = [root]
    else:
        suites = [root]

    total = errors = failures = skipped = 0
    duration = 0.0

    for suite in suites:
        total += int(suite.get("tests", 0))
        errors += int(suite.get("errors", 0))
        failures += int(suite.get("failures", 0))
        skipped += int(suite.get("skipped", 0))
        duration += float(suite.get("time", 0.0))

    passed = total - failures - errors - skipped
    all_passed = failures == 0 and errors == 0
    status = "✅ All tests passed" if all_passed else "❌ Tests failed"

    lines = [
        "## Test Summary",
        "",
        f"**{status}**",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Total | {total} |",
        f"| Passed | {passed} |",
        f"| Failed | {failures} |",
        f"| Errors | {errors} |",
        f"| Skipped | {skipped} |",
        f"| Duration | {duration:.2f}s |",
    ]

    failed_tests = []
    for suite in suites:
        for tc in suite.findall("testcase"):
            if tc.find("failure") is not None or tc.find("error") is not None:
                classname = tc.get("classname", "")
                name = tc.get("name", "")
                label = f"{classname}.{name}" if classname else name
                failed_tests.append(label)

    if failed_tests:
        lines += ["", "### Failed Tests", ""]
        for t in failed_tests:
            lines.append(f"- `{t}`")

    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    report_path = sys.argv[1] if len(sys.argv) > 1 else "artifacts/report.xml"
    print(summarize(report_path), end="")
