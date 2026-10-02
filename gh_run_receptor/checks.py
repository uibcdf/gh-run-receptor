"""Capturing and normalizing bounded job-linked check annotations."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from gh_run_receptor.errors import AcquisitionError, BundleError
from gh_run_receptor.logs import safe_diagnostic_text

MAX_ANNOTATION_CHECKS = 50
MAX_ANNOTATIONS_PER_CHECK = 100
MAX_ANNOTATION_MESSAGE = 4096
MAX_ANNOTATION_PAGE_BYTES = 2 * 1024 * 1024
TERMINATION_CONCLUSIONS = frozenset({"cancelled", "timed_out"})
ANNOTATION_STATES = frozenset({"complete", "partial", "unavailable", "invalid", "not_requested"})


def job_check_id(job: dict[str, Any], repository: str, hostname: str) -> int | None:
    """Reading an exact same-repository check URL without following remote URLs."""
    root = "https://api.github.com" if hostname == "github.com" else f"https://{hostname}/api/v3"
    prefix = f"{root}/repos/{repository}/check-runs/"
    value = job.get("check_run_url")
    if not isinstance(value, str) or not value.startswith(prefix):
        return None
    suffix = value[len(prefix) :]
    if not suffix.isascii() or not suffix.isdecimal() or len(suffix) > 20 or int(suffix) < 1:
        return None
    return int(suffix)


def validate_annotations(value: Any) -> list[dict[str, Any]]:
    """Validating one bounded annotations page while retaining unknown fields."""
    if not isinstance(value, list) or len(value) > MAX_ANNOTATIONS_PER_CHECK:
        raise BundleError("check annotations are not a bounded array")
    try:
        page = json.dumps(
            value, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode()
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as error:
        raise BundleError("check annotations are not valid UTF-8 JSON") from error
    if len(page) > MAX_ANNOTATION_PAGE_BYTES:
        raise BundleError("check annotations exceed the page-byte limit")
    for annotation in value:
        if not isinstance(annotation, dict):
            raise BundleError("check annotation is not an object")
        message = annotation.get("message")
        if not isinstance(message, str) or len(message) > MAX_ANNOTATION_MESSAGE:
            raise BundleError("check annotation message is missing or exceeds its limit")
        if (
            not isinstance(annotation.get("annotation_level"), str)
            or len(annotation["annotation_level"]) > 64
        ):
            raise BundleError("check annotation level is invalid")
    return value


def capture_termination_annotations(
    client: Any,
    repository: str,
    run: dict[str, Any],
    jobs: dict[str, Any],
    checks: dict[str, Any],
) -> list[str]:
    """Adding at most one annotations request per linked terminal job check.

    Requested missing, invalid, or truncated evidence produces explicit warnings.
    The caller retains those warnings in the bundle's ordinary completeness path.
    """
    linked = {}
    ambiguous = set()
    for job in jobs["jobs"]:
        check_id = job_check_id(job, repository, client.hostname)
        if check_id is None:
            continue
        if check_id in linked:
            ambiguous.add(check_id)
        linked[check_id] = job
    check_ids = Counter(
        check["id"]
        for check in checks["check_runs"]
        if isinstance(check.get("id"), int) and not isinstance(check["id"], bool)
    )
    warnings = []
    requested = 0
    seen = set()
    for check in checks["check_runs"]:
        check_id = check.get("id")
        if isinstance(check_id, bool) or not isinstance(check_id, int) or check_id not in linked:
            continue
        check["annotations_state"] = "not_requested"
        job = linked[check_id]
        if job.get("status") != "completed" or job.get("conclusion") not in TERMINATION_CONCLUSIONS:
            continue
        if (
            check_id in ambiguous
            or check_ids[check_id] != 1
            or check_id in seen
            or not run.get("head_sha")
            or check.get("head_sha") != run.get("head_sha")
            or not run.get("check_suite_id")
            or not isinstance(check.get("check_suite"), dict)
            or check["check_suite"].get("id") != run.get("check_suite_id")
            or check.get("status") != "completed"
            or check.get("conclusion") != job.get("conclusion")
            or job.get("run_id", run.get("id")) != run.get("id")
            or job.get("run_attempt", run.get("run_attempt")) != run.get("run_attempt")
            or job.get("head_sha", run.get("head_sha")) != run.get("head_sha")
        ):
            check["annotations_state"] = "invalid"
            warnings.append(f"check annotations invalid identity for check {check_id}")
            continue
        seen.add(check_id)
        output = check.get("output")
        count = output.get("annotations_count") if isinstance(output, dict) else None
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            continue
        if count == 0:
            check["annotations"] = []
            check["annotations_state"] = "complete"
            continue
        if requested >= MAX_ANNOTATION_CHECKS:
            check["annotations_state"] = "partial"
            warnings.append(f"check annotations exceed the {MAX_ANNOTATION_CHECKS}-check limit")
            continue
        requested += 1
        try:
            annotations = validate_annotations(
                client.json(
                    f"/repos/{repository}/check-runs/{check_id}/annotations"
                    f"?per_page={MAX_ANNOTATIONS_PER_CHECK}",
                    max_bytes=MAX_ANNOTATION_PAGE_BYTES,
                )
            )
            check["annotations"] = annotations
            complete = len(annotations) == count
            check["annotations_state"] = "complete" if complete else "partial"
            if not complete:
                warnings.append(f"check annotations partial for check {check_id}")
        except AcquisitionError as error:
            check["annotations_state"] = "unavailable"
            warnings.append(f"check annotations unavailable for check {check_id}: {error}")
        except BundleError as error:
            check["annotations_state"] = "invalid"
            warnings.append(f"check annotations invalid for check {check_id}: {error}")
    return warnings


def normalize_checks(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preserving annotation provenance separately from termination interpretation."""
    normalized = []
    for index, check in enumerate(checks):
        state = check.get("annotations_state", "not_requested")
        if not isinstance(state, str) or state not in ANNOTATION_STATES:
            raise BundleError("check annotations have an invalid evidence state")
        annotations = validate_annotations(check.get("annotations", []))
        suite = check.get("check_suite")
        normalized.append(
            {
                "id": check.get("id"),
                "head_sha": check.get("head_sha"),
                "check_suite_id": suite.get("id") if isinstance(suite, dict) else None,
                "status": check.get("status"),
                "conclusion": check.get("conclusion"),
                "source": {"member": "checks.json", "json_pointer": f"/check_runs/{index}"},
                "annotation_evidence": state,
                "annotations": [
                    {
                        "message": safe_diagnostic_text(annotation["message"]),
                        "level": annotation["annotation_level"],
                        "source": {
                            "member": "checks.json",
                            "json_pointer": f"/check_runs/{index}/annotations/{position}",
                        },
                    }
                    for position, annotation in enumerate(annotations)
                ],
            }
        )
    return normalized


def annotation_completeness(checks: list[dict[str, Any]]) -> str:
    """Aggregating explicitly requested annotation evidence without inventing absence."""
    states = {check["annotation_evidence"] for check in checks}
    return next(
        (state for state in ("invalid", "unavailable", "partial", "complete") if state in states),
        "not_requested",
    )
