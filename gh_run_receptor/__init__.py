"""Compact, truth-preserving reports for GitHub Actions runs."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("gh-run-receptor")
except PackageNotFoundError:
    try:
        from gh_run_receptor._version import __version__
    except ImportError:
        __version__ = "0+unknown"
