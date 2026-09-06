import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _source():
    return (
        ROOT / ".github/workflows/published-report-validation.yml"
    ).read_text(encoding="utf-8")


def test_published_report_validation_is_manual_bounded_and_cross_platform():
    source = _source()

    assert source.count("workflow_dispatch:") == 1
    assert "source-run:" in source
    assert "required: true" in source
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert "permissions:\n  actions: read\n  contents: read" in source
    assert "timeout-minutes: 10" in source
    assert "fail-fast: false" in source
    assert "os: [ubuntu-latest, macos-latest, windows-latest]" in source
    assert '"published"' in source
    assert '"34045953527"' in source
    assert '"terminal-source-report"' in source
    assert 'report["subject"]["run_id"] == 34045930131' in source
    assert 'report["consumer_verification"]["source_facts"] == "verified"' in source
    assert '"published-source"' in source
    assert "SOURCE_RUN_ID: ${{ inputs['source-run'] }}" in source
    assert 'report["subject"]["run_id"] == int(os.environ["SOURCE_RUN_ID"])' in source


def test_published_report_validation_pins_external_actions():
    external = [
        line.strip().removeprefix("uses: ")
        for line in _source().splitlines()
        if "uses:" in line
    ]

    assert external == [
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7"
    ]
    assert re.fullmatch(r"[^@]+@[0-9a-f]{40} # v[0-9]+", external[0])
