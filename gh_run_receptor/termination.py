"""Interpreting native termination facts without promoting textual hints."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from gh_run_receptor.checks import TERMINATION_CONCLUSIONS

_EXECUTION_LIMIT = re.compile(
    r"The job has exceeded the maximum execution time of "
    r"(?P<limit>(?:[0-9]{1,6}h)?(?:[0-9]{1,6}m)?[0-9]{1,6}s)\.?"
)


def termination_diagnostics(model: dict[str, Any]) -> dict[str, Any] | None:
    """Returning source-bound job diagnostics; cancellation causality stays unknown.

    An annotation can be emitted by workflow content. Even an exact observed
    execution-limit message is a diagnostic hint, never verified timeout causality.
    """
    checks = {}
    duplicates = set()
    for check in model.get("checks", []):
        check_id = check["id"]
        if isinstance(check_id, bool) or not isinstance(check_id, int):
            continue
        if check_id in checks:
            duplicates.add(check_id)
        checks[check_id] = check
    jobs = []
    job_check_ids = Counter(
        job["check_run_id"] for job in model["jobs"] if isinstance(job.get("check_run_id"), int)
    )
    for job in model["jobs"]:
        if job["status"] != "completed" or job["conclusion"] not in TERMINATION_CONCLUSIONS:
            continue
        check_id = job.get("check_run_id")
        check = checks.get(check_id)
        hints = []
        state = "not_requested"
        if check is not None:
            state = check["annotation_evidence"]
            identity_matches = (
                check_id not in duplicates
                and job_check_ids[check_id] == 1
                and bool(model["subject"]["head_sha"])
                and check["head_sha"] == model["subject"]["head_sha"]
                and bool(model["subject"].get("check_suite_id"))
                and check["check_suite_id"] == model["subject"]["check_suite_id"]
                and check["status"] == job["status"]
                and check["conclusion"] == job["conclusion"]
                and state in {"complete", "partial"}
            )
            if identity_matches:
                for annotation in check["annotations"]:
                    match = _EXECUTION_LIMIT.fullmatch(annotation["message"])
                    if annotation["level"] == "failure" and match is not None:
                        hints.append(
                            {
                                "kind": "job_execution_limit",
                                "verification": "diagnostic_hint",
                                "message": f"job execution limit reported ({match.group('limit')})",
                                "source": annotation["source"],
                            }
                        )
                        break
            elif state in {"complete", "partial"}:
                state = "invalid"
        jobs.append(
            {
                "job_id": job["id"],
                "job_name": job["name"],
                "conclusion": job["conclusion"],
                "cause": "native_timeout" if job["conclusion"] == "timed_out" else "unknown",
                "source": job["source"],
                "annotation_evidence": state,
                "hints": hints,
            }
        )
    conclusion = model["github"]["conclusion"]
    if not jobs and conclusion not in TERMINATION_CONCLUSIONS:
        return None
    return {
        "source_conclusion": conclusion,
        "cause": "native_timeout" if conclusion == "timed_out" else "unknown",
        "jobs": jobs,
    }
