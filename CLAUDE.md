# Project Instructions

You are working in a Docker-first Python QA automation framework using pytest, Playwright, Requests, and jsonschema.

## Project purpose
This repo demonstrates API and UI automation using:
- Playwright for UI tests
- Requests for REST API tests
- pytest for test execution
- jsonschema for contract validation
- Docker for reproducible execution

## Test commands
Run all tests:

pytest -v

Run API tests:

pytest test/api -v

Run UI tests:

pytest test/ui -v

Run with Docker:

docker build -t playwright-api-automation .
docker run --rm playwright-api-automation

## QA behavior rules
Before editing code:
1. Inspect the relevant tests, fixtures, data, and utilities.
2. Explain the risk area.
3. Propose a short plan.
4. Wait for approval before making changes.

When adding tests:
- Follow existing pytest style.
- Keep API and UI tests separated.
- Prefer clear assertions over broad checks.
- Use existing fixtures and helper methods when possible.
- Update or add test data only when needed.

When tests fail:
- Capture the failing command.
- Summarize the failure.
- Identify likely root cause.
- Suggest the smallest safe fix.