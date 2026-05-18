# Quality Gates

## PR Gate

Before a pull request may be reviewed:

- Smoke suite must pass: `pytest -m smoke -v`
- No new test may be added without at least one assertion that would fail if the feature broke.
- All new markers must be declared in `pytest.ini`.
- Before using new governance markers such as `negative`, `regression`, or `api_contract`, add them to `pytest.ini`.

## Merge Gate

Before a pull request may be merged to main:

- Full suite must pass: `pytest -v`
- No test may be merged in a `skip` or `xfail` state without a comment linking to an open issue explaining why.
- Any new page class must have a corresponding locator entry in `pages/locators.py`.
- Any new API endpoint under test must have a corresponding method in `BookingApiClient`.

## Release Gate

Before a release build is tagged:

- Full suite must pass inside Docker: `docker build -t playwright-api-automation . && docker run --rm playwright-api-automation`
- If the release run produces failure artifacts, review each screenshot/HTML dump and classify the failure as product, test, or infrastructure before making a release decision.
- Release may proceed only when failures are fixed, formally waived, or documented as non-blocking with rationale.

## Coverage Floor

At a minimum, every public API endpoint and every UI flow must have:

- At least one positive test (happy path)
- At least one negative test (error path or invalid input)

Endpoints or flows with only a positive test are considered incomplete and must be flagged in the PR description.

## Skips and Expected Failures

- `@pytest.mark.skip`: allowed only for tests blocked by an upstream bug or dependency not yet available. Must include `reason="<issue link>"`.
- `@pytest.mark.xfail`: allowed only for known, documented failures being tracked. Must include `reason="<issue link>"` and `strict=True` where appropriate.
- Skips and xfails must be removed when the blocking condition is resolved.