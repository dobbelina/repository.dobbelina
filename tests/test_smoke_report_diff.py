from scripts import smoke_report_diff


def make_report(overall, *, list_status="PASS", list_message="10 videos", error=None):
    return {
        "summary": {
            "generated": "2026-03-22T00:00:00",
            "sites_total": 1,
            "pass": 1 if overall == "PASS" else 0,
            "warn": 1 if overall == "WARN" else 0,
            "fail": 1 if overall == "FAIL" else 0,
            "error": 1 if overall == "ERROR" else 0,
            "skip": 1 if overall == "SKIP" else 0,
        },
        "sites": [
            {
                "site": "example",
                "overall": overall,
                "error": error,
                "steps": {
                    "main": {"status": "PASS", "message": "ok"},
                    "list": {"status": list_status, "message": list_message},
                    "play": {"status": "PASS", "message": "ok"},
                },
                "notifications": [],
            }
        ],
    }


def test_compare_reports_detects_new_failure():
    previous = make_report("PASS")
    current = make_report("FAIL", list_status="FAIL", list_message="List returned no videos")

    diff = smoke_report_diff.compare_reports(current, previous)

    assert diff["summary"]["new_failures"] == 1
    assert diff["new_failures"][0]["site"] == "example"
    assert diff["new_failures"][0]["class"] == "PARSER"


def test_compare_reports_detects_resolved_failure():
    previous = make_report("FAIL", list_status="FAIL", list_message="JSONDecodeError: boom")
    current = make_report("PASS")

    diff = smoke_report_diff.compare_reports(current, previous)

    assert diff["summary"]["resolved_failures"] == 1
    assert diff["resolved_failures"][0]["site"] == "example"


def test_compare_reports_detects_step_regression_without_site_failure():
    previous = make_report("PASS", list_status="PASS", list_message="10 videos")
    current = make_report("WARN", list_status="FAIL", list_message="Playback URL resolved")

    diff = smoke_report_diff.compare_reports(current, previous)

    assert diff["summary"]["step_regressions"] == 1
    assert diff["step_regressions"][0]["step"] == "list"


def test_render_markdown_includes_new_failures_section(tmp_path):
    previous = make_report("PASS")
    current = make_report("FAIL", list_status="FAIL", list_message="Connection timed out")
    diff = smoke_report_diff.compare_reports(current, previous)

    current_path = tmp_path / "current.json"
    previous_path = tmp_path / "previous.json"

    markdown = smoke_report_diff.render_markdown(diff, current_path, previous_path)

    assert "## New Failures" in markdown
    assert "example" in markdown
