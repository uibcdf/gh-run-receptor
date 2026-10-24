"""Bind immutable administrative test helpers without exposing runtime source (#60)."""

from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import tomllib
from contextlib import contextmanager
from pathlib import Path
from typing import Any

HELPER_NAMES = ("devtools", "tests")
MAX_HELPER_FILES = 1024
MAX_HELPER_BYTES = 64 * 1024 * 1024


class InstalledPath(list):
    """Keep legacy administrative imports from putting runtime source on sys.path."""

    def __init__(self, values, root: Path):
        self.root = root.resolve()
        self.blocked = 0
        super().__init__(values)

    def accepted(self, value) -> bool:
        if isinstance(value, str) and Path(value).resolve() == self.root:
            self.blocked += 1
            return False
        return True

    def insert(self, index, value):
        if self.accepted(value):
            super().insert(index, value)

    def append(self, value):
        if self.accepted(value):
            super().append(value)

    def extend(self, values):
        super().extend(value for value in values if self.accepted(value))

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            super().__setitem__(index, [item for item in value if self.accepted(item)])
        elif self.accepted(value):
            super().__setitem__(index, value)

    def __iadd__(self, values):
        self.extend(values)
        return self


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


@contextmanager
def bound_helpers(root: Path, candidate_sha: str):
    """Own only two nonruntime namespace bindings from the exact producer checkout."""
    root = root.resolve()
    if len(candidate_sha) != 40 or any(c not in "0123456789abcdef" for c in candidate_sha):
        raise ValueError("helper source requires a full immutable commit")
    if _git(root, "rev-parse", "HEAD") != candidate_sha:
        raise ValueError("helper source differs from the original producer")
    subprocess.run(
        ["git", "diff", "--quiet", candidate_sha, "--", *HELPER_NAMES], cwd=root, check=True
    )
    if any(
        any(key == n or key.startswith(n + ".") for key in sys.modules)
        or importlib.util.find_spec(n) is not None
        for n in HELPER_NAMES
    ):
        raise ValueError("administrative helper namespace is already owned or importable")
    for entry in sys.path:
        if entry and Path(entry).resolve() == root:
            raise ValueError("component source root is present on the import path")
    tracked = _git(root, "ls-files", "--", *HELPER_NAMES).splitlines()
    expected = {root / name for name in tracked if name.endswith(".py")}
    actual = set()
    for name in HELPER_NAMES:
        directory = root / name
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("helper namespace must be a real source directory")
        if (directory / "__init__.py").exists():
            raise ValueError("this bounded recovery accepts only the original namespace roots")
        for path in directory.rglob("*.py"):
            if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root.parent):
                raise ValueError("helper source contains a symlink")
            actual.add(path)
    if not actual or actual != expected or len(actual) > MAX_HELPER_FILES:
        raise ValueError("helper Python inventory differs from the committed source")
    if sum(p.stat().st_size for p in actual) > MAX_HELPER_BYTES:
        raise ValueError("helper Python source exceeds the byte limit")
    hashes = {p.resolve(): hashlib.sha256(p.read_bytes()).hexdigest() for p in actual}
    allowed_directories = {root / n for n in HELPER_NAMES}
    for path in actual:
        allowed_directories.update(p for p in path.parents if p.is_relative_to(root) and p != root)
    receipt: dict[str, Any] = {
        "candidate_sha": candidate_sha,
        "helper_files": len(hashes),
        "source_root_added_to_path": False,
        "checks": 0,
        "state": "bound",
        "helper_sha256": {
            str(path.relative_to(root)): digest for path, digest in sorted(hashes.items())
        },
    }
    owned = {}

    def check() -> None:
        if any(entry and Path(entry).resolve() == root for entry in sys.path):
            raise ValueError("component source root entered the import path")
        if any(sys.modules.get(name) is not module for name, module in owned.items()):
            raise ValueError("administrative helper namespace binding changed")
        for path, digest in hashes.items():
            if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError("administrative helper bytes changed during qualification")
        loaded = []
        for name, module in list(sys.modules.items()):
            if not any(name == n or name.startswith(n + ".") for n in HELPER_NAMES):
                continue
            location = getattr(module, "__file__", None)
            if location is not None and Path(location).resolve() not in hashes:
                raise ValueError("administrative helper import escaped its bound source")
            paths = getattr(module, "__path__", ())
            if location is None and not paths:
                raise ValueError("administrative helper has no verifiable origin")
            if any(Path(p).resolve() not in allowed_directories for p in paths):
                raise ValueError("administrative helper namespace path changed")
            loaded.append(name)
        receipt.update(checks=receipt["checks"] + 1, loaded=sorted(loaded))

    try:
        for name in HELPER_NAMES:
            spec = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
            spec.submodule_search_locations = [str(root / name)]
            sys.modules[name] = importlib.util.module_from_spec(spec)
            owned[name] = sys.modules[name]
        check()
        yield receipt
    finally:
        try:
            check()
            receipt["state"] = "verified-helpers"
        finally:
            for name in list(sys.modules):
                if any(name == n or name.startswith(n + ".") for n in HELPER_NAMES):
                    del sys.modules[name]
            receipt["bindings_removed"] = True


def run_tests(root: Path, suite: Path, candidate_sha: str, output: Path) -> int:
    """Call the unchanged pinned installed SDK with its original tests/provenance guards."""
    inventory = tomllib.loads((root / "devtools/dependency_routes.toml").read_text())
    if _git(suite, "rev-parse", "HEAD") != inventory["shared_tool"]["commit"]:
        raise ValueError("qualification SDK differs from the producer's accepted provider")
    subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=suite, check=True)
    before_path, before_argv = sys.path, list(sys.argv)
    safe_path = InstalledPath(sys.path, root)
    receipt: dict[str, Any] = {"state": "not-started"}
    try:
        sys.path = safe_path
        with bound_helpers(root, candidate_sha) as receipt:
            sys.argv = ["installed_noarch.py", "tests", "--root", str(root)]
            path = suite / "devtools/scripts/installed_noarch.py"
            spec = importlib.util.spec_from_file_location("_ghrr_installed_sdk", path)
            if spec is None or spec.loader is None:
                raise ValueError("installed SDK cannot be loaded")
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            result = module.main()
            if sys.path is not safe_path:
                raise ValueError("installed test path isolation was replaced")
            receipt["test_exit_status"] = result
            receipt["blocked_source_path_additions"] = safe_path.blocked
            return result
    finally:
        sys.path = before_path
        sys.argv[:] = before_argv
        sys.modules.pop("_ghrr_installed_sdk", None)
        output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--suite-root", type=Path, required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return run_tests(
        args.root.resolve(), args.suite_root.resolve(), args.candidate_sha, args.output
    )


if __name__ == "__main__":
    raise SystemExit(main())
