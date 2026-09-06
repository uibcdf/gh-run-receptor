from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _source():
    return (
        ROOT / ".github/workflows/workflow-run-report-validation.yml"
    ).read_text(encoding="utf-8")


def test_terminal_report_listener_has_a_narrow_completed_run_trigger():
    source = _source()

    assert "workflow_run:" in source
    assert "workflows: [Distributed Action validation]" in source
    assert "types: [completed]" in source
    assert "workflow_dispatch:" not in source
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source


def test_terminal_report_listener_is_read_only_and_executes_no_source_content():
    source = _source()

    assert "permissions:\n  actions: read\n  contents: read" in source
    assert "actions/checkout" not in source
    assert "download-artifact" not in source
    assert "github.event.workflow_run.head_sha" not in source
    assert "timeout-minutes: 10" in source


def test_terminal_report_listener_preserves_event_identity_and_conclusion():
    source = _source()

    assert "uses: uibcdf/gh-run-receptor@0.12.0" in source
    assert "run-id: ${{ github.event.workflow_run.id }}" in source
    assert "SOURCE_CONCLUSION: ${{ github.event.workflow_run.conclusion }}" in source
    assert "SOURCE_RUN_ID: ${{ github.event.workflow_run.id }}" in source
    assert 'report["subject"]["run_id"] == int(os.environ["SOURCE_RUN_ID"])' in source
    assert 'report["github"]["status"] == "completed"' in source
    assert 'os.environ["CONCLUSION"] == os.environ["SOURCE_CONCLUSION"]' in source
