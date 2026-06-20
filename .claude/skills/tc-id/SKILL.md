---
description: Inventory TC-IDs and suggest the next available ID for the API, UI, or SCRIPT suite.
disable-model-invocation: true
argument-hint: "[api|ui|script|all|validate]"
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

Inventory TC-IDs from the live test tree and suggest the next available ID for the API, UI, or SCRIPT suite. Do not edit files, run commands, create output reports, stage changes, commit, or push.

## Scope argument routing

`$ARGUMENTS` is optional. Route as follows:

| Argument | Behavior |
|---|---|
| *(blank)* or `all` | Full inventory: all three suites, issues found, next available IDs |
| `api` | TC-API suite only — range, next available, issues within that suite |
| `ui` | TC-UI suite only |
| `script` | TC-SCRIPT suite only |
| `validate` | Issues only: duplicates, malformed IDs, missing-marker candidates. No suite sections. No next-ID recommendation. |

If `$ARGUMENTS` contains any other value, print the accepted values table above and stop without inventorying.

## Discovery procedure

Discover the live TC-ID state from the repository before reporting anything. Do not rely on hardcoded knowledge of which IDs, gaps, or suffix variants exist.

**Step 1 — Grep for all TC-ID markers:**
Use the Grep tool to search `test/` recursively for the pattern `@pytest\.mark\.tc_id\(` in `.py` files only. Do not include `.pyc` or binary files.

**Step 2 — Extract TC-ID values:**
From each match line, extract the TC-ID string inside `@pytest.mark.tc_id("...")`. Ignore lines beginning with `#` — those are human-readable comment copies of the ID and must not be double-counted.

**Step 3 — Group by AREA:**
Separate extracted IDs into three groups: `API`, `UI`, `SCRIPT`. Any ID whose AREA is not one of these three is malformed.

**Step 4 — Per-group analysis:**
For each group:
- Classify each ID as a *base ID* (numeric digits only, no trailing letter) or a *suffixed ID* (numeric digits followed by exactly one lowercase letter).
- A suffixed ID is **valid** when its unsuffixed base exists in the same group. A suffixed ID whose unsuffixed base is absent from the same group is **malformed** (orphaned suffix).
- Find the maximum numeric base (ignoring any suffix when comparing).
- Identify numeric gaps in the base ID sequence. Report gaps as informational only — historical gaps are not failures and do not require backfill.
- Report all suffix variants discovered, grouped by their base ID.
- Compute next available ID: maximum numeric base + 1, zero-padded to at least three digits.

**Step 5 — Issue detection:**
- **Duplicates:** same full TC-ID string (base + optional suffix) appears at two or more distinct file:line locations.
- **Malformed:** does not match `TC-(API|UI|SCRIPT)-[0-9]{3,}[a-z]?`, or is a suffixed ID whose unsuffixed base does not exist in the same AREA.
- **Missing-marker candidates** (`validate` mode only): use Grep to count `^def test_` across `test/**/*.py`; compare with the tc_id marker count to produce an approximate delta. This count is unreliable — parametrize, helper wrappers, and multi-line definitions affect it. Report as manual-review evidence only, not as a deterministic finding.

## Output contract

Produce output in this exact structure:

```
## TC-ID Inventory — [All Suites | TC-API Suite | TC-UI Suite | TC-SCRIPT Suite | Validation Report]
**Generated from:** live grep of test/**/*.py — [today's date]
**Scope:** [blank/all | api | ui | script | validate]

### TC-API Suite        [include for: blank, all, api — omit for validate]
- Base IDs found: TC-API-[first] – TC-API-[last] ([N] base IDs)
- Gaps in base sequence: [none | list — informational only]
- Suffix variants: [none | list grouped by base]
- **Next available: TC-API-[NNN]**

### TC-UI Suite         [include for: blank, all, ui — omit for validate]
- Base IDs found: TC-UI-[first] – TC-UI-[last] ([N] base IDs)
- Gaps in base sequence: [none | list — informational only]
- Suffix variants: [none | list grouped by base]
- **Next available: TC-UI-[NNN]**

### TC-SCRIPT Suite     [include for: blank, all, script — omit for validate]
- Base IDs found: TC-SCRIPT-[first] – TC-SCRIPT-[last] ([N] base IDs)
- Gaps in base sequence: [list — informational only; historical gaps are not failures]
- Suffix variants: [list grouped by base — e.g. TC-SCRIPT-065: 065a, 065b]
- **Next available: TC-SCRIPT-[NNN]**

### Issues Found         [always present; is the only section rendered for validate]
- Duplicates: [none | list with file:line citations]
- Malformed IDs: [none | list — wrong AREA, wrong format, or orphaned suffix]
- Missing-marker candidates [validate mode only]: approximately [N] def test_ functions
  may lack a tc_id marker (imprecise — parametrize, wrappers, and multi-line definitions
  affect this count; treat as a starting point for manual review only)

### Recommendation      [include for: blank, all, api, ui, script — omit for validate]
To add a new [AREA] test, use **TC-[AREA]-[NNN]**.

⚠️ Advisory only. The engineer decides whether and how to apply this recommendation.
This skill does not edit test decorators, pytest.ini, conftest.py, JUnit output, or governance documents.
After applying a new TC-ID, validate with: pytest test/scripts/test_tc_id_uniqueness.py -v

### What This Skill Does Not Do
- Does not edit files, run tests, or execute commands
- Does not commit, push, or stage changes
- Does not make inventory claims without first grepping the live test tree
```

## Stop conditions

- If `test/` cannot be found or read: report which path is inaccessible and stop.
- If Grep returns no TC-ID markers at all: report as a finding; do not invent inventory.
- If `$ARGUMENTS` is not in the accepted list: print accepted values and stop.

## Safety boundaries

- Never call Write, Edit, Bash, WebFetch, or WebSearch
- Never stage, commit, or push changes
- Never execute commands; the validation command in the output is for the engineer to run
- Never report inventory based on hardcoded knowledge — always grep first
