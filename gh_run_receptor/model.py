"""Normalizing captured GitHub evidence without profile-specific interpretation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from gh_run_receptor.contracts import schema_id
from gh_run_receptor.errors import BundleError

MODEL_SCHEMA = schema_id("model", 1)
KNOWN_STATUSES = {"completed", "in_progress", "pending", "queued", "requested", "waiting"}
KNOWN_CONCLUSIONS = {
    "action_required",
    "cancelled",
    "failure",
    "neutral",
    "skipped",
    "stale",
    "startup_failure",
    "success",
    "timed_out",
}


def _duration_seconds(started: str | None, completed: str | None) -> int | None:
    if not started or not completed:
        return None
    try:
        start = datetime.fromisoformat(started.replace("Z", "+00:00"))
        end = datetime.fromisoformat(completed.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    seconds = round((end - start).total_seconds())
    return seconds if seconds >= 0 else None


def _object(evidence: dict[str, Any], member: str) -> dict[str, Any]:
    value = evidence.get(member)
    if not isinstance(value, dict):
        raise BundleError(f"bundle member is not a JSON object: {member}")
    return value


def _array_member(container: dict[str, Any], key: str, member: str) -> list[dict[str, Any]]:
    value = container.get(key)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise BundleError(f"bundle member has invalid {key!r} collection: {member}")
    return value


def _completeness(manifest: dict[str, Any], workflow: dict[str, Any]) -> dict[str, str]:
    log_captured = any(member.get("path") == "logs.zip" for member in manifest["members"])
    policy = manifest["capture_policy"]
    log_warning = any(str(item).startswith("logs unavailable:") for item in manifest["warnings"])
    if log_captured:
        logs = "complete"
    elif log_warning:
        logs = "unavailable"
    elif policy == "metadata":
        logs = "not_requested"
    else:
        logs = "not_requested"
    event_members = [
        member
        for member in manifest["members"]
        if member.get("kind") == "gh-run-receptor.producer_events"
    ]
    if event_members:
        producer_events = "complete"
    elif any(str(item).startswith("producer events invalid") for item in manifest["warnings"]):
        producer_events = "invalid"
    elif any(str(item).startswith("producer events unavailable") for item in manifest["warnings"]):
        producer_events = "unavailable"
    else:
        producer_events = "not_requested"
    return {
        "metadata": "complete",
        "workflow": "unavailable" if "unavailable" in workflow else "complete",
        "jobs": "complete",
        "checks": "complete",
        "artifact_inventory": "complete",
        "artifact_content": "not_requested",
        "logs": logs,
        "producer_events": producer_events,
    }


def _producer_events(manifest: dict[str, Any], evidence: dict[str, Any]) -> list[dict[str, Any]]:
    normalized = []
    for member in manifest["members"]:
        if member.get("kind") != "gh-run-receptor.producer_events":
            continue
        name = member["path"]
        document = _object(evidence, name)
        for index, event in enumerate(document["events"]):
            normalized.append(
                {
                    **event,
                    "producer": dict(document["producer"]),
                    "invocation": dict(document["subject"]),
                    "source": {
                        "member": name,
                        "json_pointer": f"/events/{index}",
                        "artifact_id": member.get("artifact_id"),
                        "artifact_name": member.get("artifact_name"),
                        "artifact_digest": member.get("artifact_digest"),
                    },
                }
            )
    normalized.sort(
        key=lambda item: (
            str(item["platform"]),
            str(item["artifact"]),
            str(item["producer"]["repository"]),
            str(item["invocation"]["job_key"]),
            -1
            if item["invocation"]["matrix_index"] is None
            else int(item["invocation"]["matrix_index"]),
        )
    )
    return normalized


def normalize_evidence(manifest: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    """Normalizing validated source evidence into ``model@1``."""
    run = _object(evidence, "run.json")
    workflow = _object(evidence, "workflow.json")
    jobs_source = _array_member(_object(evidence, "jobs.json"), "jobs", "jobs.json")
    artifacts_source = _array_member(
        _object(evidence, "artifacts.json"), "artifacts", "artifacts.json"
    )
    _array_member(_object(evidence, "checks.json"), "check_runs", "checks.json")

    jobs = []
    counts: dict[str, int] = {}
    unknowns = []
    for index, job in enumerate(jobs_source):
        status = job.get("status")
        conclusion = job.get("conclusion")
        count_key = conclusion or status or "unknown"
        counts[str(count_key)] = counts.get(str(count_key), 0) + 1
        if status is not None and status not in KNOWN_STATUSES:
            unknowns.append(
                {
                    "kind": "github.job.status",
                    "value": str(status),
                    "source": {"member": "jobs.json", "json_pointer": f"/jobs/{index}/status"},
                }
            )
        if conclusion is not None and conclusion not in KNOWN_CONCLUSIONS:
            unknowns.append(
                {
                    "kind": "github.job.conclusion",
                    "value": str(conclusion),
                    "source": {
                        "member": "jobs.json",
                        "json_pointer": f"/jobs/{index}/conclusion",
                    },
                }
            )
        steps = []
        failed_steps = []
        for step_index, step in enumerate(job.get("steps") or []):
            if not isinstance(step, dict):
                raise BundleError(f"job {index} contains a non-object step")
            step_status = step.get("status")
            step_conclusion = step.get("conclusion")
            source = {
                "member": "jobs.json",
                "json_pointer": f"/jobs/{index}/steps/{step_index}",
            }
            normalized_step = {
                "number": step.get("number"),
                "name": step.get("name"),
                "status": step_status,
                "conclusion": step_conclusion,
                "source": source,
            }
            steps.append(normalized_step)
            if step_status is not None and step_status not in KNOWN_STATUSES:
                unknowns.append(
                    {
                        "kind": "github.step.status",
                        "value": str(step_status),
                        "source": source,
                    }
                )
            if step_conclusion is not None and step_conclusion not in KNOWN_CONCLUSIONS:
                unknowns.append(
                    {
                        "kind": "github.step.conclusion",
                        "value": str(step_conclusion),
                        "source": source,
                    }
                )
            if step_conclusion not in (None, "success", "skipped"):
                failed_steps.append(normalized_step)
        jobs.append(
            {
                "id": job.get("id"),
                "name": job.get("name"),
                "status": status,
                "conclusion": conclusion,
                "duration_seconds": _duration_seconds(
                    job.get("started_at"), job.get("completed_at")
                ),
                "steps": steps,
                "failed_steps": failed_steps,
                "url": job.get("html_url"),
                "source": {"member": "jobs.json", "json_pointer": f"/jobs/{index}"},
            }
        )

    artifacts = [
        {
            "id": artifact.get("id"),
            "name": artifact.get("name"),
            "size_bytes": artifact.get("size_in_bytes"),
            "expired": artifact.get("expired"),
            "digest": artifact.get("digest"),
            "source": {"member": "artifacts.json", "json_pointer": f"/artifacts/{index}"},
        }
        for index, artifact in enumerate(artifacts_source)
    ]
    jobs.sort(key=lambda item: (str(item["name"]), int(item["id"] or 0)))
    artifacts.sort(key=lambda item: (str(item["name"]), int(item["id"] or 0)))
    workflow_name = workflow.get("path") or run.get("name")
    return {
        "schema": MODEL_SCHEMA,
        "subject": {
            "repository": manifest["repository"],
            "workflow": workflow_name,
            "run_id": manifest["run_id"],
            "run_attempt": manifest["run_attempt"],
            "head_sha": manifest.get("head_sha"),
            "event": run.get("event"),
            "head_ref": run.get("head_branch"),
            "url": run.get("html_url"),
        },
        "github": {"status": run.get("status"), "conclusion": run.get("conclusion")},
        "bundle_complete": manifest["complete"],
        "completeness": _completeness(manifest, workflow),
        "jobs": jobs,
        "job_counts": dict(sorted(counts.items())),
        "artifacts": artifacts,
        "producer_events": _producer_events(manifest, evidence),
        "unknowns": unknowns,
        "warnings": list(manifest["warnings"]),
    }
