"""Review member inputs through the pinned suite tool without publishing."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = "devtools/dependency_routes.toml"


def check_owner_inputs(root: Path) -> None:
    """Tie external gh and frozen-resource declarations to the actual source."""
    tree = ast.parse((root / "gh_run_receptor/github.py").read_text(encoding="utf-8"))
    values = [
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "MINIMUM_GH_VERSION"
            for target in node.targets
        )
    ]
    if len(values) != 1 or not isinstance(values[0], tuple) or len(values[0]) != 3:
        raise ValueError("Review the GitHub adapter's changed minimum-version declaration")
    if any(type(part) is not int or part < 0 for part in values[0]):
        raise ValueError("GitHub CLI floor must have three nonnegative integer parts")
    expected = "gh>=" + ".".join(map(str, values[0]))
    inventory = tomllib.loads((root / "devtools/conda-build/resources.toml").read_text())
    if inventory.get("external_run_requirements") != [expected]:
        raise ValueError("External gh requirement differs from the acquisition adapter floor")
    schemas = {
        path.name: path for path in (root / "gh_run_receptor/schemas").glob("*-v*.schema.json")
    }
    hashes = inventory.get("schema_sha256", {})
    if set(hashes) != set(schemas) or not hashes:
        raise ValueError("Frozen schema digest inventory differs from the package resources")
    required = set(inventory["required_paths"])
    for name, path in schemas.items():
        if f"site-packages/gh_run_receptor/schemas/{name}" not in required:
            raise ValueError(f"Required archive schema is undeclared: {name}")
        if hashes[name] != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError(f"Frozen schema digest differs: {name}")


def checked_provider(root: Path, suite: Path) -> Path:
    """Refuse a mutable or different provider checkout before invoking its SDK."""
    inventory = tomllib.loads((root / INVENTORY).read_text())
    expected = inventory["shared_tool"]["commit"]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=suite, text=True).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", expected) or head != expected:
        raise ValueError("Use the reviewed full MolSysSuite provider commit")
    subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=suite, check=True)
    return suite / "devtools/scripts"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--suite-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--candidate-sha")
    parser.add_argument("--version")
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        tools = checked_provider(root, args.suite_root.resolve())
        check_owner_inputs(root)
        if args.candidate_sha or args.version:
            plan = tomllib.loads((root / "devtools/conda-build/release_plan.toml").read_text())
            head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            if (
                not re.fullmatch(r"[0-9a-f]{40}", args.candidate_sha or "")
                or head != args.candidate_sha
            ):
                raise ValueError("Candidate must be the checked-out immutable source SHA")
            if args.version != plan["version"]:
                raise ValueError("Candidate version differs from the committed release plan")
            subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=root, check=True)
            subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(tools / "noarch_conda.py"),
                    "--root",
                    str(root),
                    "--plan",
                    "devtools/conda-build/release_plan.toml",
                ],
                check=True,
            )
        subprocess.run(
            [
                sys.executable,
                str(root / "devtools/scripts/validate_contracts.py"),
                "--baseline",
                "0.21.0",
            ],
            cwd=root,
            check=True,
        )
        response = subprocess.run(
            [
                sys.executable,
                "-B",
                str(tools / "dependency_routes.py"),
                "--root",
                str(root),
                "--inventory",
                INVENTORY,
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        proof = json.loads(response.stdout)
        proof["external_runtime_floor"] = "reviewed-against-acquisition-adapter"
        proof["schema_digests"] = "reviewed-against-frozen-source"
        if args.output:
            args.output.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
        print(f"Reviewed {len(proof['routes'])} distribution routes: {proof['qualification']}")
        return 0
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print(f"GH Run Receptor distribution inputs rejected: {error}", file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError):
            print((error.stdout or "") + (error.stderr or ""), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
