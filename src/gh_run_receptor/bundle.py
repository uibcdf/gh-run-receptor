"""Capturing and validating replayable GitHub evidence bundles."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gh_run_receptor import __version__
from gh_run_receptor.errors import AcquisitionError, BundleError
from gh_run_receptor.github import API_VERSION, GitHubClient, merge_pages

STRUCTURED_MEMBERS = ("run.json", "workflow.json", "jobs.json", "checks.json", "artifacts.json")


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_member(directory: Path, name: str, value: Any, kind: str) -> dict[str, Any]:
    data = _canonical_json(value)
    (directory / name).write_bytes(data)
    return {
        "path": name,
        "kind": kind,
        "bytes": len(data),
        "sha256": _sha256(data),
        "complete": True,
    }


def default_bundle_path(
    cache_dir: Path,
    hostname: str,
    repository: str,
    run_id: int,
    attempt: int,
    policy: str,
) -> Path:
    """Building a stable cache location for one run attempt."""
    owner, name = repository.split("/", 1)
    return cache_dir / hostname / owner / name / str(run_id) / str(attempt) / policy


def capture_bundle(
    client: GitHubClient,
    repository: str,
    run_id: int,
    *,
    attempt: int | None,
    policy: str,
    destination: Path,
    run: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Capturing one run attempt atomically into ``destination``."""
    run = run or client.json(f"/repos/{repository}/actions/runs/{run_id}")
    if not isinstance(run, dict):
        raise BundleError("workflow-run response is not an object")
    current_attempt = int(run.get("run_attempt") or 1)
    selected_attempt = attempt or current_attempt
    if selected_attempt < 1 or selected_attempt > current_attempt:
        raise BundleError(
            f"attempt {selected_attempt} is outside the available range 1..{current_attempt}"
        )

    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}-", dir=parent))
    os.chmod(temporary, 0o700)
    members: list[dict[str, Any]] = []
    warnings: list[str] = []

    try:
        members.append(_write_member(temporary, "run.json", run, "github.workflow_run"))
        workflow_id = run.get("workflow_id")
        workflow = (
            client.json(f"/repos/{repository}/actions/workflows/{workflow_id}")
            if workflow_id is not None
            else {"unavailable": "workflow_id missing from run"}
        )
        members.append(_write_member(temporary, "workflow.json", workflow, "github.workflow"))

        jobs_payload = client.json(
            f"/repos/{repository}/actions/runs/{run_id}/attempts/{selected_attempt}/jobs?per_page=100",
            paginate=True,
        )
        jobs = merge_pages(jobs_payload, "jobs")
        members.append(_write_member(temporary, "jobs.json", jobs, "github.jobs"))

        artifacts_payload = client.json(
            f"/repos/{repository}/actions/runs/{run_id}/artifacts?per_page=100", paginate=True
        )
        artifacts = merge_pages(artifacts_payload, "artifacts")
        members.append(_write_member(temporary, "artifacts.json", artifacts, "github.artifacts"))

        checks = {"total_count": 0, "check_runs": []}
        check_suite_id = run.get("check_suite_id")
        if check_suite_id:
            checks_payload = client.json(
                f"/repos/{repository}/check-suites/{check_suite_id}/check-runs?per_page=100",
                paginate=True,
            )
            checks = merge_pages(checks_payload, "check_runs")
        members.append(_write_member(temporary, "checks.json", checks, "github.check_runs"))

        fetch_logs = policy == "full" or (
            policy == "adaptive"
            and run.get("status") == "completed"
            and run.get("conclusion") != "success"
        )
        if fetch_logs:
            try:
                log_path = temporary / "logs.zip"
                client.download(
                    f"/repos/{repository}/actions/runs/{run_id}/attempts/{selected_attempt}/logs",
                    log_path,
                )
                data = log_path.read_bytes()
                members.append(
                    {
                        "path": "logs.zip",
                        "kind": "github.logs",
                        "bytes": len(data),
                        "sha256": _sha256(data),
                        "complete": True,
                    }
                )
            except AcquisitionError as error:  # the structured report remains useful
                warnings.append(f"logs unavailable: {error}")

        complete = not warnings
        manifest = {
            "schema": "gh-run-receptor.bundle@1",
            "repository": repository,
            "hostname": client.hostname,
            "run_id": run_id,
            "run_attempt": selected_attempt,
            "head_sha": run.get("head_sha"),
            "api_version": API_VERSION,
            "receptor_version": __version__,
            "capture_policy": policy,
            "captured_at": datetime.now(UTC).isoformat(),
            "complete": complete,
            "members": members,
            "warnings": warnings,
        }
        (temporary / "manifest.json").write_bytes(_canonical_json(manifest))

        if destination.exists():
            raise BundleError(f"bundle already exists: {destination}")
        temporary.replace(destination)
        return manifest
    except Exception:
        for child in temporary.iterdir():
            child.unlink()
        temporary.rmdir()
        raise


def load_bundle(directory: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validating a bundle and returning its manifest and structured evidence."""
    try:
        manifest = json.loads((directory / "manifest.json").read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise BundleError(f"cannot read bundle manifest: {error}") from error
    if manifest.get("schema") != "gh-run-receptor.bundle@1":
        raise BundleError(f"unsupported bundle schema: {manifest.get('schema')!r}")

    evidence: dict[str, Any] = {}
    seen: set[str] = set()
    for member in manifest.get("members", []):
        name = member.get("path")
        if not isinstance(name, str) or name in seen or Path(name).name != name:
            raise BundleError(f"unsafe or duplicate bundle member: {name!r}")
        seen.add(name)
        path = directory / name
        try:
            data = path.read_bytes()
        except OSError as error:
            raise BundleError(f"missing bundle member: {name}") from error
        if _sha256(data) != member.get("sha256"):
            raise BundleError(f"digest mismatch for bundle member: {name}")
        if name in STRUCTURED_MEMBERS:
            try:
                evidence[name] = json.loads(data)
            except json.JSONDecodeError as error:
                raise BundleError(f"invalid JSON bundle member: {name}") from error

    required = set(STRUCTURED_MEMBERS)
    if missing := sorted(required - evidence.keys()):
        raise BundleError(f"missing structured bundle members: {', '.join(missing)}")
    return manifest, evidence
