# Decision Log

## Scope Interpretation and Timeboxing
- Prioritized shipping a reliable UI smoke baseline first, then implemented a focused API suite.
- Kept UI scope intentionally narrow to a happy path: login and one primary action (add item to cart).
- Kept API scope intentionally small and high-value: list bookings, get by id, invalid id, and create booking.

## Framework Strategy
- Fast feedback through a small, deterministic smoke test suite.
- Clear separation of concerns between tests, page objects, utilities, and data.
- Reproducible execution both locally and in Docker.
- Readability and maintainability over large but brittle test coverage.

This reflects a production approach where smoke tests run frequently while broader regression coverage evolves over time.

## Engineering Thinking
- Optimized for signal-to-noise: selected a small set of high-value tests that verify core behavior quickly.
- Designed for maintainability over short-term speed by separating concerns (page objects, locators, API client, fixtures, schemas).
- Minimized flaky behavior by using explicit waits and consistent timeout policy rather than sleeps.
- Kept tests deterministic and readable so failures are diagnosable in local and Docker runs.

## Tradeoffs
- Chose depth over breadth: implemented stable smoke-level coverage instead of broad regression coverage.
- Chose static JSON test data for simplicity and reproducibility, while documenting CI-based extensibility as a next step.
- Kept API scope to read/create plus key negatives; deferred update/delete and auth flows to preserve timebox.
- Added failure artifacts (screenshot + HTML) for diagnostics rather than building full reporting integrations in this iteration.

## Test Selection and Coverage Rationale
- Selected a smoke scenario that validates critical user value quickly:
  - Authentication works
  - Inventory interaction works
  - Cart state is validated
- Added a small API suite to validate core service behavior and schema contracts without expanding into full regression coverage.
- Avoided broad regression-style coverage in this submission to keep execution fast and deterministic.

## Stability and Data Strategies
- Used resilient selectors in centralized locator classes to reduce maintenance cost.
- Used explicit Playwright assertions (`expect`) and default page/navigation timeouts.
- Avoided hard sleeps in favor of auto-wait behavior and explicit checks.
- Moved credentials to centralized JSON test data (`data/test_data/test_users.json`) consumed by fixtures.
- Added centralized timeout configuration in `utils/timeouts.py` with separate UI and API timeout constants.
- Added API schema validation with dedicated contracts for different response shapes (`booking_schema.json` and `booking_details_schema.json`).
- Added automatic diagnostics on failure:
  - Full-page screenshot
  - HTML dump

## Architecture Decisions
- Adopted Page Object Model with separate locator classes:
  - `pages/login_page.py`
  - `pages/inventory_page.py`
  - `pages/locators.py`
- Added an API client layer in `utils/api_client.py` to keep endpoint calls out of test bodies.
- Centralized common test setup in `conftest.py`.
- Isolated UI tests under `test/ui/` and API tests under `test/api/`.
- Configured pytest discovery in `pytest.ini` to align with the repository test directory.
- Updated Docker image default command to run `pytest -v` for container-first execution.
- Captured separate local and Docker run outputs for full, UI-only, and API-only evidence.

## Next Steps If Given More Time
- Add richer reporting (JUnit XML / HTML report, eg Allure).
- Expand API suite with update/delete and stronger negative-path coverage.
- Add test data factory/fixtures for multi-user and role-based scenarios.
- Add retries only for known flaky external dependencies, with metrics.
- Add CI workflow with parallel split for UI/API markers.
- Expand UI coverage with checkout end-to-end completion and edge cases.
- Integrate CI notifications (e.g., Slack alerts) to surface failures quickly.
- Configure cloud test execution (e.g., Sauce Labs or Playwright cloud grids) for parallel browser/device coverage.
