Read governance, audit current repo for violations/gaps, recommend smallest safe fixes.

Read CLAUDE.md and all files under agentic-qa-workflows/governance/.

Then audit the current repository against the governance rules. Do not edit files yet.

I want you to:

1. Check current tests against qa_standards.md.
2. Check marker usage against suite_taxonomy.md.
3. Check Page Object and API client boundaries against page_object_api_rules.md.
4. Check test data and environment usage against test_data_env_rules.md.
5. Check failure evidence behavior against failure_evidence.md.
6. Check current repo state against quality_gates.md.
7. Check whether future agentic edits would be guided correctly by agentic_workflow_rules.md.

Return:

- Governance areas that already comply
- Top 2–3 governance gaps
- Smallest safe fix for each gap
- Suggested order of fixes
- Exact test command to run after each fix

Do not edit test code.
Do not create files.
Do not commit or push.
