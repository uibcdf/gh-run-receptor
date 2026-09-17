from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate-capture-policy.yml"


def test_capture_policy_workflow_is_manual_bounded_and_least_privilege():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert source.count("workflow_dispatch:") == 1
    assert "push:" not in source
    assert "pull_request:" not in source
    assert "permissions: {}" in source
    assert "actions: read" in source
    assert "contents: read" in source
    assert "timeout-minutes: 10" in source
    assert "cancel-in-progress: false" in source
    assert "persist-credentials: false" in source
    assert "upload-artifact" not in source


def test_capture_policy_workflow_requires_both_paired_outcomes():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert source.count("--capture adaptive") == 2
    assert source.count("--capture full") == 2
    assert "--require-paired-success --require-paired-non-success" in source
    assert "tests/fixtures/bundles" in source


def test_capture_policy_workflow_pins_every_external_action():
    source = WORKFLOW.read_text(encoding="utf-8")
    actions = [
        line.strip().removeprefix("- ").removeprefix("uses: ")
        for line in source.splitlines()
        if "uses:" in line
    ]

    assert actions == [
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7",
        "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7",
    ]
