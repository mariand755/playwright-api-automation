# Fix 2 QA Summary — Marker Alignment
**Date:** 2026-05-18
**Fix:** Decorator-only marker changes on two existing tests

---

## What Was Changed

| File | Change |
|---|---|
| `test/ui/test_login_cart.py` | Reordered `@pytest.mark.smoke` and `@pytest.mark.ui` — `@pytest.mark.ui` now appears above `@pytest.mark.smoke` on `test_user_can_login` |
| `test/api/test_booking_api.py` | Added `@pytest.mark.negative` below `@pytest.mark.api` on `test_invalid_booking` |

No test logic, assertions, or fixtures were touched.

---

## Why It Was Changed

**Marker order on `test_user_can_login`:** Governance policy requires the area marker (`ui`) to appear above the scope marker (`smoke`). The previous order reversed this, which did not affect pytest behavior, but it did violate the project's readability and suite-taxonomy convention.

**`@pytest.mark.negative` on `test_invalid_booking`:** The test deliberately exercises an invalid booking ID to verify a 404/400 response — that is a negative/error-path test by definition. Without the marker it cannot be selected or excluded as a negative scenario when running targeted subsets, and it misrepresents the test's intent in collection output.

---

## Test Command Run

```bash
docker build -t playwright-api-automation .
docker run --rm playwright-api-automation
```

---

## Pass/Fail Result

| Suite | Result |
|---|---|
| `test/api/test_booking_api.py` (4 tests) | 4 PASSED |
| `test/ui/test_login_cart.py` (2 tests) | 2 ERRORS (pre-existing, unrelated to Fix 2) |

---

## Pre-Existing UI Errors (Not Caused by Fix 2)

Both UI tests fail at browser setup with:

> Playwright was just updated to 1.60.0 — please update docker image (currently v1.58.0-noble, required v1.60.0-noble)

The installed `playwright` Python package (1.60.0) is newer than the browser binaries baked into `mcr.microsoft.com/playwright/python:v1.58.0-noble`. This infrastructure drift existed before Fix 2. Decorator changes had no effect on this failure.

---

## Risks and Next Steps

- No risk from Fix 2 — decorator-only changes cannot affect test logic or outcomes.
- Pre-existing risk: UI tests are broken in Docker due to the image/package version mismatch. The Dockerfile base image tag and `requirements.txt` Playwright pin should both be updated to v1.60.0 before Fix 3 begins, so the Phase 3 definition of done ("all tests pass") can be verified cleanly.
- Next in sequence: Fix 3 — add TC-ID comments above all 6 tests.
