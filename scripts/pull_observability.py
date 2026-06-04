#!/usr/bin/env python3
"""Pull observability metrics and write data/release/observability_snapshot.json.

IMPORTANT: This script must remain stdlib-only. It may run directly on the GitHub
Actions runner without a Docker build or pip install. Adding non-stdlib imports will
break activation unless the CI step is updated to install dependencies.

STUB: No real API calls are made. Each provider's fetch function documents the
API interface it would use. Replace the stub body with real calls when connecting
to a live observability stack.

Supported providers (OBSERVABILITY_PROVIDER env var):
  manual     — reloads existing static file with refreshed timestamp (default)
  datadog    — Datadog Metrics API V2 (timeseries query + incident count)
  grafana    — Grafana HTTP API (dashboard panel queries)
  pagerduty  — PagerDuty Incidents API (recent incident count)

Required env vars per provider:
  datadog:   DATADOG_API_KEY, DATADOG_APP_KEY
             Optional: DATADOG_SITE (default: datadoghq.com)
  grafana:   GRAFANA_URL, GRAFANA_API_KEY, GRAFANA_DASHBOARD_UID
  pagerduty: PAGERDUTY_API_KEY, PAGERDUTY_SERVICE_ID

Optional:
  OBSERVABILITY_ENVIRONMENT   staging | prod_read_only (default: staging)
  OBSERVABILITY_WRITE         true | 1  → write snapshot to disk (default: preview only)
                               For non-manual providers, credentials must also be present.
                               Setting this flag without credentials still results in dry-run.
  OBSERVABILITY_SNAPSHOT_PATH output file path override
                               (default: data/release/observability_snapshot.json)
                               WARNING: must match the path read by scripts/release_gate.py,
                               which reads data/release/observability_snapshot.json by a
                               hardcoded path constant. Override only if release_gate.py is
                               updated to read the same path.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SNAPSHOT_PATH = Path("data/release/observability_snapshot.json")
KNOWN_PROVIDERS = ("manual", "datadog", "grafana", "pagerduty")

_PROVIDER_CREDENTIALS: dict[str, list[str]] = {
    "manual": [],
    "datadog": ["DATADOG_API_KEY", "DATADOG_APP_KEY"],
    "grafana": ["GRAFANA_URL", "GRAFANA_API_KEY", "GRAFANA_DASHBOARD_UID"],
    "pagerduty": ["PAGERDUTY_API_KEY", "PAGERDUTY_SERVICE_ID"],
}

_SAMPLE_METRICS: dict[str, object] = {
    "production_error_rate_pct": 0.3,
    "p95_latency_ms": 210,
    "p99_latency_ms": 450,
    "recent_incident_count": 0,
}

_SAMPLE_THRESHOLDS: dict[str, object] = {
    "max_error_rate_pct": 1.0,
    "max_p95_latency_ms": 500,
    "max_p99_latency_ms": 800,
    "max_recent_incident_count": 0,
}


def get_provider() -> str:
    provider = os.environ.get("OBSERVABILITY_PROVIDER", "manual").strip().lower()
    if provider not in KNOWN_PROVIDERS:
        providers_str = ", ".join(KNOWN_PROVIDERS)
        print(
            f'WARNING: unknown provider "{provider}". Valid providers: {providers_str}'
        )
        print("No snapshot generated.")
        return ""
    return provider


def check_credentials(provider: str) -> list[str]:
    required = _PROVIDER_CREDENTIALS.get(provider, [])
    return [name for name in required if not os.environ.get(name, "").strip()]


def fetch_manual(env: str) -> dict[str, dict]:  # type: ignore[type-arg]
    try:
        data = json.loads(DEFAULT_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        print(
            f"WARNING: could not load existing snapshot ({exc}) — using sample values"
        )
        return {
            "metrics": dict(_SAMPLE_METRICS),
            "thresholds": dict(_SAMPLE_THRESHOLDS),
        }
    return {
        "metrics": dict(data.get("metrics", _SAMPLE_METRICS)),
        "thresholds": dict(data.get("thresholds", _SAMPLE_THRESHOLDS)),
    }


def fetch_datadog(env: str) -> dict[str, dict]:  # type: ignore[type-arg]
    print(
        "[STUB] Datadog: would call POST https://<datadog-site>/api/v2/query/timeseries"
    )
    return {"metrics": dict(_SAMPLE_METRICS), "thresholds": dict(_SAMPLE_THRESHOLDS)}


def fetch_grafana(env: str) -> dict[str, dict]:  # type: ignore[type-arg]
    print(
        "[STUB] Grafana: would call GET"
        " https://<grafana-host>/api/dashboards/uid/<dashboard-uid>"
    )
    return {"metrics": dict(_SAMPLE_METRICS), "thresholds": dict(_SAMPLE_THRESHOLDS)}


def fetch_pagerduty(env: str) -> dict[str, dict]:  # type: ignore[type-arg]
    print(
        "[STUB] PagerDuty: would call GET"
        " https://api.pagerduty.com/incidents?service_ids[]=<service-id>"
    )
    return {"metrics": dict(_SAMPLE_METRICS), "thresholds": dict(_SAMPLE_THRESHOLDS)}


def build_snapshot(
    metrics: dict,  # type: ignore[type-arg]
    thresholds: dict,  # type: ignore[type-arg]
    env: str,
    source: str,
) -> dict:  # type: ignore[type-arg]
    return {
        "_note": (
            "In production this file is generated by scripts/pull_observability.py which calls"
            " the Datadog/Grafana/PagerDuty API. Values here are representative sample blueprint"
            " inputs — not live production data."
        ),
        "snapshot_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "environment": env,
        "source": source,
        "metrics": metrics,
        "thresholds": thresholds,
    }


def print_preview(snapshot: dict) -> None:  # type: ignore[type-arg]
    metrics = snapshot.get("metrics", {})
    print("[DRY RUN] Snapshot preview:")
    print(f"  environment: {snapshot.get('environment', '')}")
    print(f"  source: {snapshot.get('source', '')}")
    for key, value in metrics.items():
        print(f"  metrics.{key}: {value}")


def main() -> int:
    provider = get_provider()
    if not provider:
        return 0

    env = os.environ.get("OBSERVABILITY_ENVIRONMENT", "staging")
    print(f"[STUB] pull_observability.py — provider: {provider}")

    _fetchers = {
        "manual": fetch_manual,
        "datadog": fetch_datadog,
        "grafana": fetch_grafana,
        "pagerduty": fetch_pagerduty,
    }
    _source_map = {
        "manual": "manual_sample",
        "datadog": "datadog_stub",
        "grafana": "grafana_stub",
        "pagerduty": "pagerduty_stub",
    }

    result = _fetchers[provider](env)
    snapshot = build_snapshot(
        result["metrics"], result["thresholds"], env, _source_map[provider]
    )

    write_requested = os.environ.get("OBSERVABILITY_WRITE", "").strip().lower() in (
        "true",
        "1",
    )
    missing_creds = check_credentials(provider)

    if write_requested and not missing_creds:
        snapshot_path = Path(
            os.environ.get("OBSERVABILITY_SNAPSHOT_PATH", str(DEFAULT_SNAPSHOT_PATH))
        )
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(
            json.dumps(snapshot, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Snapshot written to {snapshot_path}")
    else:
        if write_requested and missing_creds:
            missing_str = ", ".join(missing_creds)
            print(f"[DRY RUN] {missing_str} not set — skipping write")
        print_preview(snapshot)

    return 0


if __name__ == "__main__":
    sys.exit(main())
