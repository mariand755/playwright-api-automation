# Agentic Workflow Rules

These rules govern how AI-assisted workflows (Claude Code or any agentic tool) must behave when working in this repository.

## Before Editing Any Test

Read and apply the following in order:

1. `CLAUDE.md` — project instructions and QA behavior rules
2. `agentic-qa-workflows/governance/qa_standards.md` — naming and assertion rules
3. `agentic-qa-workflows/governance/suite_taxonomy.md` — which suite a test belongs to

Do not edit test code before completing these reads.

## Before Adding a New Test

Also read:

1. `agentic-qa-workflows/governance/page_object_api_rules.md` — POM and API client boundaries
2. `agentic-qa-workflows/governance/test_data_env_rules.md` — data and environment rules

Confirm the new test:

- Follows naming conventions from `qa_standards.md`
- Carries the correct suite marker(s) from `suite_taxonomy.md`
- Does not duplicate setup already handled by existing fixtures

## Before Submitting a PR

Verify against `agentic-qa-workflows/governance/quality_gates.md`:

- Smoke suite passes
- Full suite passes
- Coverage floor is met for any new endpoint or flow
- Review `agentic-qa-workflows/governance/failure_evidence.md` and confirm failure artifacts or logs are captured when applicable.
- If this slice introduced an architectural decision not already captured in `agentic-qa-workflows/governance/architecture_decision_log.md`, add an ADR entry before merging.

## Session Constraints

- Make one focused change per session. Do not refactor, rename, or restructure code beyond the immediate task.
- After each change, run the smallest relevant test command and report the result.
- Do not commit or push unless the user explicitly requests it.

## Required Output

After any change, produce a QA summary containing:

1. What was reviewed
2. What was changed and why
3. Test command run and result (pass/fail)
4. Any risks or open items
5. Recommended next step
6. Failure evidence produced or reviewed, if applicable

### When to save a separate output file

Save a file under `agentic-qa-workflows/outputs/` only for:

- Governance or compliance audits
- Failure triage reports
- Release readiness or pre-release reviews
- CI evidence capture
- Significant multi-file or high-risk changes where a persistent record adds value

For small, low-risk changes — comment-only, decorator-only, single-file assertion fixes, or minor governance doc updates — produce a chat or terminal QA summary only. Do not create an output file unless the repo owner explicitly asks for one.
