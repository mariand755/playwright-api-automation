#!/usr/bin/env python3
"""Release readiness gate: consumes JUnit XML + observability + defect metrics → GO/NO_GO decision."""

import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

REPORT_XML = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts/report.xml")
OBSERVABILITY_JSON = Path("data/release/observability_snapshot.json")
DEFECT_METRICS_JSON = Path("data/release/defect_metrics.json")
OUTPUT_JSON = Path("artifacts/release-readiness.json")
OUTPUT_MD = Path("artifacts/release-readiness.md")

GATE_VERSION = "1.0"
DATA_NOTE = (
    "observability and defect inputs are sample blueprint data, "
    "not live production metrics"
)


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc


def parse_test_results(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — JUnit XML was not produced by this run"
        )
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise ValueError(f"{path} could not be parsed as JUnit XML: {exc}") from exc

    root = tree.getroot()
    if root.tag == "testsuites":
        suites = root.findall("testsuite") or [root]
    else:
        suites = [root]

    total = errors = failures = skipped = 0
    duration = 0.0
    failed_tests = []

    for suite in suites:
        total += int(suite.get("tests", 0))
        errors += int(suite.get("errors", 0))
        failures += int(suite.get("failures", 0))
        skipped += int(suite.get("skipped", 0))
        duration += float(suite.get("time", 0.0))
        for tc in suite.findall("testcase"):
            if tc.find("failure") is not None or tc.find("error") is not None:
                classname = tc.get("classname", "")
                name = tc.get("name", "")
                label = f"{classname}.{name}" if classname else name
                failed_tests.append(label)

    return {
        "total": total,
        "passed": total - failures - errors - skipped,
        "failed": failures,
        "errors": errors,
        "skipped": skipped,
        "duration_secs": round(duration, 2),
        "failed_test_names": failed_tests,
        "source": str(path),
    }


def evaluate_gate(
    test_results: dict, obs: dict, defects: dict
) -> tuple[str, list[str], list[str]]:
    gate_failures = []
    warnings = []

    # Test result rules
    if test_results["failed"] > 0:
        gate_failures.append(f"test failures: {test_results['failed']} test(s) failed")
    if test_results["errors"] > 0:
        gate_failures.append(f"test errors: {test_results['errors']} test(s) errored")

    # Observability rules
    obs_metrics = obs.get("metrics", {})
    obs_thresholds = obs.get("thresholds", {})

    error_rate = obs_metrics.get("production_error_rate_pct", 0.0)
    max_error_rate = obs_thresholds.get("max_error_rate_pct", 1.0)
    if error_rate > max_error_rate:
        gate_failures.append(
            f"production_error_rate_pct {error_rate}% exceeds threshold {max_error_rate}%"
        )

    p95 = obs_metrics.get("p95_latency_ms", 0)
    max_p95 = obs_thresholds.get("max_p95_latency_ms", 500)
    if p95 > max_p95:
        warnings.append(f"p95_latency_ms {p95}ms exceeds threshold {max_p95}ms")

    p99 = obs_metrics.get("p99_latency_ms", 0)
    max_p99 = obs_thresholds.get("max_p99_latency_ms", 800)
    if p99 > max_p99:
        warnings.append(f"p99_latency_ms {p99}ms exceeds threshold {max_p99}ms")

    incident_count = obs_metrics.get("recent_incident_count", 0)
    max_incidents = obs_thresholds.get("max_recent_incident_count", 0)
    if incident_count > max_incidents:
        warnings.append(
            f"recent_incident_count is {incident_count} (threshold: {max_incidents})"
        )

    # Defect rules
    defect_metrics = defects.get("metrics", {})

    open_blockers = defect_metrics.get("open_blocker_defects", 0)
    if open_blockers > 0:
        gate_failures.append(f"open_blocker_defects: {open_blockers} open blocker(s)")

    escape_count = defect_metrics.get("defect_escape_count", 0)
    if escape_count > 0:
        warnings.append(f"defect_escape_count is {escape_count}")

    decision = "GO" if not gate_failures else "NO_GO"
    return decision, gate_failures, warnings


def build_output(
    test_results: dict,
    obs: dict,
    defects: dict,
    decision: str,
    gate_failures: list[str],
    warnings: list[str],
) -> dict:
    obs_metrics = obs.get("metrics", {})
    defect_metrics = defects.get("metrics", {})

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_version": GATE_VERSION,
        "overall_decision": decision,
        "gate_failures": gate_failures,
        "warnings": warnings,
        "data_note": DATA_NOTE,
        "test_results": {
            "total": test_results["total"],
            "passed": test_results["passed"],
            "failed": test_results["failed"],
            "errors": test_results["errors"],
            "skipped": test_results["skipped"],
            "duration_secs": test_results["duration_secs"],
            "failed_test_names": test_results["failed_test_names"],
            "source": test_results["source"],
        },
        "observability": {
            "environment": obs.get("environment", "unknown"),
            "snapshot_timestamp": obs.get("snapshot_timestamp", ""),
            "production_error_rate_pct": obs_metrics.get("production_error_rate_pct"),
            "p95_latency_ms": obs_metrics.get("p95_latency_ms"),
            "p99_latency_ms": obs_metrics.get("p99_latency_ms"),
            "recent_incident_count": obs_metrics.get("recent_incident_count"),
        },
        "defect_metrics": {
            "environment": defects.get("environment", "unknown"),
            "snapshot_timestamp": defects.get("snapshot_timestamp", ""),
            "open_blocker_defects": defect_metrics.get("open_blocker_defects"),
            "open_critical_defects": defect_metrics.get("open_critical_defects"),
            "defect_escape_count": defect_metrics.get("defect_escape_count"),
        },
    }


def render_markdown(output: dict) -> str:
    decision = output["overall_decision"]
    badge = "✅ GO" if decision == "GO" else "❌ NO_GO"

    lines = [
        "## Release Readiness Gate",
        "",
        f"**Decision: {badge}**",
        "",
        f"_Generated: {output['generated_at']} · Gate version: {output['gate_version']}_",
        "",
    ]

    if output["gate_failures"]:
        lines += ["### Gate Failures", ""]
        for f in output["gate_failures"]:
            lines.append(f"- ❌ {f}")
        lines.append("")

    if output["warnings"]:
        lines += ["### Warnings", ""]
        for w in output["warnings"]:
            lines.append(f"- ⚠️ {w}")
        lines.append("")

    tr = output["test_results"]
    lines += [
        "### Test Results",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Total | {tr['total']} |",
        f"| Passed | {tr['passed']} |",
        f"| Failed | {tr['failed']} |",
        f"| Errors | {tr['errors']} |",
        f"| Skipped | {tr['skipped']} |",
        f"| Duration | {tr['duration_secs']}s |",
        "",
    ]

    if tr.get("failed_test_names"):
        lines += ["#### Failed Tests", ""]
        for t in tr["failed_test_names"]:
            lines.append(f"- `{t}`")
        lines.append("")

    obs = output["observability"]
    defects = output["defect_metrics"]
    lines += [
        "### Observability & Defect Signals",
        "",
        "| Signal | Value |",
        "|---|---|",
        f"| Error rate | {obs['production_error_rate_pct']}% |",
        f"| p95 latency | {obs['p95_latency_ms']}ms |",
        f"| p99 latency | {obs['p99_latency_ms']}ms |",
        f"| Recent incidents | {obs['recent_incident_count']} |",
        f"| Open blockers | {defects['open_blocker_defects']} |",
        f"| Open criticals | {defects['open_critical_defects']} |",
        f"| Defect escapes | {defects['defect_escape_count']} |",
        "",
        f"> _{output['data_note']}_",
        "",
    ]

    return "\n".join(lines)


def write_error_output(message: str) -> None:
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    error_output = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_version": GATE_VERSION,
        "overall_decision": "NO_GO",
        "gate_failures": [message],
        "warnings": [],
        "data_note": DATA_NOTE,
    }
    OUTPUT_JSON.write_text(json.dumps(error_output, indent=2), encoding="utf-8")
    OUTPUT_MD.write_text(
        "\n".join(
            [
                "## Release Readiness Gate",
                "",
                "**Decision: ❌ NO_GO**",
                "",
                "### Gate Failures",
                "",
                f"- ❌ {message}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    try:
        test_results = parse_test_results(REPORT_XML)
    except (FileNotFoundError, ValueError) as exc:
        write_error_output(str(exc))
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        obs = load_json(OBSERVABILITY_JSON)
    except (FileNotFoundError, ValueError) as exc:
        write_error_output(str(exc))
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        defects = load_json(DEFECT_METRICS_JSON)
    except (FileNotFoundError, ValueError) as exc:
        write_error_output(str(exc))
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    decision, gate_failures, warnings = evaluate_gate(test_results, obs, defects)
    output = build_output(test_results, obs, defects, decision, gate_failures, warnings)

    OUTPUT_JSON.write_text(json.dumps(output, indent=2), encoding="utf-8")
    OUTPUT_MD.write_text(render_markdown(output), encoding="utf-8")

    status = "✅ GO" if decision == "GO" else "❌ NO_GO"
    print(f"Release gate decision: {status}")
    if gate_failures:
        print("Gate failures:")
        for f in gate_failures:
            print(f"  - {f}")
    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  - {w}")
    print(f"Outputs: {OUTPUT_JSON}, {OUTPUT_MD}")

    return 0 if decision == "GO" else 1


if __name__ == "__main__":
    sys.exit(main())
