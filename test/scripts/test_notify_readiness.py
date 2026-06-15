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
    load_advisory_status,
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


# ---------------------------------------------------------------------------
# Advisory status — load_advisory_status and build_message_lines advisory section
# ---------------------------------------------------------------------------

_ADVISORY_SKIPPED: dict[str, object] = {
    "cloud_grid_status": "SKIPPED",
    "cloud_grid_detail": "",
    "cross_browser_status": "SKIPPED",
    "cross_browser_by_browser": {},
}


# TC-SCRIPT-042 — load_advisory_status: all SKIPPED when no artifacts and both env vars 'skipped'
@pytest.mark.scripts
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-042")
def test_advisory_status_all_skipped_when_not_scheduled(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "skipped")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    result = load_advisory_status()
    assert result["cloud_grid_status"] == "SKIPPED"
    assert result["cross_browser_status"] == "SKIPPED"
    assert result["cross_browser_by_browser"] == {}


# TC-SCRIPT-043 — load_advisory_status: cloud-grid PASS from status artifact
@pytest.mark.scripts
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-043")
def test_advisory_cloud_grid_pass_from_artifact(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "success")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / "cloud-grid-status.json").write_text(
        '{"status": "PASS", "detail": "smoke suite passed"}', encoding="utf-8"
    )
    result = load_advisory_status()
    assert result["cloud_grid_status"] == "PASS"
    assert result["cloud_grid_detail"] == "smoke suite passed"


# TC-SCRIPT-044 — load_advisory_status: cloud-grid FAIL with detail from artifact
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-044")
def test_advisory_cloud_grid_fail_from_artifact(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "success")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / "cloud-grid-status.json").write_text(
        '{"status": "FAIL", "detail": "remote session could not be provisioned or connection timed out"}',
        encoding="utf-8",
    )
    result = load_advisory_status()
    assert result["cloud_grid_status"] == "FAIL"
    assert "remote session" in str(result["cloud_grid_detail"])


# TC-SCRIPT-045 — load_advisory_status: cloud-grid SKIPPED propagated from artifact
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-045")
def test_advisory_cloud_grid_skipped_from_artifact(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "success")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / "cloud-grid-status.json").write_text(
        '{"status": "SKIPPED", "detail": "preflight status: SKIPPED_NOT_CONFIGURED"}',
        encoding="utf-8",
    )
    result = load_advisory_status()
    assert result["cloud_grid_status"] == "SKIPPED"


# TC-SCRIPT-046 — load_advisory_status: cross-browser PASS when all 3 browser artifacts are PASS
@pytest.mark.scripts
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-046")
def test_advisory_cross_browser_pass_all_browsers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "skipped")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "success")
    (tmp_path / "artifacts").mkdir()
    for browser in ("chromium", "firefox", "webkit"):
        (tmp_path / "artifacts" / f"cross-browser-{browser}-status.json").write_text(
            f'{{"status": "PASS", "browser": "{browser}"}}', encoding="utf-8"
        )
    result = load_advisory_status()
    assert result["cross_browser_status"] == "PASS"
    assert result["cross_browser_by_browser"] == {
        "chromium": "PASS",
        "firefox": "PASS",
        "webkit": "PASS",
    }


# TC-SCRIPT-047 — load_advisory_status: cross-browser FAIL when all browser artifacts are FAIL
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-047")
def test_advisory_cross_browser_fail_all_browsers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "skipped")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "success")
    (tmp_path / "artifacts").mkdir()
    for browser in ("chromium", "firefox", "webkit"):
        (tmp_path / "artifacts" / f"cross-browser-{browser}-status.json").write_text(
            f'{{"status": "FAIL", "browser": "{browser}"}}', encoding="utf-8"
        )
    result = load_advisory_status()
    assert result["cross_browser_status"] == "FAIL"


# TC-SCRIPT-048 — load_advisory_status: cross-browser PARTIAL when mixed pass/fail browser artifacts
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-048")
def test_advisory_cross_browser_partial(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "skipped")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "success")
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / "cross-browser-chromium-status.json").write_text(
        '{"status": "PASS", "browser": "chromium"}', encoding="utf-8"
    )
    (tmp_path / "artifacts" / "cross-browser-firefox-status.json").write_text(
        '{"status": "FAIL", "browser": "firefox"}', encoding="utf-8"
    )
    # webkit artifact absent — only chromium and firefox present
    result = load_advisory_status()
    assert result["cross_browser_status"] == "PARTIAL"


# TC-SCRIPT-049 — build_message_lines: advisory section shown when advisory jobs were scheduled
@pytest.mark.scripts
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-049")
def test_build_message_lines_includes_advisory_section_when_scheduled(monkeypatch):
    monkeypatch.setenv("CLOUD_GRID_RESULT", "success")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "success")
    advisory: dict[str, object] = {
        "cloud_grid_status": "FAIL",
        "cloud_grid_detail": "remote session could not be provisioned or connection timed out",
        "cross_browser_status": "PASS",
        "cross_browser_by_browser": {
            "chromium": "PASS",
            "firefox": "PASS",
            "webkit": "PASS",
        },
    }
    lines = build_message_lines(
        None, run_url="", ci_status=_ALL_SUCCESS, advisory_status=advisory
    )
    combined = "\n".join(lines)
    assert "Advisory Jobs" in combined, f"Expected advisory section, got: {combined!r}"
    assert "UI Cross-Browser" in combined
    assert "Cloud Grid" in combined
    assert "FAIL" in combined


# TC-SCRIPT-050 — build_message_lines: advisory section NOT shown when both advisory jobs skipped
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-050")
def test_build_message_lines_no_advisory_section_when_not_scheduled(monkeypatch):
    monkeypatch.setenv("CLOUD_GRID_RESULT", "skipped")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    lines = build_message_lines(
        None, run_url="", ci_status=_ALL_SUCCESS, advisory_status=_ADVISORY_SKIPPED
    )
    combined = "\n".join(lines)
    assert "Advisory Jobs" not in combined, (
        f"Expected no advisory section when not scheduled, got: {combined!r}"
    )


# TC-SCRIPT-051 — advisory FAIL does not change overall readiness when required lane is GO
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-051")
def test_overall_readiness_unaffected_by_advisory_fail(monkeypatch):
    monkeypatch.setenv("CLOUD_GRID_RESULT", "success")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "success")
    advisory: dict[str, object] = {
        "cloud_grid_status": "FAIL",
        "cloud_grid_detail": "connection failed",
        "cross_browser_status": "FAIL",
        "cross_browser_by_browser": {
            "chromium": "FAIL",
            "firefox": "FAIL",
            "webkit": "FAIL",
        },
    }
    gate_data: dict[str, object] = {
        "overall_decision": "GO",
        "gate_failures": [],
        "warnings": [],
        "test_results": {
            "total": 22,
            "passed": 22,
            "failed": 0,
            "skipped": 0,
            "duration_secs": 10,
        },
    }
    lines = build_message_lines(
        gate_data, run_url="", ci_status=_ALL_SUCCESS, advisory_status=advisory
    )
    combined = "\n".join(lines)
    assert "Overall Release Readiness: ✅ GO" in combined, (
        f"Advisory FAIL must not change overall readiness; expected GO line, got: {combined!r}"
    )
    assert "Advisory Jobs" in combined, (
        "Advisory section must still appear when scheduled"
    )


# TC-SCRIPT-052 — load_advisory_status: all-UNKNOWN artifacts aggregate to UNKNOWN, not PARTIAL
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-052")
def test_advisory_cross_browser_all_unknown_aggregates_to_unknown(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "skipped")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "success")
    (tmp_path / "artifacts").mkdir()
    for browser in ("chromium", "firefox", "webkit"):
        (tmp_path / "artifacts" / f"cross-browser-{browser}-status.json").write_text(
            "not valid json", encoding="utf-8"
        )
    result = load_advisory_status()
    assert result["cross_browser_status"] == "UNKNOWN", (
        f"All-UNKNOWN browser artifacts must aggregate to UNKNOWN, got: {result['cross_browser_status']!r}"
    )
    assert result["cross_browser_by_browser"] == {
        "chromium": "UNKNOWN",
        "firefox": "UNKNOWN",
        "webkit": "UNKNOWN",
    }


# TC-SCRIPT-053 — build_message_lines: advisory section hidden when both env vars are empty (local dry-run)
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-053")
def test_build_message_lines_no_advisory_section_when_env_unset(monkeypatch):
    monkeypatch.delenv("CLOUD_GRID_RESULT", raising=False)
    monkeypatch.delenv("UI_CROSS_BROWSER_RESULT", raising=False)
    advisory: dict[str, object] = {
        "cloud_grid_status": "SKIPPED",
        "cloud_grid_detail": "",
        "cross_browser_status": "SKIPPED",
        "cross_browser_by_browser": {},
    }
    lines = build_message_lines(
        None, run_url="", ci_status=_ALL_SUCCESS, advisory_status=advisory
    )
    combined = "\n".join(lines)
    assert "Advisory Jobs" not in combined, (
        f"Advisory section must be hidden when env vars are unset (local dry-run), got: {combined!r}"
    )


# TC-SCRIPT-054 — load_advisory_status: cloud-grid FAIL with preflight-failed detail renders as FAIL
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-054")
def test_advisory_cloud_grid_preflight_fail_renders_as_fail(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "success")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / "cloud-grid-status.json").write_text(
        '{"status": "FAIL", "detail": "cloud-grid preflight failed: ERROR_UNKNOWN_PROVIDER"}',
        encoding="utf-8",
    )
    result = load_advisory_status()
    assert result["cloud_grid_status"] == "FAIL", (
        f"Preflight-failed detail must render as FAIL, got: {result['cloud_grid_status']!r}"
    )
    assert "ERROR_UNKNOWN_PROVIDER" in str(result["cloud_grid_detail"])


# ---------------------------------------------------------------------------
# TC-SCRIPT-055–063 — Cloud Grid multi-browser matrix (PR #71)
# ---------------------------------------------------------------------------


# TC-SCRIPT-055 — load_advisory_status: cloud-grid all browsers PASS → aggregate PASS
@pytest.mark.scripts
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-055")
def test_advisory_cloud_grid_all_pass_aggregates_to_pass(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "success")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    (tmp_path / "artifacts").mkdir()
    for browser in ("chromium", "firefox", "webkit"):
        (tmp_path / "artifacts" / f"cloud-grid-{browser}-status.json").write_text(
            f'{{"status": "PASS", "detail": "smoke suite passed", "browser": "{browser}"}}',
            encoding="utf-8",
        )
    result = load_advisory_status()
    assert result["cloud_grid_status"] == "PASS", (
        f"All-PASS cloud-grid legs must aggregate to PASS, got: {result['cloud_grid_status']!r}"
    )
    assert result["cloud_grid_by_browser"] == {
        "chromium": "PASS",
        "firefox": "PASS",
        "webkit": "PASS",
    }


# TC-SCRIPT-056 — load_advisory_status: no cloud-grid artifacts + env skipped → SKIPPED
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-056")
def test_advisory_cloud_grid_no_artifacts_env_skipped_aggregates_to_skipped(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "skipped")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    result = load_advisory_status()
    assert result["cloud_grid_status"] == "SKIPPED", (
        f"No artifacts + env skipped must aggregate to SKIPPED, got: {result['cloud_grid_status']!r}"
    )
    assert result["cloud_grid_by_browser"] == {}


# TC-SCRIPT-057 — load_advisory_status: one cloud-grid FAIL + others PASS → PARTIAL
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-057")
def test_advisory_cloud_grid_one_fail_others_pass_aggregates_to_partial(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "success")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / "cloud-grid-chromium-status.json").write_text(
        '{"status": "FAIL", "detail": "remote session could not be provisioned", "browser": "chromium"}',
        encoding="utf-8",
    )
    (tmp_path / "artifacts" / "cloud-grid-firefox-status.json").write_text(
        '{"status": "PASS", "detail": "smoke suite passed", "browser": "firefox"}',
        encoding="utf-8",
    )
    (tmp_path / "artifacts" / "cloud-grid-webkit-status.json").write_text(
        '{"status": "PASS", "detail": "smoke suite passed", "browser": "webkit"}',
        encoding="utf-8",
    )
    result = load_advisory_status()
    assert result["cloud_grid_status"] == "PARTIAL", (
        f"One FAIL + others PASS must aggregate to PARTIAL, got: {result['cloud_grid_status']!r}"
    )
    assert result["cloud_grid_by_browser"]["chromium"] == "FAIL"
    assert result["cloud_grid_by_browser"]["firefox"] == "PASS"
    assert result["cloud_grid_by_browser"]["webkit"] == "PASS"
    assert (
        result["cloud_grid_detail_by_browser"]["chromium"]
        == "remote session could not be provisioned"
    )


# TC-SCRIPT-058 — load_advisory_status: all cloud-grid browsers FAIL → aggregate FAIL
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-058")
def test_advisory_cloud_grid_all_fail_aggregates_to_fail(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "success")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    (tmp_path / "artifacts").mkdir()
    for browser in ("chromium", "firefox", "webkit"):
        (tmp_path / "artifacts" / f"cloud-grid-{browser}-status.json").write_text(
            f'{{"status": "FAIL", "detail": "remote session could not be provisioned", "browser": "{browser}"}}',
            encoding="utf-8",
        )
    result = load_advisory_status()
    assert result["cloud_grid_status"] == "FAIL", (
        f"All-FAIL cloud-grid legs must aggregate to FAIL, got: {result['cloud_grid_status']!r}"
    )


# TC-SCRIPT-059 — load_advisory_status: all cloud-grid browsers unreadable → aggregate UNKNOWN
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-059")
def test_advisory_cloud_grid_all_unknown_aggregates_to_unknown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "success")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    (tmp_path / "artifacts").mkdir()
    for browser in ("chromium", "firefox", "webkit"):
        (tmp_path / "artifacts" / f"cloud-grid-{browser}-status.json").write_text(
            "not valid json", encoding="utf-8"
        )
    result = load_advisory_status()
    assert result["cloud_grid_status"] == "UNKNOWN", (
        f"All-UNKNOWN cloud-grid artifacts must aggregate to UNKNOWN, got: {result['cloud_grid_status']!r}"
    )
    assert result["cloud_grid_by_browser"] == {
        "chromium": "UNKNOWN",
        "firefox": "UNKNOWN",
        "webkit": "UNKNOWN",
    }


# TC-SCRIPT-060 — build_message_lines: cloud-grid PARTIAL renders per-browser detail lines
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-060")
def test_build_message_lines_renders_cloud_grid_per_browser_when_partial(monkeypatch):
    monkeypatch.setenv("CLOUD_GRID_RESULT", "success")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    advisory: dict[str, object] = {
        "cloud_grid_status": "PARTIAL",
        "cloud_grid_detail": "",
        "cloud_grid_by_browser": {
            "chromium": "FAIL",
            "firefox": "PASS",
            "webkit": "PASS",
        },
        "cloud_grid_detail_by_browser": {
            "chromium": "remote session could not be provisioned",
            "firefox": "smoke suite passed",
            "webkit": "smoke suite passed",
        },
        "cross_browser_status": "SKIPPED",
        "cross_browser_by_browser": {},
    }
    lines = build_message_lines(
        None, run_url="", ci_status=_ALL_SUCCESS, advisory_status=advisory
    )
    combined = "\n".join(lines)
    assert "PARTIAL" in combined
    assert "chromium" in combined
    assert "remote session could not be provisioned" in combined


# TC-SCRIPT-061 — build_message_lines: cloud-grid FAIL renders per-browser detail lines
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-061")
def test_build_message_lines_renders_cloud_grid_per_browser_when_fail(monkeypatch):
    monkeypatch.setenv("CLOUD_GRID_RESULT", "success")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    advisory: dict[str, object] = {
        "cloud_grid_status": "FAIL",
        "cloud_grid_detail": "",
        "cloud_grid_by_browser": {
            "chromium": "FAIL",
            "firefox": "FAIL",
            "webkit": "FAIL",
        },
        "cloud_grid_detail_by_browser": {
            "chromium": "remote session could not be provisioned",
            "firefox": "remote session could not be provisioned",
            "webkit": "remote session could not be provisioned",
        },
        "cross_browser_status": "SKIPPED",
        "cross_browser_by_browser": {},
    }
    lines = build_message_lines(
        None, run_url="", ci_status=_ALL_SUCCESS, advisory_status=advisory
    )
    combined = "\n".join(lines)
    assert "Cloud Grid" in combined
    assert "chromium" in combined
    assert "firefox" in combined
    assert "webkit" in combined


# TC-SCRIPT-062 — build_message_lines: cross-browser PARTIAL renders per-browser lines
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-062")
def test_build_message_lines_renders_cross_browser_per_browser_when_partial(
    monkeypatch,
):
    monkeypatch.setenv("CLOUD_GRID_RESULT", "skipped")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "success")
    advisory: dict[str, object] = {
        "cloud_grid_status": "SKIPPED",
        "cloud_grid_detail": "",
        "cloud_grid_by_browser": {},
        "cloud_grid_detail_by_browser": {},
        "cross_browser_status": "PARTIAL",
        "cross_browser_by_browser": {
            "chromium": "PASS",
            "firefox": "FAIL",
            "webkit": "PASS",
        },
    }
    lines = build_message_lines(
        None, run_url="", ci_status=_ALL_SUCCESS, advisory_status=advisory
    )
    combined = "\n".join(lines)
    assert "UI Cross-Browser" in combined
    assert "PARTIAL" in combined
    assert "chromium" in combined
    assert "firefox" in combined
    assert "webkit" in combined


# TC-SCRIPT-063 — build_message_lines: cloud-grid PASS → no per-browser lines (clean output)
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-063")
def test_build_message_lines_no_per_browser_detail_when_cloud_grid_all_pass(
    monkeypatch,
):
    monkeypatch.setenv("CLOUD_GRID_RESULT", "success")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    advisory: dict[str, object] = {
        "cloud_grid_status": "PASS",
        "cloud_grid_detail": "",
        "cloud_grid_by_browser": {
            "chromium": "PASS",
            "firefox": "PASS",
            "webkit": "PASS",
        },
        "cloud_grid_detail_by_browser": {
            "chromium": "smoke suite passed",
            "firefox": "smoke suite passed",
            "webkit": "smoke suite passed",
        },
        "cross_browser_status": "SKIPPED",
        "cross_browser_by_browser": {},
    }
    lines = build_message_lines(
        None, run_url="", ci_status=_ALL_SUCCESS, advisory_status=advisory
    )
    combined = "\n".join(lines)
    assert "Cloud Grid" in combined
    assert "PASS" in combined
    assert "chromium" not in combined, (
        "Happy-path PASS must not expand per-browser lines — keep notifications clean"
    )


# TC-SCRIPT-064 — load_advisory_status: all SKIPPED per-browser artifacts → aggregate SKIPPED
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-064")
def test_advisory_cloud_grid_all_skipped_per_browser_artifacts_aggregates_to_skipped(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_GRID_RESULT", "success")
    monkeypatch.setenv("UI_CROSS_BROWSER_RESULT", "skipped")
    (tmp_path / "artifacts").mkdir()
    for browser in ("chromium", "firefox", "webkit"):
        (tmp_path / "artifacts" / f"cloud-grid-{browser}-status.json").write_text(
            f'{{"status": "SKIPPED", "detail": "preflight status: SKIPPED_NOT_CONFIGURED", "browser": "{browser}"}}',
            encoding="utf-8",
        )
    result = load_advisory_status()
    assert result["cloud_grid_status"] == "SKIPPED", (
        f"All-SKIPPED per-browser artifacts must aggregate to SKIPPED, got: {result['cloud_grid_status']!r}"
    )
    assert result["cloud_grid_by_browser"] == {
        "chromium": "SKIPPED",
        "firefox": "SKIPPED",
        "webkit": "SKIPPED",
    }
