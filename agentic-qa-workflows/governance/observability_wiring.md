# Observability Integration Wiring Guide

## Overview

`scripts/pull_observability.py` is the observability data adapter for the release-readiness flow. When activated, it pulls metrics from a live observability provider (Datadog, Grafana, or PagerDuty) and writes `data/release/observability_snapshot.json` — the file `scripts/release_gate.py` consumes to make GO/NO_GO decisions.

**Current state:** The stub makes no real API calls. `data/release/observability_snapshot.json` contains static sample values. The release gate evaluates against sample data until a live provider is connected.

**When it matters:** Observability signals (error rate, latency, incident count) feed the release gate decision. When the gate produces GO or NO_GO, that result is included in the aggregate CI notification.

**Dry-run default:** The script always previews output and exits without writing unless `OBSERVABILITY_WRITE=true` is explicitly set. Credentials being present does not trigger writes. Setting `OBSERVABILITY_WRITE=true` without required credentials still dry-runs.

**Implementation:** `scripts/pull_observability.py` — stdlib only; zero new Python dependencies. When activated, the script runs directly on the GitHub Actions runner before the release gate step.

For the architectural decision record, see [ADR-017 in architecture_decision_log.md](architecture_decision_log.md#adr-017-observability-snapshot-populated-via-stub-pending-live-stack-connection).

---

## Supported Providers

| Provider | `OBSERVABILITY_PROVIDER` value | Current behavior | Required credentials |
| --- | --- | --- | --- |
| Manual (default) | `manual` | Loads existing static file, refreshes timestamp | None |
| Datadog | `datadog` | Stub: prints would-call message, returns sample | `DATADOG_API_KEY`, `DATADOG_APP_KEY` |
| Grafana | `grafana` | Stub: prints would-call message, returns sample | `GRAFANA_URL`, `GRAFANA_API_KEY`, `GRAFANA_DASHBOARD_UID` |
| PagerDuty | `pagerduty` | Stub: prints would-call message, returns sample | `PAGERDUTY_API_KEY`, `PAGERDUTY_SERVICE_ID` |

An unknown provider value prints a warning with valid provider names, generates no snapshot, and exits 0. It does not fall back to `manual`.

---

## GitHub Secrets Reference

Store all provider credentials in **GitHub Settings → Secrets and variables → Actions → Secrets tab**. Never commit credential values to the repository. Provision only the secrets for the chosen provider — only one provider is active at a time.

### Datadog

| Secret | Purpose |
| --- | --- |
| `DATADOG_API_KEY` | Datadog API key for metrics queries |
| `DATADOG_APP_KEY` | Datadog application key (scopes API access) |

> **Note on `DATADOG_SITE`:** The `pull_observability.py` stub docstring mentions `DATADOG_SITE` as a future optional parameter (default: `datadoghq.com`). This is forward-documentation for a real Datadog implementation — the current stub does not read or check `DATADOG_SITE`. A real implementation would use `DATADOG_SITE` to construct API endpoint URLs. Until then, `DATADOG_SITE` is not an active secret or env var for this repo.

### Grafana

| Secret | Purpose |
| --- | --- |
| `GRAFANA_URL` | Grafana instance base URL — treat as a secret; reveals infrastructure topology |
| `GRAFANA_API_KEY` | Grafana service account token |
| `GRAFANA_DASHBOARD_UID` | Dashboard UID for panel queries |

### PagerDuty

| Secret | Purpose |
| --- | --- |
| `PAGERDUTY_API_KEY` | PagerDuty REST API key |
| `PAGERDUTY_SERVICE_ID` | PagerDuty service ID for incident queries |

---

## Safe Variables

The following are **repository variables or runtime environment flags** — not secrets. They do not contain credential values and may be set under **Settings → Secrets and variables → Actions → Variables tab** (not the Secrets tab).

| Variable | Purpose | Default |
| --- | --- | --- |
| `OBSERVABILITY_PROVIDER` | Selects the active provider: `manual`, `datadog`, `grafana`, or `pagerduty` | `manual` |
| `OBSERVABILITY_ENVIRONMENT` | Tags the snapshot with an environment label | `staging` |
| `OBSERVABILITY_WRITE` | Set to `true` or `1` to write the snapshot to disk | Preview only |
| `OBSERVABILITY_SNAPSHOT_PATH` | Output file path override | `data/release/observability_snapshot.json` |

**Important:** `OBSERVABILITY_SNAPSHOT_PATH` must stay aligned with `scripts/release_gate.py`. See the [OBSERVABILITY_SNAPSHOT_PATH Warning](#observability_snapshot_path-warning) section below.

---

## OBSERVABILITY_WRITE (Repository Variable, not a Secret)

`OBSERVABILITY_WRITE` is a **repository variable** — not a secret.

Add it under: **Settings → Secrets and variables → Actions → Variables tab** (not the Secrets tab).

| Value | Effect |
| --- | --- |
| `true` or `1` | Enables writing the snapshot to disk when required credentials are also present |
| Unset or `false` | Preview-only — no writes regardless of credential state |

**Why it must be explicit:** An implicit write triggered by credentials alone could overwrite the tracked static file in `data/release/` during development or local testing. The explicit flag ensures writes are intentional and auditable.

**Credentials alone do not write.** Setting `OBSERVABILITY_WRITE=true` without required credentials for the selected provider still dry-runs. Both conditions must be met:

- `OBSERVABILITY_WRITE=true` is set explicitly
- All required credentials for the selected provider are present

**`manual` provider note:** The `manual` provider has no required credentials. `OBSERVABILITY_WRITE=true` with `manual` (or no provider set) will write — it refreshes the snapshot timestamp while preserving existing metrics and thresholds from the static file.

**If `OBSERVABILITY_WRITE` is added under Secrets instead of Variables**, the workflow's `${{ vars.OBSERVABILITY_WRITE }}` reference reads from the wrong namespace and resolves to an empty string — the flag silently has no effect.

---

## OBSERVABILITY_SNAPSHOT_PATH Warning

`scripts/pull_observability.py` accepts an `OBSERVABILITY_SNAPSHOT_PATH` env var to override the write destination. `scripts/release_gate.py` reads from `data/release/observability_snapshot.json` by a **hardcoded path constant** — there is no corresponding override in the gate script.

If these paths diverge, the result is silent failure: `pull_observability.py` writes to the custom path, and `release_gate.py` continues to read from the default path — evaluating against stale or sample data without warning.

**Rule:** if `OBSERVABILITY_SNAPSHOT_PATH` is set to a custom value, `scripts/release_gate.py` must be updated to read from the same path. Update both in the same activation slice (ADR-017 activation condition 3).

The default path — `data/release/observability_snapshot.json` — requires no override and no change to `release_gate.py`.

---

## Validating Dry-Run Behavior

Run these commands from the repository root to confirm stub behavior before activating a live provider.

### Default (manual provider)

```bash
python scripts/pull_observability.py
```

Expected output:

```text
[STUB] pull_observability.py — provider: manual
[DRY RUN] Snapshot preview:
  environment: staging
  source: manual_sample
  metrics.production_error_rate_pct: 0.3
  metrics.p95_latency_ms: 210
  metrics.p99_latency_ms: 450
  metrics.recent_incident_count: 0
```

### Datadog stub

```bash
OBSERVABILITY_PROVIDER=datadog python scripts/pull_observability.py
```

Expected output:

```text
[STUB] pull_observability.py — provider: datadog
[STUB] Datadog: would call POST https://<datadog-site>/api/v2/query/timeseries
[DRY RUN] Snapshot preview:
  environment: staging
  source: datadog_stub
  metrics.production_error_rate_pct: 0.3
  metrics.p95_latency_ms: 210
  metrics.p99_latency_ms: 450
  metrics.recent_incident_count: 0
```

### Grafana stub

```bash
OBSERVABILITY_PROVIDER=grafana python scripts/pull_observability.py
```

Expected output:

```text
[STUB] pull_observability.py — provider: grafana
[STUB] Grafana: would call GET https://<grafana-host>/api/dashboards/uid/<dashboard-uid>
[DRY RUN] Snapshot preview:
  environment: staging
  source: grafana_stub
  metrics.production_error_rate_pct: 0.3
  metrics.p95_latency_ms: 210
  metrics.p99_latency_ms: 450
  metrics.recent_incident_count: 0
```

### PagerDuty stub

```bash
OBSERVABILITY_PROVIDER=pagerduty python scripts/pull_observability.py
```

Expected output:

```text
[STUB] pull_observability.py — provider: pagerduty
[STUB] PagerDuty: would call GET https://api.pagerduty.com/incidents?service_ids[]=<service-id>
[DRY RUN] Snapshot preview:
  environment: staging
  source: pagerduty_stub
  metrics.production_error_rate_pct: 0.3
  metrics.p95_latency_ms: 210
  metrics.p99_latency_ms: 450
  metrics.recent_incident_count: 0
```

### Unknown provider

```bash
OBSERVABILITY_PROVIDER=splunk python scripts/pull_observability.py
```

Expected output:

```text
WARNING: unknown provider "splunk". Valid providers: manual, datadog, grafana, pagerduty
No snapshot generated.
```

Exits 0. Does not fall back to `manual`. Does not write anything.

### Write-guard validation

```bash
OBSERVABILITY_PROVIDER=datadog OBSERVABILITY_WRITE=true python scripts/pull_observability.py
```

Expected output:

```text
[STUB] pull_observability.py — provider: datadog
[STUB] Datadog: would call POST https://<datadog-site>/api/v2/query/timeseries
[DRY RUN] DATADOG_API_KEY, DATADOG_APP_KEY not set — skipping write
[DRY RUN] Snapshot preview:
  environment: staging
  source: datadog_stub
  metrics.production_error_rate_pct: 0.3
  metrics.p95_latency_ms: 210
  metrics.p99_latency_ms: 450
  metrics.recent_incident_count: 0
```

Prints missing credential names only — not their values. Does not write.

Confirm no file mutation:

```bash
git diff data/release/observability_snapshot.json  # must be empty
```

**What must not appear in any output:** API key values, Grafana URLs or dashboard UIDs, PagerDuty service IDs, SMTP credentials, webhook URLs, or any other secret values.

---

## Activation Checklist

All five conditions must be met before wiring `pull_observability.py` to CI. This checklist reproduces [ADR-017](architecture_decision_log.md#adr-017-observability-snapshot-populated-via-stub-pending-live-stack-connection) activation conditions in order.

**Condition 1 — Replace the stub body**

Replace the target provider's fetch function body in `scripts/pull_observability.py` with real API calls using the documented endpoint patterns.

- Datadog: `POST https://<your-datadog-site>/api/v2/query/timeseries`
- Grafana: `GET https://<your-grafana-host>/api/dashboards/uid/<dashboard-uid>`
- PagerDuty: `GET https://api.pagerduty.com/incidents?service_ids[]=<your-service-id>`

**Condition 2 — Provision GitHub Secrets**

Add the required secrets for the chosen provider in **GitHub Settings → Secrets and variables → Actions → Secrets tab**. See [GitHub Secrets Reference](#github-secrets-reference). Never commit credential values.

**Condition 3 — Decide output path and align with `release_gate.py`**

Decide whether `pull_observability.py` writes to the tracked static file or a workflow-local artifact path. If using a custom path, set `OBSERVABILITY_SNAPSHOT_PATH` and update `scripts/release_gate.py` to read from the same path. See [OBSERVABILITY_SNAPSHOT_PATH Warning](#observability_snapshot_path-warning).

**Condition 4 — Add snapshot freshness check**

Add a `snapshot_timestamp` age check in `scripts/release_gate.py` so a stale snapshot from a prior CI run cannot silently pass the gate. A run that fails to pull live data should warn or produce NO_GO rather than evaluate against hours-old values.

**Condition 5 — Wire to CI**

Add a `pull_observability.py` step **before** the release gate step in `.github/workflows/ci.yml`, but only after conditions 1–4 are complete.

> **Forward documentation: what this CI step would look like**
>
> Do not add this to `ci.yml` now. This is the shape to use when condition 5 is met.
>
> Datadog example:
>
> ```yaml
> - name: Pull observability snapshot
>   env:
>     DATADOG_API_KEY: ${{ secrets.DATADOG_API_KEY }}
>     DATADOG_APP_KEY: ${{ secrets.DATADOG_APP_KEY }}
>     OBSERVABILITY_PROVIDER: datadog
>     OBSERVABILITY_WRITE: "true"
>   run: python scripts/pull_observability.py
> ```
>
> Adapt the `env:` block for Grafana or PagerDuty by substituting the relevant secrets from the [GitHub Secrets Reference](#github-secrets-reference).

---

## Connection to Release Gate

`scripts/release_gate.py` reads `data/release/observability_snapshot.json` on every full-suite CI run. It consumes `metrics` and `thresholds` fields to evaluate:

- `production_error_rate_pct` vs. `max_error_rate_pct` — gate failure if exceeded
- `p95_latency_ms` and `p99_latency_ms` vs. their thresholds — warnings if exceeded
- `recent_incident_count` vs. `max_recent_incident_count` — warning if exceeded

In the current stub-only state, these values are static sample data. The gate passes on sample values. When a live provider is connected and writes fresh data before each gate run, the GO/NO_GO decision reflects real production state.

The path `release_gate.py` reads from is hardcoded. See [OBSERVABILITY_SNAPSHOT_PATH Warning](#observability_snapshot_path-warning) before using a custom write path.

**Snapshot freshness:** There is currently no freshness check in `release_gate.py`. A stale snapshot from a prior run could pass the gate silently. Adding a `snapshot_timestamp` age check is ADR-017 activation condition 4 and should be in place before wiring CI.

---

## Connection to Aggregate Notification

The `Notify` CI job reads `artifacts/release-readiness.json`, which is produced by `scripts/release_gate.py`. The "Release Gate (staging API)" line in Slack and email notifications reflects the gate's GO or NO_GO decision — which is built from observability snapshot data.

In the current stub-only state, the notification's release-gate line reflects the gate's evaluation of static sample values. When a live provider is wired and writes fresh observability data before the gate runs, the release-gate signal in notifications will reflect real production health.

For step-by-step notification setup, see [`notification_wiring.md`](notification_wiring.md).

---

## Secret Hygiene

Store all observability provider credentials only in **GitHub → Settings → Secrets and variables → Actions → Secrets tab**.

Never store credentials in:

- `.env` files
- markdown or governance docs (including this file)
- JSON data files
- source code or inline comments
- CI artifact files (`release-readiness.json`, HTML reports, or step summaries)
- screenshots

If a credential is accidentally committed: rotate it immediately (generate a new API key from your provider's dashboard), update the GitHub secret, then remove the old value from git history.

If GitHub secret scanning and push protection are enabled (**Settings → Code security and analysis**), GitHub will alert on detected credential patterns and block pushes before secrets reach the remote.

For the committed credential policy and rotation guidance, see [security_and_branch_protection.md — Observability secrets](security_and_branch_protection.md).

---

## References

- [`scripts/pull_observability.py`](../../scripts/pull_observability.py) — observability stub implementation; per-provider API interface documentation
- [`data/release/observability_snapshot.json`](../../data/release/observability_snapshot.json) — static sample snapshot consumed by the release gate
- [`scripts/release_gate.py`](../../scripts/release_gate.py) — release readiness gate; consumes the snapshot
- [`quality_gates.md`](quality_gates.md) — Release Gate section; activation pointer
- [`security_and_branch_protection.md`](security_and_branch_protection.md) — Observability secrets section
- [`architecture_decision_log.md` — ADR-017](architecture_decision_log.md#adr-017-observability-snapshot-populated-via-stub-pending-live-stack-connection)
- [`notification_wiring.md`](notification_wiring.md) — aggregate notification setup; observability dependency explained
