# Architecture Decision Log

This file records significant architectural decisions made in this repository. Each entry explains what was decided, why, what alternatives were considered, and what trade-offs were accepted.

For the governance rule that applies when adding new entries, see [`agentic_workflow_rules.md`](agentic_workflow_rules.md).

---

## Index

| ADR | Title | Status | Date |
|---|---|---|---|
| [ADR-001](#adr-001-docker-first-execution-as-source-of-truth) | Docker-first execution as source of truth | Accepted | 2026-04-12 |
| [ADR-002](#adr-002-ruff-as-single-formatlint-tool) | Ruff as single format+lint tool | Accepted | 2026-05-01 |
| [ADR-003](#adr-003-mypy-with-pragmatic-initial-strictness) | mypy with pragmatic initial strictness | Accepted | 2026-05-01 |
| [ADR-004](#adr-004-pip-audit-for-python-dependency-scanning) | pip-audit for Python dependency scanning | Accepted | 2026-05-01 |
| [ADR-005](#adr-005-trivy-for-container-image-scanning-sha-pinned) | Trivy for container image scanning, SHA-pinned | Accepted | 2026-05-01 |
| [ADR-006](#adr-006-codeql-as-a-separate-github-native-workflow) | CodeQL as a separate GitHub-native workflow | Accepted | 2026-05-01 |
| [ADR-007](#adr-007-dependabot-with-playwright-version-ignored) | Dependabot with playwright version ignored | Accepted | 2026-05-01 |
| [ADR-008](#adr-008-three-named-ci-jobs-instead-of-matrix-for-apiui-split) | Three named CI jobs instead of matrix for API/UI split | Accepted | 2026-06-01 |
| [ADR-009](#adr-009-api-only-release-gate-multi-source-deferred) | API-only release gate, multi-source deferred | Accepted | 2026-06-01 |
| [ADR-010](#adr-010-branch-protection-operates-on-job-names-not-step-names) | Branch protection operates on job names, not step names | Accepted | 2026-06-01 |
| [ADR-011](#adr-011-notification-delivery-defaults-to-dry-run-when-secrets-are-absent) | Notification delivery defaults to dry-run when secrets are absent | Accepted | 2026-06-01 |
| [ADR-012](#adr-012-pre-commit-as-advisory-local-guardrail-docker-ci-as-source-of-truth) | Pre-commit as advisory local guardrail; Docker CI as source of truth | Accepted | 2026-06-02 |
| [ADR-013](#adr-013-bounded-adjacent-risk-scan-in-qa-reviewer-prompts) | Bounded adjacent-risk scan in QA reviewer prompts | Accepted | 2026-06-02 |
| [ADR-014](#adr-014-smoke-only-ci-on-pr-and-feature-branch-push-full-suite-on-main-nightly-and-workflow_dispatch) | Smoke-only CI on PR and feature branch push; full suite on main, nightly, and workflow_dispatch | Accepted | 2026-06-02 |
| [ADR-015](#adr-015-cross-environment-selection-with-staging-default-and-prod-read-only-activation-gate) | Cross-environment selection with staging default and prod-read-only activation gate | Accepted | 2026-06-03 |
| [ADR-016](#adr-016-aggregate-ci-notification-job-after-all-required-jobs-complete) | Aggregate CI notification job after all required jobs complete | Accepted | 2026-06-03 |
| [ADR-017](#adr-017-observability-snapshot-populated-via-stub-pending-live-stack-connection) | Observability snapshot populated via stub pending live stack connection | Accepted | 2026-06-03 |
| [ADR-018](#adr-018-failure-only-aggregate-notification-on-push-to-main) | Failure-only aggregate notification on push to main | Accepted | 2026-06-06 |
| [ADR-019](#adr-019-independent-judgment-preface-in-qa-reviewer-and-planning-prompts) | Independent judgment preface in QA reviewer and planning prompts | Accepted | 2026-06-06 |
| [ADR-020](#adr-020-script-unit-test-layer-for-release-readiness-and-notification-decision-logic) | Script unit test layer for release-readiness and notification decision logic | Accepted | 2026-06-06 |
| [ADR-021](#adr-021-workflow_dispatch-inputs-for-parameterized-manual-ci-runs) | workflow_dispatch inputs for parameterized manual CI runs | Accepted | 2026-06-07 |
| [ADR-022](#adr-022-blueprint-prompt-packaging--link-to-working-prompt-files-do-not-copy) | Blueprint prompt packaging — link to working prompt files, do not copy | Accepted | 2026-06-09 |
| [ADR-023](#adr-023-dependency-update-triage-workflow) | Dependency update triage workflow | Accepted | 2026-06-08 |
| [ADR-024](#adr-024-pr-failure-notifications-behind-notify_pr_failures-activation-gate) | PR failure notifications behind NOTIFY_PR_FAILURES activation gate | Accepted | 2026-06-10 |
| [ADR-025](#adr-025-dockerfile-os-package-upgrade-for-cve-remediation) | Dockerfile OS package upgrade for CVE remediation | Accepted | 2026-06-10 |
| [ADR-026](#adr-026-dependency-review-action-as-advisory-pr-dependency-diff-gate) | Dependency Review Action as advisory PR dependency-diff gate | Accepted | 2026-06-11 |
| [ADR-027](#adr-027-gmail-smtp-live-delivery-validation-outcome) | Gmail SMTP live delivery validation outcome | Accepted | 2026-06-14 |
| [ADR-028](#adr-028-api-pytest-xdist-activation-with-serial-ui-and-script-execution) | API pytest-xdist activation with serial UI and script execution | Accepted | 2026-06-14 |
| [ADR-029](#adr-029-ui-pytest-xdist-activation-with-serial-script-and-prod-read-only-execution) | UI pytest-xdist activation with serial script and prod-read-only execution | Accepted | 2026-06-15 |
| [ADR-030](#adr-030-cross-browser-ui-matrix-and-cloud-grid-preflight-with-safe-skip-policy) | Cross-browser UI matrix and cloud-grid preflight with safe-skip policy | Accepted | 2026-06-14 |
| [ADR-031](#adr-031-sauce-labs-cloud-grid-execution-gated-by-preflight-readiness) | Sauce Labs cloud-grid execution gated by preflight readiness | Accepted | 2026-06-14 |
| [ADR-032](#adr-032-advisory-job-notification-and-cloud-grid-provider-failure-messaging) | Advisory job notification and cloud-grid provider-failure messaging | Accepted | 2026-06-15 |

---

## ADR-001: Docker-first execution as source of truth

**Status:** Accepted
**Date:** 2026-04-12

### Context

Tests needed to run consistently across local developer machines, CI runners, and team environments. Python version differences, playwright browser binary versions, and system dependency variance caused "works on my machine" class failures.

### Decision

Docker is the source-of-truth validation path. All CI gates — format, lint, type check, security scans, and test execution — run inside Docker. Local runs using a Python venv are supported as optional fast feedback only and do not replace Docker verification.

### Alternatives considered

- **Python venv with pinned requirements on the CI runner** — rejected because playwright browser binary installation, system library dependencies (libglib, libX11, etc.), and Python version cannot be pinned with the same fidelity as a Docker image.
- **GitHub Actions `setup-python` + `playwright install`** — rejected for the same reason. The runner environment differs across GitHub Actions image versions and cannot be locked to the same state as a developer machine.

### Consequences

Every CI step runs `docker build` followed by `docker run`. No `setup-python` step exists in any workflow. Local venv remains optional fast feedback. All quality gates and test results are Docker-produced.

### Activation condition

Reconsider if Docker build time consistently exceeds 5 minutes and Docker layer caching is not implemented. Reconsider if a cloud-native test execution platform (e.g., Sauce Labs, BrowserStack) is adopted as the primary runner and replaces Docker as the execution environment.

### Related PRs / Docs

- PR #2 (`feature/from-main-20260412`) — initial Docker-first CI workflow
- `README.md` — Run with Docker section
- `quality_gates.md` — Docker-First Quality Checks section

### Trade-offs and consulting value

Docker-first validation eliminates the "works on my machine" class of failure. The trade-off is longer CI wall time compared to a bare-runner Python setup. For a consulting client, this pattern is the most defensible approach to reproducible CI: the image definition is checked in, every run produces identical conditions, and onboarding a new engineer requires only Docker, not a carefully matched local Python environment.

---

## ADR-002: Ruff as single format+lint tool

**Status:** Accepted
**Date:** 2026-05-01

### Context

A format and lint gate was required in CI to enforce consistent code style and catch common errors. The Python ecosystem offers several separate tools: Black (formatting), Flake8 (linting), and isort (import ordering).

### Decision

Ruff handles formatting, linting, and import ordering in a single tool. Two CI steps exist: `ruff format --check .` and `ruff check .`. Configuration lives in `pyproject.toml` under `[tool.ruff]` and `[tool.ruff.lint]`.

### Alternatives considered

- **Black + Flake8 + isort** — three separate tools, three separate config sections, three separate CI steps, three separate `pip install` entries. Higher maintenance overhead with no meaningful quality improvement over Ruff at this project's scale.
- **Pylint** — heavier, slower, and more configuration-intensive. Better suited to mature codebases with established pylint rule sets. Premature for a project at this scale.

### Consequences

`pyproject.toml` holds all Ruff config. CI runs two Docker steps (format check, lint check) in the Docker Test Suite job. No other format or lint tooling is installed.

### Activation condition

Add a targeted Flake8 or pylint step only if a specific rule class is required that Ruff cannot enforce. No current activation condition is anticipated.

### Related PRs / Docs

- Phase 6.5 CI quality gates slice
- `pyproject.toml` — Ruff configuration
- `.github/workflows/ci.yml` — Docker Test Suite job (Check formatting and Lint steps)
- `quality_gates.md` — required checks items 4 and 5

### Trade-offs and consulting value

Single-tool approach reduces dependency management overhead and CI config complexity. Trade-off: Ruff is a newer tool with less enterprise adoption history than Flake8. For a consulting client, the single-tool approach reduces onboarding friction — engineers only need to understand one tool's configuration and error messages rather than coordinating Black, Flake8, and isort separately.

---

## ADR-003: mypy with pragmatic initial strictness

**Status:** Accepted
**Date:** 2026-05-01

### Context

Static type checking was required in CI to catch type regressions in production modules. Python test files and `conftest.py` use pytest fixtures with framework-internal return types (e.g., `Page`, `BrowserContext`) that require additional stubs and configuration to annotate correctly.

### Decision

mypy runs on `utils/`, `pages/`, and `scripts/` only. Configuration in `pyproject.toml`:

```ini
ignore_missing_imports = true
explicit_package_bases = true
```

Test files and `conftest.py` are excluded. Third-party libraries without stubs (e.g., `requests`) are silently skipped rather than errored.

### Alternatives considered

- **Full strict mode (`disallow_untyped_defs`, no `ignore_missing_imports`)** — rejected because `requests` and `playwright` do not ship complete type stubs. Enabling full strict mode before stubs are available causes cascading errors across all HTTP calls and page interactions before any useful coverage is achieved.
- **No type checking** — rejected because CI would miss type regressions in the production API client, page objects, and utility modules. Even partial coverage is significantly better than none.

### Consequences

CI catches type errors in production modules. Test file annotation is deferred. `requests.Response` fields inferred as `Any` are not type-checked at call sites.

### Activation condition

Expand to `disallow_untyped_defs = true` when annotation coverage in production modules exceeds approximately 80%. Add `types-requests` stub when strictness is increased. Extend to `conftest.py` when pytest fixture typing is configured. Track these as a dedicated "mypy strictness expansion" slice.

### Related PRs / Docs

- Phase 6.5 CI quality gates slice
- `pyproject.toml` — mypy configuration
- `.github/workflows/ci.yml` — Docker Test Suite job (Type check step)
- `quality_gates.md` — required check item 9

### Trade-offs and consulting value

Fast to adopt, avoids stub-hunting at initial setup. Trade-off: does not catch unannotated function signatures in production modules. For a consulting client, this demonstrates the correct pragmatic mypy adoption path: start with coverage on production modules and `ignore_missing_imports`, expand incrementally as annotation density grows. This is the pattern the mypy documentation recommends for brownfield adoption.

---

## ADR-004: pip-audit for Python dependency scanning

**Status:** Accepted
**Date:** 2026-05-01

### Context

A Python dependency vulnerability scan was required in CI to catch known CVEs in `requirements.txt` packages before they reach production.

### Decision

`pip-audit` queries the OSV and PyPI advisory databases. It runs inside Docker as a required gate in the Docker Test Suite job: `pip-audit -r requirements.txt --progress-spinner off`.

### Alternatives considered

- **Safety** — requires a paid tier for an up-to-date vulnerability database. Free tier has a delayed feed. Rejected on cost grounds.
- **Snyk** — external SaaS with API token management, webhook configuration, and a commercial license for full features. Adds external dependency and account management overhead for a project that can be scanned adequately by OSV.
- **GitHub Dependabot alone** — Dependabot provides update PRs but does not fail CI on a detected CVE. pip-audit provides the blocking gate that Dependabot does not.

### Consequences

Any known CVE in a `requirements.txt` dependency fails the Docker Test Suite job. Output is plain text in CI logs. No external reporting or SBOM generation is wired up.

### Activation condition

Reconsider if OSV advisory database coverage is insufficient for a specific CVE class required by a client compliance framework. Evaluate `--format cyclonedx` if SBOM generation becomes a contractual requirement (pip-audit supports this flag without additional tooling).

### Related PRs / Docs

- Phase 6.5 CI quality gates slice
- `requirements.txt`
- `.github/workflows/ci.yml` — Docker Test Suite job (Python dependency scan step)
- `quality_gates.md` — required check item 7

### Trade-offs and consulting value

Zero cost, zero external token management, runs entirely inside Docker with no external service dependency beyond the OSV advisory database query. Trade-off: OSV coverage is broad but not identical to commercial vulnerability databases — some CVEs may appear in commercial databases days before OSV. For a consulting client, pip-audit demonstrates free, reproducible supply-chain hygiene that can be adopted on any project without procurement or SaaS onboarding.

---

## ADR-005: Trivy for container image scanning, SHA-pinned

**Status:** Accepted
**Date:** 2026-05-01

### Context

Container image vulnerability scanning was required to catch fixable HIGH and CRITICAL CVEs in Docker image layers before merge to main. The scan needed to run in CI as a blocking gate.

### Decision

`aquasecurity/trivy-action` is used in `ci.yml`, pinned to a specific commit SHA (not a floating version tag). Scan scope: fixable HIGH/CRITICAL CVEs only (`--ignore-unfixed`, `--severity HIGH,CRITICAL`, `exit-code: '1'`).

### Alternatives considered

- **Snyk container scan** — requires an external API token and SaaS account. Rejected for the same reasons as ADR-004.
- **Docker Scout** — built into Docker Hub but requires a Docker Hub account and has rate limits on the free tier. Rejected on account management overhead.
- **Grype (Anchore)** — similar capabilities to Trivy, less mature GitHub Actions integration at the time of adoption.

### Consequences

The Trivy action is pinned to commit SHA `ed142fd0673e97e23eac54620cfb913e5ce36c25` (v0.36.0). Any fixable HIGH/CRITICAL CVE in the built Docker image blocks the Docker Test Suite job. Unfixable CVEs are reported in logs but do not block CI.

### Activation condition

Update the SHA pin when Trivy releases a version with required vulnerability database improvements, a critical bug fix, or a feature needed by a client compliance framework. Re-evaluate scope (severity thresholds, unfixed policy) if a specific compliance framework (SOC 2, FedRAMP) requires different thresholds.

### Related PRs / Docs

- Phase 6.5 CI quality gates slice
- `.github/workflows/ci.yml` — Docker Test Suite job (Container image scan step)
- `security_and_branch_protection.md` — gate classification table
- `quality_gates.md` — required check item 8

### Trade-offs and consulting value

Free, runs natively in GitHub Actions, zero external token management. SHA-pinning mitigates the supply-chain attack vector on the action itself — a compromised floating tag could inject malicious behavior into CI. The `--ignore-unfixed` policy avoids blocking CI on CVEs with no available fix, which is a common source of CI noise that causes teams to disable scanning entirely. For a consulting client, SHA-pinning third-party actions is a demonstrable supply-chain hygiene practice that most client CI configurations lack.

---

## ADR-006: CodeQL as a separate GitHub-native workflow

**Status:** Accepted
**Date:** 2026-05-01

### Context

Static security analysis was required. The question was whether to run CodeQL as a step in `ci.yml` or as a dedicated workflow file. CodeQL has significantly longer runtime than the other CI gates and requires different scheduling (weekly re-scan to apply updated queries to the current codebase).

### Decision

CodeQL runs in a dedicated `codeql.yml` workflow. Findings are advisory — published to GitHub Security → Code scanning alerts — rather than CI-blocking. The workflow runs on push/PR to main and weekly at 06:00 UTC Monday. `Analyze Python` is a required status check for merge: the workflow run must complete successfully, but zero findings are not required.

### Alternatives considered

- **CodeQL as a step in `ci.yml`** — rejected because CodeQL runtime (1–3 minutes for Python) would extend PR feedback time for every commit. The weekly re-scan cadence also has no natural home inside the main CI trigger. Coupling behavioral CI (test suite) with static security analysis (CodeQL) is a separation-of-concerns violation.
- **CodeQL findings as a hard blocking gate** — rejected at initial setup because a severity threshold policy was out of scope for this slice. Making findings blocking without a threshold means a low-severity advisory in a demo dependency blocks all merges.

### Consequences

`codeql.yml` runs on push/PR to main and weekly. Findings appear in GitHub Security → Code scanning alerts. The `Analyze Python` required check ensures the analysis completed — not that findings are zero.

### Activation condition

Convert findings to a blocking gate if the project adopts a formal security severity SLA (e.g., HIGH/CRITICAL findings must be resolved within a defined window before merge is permitted).

### Related PRs / Docs

- Phase 6.5 CI quality gates slice
- `.github/workflows/codeql.yml`
- `security_and_branch_protection.md` — Analyze Python required check, CodeQL advisory note, gate classification table

### Trade-offs and consulting value

Decoupled scheduling allows weekly re-scanning with updated CodeQL queries independent of the PR CI cadence. Advisory-only findings prevent low-severity alerts from blocking delivery while still surfacing them for review. Trade-off: findings require active engineer review discipline — they are not automatically surfaced in PR comments without additional GitHub configuration. For a consulting client, the separation of behavioral CI and static security analysis is a mature architectural pattern that scales to large codebases without adding PR latency.

---

## ADR-007: Dependabot with playwright version ignored

**Status:** Accepted
**Date:** 2026-05-01

### Context

Automated dependency update visibility was required. Dependabot was configured for two ecosystems: `pip` (Python packages) and `github-actions` (CI actions). The `playwright` Python package version is coupled to the Docker base image tag (`mcr.microsoft.com/playwright/python`).

### Decision

Dependabot is configured with an ignore rule for the `playwright` dependency (`versions: ["*"]`). All other pip packages and GitHub Actions receive automated update PRs on a weekly schedule.

### Alternatives considered

- **Allow Dependabot to update playwright freely** — rejected. A playwright version bump in `requirements.txt` without a corresponding Docker base image tag update produces a broken container where the installed package version mismatches the pre-installed browser binaries in the base image. This creates recurring CI noise with a non-obvious root cause.
- **Pin playwright in a separate locked requirements file** — adds complexity without solving the coordination problem between the package version and the base image tag.

### Consequences

playwright updates require a coordinated slice: update both the Docker base image tag in `Dockerfile` and the `playwright` version in `requirements.txt` together. Dependabot will not open PRs for playwright. All other pip packages and GitHub Actions updates are automatic.

### Activation condition

Remove the Dependabot ignore rule when a coordinated playwright/Docker base image update process is established — specifically, when a "playwright update" slice template exists in the prompt library that handles the base image + package version coordination correctly.

### Related PRs / Docs

- Phase 6.5 CI quality gates slice
- `.github/dependabot.yml`
- `Dockerfile` — base image tag (`mcr.microsoft.com/playwright/python:...`)
- `requirements.txt` — `playwright` package version

### Trade-offs and consulting value

Avoids recurring broken-CI noise from mismatched playwright/base-image versions. Trade-off: playwright updates require manual attention and a coordinated slice — they will fall behind if not actively monitored. For a consulting client, this documents a common and poorly-understood coupling between Docker base image tags and runtime package versions. The documented ignore rule is a deliberate choice with a clear activation condition, not an oversight.

---

## ADR-008: Three named CI jobs instead of matrix for API/UI split

**Status:** Accepted
**Date:** 2026-06-01

### Context

API and UI test suites needed to run in parallel so that failures in one suite do not hide results from the other. Two implementation approaches were available: `strategy.matrix` or individually named jobs.

### Decision

Three named jobs were created: `Docker Test Suite` (job ID: `test`), `API Tests` (job ID: `api`), and `UI Tests` (job ID: `ui`). The `API Tests` and `UI Tests` jobs run in parallel after `Docker Test Suite` passes (`needs: [test]`). Jobs are defined individually, not via a matrix.

### Alternatives considered

- **`strategy.matrix` with `{suite: [api, ui]}`** — rejected because `API Tests` and `UI Tests` have heterogeneous post-processing chains. `API Tests` runs the release readiness gate. `UI Tests` uploads failure artifacts (screenshots, HTML dumps). Implementing this in a matrix requires `if: matrix.suite == 'api'` conditionals on multiple steps, reducing YAML readability and increasing the risk of misconfigured step conditions.

### Consequences

Each job runs on its own GitHub Actions runner with its own Docker build. JUnit XML output files are named separately (`api-report.xml`, `ui-report.xml`) and mounted via volume — no collision. `$GITHUB_STEP_SUMMARY` is job-scoped: both jobs writing `## Test Summary` produces no content collision. Docker image is rebuilt per runner; layer caching between jobs is a deferred optimization.

### Activation condition

- Add Docker layer caching when build time consistently exceeds 3 minutes per runner.
- Re-evaluate matrix if the `API Tests` and `UI Tests` post-processing chains converge (e.g., both run the release gate with separate XML inputs).
- Add new named jobs (e.g., `Mobile Tests`) when additional suites with distinct post-processing requirements are introduced.

### Related PRs / Docs

- PR #20 (`feature/scheduled-regression-api-ui-split`) — API/UI CI job split
- `.github/workflows/ci.yml`
- `security_and_branch_protection.md` — required checks section, CI job structure
- `quality_gates.md` — CI job structure table
- ADR-009 (API-only release gate)
- ADR-010 (branch protection job names)

### Trade-offs and consulting value

Named jobs produce more readable YAML than a conditional matrix. Each job's purpose is self-evident from its name. Trade-off: Docker image is rebuilt on each runner, adding wall-clock time proportional to build time. For a consulting client, this pattern is the correct tool when post-processing steps differ per parallel job — it demonstrates that parallelization decisions should be driven by correctness of the output chain, not only by speed.

---

## ADR-009: API-only release gate, multi-source deferred

**Status:** Accepted
**Date:** 2026-06-01

### Context

The release readiness gate (`scripts/release_gate.py`) consumes JUnit XML + observability + defect metrics and produces a GO/NO_GO decision. After the API/UI split (ADR-008), two JUnit XML files exist: `api-report.xml` and `ui-report.xml`. The gate needed to work with the split without requiring a new consolidation step.

### Decision

The release gate runs in the `API Tests` job only, consuming `artifacts/api-report.xml`. The script was updated to accept the XML path as `sys.argv[1]` (backward-compatible; defaults to `artifacts/report.xml` if no argument is provided). UI test failures are surfaced through the `UI Tests` required check blocking merge, not through the release gate output.

### Alternatives considered

- **Run the release gate in both `API Tests` and `UI Tests`** — rejected. Two GO/NO_GO outputs with different source scopes (API-only vs. UI-only) create confusing duplicate gate summaries in the GitHub Actions job summary. The value of a single gate decision is that it is unambiguous.
- **Consolidate both XML files before running the gate** — technically the correct long-term approach. Deferred because it requires a consolidation script or multi-file parsing in `release_gate.py` that was not in scope for the API/UI split slice.

### Consequences

The release gate reflects API test results only. If all API tests pass but UI tests fail, the release gate shows GO but the `UI Tests` required check blocks merge. The combined merge protection is equivalent to a full-suite gate: both required checks must pass. Full multi-source consolidation is deferred.

### Activation condition

Implement multi-source release gate consolidation when both API and UI suites each exceed 20 tests, OR when a stakeholder requires a single unified GO/NO_GO signal covering both suites in one report. The consolidation approach should parse both `api-report.xml` and `ui-report.xml` and merge test result totals before evaluating gate thresholds.

### Related PRs / Docs

- PR #20 (`feature/scheduled-regression-api-ui-split`) — `sys.argv[1]` change to `release_gate.py`
- `scripts/release_gate.py` — line 10
- `.github/workflows/ci.yml` — API Tests job, Run release readiness gate step
- `quality_gates.md` — Release Gate section
- ADR-008 (named CI jobs)

### Trade-offs and consulting value

Minimal change to `release_gate.py` (one-line addition). No new script required. UI failures are still blocked by the `UI Tests` required check. Trade-off: the gate is narrower than the full test signal — API results alone do not represent overall product release readiness. For a consulting client, this demonstrates a pragmatic deferral pattern with a documented activation condition: the decision is not "we forgot UI results," it is a deliberate scope choice with a clear trigger for the next step.

---

## ADR-010: Branch protection operates on job names, not step names

**Status:** Accepted
**Date:** 2026-06-01

### Context

GitHub branch protection "required status checks" references CI job names as they appear in the GitHub Actions run — not individual step names within a job. After the API/UI split added `API Tests` and `UI Tests` as new jobs, the branch protection rule needed updating. The existing `Docker Test Suite` job name also needed to be preserved to avoid disrupting the branch protection rule already in place.

### Decision

The `Docker Test Suite` job name was preserved after the API/UI split (job ID: `test`, display name: `Docker Test Suite`). Individual steps within it — Check formatting, Lint, Type check, Python dependency scan, Container image scan, Verify test collection — are internal and not separately addressable as required checks. The four required checks for merge to `main` are:

```text
Docker Test Suite
API Tests
UI Tests
Analyze Python
```

A post-merge update is required each time new jobs are added: after the new jobs run on `main` at least once, go to GitHub Settings → Branches → branch protection rule and add the new job names. Job names appear in GitHub's required-check autocomplete only after they have run on the default branch.

### Alternatives considered

- **Rename `Docker Test Suite` during the split** — rejected. Renaming a job that is already a required check removes it from branch protection silently (the old name no longer exists; GitHub does not auto-update required check references). This would have temporarily removed the quality gate before the new job names could be added, creating a window where unprotected merges were possible.

### Consequences

`Docker Test Suite` is now a load-bearing job name — renaming it requires a coordinated branch protection update. Any new CI job that should be a required check must go through a two-step process: merge to main (so the job name appears in GitHub's check history), then update the branch protection rule.

### Activation condition

Update the required checks list in GitHub Settings whenever a CI job is added, renamed, or removed. If `Docker Test Suite` is ever renamed, coordinate the branch protection update to happen immediately after — or in the same deployment window — to avoid creating a gap in merge protection.

### Related PRs / Docs

- PR #20 (`feature/scheduled-regression-api-ui-split`) — three-job CI split
- `.github/workflows/ci.yml` — job IDs and display names
- `security_and_branch_protection.md` — Required status checks section, post-merge update instructions

### Trade-offs and consulting value

Preserving the existing job name prevented any disruption to the branch protection configuration during the split. Trade-off: `Docker Test Suite` is a slightly misleading name — it is the quality gate suite, not the test execution suite — and the name is now load-bearing, which constrains future renaming. For a consulting client, this documents a GitHub architectural constraint that surprises most teams: job names in `ci.yml` are not merely display labels; they are the string identifiers that branch protection rules reference by exact match.

---

## ADR-011: Notification delivery defaults to dry-run when secrets are absent

**Status:** Accepted
**Date:** 2026-06-01

### Context

Release readiness gate results need outbound delivery to Slack and email after the nightly scheduled regression. Slack incoming webhook URLs and SMTP credentials are real secrets that cannot be committed to the repository. A notification script that fails CI when credentials are absent would break any unconfigured environment — any fork, any new team member, any client repo that has not yet provisioned secrets.

### Decision

`scripts/notify.py` attempts Slack and email delivery independently. Each channel checks its own required env vars (`SLACK_WEBHOOK_URL` for Slack; `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `NOTIFY_RECIPIENTS` for email). When a channel's required vars are absent, it logs a dry-run preview and exits 0. Setting `NOTIFY_DRY_RUN=true` (or `1`) forces dry-run for all channels regardless of whether secrets are present — this allows CI operators to validate the notification wiring without triggering live delivery.

The script always exits 0. Notification failure is logged as a warning but never fails CI. The CI notification step runs only on `schedule` and `workflow_dispatch` triggers to avoid noise on push and pull request runs.

SMTP is implemented with generic env vars (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`) rather than Gmail-specific vars. Port 465 uses `smtplib.SMTP_SSL`; all other ports (default 587) use `smtplib.SMTP` with `starttls()`. Gmail configuration is documented as an example. Zero new Python dependencies are required — `urllib.request`, `smtplib`, `ssl`, and `email.mime` are all stdlib.

### Alternatives considered

- **Require secrets to be set before the notification step runs** — rejected. CI would break for any fork, any unconfigured environment, and any repo copy that has not provisioned secrets. This inverts the correct delivery order: the infrastructure should be validated before credentials exist.
- **Use a third-party Slack GitHub Action** — rejected. Third-party actions require SHA-pinning for supply-chain hygiene (see ADR-005), introduce an external service dependency, and are GitHub-specific rather than CI-platform-portable. The stdlib `urllib.request` approach is portable to any CI system.
- **Gmail-specific SMTP env vars (`GMAIL_USER`, `GMAIL_APP_PASSWORD`)** — rejected. Locks the blueprint to Google Workspace. Generic SMTP vars support Gmail, Outlook, SendGrid, AWS SES, and any internal SMTP relay without code changes.
- **Separate `notify` CI job (needs: [api, ui])** — rejected for this slice. A separate job would require `actions/upload-artifact` and `actions/download-artifact` (third-party, SHA-pinning needed) to transfer `release-readiness.json` between jobs. The step-in-`API Tests` approach has access to the artifact natively. A separate job also adds a new required-check candidate, triggering the ADR-010 two-step branch protection update process unnecessarily. **Note (ADR-016, 2026-06-03):** This alternative was later adopted when aggregate notification became a requirement. See ADR-016.

### Consequences

Notification infrastructure is in CI before live credentials are provisioned. Adding live delivery is a GitHub Settings step (add secrets), not a code change. `NOTIFY_DRY_RUN=true` as a repository variable allows CI-level validation without secrets. SMTP exceptions log only the exception class name — not `str(exc)` — to prevent server response strings from echoing usernames or partial credentials.

No new CI job is added, so branch protection required checks are unchanged (see ADR-010).

### Activation condition

- Configure `SLACK_WEBHOOK_URL` in GitHub Settings → Secrets → Actions when ready for live Slack delivery.
- Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `NOTIFY_RECIPIENTS` (and optionally `EMAIL_FROM`) when ready for live email delivery.
- Expand the notification step's trigger condition from `schedule || workflow_dispatch` to additional triggers if broader notification coverage is needed.
- Migrate email from stdlib SMTP to a dedicated delivery API (SendGrid, AWS SES) if volume, deliverability tracking, template rendering, or bounce management requirements exceed stdlib SMTP capabilities.
- Add a separate `notify` CI job (needs: [api, ui]) when multi-source notification — covering both API and UI results in a single report — is required. This aligns with the ADR-009 activation condition for multi-source release gate consolidation.

### Related PRs / Docs

- `scripts/notify.py` — notification script implementation
- `.github/workflows/ci.yml` — API Tests job, Deliver release readiness notification step
- `agentic-qa-workflows/governance/quality_gates.md` — Notification Delivery section
- `agentic-qa-workflows/governance/security_and_branch_protection.md` — Notification secrets section and gate classification table
- ADR-009 (API-only release gate, multi-source deferred)
- ADR-010 (branch protection operates on job names)

### Trade-offs and consulting value

Dry-run default makes the feature safe to ship in any environment without pre-configured credentials. Trade-off: the feature appears fully wired in CI but sends nothing until secrets are provisioned. For a consulting client, this is the correct delivery order: the consulting team ships complete notification infrastructure; the client's security team provisions GitHub Secrets independently, on their schedule, without touching the codebase. The code never changes again for live delivery to begin.

stdlib-only implementation means zero dependency management burden. The Slack incoming webhook JSON format is stable across Slack plan tiers. The SMTP interface is RFC-standard. Neither will change unpredictably, and neither requires account registration or token management to use in dry-run mode.

---

## ADR-012: Pre-commit as advisory local guardrail; Docker CI as source of truth

**Status:** Accepted
**Date:** 2026-06-02

### Context

PR #22 (notification delivery dry-run) exposed a local-validation gap: Ruff format and lint checks ran against a stale Docker image (built before the code change), not the current working tree. An 89-character line in `scripts/notify.py` passed local validation and was caught by CI only after a fresh Docker build. A parallel stale-image gap exists for mypy. `quality_gates.md` now documents the fresh Docker rebuild rule, and `failure_evidence.md` documents the CI gate failure pattern.

Local guardrails that run before `git commit` — before any Docker build, before any push — catch this class of error in seconds rather than consuming a full CI run. Pre-commit is the standard mechanism for this in Python projects.

### Decision

Add `.pre-commit-config.yaml` with hooks for `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-json`, `check-toml`, `debug-statements`, Ruff format (auto-fix), Ruff lint (auto-fix where possible), and mypy (`utils/`, `pages/`, `scripts/`).

Pre-commit is **advisory**, not mandatory:

- Hooks can be bypassed with `git commit --no-verify`.
- `pre-commit` is not added to `requirements.txt` — it is a developer ergonomics tool, not a project test dependency.
- Installation is per developer machine. Contributors who do not install pre-commit are still validated by Docker CI.

Docker CI remains the authoritative source of truth. Pre-commit is the shift-left speed layer: seconds of local feedback before a multi-minute Docker build.

### Why `language: system` instead of remote `repo:` + `rev:` pins

The standard pre-commit pattern for third-party tools pins an explicit version:

```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.9.0
  hooks:
    - id: ruff
```

This creates a pre-commit-managed isolated environment with the pinned version. The problem: a `rev:` pin in `.pre-commit-config.yaml` is a second version surface for ruff and mypy, separate from `requirements.txt`. If the two diverge — ruff 0.8.x in `requirements.txt` but `rev: v0.9.0` in the pre-commit config — a passing pre-commit run no longer predicts a passing Docker CI run. This is the "works locally, fails in CI" failure mode that this slice was created to prevent.

Using `language: system` ties the hook to the developer's active Python environment. If the developer activates the local venv (installed from `requirements.txt`), the tool versions are identical to those installed inside Docker. No separate pin is required and no pin can drift.

The trade-off: if the developer runs `git commit` without a venv active and ruff/mypy are not in their global PATH, the hook fails with "command not found" (exit 127). This is a loud failure — the developer sees it immediately — not a silent pass. Docker CI still catches everything regardless.

### Why `pre-commit` is not in `requirements.txt`

`requirements.txt` defines the project's test execution dependencies — tools that are installed inside Docker and run during CI. `pre-commit` is a developer workflow tool that orchestrates git hooks on a local machine. It is not called during Docker builds, CI test runs, or any automated pipeline. Adding it to `requirements.txt` would install it inside the Docker image unnecessarily and conflate test infrastructure with developer ergonomics.

The correct installation path is `pip install pre-commit` (or `brew install pre-commit`) as a one-time developer setup step, documented in `README.md` and `quality_gates.md`.

### Why CodeQL, pip-audit, and Trivy remain CI-only

These tools cannot be run meaningfully as pre-commit hooks:

- **CodeQL** performs interprocedural taint analysis across the full codebase call graph. It cannot run on staged files without the full CodeQL engine, the GitHub Actions environment, and 1–3 minutes of analysis time. PR #22 CodeQL findings (secret-taint logging paths) required exactly this level of analysis.
- **pip-audit** scans `requirements.txt` dependencies against the OSV advisory database. Running it on every commit adds network I/O for zero benefit — `requirements.txt` does not change on every commit.
- **Trivy** scans the built Docker image. The image must be built first. Running `docker build` inside a pre-commit hook would take 2–5 minutes and eliminate the fast-feedback value of pre-commit entirely.

A clean pre-commit run does not imply CI will pass. Security analysis and supply-chain scanning remain CI-only gates.

### Why actionlint is deferred

actionlint validates GitHub Actions workflow YAML semantics — step names, expression syntax, secret references, conditional logic. It would add value for workflow files. The blocker: actionlint is a Go binary that requires `brew install actionlint` on macOS or a binary download/`go install` on Linux. It cannot be installed via pip or pre-commit's Python package management. Adding it to `.pre-commit-config.yaml` with `language: golang` requires all contributors to have Go tooling installed.

At the current repo scale (two workflow files, both stable and passing CI), the installation overhead does not justify the coverage gain. A commented-out block in `.pre-commit-config.yaml` documents the activation path without requiring installation now.

### Alternatives considered

- **Remote `repo:` + `rev:` pins for ruff and mypy** — rejected. Creates a second version surface that silently drifts from `requirements.txt`. See the `language: system` rationale above.
- **Dockerized pre-commit hooks (`entry: docker run ... ruff format`)** — rejected. Running `docker build && docker run` per commit takes 2–5 minutes and eliminates the fast-feedback value. Docker CI is already the Docker validation path.
- **Mandatory pre-commit (enforced via CI re-run)** — rejected. A CI step that re-runs pre-commit against the pushed commit adds CI time without adding coverage beyond the existing Ruff and mypy Docker steps. The correct enforcement point is the existing Docker CI gates.
- **Skipping pre-commit entirely** — rejected. The PR #22 stale-Docker gap demonstrated that fast local feedback prevents trivial formatting violations from consuming CI cycles.

### Consequences

A developer who installs pre-commit and activates their local venv catches Ruff formatting and lint violations, mypy type errors, trailing whitespace, malformed YAML/JSON/TOML, and debug statement leaks before pushing. The PR #22 class of error — an 89-char line caught by CI after a fresh Docker build — is caught in seconds before any Docker build begins.

Contributors who do not install pre-commit are unaffected. Docker CI continues to enforce all quality gates.

### Activation conditions

- **Make pre-commit mandatory:** Add a CI step that runs `pre-commit run --all-files` against the pushed commit. Activate when the team has standardized on a shared venv workflow, or when a client engagement requires mandatory local hook enforcement.
- **Switch to remote `repo:` + `rev:` pins:** Activate if `requirements.txt` is replaced by a pinned lockfile (e.g., `ruff==0.9.0`). With fully pinned versions, a matching `rev:` in `.pre-commit-config.yaml` can be kept in sync via `pre-commit autoupdate`.
- **Enable actionlint:** Activate when workflow count or complexity grows (more than five workflow files, custom action authoring, complex matrix strategies) and when the team can standardize on a Go binary installation method.
- **Expand hook set:** Add `bandit` (security linting) if CodeQL advisory posture is tightened to blocking. Add `pyupgrade` if the minimum Python version increases beyond 3.9.

### Related PRs / Docs

- `.pre-commit-config.yaml` — hook configuration
- `agentic-qa-workflows/governance/quality_gates.md` — Local Developer Guardrails section
- `agentic-qa-workflows/governance/failure_evidence.md` — CI Gate / Workflow Failures section; stale Docker rebuild rule (root cause that motivated this slice)
- ADR-001 (Docker-first execution as source of truth)
- ADR-002 (Ruff as single format+lint tool)
- ADR-003 (mypy with pragmatic initial strictness)

### Trade-offs and consulting value

The `language: system` decision is the most architecturally significant choice in this slice and the one most likely to require explanation to a client team. Most teams either (a) copy a pre-commit config with remote `repo:` + `rev:` entries and discover version drift months later when a tool upgrade in `requirements.txt` diverges from the pre-commit pin, or (b) skip pre-commit entirely and accept slow CI feedback loops. The `language: system` pattern — document the venv coupling, own version resolution through `requirements.txt`, avoid a second version surface — is the correct approach for a repo that already has a full Docker-first CI layer and `requirements.txt` as the version authority.

The advisory positioning is correct for a consulting blueprint repo. Mandatory pre-commit creates contributor friction that is difficult to enforce without a CI-level enforcement step. For a client engagement, the correct recommendation is: start with advisory pre-commit for immediate feedback value and elevate to mandatory only when the team has standardized the local venv workflow.

The explicit documentation of what pre-commit does **not** cover — CodeQL, pip-audit, Trivy — is a consulting best practice that most teams omit. A developer who sees all green in pre-commit and concludes security analysis is satisfied is a governance failure. Both the config file header and the `quality_gates.md` entry address this directly at the point where it matters.

---

## ADR-013: Bounded adjacent-risk scan in QA reviewer prompts

**Status:** Accepted
**Date:** 2026-06-02

### Context

Prior Mode A and Mode B reviews using `qa_architect_slice_review_prompt.md` had no structured checks for: validation freshness (stale Docker image), changed-files vs. validation-coverage gap, CodeQL-style secret-taint patterns, or CI-only check awareness. PR #22 (notification delivery dry-run) demonstrated that each of these gaps can produce a CI failure that a reviewer would not have caught under the prior prompt:

- Ruff format and lint checks ran against a stale Docker image, not the current working tree
- A CodeQL taint path through a helper function argument was not flagged during review — the taint follows the function argument, not the return value
- No reviewer check asked whether pre-commit passing constituted full CI validation

The risk of adding these checks without a scope cap is unbounded review scope expansion, where reviewers enumerate adjacent findings indefinitely, making reviews non-repeatable and prompts non-reusable across projects.

This ADR is a companion to ADR-012. ADR-012 governs pre-commit as a local execution tool — which hooks to include, `language: system` vs. remote pins, why CodeQL/pip-audit/Trivy are excluded. ADR-013 governs reviewer behavior in Mode A and Mode B — what reviewers must check and how adjacent findings are classified and capped.

### Decision

Add bounded adjacent-risk scan and four specific named checks to `qa_architect_slice_review_prompt.md`:

- **Mode A additions:** `Validation integrity and coverage`, `Security and secret handling`, `Bounded adjacent-risk scan` subsections inside the plan-review evaluation criteria; corresponding output format sections.
- **Mode B additions:** Expand Dimension 6 with Docker rebuild and volume-mount validation checks; add Dimension 10 (Security and secret hygiene) and Dimension 11 (Bounded adjacent-risk scan); add `Follow-up slice items` output section.

**Bounded adjacent-risk scan cap:** Maximum 3 findings per review pass. Each finding classified as:

- **Blocker** — must be resolved before implementation begins (Mode A) or before commit (Mode B); directly affects current slice correctness or safety
- **Recommended before commit** — reduces CI surprise risk; should be addressed but does not block
- **Follow-up slice** — real risk outside current slice scope; document and defer

Implementation scope must not expand unless the finding is a Blocker that directly affects current slice correctness.

**Dimension 10 (Security and secret hygiene)** covers the full set of CodeQL taint sinks: `print()`, `logging`, f-strings referencing secret variables, exception messages, CI step summaries, helper function arguments used near logging, CI artifact files, and tuples/lists/dictionaries that later feed any logging or print output. It applies when a slice touches env vars, credentials, GitHub Secrets, `os.environ` reads, `.env` files, or secret-handling code paths. Reviewers declare N/A when not applicable.

### Why the max-3 cap

Three findings is the standard consulting "top-N" triage framing. It forces reviewers to rank rather than enumerate. More than three adjacent findings creates a secondary review loop that defeats the purpose of a bounded scan — reviewers begin chasing adjacent risks to adjacent findings. The cap makes review behavior predictable and the prompt reusable across project engagements.

### Why secret-taint gets a dedicated Mode B dimension rather than being only an adjacent-risk finding

A secret-taint violation in changed code is a direct correctness and safety finding within the slice scope — not an adjacent risk. Placing it in the bounded adjacent-risk scan would allow it to be deprioritized if two other findings consumed the cap first. Dimension 10 ensures it is a first-class required check on every review where the slice touches secret-handling code.

### Why CodeQL, pip-audit, and Trivy remain CI-only from the reviewer perspective

A reviewer can recognize patterns that CodeQL would flag — using `failure_evidence.md` as a reference — but cannot substitute for the full CodeQL analysis:

- **CodeQL** performs interprocedural taint analysis across the full codebase call graph. Reviewer reasoning is intra-procedural; it cannot trace taint through multiple call boundaries the way CodeQL can. PR #22 CodeQL findings required exactly this level of analysis.
- **pip-audit** queries the OSV advisory database live. A reviewer cannot replicate a CVE check without running the tool against a current `requirements.txt`.
- **Trivy** scans built Docker image layers. The image must exist; there is no static equivalent.

The reviewer's role for CI-only checks is to acknowledge that they will run in CI and to confirm the plan does not assume local validation is sufficient.

### Why Mode C (security-focused review) is deferred

A third review mode would change the four-step slice workflow and add coordination overhead for every slice that touches security-relevant code. The bounded Dimension 10 check achieves equivalent coverage for the currently known CodeQL taint patterns at zero workflow overhead. Activate Mode C if secret/credential handling becomes a recurring major slice category requiring a full security review pass separate from functional review.

### Alternatives considered

- **No adjacent-risk scan** — rejected. PR #22 demonstrated three concrete review gaps that would recur in any similar slice without a structured check.
- **Unlimited adjacent-risk findings** — rejected. Unbounded enumeration makes review duration unpredictable and encourages scope expansion that the four-step slice workflow is designed to prevent.
- **Fold secret-taint into the adjacent-risk scan** — rejected. A Blocker-class security finding in changed code must not be deprioritized by the 3-finding cap. Dedicated dimension prevents this.
- **Mode C (security-only review)** — rejected at this stage. See rationale above.

### Consequences

Mode A reviewers now check: whether validation commands cover all changed files, whether a fresh Docker build is specified when image contents change, whether volume-mounted validation is distinguished from full image validation, whether CI-only checks are acknowledged, whether secret-taint patterns in planned code are flagged, and whether adjacent risks are surfaced with a cap and classification.

Mode B reviewers now check all of the above against the actual implementation, plus 11 named dimensions with Pass/Fail/N/A verdicts.

`qa_architect_slice_review_prompt.md` v2 — revision noted in `prompts/README.md`.

### Activation conditions

- **Increase the cap** if 3 findings consistently proves too restrictive and important findings are being deferred unnecessarily. This is a judgment call — increase only if there is a documented pattern of cap-limited reviews missing critical findings.
- **Add Mode C** if secret/credential handling becomes a recurring major slice category requiring a dedicated security review pass.
- **Extend Dimension 10 patterns** as new CodeQL findings are documented in `failure_evidence.md` — the cross-reference in the prompt ensures the extension path is clear.

### Related PRs / Docs

- PR #23 (`feature/pre-commit-developer-guardrails`) — pre-commit advisory guardrail (ADR-012); stale Docker image root cause (PR #22)
- `agentic-qa-workflows/prompts/qa_architect_slice_review_prompt.md` — v2; the primary artifact of this ADR
- `agentic-qa-workflows/governance/failure_evidence.md` — CodeQL: secret-taint in logging section; cross-referenced by Dimension 10
- `agentic-qa-workflows/governance/quality_gates.md` — Local Developer Guardrails section; pre-commit CI-only check exclusions
- `agentic-qa-workflows/governance/agentic_workflow_rules.md` — Before Submitting a PR section; secret-taint trigger and pre-commit non-substitution rule
- ADR-012 (pre-commit as advisory local guardrail; Docker CI as source of truth)

### Trade-offs and consulting value

The bounded adjacent-risk scan with a max-3 cap and three-class classification is the established consulting code review triage pattern. It forces reviewers to rank rather than enumerate, keeps reviews repeatable, and makes the prompt reusable across client engagements.

Adding specific named dimensions (Dimension 10: security and secret hygiene; Dimension 11: adjacent-risk scan) rather than folding them into the general "Risks" dimension makes them first-class review criteria. The existing Dimension 8 "Risks and recommended fixes" is too broad to reliably prompt a reviewer to check CodeQL-style taint patterns for a specific list of sinks.

For a consulting client, the updated prompt is a tangible differentiator: most client review checklists do not distinguish volume-mounted single-file testing from full image validation, do not have a structured CodeQL-style taint check, and have no bounded mechanism for surfacing adjacent risks without opening unlimited scope. A reviewer following this prompt would have flagged both the stale Docker image scenario and the helper-function taint chain from PR #22 before CI ran.

---

## ADR-014: Smoke-only CI on PR and feature branch push; full suite on main, nightly, and workflow_dispatch

**Status:** Accepted
**Date:** 2026-06-02

### Context

The `smoke` marker has been declared in `pytest.ini` and documented in `suite_taxonomy.md` since Phase 3. `suite_taxonomy.md` states its run trigger as "every commit, every PR open, before any other suite." `quality_gates.md` documents the PR Gate as `pytest -m smoke` and the Merge Gate as the full suite. Despite this stated intent, CI has run the full API and UI test suites on every trigger — push to feature branches, pull requests, push to main, nightly schedule, and `workflow_dispatch` — since the API/UI job split in ADR-008.

As test count grows, running a full regression on every feature branch commit adds latency to PR feedback with no additional merge protection benefit. The required status checks (`API Tests`, `UI Tests`) block merge regardless of whether one test or five ran; the smoke subset provides the fast-feedback signal intended for that checkpoint.

### Decision

Add a `Determine test scope` step to both `API Tests` and `UI Tests` jobs that writes `TEST_SCOPE` and `MARKER_ARGS` to `$GITHUB_ENV`:

- `TEST_SCOPE=full`, `MARKER_ARGS=` (empty) when:
  - `github.ref == refs/heads/main` (push to main)
  - OR `github.event_name == schedule` (nightly)
  - OR `github.event_name == workflow_dispatch` (manual)
- `TEST_SCOPE=smoke`, `MARKER_ARGS=-m smoke` otherwise (PR and feature branch push)

Test execution commands use `$MARKER_ARGS` (unquoted) so that the empty full-suite case passes no extra argument and the smoke case passes `-m smoke`.

The release readiness gate (`scripts/release_gate.py`) runs only when `TEST_SCOPE=full`. On smoke runs, the step logs "Smoke-only run — release gate skipped." and exits 0. The job summary shows a "Release gate skipped" notice instead of a GO/NO_GO decision. `release-readiness.json` is not produced on smoke PR runs.

The notification step condition remains `github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'`. Both of those events are `TEST_SCOPE=full` by this logic, so the notification step always reads a full-suite gate result. No notification changes are required.

### Alternatives considered

- **Separate `API Smoke` and `UI Smoke` CI jobs** — rejected. New job names would trigger the ADR-010 two-step branch protection update process: jobs must run on `main` before they appear in the required-check autocomplete, creating a window of unprotected merges. This slice's constraint is zero branch protection disruption.
- **Full suite on all triggers forever** — rejected. The `smoke` marker and `suite_taxonomy.md` have always stated the smoke-first intent. Running full suite on every PR is an inconsistency between stated governance and actual CI behavior, not a safe status quo.
- **`strategy.matrix: [smoke, full]`** — rejected for the same reasons as ADR-008. The `API Tests` and `UI Tests` jobs have heterogeneous post-processing chains (release gate in API only, failure artifact upload in UI only). A matrix requires `if: matrix.scope == 'full'`-style conditionals on multiple steps, which is harder to read and more error-prone than the current two-job structure.
- **`if: env.TEST_SCOPE == 'full'` step condition for the release gate** — viable, but replaced with shell `if/exit 0` inside the `run:` block for explicitness: the skip reason appears in the step log, and the approach does not rely on understanding exactly when `$GITHUB_ENV`-set variables are available in GitHub Actions expression evaluation.

### Consequences

- Required status check names (`Docker Test Suite`, `API Tests`, `UI Tests`, `Analyze Python`) are unchanged. No branch protection update required.
- `release-readiness.json` is not produced on PR runs. The notification step (schedule/workflow\_dispatch only) always has full-suite gate evidence when it reads the file.
- PR smoke pass is fast feedback confirming the critical happy paths work — it is not full release readiness evidence. Regression-only and negative tests are caught on the main push, nightly schedule, or manual `workflow_dispatch` full run.
- The UI smoke subset is currently one test (TC-UI-001 `test_user_can_login`). A PR that breaks the add-to-cart flow (TC-UI-002, `regression`-only) will pass the `UI Tests` required check and be caught on the next full run. This is the accepted trade-off of the smoke-first pattern and is consistent with the marker assignments in `suite_taxonomy.md`. Marker reassignment is a separate taxonomy decision, not in scope for this slice.
- JUnit XML paths (`artifacts/api-report.xml`, `artifacts/ui-report.xml`) are unchanged. dorny/test-reporter reads the same paths in both smoke and full modes; on smoke runs the files contain the smoke subset and the reporter reflects accurate counts.

### Activation condition

- Revisit scope boundaries if the UI smoke subset (currently one test) becomes too thin to provide meaningful PR confidence — promote additional tests to `smoke` in a dedicated taxonomy slice.
- Revisit if branch protection strategy changes and new job names become feasible without a merge-protection gap.
- Revisit if full suite runtime grows large enough to require parallelization beyond the current smoke/full split (pytest-xdist decision gate per Phase 7 roadmap).

### Related PRs / Docs

- `.github/workflows/ci.yml` — `Determine test scope` step in `api` and `ui` jobs
- `agentic-qa-workflows/governance/quality_gates.md` — CI job structure table; smoke vs. full trigger documentation
- `agentic-qa-workflows/governance/suite_taxonomy.md` — `smoke` marker run trigger updated to reflect enforced CI behavior
- ADR-008 (three named CI jobs instead of matrix)
- ADR-009 (API-only release gate, multi-source deferred)
- ADR-010 (branch protection operates on job names, not step names)
- ADR-011 (notification delivery defaults to dry-run when secrets are absent)

### Trade-offs and consulting value

The smoke-first PR pattern is the answer to the most common CI question in consulting engagements: "how do we make PRs faster without losing regression coverage?" The implementation is approximately 25 lines of YAML shell logic with no new jobs, no new dependencies, and no branch protection changes. That ratio — meaningful behavioral change from minimal structural disruption — is the correct pattern for CI evolution at any scale.

The key consulting-facing decisions documented here are: (1) why the release gate is restricted to full-suite contexts only — partial-suite GO/NO_GO is misleading, not conservative; (2) why job names are preserved despite the behavioral change — the ADR-010 constraint on load-bearing job names applies equally to scope changes and structural changes; (3) why the UI smoke subset gap is accepted — the taxonomy defines smoke and regression as deliberate separate scopes, and the gap is documented rather than papered over by marker promotion.

For a client team adopting this pattern, the activation conditions define a clear growth path: add tests to `smoke` as coverage needs grow, add parallelization when runtime warrants it, revisit scope boundaries when the smoke subset no longer reflects the critical happy paths. None of these require changing the CI scope mechanism introduced here.

---

## ADR-015: Cross-environment selection with staging default and prod-read-only activation gate

**Status:** Accepted
**Date:** 2026-06-03

### Context

The repo targeted a single environment (SauceDemo UI + Restful Booker API) from inception. `test_data_env_rules.md` has always stated the intent to support multiple environments via an `ENV` var and `test_users.json` URL blocks, but the mechanism was not implemented. All CI runs used the same URL regardless of trigger or context.

Phase 7 adds prod-read-only validation as a named capability: the ability to run a safe, non-destructive subset of tests against a separate environment. The constraint is that no write, create, update, or delete operation may target a production-class environment under any CI trigger. A prod-read-only run that accidentally POSTs or DELETEs data is worse than no prod run at all.

The additional constraint is cost and speed: prod-read-only runs must not add CI overhead to PRs or feature branch pushes, which already run only the smoke subset for fast feedback (ADR-014).

### Decision

Introduce `ENV`-based environment selection throughout the test layer:

- `data/test_data/test_users.json` gains an `environments` key with `staging` and `prod_read_only` sub-blocks, each containing `base_url` and `api_base_url`. Credentials (`valid_user`, `locked_out_user`, `api_admin`, `checkout_user`) remain at the top level — they are environment-independent for this repo's demo services.
- `conftest.py` reads `ENV` from `os.environ` (default: `staging`) via a new `env_name` session fixture. A module-level `_KNOWN_ENVIRONMENTS` frozenset validates the value at collection time; unknown values fail fast with a clear error listing valid environments.
- `base_url` and `api_base_url` fixtures are updated to resolve URLs from `test_data["environments"][env_name]`.
- A new `read_only` marker is added to `pytest.ini`. It is applied only to tests with zero write or delete operations and no synthetic setup fixtures: TC-API-001 (`test_get_all_bookings`) and TC-UI-001 (`test_user_can_login`).
- Two prod-read-only steps are added inside the existing `API Tests` and `UI Tests` jobs. Each step is guarded by two conditions: `TEST_SCOPE=full` (only on main/schedule/workflow_dispatch) AND `PROD_ENV_ACTIVE=true` (a GitHub repository variable, not a secret). When either condition is not met, the step logs a skip notice and exits 0.
- The `prod_read_only` URL block uses a placeholder API URL. No real production URL is committed.
- The release gate remains staging-only. A one-test prod-read-only result is not a meaningful GO/NO_GO decision.
- The notification step is unchanged. It reads `release-readiness.json` (staging) on schedule/workflow\_dispatch — both of which are always `TEST_SCOPE=full` and always produce a staging gate result.

### Alternatives considered

- **`strategy.matrix: [staging, prod_read_only]` on the `api` and `ui` jobs** — rejected. Matrix entries change the GitHub Actions job display name from `API Tests` to `API Tests (staging)` and `API Tests (prod_read_only)`. This breaks the four required status checks documented in ADR-010. A branch protection update would be required with the ADR-010 two-step coordination process. This slice's constraint is zero branch protection disruption.
- **Separate `API Tests (prod-read-only)` and `UI Tests (prod-read-only)` jobs** — viable but adds new job names that are not required checks. These jobs would be non-blocking advisory runs, which is correct — but they require a separate branch protection promotion slice when live prod is wired. Steps inside existing jobs achieve the same advisory behavior today and promote to hard gates naturally (a step failure fails the parent job, which fails the required check) without an additional ADR-010 coordination step.
- **Per-environment config files** — rejected. A single environment-aware `test_users.json` is simpler and already described in `test_data_env_rules.md` as the preferred pattern for this repo.
- **Skip write tests at runtime via `ENV` check in test logic** — rejected. Embedding environment-awareness in test code mixes environment policy with test logic. The marker approach is cleaner: marker assignment is a deliberate, reviewable, one-time decision. A test either is or is not `read_only` — the environment at runtime does not change that classification.

### Consequences

- `ENV=staging` is the safe default. No existing test, CI run, or local command changes behavior unless `ENV` is explicitly set.
- `_KNOWN_ENVIRONMENTS` validation provides a clear error message when an unknown environment is passed — prevents silent misconfiguration.
- The `read_only` subset starts at two tests. This is intentionally thin — marking TC-API-003 or TC-UI-002 as `read_only` to look more comprehensive would misrepresent production safety.
- Prod-read-only JUnit XML (`artifacts/api-prod-report.xml`, `artifacts/ui-prod-report.xml`) is not currently consumed by `dorny/test-reporter`. Results are visible only in the step log. This is acceptable for a stub. The prod activation slice must add test-reporter publication if prod results need to appear in the CI test panel.
- Branch protection required checks (`Docker Test Suite`, `API Tests`, `UI Tests`, `Analyze Python`) are unchanged.

### Activation conditions

Before setting `PROD_ENV_ACTIVE=true` in GitHub Settings → Variables → Actions:

1. A real prod URL must be known and accessible from GitHub Actions runners.
2. Per-environment prod credentials must be stored as GitHub Secrets — for example `PROD_API_USERNAME` / `PROD_API_PASSWORD` — and injected via Docker `-e` flags in the prod-read-only step. They must never be added to `test_users.json`.
3. The `read_only` suite must be reviewed for production safety against the actual prod environment (auth requirements, rate limits, data visibility).
4. A dedicated activation slice must document the credential wiring and add `dorny/test-reporter` publication for `artifacts/api-prod-report.xml` and `artifacts/ui-prod-report.xml` if prod results need to appear in the CI test panel.
5. If the prod URL must also be kept secret (i.e., not committed to `test_users.json`), inject it via a GitHub Secret and override the `prod_read_only.api_base_url` value using a Docker `-e API_BASE_URL=...` flag with a corresponding `conftest.py` env var check.

### Related PRs / Docs

- `data/test_data/test_users.json` — `environments` block
- `conftest.py` — `env_name` fixture, `_KNOWN_ENVIRONMENTS`, updated `base_url` and `api_base_url` fixtures
- `pytest.ini` — `read_only` marker declaration
- `agentic-qa-workflows/governance/suite_taxonomy.md` — `read_only` marker section
- `agentic-qa-workflows/governance/test_data_env_rules.md` — Multiple Environments section updated from intent to active behavior
- `agentic-qa-workflows/governance/quality_gates.md` — CI scope table updated with environment column and prod-read-only row
- ADR-008 (three named CI jobs instead of matrix for API/UI split)
- ADR-010 (branch protection operates on job names, not step names)
- ADR-011 (notification delivery defaults to dry-run when secrets are absent — same activation variable pattern)
- ADR-014 (smoke/full trigger scope — prod-read-only steps only run when `TEST_SCOPE=full`)

### Trade-offs and consulting value

The `ENV` var + JSON URL block pattern is the correct lightweight answer to "how do we parameterize environments without per-environment config files or secrets in code?" It keeps the test layer environment-agnostic (fixtures resolve URLs from a named block; tests never reference URLs directly) while keeping the environment topology visible and reviewable in a single committed file.

The `PROD_ENV_ACTIVE` guard is the key insight for any client engagement delivering this pattern. It means the mechanism can be merged into the main branch on day one without risk of live prod traffic — the first prod run only happens after explicit opt-in with a documented activation checklist. The same pattern is already established in this repo for notification delivery (`NOTIFY_DRY_RUN`), making `PROD_ENV_ACTIVE` consistent with existing idioms rather than a one-off.

The `read_only` marker strategy resolves the hardest problem in multi-environment testing: how to prevent write tests from running in prod without embedding environment checks in test code. The answer is that prod safety is a property of the test, not of the runtime environment — a test either writes or it does not, and that property is captured at authoring time with a marker. When prod coverage grows, the review process for adding `read_only` to a new test is the same as any marker assignment: explicit, documented, and separately reviewable from the test logic itself.

---

## ADR-016: Aggregate CI notification job after all required jobs complete

**Status:** Accepted
**Date:** 2026-06-03

### Context

The release readiness notification ran inside the `API Tests` job, which runs in parallel with `UI Tests`. The release gate could produce a GO decision, Slack would fire immediately with `Release Readiness: ✅ GO`, and the `UI Tests` job could then fail — leaving a delivered GO notification against a workflow that ended in failure. This is incorrect release-readiness semantics.

The root cause is timing: notification was placed in the first job that generated gate data, not in a job that could observe all required job outcomes.

This ADR fulfills the activation condition stated in ADR-011: "Add a separate notify CI job when multi-source notification is required."

### Decision

Add a new `notify` job with `needs: [test, api, ui]` and `if: always() && (schedule || workflow_dispatch)`. The job runs after all three required jobs complete, regardless of their outcomes. It:

- Receives `needs.test.result`, `needs.api.result`, and `needs.ui.result` as env vars (`DOCKER_TEST_SUITE_RESULT`, `API_TESTS_RESULT`, `UI_TESTS_RESULT`).
- Downloads `release-readiness.json` from the `api` job via `actions/upload-artifact@v4` / `actions/download-artifact@v4`. The download step uses `continue-on-error: true` so the notify job proceeds even when the artifact was not produced.
- Computes **Overall Release Readiness** as BLOCKED if any required job result is not exactly `success` (failure, cancelled, skipped, and unknown are all BLOCKED), GO if all jobs succeeded and the gate decision is GO, NO_GO if all jobs succeeded and the gate decision is NO_GO, and UNKNOWN if all jobs succeeded but gate data is missing.
- Delivers the aggregate message to Slack and email via `scripts/notify.py` (stdlib-only, runs directly on the runner without Docker or pip install).

The `notify` job is not a required branch protection check. It is advisory notification delivery. `scripts/notify.py` always exits 0 — notification failure never blocks CI.

### Alternatives rejected

- **Keep notification inside `API Tests`** — rejected. `API Tests` and `UI Tests` run in parallel. Notification from `API Tests` fires before `UI Tests` completes. A UI failure after notification produces a false GO.
- **Separate webhook call from each job** — rejected. Multiple partial notifications per run produce redundant, inconsistent delivery with no aggregate view. Recipients would need to reconcile three separate messages to determine overall CI state.
- **Mark `notify` as a required branch protection check** — rejected. Notification is advisory delivery, not a release gate. Making it a required check would add branch protection churn per ADR-010 with no correctness benefit. Notification failures are expected under unconfigured secret conditions and must not block merges.

### Consequences

- The notification message now includes an **Overall Release Readiness** line, a **CI Status** section with per-job result rows, and a **Release Gate** line that shows the component gate result. When Overall Release Readiness is BLOCKED and the Release Gate shows GO, the message annotates the gate line: `(component signal only — overall readiness is BLOCKED)`.
- `release-readiness.json` is now transferred via artifact upload in `api` job / artifact download in `notify` job. `overwrite: true` on the upload step makes CI re-runs safe (avoids duplicate artifact name failure).
- The `notify` job is the only CI job that receives the three `needs.*.result` values. Running locally without CI context, all three env vars are empty strings — `compute_overall_readiness` skips empty values, preserving backward-compatible behavior.
- Existing required job names (`Docker Test Suite`, `API Tests`, `UI Tests`) are unchanged. No branch protection update required.

### Activation condition

No further activation required — the `notify` job is live on every `schedule` and `workflow_dispatch` run. To enable live delivery: configure `SLACK_WEBHOOK_URL` and SMTP secrets in GitHub Settings → Secrets → Actions. `NOTIFY_DRY_RUN=true` (repository variable) forces dry-run while secrets are being validated.

### Related PRs / Docs

- `.github/workflows/ci.yml` — `notify` job; artifact upload step in `api` job
- `scripts/notify.py` — `get_ci_status()`, `compute_overall_readiness()`, updated `build_message_lines()`
- `agentic-qa-workflows/governance/quality_gates.md` — CI job structure table; Notification Delivery section
- `agentic-qa-workflows/governance/notification_wiring.md` — overview and validation sections
- ADR-009 (API-only release gate, multi-source deferred)
- ADR-010 (branch protection operates on job names — `notify` is not a required check)
- ADR-011 (notification delivery defaults to dry-run — activation condition fulfilled)
- ADR-014 (smoke/full trigger scope — `notify` job only fires on full-suite triggers)

### Trade-offs and consulting value

**Accepted trade-off:** Notification arrives after all three jobs complete rather than after the first job that generates gate data. This is unconditionally better — a notification that arrives with the complete picture is worth more than one that arrives one minute earlier with potentially incorrect content.

**Accepted trade-off:** Cross-job artifact upload/download adds two steps and one inter-job artifact. This is the canonical GitHub Actions pattern for cross-job data sharing and is well understood by any team familiar with the platform.

**Consulting value:** The `needs.*.result` aggregation pattern for downstream notification is the most commonly misimplemented part of multi-job CI pipelines. Most teams place notification inside the first job that generates useful data — exactly what this repo was doing before this slice. ADR-016 makes the failure mode explicit (parallel job, early notification, false GO) and documents the correct aggregate pattern. The distinction between "component gate passed" and "overall release readiness" is a concept that recurs in every client engagement that has both API and UI test jobs in the same pipeline.

---

## ADR-017: Observability snapshot populated via stub pending live stack connection

**Status:** Accepted
**Date:** 2026-06-03

### Context

`scripts/release_gate.py` reads `data/release/observability_snapshot.json` to include observability metrics in the GO/NO_GO decision. That file currently contains static sample values with `"source": "manual_sample"`. A comment inside the file states: *"In production this file is generated by `scripts/pull_observability.py`."*

A live implementation would pull real error rate, latency, and incident data from Datadog, Grafana, or PagerDuty before each release gate run. No live observability stack is available at this time, and provisioning real credentials for a blueprint repo is not warranted. The pull interface and credential conventions need to be documented before the live stack is connected, so any future implementer — or consulting client team — can complete the integration without reverse-engineering the expected output schema.

### Decision

Implement `scripts/pull_observability.py` as a documentation stub. Each provider's fetch function prints the API call it would make (using literal placeholder strings — not real URLs or credential values) and returns static representative values. The static `data/release/observability_snapshot.json` remains unchanged as the release gate's consumed input. The real implementation replaces the stub bodies when a live observability stack is available and credentials are provisioned.

The script is stdlib-only, always exits 0, defaults to dry-run (preview only), and requires `OBSERVABILITY_WRITE=true` as an explicit write guard. Credentials alone do not trigger writes. Unknown providers print a warning listing valid providers and produce no snapshot.

### Activation conditions

All five conditions must be met before wiring `pull_observability.py` to CI:

1. Replace the stub body of the target provider's fetch function with real API calls using the documented endpoint patterns.
2. Provision all required credentials as GitHub Secrets (`DATADOG_API_KEY`, `DATADOG_APP_KEY`, `GRAFANA_URL`, `GRAFANA_API_KEY`, `GRAFANA_DASHBOARD_UID`, `PAGERDUTY_API_KEY`, `PAGERDUTY_SERVICE_ID` — only the secrets for the chosen provider are required). Never commit credential values.
3. Decide whether the script writes to the tracked static file (`data/release/observability_snapshot.json`) or to an artifact-only path. If using a custom path, set `OBSERVABILITY_SNAPSHOT_PATH` and update `scripts/release_gate.py` to read the same path — they must match or the gate will evaluate against stale sample data.
4. Add a `snapshot_timestamp` freshness check in `scripts/release_gate.py` so a stale snapshot from a prior CI run cannot silently pass the gate. A run that fails to pull live data should warn (or NO_GO) rather than evaluate against hours-old values.
5. Add the `pull_observability.py` step before the release gate step in `.github/workflows/ci.yml` only after all the above are in place.

### Alternatives rejected

- **Skip the stub entirely** — rejected. A blank space in the scripts directory with no interface documentation makes future integration harder. Any team member or consulting client who wasn't part of the original design would need to reverse-engineer the expected output schema from `release_gate.py` before writing a single line of integration code.
- **Implement live integration now** — rejected. No live stack available. Would require real credentials and real endpoints that cannot be committed. A fictional live integration adds complexity with no functional benefit.
- **Use `jsonschema` for snapshot validation** — rejected. Violates the stdlib-only constraint that applies to all scripts that may run directly on the GitHub Actions runner. `release_gate.py` already handles malformed data gracefully (missing keys produce `None` warnings, not errors).

### Consequences

- `data/release/observability_snapshot.json` remains static until the stub is replaced with a real provider implementation. The release gate continues to evaluate against sample values.
- `scripts/release_gate.py` is unchanged. CI is unchanged.
- Credentials are documented as future GitHub Secrets only; none are committed.
- The stub is activation-ready: provisioning secrets and setting `OBSERVABILITY_WRITE=true` is the only change needed to begin testing the write path before wiring CI.

### Related PRs / Docs

- `scripts/pull_observability.py` — stub implementation; per-provider API interface documentation
- `data/release/observability_snapshot.json` — static sample file consumed by `scripts/release_gate.py`
- `agentic-qa-workflows/governance/quality_gates.md` — Release Gate section; one-sentence activation pointer
- `.private/agentic-qa-roadmap.md` — Phase 7 observability integration item
- ADR-009 (API-only release gate, multi-source deferred — original deferral of live observability)
- ADR-011 (dry-run default pattern — same `OBSERVABILITY_WRITE` explicit write guard convention)

### Trade-offs and consulting value

**Accepted trade-off:** The static sample file is unchanged. The release gate continues to run on representative values that are not live production data. This is the correct decision — a fictional live integration with no real stack would be worse than clearly labeled sample data.

**Consulting value:** The stub-first interface pattern addresses one of the most common hand-off failures in QA platform projects. Teams build the test and gate infrastructure first, then stall when the observability stack is ready because no interface was documented. A well-commented stub with per-provider endpoint patterns, credential naming conventions, and an ADR with an ordered activation checklist gives any future implementer everything needed to complete the integration in a single session without reading a design document or asking the original architect. The five-item activation checklist — replace stub body, provision secrets, align paths, add freshness check, wire CI — is the consulting deliverable: it converts "we deferred this" into "here is exactly how to activate it."

---

## ADR-018: Failure-only aggregate notification on push to main

**Status:** Accepted
**Date:** 2026-06-06

### Context

The `notify` job (ADR-016) runs after all three required CI jobs complete and delivers an aggregate Slack/email notification. Since its introduction, the job has fired only on `schedule` and `workflow_dispatch` triggers. Push to main runs the full suite and the release gate but sends no outbound notification on any outcome — a push-to-main failure is visible only in CI logs and GitHub branch status, with no active alert to the team.

ADR-011 explicitly deferred this as an activation condition (line 475): "Expand the notification step's trigger condition from `schedule || workflow_dispatch` to additional triggers if broader notification coverage is needed."

Notifying on every push to main would produce noise on clean merges. The correct policy is "opinionated silence" on clean pushes — teams receive a notification only when the main branch is unhealthy.

### Decision

Expand the `notify` job-level `if:` condition in `.github/workflows/ci.yml` to include push-to-main runs where any required job result is not exactly `success`:

```yaml
if: >-
  always() && (
  github.event_name == 'schedule' ||
  github.event_name == 'workflow_dispatch' ||
  (github.event_name == 'push' && github.ref == 'refs/heads/main' &&
  (needs.test.result != 'success' || needs.api.result != 'success' || needs.ui.result != 'success')))
```

**Trigger policy:**

| Trigger | Outcome | Notify? |
|---|---|---|
| `schedule` | any | Always — unchanged |
| `workflow_dispatch` | any | Always — unchanged |
| `push` to `main` | any required job not `success` | Yes — BLOCKED notification |
| `push` to `main` | all required jobs `success` | No — silent clean merge |
| `pull_request` | any | No — unchanged |
| feature branch push | any | No — unchanged |

No changes to `scripts/notify.py`, `scripts/release_gate.py`, job structure, job names, env vars, secrets, or branch protection.

### Why `always()` is required

`always()` is not optional. Without it, GitHub Actions automatically skips a job whose `needs:` list includes any job that failed, was cancelled, or was skipped — this is the platform default. Removing `always()` would silently prevent the `notify` job from ever starting on push-to-main failure, because the upstream job failure would trigger the default skip behavior before the `if:` expression is evaluated.

`always()` causes the platform to evaluate the job's `if:` condition regardless of upstream outcomes. The expanded condition then determines whether to start the job based on event, ref, and upstream results. Both are required together.

### Semantic rules

**Skipped required jobs are BLOCKED.** There is no skip-by-design mechanism for required jobs on push to main. Push to main always runs `TEST_SCOPE=full` (ADR-014). A skipped required job on main means the workflow was interrupted before that job started — this is a pipeline failure, not an intentional opt-out.

**Cancelled required jobs are BLOCKED.** A cancelled job on main means the workflow was aborted before delivery was complete. Deliberate.

**Release gate NO_GO is captured by `needs.api.result != 'success'`.** `scripts/release_gate.py` exits 1 on any non-GO decision (line 316: `return 0 if decision == "GO" else 1`). A non-GO exit code fails the `Run release readiness gate` step, which fails the `API Tests` job, which makes `needs.api.result = 'failure'`. No separate gate-decision check is needed in the trigger condition.

**`NOTIFY_DRY_RUN` applies to all trigger types.** When `NOTIFY_DRY_RUN=true` (GitHub repository variable), push-to-main failure notifications also dry-run — the `notify` job starts and logs a preview but sends no live Slack or email. Operators relying on push-to-main failure alerts must confirm `NOTIFY_DRY_RUN` is unset or `false`.

### Alternatives considered

- **Step-level shell guard in the `Deliver aggregate CI notification` step** — rejected. Requires the Notify job to start on every push-to-main (clean or not), consuming a runner for a few seconds with no delivery. Also produces ambiguous CI logs: `Notify: success` for both "delivery succeeded" and "delivery silently skipped." The job-level `if:` is the correct mechanism for trigger eligibility.
- **Logic in `scripts/notify.py` to read `GITHUB_EVENT_NAME` and `GITHUB_REF`** — rejected. Violates separation of concerns. Trigger eligibility is a CI orchestration decision, not a script responsibility. The script should know how to deliver, not whether the job should run. Would also make it harder to validate the policy by reading the workflow YAML.
- **Helper eligibility script** — rejected. No codebase precedent. Adds a file for a function expressible as one condition in YAML. No benefit over the job-level approach.

### Consequences

- Push-to-main failures produce an active Slack/email notification. Clean merges are silent.
- Existing schedule/workflow_dispatch behavior is unchanged.
- `compute_overall_readiness()` in `notify.py` already handles BLOCKED/GO/NO_GO/UNKNOWN correctly for all job result combinations — no script changes required.
- Job names (`Docker Test Suite`, `API Tests`, `UI Tests`) and required branch protection checks are unchanged. No post-merge branch protection update required.
- Gmail/SMTP live delivery debugging remains deferred. The push-to-main notification fires but dry-runs until live credentials are provisioned.

### Activation condition

No further activation required. The condition is live on push to main immediately after this PR merges.

- **Live delivery:** configure `SLACK_WEBHOOK_URL` and/or SMTP secrets in GitHub Settings → Secrets → Actions. Confirm `NOTIFY_DRY_RUN` is unset or `false`.
- **Expand further:** if notification is needed on additional triggers (e.g., tag push, release), extend the `if:` condition in a new slice.

### Related PRs / Docs

- `.github/workflows/ci.yml` — `notify` job, `if:` condition
- `agentic-qa-workflows/governance/notification_wiring.md` — "When it runs" and NOTIFY_DRY_RUN sections
- `agentic-qa-workflows/governance/quality_gates.md` — CI job structure table; Notification Delivery section
- `agentic-qa-workflows/governance/security_and_branch_protection.md` — gate classification table, Notification delivery row
- ADR-011 — activation condition fulfilled (trigger expansion); notification delivery defaults
- ADR-016 — aggregate Notify job structure being extended

### Trade-offs and consulting value

**Accepted trade-off:** clean push-to-main merges are silent — no outbound confirmation. Teams that want explicit delivery confirmation can use `workflow_dispatch`. This is the correct default: notification frequency should be bounded by failure frequency, not push frequency.

**Consulting value:** The "opinionated silence on clean merges" pattern is the answer to the most common notification design question in CI consulting: "how do we get alerted when something breaks on main without getting spammed on every commit?" The implementation is a single `if:` condition change with no new jobs, no new scripts, no new dependencies, and no branch protection changes. The ratio of behavioral capability to structural change is the correct pattern for incremental CI evolution.

The `skipped = BLOCKED` and `cancelled = BLOCKED` semantics are worth documenting explicitly because most teams treat skipped as "not applicable" rather than "interrupted." Making this intent explicit — and encoding it as `!= 'success'` rather than `== 'failure'` — is a reusable architectural teaching point for any client engagement that has multi-job pipelines with downstream notification.

---

## ADR-019: Independent judgment preface in QA reviewer and planning prompts

**Status:** Accepted
**Date:** 2026-06-06

### Context

ADR-013 (2026-06-02) hardened the QA reviewer prompt framework with technical checks: validation integrity and coverage, security and secret hygiene (Dimension 10), and bounded adjacent-risk scan (Dimension 11). ADR-013 expanded *what* reviewers check — technical dimensions, validation integrity, security/secret hygiene, and bounded adjacent-risk scan — but did not address *how* reviewers should approach the check.

Neither the reviewer prompt (`qa_architect_slice_review_prompt.md`) nor the planning template (`slice_planning_prompt_template.md`) contained any instruction telling the reviewer or planner to act independently. A long checklist without behavioral framing can produce confirmation-loop behavior: the AI reads the listed items and confirms them rather than challenging the underlying plan. This ADR addresses that gap.

### Decision

Add a shared **Independence preface** section to `qa_architect_slice_review_prompt.md`, placed after the existing role declaration ("Act as a QA Architect and Solution Architect reviewer.") and before the "Context to establish" section. The preface applies to both Mode A and Mode B without duplication.

Expand the **Important** section in `slice_planning_prompt_template.md` so planning does not assume the suggested path is automatically correct.

Add a **stop-and-explain** sentence to the Session Constraints in `agentic_workflow_rules.md` so implementation stops and explains rather than silently expanding scope if a better path is discovered mid-edit.

No existing review dimensions, output format sections, or validation/security checks are removed or weakened.

### Independence preface text

> Do not treat the review items below as a checklist to confirm — use them as context and known risk areas. Verify the actual repo state before evaluating the plan or implementation. Challenge assumptions, identify missing risks, and propose a better approach or flag a follow-up slice if the plan or implementation is not the best option. Bring in industry judgment around CI/CD reliability, release governance, security, data handling, maintainability, and consulting blueprint value. Both modes apply this framing.

### Why a shared preface, not per-mode additions

Mode A and Mode B have the same independence gap. A per-mode duplicate would be inconsistent and verbose. The shared preface is placed in the common preamble so both modes inherit it without repetition.

### ADR-013 relationship

ADR-013 changed *what* to check by adding validation integrity, security/secret hygiene, and bounded adjacent-risk scan expectations. ADR-019 changes *how* to approach the review by adding independence framing. Separating them keeps ADR-013 focused on technical review hardening while ADR-019 documents the behavioral framing needed to prevent checklist-confirmation drift.

### Alternatives considered

- **Remove the checklists entirely** — rejected. Known risk areas are still valuable; removing them would make reviews vague and non-repeatable.
- **Add separate prefaces to Mode A and Mode B** — rejected as unnecessary duplication. Both modes need the same behavioral framing.
- **Update `CLAUDE.md`** — rejected. Changes to CLAUDE.md affect all sessions globally; this change is scoped to the slice review and planning workflow.
- **Add a mandatory "assumptions challenged" output section** — deferred. If the preface proves insufficient to shift reviewer behavior, this is the next escalation step (see Activation condition below).

### Consequences

Future Mode A and Mode B reviews should challenge plan assumptions, propose alternatives or follow-up slices when warranted, and verify the actual repo state before evaluating the plan. Future planning prompts should interrogate the suggested path before proposing implementation. Future implementation work should stop and explain before changing scope mid-edit.

All existing validation integrity, security/secret hygiene, and adjacent-risk scan checks (Mode B Dimensions 1–11, Mode A evaluation subsections) remain mandatory and unchanged.

### Activation condition

If reviews still drift into mechanical checklist confirmation despite this preface, add a required "Assumptions challenged" output section to both modes that forces the reviewer to name at least one assumption they tested and either confirmed against the repo or rejected. This escalation is the next step before considering a Mode C (security-only) or Mode D (architectural challenge) review pass.

### Related PRs / Docs

- `agentic-qa-workflows/prompts/qa_architect_slice_review_prompt.md` — v3; primary artifact of this ADR
- `agentic-qa-workflows/prompts/slice_planning_prompt_template.md` — v2; Important section expanded
- `agentic-qa-workflows/governance/agentic_workflow_rules.md` — Session Constraints; stop-and-explain addition
- ADR-013 — predecessor (bounded adjacent-risk scan, validation integrity, security/secret hygiene)

---

## ADR-020: Script unit test layer for release-readiness and notification decision logic

**Status:** Accepted
**Date:** 2026-06-06

### Context

`scripts/release_gate.py` (321 lines) drives the CI GO/NO_GO decision — the artifact that feeds the notification chain and determines whether a release can proceed. `scripts/ci_summary.py` (86 lines) parses JUnit XML to produce the GitHub Step Summary for each CI job. `compute_overall_readiness()` in `scripts/notify.py` determines BLOCKED/GO/NO_GO/UNKNOWN for notification dispatch based on upstream CI job statuses and the gate decision.

All three had zero test coverage. For a consulting QA architecture blueprint, an untested release decision engine is the largest credibility gap: the QA practice does not apply to itself.

### Decision

Add `test/scripts/` as a new test layer for offline unit tests of QA platform logic. Add a `scripts` pytest marker to identify this layer. Run script tests in the **Docker Test Suite job** (`test` job in `ci.yml`), as a new step after test collection verification. This positions script tests as infrastructure-level gates alongside formatting, linting, type-checking, and security scanning — not as application-level API or UI tests.

Add `scripts/__init__.py` to make `scripts/` an explicit Python package and avoid relying on namespace package behavior for imports in tests.

### What is tested

**Scope note:** These are unit tests for repo-owned QA tooling — `release_gate.py`, `ci_summary.py`, and `notify.py` — not unit tests for the external application under test. This layer does not test SauceDemo, Restful Booker, or any backend we do not own.

- `parse_test_results()` in `release_gate.py`: JUnit XML parsing for the cases that affect CI — valid passing XML, valid XML with failures, missing file (raises `FileNotFoundError`), and malformed XML (raises `ValueError`).
- `evaluate_gate()` in `release_gate.py`: all 4 hard gate conditions (test failures, test errors, high error rate, open blocker defects) and the warning-only path (p95 latency and defect escape count both over threshold → GO with exactly 2 warnings, no gate failures).
- `summarize()` in `ci_summary.py`: all 4 branches — missing file returns error string, malformed XML returns error string, all-passing returns `✅` indicator, with-failures returns `❌` indicator and the failed test name.
- `compute_overall_readiness()` in `notify.py`: all 4 return values (GO, NO_GO, UNKNOWN, BLOCKED), including the documented edge case that absent or empty-string CI status keys do not trigger BLOCKED (only a truthy non-`"success"` value does), and that all three blocking statuses — `failure`, `cancelled`, `skipped` — trigger BLOCKED.

### What is explicitly excluded

- **`main()` entrypoints**: integration-style; require full artifact file tree setup; deferred.
- **`build_output()` and `render_markdown()`**: formatting functions with no decision logic; format string assertions are brittle on cosmetic changes; deferred.
- **`send_slack()` and `send_email()`**: require network calls; no stdlib mocking is added in this slice; deferred to a dedicated notification-delivery test slice.
- **`pull_observability.py`**: all provider implementations are stubs returning hardcoded sample data; zero decision value until live providers are connected.
- **JUnit XML reporter for script tests**: deferred in PR #35 (initial script-test slice) pending layer growth. Activated early for blueprint consistency — the `test` job now produces `artifacts/scripts-report.xml` and publishes a `Script Unit Test Results` check via `dorny/test-reporter`. All test layers are now first-class CI reporting signals.

### Why the Docker Test Suite job, not a new job

Script tests validate CI platform logic, not application behavior. They belong in the same gate that validates the platform itself — alongside formatting, linting, type-checking, and security scanning. A separate job would create unnecessary fan-out for 19 test functions that run in under a second combined.

### Why no production script refactor

All target functions (`parse_test_results`, `evaluate_gate`, `summarize`, `compute_overall_readiness`) accept parameters directly. None require path resolution at import time or network access. Tests construct inputs via `tmp_path` and plain dicts. No refactor is needed to achieve full branch coverage of the decision logic.

### Alternatives considered

- **No new marker — fold into existing test tree without a `scripts` marker**: rejected. The `scripts` marker enables `pytest -m scripts` selection, distinguishes script tests from application tests in CI output, and makes the test layer explicit in governance documentation.
- **Split into three PRs** (one per script): rejected. All three functions feed the same release readiness pipeline. Combined scope is 19 test functions — still PR-sized. Three PRs add process overhead without architectural benefit.
- **Subprocess/integration tests for `main()`**: deferred. Subprocess tests require full artifact file tree setup and test integration behavior, not decision logic. Decision logic is covered by unit tests of the underlying functions.

### Consequences

`test/scripts/` is the canonical location for offline unit tests of QA platform scripts. Any new decision logic added to `release_gate.py`, `ci_summary.py`, or `notify.py` should be tested here before the function is used in CI. Script tests run on every push, PR, and nightly build. The `test` job gates CI on both quality checks and script test results.

Script test reporting activated: `artifacts/scripts-report.xml` is produced by the `test` job and published as `Script Unit Test Results` via `dorny/test-reporter`. `Script Unit Test Results` is advisory only (`fail-on-error: false`) — `Docker Test Suite` remains the required branch-protection gate. Promote `Script Unit Test Results` to a required check only after it consistently passes on main and the team intentionally follows the ADR-010 branch-protection process. Future work: add delivery function tests (`send_slack`, `send_email`) in a separate slice with appropriate stdlib mocking.

### Trade-offs and cost / benefit

#### 1. Dedicated `test/scripts/` layer vs. folding script tests into API/UI tests

| | Dedicated `test/scripts/` | Folded into `test/api/` or `test/ui/` |
|---|---|---|
| **Benefit** | Separation of concerns: platform logic tests are clearly distinct from application behavior tests. `pytest -m scripts` targets the layer precisely. CI step is scoped and named for its purpose. | No new directory. Reuses existing conftest. |
| **Cost / maintenance** | New directory, new conftest, new marker, new CI step, new ADR. | Platform logic tests mixed with application tests. Harder to distinguish in CI output, collection, and governance. Misleading: `test/api/` would contain tests that never call the API. |
| **Risk** | Minimal. The layer is small and well-bounded. | Taxonomy drift: the `api` or `ui` marker would be misapplied to tests validating offline Python logic. Future contributors would not know which suite these tests belong to. |
| **Decision** | **Accepted** | **Rejected** |

#### 2. New `scripts` marker vs. no marker (path-only selection)

| | New `scripts` marker | No marker — `pytest test/scripts/` only |
|---|---|---|
| **Benefit** | Explicit taxonomy entry. Enables `pytest -m scripts` for targeted execution. Visible in `suite_taxonomy.md` and `pytest.ini` for governance traceability. Cross-marker expressions (`pytest -m "scripts and smoke"`) are possible. | No marker declaration overhead. |
| **Cost / maintenance** | One marker entry in `pytest.ini`, one `suite_taxonomy.md` section, one decorator per test function. | Selection is brittle if the directory is ever restructured. No taxonomy record of this layer's purpose, constraints, or run trigger. |
| **Risk** | Low. Declared before use per existing taxonomy governance. | No documented constraint that these tests must have no network calls or secrets. Future contributors have no governance anchor for this layer. |
| **Decision** | **Accepted** | **Rejected** |

#### 3. One combined script-test PR vs. splitting release_gate / ci_summary / notify into separate PRs

| | Combined PR (all three scripts) | Three separate PRs |
|---|---|---|
| **Benefit** | 19 test functions across three scripts is still PR-sized. All three functions feed the same release readiness pipeline — the test layer is coherent as a single deliverable. One ADR. One taxonomy update. One CI step. | Each PR is smaller in isolation. Easier to revert one script's tests independently. |
| **Cost / maintenance** | Slightly wider review scope than a single-script slice. | Three PRs, three ADR updates, three rounds of Mode A + Mode B review overhead. Risk of shipping half the coverage with no clear "done" state. |
| **Risk** | Low. The three scripts are tightly coupled: `ci_summary` parses JUnit XML that feeds the release gate context; `notify` aggregates the gate decision. | Mid-pipeline state: one script has tests, adjacent scripts do not, which creates a false sense of coverage completeness and leaves the coupled pipeline partially validated. |
| **Decision** | **Accepted** | **Rejected** |

#### 4. Testing pure decision logic now vs. testing Slack/SMTP delivery now

| | Pure decision logic (`evaluate_gate`, `compute_overall_readiness`, `summarize`) | Slack/SMTP delivery (`send_slack`, `send_email`) |
|---|---|---|
| **Benefit** | Pure functions with no external dependencies. Full branch coverage achievable with plain dicts and `tmp_path`. Zero network calls, zero secrets, zero mocking infrastructure. Highest return per test line written. | Delivery functions are the final output stage; a test that confirms end-to-end delivery closes the full pipeline loop. |
| **Cost / maintenance** | Delivery behavior remains untested in this slice. A live delivery bug would not be caught here. | Requires stdlib mocking (`unittest.mock.patch` on `urllib.request.urlopen`, `smtplib.SMTP`, `smtplib.SMTP_SSL`) or a live test target. Mock maintenance overhead scales with delivery code path count. Secrets cannot be present in test files under any circumstances. |
| **Risk** | Delivery-path bugs are not caught until CI live delivery is configured. Known and accepted; deferred to a dedicated notification-delivery test slice. | Mock drift: mocks that do not accurately reflect real `smtplib` or `urllib` behavior can pass tests while real delivery fails. Imprecise mock setup produces false confidence. |
| **Decision** | **Accepted** — decision logic now | **Deferred** — delivery in a separate slice |

#### 5. Adding script-test JUnit reporting now vs. deferring until the layer is proven

| | JUnit XML + `dorny/test-reporter` now | Defer JUnit reporting |
|---|---|---|
| **Benefit** | Script test results appear in the GitHub Actions test panel alongside API and UI results. Full structured visibility from day one. | Simpler CI step. No `--junitxml` flag, no new artifact path, no new `dorny/test-reporter` step, no artifact name collision risk. |
| **Cost / maintenance** | New `--junitxml` flag, new artifact path (`artifacts/scripts-report.xml`), new `dorny/test-reporter` step in the `test` job, new artifact name to manage across CI re-runs. | Results visible only in raw CI step log with `-v` output. Acceptable for a 21-test layer that runs in 0.05 seconds. |
| **Risk** | Low, but adds configuration surface to the `test` job before knowing whether the layer will grow. Over-instrumenting a small layer adds maintenance cost that may never be amortized. | Script test failures surface in step logs; verbose output is sufficient at this layer size. |
| **Decision** | **Deferred** — add when the layer grows past ~50 tests or when a client engagement requires structured test reporting for platform tests |

### Related PRs / Docs

- `test/scripts/test_release_gate.py` — release gate decision logic coverage
- `test/scripts/test_ci_summary.py` — CI summary parsing coverage
- `test/scripts/test_notify_readiness.py` — notification readiness coverage
- `scripts/__init__.py` — makes `scripts/` an explicit Python package
- ADR-009 — API-only release gate design (upstream context)
- ADR-016 — aggregate CI notification job (upstream context)

---

## ADR-021: workflow_dispatch inputs for parameterized manual CI runs

**Status:** Accepted
**Date:** 2026-06-07

### Context

`workflow_dispatch:` was declared bare in `.github/workflows/ci.yml` — no inputs block. Every manual trigger ran the full test suite with `TEST_SCOPE=full` and read `NOTIFY_DRY_RUN` from the `vars.NOTIFY_DRY_RUN` repository variable. Operators had no per-run control over either behavior.

Two operator needs were identified that the bare dispatch did not support:

1. A fast smoke-only sanity check after a hotfix or recovery — without waiting for a full regression run.
2. Per-run notification override — an operator who wants a guaranteed dry-run for a specific dispatch (to validate CI scope without notification noise) had to edit and then revert the `NOTIFY_DRY_RUN` repo variable, creating a multi-step process with a window of unexpected behavior.

ADR-014 states that `workflow_dispatch` always triggers a full suite run. This slice amends that decision: `full` remains the default, but operators can now select `smoke`.

### Decision

Add two `workflow_dispatch` inputs. Both are closed `type: choice` selects with safe defaults that preserve existing behavior for all non-dispatch triggers and for dispatch runs that do not change the inputs.

#### Input 1: `test_scope`

```yaml
test_scope:
  description: "Test scope — full runs all tests and the release gate; smoke runs smoke-tagged tests only"
  required: false
  default: full
  type: choice
  options:
    - full
    - smoke
```

Default `full` — all existing dispatch runs that did not set this input continue to run the full suite.

The `Determine test scope` step in both `API Tests` and `UI Tests` jobs is updated to check `github.event_name == 'workflow_dispatch'` first and read `inputs.test_scope` only in that branch. Non-dispatch triggers (`push` to main, `schedule`, PR, feature branch push) continue to use the existing logic without change.

#### Input 2: `notification_mode`

```yaml
notification_mode:
  description: "Notification mode — repo_default uses NOTIFY_DRY_RUN variable; dry_run/live override for this manual run"
  required: false
  default: repo_default
  type: choice
  options:
    - repo_default
    - dry_run
    - live
```

Default `repo_default` — all existing dispatch runs that did not set this input continue to use `vars.NOTIFY_DRY_RUN`, preserving current behavior. An operator who has `NOTIFY_DRY_RUN=true` set and dispatches with the default input continues to get a dry-run, as before.

Semantics for dispatch runs:
- `repo_default` → writes `NOTIFY_DRY_RUN=${{ vars.NOTIFY_DRY_RUN }}` to `$GITHUB_ENV`; current repo variable behavior is preserved
- `dry_run` → writes `NOTIFY_DRY_RUN=true` to `$GITHUB_ENV`; forces dry-run regardless of repo variable
- `live` → writes `NOTIFY_DRY_RUN=` (empty string) to `$GITHUB_ENV`; forces live delivery regardless of repo variable (delivery still requires secrets to be configured)

For `schedule` and `push` to `main`, `inputs.notification_mode` is inaccessible (returns empty string on non-dispatch events). The "Determine notification mode" step is guarded by `github.event_name == 'workflow_dispatch'` and falls through to `vars.NOTIFY_DRY_RUN` on all other triggers.

`NOTIFY_DRY_RUN` is removed from the `Deliver aggregate CI notification` step's `env:` block. A step-level `env:` key overrides `$GITHUB_ENV` for that step; removing the key allows `$GITHUB_ENV` (set by the prior "Determine notification mode" step) to flow through. All other env vars in the delivery step's `env:` block are unchanged.

### Inputs deferred

**Environment selector (prod_read_only):** Rejected. ADR-015 defines a five-item activation checklist for prod-read-only: real prod URLs, per-environment GitHub Secrets, `read_only` suite safety review, test-reporter publication for prod XML, and optional URL injection. None of these are complete. A dispatch input that can request `prod_read_only` would bypass the ADR-015 checklist — an operator could select it before real prod URLs or credentials exist, producing confusing silent failures. Defer until the ADR-015 checklist is satisfied.

**Free-text marker expression:** Rejected. A free-text input (e.g., `api_contract`) allows mistyped expressions (e.g., `-m regresiion`) that produce passing CI with zero tests collected. No operator use case requires targeting a single marker via dispatch — `smoke` and `full` cover the two documented execution contexts. Targeted marker runs are a developer-only concern handled locally.

**Observability provider selector:** Rejected. All provider implementations in `scripts/pull_observability.py` are stubs returning static sample data. An input selecting between Datadog, Grafana, and PagerDuty stubs has no functional effect. Defer until at least one stub is replaced with a real implementation.

### Impact on existing triggers

| Trigger | TEST_SCOPE | NOTIFY_DRY_RUN source | Changed? |
|---|---|---|---|
| `push` to `main` | `full` | `vars.NOTIFY_DRY_RUN` | No |
| `schedule` (nightly) | `full` | `vars.NOTIFY_DRY_RUN` | No |
| `pull_request` to main | `smoke` | N/A — notify doesn't fire | No |
| `push` to `feature/**` | `smoke` | N/A — notify doesn't fire | No |
| `workflow_dispatch` (default inputs) | `full` | `vars.NOTIFY_DRY_RUN` | Behavior equivalent; now explicit |
| `workflow_dispatch` (`test_scope=smoke`) | `smoke` | `vars.NOTIFY_DRY_RUN` | New capability |
| `workflow_dispatch` (`notification_mode=dry_run`) | `full` | `NOTIFY_DRY_RUN=true` | New capability |
| `workflow_dispatch` (`notification_mode=live`) | `full` | `NOTIFY_DRY_RUN=` (empty) | New capability |

### Smoke dispatch and the release gate

When `test_scope=smoke` is selected, `TEST_SCOPE=smoke` is set and the release gate step calls `release_gate.py --skipped "$TEST_SCOPE"` instead of exiting without artifacts. `release_gate.py` writes a schema-consistent placeholder: `artifacts/release-readiness.json` with `overall_decision: "UNKNOWN"` and `gate_skipped: true`, and `artifacts/release-readiness.md` with a "release gate intentionally skipped" notice. The upload-artifact step uploads the placeholder; the `notify` job's download step succeeds without error. `notify.py` detects `gate_skipped: true` and displays "Release Gate (staging API): ⚠️ Skipped — smoke-only run does not produce a release gate decision" rather than ❌ UNKNOWN or a missing-data warning. Overall readiness remains UNKNOWN — accurate, because a smoke run does not produce sufficient evidence for a release decision.

**Amendment note:** The initial ADR-021 text stated "No remediation is required; UNKNOWN on a smoke dispatch is the correct signal." Manual validation revealed that the missing artifact produced an "Artifact not found" error in the Notify job log and a misleading "No release gate data (gate did not run or api job failed)" notification message. The behavior was corrected: `release_gate.py` now owns the placeholder output (consistent schema, testable), and `notify.py` handles `gate_skipped: true` explicitly. Full-run paths are unchanged.

### Alternatives considered

| Option | Why rejected |
|---|---|
| Free-text `marker_expression` input | Invalid expressions produce passing CI with zero tests run — no operator use case justifies this risk |
| Three-choice `test_scope` (full / smoke / api_contract) | `api_contract` is a developer-facing targeted run, not an operator scope; two choices align with the suite taxonomy's two execution contexts |
| `notification_mode=live` as default | If `NOTIFY_DRY_RUN=true` is set as a repo variable, defaulting to `live` would bypass it and unexpectedly trigger live delivery on dispatch — not backward-compatible |
| Shell guard in delivery step instead of a separate "Determine notification mode" step | `env:` block values are resolved at step startup before the shell runs; a prior step writing to `$GITHUB_ENV` is the correct cross-step communication pattern |
| Environment selector for prod_read_only | Bypasses ADR-015 activation checklist; no real prod URLs committed; deferred explicitly |

### Consequences

- Operators can run `workflow_dispatch` with `test_scope=smoke` for a fast post-hotfix sanity check.
- Operators can run `workflow_dispatch` with `notification_mode=dry_run` to force a dry-run on a specific dispatch without editing the repo variable.
- Operators can run `workflow_dispatch` with `notification_mode=live` to force live delivery on a specific dispatch when `NOTIFY_DRY_RUN=true` is set as a repo variable.
- All non-dispatch triggers are unchanged.
- `NOTIFY_DRY_RUN` is no longer in the `Deliver aggregate CI notification` step's `env:` block; it flows through `$GITHUB_ENV` from the preceding "Determine notification mode" step.
- ADR-014 is amended: `workflow_dispatch` scope is now `full` by default but selectable.

### Activation condition

No further activation required. Both inputs are live immediately. Revisit deferred inputs (environment selector, observability provider) when their respective prerequisite conditions are met.

### Related PRs / Docs

- `.github/workflows/ci.yml` — `on.workflow_dispatch.inputs` block; updated "Determine test scope" steps × 2; new "Determine notification mode" step; removed `NOTIFY_DRY_RUN` from delivery step `env:`
- `agentic-qa-workflows/governance/quality_gates.md` — CI test scope by trigger table updated
- `agentic-qa-workflows/governance/notification_wiring.md` — `notification_mode` input documentation added
- ADR-011 — `NOTIFY_DRY_RUN` repo variable behavior (unchanged for non-dispatch triggers)
- ADR-014 — smoke/full trigger scope (amended: `workflow_dispatch` scope is now selectable)
- ADR-015 — prod-read-only activation gate (environment selector deferred to avoid bypassing this checklist)
- ADR-016 — aggregate Notify job structure (Determine notification mode step added)
- ADR-017 — observability stubs (observability provider input deferred)

### Trade-offs and consulting value

**The backward-compatibility constraint on `notification_mode` default is the key decision.** Setting the default to `live` would have been simpler to reason about ("dispatch input overrides the repo variable") but would have silently changed behavior for any team that has `NOTIFY_DRY_RUN=true` in their repo variable. The `repo_default` option preserves the principle that adding an input must not change existing behavior — operators who do not use the input get exactly the same run they had before.

**The closed-select decision for `test_scope` is the most important safety call.** A free-text marker input would allow operators to express targeted runs (`api_contract`, `regression`) without requiring a taxonomy change. The cost is invisible: a mistyped expression passes CI with zero tests collected and no warning in the job summary (pytest exits 0 with an empty collection). For a consulting blueprint, this class of invisible CI pass is worse than a slightly less expressive UI. Two choices are enough.

**For a consulting client**, both inputs demonstrate the correct CI ergonomics pattern: operator-facing controls that expose only safe, well-defined choices, default to preserving existing behavior, and are backed by clear per-run semantics. The `notification_mode` input in particular shows the correct way to provide per-run override capability without requiring repo variable editing — a pattern that recurs in any CI environment where multiple operators need different delivery behavior on specific runs.

---

## ADR-022: Blueprint prompt packaging — link to working prompt files, do not copy

**Status:** Accepted
**Date:** 2026-06-09

### Context

`blueprint/README.md` Section 5 (Agentic QA Workflow Pattern) linked to three prompt files under `agentic-qa-workflows/prompts/` but did not document the 4-step slice workflow or cover all five prompts. A dedicated `blueprint/prompts/` folder was identified as the next extraction slice, with the ownership question deferred: keep prompts in `agentic-qa-workflows/prompts/` (link from blueprint) or move them to `blueprint/prompts/`.

Two structural options were evaluated:
- **Copy or move** prompt files into `blueprint/prompts/` — gives blueprint consumers a self-contained folder but creates two sources of truth
- **Link only** — create `blueprint/prompts/README.md` as a workflow guide that links to source files; source files remain in `agentic-qa-workflows/prompts/`

### Decision

Keep reusable prompt source files under `agentic-qa-workflows/prompts/`. Add `blueprint/prompts/README.md` as a standalone workflow guide that links to those files. Do not copy or move prompt files.

### Rationale

- `agentic-qa-workflows/prompts/README.md` already holds operational context (versioning notes, revision history, usage instructions) that would have to be duplicated or summarized in a copied version
- The ADR log (this file) references prompt file paths at ADR-013 and ADR-019 — moving files would require retroactively updating ADR artifacts
- Prompt files are actively versioned (v2, v3 with dated revision notes); a copied version is stale from the moment it is written and would diverge within a few PRs
- The blueprint's own design principle: "Every blueprint area points to working source files. Use them as the reference, not as files to copy." Prompts are working source files.

### Consequences

- `blueprint/prompts/README.md` must be updated when new prompts are added to `agentic-qa-workflows/prompts/` (one table row per new file)
- Blueprint documentation must link to source prompt files rather than reproducing their content
- This ADR establishes the ownership pattern for future blueprint extraction decisions: assets that are actively used and versioned in the working repo should be linked from `blueprint/`, not copied

### Related files

- `blueprint/prompts/README.md` — new file; primary artifact of this ADR
- `blueprint/README.md` — Section 5 updated; Slice 2 row in extraction table resolved

---

## ADR-023: Dependency update triage workflow

**Status:** Accepted
**Date:** 2026-06-08

### Context

Dependabot creates pull requests weekly for both `pip` and `github-actions` ecosystems. Without a documented triage workflow, PRs accumulate: no agreed merge cadence means no one merges them, newer updates arrive on top of unprocessed older ones, and the version gap grows until a multi-major jump requires substantial review.

By June 2026, five GitHub Actions PRs had been open for 7+ days, with version jumps ranging from +1 to +4 major versions. The root cause was not the updates themselves — all five had full CI green — but the absence of a process for deciding when and how to merge them.

A second structural issue: CI passing on a Dependabot PR confirms the existing test suite runs with the updated action. It does not confirm that the action's behavioral contract (output variables, permission model, edge-case behavior) is unchanged. GitHub Actions are CI infrastructure, not just code dependencies, and must be reviewed accordingly.

### Decision

1. **Adopt a three-checker triage model**: Dependabot creates candidate PRs → CI/security gates validate them → a human reviewer decides to merge, defer, or investigate.

2. **No auto-merge for GitHub Actions major version updates.** A broken action update disables the ability to detect regressions in the product under test. Multi-major version jumps require human changelog review. The `actions/upload-artifact` and `actions/download-artifact` interaction requires coordinated merging that auto-merge cannot enforce.

3. **Require human review before merging any GitHub Actions major version update.** The reviewer checklist in `dependency_update_triage.md` defines the minimum review for Tier 1, 2, and 3 (coordinated) updates.

4. **Coordinate artifact-actions updates.** `actions/upload-artifact` and `actions/download-artifact` interact in the same pipeline (API Tests uploads, Notify downloads). Group them in `dependabot.yml` so they arrive as a single PR. For PRs that arrived before the group was configured, review and merge both in the same review window.

5. **Cap open GitHub Actions PRs at 3.** Set `open-pull-requests-limit: 3` for the `github-actions` ecosystem. This prevents more than 3 updates from queuing simultaneously, forcing older ones to be processed before new ones arrive.

6. **Set a Monday schedule for GitHub Actions updates.** PRs arriving at the start of the work week receive more review attention than those arriving mid-week or on Friday.

7. **Document cadence expectations.** GitHub Actions updates: review within 7 days. Python pip patch/minor: review within 14 days. Security-labeled PRs: review within 24 hours.

### Consequences

- Dependency PRs will accumulate less because the cap and Monday schedule align arrival with review bandwidth.
- Human review effort increases slightly: major version bumps require changelog review before merging. This is the correct tradeoff — the alternative (merging without review) creates invisible CI infrastructure risk.
- The triage workflow must be applied to the current backlog of open PRs (PR #14, #15, #16, #17, #40) before the next Dependabot cycle.
- Python pip patch/minor auto-merge is a future option if desired; it requires a separate ADR and `dependabot.yml` configuration change.
- The playwright ignore rule (ADR-007) is unaffected.
- `actions/dependency-review-action` was evaluated and deferred to a future slice. It will be considered after the triage workflow has been applied to at least one real update cycle and its advisory gate behavior can be validated against this repo's PR patterns.

### Related files

- `agentic-qa-workflows/governance/dependency_update_triage.md` — full triage workflow, risk tiers, reviewer checklist, cadence; primary artifact of this ADR
- `.github/dependabot.yml` — `artifact-actions` group; `open-pull-requests-limit: 3`; Monday schedule; playwright ignore rule unchanged
- ADR-007 — playwright ignore rule; activation condition for removing the ignore rule

---

## ADR-024: PR failure notifications behind NOTIFY_PR_FAILURES activation gate

**Status:** Accepted
**Date:** 2026-06-10

### Context

A real PR check failure exposed a gap in the notification policy: the `Notify` job was not configured to run on `pull_request` events. The failure was visible in the GitHub PR status panel but no Slack or email notification was delivered. Teams relying on Slack for CI awareness had no active alert.

The existing trigger policy (ADR-016, ADR-018) covered `schedule`, `workflow_dispatch`, and push-to-main failures. ADR-011 explicitly excluded `pull_request` events ("not on pull request or feature branch push"). That exclusion was correct as a starting default — PR failures during active development are frequent and noisy — but is now worth overriding with an opt-in gate.

### Decision

Expand the `notify` job `if:` condition in `.github/workflows/ci.yml` to include pull request failures when the `NOTIFY_PR_FAILURES` repository variable is set to `true`:

```yaml
(github.event_name == 'pull_request' && vars.NOTIFY_PR_FAILURES == 'true' &&
(needs.test.result != 'success' || needs.api.result != 'success' || needs.ui.result != 'success'))
```

`NOTIFY_PR_FAILURES` is a **repository variable** (Settings → Secrets and variables → Actions → Variables tab), not a secret. When unset or any value other than `'true'`, PR failures remain silent — the GitHub PR status panel is the only CI signal.

No changes to `scripts/notify.py`. The script already handles all PR edge cases correctly:
- Smoke runs produce `release-readiness.json` with `gate_skipped: true` (ADR-021 amendment) — the artifact exists even when tests fail.
- `notify.py` reads `gate_skipped: true` and displays "Release Gate: ⚠️ Skipped — smoke-only run".
- A failed required job makes overall readiness `BLOCKED` via the existing `compute_overall_readiness()` logic.
- If `Docker Test Suite` fails, downstream jobs are skipped; `notify.py` handles empty `needs.*.result` env vars gracefully.

### Alternatives rejected

**Notify all PR failures (no gate):** Rejected. PR failures during active development are frequent — WIP branches, iterative fixes, experiments. Notifying on every failure without an opt-in would generate more noise than signal and defeat the "opinionated silence" principle from ADR-018. Teams should receive a notification only when they have chosen to receive it.

**Label-based notification (`notify-on-failure` PR label):** Rejected. Requires per-PR label management — authors must remember to add the label, and the label must be present before the failure occurs. A single repo variable is simpler to reason about and easier to toggle without touching individual PRs.

**Defer PR notification entirely:** Rejected. A real PR failure proved the gap has operational impact. The fix is one condition clause and no script changes — the risk is low and the value is immediate.

### Consequences

- PR failures produce active Slack/email notification when `NOTIFY_PR_FAILURES=true`. When unset, behavior is unchanged.
- Fork PRs do not have access to repository secrets — Slack and email channels dry-run for fork-origin PR failures even when `NOTIFY_PR_FAILURES=true`. This is the correct safe default.
- `NOTIFY_DRY_RUN` and `NOTIFY_PR_FAILURES` operate independently: `NOTIFY_PR_FAILURES` controls job eligibility; `NOTIFY_DRY_RUN` controls channel delivery. Both can be set independently to stage validation.
- The `Notify` job remains non-blocking and advisory. It is not a required status check. Branch protection is unchanged.
- `scripts/notify.py`, `blueprint/scripts/notify.py`, and all other files are unchanged.

### Activation condition

1. Add `SLACK_WEBHOOK_URL` to GitHub Settings → Secrets → Actions (Slack live delivery).
2. Confirm `NOTIFY_DRY_RUN` is unset or `false` in repository variables.
3. Add `NOTIFY_PR_FAILURES=true` to GitHub Settings → Secrets and variables → Actions → Variables tab.
4. Validate: create a failing PR and confirm the `Notify` job appears in the PR CI panel and delivers to Slack.

### Deferred

- SMTP/Gmail live delivery validation — runner SMTP restrictions may require port 465 or a transactional email API; deferred to a separate slice.
- Forced-live critical failure notifications — deferred until live delivery is reliably validated end-to-end.
- Transactional email API (SendGrid, AWS SES, Postmark) — would require a non-stdlib dependency and a new ADR; deferred.
- Blueprint asset updates — `blueprint/scripts/notify.py` adaptation notes do not need updating until the production script changes; reassess after second-repo adoption.

### Related PRs / Docs

- `.github/workflows/ci.yml` — `notify` job `if:` condition
- `agentic-qa-workflows/governance/notification_wiring.md` — trigger table; `NOTIFY_PR_FAILURES` section; Slack live validation steps; SMTP deferred note
- `agentic-qa-workflows/governance/quality_gates.md` — CI job structure table Notify row; Notification Delivery trigger table
- `agentic-qa-workflows/governance/security_and_branch_protection.md` — gate classification table Notification delivery row
- ADR-011 — notification dry-run default; PR exclusion was the original policy; this ADR fulfills ADR-011 activation condition ("Expand the notification step's trigger condition to additional triggers if broader notification coverage is needed")
- ADR-016 — aggregate Notify job structure; `if:` condition being extended
- ADR-018 — failure-only push-to-main notification; "opinionated silence" principle extended to PR events with opt-in gate
- ADR-021 — smoke dispatch placeholder artifact; ensures `release-readiness.json` exists on PR runs so the `Notify` job can download it without error

### Trade-offs and consulting value

**The opt-in gate is the key design decision.** Notifying on all PR failures by default produces a team that ignores notifications — exactly the failure mode the notification infrastructure was built to avoid. An opt-in variable requires a deliberate choice, which means teams that enable it have already decided they want the signal. The cost of the gate is one extra setup step; the benefit is a notification channel that teams actually read.

**The fork PR behavior is worth documenting explicitly.** Open-source contributors and collaborators working from forks will not receive live notifications even when `NOTIFY_PR_FAILURES=true` is set. This is a GitHub Actions platform constraint (fork PRs cannot access repo secrets), not a bug. Documenting it prevents false assumptions about notification completeness.

**The "no script changes" outcome is the correct architecture validation.** Adding PR failure support required only a CI condition change — no new logic in `notify.py`, no new env vars in the delivery step, no new artifact handling. This confirms that the aggregate notification architecture (ADR-016) was designed with sufficient generality to accommodate new trigger types without structural changes.

---

## ADR-025: Dockerfile OS package upgrade for CVE remediation

**Status:** Accepted
**Date:** 2026-06-10

### Context

During base-image drift in June 2026, the Docker image scan surfaced a fixable HIGH OpenSSL CVE (CVE-2026-45447) in the Ubuntu 24.04 OS layer of the Playwright base image. The vulnerable packages were Ubuntu OS packages (`libssl3t64`, `openssl`) — not Python dependencies and not Playwright test code. Patched Ubuntu packages were available before a newer Playwright base image was published. The Trivy advisory database had been updated to flag the CVE, but the Playwright base image had not yet been rebuilt with the patch.

The Trivy step is a hard gate that exits 1 on fixable HIGH/CRITICAL findings. The CI failure was real and blocking.

### Decision

Add `apt-get upgrade -y --no-install-recommends` to the Dockerfile apt step, before project dependency installation. This ensures every `docker build` pulls the latest patched OS packages from the Ubuntu package repository, resolving fixable OS-layer CVEs without requiring a Playwright base image version bump.

```dockerfile
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && apt-get install -y --no-install-recommends python3.12-venv \
    && rm -rf /var/lib/apt/lists/*
```

### Alternatives rejected

- **Suppress the CVE with `--ignore-unfixed`** — rejected. This flag only suppresses findings with no available fix. CVE-2026-45447 had a patched package available, so `--ignore-unfixed` did not suppress it.
- **Immediately bump the Playwright base image** — rejected for OS-layer CVEs when patched OS packages are already available. A base image bump introduces Playwright/browser/Node version changes that require coordinated testing. OS package patches can be applied without changing the browser runtime.
- **Accept the CVE temporarily** — rejected. The Trivy gate is a hard CI gate for fixable HIGH/CRITICAL findings. Bypassing it undermines the security posture the gate was designed to enforce.

### Consequences

- OS-layer CVEs with available Ubuntu package fixes are remediated during `docker build`.
- The Docker layer may change as Ubuntu publishes security updates between base image releases. This is acceptable for a QA automation image rebuilt on every CI run.
- This does not remediate Playwright, browser, or Node CVEs embedded in the base image. Those require a coordinated base image tag bump and Playwright pip package update (see ADR-007).
- `apt-get upgrade` is a broad OS upgrade. Running before project dependency installation ensures the OS layer is patched before project code is added.

### Related PRs / Docs

- PR #55 — OpenSSL CVE fix implementation
- `Dockerfile` — `apt-get upgrade` step
- `security_and_branch_protection.md` — Docker base image lifecycle section
- `dependency_update_triage.md` — OS-layer CVEs versus Playwright version updates; ADR-007 relationship
- ADR-007 — Dependabot with Playwright version ignored; coordinated base image update policy

---

## ADR-026: Dependency Review Action as advisory PR dependency-diff gate

**Status:** Accepted
**Date:** 2026-06-11

### Context

ADR-023 established dependency update triage governance and deferred `actions/dependency-review-action` until the repo had a clearer dependency-review operating model.

The repo already has several complementary dependency and security controls:

- Dependabot opens scheduled dependency update PRs.
- pip-audit scans installed Python dependencies during Docker CI.
- Trivy scans the built Docker image for fixable HIGH/CRITICAL CVEs.
- CodeQL runs static security analysis.
- ADR-025 documents OS-layer CVE remediation through Docker build package upgrades.

Dependency Review adds a different signal: it evaluates dependency changes introduced by a pull request before merge using GitHub's dependency comparison and advisory data.

### Decision

Add `actions/dependency-review-action` as a separate pull-request-only workflow.

Initial configuration:

- separate `.github/workflows/dependency-review.yml`
- `pull_request` trigger only
- `permissions: contents: read`
- `actions/dependency-review-action@v5`
- `fail-on-severity: high`
- `comment-summary-in-pr: never`
- `license-check: false`
- not added to branch protection required checks

This makes the check visible on PRs without making it a required merge gate during the first validation cycle.

### Rejected alternatives

- **Add the job to `ci.yml`** — rejected. `ci.yml` has push, pull_request, schedule, and workflow_dispatch triggers. Dependency Review is PR-diff-specific and is clearer as a separate purpose-scoped workflow with its own narrow permissions.
- **Make Dependency Review required immediately** — rejected. ADR-023 called for observing advisory behavior first. Promoting an unobserved gate to required status risks making noisy or misunderstood findings into merge blockers.
- **Enable PR comments immediately** — rejected. PR comments require `pull-requests: write`. The first pass keeps permissions minimal and relies on job logs and check summaries.
- **Enable license enforcement immediately** — rejected. The repo has not defined an allow/deny license policy. Enforcing licenses without a policy creates noise instead of governance.

### Consequences

- Pull requests that introduce vulnerable dependencies at high severity or above will show a failing advisory Dependency Review check.
- Because the check is not required in branch protection, it does not block merges during the first validation cycle.
- Dependency Review complements pip-audit and Trivy; it does not replace either.
- License policy enforcement is explicitly deferred.

### Activation condition

Revisit promotion to a required gate only after all of the following are true:

1. At least one complete post-ADR-023 Dependabot cycle has run with Dependency Review enabled.
2. Advisory behavior has been observed against real PRs.
3. Noise level and failure modes are understood.
4. A license policy has been defined if license checks are desired.
5. A separate Mode A review approves promotion to required status.

### Related PRs / Docs

- ADR-023 — Dependency update triage workflow
- ADR-025 — Dockerfile OS package upgrade for CVE remediation
- `dependency_update_triage.md`
- `security_and_branch_protection.md`
- `.github/workflows/dependency-review.yml`

---

## ADR-027: Gmail SMTP live delivery validation outcome

**Status:** Accepted
**Date:** 2026-06-14

### Context

Slack live delivery had already been validated for aggregate CI notifications. Gmail/SMTP email delivery remained open after aggregate notification wiring was added.

`notify.py` already supported generic SMTP delivery using `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, and `NOTIFY_RECIPIENTS`. It supported Gmail App Password configuration, STARTTLS on port `587`, and SMTP_SSL on port `465`.

PR #60 added safe SMTP diagnostics before live validation so the selected transport path would be visible without printing secrets.

### Validation

A manual `workflow_dispatch` run was executed on the PR branch with `test_scope=full` and `notification_mode=live`, using Gmail App Password credentials configured through GitHub Actions secrets.

Observed result:

- Required CI jobs passed.
- Release readiness was `GO`.
- Slack delivered successfully with HTTP 200.
- Email attempted delivery via STARTTLS on port `587`.
- Email delivered to one recipient.
- Gmail placed the message in Spam.
- The `Notify` job succeeded.
- No secrets were printed in logs.

### Decision

Gmail SMTP using STARTTLS on port `587` is validated as a working live email delivery path from GitHub Actions for this repo.

Email delivery remains advisory and secondary. Slack remains the primary validated live notification channel because Gmail may classify automation-generated messages as Spam.

The documented Gmail path remains `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_PASSWORD=<Gmail App Password>`.

Port `465` remains documented as a fallback path for network/connectivity failures on port `587`, but it was not needed for this validation.

### Rejected alternatives

- **Treat Spam placement as delivery failure** — rejected. The SMTP server accepted the message and the recipient received it. Spam placement is a deliverability caveat, not an SMTP delivery failure.
- **Switch to port 465 after successful 587 delivery** — rejected. Port `587` successfully delivered, so there is no evidence-based reason to change ports.
- **Make email delivery a hard CI gate** — rejected. Notifications are operational signals and must remain advisory.
- **Add a transactional email provider immediately** — rejected. Gmail SMTP is validated. A transactional provider may still be useful later for stronger inbox placement, but that requires a separate Mode A review.
- **Print full SMTP exception messages** — rejected. SMTP server responses may include email addresses or provider-specific details. The script continues logging exception class names only.

### Consequences

- The repo now has two validated live notification channels: Slack (primary) and Gmail SMTP (secondary, with Spam-placement caveat).
- Teams using Gmail should check Spam during initial setup and mark the message as not spam.
- Email remains advisory; failed or delayed email delivery must not fail CI.
- Transactional email API integration remains a future option only if stronger deliverability is required.

### Related PRs / Docs

- `scripts/notify.py`
- `notification_wiring.md`
- PR #60 — SMTP live delivery diagnostics and validation procedure

---

## ADR-028: API pytest-xdist activation with serial UI and script execution

**Status:** Accepted
**Date:** 2026-06-14

### Context

The behavioral test suite reached 22 tests after PR #62: 13 API and 9 UI. This crossed the `>20` behavioral-test threshold documented in `parallelization_readiness.md`.

PR #63 split the API suite into behavior-grouped files, making API fixture dependencies and parallelization risk easier to inspect before activation.

A fixture isolation audit was completed before enabling process-level parallelism.

### Decision

Activate `pytest-xdist` for the standard API Tests CI job only, using:

```bash
pytest test/api $MARKER_ARGS -v -n auto --junitxml=artifacts/api-report.xml
```

UI tests and script tests remain serial.

The prod-read-only API step remains serial because it is a small gated read-only subset and should stay conservative until production activation is reviewed separately.

### Fixture audit result

- `booking_api` is safe: stateless HTTP client, immutable after construction.
- `auth_token` is safe: immutable string; each worker process creates its own token via a separate `/auth` POST; no test mutates it.
- `booking_payload_factory` is safe: function-scoped factory with no shared mutable state.
- `created_booking` is safe for API xdist: each fixture invocation creates a unique booking ID, and teardown deletes that specific booking. Concurrent teardowns delete distinct resources. The prior concern about concurrent DELETE teardowns in `parallelization_readiness.md` was incorrect — a race would only exist if tests shared a single pre-created booking, which they do not.
- Read-only data fixtures (`test_data`, `base_url`, `api_base_url`, `credentials`) are safe: loaded data is not mutated by any test.

### Why API first

API tests have no browser-context isolation concerns and are the best first target for xdist. The suite now has enough behavioral tests to justify a controlled activation.

### Why UI remains serial

UI tests remain serial because Playwright browser/page/context isolation under xdist requires a separate Mode A review. The current UI suite has 9 tests, which does not yet justify adding browser-parallelization risk in the same PR.

### Why scripts remain serial

Script tests are governance and tooling checks. They are fast and should remain deterministic, especially the TC-ID uniqueness guard (TC-SCRIPT-031) and release gate logic.

### Rejected alternatives

- **Activate API and UI xdist together** — rejected. UI isolation requires a separate Mode A review.
- **Use `--dist=loadscope`** — rejected. With tests now split across five behavior-grouped files, `loadscope` would assign each module to a single worker, reducing effective distribution.
- **Use explicit `-n 2`** — rejected. `-n auto` is idiomatic and adapts to available runner CPU without hardcoding an assumption about runner size.
- **Add xdist globally via `pytest.ini` `addopts`** — rejected. Activation should be command-specific, not global. Script tests must remain serial.
- **Parallelize script tests** — rejected. Script governance checks should remain serial and deterministic.

### Consequences

- API Tests job now runs with process-level parallelism (`-n auto`).
- UI Tests and Docker Test Suite remain unchanged.
- JUnit output is produced by the API Tests job and remains compatible with the existing `dorny/test-reporter` step.
- If API flakiness appears post-activation, first rollback is to remove `-n auto` from the API Tests command.

### Rollback

Remove `-n auto` from the normal `Run API test suite` command in `.github/workflows/ci.yml`. No fixture changes are required for rollback. `pytest-xdist` may remain in `requirements.txt` — it is inert when not invoked with `-n`.

### Future follow-up

A separate Mode A review should evaluate UI xdist when either:

- UI test count exceeds 15, or
- UI job runtime exceeds 3 minutes, or
- a portfolio or client need justifies browser-level parallel execution.

### Related docs

- `parallelization_readiness.md` — fixture isolation audit details and future activation conditions
- `requirements.txt` — `pytest-xdist` dependency
- `.github/workflows/ci.yml` — `Run API test suite` step

---

## ADR-029: UI pytest-xdist activation with serial script and prod-read-only execution

**Status:** Accepted
**Date:** 2026-06-15

### Context

API xdist was activated in ADR-028. The UI suite remained serial pending a Playwright/browser-context isolation review.

PR #66 split the UI suite into behavior-grouped files:

- `test_login_ui.py`
- `test_cart_ui.py`
- `test_checkout_ui.py`

PR #66 also hardened failure artifact filenames from `item.name` to a sanitized `item.nodeid` stem, reducing collision risk before UI parallelization.

The portfolio/client blueprint now benefits from demonstrating both API and UI parallelization patterns while keeping production-gated and governance-critical paths conservative.

### Decision

Activate `pytest-xdist` for the standard UI Tests CI job only, using:

```bash
pytest test/ui $MARKER_ARGS -v -n auto --junitxml=artifacts/ui-report.xml
```

The prod-read-only UI step, script tests, and Docker Test Suite remain serial.

### Fixture isolation audit

- Session-scoped data fixtures (`base_url`, `credentials`, `locked_out_credentials`, `checkout_data`, `test_data`) are safe because they are read-only and not mutated by UI tests.
- The `page` fixture is function-scoped. Each UI test receives its own Playwright page/context through pytest-playwright.
- `expect.set_options(timeout=UI_EXPECT_TIMEOUT_MS)` sets process-global Playwright expectation timeout inside each worker process. Under xdist, workers are separate Python subprocesses, so workers do not share this state.
- Page objects (`LoginPage`, `InventoryPage`, `CartPage`, `CheckoutPage`) are instantiated inside individual tests from the function-scoped page fixture and do not share state.

### Failure artifact safety

The failure evidence hook now writes screenshots and HTML dumps using a sanitized `item.nodeid` stem.

This makes artifact filenames unique across:

- split UI files
- future duplicate test function names in different files
- future parameterized tests

### Why UI xdist is safe

pytest-playwright works with pytest-xdist because workers run in separate subprocesses and tests receive isolated Playwright page/context fixtures. The current UI tests do not share mutable state.

### Why `-n auto`

This matches ADR-028 for API xdist. It is idiomatic and adapts to available runner CPU without hardcoding `-n 2`.

### Why default `--dist=load`

The UI suite has 9 tests across three behavior-grouped modules. Default load distribution is simple and sufficient.

### Why prod-read-only UI remains serial

The prod-read-only UI path is a production-gated subset and should remain conservative and serial.

### Why scripts remain serial

Script tests are fast governance checks. Serial execution keeps the TC-ID uniqueness guard, release gate checks, notification checks, and CI summary checks deterministic.

### Why Docker Test Suite remains serial

The Docker Test Suite remains the serial source-of-truth baseline for collection, script unit tests, quality checks, and security checks.

### Rejected alternatives

- **Activate API and UI xdist in one PR** — rejected. API xdist was intentionally activated first in ADR-028. UI xdist is activated independently after the UI suite split and artifact hardening in PR #66.
- **Use fixed `-n 2`** — rejected. `-n auto` is consistent with ADR-028 and adapts to runner CPU.
- **Use `--dist=loadscope`** — rejected. Default `--dist=load` is simpler and sufficient for the current suite.
- **Parallelize scripts** — rejected. Script governance checks remain serial and deterministic.
- **Parallelize prod-read-only UI** — rejected. Production-gated paths remain conservative.

### Consequences

- UI Tests job now runs with process-level parallelism.
- API Tests job remains unchanged and already uses xdist from ADR-028.
- Docker Test Suite remains unchanged.
- JUnit output remains compatible with the existing `dorny/test-reporter` step.
- UI failure artifact capture remains unchanged and now uses sanitized node IDs.

### Rollback

Remove `-n auto` from the standard `Run UI test suite` command in `.github/workflows/ci.yml`.

Do not remove `pytest-xdist` from `requirements.txt`, because API xdist still depends on it.

### Future follow-up

When UI coverage grows, evaluate cross-browser matrix execution (`chromium`, `firefox`, `webkit`) or cloud grid execution as separate decision-gated slices.

### Related docs

- `parallelization_readiness.md` — fixture audit and activation state
- `.github/workflows/ci.yml` — `Run UI test suite` step
- `failure_evidence.md` — artifact filename convention

---

## ADR-030: Cross-browser UI matrix and cloud-grid preflight with safe-skip policy

**Status:** Accepted
**Date:** 2026-06-14

### Context

API xdist (ADR-028) and UI xdist (ADR-029) are complete. ADR-029's Future follow-up cited
cross-browser matrix and cloud grid as the next area. `parallelization_readiness.md` Future
Activation Conditions listed cross-browser as a separate review requiring a Mode A architecture
review before activation.

The Playwright base image (`mcr.microsoft.com/playwright/python:v1.60.0-noble`) pre-installs all
three browsers (chromium, firefox, webkit) with their system dependencies — no Dockerfile change
is required to activate cross-browser testing.

### Decision

Activate a cross-browser UI matrix CI job (`ui-cross-browser`) on nightly schedule and
`workflow_dispatch` only, running the smoke suite across `chromium`, `firefox`, and `webkit`.
The job is advisory (`continue-on-error: true`) and is not listed in branch protection required
checks.

Add `scripts/cloud_grid_preflight.py`, a credential-safe preflight script that validates whether
a cloud browser-grid provider is configured and reachable. The script always exits 0 for
missing, invalid, or unreachable credentials. It exits 1 only for repository configuration bugs
(unknown provider value). Cloud-grid execution is deferred to a separate slice.

**Cross-browser CI command (per matrix leg):**

```bash
pytest test/ui -m smoke -v --browser ${{ matrix.browser }} \
  --junitxml=artifacts/ui-${{ matrix.browser }}-report.xml
```

**Preflight provider model:** `CLOUD_GRID_PROVIDER=none | sauce` (default: `none`).

### Why nightly and workflow_dispatch only

Cross-browser CI is orthogonal to functional correctness — it validates rendering and browser
engine compatibility, not feature correctness. Running it on every PR would slow the PR feedback
loop without adding signal relevant to merge decisions. Nightly is sufficient to surface
browser-specific regressions.

### Why smoke only

Nine UI tests × 3 browsers = 27 executions if the full suite is used. Smoke (1 test × 3 browsers)
proves the matrix configuration is correct and the browser-specific rendering path works. Full
cross-browser can be activated in a later slice once smoke stability is confirmed.

### Why advisory

Demo-site CSS/rendering differences across browsers are not blocking defects in a reference
implementation. Cross-browser failures should surface as advisory signal, not merge blockers.

### Why no xdist inside matrix legs

Each matrix leg runs 1 smoke test. Spawning 2 xdist workers for 1 test adds process overhead
with zero parallelism benefit. No xdist inside cross-browser legs.

### Why safe-skip on missing or invalid cloud credentials

CI must never fail due to absent secrets. The pattern mirrors Slack/SMTP notification channels
(ADR-011): missing credentials trigger a dry-run log message and exit 0, not a CI failure. Cloud
providers are optional external dependencies — a missing `SAUCE_ACCESS_KEY` is a configuration
choice, not a broken build.

### Preflight output statuses

| Status | Meaning | Exit code |
|---|---|---|
| `READY` | Credentials valid; provider reachable | 0 |
| `SKIPPED_NOT_CONFIGURED` | `CLOUD_GRID_PROVIDER=none` or unset | 0 |
| `SKIPPED_MISSING_CREDENTIALS` | Required secrets not set | 0 |
| `SKIPPED_INVALID_CREDENTIALS` | Provider API returned 401 or 403 | 0 |
| `SKIPPED_PROVIDER_UNAVAILABLE` | Network error, timeout, or unexpected HTTP error | 0 |
| `ERROR_UNKNOWN_PROVIDER` | Unsupported provider value — repo configuration bug | 1 |

### Rejected alternatives

- **Required cross-browser gate:** rejected — cross-browser variability at a demo site should not
  block PRs.
- **xdist inside matrix legs:** rejected — 1 smoke test per leg; overhead exceeds benefit.
- **Full UI suite cross-browser in PR #68:** rejected — smoke first, prove stability, expand
  later.
- **BrowserStack in PR #68:** deferred — Sauce Labs is the concrete first implementation;
  BrowserStack can be added as a second provider in a later slice.
- **Jenkins template in PR #68:** deferred — no client requirement established yet; evaluate
  after second-repo adoption identifies whether a Jenkins adapter is needed.

### Consequences

- `ui-cross-browser` matrix job runs on nightly and workflow_dispatch; advisory; 3 browser legs.
- `notify` job `needs: [test, api, ui]` — unchanged; cross-browser is not a notify dependency.
- Release gate: unchanged; consumes `api-report.xml` only.
- Collection count: 65 nodes (55 existing + 10 new TC-SCRIPT-032–TC-SCRIPT-041 preflight unit
  tests).
- `scripts/cloud_grid_preflight.py` and `test/scripts/test_cloud_grid_preflight.py` added.

### Rollback

**Cross-browser matrix:** Remove the `ui-cross-browser` job from `.github/workflows/ci.yml`.
Advisory — no branch protection to update. No other job depends on it.

**Cloud-grid preflight:** Remove `scripts/cloud_grid_preflight.py` and
`test/scripts/test_cloud_grid_preflight.py`. No CI job depends on the preflight output until a
cloud-grid execution slice (PR #69) is implemented.

Both rollbacks are independent of each other and do not affect existing API or UI test jobs.

### Future follow-up

- PR #69: Sauce Labs cloud-grid execution step, gated on `READY` preflight status.
- Full UI suite cross-browser: activate when smoke cross-browser is stable and coverage
  justifies the added execution time.
- BrowserStack: add as a second provider option when a client requirement establishes the need.

### Related docs

- `parallelization_readiness.md` — xdist activation state; Future Activation Conditions
- `.github/workflows/ci.yml` — `ui-cross-browser` job
- `scripts/cloud_grid_preflight.py` — preflight implementation
- `test/scripts/test_cloud_grid_preflight.py` — preflight unit tests (TC-SCRIPT-032–TC-SCRIPT-041)

---

## ADR-031: Sauce Labs cloud-grid execution gated by preflight readiness

**Status:** Accepted
**Date:** 2026-06-14

### Context

ADR-030 (PR #68) implemented `scripts/cloud_grid_preflight.py` — a credential-safe preflight
script that validates whether a cloud browser-grid provider is configured and reachable. ADR-030
explicitly deferred actual cloud-grid execution to a separate slice:

> "PR #69: Sauce Labs cloud-grid execution step, gated on `READY` preflight status."

The `CLOUD_GRID_PROVIDER=none|sauce` provider model is established. Preflight exits 0 for all
skip conditions and exits 1 only for an unknown provider value (repository configuration bug).

### Decision

Add a `cloud-grid` CI job (advisory, nightly + `workflow_dispatch`, chromium smoke suite, gated
on `READY` preflight status). Override the `browser` fixture in `conftest.py` to detect
`CLOUD_GRID_PROVIDER=sauce` and connect to Sauce Labs via
`playwright.{browser_name}.connect(endpoint)`. Fall back to local browser launch when
`CLOUD_GRID_PROVIDER` is unset or `none`.

**Cloud-grid CI command (when preflight status is `READY`):**

```bash
pytest test/ui -m smoke -v --browser chromium \
  --junitxml=artifacts/cloud-grid-report.xml
```

**`browser` fixture override (conftest.py):**

```python
@pytest.fixture(scope="session")
def browser(playwright, browser_name, browser_type_launch_args):
    cloud_provider = os.environ.get("CLOUD_GRID_PROVIDER", "none").strip().lower()
    if cloud_provider == "sauce":
        # endpoint URL embeds credentials — never printed or logged
        endpoint = (
            f"wss://{username}:{access_key}@ondemand.{region}.saucelabs.com"
            f":443/playwright/{browser_name}"
        )
        b = getattr(playwright, browser_name).connect(endpoint)
        yield b
        b.close()
    else:
        b = getattr(playwright, browser_name).launch(**browser_type_launch_args)
        yield b
        b.close()
```

### Preflight gate behavior

| Preflight status | Cloud execution | Job result |
|---|---|---|
| `READY` | Runs Sauce Labs chromium smoke suite | Advisory pass/fail |
| `SKIPPED_NOT_CONFIGURED` | Step skipped; summary note written | Success |
| `SKIPPED_MISSING_CREDENTIALS` | Step skipped; summary note written | Success |
| `SKIPPED_INVALID_CREDENTIALS` | Step skipped; summary note written | Success |
| `SKIPPED_PROVIDER_UNAVAILABLE` | Step skipped; summary note written | Success |
| `ERROR_UNKNOWN_PROVIDER` | Preflight exits 1; cloud step skipped | Failure — repo config bug |

### Why `conftest.py` browser fixture override

The `browser` fixture (session-scoped, pytest-playwright) controls browser launch. Overriding it
is the only approach that runs existing pytest tests against Sauce Labs without duplicating test
logic. Alternatives rejected:

- **Standalone script** — duplicates all test scenario logic outside pytest; two codebases to
  maintain; does not prove real pytest tests run against Sauce Labs.
- **`test/cloud/conftest.py`** — separate invocation path creates two maintenance surfaces;
  requires duplicating or importing test files.
- **Provider CLI tooling** — no CLI-driven Playwright cloud execution tool exists for Python
  pytest.

The fixture change is minimal (~20 lines), gated by `CLOUD_GRID_PROVIDER` env var, and reuses
`browser_type_launch_args` so all pytest-playwright defaults are preserved in the local fallback.

### Why advisory

Cloud provider availability, session limits, and billing are external dependencies outside the
repo's control. Sauce Labs failures must not block PRs or merges. Same rationale as
`ui-cross-browser` (ADR-030).

### Why nightly and `workflow_dispatch` only

Cloud execution validates provider connectivity and session provisioning, not feature
correctness. Running it on every PR would consume Sauce Labs session quota without adding signal
relevant to merge decisions. Nightly is sufficient to surface provider-side regressions.

### Why smoke only

1 smoke test × 1 cloud session proves the cloud path works. Full cloud suite is PR #70. Smoke
first — confirm stability, then expand.

### Why preflight gates execution

Mirrors the Slack/SMTP dry-run philosophy (ADR-011) and ADR-030: missing or invalid credentials
are configuration choices, not broken builds. CI must never fail due to absent secrets. The
preflight output (`cloud-grid-preflight.json`) is the single authoritative signal for whether
cloud execution should run.

### Why chromium only

Sauce Labs recommends Chromium as the first Playwright browser. Multi-browser cloud matrix
(chromium + firefox + webkit on Sauce Labs) is PR #70.

### Why no xdist inside the cloud-grid job

1 smoke test. Spawning 2 xdist workers opens 2 Sauce Labs sessions for zero parallelism benefit.
Sauce Labs charges per session/minute.

### Why Sauce Labs first, not BrowserStack

ADR-030 established Sauce Labs as the concrete first implementation. BrowserStack is a separate
provider slice, deferred until a client requirement establishes the need.

### Why Jenkins template not in this PR

Same deferral as ADR-030. No client requirement established; evaluate after second-repo adoption.

### Security constraints

- Sauce Labs credentials (`SAUCE_USERNAME`, `SAUCE_ACCESS_KEY`) are embedded in the WebSocket
  endpoint URL and never printed, logged, or written to artifacts.
- Exception handler in the `browser` fixture uses `from None` to suppress chained tracebacks
  that might contain the URL; only `type(exc).__name__` surfaces in the error message.
- `CLOUD_GRID_PROVIDER` and `SAUCE_REGION` are non-sensitive repository variables (not secrets).

### Consequences

- `cloud-grid` CI job runs on nightly and `workflow_dispatch`; advisory; chromium only.
- `notify` job `needs: [test, api, ui]` — unchanged; cloud-grid is not a notify dependency.
- Release gate: unchanged; consumes `api-report.xml` only.
- Collection count: 65 nodes — unchanged (no new test files).
- `conftest.py` adds a session-scoped `browser` fixture override; local execution paths
  are unaffected (fallback branch is identical to pytest-playwright's default behavior).

### Rollback

**Cloud-grid job:** Remove the `cloud-grid` job from `.github/workflows/ci.yml`. Advisory — no
branch protection to update. No other job depends on it.

**`conftest.py` fixture override:** Remove the `browser` fixture from `conftest.py`. pytest-playwright
resumes ownership. Existing tests are unaffected — they never depended on the override in local
mode.

Both rollbacks are independent and do not affect the existing `test`, `api`, `ui`,
`ui-cross-browser`, or `notify` jobs.

### Future follow-up

- PR #70: Multi-browser cloud matrix (chromium, firefox, webkit on Sauce Labs).
- BrowserStack: add as a second provider option when a client requirement establishes the need.
- Jenkins blueprint: evaluate after second-repo adoption identifies whether a Jenkins adapter is
  needed.

### Related docs

- `parallelization_readiness.md` — cloud-grid execution state
- `.github/workflows/ci.yml` — `cloud-grid` job
- `conftest.py` — `browser` fixture override
- `scripts/cloud_grid_preflight.py` — preflight implementation (ADR-030)
- `test/scripts/test_cloud_grid_preflight.py` — preflight unit tests (TC-SCRIPT-032–TC-SCRIPT-041)

---

## ADR-032: Advisory job notification and cloud-grid provider-failure messaging

**Status:** Accepted
**Date:** 2026-06-15

### Context

ADR-031 (PR #69) activated Sauce Labs cloud-grid execution and PR #68 activated the cross-browser
UI matrix. A manual run with Sauce Labs enabled proved the advisory lane works end-to-end but
revealed three gaps:

1. Connection failure message was too generic: `"Sauce Labs connection failed: Error"` — no provider,
   region, browser, or likely-cause information.
2. Connection attempt took ~5 minutes with no explicit timeout cap — `playwright.connect()` was
   called without a `timeout` parameter.
3. Notification did not include advisory job status — cloud-grid and cross-browser failures were
   invisible in the aggregate CI signal. Required and advisory lanes looked identical in the
   notification output.

Additionally, `continue-on-error: true` on both advisory jobs means `needs.*.result` returns
`'success'` even when tests fail. Naively reading `needs.cloud-grid.result` cannot distinguish
PASS from FAIL — a status artifact is required.

### Decision

**1. Sauce Labs connection timeout:** Add `SAUCE_CONNECT_TIMEOUT_MS` env var (default 60 000 ms)
to the `browser` fixture `connect()` call:

```python
timeout_ms = int(os.environ.get("SAUCE_CONNECT_TIMEOUT_MS", "60000"))
getattr(playwright, browser_name).connect(endpoint, timeout=timeout_ms)
```

Configurable via `vars.SAUCE_CONNECT_TIMEOUT_MS` in CI. Passed to Docker with
`-e SAUCE_CONNECT_TIMEOUT_MS="${SAUCE_CONNECT_TIMEOUT_MS:-60000}"`.

**2. Structured failure message:** Replace the generic `"Sauce Labs connection failed: Error"`
with a multi-line message that includes provider, region, browser, error type, likely causes,
and a "secrets redacted" line. Credentials and the WebSocket endpoint URL are never printed.

**3. Advisory status artifacts:** Each advisory CI job writes a per-job status JSON file
(`artifacts/cloud-grid-status.json`, `artifacts/cross-browser-{browser}-status.json`) after
execution, regardless of outcome. The `cloud-grid` job uses `steps.sauce_run.outcome` (real
outcome) vs `steps.sauce_run.conclusion` (always `'success'` due to `continue-on-error: true`).

**4. `notify.needs` extended:** Add `ui-cross-browser` and `cloud-grid` to `notify.needs`.
This ensures `Notify` waits for advisory jobs on nightly and `workflow_dispatch` before
delivering the notification. On PR and push-to-feature triggers, advisory jobs are SKIPPED
immediately, so `Notify` is never delayed on those events.

**5. `notify.py` extended:** New `load_advisory_status()` reads status artifact files and env
vars. `build_message_lines()` gains an `advisory_status` parameter and appends an Advisory Jobs
section when advisory jobs were scheduled (both `needs.*.result == 'skipped'` → section hidden).
`compute_overall_readiness()` is UNCHANGED — advisory status is display-only.

### Why `needs.*.result` is insufficient for `continue-on-error` advisory jobs

When `continue-on-error: true` is set on a job (or matrix job), GitHub Actions sets
`needs.<job>.result = 'success'` even when the job fails. The only safe way to detect SKIPPED
(never scheduled) vs EXECUTED (ran, pass or fail) is `needs.*.result == 'skipped'`. For actual
PASS/FAIL distinction, a status artifact written by the job is required.

| Scenario | `needs.cloud-grid.result` | Actual status |
|---|---|---|
| Job not scheduled (PR/push) | `skipped` | SKIPPED — omit advisory section |
| Preflight status is SKIPPED_* | `success` | SKIPPED — read from artifact |
| Sauce connection failed | `success` | FAIL — read from artifact |
| Smoke suite tests failed | `success` | FAIL — read from artifact |
| All tests passed | `success` | PASS — read from artifact |

### Why advisory status in notifications

Hiding advisory failures defeats their purpose as signal. The advisory lane exists to surface
cloud-provider and cross-browser issues without blocking the required release lane. A failing
Sauce Labs run that is invisible in the notification provides no signal value.

**Required release readiness** (GO/NO_GO/BLOCKED) is computed only from Docker Test Suite,
API Tests, UI Tests, and the release gate. Advisory status cannot change this verdict.

### Why secrets remain redacted in failure messages

CI step logs can be read by anyone with repository access. The WebSocket endpoint URL embeds
`username:access_key`. Only `type(exc).__name__` and non-sensitive contextual metadata
(region, browser name) are included in the error message. `from None` suppresses chained
tracebacks that might contain credential strings.

### Why PR #71 multi-browser cloud matrix is deferred

PR #70 establishes the observability foundation: timeout cap, structured messaging, and advisory
status in notifications. Expanding to firefox + webkit on Sauce Labs should follow after PR #70
proves the notification infrastructure works correctly in production with chromium.

### Consequences

- `conftest.py` browser fixture: timeout cap + structured failure message for Sauce connections.
- `cloud-grid` CI job: `id: sauce_run`, `continue-on-error: true` on smoke step; new "Write
  cloud-grid execution status" step; new "Upload cloud-grid status artifact" step.
- `ui-cross-browser` CI job: new "Write cross-browser execution status" step per matrix leg;
  new "Upload cross-browser status artifact" step per leg.
- `notify` job: `needs` extended to `[test, api, ui, ui-cross-browser, cloud-grid]`; advisory
  artifact download steps added; `UI_CROSS_BROWSER_RESULT` and `CLOUD_GRID_RESULT` env vars
  added to delivery step.
- `notify.py`: `load_advisory_status()` added; `build_message_lines()` gains `advisory_status`
  parameter (default `None` — existing tests unaffected); advisory section appended when
  advisory jobs were scheduled.
- `compute_overall_readiness()`: UNCHANGED.
- Collection count: 75 nodes (65 existing + 10 new TC-SCRIPT-042–TC-SCRIPT-051).

### Rollback

All four change groups are independently reversible and do not affect the required release lane:

1. **conftest.py timeout/message:** Revert to `connect(endpoint)` without timeout or set
   `SAUCE_CONNECT_TIMEOUT_MS=0` to use Playwright default.
2. **Advisory status artifact steps:** Remove write/upload steps from `cloud-grid` and
   `ui-cross-browser` jobs. No downstream impact.
3. **notify.py advisory section:** Remove `load_advisory_status()` call and advisory block
   from `build_message_lines()`.
4. **notify.needs:** Revert to `[test, api, ui]` — notify no longer waits for advisory jobs.

### Future follow-up

- BrowserStack: add as a second provider option when a client requirement establishes the need.
- Jenkins/client adapter: deferred until a specific client deployment target is established.

### Related docs

- `notification_wiring.md` — advisory status section; message structure
- `quality_gates.md` — CI job structure; notify depends-on column
- `.github/workflows/ci.yml` — `cloud-grid` job, `ui-cross-browser` job, `notify` job
- `conftest.py` — `browser` fixture override
- `scripts/notify.py` — `load_advisory_status()`, `build_message_lines()`
- `test/scripts/test_notify_readiness.py` — TC-SCRIPT-042–TC-SCRIPT-054

---

## ADR-033: Sauce Labs multi-browser cloud matrix and advisory browser-detail rendering

**Status:** Accepted
**Date:** 2026-06-15

### Context

ADR-032 (PR #70) established the advisory observability foundation: per-job status artifacts,
`load_advisory_status()`, and the Advisory Jobs section in notifications. The `cloud-grid` job
executed a single chromium smoke leg. This PR expands it to a 3-browser matrix and adds
per-browser detail rendering in the notification.

Three improvements are bundled because they are tightly coupled: the matrix expansion produces
per-browser artifacts; the aggregation logic consumes them; and the rendering makes the
aggregated result actionable. Separating them would require three PRs with no meaningful
intermediate state.

### Decision

1. Convert the `cloud-grid` CI job to a 3-browser matrix: `[chromium, firefox, webkit]`.
2. Each matrix leg writes a browser-specific status artifact:
   `artifacts/cloud-grid-{browser}-status.json`.
3. The `notify` job downloads all three via pattern download
   (`cloud-grid-*-execution-status`, `merge-multiple: true`).
4. `notify.py` reads per-browser cloud-grid artifacts via `CLOUD_GRID_BROWSERS` loop
   (matching the existing `CROSS_BROWSER_BROWSERS` pattern) and aggregates to
   PASS / FAIL / PARTIAL / SKIPPED / UNKNOWN using the same 5-branch logic as cross-browser.
5. Notification renders per-browser detail lines when cloud-grid aggregate is PARTIAL or FAIL.
6. Notification renders per-browser detail lines when cross-browser aggregate is PARTIAL
   (deferred item R5 from PR #70 Mode B, included here because the data is already collected
   and the rendering pattern is identical).
7. Legacy fallback: if no per-browser files exist but `artifacts/cloud-grid-status.json` does,
   `load_advisory_status()` reads it as the chromium result so pre-PR #71 artifacts remain
   readable without breaking existing tests.
8. Non-READY preflight states (both `SKIPPED_*` and `ERROR_*`) write a GitHub step summary
   line, making error states visible in the Actions panel (deferred item R2 from PR #70 Mode B).
9. Required release readiness (`compute_overall_readiness()`) is unchanged.

### Why cloud-grid expands to 3 browsers

Sauce Labs supports chromium, firefox, and webkit. PR #70 proved the advisory infrastructure
works end-to-end with chromium. Expanding to all three provides full cross-browser signal from
real remote devices — the same set that local `ui-cross-browser` tests cover — without
additional infrastructure cost beyond job time.

### Why cloud-grid remains advisory

Adding cloud-grid to the required release lane would make Sauce Labs account availability and
quota limits a release blocker. Advisory status provides signal without imposing infrastructure
dependency on the release process.

### Why cloud-grid remains smoke-only

Full regression on Sauce Labs per nightly would be cost-prohibitive. Smoke provides connectivity
and basic functionality signal. Full cloud regression is a future consideration gated on usage
patterns and cost review.

### Why per-browser detail is rendered on PARTIAL or FAIL only

Happy-path notifications (PASS) should be clean and scannable. Detail lines are diagnostic —
they are only useful when something is wrong. PARTIAL and FAIL trigger the expanded view;
PASS, SKIPPED, and UNKNOWN show a single summary line.

### Why BrowserStack is deferred

PR #71 proves the multi-browser cloud matrix pattern works. BrowserStack as a second provider
follows after a client requirement or comparative benchmark establishes the need.

### Why Jenkins/client adapter is deferred

No specific client deployment target has been established for this repo. The advisory lane
pattern is provider-agnostic; a Jenkins adapter would reuse `cloud_grid_preflight.py` and the
artifact write/upload pattern without changes to required lane semantics.

### Rollback

1. **Revert cloud-grid matrix:** change `strategy.matrix.browser` back to single `chromium`;
   rename artifact paths back to `cloud-grid-report.xml` and `cloud-grid-status.json`;
   revert notify download step to single-name download.
2. **Revert notify.py cloud-grid section:** remove `CLOUD_GRID_BROWSERS` loop; restore
   single-file `cg_artifact` read; remove `cloud_grid_by_browser` and
   `cloud_grid_detail_by_browser` keys from return dict.
3. **Revert build_message_lines per-browser rendering:** remove per-browser detail blocks
   for both cloud-grid and cross-browser; restore original single-line rendering.

None of these changes affect the required release lane.

### Consequences

- Cloud-grid nightly job time increases (3 browser legs × smoke duration, parallel).
- Notification advisory section shows per-browser breakdown when any cloud-grid leg fails.
- 9 new unit tests (TC-SCRIPT-055–TC-SCRIPT-063); collection total: 87 nodes.
- Pre-PR #71 artifacts (`cloud-grid-status.json`) are supported via legacy fallback.

### Related docs

- `notification_wiring.md` — multi-browser cloud-grid configuration; artifact naming; per-browser rendering rules
- `quality_gates.md` — CI job structure; `Cloud Grid` row updated to 3-browser matrix
- `.github/workflows/ci.yml` — `cloud-grid` matrix job; `notify` pattern download
- `scripts/notify.py` — `CLOUD_GRID_BROWSERS`, `load_advisory_status()`, `build_message_lines()`
- `test/scripts/test_notify_readiness.py` — TC-SCRIPT-042–TC-SCRIPT-063

---

## ADR-034: Cloud-grid provider abstraction, BrowserStack readiness preflight, and release-confidence notification signal

**Status:** Accepted
**Date:** 2026-06-15

### Context

ADR-033 (PR #71) proved the Sauce Labs 3-browser advisory cloud matrix end-to-end. The `cloud-grid` CI job, `cloud_grid_preflight.py`, and `notify.py` were all Sauce-specific. Three gaps remained:

1. Adding BrowserStack as a second cloud provider required code changes across preflight, CI, and notification — no abstraction layer existed.
2. The notification showed `Cloud Grid:` with no indication of which provider ran, making multi-provider signals ambiguous.
3. `Overall Release Readiness` (GO / NO_GO / UNKNOWN / BLOCKED) is accurate but machine-facing. Engineers reading notifications needed a plain-language confidence interpretation of the combined CI + gate + advisory signal.

### Decision

**1. Provider abstraction in `cloud_grid_preflight.py`:**
- Add `browserstack` as a known provider alongside `none` and `sauce`.
- Add `STATUS_SKIPPED_PROVIDER_EXECUTION_NOT_IMPLEMENTED` constant.
- BrowserStack branch: validate `BROWSERSTACK_USERNAME` + `BROWSERSTACK_ACCESS_KEY` presence only. Missing → `SKIPPED_MISSING_CREDENTIALS`. Present → `SKIPPED_PROVIDER_EXECUTION_NOT_IMPLEMENTED`. No HTTP check. Always exits 0.
- Unknown provider (e.g., `jenkins`) still exits 1 (`ERROR_UNKNOWN_PROVIDER`).

**2. Provider field in cloud-grid status artifacts:**
- The `Write cloud-grid execution status` step adds `"provider": "${{ vars.CLOUD_GRID_PROVIDER }}"` to each per-browser status JSON.
- `load_advisory_status()` reads `provider` from the first available artifact and returns `cloud_grid_provider` in its dict.
- Absent `provider` field (pre-PR #72 artifacts) → empty string → legacy `Cloud Grid:` label.

**3. Provider-aware notification labels:**
- Add `PROVIDER_LABELS: dict[str, str] = {"sauce": "Sauce Labs", "browserstack": "BrowserStack"}` constant.
- `build_message_lines()` renders `Cloud Grid (Sauce Labs):` / `Cloud Grid (BrowserStack):` / `Cloud Grid:` (fallback).

**4. BrowserStack secrets in CI:**
- Add `BROWSERSTACK_USERNAME` and `BROWSERSTACK_ACCESS_KEY` to the `Run cloud-grid preflight` step env.
- Absent secrets → empty strings → `SKIPPED_MISSING_CREDENTIALS`. CI never fails due to absent BrowserStack secrets.
- Secret values are never printed, logged, or written to artifacts.

**5. CI execution step rename:**
- `Run Sauce Labs smoke suite` → `Run cloud-grid smoke suite`.
- Condition `if: steps.preflight.outputs.status == 'READY'` unchanged. BrowserStack never reaches `READY` in PR #72, so the execution step is naturally skipped.

**6. Release Confidence line:**
- Add `compute_release_confidence(overall, data, advisory_status) → tuple[str, str, str]` to `notify.py`.
- `build_message_lines()` appends `Release Confidence: {emoji} {label} — {meaning}` immediately after `Overall Release Readiness`.
- Four levels: 🟢 High, 🟠 Low, 🟡 Medium, 🔴 Blocked.
- `compute_overall_readiness()` is unchanged — confidence is display-only.

**7. Live BrowserStack execution deferred to ADR-036.**

### Why provider abstraction before live execution

Credentials validation and provider registration should precede execution implementation. PR #72 proves the abstraction compiles, tests pass, and notifications correctly label providers before any live BrowserStack traffic is attempted. This avoids coupling provider-specific secrets and step names into the execution flow before the pattern is established.

### Why `SKIPPED_PROVIDER_EXECUTION_NOT_IMPLEMENTED`

Distinguishes "provider configured, credentials present, but execution not yet live" from:
- `SKIPPED_NOT_CONFIGURED` — `CLOUD_GRID_PROVIDER=none`
- `SKIPPED_MISSING_CREDENTIALS` — provider selected but secrets absent
- `SKIPPED_INVALID_CREDENTIALS` — Sauce credentials rejected

The status is actionable: it tells the operator that the provider is recognized and ready to activate, pending ADR-035.

### Why provider in artifact (not env var in notify step)

The artifact is self-describing. The `notify` job does not need a new `CLOUD_GRID_PROVIDER` env var. Backward compatibility is trivial — absent `provider` field → `cg_provider = ""` → `PROVIDER_LABELS.get("", "")` → `""` → fallback `Cloud Grid:` header. All pre-PR #72 tests continue to pass without modification.

### Why Release Confidence

`Overall Release Readiness` (GO / NO_GO / UNKNOWN / BLOCKED) is precise but requires mental mapping. The confidence line provides a single human-readable interpretation that combines required CI, gate decision, and advisory signals into an actionable phrase. Engineers can read a notification and immediately understand whether the release evidence is complete, incomplete, or blocked.

The four levels are designed to be exhaustive with no overlap:
- **Blocked**: required CI is not `success` — nothing else matters.
- **Low**: required CI passed, but gate is NO_GO or advisory has FAIL — caution before release.
- **High**: required CI passed, gate is GO, and advisory shows no FAIL or LIMITED signal — clean signal.
- **Medium**: everything else — signal exists but is incomplete (SKIPPED, UNKNOWN, PARTIAL, gate skipped).

### Why advisory remains advisory

Cloud Grid and Cross-Browser are not required checks. Adding them to the required release lane would make provider availability and quota limits a release blocker. Advisory status informs; it does not gate.

### Secret safety

`BROWSERSTACK_USERNAME` and `BROWSERSTACK_ACCESS_KEY` are passed to Docker as env vars. The BrowserStack branch in `cloud_grid_preflight.py` only tests for presence (`len > 0`); values are never interpolated into messages, printed, or written to artifacts. The `_write_artifacts()` function receives only the static `msg` string.

### Rollback

1. Remove `elif provider == "browserstack":` block and `STATUS_SKIPPED_PROVIDER_EXECUTION_NOT_IMPLEMENTED` constant from `cloud_grid_preflight.py`.
2. Remove `BROWSERSTACK_USERNAME` / `BROWSERSTACK_ACCESS_KEY` from CI preflight step env and docker args.
3. Remove `provider` field from `Write cloud-grid execution status` python one-liner.
4. Revert CI execution step name to `Run Sauce Labs smoke suite`.
5. Remove `PROVIDER_LABELS`, `cg_provider` extraction, and provider header logic from `notify.py`.
6. Remove `compute_release_confidence()` and the confidence line from `build_message_lines()`.
7. Revert TC-SCRIPT-041 to use `"browserstack"`; remove TC-SCRIPT-065–TC-SCRIPT-072.
8. Revert quality_gates.md, notification_wiring.md, README.md, agentic-qa-workflows/README.md.

None of these changes affect the required release lane.

### Consequences

- `cloud_grid_preflight.py`: BrowserStack recognized as a known provider; always exits 0.
- `.github/workflows/ci.yml`: BrowserStack secrets in preflight env; `provider` field in status artifacts.
- `notify.py`: `PROVIDER_LABELS`, `cloud_grid_provider` in return dict, `compute_release_confidence()`, provider-aware header, `Release Confidence` line.
- 8 new unit tests (TC-SCRIPT-065–TC-SCRIPT-072); collection total: 96 nodes.
- TC-SCRIPT-041 updated: provider changed from `"browserstack"` to `"jenkins"` (browserstack is now a known provider).

### Related docs

- `notification_wiring.md` — BrowserStack secrets; provider label rendering; Release Confidence table; per-browser artifact schema
- `quality_gates.md` — `Cloud Grid` row updated; `CLOUD_GRID_PROVIDER` values documented
- `.github/workflows/ci.yml` — `Run cloud-grid preflight` step env; `Write cloud-grid execution status` provider field
- `scripts/cloud_grid_preflight.py` — `STATUS_SKIPPED_PROVIDER_EXECUTION_NOT_IMPLEMENTED`; BrowserStack branch
- `scripts/notify.py` — `PROVIDER_LABELS`; `compute_release_confidence()`; `build_message_lines()` provider header and confidence line
- `test/scripts/test_cloud_grid_preflight.py` — TC-SCRIPT-041 updated; TC-SCRIPT-065–TC-SCRIPT-066
- `test/scripts/test_notify_readiness.py` — TC-SCRIPT-067–TC-SCRIPT-072

---

## ADR-035: Docker image build-once artifact reuse and registry-resilience hardening

**Status:** Accepted
**Date:** 2026-06-15

### Context

PR #72 introduced a Docker build retry loop scoped to the three required CI jobs (Docker Test Suite, API Tests, UI Tests) to mitigate repeated MCR (mcr.microsoft.com) rate-limit and auth failures on GitHub Actions shared runners. Each CI job ran independently on a fresh runner and rebuilt the Docker image from scratch, pulling the Playwright base image from MCR up to five times per run. The retry loop reduced blocking failures but did not eliminate the root cause: redundant base-image pulls that hit MCR's rate limits under shared-runner load.

Three gaps remained:

1. Four downstream jobs (API Tests, UI Tests, UI Cross-Browser, Cloud Grid) each rebuilt an identical image, paying the MCR pull cost independently.
2. Advisory jobs (UI Cross-Browser, Cloud Grid) had no retry loop — a single MCR auth failure would silently skip an advisory run.
3. The PR #72 retry comment `# Fresh runner — image must be rebuilt; Docker layer caching is a future optimization.` was deferred optimism with no implementation plan.

### Decision

Build the Docker image exactly once in the `Docker Test Suite` (`test`) job. After all validation passes (ruff, mypy, pip-audit, Trivy, pytest collection, script unit tests), export the image with `docker save | gzip` and upload it as a GitHub Actions artifact (`playwright-api-automation-image`, `retention-days: 1`). All downstream jobs download and `docker load` the artifact instead of rebuilding.

**Workflow changes:**

- `test` job: add `Save Docker image` and `Upload Docker image artifact` steps after `Publish Script Unit Test Results`. Upload uses `if-no-files-found: error` — a failed save is a hard failure, not a silent skip.
- `api`, `ui`, `ui-cross-browser`, `cloud-grid` jobs: replace `Build Docker image` step with `Download Docker image artifact` + `Load Docker image`. Remove retry loops from `api` and `ui` (no longer building — nothing to retry). Remove stale `# Fresh runner` comments.
- All `docker run` steps remain identical — same commands, same env vars, same volume mounts.
- `notify` job: unchanged.

**Artifact design:**

| Property | Value |
| --- | --- |
| Name | `playwright-api-automation-image` |
| Path | `/tmp/playwright-api-automation.tar.gz` |
| Format | `docker save \| gzip` |
| Retention | 1 day |
| Upload condition | Default (success only) — downstream jobs never run if `test` fails |
| if-no-files-found | `error` |

### Alternatives considered

**Option B — Buildx / GitHub Actions cache:** Reduces layer transfer size but still contacts MCR on each job to validate layer hashes. Does not eliminate rate-limit exposure. Requires `docker/setup-buildx-action` and `docker/build-push-action` — new dependencies not justified by the benefit.

**Option C — GHCR mirror:** Eliminates MCR dependency entirely (mirror the Playwright base image or final project image to GitHub Container Registry). More durable long-term but requires credentials, package visibility settings, manual push steps, and a new registry dependency. Out of scope for a consulting blueprint; deferred to a future slice if MCR rate-limit incidents recur after this PR.

### Why the artifact approach fits this repo

The existing workflow already uses `actions/upload-artifact@v7` and `actions/download-artifact@v8` for JUnit reports, status artifacts, and failure screenshots. An image artifact is the same pattern at larger scale. No new actions, no new registry, no new credentials.

All downstream jobs already `needs: [test]`, so the artifact is guaranteed present whenever a downstream job starts. No fallback rebuild path is needed.

### Why no fallback rebuild

A conditional fallback (`if: failure()`) docker build in downstream jobs would re-introduce MCR exposure and add complexity. Because all downstream jobs `need: [test]`, if the `test` job fails (and thus the artifact was never uploaded), the downstream jobs are skipped by GitHub Actions before they reach the download step. The artifact is always present when downstream jobs run.

### Performance trade-off

| Metric | Before (per job rebuild) | After (artifact reuse) |
| --- | --- | --- |
| MCR pulls per run | Up to 5 | 1 |
| `docker build` executions | 5 | 1 |
| Extra steps per downstream job | 0 | 2 (download + load, ~60–90s each) |
| Estimated net CI time savings | — | ~8–15 min per run |
| Artifact size | — | ~800 MB–1.2 GB compressed |

The upload/download overhead is accepted as the cost of eliminating four redundant MCR pulls.

### Rollback

1. Remove `Save Docker image` and `Upload Docker image artifact` steps from the `test` job.
2. In `api` and `ui` jobs: replace `Download Docker image artifact` + `Load Docker image` with the retry `Build Docker image` block from PR #72.
3. In `ui-cross-browser` and `cloud-grid` jobs: replace `Download Docker image artifact` + `Load Docker image` with `docker build -t playwright-api-automation .` (simple, no retry — advisory jobs).
4. Mark ADR-035 `Superseded`.

None of these changes affect the required release lane, test behavior, or notification behavior.

### Consequences

- MCR is contacted exactly once per CI run (in the `test` job build step with retry).
- Retry loop remains only on the `test` job `Build Docker image` step; removed from `api` and `ui`.
- Downstream jobs run the same image that passed all validation gates — identical binary to what ruff, mypy, Trivy, pip-audit, and pytest verified.
- `docker save | gzip` adds ~60–90s to `test` job wall time.
- `docker load` in each downstream job takes ~60–90s (replacing a ~2–4 min docker build).
- Artifact stored on GitHub Actions storage; `retention-days: 1` prevents accumulation.
- No Dockerfile changes, no new registry dependencies, no new credentials.

### Related docs

- `.github/workflows/ci.yml` — `Save Docker image`, `Upload Docker image artifact` in `test`; `Download Docker image artifact`, `Load Docker image` in `api`, `ui`, `ui-cross-browser`, `cloud-grid`; `timeout-minutes` on `test` job bumped to 40 to accommodate save/upload
- `agentic-qa-workflows/governance/quality_gates.md` — CI job structure table updated; Docker image artifact reuse documented
- `agentic-qa-workflows/README.md` — ADR range updated to `ADR-001–ADR-035`
- `agentic-qa-workflows/governance/architecture_decision_log.md` (ADR-034) — corrected BrowserStack live execution deferral from `ADR-035` to `ADR-036`
