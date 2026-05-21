# QA Repo Review Workflow

Use this workflow when asked to review the automation framework for quality, coverage, maintainability, or risk.

## Steps

1. Read README.md.
2. Inspect pytest.ini, conftest.py, requirements.txt, Dockerfile, test/, pages/, utils/, and data/.
3. Identify the current UI and API coverage.
4. Identify the highest-risk missing coverage.
5. Run the relevant test command.
6. If tests fail, diagnose before changing anything.
7. Recommend no more than 3 improvements.
8. If asked to implement, make one focused change at a time.
9. Re-run the smallest relevant test command.
10. Produce a QA summary with:
   - What was reviewed
   - What passed
   - What failed
   - Risks found
   - Recommended next step