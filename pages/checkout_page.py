from playwright.sync_api import Page, expect

from pages.locators import CheckoutPageLocators


class CheckoutPage:
    def __init__(self, page: Page):
        self.page = page
        self.first_name = page.locator(CheckoutPageLocators.FIRST_NAME)
        self.last_name = page.locator(CheckoutPageLocators.LAST_NAME)
        self.postal_code = page.locator(CheckoutPageLocators.POSTAL_CODE)
        self.continue_button = page.locator(CheckoutPageLocators.CONTINUE_BUTTON)
        self.finish_button = page.locator(CheckoutPageLocators.FINISH_BUTTON)
        self.complete_header = page.locator(CheckoutPageLocators.COMPLETE_HEADER)

    def fill_information(self, first_name: str, last_name: str, postal_code: str):
        self.first_name.fill(first_name)
        self.last_name.fill(last_name)
        self.postal_code.fill(postal_code)

    def continue_checkout(self):
        self.continue_button.click()

    def finish_checkout(self):
        self.finish_button.click()

    def verify_order_complete(self):
        expect(self.complete_header).to_contain_text("Thank you for your order!")
