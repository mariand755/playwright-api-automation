# QA Standards

## Naming Conventions

### Files

- Test files: `test_[feature].py` (e.g. `test_[domain]_api.py`, `test_[feature]_ui.py`)
- Page classes: `[feature]_page.py`
- API clients: `[domain]_client.py`

### Functions

- Test functions: `test_[action]_[expected_outcome]` (e.g. `test_[feature]_returns_valid_response`, `test_[action]_succeeds_with_valid_input`)
- Page methods: `[verb]_[noun]` (e.g. `navigate()`, `submit_form()`, `verify_[state]()`)
- Fixtures: noun or noun phrase (e.g. `[domain]_api`, `base_url`, `authenticated_session`)
- Action methods should describe user behavior.
- Verification methods may use `verify_` or `assert_`, but tests should still make the scenario intent clear.

### Test Case IDs

Tag each test with a unique ID comment above the decorator stack and with a `@pytest.mark.tc_id(...)` marker as the last decorator.

```python
# TC-[AREA]-[NNN]
@pytest.mark.[your-area]
@pytest.mark.smoke
@pytest.mark.tc_id("TC-[AREA]-[NNN]")
def test_[action]_[expected_outcome](...):
    ...
```

Pattern: `TC-[AREA]-[NNN]`, where `AREA` is a short uppercase label for your test layer (e.g. `API`, `UI`, `SCRIPTS`).

For marker declaration and the full `tc_id` decorator pattern, see [`suite_taxonomy_template.md`](suite_taxonomy_template.md).

---

## DRY Rules

- All URLs and credentials come from fixtures — never inline strings in tests.
- Session-level setup (clients, data loading) belongs in `conftest.py` fixtures, not in test functions.
- If setup code appears in two or more tests, extract it to a fixture or page method.
- Test payloads may be inline in the test function unless the same payload is used across 3+ tests; then move to a shared fixture or data file.

---

## Assertion Standards

- Prefer one logical assertion group per test intent. Multiple assertions are acceptable when they verify the same behavior — for example, status code, schema, and returned field values for one API response.
- UI tests: use `expect()` from your UI framework for element state; reserve plain `assert` for non-element conditions.
- API tests: assert `status_code` first, then validate schema with a schema validation library, then assert specific field values for data round-trip.
- Error message: prefer `assert x == y, "clear failure description"` when the default output is ambiguous.
- Never assert `True` or `is not None` alone — assert the specific value or state you expect.

---

## Coverage Floor

At a minimum, every public API endpoint and every UI flow must have:

- At least one positive test (happy path)
- At least one negative test (error path or invalid input)

Endpoints or flows with only a positive test are considered incomplete and must be flagged in the PR description.

---

## Skips and Expected Failures

- `@pytest.mark.skip`: allowed only for tests blocked by an upstream bug or dependency not yet available. Must include `reason="<issue link>"`.
- `@pytest.mark.xfail`: allowed only for known, documented failures being tracked. Must include `reason="<issue link>"` and `strict=True` where appropriate.
- Skips and xfails must be removed when the blocking condition is resolved.
