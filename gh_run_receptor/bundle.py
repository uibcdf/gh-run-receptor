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
_CAPTURE_POLICIES = {"full", "adaptive", "metadata"}


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _strict_json(data: str | bytes, context: str) -> Any:
    def object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise BundleError(f"duplicate JSON key in {context}: {key!r}")
            value[key] = item
        return value

    def reject_constant(value: str) -> None:
        raise BundleError(f"non-finite JSON number in {context}: {value}")

    try:
        return json.loads(
            data,
            object_pairs_hook=object_without_duplicates,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BundleError(f"invalid JSON in {context}: {error}") from error


def _validate_manifest(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise BundleError("bundle manifest is not a JSON object")
    if manifest.get("schema") != "gh-run-receptor.bundle@1":
        raise BundleError(f"unsupported bundle schema: {manifest.get('schema')!r}")
    required_types = {
        "repository": str,
        "hostname": str,
        "run_id": int,
        "run_attempt": int,
        "api_version": str,
        "receptor_version": str,
        "capture_policy": str,
        "captured_at": str,
        "complete": bool,
        "members": list,
        "warnings": list,
    }
    for key, expected in required_types.items():
        value = manifest.get(key)
        if not isinstance(value, expected) or (expected is int and isinstance(value, bool)):
            raise BundleError(f"bundle manifest field {key!r} has invalid type")
    if manifest["repository"].count("/") != 1 or not all(manifest["repository"].split("/")):
        raise BundleError("bundle manifest repository must have OWNER/REPO form")
    if not manifest["hostname"] or "/" in manifest["hostname"]:
        raise BundleError("bundle manifest hostname is invalid")
    if manifest["run_id"] < 1 or manifest["run_attempt"] < 1:
        raise BundleError("bundle run and attempt identifiers must be positive")
    if manifest["capture_policy"] not in _CAPTURE_POLICIES:
        raise BundleError(f"unsupported capture policy: {manifest['capture_policy']!r}")
    if not all(isinstance(item, str) for item in manifest["warnings"]):
        raise BundleError("bundle warnings must be strings")
    if manifest.get("head_sha") is not None and not isinstance(manifest["head_sha"], str):
        raise BundleError("bundle head_sha must be a string or null")
    return manifest


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
        manifest_data = (directory / "manifest.json").read_bytes()
    except OSError as error:
        raise BundleError(f"cannot read bundle manifest: {error}") from error
    manifest = _validate_manifest(_strict_json(manifest_data, "manifest.json"))

    evidence: dict[str, Any] = {}
    seen: set[str] = set()
    for member in manifest["members"]:
        if not isinstance(member, dict):
            raise BundleError("bundle member record is not an object")
        name = member.get("path")
        if not isinstance(name, str) or name in seen or Path(name).name != name:
            raise BundleError(f"unsafe or duplicate bundle member: {name!r}")
        if not isinstance(member.get("kind"), str) or not member["kind"]:
            raise BundleError(f"bundle member has invalid kind: {name}")
        if (
            not isinstance(member.get("bytes"), int)
            or isinstance(member["bytes"], bool)
            or member["bytes"] < 0
        ):
            raise BundleError(f"bundle member has invalid byte count: {name}")
        if not isinstance(member.get("complete"), bool):
            raise BundleError(f"bundle member has invalid completeness: {name}")
        digest = member.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise BundleError(f"bundle member has invalid digest: {name}")
        seen.add(name)
        path = directory / name
        try:
            data = path.read_bytes()
        except OSError as error:
            raise BundleError(f"missing bundle member: {name}") from error
        if len(data) != member["bytes"]:
            raise BundleError(f"byte-count mismatch for bundle member: {name}")
        if _sha256(data) != digest:
            raise BundleError(f"digest mismatch for bundle member: {name}")
        if name in STRUCTURED_MEMBERS:
            evidence[name] = _strict_json(data, name)

    required = set(STRUCTURED_MEMBERS)
    if missing := sorted(required - evidence.keys()):
        raise BundleError(f"missing structured bundle members: {', '.join(missing)}")
    return manifest, evidence
