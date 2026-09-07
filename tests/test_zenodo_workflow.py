from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/verify-zenodo-release.yml"


def test_zenodo_gate_is_manual_read_only_and_bounded():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert source.count("workflow_dispatch:") == 1
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert "permissions:\n  contents: read" in source
    assert "timeout-minutes: 5" in source
    assert "GH_TOKEN" not in source


def test_zenodo_gate_uses_public_bounded_acquisition_and_semantic_verifier():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "https://zenodo.org/api/records/" in source
    assert "--data 'all_versions=true' --data 'size=25'" in source
    assert 'release_tools.py zenodo "$RELEASE_VERSION"' in source
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7" in source
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7" in source
