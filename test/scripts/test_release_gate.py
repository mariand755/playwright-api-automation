"""Unit tests for scripts/release_gate.py — JUnit XML parsing and gate decision logic.

Covers parse_test_results() (TC-SCRIPT-001 to TC-SCRIPT-003b), evaluate_gate()
(TC-SCRIPT-004 to TC-SCRIPT-009), write_skipped_output() (TC-SCRIPT-019 to
TC-SCRIPT-020), write_error_output() (TC-SCRIPT-023), and main() custom output
paths (TC-SCRIPT-024).
"""

import json
import sys

import pytest

import scripts.release_gate as release_gate
from scripts.release_gate import evaluate_gate, parse_test_results


# ---------------------------------------------------------------------------
# parse_test_results
# ---------------------------------------------------------------------------


# TC-SCRIPT-001 — parse_test_results: valid XML, all passing
@pytest.mark.scripts
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-001")
def test_parse_valid_all_passing(clean_junit_xml):
    result = parse_test_results(clean_junit_xml)
    assert result["failed"] == 0, f"Expected 0 failures, got {result['failed']}"
    assert result["errors"] == 0, f"Expected 0 errors, got {result['errors']}"
    assert result["passed"] == 3, f"Expected 3 passed, got {result['passed']}"


# TC-SCRIPT-002 — parse_test_results: valid XML, one failure recorded in failed_test_names
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-002")
def test_parse_valid_with_failures(failing_junit_xml):
    result = parse_test_results(failing_junit_xml)
    assert result["failed"] == 1, f"Expected 1 failure, got {result['failed']}"
    assert any("test_two" in name for name in result["failed_test_names"]), (
        f"Expected 'test_two' in failed_test_names, got {result['failed_test_names']}"
    )


# TC-SCRIPT-003 — parse_test_results: missing XML raises FileNotFoundError
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-003")
def test_parse_missing_file(tmp_path):
    missing = tmp_path / "nonexistent.xml"
    with pytest.raises(FileNotFoundError):
        parse_test_results(missing)


# TC-SCRIPT-003b — parse_test_results: malformed XML raises ValueError
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-003b")
def test_parse_malformed_xml(malformed_xml_file):
    with pytest.raises(ValueError):
        parse_test_results(malformed_xml_file)


# ---------------------------------------------------------------------------
# evaluate_gate
# ---------------------------------------------------------------------------


# TC-SCRIPT-004 — evaluate_gate: clean inputs produce GO with no failures or warnings
@pytest.mark.scripts
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-004")
def test_evaluate_gate_go_clean(clean_test_results, clean_obs, clean_defects):
    decision, gate_failures, warnings = evaluate_gate(
        clean_test_results, clean_obs, clean_defects
    )
    assert decision == "GO", f"Expected GO, got {decision}"
    assert gate_failures == [], f"Expected no gate failures, got {gate_failures}"
    assert warnings == [], f"Expected no warnings, got {warnings}"


# TC-SCRIPT-005 — evaluate_gate: test failures are a hard gate → NO_GO
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-005")
def test_evaluate_gate_no_go_test_failures(
    clean_test_results, clean_obs, clean_defects
):
    test_results = {**clean_test_results, "failed": 2, "passed": 1}
    decision, gate_failures, _ = evaluate_gate(test_results, clean_obs, clean_defects)
    assert decision == "NO_GO", f"Expected NO_GO, got {decision}"
    assert any("test failures" in f for f in gate_failures), (
        f"Expected 'test failures' in gate_failures, got {gate_failures}"
    )


# TC-SCRIPT-006 — evaluate_gate: test errors are a hard gate → NO_GO
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-006")
def test_evaluate_gate_no_go_test_errors(clean_test_results, clean_obs, clean_defects):
    test_results = {**clean_test_results, "errors": 1, "passed": 2}
    decision, gate_failures, _ = evaluate_gate(test_results, clean_obs, clean_defects)
    assert decision == "NO_GO", f"Expected NO_GO, got {decision}"
    assert any("test errors" in f for f in gate_failures), (
        f"Expected 'test errors' in gate_failures, got {gate_failures}"
    )


# TC-SCRIPT-007 — evaluate_gate: error rate above threshold is a hard gate → NO_GO
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-007")
def test_evaluate_gate_no_go_high_error_rate(clean_test_results, clean_defects):
    obs = {
        "metrics": {
            "production_error_rate_pct": 2.0,
            "p95_latency_ms": 210,
            "p99_latency_ms": 450,
            "recent_incident_count": 0,
        },
        "thresholds": {
            "max_error_rate_pct": 1.0,
            "max_p95_latency_ms": 500,
            "max_p99_latency_ms": 800,
            "max_recent_incident_count": 0,
        },
    }
    decision, gate_failures, _ = evaluate_gate(clean_test_results, obs, clean_defects)
    assert decision == "NO_GO", f"Expected NO_GO, got {decision}"
    assert any("error_rate" in f for f in gate_failures), (
        f"Expected 'error_rate' in gate_failures, got {gate_failures}"
    )


# TC-SCRIPT-008 — evaluate_gate: open blocker defects are a hard gate → NO_GO
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-008")
def test_evaluate_gate_no_go_blocker_defects(clean_test_results, clean_obs):
    defects = {"metrics": {"open_blocker_defects": 1, "defect_escape_count": 0}}
    decision, gate_failures, _ = evaluate_gate(clean_test_results, clean_obs, defects)
    assert decision == "NO_GO", f"Expected NO_GO, got {decision}"
    assert any("blocker" in f for f in gate_failures), (
        f"Expected 'blocker' in gate_failures, got {gate_failures}"
    )


# TC-SCRIPT-009 — evaluate_gate: p95 latency and defect escape warnings do not block → GO
# p95=600 > max_p95=500 (warning), escape_count=2 > 0 (warning); both non-gate conditions
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-009")
def test_evaluate_gate_warnings_do_not_block(clean_test_results):
    obs = {
        "metrics": {
            "production_error_rate_pct": 0.3,
            "p95_latency_ms": 600,
            "p99_latency_ms": 450,
            "recent_incident_count": 0,
        },
        "thresholds": {
            "max_error_rate_pct": 1.0,
            "max_p95_latency_ms": 500,
            "max_p99_latency_ms": 800,
            "max_recent_incident_count": 0,
        },
    }
    defects = {"metrics": {"open_blocker_defects": 0, "defect_escape_count": 2}}
    decision, gate_failures, warnings = evaluate_gate(clean_test_results, obs, defects)
    assert decision == "GO", f"Expected GO despite warnings, got {decision}"
    assert gate_failures == [], f"Expected no gate failures, got {gate_failures}"
    assert len(warnings) == 2, (
        f"Expected exactly 2 warnings (p95 latency + defect escape), got {warnings}"
    )


# ---------------------------------------------------------------------------
# write_skipped_output
# ---------------------------------------------------------------------------


# TC-SCRIPT-019 — write_skipped_output: produces release-readiness.json with correct fields
@pytest.mark.scripts
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-019")
def test_write_skipped_output_json(tmp_path):
    out_json = tmp_path / "release-readiness.json"
    out_md = tmp_path / "release-readiness.md"

    release_gate.write_skipped_output("smoke", output_json=out_json, output_md=out_md)

    assert out_json.exists(), "release-readiness.json was not created"
    data = json.loads(out_json.read_text())
    assert data["overall_decision"] == "UNKNOWN", (
        f"Expected overall_decision=UNKNOWN, got {data['overall_decision']}"
    )
    assert data["gate_skipped"] is True, "Expected gate_skipped=true"
    assert "smoke" in data["gate_skip_reason"], (
        f"Expected 'smoke' in gate_skip_reason, got {data['gate_skip_reason']}"
    )
    assert data["gate_failures"] == [], (
        f"Expected empty gate_failures, got {data['gate_failures']}"
    )
    assert data["warnings"] == [], f"Expected empty warnings, got {data['warnings']}"


# TC-SCRIPT-020 — write_skipped_output: produces release-readiness.md with expected content
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-020")
def test_write_skipped_output_md(tmp_path):
    out_json = tmp_path / "release-readiness.json"
    out_md = tmp_path / "release-readiness.md"

    release_gate.write_skipped_output("smoke", output_json=out_json, output_md=out_md)

    assert out_md.exists(), "release-readiness.md was not created"
    content = out_md.read_text()
    assert "Release Readiness Gate" in content, (
        f"Expected 'Release Readiness Gate' heading in MD, got: {content!r}"
    )
    assert "intentionally skipped" in content, (
        f"Expected 'intentionally skipped' in MD, got: {content!r}"
    )


# TC-SCRIPT-023 — write_error_output: writes NO_GO decision to custom output paths
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-023")
def test_write_error_output_custom_paths(tmp_path):
    out_json = tmp_path / "custom-error.json"
    out_md = tmp_path / "custom-error.md"

    release_gate.write_error_output(
        "test failure message", output_json=out_json, output_md=out_md
    )

    assert out_json.exists(), "custom error JSON was not created"
    data = json.loads(out_json.read_text())
    assert data["overall_decision"] == "NO_GO", (
        f"Expected NO_GO, got {data['overall_decision']}"
    )
    assert any("test failure message" in f for f in data["gate_failures"]), (
        f"Expected 'test failure message' in gate_failures, got {data['gate_failures']}"
    )
    assert out_md.exists(), "custom error MD was not created"
    content = out_md.read_text()
    assert "NO_GO" in content, f"Expected 'NO_GO' in MD output, got: {content!r}"
    assert "test failure message" in content, (
        f"Expected 'test failure message' in MD output, got: {content!r}"
    )


# TC-SCRIPT-024 — main() honors --output-json and --output-md; writes to custom paths
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-024")
def test_main_honors_custom_output_paths(
    tmp_path, monkeypatch, clean_junit_xml, clean_obs, clean_defects
):
    out_json = tmp_path / "gate-output.json"
    out_md = tmp_path / "gate-output.md"
    obs_file = tmp_path / "obs.json"
    defect_file = tmp_path / "defects.json"
    obs_file.write_text(json.dumps(clean_obs), encoding="utf-8")
    defect_file.write_text(json.dumps(clean_defects), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "release_gate.py",
            str(clean_junit_xml),
            "--observability-json",
            str(obs_file),
            "--defect-metrics-json",
            str(defect_file),
            "--output-json",
            str(out_json),
            "--output-md",
            str(out_md),
        ],
    )
    rc = release_gate.main()

    assert rc == 0, f"Expected exit code 0 (GO), got {rc}"
    assert out_json.exists(), "Custom output JSON was not created"
    assert out_md.exists(), "Custom output MD was not created"
    data = json.loads(out_json.read_text())
    assert data["overall_decision"] == "GO", (
        f"Expected GO with clean inputs, got {data['overall_decision']}"
    )
