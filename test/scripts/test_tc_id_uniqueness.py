"""TC-ID uniqueness guard for the full test suite.

Covers TC-SCRIPT-031.
Scans test/**/*.py for @pytest.mark.tc_id("TC-...") decorators and fails
if any TC-ID appears in more than one location.
"""

import re
from pathlib import Path

import pytest


# TC-SCRIPT-031 — no duplicate tc_id markers across the test suite
@pytest.mark.scripts
@pytest.mark.regression
@pytest.mark.tc_id("TC-SCRIPT-031")
def test_no_duplicate_tc_ids():
    pattern = re.compile(r'^@pytest\.mark\.tc_id\("(TC-[^"]+)"\)')
    seen: dict[str, list[str]] = {}

    test_root = Path(__file__).parent.parent
    for path in sorted(test_root.rglob("*.py")):
        rel = str(path.relative_to(test_root.parent))
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = pattern.match(raw.strip())
            if match:
                tc_id = match.group(1)
                seen.setdefault(tc_id, []).append(f"{rel}:{lineno}")

    duplicates = {tc_id: locs for tc_id, locs in seen.items() if len(locs) > 1}

    if duplicates:
        lines = ["Duplicate TC IDs found:"]
        for tc_id, locs in sorted(duplicates.items()):
            lines.append(f"  {tc_id}:")
            for loc in locs:
                lines.append(f"    - {loc}")
        pytest.fail("\n".join(lines))
