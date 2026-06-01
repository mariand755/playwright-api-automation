# Security and Branch Protection

This document covers GitHub repository administrator settings and security policies. These are not CI workflow configurations — they must be applied manually in GitHub → Settings → Branches and Settings → Code security and analysis.

---

## Recommended branch protection settings for `main`

Navigate to: **GitHub → Settings → Branches → Add branch protection rule → Branch name pattern: `main`**

### Minimum recommended settings

| Setting | Recommended value |
|---|---|
| Require a pull request before merging | Enabled |
| Require status checks to pass before merging | Enabled |
| Require branches to be up to date before merging | Enabled |
| Dismiss stale pull request approvals when new commits are pushed | Enabled |
| Do not allow bypassing the above settings | Enabled |

### Required status checks

Add exactly two required checks by job name:

```
Docker Test Suite
Analyze Python
```

**Important:** GitHub branch protection operates at the **job level**, not the step level. Individual CI steps — Check formatting, Lint, Python dependency scan, Container image scan, Verify test collection, Run full test suite, Run release readiness gate — are internal steps within the `Docker Test Suite` job. They are not separately addressable as required status checks. Requiring `Docker Test Suite` to pass requires all internal steps to pass first.

#### What `Docker Test Suite` covers

The `Docker Test Suite` job (`.github/workflows/ci.yml`) runs the following gates in order. All nine must pass for the job to succeed:

1. Docker build
2. Ruff format check
3. Ruff lint check
4. mypy type check (utils/, pages/, scripts/)
5. Python dependency vulnerability scan (pip-audit)
6. Container image vulnerability scan (Trivy — fixable HIGH/CRITICAL only)
7. pytest collection check
8. Full test suite
9. Release readiness gate

#### What `Analyze Python` covers

The `Analyze Python` job (`.github/workflows/codeql.yml`) runs CodeQL static security analysis on the Python codebase.

**Note:** Requiring `Analyze Python` ensures the CodeQL analysis has run and completed successfully — not that zero findings exist. Findings are published to the GitHub Security tab (Security → Code scanning alerts) and are advisory by default. In the rare event of a CodeQL infrastructure failure (workflow error, not a finding), this required check would block merges until the failure is resolved.

---

## Gate classification

| Check | Type | Blocking | Surface | Trigger |
|---|---|---|---|---|
| Ruff format | Hard CI gate | Yes — fails `Docker Test Suite` | CI step | PR / push |
| Ruff lint | Hard CI gate | Yes — fails `Docker Test Suite` | CI step | PR / push |
| pip-audit | Hard CI gate | Yes — fails `Docker Test Suite` | CI step | PR / push |
| Trivy (fixable HIGH/CRITICAL) | Hard CI gate | Yes — fails `Docker Test Suite` | CI step | PR / push |
| pytest collection | Hard CI gate | Yes — fails `Docker Test Suite` | CI step | PR / push |
| Full test suite | Hard CI gate | Yes — fails `Docker Test Suite` | CI step | PR / push |
| Release readiness gate | Hard CI gate | Yes — fails `Docker Test Suite` | CI step | PR / push |
| CodeQL findings | Advisory | No — Security tab | GitHub Security tab | PR / push / weekly |
| Dependabot updates | Update visibility | No — creates PRs | Dependabot PRs | Weekly |
| GitHub secret scanning | Platform protection | Yes (push protection enabled) | Git push rejection | Push |

---

## Secret scanning guidance

### Enabling GitHub secret scanning and push protection

Navigate to: **GitHub → Settings → Code security and analysis**

- **Secret scanning:** Enable. GitHub scans all commits and alerts on detected credentials matching known secret patterns (API keys, tokens, and service credentials).
- **Push protection:** Enable. GitHub rejects pushes containing detected secrets before they reach the remote, independent of CI.

Both settings are free for public repositories. For private repositories they require GitHub Advanced Security.

### Committed credential policy

Real secrets — API keys, tokens, service credentials, passwords for real systems — must never be committed to this repository.

Real secrets must be stored in GitHub Secrets and injected as environment variables in CI workflows.

If a real secret is accidentally committed: rotate it immediately, then remove it from git history. Push protection would have blocked the original push if it was enabled.

### Demo credential classification

This repo tests against public demo services. The following credentials are publicly documented on their respective service websites and are not secrets:

| Service | Username | Password | Classification |
|---|---|---|---|
| Restful Booker | `admin` | `password123` | Public demo credential — safe to commit |
| SauceDemo | `standard_user` | `secret_sauce` | Public demo credential — safe to commit |
| SauceDemo | `locked_out_user` | `secret_sauce` | Public demo credential — safe to commit |

These credentials are stored in `data/test_users.json` and loaded via fixtures. They do not trigger GitHub secret scanning because they are not registered secret patterns.

---

## Future optional: gitleaks

gitleaks is an open-source secret scanning tool that can be added as a CI step or pre-commit hook to scan git history and staged changes for secrets matching configurable patterns.

**What it adds over GitHub native secret scanning:**
- Runs locally before push in pre-commit mode
- Supports configurable custom patterns for project-specific secret formats
- Can scan full git history, not just new pushes

**Condition for implementation:** Add gitleaks when this repo transitions from public demo credentials to real environment credentials, or when a dedicated slice explicitly approves adding it. Do not add gitleaks until that slice is approved.
