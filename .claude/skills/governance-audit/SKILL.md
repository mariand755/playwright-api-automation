---
description: Run a read-only governance compliance audit with evidence and smallest-safe-fix recommendations.
disable-model-invocation: true
argument-hint: "[full|markers|test-data|failure-evidence|quality-gates|naming]"
allowed-tools:
  - Read
  - Grep
  - Glob
disallowed-tools:
  - Write
  - Edit
  - Bash
  - WebFetch
  - WebSearch
---

Run a read-only governance compliance audit of this repository against its governance framework. Produce structured findings with evidence, risk, and smallest-safe-fix recommendations. Do not edit files, run commands, create output reports, stage changes, commit, or push.

## Scope argument routing

`$ARGUMENTS` is optional. Route as follows:

| Argument | Behavior |
|---|---|
| *(blank)* | Default: report top 2–3 highest-value gaps, plus compliant areas summary |
| `full` | Report all gaps found across the seven selected audit-control documents |
| `markers` | Scope to marker taxonomy and `tc_id` compliance only |
| `test-data` | Scope to test data and environment rules only |
| `failure-evidence` | Scope to failure evidence capture only |
| `quality-gates` | Scope to PR, merge, release, and Docker gate rules only |
| `naming` | Scope to naming conventions and TC-ID format only |

If `$ARGUMENTS` contains any other value, print the accepted values table above and stop without auditing.

## Required reading per scope

Read only the files listed for the active scope before reporting. Do not make compliance claims outside the inspected scope.

| Invocation | Required reading |
|---|---|
| *(blank)* / `full` | CLAUDE.md + the seven selected audit-control documents + relevant test, fixture, page-object, and API-client files + pytest.ini + conftest.py + `.github/workflows/ci.yml` + relevant CI and release scripts |
| `markers` | CLAUDE.md, `agentic-qa-workflows/governance/qa_standards.md`, `agentic-qa-workflows/governance/suite_taxonomy.md`, pytest.ini, conftest.py, test files |
| `naming` | CLAUDE.md, `agentic-qa-workflows/governance/qa_standards.md`, `agentic-qa-workflows/governance/suite_taxonomy.md`, relevant test files, page-object files, and API-client files |
| `test-data` | CLAUDE.md, `agentic-qa-workflows/governance/test_data_env_rules.md`, relevant fixture files and test files |
| `failure-evidence` | CLAUDE.md, `agentic-qa-workflows/governance/failure_evidence.md`, conftest.py, relevant UI test files |
| `quality-gates` | CLAUDE.md, `agentic-qa-workflows/governance/quality_gates.md`, `.github/workflows/ci.yml`, relevant scripts and test files |

## Seven selected audit-control documents

1. `agentic-qa-workflows/governance/qa_standards.md`
2. `agentic-qa-workflows/governance/suite_taxonomy.md`
3. `agentic-qa-workflows/governance/page_object_api_rules.md`
4. `agentic-qa-workflows/governance/test_data_env_rules.md`
5. `agentic-qa-workflows/governance/failure_evidence.md`
6. `agentic-qa-workflows/governance/quality_gates.md`
7. `agentic-qa-workflows/governance/agentic_workflow_rules.md`

## Stop conditions

- If any required governance file cannot be read: report which file is missing and stop.
- If no test files are found under `test/`: report this finding and stop.
- Do not expand to concerns not covered by the governance files in scope.

## Output contract

Produce output in this exact structure:

```
## Governance Compliance Audit — [Default (Prioritized) | Full | Markers | Test-Data | Failure-Evidence | Quality-Gates | Naming]
**Date:** [today's date]
**Governance files read:** [list]
**Implementation evidence inspected:** [count and types]

### Compliant Areas
- [area]: [one-line evidence citation with file and observation]

### Gaps Found (Top N for default invocation; all findings for full or named-scope invocation)
#### Gap [N]: [short descriptive title]
- **Governing rule:** [exact document §section — quote the rule briefly]
- **Evidence:** [what the current implementation evidence shows: a test, fixture, page object, API client, workflow, script, or conftest location with the observation]
- **Risk:** [why this gap matters in one sentence]
- **Smallest safe fix:** [minimum targeted change; do not propose refactors]
- **Validation command:** [exact command for the engineer to run; do not run it yourself]

### Recommended Fix Order
[ordered list with rationale]

### What This Audit Does Not Do
- Does not edit files, run tests, or execute commands
- Does not create an output report (save this output manually if a permanent record is needed)
- Does not commit, push, or stage changes
- Does not make compliance claims outside the inspected scope
```

## Human-approval boundary

Mode A guidance only — do not edit files, create output reports, stage, commit, or push.

The engineer reviews each gap, decides which fixes to apply, applies them manually, and runs the validation commands listed in the output.

## Safety boundaries

- Never call Write, Edit, Bash, WebFetch, or WebSearch
- Never stage, commit, or push changes
- Never execute commands; validation commands are for the engineer to run
- Never make compliance claims outside the files read for the active scope
