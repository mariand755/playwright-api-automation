# Slice Planning Prompt Template

**How to use:** Fill in all `[PLACEHOLDER]` values before pasting this into an AI session. This template is repo-agnostic — it provides the structure only. Repo-specific constraints (execution environment, governance rules, prohibited changes) come from `CLAUDE.md` and the governance files the AI will read at runtime. Do not hardcode repo-specific content here.

Replace `[PLACEHOLDER]` values with the actual slice context. Remove any section that does not apply to this slice. Do not leave unfilled placeholders in the prompt — they produce generic, low-value output.

---

We are on branch: [BRANCH_NAME]

Goal:
[SLICE_GOAL — one sentence describing what this slice accomplishes and why it is needed now]

Important:
Do not edit files yet. First inspect the relevant files and propose the smallest safe implementation plan.

Context:
[CONTEXT_SUMMARY — 2–5 sentences on the current state of the repo, why this slice is needed, and what recent work it builds on. Include any constraints that are not obvious from reading the files.]

Read:
[FILES_TO_READ — list the specific files the AI should read before proposing the plan. Be explicit. Include config files, governance docs, and any files the slice will change.]

Expected outcomes:
[EXPECTED_OUTCOMES — numbered list of what this slice should produce. Include new files, changed files, new behaviors, and CI changes. Be specific enough that the AI can verify completeness.]

Questions to answer before editing:
[QUESTIONS — numbered list of decisions or trade-offs the AI should resolve in the plan output, before proposing any file changes. Include questions about approach, scope, alternative implementations, and deferral candidates.]

Constraints — do not change:
[DO_NOT_CHANGE_LIST — list of files, behaviors, systems, or patterns that must not be modified in this slice. Be explicit. If a file is not listed here but should not be changed, add it.]

Validation required after implementation:
[VALIDATION_COMMANDS — commands or checks that must pass before the slice is considered done. Include Docker commands if the repo uses Docker-first validation, lint/type-check commands, and any manual verification steps.]

Trade-offs and consulting value to address in the plan:
- What alternatives were considered for the proposed approach?
- Why is the proposed approach the best fit for this slice?
- What cost, speed, risk, or maintenance benefit does this create?
- What is intentionally deferred, and why is deferral the right call here?
- How would this decision help a consulting client or QA architecture team?

Output expected:
- Inspection findings (what was read and what was learned)
- Proposed file-by-file plan (what changes, what stays the same, what is new)
- Answers to the questions above
- Risks and open items before editing
- Trade-offs, benefits, and consulting value
- Wait for approval before editing any files
