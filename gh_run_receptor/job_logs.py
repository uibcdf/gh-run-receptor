"""Binding one bounded job log to an explicit workflow-run attempt."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from gh_run_receptor.errors import BundleError
from gh_run_receptor.github import GitHubClient
from gh_run_receptor.logs import MAX_MEMBER_BYTES


def job_log_name(job_id: int) -> str:
    """Validate a bounded numeric ID before it can enter a cache path or API request."""
    if isinstance(job_id, bool) or not isinstance(job_id, int) or not 1 <= job_id < 10**20:
        raise BundleError("job ID must be a positive integer with at most 20 digits")
    return f"job-{job_id}.log"


def completed_job(
    jobs: Any, job_id: int, *, run_id: int, attempt: int, head_sha: str | None
) -> dict[str, Any]:
    """Require unique membership in an attempt-qualified collection before reading logs."""
    job_log_name(job_id)
    if not isinstance(jobs, dict) or not isinstance(jobs.get("jobs"), list):
        raise BundleError("job-log selection requires an attempt-qualified jobs collection")
    matches = [job for job in jobs["jobs"] if isinstance(job, dict) and job.get("id") == job_id]
    if len(matches) != 1:
        raise BundleError("selected job must occur exactly once in the requested attempt")
    job = matches[0]
    if (
        isinstance(job.get("id"), bool)
        or type(job.get("run_id")) is not int
        or job.get("run_id") != run_id
    ):
        raise BundleError("selected job has conflicting run identity")
    if (
        type(job.get("run_attempt", attempt)) is not int
        or job.get("run_attempt", attempt) != attempt
    ):
        raise BundleError("selected job has conflicting attempt identity")
    if head_sha is not None and job.get("head_sha", head_sha) != head_sha:
        raise BundleError("selected job has conflicting source SHA")
    if job.get("status") != "completed":
        raise BundleError("job-log inspection requires a completed job")
    return job


def capture_job_log(
    client: GitHubClient,
    repository: str,
    job_id: int,
    destination: Path,
    *,
    run_id: int,
    attempt: int,
) -> dict[str, Any]:
    """Download original plain-text bytes into caller-owned private capture staging."""
    name = job_log_name(job_id)
    path = destination / name
    try:
        client.download(
            f"/repos/{repository}/actions/jobs/{job_id}/logs", path, max_bytes=MAX_MEMBER_BYTES
        )
        with path.open("rb") as stream:
            data = stream.read(MAX_MEMBER_BYTES + 1)
        if len(data) > MAX_MEMBER_BYTES:
            raise BundleError("job log exceeds the byte limit")
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return {
        "path": name,
        "kind": "github.job_log",
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "complete": True,
        "job_id": job_id,
        "run_id": run_id,
        "run_attempt": attempt,
    }


def validate_job_log_scope(manifest: dict[str, Any], evidence: dict[str, Any]) -> None:
    """Reject forged or ambiguous job-only evidence during offline replay."""
    scope = manifest.get("log_scope")
    error = manifest.get("job_log_error")
    members = [m for m in manifest["members"] if m.get("kind") == "github.job_log"]
    if scope is None:
        if members or error is not None:
            raise BundleError("job log member requires an explicit job-only scope")
        return
    if not isinstance(scope, dict) or scope.get("kind") != "job":
        raise BundleError("unsupported log scope")
    job_id = scope.get("job_id")
    completed_job(
        evidence["jobs.json"],
        job_id,
        run_id=manifest["run_id"],
        attempt=manifest["run_attempt"],
        head_sha=manifest.get("head_sha"),
    )
    if error is not None and (
        not isinstance(error, dict)
        or not isinstance(error.get("category"), str)
        or not 1 <= len(error["category"]) <= 80
        or (
            error.get("http_status") is not None
            and (type(error["http_status"]) is not int or not 100 <= error["http_status"] <= 599)
        )
        or members
        or manifest["complete"]
        or manifest["capture_policy"] == "metadata"
    ):
        raise BundleError("invalid job-log acquisition error evidence")
    if len(members) > 1 or any(m["path"] == "logs.zip" for m in manifest["members"]):
        raise BundleError("job-only scope cannot contain an attempt archive or multiple logs")
    if manifest["capture_policy"] == "metadata" and members:
        raise BundleError("metadata-only selection cannot contain job logs")
    for member in members:
        expected = {
            "path": f"job-{job_id}.log",
            "job_id": job_id,
            "run_id": manifest["run_id"],
            "run_attempt": manifest["run_attempt"],
            "complete": True,
        }
        if any(member.get(key) != value for key, value in expected.items()):
            raise BundleError("job log member has conflicting identity or completeness")
        if member["bytes"] > MAX_MEMBER_BYTES:
            raise BundleError("job log exceeds the byte limit")
    if (
        not members
        and manifest["capture_policy"] != "metadata"
        and not any(w.startswith("job logs unavailable:") for w in manifest["warnings"])
    ):
        raise BundleError("requested job log is missing without an unavailable state")
