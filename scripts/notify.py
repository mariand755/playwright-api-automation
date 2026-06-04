#!/usr/bin/env python3
"""Deliver release readiness notification to Slack and/or email.

IMPORTANT: This script must remain stdlib-only. It runs directly on the GitHub Actions runner
in the `notify` job without a Docker build or pip install. Adding non-stdlib imports will break
CI unless the notify job is updated to install dependencies or run inside Docker.

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

CI job result env vars (set by the notify job via needs.*.result):
  DOCKER_TEST_SUITE_RESULT  Result of the Docker Test Suite job
  API_TESTS_RESULT          Result of the API Tests job
  UI_TESTS_RESULT           Result of the UI Tests job

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


def get_ci_status() -> dict[str, str]:
    return {
        "docker_test_suite": os.environ.get("DOCKER_TEST_SUITE_RESULT", ""),
        "api_tests": os.environ.get("API_TESTS_RESULT", ""),
        "ui_tests": os.environ.get("UI_TESTS_RESULT", ""),
    }


def compute_overall_readiness(
    ci_status: dict[str, str], gate_decision: str | None
) -> str:
    required = ["docker_test_suite", "api_tests", "ui_tests"]
    # Any result that is not exactly "success" is treated as BLOCKED —
    # failure, cancelled, skipped, or any unknown/non-success value is unsafe for release.
    # Empty string means the env var was not set (local run); skip those to preserve
    # backward-compatible behavior when running without CI context.
    if any(v and v != "success" for v in (ci_status.get(k, "") for k in required)):
        return "BLOCKED"
    if gate_decision == "GO":
        return "GO"
    if gate_decision == "NO_GO":
        return "NO_GO"
    return "UNKNOWN"


def build_message_lines(
    data: dict[str, object] | None,
    run_url: str,
    ci_status: dict[str, str],
) -> list[str]:
    """Build channel-agnostic message lines including overall CI status and release gate."""
    gate_decision = str(data.get("overall_decision", "")) if data is not None else None
    overall = compute_overall_readiness(ci_status, gate_decision)
    _overall_emoji = {"GO": "✅", "NO_GO": "❌"}
    overall_emoji = _overall_emoji.get(overall, "⚠️")

    lines: list[str] = [f"Overall Release Readiness: {overall_emoji} {overall}"]

    job_labels = [
        ("docker_test_suite", "Docker Test Suite"),
        ("api_tests", "API Tests"),
        ("ui_tests", "UI Tests"),
    ]
    non_empty = [
        (label, ci_status.get(key, ""))
        for key, label in job_labels
        if ci_status.get(key, "")
    ]
    if non_empty:
        all_success = all(result == "success" for _, result in non_empty)
        ci_emoji = "✅" if all_success else "❌"
        ci_label = (
            "All required jobs passed" if all_success else "Failed job(s) detected"
        )
        lines.append(f"CI Status: {ci_emoji} {ci_label}")
        for label, result in non_empty:
            lines.append(f"  · {label}: {result}")

    if data is None:
        lines.append(
            "Release Gate: ⚠️ No release gate data (gate did not run or api job failed)"
        )
    else:
        gate_str = str(data.get("overall_decision", "UNKNOWN"))
        gate_emoji = "✅" if gate_str == "GO" else "❌"
        gate_line = f"Release Gate (staging API): {gate_emoji} {gate_str}"
        if overall == "BLOCKED" and gate_str == "GO":
            gate_line += " — component signal only; overall readiness is BLOCKED"
        lines.append(gate_line)

        tr = data.get("test_results", {})
        if isinstance(tr, dict):
            total = tr.get("total", "?")
            passed = tr.get("passed", "?")
            failed = tr.get("failed", "?")
            skipped = tr.get("skipped", "?")
            duration = tr.get("duration_secs", "?")
        else:
            total = passed = failed = skipped = duration = "?"

        lines.append(
            f"Tests: {passed} passed, {failed} failed, {skipped} skipped"
            f" ({total} total, {duration}s)"
        )

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


def send_slack(
    data: dict[str, object] | None,
    run_url: str,
    dry_run_forced: bool,
    ci_status: dict[str, str],
) -> bool:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    lines = build_message_lines(data, run_url, ci_status)

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
    data: dict[str, object] | None,
    run_url: str,
    dry_run_forced: bool,
    ci_status: dict[str, str],
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

    lines = build_message_lines(data, run_url, ci_status)

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

    gate_decision = str(data.get("overall_decision", "")) if data is not None else None
    overall = compute_overall_readiness(ci_status, gate_decision)
    emoji = {"GO": "✅", "NO_GO": "❌"}.get(overall, "⚠️")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    subject_suffix = f" — {repo}" if repo else ""
    subject = f"Release Readiness: {emoji} {overall}{subject_suffix}"

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
    ci_status = get_ci_status()

    if data is None:
        print(
            f"WARNING: {ARTIFACT_JSON} not found or unreadable"
            " — release gate data unavailable"
        )

    slack_ok = send_slack(data, run_url, dry_run_forced, ci_status)
    email_ok = send_email(data, run_url, dry_run_forced, ci_status)

    if not slack_ok or not email_ok:
        print("WARNING: one or more notification channels failed — see above")

    return 0


if __name__ == "__main__":
    sys.exit(main())
