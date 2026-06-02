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

---

## CI Gate / Workflow Failures

When a required CI check blocks a PR, collect the following before proposing a fix:

| Field | What to capture |
| --- | --- |
| PR | PR number and title |
| Failing check | Exact check name as shown in the PR checks panel |
| Failing job or integration | Workflow job name (e.g., `Docker Test Suite`) or GitHub-native integration (e.g., code scanning) |
| Failing step or alert location | Step name within the job, or file path and line number for a code scanning alert |
| Trigger | `pull_request`, `push`, `schedule`, or `workflow_dispatch` |
| Commit SHA | The commit the check ran against |
| Error excerpt | Exact error text or annotation message, sanitized — do not paste secret values |
| Root cause class | Code defect / CI/YAML defect / dependency scan finding / environment or secret issue / GitHub settings issue / flaky or external service issue |
| PR-introduced or pre-existing | Whether the failure exists on `main` before this PR |
| Smallest safe fix | Minimal change — do not overbuild |
| Validation to rerun | Commands or checks that confirm the fix |
| Governance or ADR update needed | Whether the failure reveals a reusable rule or missing operating instruction |

### Note: GitHub code scanning vs. workflow job checks

A `CodeQL` code scanning check and an `Analyze Python` workflow job check are distinct entries in the PR checks panel, even when the same `codeql.yml` workflow produces both.

- `Analyze Python` — the workflow job that runs the CodeQL analysis. Passes when the job executes without error.
- `CodeQL` (or `Code scanning results / CodeQL`) — a GitHub-native check posted by the code scanning integration after the analysis completes. Fails when new high or critical alerts are found in code changed by the PR.

Both may be required checks. Confirm which check is blocking before investigating the workflow logs — the workflow job can pass while the code scanning check fails.

### CodeQL: secret-taint in logging

CodeQL's taint analysis traces secret env var reads through function arguments into log sinks. A helper function that transforms a secret value (e.g., returning `"set"` or `"not set"`) is not treated as a sanitizer if the secret variable is passed as an argument — CodeQL flags the call site, not just direct use.

Rules for scripts that read from secret env vars:

- Do not pass secret env var values into any function used near `print()` or `logging` calls.
- Do not rely on helper functions to sanitize secret values for logging — the taint follows the argument, not the return value.
- Break the taint chain entirely: avoid referencing the secret variable in any expression that leads to a log sink.
- Print hardcoded status strings (`"configured"`, `"set"`, `"not set"`) derived from truthiness checks (`if secret_var:`) rather than from the value itself.

Example — flagged by CodeQL:

```python
webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
print(f"Webhook: {_secret_status(webhook_url)}")  # taint: webhook_url → argument → print
```

Example — not flagged:

```python
webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
print("[DRY RUN] SLACK_WEBHOOK_URL not set")  # webhook_url not referenced in print
```
