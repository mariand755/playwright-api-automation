# Test Data and Environment Rules

## URLs and Credentials

- All base URLs and user credentials are loaded from `data/test_data/test_users.json`.
- No URL strings or credential values may be hardcoded in test files, page classes, or utility code. Public demo credentials may live in `data/test_data/test_users.json`; real secrets must use environment variables or `.private/`.
- Access URLs and credentials through session-scoped fixtures defined in `conftest.py` (`base_url`, `api_base_url`, `credentials`).

## Test Payloads

- API request payloads may be defined inline in test functions when they are unique to that test.
- If the same payload structure is used in 3 or more tests, extract it to a shared pytest fixture or a JSON file in `data/test_data/`.
- Payloads must use deterministic, static values — no `random`, `uuid`, or timestamp-based values unless the test is explicitly validating uniqueness behavior.

## Test Isolation

- Each test must be independently runnable: `pytest test/api/test_booking_api.py::test_create_booking` must pass without running other tests first.
- No test may depend on side effects left by a previous test (e.g. a booking ID created by a different test function).
- If a test creates external state, it should clean up that state through fixture teardown when cleanup is available.
- If cleanup is not available yet, document the limitation in the test or DecisionLog.md and keep created data deterministic and low-risk.

## Sensitive Data

- Credentials, API tokens, and private keys must never be committed to the repository.
- Use `.private/` only for local-only notes; do not commit sensitive data even there unless the folder is confirmed gitignored.
- For CI environments, use environment variables and reference them from `conftest.py` with a clear fallback error if unset.

## Multiple Environments

- The test data file (`test_users.json`) is the single source of truth for environment URLs.
- To support multiple environments (staging, production), introduce an `ENV` environment variable that selects the correct URL block from `test_users.json`.
- Prefer one environment-aware data file for this repo unless the environment structure becomes too large to maintain cleanly.
