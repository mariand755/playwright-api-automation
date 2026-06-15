import pytest
from pages.login_page import LoginPage


# Smoke test: verifies login functionality in isolation.
# TC-UI-001
@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.read_only
@pytest.mark.tc_id("TC-UI-001")
def test_user_can_login(page, base_url, credentials):
    login = LoginPage(page)

    login.navigate(base_url)
    login.login(credentials["username"], credentials["password"])
    login.verify_login_success()


# Negative test: locked-out user is blocked with a visible error message.
# TC-UI-003
@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.tc_id("TC-UI-003")
def test_locked_out_user_sees_error(page, base_url, locked_out_credentials):
    login = LoginPage(page)

    login.navigate(base_url)
    login.login(locked_out_credentials["username"], locked_out_credentials["password"])
    login.verify_login_error_message("Sorry, this user has been locked out.")
