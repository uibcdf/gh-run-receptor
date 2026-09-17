"""Configuring the public gh-run-receptor documentation."""

from __future__ import annotations

project = "gh-run-receptor"
copyright = "2026, UIBCDF Lab"
author = "UIBCDF Lab"

try:
    from gh_run_receptor import __version__ as release
except Exception:
    release = "0+unknown"

extensions = ["myst_parser"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
source_suffix = {".md": "markdown"}

html_theme = "sphinx_rtd_theme"
html_title = "gh-run-receptor"

myst_heading_anchors = 3
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
]
