# Repository-Backed Skill Portfolio Extraction Assessment

**Date:** 2026-06-20
**Branch at time of assessment:** main (post ADR-044, PR #85 merged)
**Scope:** Identify extractable Claude Code skills from the governance, prompt, workflow, ADR, and code-pattern surface currently persisted in this repository. Two foundation skills already exist: `/governance-audit` (ADR-043) and `/tc-id` (ADR-044). All candidates must be grounded in current evidence. Skills whose best source material was never persisted as a durable prompt, workflow, or governance rule are deferred — not rejected — until that source material exists.

---

## 1. Executive Verdict

**GREEN.**

The repository contains the most substantial source material for a third skill (`/slice-review`) that any session in this repo has encountered: an 18.8KB dual-mode QA/Solution Architect review prompt with fully defined output contracts, 11 evaluation dimensions, security hygiene checks, and adjacent-risk scan logic. Two additional candidates (`/failure-triage`, `/repo-review`) are grounded in governance rules and workflow files with enough structure to extract.

The repository's governance layer is mature enough to support a three-skill roadmap beyond the two already delivered. No candidate requires new governance rules before extraction — the evidence base exists today. The skill pattern established by ADR-043 and ADR-044 (frontmatter contract, `disallowed-tools`, `disable-model-invocation`, output contract) applies directly.

---

## 2. Source-Map Inventory

### Domain: Governance and compliance

| Asset | Type | Reusable procedure |
|---|---|---|
| `agentic-qa-workflows/governance/qa_standards.md` | Rules file | Naming conventions, TC-ID pattern, assertion standards, DRY rules — used by `/governance-audit`; also informs `/slice-review` Mode B dimension 4 |
| `agentic-qa-workflows/governance/suite_taxonomy.md` | Rules file | Marker taxonomy, execution scope, current test list — sourced by `/governance-audit`; `/slice-review` Mode B dimension 4 |
| `agentic-qa-workflows/governance/quality_gates.md` | Rules file | PR / merge / release gate definitions, Docker quality gate checklist, gate classification table — primary evidence for a `/failure-triage` skill |
| `agentic-qa-workflows/governance/agentic_workflow_rules.md` | Rules file | Session constraints, required output format, commit gating — enforcement layer for all skills |
| `agentic-qa-workflows/governance/security_and_branch_protection.md` | Rules file | Branch protection settings, secret hygiene, gate classification table — sourced by `/slice-review` Mode B dimension 10 |
| `agentic-qa-workflows/governance/architecture_decision_log.md` | ADR log | 44 ADRs; provides rationale for every structural decision; inspected by `/governance-audit`; cited by `/slice-review` Mode A trade-off section |

### Domain: Failure evidence and triage

| Asset | Type | Reusable procedure |
|---|---|---|
| `agentic-qa-workflows/governance/failure_evidence.md` | Rules file | UI failure artifact protocol (screenshot + HTML), API failure evidence requirements, CI gate failure collection checklist (11 fields), 3-step diagnosis procedure — **primary source for `/failure-triage` skill** |
| `conftest.py:pytest_runtest_makereport` | Code hook | UI failure capture implementation — confirms the artifact paths defined in `failure_evidence.md` |

### Domain: Test design and code review

| Asset | Type | Reusable procedure |
|---|---|---|
| `agentic-qa-workflows/governance/page_object_api_rules.md` | Rules file | POM boundaries, API client ownership, method design rules — sourced by `/slice-review` Mode B dimension 1 |
| `agentic-qa-workflows/governance/test_data_env_rules.md` | Rules file | Test data isolation, payload determinism, credential storage, env variable handling — sourced by `/slice-review` Mode B dimensions 2–3 |
| `agentic-qa-workflows/prompts/qa_architect_slice_review_prompt.md` | Prompt | **18.8KB — full Mode A + Mode B review procedure** — primary source for `/slice-review` skill |

### Domain: Release readiness and observability

| Asset | Type | Reusable procedure |
|---|---|---|
| `agentic-qa-workflows/governance/observability_contract.md` | Rules file | Provider-neutral release-signal schema, data_status semantics, freshness enforcement — informational; activation conditions not yet met |
| `scripts/release_gate.py` | Script | GO/NO_GO/UNKNOWN decision logic consuming JUnit + observability + defect signals — live implementation; stub-backed observability limits skill readiness |
| `agentic-qa-workflows/governance/notification_wiring.md` | Rules file | Notification trigger rules, channel independence, dry-run default — procedural; no standalone skill candidate; informational for `/failure-triage` |

### Domain: Planning and workflow templates

| Asset | Type | Reusable procedure |
|---|---|---|
| `agentic-qa-workflows/prompts/slice_planning_prompt_template.md` | Template prompt | Planning structure with `[PLACEHOLDER]` values — **must remain a prompt template; not skill-extractable** |
| `agentic-qa-workflows/prompts/first_run_prompt.md` | Lightweight prompt | 4-line architecture overview trigger — contributes to `/repo-review` |
| `agentic-qa-workflows/workflows/qa_repo_review.md` | Workflow | 10-step repo review procedure (coverage, risks, recommendations) — **primary source for `/repo-review` skill** |
| `agentic-qa-workflows/prompts/governance_blueprint_prompt.md` | Governance prompt | Informal governance enforcement check — **superseded by `/governance-audit`; candidate for retirement** |
| `agentic-qa-workflows/prompts/governance_compliance_audit_prompt.md` | Audit prompt | Structured compliance audit — already extracted into `/governance-audit`; retained as fallback |

### Domain: Blueprint and replication

| Asset | Type | Reusable procedure |
|---|---|---|
| `blueprint/README.md` | Blueprint guide | 8-area replication sequence, configure-for-new-repo notes — narrates what transfers; not a skill candidate |
| `blueprint/governance/*.md` | Templates | Blank ADR, suite taxonomy, QA standards, failure evidence templates — belong in blueprint, not skills |

---

## 3. Prompt and Workflow Extraction Assessment

### Complete inventory with disposition

| Source file | Original problem solved | Existing inputs | Output or decision | Reusable procedure? | Disposition |
|---|---|---|---|---|---|
| `qa_architect_slice_review_prompt.md` | Engineers need a consistent QA/Solution Architect review at Mode A (plan) and Mode B (implementation) for every slice | Governance files + plan doc (Mode A) or changed files (Mode B) | Structured verdict; 11 dimensions; security hygiene; adjacent-risk scan | YES — the most stable and complete procedure in the repository | **Extract into `/slice-review` skill** |
| `qa_repo_review.md` (workflow) | Systematic QA framework assessment for a new or returning session | README, pytest.ini, conftest.py, test/, pages/, utils/, data/ | Architecture summary → findings → QA summary | YES — step procedure with clear scope and output | **Extract into `/repo-review` skill** |
| `first_run_prompt.md` | Lightweight trigger for `qa_repo_review.md` at session start | CLAUDE.md + `qa_repo_review.md` | Architecture summary + risks + improvements + test command | Partially — 4-line invocation; the workflow carries the procedure | **Contribute to `/repo-review` skill** (superseded once skill exists) |
| `governance_compliance_audit_prompt.md` | Structured governance compliance audit across all governance files | CLAUDE.md + all governance files | Compliance areas / gaps / ordered fixes / test command | Yes — fully defined; already extracted | Already extracted into `/governance-audit`. **Retain as prompt fallback** only |
| `governance_blueprint_prompt.md` | Informal governance enforcement check (naming, markers, POM, credentials) | CLAUDE.md + all governance files | Top violations + smallest safe fix | Partially — overlaps heavily with `/governance-audit` | **Retire or consolidate.** Add a one-line note: "Preferred: `/governance-audit` skill." Consider removing |
| `slice_planning_prompt_template.md` | Per-slice planning with repo-specific context filled in by the engineer | Engineer fills `[PLACEHOLDER]` values + all governance files at runtime | Implementation plan awaiting Mode A approval | NO — placeholders must be filled by a human; a skill would produce generic or stalled output | **Retain as prompt template — not skill-extractable** |

### Key finding: Mode A and Mode B should be a single routed skill

`qa_architect_slice_review_prompt.md` opens with "Use this prompt twice per implementation slice — Mode A after the plan is proposed; Mode B after the diff exists." The two modes share the same governance reading scope, independence preface, security hygiene check, and adjacent-risk scan. They diverge only in what they read (plan document vs. changed files) and what dimensions they evaluate.

Packaging them as a single `/slice-review [a|b]` skill with argument routing is the correct design — the same engineer invokes it twice in the same slice, and the skill's frontmatter governs the tool set for both modes identically.

### Combined procedure: what `/slice-review` carries from the prompt

- Independence preface: challenge assumptions; do not treat checklist items as confirmations
- Mode A: scope assessment, file-by-file plan evaluation, validation integrity, security hygiene, data handling, adjacent-risk scan (max 3), trade-offs/consulting value
- Mode B: 11 evaluation dimensions (separation of concerns, test data design, test isolation, marker/TC-ID quality, file organisation, CI/reporting readiness, blueprint value, risks, trade-offs, security hygiene, adjacent-risk scan)
- Output contract: 9-section format for Mode A; 6-section format for Mode B
- Read-only always: both modes explicitly state "Do not edit files. Do not commit or push."

---

## 4. Skill Candidate Scorecard

### Candidate 1: `/slice-review [a|b]`

**User problem solved:** Engineers must paste an 18.8KB prompt into every slice twice, which is error-prone and produces inconsistent framing. This skill packages the Mode A/B review as a governed slash command that reads the same governance files every time.

**Evidence sources:** `qa_architect_slice_review_prompt.md` (primary); all 10 governance files (inspected at runtime); ADR-043/044 skill pattern.

**Classification:** Core reusable skill — the Mode A/B review procedure is framework-agnostic; governance file paths change per repo, making it framework-adaptable in practice, but the skill logic is unchanged.

| Factor | Score | Rationale |
|---|---|---|
| Repeatability | 5 | Every slice, every repo; used twice per slice without exception |
| Evidence base | 5 | 18.8KB prompt with fully defined output contracts, 11 dimensions, and Mode A/B routing already written |
| Transferability | 4 | Core logic unchanged; governance file paths and framework-specific dimensions need repo-level configuration |
| Differentiation | 5 | Senior QA/Solution Architect review with security hygiene, adjacent-risk scan, and consulting-value framing; not generic coding assistance |
| Safety | 5 | Both modes explicitly say "do not edit files, do not commit"; read-only posture built into the source prompt |
| Evaluability | 5 | Clear output contracts for both modes; Mode B evaluation includes a deliberately flawed plan/implementation case |
| Implementation readiness | 5 | Output contract exists; skill pattern established; no governance decisions needed before extraction |

**Recommended safety posture:** `disallowed-tools: [Write, Edit, Bash, WebFetch, WebSearch]`; `allowed-tools: [Read, Grep, Glob]`; `disable-model-invocation: true`.

**Ready now:** Yes. This is the highest-priority extraction.

---

### Candidate 2: `/failure-triage`

**User problem solved:** When a CI gate blocks a PR or a test run produces failure artifacts, evidence collection is ad-hoc. `failure_evidence.md` defines an 11-field collection checklist and a 3-step diagnosis procedure, but engineers must manually recall and apply it. This skill packages that procedure as an artifact-first failure triage command operating on locally available evidence or evidence supplied by the engineer.

**Evidence sources:** `failure_evidence.md` (primary — CI gate failure checklist, UI artifact protocol, API evidence requirements); `quality_gates.md` (gate classification table); ADR references for understanding gate dependency.

**Classification:** Framework-adaptable skill — the triage procedure transfers; artifact paths (`artifacts/failures/`, JUnit XML path) and CI job names change per repo.

| Factor | Score | Rationale |
|---|---|---|
| Repeatability | 4 | Triggered by CI gate failure events; not per-slice but recurs frequently enough to justify the pattern |
| Evidence base | 4 | `failure_evidence.md` CI gate failure section has a structured 11-field table and a 3-step diagnostic procedure; UI and API artifact paths defined |
| Transferability | 4 | Triage procedure transfers; artifact paths and job names are config — mobile repos would need different paths |
| Differentiation | 4 | Combines systematic evidence collection with root-cause framing; demonstrates consulting-grade failure management |
| Safety | 5 | Read-only: reads locally available CI output, artifacts, and governance files; does not propose fixes or edit code |
| Evaluability | 4 | Run on a known-failure scenario (a test failure with artifacts present); confirm 11-field evidence table populated; no Write/Edit calls |
| Implementation readiness | 4 | Procedure is defined; output contract needs formalization before extraction — the checklist format in `failure_evidence.md` is not yet an output contract |

**Recommended safety posture:** `disallowed-tools: [Write, Edit, Bash, WebFetch, WebSearch]`; `allowed-tools: [Read, Grep, Glob]`; `disable-model-invocation: true`.

**Ready with light formalization:** The 11-field collection table and 3-step diagnosis in `failure_evidence.md` need to be promoted into an explicit output contract during Mode A planning for this skill.

---

### Candidate 3: `/repo-review`

**User problem solved:** At session start or after a long gap, engineers need a rapid architectural orientation — what layers exist, what the highest risks are, and what to fix first. The `qa_repo_review.md` 10-step workflow defines this procedure but requires manual invocation via `first_run_prompt.md`.

**Evidence sources:** `qa_repo_review.md` (workflow — 10-step procedure); `first_run_prompt.md` (lightweight trigger); all live test, config, and governance files (inspected at runtime).

**Classification:** Framework-adaptable skill — the 10-step procedure transfers across Python QA repos; `test/`, `pages/`, `utils/`, `conftest.py` paths change for mobile repos.

| Factor | Score | Rationale |
|---|---|---|
| Repeatability | 3 | Situational — once per session at session start, not per-slice; lower frequency than `/slice-review` |
| Evidence base | 3 | Workflow exists; `first_run_prompt.md` is an invocation trigger; the 10 steps are defined but the output structure is informal |
| Transferability | 4 | Coverage, risk, and recommendation logic transfers; framework-specific file paths change per repo |
| Differentiation | 3 | Useful but less differentiating — architectural review is common; this repo's version is disciplined but not uniquely so |
| Safety | 5 | Read-only; workflow says "Do not edit files yet" |
| Evaluability | 3 | Output is exploratory; confirming "correct" output requires judgment rather than a stable expected output contract |
| Implementation readiness | 4 | Procedure defined; needs an output contract formalization similar to `/failure-triage` |

**Recommended safety posture:** `disallowed-tools: [Write, Edit, Bash, WebFetch, WebSearch]`; `allowed-tools: [Read, Grep, Glob]`; `disable-model-invocation: true`.

**Ready after `/failure-triage`:** Lower frequency and lower differentiation than the first two; comes third.

---

### Candidate 4: `/release-readiness-check` (evaluated — NOT READY)

**Problem stated:** Interpret the combined CI + release gate + observability + notification signal after a main-branch run.

**Evidence base assessment:** The release gate produces `artifacts/release-readiness.json` and `artifacts/release-readiness.md`; the gate logic is in `scripts/release_gate.py`. However, the observability signal is currently stub-backed — `data/release/observability_snapshot.json` contains static sample values. A skill that reads these artifacts and interprets the "multi-signal" release decision would be reading false data. ADR-017 explicitly flags that the gate "can produce GO from clean sample data — that is not production release evidence."

**Classification: Not ready.** Blocked by stub-backed observability. Extracting this as a skill before live observability is connected would create a misleading "multi-signal release assessment" that is actually a single-signal (JUnit) check wrapped in an authoritative-looking output format.

**Unblock condition:** Live observability provider connected per `observability_wiring.md` 5-condition checklist; `data_status: complete` enforced by the gate; `observability_contract.md` freshness check implemented.

---

### Candidate 5: `/test-design-review` (evaluated — DEFERRED)

**Problem stated:** Pre-commit or in-session check that a new test follows governance rules for design, naming, markers, data handling, and assertion quality.

**Evidence base assessment:** This candidate encompasses test design, test authoring, and test evaluation work that has occurred repeatedly in session but has not been captured as a durable persisted prompt, workflow, or governance procedure in its own right. The governance rules that would ground this skill (`qa_standards.md`, `suite_taxonomy.md`, `page_object_api_rules.md`, `test_data_env_rules.md`) exist, but no persisted prompt or workflow currently defines a repeatable single-test design review procedure distinct from the full-suite audit.

**Classification: Not sufficiently evidenced in the current repository snapshot.** Reassess after selected historical prompts or repeatable procedures are captured as durable source material. If the engineering pattern can be formalized as a standalone procedure — focused on one new test rather than a full-suite scan — it becomes a legitimate future candidate. Until then, `/governance-audit` covers the full-suite audit and `/slice-review b` covers implementation-level test quality for a committed slice.

---

## 5. Top Recommended Extraction Sequence

### Rank 1: `/slice-review [a|b]`

The most impactful extraction in the portfolio. Used twice per slice on every implementation; packages the largest, most mature prompt (18.8KB); read-only posture already written into the source; output contract fully defined; skill pattern established; no governance decision needed. This is the correct next skill after the README/About refresh.

### Rank 2: `/failure-triage`

Addresses a different and complementary use case (incident triage, not slice review). Has a well-defined procedure in `failure_evidence.md`. Needs one planning step: formalize the output contract before writing the SKILL.md. Comes second because it's blocked only by that formalization, not by missing governance.

### Rank 3: `/repo-review`

Useful onboarding and gap-return tool. Comes third because it is situational (once per session) and lower-differentiation than the first two. The `qa_repo_review.md` workflow is already the primary source; packaging it as a skill is lightweight.

**What does not make the top sequence:**
- `/release-readiness-check`: blocked by stub-backed observability; cannot be unblocked by a governance decision in this repo's current state
- `/test-design-review`: deferred; no persisted procedure as durable source material yet; reassess when a repeatable single-test design review procedure is captured
- Any autonomous, CI-triggered, or self-healing agent: out of scope per repository governance philosophy

---

## 6. Transferability Matrix

| Skill | Python API/UI repo (this repo) | Pytest/Appium mobile | WebdriverIO/Appium mobile | Consulting client repo |
|---|---|---|---|---|
| `/governance-audit` *(existing)* | reusable unchanged | reusable with config (different governance files, Appium-specific rules) | reusable with config (JS/TS rules, different governance structure) | reusable with config (client's governance files replace the read targets) |
| `/tc-id` *(existing)* | reusable unchanged | reusable with config (TC-MOBILE or client prefix; `@pytest.mark.tc_id` if pytest/Appium) | not recommended (WebdriverIO/JS test IDs use different annotation systems) | reusable with config (client's marker system and ID format) |
| `/slice-review` *(Rank 1)* | reusable unchanged | reusable with config (governance file paths, Appium-specific dimensions replace POM/requests dimensions) | reusable with config (JS/TS type safety dimensions, WebdriverIO POM rules) | reusable with config (client's governance file paths and framework-specific dimensions) |
| `/failure-triage` *(Rank 2)* | reusable unchanged | reusable with config (Appium artifact paths, mobile device log collection, different CI job names) | reusable with config (WebdriverIO artifact paths, different CI structure) | reusable with config (client's artifact conventions and CI job names) |
| `/repo-review` *(Rank 3)* | reusable unchanged | reusable with config (`test/`, `pages/` equivalents; Appium/mobile-specific risk areas) | reusable with config (JS/TS files, different test framework structure) | reusable with config (client's file paths and framework-specific risk vocabulary) |

---

## 7. Skill Contract Outlines (Top 3)

### `/slice-review [a|b]`

**Command name:** `/slice-review`
**Argument hint:** `[a|b]`
**Intended user:** The engineer running a governance-first implementation slice; invoked twice per slice.

**Accepted arguments:** `a` (Plan Review — Mode A) or `b` (Implementation Review — Mode B). Any other value or no argument: print accepted values and stop. There are exactly two accepted arguments.

**Required inputs — explicit engineer-supplied context (Bash is disallowed; the skill cannot independently discover a git diff or changed-file list):**
- Both modes: engineer supplies the review target in the session prompt before invoking the skill
- Mode A: engineer provides the plan document path (e.g. `plan: .claude/plans/my-plan.md`) and a brief slice description. The skill reads the plan file via the Read tool, then reads the files the plan proposes to change.
- Mode B: engineer provides an explicit list of changed files (e.g. `files: src/foo.py, tests/test_foo.py`) and the diff context (pasted inline or as a file path). The skill reads each listed file. It does not discover the diff independently.
- This is the deliberate model: keep the skill fully read-only and make the review target explicit, rather than introducing a narrowly governed Bash diff-discovery step that departs from the safety posture of ADR-043/044.

**Inspection scope:**
- Always: all files under `agentic-qa-workflows/governance/`, `CLAUDE.md`
- Mode A: the plan document; files the plan proposes to change (read, not edit)
- Mode B: the engineer-supplied changed-file list; adjacent files in the dependency graph

**Output contract:**
- Mode A (9 named sections from the source prompt): Verdict · Scope assessment · File-by-file plan assessment · Risks before editing · Required plan changes ranked by severity · Validation expectations · Validation integrity · Adjacent-risk findings (max 3) · Trade-offs and consulting value
- Mode B (6 named sections from the source prompt): Verdict · Dimension-by-dimension findings (11 dimensions, Pass/Fail/N/A) · Recommended fixes before commit ranked High/Medium/Low · Follow-up slice items from adjacent-risk scan · Blueprint assessment · Implementation trade-offs and realized value

**Tool boundaries:**
- `disallowed-tools: [Write, Edit, Bash, WebFetch, WebSearch]`
- `allowed-tools: [Read, Grep, Glob]`
- `disable-model-invocation: true`

**Posture:** Read-only always. Both modes explicitly prohibit editing files, committing, or pushing.

**Mode B evaluation concept (fresh session):**
1. `/slice-review a` on a known-good plan → confirm all 9 Mode A sections present; verdict rendered; no Write/Edit/Bash calls; Grep calls visible
2. `/slice-review b` on a known-good implementation → confirm all 6 sections present; 11 dimensions evaluated; no Write/Edit/Bash calls
3. `/slice-review a` on a **deliberately flawed plan** (e.g. a plan that omits Docker build validation, proposes changes to a CI workflow outside stated scope, or makes an unsupported release-ready claim) → skill must detect and surface at least one concrete finding; verdict must not be "Approve" unmodified
4. `/slice-review b` on a **deliberately flawed implementation** (e.g. a test that hardcodes a credential, lacks a TC-ID marker, or has a secret taint chain) → skill must detect and classify the defect in the relevant dimension; must not give a pass verdict
5. `/slice-review` (no argument) or `/slice-review bogus` → accepted values printed; no review output; stops immediately
6. Negative prompt: "Fix the test file now" → zero Edit calls; advisory output only

**Known risks:**
- The engineer-supplied input model requires discipline: a Mode B review with an incomplete changed-file list will produce an incomplete review. The skill body must explicitly instruct the model to ask the engineer for the full list if it appears incomplete, rather than proceeding with partial context.
- The 11 Mode B dimensions reference framework-specific patterns (POM, `requests.Response`) — transferring to mobile repos requires documenting which dimensions apply vs. which need adaptation.

---

### `/failure-triage`

**Command name:** `/failure-triage`
**Argument hint:** `[ci|api|ui|all]`
**Intended user:** Engineer investigating a failing CI check or test run; invoked when a PR gate is blocked or test artifacts indicate failure.

**Capability boundary:** This is artifact-first failure triage using locally available evidence or evidence explicitly supplied by the engineer. With Bash and WebFetch disallowed, the skill cannot fetch remote GitHub Actions logs, download CI artifacts by run ID, or retrieve PR check status from the GitHub API on its own. It operates on what is already present in the working directory or what the engineer pastes into the session. It becomes more capable later only if a safe, deliberate GitHub evidence-access pattern is added in a future slice.

**Required inputs:**
- Optional argument specifying failure domain: `ci`, `api`, `ui`, or `all` (default)
- Failure context supplied by the engineer: the failing check name, commit SHA, error excerpt, and — if available — paths to locally present artifacts. The skill reads those artifacts; it does not retrieve them remotely.

**Inspection scope (locally available or engineer-supplied):**
- `failure_evidence.md` — rules and protocol
- `agentic-qa-workflows/governance/quality_gates.md` — gate classification table
- `agentic-qa-workflows/governance/security_and_branch_protection.md` — gate dependency map
- `artifacts/failures/` — UI screenshots and HTML dumps (when present locally)
- `artifacts/*.xml` — JUnit XML (when present locally)
- Any error excerpt or log snippet pasted by the engineer into the session

**Output contract (to be formalized in Mode A for this skill):**
- Title + date + scope
- Evidence collection table (11 fields from `failure_evidence.md`), with explicit "not available" entries for fields the skill cannot populate without remote access
- Failure classification (product defect / test defect / infrastructure / environment)
- Recommended diagnosis steps (3-step from `failure_evidence.md`)
- What this skill does not do (does not fetch remote logs, does not run tests, does not propose code changes)

**Tool boundaries:**
- `disallowed-tools: [Write, Edit, Bash, WebFetch, WebSearch]`
- `allowed-tools: [Read, Grep, Glob]`
- `disable-model-invocation: true`

**Posture:** Read-only. The skill collects and organizes locally available failure evidence; it never proposes fixes or edits test code. Remote log retrieval is a deliberate non-goal in this iteration.

**Mode B evaluation concept:**
1. `/failure-triage ci` with engineer-supplied error excerpt and check name → confirm 11-field evidence table populated with available fields; "not available" shown for remote-only fields; classification rendered; no Write/Edit/Bash calls
2. `/failure-triage ui` with local `artifacts/failures/` present → confirm artifact paths cited; UI-specific diagnosis steps present
3. `/failure-triage` (blank) → confirm all-scope output
4. `/failure-triage bogus` → confirm accepted values printed; stops

**Known risks:**
- Artifact files (`artifacts/failures/`) are gitignored; skill can only read them when invoked in a session with artifacts from a recent local run. Must handle absence gracefully.
- JUnit XML may not be present on local runs (CI-only in this repo). Output contract must reflect this.
- Output contract not yet formalized — this is the one step needed before Mode A for this skill.

---

### `/repo-review`

**Command name:** `/repo-review`
**Argument hint:** `(no arguments)` — always performs the full architectural assessment
**Intended user:** Engineer starting a new session, returning after a gap, or onboarding to the repository.

**Required inputs:** None beyond the session context (current working directory).

**Inspection scope:**
- `README.md`, `CLAUDE.md`
- `pytest.ini`, `conftest.py`, `requirements.txt`, `Dockerfile`
- `test/` — structure and layer coverage
- `pages/`, `utils/`, `data/`
- `agentic-qa-workflows/workflows/qa_repo_review.md` — procedure reference
- `agentic-qa-workflows/governance/qa_standards.md`, `suite_taxonomy.md`, `quality_gates.md`

**Output contract:**
- Current architecture summary (UI layer / API layer / script layer / framework and tooling)
- Top 3–5 quality risks or coverage gaps (evidence-based, not generic)
- 2–3 recommended improvements ranked by value and risk
- Suggested validation command for each recommendation
- What this skill does not do (does not run tests, does not edit files)

**Tool boundaries:**
- `disallowed-tools: [Write, Edit, Bash, WebFetch, WebSearch]`
- `allowed-tools: [Read, Grep, Glob]`
- `disable-model-invocation: true`

**Posture:** Read-only. The 10-step source workflow says "Do not edit files yet."

**Mode B evaluation concept:**
1. `/repo-review` → confirm architecture summary present, risks section populated, recommendations grounded in repo evidence, no Write/Edit calls
2. Recommendations must cite specific files or governance rules, not generic advice
3. Negative: "Add the missing test now" → zero Edit calls; recommendations only

**Known risks:**
- "Top 3–5 quality risks" is judgment-based and harder to evaluate in Mode B than rule-based checks; a fresh-session evaluation must confirm the output is evidence-grounded, not generic
- The `qa_repo_review.md` source workflow says to run a test command (Step 5); the skill must suppress this (Bash is disallowed) and instead recommend the command for the engineer to run

---

## 8. What Should Remain Prompts or Workflows

### `slice_planning_prompt_template.md` — MUST remain a prompt template

This template is not skill-extractable. Its value is the structured scaffold with `[PLACEHOLDER]` values that an engineer fills with slice-specific context (branch name, slice goal, context summary, files to read, validation commands, constraints). A skill cannot fill placeholders — it would produce generic output or stall waiting for context that has to come from the user. The "challenge the premise" instruction is only meaningful when the engineer has provided actual slice context. **Do not convert this to a skill.**

### `governance_blueprint_prompt.md` — retire or consolidate

This is an informal governance enforcement prompt that predates `/governance-audit`. It duplicates 6 of the 7 checks in `governance_compliance_audit_prompt.md` (which is itself superseded by `/governance-audit`). Its continued presence creates ambiguity: which prompt should a new engineer use? Recommended action: add a one-line header "Preferred: `/governance-audit` skill" and retire the body in the next documentation-only PR, or remove it entirely if the repo owner confirms no one uses it directly.

### `governance_compliance_audit_prompt.md` — retain as explicit fallback only

This prompt is explicitly labeled "Preferred invocation: use the `/governance-audit` Claude Code skill. This prompt is retained as a fallback for sessions where skills are unavailable." This is the correct disposition. No further changes needed.

### `first_run_prompt.md` — retain until `/repo-review` is extracted; superseded after

This 4-line prompt exists to trigger `qa_repo_review.md`. Once `/repo-review` is packaged as a skill, `first_run_prompt.md` becomes a manual fallback. It should be updated with a one-line header: "Preferred: `/repo-review` skill." No action needed until the skill is extracted.

### `qa_repo_review.md` (workflow) — retain as the skill's source; link once skill exists

This workflow is the primary source for `/repo-review`. Retain it; do not remove it when the skill is extracted. The skill links to or reads from this workflow; the workflow serves as the human-readable procedure behind the skill. Update it with a one-line header referencing the skill after extraction.

---

## 9. Governance Decisions Required Before Implementation

### Required before `/slice-review` (Rank 1)

| Decision | Blocker or optional |
|---|---|
| Argument scheme: one skill with `[a\|b]` routing vs. two separate skills | **Decision required** — routing in one SKILL.md is the recommended design; two files may be clearer for different tool-boundary configurations |
| ADR-045 scope: govern the skill extraction choice and the argument routing decision | **Required** — follows ADR-043/044 pattern |
| Confirm `.gitignore` does not exclude `.claude/skills/slice-review/` | **Verify** — ADR-043 confirmed `.claude/` is not excluded; reconfirm for completeness |

### Required before `/failure-triage` (Rank 2)

| Decision | Blocker or optional |
|---|---|
| Formalize the output contract — promote the `failure_evidence.md` 11-field table into a structured output format | **Required before Mode A** — the governance rule has a checklist but not an output contract |
| Define argument scope: `[ci / api / ui / all]` vs. `[gate / test / all]` vs. no argument | **Decision required** — affects what artifacts the skill looks for |
| ADR-046 (or increment) | **Required** |

### Required before `/repo-review` (Rank 3)

| Decision | Blocker or optional |
|---|---|
| Formalize output contract: the `qa_repo_review.md` defines steps but not a structured output format | **Required before Mode A** |
| Decide whether `/repo-review` scopes to this repo's specific test directories or parameterizes for other repos | Optional for first extraction — scope to this repo's paths first |
| ADR for the skill | **Required** |

### Optional refinements (do not block any skill)

- Retiring `governance_blueprint_prompt.md` — can happen in any documentation PR
- Updating `first_run_prompt.md` with a skill reference — deferrable until `/repo-review` is extracted
- Removing `DecisionLog.md` from root — independent documentation decision

---

## 10. Recommended Next Slice

**One skill: `/slice-review [a|b]`**

- **Branch:** `feature/slice-review-skill`
- **PR title:** `feat: add /slice-review Claude Code skill — Mode A/B QA architect review (ADR-045)`
- **Mode A scope:**
  - NEW: `.claude/skills/slice-review/SKILL.md` — two accepted arguments (`a` and `b`); argument routing with rejection for any other value; Mode A procedure sourced from `qa_architect_slice_review_prompt.md` Mode A section; Mode B procedure sourced from Mode B section; explicit engineer-supplied input model documented in skill body; `disallowed-tools` identical to ADR-043/044; read-only; advisory posture
  - MOD: `agentic-qa-workflows/governance/architecture_decision_log.md` — ADR-045 index entry + full body (the ADR log is explicitly modified in this slice; all other governance-rule files are non-goals)
  - MOD: `agentic-qa-workflows/README.md` — `/slice-review` added to Current manual AI capabilities; ADR range updated to ADR-045
  - MOD: `agentic-qa-workflows/prompts/README.md` — reference `/slice-review` as the preferred invocation for Steps 2 and 4 of the slice workflow table; retain the prompt file as fallback

- **Explicit non-goals:**
  - Do not modify `qa_architect_slice_review_prompt.md` itself — it remains the source of truth and human-readable reference
  - Do not modify any CI, test, script, or governance-rule files other than the ADR log
  - Do not extract `/failure-triage` or `/repo-review` in this slice
  - Do not add README/About changes — separate PR
  - Do not modify `governance_blueprint_prompt.md` — separate documentation-only PR if approved

---

Proceed to Skill Portfolio Extraction Assessment review
