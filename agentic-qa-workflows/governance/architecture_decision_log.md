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
