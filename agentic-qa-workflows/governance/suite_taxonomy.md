# Suite Taxonomy

## Marker Types

Markers fall into two categories:

- **Area markers** (`ui`, `api`): identify which layer the test exercises. Apply these first.
- **Execution-scope markers** (`smoke`, `negative`, `regression`, `api_contract`): identify when and why the test runs. Apply these after the area marker.

Each test should carry its area marker and, where applicable, one or more execution-scope markers:

```python
@pytest.mark.ui
@pytest.mark.smoke
def test_user_can_login(...):
    ...

@pytest.mark.api
@pytest.mark.negative
def test_invalid_booking(...):
    ...
```

## Currently Active Markers (declared in pytest.ini)

### `ui`

Marks tests that drive the browser via Playwright. All tests in `test/ui/` must carry this marker.

### `api`

Marks tests that call REST endpoints via `BookingApiClient`. All tests in `test/api/` must carry this marker.

### `smoke`

Fast sanity check that the critical happy path works.

- Scope: one positive test per major feature area.
- Run trigger: every commit, every PR open, before any other suite.
- Pass requirement for: unblocking further test execution.
- Target runtime: under 60 seconds.
- Current tests: `test_user_can_login`, `test_get_all_bookings`, `test_create_booking`, `test_delete_booking`

### `negative`

Verifies the system handles invalid input, missing data, and error conditions correctly.

- Scope: one negative test per user-facing error state (locked account, invalid ID, missing required field).
- Run trigger: every commit, alongside the relevant area suite.
- Pass requirement for: PR merge.

### `regression`

Full coverage sweep run before a release to catch cross-feature regressions.

- Scope: all suites combined plus feature-area edge cases.
- Run trigger: manually before releases; automatically in Docker on the main branch.
- Pass requirement for: release sign-off.

### `api_contract`

Marks tests that validate API response schema against a declared JSON schema contract using `jsonschema.validate()`.

- Scope: any test that calls `jsonschema.validate()` against a schema file from `data/schemas/`. Must be declared in `pytest.ini` before use.
- Run trigger: every commit alongside the API area suite; targeted execution via `pytest -m api_contract`.
- Current tests: `test_get_booking_by_id` (TC-API-002), `test_create_booking` (TC-API-004)

## Traceability Markers

Traceability markers are a third category, distinct from area markers and execution-scope markers. They are not used for test selection or targeted execution — their purpose is to carry structured metadata that can be consumed by downstream tooling (JUnit XML parsers, test-management systems, CI dashboards).

### `tc_id`

Marks a test with its unique test case ID for machine-readable traceability.

- **Purpose:** writes `<property name="tc_id" value="TC-..."/>` into the JUnit XML `<properties>` block for each `<testcase>` element, via the `pytest_collection_modifyitems` hook in `conftest.py`.
- **Scope:** every test that has a TC-ID. Apply to all tests as the last decorator in the stack.
- **Run trigger:** not used for test selection (`pytest -m tc_id` is not a supported command). Applied at collection time only.
- **Behavior on absence:** silent. A test without a `tc_id` marker produces no property in JUnit XML. Collection does not fail or warn.
- **Future use:** collection enforcement (fail/warn if missing), CI summary display, test-management integration (Xray, TestRail, Zephyr).

## Future / Target Markers

No target-only markers are currently defined. All active markers are declared in `pytest.ini`.

Any future marker must be:

1. Defined here with purpose, scope, and run trigger before any test uses it.
2. Added to `pytest.ini` under `markers` before any test is decorated with it.
3. Moved from this section to "Currently Active Markers" once at least one test carries it.

## Adding a Test to a Suite

| Condition | Area marker | Scope marker |
| --- | --- | --- |
| Browser-driven test | `ui` | — |
| REST API test | `api` | — |
| First passing test for a new feature | `ui` or `api` | `smoke` |
| Error path or invalid input | `ui` or `api` | `negative` |
| Protecting a shipped feature from regression | `ui` or `api` | `regression` |
| API response structure must match schema | `api` | `api_contract` |

## Adding New Markers

All markers must be declared in `pytest.ini` before use:

```ini
[pytest]
markers =
    ui: marks tests as UI tests
    api: marks tests as API tests
    smoke: marks tests as smoke tests
    negative: marks tests for negative/error-path scenarios
    regression: marks tests for regression coverage
    api_contract: marks tests that validate API response schema against a declared JSON schema contract
```

Running a test with an undeclared marker will produce a warning. Treat undeclared-marker warnings as errors in CI.
