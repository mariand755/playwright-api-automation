"""Unit tests for scripts/ci_summary.py — JUnit XML parsing and markdown output.

Covers summarize() (TC-SCRIPT-010 to TC-SCRIPT-013). Assertions check status indicators
and failed test names only; exact markdown table layout is not asserted.
"""

import pytest

from scripts.ci_summary import summarize


# TC-SCRIPT-010 — summarize: missing XML returns error string, does not raise
@pytest.mark.scripts
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-010")
def test_summarize_missing_file(tmp_path):
    missing = str(tmp_path / "nonexistent.xml")
    result = summarize(missing)
    assert isinstance(result, str), "Expected string return for missing file"
    assert "not found" in result, f"Expected 'not found' in result, got:\n{result}"


# TC-SCRIPT-011 — summarize: malformed XML returns error string, does not raise
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-011")
def test_summarize_malformed_xml(malformed_xml_file):
    result = summarize(str(malformed_xml_file))
    assert isinstance(result, str), "Expected string return for malformed XML"
    assert "parse" in result.lower() or "error" in result.lower(), (
        f"Expected 'parse' or 'error' in result, got:\n{result}"
    )


# TC-SCRIPT-012 — summarize: all-passing XML returns pass indicator
@pytest.mark.scripts
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-012")
def test_summarize_all_passing(clean_junit_xml):
    result = summarize(str(clean_junit_xml))
    assert "✅" in result, f"Expected pass indicator '✅' in result, got:\n{result}"


# TC-SCRIPT-013 — summarize: failing XML returns fail indicator and failed test name
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-013")
def test_summarize_with_failures(failing_junit_xml):
    result = summarize(str(failing_junit_xml))
    assert "❌" in result, f"Expected fail indicator '❌' in result, got:\n{result}"
    assert "test_two" in result, f"Expected 'test_two' in result, got:\n{result}"
