from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_distributed_action_validation_is_manual_bounded_and_cross_platform():
    source = (
        ROOT / ".github/workflows/action-distribution-validation.yml"
    ).read_text(encoding="utf-8")

    assert source.count("workflow_dispatch:") == 1
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert "timeout-minutes: 10" in source
    assert "fail-fast: false" in source
    assert "os: [ubuntu-latest, macos-latest, windows-latest]" in source
    assert "uses: uibcdf/gh-run-receptor@074c01349034d3374ca270be2cf3768cc0e0bfae" in source
    assert 'assert os.environ["ASSESSMENT"] == "PASS"' in source
    assert '"ref": "074c01349034d3374ca270be2cf3768cc0e0bfae"' in source


def test_distributed_action_validation_uses_only_read_permissions():
    source = (
        ROOT / ".github/workflows/action-distribution-validation.yml"
    ).read_text(encoding="utf-8")

    assert "permissions:\n  actions: read\n  contents: read" in source
