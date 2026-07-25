---
description: QA Architect / Solution Architect review for any implementation slice — Mode A (plan review before editing) or Mode B (implementation review before committing).
disable-model-invocation: true
argument-hint: "[a|b] <path>"
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

Run a read-only QA Architect / Solution Architect review for an implementation slice. Mode A reviews a plan before file editing begins. Mode B reviews an implementation before committing. Do not edit files, run commands, create output reports, stage changes, commit, or push.

## Argument routing

`$ARGUMENTS` must contain exactly two tokens: a mode and a path.

| Argument | Behavior |
|---|---|
| `a <plan-path>` | Mode A — Plan Review: reads the plan at `<plan-path>` and evaluates it before any file editing |
| `b <review-packet-path>` | Mode B — Implementation Review: reads the review packet at `<review-packet-path>` and evaluates the implementation before committing |

If `$ARGUMENTS` is blank or the first token is not `a` or `b`, print this table and stop.

## Mode B review packet format

Mode B requires a review packet — a temporary, untracked file the engineer creates before invoking the skill. Recommended location: `.private/slice-review-packet.md`.

```
# Slice Review Packet

Slice: <brief name>

Changed files:
- path/one.py
- path/two.md

Diff:
<pasted unified diff>
```

The review packet is temporary and untracked. Delete it after the session.

## Stop conditions

1. `$ARGUMENTS` is blank → print the argument routing table; stop. No files read.
2. First token is not `a` or `b` → print the argument routing table; stop. No files read.
3. Second token (path) is absent → print the required invocation format for the detected mode; stop.
4. The file at `<path>` cannot be read → report the path; stop.
5. Mode B — review packet `Slice:` field is absent or blank → report which field is missing; stop.
6. Mode B — review packet is missing `Changed files:` field → report which field is absent; stop.
7. Mode B — review packet has no `Diff:` section or the section is empty → report; stop. Do not conduct a partial review.
8. Any governance file cannot be read during the inspection step → report which file is inaccessible; stop.

## Inspection sequence

**Step 1 — Argument routing**
Parse `$ARGUMENTS`. Extract mode token (first) and path token (remainder). Apply stop conditions 1–3.

**Step 2 — Read the supplied file**
Read the file at `<path>`. Apply stop conditions 4–7.
- Mode A: note the plan title heading; this becomes the slice name in the output header. If no usable heading exists, use "unnamed."
- Mode B: validate required packet fields (`Slice:`, `Changed files:`, `Diff:`).

**Step 3 — Read governance files**
Read `CLAUDE.md` and all files under `agentic-qa-workflows/governance/`. Apply stop condition 8.

**Step 4 (Mode A) — Read proposed-change files**
Read each file the plan proposes to change, where readable.

**Step 4 (Mode B) — Read implementation files**
Read each file listed under `Changed files:` in the packet. Read adjacent files as needed to evaluate separation of concerns, dependency relationships, or marker compliance.

**Step 5 — Apply independence preface**
Before evaluating: do not treat review criteria as a checklist to confirm. Verify the actual state from the files read. Challenge assumptions, identify missing risks, and propose a better approach or flag a follow-up slice if the plan or implementation is not the best option. Bring in industry judgment around CI/CD reliability, release governance, security, data handling, maintainability, and consulting blueprint value.

**Step 6 — Produce output**
Produce the full output in Mode A (9-section) or Mode B (6-section, 11-dimension) format. Do not omit any named section, even if the finding is N/A or "none identified."

## Mode A output contract

```
## Slice Review — Mode A: Plan Review
**Slice:** [derived from plan title heading, or "unnamed" if no usable heading]
**Date:** [today's date]
**Plan file reviewed:** [path]

**Verdict**: Approve plan / Approve plan with changes / Rework plan

**Scope assessment**: [PR-sized? Should anything be split or deferred?]

**File-by-file plan assessment**:
[For each planned file: does the change belong here? Is it complete? Is anything missing?]

**Risks before editing**:
[What could go wrong if the plan is executed as written]

**Required plan changes before implementation**:
[Ranked by severity. Each finding: what to change + why. If none: "None."]

**Validation expectations**:
[Commands that must pass after implementation before the slice is considered done]

**Validation integrity**:
[Do the proposed validation commands cover all changed files?]
[Docker rebuild: required if Python files, Dockerfile, or requirements.txt are changed. Declare N/A if not applicable.]
[CI-only checks (CodeQL, pip-audit, Trivy): acknowledged as CI-only if applicable. Declare N/A if not applicable.]
[Branch protection or GitHub settings impact: addressed if applicable. Declare N/A if not applicable.]
[Security and secret handling: applies when the plan touches env vars, credentials, GitHub Secrets, os.environ reads, or .env files. Declare N/A if not applicable.]
[Data handling and artifact exposure: applies when the slice activates a production data path, extends CI artifact production, or routes data to external services. Declare N/A if not applicable.]

**Adjacent-risk findings (max 3)**:
[For each: description — classification (Blocker / Recommended before commit / Follow-up slice) — rationale]
[Blocker findings also appear in "Required plan changes before implementation." If none: "None identified."]

**Trade-offs, benefits, and consulting value**:
- Alternatives considered: [...]
- Why the proposed approach is the best fit: [...]
- Cost, speed, risk, or maintenance benefit: [...]
- Intentionally deferred and why: [...]
- How this helps a consulting client or QA architecture team: [...]
```

## Evaluation dimensions

Evaluate all 11 dimensions using these criteria. For any dimension whose criteria do not apply to the file types changed in this slice, declare N/A with explicit rationale — do not silently omit.

**1. Separation of concerns** — API clients return raw Response with no assertions. Fixtures handle setup/teardown only. Tests hold all assertions. Page objects hold locators and `expect()`. No boundary violations across these roles.

**2. Test data design** — Deterministic payloads; credentials and URLs from fixtures, never inlined in tests. Factory fixture introduced at 3+ uses; callable with named, overridable parameters.

**3. Test isolation and cleanup** — Each test independently runnable. Cleanup via fixture teardown or `addfinalizer`. Teardown failures visible, not swallowed. Any known isolation limitation documented in an ADR.

**4. Marker and TC-ID quality** — TC-ID comment (`# TC-AREA-NNN`) above the full decorator stack. Area marker and scope marker(s) present. `api_contract` marker on any test that calls `jsonschema.validate()`. Markers match `suite_taxonomy.md`. New markers declared in `pytest.ini` before use.

**5. File organisation and scalability** — File split by domain or workflow, not by marker. Split a file at ~10–12 tests or when mixed workflows appear. Schema files in `data/schemas/`.

**6. CI, reporting, and release-gate readiness** — No CI redesign required. Test paths collected by existing `testpaths`. Output artifacts written to `artifacts/`. Docker rebuild confirmed if Python files, `Dockerfile`, or `requirements.txt` changed. No reliance on a stale image. Pre-commit is not treated as a substitute for Docker CI.

**7. Blueprint and consulting value** — Pattern is liftable by a blueprint adopter. Correctly documented for its usage. Scale is appropriate. Avoids obvious future rework.

**8. Risks and recommended fixes** — Brittle assertions, silent failure paths, dead code, flakiness vectors, scope creep, reasons a split-before-merge would be safer.

**9. Trade-offs and consulting value** — Meaningful alternatives were considered. Best fit chosen. Cost/speed/risk/maintenance balance is explicit. Deferred work has documented rationale. Pattern is credible and reusable for a consulting reader.

**10. Security and secret hygiene** — Applies when the slice touches env vars, credentials, GitHub Secrets, `os.environ` reads, `.env` files, or produces new CI artifacts or routes data to external services. Taint chain: secret read → variable → only hardcoded status strings in log/print; taint broken at variable level. Declare N/A if not applicable.

**11. Bounded adjacent-risk scan** — Cap at 3 findings. Classify each: Blocker / Recommended before commit / Follow-up slice. Do not expand scope unless a finding is Blocker. Blocker findings also appear in "Recommended fixes before commit."

## Mode B output contract

```
## Slice Review — Mode B: Implementation Review
**Slice:** [from packet Slice: field]
**Date:** [today's date]
**Files reviewed:** [list from packet Changed files:]

**Verdict**: Approve / Approve with fixes / Request changes

**Dimension-by-dimension findings**:

1. Separation of concerns: [Pass/Fail/N/A] — [specific observation]
2. Test data design: [Pass/Fail/N/A] — [specific observation]
3. Test isolation and cleanup: [Pass/Fail/N/A] — [specific observation]
4. Marker and TC-ID quality: [Pass/Fail/N/A] — [specific observation]
5. File organisation and scalability: [Pass/Fail/N/A] — [specific observation]
6. CI, reporting, and release-gate readiness: [Pass/Fail/N/A] — [specific observation]
7. Blueprint and consulting value: [Pass/Fail/N/A] — [specific observation]
8. Risks and recommended fixes: [Pass/Fail/N/A] — [specific observation]
9. Trade-offs and consulting value: [Pass/Fail/N/A] — [specific observation]
10. Security and secret hygiene: [Pass/Fail/N/A] — [specific observation]
11. Bounded adjacent-risk scan: [Pass/Fail/N/A] — [up to 3 findings; description — classification (Blocker / Recommended before commit / Follow-up slice) — rationale]

**Recommended fixes before commit**:
[Ranked High/Medium/Low. Each: file + what to change + why.
Blocker findings from Dimension 11 belong here. If none: "None."]

**Follow-up slice items from adjacent-risk scan**:
[For each Follow-up slice finding from Dimension 11:
description — rationale — suggested slice scope. If none: "None identified."]

**Blueprint assessment**:
[One short paragraph: does this slice move the repo meaningfully toward the
production-style QA architecture blueprint?]

**Implementation trade-offs and realized value**:
- Did the implementation preserve the intended trade-offs from the plan? [...]
- Did any new trade-off appear during implementation? [...]
- Benefit in terms of speed, cost, maintainability, risk reduction, or release confidence: [...]
- Is the benefit clear enough for a future consulting/client reader? [...]
```

## Human-approval boundary

Advisory only. Do not edit files, create output reports, stage changes, commit, or push in either mode.

The engineer reviews the output, decides which required changes to apply, applies them manually, and re-invokes `/slice-review b` if significant changes were made before committing.

## Safety boundaries

- Never call Write, Edit, Bash, WebFetch, or WebSearch
- Never stage, commit, or push changes
- Never execute commands; validation commands in the output are for the engineer to run
- Never edit files in either Mode A or Mode B, regardless of what the engineer requests
