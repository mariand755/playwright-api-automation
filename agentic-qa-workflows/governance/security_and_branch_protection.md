# Security and Branch Protection

This document covers GitHub repository administrator settings and security policies. These are not CI workflow configurations — they must be applied manually in GitHub → Settings → Branches and Settings → Code security and analysis.

---

## Recommended branch protection settings for `main`

Navigate to: **GitHub → Settings → Branches → Add branch protection rule → Branch name pattern: `main`**

### Minimum recommended settings

| Setting | Recommended value |
|---|---|
| Require a pull request before merging | Enabled |
| Require status checks to pass before merging | Enabled |
| Require branches to be up to date before merging | Enabled |
| Dismiss stale pull request approvals when new commits are pushed | Enabled |
| Do not allow bypassing the above settings | Enabled |

### Required status checks

Add exactly four required checks by job name:

```text
Docker Test Suite
API Tests
UI Tests
Analyze Python
```

**Important:** GitHub branch protection operates at the **job level**, not the step level. Individual CI steps — Check formatting, Lint, Type check, Python dependency scan, Container image scan, Verify test collection — are internal steps within the `Docker Test Suite` job. They are not separately addressable as required status checks. Requiring `Docker Test Suite` to pass requires all internal steps to pass first.

**Post-merge update required:** `API Tests` and `UI Tests` will not appear in GitHub's branch protection check autocomplete until those jobs have run on `main` at least once. The correct sequence is: merge PR → CI runs on main → job names appear in check history → go to Settings → Branches → edit branch protection rule → add `API Tests` and `UI Tests` as required checks alongside the existing `Docker Test Suite` and `Analyze Python`.

#### What `Docker Test Suite` covers

The `Docker Test Suite` job (`.github/workflows/ci.yml`) runs the following gates in order. Steps 1–8 must all pass for the job to succeed. Step 9 is an advisory reporting step that does not block the job:

1. Docker build
2. Ruff format check
3. Ruff lint check
4. mypy type check (`utils/`, `pages/`, `scripts/`)
5. Python dependency vulnerability scan (pip-audit)
6. Container image vulnerability scan (Trivy — fixable HIGH/CRITICAL only)
7. pytest collection check
8. Script unit tests (`test/scripts/`) — produces `artifacts/scripts-report.xml`; any test failure fails the `Docker Test Suite` job
9. `Script Unit Test Results` via dorny/test-reporter — advisory check annotation (`fail-on-error: false`); `Docker Test Suite` is and remains the required branch-protection gate for script unit tests

#### What `API Tests` covers

The `API Tests` job (`.github/workflows/ci.yml`) runs after `Docker Test Suite` passes. It covers:

1. Docker build (fresh runner)
2. API test suite execution (`test/api/`) — produces `artifacts/api-report.xml`
3. API CI summary using `scripts/ci_summary.py`
4. Release readiness gate using `artifacts/api-report.xml` + observability + defect metrics
5. API test report through dorny/test-reporter as `API Test Results`

#### What `UI Tests` covers

The `UI Tests` job (`.github/workflows/ci.yml`) runs after `Docker Test Suite` passes. It covers:

1. Docker build (fresh runner)
2. UI test suite execution (`test/ui/`) — produces `artifacts/ui-report.xml`
3. UI CI summary using `scripts/ci_summary.py`
4. UI test report through dorny/test-reporter as `UI Test Results`
5. Failure artifact upload for screenshots and HTML on UI test failure

**Note:** The release readiness gate currently reflects API test results only. UI failures are surfaced through the `UI Tests` required check blocking merge. Multi-source release gate consolidation (combining API + UI results) is deferred to a future slice.

**Note about job summaries:** Both `API Tests` and `UI Tests` output `## Test Summary` in their respective job summaries. This is intentional — GitHub Actions displays each job's summary separately, so there is no content collision between the two.

#### What `Analyze Python` covers

The `Analyze Python` job (`.github/workflows/codeql.yml`) runs CodeQL static security analysis on the Python codebase.

**Note:** Requiring `Analyze Python` ensures the CodeQL analysis has run and completed successfully — not that zero findings exist. Findings are published to the GitHub Security tab (Security → Code scanning alerts) and are advisory by default. In the rare event of a CodeQL infrastructure failure (workflow error, not a finding), this required check would block merges until the failure is resolved.

---

## Gate classification

| Check | Type | Blocking | Surface | Trigger |
|---|---|---|---|---|
| Ruff format | Hard CI gate | Yes — fails `Docker Test Suite` | CI step | PR / push / nightly |
| Ruff lint | Hard CI gate | Yes — fails `Docker Test Suite` | CI step | PR / push / nightly |
| mypy type check | Hard CI gate | Yes — fails `Docker Test Suite` | CI step | PR / push / nightly |
| pip-audit | Hard CI gate | Yes — fails `Docker Test Suite` | CI step | PR / push / nightly |
| Trivy (fixable HIGH/CRITICAL) | Hard CI gate | Yes — fails `Docker Test Suite` | CI step | PR / push / nightly |
| pytest collection | Hard CI gate | Yes — fails `Docker Test Suite` | CI step | PR / push / nightly |
| Script unit tests (`test/scripts/`) | Hard CI gate | Yes — fails `Docker Test Suite` | CI step | PR / push / nightly |
| `Script Unit Test Results` (dorny panel) | Advisory | No — check annotation only; `Docker Test Suite` is the required gate | dorny/test-reporter check | PR / push / nightly |
| API test suite | Hard CI gate | Yes — fails `API Tests` | CI job | PR / push / nightly |
| UI test suite | Hard CI gate | Yes — fails `UI Tests` | CI job | PR / push / nightly |
| Release readiness gate | Hard CI gate | Yes — fails `API Tests` | CI step | PR / push / nightly |
| CodeQL findings | Advisory | No — Security tab | GitHub Security tab | PR / push / weekly |
| Dependabot updates | Update visibility | No — creates PRs | Dependabot PRs | Weekly |
| GitHub secret scanning | Platform protection | Yes (push protection enabled) | Git push rejection | Push |
| Notification delivery | Advisory | No — exits 0 always | CI step output | schedule / workflow_dispatch / push to main (on failure) / pull_request (on failure, when `NOTIFY_PR_FAILURES=true`) |

---

## Secret scanning guidance

### Enabling GitHub secret scanning and push protection

Navigate to: **GitHub → Settings → Code security and analysis**

- **Secret scanning:** Enable. GitHub scans all commits and alerts on detected credentials matching known secret patterns (API keys, tokens, and service credentials).
- **Push protection:** Enable. GitHub rejects pushes containing detected secrets before they reach the remote, independent of CI.

Both settings are free for public repositories. For private repositories they require GitHub Advanced Security.

### Committed credential policy

Real secrets — API keys, tokens, service credentials, passwords for real systems — must never be committed to this repository.

Real secrets must be stored in GitHub Secrets and injected as environment variables in CI workflows.

If a real secret is accidentally committed: rotate it immediately, then remove it from git history. Push protection would have blocked the original push if it was enabled.

### Demo credential classification

This repo tests against public demo services. The following credentials are publicly documented on their respective service websites and are not secrets:

| Service | Username | Password | Classification |
|---|---|---|---|
| Restful Booker | `admin` | `password123` | Public demo credential — safe to commit |
| SauceDemo | `standard_user` | `secret_sauce` | Public demo credential — safe to commit |
| SauceDemo | `locked_out_user` | `secret_sauce` | Public demo credential — safe to commit |

These credentials are stored in `data/test_users.json` and loaded via fixtures. They do not trigger GitHub secret scanning because they are not registered secret patterns.

---

### Notification secrets

The following secrets are required for live notification delivery from `scripts/notify.py`. Store all values in **GitHub Settings → Secrets → Actions**. Never commit these values to the repository. Rotate and remove from git history if accidentally committed.

| Secret | Purpose |
| --- | --- |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL — the URL itself is the credential |
| `SMTP_HOST` | SMTP server hostname (e.g., `smtp.gmail.com` for Gmail) |
| `SMTP_PORT` | SMTP port (optional; default `587` for STARTTLS, `465` for SMTP_SSL) |
| `SMTP_USER` | SMTP login / sender email address |
| `SMTP_PASSWORD` | SMTP password or app password — see Gmail note below |
| `EMAIL_FROM` | Sender display address (optional; defaults to `SMTP_USER`) |
| `NOTIFY_RECIPIENTS` | Comma-separated recipient email addresses |

**Gmail configuration:** set `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`. `SMTP_PASSWORD` must be a **Gmail App Password** (Google Account → Security → App passwords) — not the Google account password. App passwords are 16-character codes generated per application.

**No branch protection change required.** The notification step runs inside the existing `API Tests` job (not a new CI job), so the four required checks remain unchanged.

**`NOTIFY_DRY_RUN`.** Set to `true` or `1` as a GitHub repository variable (Settings → Variables → Actions, not Secrets) to force dry-run for all channels without removing the secrets. Useful for temporarily pausing live delivery without credential changes.

For the notification delivery architecture and alternatives considered, see [`architecture_decision_log.md` — ADR-011](architecture_decision_log.md#adr-011-notification-delivery-defaults-to-dry-run-when-secrets-are-absent).
For step-by-step live Slack and SMTP setup, see [`notification_wiring.md`](notification_wiring.md).

---

### Observability secrets

The following secrets are required for live observability data pulls from `scripts/pull_observability.py`. Store all values in **GitHub Settings → Secrets and variables → Actions → Secrets tab**. Never commit these values to the repository. Rotate and remove from git history if accidentally committed.

| Secret | Provider | Purpose |
| --- | --- | --- |
| `DATADOG_API_KEY` | Datadog | Datadog API authentication key |
| `DATADOG_APP_KEY` | Datadog | Datadog application key (scopes API access) |
| `GRAFANA_URL` | Grafana | Grafana instance base URL — treat as a secret; reveals infrastructure topology |
| `GRAFANA_API_KEY` | Grafana | Grafana service account token |
| `GRAFANA_DASHBOARD_UID` | Grafana | Dashboard UID for panel queries |
| `PAGERDUTY_API_KEY` | PagerDuty | PagerDuty REST API key |
| `PAGERDUTY_SERVICE_ID` | PagerDuty | PagerDuty service ID for incident queries |

Provision only the secrets for the chosen provider. `OBSERVABILITY_PROVIDER` (a repository variable, not a secret) selects which provider is active — only one provider runs at a time.

**`OBSERVABILITY_WRITE`** is a GitHub repository variable, not a secret. Add it under **Settings → Secrets and variables → Actions → Variables tab**. Setting `OBSERVABILITY_WRITE=true` without the required credentials for the selected provider still dry-runs — credentials alone do not enable writes.

**`DATADOG_SITE`** is forward-documented in the stub for a real Datadog implementation but is not read by the current stub. It is not an active secret and should not be stored in GitHub Secrets until a real Datadog integration is implemented.

For step-by-step provider activation, variable configuration, and validation commands, see [`observability_wiring.md`](observability_wiring.md).

---

## Future optional: gitleaks

gitleaks is an open-source secret scanning tool that can be added as a CI step or pre-commit hook to scan git history and staged changes for secrets matching configurable patterns.

**What it adds over GitHub native secret scanning:**

- Runs locally before push in pre-commit mode
- Supports configurable custom patterns for project-specific secret formats
- Can scan full git history, not just new pushes

**Condition for implementation:** Add gitleaks when this repo transitions from public demo credentials to real environment credentials, or when a dedicated slice explicitly approves adding it. Do not add gitleaks until that slice is approved.
