"""Verify the noarch installation's version, frozen schemas and local commands."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import importlib.resources
import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import gh_run_receptor
from gh_run_receptor.contracts import CONTRACTS
from gh_run_receptor.github import GitHubClient

ROOT = Path(__file__).resolve().parents[1]


def verify_schemas(inventory: dict) -> None:
    """Require every installed contract resource to retain its frozen bytes."""
    names = {schema.resource for spec in CONTRACTS.values() for schema in spec.schemas}
    hashes = inventory.get("schema_sha256", {})
    if set(hashes) != names:
        raise ValueError("Installed contract registry differs from the frozen schema inventory")
    resources = importlib.resources.files("gh_run_receptor.schemas")
    for name in sorted(names):
        raw = resources.joinpath(name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != hashes[name]:
            raise ValueError(f"Installed frozen schema differs: {name}")


def verify_commands(prefix: Path) -> dict[str, str]:
    """Require prefix-owned commands and the adapter's functional gh floor."""
    commands = {}
    for name in ("gh", "gh-run-receptor"):
        executable = shutil.which(name)
        if not executable or not Path(executable).resolve().is_relative_to(prefix):
            raise ValueError(f"Installed {name} command must belong to the qualified prefix")
        commands[name] = executable
    # Reuse the acquisition adapter's bounded parser and functional floor. This
    # invokes only gh --version and does not acquire GitHub data or credentials.
    GitHubClient()._ensure_supported_cli()
    return commands


def verify_installation(root: Path, expected: str) -> dict:
    """Exercise only offline commands; never query authentication or the API."""
    prefix = Path(sys.prefix).resolve()
    origin = Path(gh_run_receptor.__file__).resolve()
    if not origin.is_relative_to(prefix) or origin.is_relative_to(root.resolve()):
        raise ValueError("Package import must belong to the isolated installed prefix")
    embedded = importlib.import_module("gh_run_receptor._version")
    if (
        gh_run_receptor.__version__ != expected
        or embedded.__version__ != expected
        or importlib.metadata.version("gh-run-receptor") != expected
    ):
        raise ValueError(
            "Runtime, embedded and distribution versions must agree with the candidate"
        )
    inventory = tomllib.loads((root / "devtools/conda-build/resources.toml").read_text())
    verify_schemas(inventory)
    commands = verify_commands(prefix)
    result = subprocess.run(
        [commands["gh-run-receptor"], "--version"],
        cwd=root.parent,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.stdout.strip() != expected:
        raise ValueError("Installed console launcher reports a different version")
    return dict(
        version=expected,
        origin=str(origin),
        prefix=str(prefix),
        commands=commands,
        schemas=len(inventory["schema_sha256"]),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()
    print(json.dumps(verify_installation(args.root, args.expected_version), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
