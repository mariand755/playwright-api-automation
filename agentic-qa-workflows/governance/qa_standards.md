# QA Standards

## Naming Conventions

### Files
- Test files: `test_<feature>.py` (e.g. `test_login_cart.py`, `test_booking_api.py`)
- Page classes: `<feature>_page.py` (e.g. `login_page.py`, `inventory_page.py`)
- API clients: `<domain>_client.py` (e.g. `api_client.py`)

### Functions
- Test functions: `test_<action>_<expected_outcome>` (e.g. `test_user_can_login`, `test_create_booking_returns_valid_schema`)
- Page methods: `<verb>_<noun>` (e.g. `navigate()`, `add_product_to_cart()`, `verify_login_success()`)
- Fixtures: noun or noun phrase (e.g. `booking_api`, `credentials`, `base_url`)
- Action methods should describe user behavior, such as `login()` or `add_product_to_cart()`.
- Verification methods may use `verify_` or `assert_`, but tests should still make the scenario intent clear.

### Test Case IDs
Tag each test with a unique ID in a comment on the line above the function:

```python
# TC-UI-001
def test_user_can_login(page, base_url, credentials):
```

Pattern: `TC-<AREA>-<NNN>`, where `AREA` is `UI` or `API`.
Use pytest markers such as `smoke`, `negative`, `regression`, or `api_contract` to classify execution scope.

## DRY Rules

- All URLs and credentials come from fixtures — never inline strings in tests.
- Session-level setup (clients, data loading) belongs in `conftest.py` fixtures, not in test functions.
- If setup code appears in two or more tests, extract it to a fixture or page method.
- Test payloads may be inline in the test function unless the same payload is used across 3+ tests; then move to a shared fixture or data file.

## Assertion Standards

- Prefer one logical assertion group per test intent. Multiple assertions are acceptable when they verify the same behavior, such as status code, schema, and returned field values for one API response.
- UI tests: use `expect()` from `playwright.sync_api` for element state; reserve plain `assert` for non-element conditions.
- API tests: assert `status_code` first, then validate schema with `jsonschema.validate()`, then assert specific field values for data round-trip.
- Error message: prefer `assert x == y, "clear failure description"` when the default output is ambiguous.
- Never assert `True` or `is not None` alone — assert the specific value or state you expect.
