"""Compact, truth-preserving reports for GitHub Actions runs."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("gh-run-receptor")
except PackageNotFoundError:
    try:
        from gh_run_receptor._version import __version__
    except ImportError:
        from gh_run_receptor.source_version import version_from_source_checkout

        __version__ = version_from_source_checkout() or "0+unknown"
