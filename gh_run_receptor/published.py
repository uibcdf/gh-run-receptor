"""Consuming bounded Action reports without trusting artifact claims as source facts."""

from __future__ import annotations

import hashlib
import re
import stat
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from gh_run_receptor.bundle import _strict_json
from gh_run_receptor.errors import BundleError
from gh_run_receptor.github import GitHubClient, merge_pages
from gh_run_receptor.limits import MAX_PUBLISHED_ARTIFACT_BYTES, MAX_REPORT_BYTES
from gh_run_receptor.report import exit_code, render_human, render_llm

_ARTIFACT_NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,79})")
_BASE_ASSESSMENT = {
    "success": "PASS",
    "failure": "FAIL",
    "cancelled": "CANCELLED",
    "timed_out": "TIMED_OUT",
    "action_required": "ACTION_REQUIRED",
    "stale": "STALE",
}


def _artifact_name(value: str) -> str:
    if _ARTIFACT_NAME.fullmatch(value) is None:
        raise BundleError(
            "artifact name must contain only letters, digits, period, underscore, or hyphen"
        )
    return value


def _object(container: dict[str, Any], key: str) -> dict[str, Any]:
    value = container.get(key)
    if not isinstance(value, dict):
        raise BundleError(f"published report field {key!r} is not an object")
    return value


def _validate_report_structure(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BundleError("published report is not a JSON object")
    if value.get("schema") != "gh-run-receptor.report@1":
        raise BundleError(f"unsupported published report schema: {value.get('schema')!r}")
    for key in ("subject", "github", "receptor", "completeness", "configuration", "expectations"):
        _object(value, key)
    for key in ("jobs", "artifacts", "causes", "unknowns", "warnings"):
        items = value.get(key)
        if not isinstance(items, list):
            raise BundleError(f"published report field {key!r} is not an array")
    if not all(isinstance(item, str) for item in value["warnings"]):
        raise BundleError("published report warnings must be strings")
    if not isinstance(value.get("job_counts"), dict) or not isinstance(value.get("matrix"), dict):
        raise BundleError("published report job_counts and matrix must be objects")

    subject = value["subject"]
    repository = subject.get("repository")
    if (
        not isinstance(repository, str)
        or repository.count("/") != 1
        or not all(repository.split("/"))
    ):
        raise BundleError("published report subject repository is invalid")
    for key in ("run_id", "run_attempt"):
        item = subject.get(key)
        if isinstance(item, bool) or not isinstance(item, int) or item < 1:
            raise BundleError(f"published report subject {key} is invalid")
    if not isinstance(subject.get("head_sha"), str) or not subject["head_sha"]:
        raise BundleError("published report subject head_sha is invalid")

    receptor = value["receptor"]
    if not isinstance(receptor.get("assessment"), str):
        raise BundleError("published report assessment is invalid")
    if not isinstance(receptor.get("profile"), str):
        raise BundleError("published report profile is invalid")
    if not isinstance(receptor.get("evidence_sufficient"), bool):
        raise BundleError("published report evidence_sufficient is invalid")

    publisher = _object(value, "publisher")
    publisher_repository = publisher.get("repository")
    if (
        publisher.get("kind") != "github_action"
        or not isinstance(publisher_repository, str)
        or publisher_repository.count("/") != 1
        or not all(publisher_repository.split("/"))
        or not isinstance(publisher.get("ref"), str)
        or not publisher["ref"]
    ):
        raise BundleError("published report Action provenance is invalid")
    return value


def _read_report_archive(path: Path) -> dict[str, Any]:
    if path.stat().st_size > MAX_PUBLISHED_ARTIFACT_BYTES:
        raise BundleError("downloaded report artifact exceeds the compressed-byte limit")
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) != 1:
                raise BundleError("report artifact must contain exactly one JSON file")
            member = members[0]
            name = member.filename
            mode = member.external_attr >> 16
            file_type = stat.S_IFMT(mode)
            if (
                member.is_dir()
                or Path(name).name != name
                or not name.endswith(".json")
                or member.flag_bits & 0x1
                or file_type not in (0, stat.S_IFREG)
            ):
                raise BundleError("report artifact contains an unsafe member")
            if member.file_size > MAX_REPORT_BYTES:
                raise BundleError("published report exceeds the expanded-byte limit")
            with archive.open(member) as stream:
                data = stream.read(MAX_REPORT_BYTES + 1)
            if len(data) > MAX_REPORT_BYTES or len(data) != member.file_size:
                raise BundleError("published report exceeds the expanded-byte limit")
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as error:
        raise BundleError(f"invalid report artifact ZIP: {error}") from error
    return _validate_report_structure(_strict_json(data, name))


def _verify_digest(path: Path, digest: Any) -> str | None:
    if digest is None:
        return None
    if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise BundleError("report artifact digest is invalid")
    actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != digest:
        raise BundleError("report artifact digest mismatch")
    return digest


def _verify_source(report: dict[str, Any], source: Any, repository: str) -> None:
    if not isinstance(source, dict):
        raise BundleError("source workflow-run response is not an object")
    subject = report["subject"]
    github = report["github"]
    if subject["repository"] != repository:
        raise BundleError("cross-repository published reports are not supported")
    comparisons = {
        "run ID": (subject["run_id"], source.get("id")),
        "attempt": (subject["run_attempt"], source.get("run_attempt") or 1),
        "head SHA": (subject["head_sha"], source.get("head_sha")),
        "status": (github.get("status"), source.get("status")),
        "conclusion": (github.get("conclusion"), source.get("conclusion")),
    }
    if subject.get("url") is not None:
        comparisons["URL"] = (subject["url"], source.get("html_url"))
    for label, (published, authoritative) in comparisons.items():
        if published != authoritative:
            raise BundleError(f"published report {label} conflicts with GitHub")
    if source.get("status") != "completed" or not isinstance(source.get("conclusion"), str):
        raise BundleError("published source run is not terminal")

    assessment = report["receptor"]["assessment"]
    expected = _BASE_ASSESSMENT.get(source["conclusion"], "UNKNOWN")
    allowed = {expected, "INCOMPLETE"}
    if source["conclusion"] == "success":
        allowed.add("FAIL")
    elif source["conclusion"] == "failure":
        allowed.add("PARTIAL")
    if assessment not in allowed:
        raise BundleError("published assessment conflicts with the official conclusion")
    if not report["receptor"]["evidence_sufficient"] and assessment != "INCOMPLETE":
        raise BundleError("insufficient published evidence must remain INCOMPLETE")


def consume_published_report(
    client: GitHubClient,
    repository: str,
    reporter_run_id: int,
    *,
    artifact_name: str,
) -> dict[str, Any]:
    """Downloading one report and verifying its terminal source facts."""
    if (
        isinstance(reporter_run_id, bool)
        or not isinstance(reporter_run_id, int)
        or reporter_run_id < 1
    ):
        raise BundleError("reporter run ID must be a positive integer")
    selected_name = _artifact_name(artifact_name)
    reporter = client.json(f"/repos/{repository}/actions/runs/{reporter_run_id}")
    if not isinstance(reporter, dict) or reporter.get("status") != "completed":
        raise BundleError("reporter run must be completed")
    inventory = merge_pages(
        client.json(
            f"/repos/{repository}/actions/runs/{reporter_run_id}/artifacts?per_page=100",
            paginate=True,
        ),
        "artifacts",
    )
    if not all(isinstance(item, dict) for item in inventory["artifacts"]):
        raise BundleError("reporter artifact inventory contains a non-object")
    matches = [item for item in inventory["artifacts"] if item.get("name") == selected_name]
    if len(matches) != 1:
        raise BundleError(f"expected exactly one report artifact named {selected_name!r}")
    artifact = matches[0]
    if artifact.get("expired") is not False:
        raise BundleError("report artifact is expired or has unknown availability")
    size = artifact.get("size_in_bytes")
    artifact_id = artifact.get("id")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise BundleError("report artifact has an invalid byte count")
    if size > MAX_PUBLISHED_ARTIFACT_BYTES:
        raise BundleError("report artifact exceeds the compressed-byte limit")
    if isinstance(artifact_id, bool) or not isinstance(artifact_id, int) or artifact_id < 1:
        raise BundleError("report artifact has an invalid ID")

    with tempfile.TemporaryDirectory(prefix="gh-run-receptor-published-") as temporary:
        archive = Path(temporary) / "report.zip"
        client.download(
            f"/repos/{repository}/actions/artifacts/{artifact_id}/zip",
            archive,
            max_bytes=MAX_PUBLISHED_ARTIFACT_BYTES,
        )
        if archive.stat().st_size > MAX_PUBLISHED_ARTIFACT_BYTES:
            raise BundleError("downloaded report artifact exceeds the compressed-byte limit")
        digest = _verify_digest(archive, artifact.get("digest"))
        report = _read_report_archive(archive)

    source_run_id = report["subject"]["run_id"]
    source = client.json(f"/repos/{repository}/actions/runs/{source_run_id}")
    _verify_source(report, source, repository)
    report["consumer_verification"] = {
        "source_facts": "verified",
        "interpretation": "published_not_recomputed",
        "reporter_run_id": reporter_run_id,
        "artifact_id": artifact_id,
        "artifact_name": selected_name,
        "artifact_digest": digest,
    }
    report["warnings"].append(
        "published source facts verified; profile interpretation was not independently recomputed"
    )
    try:
        render_human(report)
        render_llm(report)
        exit_code(report)
    except (KeyError, TypeError, ValueError) as error:
        raise BundleError(f"published report cannot be rendered: {error}") from error
    return report
