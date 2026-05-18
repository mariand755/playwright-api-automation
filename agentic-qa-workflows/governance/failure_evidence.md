# Failure Evidence

## UI Test Failures

Every UI test failure must automatically produce:

- **Full-page screenshot**: `artifacts/failures/<test_name>.png`
- **Page HTML dump**: `artifacts/failures/<test_name>.html`

This is already implemented via the `pytest_runtest_makereport` hook in `conftest.py`. Do not remove or bypass this hook.

The `artifacts/failures/` directory is gitignored. It must be archived as a CI build artifact so failures are inspectable after the run.

## API Test Failures

When an API assertion fails, the test output must include enough context to diagnose the failure without re-running. Ensure the following are visible in the pytest short traceback:

- HTTP method and full URL
- Response status code
- Response body (or a meaningful excerpt if large)

Achieve this by asserting with a descriptive message:

```python
assert response.status_code == 200, (
    f"POST {response.url} failed: "
    f"status={response.status_code}, body={response.text[:200]}"
)
```

## Artifact Directory

| Artifact | Path | Gitignored |
|---|---|---|
| UI screenshot | `artifacts/failures/<test_name>.png` | Yes |
| UI HTML dump | `artifacts/failures/<test_name>.html` | Yes |
| Full run output | `artifacts/local-run-output.txt` | No |
| Docker run output | `artifacts/docker-run-output.txt` | No |

## CI Requirements

- Archive `artifacts/failures/` as a build artifact on test failure.
- Publish `artifacts/local-run-output.txt`, `artifacts/docker-run-output.txt`, or the equivalent CI log for every run.
- Do not commit generated screenshots or HTML files to the repository.
