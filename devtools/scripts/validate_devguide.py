#!/usr/bin/env python3
"""Validate local lifecycle invariants for developer reports."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from devguide_reports import ROOT, validate_all


def main() -> int:
    errors = validate_all()
    index = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("devguide_index.py")), "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if index.returncode:
        errors.append(index.stdout.strip() or index.stderr.strip())
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Developer report lifecycle is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
