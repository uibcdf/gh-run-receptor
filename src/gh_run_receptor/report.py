"""Building and rendering bounded generic workflow reports."""

from __future__ import annotations

import json
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from gh_run_receptor.logs import extract_causes

MAX_FAILURES = 10
MAX_ARTIFACTS = 10
MAX_HUMAN_JOBS = 100
MAX_TEXT_FIELD = 300
_BIDI_CONTROLS = frozenset(
    "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
)
_CONDA_PLATFORMS = ("linux-64", "linux-aarch64", "osx-64", "osx-arm64", "win-64")


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


def _detect_profile(workflow: Any, jobs: list[dict[str, Any]]) -> str:
    workflow_text = str(workflow).lower()
    observed = {
        platform
        for platform in _CONDA_PLATFORMS
        if any(platform in str(job.get("name", "")).lower() for job in jobs)
    }
    if len(observed) >= 2 and ("conda" in workflow_text or "rattler" in workflow_text):
        return "conda"
    return "generic"


def _conda_matrix(jobs: list[dict[str, Any]], artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    platforms = []
    for platform in _CONDA_PLATFORMS:
        platform_jobs = [job for job in jobs if platform in str(job.get("name", "")).lower()]
        platform_artifacts = [
            artifact for artifact in artifacts if platform in str(artifact.get("name", "")).lower()
        ]
        if not platform_jobs and not platform_artifacts:
            continue
        failed = any(job.get("conclusion") == "failure" for job in platform_jobs)
        successful = any(job.get("conclusion") == "success" for job in platform_jobs)
        platforms.append(
            {
                "name": platform,
                "job_ids": [job.get("id") for job in platform_jobs],
                "artifact_ids": [artifact.get("id") for artifact in platform_artifacts],
                "status": "failed" if failed else "success" if successful else "unknown",
                "reusable": successful and bool(platform_artifacts),
            }
        )
    return {"kind": "conda", "platforms": platforms}


def build_report(
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    *,
    profile: str = "generic",
    bundle_directory: Path | None = None,
) -> dict[str, Any]:
    """Building a generic report without changing source conclusions."""
    run = evidence["run.json"]
    workflow = evidence["workflow.json"]
    jobs = evidence["jobs.json"].get("jobs", [])
    artifacts = evidence["artifacts.json"].get("artifacts", [])
    selected_profile = (
        _detect_profile(workflow.get("path") or run.get("name"), jobs)
        if profile == "auto"
        else profile
    )

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

    failed_jobs = [job for job in normalized_jobs if job["conclusion"] == "failure"]
    log_member = next(
        (member for member in manifest.get("members", []) if member.get("path") == "logs.zip"), None
    )
    causes: list[dict[str, Any]] = []
    analysis_warnings: list[str] = []
    cause_evidence = "not_captured"
    if log_member and bundle_directory is not None:
        causes, analysis_warnings = extract_causes(bundle_directory / "logs.zip", failed_jobs)
        diagnosed_jobs = {
            occurrence["job_id"]
            for cause in causes
            for occurrence in cause["occurrences"]
        }
        cause_evidence = "complete" if len(diagnosed_jobs) == len(failed_jobs) else "partial"

    matrix = (
        _conda_matrix(normalized_jobs, normalized_artifacts)
        if selected_profile == "conda"
        else {}
    )
    assessment = _assessment(run.get("status"), run.get("conclusion"))
    if (
        selected_profile == "conda"
        and assessment == "FAIL"
        and any(platform["reusable"] for platform in matrix["platforms"])
    ):
        assessment = "PARTIAL"

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
            "assessment": assessment,
            "profile": selected_profile,
            "evidence_sufficient": bool(manifest.get("complete")),
            "cause_evidence": cause_evidence,
        },
        "jobs": normalized_jobs,
        "job_counts": dict(sorted(counts.items())),
        "artifacts": normalized_artifacts,
        "matrix": matrix,
        "causes": causes,
        "warnings": [*manifest.get("warnings", []), *analysis_warnings],
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
            f"run={subject['run_id']} attempt={subject['run_attempt']} | "
            f"profile={receptor['profile']}"
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

    if report["matrix"]:
        platforms = report["matrix"]["platforms"]
        reusable = [item["name"] for item in platforms if item["reusable"]]
        failed_platforms = [item["name"] for item in platforms if item["status"] == "failed"]
        lines.append(
            f"conda platforms: reusable={len(reusable)} failed={len(failed_platforms)} "
            f"observed={len(platforms)}"
        )
        if reusable:
            lines.append(f"reusable: {', '.join(reusable)}")

    if report["causes"]:
        lines.append(f"root causes ({len(report['causes'])}):")
        for index, cause in enumerate(report["causes"][:MAX_FAILURES], start=1):
            lines.append(
                f"[{index}] {_safe_text(cause['message'])} | jobs={len(cause['occurrences'])}"
            )
            sample = cause["occurrences"][0]
            lines.append(f"    evidence: {_safe_text(sample['member'])}:{sample['line']}")

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
        f"Profile:     {receptor['profile']}",
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

    if report["matrix"]:
        lines.extend(["", "Conda platforms"])
        for platform in report["matrix"]["platforms"]:
            reusable = ", reusable artifact" if platform["reusable"] else ""
            lines.append(f"  {platform['status']:<8} {platform['name']}{reusable}")

    if report["causes"]:
        lines.extend(["", f"Root causes ({len(report['causes'])})"])
        for cause in report["causes"][:MAX_FAILURES]:
            lines.append(
                f"  {_safe_text(cause['message'])} ({len(cause['occurrences'])} jobs)"
            )
            for occurrence in cause["occurrences"][:5]:
                lines.append(
                    f"    {_safe_text(occurrence['job_name'])}: "
                    f"{_safe_text(occurrence['member'])}:{occurrence['line']}"
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
    if assessment in {"FAIL", "PARTIAL"}:
        return 1
    if assessment == "PENDING":
        return 3
    if assessment in {"CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STALE", "UNKNOWN"}:
        return 2
    return 5
