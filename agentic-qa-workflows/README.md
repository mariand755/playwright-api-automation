# Agentic QA Workflows
This folder documents the QA governance, prompts, and repeatable AI-assisted workflows used for this Playwright + API automation framework.

## Purpose
The goal is to make AI-assisted QA work controlled, reviewable, and repeatable.

Instead of allowing an AI coding assistant to edit tests directly, this repo defines:
- governance rules
- prompt templates
- workflow checklists
- output expectations
- quality gates

## Folder Structure
```text
agentic-qa-workflows/
├── governance/   # QA standards and quality rules
├── prompts/      # Reusable prompts for Claude Code or other AI coding tools
├── workflows/    # Step-by-step QA workflows
└── outputs/      # Generated reports and review outputs
```

## How to Use These Workflows
1. Read CLAUDE.md for project-level instructions.
2. Review the relevant governance files under agentic-qa-workflows/governance/.
3. Choose the right prompt from agentic-qa-workflows/prompts/.
4. Run the prompt in Plan mode first when using an AI coding assistant.
5. Review the proposed plan before allowing edits.
6. Make one focused change at a time.
7. Run the smallest relevant test command.
8. Produce a QA summary.
9. Save output files only for audits, triage reports, release/readiness reviews, CI evidence, or significant multi-file changes.

## Governance Files
- qa_standards.md
- suite_taxonomy.md
- page_object_api_rules.md
- test_data_env_rules.md
- failure_evidence.md
- quality_gates.md
- agentic_workflow_rules.md

## Design Principle
AI can assist with analysis, test design, and implementation, but governance controls the workflow.
