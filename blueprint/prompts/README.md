# Agentic QA Workflow Prompts — Blueprint Guide

## Purpose

This guide documents the agentic QA workflow prompt system as a reusable blueprint asset. The source prompt files remain under `agentic-qa-workflows/prompts/` — this guide links to them rather than copying them to avoid a second source of truth.

## Who This Is For

- A consulting engineer applying this blueprint to a new Python/pytest automation project
- A QA architect evaluating whether to adopt the governance-first agentic workflow
- An engineering lead who wants to understand how the review gates connect before adopting them

## Why Prompts Stay in `agentic-qa-workflows/prompts/`

The prompts in this repo are actively used — they are versioned, referenced in ADRs, and updated as the workflow matures. Copying them into `blueprint/prompts/` would create two sources of truth that diverge within a few PRs. Linking from the blueprint keeps the guide accurate without requiring synchronization.

## The 4-Step Slice Workflow

Every non-trivial implementation slice follows this sequence:

| Step | When | Prompt |
|---|---|---|
| 1. Inspect and plan | Before editing any files | `slice_planning_prompt_template.md` |
| 2. Mode A — Plan review | After plan proposed, before editing | `qa_architect_slice_review_prompt.md` (Mode A section) |
| 3. Implement | After Mode A approval | — (implement per the approved plan) |
| 4. Mode B — Implementation review | After implementation, before committing | `qa_architect_slice_review_prompt.md` (Mode B section) |

**When to skip:** For small, low-risk changes — comment-only, single decorator, minor doc fix, one-line config tweak — the full workflow is optional. Produce a QA summary in chat and proceed. If in doubt, run Mode A.

---

## Prompt Inventory

Source files are in [`../../agentic-qa-workflows/prompts/`](../../agentic-qa-workflows/prompts/). Links below point directly to each source file.

| File | Purpose | When to use |
|---|---|---|
| [`qa_architect_slice_review_prompt.md`](../../agentic-qa-workflows/prompts/qa_architect_slice_review_prompt.md) | Dual-mode reviewer: Mode A (plan review before editing) and Mode B (implementation review before committing). No repo-specific content — use directly in any Python automation project. | Steps 2 and 4 of every non-trivial slice |
| [`slice_planning_prompt_template.md`](../../agentic-qa-workflows/prompts/slice_planning_prompt_template.md) | Structured planning template with `[PLACEHOLDER]` fields. Fill in the branch, goal, files to read, constraints, and validation commands for your slice. | Step 1 — start of any non-trivial slice |
| [`governance_compliance_audit_prompt.md`](../../agentic-qa-workflows/prompts/governance_compliance_audit_prompt.md) | Structured compliance audit across all governance files. Produces an audit report. The file list section references this repo's governance file names — adapt that section for your repo. | When running a formal governance audit |
| [`governance_blueprint_prompt.md`](../../agentic-qa-workflows/prompts/governance_blueprint_prompt.md) | Informal governance enforcement review: naming conventions, markers, POM/API client boundaries, credentials. No adaptation needed. | When reviewing repo governance compliance quickly |
| [`first_run_prompt.md`](../../agentic-qa-workflows/prompts/first_run_prompt.md) | Initial architectural overview: current architecture, top quality risks, improvement recommendations. No adaptation needed. | First session on a new repo, or after a long gap between sessions |

---

## Adapting to a New Repo

1. **Copy the 5 prompt files** to your repo's `agentic-qa-workflows/prompts/` directory.
2. **No modification needed** for `qa_architect_slice_review_prompt.md`, `slice_planning_prompt_template.md`, `governance_blueprint_prompt.md`, and `first_run_prompt.md` — they are repo-agnostic.
3. **Adapt `governance_compliance_audit_prompt.md`**: the file list section references this repo's governance file names. Update those names to match your governance directory.
4. **Create your own governance files** following the structure in `agentic-qa-workflows/governance/`. Do not copy governance content — the ADR log and rule files are specific to this repo's decisions.
5. **Create a `CLAUDE.md`** at your repo root. The review prompts reference `CLAUDE.md` at runtime — this is how repo-specific constraints reach the AI without being hardcoded in the prompts themselves.

---

## What Not to Copy Blindly

| Asset | Why |
|---|---|
| `agentic-qa-workflows/governance/architecture_decision_log.md` | All ADRs record this repo's specific decisions. Start fresh from the ADR format. |
| `agentic-qa-workflows/governance/agentic_workflow_rules.md` | Transferable as-is — no repo-specific content. |
| `agentic-qa-workflows/prompts/README.md` | This is the operational guide for this repo's users, not the blueprint guide. Use this file (`blueprint/prompts/README.md`) as your starting point instead. |

---

## What This Prompt Package Does Not Provide

- An agent framework or automated orchestration layer — prompts are used manually by a human in an AI coding session
- AI autonomy — the four-step workflow is explicitly human-gated at each step
- Governance content ready to use verbatim — the ADR log and rule files require adaptation per repo
- Compliance certification
