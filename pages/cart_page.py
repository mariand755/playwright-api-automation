from playwright.sync_api import Page, expect

from pages.locators import CartPageLocators


class CartPage:

    def __init__(self, page: Page):
        self.page = page
        self.checkout_button = page.locator(CartPageLocators.CHECKOUT_BUTTON)

    def verify_product_in_cart(self, expected_name: str):
        item_locator = self.page.locator(CartPageLocators.CART_ITEM, has_text=expected_name)
        expect(item_locator).to_be_visible()

    def proceed_to_checkout(self):
        self.checkout_button.click()
