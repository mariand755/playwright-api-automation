# Prompt Library

This folder contains reusable prompt templates for AI-assisted QA and architecture work in this repository.

---

## Slice workflow

Every non-trivial implementation slice follows a four-step process. Use the correct prompt at each step:

| Step | When | Prompt file |
|---|---|---|
| 1. Inspect and plan | Before editing any files | `slice_planning_prompt_template.md` |
| 2. Mode A — Plan review | After plan is proposed, before editing | `qa_architect_slice_review_prompt.md` (Mode A section) |
| 3. Implement | After Mode A approval | — (implement per the approved plan) |
| 4. Mode B — Implementation review | After implementation, before committing | `qa_architect_slice_review_prompt.md` (Mode B section) |

**When to skip the four-step workflow:** For small, low-risk changes — comment-only, single decorator, minor doc fix, one-line config tweak — the full workflow is optional. Produce a QA summary in chat and proceed directly to implementation. If in doubt, run Mode A.

---

## Prompt files

| File | Purpose | When to use |
|---|---|---|
| `slice_planning_prompt_template.md` | Fill-in template for Step 1: proposing an implementation plan (v2 — 2026-06-06: expanded Important section with challenge-the-premise instruction) | At the start of any non-trivial slice |
| `qa_architect_slice_review_prompt.md` | QA Architect / Solution Architect dual-mode reviewer (Mode A and Mode B) (v2 — 2026-06-02: added validation integrity, security/secret hygiene, and bounded adjacent-risk scan to both modes; v3 — 2026-06-06: added independence preface shared across both modes) | Step 2 (Mode A) and Step 4 (Mode B) |
| `governance_blueprint_prompt.md` | Governance enforcement review: naming, markers, POM/API client boundaries, credentials | When reviewing repo governance compliance informally |
| `governance_compliance_audit_prompt.md` | Structured compliance audit across all governance files | When running a formal governance audit with an output report |
| `first_run_prompt.md` | Initial architectural overview: current architecture, top quality risks, improvement recommendations | First session on a new repo, or after a long gap between sessions |

---

## How to invoke a prompt

1. Paste the contents of the relevant prompt file into the AI session.
2. Add slice-specific context: branch name, slice goal, files to read, constraints.
3. For `slice_planning_prompt_template.md`: fill in all `[PLACEHOLDER]` values before pasting. Do not leave placeholders unfilled — they produce generic output.
4. For `qa_architect_slice_review_prompt.md`: specify which mode (A or B) at the top of your message and provide the slice context described in the prompt header.

---

## Note for AI-assisted PR creation

GitHub automatically populates `.github/pull_request_template.md` when a PR is opened from the GitHub UI. When creating PRs via `gh pr create` (CLI or AI-assisted), the template is not auto-populated. Pass all template sections explicitly in the `--body` argument to maintain governance consistency.

---

## Maintaining this library

- When a new prompt file is added, add a row to the table above.
- When the four-step slice workflow changes (e.g., a new review mode is added), update the workflow table.
- Prompt files should not be modified mid-slice — use the version that was current when the slice started.
- When a prompt is substantially revised, add a revision note `(vN — YYYY-MM-DD: summary)` to the prompt's row in the table above, and update this README if the usage instructions change.
