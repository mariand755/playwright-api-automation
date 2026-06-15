import pytest
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from pages.cart_page import CartPage


# E2E happy path: login + add product to cart + verify cart contents.
# TC-UI-002
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.tc_id("TC-UI-002")
def test_user_can_login_and_add_to_cart(page, base_url, credentials):
    login = LoginPage(page)
    inventory = InventoryPage(page)
    cart = CartPage(page)

    login.navigate(base_url)
    login.login(credentials["username"], credentials["password"])
    login.verify_login_success()

    inventory.add_product_to_cart()
    inventory.open_cart()
    cart.verify_product_in_cart("Sauce Labs Backpack")


# TC-UI-005
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.tc_id("TC-UI-005")
def test_user_can_remove_from_cart(page, base_url, credentials):
    login = LoginPage(page)
    inventory = InventoryPage(page)
    cart = CartPage(page)

    login.navigate(base_url)
    login.login(credentials["username"], credentials["password"])
    login.verify_login_success()

    inventory.add_product_to_cart()
    inventory.open_cart()
    cart.remove_from_cart()
    cart.verify_cart_is_empty()


# TC-UI-006
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.tc_id("TC-UI-006")
def test_cart_badge_reflects_item_count(page, base_url, credentials):
    login = LoginPage(page)
    inventory = InventoryPage(page)

    login.navigate(base_url)
    login.login(credentials["username"], credentials["password"])
    login.verify_login_success()

    inventory.add_product_to_cart()
    inventory.verify_cart_badge_count(1)
    inventory.add_product_to_cart()
    inventory.verify_cart_badge_count(2)


# TC-UI-009
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.tc_id("TC-UI-009")
def test_multiple_items_cart_badge_count(page, base_url, credentials):
    login = LoginPage(page)
    inventory = InventoryPage(page)

    login.navigate(base_url)
    login.login(credentials["username"], credentials["password"])
    login.verify_login_success()

    inventory.add_product_to_cart_by_index(0)
    inventory.add_product_to_cart_by_index(1)
    inventory.verify_cart_badge_count(2)
