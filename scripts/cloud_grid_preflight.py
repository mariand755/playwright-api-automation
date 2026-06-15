#!/usr/bin/env python3
"""Cloud-grid credential preflight check.

Validates whether a cloud browser-grid provider is configured and reachable before
any cloud-grid execution step attempts to use it. The script always exits 0 for
missing, invalid, or unreachable credentials — CI must never fail due to absent
secrets. It exits 1 only for repository configuration bugs (unknown provider value).

Environment variables:
  CLOUD_GRID_PROVIDER   Provider name (default: none). Supported: none, sauce.
  SAUCE_USERNAME        Sauce Labs username (required when provider=sauce).
  SAUCE_ACCESS_KEY      Sauce Labs access key (required when provider=sauce).
  SAUCE_REGION          Sauce Labs region (default: us-west-1).

Output artifacts:
  artifacts/cloud-grid-preflight.json   Machine-readable preflight result.
  artifacts/cloud-grid-preflight.md     Human-readable summary (appended to step summary in CI).

Security: credential values are never printed, logged, or written to artifacts.
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STATUS_READY = "READY"
STATUS_SKIPPED_NOT_CONFIGURED = "SKIPPED_NOT_CONFIGURED"
STATUS_SKIPPED_MISSING_CREDENTIALS = "SKIPPED_MISSING_CREDENTIALS"
STATUS_SKIPPED_INVALID_CREDENTIALS = "SKIPPED_INVALID_CREDENTIALS"
STATUS_PROVIDER_UNAVAILABLE = "SKIPPED_PROVIDER_UNAVAILABLE"

ARTIFACTS_DIR = Path("artifacts")
PREFLIGHT_JSON = ARTIFACTS_DIR / "cloud-grid-preflight.json"
PREFLIGHT_MD = ARTIFACTS_DIR / "cloud-grid-preflight.md"
HTTP_TIMEOUT = 10


def _write_artifacts(provider: str, status: str, message: str) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "provider": provider,
        "status": status,
        "message": message,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    PREFLIGHT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    skipped = status.startswith("SKIPPED_")
    icon = "✅" if status == STATUS_READY else "⏭️" if skipped else "❌"
    md_lines = [
        "## Cloud-Grid Preflight",
        "",
        f"{icon} **{status}**",
        "",
        f"Provider: `{provider}`",
        "",
        f"> {message}",
        "",
    ]
    PREFLIGHT_MD.write_text("\n".join(md_lines), encoding="utf-8")


def _check_sauce(username: str, access_key: str, region: str) -> tuple[str, str]:
    url = f"https://api.{region}.saucelabs.com/rest/v1/users/{username}"
    token = base64.b64encode(f"{username}:{access_key}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {token}"})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            if resp.status == 200:
                return (
                    STATUS_READY,
                    "Sauce Labs credentials are valid and the API is reachable.",
                )
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return (
                STATUS_SKIPPED_INVALID_CREDENTIALS,
                "Sauce Labs credentials were rejected by the API. "
                "Verify SAUCE_USERNAME and SAUCE_ACCESS_KEY.",
            )
        return (
            STATUS_PROVIDER_UNAVAILABLE,
            f"Sauce Labs API returned an unexpected HTTP error: {type(exc).__name__}.",
        )
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return (
            STATUS_PROVIDER_UNAVAILABLE,
            f"Sauce Labs API is unreachable: {type(exc).__name__}.",
        )
    return (
        STATUS_PROVIDER_UNAVAILABLE,
        "Sauce Labs API returned an unexpected response.",
    )


def run() -> int:
    provider = os.environ.get("CLOUD_GRID_PROVIDER", "none").strip().lower()

    if provider == "none":
        msg = (
            "CLOUD_GRID_PROVIDER is not set or is 'none'. "
            "Set CLOUD_GRID_PROVIDER=sauce (and required secrets) to enable cloud-grid execution."
        )
        _write_artifacts(provider, STATUS_SKIPPED_NOT_CONFIGURED, msg)
        print(f"[cloud-grid-preflight] {STATUS_SKIPPED_NOT_CONFIGURED}: {msg}")
        return 0

    if provider == "sauce":
        username = os.environ.get("SAUCE_USERNAME", "").strip()
        access_key = os.environ.get("SAUCE_ACCESS_KEY", "").strip()
        if not username or not access_key:
            msg = "SAUCE_USERNAME or SAUCE_ACCESS_KEY is not set."
            _write_artifacts(provider, STATUS_SKIPPED_MISSING_CREDENTIALS, msg)
            print(f"[cloud-grid-preflight] {STATUS_SKIPPED_MISSING_CREDENTIALS}: {msg}")
            return 0
        region = os.environ.get("SAUCE_REGION", "us-west-1").strip()
        status, msg = _check_sauce(username, access_key, region)
        _write_artifacts(provider, status, msg)
        print(f"[cloud-grid-preflight] {status}: {msg}")
        return 0

    msg = (
        f"Unknown CLOUD_GRID_PROVIDER value: '{provider}'. "
        "Supported values: none, sauce. This is a repository configuration error."
    )
    print(f"[cloud-grid-preflight] ERROR: {msg}", file=sys.stderr)
    _write_artifacts(provider, "ERROR_UNKNOWN_PROVIDER", msg)
    return 1


if __name__ == "__main__":
    sys.exit(run())
