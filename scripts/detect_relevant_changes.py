"""Classify changed files to determine which CI test suites are relevant.

Outputs run_api and run_ui (true/false) for GitHub Actions downstream jobs.
Fail-closed: unknown paths, empty diffs, git errors, and bypass events all
default to run_api=true, run_ui=true.
"""

from __future__ import annotations

import os
import subprocess
import sys

# Exact-match shared paths — always run API and UI.
# Single files use exact match to avoid false positives (e.g. Dockerfile.notes).
SHARED_EXACT: frozenset[str] = frozenset(
    [
        # CI control-plane scripts — must never self-suppress
        "scripts/detect_relevant_changes.py",
        "scripts/release_gate.py",
        "scripts/notify.py",
        "scripts/cloud_grid_preflight.py",
        "scripts/ci_summary.py",
        # Shared single-file config
        "Dockerfile",
        "requirements.txt",
        "pytest.ini",
        "conftest.py",
    ]
)

# Prefix-match shared directories — always run API and UI
SHARED_PREFIX: frozenset[str] = frozenset(
    [
        ".github/workflows/",
        "utils/",
        "data/",
    ]
)

# API-only path prefixes
API_ONLY: frozenset[str] = frozenset(["test/api/"])

# UI-only path prefixes
UI_ONLY: frozenset[str] = frozenset(["test/ui/", "pages/"])

# Script-test-only paths — Docker Test Suite already exercises these; API/UI not needed
SCRIPT_TEST_ONLY: frozenset[str] = frozenset(["test/scripts/"])

# Documentation-only path prefixes — no test contribution
DOC_ONLY: frozenset[str] = frozenset(
    [
        "agentic-qa-workflows/",
        "blueprint/",
    ]
)

# scripts/ prefix (beyond named SHARED_EXACT entries) → UNKNOWN → conservative fallback
_SCRIPTS_PREFIX = "scripts/"

# ci/ prefix (non-.md files) → UNKNOWN → conservative fallback
_CI_PREFIX = "ci/"


def classify_files(changed_files: list[str]) -> tuple[bool, bool, str]:
    """Return (run_api, run_ui, classification) for a list of changed file paths.

    Uses explicit ordered precedence — first matching rule wins per file.
    Short-circuits to (True, True) as soon as any shared path is detected.
    """
    if not changed_files:
        return True, True, "classifier_error_no_changed_files"

    api_touched = False
    ui_touched = False

    for path in changed_files:
        # Rule 1: SHARED_EXACT — exact filename match
        if path in SHARED_EXACT:
            return True, True, "shared_exact"

        # Rule 2: SHARED_PREFIX — path starts with a shared directory
        if any(path.startswith(prefix) for prefix in SHARED_PREFIX):
            return True, True, "shared_prefix"

        # Rule 3: Markdown suffix — doc-only regardless of directory
        # Evaluated before API/UI rules so test/api/README.md → doc-only, not API
        if path.endswith(".md"):
            continue

        # Rule 4: DOC_ONLY prefix — explicit documentation directories
        if any(path.startswith(prefix) for prefix in DOC_ONLY):
            continue

        # Rule 5: ci/ prefix (non-.md already filtered by rule 3) → UNKNOWN → conservative
        if path.startswith(_CI_PREFIX):
            return True, True, "unknown_ci_path"

        # Rule 6: API_ONLY prefix
        if any(path.startswith(prefix) for prefix in API_ONLY):
            api_touched = True
            continue

        # Rule 7: UI_ONLY prefix
        if any(path.startswith(prefix) for prefix in UI_ONLY):
            ui_touched = True
            continue

        # Rule 8: SCRIPT_TEST_ONLY — test/scripts/ only; Docker Test Suite covers this layer
        if any(path.startswith(prefix) for prefix in SCRIPT_TEST_ONLY):
            continue

        # Rule 9: scripts/ not in SHARED_EXACT → UNKNOWN → conservative
        if path.startswith(_SCRIPTS_PREFIX):
            return True, True, "unknown_scripts_path"

        # Rule 10: No match → UNKNOWN → conservative
        return True, True, "unknown_path"

    if api_touched and ui_touched:
        classification = "api_and_ui"
    elif api_touched:
        classification = "api_only"
    elif ui_touched:
        classification = "ui_only"
    else:
        classification = "doc_or_script_only"

    return api_touched, ui_touched, classification


def write_output(key: str, value: str) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"{key}={value}\n")
    else:
        print(f"OUTPUT: {key}={value}")


def main() -> None:
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    ref = os.environ.get("GITHUB_REF", "")

    # Bypass events — classification is skipped entirely
    if event in ("schedule", "workflow_dispatch") or (
        event == "push" and ref == "refs/heads/main"
    ):
        write_output("run_api", "true")
        write_output("run_ui", "true")
        write_output("classification", "bypass_change_detection_event")
        sys.exit(0)

    base_sha = os.environ.get("BASE_SHA", "").strip()

    # First push to a new branch — github.event.before is all zeros
    if base_sha == "0000000000000000000000000000000000000000" or not base_sha:
        write_output("run_api", "true")
        write_output("run_ui", "true")
        write_output("classification", "classifier_error_null_base_sha")
        sys.exit(0)

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_sha, "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        changed_files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except Exception:
        write_output("run_api", "true")
        write_output("run_ui", "true")
        write_output("classification", "classifier_error_git_diff_failed")
        sys.exit(0)

    run_api, run_ui, classification = classify_files(changed_files)

    write_output("run_api", "true" if run_api else "false")
    write_output("run_ui", "true" if run_ui else "false")
    write_output("classification", classification)


if __name__ == "__main__":
    main()
