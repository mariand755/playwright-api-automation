"""Unit tests for notify readiness helpers in scripts/notify.py.

Covers TC-SCRIPT-014 to TC-SCRIPT-018, TC-SCRIPT-026 to TC-SCRIPT-030.
Delivery functions (send_slack, send_email) are excluded — they require
network calls outside the scope of this slice.
"""

import pytest

from scripts.notify import (
    build_message_lines,
    compute_overall_readiness,
    get_smtp_transport_mode,
)

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


# ---------------------------------------------------------------------------
# build_message_lines — gate_skipped and data=None paths
# ---------------------------------------------------------------------------


# TC-SCRIPT-029 — build_message_lines: gate_skipped artifact emits smoke-skip message
# Verifies ⚠️ Skipped line appears and no "?" test-count placeholder leaks through.
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-029")
def test_build_message_lines_gate_skipped():
    data = {
        "overall_decision": "UNKNOWN",
        "gate_skipped": True,
        "gate_skip_reason": "release_gate_skipped_for_smoke_scope",
        "gate_failures": [],
        "warnings": [],
    }
    lines = build_message_lines(data, run_url="", ci_status=_ALL_SUCCESS)
    combined = "\n".join(lines)
    assert "Skipped" in combined, (
        f"Expected 'Skipped' in release gate message, got: {combined!r}"
    )
    assert "?" not in combined, (
        f"Expected no '?' (missing test counts) in message when gate_skipped, got: {combined!r}"
    )


# TC-SCRIPT-030 — build_message_lines: data=None still emits the existing no-gate-data message
# Regression guard: the existing data=None fallback must not be broken by the gate_skipped branch.
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-030")
def test_build_message_lines_no_gate_data():
    lines = build_message_lines(None, run_url="", ci_status=_ALL_SUCCESS)
    combined = "\n".join(lines)
    assert "No release gate data" in combined, (
        f"Expected 'No release gate data' in message when data=None, got: {combined!r}"
    )


# ---------------------------------------------------------------------------
# get_smtp_transport_mode
# ---------------------------------------------------------------------------


# TC-SCRIPT-026 — port 465 → SMTP_SSL
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-026")
def test_smtp_transport_mode_465():
    assert get_smtp_transport_mode(465) == "SMTP_SSL"


# TC-SCRIPT-027 — port 587 → STARTTLS
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-027")
def test_smtp_transport_mode_587():
    assert get_smtp_transport_mode(587) == "STARTTLS"


# TC-SCRIPT-028 — any non-465 port → STARTTLS (e.g. 2525)
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-028")
def test_smtp_transport_mode_non_465():
    assert get_smtp_transport_mode(2525) == "STARTTLS"
