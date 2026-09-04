"""Testing source-checkout version fallback for the GitHub CLI extension."""

import re
import subprocess
import sys
from pathlib import Path

from gh_run_receptor.source_version import parse_git_describe, version_from_source_checkout

ROOT = Path(__file__).resolve().parents[1]


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
    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:\+[0-9]+\.g[0-9a-f]+(?:\.dirty)?)?", version)


def test_source_launcher_does_not_borrow_installed_distribution_version():
    expected = version_from_source_checkout()

    result = subprocess.run(
        [sys.executable, str(ROOT / "gh-run-receptor"), "--version"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == expected
