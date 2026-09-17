"""Aggregating independent workflow reports without merging source truth."""

from __future__ import annotations

import json
import unicodedata
from collections import Counter
from typing import Any

from gh_run_receptor import exit_codes
from gh_run_receptor.contracts import schema_id
from gh_run_receptor.errors import BundleError
from gh_run_receptor.report import exit_code as report_exit_code

AGGREGATE_SCHEMA = schema_id("aggregate", 1)
MIN_SOURCES = 2
MAX_SOURCES = 50
MAX_RENDERED_SOURCES = 20
MAX_WARNINGS = 10
MAX_TEXT_VALUE = 240
REQUIRED_DIMENSIONS = ("metadata", "jobs", "artifact_inventory")
_BIDI_CONTROLS = frozenset(
    "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
)


def _safe(value: Any) -> str:
    text = " ".join(str(value).split())
    cleaned = "".join(
        f"\\u{ord(character):04x}"
        if unicodedata.category(character) == "Cc" or character in _BIDI_CONTROLS
        else character
        for character in text
    )
    return cleaned[:MAX_TEXT_VALUE] + ("..." if len(cleaned) > MAX_TEXT_VALUE else "")


def _count(values: list[Any]) -> dict[str, int]:
    counts = Counter("none" if value is None else str(value) for value in values)
    return dict(sorted(counts.items()))


def _source(report: dict[str, Any]) -> dict[str, Any]:
    subject = report["subject"]
    receptor = report["receptor"]
    completeness = {key: report["completeness"].get(key) for key in REQUIRED_DIMENSIONS}
    sufficient = bool(receptor.get("evidence_sufficient")) and all(
        value == "complete" for value in completeness.values()
    )
    return {
        "repository": subject["repository"],
        "workflow": subject.get("workflow"),
        "run_id": subject["run_id"],
        "run_attempt": subject["run_attempt"],
        "head_sha": subject.get("head_sha"),
        "url": subject.get("url"),
        "profile": receptor["profile"],
        "status": report["github"].get("status"),
        "conclusion": report["github"].get("conclusion"),
        "assessment": receptor["assessment"],
        "evidence_sufficient": sufficient,
        "completeness": completeness,
        "jobs": {"total": len(report["jobs"]), "counts": report["job_counts"]},
        "artifacts": {"total": len(report["artifacts"])},
        "exit_code": report_exit_code(report),
    }


def _assessment(sources: list[dict[str, Any]]) -> str:
    codes = {source["exit_code"] for source in sources}
    if exit_codes.FAILURE in codes:
        return "FAIL"
    if exit_codes.TERMINAL_NON_SUCCESS in codes:
        return "NON_SUCCESS"
    if exit_codes.PENDING in codes:
        return "PENDING"
    if exit_codes.INCOMPLETE in codes:
        return "INCOMPLETE"
    if codes == {exit_codes.SUCCESS}:
        return "PASS"
    raise BundleError("aggregate contains an unsupported source exit status")


def build_aggregate(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Building a bounded aggregate while retaining every report identity."""
    if not MIN_SOURCES <= len(reports) <= MAX_SOURCES:
        raise BundleError(
            f"aggregate requires between {MIN_SOURCES} and {MAX_SOURCES} source reports"
        )
    sources = [_source(report) for report in reports]
    identities = [
        (source["repository"], source["run_id"], source["run_attempt"]) for source in sources
    ]
    if len(set(identities)) != len(identities):
        raise BundleError("aggregate source run attempts must be unique")
    sources.sort(
        key=lambda source: (
            source["repository"],
            str(source["workflow"] or ""),
            source["run_id"],
            source["run_attempt"],
        )
    )
    workflow_identities = [
        f"{source['repository']}:{source['workflow'] or '(unknown)'}" for source in sources
    ]
    warnings = [
        f"source evidence is incomplete: {source['repository']} "
        f"run={source['run_id']} attempt={source['run_attempt']}"
        for source in sources
        if not source["evidence_sufficient"]
    ]
    return {
        "schema": AGGREGATE_SCHEMA,
        "assessment": _assessment(sources),
        "evidence_sufficient": all(source["evidence_sufficient"] for source in sources),
        "source_count": len(sources),
        "summary": {
            "assessment_counts": _count([source["assessment"] for source in sources]),
            "status_counts": _count([source["status"] for source in sources]),
            "conclusion_counts": _count([source["conclusion"] for source in sources]),
            "profile_counts": _count([source["profile"] for source in sources]),
            "repository_counts": _count([source["repository"] for source in sources]),
            "workflow_counts": _count(workflow_identities),
        },
        "totals": {
            "jobs": sum(source["jobs"]["total"] for source in sources),
            "artifacts": sum(source["artifacts"]["total"] for source in sources),
        },
        "sources": sources,
        "warnings": warnings,
    }


def render_json(aggregate: dict[str, Any]) -> str:
    """Rendering deterministic aggregate JSON."""
    return json.dumps(aggregate, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _counts_text(values: dict[str, int]) -> str:
    return ",".join(f"{_safe(key)}:{value}" for key, value in values.items()) or "none"


def _source_line(index: int, source: dict[str, Any]) -> str:
    evidence = "complete" if source["evidence_sufficient"] else "incomplete"
    return (
        f"[{index}] {_safe(source['assessment'])} conclusion={_safe(source['conclusion'])} "
        f"status={_safe(source['status'])} | {_safe(source['repository'])} | "
        f"workflow={_safe(source['workflow'])} | run={source['run_id']} "
        f"attempt={source['run_attempt']} | profile={_safe(source['profile'])} "
        f"jobs={source['jobs']['total']} artifacts={source['artifacts']['total']} "
        f"evidence={evidence}"
    )


def render_llm(aggregate: dict[str, Any]) -> str:
    """Rendering a bounded multi-run aggregate for language-model consumption."""
    summary = aggregate["summary"]
    evidence = "complete" if aggregate["evidence_sufficient"] else "incomplete"
    lines = [
        f"{aggregate['assessment']} aggregate sources={aggregate['source_count']} | "
        f"assessments={_counts_text(summary['assessment_counts'])} | "
        f"jobs={aggregate['totals']['jobs']} artifacts={aggregate['totals']['artifacts']} | "
        f"repositories={len(summary['repository_counts'])} "
        f"workflows={len(summary['workflow_counts'])} | evidence={evidence}"
    ]
    lines.extend(
        _source_line(index, source)
        for index, source in enumerate(aggregate["sources"][:MAX_RENDERED_SOURCES], start=1)
    )
    omitted = len(aggregate["sources"]) - MAX_RENDERED_SOURCES
    if omitted > 0:
        lines.append(f"... {omitted} more sources in JSON aggregate")
    lines.extend(f"warning: {_safe(item)}" for item in aggregate["warnings"][:MAX_WARNINGS])
    return "\n".join(lines) + "\n"


def render_human(aggregate: dict[str, Any]) -> str:
    """Rendering a bounded explanatory multi-run aggregate."""
    summary = aggregate["summary"]
    evidence = "complete" if aggregate["evidence_sufficient"] else "incomplete"
    lines = [
        f"Workflow aggregate: {aggregate['assessment']}",
        f"Sources: {aggregate['source_count']}; evidence: {evidence}",
        f"Assessments: {_counts_text(summary['assessment_counts'])}",
        f"Repositories: {len(summary['repository_counts'])}; "
        f"workflows: {len(summary['workflow_counts'])}; "
        f"jobs: {aggregate['totals']['jobs']}; artifacts: {aggregate['totals']['artifacts']}",
        "",
        "Source runs",
    ]
    lines.extend(
        "  " + _source_line(index, source)
        for index, source in enumerate(aggregate["sources"][:MAX_RENDERED_SOURCES], start=1)
    )
    omitted = len(aggregate["sources"]) - MAX_RENDERED_SOURCES
    if omitted > 0:
        lines.append(f"  ... {omitted} more sources in JSON aggregate")
    if aggregate["warnings"]:
        lines.extend(["", "Warnings"])
        lines.extend(f"  {_safe(item)}" for item in aggregate["warnings"][:MAX_WARNINGS])
    return "\n".join(lines) + "\n"


def exit_code(aggregate: dict[str, Any]) -> int:
    """Returning the strongest known source outcome without hiding uncertainty."""
    return {
        "PASS": exit_codes.SUCCESS,
        "FAIL": exit_codes.FAILURE,
        "NON_SUCCESS": exit_codes.TERMINAL_NON_SUCCESS,
        "PENDING": exit_codes.PENDING,
        "INCOMPLETE": exit_codes.INCOMPLETE,
    }.get(aggregate.get("assessment"), exit_codes.RECEPTOR_ERROR)
