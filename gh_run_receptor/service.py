"""Sharing capture and report orchestration across entry points."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gh_run_receptor.bundle import capture_bundle, default_bundle_path, load_bundle
from gh_run_receptor.errors import BundleError
from gh_run_receptor.github import GitHubClient
from gh_run_receptor.report import build_report


@dataclass(frozen=True)
class CapturedEvidence:
    """Holding one validated bundle and its structured evidence."""

    manifest: dict[str, Any]
    evidence: dict[str, Any]
    path: Path


def acquire_evidence(
    client: GitHubClient,
    repository: str,
    run_id: int,
    *,
    attempt: int | None,
    policy: str,
    cache_root: Path,
    output: Path | None = None,
) -> CapturedEvidence:
    """Acquiring or reusing one identity-checked evidence bundle."""
    run = client.json(f"/repos/{repository}/actions/runs/{run_id}")
    current_attempt = int(run.get("run_attempt") or 1)
    selected_attempt = attempt or current_attempt
    destination = output or default_bundle_path(
        cache_root, client.hostname, repository, run_id, selected_attempt, policy
    )
    if destination.exists():
        manifest, evidence = load_bundle(destination)
        expected = (repository, run_id, selected_attempt, policy)
        actual = (
            manifest.get("repository"),
            manifest.get("run_id"),
            manifest.get("run_attempt"),
            manifest.get("capture_policy"),
        )
        if actual != expected:
            raise BundleError(
                "existing bundle identity or capture policy does not match the request"
            )
    else:
        manifest = capture_bundle(
            client,
            repository,
            run_id,
            attempt=attempt,
            policy=policy,
            destination=destination,
            run=run,
        )
        _, evidence = load_bundle(destination)
    return CapturedEvidence(manifest=manifest, evidence=evidence, path=destination)


def create_report(
    *,
    repository: str,
    hostname: str,
    run_id: int,
    profile: str,
    capture: str,
    cache_root: Path,
) -> dict[str, Any]:
    """Creating one report through the same core used by the external CLI."""
    client = GitHubClient(hostname)
    resolved_repository = client.repository(repository)
    captured = acquire_evidence(
        client,
        resolved_repository,
        run_id,
        attempt=None,
        policy=capture,
        cache_root=cache_root,
    )
    return build_report(
        captured.manifest,
        captured.evidence,
        profile=profile,
        bundle_directory=captured.path,
    )
