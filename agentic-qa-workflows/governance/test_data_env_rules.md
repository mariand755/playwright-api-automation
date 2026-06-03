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
- URLs are organised under an `environments` key. Each sub-key is a named environment block with `base_url` and `api_base_url`:

  ```json
  {
    "environments": {
      "staging": {
        "base_url": "https://www.saucedemo.com",
        "api_base_url": "https://restful-booker.herokuapp.com"
      },
      "prod_read_only": {
        "base_url": "...",
        "api_base_url": "..."
      }
    }
  }
  ```

- `conftest.py` reads the `ENV` environment variable (default: `staging`) via the `env_name` session fixture. Only values listed in `_KNOWN_ENVIRONMENTS` are accepted; an unknown value fails fast with a clear error message listing valid environments.
- Credentials (`valid_user`, `locked_out_user`, `api_admin`, `checkout_user`) remain at the top level of `test_users.json` and are environment-independent for this repo's demo services.
- Invalid `ENV` values raise `ValueError` at collection time, not at test runtime.
- Real prod URLs must not be committed to `test_users.json`. When real prod wiring is activated, the URL must be injected as a GitHub Secret or environment variable and not hard-coded in any committed file.
- Real prod credentials must be stored as GitHub Secrets and injected via Docker `-e` flags at runtime. They must never be added to `test_users.json`.
- Prefer one environment-aware data file for this repo unless the environment structure becomes too large to maintain cleanly.
