# AAA Life SDET Assessment

Production-style test automation framework using Python, pytest, and Playwright.

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

## Project Structure
- `pages/`: UI Page Objects and locator definitions (`login_page.py`, `inventory_page.py`, `locators.py`)
- `test/ui/`: UI smoke tests
- `test/api/`: API tests
- `utils/`: Shared helpers — API client (`api_client.py`), timeout constants (`timeouts.py`), test helpers (`helpers.py`)
- `data/schemas/`: JSON Schema contracts for API response validation
- `data/test_data/`: External test data (`test_users.json`, `booking_ids.json`)
- `artifacts/`: Local and Docker run outputs
- `conftest.py`: Shared pytest fixtures (browser, credentials, API client, timeouts, failure hooks)
- `artifacts/failures/`: failure diagnostics generated during test runs

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
docker build -t aaa-life-sdet .  #build the Docker image with the tag "aaa-life-sdet"
```

Run tests:
```bash
docker run --rm aaa-life-sdet  #run the Docker container and execute tests, removing the container after completion
```

Run UI tests only in Docker:
```bash
docker run --rm aaa-life-sdet pytest test/ui -v  #run only the UI tests in the Docker container

```

Run API tests only in Docker:
```bash
docker run --rm aaa-life-sdet pytest test/api -v  #run only the API tests in the Docker container
```

## UI Smoke Coverage
Implemented in `test/ui/test_login_checkout.py` using:
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
