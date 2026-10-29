"""Validating bounded structured evidence emitted by workflow producers."""

from __future__ import annotations

import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path
from typing import Any

from gh_run_receptor.contracts import schema_id, upgrade_contract
from gh_run_receptor.errors import BundleError, ContractError

EVENTS_SCHEMA = schema_id("events", 1)
EVENT_DOCUMENT_NAME = "gh-run-receptor-events.json"
EVENT_ARTIFACT_STEM = "gh-run-receptor-events-v1"
MAX_EVENT_ARTIFACTS = 50
MAX_EVENT_ARCHIVE_BYTES = 4 * 1024 * 1024
MAX_EVENT_DOCUMENT_BYTES = 1024 * 1024
MAX_EVENTS = 500
MAX_EVENT_STRING = 512
_SAFE_SUFFIX = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,159})")
_REPOSITORY = re.compile(r"[^/\s]+/[^/\s]+")
_PLATFORM = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+){0,3}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_RESULTS = {"success", "failure", "not_requested"}


def event_artifact_prefix(run_id: int, run_attempt: int) -> str:
    """Building the reserved artifact prefix for one exact run attempt."""
    for label, value in (("run ID", run_id), ("run attempt", run_attempt)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise BundleError(f"producer-event {label} must be a positive integer")
    return f"{EVENT_ARTIFACT_STEM}-{run_id}-{run_attempt}-"


def select_event_artifacts(
    artifacts: list[dict[str, Any]], run_id: int, run_attempt: int
) -> list[dict[str, Any]]:
    """Selecting bounded, attempt-qualified producer-event artifacts."""
    prefix = event_artifact_prefix(run_id, run_attempt)
    selected = []
    for artifact in artifacts:
        name = artifact.get("name")
        if not isinstance(name, str) or not name.startswith(prefix):
            continue
        suffix = name[len(prefix) :]
        if _SAFE_SUFFIX.fullmatch(suffix) is None:
            raise BundleError("producer-event artifact has an unsafe identity suffix")
        artifact_id = artifact.get("id")
        size = artifact.get("size_in_bytes")
        if isinstance(artifact_id, bool) or not isinstance(artifact_id, int) or artifact_id < 1:
            raise BundleError("producer-event artifact has an invalid ID")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise BundleError("producer-event artifact has an invalid byte count")
        if size > MAX_EVENT_ARCHIVE_BYTES:
            raise BundleError("producer-event artifact exceeds the compressed-byte limit")
        if artifact.get("expired") is not False:
            raise BundleError("producer-event artifact is expired or has unknown availability")
        digest = artifact.get("digest")
        if digest is not None and (
            not isinstance(digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None
        ):
            raise BundleError("producer-event artifact has an invalid digest")
        selected.append(artifact)
    selected.sort(key=lambda item: (str(item["name"]), int(item["id"])))
    if len(selected) > MAX_EVENT_ARTIFACTS:
        raise BundleError(
            f"producer-event artifact count exceeds the {MAX_EVENT_ARTIFACTS}-artifact limit"
        )
    return selected


def _strict_json(data: bytes) -> Any:
    def object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise BundleError(f"duplicate JSON key in {EVENT_DOCUMENT_NAME}: {key!r}")
            value[key] = item
        return value

    def reject_constant(value: str) -> None:
        raise BundleError(f"non-finite JSON number in {EVENT_DOCUMENT_NAME}: {value}")

    try:
        return json.loads(
            data,
            object_pairs_hook=object_without_duplicates,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BundleError(f"invalid JSON in {EVENT_DOCUMENT_NAME}: {error}") from error


def _required_string(container: dict[str, Any], key: str, context: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value or len(value) > MAX_EVENT_STRING:
        raise BundleError(f"producer events {context} {key!r} is invalid")
    return value


def validate_event_document(
    value: Any,
    *,
    repository: str,
    run_id: int,
    run_attempt: int,
    head_sha: str | None,
) -> dict[str, Any]:
    """Validating one producer document against its captured source identity."""
    try:
        value = upgrade_contract(value, "events")
    except ContractError as error:
        raise BundleError(str(error)) from error
    if set(value) != {"schema", "producer", "subject", "events"}:
        raise BundleError("producer events document has invalid root fields")

    producer = value["producer"]
    if not isinstance(producer, dict) or set(producer) != {"repository", "ref"}:
        raise BundleError("producer events document has invalid producer identity")
    if _REPOSITORY.fullmatch(_required_string(producer, "repository", "producer")) is None:
        raise BundleError("producer events repository identity is invalid")
    _required_string(producer, "ref", "producer")

    subject = value["subject"]
    required_subject = {
        "repository",
        "run_id",
        "run_attempt",
        "head_sha",
        "job_key",
        "matrix_index",
    }
    if not isinstance(subject, dict) or set(subject) != required_subject:
        raise BundleError("producer events document has invalid subject identity")
    _required_string(subject, "repository", "subject")
    _required_string(subject, "head_sha", "subject")
    _required_string(subject, "job_key", "subject")
    matrix_index = subject["matrix_index"]
    if matrix_index is not None and (
        isinstance(matrix_index, bool) or not isinstance(matrix_index, int) or matrix_index < 0
    ):
        raise BundleError("producer events subject matrix index is invalid")
    expected = {
        "repository": repository,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "head_sha": head_sha,
    }
    for key, expected_value in expected.items():
        if subject.get(key) != expected_value:
            label = key.replace("_", " ")
            raise BundleError(f"producer events subject {label} conflicts with bundle")

    events = value["events"]
    if not isinstance(events, list) or not events or len(events) > MAX_EVENTS:
        raise BundleError("producer events collection is empty or exceeds its limit")
    identities = set()
    for index, event in enumerate(events):
        required = {"kind", "platform", "artifact", "sha256", "build", "upload"}
        optional = {"python_versions"}
        invalid_fields = (
            not isinstance(event, dict)
            or not required <= set(event)
            or bool(set(event) - required - optional)
        )
        if invalid_fields:
            raise BundleError(f"producer event {index} has invalid fields")
        if event["kind"] != "conda.package":
            raise BundleError(f"producer event {index} has unsupported kind")
        platform = _required_string(event, "platform", f"event {index}")
        artifact = _required_string(event, "artifact", f"event {index}")
        if _PLATFORM.fullmatch(platform) is None:
            raise BundleError(f"producer event {index} has invalid platform")
        if Path(artifact).name != artifact:
            raise BundleError(f"producer event {index} has unsafe artifact name")
        digest = _required_string(event, "sha256", f"event {index}")
        if _SHA256.fullmatch(digest) is None:
            raise BundleError(f"producer event {index} has invalid artifact digest")
        if event["build"] not in _RESULTS or event["upload"] not in _RESULTS:
            raise BundleError(f"producer event {index} has unsupported result")
        versions = event.get("python_versions", [])
        if (
            not isinstance(versions, list)
            or len(versions) > 20
            or not all(isinstance(item, str) and 0 < len(item) <= 40 for item in versions)
            or len(versions) != len(set(versions))
        ):
            raise BundleError(f"producer event {index} has invalid Python versions")
        identity = (platform, artifact, digest)
        if identity in identities:
            raise BundleError(f"producer event {index} duplicates a package identity")
        identities.add(identity)
    return value


def read_event_archive(
    path: Path,
    *,
    repository: str,
    run_id: int,
    run_attempt: int,
    head_sha: str | None,
) -> tuple[bytes, dict[str, Any]]:
    """Reading one safe single-document producer artifact."""
    if path.stat().st_size > MAX_EVENT_ARCHIVE_BYTES:
        raise BundleError("downloaded producer-event artifact exceeds the compressed-byte limit")
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) != 1:
                raise BundleError("producer-event artifact must contain exactly one JSON file")
            member = members[0]
            mode = member.external_attr >> 16
            file_type = stat.S_IFMT(mode)
            if (
                member.filename != EVENT_DOCUMENT_NAME
                or member.is_dir()
                or member.flag_bits & 0x1
                or file_type not in (0, stat.S_IFREG)
            ):
                raise BundleError("producer-event artifact contains an unsafe member")
            if member.file_size > MAX_EVENT_DOCUMENT_BYTES:
                raise BundleError("producer-event document exceeds the expanded-byte limit")
            with archive.open(member) as stream:
                data = stream.read(MAX_EVENT_DOCUMENT_BYTES + 1)
            if len(data) > MAX_EVENT_DOCUMENT_BYTES or len(data) != member.file_size:
                raise BundleError("producer-event document exceeds the expanded-byte limit")
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as error:
        raise BundleError(f"invalid producer-event artifact ZIP: {error}") from error
    document = validate_event_document(
        _strict_json(data),
        repository=repository,
        run_id=run_id,
        run_attempt=run_attempt,
        head_sha=head_sha,
    )
    return data, document


def verify_event_archive_digest(path: Path, expected: Any) -> str:
    """Verifying an optional GitHub artifact digest and returning the local digest."""
    actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    if expected is not None and actual != expected:
        raise BundleError("producer-event artifact digest mismatch")
    return actual
