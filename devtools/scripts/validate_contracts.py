"""Compatibility CLI with explicit checkout defaults and caller-relative paths."""

import os
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    arguments = list(sys.argv[1:])
    if "--root" not in arguments:
        arguments += ["--root", str(root)]
    environment = dict(os.environ, PYTHONPATH=str(root))
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "gh_run_receptor_tools.validate_contracts", *arguments],
            env=environment,
        )
    )
