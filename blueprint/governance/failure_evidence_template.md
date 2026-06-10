# Failure Evidence

## UI Test Failures

Every UI test failure must automatically produce:

- **Full-page screenshot**: `[your-project]/artifacts/failures/[test_name].png`
- **Page source snapshot**: `[your-project]/artifacts/failures/[test_name].html`

Implement this via a `pytest_runtest_makereport` hook in `conftest.py`. Do not remove or bypass this hook.

The `artifacts/failures/` directory must be gitignored. Archive it as a CI build artifact so failures are inspectable after the run.

For artifact sensitivity and retention guidance, see [`blueprint/data_handling_guide.md`](../data_handling_guide.md).

---

## API Test Failures

When an API assertion fails, the test output must include enough context to diagnose the failure without re-running. Ensure the following are visible in the pytest short traceback:

- HTTP method and full URL
- Response status code
- Response body (or a meaningful excerpt if large)

Achieve this by asserting with a descriptive message:

```python
method = "POST"  # Replace with the request method used by this check.

assert response.status_code == 200, (
    f"{method} {response.url} failed: "
    f"status={response.status_code}, body={response.text[:200]}"
)
```

---

## Artifact Directory

| Artifact | Path | Gitignored |
|---|---|---|
| UI screenshot | `[your-project]/artifacts/failures/[test_name].png` | Yes |
| UI page snapshot | `[your-project]/artifacts/failures/[test_name].html` | Yes |
| Full run output | `[your-project]/artifacts/[run-output].txt` | No |
| Docker run output | `[your-project]/artifacts/[docker-run-output].txt` | No |

---

## CI Requirements

- Archive `artifacts/failures/` as a build artifact on test failure.
- Publish the CI run log (step output or equivalent artifact) for every run.
- Do not commit generated screenshots or page snapshots to the repository.

---

## CI Gate / Workflow Failures

When a required CI check blocks a PR, collect the following before proposing a fix:

| Field | What to capture |
|---|---|
| PR | PR number and title |
| Failing check | Exact check name as shown in the PR checks panel |
| Failing job or integration | Workflow job name or GitHub-native integration (e.g. code scanning) |
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

A code scanning check and a workflow job check are distinct entries in the PR checks panel, even when the same workflow file produces both.

- The **workflow job** — passes when the job executes without error.
- The **code scanning check** — posted by the GitHub code scanning integration after analysis completes. Fails when new high or critical alerts are found in code changed by the PR.

Both may be required checks. Confirm which check is blocking before investigating workflow logs — the workflow job can pass while the code scanning check fails.

### Secret values in log sinks

Static analysis tools (e.g. CodeQL) trace secret environment variable reads through function arguments into log and print sinks. Break the taint chain entirely: reference a secret variable only in a truthiness check, not in any expression that flows into a log or print sink. Analysis tools trace the argument itself into the sink, not the return value of a helper function — a helper that returns `"set"` or `"not set"` does not sanitize the taint if the secret variable is passed as an argument.

---

## Failure Classification

Classify every CI failure before proposing a fix:

| Class | Examples |
|---|---|
| Code defect | Assertion fails on changed logic; import error in modified file |
| CI/YAML defect | Wrong step name; missing `env:` block; incorrect artifact path |
| Dependency scan finding | New CVE in a pinned package; unfixed HIGH finding in container image |
| Environment or secret issue | Missing secret; expired credential; SMTP relay unreachable from runner |
| GitHub settings issue | Required check name mismatch; branch protection misconfiguration |
| Flaky or external service issue | Network timeout; third-party API rate limit; intermittent DNS |

---

## Triage Ownership

| Failure class | First owner |
|---|---|
| Code defect | Author of the PR that introduced it |
| CI/YAML defect | Author of the CI change |
| Dependency scan finding | Maintainer on rotation; escalate if no fix available |
| Environment or secret issue | Repo owner or infrastructure contact |
| GitHub settings issue | Repo admin |
| Flaky or external service issue | On-call or team rotation |
