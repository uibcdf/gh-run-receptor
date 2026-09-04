"""Building and rendering bounded generic workflow reports."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from gh_run_receptor.config import select_rule
from gh_run_receptor.logs import extract_causes
from gh_run_receptor.model import normalize_evidence

MAX_FAILURES = 10
MAX_ARTIFACTS = 10
MAX_HUMAN_JOBS = 100
MAX_TEXT_FIELD = 300
_BIDI_CONTROLS = frozenset(
    "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
)
_CONDA_PLATFORMS = ("linux-64", "linux-aarch64", "osx-64", "osx-arm64", "win-64")
_CI_ROLES = (
    ("publish", ("publish", "publishing", "release", "deploy", "upload")),
    ("docs", ("documentation", "docs", "sphinx", "notebook", "notebooks")),
    ("lint", ("ruff", "lint", "format", "clippy", "type check")),
    ("coverage", ("coverage", "codecov")),
    ("test", ("test", "tests", "testing", "pytest", "smoke", "matrix", "e2e", "qt")),
    ("build", ("build", "wheel", "wheels", "package", "packages", "artifact")),
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


def _conda_matrix(
    jobs: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    expected_platforms: list[str] | None = None,
) -> dict[str, Any]:
    platforms = []
    expected = set(expected_platforms or [])
    for platform in _CONDA_PLATFORMS:
        platform_jobs = [job for job in jobs if platform in str(job.get("name", "")).lower()]
        platform_artifacts = [
            artifact for artifact in artifacts if platform in str(artifact.get("name", "")).lower()
        ]
        if not platform_jobs and not platform_artifacts and platform not in expected:
            continue
        failed = any(job.get("conclusion") == "failure" for job in platform_jobs)
        successful = any(job.get("conclusion") == "success" for job in platform_jobs)
        platforms.append(
            {
                "name": platform,
                "job_ids": [job.get("id") for job in platform_jobs],
                "artifact_ids": [artifact.get("id") for artifact in platform_artifacts],
                "status": (
                    "failed"
                    if failed
                    else "success"
                    if successful
                    else "missing"
                    if platform in expected and not platform_artifacts
                    else "unknown"
                ),
                "reusable": successful and bool(platform_artifacts),
                "expected": platform in expected,
            }
        )
    return {"kind": "conda", "platforms": platforms}


def _ci_role(name: Any) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", str(name or "").lower()).strip()
    words = set(normalized.split())
    for role, keywords in _CI_ROLES:
        matched = any(
            keyword in normalized if " " in keyword else keyword in words
            for keyword in keywords
        )
        if matched:
            return role
    return "other"


def _ci_matrix(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for job in jobs:
        grouped.setdefault(_ci_role(job.get("name")), []).append(job)
    roles = []
    for role in (*[name for name, _ in _CI_ROLES], "other"):
        role_jobs = grouped.get(role, [])
        if not role_jobs:
            continue
        counts: dict[str, int] = {}
        for job in role_jobs:
            state = str(job.get("conclusion") or job.get("status") or "unknown")
            counts[state] = counts.get(state, 0) + 1
        roles.append(
            {
                "name": role,
                "job_ids": [job.get("id") for job in role_jobs],
                "counts": dict(sorted(counts.items())),
            }
        )
    return {"kind": "ci", "roles": roles}


def _ci_failure_groups(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, tuple[str, ...]], list[dict[str, Any]]] = {}
    for job in jobs:
        if job["conclusion"] in (None, "success", "skipped", "neutral"):
            continue
        steps = tuple(str(step["name"] or "unnamed") for step in job["failed_steps"])
        grouped.setdefault((job["conclusion"], steps), []).append(job)
    groups = []
    for (conclusion, steps), members in grouped.items():
        groups.append(
            {
                "conclusion": conclusion,
                "steps": steps,
                "jobs": members,
            }
        )
    groups.sort(key=lambda item: (-len(item["jobs"]), str(item["steps"]), str(item["conclusion"])))
    return groups


def build_report(
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    *,
    profile: str = "generic",
    bundle_directory: Path | None = None,
) -> dict[str, Any]:
    """Building a generic report without changing source conclusions."""
    model = normalize_evidence(manifest, evidence)
    jobs = model["jobs"]
    artifacts = model["artifacts"]
    workflow = evidence["workflow.json"]
    config_capture = evidence.get("config.json")
    selected_rule = None
    config_source = None
    if isinstance(config_capture, dict):
        config_source = config_capture.get("source")
        config = config_capture.get("config")
        if isinstance(config, dict):
            selected_rule = select_rule(
                config,
                path=workflow.get("path"),
                workflow_id=workflow.get("id"),
                name=workflow.get("name") or evidence["run.json"].get("name"),
            )
    if profile != "auto":
        selected_profile = profile
    elif selected_rule is not None:
        selected_profile = selected_rule["profile"]
    else:
        selected_profile = _detect_profile(model["subject"]["workflow"], jobs)
    settings = selected_rule.get("settings", {}) if selected_rule else {}
    expected_platforms = settings.get("expected_platforms")

    failed_jobs = [job for job in jobs if job["conclusion"] == "failure"]
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

    if selected_profile == "conda":
        matrix = _conda_matrix(jobs, artifacts, expected_platforms)
    elif selected_profile == "ci":
        matrix = _ci_matrix(jobs)
    else:
        matrix = {}
    missing_platforms = (
        [item["name"] for item in matrix["platforms"] if item["status"] == "missing"]
        if matrix.get("kind") == "conda"
        else []
    )
    assessment = _assessment(model["github"]["status"], model["github"]["conclusion"])
    if not model["bundle_complete"]:
        assessment = "INCOMPLETE"
    if (
        selected_profile == "conda"
        and assessment == "FAIL"
        and any(platform["reusable"] for platform in matrix["platforms"])
    ):
        assessment = "PARTIAL"
    if missing_platforms and assessment == "PASS":
        assessment = "FAIL"

    return {
        "schema": "gh-run-receptor.report@1",
        "subject": model["subject"],
        "github": model["github"],
        "receptor": {
            "assessment": assessment,
            "profile": selected_profile,
            "profile_version": 1,
            "evidence_sufficient": model["bundle_complete"],
            "cause_evidence": cause_evidence,
        },
        "completeness": model["completeness"],
        "configuration": {
            "matched": selected_rule is not None,
            "source": config_source,
            "match": selected_rule.get("match") if selected_rule else None,
            "profile": selected_rule.get("profile") if selected_rule else None,
            "settings": settings,
        },
        "expectations": {
            "satisfied": not missing_platforms,
            "missing_platforms": missing_platforms,
        },
        "jobs": jobs,
        "job_counts": model["job_counts"],
        "artifacts": artifacts,
        "matrix": matrix,
        "causes": causes,
        "unknowns": model["unknowns"],
        "warnings": [*model["warnings"], *analysis_warnings],
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
    if receptor["assessment"] == "PASS":
        successful_jobs = sum(job["conclusion"] == "success" for job in report["jobs"])
        fields = ["PASS conclusion=success", f"profile={receptor['profile']}"]
        if report["matrix"].get("kind") == "conda":
            platforms = report["matrix"]["platforms"]
            successful_platforms = sum(item["status"] == "success" for item in platforms)
            fields.append(f"platforms={successful_platforms}/{len(platforms)}")
        elif report["matrix"].get("kind") == "ci":
            roles = ",".join(
                f"{role['name']}:{len(role['job_ids'])}" for role in report["matrix"]["roles"]
            )
            fields.append(f"roles={roles or 'none'}")
        if report["expectations"]["missing_platforms"]:
            fields.append(
                "missing=" + ",".join(report["expectations"]["missing_platforms"])
            )
        fields.extend(
            [
                f"jobs={successful_jobs}/{len(report['jobs'])}",
                f"artifacts={len(report['artifacts'])}",
                f"{_safe_text(subject['repository'])} run={subject['run_id']}",
            ]
        )
        return " | ".join(fields) + "\n"

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
    if failed and receptor["profile"] == "ci":
        groups = _ci_failure_groups(report["jobs"])
        lines.append(f"failed groups ({len(groups)}, {len(failed)} jobs):")
        for group in groups[:MAX_FAILURES]:
            members = group["jobs"]
            steps = ", ".join(_safe_text(step) for step in group["steps"])
            step_suffix = f" | steps: {steps}" if steps else ""
            if len(members) == 1:
                member = members[0]
                lines.append(
                    f"- {_safe_text(member['name'])} | {_safe_text(group['conclusion'])}"
                    f"{step_suffix}"
                )
            else:
                lines.append(
                    f"- {len(members)} jobs | {_safe_text(group['conclusion'])}{step_suffix} | "
                    f"sample: {_safe_text(members[0]['name'])} (+{len(members) - 1})"
                )
        if len(groups) > MAX_FAILURES:
            lines.append(f"- ... {len(groups) - MAX_FAILURES} more groups in JSON report")
    elif failed:
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

    if report["matrix"].get("kind") == "conda":
        platforms = report["matrix"]["platforms"]
        reusable = [item["name"] for item in platforms if item["reusable"]]
        successful = [item["name"] for item in platforms if item["status"] == "success"]
        failed_platforms = [item["name"] for item in platforms if item["status"] == "failed"]
        missing_platforms = [item["name"] for item in platforms if item["status"] == "missing"]
        lines.append(
            f"conda platforms: successful={len(successful)} failed={len(failed_platforms)} "
            f"missing={len(missing_platforms)} artifacts={len(report['artifacts'])} "
            f"observed={len(platforms) - len(missing_platforms)}"
        )
        if missing_platforms:
            lines.append(f"missing expected: {', '.join(missing_platforms)}")
        if reusable:
            lines.append(f"reusable: {', '.join(reusable)}")
    elif report["matrix"].get("kind") == "ci":
        summaries = []
        for role in report["matrix"]["roles"]:
            counts = ",".join(f"{key}:{value}" for key, value in role["counts"].items())
            summaries.append(f"{role['name']}={len(role['job_ids'])}({counts})")
        lines.append("ci roles: " + "; ".join(summaries))

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

    if report["matrix"].get("kind") == "conda":
        lines.extend(["", "Conda platforms"])
        for platform in report["matrix"]["platforms"]:
            reusable = ", reusable artifact" if platform["reusable"] else ""
            lines.append(f"  {platform['status']:<8} {platform['name']}{reusable}")
    elif report["matrix"].get("kind") == "ci":
        lines.extend(["", "CI roles"])
        for role in report["matrix"]["roles"]:
            counts = ", ".join(f"{key}={value}" for key, value in role["counts"].items())
            lines.append(f"  {role['name']:<10} {len(role['job_ids']):>3} jobs ({counts})")

    if report["configuration"]["matched"]:
        source = report["configuration"]["source"] or {}
        match = report["configuration"]["match"] or {}
        match_key, match_value = next(iter(match.items()))
        lines.extend(
            [
                "",
                "Repository configuration",
                f"  Source: {source.get('path', '?')} at {source.get('ref', '?')}",
                f"  Rule:   {match_key}={_safe_text(match_value)}",
            ]
        )

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
    if assessment == "INCOMPLETE":
        return 4
    return 5
