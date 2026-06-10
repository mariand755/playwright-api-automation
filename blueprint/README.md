# QA Architecture Blueprint — Replication Guide

## Purpose

This guide explains how to adapt the patterns from this repo to another Python/pytest API/UI automation project. The working implementation here is the reference — this guide describes the adaptation path, not a recipe to copy files verbatim.

## Who This Is For

- A consulting engineer setting up QA infrastructure for a new client project
- A QA architect evaluating which patterns to adopt from this stack
- An engineering lead who wants to understand how these patterns connect before applying them

## Reference Implementation

This repo demonstrates each blueprint pattern in a working, production-style context:

- 7 API + 6 UI + 25 script unit tests with TC-ID traceability and JUnit reporting
- Docker-first 4-job CI pipeline with smoke/full scope gating and nightly regression
- Multi-signal release readiness gate (JUnit + observability + defect signals → GO/NO_GO)
- Slack + SMTP notification delivery, dry-run by default, activation-gated
- ADR-backed governance layer with suite taxonomy, quality gates, and activation guides

Every blueprint area below points to working source files. Use them as the reference, not as files to copy.

## Replication Sequence

Apply these patterns in order. Each builds on the previous:

1. Test suite structure — pytest.ini, conftest.py, marker taxonomy, TC-ID system
2. CI quality gate pipeline — Docker-first 4-job pipeline, smoke/full scope gating, code quality gates
3. Release readiness gate — JUnit + observability + defect signals → GO/NO_GO
4. Notification delivery — Slack + SMTP, dry-run default, activation-gated
5. Governance layer — ADR-backed decisions, suite taxonomy, quality gates, activation guides
6. Agentic QA workflow — Mode A/B review gates, planning templates, governance-first prompts
7. Observability integration — stub-first, explicit activation conditions, provider-independent

---

## Blueprint Areas

Sections below are grouped by dependency complexity, not by application order — see Replication Sequence above for the recommended order to apply these patterns to a new repo.

### 1. CI Quality Gate Pattern

A 4-job pipeline (Docker Test Suite → API Tests ∥ UI Tests → Notify) with smoke-only runs on PR/feature branch push and full-suite runs on push to main, nightly, and `workflow_dispatch`. The Docker Test Suite job runs all code quality gates (Ruff, mypy, pip-audit, Trivy) and script unit tests before any behavioral tests run.

**Reference:** [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml) · [`../agentic-qa-workflows/governance/quality_gates.md`](../agentic-qa-workflows/governance/quality_gates.md)

**Configure for a new repo:**
- Job names (rename `API Tests` / `UI Tests` to match your test domains)
- Docker image name and `COPY` paths
- `if:` condition on the `Notify` job (trigger rules for your project)
- Remove the prod-read-only guarded steps until you have an equivalent ADR

---

### 2. Release Readiness Pattern

`scripts/release_gate.py` consumes JUnit XML + observability snapshot + defect metrics and produces a GO / NO_GO / UNKNOWN decision as JSON and Markdown artifacts. On smoke runs, it writes a `gate_skipped: true` placeholder so the Notify job always has an artifact to consume.

**Blueprint asset:** [`scripts/release_gate.py`](scripts/release_gate.py) — extracted reusable template with adaptation points annotated; start here for new projects.

**Live source reference:** [`../scripts/release_gate.py`](../scripts/release_gate.py) · [`../data/release/observability_snapshot.json`](../data/release/observability_snapshot.json) · [`../data/release/defect_metrics.json`](../data/release/defect_metrics.json) — working implementation used by this repo's CI.

**Configure for a new repo:** Override input/output paths via CLI args: `--observability-json`, `--defect-metrics-json`, `--output-json`, `--output-md`. The positional XML arg handles the JUnit report path. All args default to this repo's artifact layout — pass your paths explicitly to adapt to a new repo without modifying the script.

**Release gate semantics:** The gate exits `1` on `NO_GO`, which blocks CI; use `continue-on-error: true` if the gate should be advisory only. Running the gate before live observability is connected can produce `GO` from clean sample data — that is not production release evidence. Review ADR-017 activation conditions before using this gate for production release decisions.

---

### 3. Notification Policy Pattern

`scripts/notify.py` is a stdlib-only script (zero dependencies). Both Slack and SMTP/email dry-run by default — CI never fails due to missing credentials. Each channel checks its own env vars independently. The script runs directly on the GitHub Actions runner without a Docker build.

**Blueprint asset:** [`scripts/notify.py`](scripts/notify.py) — extracted reusable template with adaptation points annotated; start here for new projects.

**Live source reference:** [`../scripts/notify.py`](../scripts/notify.py) · [`../agentic-qa-workflows/governance/notification_wiring.md`](../agentic-qa-workflows/governance/notification_wiring.md) — working implementation used by this repo's CI.

**Configure for a new repo:** Rename the three job-result env var names in your `ci.yml` notify step to match your actual job names — `DOCKER_TEST_SUITE_RESULT`, `API_TESTS_RESULT`, `UI_TESTS_RESULT` are this repo's names.

**Activation prerequisites:**
- **Slack:** add `SLACK_WEBHOOK_URL` as a GitHub Actions Secret
- **SMTP/email:** add `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `NOTIFY_RECIPIENTS`; validate against your runner's SMTP restrictions (port 465 or a transactional email API may be required)

---

### 4. Governance Pattern

An ADR-backed governance layer that documents every structural decision, defines suite taxonomy and marker conventions, enforces quality gates, and establishes explicit activation conditions for each deferred capability.

**Reference:** [`../agentic-qa-workflows/governance/`](../agentic-qa-workflows/governance/)

**Key files to read and adapt (do not copy verbatim):**

| File | What transfers |
|---|---|
| [`architecture_decision_log.md`](../agentic-qa-workflows/governance/architecture_decision_log.md) | ADR format: title, status, context, decision, consequences, activation conditions |
| [`suite_taxonomy.md`](../agentic-qa-workflows/governance/suite_taxonomy.md) | Marker taxonomy (area + scope + traceability), TC-ID prefix conventions |
| [`quality_gates.md`](../agentic-qa-workflows/governance/quality_gates.md) | PR gate / merge gate / release gate philosophy |
| [`page_object_api_rules.md`](../agentic-qa-workflows/governance/page_object_api_rules.md) | POM and API client ownership — fully transferable as-is |
| [`test_data_env_rules.md`](../agentic-qa-workflows/governance/test_data_env_rules.md) | Data isolation and environment selection rules — mostly transferable |
| [`failure_evidence.md`](../agentic-qa-workflows/governance/failure_evidence.md) | Screenshot/HTML capture, API failure context, CodeQL secret-taint rules |
| [`agentic_workflow_rules.md`](../agentic-qa-workflows/governance/agentic_workflow_rules.md) | AI-assisted workflow constraints — fully transferable as-is |

**Do not copy the ADRs.** Every ADR in this repo is specific to its own decisions. Start fresh from the ADR format.

---

### 5. Agentic QA Workflow Pattern

A governance-first agentic workflow where every implementation slice gets a Mode A plan review (before editing) and a Mode B implementation review (before committing). Prompts are repo-agnostic and ready to use in any Python automation project.

**Reference:** [`../agentic-qa-workflows/prompts/`](../agentic-qa-workflows/prompts/)

| Prompt | Purpose |
|---|---|
| [`qa_architect_slice_review_prompt.md`](../agentic-qa-workflows/prompts/qa_architect_slice_review_prompt.md) | Mode A/B review — no repo-specific content; use directly |
| [`slice_planning_prompt_template.md`](../agentic-qa-workflows/prompts/slice_planning_prompt_template.md) | Planning template — fill in `[PLACEHOLDER]` values for your repo |
| [`governance_compliance_audit_prompt.md`](../agentic-qa-workflows/prompts/governance_compliance_audit_prompt.md) | Governance audit — adapt the file list section to your repo |

See [`prompts/README.md`](prompts/README.md) for the complete 4-step workflow guide and full prompt inventory. Source files stay in `agentic-qa-workflows/prompts/` — the blueprint guide links to them rather than copying them.

---

### 6. Test Suite Structure Pattern

Three test layers — API (pytest + Requests), UI (pytest + Playwright), script unit tests — each with area markers (`api`, `ui`, `scripts`) and execution-scope markers (`smoke`, `regression`, `negative`, `api_contract`). Every test carries a TC-ID for JUnit traceability. Fixtures own setup/teardown; tests own assertions.

**Reference:** [`../pytest.ini`](../pytest.ini) · [`../conftest.py`](../conftest.py) · [`../agentic-qa-workflows/governance/suite_taxonomy.md`](../agentic-qa-workflows/governance/suite_taxonomy.md)

**Configure for a new repo:**
- `pytest.ini` — update `testpaths`, declare your marker set
- `conftest.py` — replace the `test_users.json` environment selection with your URL/credential source; keep the `pytest_runtest_makereport` hook for UI failure capture
- Your TC-ID prefix (e.g., `TC-API-001`, `TC-UI-001`)

**Do not copy test files.** The test implementations are SauceDemo / Restful Booker specific. The pattern (TC-ID + area marker + scope marker, fixture-owned setup, assertion messages with URL/status/body) is what transfers.

---

### 7. Observability Integration Pattern

A stub-first adapter (`pull_observability.py`) that documents the Datadog/Grafana/PagerDuty API call interface without making real calls. The release gate evaluates against static sample data until a live provider is connected.

**Reference:** [`../scripts/pull_observability.py`](../scripts/pull_observability.py) · [`../agentic-qa-workflows/governance/observability_wiring.md`](../agentic-qa-workflows/governance/observability_wiring.md)

These files are already the blueprint. Copy both to a new repo. Follow the 5-condition activation checklist in `observability_wiring.md` when a live observability stack is available.

---

## What Not to Copy Blindly

| File / Asset | Why |
|---|---|
| `.github/workflows/ci.yml` | Prod-read-only steps and inline ADR references are repo-specific; adapt the pattern |
| `agentic-qa-workflows/governance/architecture_decision_log.md` | All ADRs are specific to this repo's decisions; start fresh from the format |
| `scripts/release_gate.py` | Input/output paths configurable via CLI args; set `--output-json` and `--output-md` to match your artifact layout; `--observability-json` and `--defect-metrics-json` default to this repo's sample data — replace with your own |
| All test files (`test_booking_api.py`, `test_login_cart.py`, etc.) | SauceDemo / Restful Booker specific; follow the pattern, do not copy |
| `conftest.py` | `test_users.json` env structure is repo-specific; keep the fixture architecture, replace the data source |

---

## What This Blueprint Does Not Provide

- A packaged or SaaS-deployable product
- Cross-browser test execution (architecture is xdist-ready; not yet activated)
- Live production observability (stub-backed until a provider is connected)
- Validated SMTP email delivery (infrastructure-ready; runner SMTP restrictions may require a transactional API)
- Compliance certification
- A second-repo case study (planned in a future extraction slice)

---

## Safe Adaptation Principles

1. **Adapt structure, not content.** Use working files as shape references; replace all repo-specific values.
2. **Write an ADR before activating any deferred capability.** Dry-run defaults and activation checklists exist for this reason.
3. **Follow governance rules, don't copy governance content.** `page_object_api_rules.md`, `test_data_env_rules.md`, and `failure_evidence.md` transfer directly; the ADR log does not.
4. **Do not skip Mode A plan review.** Use `slice_planning_prompt_template.md` before editing files.
5. **Validate with Docker.** Local pytest is advisory only; Docker CI is the source of truth.
6. **Review data flows before activating external channels.** See [`data_handling_guide.md`](data_handling_guide.md) for a consolidated view of what data this framework produces, where it goes, and what controls to evaluate before enabling notifications, observability, or prod-read-only testing.

---

## Extraction Slices

| Slice | Content | Status |
|---|---|---|
| Slice 2 | [`blueprint/prompts/README.md`](prompts/README.md) — agentic QA workflow guide | Done — PR #44 |
| Data handling guide | [`blueprint/data_handling_guide.md`](data_handling_guide.md) — data flows, sensitivity notes, activation checklist | Done — PR #45 (out-of-sequence) |
| Slice 3 | [`blueprint/scripts/notify.py`](scripts/notify.py) — stdlib-only notification script with adaptation notes | Done — PR #49 |
| Slice 4 | [`blueprint/scripts/release_gate.py`](scripts/release_gate.py) — release readiness gate with adaptation points annotated | Done — this PR |
| Slice 5 | `blueprint/governance/` — blank ADR template, suite taxonomy template | Future — after Slice 4 |
| Slice 6 | Second repo application + case study | Future — after full `blueprint/` folder stable |
