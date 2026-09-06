#!/usr/bin/env python3
"""Synchronize the canonical consumer guide to sibling repositories."""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_REPOSITORIES = (
    "action-build-and-upload-conda-packages",
    "argdigest",
    "depdigest",
    "elastnetmt",
    "molsysmt",
    "molsysviewer",
    "pharmacophoremt",
    "pytest-receptor",
    "pyunitwizard",
    "smonitor",
    "topomt",
)


def synchronize(root: Path, repositories: list[str], *, check: bool, dry_run: bool) -> int:
    source = root / "gh-run-receptor" / "standards" / "GH_RUN_RECEPTOR_GUIDE.md"
    if not source.is_file():
        raise ValueError(f"canonical guide not found: {source}")
    payload = source.read_text(encoding="utf-8")
    stale = []
    for name in repositories:
        target = root / name / "GH_RUN_RECEPTOR_GUIDE.md"
        if not target.parent.is_dir():
            raise ValueError(f"client repository not found: {target.parent}")
        matches = target.is_file() and target.read_text(encoding="utf-8") == payload
        if check:
            if not matches:
                stale.append(name)
        elif dry_run:
            state = "current" if matches else "would update"
            print(f"{name}: {state}")
        elif not matches:
            target.write_text(payload, encoding="utf-8")
            print(f"Updated {target}")
    if stale:
        print("Out-of-date consumer guides: " + ", ".join(stale))
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="directory containing gh-run-receptor and its client repositories",
    )
    parser.add_argument("--repo", action="append", dest="repositories")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repositories = args.repositories or list(DEFAULT_REPOSITORIES)
    return synchronize(args.root.resolve(), repositories, check=args.check, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
