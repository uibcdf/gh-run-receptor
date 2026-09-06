from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/permission-boundary-validation.yml"
PIN = "09c164a4cac2187068d8058b630a92a049486a1d"


def test_permission_boundary_probe_is_manual_bounded_and_exactly_pinned():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert source.count("workflow_dispatch:") == 1
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert source.count("timeout-minutes: 10") == 3
    assert source.count(f"uses: uibcdf/gh-run-receptor@{PIN}") == 3
    assert 'run-id: "34037657805"' in source


def test_permission_boundary_probe_removes_one_scope_at_a_time():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "permissions: {}" in source
    assert source.count("      actions: read") == 2
    assert source.count("      contents: read") == 2
    assert "Minimum documented permissions" in source
    assert "Verify public run without actions read" in source
    assert "Verify public run without contents read" in source
    assert source.count('test "$REPORT_READY" = "true"') == 2
    assert source.count('test -z "$ERROR_CATEGORY"') == 2


def test_minimum_permission_case_asserts_inline_source_provenance():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "rules: |" in source
    assert "profile: auto" in source
    assert 'assert os.environ["REPORT_READY"] == "true"' in source
    assert 'assert os.environ["ERROR_CATEGORY"] == ""' in source
    assert 'assert source["kind"] == "action_inline"' in source
    assert (
        'assert source["path"] == ".github/workflows/permission-boundary-validation.yml"' in source
    )
