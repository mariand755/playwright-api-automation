# MCP Integration Evaluation

## Purpose

This document evaluates three Model Context Protocol (MCP) integration areas — GitHub, Slack/Gmail, and observability — before implementing reusable Claude Code skills. It defines the evaluation framework, per-use-case assessments, a shared security framework, and activation conditions for any future connection that passes evaluation.

This document does not activate any MCP connection, install any MCP server, provision credentials, or change CI. See [`observability_wiring.md`](observability_wiring.md) for observability activation guidance and [`notification_wiring.md`](notification_wiring.md) for notification activation guidance.

For the architectural decision record, see [ADR-042](architecture_decision_log.md#adr-042-mcp-integration-evaluation--github-slackgmail-and-observability).

---

## Evaluation Framework

Each use case is assessed against five criteria:

| Criterion | Description |
|---|---|
| Current solution | What the existing scripts or CI layer already provide |
| Session-level value | What MCP enables in interactive Claude Code governance sessions |
| Credential scope | Minimum necessary permissions; comparison to the current approach |
| Configuration risk | Where credentials would live; exposure surface vs. GitHub Secrets |
| Verdict | DEFER (value confirmed, activation conditions not yet met) or REJECT (narrower current solution is sufficient; MCP adds risk without proportional gain) |

MCP value in this blueprint is **session-level**, not CI-level. MCP connections improve what Claude Code can do during interactive governance sessions (Mode A/B reviews, compliance audits). They do not improve the CI pipeline itself. No activation in this document changes `.github/workflows/ci.yml`, scripts, or test files.

---

## GitHub MCP

### Current solution

Engineers retrieve PR, workflow, and artifact evidence through GitHub's native UI, approved local tooling, and CI artifacts. This blueprint does not currently prescribe a persistent local GitHub token or a specific CLI evidence workflow.

### Session-level value

A GitHub MCP connection could allow Claude Code to read live PR diffs, workflow run logs, and issue context during Mode A/B reviews — without the engineer manually copying output into the session. Reading live PR and workflow evidence in this way would directly support the governance compliance audit skill planned in Group F.

### Credential scope

A future activation ADR must first enumerate the exact read endpoints required by the chosen MCP server and grant only the corresponding read-only permissions. ADR-042 does not pre-approve a PAT, GitHub App token, or specific permission set.

### Configuration risk

A future GitHub MCP integration may store, cache, or request credentials outside GitHub Actions. Before activation, its ADR must document:

- Credential-storage location and persistence model
- Local secret-store protections
- Rotation process and cadence
- Revocation path
- Exposure risks relative to current CI GitHub Secrets (which are scoped to workflow execution)

A future interactive-session connection must use separately provisioned credentials and must never reuse CI secrets.

### Verdict: DEFER

Value for agentic sessions is confirmed. **Activation conditions:**

1. Define the minimum required read permissions for the chosen MCP server.
2. Document the credential lifecycle: storage location, expiration or rotation cadence, and revocation procedure.
3. Confirm the connection exposes no write-capable repository, workflow, issue, pull-request, secret, or deployment operation.
4. Do not activate until Claude Code skills are ready to consume it (Group F).

---

## Slack/Gmail MCP

### Current solution

The repository implements outbound Slack webhook delivery and outbound SMTP delivery only (`scripts/notify.py`). It does not read email content, mailbox state, or Slack channel history. Dry-run is the default when required environment variables are absent.

### Session-level value — Slack

A Slack MCP connection could allow Claude Code to read recent incident threads or alert messages for context during a release governance session. However, reading Slack conversation or incident context would require an OAuth-based authorization model with the conversation, history, and identity access required by the chosen integration. The exact scope set must be evaluated in a future activation ADR. Write access must not be assumed or granted unless a separately approved use case requires it.

### Session-level value — Gmail

A Gmail MCP connection could allow Claude Code to read email for incident context. This would require an OAuth token with `gmail.readonly` or broader scope — far wider than the outbound-only SMTP path currently used.

### Credential scope

Expanding from webhook → OAuth-based authorization (Slack) or outbound SMTP → OAuth (Gmail) for marginal interactive read capability is a disproportionate scope increase. Future mailbox-read access would require a separate workflow justification, a dedicated read-only authorization model, and a separate activation ADR. Do not characterize the SMTP credential itself as provider-level send-only — that characterization belongs in an activation ADR that has evaluated the provider's actual account controls.

### Configuration risk

A future Slack or Gmail MCP integration may store, cache, or request credentials outside GitHub Actions. Before any activation, its ADR must document the credential-storage location, persistence model, local secret-store protections, rotation process, revocation path, and exposure risks.

### Verdict: REJECT for both notification paths

The current Slack webhook and outbound SMTP are sufficient for one-way notification and have a narrower attack surface. MCP would be appropriate only if incident-context reading becomes a defined workflow requirement with an approved read-authorization model. That is not a current use case in this blueprint, and no activation path is defined.

---

## Observability MCP

### Current solution

`scripts/pull_observability.py` provides stubs for Datadog, Grafana, and PagerDuty. `data/release/observability_snapshot.json` holds a static sample. The release gate evaluates against sample data until ADR-017's five activation conditions are met. ADR-041 defines the canonical schema that any live implementation must satisfy.

### Session-level value

An observability MCP connection could allow Claude Code to query current error rate, latency, and incident counts directly during a release governance session — without waiting for a CI snapshot write. This is complementary to, not a replacement for, the CI-based pull path defined in ADR-017.

### Credential scope

A future live-provider implementation would require provider-specific read-only credentials (Datadog API and app keys, Grafana service account token, or PagerDuty API key). The current repository does not yet call a live provider or consume provider credentials in CI. A future MCP activation must use separately provisioned scoped credentials and must never reuse any provider credentials provisioned for the ADR-017 CI activation slice.

### Configuration risk

A future observability MCP integration may store, cache, or request credentials outside GitHub Actions. Before activation, its ADR must document the credential-storage location, persistence model, local secret-store protections, rotation process, revocation path, and exposure risks. CI GitHub Secrets are scoped to workflow execution; a future interactive-session connection must use separately provisioned read-only credentials.

### Verdict: DEFER

Value for interactive governance sessions is real, but the credential risk differential is material. **Activation conditions:**

1. Complete the ADR-017 live activation slice first — live data must already be flowing via CI.
2. Assess whether a separate read-only service account with tightly scoped credentials can be provisioned for MCP use.
3. Do not reuse CI credentials for local MCP sessions.
4. Document the full credential lifecycle and configuration risk in the activation ADR.

---

## Security and Credential Exposure Framework

These rules apply to any MCP connection that passes future evaluation and proceeds to an activation ADR.

### What may appear in Claude Code session output

- Use-case descriptions and evaluation verdicts
- Canonical metric values (if observability MCP is activated per the conditions in the Observability MCP section above)
- PR titles, branch names, and test counts (if GitHub MCP is activated per the conditions in the GitHub MCP section above)
- Gate decision (`GO`, `NO_GO`, `UNKNOWN`) and reason text

### What must never appear in any MCP session output or configuration

- API key values or partial values
- Grafana instance URLs or dashboard UIDs
- PagerDuty service IDs
- OAuth token values
- Raw provider API response bodies
- `str(exc)` or `exc.args` content from provider or integration exceptions — only `type(exc).__name__` is permitted

### Least-privilege principles

- Scope each MCP connection to read-only where the use case permits
- Use short-lived or rotatable credentials; prefer credential types that support expiration
- Never co-opt CI GitHub Secrets for local MCP sessions — provision separate, scoped credentials
- Document the minimum required scope for each connection in its activation ADR

### Data minimization

MCP-returned content must be limited to the minimum fields needed for the named review question. Summaries may contain approved aggregate status, test counts, branch names, and contract-safe metric values when their source classification permits it.

Do not persist raw PR diffs, workflow logs, issue comments, provider responses, incident narratives, or email/Slack content in repository files, PR descriptions, CI artifacts, or MCP configuration.

### Human confirmation

A reviewer must explicitly request any retrieval of live operational data, workflow logs, or communication context. Broad repository, mailbox, channel, or metric-history searches are out of scope by default.

---

## Summary Recommendations

| Use case | Verdict | Activation condition summary |
|---|---|---|
| GitHub PR and evidence retrieval | DEFER | Define minimum read permissions and full credential lifecycle; no write operations; activate when Claude Code skills are ready (Group F) |
| Slack notification / incident context | REJECT | Current webhook is sufficient and narrower; no activation path defined |
| Gmail/SMTP notification / inbox read | REJECT | Current outbound SMTP is sufficient and narrower; no activation path defined |
| Observability signal retrieval | DEFER | Complete ADR-017 live activation first; provision a separate read-only service account; do not reuse CI credentials |

---

## Non-Goals

This document does not:

- Install or configure any MCP server
- Provision credentials or change GitHub Secrets or repository variables
- Change `scripts/pull_observability.py`, `scripts/notify.py`, `scripts/release_gate.py`, or `.github/workflows/ci.yml`
- Select a live observability provider or define an activation timeline
- Implement Claude Code skills — that follows this evaluation in Group F
