from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_compatibility_workflow_is_manual_bounded_and_complete():
    workflow = ROOT / ".github/workflows/compatibility.yml"
    source = workflow.read_text(encoding="utf-8")

    assert source.count("workflow_dispatch:") == 1
    assert "\n  push:" not in source
    assert "\n  schedule:" not in source
    assert "\n  pull_request:" not in source
    assert "permissions:\n  contents: read" in source
    assert "fail-fast: false" in source
    assert "timeout-minutes: 15" in source
    assert source.count("os: ubuntu-latest") == 3
    assert source.count("os: macos-latest") == 3
    assert source.count("os: windows-latest") == 3
    for python in ("3.11", "3.12", "3.13"):
        assert source.count(f'python: "{python}"') == 3
    assert "python -m pytest --receptor=llm" in source
    assert "python -m build" in source
    assert "working-directory: ${{ runner.temp }}" in source
    assert "0+unknown" in source


def test_compatibility_workflow_pins_every_external_action():
    source = (ROOT / ".github/workflows/compatibility.yml").read_text(encoding="utf-8")
    action_lines = [line.strip() for line in source.splitlines() if "uses:" in line]

    assert action_lines == [
        "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7",
        "uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7",
    ]


def test_byte_exact_fixtures_are_checked_out_with_lf_on_every_platform():
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")

    assert "tests/fixtures/** text eol=lf" in attributes.splitlines()
