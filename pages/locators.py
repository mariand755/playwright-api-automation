class LoginPageLocators:
    USERNAME = "#user-name"
    PASSWORD = "#password"
    LOGIN_BUTTON = "#login-button"
    PRODUCTS_TITLE = ".title"
    ERROR_MESSAGE = "[data-test='error']"


class InventoryPageLocators:
    ADD_TO_CART_BUTTON = 'text="Add to cart"'
    CART_ICON = ".shopping_cart_link"
    CART_BADGE = ".shopping_cart_badge"


class CartPageLocators:
    CART_ITEM = ".inventory_item_name"
    CHECKOUT_BUTTON = "[data-test='checkout']"
    REMOVE_FROM_CART_BUTTON = "[data-test^='remove-']"


class CheckoutPageLocators:
    FIRST_NAME = "[data-test='firstName']"
    LAST_NAME = "[data-test='lastName']"
    POSTAL_CODE = "[data-test='postalCode']"
    CONTINUE_BUTTON = "[data-test='continue']"
    FINISH_BUTTON = "[data-test='finish']"
    COMPLETE_HEADER = "[data-test='complete-header']"
    ERROR_MESSAGE = "[data-test='error']"
