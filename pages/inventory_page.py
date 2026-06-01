from playwright.sync_api import Page

from pages.locators import InventoryPageLocators


class InventoryPage:

    def __init__(self, page: Page):
        self.page = page
        self.add_to_cart_button = page.locator(InventoryPageLocators.ADD_TO_CART_BUTTON).first
        self.cart_icon = page.locator(InventoryPageLocators.CART_ICON)

    def add_product_to_cart(self):
        self.add_to_cart_button.click()

    def open_cart(self):
        self.cart_icon.click()
