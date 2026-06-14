# Parallelization Readiness

This document records the pytest parallelization baseline, the fixture isolation audit result, and the activation decision for `pytest-xdist`.

---

## Current State (as of PR #64)

Current pytest collection after PR #63:

| Category | Count |
|---|---|
| API behavioral tests | 13 |
| UI behavioral tests | 9 |
| Behavioral total | 22 |
| Script test nodes collected | 33 |
| Total collected pytest nodes | 55 |

**API xdist activated.** UI tests remain serial. Script tests remain serial.

See [ADR-028](architecture_decision_log.md#adr-028-api-pytest-xdist-activation-with-serial-ui-and-script-execution) for the full decision record.

---

## Existing CI-Level Parallelism

The repo already achieves job-level parallelism. `API Tests` and `UI Tests` run as separate parallel jobs in `ci.yml` — they start simultaneously after `Docker Test Suite` passes. This provides the largest share of wall-clock savings available at the current suite size.

`pytest-xdist` adds process-level parallelism within the API Tests job, further reducing per-job test execution time.

---

## Activation Outcome — API xdist (PR #64)

**Command (API Tests job, standard run):**

```bash
pytest test/api $MARKER_ARGS -v -n auto --junitxml=artifacts/api-report.xml
```

- `-n auto` resolves to 2 workers on a standard GitHub Actions `ubuntu-latest` runner (2 vCPU).
- `--dist=load` (xdist default) distributes tests dynamically across workers.
- UI tests and script tests remain serial — no `-n` flag on those steps.
- Prod-read-only API step remains serial (small gated subset).

**Rollback:** Remove `-n auto` from the `Run API test suite` step in `.github/workflows/ci.yml`. No fixture changes or `requirements.txt` changes needed for rollback.

---

## Fixture Isolation Audit

Completed before API xdist activation in PR #64.

### Session-scoped fixtures

| Fixture | Audit result | Reasoning |
|---|---|---|
| `booking_api` | **Safe** | Stateless HTTP client; immutable after construction |
| `auth_token` | **Safe** | Immutable string; each worker process creates its own token via a separate `/auth` POST; no test mutates it |
| `test_data`, `base_url`, `api_base_url`, `credentials` | **Safe** | Read-only data; no network calls |

### Function-scoped fixtures

| Fixture | Audit result | Reasoning |
|---|---|---|
| `booking_payload_factory` | **Safe** | Returns a factory closure with no shared mutable state |
| `created_booking` | **Audited safe for API xdist** | Each invocation POSTs a new booking and receives a unique `bookingid` from the API. Teardown deletes that specific booking. Concurrent teardowns delete distinct resources — no race. The prior concern about concurrent DELETE teardowns was incorrect: it only applies if tests share a single pre-created booking, which they do not. |

### UI fixtures — deferred

The Playwright `page` fixture wraps browser context. Isolation under `pytest-xdist` requires a separate Mode A review before UI parallelization is considered.

### Script fixtures — deferred

Script tests use `tmp_path` and plain dicts only. They are fast governance checks. Serial execution is required for the TC-ID uniqueness guard (TC-SCRIPT-031) and release gate logic.

---

## Future Activation Conditions

### UI xdist

Trigger a new Mode A review when any of the following are true:

- UI test count exceeds **15**, or
- UI Tests job runtime exceeds **3 minutes**, or
- a portfolio or client need justifies browser-level parallel execution.

### Script xdist

No activation planned. Script tests are fast deterministic governance checks and should remain serial.

---

## References

- [ADR-028](architecture_decision_log.md#adr-028-api-pytest-xdist-activation-with-serial-ui-and-script-execution) — full decision record for this activation
- `quality_gates.md` — CI job structure and test execution policy
