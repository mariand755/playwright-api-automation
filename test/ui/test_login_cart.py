import pytest
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage


#Smoke test: verifies login functionality in isolation.
# TC-UI-001
@pytest.mark.ui
@pytest.mark.smoke
def test_user_can_login(page, base_url, credentials):
    login = LoginPage(page)

    login.navigate(base_url)
    login.login(credentials["username"], credentials["password"])
    login.verify_login_success()


# Negative test: locked-out user is blocked with a visible error message.
# TC-UI-003
@pytest.mark.ui
@pytest.mark.negative
def test_locked_out_user_sees_error(page, base_url, locked_out_credentials):
    login = LoginPage(page)

    login.navigate(base_url)
    login.login(locked_out_credentials["username"], locked_out_credentials["password"])
    login.verify_login_error_message("Sorry, this user has been locked out.")


# E2E happy path: login + add product to cart + verify cart contents.
# TC-UI-002
@pytest.mark.ui
def test_user_can_login_and_add_to_cart(page, base_url, credentials):
    login = LoginPage(page)
    inventory = InventoryPage(page)

    login.navigate(base_url)
    login.login(credentials["username"], credentials["password"])
    login.verify_login_success()

    inventory.add_product_to_cart()
    inventory.open_cart()
    inventory.verify_product_in_cart()
