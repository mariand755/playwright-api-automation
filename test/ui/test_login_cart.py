
import pytest
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage


#Smoke test: verifies login functionality in isolation.
@pytest.mark.smoke
@pytest.mark.ui
def test_user_can_login(page, base_url, credentials):
    login = LoginPage(page)

    login.navigate(base_url)
    login.login(credentials["username"], credentials["password"])
    login.verify_login_success()


# E2E happy path: login + add product to cart + verify cart contents.
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
