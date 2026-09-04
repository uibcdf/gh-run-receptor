"""Building and rendering bounded generic workflow reports."""

from __future__ import annotations

import json
import unicodedata
from datetime import datetime
from typing import Any

MAX_FAILURES = 10
MAX_ARTIFACTS = 10
MAX_HUMAN_JOBS = 100
MAX_TEXT_FIELD = 300
_BIDI_CONTROLS = frozenset(
    "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
)


def _safe_text(value: Any) -> str:
    text = str(value)
    cleaned = "".join(
        f"\\u{ord(character):04x}"
        if unicodedata.category(character) == "Cc" or character in _BIDI_CONTROLS
        else character
        for character in text
    )
    if len(cleaned) > MAX_TEXT_FIELD:
        return cleaned[: MAX_TEXT_FIELD - 1] + "…"
    return cleaned


def _duration_seconds(started: str | None, completed: str | None) -> int | None:
    if not started or not completed:
        return None
    try:
        start = datetime.fromisoformat(started.replace("Z", "+00:00"))
        end = datetime.fromisoformat(completed.replace("Z", "+00:00"))
    except ValueError:
        return None
    seconds = round((end - start).total_seconds())
    return seconds if seconds >= 0 else None


def _assessment(status: Any, conclusion: Any) -> str:
    if status != "completed":
        return "PENDING"
    mapping = {
        "success": "PASS",
        "failure": "FAIL",
        "cancelled": "CANCELLED",
        "timed_out": "TIMED_OUT",
        "action_required": "ACTION_REQUIRED",
        "stale": "STALE",
    }
    return mapping.get(conclusion, "UNKNOWN")


def build_report(manifest: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    """Building a generic report without changing source conclusions."""
    run = evidence["run.json"]
    workflow = evidence["workflow.json"]
    jobs = evidence["jobs.json"].get("jobs", [])
    artifacts = evidence["artifacts.json"].get("artifacts", [])

    normalized_jobs = []
    counts: dict[str, int] = {}
    for job in jobs:
        conclusion = job.get("conclusion") or job.get("status") or "unknown"
        counts[conclusion] = counts.get(conclusion, 0) + 1
        failed_steps = [
            {
                "number": step.get("number"),
                "name": step.get("name"),
                "conclusion": step.get("conclusion"),
            }
            for step in job.get("steps", [])
            if step.get("conclusion") not in (None, "success", "skipped")
        ]
        normalized_jobs.append(
            {
                "id": job.get("id"),
                "name": job.get("name"),
                "status": job.get("status"),
                "conclusion": job.get("conclusion"),
                "duration_seconds": _duration_seconds(
                    job.get("started_at"), job.get("completed_at")
                ),
                "failed_steps": failed_steps,
                "url": job.get("html_url"),
            }
        )

    normalized_jobs.sort(key=lambda item: (str(item["name"]), int(item["id"] or 0)))
    normalized_artifacts = [
        {
            "id": artifact.get("id"),
            "name": artifact.get("name"),
            "size_bytes": artifact.get("size_in_bytes"),
            "expired": artifact.get("expired"),
            "digest": artifact.get("digest"),
        }
        for artifact in artifacts
    ]
    normalized_artifacts.sort(key=lambda item: (str(item["name"]), int(item["id"] or 0)))

    return {
        "schema": "gh-run-receptor.report@1",
        "subject": {
            "repository": manifest["repository"],
            "workflow": workflow.get("path") or run.get("name"),
            "run_id": manifest["run_id"],
            "run_attempt": manifest["run_attempt"],
            "head_sha": manifest.get("head_sha"),
            "url": run.get("html_url"),
        },
        "github": {"status": run.get("status"), "conclusion": run.get("conclusion")},
        "receptor": {
            "assessment": _assessment(run.get("status"), run.get("conclusion")),
            "profile": "generic",
            "evidence_sufficient": bool(manifest.get("complete")),
        },
        "jobs": normalized_jobs,
        "job_counts": dict(sorted(counts.items())),
        "artifacts": normalized_artifacts,
        "warnings": list(manifest.get("warnings", [])),
    }


def render_json(report: dict[str, Any]) -> str:
    """Rendering canonical human-readable JSON."""
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _format_duration(seconds: int | None) -> str:
    if seconds is None:
        return "duration=?"
    minutes, remainder = divmod(seconds, 60)
    return f"duration={minutes}m{remainder:02d}s" if minutes else f"duration={remainder}s"


def render_llm(report: dict[str, Any]) -> str:
    """Rendering a compact report intended for low-token inspection."""
    subject = report["subject"]
    github = report["github"]
    receptor = report["receptor"]
    counts = ", ".join(f"{key}={value}" for key, value in report["job_counts"].items()) or "none"
    lines = [
        (
            f"{receptor['assessment']} conclusion={_safe_text(github['conclusion'])} "
            f"status={_safe_text(github['status'])} | {_safe_text(subject['repository'])} | "
            f"run={subject['run_id']} attempt={subject['run_attempt']}"
        ),
        f"workflow: {_safe_text(subject['workflow'])} | jobs: {len(report['jobs'])} ({counts})",
    ]

    failed = [
        job
        for job in report["jobs"]
        if job["conclusion"] not in (None, "success", "skipped", "neutral")
    ]
    if failed:
        lines.append(f"failed jobs ({len(failed)}):")
        for job in failed[:MAX_FAILURES]:
            steps = ", ".join(_safe_text(step["name"] or "unnamed") for step in job["failed_steps"])
            suffix = f" | steps: {steps}" if steps else ""
            duration = _format_duration(job["duration_seconds"])
            name = _safe_text(job["name"])
            conclusion = _safe_text(job["conclusion"])
            lines.append(f"- {name} | {conclusion} | {duration}{suffix}")
        if len(failed) > MAX_FAILURES:
            lines.append(f"- ... {len(failed) - MAX_FAILURES} more failed jobs in JSON report")

    artifacts = report["artifacts"]
    if artifacts:
        shown = ", ".join(_safe_text(item["name"]) for item in artifacts[:MAX_ARTIFACTS])
        remainder = (
            f", ... +{len(artifacts) - MAX_ARTIFACTS}"
            if len(artifacts) > MAX_ARTIFACTS
            else ""
        )
        lines.append(f"artifacts ({len(artifacts)}): {shown}{remainder}")
    else:
        lines.append("artifacts: none")

    for warning in report["warnings"][:5]:
        lines.append(f"warning: {_safe_text(warning)}")
    if subject.get("url"):
        lines.append(f"run: {_safe_text(subject['url'])}")
    return "\n".join(lines) + "\n"


def render_human(report: dict[str, Any]) -> str:
    """Rendering a bounded, explanatory report for terminal readers."""
    subject = report["subject"]
    github = report["github"]
    receptor = report["receptor"]
    github_state = (
        f"status={_safe_text(github['status'])}, "
        f"conclusion={_safe_text(github['conclusion'])}"
    )
    lines = [
        f"gh-run-receptor: {receptor['assessment']}",
        "",
        f"Repository:  {_safe_text(subject['repository'])}",
        f"Workflow:    {_safe_text(subject['workflow'])}",
        f"Run:         {subject['run_id']} (attempt {subject['run_attempt']})",
        f"GitHub:      {github_state}",
        f"Evidence:    {'complete' if receptor['evidence_sufficient'] else 'incomplete'}",
        "",
        f"Jobs ({len(report['jobs'])})",
    ]
    for job in report["jobs"][:MAX_HUMAN_JOBS]:
        duration = _format_duration(job["duration_seconds"]).removeprefix("duration=")
        state = _safe_text(job["conclusion"] or job["status"] or "unknown")
        lines.append(f"  {state:<12} {duration:>8}  {_safe_text(job['name'])}")
        for step in job["failed_steps"]:
            lines.append(f"      failed step {step['number']}: {_safe_text(step['name'])}")
    if len(report["jobs"]) > MAX_HUMAN_JOBS:
        lines.append(f"  ... {len(report['jobs']) - MAX_HUMAN_JOBS} additional jobs in JSON output")

    lines.extend(["", f"Artifacts ({len(report['artifacts'])})"])
    for artifact in report["artifacts"][:MAX_ARTIFACTS]:
        size = artifact["size_bytes"]
        size_text = f"{size} bytes" if size is not None else "size unknown"
        expired = " [expired]" if artifact["expired"] else ""
        lines.append(f"  {_safe_text(artifact['name'])} ({size_text}){expired}")
    if not report["artifacts"]:
        lines.append("  None")
    if len(report["artifacts"]) > MAX_ARTIFACTS:
        lines.append(
            f"  ... {len(report['artifacts']) - MAX_ARTIFACTS} additional artifacts in JSON output"
        )

    if report["warnings"]:
        lines.extend(["", "Warnings"])
        lines.extend(f"  {_safe_text(warning)}" for warning in report["warnings"][:5])
    if subject.get("url"):
        lines.extend(["", f"GitHub run: {_safe_text(subject['url'])}"])
    return "\n".join(lines) + "\n"


def exit_code(report: dict[str, Any]) -> int:
    """Mapping authoritative run state to the provisional CLI exit contract."""
    if not report["receptor"]["evidence_sufficient"]:
        return 4
    assessment = report["receptor"]["assessment"]
    if assessment == "PASS":
        return 0
    if assessment == "FAIL":
        return 1
    if assessment == "PENDING":
        return 3
    if assessment in {"CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STALE", "UNKNOWN"}:
        return 2
    return 5
