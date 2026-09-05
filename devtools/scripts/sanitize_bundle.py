#!/usr/bin/env python3
"""Reduce a reviewed public capture to the source fields used by contract tests."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from gh_run_receptor.bundle import load_bundle


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def _selected_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    run = evidence["run.json"]
    workflow = evidence["workflow.json"]
    jobs = evidence["jobs.json"]["jobs"]
    artifacts = evidence["artifacts.json"]["artifacts"]
    selected = {
        "run.json": {
            key: run.get(key)
            for key in ("status", "conclusion", "name", "html_url", "head_sha")
        },
        "workflow.json": {"path": workflow.get("path")},
        "jobs.json": {
            "total_count": len(jobs),
            "jobs": [
                {
                    "id": job.get("id"),
                    "name": job.get("name"),
                    "status": job.get("status"),
                    "conclusion": job.get("conclusion"),
                    "started_at": job.get("started_at"),
                    "completed_at": job.get("completed_at"),
                    "html_url": job.get("html_url"),
                    "steps": [
                        {
                            "number": step.get("number"),
                            "name": step.get("name"),
                            "conclusion": step.get("conclusion"),
                        }
                        for step in job.get("steps") or []
                    ],
                }
                for job in jobs
            ],
        },
        "checks.json": {"total_count": 0, "check_runs": []},
        "artifacts.json": {
            "total_count": len(artifacts),
            "artifacts": [
                {
                    "id": artifact.get("id"),
                    "name": artifact.get("name"),
                    "size_in_bytes": artifact.get("size_in_bytes"),
                    "expired": artifact.get("expired"),
                    "digest": artifact.get("digest"),
                }
                for artifact in artifacts
            ],
        },
    }
    if "config.json" in evidence:
        selected["config.json"] = evidence["config.json"]
    return selected


def sanitize(source: Path, destination: Path) -> None:
    manifest, evidence = load_bundle(source)
    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    destination.mkdir(parents=True)
    members = []
    selected = _selected_evidence(evidence)
    for name, value in selected.items():
        data = _canonical(value)
        (destination / name).write_bytes(data)
        source_member = next(item for item in manifest["members"] if item["path"] == name)
        members.append(
            {
                "path": name,
                "kind": source_member["kind"],
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "complete": source_member["complete"],
            }
        )
    sanitized_manifest = {
        "schema": "gh-run-receptor.bundle@1",
        "repository": manifest["repository"],
        "hostname": manifest["hostname"],
        "run_id": manifest["run_id"],
        "run_attempt": manifest["run_attempt"],
        "head_sha": manifest.get("head_sha"),
        "api_version": manifest["api_version"],
        "receptor_version": manifest["receptor_version"],
        "capture_policy": "metadata",
        "captured_at": manifest["captured_at"],
        "complete": manifest["complete"],
        "members": members,
        "warnings": manifest["warnings"],
    }
    (destination / "manifest.json").write_bytes(_canonical(sanitized_manifest))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    sanitize(args.source, args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
