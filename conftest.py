
import json
from pathlib import Path
import pytest
from playwright.sync_api import expect

from utils.timeouts import (
    API_REQUEST_TIMEOUT_SECONDS,
    UI_ACTION_TIMEOUT_MS,
    UI_EXPECT_TIMEOUT_MS,
    UI_NAVIGATION_TIMEOUT_MS,
)


@pytest.fixture(scope="session")
def base_url():
    return "https://www.saucedemo.com"


@pytest.fixture(scope="session")
def credentials():
    # Load from data/test_data/test_users.json.
    data_file = Path(__file__).parent / "data" / "test_data" / "test_users.json"
    with open(data_file) as f:
        users = json.load(f)

    # Use valid_user by default.
    valid_user = users.get("valid_user", {})
    return {
        "username": valid_user.get("username", "standard_user"),
        "password": valid_user.get("password", "secret_sauce"),
    }


@pytest.fixture(scope="session")
def api_base_url():
    return "https://restful-booker.herokuapp.com"


@pytest.fixture(scope="session")
def booking_api(api_base_url):
    from utils.api_client import BookingApiClient

    return BookingApiClient(api_base_url, timeout=API_REQUEST_TIMEOUT_SECONDS)


@pytest.fixture
def page(page):
    page.set_default_timeout(UI_ACTION_TIMEOUT_MS)
    page.set_default_navigation_timeout(UI_NAVIGATION_TIMEOUT_MS)
    expect.set_options(timeout=UI_EXPECT_TIMEOUT_MS)
    return page


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            artifacts_dir = Path("artifacts") / "failures"
            artifacts_dir.mkdir(parents=True, exist_ok=True)

            screenshot_path = artifacts_dir / f"{item.name}.png"
            html_path = artifacts_dir / f"{item.name}.html"

            page.screenshot(path=str(screenshot_path), full_page=True)
            html_path.write_text(page.content(), encoding="utf-8")
