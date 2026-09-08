"""Testing the same-revision reusable reporting workflow contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REUSABLE = ROOT / ".github/workflows/reusable-report.yml"
VALIDATION = ROOT / ".github/workflows/validate-reusable-report.yml"


def test_reusable_report_is_call_only_read_only_and_bounded():
    source = REUSABLE.read_text(encoding="utf-8")

    assert source.count("workflow_call:") == 1
    assert "workflow_dispatch:" not in source
    assert "workflow_run:" not in source
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert "permissions:\n  actions: read\n  contents: read" in source
    assert "runs-on: ubuntu-latest" in source
    assert "timeout-minutes: 10" in source


def test_reusable_report_uses_the_action_from_its_exact_own_revision():
    source = REUSABLE.read_text(encoding="utf-8")

    assert "uses: $/." in source
    assert "uses: uibcdf/gh-run-receptor@" not in source
    assert "actions/checkout" not in source
    assert source.count("uses:") == 1


def test_reusable_report_forwards_every_input_once():
    source = REUSABLE.read_text(encoding="utf-8")
    names = ("repository", "profile", "capture", "rules")

    for name in names:
        assert source.count(f"          {name}: ${{{{ inputs.{name} }}}}") == 1
    for name in ("run-id", "report-name", "strict-reporter"):
        assert source.count(f"          {name}: ${{{{ inputs['{name}'] }}}}") == 1


def test_reusable_outputs_cross_only_durable_job_boundaries():
    source = REUSABLE.read_text(encoding="utf-8")
    durable = (
        "assessment",
        "github-conclusion",
        "profile",
        "failed-groups",
        "incomplete-groups",
        "report-artifact",
        "report-ready",
        "error-category",
    )

    for name in ("assessment", "profile"):
        assert f"value: ${{{{ jobs.report.outputs.{name} }}}}" in source
        assert f"{name}: ${{{{ steps.receptor.outputs.{name} }}}}" in source
    for name in set(durable) - {"assessment", "profile"}:
        assert f"value: ${{{{ jobs.report.outputs['{name}'] }}}}" in source
        assert f"{name}: ${{{{ steps.receptor.outputs['{name}'] }}}}" in source
    assert "report-path" not in source


def test_remote_distribution_gate_is_manual_and_checks_called_outputs():
    source = VALIDATION.read_text(encoding="utf-8")

    assert source.count("workflow_dispatch:") == 1
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert "permissions:\n  actions: read\n  contents: read" in source
    assert "uibcdf/gh-run-receptor/.github/workflows/reusable-report.yml@main" in source
    assert 'run-id: "34037657805"' in source
    assert "strict-reporter: true" in source
    assert "needs: report" in source
    assert 'os.environ["REPORT_READY"] == "true"' in source
    assert "gh-run-receptor-reusable-34037657805-1" in source
    assert 'gh run download "$GITHUB_RUN_ID"' in source
    assert "EXPECTED_SHA: ${{ github.sha }}" in source
    assert "report['publisher'] ==" in source
    assert "'ref': os.environ['EXPECTED_SHA']" in source
