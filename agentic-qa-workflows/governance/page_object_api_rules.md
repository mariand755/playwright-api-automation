# Page Object and API Client Rules

## Page Object Model (POM)

### Ownership
- Page classes own navigation, user actions, and reusable page-level verifications, such as `navigate()`, `login()`, `add_product_to_cart()`, and `verify_login_success()`.
- Test functions own the scenario flow — which pages to use, in what order, and what business behavior the test is proving.

### Locators
- All CSS selectors and locator strings live in `pages/locators.py`.
- No raw selector strings may appear in test files or page method bodies. Page objects should reference locator constants from `pages/locators.py`.
- Group locators by page in named classes (e.g. `LoginPageLocators`, `InventoryPageLocators`).

### Method design
- One method per user action. Do not chain side effects (e.g. a `login()` method must not also navigate to the cart).
- Methods that verify state should use `expect()` and raise an assertion error on failure — tests should not re-assert what a page method already checks.
- No `time.sleep()` — use Playwright's built-in waiting via `expect()` or `page.wait_for_*()`.

### Extending POM
- Add a new page class in `pages/` for each new page or major UI section.
- Add locators to `pages/locators.py` before writing any page method that uses them.
- Import new page classes in the test file, not in `conftest.py` (page classes are not fixtures).

## API Client (`BookingApiClient`)

### Ownership
- `BookingApiClient` owns: HTTP method calls, base URL composition, and timeout config.
- Test functions own: request payloads, response assertions, and schema validation.

### Method design
- One method per API operation (e.g. `get_all_bookings()`, `create_booking(payload)`).
- Methods return the raw `requests.Response` object — do not parse or assert inside the client.
- No hardcoded URLs in methods — compose paths from the `base_url` passed at construction.

### Extending the API client
- Add a new method to `BookingApiClient` for each new endpoint to test.
- If a new API domain is introduced, create a new client class in `utils/` following the same pattern.
- Auth tokens, if needed, are passed as constructor arguments or set via a dedicated `authenticate()` method — not embedded in individual request methods.
