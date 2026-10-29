"""Validate the explicitly selected repository report lifecycle and indexes."""

import argparse
from pathlib import Path

from .devguide_index import render, update
from .devguide_reports import queues, validate_all


def validate_repository(root: Path) -> list[str]:
    errors = validate_all(root)
    for directory in queues(root).values():
        if update(directory / "README.md", render(directory), check=True):
            errors.append(f"Stale devguide index: {directory.relative_to(root)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = validate_repository(args.root.resolve())
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Developer report lifecycle is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
