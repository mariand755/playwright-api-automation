# QA Architecture Blueprint — Python/Playwright/pytest

[![CI](https://github.com/mariand755/playwright-api-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/mariand755/playwright-api-automation/actions/workflows/ci.yml)

A working, production-style reference implementation of how to design, build, govern, and operationalize a Python QA system. Covers multi-layer testing (API, UI, script unit), a Docker-first CI gate chain with release-readiness governance, a notification delivery layer, and an ADR-backed governance documentation layer. Designed to be adapted to a client codebase — the governance layer, CI structure, and activation-gated features apply to any Python API/UI automation project.

Stack: Python, pytest, Playwright, Requests, jsonschema, Docker, GitHub Actions, Ruff, mypy, pip-audit, Trivy, CodeQL, and Dependabot.

## What This Repo Demonstrates

- Multi-layer test suite: API (CRUD + contract validation), UI (page-object flows), and script unit tests covering QA tooling logic
- 4-job CI pipeline with smoke/full test-scope gating, code quality gates, JUnit reporting, and nightly regression
- Multi-signal release readiness gate: test results + observability signals + defect metrics → GO/NO_GO decision
- Notification delivery infrastructure: Slack and SMTP channels, dry-run by default, activation-gated by secrets
- ADR-backed governance documentation layer: suite taxonomy, quality gate definitions, notification and observability activation guides
- Consulting-style delivery pattern: dry-run defaults, activation-gated features with documented conditions, explicit deferral rationale

## Test Layers

| Layer | Tests | Framework | Coverage |
|---|---|---|---|
| API | 7 | pytest + Requests | CRUD + auth + contract validation — Restful Booker |
| UI | 6 | pytest + Playwright | Login, cart, checkout, negative paths — SauceDemo |
| Script unit | 25 | pytest | Release gate, CI summary, notification decision logic |

## Target Applications

- [Restful Booker](https://restful-booker.herokuapp.com) — API test target (hotel booking REST API)
- [SauceDemo](https://www.saucedemo.com) — UI test target (e-commerce demo site)

## CI Quality Gate Pipeline

### Job structure

| Job | Runs | Depends on |
|---|---|---|
| Docker Test Suite | Builds image, validates pytest collection | — |
| API Tests | Full API suite, JUnit report, dorny test panel | Docker Test Suite |
| UI Tests | Full UI suite, JUnit report, dorny test panel, failure artifacts | Docker Test Suite |
| Notify | Builds release readiness notification and delivers to configured channels | API Tests + UI Tests |

### Test scope by trigger

| Trigger | Scope | Release gate |
|---|---|---|
| Push to feature branch / PR | Smoke | Skipped — placeholder artifact written |
| Push to `main` | Full | GO / NO_GO decision |
| Nightly (02:00 UTC) | Full | GO / NO_GO decision |
| `workflow_dispatch` | `test_scope` input: full or smoke | GO / NO_GO if full; skipped if smoke |

`workflow_dispatch` also accepts a `notification_mode` input (`repo_default` / `dry_run` / `live`) for manual notification control during a run.

## Code Quality and Supply-Chain Gates

- **Ruff** — formatting and linting (CI-enforced in Docker)
- **mypy** — static type checking (CI-enforced in Docker)
- **pip-audit** — Python dependency vulnerability scanning
- **Trivy** — container image vulnerability scanning
- **CodeQL** — static security analysis (GitHub Advanced Security)
- **Dependabot** — automated dependency updates
- **pre-commit** — local advisory guardrails (formatting, lint, type check before push); Docker CI is source of truth

See [agentic-qa-workflows/governance/quality_gates.md](agentic-qa-workflows/governance/quality_gates.md) for full gate definitions and what pre-commit does not cover (CodeQL, pip-audit, Trivy).

## Release Readiness Gate

`scripts/release_gate.py` consumes three signal sources:

- JUnit XML from the API test job
- Observability signals via `pull_observability.py` (error rate, p95/p99 latency, incident count)
- Defect metrics (open blockers, escape count)

It produces a `GO` / `NO_GO` / `UNKNOWN` decision written to `artifacts/release-readiness.json` and `artifacts/release-readiness.md`. On smoke runs, the gate writes a schema-consistent `gate_skipped: true` placeholder so the Notify job always has an artifact to consume.

Observability providers are currently stub-backed — Datadog, Grafana, and PagerDuty interfaces are documented; stub bodies return sample data. See [agentic-qa-workflows/governance/observability_wiring.md](agentic-qa-workflows/governance/observability_wiring.md) for activation steps when a live observability stack is available.

## Notification Delivery

Notifications are built and delivered after each CI run. Both channels dry-run by default — CI never fails due to missing credentials.

**Slack:** dry-run by default. Activate by adding a `SLACK_WEBHOOK_URL` GitHub Actions secret.

**SMTP/email:** infrastructure-ready; dry-run by default. Live delivery requires SMTP environment validation — runner outbound SMTP restrictions may require port 465 or a transactional email API.

See [agentic-qa-workflows/governance/notification_wiring.md](agentic-qa-workflows/governance/notification_wiring.md) for full activation steps for both channels.

## Governance and ADR-Backed Decision Layer

`agentic-qa-workflows/` contains the full governance layer:

- **Architecture Decision Log** — ADR-backed rationale for every structural decision (framework choices, scope gating, notification model, environment strategy, quality gate thresholds)
- **Suite Taxonomy** — test IDs, layers, markers, and coverage intent
- **Quality Gates** — full gate definitions for CI and pre-commit
- **Notification Wiring** — live activation guide for Slack and SMTP
- **Observability Wiring** — interface definitions and provider activation guide
- **Prompt templates and audit workflows** — for AI-assisted QA work under review

See [agentic-qa-workflows/README.md](agentic-qa-workflows/README.md) for the full index.

## How to Run

### Docker (source of truth)

```bash
docker build -t playwright-api-automation .
docker run --rm playwright-api-automation
```

Run a specific layer:

```bash
docker run --rm playwright-api-automation pytest test/api -v
docker run --rm playwright-api-automation pytest test/ui -v
docker run --rm playwright-api-automation pytest test/scripts -v
```

### Local (optional fast feedback)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
pytest -v
```

### Pre-commit guardrails (optional)

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Failure Diagnostics

On any UI test failure, the framework captures a screenshot (`artifacts/failures/<test_name>.png`) and HTML dump (`artifacts/failures/<test_name>.html`) via the `pytest_runtest_makereport` hook in `conftest.py`. In CI these are uploaded as the `failure-artifacts` artifact; the upload is skipped silently when no files are present. API failures surface diagnostic context (URL, status code, response body excerpt) directly in the pytest traceback.

## Planned / Deferred Capabilities

| Capability | Status | Notes |
|---|---|---|
| SMTP/email live delivery validation | ⏳ Deferred | Runner SMTP restrictions; may need port 465 or transactional API |
| Forced-live critical failure alerts | ⏳ Deferred | Needs ADR before activation |
| Live observability API integration | ⏳ Deferred | Replace stub bodies when live observability stack is available |
| pytest-xdist parallelization | ⏳ Deferred | Gate: >30 tests or >2 min runtime (not yet met) |
| Blueprint extraction | ⏳ Deferred | Phase 8; after README refresh |

Prod-read-only CI mode is activation-ready, gated by the `PROD_ENV_ACTIVE` repository variable. See [ADR-015](agentic-qa-workflows/governance/architecture_decision_log.md#adr-015-cross-environment-selection-with-staging-default-and-prod-read-only-activation-gate) for the activation checklist.

## GitHub About (Set Manually in GitHub Settings)

**Description:**
```
QA Architecture blueprint — Python/Playwright/pytest, Docker-first CI gate chain, release-readiness governance, agentic QA workflow foundation
```

**Topics:** `pytest` `playwright` `python` `api-testing` `ui-testing` `test-automation` `docker` `ci-cd` `github-actions` `quality-engineering` `release-gate` `governance` `adr` `qa-architecture` `jsonschema` `agentic-qa`
