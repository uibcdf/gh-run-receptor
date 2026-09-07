#!/usr/bin/env python3
"""Validating the frozen serialized-contract baseline."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gh_run_receptor.contracts import (  # noqa: E402
    CONTRACTS,
    MIGRATIONS,
    SCHEMA_BASELINE_TAG,
    schema_id,
)

Runner = Callable[..., subprocess.CompletedProcess[bytes]]


def _baseline_bytes(
    root: Path, tag: str, relative: Path, runner: Runner
) -> tuple[bytes | None, str | None]:
    result = runner(
        ["git", "show", f"{tag}:{relative.as_posix()}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").splitlines()
        return None, detail[-1][:240] if detail else "git show failed"
    return result.stdout, None


def validate_contracts(
    root: Path,
    *,
    baseline_tag: str = SCHEMA_BASELINE_TAG,
    runner: Runner = subprocess.run,
) -> list[str]:
    """Returning contract registry, schema, migration, and baseline errors."""

    errors: list[str] = []
    schema_root = root / "gh_run_receptor/schemas"
    registered = {schema.resource for spec in CONTRACTS.values() for schema in spec.schemas}
    discovered = {path.name for path in schema_root.glob("*-v*.schema.json")}
    if discovered != registered:
        errors.append(
            "registered schema resources disagree with package files: "
            f"registered={sorted(registered)!r} files={sorted(discovered)!r}"
        )

    for kind, spec in CONTRACTS.items():
        if spec.current_version not in spec.readable_versions:
            errors.append(f"{kind} current version is not readable")
        schema_versions = {schema.version for schema in spec.schemas}
        if len(schema_versions) != len(spec.schemas):
            errors.append(f"{kind} contains duplicate schema versions")
        if not spec.readable_versions <= schema_versions:
            errors.append(f"{kind} readable versions lack packaged schemas")
        for version in range(1, spec.current_version):
            if version in spec.readable_versions and (kind, version) not in MIGRATIONS:
                errors.append(f"{kind} readable version {version} has no forward migration")
        for schema in spec.schemas:
            path = schema_root / schema.resource
            try:
                raw = path.read_bytes()
                payload = json.loads(raw)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{schema.resource} cannot be read as JSON: {exc}")
                continue
            expected_identifier = schema_id(kind, schema.version)
            if payload.get("title") != expected_identifier:
                errors.append(f"{schema.resource} title disagrees with registry")
            schema_property = payload.get("properties", {}).get("schema", {})
            if schema_property.get("const") != expected_identifier:
                errors.append(f"{schema.resource} schema const disagrees with registry")
            expected_id = f"https://uibcdf.org/gh-run-receptor/schemas/{schema.resource}"
            if payload.get("$id") != expected_id:
                errors.append(f"{schema.resource} $id disagrees with resource path")

            if schema.frozen_since is None:
                continue
            relative = path.relative_to(root)
            baseline, detail = _baseline_bytes(root, schema.frozen_since, relative, runner)
            if baseline is None:
                errors.append(f"cannot read {relative} from {schema.frozen_since}: {detail}")
            elif baseline != raw:
                errors.append(f"{relative} changed after frozen baseline {schema.frozen_since}")
    frozen_tags = {
        schema.frozen_since
        for spec in CONTRACTS.values()
        for schema in spec.schemas
        if schema.frozen_since is not None
    }
    if baseline_tag not in frozen_tags:
        errors.append(f"required baseline {baseline_tag!r} is not registered")
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--baseline", default=SCHEMA_BASELINE_TAG)
    args = parser.parse_args(argv)
    errors = validate_contracts(args.root.resolve(), baseline_tag=args.baseline)
    if errors:
        for error in errors:
            print(f"Contract compatibility: FAIL — {error}", file=sys.stderr)
        return 1
    frozen = sum(
        schema.frozen_since is not None for spec in CONTRACTS.values() for schema in spec.schemas
    )
    print(
        f"Contract compatibility: PASS — contracts={len(CONTRACTS)} "
        f"frozen={frozen} baseline={args.baseline}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
