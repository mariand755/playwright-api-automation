# Parallelization Readiness

This document records the current pytest parallelization baseline, identifies what must be true before `pytest-xdist` is activated, and explains why the decision is deferred.

---

## Current State (as of PR #62)

Current pytest collection after PR #62:

| Category | Count |
|---|---|
| API behavioral tests | 13 |
| UI behavioral tests | 9 |
| Behavioral total | 22 |
| Script test nodes collected | 33 |
| Total collected pytest nodes | 55 |

The behavioral test count now exceeds the `>20` activation threshold. `pytest-xdist` is still deferred in this PR because activation requires a separate fixture isolation audit, runtime measurement, and explicit Mode A approval for the parallelization strategy.

---

## Existing CI-Level Parallelism

The repo already achieves job-level parallelism. `API Tests` and `UI Tests` run as separate parallel jobs in `ci.yml` — they start simultaneously after `Docker Test Suite` passes. This provides the largest share of wall-clock savings available to this suite at its current size.

Adding `pytest-xdist` (process-level parallelism within a single job) would provide diminishing returns until the per-job test count is high enough that job runtime is the bottleneck.

---

## Why `pytest-xdist` Is Deferred

**Threshold is now met, but activation is separate.** At 22 behavioral tests (13 API + 9 UI), the suite is ready for a dedicated `pytest-xdist` activation review. This PR only grows coverage and updates readiness evidence; it does not activate process-level parallelism.

**Runtime has not been measured.** The activation decision requires observed runtime data, not estimated savings.

**Fixture isolation risks exist.** Before xdist can be enabled safely:

| Fixture | Risk |
|---|---|
| `created_booking` (function scope, finalizer) | Concurrent teardowns on the same booking API could race on DELETE; each worker would need its own booking |
| `auth_token` (session scope) | Safe to share across workers only if never mutated; verify no test writes to the token |
| Playwright `page` / `browser_context` (function scope) | Not xdist-safe by default; requires `--dist=no` for UI tests or explicit `browser_type` fixture isolation per worker |

---

## Runtime Measurement Command

To measure full Docker suite runtime before activating xdist:

```bash
time docker run --rm playwright-api-automation pytest -q
```

Run this at least twice and take the median. Record the result in an ADR or as a note here when measured.

---

## Activation Criteria

Do not add `pytest-xdist` until **all** of the following are true:

1. Behavioral test count (API + UI combined) exceeds **20**, OR measured full Docker suite runtime exceeds **5 minutes**.
2. A fixture isolation audit has been completed — confirm `created_booking` teardowns are worker-safe, `auth_token` is read-only in all tests, and Playwright fixture isolation is understood.
3. Explicit Mode A approval identifies the specific parallelization strategy (API tests only, UI tests only, or both; `--dist=loadscope` vs `--dist=each`).

---

## ADR Note

Do not create ADR-028 now. ADR-028 should be created only when `pytest-xdist` is actually activated or explicitly rejected after evidence. A readiness assessment is not a decision.

---

## References

- `quality_gates.md` — CI job structure and test execution policy
- `architecture_decision_log.md` — ADR-028 placeholder (not yet written)
