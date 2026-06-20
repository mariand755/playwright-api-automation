# Observability Release-Signal Contract

## Purpose

This document defines the provider-neutral contract that the observability adapter layer (`scripts/pull_observability.py`) must satisfy before the release gate (`scripts/release_gate.py`) can consume live data. It separates current stub reality from the target live-data contract and specifies the canonical schema that any Datadog, Grafana, or PagerDuty implementation must normalize into.

This document does not describe API endpoints, provider-specific credentials, or CI activation steps. See [`observability_wiring.md`](observability_wiring.md) for those details.

---

## Current State vs. Target State

| Dimension | Current state | Target state |
|---|---|---|
| Data source | Static sample in `data/release/observability_snapshot.json` | Live pull via `pull_observability.py` before each gate run |
| Freshness check | None — any file passes regardless of `snapshot_timestamp` age | Gate must enforce a maximum allowed age on `snapshot_timestamp` |
| Data status | `data_status` field not present in snapshot | `data_status` required; gate must handle `complete`, `partial`, `stale`, `missing` |
| Provider normalization | Stub emits identical sample values regardless of provider | Each provider's response normalized to the canonical schema below |
| Exception hygiene | Current stub may include exception text when loading the local sample fails | Live implementation must emit only `type(exc).__name__` — never raw exception text or provider response content |

---

## Canonical Release-Signal Schema

All fields in the snapshot that `scripts/release_gate.py` consumes or must consume after live activation.

### Mandatory fields (present in the current stub)

| Field | Type | Notes |
|---|---|---|
| `environment` | string | Environment label; matches `OBSERVABILITY_ENVIRONMENT` variable |
| `source` | string | Current stub values: `manual_sample`, `datadog_stub`, `grafana_stub`, `pagerduty_stub`. A live implementation must emit a truthful provider-specific identifier such as `datadog_live`. |
| `snapshot_timestamp` | ISO-8601 UTC string | When the snapshot was written. Present in the current stub. Future gate activation must enforce a maximum allowed age — see [Freshness override](#freshness-override) below. |
| `metrics.production_error_rate_pct` | float | Current error rate as a percentage |
| `metrics.p95_latency_ms` | int | 95th-percentile response latency in milliseconds |
| `metrics.p99_latency_ms` | int | 99th-percentile response latency in milliseconds |
| `metrics.recent_incident_count` | int | Open or recent incidents in the collection window |
| `thresholds.*` | numeric | Gate pass/fail limits consumed by `release_gate.py`; already present in the snapshot |

### Activation-required fields (not yet present in stub or enforced by gate)

| Field | Type | Notes |
|---|---|---|
| `time_window_minutes` | int | Metric aggregation window used by the provider query. Required so the gate can assess whether the window is appropriate for the deployment cadence. |
| `data_status` | enum | `complete` — all fields present and fresh. `partial` — one or more metric fields unavailable from this provider. `stale` — snapshot age exceeds the allowed freshness threshold. `missing` — no live data could be retrieved. Gate semantics defined in [Data-Status Semantics](#data-status-semantics). |
