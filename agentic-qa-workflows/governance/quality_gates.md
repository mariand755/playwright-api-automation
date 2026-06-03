# Quality Gates

## PR Gate

Before a pull request may be reviewed:

- Dockerized smoke suite must pass:
  `docker build -t playwright-api-automation . && docker run --rm playwright-api-automation pytest -m smoke -v`
- No new test may be added without at least one assertion that would fail if the feature broke.
- All new markers must be declared in `pytest.ini`.
- Before using new governance markers such as `negative`, `regression`, or `api_contract`, add them to `pytest.ini`.
- Local pytest runs are optional fast feedback only and do not replace Docker verification.
- Formatting and lint checks must pass: see Docker-First Quality Checks section below.
- Dependency and container scans must pass: see Docker-First Quality Checks section below.
- CodeQL findings should be reviewed before merging: see GitHub-Native Security Checks section below.

## Merge Gate

Before a pull request may be merged to main:

- Docker full suite must pass:
  `docker build -t playwright-api-automation . && docker run --rm playwright-api-automation`
- No test may be merged in a `skip` or `xfail` state without a comment linking to an open issue explaining why.
- Any new page class must have a corresponding locator entry in `pages/locators.py`.
- Any new API endpoint under test must have a corresponding method in `BookingApiClient`.

## Release Gate

Before a release build is tagged:

- Full suite must pass inside Docker: `docker build -t playwright-api-automation . && docker run --rm playwright-api-automation`
- If the release run produces failure artifacts, review each screenshot/HTML dump and classify the failure as product, test, or infrastructure before making a release decision.
- Release may proceed only when failures are fixed, formally waived, or documented as non-blocking with rationale.

---

## Docker-First Quality Checks

Docker is the default execution environment for this repo. Local commands are optional fast-feedback only and should not be assumed. An AI agent must ask the repo owner before running local commands or relying on local virtualenv dependencies.

After editing any file that is copied into the Docker image (`COPY . .` in the Dockerfile), rebuild the image before running Dockerized validation. `ruff`, `mypy`, and `pytest` validate the image contents, not the local working tree. A volume-mounted dry-run, such as `-v $(pwd)/file.py:/app/file.py`, tests that mounted file in isolation and does not prove the rebuilt image passes all checks.

### Current required checks

1. **Docker build:**

   ```bash
   docker build -t playwright-api-automation .
   ```

2. **Dockerized pytest collection** — confirm tests collect cleanly with no marker or import errors:

   ```bash
   docker run --rm playwright-api-automation pytest --collect-only -q
   ```

3. **Dockerized targeted test check** — run only the smallest relevant suite for the change. The commands below are examples; choose the one that matches the scope of the change:

   ```bash
   docker run --rm playwright-api-automation pytest -m smoke -v
   docker run --rm playwright-api-automation pytest test/api -v
   docker run --rm playwright-api-automation pytest test/ui -v
   ```

4. **Dockerized format check** — confirm all Python files match Ruff formatting:

   ```bash
   docker run --rm playwright-api-automation ruff format --check .
   ```

5. **Dockerized lint check** — confirm all Python files pass Ruff linting:

   ```bash
   docker run --rm playwright-api-automation ruff check .
   ```

6. **Docker full-suite verification** — final confidence check before push or PR:

   ```bash
   docker run --rm playwright-api-automation
   ```

7. **Python dependency vulnerability scan** — confirms no known CVEs in project dependencies (queries OSV/PyPI advisory database); runs inside Docker:

   ```bash
   docker run --rm playwright-api-automation pip-audit -r requirements.txt --progress-spinner off
   ```

8. **Container image vulnerability scan** — confirms no fixable HIGH or CRITICAL CVEs in the built Docker image; runs as a CI step via `aquasecurity/trivy-action` (v0.36.0, pinned to commit SHA) with `--ignore-unfixed` and `--severity HIGH,CRITICAL`.

9. **Dockerized type check** — confirms no type errors in production modules (`utils/`, `pages/`, `scripts/`); runs inside Docker:

   ```bash
   docker run --rm playwright-api-automation mypy utils/ pages/ scripts/
   ```

   Initial strictness: `ignore_missing_imports = true`. Third-party libraries without type stubs (e.g. `requests`) are silently skipped rather than errored. Test files and `conftest.py` are excluded — pytest fixture return types depend on framework internals that require a separate future typing/stubs slice to configure correctly.

   Structural config: `explicit_package_bases = true` resolves module paths relative to the project root for directories without standard `__init__.py` package files.

### Local Developer Guardrails

Pre-commit provides optional fast feedback before push. It is not a replacement for Docker CI and does not constitute a quality gate — Docker CI remains the enforcement layer for all required checks.

| Property | Value |
| --- | --- |
| Advisory | Yes — `--no-verify` bypasses all hooks |
| Docker CI replacement | No — Docker CI is the source of truth |
| Required for contributors | No — install is per developer machine |

Install and register once per developer machine:

```bash
pip install pre-commit   # or: brew install pre-commit
pre-commit install       # registers the git hook in .git/hooks/pre-commit
```

Run manually against all files:

```bash
pre-commit run --all-files
```

#### Hooks included

| Hook | Source | Scope | Catches |
| --- | --- | --- | --- |
| `trailing-whitespace` | pre-commit-hooks | All files | Trailing whitespace |
| `end-of-file-fixer` | pre-commit-hooks | All files | Missing end-of-file newline |
| `check-yaml` | pre-commit-hooks | `.yml`/`.yaml` | Malformed YAML syntax |
| `check-json` | pre-commit-hooks | `.json` | Malformed JSON |
| `check-toml` | pre-commit-hooks | `.toml` | Malformed TOML — protects `pyproject.toml` config |
| `debug-statements` | pre-commit-hooks | `.py` | Committed `pdb`/`breakpoint()` debug calls |
| `ruff format` | local/system | `.py` | Formatting violations (auto-fixes) |
| `ruff check --fix` | local/system | `.py` | Lint violations (auto-fixes where possible) |
| `mypy` | local/system | `utils/`, `pages/`, `scripts/` | Type errors — same scope as CI |

#### What pre-commit does NOT cover

Pre-commit does **not** run CodeQL, pip-audit, Trivy, or Docker test execution. These remain CI-only gates:

- **CodeQL** — interprocedural taint analysis; requires the full CodeQL engine and codebase call graph. Cannot be replicated by a pre-commit hook. PR #22 CodeQL findings (secret-taint logging paths) required exactly this level of analysis.
- **pip-audit** — Python dependency vulnerability scan against the OSV advisory database.
- **Trivy** — container image vulnerability scan against the built Docker image layers.
- **Docker test execution** — pytest inside Docker; the authoritative test result.

A clean pre-commit run does not imply CI will pass. Always validate with a fresh Docker build before pushing a PR.

#### Tool-version coupling

Ruff and mypy run via `language: system` — they invoke tools from your active Python environment, not from a pre-commit-managed isolated environment. Activate your local venv (installed from `requirements.txt`) before committing to match the versions used in Docker CI. See [ADR-012](architecture_decision_log.md#adr-012-pre-commit-as-advisory-local-guardrail-docker-ci-as-source-of-truth) for the rationale.

### Future-state checks

- Expand mypy strictness: add `disallow_untyped_defs = true` per-module as annotation coverage grows.
- Add `types-requests` stubs to `requirements.txt` when mypy strictness increases to benefit from full `requests.Response` type resolution.
- Extend type checking to `conftest.py` when pytest typing is configured.

### CI job structure

The GitHub Actions workflow (`.github/workflows/ci.yml`) distributes the checks above across three jobs:

| Job | Covers | Depends on |
| --- | --- | --- |
| `Docker Test Suite` | Docker build, Ruff format, Ruff lint, mypy type check, pip-audit, Trivy, pytest collection | — |
| `API Tests` | API test suite, CI summary, release readiness gate | `Docker Test Suite` |
| `UI Tests` | UI test suite, CI summary, failure artifact upload | `Docker Test Suite` |

`API Tests` and `UI Tests` run in parallel after `Docker Test Suite` passes. All three jobs are required status checks for merge to `main`.

For the full required checks configuration and post-merge update instructions, see [`agentic-qa-workflows/governance/security_and_branch_protection.md`](security_and_branch_protection.md).

## Notification Delivery

Notification is report delivery, not a release gate. It does not block CI and is not a required status check.

The notification step (`Deliver release readiness notification`) runs in the `API Tests` job after the release gate summary is written. It reads `artifacts/release-readiness.json` and delivers the GO/NO_GO decision, test totals, gate failures, and warnings to Slack and email.

| Property | Value |
| --- | --- |
| Triggers | `schedule` and `workflow_dispatch` only — not on push or pull request |
| Blocking | Never — script always exits 0 |
| Required check | No — no branch protection change required |
| Implementation | `scripts/notify.py` — stdlib only, zero new dependencies |

**Channels are independent.** Slack can send while email dry-runs, and vice versa. Each channel checks its own env vars separately.

**Missing secrets trigger dry-run, not failure.** When a channel's required env vars are absent, the step logs a message preview and continues. CI does not fail.

**Live credentials are added through GitHub Settings, not committed config.** To enable live delivery:

- Slack: add `SLACK_WEBHOOK_URL` to GitHub Settings → Secrets → Actions
- Email: add `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `NOTIFY_RECIPIENTS` (and optionally `EMAIL_FROM`)
- Gmail example: `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_PASSWORD` must be a Gmail App Password (not the account password)

**`NOTIFY_DRY_RUN`.** Set to `true` or `1` (as a GitHub repository variable or local env var) to force dry-run for all channels even when secrets are present. Useful for validating notification wiring without triggering live delivery.

For the architectural decision record, see [`architecture_decision_log.md` — ADR-011](architecture_decision_log.md#adr-011-notification-delivery-defaults-to-dry-run-when-secrets-are-absent).
For the secrets policy, see [`security_and_branch_protection.md` — Notification secrets](security_and_branch_protection.md).
For step-by-step live Slack and SMTP setup, see [`notification_wiring.md`](notification_wiring.md).

## GitHub-Native Security Checks

These checks are GitHub-managed. They are not Docker-executed and cannot be run with a local `docker run` command.

### CodeQL

Static security analysis for Python. Configured in `.github/workflows/codeql.yml`. Runs on pull requests to `main`, pushes to `main`, and weekly on a schedule (to apply updated CodeQL queries to the current codebase).

Findings are published to the GitHub Security tab (Security → Code scanning alerts). A CodeQL finding does not block the CI test job; it creates a security alert for review and remediation.

### Dependabot

Automated dependency update visibility. Configured in `.github/dependabot.yml` for two ecosystems:

- **pip** — Python packages declared in `requirements.txt`. Note: `playwright` updates are intentionally ignored; the `playwright` version is coupled to the Docker base image and must be updated in a coordinated slice.
- **github-actions** — Actions used in `.github/workflows/*.yml`, including SHA-pinned third-party actions.

Dependabot creates pull requests on a weekly schedule when newer versions are available. It does not block CI; it provides update visibility and keeps dependency versions current.

For recommended GitHub repository settings (branch protection required checks and secret scanning), see [`agentic-qa-workflows/governance/security_and_branch_protection.md`](security_and_branch_protection.md).

---

## Coverage Floor

At a minimum, every public API endpoint and every UI flow must have:

- At least one positive test (happy path)
- At least one negative test (error path or invalid input)

Endpoints or flows with only a positive test are considered incomplete and must be flagged in the PR description.

## Skips and Expected Failures

- `@pytest.mark.skip`: allowed only for tests blocked by an upstream bug or dependency not yet available. Must include `reason="<issue link>"`.
- `@pytest.mark.xfail`: allowed only for known, documented failures being tracked. Must include `reason="<issue link>"` and `strict=True` where appropriate.
- Skips and xfails must be removed when the blocking condition is resolved.
