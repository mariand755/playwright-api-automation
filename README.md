# Playwright API Automation
A Python test automation framework that covers both UI testing (via Playwright) and REST API testing (via Requests), targeting two separate applications. The framework is designed to be simple, maintainable, and reproducible across local and Docker environments.  


## Target Applications
- SauceDemo (https://www.saucedemo.com) — UI test target (e-commerce demo site)
- Restful Booker (https://restful-booker.herokuapp.com) — API test target (hotel booking REST API)


## Scope Implemented
- UI smoke flow
- API test suite
- Page Object Model with separate locator classes
- Failure diagnostics (screenshot + HTML dump)
- Ready to run locally and in Docker

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
└── artifacts/               # Auto-generated: screenshots + HTML on UI test failure
```

## Tooling Rationale
This framework uses:

- **pytest** for lightweight and readable test execution
- **Playwright** for reliable browser automation with built-in waiting
- **requests** for API interactions
- **jsonschema** for API contract validation
- **Docker** for consistent execution across environments

The goal is to keep the framework simple, maintainable, and reproducible across local and containerized environments.

## Prerequisites
- Python 3.9+
- pip
- Playwright browser binaries
- Docker (optional)

## Setup (Local)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
```

## Run Tests (Local)
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
On any test failure, framework captures:
- Full-page screenshot: `artifacts/failures/<test_name>.png`
- Page HTML dump: `artifacts/failures/<test_name>.html`

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
