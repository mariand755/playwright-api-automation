from playwright.sync_api import Page, expect

from pages.locators import InventoryPageLocators


class InventoryPage:

    def __init__(self, page: Page):
        self.page = page
        self.add_bike_light = page.locator(InventoryPageLocators.ADD_TO_CART_BUTTON).first
        self.cart_icon = page.locator(InventoryPageLocators.CART_ICON)

    def add_product_to_cart(self):
        self.add_bike_light.click()

    def open_cart(self):
        self.cart_icon.click()

    def verify_product_in_cart(self, expected_name: str):
        item_locator = self.page.locator(
            InventoryPageLocators.CART_ITEM, has_text=expected_name
        )
        expect(item_locator).to_be_visible()
