# QA Governance Blueprint — Template Guide

## Purpose

This folder contains reusable governance templates for a new Python/pytest QA automation project. Each template is a generic starting point — fill in the placeholders for your project.

These are not copies of any specific repo's governance documents. They represent the governance patterns that have proven useful in practice.

---

## Included Templates

| Template | Use when |
|---|---|
| [`adr_template.md`](adr_template.md) | You need to record a significant architectural or tooling decision |
| [`suite_taxonomy_template.md`](suite_taxonomy_template.md) | You are defining your test marker taxonomy for the first time |

---

## Use Live Source Links for These

Some governance patterns are best read from the reference implementation directly rather than copied from a generic template. The patterns here are closely tied to specific tooling and CI configuration, and a generic copy would diverge from both the original and your implementation.

| Live source file | What to read | Why not extracted here |
|---|---|---|
| [`../agentic-qa-workflows/governance/quality_gates.md`](../agentic-qa-workflows/governance/quality_gates.md) | PR gate, merge gate, release gate philosophy; Docker-first quality check sequence | 17KB, CI-step-specific; adapt Section 1 of blueprint/README.md to your pipeline instead |
| [`../agentic-qa-workflows/governance/notification_wiring.md`](../agentic-qa-workflows/governance/notification_wiring.md) | Step-by-step Slack and SMTP wiring | Job-name-specific; write your own wiring guide from the blueprint/scripts/notify.py adaptation notes |
| [`../agentic-qa-workflows/governance/observability_wiring.md`](../agentic-qa-workflows/governance/observability_wiring.md) | 5-condition activation checklist for live observability providers | The wiring guide itself is designed to be copied; see blueprint/README.md Section 7 |
| [`../agentic-qa-workflows/governance/page_object_api_rules.md`](../agentic-qa-workflows/governance/page_object_api_rules.md) | POM boundaries, API client ownership | Fully transferable as-is; no adaptation needed beyond renaming the example client class |
| [`../agentic-qa-workflows/governance/test_data_env_rules.md`](../agentic-qa-workflows/governance/test_data_env_rules.md) | Test data isolation, environment variable handling, credential storage | Mostly transferable; replace the environment JSON structure with your own |
| [`../agentic-qa-workflows/governance/failure_evidence.md`](../agentic-qa-workflows/governance/failure_evidence.md) | Failure artifact standards, CI gate failure analysis checklist | Directly applicable; adapt artifact paths to your project layout |
| [`../agentic-qa-workflows/governance/security_and_branch_protection.md`](../agentic-qa-workflows/governance/security_and_branch_protection.md) | Branch protection settings, secret scanning guidance, gate classification | Adapt the required status check job names to your CI pipeline |

---

## What Not to Copy

**Do not copy the ADR log.**

`agentic-qa-workflows/governance/architecture_decision_log.md` contains every architectural decision for the reference implementation. Every ADR in it is specific to that repo's technology choices and constraints. Use `adr_template.md` to start fresh.

**Do not copy governance documents verbatim.** The reference implementation's governance docs are written for a specific stack (SauceDemo + Restful Booker, GitHub Actions, Docker, Playwright, Requests). Their principles transfer; their specifics do not.

---

## Deferred Governance Templates

These templates are planned for future extraction slices. Use the live source files as reference in the meantime.

| Template | Source to read now |
|---|---|
| QA standards template (TC-ID system, assertion standards) | [`../agentic-qa-workflows/governance/qa_standards.md`](../agentic-qa-workflows/governance/qa_standards.md) |
| Failure evidence template (CI gate failure checklist) | [`../agentic-qa-workflows/governance/failure_evidence.md`](../agentic-qa-workflows/governance/failure_evidence.md) |
| Dependency update triage template | [`../agentic-qa-workflows/governance/dependency_update_triage.md`](../agentic-qa-workflows/governance/dependency_update_triage.md) |
| Security and branch protection checklist | [`../agentic-qa-workflows/governance/security_and_branch_protection.md`](../agentic-qa-workflows/governance/security_and_branch_protection.md) |

---

## Adoption Sequence

1. Write your first ADR using `adr_template.md` — record your test framework and CI tooling decisions before writing any code.
2. Define your test marker taxonomy using `suite_taxonomy_template.md` — declare your markers in `pytest.ini` before adding any tests.
3. Read the live source governance files listed above. Adapt, do not copy.
4. Follow the blueprint/README.md Replication Sequence for applying the full QA architecture pattern.
