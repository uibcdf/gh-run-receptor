from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/minimum-gh-cli-validation.yml"


def _source():
    return WORKFLOW.read_text(encoding="utf-8")


def test_minimum_cli_gate_is_manual_linux_only_and_bounded():
    source = _source()

    assert source.count("workflow_dispatch:") == 1
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert "runs-on: ubuntu-latest" in source
    assert "timeout-minutes: 10" in source
    assert "GH_VERSION: 2.48.0" in source


def test_minimum_cli_gate_pins_archive_release_and_checksum():
    source = _source()

    assert "actions/checkout" not in source
    assert "releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_amd64.tar.gz" in source
    assert "1c477e2562aca8679b0219569f0482f1975de76daca8ba307892c1787338a28d" in source
    assert "sha256sum --check --strict" in source
    assert 'test "$(gh --version | sed -n \'1p\')" = "gh version 2.48.0 (2024-04-17)"' in source


def test_minimum_cli_gate_installs_the_extension_and_exercises_remote_pagination():
    source = _source()

    assert "gh extension install uibcdf/gh-run-receptor --pin 0.17.0" in source
    assert 'test "$(gh run-receptor --version)" = "0.17.0"' in source
    assert "inspect 34037657805 --profile=ci --capture=metadata" in source
    assert "report['github']['conclusion'] == 'success'" in source
    assert "report['receptor']['assessment'] == 'PASS'" in source
