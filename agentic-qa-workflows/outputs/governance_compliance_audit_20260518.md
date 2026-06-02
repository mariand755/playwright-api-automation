# Governance Compliance Audit — playwright-api-automation
**Date:** 2026-05-18
**Audited against:** `agentic-qa-workflows/governance/`

---

## Areas That Already Comply ✅

**1. File and function naming (`qa_standards.md`)**
All test files, page classes, and API client follow defined patterns. Page method names (`navigate()`, `login()`, `add_product_to_cart()`, `verify_login_success()`) match the `<verb>_<noun>` convention. Fixtures use noun-phrases (`booking_api`, `credentials`, `base_url`).

**2. POM and API client boundaries (`page_object_api_rules.md`)**
All CSS selectors are in `pages/locators.py` — no raw selector strings in test files. `BookingApiClient` returns raw `requests.Response` objects; tests own all payload construction and response assertion. No HTTP calls appear in test files. No `time.sleep()` found.

**3. Test data and environment usage (`test_data_env_rules.md`)**
All URLs and credentials are loaded from `data/test_data/test_users.json` via session-scoped fixtures. No hardcoded URL strings in tests or page classes. Public SauceDemo credentials are acceptable in the data file per the governance rule. Payloads are static and deterministic.

**4. UI failure evidence (`failure_evidence.md`)**
The `pytest_runtest_makereport` hook in `conftest.py:72-87` produces `artifacts/failures/<test_name>.png` and `.html` on every UI failure. Directory is gitignored. Artifact naming matches the governance spec exactly.

**5. DRY and fixture centralization (`qa_standards.md`)**
Session-scoped fixtures for all shared state live in `conftest.py`. No duplicated setup across test functions.

---

## Top 3 Governance Gaps

---

### Gap 1 — No test case IDs on any test (`qa_standards.md`)

`qa_standards.md` requires a `# TC-<AREA>-<NNN>` comment above every test function. Zero tests carry one.

```python
# missing — governance requires this above every test
def test_user_can_login(page, base_url, credentials):
```

**Smallest safe fix:** Add a TC comment line above each of the 6 test functions. No functional change.

```python
# TC-UI-001
@pytest.mark.ui
@pytest.mark.smoke
def test_user_can_login(page, base_url, credentials):
```

IDs to assign:

| Test | ID |
|---|---|
| `test_user_can_login` | `TC-UI-001` |
| `test_user_can_login_and_add_to_cart` | `TC-UI-002` |
| `test_get_all_bookings` | `TC-API-001` |
| `test_get_booking_by_id` | `TC-API-002` |
| `test_invalid_booking` | `TC-API-003` |
| `test_create_booking` | `TC-API-004` |

**Verify with:** `pytest -v`

---

### Gap 2 — Marker violations: wrong order, missing `negative`, undeclared markers (`suite_taxonomy.md`)

Three issues:

**a) `negative` and `regression` not in `pytest.ini`.**
`suite_taxonomy.md` requires these to be declared before use. Currently only `ui`, `api`, and `smoke` are declared. Undeclared-marker warnings must be treated as CI errors.

**b) Marker order wrong on `test_user_can_login`.**
Governance requires area marker first, then scope markers. Current order is reversed:

```python
# current — violates governance
@pytest.mark.smoke
@pytest.mark.ui

# correct
@pytest.mark.ui
@pytest.mark.smoke
```

**c) `test_invalid_booking` missing `@pytest.mark.negative`.**
It is an error-path test and must carry both `@pytest.mark.api` and `@pytest.mark.negative`.

**Smallest safe fix:**

1. Add to `pytest.ini` under `markers`:
   ```ini
   negative: marks tests for negative/error-path scenarios
   regression: marks tests for full-suite regression coverage
   ```
2. Reorder decorators on `test_user_can_login` (area first).
3. Add `@pytest.mark.negative` to `test_invalid_booking`.

**Verify with:** `pytest --collect-only -q` (no marker warnings), then `pytest -v`

---

### Gap 3 — API assertions lack descriptive failure messages; `test_get_booking_by_id` missing data round-trip assertion (`failure_evidence.md` + `qa_standards.md`)

API tests currently use bare status-code assertions without descriptive failure messages.

```python
# current — no context on failure
assert response.status_code == 200

# governance-compliant
assert response.status_code == 200, (
    f"GET {response.url} failed: "
    f"status={response.status_code}, body={response.text[:200]}"
)
```

Additionally, `test_get_booking_by_id` validates schema shape but never checks that retrieved data matches the submitted payload. `test_create_booking` correctly asserts `response_json["booking"]["firstname"] == payload["firstname"]`. The same round-trip check is missing from `test_get_booking_by_id`.

**Smallest safe fix:** Add descriptive messages to the 4 status code asserts in `test/api/test_booking_api.py`. Add one field assertion to `test_get_booking_by_id` after `validate()`.

**Verify with:** `pytest test/api -v`

---

## Suggested Order of Fixes

| Order | Fix | Risk | Command |
|---|---|---|---|
| 1 | Add `negative` and `regression` to `pytest.ini` | Zero — no test changes | `pytest --collect-only -q` |
| 2 | Fix marker order on `test_user_can_login`; add `@pytest.mark.negative` to `test_invalid_booking` | Zero — decorator-only | `pytest -v` |
| 3 | Add TC-ID comments above all 6 tests | Zero — comment-only | `pytest -v` |
| 4 | Add descriptive assertion messages + round-trip assert to `test_get_booking_by_id` | Low — assertion tightening | `pytest test/api -v` |
| 5 | Add negative UI test (`locked_out_user`) | Medium — new test + new test data | `pytest test/ui -v` |

Fix 1 is the prerequisite for Fix 2 — the `negative` marker cannot be applied until it is declared in `pytest.ini`.
