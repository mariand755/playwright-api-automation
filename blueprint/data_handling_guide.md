# Data Handling Guide

## Purpose

This guide documents what data the QA automation framework produces, where it goes, and what
controls exist. It is for consulting engineers and client reviewers who need to understand the
data surface before activating notifications, observability, or production-adjacent testing.

---

## Data Flows at a Glance

| Data item | Source in this repo | Where it goes | Sensitivity | Default state |
|---|---|---|---|---|
| JUnit XML (`artifacts/api-report.xml`, `ui-report.xml`, `scripts-report.xml`) | pytest `--junitxml` | GitHub check annotations (dorny/test-reporter); release gate input for `api-report.xml` only | Medium — includes assertion text, HTTP URLs, response body excerpts up to 200 chars | Always active |
| UI failure screenshots (`artifacts/failures/*.png`) | `conftest.py` Playwright hook | `failure-artifacts` CI artifact | High — full-page browser capture; may include login forms, session state, or PII | Only on UI test failure |
| UI failure HTML dumps (`artifacts/failures/*.html`) | `conftest.py` Playwright hook | `failure-artifacts` CI artifact | High — full page source; may include hidden fields, auth attributes, DOM-embedded tokens | Only on UI test failure |
| API response excerpts in CI logs | pytest assertion messages | GitHub Actions step logs | Medium — up to 200 chars of response body per assertion; may surface tokens or user data in non-demo repos | Always active in test runs |
| Observability snapshot (`data/release/observability_snapshot.json`) | `scripts/pull_observability.py` | Release gate input; stays within CI runner | Low now / Medium when live — static sample values until a live provider is activated | Stub-backed (sample data) |
| Defect metrics (`data/release/defect_metrics.json`) | Repository (committed sample file) | Release gate input; stays within CI runner | Low now — static sample counts (open blockers, criticals, escapes); real defect data only when replaced with a live source | Stub-backed (sample data) |
| Release readiness JSON (`artifacts/release-readiness.json`) | `scripts/release_gate.py` | `release-readiness-report` CI artifact; Notify job input | Low — test counts, failed test names, observability metrics (sample data until live provider active) | Always active on full runs |
| Release gate step summary (`artifacts/release-readiness.md`) | `scripts/release_gate.py` | GitHub Actions step summary (CI run page) | Low — same content as release-readiness.json | Always active on full runs |
| Slack notification | `scripts/notify.py` | Slack workspace via webhook (Slack's servers) | Medium — readiness verdict, CI job names and results, test counts, run URL; no response excerpts or screenshots | Dry-run by default |
| Email notification | `scripts/notify.py` | SMTP relay → recipient inboxes | Medium — same as Slack; subject includes repo name; may persist longer than Slack messages | Dry-run by default |
| Test credentials (`data/test_data/test_users.json`) | Repository (committed) | Read by `conftest.py` at test time; never written to artifacts | Low for this repo — public demo accounts only; real credentials must use GitHub Secrets | Always in repo |

---

## Key Sensitivity Notes

### JUnit XML and check annotations

Failure messages in JUnit XML include assertion text from test files. In this repo, API test
assertions use `response.text[:200]`, so up to 200 characters of response body appear in GitHub
check annotations and step logs. For tests against non-demo services, evaluate whether response
bodies may contain session tokens, user IDs, or other data your client classifies as sensitive.
Adjust the truncation limit or strip sensitive fields from assertion messages accordingly.

### UI failure screenshots and HTML dumps

Screenshots and HTML dumps capture the browser state at the exact moment of failure. If the
failing page shows a login form, a session-authenticated screen, or user-generated content, that
material appears in the artifact. These are uploaded to GitHub Actions only when UI tests actually
fail. Before running against real services, evaluate:

- Who has access to GitHub Actions artifacts for this repo (Settings → Actions → Artifact and log
  retention settings)
- Whether HTML dumps from your test environment could contain auth tokens or session identifiers
  embedded in DOM state
- Whether the default GitHub artifact retention period (90 days) is appropriate for your client's
  data classification

### Notifications do not contain raw test output

Slack and email notifications contain: overall readiness verdict (GO/NO_GO/BLOCKED/UNKNOWN), CI
job names and results, test counts (passed/failed/skipped), and a link to the GitHub Actions run.
They do not contain individual test names, response body excerpts, or failure screenshots.

Credentials (SMTP password, Slack webhook URL) are never logged — the notification script
(`scripts/notify.py`) breaks the CodeQL taint chain by referencing only truthiness checks, not
credential values, near any log output.

When Slack delivery is active, release readiness decisions become visible to everyone in your Slack
workspace with access to the notification channel. Choose the channel accordingly.

### Observability data is sample-only until activated

`data/release/observability_snapshot.json` contains static sample values (error rate 0.3%,
p95 210ms, etc.) and a `_note` field that marks these explicitly as non-live data. The release
readiness JSON output carries a `data_note` field with the same warning. When a live observability
provider (Datadog, Grafana, or PagerDuty) is activated per
[`observability_wiring.md`](../agentic-qa-workflows/governance/observability_wiring.md), real production performance metrics
will flow through to release-readiness.json and appear in Slack and email notifications. Evaluate
the sensitivity of those metrics and confirm the provider credentials have read-only scope before
activation.

---

## Controls to Evaluate Before Activating Each Capability

### Slack notifications

Require: `SLACK_WEBHOOK_URL` as a GitHub Actions Secret.

- Choose the destination channel — access to that channel determines who sees release readiness
  decisions
- Treat the webhook URL as a password; rotate immediately if accidentally exposed
- Use `NOTIFY_DRY_RUN=true` (GitHub repository variable) to force dry-run while validating

Full setup: [`notification_wiring.md`](../agentic-qa-workflows/governance/notification_wiring.md)

### SMTP email notifications

Require: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `NOTIFY_RECIPIENTS` as GitHub Actions Secrets.

- Confirm SMTP relay is reachable from GitHub Actions runners; port 465 or a transactional email
  API may be required
- Review recipient inboxes and organisational retention policies — email typically persists longer
  than Slack messages
- Test with `NOTIFY_DRY_RUN=true` before enabling live delivery

Full setup: [`notification_wiring.md`](../agentic-qa-workflows/governance/notification_wiring.md)

### Live observability

Require: activate `scripts/pull_observability.py` with a real provider per the 5-condition
checklist in [`observability_wiring.md`](../agentic-qa-workflows/governance/observability_wiring.md).

- Confirm provider credentials are scoped read-only
- Implement the snapshot freshness guard (ADR-017 activation condition 4) before relying on the
  gate for real release decisions — a stale snapshot from a prior CI run can silently pass the gate
- Decide whether to write to the tracked static file or a workflow-local artifact path; if using a
  custom path, update `scripts/release_gate.py` to match

### Prod-read-only testing

Require: `PROD_ENV_ACTIVE=true` as a GitHub repository variable; real prod URLs and credentials as
GitHub Secrets (not in `data/test_data/test_users.json`).

- Confirm test assertions do not log sensitive prod response content to CI step logs
- Failure artifacts (screenshots, HTML) from a prod-adjacent page carry higher classification than
  staging artifacts
- Document the decision to run automated read-only tests against prod in an ADR before activating
  (see ADR-015 for the existing activation conditions)

---

## What This Repo Does Not Do

- No live production observability — stub-backed until a provider is activated per
  [`observability_wiring.md`](../agentic-qa-workflows/governance/observability_wiring.md)
- No validated SMTP delivery — infrastructure-ready; runner SMTP restrictions may require a
  transactional email API
- No prod-read-only testing by default — gated by `PROD_ENV_ACTIVE` repository variable
- No compliance certification for any data handling regime

Data handling obligations depend on client context: the target application, the data it processes,
the test environment, and the applicable regulatory framework. This guide documents controls and
activation gates; it does not make compliance determinations.

---

## Client Adaptation Checklist

Before activating this framework against client infrastructure:

- [ ] Review assertion format in test files — evaluate whether `response.text[:200]` may surface
      sensitive data from non-demo APIs; adjust truncation or sanitise fields as needed
- [ ] Review GitHub Actions artifact access settings — confirm who can download failure artifacts
      if screenshots or HTML dumps may contain sensitive content
- [ ] Set artifact retention period to match your client's data classification requirements
- [ ] Confirm `data/test_data/test_users.json` contains only non-sensitive staging accounts;
      move real credentials to GitHub Secrets before running against real services
- [ ] Validate Slack channel audience before enabling live Slack notifications
- [ ] Validate SMTP relay compatibility with GitHub Actions runners before enabling live email
- [ ] Set `NOTIFY_DRY_RUN=true` during initial notification validation; remove only after live
      delivery is confirmed
- [ ] Confirm observability provider credentials have read-only scope before wiring live data
- [ ] Write an ADR before activating prod-read-only testing — document scope, data sensitivity
      decision, and client approval
