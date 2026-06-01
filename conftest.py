import json
import pytest

from pathlib import Path
from playwright.sync_api import expect
from utils.api_client import BookingApiClient

from utils.timeouts import (
    API_REQUEST_TIMEOUT_SECONDS,
    UI_ACTION_TIMEOUT_MS,
    UI_EXPECT_TIMEOUT_MS,
    UI_NAVIGATION_TIMEOUT_MS,
)


@pytest.fixture(scope="session")
def test_data():
    data_file = Path(__file__).parent / "data" / "test_data" / "test_users.json"
    with open(data_file, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def base_url(test_data):
    url = test_data.get("urls", {}).get("base_url")
    if not url:
        raise ValueError("Missing urls.base_url in data/test_data/test_users.json")
    return url


@pytest.fixture(scope="session")
def credentials(test_data):
    # Use valid_user by default.
    valid_user = test_data.get("valid_user", {})
    username = valid_user.get("username")
    password = valid_user.get("password")

    if not username or not password:
        raise ValueError(
            "Missing valid_user.username or valid_user.password in data/test_data/test_users.json"
        )

    return {
        "username": username,
        "password": password,
    }


@pytest.fixture(scope="session")
def locked_out_credentials(test_data):
    locked_out_user = test_data.get("locked_out_user", {})
    username = locked_out_user.get("username")
    password = locked_out_user.get("password")

    if not username or not password:
        raise ValueError(
            "Missing locked_out_user.username or locked_out_user.password in data/test_data/test_users.json"
        )

    return {
        "username": username,
        "password": password,
    }


@pytest.fixture(scope="session")
def api_base_url(test_data):
    url = test_data.get("urls", {}).get("api_base_url")
    if not url:
        raise ValueError("Missing urls.api_base_url in data/test_data/test_users.json")
    return url


@pytest.fixture(scope="session")
def checkout_data(test_data):
    user = test_data.get("checkout_user", {})
    first_name = user.get("first_name")
    last_name = user.get("last_name")
    postal_code = user.get("postal_code")

    if not first_name or not last_name or not postal_code:
        raise ValueError(
            "Missing checkout_user.first_name, last_name, or postal_code "
            "in data/test_data/test_users.json"
        )

    return {
        "first_name": first_name,
        "last_name": last_name,
        "postal_code": postal_code,
    }


@pytest.fixture(scope="session")
def booking_api(api_base_url):
    return BookingApiClient(api_base_url, timeout=API_REQUEST_TIMEOUT_SECONDS)


@pytest.fixture(scope="session")
def auth_token(booking_api, test_data):
    admin = test_data.get("api_admin", {})
    username = admin.get("username")
    password = admin.get("password")
    if not username or not password:
        raise ValueError(
            "Missing api_admin.username or api_admin.password in data/test_data/test_users.json"
        )
    return booking_api.create_token(username, password)


@pytest.fixture
def booking_payload_factory():
    def _factory(
        firstname="Test",
        lastname="User",
        totalprice=100,
        depositpaid=False,
        checkin="2024-01-01",
        checkout="2024-01-05",
        additionalneeds=None,
    ):
        payload = {
            "firstname": firstname,
            "lastname": lastname,
            "totalprice": totalprice,
            "depositpaid": depositpaid,
            "bookingdates": {"checkin": checkin, "checkout": checkout},
        }
        if additionalneeds is not None:
            payload["additionalneeds"] = additionalneeds
        return payload

    return _factory


@pytest.fixture
def created_booking(booking_api, auth_token, booking_payload_factory):
    payload = booking_payload_factory(
        firstname="Deterministic",
        lastname="User",
        totalprice=125,
        depositpaid=False,
        checkin="2024-05-01",
        checkout="2024-05-03",
        additionalneeds="Late Checkout",
    )
    response = booking_api.create_booking(payload)
    assert response.status_code == 200, (
        f"Fixture setup failed: status={response.status_code}, body={response.text[:200]}"
    )
    data = response.json()
    yield data
    delete_response = booking_api.delete_booking(data["bookingid"], auth_token)
    if delete_response.status_code not in (201, 404):
        raise RuntimeError(
            f"Fixture teardown failed: delete booking {data['bookingid']} "
            f"returned status={delete_response.status_code}, body={delete_response.text[:200]}"
        )


# UI test fixture to set consistent timeouts across all tests.
@pytest.fixture
def page(page):
    page.set_default_timeout(UI_ACTION_TIMEOUT_MS)
    page.set_default_navigation_timeout(UI_NAVIGATION_TIMEOUT_MS)
    expect.set_options(timeout=UI_EXPECT_TIMEOUT_MS)
    return page


# Pytest hook to capture screenshots and HTML on UI test failure.
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
