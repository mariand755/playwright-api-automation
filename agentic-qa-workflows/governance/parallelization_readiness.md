# Parallelization Readiness

This document records the pytest parallelization baseline, the fixture isolation audit results, and the activation decisions for `pytest-xdist`.

---

## Current State (as of PR #67)

Current pytest collection after PR #63:

| Category | Count |
|---|---|
| API behavioral tests | 13 |
| UI behavioral tests | 9 |
| Behavioral total | 22 |
| Script test nodes collected | 33 |
| Total collected pytest nodes | 55 |

**API and standard UI pytest-xdist activated.** Script tests remain serial. Docker Test Suite remains serial. Prod-read-only API and UI steps remain serial.

See [ADR-028](architecture_decision_log.md#adr-028-api-pytest-xdist-activation-with-serial-ui-and-script-execution) and [ADR-029](architecture_decision_log.md#adr-029-ui-pytest-xdist-activation-with-serial-script-and-prod-read-only-execution) for the full decision records.

---

## Existing CI-Level Parallelism

The repo already achieves job-level parallelism. `API Tests` and `UI Tests` run as separate parallel jobs in `ci.yml` — they start simultaneously after `Docker Test Suite` passes.

`pytest-xdist` adds process-level parallelism within each of those jobs, further reducing per-job test execution time.

---

## Activation Outcome — API xdist (PR #64, ADR-028)

**Command (API Tests job, standard run):**

```bash
pytest test/api $MARKER_ARGS -v -n auto --junitxml=artifacts/api-report.xml
```

- `-n auto` resolves to 2 workers on a standard GitHub Actions `ubuntu-latest` runner (2 vCPU).
- `--dist=load` (xdist default) distributes tests dynamically across workers.
- Prod-read-only API step remains serial (small gated subset).

**Rollback:** Remove `-n auto` from the `Run API test suite` step in `.github/workflows/ci.yml`. Do not remove `pytest-xdist` — UI xdist still depends on it.

---

## Activation Outcome — UI xdist (PR #67, ADR-029)

**Command (UI Tests job, standard run):**

```bash
pytest test/ui $MARKER_ARGS -v -n auto --junitxml=artifacts/ui-report.xml
```

- `-n auto` resolves to 2 workers on a standard GitHub Actions `ubuntu-latest` runner (2 vCPU).
- `--dist=load` (xdist default) distributes tests dynamically across workers.
- Prod-read-only UI step remains serial (small gated subset; conservative production path).

**Rollback:** Remove `-n auto` from the `Run UI test suite` step in `.github/workflows/ci.yml`. Do not remove `pytest-xdist` — API xdist still depends on it.

---

## Fixture Isolation Audit

### API fixtures (audited in PR #64)

| Fixture | Audit result | Reasoning |
|---|---|---|
| `booking_api` | **Safe** | Stateless HTTP client; immutable after construction |
| `auth_token` | **Safe** | Immutable string; each worker process creates its own token via a separate `/auth` POST; no test mutates it |
| `test_data`, `base_url`, `api_base_url`, `credentials` | **Safe** | Read-only data; no network calls |
| `booking_payload_factory` | **Safe** | Returns a factory closure with no shared mutable state |
| `created_booking` | **Audited safe** | Each fixture invocation creates a unique booking ID, and teardown deletes that specific booking. Concurrent teardowns delete distinct resources — no race. |

### UI fixtures (audited in PR #67)

| Fixture | Audit result | Reasoning |
|---|---|---|
| `base_url`, `credentials`, `locked_out_credentials`, `checkout_data`, `test_data` | **Safe** | Read-only session-scoped data; not mutated by any UI test |
| `page` (function-scoped, overridden in `conftest.py`) | **Safe** | pytest-playwright's `page` is function-scoped; each test in each worker receives an isolated browser page. |
| `expect.set_options(timeout=...)` in page fixture | **Safe** | Sets process-global Playwright expectation timeout. Under xdist, workers are separate Python subprocesses — worker A's state cannot affect worker B. |
| Page objects (`LoginPage`, `InventoryPage`, `CartPage`, `CheckoutPage`) | **Safe** | Instantiated inside each test from the function-scoped `page` fixture; no shared state. |

### UI failure artifact safety

The `pytest_runtest_makereport` hook writes failure artifacts using a sanitized `item.nodeid` stem (PR #66 hardening):

```text
artifacts/failures/<sanitized-nodeid>.png
artifacts/failures/<sanitized-nodeid>.html
```

Filenames are unique across split UI files, future duplicate function names in different files, and future parameterized tests. The CI `artifacts/failures/` directory is pre-cleaned before the Docker run.

### Script fixtures — serial

Script tests use `tmp_path` and plain dicts only. They are fast governance checks. Serial execution is required for the TC-ID uniqueness guard (TC-SCRIPT-031) and release gate logic.

---

## Serial Paths

| Path | Reason |
|---|---|
| Prod-read-only API step | Small gated read-only subset; conservative production path |
| Prod-read-only UI step | Small gated read-only subset; conservative production path |
| Script unit tests | Fast deterministic governance checks; TC-ID uniqueness guard and release gate must remain serial |
| Docker Test Suite collection check | Source-of-truth serial baseline; does not run behavioral tests |

---

## Future Activation Conditions

### Script xdist

No activation planned. Script tests are fast deterministic governance checks and should remain serial.

### Cross-browser Playwright matrix or cloud grid

Activate only when cross-browser coverage or cross-device coverage becomes a stated requirement. Separate Mode A review required.

---

## References

- [ADR-028](architecture_decision_log.md#adr-028-api-pytest-xdist-activation-with-serial-ui-and-script-execution) — API xdist decision
- [ADR-029](architecture_decision_log.md#adr-029-ui-pytest-xdist-activation-with-serial-script-and-prod-read-only-execution) — UI xdist decision
- `quality_gates.md` — CI job structure and test execution policy
