"""Sharing capture and report orchestration across entry points."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

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


def _discard_bundle(path: Path) -> None:
    """Discarding one cache path without following a symlink."""
    if path.is_symlink():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def _refresh_bundle(
    client: GitHubClient,
    repository: str,
    run_id: int,
    *,
    attempt: int | None,
    policy: str,
    destination: Path,
    run: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Replacing one nonterminal cache entry after validating fresh evidence."""
    nonce = uuid4().hex
    replacement = destination.with_name(f".{destination.name}.refresh-{nonce}")
    stale = destination.with_name(f".{destination.name}.stale-{nonce}")
    try:
        capture_bundle(
            client,
            repository,
            run_id,
            attempt=attempt,
            policy=policy,
            destination=replacement,
            run=run,
        )
        load_bundle(replacement)
        destination.rename(stale)
        try:
            replacement.rename(destination)
        except Exception:
            stale.rename(destination)
            raise
        _discard_bundle(stale)
        return load_bundle(destination)
    finally:
        _discard_bundle(replacement)


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
        retained_run = evidence.get("run.json")
        if not isinstance(retained_run, dict) or retained_run.get("status") != "completed":
            manifest, evidence = _refresh_bundle(
                client,
                repository,
                run_id,
                attempt=attempt,
                policy=policy,
                destination=destination,
                run=run,
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
    config_override: dict[str, Any] | None = None,
    config_source_override: dict[str, Any] | None = None,
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
    build_options: dict[str, Any] = {
        "profile": profile,
        "bundle_directory": captured.path,
    }
    if config_override is not None:
        build_options["config_override"] = config_override
        build_options["config_source_override"] = config_source_override
    return build_report(
        captured.manifest,
        captured.evidence,
        **build_options,
    )
