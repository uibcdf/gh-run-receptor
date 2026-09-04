"""Compact, truth-preserving reports for GitHub Actions runs."""

from importlib.metadata import PackageNotFoundError, version

from gh_run_receptor.source_version import version_from_source_checkout

__version__ = version_from_source_checkout()
if __version__ is None:
    try:
        from gh_run_receptor._version import __version__
    except ImportError:
        try:
            __version__ = version("gh-run-receptor")
        except PackageNotFoundError:
            __version__ = "0+unknown"
