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

---

## Provider Mapping Rules

How each provider's native signals map to the canonical schema. A field listed as "not available" must be omitted from the snapshot, and `data_status` must be set to `partial` for that run.

| Canonical field | Datadog | Grafana | PagerDuty |
|---|---|---|---|
| `production_error_rate_pct` | `timeseries` query on error-rate metric | Panel query result | Not available from PagerDuty incidents alone; omit and set `data_status=partial` |
| `p95_latency_ms` | `timeseries` query on p95 latency | Panel query result | Not available; omit and set `data_status=partial` |
| `p99_latency_ms` | `timeseries` query on p99 latency | Panel query result | Not available; omit and set `data_status=partial` |
| `recent_incident_count` | Map from a provider-specific incident or alert signal; the live implementation must document the query source and time window | Not available from the standard Grafana dashboard integration; omit and set `data_status=partial` | Map from PagerDuty `incidents` endpoint |

Provider endpoint patterns are documented in [`observability_wiring.md` — Activation Checklist, Condition 1](observability_wiring.md#activation-checklist).

---

## Evidence and Provenance Rules

### What may appear in CI artifacts

The following values are safe to include in `artifacts/release-readiness.json`, step summaries, and Slack/email notifications:

- Canonical metric values (`production_error_rate_pct`, `p95_latency_ms`, `p99_latency_ms`, `recent_incident_count`)
- `data_status`, `environment`, `source` identifier
- `snapshot_timestamp`
- Gate decision (`GO`, `NO_GO`, `UNKNOWN`) and reason text

### What must never appear in any output

- API key values or partial values
- Grafana instance URLs or dashboard UIDs
- PagerDuty service IDs
- Raw provider API response bodies
- `str(exc)` or `exc.args` content from provider or file-load exceptions — only `type(exc).__name__` is permitted

---

## Data-Status Semantics

These are requirements on any live implementation. The current gate does not enforce them.

| `data_status` value | Required gate behaviour |
|---|---|
| `complete` | Evaluate all fields against thresholds; produce GO or NO_GO normally |
| `partial` | Evaluate available fields; produce a warning for each missing field; GO is permitted only if all present fields pass and no missing field is a gate-failure dimension |
| `stale` | Produce NO_GO with "stale snapshot" reason; do not evaluate metric values |
| `missing` | Produce NO_GO; cannot evaluate without signals |
| Absent or empty | Treat as `missing` (fail-closed) |

### Freshness override

The gate must derive or override stale status from `snapshot_timestamp` age at evaluation time. It must not rely solely on a provider-supplied `data_status` value — a formerly `complete` snapshot must not be treated as fresh indefinitely. If `snapshot_timestamp` age exceeds the configured threshold, the gate must set effective status to `stale` and produce NO_GO regardless of the stored `data_status` value.

---

## Non-Goals

This document does not:

- Describe live API calls, authentication, or provider-specific query construction (see `observability_wiring.md`)
- Specify GitHub Actions secrets or environment variables
- Change `scripts/pull_observability.py`, `scripts/release_gate.py`, or `.github/workflows/ci.yml`
- Select a provider or define an activation timeline
- Commit to any implementation schedule — that belongs in the activation slice ADR
