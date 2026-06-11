# Dependency Update Triage Workflow

## Purpose

This document defines how dependency update pull requests — primarily those created by Dependabot — are triaged, reviewed, and merged in this repo. It applies to both Python package updates (`pip` ecosystem) and GitHub Actions updates (`github-actions` ecosystem).

The goal is a repeatable process that prevents dependency PRs from piling up while ensuring major version changes receive appropriate human review before reaching `main`.

---

## Why This Matters

### GitHub Actions updates are CI infrastructure changes

When Dependabot proposes an update to a GitHub Action (e.g., `actions/checkout`, `github/codeql-action`, `dorny/test-reporter`), CI passing on that PR confirms that the existing test suite runs with the updated action. It does not confirm:

- That the action's output variable names are unchanged
- That the action's permission model is unchanged
- That the action's behavior in edge cases not exercised by the current workflow is unchanged
- That the action is compatible with other actions in the same job (e.g., `actions/upload-artifact` and `actions/download-artifact` interact in the same pipeline)

GitHub Actions are the CI infrastructure, not just code dependencies. A broken action update does not break the product under test — it breaks the ability to detect that the product is broken.

### Why PRs accumulate

Without a triage cadence, Dependabot PRs pile up. Each new update supersedes prior ones, creating multi-major version jumps that require more review than a single-version change would have. The five open GitHub Actions PRs in this repo (June 2026) were caused by this pattern: no triage workflow → no merge cadence → versions queued for 7+ days → newer updates arrived on top.

### What CI passing guarantees

CI passing on a Dependabot PR means:
- The existing test suite still passes with the updated action or package
- No known CVEs are introduced in Python packages (pip-audit gate)
- No new HIGH/CRITICAL CVEs are introduced in the Docker image (Trivy gate)
- CodeQL finds no new Python security issues

CI passing does not mean the action behaves identically in all circumstances, or that a multi-major version jump contains no behavioral changes relevant to this workflow.

---

## Three-Checker Triage Model

All dependency updates pass through three checkers before merging:

**Checker 1 — Dependabot (automated)**

Creates update PRs on the weekly Monday schedule. Maintains SHA pins for third-party actions (`dorny`, `aquasecurity`). Groups `actions/upload-artifact` and `actions/download-artifact` into a single PR. Opens no more than 3 GitHub Actions PRs at a time (enforced by `open-pull-requests-limit`).

**Checker 2 — CI / security gates (automated)**

All four required checks must pass before a Dependabot PR is eligible to merge:

- Docker Test Suite (Docker build, Ruff, mypy, pip-audit, Trivy, script unit tests)
- API Tests
- UI Tests
- Analyze Python (CodeQL)

These are the same required status checks enforced by branch protection for all PRs. A Dependabot PR that fails any required check is not eligible to merge.

**Checker 3 — Human review (QA Architect / repo owner)**

Required before merging any GitHub Actions major version update. For Python pip patch and minor updates, human review is encouraged but not required if CI passes and no changelog flags behavioral changes. See [Reviewer Checklist](#reviewer-checklist).

---

## Risk Tiers

### Tier 1 — Low risk

**Criteria:** First-party GitHub-maintained action (`actions/*`, `github/*`) with a single major version jump, OR a third-party action used in an advisory-only (non-blocking) role.

**Review required:** Skim release notes for the version range. Check for breaking changes, new required inputs, renamed outputs, permission model changes.

**Examples in this repo:** `github/codeql-action` v3→v4 (first-party, one major version, advisory role); `dorny/test-reporter` v1.9.1→v3.0.0 (third-party SHA-pinned, used with `fail-on-error: false` — advisory only)

### Tier 2 — Medium risk

**Criteria:** Multiple major version jumps, OR a first-party action that touches a required CI gate, OR a third-party action with pipeline impact.

**Review required:** Full changelog review for each major version in the jump range. Check for breaking changes, new required inputs, changed default behavior, removed features.

**Examples in this repo:** `actions/checkout` v4→v6 (two major versions, all 4 CI jobs and `codeql.yml`); `actions/upload-artifact` v4→v7 (three major versions)

### Tier 3 — Coordinated update required

**Criteria:** Two or more actions that interact in the same pipeline and must be updated together.

**Review required:** Same as Tier 2 for each action. Both changelogs must be reviewed before merging either. Merge together in the same review window: merge one, immediately merge the other.

**Example in this repo:** `actions/upload-artifact` and `actions/download-artifact` — the Notify job downloads what the API Tests job uploads (`artifacts/release-readiness.json`). These must be reviewed and merged as a unit.

---

## Action Trust Levels and SHA Pinning

This repo enforces SHA pinning for third-party actions:

| Publisher | Trust level | Pinning model |
|---|---|---|
| `actions/*` (GitHub first-party) | Owned and maintained by GitHub | Major version tag (e.g., `@v4`) — pragmatic tradeoff; SHA pinning is OSSF best practice but not yet enforced for first-party |
| `github/*` (GitHub first-party) | Same | Same — documented in `.github/workflows/codeql.yml` comment |
| `dorny/*` (third-party) | Community-maintained | SHA pin required — enforced ✓ |
| `aquasecurity/*` (third-party) | Community-maintained | SHA pin required — enforced ✓ |

Dependabot maintains SHA pins automatically when a new version is available. When a dorny or aquasecurity PR arrives, verify the proposed SHA against the release tag on the action's GitHub releases page.

Future improvement: move `actions/*` and `github/*` to SHA pinning per OSSF/SLSA supply chain guidance. Track as a future ADR when the overhead of pinning 10+ occurrences across two workflow files is justified by the risk posture.

---

## Handling GitHub Actions Updates

Before merging any GitHub Actions Dependabot PR:

1. Identify the risk tier (Tier 1, 2, or 3 — see above).
2. Read the release notes for each major version in the jump range. The GitHub releases page for the action is the canonical source.
3. Check whether any interacting actions need to be coordinated (see [Coordinated Updates](#coordinated-updates-artifact-actions)).
4. Confirm all four CI required checks passed on the Dependabot PR.
5. Work through the [Reviewer Checklist](#reviewer-checklist).

**No auto-merge for GitHub Actions major version updates.** See [Auto-Merge Policy](#auto-merge-policy).

---

## Handling Python Package Updates

Python dependency updates (`pip` ecosystem) are lower-risk for this repo:

- `pip-audit` in Docker Test Suite catches known CVEs before merge
- Ruff, mypy, and the full pytest suite validate compatibility with the current codebase
- Python API changes (vs. behavioral action changes) are surfaced by static analysis and tests

**Patch and minor updates:** Merge when CI passes. Human changelog review not required.

**Major updates:** Apply the same Tier 2 review as GitHub Actions major version bumps: read the changelog for each major version in the jump range, check for breaking API changes that the current test suite may not catch.

**playwright:** Intentionally ignored by Dependabot. The playwright version is coupled to the Docker base image tag. Updates require a coordinated base image + requirements change. See [ADR-007](architecture_decision_log.md#adr-007-dependabot-with-playwright-version-ignored) and the ignore rule in `.github/dependabot.yml`.

---

## Handling Security Updates

When Dependabot creates a PR labeled `security`:

- Review within 24 hours — do not wait for the weekly triage cadence.
- The security fix takes priority over the coordinated-update rule: a security patch for `actions/upload-artifact` merges without waiting for `actions/download-artifact` if the vulnerability is specific to upload-artifact.
- If the security fix also involves a major version bump, changelog review is still required, but on an expedited timeline.
- For Python packages: pip-audit flags known CVEs during CI runs on every PR; a security-labeled Dependabot PR is the fix.

The `github-actions` `open-pull-requests-limit: 3` controls routine version update PR volume only. Dependabot security update PRs bypass this limit and should be triaged independently with the 24-hour security-update SLA regardless of how many version update PRs are currently open.

---

## Coordinated Updates: artifact-actions

`actions/upload-artifact` and `actions/download-artifact` interact within the same pipeline: the `API Tests` job uploads `artifacts/release-readiness.json`; the `Notify` job downloads it. Incompatible versions between upload and download can produce silent failures in the Notify job.

**Configuration:** `.github/dependabot.yml` groups these two actions as `artifact-actions`. Dependabot creates a single PR covering both, eliminating the coordination problem for future updates.

**For PRs that arrived before the group was configured (PR #14 and PR #40, June 2026):** Review both changelogs together and merge in the same review window. Do not merge one without the other. This grouping applies to future Dependabot PRs only — existing separate PRs will not be automatically closed or regrouped when this configuration merges to `main`.

**Note:** `actions/download-artifact` uses `continue-on-error: true` in the Notify job, so a version mismatch will not fail CI — it will fail silently. Explicit coordination is more important, not less, because CI will not catch the breakage.

---

## Auto-Merge Policy

**GitHub Actions updates: no auto-merge.** The reasons are structural:

1. GitHub Actions are CI infrastructure. A silently broken action disables the ability to detect regressions in the product under test.
2. Multi-major version jumps (common when PRs accumulate) require human changelog review that cannot be automated.
3. The upload-artifact + download-artifact interaction requires coordinated merging that auto-merge cannot enforce.

**Python pip patch/minor updates:** Auto-merge is a reasonable future option when CI (including pip-audit) is required to pass. Requires a separate ADR decision and configuration. Not enabled in this repo.

---

## Reviewer Checklist

Before merging any GitHub Actions Dependabot PR, confirm:

- [ ] All four CI required checks passed on this PR (Docker Test Suite, API Tests, UI Tests, Analyze Python)
- [ ] Risk tier identified (Tier 1, 2, or 3)
- [ ] Release notes read for each major version in the jump range
- [ ] No breaking changes identified that affect this repo's workflow inputs, outputs, or permissions
- [ ] If dorny or aquasecurity (SHA-pinned): proposed SHA verified against the release tag
- [ ] If Tier 3 (coordinated): both interacting actions reviewed and being merged in the same window
- [ ] No permission model changes noted in changelog
- [ ] No renamed output variables that `ci.yml` depends on

If any item cannot be confirmed: defer the PR (add a `needs-changelog-review` label and note the blocker in the PR comment).

---

## Cadence Expectations

| Update type | Review target |
|---|---|
| GitHub Actions, any tier | Within 7 days of PR creation |
| Python pip patch/minor | Within 14 days |
| Python pip major | Within 7 days (same as GitHub Actions) |
| Coordinated updates (artifact-actions) | Within 14 days — allows time to review both changelogs |
| Security-labeled PRs | Within 24 hours |

The `open-pull-requests-limit: 3` on the `github-actions` ecosystem prevents more than 3 GitHub Actions update PRs from queuing simultaneously. When the limit is reached, Dependabot does not open new PRs until existing ones are merged or closed.

---

## Triage Labels

These labels are applied manually during triage — no automation required:

| Label | When to apply |
|---|---|
| `safe-to-merge` | Reviewer checklist completed; PR is ready to merge |
| `needs-changelog-review` | Multi-major version jump identified; changelog not yet reviewed |
| `coordinated-update` | Two interacting PRs must move together (pre-group PRs only) |
| `deferred` | Active blocker prevents merge; noted in PR comment |

---

## When to Defer

Defer a Dependabot PR when:
- A changelog review reveals breaking changes that require a `ci.yml` update before the action can be merged safely
- A coordinated partner PR has not yet arrived (wait for both before reviewing either)
- A security-labeled PR for a higher-priority dependency is blocking attention

Do not defer indefinitely. A deferred PR causes the version gap to grow, increasing the review burden when it is eventually addressed.

---

## When to Close / Supersede

Close a Dependabot PR when:
- Dependabot has opened a newer PR for the same action at a higher version (Dependabot typically closes older PRs automatically when the group produces a new one)
- A manual combined PR has been created to handle a coordinated update that arrived as two separate PRs

---

## Out of Scope

This workflow does not cover:
- Docker base image updates (handled as a coordinated slice per ADR-007 playwright activation conditions)
- Observability provider credential rotation (see [`observability_wiring.md`](observability_wiring.md))
- GitHub repository settings or branch protection changes (see [`security_and_branch_protection.md`](security_and_branch_protection.md))
- Adding new dependencies to `requirements.txt` (covered by PR review, not dependency update triage)

---

## Relationship to Quality Gates and Branch Protection

The four required CI status checks apply equally to Dependabot PRs and human-authored PRs. A Dependabot PR must pass all required checks before merging, regardless of its risk tier.

`dorny/test-reporter` annotations (Script Unit Test Results, API Test Results, UI Test Results) are advisory (`fail-on-error: false`) — they do not block merge. A failure in test-reporter itself would appear as missing annotations, not a CI block. This is relevant when reviewing a dorny PR: CI can pass even if the reporter is temporarily broken by a version change.

CodeQL findings are advisory (Security → Code scanning alerts). A CodeQL finding on a Dependabot PR indicates a new security pattern introduced by the package change and warrants investigation before merging.

For the full required checks configuration and post-merge update instructions, see [`security_and_branch_protection.md`](security_and_branch_protection.md).

---

## Relationship to ADR-007

[ADR-007](architecture_decision_log.md#adr-007-dependabot-with-playwright-version-ignored) documents the decision to ignore playwright in Dependabot because the playwright version is coupled to the Docker base image tag. The ignore rule in `.github/dependabot.yml` is preserved unchanged by this workflow:

```yaml
ignore:
  - dependency-name: playwright
    versions: ["*"]
    # playwright version is coupled to the Docker base image tag;
    # updates require a coordinated base image + requirements change
```

The grouping, cadence, and open-PR-limit changes introduced alongside this doc do not affect the playwright ignore rule or the ADR-007 activation condition ("Remove the ignore rule once playwright is no longer coupled to a base image that pins the version").

**OS-layer CVEs are handled separately.** The Playwright ignore rule applies to Python package version tracking only. CVEs in OS packages inside the Docker base image — for example Ubuntu packages such as OpenSSL/libssl, curl, or system libraries — are remediated by `apt-get upgrade -y --no-install-recommends` during `docker build` when patched packages are available from the Ubuntu package repository. This is independent of Dependabot and independent of the Playwright package version pin. Playwright, browser, and Node CVEs embedded in the base image still require a coordinated base image tag and Playwright package update. See ADR-025 and the Docker base image lifecycle section in `security_and_branch_protection.md`.

---

## References

- [`.github/dependabot.yml`](../../.github/dependabot.yml) — Dependabot configuration; `artifact-actions` group; `open-pull-requests-limit`; playwright ignore rule
- [`security_and_branch_protection.md`](security_and_branch_protection.md) — required status checks; Dependabot update visibility
- [`quality_gates.md`](quality_gates.md) — CI job structure; GitHub-native security checks section
- [`architecture_decision_log.md` — ADR-007](architecture_decision_log.md#adr-007-dependabot-with-playwright-version-ignored)
- [`architecture_decision_log.md` — ADR-023](architecture_decision_log.md#adr-023-dependency-update-triage-workflow)
