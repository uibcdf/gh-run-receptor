"""Publishing a shared-core report from a GitHub Actions step."""

from __future__ import annotations

import html
import os
import re
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from gh_run_receptor.errors import AcquisitionError, ReceptorError
from gh_run_receptor.github import _safe_error_line
from gh_run_receptor.report import render_json, render_llm
from gh_run_receptor.service import create_report

MAX_REPORT_BYTES = 8 * 1024 * 1024
MAX_SUMMARY_BYTES = 32 * 1024
MAX_REPORT_NAME = 80
_REPORT_NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,79})")
_PROFILES = {"auto", "generic", "ci", "conda", "docs", "release"}
_CAPTURE_POLICIES = {"full", "adaptive", "metadata"}
ReportFactory = Callable[..., dict[str, Any]]


def _required_path(environment: Mapping[str, str], name: str) -> Path:
    value = environment.get(name, "")
    if not value:
        raise ReceptorError(f"GitHub Actions environment is missing {name}")
    return Path(value)


def _run_id(environment: Mapping[str, str]) -> int:
    value = environment.get("INPUT_RUN_ID") or environment.get("GITHUB_RUN_ID", "")
    if not value.isdigit() or int(value) < 1:
        raise ReceptorError("run-id must be a positive integer")
    return int(value)


def _hostname(environment: Mapping[str, str]) -> str:
    parsed = urlparse(environment.get("GITHUB_SERVER_URL", "https://github.com"))
    if parsed.scheme != "https" or not parsed.hostname:
        raise ReceptorError("GITHUB_SERVER_URL must be an HTTPS URL with a hostname")
    return parsed.hostname


def _choice(environment: Mapping[str, str], name: str, allowed: set[str], default: str) -> str:
    value = environment.get(name, "").strip() or default
    if value not in allowed:
        raise ReceptorError(f"{name.removeprefix('INPUT_').lower()} has an unsupported value")
    return value


def _report_name(environment: Mapping[str, str]) -> str:
    value = environment.get("INPUT_REPORT_NAME", "").strip() or "gh-run-receptor-report"
    if len(value) > MAX_REPORT_NAME or _REPORT_NAME.fullmatch(value) is None:
        raise ReceptorError(
            "report-name must contain only letters, digits, period, underscore, or hyphen"
        )
    return value


def _publisher(environment: Mapping[str, str]) -> dict[str, str]:
    repository = (
        environment.get("RECEPTOR_ACTION_REPOSITORY", "").strip()
        or environment.get("GITHUB_REPOSITORY", "").strip()
    )
    reference = environment.get("RECEPTOR_ACTION_REF", "").strip() or "local"
    if repository.count("/") != 1 or not all(repository.split("/")):
        raise ReceptorError("action repository provenance must use OWNER/REPO form")
    if len(reference) > 200 or any(ord(character) < 32 for character in reference):
        raise ReceptorError("action ref provenance is invalid")
    return {"kind": "github_action", "repository": repository, "ref": reference}


def _failed_groups(report: dict[str, Any]) -> int:
    groups = set()
    for job in report["jobs"]:
        conclusion = job.get("conclusion")
        if conclusion in (None, "success", "skipped", "neutral"):
            continue
        steps = tuple(step.get("name") for step in job.get("failed_steps", []))
        groups.add((conclusion, steps))
    return len(groups)


def _incomplete_groups(report: dict[str, Any]) -> int:
    accepted = {"complete", "not_requested"}
    return sum(value not in accepted for value in report["completeness"].values())


def _append_outputs(path: Path, values: Mapping[str, str]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        for key, value in values.items():
            if "\n" in value or "\r" in value:
                raise ReceptorError(f"action output {key!r} is not a scalar")
            stream.write(f"{key}={value}\n")


def _success_summary(report: dict[str, Any], compact: str) -> str:
    subject = report["subject"]
    receptor = report["receptor"]
    github = report["github"]
    warnings = "".join(
        f"\n- Warning: {html.escape(str(warning))}" for warning in report["warnings"][:5]
    )
    url = html.escape(str(subject.get("url") or ""), quote=True)
    link = f"\n\n[Open source run]({url})" if url else ""
    summary = (
        "## gh-run-receptor\n\n"
        f"| Assessment | GitHub conclusion | Profile | Jobs |\n"
        f"| --- | --- | --- | ---: |\n"
        f"| `{html.escape(str(receptor['assessment']))}` | "
        f"`{html.escape(str(github.get('conclusion') or ''))}` | "
        f"`{html.escape(str(receptor['profile']))}` | {len(report['jobs'])} |\n\n"
        f"<pre>{html.escape(compact)}</pre>{warnings}{link}\n"
    )
    encoded = summary.encode("utf-8")
    if len(encoded) > MAX_SUMMARY_BYTES:
        raise ReceptorError(f"step summary exceeds the {MAX_SUMMARY_BYTES}-byte limit")
    return summary


def _safe_error(error: Exception) -> str:
    _, detail, _ = _safe_error_line(str(error).encode("utf-8", errors="replace"))
    if isinstance(error, AcquisitionError):
        return f"RECEPTOR_ERROR category={error.category}: {detail}"
    return f"RECEPTOR_ERROR: {detail}"


def _write_error(environment: Mapping[str, str], message: str) -> None:
    output = environment.get("GITHUB_OUTPUT")
    if output:
        _append_outputs(Path(output), {"report-ready": "false"})
    summary = environment.get("GITHUB_STEP_SUMMARY")
    if summary:
        text = f"## gh-run-receptor\n\n`{html.escape(message)}`\n"
        Path(summary).write_text(text[:MAX_SUMMARY_BYTES], encoding="utf-8")
    print(message, file=sys.stderr)


def run_action(
    environment: Mapping[str, str] | None = None,
    *,
    report_factory: ReportFactory = create_report,
) -> int:
    """Producing Action outputs while separating source failure from reporter failure."""
    values = os.environ if environment is None else environment
    try:
        run_id = _run_id(values)
        repository = values.get("INPUT_REPOSITORY") or values.get("GITHUB_REPOSITORY", "")
        if repository.count("/") != 1 or not all(repository.split("/")):
            raise ReceptorError("repository must use OWNER/REPO form")
        profile = _choice(values, "INPUT_PROFILE", _PROFILES, "auto")
        capture = _choice(values, "INPUT_CAPTURE", _CAPTURE_POLICIES, "adaptive")
        _choice(values, "INPUT_STRICT_REPORTER", {"true", "false"}, "false")
        report_name = _report_name(values)
        runner_temp = _required_path(values, "RUNNER_TEMP")
        output_path = _required_path(values, "GITHUB_OUTPUT")
        summary_path = _required_path(values, "GITHUB_STEP_SUMMARY")
        cache_root = runner_temp / "gh-run-receptor-action"
        report = report_factory(
            repository=repository,
            hostname=_hostname(values),
            run_id=run_id,
            profile=profile,
            capture=capture,
            cache_root=cache_root,
        )
        report["publisher"] = _publisher(values)
        rendered = render_json(report).encode("utf-8")
        if len(rendered) > MAX_REPORT_BYTES:
            raise ReceptorError(f"JSON report exceeds the {MAX_REPORT_BYTES}-byte limit")
        compact = render_llm(report)
        summary = _success_summary(report, compact)
        report_path = runner_temp / f"{report_name}.json"
        report_path.write_bytes(rendered)
        summary_path.write_text(summary, encoding="utf-8")
        _append_outputs(
            output_path,
            {
                "assessment": str(report["receptor"]["assessment"]),
                "github-conclusion": str(report["github"].get("conclusion") or ""),
                "profile": str(report["receptor"]["profile"]),
                "failed-groups": str(_failed_groups(report)),
                "incomplete-groups": str(_incomplete_groups(report)),
                "report-artifact": report_name,
                "report-path": str(report_path),
                "report-ready": "true",
            },
        )
        print(compact, end="")
        return 0
    except (ReceptorError, OSError, KeyError, TypeError, ValueError) as error:
        _write_error(values, _safe_error(error))
        return 5


if __name__ == "__main__":
    raise SystemExit(run_action())
