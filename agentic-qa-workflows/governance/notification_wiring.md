# Notification Wiring Guide

## Overview

The `Notify` CI job runs after `Docker Test Suite`, `API Tests`, and `UI Tests` all complete. It downloads `artifacts/release-readiness.json` from the `API Tests` artifact upload, receives each required job's outcome via `needs.*.result` env vars, and delivers an aggregate message to Slack and email.

**When it runs:**

| Trigger | Outcome | Notify? |
|---|---|---|
| `schedule` (nightly) | any | Yes — always |
| `workflow_dispatch` | any | Yes — always |
| `push` to `main` | any required job not `success` | Yes — BLOCKED notification |
| `push` to `main` | all required jobs `success` | No — opinionated silence on clean merges |
| `pull_request` | any required job not `success` AND `NOTIFY_PR_FAILURES=true` | Yes — BLOCKED notification |
| `pull_request` | all required jobs `success`, or `NOTIFY_PR_FAILURES` unset | No |
| feature branch push | any | No |

PR failure notification is opt-in via the `NOTIFY_PR_FAILURES` repository variable (see below). When unset, PR failures are silent — only the GitHub PR status panel shows the result. When set to `true`, the `Notify` job fires on PR failures using the same BLOCKED semantics as push-to-main failures.

**Fork PR note:** Pull requests from forks do not have access to repository secrets. When `NOTIFY_PR_FAILURES=true` is set and a fork PR fails, the `Notify` job will start but channels that require secrets (Slack, SMTP) will dry-run — no live delivery occurs. This is the correct safe default.

**Message structure:** Each notification includes:
- **Overall Release Readiness** — the aggregate verdict: GO, NO_GO, BLOCKED, or UNKNOWN. BLOCKED if any required job result is not exactly `success` (failure, cancelled, skipped, and unknown are all BLOCKED).
- **CI Status** — per-job result rows for Docker Test Suite, API Tests, and UI Tests.
- **Release Gate (staging API)** — the component gate decision from `release-readiness.json`. When overall readiness is BLOCKED but the component gate says GO, the line is annotated: `— component signal only; overall readiness is BLOCKED`.
- **Tests** — pass/fail/skip counts and duration (when release gate data is present).
- **Advisory Jobs** — cloud-grid and cross-browser status (PASS / FAIL / SKIPPED / PARTIAL), shown only on nightly and `workflow_dispatch` runs when advisory jobs were scheduled. Advisory status is display-only and does not affect Overall Release Readiness.
- **Run URL** — link to the GitHub Actions run.

**Dry-run default:** each channel checks its own required environment variables independently. When a channel's required variables are absent, it logs a message preview and continues without failing CI. Dry-run output includes all CI Status rows so wiring can be validated before live credentials are provisioned.

**Channel independence:** Slack and email operate independently. Slack can deliver live while email dry-runs, and vice versa.

**Implementation:** `scripts/notify.py` — stdlib only; zero new Python dependencies. The script runs directly on the GitHub Actions runner in the `notify` job without a Docker build or pip install.

**Observability data in the release gate line:** The "Release Gate (staging API)" line is derived from `artifacts/release-readiness.json`, which `scripts/release_gate.py` builds from `data/release/observability_snapshot.json`. In the current repo state, that snapshot contains static sample values — the release gate signal in notifications reflects sample data, not live production metrics. When `scripts/pull_observability.py` is activated with a live provider, notifications will reflect real observability evidence. See [`observability_wiring.md`](observability_wiring.md) for provider activation guidance.

For the architectural decision record, see [ADR-016 in architecture_decision_log.md](architecture_decision_log.md#adr-016-aggregate-ci-notification-job-after-all-required-jobs-complete) and [ADR-011](architecture_decision_log.md#adr-011-notification-delivery-defaults-to-dry-run-when-secrets-are-absent).

---

## Slack Setup

### What you need

A Slack workspace where you have permission to create apps, or an existing app with Incoming Webhooks already enabled.

### Steps

1. Go to api.slack.com/apps and sign in with your Slack workspace account.
2. Click **Create New App** → **From scratch**.
3. Enter an app name (for example, `CI Notifier`), select your workspace, and click **Create App**.
4. In the app settings sidebar, under **Features**, click **Incoming Webhooks**.
5. Toggle **Activate Incoming Webhooks** to **On**.
6. Click **Add New Webhook to Workspace**.
7. Select the channel to post notifications to and click **Allow**.
8. Copy the webhook URL shown on the Incoming Webhooks page. The format is:

   `https://hooks.slack.com/services/<workspace-id>/<app-id>/<webhook-token>`

9. In GitHub, go to **Settings → Secrets and variables → Actions → Secrets tab**.
10. Click **New repository secret**, set **Name** to `SLACK_WEBHOOK_URL`, and paste the webhook URL as the **Secret**.
11. Click **Add secret**.

### Security

The webhook URL is a credential — treat it as a password:

- Never commit it to the repository, `.env` files, screenshots, markdown, JSON data files, or CI artifact files.
- Rotate it immediately if accidentally exposed: delete the webhook in your Slack app settings, create a new one, and update the GitHub secret. Remove the old URL from git history.
- GitHub secret scanning (if enabled) will alert on detected webhook patterns. GitHub push protection (if enabled) will block pushes containing known secret formats before they reach the remote.

---

## Email / SMTP Setup

### Required GitHub secrets

Add all of the following in **GitHub → Settings → Secrets and variables → Actions → Secrets tab**:

| Secret | Purpose |
|---|---|
| `SMTP_HOST` | SMTP server hostname |
| `SMTP_PORT` | SMTP port (`587` for STARTTLS, `465` for SMTP_SSL) — optional; defaults to `587` |
| `SMTP_USER` | SMTP login / sender email address |
| `SMTP_PASSWORD` | SMTP password or app password |
| `EMAIL_FROM` | Sender display address — optional; defaults to `SMTP_USER` if not set |
| `NOTIFY_RECIPIENTS` | Comma-separated recipient email addresses |

### Gmail example

For Gmail, use the following values (substitute your own account and recipients):

- `SMTP_HOST`: `smtp.gmail.com`
- `SMTP_PORT`: `587`
- `SMTP_USER`: `your.address@gmail.com`
- `SMTP_PASSWORD`: a Gmail App Password — not your Google account password (see below)
- `NOTIFY_RECIPIENTS`: `team@example.com` (comma-separated for multiple recipients)

### Generating a Gmail App Password

Gmail requires an App Password when SMTP is used with an account that has 2-Step Verification enabled.

1. Sign in to the Gmail account that will send the notifications.
2. Go to **Google Account → Security**.
3. Under **How you sign in to Google**, confirm **2-Step Verification** is on. Enable it first if not already active.
4. Search for **App passwords** in the Google Account search bar and open it.
5. Select app: **Mail**. Select device: **Other**, enter a name such as `CI Notifier`.
6. Click **Generate** and copy the 16-character code shown on screen.
7. In GitHub: **Settings → Secrets and variables → Actions → Secrets tab → New repository secret**.
   Set **Name** to `SMTP_PASSWORD` and paste the 16-character code as the **Secret**.
8. Click **Add secret**.

You cannot view the app password again after leaving that screen. If lost, return to Google Account → Security → App passwords and generate a new one.

### Other SMTP providers

The same env vars work with any SMTP provider. Replace `smtp.gmail.com` and the Gmail credentials with your provider's values. Port `465` uses `SMTP_SSL`; all other ports (default `587`) use `STARTTLS`.

---

## NOTIFY_DRY_RUN (Repository Variable, not a Secret)

`NOTIFY_DRY_RUN` is a **GitHub repository variable** — not a secret.

Add it under: **Settings → Secrets and variables → Actions → Variables tab** (not the Secrets tab).

| Value | Effect |
|---|---|
| `true` or `1` | Forces dry-run for all channels, even when secrets are present |
| Unset or `false` | Allows live delivery when required secrets are configured |

**When to use it:**

- Validate the notification wiring before live credentials are provisioned
- Temporarily pause live delivery without removing or rotating secrets
- Re-enable live delivery by deleting the variable or setting its value to `false`

**Push-to-main failure notifications:** `NOTIFY_DRY_RUN=true` applies to all trigger types, including push-to-main failure notifications. A push to main that fails a required job will cause the `Notify` job to run, but all channels will dry-run — no live Slack or email is sent. Confirm `NOTIFY_DRY_RUN` is unset or `false` before relying on live push-to-main failure alerts.

**Important:** if `NOTIFY_DRY_RUN` is added under **Secrets** instead of **Variables**, the workflow's `${{ vars.NOTIFY_DRY_RUN }}` reference reads from the wrong namespace and resolves to an empty string. The flag silently has no effect.

---

## NOTIFY_PR_FAILURES (Repository Variable, not a Secret)

`NOTIFY_PR_FAILURES` is a **GitHub repository variable** — not a secret.

Add it under: **Settings → Secrets and variables → Actions → Variables tab** (not the Secrets tab).

| Value | Effect |
|---|---|
| `true` | The `Notify` job fires on PR failures when any required job is not `success` |
| Unset or any other value | PR failures are silent — only the GitHub PR status panel shows the result |

**Default behavior:** When `NOTIFY_PR_FAILURES` is unset, PR failures do not trigger the `Notify` job. This matches the "opinionated silence" policy from ADR-018 — teams receive a notification only when they have explicitly opted in.

**Fork PRs:** Pull requests from forks do not have access to repository secrets. When `NOTIFY_PR_FAILURES=true` is set and a fork PR fails, the `Notify` job will start but Slack and email channels will dry-run — no live delivery occurs. This is the correct safe default.

**Interaction with `NOTIFY_DRY_RUN`:** `NOTIFY_PR_FAILURES` controls job eligibility (does the job start on PR events?). `NOTIFY_DRY_RUN` controls channel delivery (does live delivery happen when the job runs?). Both can be set independently:

| `NOTIFY_PR_FAILURES` | `NOTIFY_DRY_RUN` | Effect on PR failure |
|---|---|---|
| unset | any | Notify job does not start — PR failure is silent |
| `true` | `true` | Notify job starts — all channels dry-run (useful for wiring validation) |
| `true` | unset or `false` | Notify job starts — live delivery if secrets are configured |

---

## Advisory Cloud Grid Configuration

### `SAUCE_CONNECT_TIMEOUT_MS` variable

`SAUCE_CONNECT_TIMEOUT_MS` is an optional **GitHub repository variable** (not a secret).

Add it under: **Settings → Secrets and variables → Actions → Variables tab**.

| Variable                   | Default | Purpose                                |
|----------------------------|---------|----------------------------------------|
| `SAUCE_CONNECT_TIMEOUT_MS` | `60000` | Playwright remote connect timeout (ms) |

When unset, the `cloud-grid` job defaults to 60 000 ms (60 seconds). Increase this value if your Sauce Labs account experiences frequent provisioning delays. The value is passed to the Docker container via `-e SAUCE_CONNECT_TIMEOUT_MS` and read by the `browser` fixture in `conftest.py`.

### Multi-browser cloud-grid matrix (PR #71)

The `cloud-grid` job is a 3-browser matrix (chromium, firefox, webkit). Each leg runs independently with `fail-fast: false` and `continue-on-error: true`.

**Per-browser status artifacts** written by each leg:

```text
artifacts/cloud-grid-chromium-status.json
artifacts/cloud-grid-firefox-status.json
artifacts/cloud-grid-webkit-status.json
```

Each file contains `{ "status": "PASS|FAIL|SKIPPED", "detail": "...", "browser": "...", "provider": "...", "timestamp": "..." }`. The `provider` field drives provider-aware header labels in `notify.py`.

**Artifact upload names** per leg: `cloud-grid-{browser}-execution-status`

The `notify` job downloads all three using a pattern download (`cloud-grid-*-execution-status` with `merge-multiple: true`) so all files land in `artifacts/` before `notify.py` runs.

**Aggregation logic** in `load_advisory_status()`:

| All legs | Aggregate |
|---|---|
| All PASS | PASS |
| All SKIPPED | SKIPPED |
| All FAIL or UNKNOWN | FAIL |
| Any FAIL, others PASS | PARTIAL |
| All UNKNOWN | UNKNOWN |
| Mixed (PASS + SKIPPED, etc.) | PARTIAL |

**Notification rendering:**

- PASS or SKIPPED → single summary line, no per-browser detail (clean output)
- PARTIAL or FAIL → per-browser detail lines with status and detail string

**Legacy fallback:** If no per-browser files exist but `artifacts/cloud-grid-status.json` does (produced by a pre-PR #71 run), `load_advisory_status()` reads it as the chromium result. This preserves backward compatibility during the transition window.

**Preflight runs once per matrix leg** (idempotent; fast enough to not justify a shared preflight job). Non-READY preflight states write a GitHub step summary line for both `SKIPPED_*` and `ERROR_*` states.

### Provider label rendering

`notify.py` reads the `provider` field from the first available cloud-grid status artifact and renders a human-readable label in the Advisory Jobs section:

| Artifact `provider` value | Notification header |
|---|---|
| `sauce` | `Cloud Grid (Sauce Labs)` |
| `browserstack` | `Cloud Grid (BrowserStack)` |
| empty or absent | `Cloud Grid` (backward compat with pre-PR #72 artifacts) |

### BrowserStack activation (ADR-036)

BrowserStack live cloud-grid execution is active as of PR #74 (ADR-036). When `CLOUD_GRID_PROVIDER=browserstack` is set and credentials are valid, the 3-browser smoke matrix runs against BrowserStack's Automate grid. Preflight hits `https://api.browserstack.com/automate/plan.json` with HTTP Basic auth to validate credentials before the smoke step executes.

BrowserStack is optional and account-dependent. This blueprint supports BrowserStack Automate through GitHub Actions secrets and provider selection. BrowserStack dashboard integrations such as Slack/GitHub are not required because CI reporting and notifications are handled by this repo.

**Required secrets** (Settings → Secrets and variables → Actions → Secrets tab):

| Secret | Purpose |
| --- | --- |
| `BROWSERSTACK_USERNAME` | BrowserStack account username |
| `BROWSERSTACK_ACCESS_KEY` | BrowserStack access key |

**Optional variable** (Settings → Secrets and variables → Actions → Variables tab):

| Variable | Default | Purpose |
| --- | --- | --- |
| `BROWSERSTACK_CONNECT_TIMEOUT_MS` | `60000` | Playwright remote connect timeout for BrowserStack sessions (ms) |

**Status outcomes:**

- Absent credentials → `SKIPPED_MISSING_CREDENTIALS` (exits 0)
- Credentials rejected by API → `SKIPPED_INVALID_CREDENTIALS` (exits 0)
- API unreachable → `SKIPPED_PROVIDER_UNAVAILABLE` (exits 0)
- Credentials valid → `READY` → smoke suite runs

Secret values are never printed, logged, or written to artifacts. The endpoint URL (which embeds credentials in the capabilities JSON) is also never logged.

For trial accounts, validate with `workflow_dispatch` first and switch `CLOUD_GRID_PROVIDER` back to `sauce` or `none` after proof is captured to avoid consuming trial minutes unintentionally.

**Dashboard status marking (ADR-037):** BrowserStack dashboard session status marking is best-effort and cosmetic. The repo may mark sessions passed/failed through the BrowserStack executor protocol (`browserstack_executor:` JS-evaluate convention) when `CLOUD_GRID_PROVIDER=browserstack`, but GitHub Actions, JUnit artifacts, release gate output, and Slack/Gmail notifications remain the authoritative reporting path. A marking failure is silently ignored and never affects test outcome or any required signal.

### Release Confidence line

The notification includes a `Release Confidence` line after `Overall Release Readiness`. It provides a plain-language interpretation of the combined CI + release gate + advisory signal:

| Confidence | Condition | Meaning |
| --- | --- | --- |
| 🟢 High | required CI passed, gate GO, advisory all PASS | Required CI and release gate passed; advisory checks are clean |
| 🟠 Low | required CI passed, gate NO_GO or advisory FAIL | Release gate or advisory signal failed; review before release |
| 🟡 Medium | required CI passed, signal limited/skipped/partial/unknown | Signal is incomplete; advisory or gate data not available |
| 🔴 Blocked | any required CI job not `success` | Fix required lane before release evaluation |

`compute_overall_readiness()` is unchanged. `Release Confidence` is display-only and has no effect on gate decisions.

---

### Per-run override via `workflow_dispatch` input

Manual CI runs (`workflow_dispatch`) support a `notification_mode` input that overrides `NOTIFY_DRY_RUN` for that specific run without changing the repo variable:

| `notification_mode` input | Effect |
|---|---|
| `repo_default` (default) | Uses `vars.NOTIFY_DRY_RUN` — preserves current behavior |
| `dry_run` | Forces `NOTIFY_DRY_RUN=true` for this run only |
| `live` | Clears `NOTIFY_DRY_RUN` for this run only — live delivery if secrets are configured |

The input is available only on `workflow_dispatch`. On `schedule` and `push` to `main`, `vars.NOTIFY_DRY_RUN` is always used. Missing secrets still prevent live delivery regardless of the input value — `notify.py` dry-runs per channel when required env vars are absent.

---

## Forced-Live Critical Alert Policy

**ADR:** [ADR-039](architecture_decision_log.md#adr-039-forced-live-critical-failure-alert-policy)

### Overview

Setting `NOTIFY_DRY_RUN=true` suppresses all live notification delivery. This is the correct default for noise control. However, a required-lane failure on push to `main` or a scheduled run is a genuine release-blocking event — silencing it defeats the purpose of having alerts.

The forced-live policy is a narrow override: when `NOTIFY_DRY_RUN=true` is active **and** a critical event is detected, `notify.py` overrides the dry-run flag and attempts live delivery to each configured channel.

### What counts as a critical event

All three conditions must hold simultaneously:

1. Running inside GitHub Actions (`GITHUB_ACTIONS=true` — auto-set in all steps, absent on local and Jenkins)
2. Trigger is `push` to `refs/heads/main` **or** `schedule` (nightly)
3. At least one required lane result is not `success` — `docker_test_suite`, `api_tests`, or `ui_tests`

Any non-empty value other than `"success"` qualifies: `failure`, `cancelled`, `skipped`, `timed_out`, or any other non-success string.

### Critical-event truth table

| Trigger | Required lane result | NOTIFY_DRY_RUN | Behavior |
|---|---|---|---|
| Push to `main` | Any required failure | `true` | Override → live delivery attempted |
| Push to `main` | All required success | `true` | Dry-run — no override |
| Scheduled run | Any required failure | `true` | Override → live delivery attempted |
| Scheduled run | All required success | `true` | Dry-run — no override |
| `workflow_dispatch` | Failure | `dry_run` | Dry-run — no override |
| `workflow_dispatch` | Failure | `live` | Live through existing behavior |
| `pull_request` | Failure | `true` | Dry-run — no override |
| Advisory-only failure | Required lane success | `true` | Dry-run — no override |
| Local / Jenkins | Any | `true` | Dry-run — no override (`GITHUB_ACTIONS` absent) |

### Effective dry-run precedence model

```
requested_dry_run  = is_dry_run_forced()                                    # reads NOTIFY_DRY_RUN
forced_live        = should_force_live_delivery(requested_dry_run, ci_status)
effective_dry_run  = requested_dry_run and not forced_live
```

`forced_live` is only ever `True` when `requested_dry_run` was `True`. When `NOTIFY_DRY_RUN` is already `false`, `forced_live` stays `False` — delivery is already live through existing behavior, and the alert banner is suppressed.

### Notification content when override applies

The first line of the notification becomes:

```
🚨 Critical Alert Policy: Live-delivery override applied — required release lane failed on main or scheduled run.
```

This line appears only when `forced_live=True`. Ordinary live notifications, `workflow_dispatch`, and dry-run paths never include it.

### Credential dependency

A forced-live override attempts delivery — it does not guarantee it. Each channel still requires its own credentials:

- **Slack:** `SLACK_WEBHOOK_URL` must be provisioned as a GitHub Actions secret
- **Email:** `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `NOTIFY_RECIPIENTS` must be set

When the override fires but a channel's credentials are absent, `notify.py` logs:

```
[CRITICAL] Slack: live-delivery override applied, but channel unavailable — SLACK_WEBHOOK_URL not configured
[CRITICAL] Email: live-delivery override applied, but channel unavailable — SMTP_HOST not configured
```

No credential values appear in these log lines — only variable names.

### Testing without intentional main failure

Unit tests in `test/scripts/test_notify_readiness.py` (TC-SCRIPT-080 through TC-SCRIPT-092) cover all policy branches using `monkeypatch.setenv` / `monkeypatch.delenv`. No intentional CI failure is needed to validate policy logic.

### Disabling the override

Two options:

1. **Remove the dry-run:** Set `NOTIFY_DRY_RUN` to `false` or delete the repo variable — live delivery is already active for all events; no override is needed or applied.
2. **Revert ADR-039:** Remove `is_critical_event()` and `should_force_live_delivery()` from `notify.py`, restore `is_dry_run_forced()` as the sole dry-run control — see ADR-039 rollback steps.

---

## Validating the Wiring

### Step 1 — Dry-run validation (no secrets required)

1. Go to **GitHub → Actions → CI → Run workflow**, select branch `main`, and click **Run workflow**.
2. Wait for `Docker Test Suite`, `API Tests`, and `UI Tests` to complete.
3. Open the `Notify` job and expand the **Deliver aggregate CI notification** step.

Expected output when no secrets are configured:

```text
[DRY RUN] Slack: SLACK_WEBHOOK_URL not set — skipping live delivery
[DRY RUN] Slack message preview:
  Overall Release Readiness: ✅ GO
  CI Status: ✅ All required jobs passed
    · Docker Test Suite: success
    · API Tests: success
    · UI Tests: success
  Release Gate (staging API): ✅ GO
  Tests: N passed, 0 failed, 0 skipped (N total, ...s)
  Run: https://github.com/.../actions/runs/...
[DRY RUN] Email: SMTP_HOST, SMTP_USER, SMTP_PASSWORD, NOTIFY_RECIPIENTS not set — skipping live delivery
[DRY RUN] Email would be sent to: NOTIFY_RECIPIENTS not set
[DRY RUN] Email body preview:
  Overall Release Readiness: ✅ GO
  CI Status: ✅ All required jobs passed
    · Docker Test Suite: success
    · API Tests: success
    · UI Tests: success
  Release Gate (staging API): ✅ GO
  Tests: N passed, 0 failed, 0 skipped (N total, ...s)
  Run: https://github.com/.../actions/runs/...
```

**What must not appear in logs:**

- Webhook URLs
- SMTP passwords or app passwords
- Recipient email addresses or recipient lists
- Auth tokens or secret values of any kind

### Step 2 — Live Slack validation

After adding `SLACK_WEBHOOK_URL` to GitHub Secrets:

1. Confirm `NOTIFY_DRY_RUN` is unset or `false` (check **Settings → Secrets and variables → Actions → Variables tab**).
2. Go to **GitHub → Actions → CI → Run workflow**, select branch `main`.
3. Set **Notification mode** to `live` and click **Run workflow**.
4. Open the `Notify` job and expand **Deliver aggregate CI notification**.

Expected in step logs: `Slack: delivered (HTTP 200)`

Expected in the Slack channel: a message with Overall Release Readiness, CI Status rows, Release Gate status, test counts, and a link to the CI run.

**What must not appear in logs:**

- Webhook URLs or any portion of `SLACK_WEBHOOK_URL`
- SMTP passwords, app passwords, or auth tokens
- Recipient email addresses

After confirming live delivery, you may set `NOTIFY_DRY_RUN=true` to revert to dry-run without removing the secret.

### Step 3 — PR failure notification validation

After confirming live Slack delivery (Step 2), validate the `NOTIFY_PR_FAILURES` gate:

1. Confirm `NOTIFY_PR_FAILURES=true` is set under **Settings → Secrets and variables → Actions → Variables tab**.
2. Confirm `SLACK_WEBHOOK_URL` is provisioned as a GitHub Actions secret (done in Step 2).
3. Confirm `NOTIFY_DRY_RUN` is unset or `false` so live Slack delivery is active.
4. Create a controlled failing PR — for example, introduce a Ruff lint violation or a deliberate test failure on a feature branch and open a PR to main.
5. Wait for the CI jobs to complete. Open the PR's **Checks** panel.
6. Confirm the `Notify` job appears in the PR CI panel. It must show as **advisory** — it must not appear in the list of required checks blocking merge.
7. Expand the `Notify` job → **Deliver aggregate CI notification** step.

Expected in step logs:
```text
Slack: delivered (HTTP 200)
```

Expected overall readiness in the Slack message:
```text
Overall Release Readiness: ❌ BLOCKED
CI Status: ❌ Required job(s) failed
  · <failing job name>: failure
```

8. Fix the PR (remove the lint error or revert the test change) and push. Confirm the CI jobs pass.
9. Confirm the `Notify` job does **not** appear or does not run on the clean PR run — clean PRs must remain silent.

**What must not appear in logs:**

- Webhook URLs or any portion of `SLACK_WEBHOOK_URL`
- SMTP passwords, app passwords, or auth tokens
- Recipient email addresses

After validating, you may optionally remove `NOTIFY_PR_FAILURES` from repo variables to revert to silent PR behavior.

### Step 4 — Live email validation

#### Required secrets and variables

Provision the following in **GitHub → Settings → Secrets and variables → Actions → Secrets tab** before running:

| Secret / Variable | Value |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` (first attempt); switch to `465` if 587 fails |
| `SMTP_USER` | Sending Gmail address |
| `SMTP_PASSWORD` | Gmail App Password — not the account password (see Gmail setup above) |
| `EMAIL_FROM` | Sending address or display name — optional; defaults to `SMTP_USER` |
| `NOTIFY_RECIPIENTS` | Recipient email address(es), comma-separated |
| `NOTIFY_DRY_RUN` | Must be **unset or `false`** in the Variables tab |

#### Running the first live test

1. Go to **GitHub → Actions → CI → Run workflow**, select the branch.
2. Set **Notification mode** to `live`.
3. Click **Run workflow** and wait for all jobs to complete.
4. Open the `Notify` job → expand **Deliver aggregate CI notification**.
5. Confirm no secrets appear in the logs (see "What must not appear" below).
6. Confirm the `Notify` job exits `0` regardless of email outcome.
7. Confirm Slack behavior is unchanged (dry-runs or delivers per existing config).

#### Expected diagnostic output

`notify.py` emits a transport-mode line before each attempt:

```text
Email: attempting delivery via STARTTLS on port 587
```

or, when port 465 is configured:

```text
Email: attempting delivery via SMTP_SSL on port 465
```

Followed by one of:

```text
Email: delivered to N recipient(s)
```

or:

```text
WARNING: Email delivery failed: <ExceptionClassName>
```

#### Classification table

| Log output | Classification | Next action |
|---|---|---|
| `Email: delivered to N recipient(s)` on port 587 | PASS — Gmail STARTTLS 587 works | Document result in ADR-027 |
| `Email: delivered to N recipient(s)` but message appears in Spam | PASS with deliverability caveat | Mark as not spam; document outcome in ADR-027 |
| `SMTPAuthenticationError` on any port | CONFIG — Gmail App Password issue | Verify App Password; 2-Step Verification must be on; retest |
| `gaierror` | CONFIG/DNS — SMTP host could not be resolved | Verify `SMTP_HOST` is exactly `smtp.gmail.com`; do not include protocol, port, quotes, or spaces; rerun 587 |
| `TimeoutError`, `ConnectionRefusedError`, or `SMTPConnectError` on port 587 | NETWORK — runner likely blocks 587 | Switch `SMTP_PORT` secret to `465` and rerun |
| `Email: delivered to N recipient(s)` on port 465 | PASS — Gmail SMTP_SSL 465 works | Document result in ADR-027 |
| Network/connect failure on both 587 and 465 | FAIL — GitHub-hosted runner blocks outbound SMTP | Recommend transactional email API in ADR-027 |

#### Validated outcome — Gmail STARTTLS 587

On 2026-06-14, Gmail SMTP delivery was validated from GitHub Actions using STARTTLS on port `587`.

Observed result:

- Slack delivered with HTTP 200.
- Email attempted delivery via STARTTLS on port `587`.
- Email delivered to one recipient.
- Gmail placed the message in Spam.
- Notify job succeeded.
- No secrets appeared in logs.

Classification: **PASS — Gmail STARTTLS 587 works, with Spam-placement caveat.**

During first-time setup, check Spam and mark the message as **Not spam** if Gmail classifies the automation email incorrectly.

See ADR-027 for the full decision record.

#### What must not appear in logs

- `SMTP_PASSWORD` or App Password value
- `SLACK_WEBHOOK_URL` or any portion of the webhook URL
- `SMTP_USER` address or `NOTIFY_RECIPIENTS` addresses
- Full SMTP server error messages (exception class name only is logged)

#### Safety notes

- Do not paste secrets, App Passwords, or recipient addresses into PRs, issues, screenshots, logs, or documentation.
- Email remains advisory — `notify.py` returns `0` even when delivery fails.
- Slack remains the primary validated live channel until email is confirmed working.
- If both SMTP ports fail due to runner restrictions, do not retry blindly. Document the outcome in ADR-027 and evaluate a transactional email API in a separate PR with a separate Mode A review.

#### ADR-027

See [ADR-027 in architecture_decision_log.md](architecture_decision_log.md#adr-027-gmail-smtp-live-delivery-validation-outcome) for the full live validation decision record.

### Reverting to dry-run

Set `NOTIFY_DRY_RUN` to `true` in **Settings → Secrets and variables → Actions → Variables tab**. Live delivery stops on the next run without removing any secrets.

---

## Secret Hygiene

Store all notification credentials only in **GitHub → Settings → Secrets and variables → Actions → Secrets tab**.

Never store credentials in:

- `.env` files
- markdown or governance docs (including this file)
- JSON data files
- screenshots
- source code or inline comments
- CI artifact files (`release-readiness.json`, HTML reports, or step summaries)

If a credential is accidentally committed: rotate it immediately (generate a new Slack webhook URL or a new Gmail App Password), update the GitHub secret, then remove the old value from git history.

For the committed credential policy and rotation guidance, see [security_and_branch_protection.md — Committed credential policy](security_and_branch_protection.md).

If GitHub secret scanning and push protection are enabled (**Settings → Code security and analysis**), GitHub will alert on detected credential patterns and block pushes before secrets reach the remote.

---

## References

- [`scripts/notify.py`](../../scripts/notify.py) — notification script implementation
- [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) — `notify` job; artifact upload step in `api` job
- [`quality_gates.md`](quality_gates.md) — Notification Delivery section; CI job structure table
- [`security_and_branch_protection.md`](security_and_branch_protection.md) — Notification secrets section
- [`architecture_decision_log.md` — ADR-024](architecture_decision_log.md#adr-024-pr-failure-notifications-behind-notify_pr_failures-activation-gate)
- [`architecture_decision_log.md` — ADR-018](architecture_decision_log.md#adr-018-failure-only-aggregate-notification-on-push-to-main)
- [`architecture_decision_log.md` — ADR-016](architecture_decision_log.md#adr-016-aggregate-ci-notification-job-after-all-required-jobs-complete)
- [`architecture_decision_log.md` — ADR-011](architecture_decision_log.md#adr-011-notification-delivery-defaults-to-dry-run-when-secrets-are-absent)
