"""Unit tests for utils/browserstack_capabilities.py.

Covers TC-SCRIPT-073 to TC-SCRIPT-079.
Pure-function tests — no Playwright, network, or BrowserStack access required.
"""

from importlib.metadata import version

import pytest

from utils.browserstack_capabilities import (
    build_browserstack_caps,
    browserstack_status_payload,
    resolve_browser_capability,
)


# TC-SCRIPT-073 — chromium resolves to chrome
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-073")
def test_resolve_browser_capability_maps_chromium():
    assert resolve_browser_capability("chromium") == "chrome"


# TC-SCRIPT-074 — firefox resolves to playwright-firefox
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-074")
def test_resolve_browser_capability_maps_firefox():
    assert resolve_browser_capability("firefox") == "playwright-firefox"


# TC-SCRIPT-075 — webkit resolves to playwright-webkit
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-075")
def test_resolve_browser_capability_maps_webkit():
    assert resolve_browser_capability("webkit") == "playwright-webkit"


# TC-SCRIPT-076 — unsupported browser name fails fast with ValueError
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-076")
def test_resolve_browser_capability_rejects_unknown_browser():
    with pytest.raises(ValueError, match="msedge"):
        resolve_browser_capability("msedge")


# TC-SCRIPT-077 — caps include matching client/browserstack Playwright versions
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-077")
def test_build_browserstack_caps_includes_playwright_versions():
    expected_version = version("playwright")

    caps = build_browserstack_caps(
        browser_name="firefox",
        bs_username="user",
        bs_access_key="key",
    )

    assert caps["browser"] == "playwright-firefox"
    assert caps["client.playwrightVersion"] == expected_version
    assert caps["browserstack.playwrightVersion"] == expected_version


# TC-SCRIPT-078 — passed status payload contains the nodeid
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-078")
def test_browserstack_status_payload_passed_contains_nodeid_only():
    payload = browserstack_status_payload(True, "test/ui/test_login.py::test_login")

    assert payload["action"] == "setSessionStatus"
    assert payload["arguments"]["status"] == "passed"
    assert "test/ui/test_login.py::test_login" in payload["arguments"]["reason"]


# TC-SCRIPT-079 — failed status payload redacts exception details
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-079")
def test_browserstack_status_payload_failed_redacts_exception_details():
    payload = browserstack_status_payload(False, "test/ui/test_login.py::test_login")
    reason = payload["arguments"]["reason"]

    assert payload["arguments"]["status"] == "failed"
    assert "test/ui/test_login.py::test_login" in reason
    assert "Traceback" not in reason
    assert "Error:" not in reason
    assert "Exception" not in reason
