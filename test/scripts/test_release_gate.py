"""Unit tests for scripts/release_gate.py — JUnit XML parsing and gate decision logic.

Covers parse_test_results() (TC-SCRIPT-001 to TC-SCRIPT-003b) and evaluate_gate()
(TC-SCRIPT-004 to TC-SCRIPT-009). Network calls, file writes, and main() are excluded.
"""

import pytest

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
