# Test Suite Taxonomy

## Marker Structure

Markers fall into two categories:

- **Area markers** — identify which layer the test exercises. Apply these first.
- **Execution-scope markers** — identify when and why the test runs. Apply these after the area marker.

Each test carries its area marker and, where applicable, one or more execution-scope markers:

```python
@pytest.mark.[area]
@pytest.mark.[scope]
def test_[action]_[expected_outcome](...):
    ...
```

Declare all markers in `pytest.ini` before use. Running a test with an undeclared marker produces a warning; treat undeclared-marker warnings as errors in CI.

---

## Area Markers

Define one area marker per test layer in your project. Typical examples:

| Marker | Scope | Notes |
|---|---|---|
| `[your-ui-marker]` | Browser-driven tests via [your UI framework] | All tests in `test/ui/` carry this marker |
| `[your-api-marker]` | REST API tests via [your HTTP library] | All tests in `test/api/` carry this marker |
| `[your-scripts-marker]` | Offline unit tests for platform scripts | All tests in `test/scripts/` carry this marker |

Add additional area markers if your project has more test layers (e.g., `mobile`, `integration`, `load`).

---

## Execution-Scope Markers

### `smoke`

Fast sanity check that the critical happy path works.

- **Scope:** one positive test per major feature area.
- **Run trigger:** CI runs smoke-tagged tests on every PR and feature branch push.
- **Target runtime:** under 60 seconds.
- **Pass requirement:** unblocking further test execution.

### `regression`

Full coverage sweep run before a release.

- **Scope:** all suites combined plus feature-area edge cases.
- **Run trigger:** push to main, nightly schedule, and pre-release.
- **Pass requirement:** release sign-off.

### `negative`

Verifies the system handles invalid input, missing data, and error conditions correctly.

- **Scope:** one negative test per user-facing error state.
- **Run trigger:** alongside the relevant area suite.
- **Pass requirement:** PR merge.

### `[your-contract-marker]` (optional)

Marks tests that validate API response schema against a declared schema contract.

- **Scope:** any test that validates a response against a schema file.
- **Run trigger:** alongside the API area suite.

---

## Traceability Marker

### `tc_id`

Marks a test with its unique test case ID for machine-readable traceability.

- **Purpose:** writes test case IDs into JUnit XML properties for downstream tooling (test management systems, CI dashboards).
- **Format:** `TC-[AREA]-[NNN]` — for example, `TC-UI-001`, `TC-API-003`.
- **Scope:** every test that has a TC-ID. Apply as the last decorator in the stack.
- **Behavior on absence:** silent — a test without a `tc_id` marker produces no property in JUnit XML.

```python
# TC-[AREA]-[NNN]
@pytest.mark.[area]
@pytest.mark.smoke
@pytest.mark.tc_id("TC-[AREA]-[NNN]")
def test_[action]_[expected_outcome](...):
    ...
```

Declare `tc_id` in `pytest.ini`:

```ini
[pytest]
markers =
    tc_id: unique test case ID for JUnit XML traceability
```

---

## Marker Decision Table

| Condition | Area marker | Scope marker |
|---|---|---|
| Browser-driven test | `[your-ui-marker]` | — |
| REST API test | `[your-api-marker]` | — |
| Platform/script test | `[your-scripts-marker]` | — |
| First passing test for a new feature | appropriate area | `smoke` |
| Error path or invalid input | appropriate area | `negative` |
| Protecting a shipped feature from regression | appropriate area | `regression` |
| API response schema validation | `[your-api-marker]` | `[your-contract-marker]` |

---

## Adding a New Marker

Any new marker must be:

1. Defined in this document with purpose, scope, and run trigger **before** any test uses it.
2. Added to `pytest.ini` under `markers` **before** any test is decorated with it.
3. Moved from a "planned" section to the appropriate section above once at least one test carries it.

---

## pytest.ini Starter

```ini
[pytest]
testpaths = test
markers =
    [your-ui-marker]: marks tests as UI tests
    [your-api-marker]: marks tests as API tests
    [your-scripts-marker]: marks tests for platform script logic
    smoke: marks tests as smoke tests (fast happy path)
    regression: marks tests for full regression coverage
    negative: marks tests for error-path scenarios
    tc_id: unique test case ID for JUnit XML traceability
```
