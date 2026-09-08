from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/publish-release.yml"


def _source() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_release_workflow_is_manual_bounded_and_has_one_writer():
    source = _source()

    assert source.count("workflow_dispatch:") == 1
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert "permissions:\n  contents: write" in source
    assert source.count("runs-on:") == 1
    assert "timeout-minutes: 15" in source
    assert "cancel-in-progress: false" in source


def test_release_workflow_checks_exact_tag_before_building():
    source = _source()

    assert "persist-credentials: false" in source
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7" in source
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7" in source
    assert "ref: ${{ inputs.tag }}" in source
    assert "^[0-9]+\\.[0-9]+\\.[0-9]+$" in source
    assert 'test "$GITHUB_REF" = "refs/tags/$RELEASE_TAG"' in source
    assert 'git tag --points-at HEAD --list "$RELEASE_TAG"' in source
    assert 'git rev-list -n 1 "$RELEASE_TAG"' in source
    assert "python -m pytest --receptor=llm" in source
    assert "validate_contracts.py --baseline 0.19.0" in source
    assert "python -m build" in source


def test_release_workflow_verifies_draft_before_publication_and_rechecks_public_state():
    source = _source()
    draft = source.index("--state draft")
    publish = source.index("--draft=false")
    published = source.index("--state published")

    assert "gh release create" in source
    assert "--draft --verify-tag" in source
    assert "--json databaseId --jq .databaseId" in source
    assert 'gh api "repos/$GITHUB_REPOSITORY/releases/$release_id"' in source
    assert draft < publish < published
    assert "release_tools.py manifest" in source
    assert "release_tools.py citation" in source
    assert "release_tools.py notes" in source
