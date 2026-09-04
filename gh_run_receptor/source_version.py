"""Resolving a version for an unbuilt GitHub CLI script-extension checkout."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_DESCRIBE = re.compile(
    r"^(?P<tag>[0-9]+\.[0-9]+\.[0-9]+)-(?P<distance>[0-9]+)-g"
    r"(?P<revision>[0-9a-f]+)(?P<dirty>-dirty)?$"
)


def parse_git_describe(value: str) -> str | None:
    """Converting long ``git describe`` output to a PEP 440 version."""
    match = _DESCRIBE.fullmatch(value.strip())
    if match is None:
        return None
    tag = match.group("tag")
    distance = int(match.group("distance"))
    dirty = match.group("dirty") is not None
    if distance == 0 and not dirty:
        return tag
    version = f"{tag}+{distance}.g{match.group('revision')}"
    return f"{version}.dirty" if dirty else version


def version_from_source_checkout() -> str | None:
    """Reading the nearest release tag without importing a build dependency."""
    repository = Path(__file__).resolve().parent.parent
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "describe",
                "--tags",
                "--long",
                "--dirty",
                "--match",
                "[0-9]*",
            ],
            check=False,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return parse_git_describe(result.stdout)
