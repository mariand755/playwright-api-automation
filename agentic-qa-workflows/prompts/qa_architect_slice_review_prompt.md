# QA Architect / Solution Architect Slice Review Prompt

Use this prompt twice per implementation slice:

- **Plan Review (Mode A):** after Claude proposes the implementation plan, before editing files.
- **Implementation Review (Mode B):** after the diff and Docker-first validation results exist, before committing.

---

Read CLAUDE.md and all files under agentic-qa-workflows/governance/.

Then read all files relevant to the current slice (plan document for Mode A; changed files for Mode B).

Act as a QA Architect and Solution Architect reviewer. Do not edit files in either mode.

---

## Context to establish before reviewing

- What slice is this? (name, number, branch)
- What were the stated goals of this slice?
- Which review mode is this? (A — Plan Review, or B — Implementation Review)

---

## Review modes

### Mode A — Plan Review

Use this before editing files. Plan Review should happen after the implementation plan is proposed and before any file changes begin.

Reviewer should evaluate:

- Does the plan match the roadmap slice?
- Is the scope PR-sized?
- Should the work be split into smaller slices?
- Are the right files being touched?
- Are any files missing from the plan?
- Does the plan preserve Docker-first execution?
- Does the plan preserve separation of concerns?
- Does the plan avoid unnecessary dependencies?
- Does the plan avoid future rework (e.g. will it need to be changed when JUnit XML, release gate, or notification delivery is added)?
- Does the plan align with production-style QA architecture and consulting blueprint goals?
- What validation commands should be required after implementation?
- What should be explicitly out of scope for this slice?
- What alternatives were considered for this approach, and why was the chosen approach the best fit?
- What cost, speed, risk, or maintenance benefit does this create?
- What is intentionally deferred, and why is deferral the right call for this slice?
- How would this decision benefit a consulting client or QA architecture team?

### Validation integrity and coverage

- Do the proposed validation commands cover every file the plan touches? A command that tests a subset of changed files does not constitute full validation.
- If the plan edits Python files, `Dockerfile`, or `requirements.txt` (anything copied into the image by `COPY . .`): does the plan require a fresh `docker build` before validation? Or does it rely on a stale image that predates the changes?
- If validation uses a volume-mounted file, such as `-v $(pwd)/file.py:/app/file.py`, is it clearly labeled as a partial check only? Does the plan also require running the relevant command against the fully rebuilt image before the slice is considered done?
- Are any required quality checks CI-only (CodeQL, pip-audit, Trivy)? If yes, does the plan acknowledge these will only run in CI and cannot be validated locally?
- If the plan includes pre-commit as a validation step: is pre-commit clearly labeled as advisory only? Pre-commit does not run CodeQL, pip-audit, or Trivy.
- Does the slice rename any CI job, add or remove required status checks, or modify GitHub Actions workflows in a way that would affect branch protection? If yes, have the required checks in `security_and_branch_protection.md` and GitHub repository settings been updated?

### Security and secret handling

(Applies when the plan touches env vars, credentials, GitHub Secrets, `os.environ` reads, `.env` files, or scripts and modules that handle secret values. Declare N/A if not applicable.)

- Does any planned code read from env vars or GitHub Secrets?
- If yes: could secret variable values flow into any of the following — `print()` calls; `logging` calls; f-strings that reference secret variables; exception messages; CI step summaries; helper function arguments used near logging; CI artifact files such as `release-readiness.json`, HTML reports, or markdown summaries; or tuples, lists, or dictionaries that later feed any logging or print output, even when the final printed value appears to be only a non-secret key or label?
- Does the plan break the taint chain at the variable level, not delegate it to a helper function? A helper function that transforms a secret value is not a CodeQL sanitizer — the taint follows the argument, not the return value.
- What CodeQL findings would this code be likely to generate? See `failure_evidence.md — CodeQL: secret-taint in logging` for the specific patterns.

### Data handling and artifact exposure

(Applies when the slice activates a production data path, extends CI artifact production, or changes what external services receive from this framework. Declare N/A if not applicable.)

- If the slice activates a production data path, extends CI artifact production, or changes what external services receive from this framework: assess whether any artifact, notification, or transmitted data could carry regulated or sensitive information in the client's deployment context. Examples include UI screenshots at failure, HTML dumps, API response excerpts in assertions, observability metrics, JUnit XML, GitHub Step Summary content, Slack/email notifications, and future MCP-routed evidence. If yes, the plan must specify what data could be present, whether masking or redaction is required, the appropriate artifact retention period, and which external services will receive that data.

### Bounded adjacent-risk scan

Scan for risks in files or behaviors adjacent to the slice's changes that the plan does not address — files the implementation might inadvertently affect, or downstream behaviors that depend on files this slice modifies.

- Return at most 3 findings.
- For each finding, state: description, classification, and rationale.
- Classification: **Blocker** (must be resolved before implementation begins; directly affects current slice correctness or safety), **Recommended before commit** (reduces CI surprise risk; should be addressed but does not block plan approval), **Follow-up slice** (real risk but outside current slice scope; document and defer).
- Do not expand implementation scope unless the finding is a Blocker that directly affects current slice correctness or safety.
- Blocker findings must appear in "Required plan changes before implementation." Follow-up slice findings are documented here and do not block plan approval.

Output format for Mode A:

**Verdict**: Approve plan / Approve plan with changes / Rework plan

**Scope assessment**: Is this PR-sized? Should anything be split or deferred?

**File-by-file plan assessment**: For each planned file, does the change belong here? Is it complete? Is anything missing?

**Risks before editing**: What could go wrong if the plan is executed as written?

**Required plan changes before implementation**: Ranked by severity. Each change must include what to modify and why.

**Validation expectations**: List the commands that must pass after implementation before the slice is considered done.

**Validation integrity**: Do the proposed validation commands cover all changed files? Does the plan require a fresh Docker build when image contents change? Are CI-only checks (CodeQL, pip-audit, Trivy) acknowledged as CI-only? Is branch protection or GitHub settings impact addressed?

**Adjacent-risk findings (max 3)**: For each finding: description — classification (Blocker / Recommended before commit / Follow-up slice) — rationale. Blocker findings belong in "Required plan changes before implementation." Follow-up slice findings are documented here and do not block plan approval. If none found: "None identified."

**Trade-offs, benefits, and consulting value**: Answer the following:

- What alternatives were considered?
- Why is the proposed approach the best fit for this slice?
- What cost, speed, risk, or maintenance benefit does this create?
- What is intentionally deferred, and why?
- How would this decision help a consulting client or QA architecture team?

---

### Mode B — Implementation Review

Use this after files have changed and Docker-first validation has run, before committing.

---

## Context to establish before reviewing (Mode B)

- What files changed?

---

## Review dimensions (Mode B)

### 1. Separation of concerns

- API client methods return raw Response objects. No assertions, no parsing inside the client.
- Fixtures own setup and teardown. Tests do not inline setup that belongs in a fixture.
- Tests own behavior assertions. Fixtures do not assert business behavior.
- Page objects own locators, navigation, and `expect()`-based verifications. Tests do not contain raw selectors or direct `expect()` calls on page elements.
- No boundary violations: no HTTP calls in test functions, no selectors in test files.

### 2. Test data design

- All payloads are deterministic. No `random`, `uuid`, or timestamp-based values unless uniqueness is explicitly under test.
- Credentials and URLs come from `test_users.json` via fixtures, not hardcoded in tests.
- Public demo credentials (e.g. Restful Booker admin, SauceDemo standard_user) may live in `test_users.json`. Real secrets must use environment variables.
- If the same payload shape is constructed in 3 or more places, it belongs in a factory fixture.
- Factory fixtures return a callable with named, overridable parameters and deterministic defaults.

### 3. Test isolation and cleanup

- Each test must be independently runnable without depending on state from a previous test.
- If a test creates external state and cleanup is available, it must clean up via fixture teardown or `request.addfinalizer`.
- Teardown failures must be visible. Do not silently swallow delete/cleanup errors. Capture the response and raise a clear error on unexpected status codes.
- Document any known limitation in `DecisionLog.md` when cleanup is genuinely not available.

### 4. Marker and TC-ID quality

- TC-ID comment (`# TC-UI-NNN` or `# TC-API-NNN`) must appear above the pytest marker decorators.
- Every test carries an area marker (`ui` or `api`) and at least one scope marker (`smoke`, `regression`, `negative`, or `api_contract`).
- `@api_contract` is used on any test that calls `jsonschema.validate()`.
- Markers match the suite taxonomy in `suite_taxonomy.md`. If a new marker is introduced, it must be declared in `pytest.ini` first.
- For this repo, smoke and regression are treated as mutually exclusive execution-scope markers so targeted suite counts remain clear:
  - `smoke` = minimum viable sanity checks for PR/commit confidence.
  - `regression` = shipped-feature protection for broader release/nightly confidence.
  - The full suite still runs both smoke and regression tests.

### 5. File organisation and scalability

- Test files are split by domain or workflow, not by marker.
- Do not split a test file prematurely. A single file handling one domain area is correct until it becomes unwieldy.
- Consider splitting when a file grows past roughly 10–12 tests, or when it begins mixing unrelated workflows.
  - UI checkout flow should live in a separate `test_checkout.py` when the checkout slice is added, not in `test_login_cart.py`.
  - API write/auth/delete expansion may justify splitting `test_booking_api.py` into read-focused and write-focused files when the total test count warrants it.
- Page classes follow the same rule: one class per page or major UI section.
- Schema files live in `data/schemas/`. One schema file per response shape.

### 6. CI, reporting, and release-gate readiness

- No change should require CI to be redesigned before JUnit XML, dynamic summary, or release gate can be added.
- New test files must be collected by the existing `testpaths = test` configuration in `pytest.ini`.
- Markers used in the slice must be consistent with the targeted execution commands already defined in `quality_gates.md`.
- If the slice adds fixtures or utilities that produce output files, confirm the output path is within `artifacts/` so Docker volume-mounting works without CI changes.
- Was Docker rebuilt after Python files, `Dockerfile`, or `requirements.txt` were edited? Validation against a stale image that predates the changes does not constitute full validation.
- Was validation run against the fully rebuilt Docker image, not a volume-mounted single-file test? A command like `-v $(pwd)/file.py:/app/file.py` tests that file in isolation and does not prove the rebuilt image passes all checks.
- Was a volume-mounted single-file test used and correctly labeled as partial coverage, with full image validation also confirmed?
- Did the implementation rely on a clean pre-commit run as evidence that Docker CI will pass? Pre-commit is advisory only. It does not run CodeQL, pip-audit, or Trivy.
- If the slice is relevant to CodeQL, pip-audit, or Trivy: are these acknowledged as CI-only checks that cannot be reproduced by local validation?

### 7. Blueprint and consulting value

- Would a consulting team be able to lift this pattern directly and apply it to a different project?
- Are the patterns introduced (factory fixture, yield fixture, addfinalizer teardown, token reuse, scoped locator) documented implicitly by their correct usage?
- Does the slice avoid over-engineering for this project's current scale while still demonstrating production-grade intent?
- Does the slice avoid rework before the next planned phase (JUnit XML, release gate, notification delivery)?

### 8. Risks and recommended fixes

Identify any of the following:

- Brittle assertions tied to third-party demo API behaviour that may change without notice.
- Silent failure paths: missing error messages, bare dict key access that could raise `KeyError`, teardown that swallows exceptions.
- Dead code: unused attributes, unreachable branches, leftover inline setup that a fixture replaced.
- Flakiness vectors: shared mutable state, ordering dependencies, missing `if data:` guards on conditional schema validation.
- Scope creep that should be deferred to a later slice.
- Any reason to split the PR before merging.

### 9. Trade-offs and consulting value

- Were there meaningful alternatives for the approach taken?
- Why is the chosen approach the best fit given project scale and constraints?
- What cost, speed, risk, or maintenance benefit does this implementation create?
- Is anything deferred intentionally, and is the deferral well-reasoned?
- Would a consulting client or QA architecture team find this decision credible and reusable?

### 10. Security and secret hygiene

(Apply when the slice touches env vars, credentials, GitHub Secrets, `os.environ` reads, `.env` files, or any code path that handles secret values. Declare Pass/N/A if not applicable.)

- Do any changed scripts or modules read from env vars or GitHub Secrets?
- If yes: do secret variable values flow — directly or via argument — into any of the following: `print()` calls; `logging` calls; f-strings that reference secret variables; exception messages; CI step summaries; helper function arguments used near logging; CI artifact files such as `release-readiness.json`, HTML reports, or markdown summaries; or as values in tuples, lists, or dictionaries that later feed any logging or print output, even when the final printed value appears to be only a non-secret key or label?
- Is the taint chain broken at the variable level — not delegated to a helper function? A helper function that transforms a secret value is not a CodeQL sanitizer; CodeQL follows the argument, not the return value.
- Are log and print statements using hardcoded status strings (`"configured"`, `"set"`, `"not set"`) derived from truthiness checks (`if secret_var:`) rather than from the secret variable's value?
- Reference: `failure_evidence.md — CodeQL: secret-taint in logging` for the specific patterns CodeQL will flag.
- If the slice produces or extends CI artifacts, or routes data to external services: verify whether any produced artifact or transmitted data could carry regulated or sensitive information in the client's deployment context. If yes, confirm masking/redaction is in place or explicitly deferred with rationale, and confirm artifact retention and external-service exposure are appropriate for the slice. This check applies regardless of whether the credential-handling questions above are applicable — apply whenever the slice produces new CI artifacts or routes data to external services.

### 11. Bounded adjacent-risk scan

Scan for risks in files or behaviors adjacent to the slice's changes that are not covered by the main review dimensions above.

- Return at most 3 findings.
- For each finding, state: description, classification, and rationale.
- Classification: **Blocker** (must be fixed before commit; directly affects current PR correctness or safety), **Recommended before commit** (reduces CI surprise risk; should be addressed but does not block), **Follow-up slice** (real risk but outside current slice scope; document and defer).
- Do not expand review scope or implementation scope beyond what is needed to resolve Blockers.
- Blocker findings belong in "Recommended fixes before commit." Follow-up slice findings belong in "Follow-up slice items from adjacent-risk scan."

---

## Output format (Mode B)

Return the following sections:

**Verdict**: Approve / Approve with fixes / Request changes

**Dimension-by-dimension findings**: Pass or Fail with specific observations for each of the 11 dimensions above. Dimension 10 (Security and secret hygiene) and Dimension 11 (Bounded adjacent-risk scan) follow the same Pass/Fail/N/A format as dimensions 1–9.

**Recommended fixes before commit**: Ranked by severity (High / Medium / Low). For each fix, include the file, what to change, and why. Blocker findings from Dimension 11 belong here.

**Follow-up slice items from adjacent-risk scan**: For each Follow-up slice finding from Dimension 11: description — rationale — suggested slice scope. If none: "None identified." These items do not affect the verdict and do not block commit.

**Blueprint assessment**: One short paragraph on whether this slice moves the repo meaningfully toward the production-style QA architecture blueprint.

**Implementation trade-offs and realized value**: Answer the following:

- Did the implementation preserve the intended trade-offs from the plan?
- Did any new trade-off appear during implementation?
- What benefit does this provide in terms of speed, cost, maintainability, risk reduction, or release confidence?
- Is the benefit clear enough for a future consulting/client reader?

---

## Constraints

Do not edit files in either mode.
Do not commit or push.
Do not create an output report file.
Do not run tests.
