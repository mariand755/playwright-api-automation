# Notification Wiring Guide

## Overview

The notification step in CI reads `artifacts/release-readiness.json` after the release readiness gate runs and delivers the GO/NO_GO decision, test counts, gate failures, and warnings to Slack and email.

**When it runs:** `schedule` (nightly) and `workflow_dispatch` (manual) triggers only — not on push or pull request.

**Dry-run default:** each channel checks its own required environment variables independently. When a channel's required variables are absent, it logs a message preview and continues without failing CI.

**Channel independence:** Slack and email operate independently. Slack can deliver live while email dry-runs, and vice versa.

**Implementation:** `scripts/notify.py` — stdlib only; zero new Python dependencies.

For the architectural decision record, see [ADR-011 in architecture_decision_log.md](architecture_decision_log.md#adr-011-notification-delivery-defaults-to-dry-run-when-secrets-are-absent).

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

**Important:** if `NOTIFY_DRY_RUN` is added under **Secrets** instead of **Variables**, the workflow's `${{ vars.NOTIFY_DRY_RUN }}` reference reads from the wrong namespace and resolves to an empty string. The flag silently has no effect.

---

## Validating the Wiring

### Step 1 — Dry-run validation (no secrets required)

1. Go to **GitHub → Actions → CI → Run workflow**, select branch `main`, and click **Run workflow**.
2. Wait for the `API Tests` job to complete.
3. Open the `API Tests` job and expand the **Deliver release readiness notification** step.

Expected output when no secrets are configured:

```text
[DRY RUN] Slack: SLACK_WEBHOOK_URL not set — skipping live delivery
[DRY RUN] Slack message preview:
  Release Readiness: ✅ GO
  Tests: N passed, 0 failed, 0 skipped (N total, ...s)
  Run: https://github.com/.../actions/runs/...
[DRY RUN] Email: SMTP_HOST, SMTP_USER, SMTP_PASSWORD, NOTIFY_RECIPIENTS not set — skipping live delivery
[DRY RUN] Email would be sent to: NOTIFY_RECIPIENTS not set
[DRY RUN] Email body preview:
  Release Readiness: ✅ GO
  Tests: N passed, 0 failed, 0 skipped (N total, ...s)
  Run: https://github.com/.../actions/runs/...
```

**What must not appear in logs:**

- Webhook URLs
- SMTP passwords or app passwords
- Recipient email addresses or recipient lists
- Auth tokens or secret values of any kind

### Step 2 — Optional live Slack validation

After adding `SLACK_WEBHOOK_URL` to GitHub Secrets:

1. Confirm `NOTIFY_DRY_RUN` is unset or `false` (check **Settings → Secrets and variables → Actions → Variables tab**).
2. Trigger a `workflow_dispatch` run on `main`.
3. Open the `API Tests` job and expand **Deliver release readiness notification**.

Expected in step logs: `Slack: delivered (HTTP 200)`

Expected in the Slack channel: a message with the release readiness status and a link to the CI run.

### Step 3 — Optional live email validation

After adding all SMTP secrets and `NOTIFY_RECIPIENTS`:

1. Confirm `NOTIFY_DRY_RUN` is unset or `false`.
2. Trigger a `workflow_dispatch` run on `main`.
3. Open the `API Tests` job and expand **Deliver release readiness notification**.

Expected in step logs: `Email: delivered to N recipient(s)`

Expected in the recipient inbox: an email with subject `Release Readiness: ✅ GO — <repository-name>`.

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
- [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) — API Tests job, Deliver release readiness notification step
- [`quality_gates.md`](quality_gates.md) — Notification Delivery section
- [`security_and_branch_protection.md`](security_and_branch_protection.md) — Notification secrets section
- [`architecture_decision_log.md` — ADR-011](architecture_decision_log.md#adr-011-notification-delivery-defaults-to-dry-run-when-secrets-are-absent)
