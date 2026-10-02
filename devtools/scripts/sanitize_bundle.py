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


def _selected_evidence(
    evidence: dict[str, Any], *, include_config: bool = True, include_annotations: bool = False
) -> dict[str, Any]:
    run = evidence["run.json"]
    workflow = evidence["workflow.json"]
    jobs = evidence["jobs.json"]["jobs"]
    artifacts = evidence["artifacts.json"]["artifacts"]
    selected = {
        "run.json": {
            key: run.get(key)
            for key in (
                "id",
                "run_attempt",
                "status",
                "conclusion",
                "name",
                "html_url",
                "head_sha",
                "event",
                "head_branch",
            )
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
                            "status": step.get("status"),
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
    if include_annotations:
        selected["run.json"]["check_suite_id"] = run.get("check_suite_id")
        for source_job, selected_job in zip(jobs, selected["jobs.json"]["jobs"], strict=True):
            for key in ("check_run_url", "run_id", "run_attempt", "head_sha"):
                if key in source_job:
                    selected_job[key] = source_job[key]
        checks = []
        for check in evidence["checks.json"]["check_runs"]:
            if "annotations" not in check:
                continue
            checks.append(
                {
                    **{
                        key: check.get(key)
                        for key in ("id", "head_sha", "status", "conclusion", "annotations_state")
                    },
                    "check_suite": {"id": check.get("check_suite", {}).get("id")},
                    "output": {
                        "annotations_count": check.get("output", {}).get("annotations_count")
                    },
                    "annotations": [
                        {
                            key: annotation.get(key)
                            for key in (
                                "annotation_level",
                                "message",
                                "path",
                                "start_line",
                                "end_line",
                            )
                        }
                        for annotation in check["annotations"]
                    ],
                }
            )
        selected["checks.json"] = {"total_count": len(checks), "check_runs": checks}
    if include_config and "config.json" in evidence:
        selected["config.json"] = evidence["config.json"]
    for name, value in evidence.items():
        if name.startswith("producer-events-") and name.endswith(".json"):
            selected[name] = value
    return selected


def sanitize(
    source: Path,
    destination: Path,
    *,
    include_config: bool = True,
    include_annotations: bool = False,
) -> None:
    manifest, evidence = load_bundle(source)
    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    destination.mkdir(parents=True)
    members = []
    selected = _selected_evidence(
        evidence, include_config=include_config, include_annotations=include_annotations
    )
    for name, value in selected.items():
        data = _canonical(value)
        (destination / name).write_bytes(data)
        source_member = next(item for item in manifest["members"] if item["path"] == name)
        member = {
            "path": name,
            "kind": source_member["kind"],
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "complete": source_member["complete"],
        }
        for key in (
            "artifact_id",
            "artifact_name",
            "artifact_digest",
            "archive_sha256",
        ):
            if key in source_member:
                member[key] = source_member[key]
        members.append(member)
    removed_logs = any(member.get("path") == "logs.zip" for member in manifest["members"])
    sanitized_manifest = {
        "schema": "gh-run-receptor.bundle@1",
        "repository": manifest["repository"],
        "hostname": manifest["hostname"],
        "run_id": manifest["run_id"],
        "run_attempt": manifest["run_attempt"],
        "head_sha": manifest.get("head_sha"),
        "api_version": manifest["api_version"],
        "receptor_version": manifest["receptor_version"],
        "capture_policy": "metadata" if removed_logs else manifest["capture_policy"],
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
    parser.add_argument(
        "--without-config",
        action="store_true",
        help="omit captured repository rules when they do not define the fixture behavior",
    )
    parser.add_argument(
        "--with-check-annotations",
        action="store_true",
        help="retain reviewed public check annotations and their job/attempt identity",
    )
    args = parser.parse_args()
    sanitize(
        args.source,
        args.destination,
        include_config=not args.without_config,
        include_annotations=args.with_check_annotations,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
