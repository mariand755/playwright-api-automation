# Governance

This folder contains the rules, standards, and architectural records that govern AI-assisted and human QA work in this repository.

---

## Files

| File | Purpose | When to read |
|---|---|---|
| `qa_standards.md` | Test naming conventions, test case ID format (`TC-UI-NNN`, `TC-API-NNN`), assertion style | Before adding or editing any test |
| `suite_taxonomy.md` | Marker definitions (`ui`, `api`, `smoke`, `regression`, `negative`, `api_contract`) and when to apply each | Before adding or editing any test |
| `page_object_api_rules.md` | Page Object Model boundaries; API client boundaries; what belongs in a test vs. a fixture vs. a client | Before adding UI page classes or API client methods |
| `test_data_env_rules.md` | Test data design; environment variable handling; credential storage rules | Before adding test data files, fixtures, or environment configuration |
| `failure_evidence.md` | Screenshot and HTML dump capture requirements; failure artifact expectations in CI | Before adding new test types or CI jobs that produce failure evidence |
| `quality_gates.md` | PR gate, merge gate, release gate definitions; Docker-first quality checks; CI job structure | Before submitting a PR; before adding CI steps or jobs |
| `agentic_workflow_rules.md` | How AI agents must behave in this repo; session constraints; required output format; ADR maintenance obligation | At the start of every AI-assisted session |
| `security_and_branch_protection.md` | GitHub branch protection required checks; secret scanning guidance; demo credential policy; gate classification | When adding CI jobs; when configuring GitHub repository settings |
| `notification_wiring.md` | Step-by-step guide for wiring live Slack and SMTP email notifications through GitHub Actions repository secrets | When enabling live notification delivery |
| `architecture_decision_log.md` | ADR entries for major architectural decisions: what was decided, why, what alternatives were rejected, and what is deferred | When making tooling or architecture decisions; when onboarding to the repo |
