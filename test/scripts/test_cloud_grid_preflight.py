"""Unit tests for scripts/cloud_grid_preflight.py.

Covers TC-SCRIPT-032 to TC-SCRIPT-041.
All tests use monkeypatch for env vars and mock the HTTP call.
No real network calls are made; no real credentials are used.
"""

import json
import urllib.error
import urllib.request
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import scripts.cloud_grid_preflight as preflight


def _http_response(status: int) -> MagicMock:
    """Return a mock urlopen context-manager response with the given HTTP status."""
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.__enter__ = lambda self: self
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _read_preflight_json(tmp_path: Path) -> dict:
    return json.loads((tmp_path / "cloud-grid-preflight.json").read_text())


# ---------------------------------------------------------------------------
# Provider = none
# ---------------------------------------------------------------------------


# TC-SCRIPT-032 — provider 'none' exits 0 with SKIPPED_NOT_CONFIGURED
@pytest.mark.scripts
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-032")
def test_provider_none_returns_skipped_not_configured(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOUD_GRID_PROVIDER", "none")
    monkeypatch.chdir(tmp_path)
    result = preflight.run()
    assert result == 0
    data = _read_preflight_json(tmp_path / "artifacts")
    assert data["status"] == preflight.STATUS_SKIPPED_NOT_CONFIGURED
    assert data["provider"] == "none"


# TC-SCRIPT-033 — provider unset defaults to 'none'; exits 0 with SKIPPED_NOT_CONFIGURED
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-033")
def test_provider_unset_defaults_to_not_configured(monkeypatch, tmp_path):
    monkeypatch.delenv("CLOUD_GRID_PROVIDER", raising=False)
    monkeypatch.chdir(tmp_path)
    result = preflight.run()
    assert result == 0
    data = _read_preflight_json(tmp_path / "artifacts")
    assert data["status"] == preflight.STATUS_SKIPPED_NOT_CONFIGURED


# ---------------------------------------------------------------------------
# Provider = sauce — missing credentials
# ---------------------------------------------------------------------------


# TC-SCRIPT-034 — sauce missing SAUCE_USERNAME → SKIPPED_MISSING_CREDENTIALS
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-034")
def test_sauce_missing_username(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOUD_GRID_PROVIDER", "sauce")
    monkeypatch.delenv("SAUCE_USERNAME", raising=False)
    monkeypatch.setenv("SAUCE_ACCESS_KEY", "some-key")
    monkeypatch.chdir(tmp_path)
    result = preflight.run()
    assert result == 0
    data = _read_preflight_json(tmp_path / "artifacts")
    assert data["status"] == preflight.STATUS_SKIPPED_MISSING_CREDENTIALS


# TC-SCRIPT-035 — sauce missing SAUCE_ACCESS_KEY → SKIPPED_MISSING_CREDENTIALS
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-035")
def test_sauce_missing_access_key(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOUD_GRID_PROVIDER", "sauce")
    monkeypatch.setenv("SAUCE_USERNAME", "some-user")
    monkeypatch.delenv("SAUCE_ACCESS_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    result = preflight.run()
    assert result == 0
    data = _read_preflight_json(tmp_path / "artifacts")
    assert data["status"] == preflight.STATUS_SKIPPED_MISSING_CREDENTIALS


# ---------------------------------------------------------------------------
# Provider = sauce — HTTP call mocked
# ---------------------------------------------------------------------------


# TC-SCRIPT-036 — sauce valid credentials (mock 200) → READY
@pytest.mark.scripts
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-036")
def test_sauce_valid_credentials_returns_ready(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOUD_GRID_PROVIDER", "sauce")
    monkeypatch.setenv("SAUCE_USERNAME", "test-user")
    monkeypatch.setenv("SAUCE_ACCESS_KEY", "test-key")
    monkeypatch.setenv("SAUCE_REGION", "us-west-1")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        urllib.request, "urlopen", lambda req, timeout=None: _http_response(200)
    )
    result = preflight.run()
    assert result == 0
    data = _read_preflight_json(tmp_path / "artifacts")
    assert data["status"] == preflight.STATUS_READY
    assert data["provider"] == "sauce"


# TC-SCRIPT-037 — sauce invalid credentials (mock 401) → SKIPPED_INVALID_CREDENTIALS
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-037")
def test_sauce_invalid_credentials_401(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOUD_GRID_PROVIDER", "sauce")
    monkeypatch.setenv("SAUCE_USERNAME", "bad-user")
    monkeypatch.setenv("SAUCE_ACCESS_KEY", "bad-key")
    monkeypatch.chdir(tmp_path)

    def raise_401(req, timeout=None):
        raise urllib.error.HTTPError(
            url=None, code=401, msg="Unauthorized", hdrs=None, fp=BytesIO(b"")
        )

    monkeypatch.setattr(urllib.request, "urlopen", raise_401)
    result = preflight.run()
    assert result == 0
    data = _read_preflight_json(tmp_path / "artifacts")
    assert data["status"] == preflight.STATUS_SKIPPED_INVALID_CREDENTIALS


# TC-SCRIPT-038 — sauce invalid credentials (mock 403) → SKIPPED_INVALID_CREDENTIALS
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-038")
def test_sauce_invalid_credentials_403(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOUD_GRID_PROVIDER", "sauce")
    monkeypatch.setenv("SAUCE_USERNAME", "bad-user")
    monkeypatch.setenv("SAUCE_ACCESS_KEY", "bad-key")
    monkeypatch.chdir(tmp_path)

    def raise_403(req, timeout=None):
        raise urllib.error.HTTPError(
            url=None, code=403, msg="Forbidden", hdrs=None, fp=BytesIO(b"")
        )

    monkeypatch.setattr(urllib.request, "urlopen", raise_403)
    result = preflight.run()
    assert result == 0
    data = _read_preflight_json(tmp_path / "artifacts")
    assert data["status"] == preflight.STATUS_SKIPPED_INVALID_CREDENTIALS


# TC-SCRIPT-039 — sauce network error (URLError) → SKIPPED_PROVIDER_UNAVAILABLE
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-039")
def test_sauce_provider_unavailable_on_network_error(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOUD_GRID_PROVIDER", "sauce")
    monkeypatch.setenv("SAUCE_USERNAME", "test-user")
    monkeypatch.setenv("SAUCE_ACCESS_KEY", "test-key")
    monkeypatch.chdir(tmp_path)

    def raise_url_error(req, timeout=None):
        raise urllib.error.URLError(reason="Network unreachable")

    monkeypatch.setattr(urllib.request, "urlopen", raise_url_error)
    result = preflight.run()
    assert result == 0
    data = _read_preflight_json(tmp_path / "artifacts")
    assert data["status"] == preflight.STATUS_PROVIDER_UNAVAILABLE


# TC-SCRIPT-040 — sauce timeout (OSError) → SKIPPED_PROVIDER_UNAVAILABLE
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-040")
def test_sauce_provider_unavailable_on_timeout(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOUD_GRID_PROVIDER", "sauce")
    monkeypatch.setenv("SAUCE_USERNAME", "test-user")
    monkeypatch.setenv("SAUCE_ACCESS_KEY", "test-key")
    monkeypatch.chdir(tmp_path)

    def raise_timeout(req, timeout=None):
        raise TimeoutError("timed out")

    monkeypatch.setattr(urllib.request, "urlopen", raise_timeout)
    result = preflight.run()
    assert result == 0
    data = _read_preflight_json(tmp_path / "artifacts")
    assert data["status"] == preflight.STATUS_PROVIDER_UNAVAILABLE


# ---------------------------------------------------------------------------
# Unknown provider — configuration bug
# ---------------------------------------------------------------------------


# TC-SCRIPT-041 — unknown CLOUD_GRID_PROVIDER value → exit 1 (repo config bug)
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-041")
def test_unknown_provider_exits_nonzero(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOUD_GRID_PROVIDER", "jenkins")
    monkeypatch.chdir(tmp_path)
    result = preflight.run()
    assert result == 1


# ---------------------------------------------------------------------------
# Provider = browserstack
# ---------------------------------------------------------------------------


# TC-SCRIPT-065 — browserstack missing credentials → SKIPPED_MISSING_CREDENTIALS
@pytest.mark.scripts
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-065")
def test_browserstack_missing_credentials_returns_skipped_missing(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("CLOUD_GRID_PROVIDER", "browserstack")
    monkeypatch.delenv("BROWSERSTACK_USERNAME", raising=False)
    monkeypatch.delenv("BROWSERSTACK_ACCESS_KEY", raising=False)
    monkeypatch.chdir(tmp_path)

    result = preflight.run()

    assert result == 0
    data = _read_preflight_json(tmp_path / "artifacts")
    assert data["status"] == preflight.STATUS_SKIPPED_MISSING_CREDENTIALS
    assert data["provider"] == "browserstack"


# TC-SCRIPT-066 — browserstack credentials present → SKIPPED_PROVIDER_EXECUTION_NOT_IMPLEMENTED
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-066")
def test_browserstack_credentials_present_returns_not_implemented(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("CLOUD_GRID_PROVIDER", "browserstack")
    monkeypatch.setenv("BROWSERSTACK_USERNAME", "test-bs-user")
    monkeypatch.setenv("BROWSERSTACK_ACCESS_KEY", "test-bs-key")
    monkeypatch.chdir(tmp_path)

    result = preflight.run()

    assert result == 0
    data = _read_preflight_json(tmp_path / "artifacts")
    assert data["status"] == preflight.STATUS_SKIPPED_PROVIDER_EXECUTION_NOT_IMPLEMENTED
    assert data["provider"] == "browserstack"
