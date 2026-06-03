# Playwright API Automation

[![CI](https://github.com/mariand755/playwright-api-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/mariand755/playwright-api-automation/actions/workflows/ci.yml)

A Python test automation framework that covers both UI testing (via Playwright) and REST API testing (via Requests), targeting two separate applications. The framework is designed to be simple, maintainable, and reproducible across local and Docker environments.


## Target Applications
- SauceDemo (https://www.saucedemo.com) — UI test target (e-commerce demo site)
- Restful Booker (https://restful-booker.herokuapp.com) — API test target (hotel booking REST API)


## Scope Implemented
- UI smoke flow
- API test suite
- Page Object Model with separate locator classes
- Failure diagnostics (screenshot + HTML dump)
- Docker is the recommended validation path; local runs are supported as optional fast feedback

## Architecture Overview
Tests are organized in layers:

```text
UI Tests (Playwright + Page Objects)
	↓
Test Layer (pytest test cases)
	↓
Utility Layer (API client, helpers, fixtures)
	↓
External Systems (Restful Booker API / SauceDemo UI)
```

## Test Coverage Summary

### UI
Smoke flow:
- Login with valid credentials
- Add product to cart
- Validate cart contents

Primary journey selected for this assessment: login + add-to-cart (checkout completion is listed in Next Steps).

### API
Endpoints covered:
- GET /booking
- GET /booking/{id}
- POST /booking

Coverage types:
- Positive tests
- Negative tests
- Schema validation
- Data-driven tests using external JSON

## Repo Structure
```text
playwright-api-automation/
│
├── conftest.py              # Global pytest fixtures (shared between UI & API tests)
├── pytest.ini               # Pytest config: test paths, markers, default options
├── requirements.txt         # Dependencies: pytest, playwright, requests, jsonschema
├── Dockerfile               # Docker image for running tests in isolation
│
├── test/                    # All test cases organized by type
│   ├── api/
│   │   └── test_booking_api.py   # API tests against Restful Booker
│   └── ui/
│       └── test_login_cart.py    # UI tests against SauceDemo
│
├── pages/                   # Page Object Model (POM) classes
│   ├── locators.py          # All CSS/text selectors, centralized
│   ├── login_page.py        # LoginPage: navigate, login, verify_login_success
│   └── inventory_page.py    # InventoryPage: add to cart, open cart, verify
│
├── utils/                   # Shared utilities
│   ├── api_client.py        # BookingApiClient: wraps Requests calls to Restful Booker
│   ├── helpers.py           # load_json() and get_schema() for loading test data/schemas
│   └── timeouts.py          # Central timeout constants (UI in ms, API in seconds)
│
├── data/
│   ├── test_data/
│   │   └── test_users.json  # URLs + test credentials (SauceDemo standard_user)
│   └── schemas/
│       ├── booking_schema.json          # JSON Schema: create booking response
│       └── booking_details_schema.json  # JSON Schema: get booking by ID response
│
├── agentic-qa-workflows/    # QA governance, prompts, workflows, and audit outputs
│   ├── governance/
│   ├── prompts/
│   ├── workflows/
│   └── outputs/
│
└── artifacts/               # Auto-generated: screenshots + HTML on UI test failure
```

## Agentic QA Governance

This repo includes a governance layer for AI-assisted QA work under `agentic-qa-workflows/`.

It defines standards, prompt templates, audit workflows, and repeatable output patterns
that keep AI-driven changes controlled and reviewable.

See [agentic-qa-workflows/README.md](agentic-qa-workflows/README.md) for details.

## Tooling Rationale
This framework uses:

- **pytest** for lightweight and readable test execution
- **Playwright** for reliable browser automation with built-in waiting
- **requests** for API interactions
- **jsonschema** for API contract validation
- **Docker** for consistent execution across environments
- **Ruff** for code formatting and linting (enforced in CI via Docker)

The goal is to keep the framework simple, maintainable, and reproducible across local and containerized environments.

## CI

GitHub Actions runs a Docker-first workflow that builds the image and verifies pytest collection. On PRs and feature branch pushes, CI runs the smoke subset for fast feedback. On push to `main`, nightly schedule, and `workflow_dispatch`, CI runs the full suite and produces a release readiness decision. Failure artifacts are uploaded when UI test evidence is present.

The `ENV` environment variable selects the URL block from `data/test_data/test_users.json`. `staging` is the default and is used for all standard CI runs. A `prod_read_only` environment block is defined as an activation-ready stub: prod-read-only steps run `read_only`-marked tests only and are gated by `PROD_ENV_ACTIVE=true` (a GitHub repository variable). See [ADR-015](agentic-qa-workflows/governance/architecture_decision_log.md#adr-015-cross-environment-selection-with-staging-default-and-prod-read-only-activation-gate) for activation conditions.

For live Slack and SMTP notification setup, see [agentic-qa-workflows/governance/notification_wiring.md](agentic-qa-workflows/governance/notification_wiring.md).

## Prerequisites
- Docker — required for CI-parity validation
- Python 3.9+, pip, Playwright browser binaries — for optional local runs only

## Local Setup (optional)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
```

## Optional: Pre-commit Guardrails

Pre-commit hooks provide optional fast feedback before push — catching formatting issues, lint violations, and type errors in seconds without a Docker build. This is advisory; Docker CI remains the gate.

```bash
pip install pre-commit   # or: brew install pre-commit
pre-commit install       # registers the hook — runs automatically on git commit
pre-commit run --all-files  # optional: run on all files immediately
```

See [agentic-qa-workflows/governance/quality_gates.md](agentic-qa-workflows/governance/quality_gates.md) for the full hook list and what pre-commit does not cover (CodeQL, pip-audit, Trivy).

## Run Tests (Local — optional fast feedback)
Run all tests:
```bash
pytest -v
```

Run UI smoke only:
```bash
pytest test/ui -v
```

Run API tests only:
```bash
pytest test/api -v
```

## Run with Docker

Docker is the source-of-truth path for full-suite validation and CI parity.

Build image:
```bash
docker build -t playwright-api-automation .  #build the Docker image
```

Run tests:
```bash
docker run --rm playwright-api-automation  #run all tests, container removed after completion
```

Run UI tests only in Docker:
```bash
docker run --rm playwright-api-automation pytest test/ui -v  #run only UI tests

```

Run API tests only in Docker:
```bash
docker run --rm playwright-api-automation pytest test/api -v  #run only API tests
```

## UI Smoke Coverage
Implemented in `test/ui/test_login_cart.py` using:
- `pages/login_page.py`
- `pages/inventory_page.py`
- `pages/locators.py`

## Failure Diagnostics

On any UI test failure, the framework automatically captures:

- Screenshot: `artifacts/failures/<test_name>.png`
- HTML dump: `artifacts/failures/<test_name>.html`

Capture is handled by the `pytest_runtest_makereport` hook in `conftest.py`. API test failures surface diagnostic context (URL, status code, response body excerpt) directly in the pytest traceback — no separate artifact file.

**In CI:** The workflow volume-mounts `artifacts/` into the Docker container so evidence written inside the container persists on the runner. On failure, GitHub Actions uploads `artifacts/failures/` as the `failure-artifacts` artifact. The upload is skipped silently when no files are present (API-only failures produce no screenshot).

## Assessment Artifacts
- Source code: repository root
- Decision log: `DecisionLog.md`
- Full local run output: `artifacts/local-run-output.txt`
- Local UI-only run output: `artifacts/local-ui-run-output.txt`
- Local API-only run output: `artifacts/local-api-run-output.txt`
- Docker UI-only run output: `artifacts/docker-ui-run-output.txt`
- Docker API-only run output: `artifacts/docker-api-run-output.txt`

## Execution Time
Typical runtime observed from current local logs:
- UI smoke: ~1.5 to 2 seconds
- API suite: ~1 to 2 seconds
- Full suite: ~3 to 4 seconds
