#!/usr/bin/env python3
"""Deliver release readiness notification to Slack and/or email.

Dry-runs when required env vars are absent or when NOTIFY_DRY_RUN is set.
CI never fails due to missing credentials — each channel dry-runs independently.

Required env vars per channel:
  Slack:  SLACK_WEBHOOK_URL
  Email:  SMTP_HOST, SMTP_USER, SMTP_PASSWORD, NOTIFY_RECIPIENTS

Optional env vars:
  SMTP_PORT       SMTP port (default: 587; use 465 for SMTP_SSL)
  EMAIL_FROM      Sender address (defaults to SMTP_USER if not set)
  NOTIFY_DRY_RUN  Set to 'true' or '1' to force dry-run for all channels

GitHub Actions env vars (auto-set, used to construct the run URL):
  GITHUB_SERVER_URL, GITHUB_REPOSITORY, GITHUB_RUN_ID

Gmail example configuration:
  SMTP_HOST=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USER=your.address@gmail.com
  SMTP_PASSWORD=<Gmail App Password — not your Google account password>
  NOTIFY_RECIPIENTS=recipient@example.com,another@example.com
"""

import json
import os
import smtplib
import socket
import ssl
import sys
import urllib.error
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

ARTIFACT_JSON = Path("artifacts/release-readiness.json")
MAX_ITEMS_IN_MESSAGE = 3
NETWORK_TIMEOUT = 10  # seconds


def get_run_url() -> str:
    server = os.environ.get("GITHUB_SERVER_URL", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    if server and repo and run_id:
        return f"{server}/{repo}/actions/runs/{run_id}"
    return ""


def load_release_data() -> dict[str, object] | None:
    if not ARTIFACT_JSON.exists():
        return None
    try:
        data = json.loads(ARTIFACT_JSON.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data  # type: ignore[return-value]
        return None
    except (json.JSONDecodeError, OSError):
        return None


def is_dry_run_forced() -> bool:
    return os.environ.get("NOTIFY_DRY_RUN", "").strip().lower() in ("true", "1")


def build_message_lines(data: dict[str, object], run_url: str) -> list[str]:
    """Build channel-agnostic message lines from release gate data."""
    decision = str(data.get("overall_decision", "UNKNOWN"))
    emoji = "✅" if decision == "GO" else "❌"

    tr = data.get("test_results", {})
    if isinstance(tr, dict):
        total = tr.get("total", "?")
        passed = tr.get("passed", "?")
        failed = tr.get("failed", "?")
        skipped = tr.get("skipped", "?")
        duration = tr.get("duration_secs", "?")
    else:
        total = passed = failed = skipped = duration = "?"

    lines: list[str] = [
        f"Release Readiness: {emoji} {decision}",
        f"Tests: {passed} passed, {failed} failed, {skipped} skipped"
        f" ({total} total, {duration}s)",
    ]

    gate_failures = data.get("gate_failures", [])
    if isinstance(gate_failures, list) and gate_failures:
        lines.append("Gate failures:")
        for item in gate_failures[:MAX_ITEMS_IN_MESSAGE]:
            lines.append(f"  - {item}")
        remaining = len(gate_failures) - MAX_ITEMS_IN_MESSAGE
        if remaining > 0:
            lines.append(f"  ... and {remaining} more")

    warnings = data.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        lines.append("Warnings:")
        for item in warnings[:MAX_ITEMS_IN_MESSAGE]:
            lines.append(f"  - {item}")
        remaining = len(warnings) - MAX_ITEMS_IN_MESSAGE
        if remaining > 0:
            lines.append(f"  ... and {remaining} more")

    if run_url:
        lines.append(f"Run: {run_url}")

    return lines


def _fallback_message_lines(run_url: str) -> list[str]:
    lines = [
        "Release Readiness: ⚠️ UNKNOWN",
        f"{ARTIFACT_JSON} not found or unreadable.",
        "The release gate may not have run or failed before producing output.",
    ]
    if run_url:
        lines.append(f"Run: {run_url}")
    return lines


def send_slack(
    data: dict[str, object] | None, run_url: str, dry_run_forced: bool
) -> bool:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")

    lines = (
        build_message_lines(data, run_url)
        if data is not None
        else _fallback_message_lines(run_url)
    )

    if dry_run_forced or not webhook_url:
        if dry_run_forced and webhook_url:
            print("[DRY RUN] Slack: NOTIFY_DRY_RUN is set — skipping live delivery")
        else:
            print("[DRY RUN] Slack: SLACK_WEBHOOK_URL not set — skipping live delivery")
        print("[DRY RUN] Slack message preview:")
        for line in lines:
            print(f"  {line}")
        return True

    text = "\n".join(lines)
    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=NETWORK_TIMEOUT) as resp:
            status_code = resp.status
        print(f"Slack: delivered (HTTP {status_code})")
        return True
    except urllib.error.HTTPError as exc:
        print(f"WARNING: Slack delivery failed: {type(exc).__name__} HTTP {exc.code}")
        return False
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"WARNING: Slack delivery failed: {type(exc).__name__}")
        return False


def send_email(
    data: dict[str, object] | None, run_url: str, dry_run_forced: bool
) -> bool:
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port_str = os.environ.get("SMTP_PORT", "587")
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    email_from = os.environ.get("EMAIL_FROM", "") or smtp_user
    recipients_str = os.environ.get("NOTIFY_RECIPIENTS", "")

    required_missing: list[str] = []
    if not smtp_host:
        required_missing.append("SMTP_HOST")
    if not smtp_user:
        required_missing.append("SMTP_USER")
    if not smtp_password:
        required_missing.append("SMTP_PASSWORD")
    if not recipients_str:
        required_missing.append("NOTIFY_RECIPIENTS")

    lines = (
        build_message_lines(data, run_url)
        if data is not None
        else _fallback_message_lines(run_url)
    )

    if dry_run_forced or required_missing:
        if dry_run_forced and not required_missing:
            print("[DRY RUN] Email: NOTIFY_DRY_RUN is set — skipping live delivery")
        else:
            missing_str = ", ".join(required_missing)
            print(f"[DRY RUN] Email: {missing_str} not set — skipping live delivery")
        recipients_status = "configured" if recipients_str else "not set"
        print(
            f"[DRY RUN] Email would be sent to: NOTIFY_RECIPIENTS {recipients_status}"
        )
        print("[DRY RUN] Email body preview:")
        for line in lines:
            print(f"  {line}")
        return True

    recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]
    if not recipients:
        print("WARNING: NOTIFY_RECIPIENTS contains no valid addresses — skipping email")
        return True

    try:
        port = int(smtp_port_str)
    except ValueError:
        print("WARNING: SMTP_PORT is not a valid integer — skipping email")
        return False

    decision = str((data or {}).get("overall_decision", "UNKNOWN"))
    emoji = "✅" if decision == "GO" else "❌"
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    subject_suffix = f" — {repo}" if repo else ""
    subject = f"Release Readiness: {emoji} {decision}{subject_suffix}"

    body_text = "\n".join(lines)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(body_text, "plain"))

    context = ssl.create_default_context()
    try:
        if port == 465:
            with smtplib.SMTP_SSL(
                smtp_host, port, context=context, timeout=NETWORK_TIMEOUT
            ) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(email_from, recipients, msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, port, timeout=NETWORK_TIMEOUT) as server:
                server.starttls(context=context)
                server.login(smtp_user, smtp_password)
                server.sendmail(email_from, recipients, msg.as_string())
        print(f"Email: delivered to {len(recipients)} recipient(s)")
        return True
    except (smtplib.SMTPException, TimeoutError, OSError, socket.timeout) as exc:
        print(f"WARNING: Email delivery failed: {type(exc).__name__}")
        return False


def main() -> int:
    data = load_release_data()
    run_url = get_run_url()
    dry_run_forced = is_dry_run_forced()

    if data is None:
        print(
            f"WARNING: {ARTIFACT_JSON} not found or unreadable"
            " — sending fallback notification"
        )

    slack_ok = send_slack(data, run_url, dry_run_forced)
    email_ok = send_email(data, run_url, dry_run_forced)

    if not slack_ok or not email_ok:
        print("WARNING: one or more notification channels failed — see above")

    return 0


if __name__ == "__main__":
    sys.exit(main())
