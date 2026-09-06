from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/inline-rules-pr-boundary.yml"
PIN = "09c164a4cac2187068d8058b630a92a049486a1d"


def test_pull_request_boundary_is_narrow_bounded_and_exactly_pinned():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert source.count("pull_request:") == 1
    assert "\n  push:" not in source
    assert "workflow_dispatch:" not in source
    assert "types: [opened, synchronize, reopened]" in source
    assert ".github/gh-run-receptor-pr-boundary-probe" in source
    assert "timeout-minutes: 10" in source
    assert f"uses: uibcdf/gh-run-receptor@{PIN}" in source


def test_pull_request_boundary_requires_rejection_before_report_creation():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "rules: |" in source
    assert 'test "$REPORT_READY" = "false"' in source
    assert 'test "$ERROR_CATEGORY" = "untrusted_inline_rules"' in source
    assert 'test -z "$REPORT_PATH"' in source
    assert "strict-reporter:" not in source
