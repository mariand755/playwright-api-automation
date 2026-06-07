import textwrap

import pytest


@pytest.fixture
def clean_junit_xml(tmp_path):
    """JUnit XML with 3 tests, 0 failures."""
    content = textwrap.dedent("""\
        <?xml version="1.0" encoding="utf-8"?>
        <testsuites>
          <testsuite name="pytest" errors="0" failures="0" skipped="0" tests="3" time="1.20">
            <testcase classname="test_a" name="test_one" time="0.40"/>
            <testcase classname="test_a" name="test_two" time="0.40"/>
            <testcase classname="test_a" name="test_three" time="0.40"/>
          </testsuite>
        </testsuites>
    """)
    p = tmp_path / "report.xml"
    p.write_text(content)
    return p


@pytest.fixture
def failing_junit_xml(tmp_path):
    """JUnit XML with 3 tests, 1 failure on test_two."""
    content = textwrap.dedent("""\
        <?xml version="1.0" encoding="utf-8"?>
        <testsuites>
          <testsuite name="pytest" errors="0" failures="1" skipped="0" tests="3" time="1.20">
            <testcase classname="test_a" name="test_one" time="0.40"/>
            <testcase classname="test_a" name="test_two" time="0.40">
              <failure message="AssertionError">assert False</failure>
            </testcase>
            <testcase classname="test_a" name="test_three" time="0.40"/>
          </testsuite>
        </testsuites>
    """)
    p = tmp_path / "report.xml"
    p.write_text(content)
    return p


@pytest.fixture
def malformed_xml_file(tmp_path):
    """File containing invalid XML."""
    p = tmp_path / "bad.xml"
    p.write_text("<<not valid xml>>")
    return p


@pytest.fixture
def clean_test_results():
    """Test results dict matching parse_test_results() output: 3 tests, all passing."""
    return {
        "total": 3,
        "passed": 3,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "duration_secs": 1.20,
        "failed_test_names": [],
        "source": "test/report.xml",
    }


@pytest.fixture
def clean_obs():
    """Observability snapshot with all metrics within thresholds."""
    return {
        "metrics": {
            "production_error_rate_pct": 0.3,
            "p95_latency_ms": 210,
            "p99_latency_ms": 450,
            "recent_incident_count": 0,
        },
        "thresholds": {
            "max_error_rate_pct": 1.0,
            "max_p95_latency_ms": 500,
            "max_p99_latency_ms": 800,
            "max_recent_incident_count": 0,
        },
    }


@pytest.fixture
def clean_defects():
    """Defect metrics with no blockers or escapes."""
    return {
        "metrics": {
            "open_blocker_defects": 0,
            "defect_escape_count": 0,
        }
    }
