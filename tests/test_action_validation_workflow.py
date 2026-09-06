import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_action_validation_is_manual_bounded_and_cross_platform():
    source = (ROOT / ".github/workflows/action-validation.yml").read_text(encoding="utf-8")

    assert source.count("workflow_dispatch:") == 1
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert "\n  schedule:" not in source
    assert "actions: read\n  contents: read" in source
    assert "fail-fast: false" in source
    assert "timeout-minutes: 15" in source
    assert "os: [ubuntu-latest, macos-latest, windows-latest]" in source
    assert "gh extension install ." in source
    assert "GH_TOKEN: ${{ github.token }}" in source
    assert source.count("uses: ./") == 3
    assert 'assert os.environ["ASSESSMENT"] == "PASS"' in source
    assert 'assert os.environ["ASSESSMENT"] == "PENDING"' in source
    assert 'assert os.environ["ASSESSMENT"] == "FAIL"' in source


def test_action_validation_pins_every_external_action():
    source = (ROOT / ".github/workflows/action-validation.yml").read_text(encoding="utf-8")
    external = [
        line.strip().removeprefix("uses: ")
        for line in source.splitlines()
        if "uses:" in line and "uses: ./" not in line
    ]

    assert external == [
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7"
    ]
    assert re.fullmatch(r"[^@]+@[0-9a-f]{40} # v[0-9]+", external[0])
