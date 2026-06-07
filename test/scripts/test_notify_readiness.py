"""Unit tests for compute_overall_readiness() in scripts/notify.py.

Covers TC-SCRIPT-014 to TC-SCRIPT-018. Delivery functions (send_slack, send_email)
are excluded — they require network calls outside the scope of this slice.
"""

import pytest

from scripts.notify import compute_overall_readiness

_ALL_SUCCESS = {
    "docker_test_suite": "success",
    "api_tests": "success",
    "ui_tests": "success",
}


# TC-SCRIPT-014 — compute_overall_readiness: all jobs success + gate GO → "GO"
@pytest.mark.scripts
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-014")
def test_readiness_go():
    result = compute_overall_readiness(_ALL_SUCCESS, "GO")
    assert result == "GO", f"Expected GO, got {result}"


# TC-SCRIPT-015 — compute_overall_readiness: all jobs success + gate NO_GO → "NO_GO"
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-015")
def test_readiness_no_go():
    result = compute_overall_readiness(_ALL_SUCCESS, "NO_GO")
    assert result == "NO_GO", f"Expected NO_GO, got {result}"


# TC-SCRIPT-016 — compute_overall_readiness: all jobs success + gate None → "UNKNOWN"
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-016")
def test_readiness_unknown():
    result = compute_overall_readiness(_ALL_SUCCESS, None)
    assert result == "UNKNOWN", f"Expected UNKNOWN, got {result}"


# TC-SCRIPT-017 — compute_overall_readiness: any required job not success → "BLOCKED"
# Parametrized to verify failure, cancelled, and skipped all trigger BLOCKED.
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-017")
@pytest.mark.parametrize("failing_status", ["failure", "cancelled", "skipped"])
def test_readiness_blocked_on_non_success(failing_status):
    ci_status = {**_ALL_SUCCESS, "api_tests": failing_status}
    result = compute_overall_readiness(ci_status, "GO")
    assert result == "BLOCKED", (
        f"Expected BLOCKED when api_tests='{failing_status}', got {result}"
    )


# TC-SCRIPT-018 — compute_overall_readiness: missing keys in ci_status do not trigger BLOCKED
# Empty string (absent env var) is falsy; only a truthy non-"success" value is BLOCKED.
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-018")
def test_readiness_missing_ci_status_not_blocked():
    result = compute_overall_readiness({}, "GO")
    assert result == "GO", (
        f"Expected GO when ci_status is empty (absent keys ≠ failed), got {result}"
    )
