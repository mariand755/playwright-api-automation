Read CLAUDE.md and all files under agentic-qa-workflows/governance/.

Then act as a QA governance enforcer for this repo. Do not edit files yet.

I want you to:
1. Confirm naming conventions are followed across test/, pages/, utils/, and data/.
2. Verify each test is tagged to the correct suite marker (smoke, api, negative, regression).
3. Check that POM and API client rules are respected — no selectors or HTTP calls in test files.
4. Confirm all URLs and credentials come from test data, not hardcoded values.
5. Verify failure evidence artifacts are wired up for all UI tests.
6. Assess whether the current suite meets the PR, merge, and release quality gates.
7. Identify the top 2–3 governance violations or gaps, and recommend the smallest safe fix for each.
8. Tell me which test command to run to verify compliance.

Do not edit test code yet.
Do not create files yet.
Do not commit or push.