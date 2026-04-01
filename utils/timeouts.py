"""Central timeout values for UI and API tests."""

# UI waits are in milliseconds because Playwright APIs use ms units.
UI_ACTION_TIMEOUT_MS = 10_000
UI_NAVIGATION_TIMEOUT_MS = 10_000
UI_EXPECT_TIMEOUT_MS = 10_000

# API request timeout is in seconds because requests uses seconds.
API_REQUEST_TIMEOUT_SECONDS = 15