import pytest
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage


# TC-UI-004
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.tc_id("TC-UI-004")
def test_user_can_complete_checkout(page, base_url, credentials, checkout_data):
    login = LoginPage(page)
    inventory = InventoryPage(page)
    cart = CartPage(page)
    checkout = CheckoutPage(page)

    login.navigate(base_url)
    login.login(credentials["username"], credentials["password"])
    login.verify_login_success()

    inventory.add_product_to_cart()
    inventory.open_cart()
    cart.verify_product_in_cart("Sauce Labs Backpack")
    cart.proceed_to_checkout()

    checkout.fill_information(
        checkout_data["first_name"],
        checkout_data["last_name"],
        checkout_data["postal_code"],
    )
    checkout.continue_checkout()
    checkout.finish_checkout()
    checkout.verify_order_complete()
