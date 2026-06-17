# Jenkins CI/CD Adapter Wiring Guide

This guide covers how to configure, extend, and adapt the Jenkins reference pipeline for enterprise or client environments. For the authoritative CI implementation, see `.github/workflows/ci.yml`.

---

## Overview

`ci/jenkins/Jenkinsfile` is a reference adapter that runs the same Docker-first required lane as the GitHub Actions workflow — without modifying tests, the release gate, `notify.py`, the Dockerfile, or any GitHub Actions configuration.

**Use Jenkins when:**
- The client or enterprise environment standardizes on Jenkins and cannot adopt GitHub Actions.
- A QA blueprint demonstration needs to run outside of GitHub.
- You are adapting this repo to a client's existing Jenkins infrastructure.

**Do not use Jenkins when:**
- GitHub Actions is available and working — it is the primary CI for this repo.
- You need live BrowserStack/Sauce Labs cloud-grid execution immediately (documented below as a follow-on extension).

---

## Pipeline Location and Discovery

The Jenkinsfile lives at `ci/jenkins/Jenkinsfile` rather than the repository root to signal that GitHub Actions remains primary CI and to avoid auto-detection ambiguity.

**To use it in Jenkins:**
- Create a **Multibranch Pipeline** or **Pipeline from SCM** project.
- Set **Script Path** to `ci/jenkins/Jenkinsfile`.

Teams that prefer a root `Jenkinsfile` can copy or symlink it there without any content change.

---

## Required Jenkins Capabilities

| Capability | Notes |
| --- | --- |
| Jenkins Pipeline support | Standard in all modern Jenkins installations |
| Docker available on the build agent | The pipeline builds and runs a Docker image; the agent must have Docker installed and the Jenkins user must be in the `docker` group |
| JUnit test result publishing | Standard Jenkins capability (JUnit plugin); used by `junit` steps throughout the pipeline |
| Artifact archival | Built-in `archiveArtifacts` step; no additional plugin needed |
| Credentials Binding (optional) | Required only for live notification delivery or cloud-grid execution |

No additional plugins are required for the required lane (quality gates, script/API/UI tests, release gate, dry-run notification).

---

## Key Architecture Difference: Docker Image Reuse

| | GitHub Actions | Jenkins (this adapter) |
| --- | --- | --- |
| Runner isolation | Each job runs on a separate, isolated runner | All stages share one agent workspace and Docker daemon |
| Image sharing | PR #73: build → `docker save` → upload artifact → download + `docker load` in each job | Build once in `Build Docker Image` stage; image persists on local Docker daemon for the entire pipeline run |
| Save/load step needed? | Yes | No |

This is a simplification, not a limitation. The Jenkins adapter produces equivalent test execution without any image transfer overhead.

---

## GitHub Actions vs Jenkins Stage Mapping

| GitHub Actions Job | Jenkins Stage | Notes |
| --- | --- | --- |
| `test` (Docker build + quality checks + script tests) | `Build Docker Image` + `Static Quality Gates` + `Script Unit Tests` | Split for clarity; behavior identical |
| `api` (API tests + release gate) | `API Tests` (inside `Behavioral Tests`) + `Release Gate` | Release gate is its own stage |
| `ui` (UI tests) | `UI Tests` (inside `Behavioral Tests`) | Same pytest command |
| `ui-cross-browser` (advisory) | Not in this adapter | Deferred; see cloud-grid section below |
| `cloud-grid` (advisory) | Not in this adapter | Deferred; see cloud-grid section below |
| `notify` | `post { always { ... } }` | Dry-run by default; see notification section |
| Deploy | `Client Deploy Hook (Placeholder)` | Manual approval gate; no real deployment |

---

## Artifact Filenames

Artifact filenames match `ci.yml` exactly so the release gate and notify scripts work without modification:

| Output | Path |
| --- | --- |
| Script unit test JUnit | `artifacts/scripts-report.xml` |
| API test JUnit | `artifacts/api-report.xml` |
| UI test JUnit | `artifacts/ui-report.xml` |
| Release readiness (JSON) | `artifacts/release-readiness.json` |
| Release readiness (Markdown) | `artifacts/release-readiness.md` |
| UI failure screenshots | `artifacts/failures/<sanitized-nodeid>.png` |
| UI failure HTML dumps | `artifacts/failures/<sanitized-nodeid>.html` |

---

## JUnit Publishing

Jenkins publishes JUnit reports via the standard `junit` step (JUnit plugin), which is included in all modern Jenkins installations. Each test stage publishes its own report in a `post { always { ... } }` block so results appear in Jenkins even when tests fail.

The `post { always { ... } }` at the pipeline level also collects all `artifacts/*-report.xml` files as a safety net.

**GitHub Actions equivalent:** `dorny/test-reporter` (not available in Jenkins; `junit` step is the standard alternative).

---

## Release Gate Behavior

The release gate runs `scripts/release_gate.py artifacts/api-report.xml` after both API and UI tests complete.

| Condition | Behavior |
| --- | --- |
| API tests pass; `api-report.xml` present | Gate evaluates; writes GO or NO_GO artifact |
| API tests fail; `api-report.xml` still written by pytest | Gate evaluates from partial results; likely NO_GO |
| API tests fail; `api-report.xml` missing (Docker crash / collection error) | Gate writes an error artifact and exits 1; Jenkins build FAILS |
| Release gate exits 1 (NO_GO or error) | Jenkins build is marked FAILED; `post { always { ... } }` still archives all artifacts |

The Jenkins pipeline does not implement the smoke/skipped gate path (`--skipped <scope>`) from GitHub Actions. To add branch-conditional smoke behavior, check `env.BRANCH_NAME` in a `script {}` block and pass `--skipped smoke` for non-main branches.

---

## Credential Mapping

No credentials are required for the required lane. The pipeline runs entirely with `NOTIFY_DRY_RUN=true` and no cloud provider.

For live notification and cloud-grid execution, map GitHub Actions secrets to Jenkins credentials:

| GitHub Actions Secret / Variable | Jenkins Credential Type | Suggested Credential ID |
| --- | --- | --- |
| `SLACK_WEBHOOK_URL` | Secret text | `slack-webhook-url` |
| `SMTP_HOST` | String parameter / env var | — |
| `SMTP_PORT` | String parameter / env var | — |
| `SMTP_USER` | Username with password | `smtp-credentials` |
| `SMTP_PASSWORD` | (use username/password above) | — |
| `EMAIL_FROM` | String parameter / env var | — |
| `NOTIFY_RECIPIENTS` | String parameter / env var | — |
| `SAUCE_USERNAME` | Username with password | `sauce-credentials` |
| `SAUCE_ACCESS_KEY` | (use username/password above) | — |
| `BROWSERSTACK_USERNAME` | Username with password | `browserstack-credentials` |
| `BROWSERSTACK_ACCESS_KEY` | (use username/password above) | — |

**Binding pattern** (add inside the relevant `sh` step):

```groovy
withCredentials([string(credentialsId: 'slack-webhook-url', variable: 'SLACK_WEBHOOK_URL')]) {
    sh '''
        docker run --rm \
          -v "$ARTIFACTS_DIR:/app/artifacts" \
          -e SLACK_WEBHOOK_URL="$SLACK_WEBHOOK_URL" \
          -e NOTIFY_DRY_RUN=false \
          "$IMAGE_NAME" \
          python scripts/notify.py
    '''
}
```

Never hardcode credential values in the Jenkinsfile.

---

## Notification Integration

`scripts/notify.py` can be called from Jenkins via a Docker exec in `post { always { ... } }`. The pipeline sets `NOTIFY_DRY_RUN=true` by default — no credentials required, no Slack or SMTP calls are made.

**Important limitation:** `notify.py` reads per-job status env vars set by the GitHub Actions `notify` job (`JOBS_STATUS_TEST`, `JOBS_STATUS_API`, `JOBS_STATUS_UI`, `JOBS_STATUS_UI_CROSS_BROWSER`, `JOBS_STATUS_CLOUD_GRID`). These are populated from GitHub Actions job outcomes and are not present in a Jenkins run. In dry-run mode this is safe — no outbound call is made and there is no visible gap. For live delivery, the notification message will be missing individual job pass/fail context unless you map Jenkins stage results to these variables before calling `notify.py`.

**Jenkins-to-notify.py env var mapping pattern:**

```groovy
// Capture stage results via currentBuild.result or per-stage result tracking,
// then expose as JOBS_STATUS_* vars before calling notify.py.
// Example (simplified — adapt to match your stage result tracking):
sh """
    docker run --rm \
      -v "$ARTIFACTS_DIR:/app/artifacts" \
      -e JOBS_STATUS_TEST=success \
      -e JOBS_STATUS_API="${apiTestsResult}" \
      -e JOBS_STATUS_UI="${uiTestsResult}" \
      -e NOTIFY_DRY_RUN=false \
      "$IMAGE_NAME" \
      python scripts/notify.py
"""
```

Per-stage result tracking in Jenkins requires a `script {}` block and Groovy variables — see [Jenkins Pipeline documentation](https://www.jenkins.io/doc/book/pipeline/getting-started/) for patterns.

**To enable live Slack delivery (dry-run → live):**
1. Add a Jenkins secret text credential with the Slack webhook URL.
2. Wrap the notify `sh` step in `withCredentials([string(...)])` as shown in the Credential Mapping section.
3. Add the `JOBS_STATUS_*` env var mapping above.
4. Set `NOTIFY_DRY_RUN=false`.

**To enable live SMTP email delivery:**
Follow the same steps as `notification_wiring.md` — the activation requirements are identical; only the binding mechanism differs (Jenkins `withCredentials` vs GitHub Actions `secrets`).

---

## Advisory Cloud-Grid Extension (Sauce Labs / BrowserStack)

Cloud-grid stages are intentionally deferred from the Jenkins reference adapter. They can be added as additional parallel branches in a `stage('Cloud Grid')` block using the same provider env vars and credentials documented in `notification_wiring.md` and ADR-036/037.

**Stub pattern** (adapt with real credentials binding):

```groovy
stage('Cloud Grid (Advisory)') {
    when { anyOf { branch 'main'; triggeredBy 'TimerTrigger' } }
    steps {
        catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
            withCredentials([
                usernamePassword(credentialsId: 'browserstack-credentials',
                                 usernameVariable: 'BROWSERSTACK_USERNAME',
                                 passwordVariable: 'BROWSERSTACK_ACCESS_KEY')
            ]) {
                sh '''
                    docker run --rm \
                      -v "$ARTIFACTS_DIR:/app/artifacts" \
                      -e CLOUD_GRID_PROVIDER=browserstack \
                      -e BROWSERSTACK_USERNAME="$BROWSERSTACK_USERNAME" \
                      -e BROWSERSTACK_ACCESS_KEY="$BROWSERSTACK_ACCESS_KEY" \
                      "$IMAGE_NAME" \
                      python scripts/cloud_grid_preflight.py
                '''
            }
        }
    }
}
```

Cloud-grid should remain advisory (`catchError` preserving `buildResult: 'SUCCESS'`) and must never be added to branch protection.

---

## Client Deploy Hook Placeholder

The `Client Deploy Hook (Placeholder)` stage fires only on the `main` branch (requires Multibranch Pipeline for `BRANCH_NAME` to be set). It pauses the pipeline with a Jenkins `input` step until an operator approves, then echoes a placeholder message.

**To wire a real deployment:**
Replace the `echo` line with the actual deployment command (Ansible, `kubectl apply`, a remote SSH call, or a downstream Jenkins job trigger via `build job: '...'`). Keep the `input` gate — it ensures a human reviews the release gate artifact before deploying.

**Note:** The `input` step occupies a Jenkins executor thread while waiting. For long approval windows, consider using the [Milestone and Lock step](https://plugins.jenkins.io/pipeline-milestone-step/) pattern or a downstream parameterized build.

---

## What Is Intentionally Not Implemented

| Item | Reason |
| --- | --- |
| Real deployment | Out of scope — this repo does not deploy an application |
| Jenkins server setup | Operator responsibility; standard Jenkins administration |
| Trivy container scan | GitHub-Actions-specific action; Jenkins equivalent: `sh 'trivy image "$IMAGE_NAME"'` in a dedicated stage |
| CodeQL analysis | GitHub Advanced Security feature; Jenkins equivalent: SonarQube or a Semgrep stage |
| Cloud-grid execution in Jenkinsfile | Deferred; documented above as an extension path |
| Smoke/branch-conditional gate path | Not implemented; documented in release gate section as an adaptation note |
| `BRANCH_NAME`-based test-scope branching | Not implemented; add a `script {}` block with `env.BRANCH_NAME` check if needed |

---

## Rollback / Adaptation Notes

To remove the Jenkins adapter entirely:
1. Delete `ci/jenkins/Jenkinsfile` and the `ci/jenkins/` directory.
2. Delete `agentic-qa-workflows/governance/jenkins_wiring.md`.
3. Revert the one-line additions to `README.md`, `agentic-qa-workflows/README.md`, `agentic-qa-workflows/governance/README.md`, and ADR-037/ADR-038.
4. No test, gate, notification, or GitHub Actions behavior is affected.

To adapt for a client environment:
- Change `IMAGE_NAME` in the `environment {}` block to match the client's image naming convention.
- Add credential bindings for whichever notification and cloud-grid providers the client uses.
- Move the Jenkinsfile to the repository root if the client's Jenkins configuration expects it there.
- Add the smoke/branch-conditional gate path if the client has a PR build / main build distinction.
