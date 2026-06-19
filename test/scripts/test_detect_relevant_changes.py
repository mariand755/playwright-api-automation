"""Unit tests for scripts/detect_relevant_changes.py classifier logic.

Covers TC-SCRIPT-095 through TC-SCRIPT-113.
Tests target classify_files() directly; main() env-integration tests use
monkeypatch to control GITHUB_EVENT_NAME, GITHUB_REF, BASE_REF.
"""

from __future__ import annotations

import pytest

from scripts.detect_relevant_changes import classify_files, main


# ---------------------------------------------------------------------------
# TC-SCRIPT-095 — API-only test file change
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-095")
def test_tc_script_095_api_only() -> None:
    run_api, run_ui, classification = classify_files(["test/api/test_bookings.py"])
    assert run_api is True
    assert run_ui is False
    assert classification == "api_only"


# ---------------------------------------------------------------------------
# TC-SCRIPT-096 — UI-only test file change
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-096")
def test_tc_script_096_ui_only() -> None:
    run_api, run_ui, classification = classify_files(["test/ui/test_login.py"])
    assert run_api is False
    assert run_ui is True
    assert classification == "ui_only"


# ---------------------------------------------------------------------------
# TC-SCRIPT-097 — Pages-only change
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-097")
def test_tc_script_097_pages_only() -> None:
    run_api, run_ui, classification = classify_files(["pages/login_page.py"])
    assert run_api is False
    assert run_ui is True
    assert classification == "ui_only"


# ---------------------------------------------------------------------------
# TC-SCRIPT-098 — test/scripts/ change only (Docker Test Suite layer)
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-098")
def test_tc_script_098_test_scripts_only() -> None:
    run_api, run_ui, classification = classify_files(
        ["test/scripts/test_release_gate.py"]
    )
    assert run_api is False
    assert run_ui is False
    assert classification == "doc_or_script_only"


# ---------------------------------------------------------------------------
# TC-SCRIPT-099 — Documentation/governance change
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-099")
@pytest.mark.parametrize(
    "path",
    [
        "agentic-qa-workflows/governance/architecture_decision_log.md",
        "README.md",
        "CHANGELOG.md",
        "blueprint/README.md",
    ],
)
def test_tc_script_099_doc_only(path: str) -> None:
    run_api, run_ui, classification = classify_files([path])
    assert run_api is False
    assert run_ui is False


# ---------------------------------------------------------------------------
# TC-SCRIPT-100 — Workflow file change
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-100")
def test_tc_script_100_workflow_file() -> None:
    run_api, run_ui, classification = classify_files([".github/workflows/ci.yml"])
    assert run_api is True
    assert run_ui is True
    assert classification == "shared_prefix"


# ---------------------------------------------------------------------------
# TC-SCRIPT-101 — Shared config file changes (parametrized; SHARED_EXACT)
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-101")
@pytest.mark.parametrize("path", ["requirements.txt", "Dockerfile", "pytest.ini"])
def test_tc_script_101_shared_config(path: str) -> None:
    run_api, run_ui, classification = classify_files([path])
    assert run_api is True
    assert run_ui is True
    assert classification == "shared_exact"


# ---------------------------------------------------------------------------
# TC-SCRIPT-102 — Shared utils/ change
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-102")
def test_tc_script_102_utils_change() -> None:
    run_api, run_ui, classification = classify_files(["utils/helpers.py"])
    assert run_api is True
    assert run_ui is True
    assert classification == "shared_prefix"


# ---------------------------------------------------------------------------
# TC-SCRIPT-103 — conftest.py change (SHARED_EXACT)
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-103")
def test_tc_script_103_conftest() -> None:
    run_api, run_ui, classification = classify_files(["conftest.py"])
    assert run_api is True
    assert run_ui is True
    assert classification == "shared_exact"


# ---------------------------------------------------------------------------
# TC-SCRIPT-104 — Mixed API + UI change
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-104")
def test_tc_script_104_mixed_api_ui() -> None:
    run_api, run_ui, classification = classify_files(
        ["test/api/test_auth.py", "test/ui/test_checkout.py"]
    )
    assert run_api is True
    assert run_ui is True
    assert classification == "api_and_ui"


# ---------------------------------------------------------------------------
# TC-SCRIPT-105 — Mixed API + shared (conftest.py) — SHARED short-circuits
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-105")
def test_tc_script_105_api_plus_shared() -> None:
    run_api, run_ui, classification = classify_files(
        ["test/api/test_auth.py", "conftest.py"]
    )
    assert run_api is True
    assert run_ui is True
    assert classification == "shared_exact"


# ---------------------------------------------------------------------------
# TC-SCRIPT-106 — Unknown/unclassified path → conservative fallback
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-106")
def test_tc_script_106_unknown_path() -> None:
    run_api, run_ui, classification = classify_files(["some/unknown/new_file.py"])
    assert run_api is True
    assert run_ui is True
    assert classification == "unknown_path"


# ---------------------------------------------------------------------------
# TC-SCRIPT-107 — Empty changed file list → conservative fallback
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-107")
def test_tc_script_107_empty_changed_files() -> None:
    run_api, run_ui, classification = classify_files([])
    assert run_api is True
    assert run_ui is True
    assert classification == "classifier_error_no_changed_files"


# ---------------------------------------------------------------------------
# TC-SCRIPT-108 — Missing BASE_REF → conservative fallback (main() level)
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-108")
def test_tc_script_108_missing_base_ref(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.Path
) -> None:
    output_file = tmp_path / "github_output"
    output_file.write_text("")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/feature/new-thing")
    monkeypatch.setenv("BASE_REF", "")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0

    outputs = dict(
        line.split("=", 1)
        for line in output_file.read_text().splitlines()
        if "=" in line
    )
    assert outputs["run_api"] == "true"
    assert outputs["run_ui"] == "true"
    assert outputs["classification"] == "classifier_error_missing_base_ref"


# ---------------------------------------------------------------------------
# TC-SCRIPT-109 — Bypass events (parametrized)
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-109")
@pytest.mark.parametrize(
    "event_name,ref",
    [
        ("push", "refs/heads/main"),
        ("schedule", "refs/heads/main"),
        ("workflow_dispatch", "refs/heads/main"),
        ("workflow_dispatch", "refs/heads/feature/foo"),
    ],
)
def test_tc_script_109_bypass_events(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pytest.Path,
    event_name: str,
    ref: str,
) -> None:
    output_file = tmp_path / "github_output"
    output_file.write_text("")
    monkeypatch.setenv("GITHUB_EVENT_NAME", event_name)
    monkeypatch.setenv("GITHUB_REF", ref)
    monkeypatch.setenv("BASE_REF", "abc123def456")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0

    outputs = dict(
        line.split("=", 1)
        for line in output_file.read_text().splitlines()
        if "=" in line
    )
    assert outputs["run_api"] == "true"
    assert outputs["run_ui"] == "true"
    assert outputs["classification"] == "bypass_change_detection_event"


# ---------------------------------------------------------------------------
# TC-SCRIPT-110 — Named CI-control scripts → SHARED_EXACT (parametrized)
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-110")
@pytest.mark.parametrize(
    "path",
    [
        "scripts/detect_relevant_changes.py",
        "scripts/release_gate.py",
        "scripts/notify.py",
        "scripts/cloud_grid_preflight.py",
        "scripts/ci_summary.py",
    ],
)
def test_tc_script_110_named_ci_scripts(path: str) -> None:
    run_api, run_ui, classification = classify_files([path])
    assert run_api is True
    assert run_ui is True
    assert classification == "shared_exact"


# ---------------------------------------------------------------------------
# TC-SCRIPT-111 — Unknown scripts/ file not in SHARED_EXACT → conservative fallback
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-111")
def test_tc_script_111_unknown_scripts_path() -> None:
    run_api, run_ui, classification = classify_files(["scripts/some_new_helper.py"])
    assert run_api is True
    assert run_ui is True
    assert classification == "unknown_scripts_path"


# ---------------------------------------------------------------------------
# TC-SCRIPT-112 — Non-Markdown ci/ file → conservative fallback
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-112")
def test_tc_script_112_non_md_ci_file() -> None:
    run_api, run_ui, classification = classify_files(["ci/jenkins/Jenkinsfile"])
    assert run_api is True
    assert run_ui is True
    assert classification == "unknown_ci_path"


# ---------------------------------------------------------------------------
# TC-SCRIPT-113 — test/api/README.md → doc-only (Markdown rule before API-path rule)
# ---------------------------------------------------------------------------
@pytest.mark.scripts
@pytest.mark.tc_id("TC-SCRIPT-113")
def test_tc_script_113_api_readme_is_doc_only() -> None:
    run_api, run_ui, classification = classify_files(["test/api/README.md"])
    assert run_api is False
    assert run_ui is False
    assert classification == "doc_or_script_only"
