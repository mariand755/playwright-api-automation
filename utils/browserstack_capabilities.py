"""Pure helpers for BrowserStack capability construction and dashboard status marking.

No Playwright/network dependency. Kept separate from conftest.py so capability
behavior can be unit-tested without live BrowserStack access.
"""

from importlib.metadata import PackageNotFoundError, version
from typing import Any

BS_BROWSER_MAP: dict[str, str] = {
    "chromium": "chrome",
    "firefox": "playwright-firefox",
    "webkit": "playwright-webkit",
}


def resolve_browser_capability(browser_name: str) -> str:
    try:
        return BS_BROWSER_MAP[browser_name]
    except KeyError:
        raise ValueError(
            f"Unsupported BrowserStack browser: {browser_name!r}. "
            f"Supported: {sorted(BS_BROWSER_MAP)}."
        ) from None


def playwright_client_version() -> str:
    try:
        return version("playwright")
    except PackageNotFoundError:
        return "0.0.0"


def build_browserstack_caps(
    browser_name: str,
    bs_username: str,
    bs_access_key: str,
) -> dict[str, str]:
    pw_version = playwright_client_version()

    return {
        "browser": resolve_browser_capability(browser_name),
        "browser_version": "latest",
        "os": "osx",
        "os_version": "ventura",
        "name": "playwright-api-automation smoke",
        "build": "playwright-api-automation",
        "browserstack.username": bs_username,
        "browserstack.accessKey": bs_access_key,
        "client.playwrightVersion": pw_version,
        "browserstack.playwrightVersion": pw_version,
    }


def browserstack_status_payload(passed: bool, nodeid: str) -> dict[str, Any]:
    return {
        "action": "setSessionStatus",
        "arguments": {
            "status": "passed" if passed else "failed",
            "reason": f"pytest: {nodeid}",
        },
    }
