import json
import os
import urllib.parse
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

_KNOWN_ENVIRONMENTS = frozenset({"staging", "prod_read_only"})

# BrowserStack CDP always uses playwright.chromium.connect(); browser is
# specified in the capabilities JSON and routed by BrowserStack's proxy layer.
_BS_BROWSER_MAP: dict[str, str] = {
    "chromium": "chrome",
    "firefox": "firefox",
    "webkit": "playwright-webkit",
}


@pytest.fixture(scope="session")
def test_data():
    data_file = Path(__file__).parent / "data" / "test_data" / "test_users.json"
    with open(data_file, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def env_name() -> str:
    env = os.environ.get("ENV", "staging")
    if env not in _KNOWN_ENVIRONMENTS:
        raise ValueError(
            f"Unknown ENV={env!r}. Valid environments: {sorted(_KNOWN_ENVIRONMENTS)}"
        )
    return env


@pytest.fixture(scope="session")
def base_url(test_data, env_name):
    url = test_data.get("environments", {}).get(env_name, {}).get("base_url")
    if not url:
        raise ValueError(
            f"Missing environments.{env_name}.base_url in data/test_data/test_users.json"
        )
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
def api_base_url(test_data, env_name):
    url = test_data.get("environments", {}).get(env_name, {}).get("api_base_url")
    if not url:
        raise ValueError(
            f"Missing environments.{env_name}.api_base_url in data/test_data/test_users.json"
        )
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


@pytest.fixture(scope="session")
def browser(playwright, browser_name, browser_type_launch_args):
    cloud_provider = os.environ.get("CLOUD_GRID_PROVIDER", "none").strip().lower()

    if cloud_provider == "sauce":
        username = os.environ.get("SAUCE_USERNAME", "")
        access_key = os.environ.get("SAUCE_ACCESS_KEY", "")
        region = os.environ.get("SAUCE_REGION", "us-west-1")
        # Credentials embedded in endpoint URL — never printed or logged
        endpoint = (
            f"wss://{username}:{access_key}@ondemand.{region}.saucelabs.com"
            f":443/playwright/{browser_name}"
        )
        timeout_ms = int(os.environ.get("SAUCE_CONNECT_TIMEOUT_MS", "60000"))
        try:
            b = getattr(playwright, browser_name).connect(endpoint, timeout=timeout_ms)
        except Exception as exc:
            raise RuntimeError(
                f"Sauce Labs remote session could not be provisioned.\n"
                f"Provider: sauce  Region: {region}  Browser: {browser_name}\n"
                f"Error type: {type(exc).__name__}\n"
                f"Likely causes: inactive/expired Sauce account, quota or concurrency limit reached,\n"
                f"  region mismatch, provider outage, or session provisioning timeout.\n"
                f"Secrets and WebSocket endpoint were redacted from this message."
            ) from None
        yield b
        b.close()
    elif cloud_provider == "browserstack":
        bs_username = os.environ.get("BROWSERSTACK_USERNAME", "")
        bs_access_key = os.environ.get("BROWSERSTACK_ACCESS_KEY", "")
        timeout_ms = int(os.environ.get("BROWSERSTACK_CONNECT_TIMEOUT_MS", "60000"))
        bs_browser = _BS_BROWSER_MAP.get(browser_name, browser_name)
        # Credentials embedded in caps JSON inside endpoint URL — never printed or logged
        caps = json.dumps(
            {
                "browser": bs_browser,
                "browser_version": "latest",
                "os": "osx",
                "os_version": "ventura",
                "name": "playwright-api-automation smoke",
                "build": "playwright-api-automation",
                "browserstack.username": bs_username,
                "browserstack.accessKey": bs_access_key,
            }
        )
        endpoint = (
            f"wss://cdp.browserstack.com/playwright?caps={urllib.parse.quote(caps)}"
        )
        try:
            b = playwright.chromium.connect(endpoint, timeout=timeout_ms)
        except Exception as exc:
            raise RuntimeError(
                f"BrowserStack remote session could not be provisioned.\n"
                f"Provider: browserstack  Browser: {bs_browser}\n"
                f"Error type: {type(exc).__name__}\n"
                f"Likely causes: invalid credentials, Automate plan limit reached,\n"
                f"  unsupported browser/OS combination, or provider outage.\n"
                f"Secrets and WebSocket endpoint were redacted from this message."
            ) from None
        yield b
        b.close()
    else:
        b = getattr(playwright, browser_name).launch(**browser_type_launch_args)
        yield b
        b.close()


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

            safe_name = (
                item.nodeid.replace("/", "_")
                .replace("\\", "_")
                .replace("::", "__")
                .replace("[", "_")
                .replace("]", "_")
            )
            screenshot_path = artifacts_dir / f"{safe_name}.png"
            html_path = artifacts_dir / f"{safe_name}.html"

            page.screenshot(path=str(screenshot_path), full_page=True)
            html_path.write_text(page.content(), encoding="utf-8")


def pytest_collection_modifyitems(items):
    for item in items:
        marker = item.get_closest_marker("tc_id")
        if marker and marker.args:
            item.user_properties.append(("tc_id", str(marker.args[0])))
