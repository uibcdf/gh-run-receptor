"""Testing source-checkout version fallback for the GitHub CLI extension."""

from gh_run_receptor.source_version import parse_git_describe, version_from_source_checkout


def test_exact_clean_tag_is_the_release_version():
    assert parse_git_describe("0.2.1-0-g1234abc") == "0.2.1"


def test_commit_distance_and_dirty_state_are_pep440_local_versions():
    assert parse_git_describe("0.2.0-3-g1234abc") == "0.2.0+3.g1234abc"
    assert parse_git_describe("0.2.0-0-g1234abc-dirty") == "0.2.0+0.g1234abc.dirty"


def test_unrecognized_tag_is_not_reported_as_a_version():
    assert parse_git_describe("release-0.2.0-1-g1234abc") is None


def test_repository_checkout_has_a_source_version():
    version = version_from_source_checkout()

    assert version is not None
    assert version.startswith("0.2.0")
