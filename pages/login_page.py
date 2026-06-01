from playwright.sync_api import Page, expect

from pages.locators import LoginPageLocators


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username = page.locator(LoginPageLocators.USERNAME)
        self.password = page.locator(LoginPageLocators.PASSWORD)
        self.login_button = page.locator(LoginPageLocators.LOGIN_BUTTON)
        self.products_title = page.locator(LoginPageLocators.PRODUCTS_TITLE)
        self.error_message = page.locator(LoginPageLocators.ERROR_MESSAGE)

    def navigate(self, base_url):
        self.page.goto(base_url)

    def login(self, username, password):
        self.username.fill(username)
        self.password.fill(password)
        self.login_button.click()

    def verify_login_success(self):
        expect(self.products_title).to_have_text("Products")

    def verify_login_error_message(self, expected_message: str):
        expect(self.error_message).to_be_visible()
        expect(self.error_message).to_contain_text(expected_message)
