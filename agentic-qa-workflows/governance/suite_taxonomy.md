# Suite Taxonomy

## Marker Types

Markers fall into two categories:

- **Area markers** (`ui`, `api`): identify which layer the test exercises. Apply these first.
- **Execution-scope markers** (`smoke`, `negative`, `regression`): identify when and why the test runs. Apply these after the area marker.

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
- Current tests: `test_user_can_login`

## Target Markers (must be added to pytest.ini before use)

The following markers are defined as governance targets. They must be declared in `pytest.ini` under `markers` before any test uses them.

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

## Adding a Test to a Suite

| Condition | Area marker | Scope marker |
|---|---|---|
| Browser-driven test | `ui` | — |
| REST API test | `api` | — |
| First passing test for a new feature | `ui` or `api` | `smoke` |
| Error path or invalid input | `ui` or `api` | `negative` |
| Protecting a shipped feature from regression | `ui` or `api` | `regression` |

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
```

Running a test with an undeclared marker will produce a warning. Treat undeclared-marker warnings as errors in CI.
