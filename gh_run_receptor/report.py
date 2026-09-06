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
_PLATFORM_STATE_PRECEDENCE = (
    "failure",
    "timed_out",
    "cancelled",
    "action_required",
    "stale",
    "startup_failure",
    "in_progress",
    "pending",
    "queued",
    "requested",
    "waiting",
)
_CI_ROLES = (
    ("publish", ("publish", "publishing", "release", "deploy", "upload")),
    ("docs", ("documentation", "docs", "sphinx", "notebook", "notebooks")),
    ("lint", ("ruff", "lint", "format", "clippy", "type check")),
    ("coverage", ("coverage", "codecov")),
    ("test", ("test", "tests", "testing", "pytest", "smoke", "matrix", "e2e", "qt")),
    ("build", ("build", "wheel", "wheels", "package", "packages", "artifact")),
)
_DOCS_PHASES = (
    ("notebooks", ("notebook", "notebooks")),
    ("links", ("link check", "linkcheck", "links")),
    ("warnings", ("warning", "warnings")),
    ("artifact", ("artifact", "artifacts", "failure logs")),
    ("deploy", ("deploy", "deployment", "publish", "publishing", "gh pages", "github pages")),
    (
        "build",
        (
            "sphinx",
            "mkdocs",
            "build docs",
            "build documentation",
            "build site",
            "build html",
            "generate docs",
            "generate documentation",
        ),
    ),
    (
        "setup",
        (
            "setup",
            "set up",
            "checkout",
            "install",
            "environment",
            "toolchain",
            "conda",
            "complete job",
        ),
    ),
)
_RELEASE_PHASES = (
    (
        "identity",
        (
            "candidate identity",
            "release identity",
            "inject version",
            "derive version",
            "package version",
            "release tag",
            "tag",
            "ref",
        ),
    ),
    ("gate", ("validate", "validation", "verify", "verification", "test", "check", "lint")),
    ("package", ("build", "bundle", "wheel", "wheels", "sdist", "packaging", "compile")),
    (
        "publish",
        (
            "publish",
            "publishing",
            "upload package",
            "upload packages",
            "release platform",
        ),
    ),
    ("archive", ("zenodo", "doi", "citation", "archive", "archived")),
    ("artifact", ("artifact", "artifacts", "provenance")),
    (
        "setup",
        (
            "setup",
            "set up",
            "checkout",
            "install",
            "dependencies",
            "environment",
            "toolchain",
            "complete job",
        ),
    ),
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
    package_kind: str = "native",
    artifact_inventory: str = "complete",
) -> dict[str, Any]:
    if package_kind == "noarch":
        available = [artifact for artifact in artifacts if artifact.get("expired") is False]
        expired = [artifact for artifact in artifacts if artifact.get("expired") is True]
        if available:
            artifact_evidence = "available"
        elif expired and len(expired) == len(artifacts):
            artifact_evidence = "expired"
        elif artifacts:
            artifact_evidence = "observed"
        elif artifact_inventory == "complete":
            artifact_evidence = "not_observed"
        else:
            artifact_evidence = "unknown"
        counts: dict[str, int] = {}
        for job in jobs:
            state = str(job.get("conclusion") or job.get("status") or "unknown")
            counts[state] = counts.get(state, 0) + 1
        return {
            "kind": "conda",
            "package_kind": "noarch",
            "platforms": [],
            "package": {
                "job_ids": [job.get("id") for job in jobs],
                "job_counts": dict(sorted(counts.items())),
                "artifact_ids": [artifact.get("id") for artifact in artifacts],
                "available_artifact_ids": [artifact.get("id") for artifact in available],
                "expired_artifact_ids": [artifact.get("id") for artifact in expired],
                "artifact_evidence": artifact_evidence,
            },
        }
    platforms = []
    expected = set(expected_platforms or [])
    for platform in _CONDA_PLATFORMS:
        platform_jobs = [job for job in jobs if platform in str(job.get("name", "")).lower()]
        platform_artifacts = [
            artifact for artifact in artifacts if platform in str(artifact.get("name", "")).lower()
        ]
        if not platform_jobs and not platform_artifacts and platform not in expected:
            continue
        states = [
            str(job.get("conclusion") or job.get("status") or "unknown")
            for job in platform_jobs
        ]
        status = "unknown"
        for state in _PLATFORM_STATE_PRECEDENCE:
            if state in states:
                status = "failed" if state == "failure" else state
                break
        else:
            if states and len(set(states)) == 1:
                status = states[0]
            elif platform in expected and not platform_artifacts and not states:
                status = "missing"
        successful = status == "success"
        platforms.append(
            {
                "name": platform,
                "job_ids": [job.get("id") for job in platform_jobs],
                "artifact_ids": [artifact.get("id") for artifact in platform_artifacts],
                "status": status,
                "reusable": successful and bool(platform_artifacts),
                "expected": platform in expected,
            }
        )
    return {"kind": "conda", "package_kind": "native", "platforms": platforms}


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


def _matches_keywords(normalized: str, words: set[str], keywords: tuple[str, ...]) -> bool:
    return any(
        keyword in normalized if " " in keyword else keyword in words
        for keyword in keywords
    )


def _docs_phase(name: Any) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", str(name or "").lower()).strip()
    words = set(normalized.split())
    matches = {
        phase: _matches_keywords(normalized, words, keywords)
        for phase, keywords in _DOCS_PHASES
    }
    if matches["build"] and matches["deploy"]:
        return "build_deploy"
    for phase, _ in _DOCS_PHASES:
        if matches[phase]:
            return phase
    return "other"


def _docs_matrix(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for job in jobs:
        units = job["steps"] or [job]
        for unit in units:
            phase = _docs_phase(unit.get("name"))
            grouped.setdefault(phase, []).append(
                {
                    "job_id": job.get("id"),
                    "step_number": unit.get("number") if unit is not job else None,
                    "kind": "step" if unit is not job else "job",
                    "state": str(unit.get("conclusion") or unit.get("status") or "unknown"),
                }
            )
    phases = []
    order = ("build_deploy", *[name for name, _ in _DOCS_PHASES], "other")
    for phase in order:
        evidence = grouped.get(phase, [])
        if not evidence:
            continue
        counts: dict[str, int] = {}
        for item in evidence:
            counts[item["state"]] = counts.get(item["state"], 0) + 1
        phases.append(
            {
                "name": phase,
                "counts": dict(sorted(counts.items())),
                "evidence": evidence,
            }
        )
    return {"kind": "docs", "phases": phases}


def _docs_has_state(matrix: dict[str, Any], phases: set[str], state: str) -> bool:
    return any(
        phase["name"] in phases and phase["counts"].get(state, 0) > 0
        for phase in matrix["phases"]
    )


def _release_facets(name: Any) -> tuple[str, ...]:
    normalized = re.sub(r"[^a-z0-9]+", " ", str(name or "").lower()).strip()
    words = set(normalized.split())
    facets = [
        phase
        for phase, keywords in _RELEASE_PHASES
        if _matches_keywords(normalized, words, keywords)
    ]
    if "artifact" in facets and "publish" in facets:
        facets.remove("publish")
    if len(facets) > 1 and "setup" in facets:
        facets.remove("setup")
    return tuple(facets or ["other"])


def _release_matrix(subject: dict[str, Any], jobs: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for job in jobs:
        units = job["steps"] or [job]
        for unit in units:
            facets = _release_facets(unit.get("name"))
            phase = "+".join(facets)
            grouped.setdefault(phase, []).append(
                {
                    "job_id": job.get("id"),
                    "step_number": unit.get("number") if unit is not job else None,
                    "kind": "step" if unit is not job else "job",
                    "facets": list(facets),
                    "state": str(unit.get("conclusion") or unit.get("status") or "unknown"),
                }
            )
    phases = []
    simple_order = [name for name, _ in _RELEASE_PHASES]
    order = [*simple_order, "other", *sorted(set(grouped) - {*simple_order, "other"})]
    for phase in order:
        evidence = grouped.get(phase, [])
        if not evidence:
            continue
        counts: dict[str, int] = {}
        for item in evidence:
            counts[item["state"]] = counts.get(item["state"], 0) + 1
        phases.append(
            {
                "name": phase,
                "counts": dict(sorted(counts.items())),
                "evidence": evidence,
            }
        )
    successful_step_facets = {
        facet
        for phase in phases
        for item in phase["evidence"]
        if item["kind"] == "step" and item["state"] == "success"
        for facet in item["facets"]
    }
    return {
        "kind": "release",
        "identity": {
            "event": subject.get("event"),
            "head_ref": subject.get("head_ref"),
            "head_sha": subject.get("head_sha"),
            "tag_verification": "not_observed",
        },
        "verification": {
            "registry": (
                "step_success" if "publish" in successful_step_facets else "not_observed"
            ),
            "archive": (
                "step_success" if "archive" in successful_step_facets else "not_observed"
            ),
        },
        "phases": phases,
    }


def _release_has_simple_state(
    matrix: dict[str, Any], facet: str, states: set[str]
) -> bool:
    return any(
        item["facets"] == [facet] and item["state"] in states
        for phase in matrix["phases"]
        for item in phase["evidence"]
    )


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


def _non_success_label(jobs: list[dict[str, Any]], noun: str) -> str:
    prefix = "failed" if all(job.get("conclusion") == "failure" for job in jobs) else "non-success"
    return f"{prefix} {noun}"


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
    package_kind = settings.get("package_kind", "native")

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
        matrix = _conda_matrix(
            jobs,
            artifacts,
            expected_platforms,
            package_kind,
            model["completeness"]["artifact_inventory"],
        )
    elif selected_profile == "ci":
        matrix = _ci_matrix(jobs)
    elif selected_profile == "docs":
        matrix = _docs_matrix(jobs)
    elif selected_profile == "release":
        matrix = _release_matrix(model["subject"], jobs)
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
    if (
        selected_profile == "docs"
        and assessment == "FAIL"
        and _docs_has_state(matrix, {"build"}, "success")
        and _docs_has_state(matrix, {"deploy"}, "failure")
    ):
        assessment = "PARTIAL"
    if (
        selected_profile == "release"
        and assessment == "FAIL"
        and _release_has_simple_state(matrix, "package", {"success"})
        and _release_has_simple_state(matrix, "publish", {"failure", "skipped"})
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


def _render_docs_llm_failure(report: dict[str, Any]) -> str:
    subject = report["subject"]
    github = report["github"]
    receptor = report["receptor"]
    identity = subject.get("url") or (
        f"{_safe_text(subject['repository'])} run={subject['run_id']}"
    )
    counts = ",".join(f"{key}={value}" for key, value in report["job_counts"].items())
    lines = [
        (
            f"{receptor['assessment']} conclusion={_safe_text(github['conclusion'])} "
            f"status={_safe_text(github['status'])} | profile=docs | {_safe_text(identity)} "
            f"| attempt={subject['run_attempt']}"
        ),
        (
            f"workflow={_safe_text(subject['workflow'])} | "
            f"jobs={len(report['jobs'])}({counts or 'none'})"
        ),
    ]
    failed = [
        job
        for job in report["jobs"]
        if job["conclusion"] not in (None, "success", "skipped", "neutral")
    ]
    if failed:
        lines.append(_non_success_label(failed, "jobs") + ":")
        for job in failed[:MAX_FAILURES]:
            steps = ", ".join(_safe_text(step["name"] or "unnamed") for step in job["failed_steps"])
            suffix = f" | steps={steps}" if steps else ""
            lines.append(f"- {_safe_text(job['name'])} | {_safe_text(job['conclusion'])}{suffix}")
        if len(failed) > MAX_FAILURES:
            lines.append(
                f"- ... {len(failed) - MAX_FAILURES} more "
                f"{_non_success_label(failed, 'jobs')} in JSON report"
            )

    phase_summaries = []
    for phase in report["matrix"]["phases"]:
        visible_counts = phase["counts"]
        if phase["name"] in {"setup", "other"}:
            visible_counts = {
                key: value for key, value in visible_counts.items() if key != "success"
            }
        if visible_counts:
            counts_text = ",".join(f"{key}:{value}" for key, value in visible_counts.items())
            phase_summaries.append(f"{phase['name']}={counts_text}")
    lines.append("phases: " + "; ".join(phase_summaries or ["none"]))

    artifacts = report["artifacts"]
    if artifacts:
        shown = ", ".join(_safe_text(item["name"]) for item in artifacts[:MAX_ARTIFACTS])
        remainder = (
            f", ... +{len(artifacts) - MAX_ARTIFACTS}"
            if len(artifacts) > MAX_ARTIFACTS
            else ""
        )
        lines.append(f"artifacts: {shown}{remainder}")
    else:
        lines.append("artifacts: none")
    if report["causes"]:
        lines.append(f"root causes ({len(report['causes'])}):")
        for index, cause in enumerate(report["causes"][:MAX_FAILURES], start=1):
            lines.append(
                f"[{index}] {_safe_text(cause['message'])} | "
                f"jobs={len(cause['occurrences'])}"
            )
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {_safe_text(warning)}")
    return "\n".join(lines) + "\n"


def _render_release_llm_failure(report: dict[str, Any]) -> str:
    subject = report["subject"]
    github = report["github"]
    receptor = report["receptor"]
    matrix = report["matrix"]
    identity = matrix["identity"]
    lines = [
        (
            f"{receptor['assessment']} conclusion={_safe_text(github['conclusion'])} | "
            f"release event={_safe_text(identity['event'])} "
            f"ref={_safe_text(identity['head_ref'])} "
            f"sha={_safe_text(identity['head_sha'])} "
            "tag=unverified | "
            f"{_safe_text(subject['repository'])} run={subject['run_id']} "
            f"attempt={subject['run_attempt']}"
        ),
    ]
    failed = [
        job
        for job in report["jobs"]
        if job["conclusion"] not in (None, "success", "skipped", "neutral")
    ]
    failures = []
    for job in failed[:MAX_FAILURES]:
        steps = ",".join(
            _safe_text(step["name"] or "unnamed") for step in job["failed_steps"]
        )
        failures.append(steps or _safe_text(job["name"]))
    if len(failed) > MAX_FAILURES:
        failures.append(f"+{len(failed) - MAX_FAILURES} jobs in JSON")

    summaries = []
    for phase in matrix["phases"]:
        if phase["name"] in {"identity", "setup", "other"}:
            continue
        visible_counts = {
            key: value for key, value in phase["counts"].items() if key != "failure"
        }
        if visible_counts:
            states = ",".join(
                key if value == 1 else f"{key}:{value}"
                for key, value in visible_counts.items()
            )
            summaries.append(f"{phase['name']}={states}")
    artifacts = report["artifacts"]
    if artifacts:
        shown = ", ".join(_safe_text(item["name"]) for item in artifacts[:MAX_ARTIFACTS])
        remainder = (
            f", ... +{len(artifacts) - MAX_ARTIFACTS}"
            if len(artifacts) > MAX_ARTIFACTS
            else ""
        )
        artifact_text = f"{len(artifacts)}({shown}{remainder})"
    else:
        artifact_text = "0"
    workflow = Path(str(subject["workflow"])).name
    state_field = (
        "failed"
        if all(job.get("conclusion") == "failure" for job in failed)
        else "non_success"
    )
    lines.append(
        f"workflow={_safe_text(workflow)} | {state_field}={'; '.join(failures) or 'none'} | "
        f"phases={','.join(summaries) or 'none'} | "
        f"external=not_observed artifacts={artifact_text}"
    )
    if report["causes"]:
        lines.append(f"root causes ({len(report['causes'])}):")
        for index, cause in enumerate(report["causes"][:MAX_FAILURES], start=1):
            lines.append(
                f"[{index}] {_safe_text(cause['message'])} | "
                f"jobs={len(cause['occurrences'])}"
            )
    for warning in report["warnings"][:5]:
        lines.append(f"warning: {_safe_text(warning)}")
    return "\n".join(lines) + "\n"


def render_llm(report: dict[str, Any]) -> str:
    """Rendering a compact report intended for low-token inspection."""
    subject = report["subject"]
    github = report["github"]
    receptor = report["receptor"]
    if receptor["assessment"] == "PASS":
        successful_jobs = sum(job["conclusion"] == "success" for job in report["jobs"])
        fields = [
            "PASS conclusion=success",
            "release" if receptor["profile"] == "release" else f"profile={receptor['profile']}",
        ]
        if report["matrix"].get("kind") == "conda":
            if report["matrix"].get("package_kind") == "noarch":
                package = report["matrix"]["package"]
                fields.extend(
                    [
                        "package=noarch",
                        f"artifact_evidence={package['artifact_evidence']}",
                    ]
                )
            else:
                platforms = report["matrix"]["platforms"]
                successful_platforms = sum(item["status"] == "success" for item in platforms)
                fields.append(f"platforms={successful_platforms}/{len(platforms)}")
        elif report["matrix"].get("kind") == "ci":
            roles = ",".join(
                f"{role['name']}:{len(role['job_ids'])}" for role in report["matrix"]["roles"]
            )
            fields.append(f"roles={roles or 'none'}")
        elif report["matrix"].get("kind") == "docs":
            phases = ",".join(
                f"{phase['name']}:{len(phase['evidence'])}"
                for phase in report["matrix"]["phases"]
            )
            fields.append(f"phases={phases or 'none'}")
        elif report["matrix"].get("kind") == "release":
            matrix = report["matrix"]
            identity = matrix["identity"]
            phases = ",".join(
                f"{phase['name']}:{len(phase['evidence'])}"
                for phase in matrix["phases"]
                if phase["name"] not in {"identity", "setup"}
            )
            verification = matrix["verification"]
            fields.extend(
                [
                    f"event={_safe_text(identity['event'])}",
                    f"ref={_safe_text(identity['head_ref'])}",
                    f"sha={_safe_text(identity['head_sha'])}",
                    "tag=unverified",
                    f"phases={phases or 'none'}",
                    f"registry={verification['registry']}",
                    f"archive={verification['archive']}",
                ]
            )
        if report["expectations"]["missing_platforms"]:
            fields.append(
                "missing=" + ",".join(report["expectations"]["missing_platforms"])
            )
        if receptor["profile"] != "release":
            fields.append(f"jobs={successful_jobs}/{len(report['jobs'])}")
        consumer_verification = report.get("consumer_verification")
        if isinstance(consumer_verification, dict):
            fields.extend(
                [
                    f"source_facts={_safe_text(consumer_verification.get('source_facts'))}",
                    "interpretation="
                    + _safe_text(consumer_verification.get("interpretation")),
                ]
            )
            if consumer_verification.get("reporter_identity") == "verified":
                fields.append("reporter_identity=verified")
        fields.extend(
            [
                f"artifacts={len(report['artifacts'])}",
                f"{_safe_text(subject['repository'])} run={subject['run_id']}",
            ]
        )
        return " | ".join(fields) + "\n"

    if receptor["profile"] == "docs":
        return _render_docs_llm_failure(report)
    if receptor["profile"] == "release":
        return _render_release_llm_failure(report)

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
        lines.append(
            f"{_non_success_label(failed, 'groups')} ({len(groups)}, {len(failed)} jobs):"
        )
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
        label = _non_success_label(failed, "jobs")
        lines.append(f"{label} ({len(failed)}):")
        for job in failed[:MAX_FAILURES]:
            steps = ", ".join(_safe_text(step["name"] or "unnamed") for step in job["failed_steps"])
            suffix = f" | steps: {steps}" if steps else ""
            duration = _format_duration(job["duration_seconds"])
            name = _safe_text(job["name"])
            conclusion = _safe_text(job["conclusion"])
            lines.append(f"- {name} | {conclusion} | {duration}{suffix}")
        if len(failed) > MAX_FAILURES:
            lines.append(f"- ... {len(failed) - MAX_FAILURES} more {label} in JSON report")

    if report["matrix"].get("kind") == "conda":
        if report["matrix"].get("package_kind") == "noarch":
            package = report["matrix"]["package"]
            job_counts = ",".join(
                f"{key}:{value}" for key, value in package["job_counts"].items()
            )
            lines.append(
                "conda package: kind=noarch "
                f"jobs={job_counts or 'none'} artifact_evidence={package['artifact_evidence']}"
            )
        else:
            platforms = report["matrix"]["platforms"]
            reusable = [item["name"] for item in platforms if item["reusable"]]
            successful = [item["name"] for item in platforms if item["status"] == "success"]
            failed_platforms = [item["name"] for item in platforms if item["status"] == "failed"]
            missing_platforms = [item["name"] for item in platforms if item["status"] == "missing"]
            other_counts = []
            other_states = {
                item["status"]
                for item in platforms
                if item["status"] not in {"success", "failed", "missing"}
            }
            preferred_order = (*_PLATFORM_STATE_PRECEDENCE[1:], "skipped", "neutral", "unknown")
            state_order = [state for state in preferred_order if state in other_states]
            state_order.extend(sorted(other_states - set(state_order)))
            for state in state_order:
                count = sum(item["status"] == state for item in platforms)
                other_counts.append(f"{state}={count}")
            platform_summary = (
                f"conda platforms: successful={len(successful)} "
                f"failed={len(failed_platforms)}"
            )
            if other_counts:
                platform_summary += " " + " ".join(other_counts)
            platform_summary += (
                f" missing={len(missing_platforms)} artifacts={len(report['artifacts'])} "
                f"observed={len(platforms) - len(missing_platforms)}"
            )
            lines.append(platform_summary)
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
    elif report["matrix"].get("kind") == "docs":
        summaries = []
        for phase in report["matrix"]["phases"]:
            counts = ",".join(f"{key}:{value}" for key, value in phase["counts"].items())
            summaries.append(f"{phase['name']}={len(phase['evidence'])}({counts})")
        lines.append("docs phases: " + "; ".join(summaries))
    elif report["matrix"].get("kind") == "release":
        summaries = []
        for phase in report["matrix"]["phases"]:
            counts = ",".join(f"{key}:{value}" for key, value in phase["counts"].items())
            summaries.append(f"{phase['name']}={len(phase['evidence'])}({counts})")
        lines.append("release phases: " + "; ".join(summaries))

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
        if report["matrix"].get("package_kind") == "noarch":
            package = report["matrix"]["package"]
            counts = ", ".join(
                f"{key}={value}" for key, value in package["job_counts"].items()
            )
            lines.extend(
                [
                    "",
                    "Conda package",
                    "  Kind:              noarch",
                    f"  Jobs:              {counts or 'none'}",
                    f"  Artifact evidence: {package['artifact_evidence']}",
                ]
            )
        else:
            lines.extend(["", "Conda platforms"])
            for platform in report["matrix"]["platforms"]:
                reusable = ", reusable artifact" if platform["reusable"] else ""
                lines.append(f"  {platform['status']:<8} {platform['name']}{reusable}")
    elif report["matrix"].get("kind") == "ci":
        lines.extend(["", "CI roles"])
        for role in report["matrix"]["roles"]:
            counts = ", ".join(f"{key}={value}" for key, value in role["counts"].items())
            lines.append(f"  {role['name']:<10} {len(role['job_ids']):>3} jobs ({counts})")
    elif report["matrix"].get("kind") == "docs":
        lines.extend(["", "Documentation phases"])
        for phase in report["matrix"]["phases"]:
            counts = ", ".join(f"{key}={value}" for key, value in phase["counts"].items())
            lines.append(
                f"  {phase['name']:<14} {len(phase['evidence']):>3} entries ({counts})"
            )
    elif report["matrix"].get("kind") == "release":
        identity = report["matrix"]["identity"]
        verification = report["matrix"]["verification"]
        lines.extend(
            [
                "",
                "Release identity",
                f"  event             {_safe_text(identity['event'])}",
                f"  observed ref      {_safe_text(identity['head_ref'])}",
                f"  head SHA          {_safe_text(identity['head_sha'])}",
                f"  tag verification  {identity['tag_verification']}",
                "",
                "Release phases",
            ]
        )
        for phase in report["matrix"]["phases"]:
            counts = ", ".join(f"{key}={value}" for key, value in phase["counts"].items())
            lines.append(
                f"  {phase['name']:<24} {len(phase['evidence']):>3} entries ({counts})"
            )
        lines.append(
            "  verification              "
            f"registry={verification['registry']}, archive={verification['archive']}"
        )

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
