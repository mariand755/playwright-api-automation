# Fix 3 QA Summary — Test Case ID Comments
**Date:** 2026-05-19
**Fix:** Comment-only addition of TC-ID tags above all 6 existing tests

---

## What Was Changed

A `# TC-<AREA>-<NNN>` comment was added immediately above the pytest marker decorators of every test function. No test logic, assertions, fixtures, or markers were modified.

| File | Function | TC-ID added |
|---|---|---|
| `test/ui/test_login_cart.py` | `test_user_can_login` | `# TC-UI-001` |
| `test/ui/test_login_cart.py` | `test_user_can_login_and_add_to_cart` | `# TC-UI-002` |
| `test/api/test_booking_api.py` | `test_get_all_bookings` | `# TC-API-001` |
| `test/api/test_booking_api.py` | `test_get_booking_by_id` | `# TC-API-002` |
| `test/api/test_booking_api.py` | `test_invalid_booking` | `# TC-API-003` |
| `test/api/test_booking_api.py` | `test_create_booking` | `# TC-API-004` |

---

## TC-ID Mapping Applied

| TC-ID | Test function | Area | Scope marker |
|---|---|---|---|
| TC-UI-001 | `test_user_can_login` | UI | smoke |
| TC-UI-002 | `test_user_can_login_and_add_to_cart` | UI | — |
| TC-API-001 | `test_get_all_bookings` | API | — |
| TC-API-002 | `test_get_booking_by_id` | API | — |
| TC-API-003 | `test_invalid_booking` | API | negative |
| TC-API-004 | `test_create_booking` | API | — |

---

## Why It Was Changed

`qa_standards.md` requires every test function to carry a unique `# TC-<AREA>-<NNN>` comment tag on the line immediately above the function. Zero tests carried one before this fix. These comments provide human-readable traceability only. They do not yet appear in pytest reports or support targeted execution by TC-ID; that will require future pytest metadata or reporting support.

Comment placement follows the project rule: TC-ID appears above the first decorator, not between decorators and the function definition.

---

## Test Commands Run

```bash
# Step 1 — build Docker image
docker build -t playwright-api-automation .

# Step 2 — collection check
docker run --rm playwright-api-automation pytest --collect-only -q

# Step 3 — full suite
docker run --rm playwright-api-automation
```

---

## Pass/Fail Result

| Command | Result |
|---|---|
| `pytest --collect-only -q` | 6 tests collected, 0 warnings |
| `docker run --rm playwright-api-automation` | 6/6 passed in 2.89s |

---

## Risks or Open Items

- No risk from Fix 3 — comment-only changes cannot affect test collection, execution, or outcomes.
- Local environment note: Docker remains the source of truth for verification. If local runs are needed, rebuild the virtual environment with `python -m venv venv`, reinstall dependencies with `pip install -r requirements.txt`, and run `playwright install`.
- TC-UI-002 (`test_user_can_login_and_add_to_cart`) carries no scope marker. It is a positive E2E test that could reasonably carry `@pytest.mark.regression` in a future session once regression coverage is intentionally activated.

---

## Next Recommended Step

Fix 4 — Add descriptive assertion messages to all status-code asserts in `test/api/test_booking_api.py`, and add a data round-trip field assertion to `test_get_booking_by_id`. Verify with `pytest test/api -v` inside Docker.
