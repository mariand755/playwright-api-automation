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
- **Separate `notify` CI job (needs: [api, ui])** — rejected for this slice. A separate job would require `actions/upload-artifact` and `actions/download-artifact` (third-party, SHA-pinning needed) to transfer `release-readiness.json` between jobs. The step-in-`API Tests` approach has access to the artifact natively. A separate job also adds a new required-check candidate, triggering the ADR-010 two-step branch protection update process unnecessarily.

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
