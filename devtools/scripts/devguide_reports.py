#!/usr/bin/env python3
"""Parsing and validation helpers for issue-backed developer reports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEVGUIDE = ROOT / "devguide"
OPEN_STATUSES = {"open", "active", "blocked", "partial"}
CLOSED_STATUSES = {"resolved", "withdrawn", "superseded"}
VERIFICATIONS = {"reproduced", "measured", "inspected", "upstream", "asserted"}
SEVERITIES = {"critical", "high", "medium", "low"}
ISSUE_RE = re.compile(r"^uibcdf/gh-run-receptor#([1-9][0-9]*)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

QUEUES = {
    "pending_bugs": DEVGUIDE / "pending_bugs",
    "pending_proposals": DEVGUIDE / "pending_proposals",
    "resolved_bugs": DEVGUIDE / "archive" / "resolved_bugs",
    "withdrawn_bugs": DEVGUIDE / "archive" / "withdrawn_bugs",
    "resolved_proposals": DEVGUIDE / "archive" / "resolved_proposals",
    "withdrawn_proposals": DEVGUIDE / "archive" / "withdrawn_proposals",
}


@dataclass(frozen=True)
class Report:
    path: Path
    fields: dict[str, object]

    @property
    def issue_number(self) -> int:
        match = ISSUE_RE.fullmatch(str(self.fields["issue"]))
        if match is None:  # pragma: no cover - validation produces the useful error
            raise ValueError(f"invalid issue reference in {self.path}")
        return int(match.group(1))


def _value(raw: str) -> object:
    raw = raw.strip()
    if not raw:
        return ""
    if raw.startswith("[") and raw.endswith("]"):
        contents = raw[1:-1].strip()
        if not contents:
            return []
        return [item.strip().strip('"\'') for item in contents.split(",")]
    return raw.strip('"\'')


def parse_report(path: Path) -> Report:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"{path.relative_to(ROOT)}: missing YAML front matter")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ValueError(f"{path.relative_to(ROOT)}: unterminated YAML front matter") from error
    fields: dict[str, object] = {}
    for number, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"{path.relative_to(ROOT)}:{number}: expected key: value")
        key, raw = line.split(":", 1)
        key = key.strip()
        if not key or key in fields:
            raise ValueError(f"{path.relative_to(ROOT)}:{number}: invalid or duplicate key")
        fields[key] = _value(raw)
    return Report(path, fields)


def iter_reports() -> list[Report]:
    reports = []
    for directory in QUEUES.values():
        reports.extend(
            parse_report(path)
            for path in sorted(directory.glob("*.md"))
            if path.name != "README.md"
        )
    return reports


def validate_report(report: Report) -> list[str]:
    rel = report.path.relative_to(ROOT)
    fields = report.fields
    errors: list[str] = []
    required = {
        "summary",
        "issue",
        "status",
        "opened",
        "closed",
        "verification",
        "area",
        "guard",
        "normative",
        "blocked_by",
        "supersedes",
    }
    for key in sorted(required - fields.keys()):
        errors.append(f"{rel}: missing field {key!r}")
    if errors:
        return errors
    if not str(fields["summary"]).strip():
        errors.append(f"{rel}: summary must not be empty")
    if ISSUE_RE.fullmatch(str(fields["issue"])) is None:
        errors.append(f"{rel}: issue must match uibcdf/gh-run-receptor#<number>")
    status = str(fields["status"])
    if status not in OPEN_STATUSES | CLOSED_STATUSES:
        errors.append(f"{rel}: invalid status {status!r}")
    if DATE_RE.fullmatch(str(fields["opened"])) is None:
        errors.append(f"{rel}: opened must be an ISO date")
    if str(fields["verification"]) not in VERIFICATIONS:
        errors.append(f"{rel}: invalid verification {fields['verification']!r}")
    for key in ("area", "blocked_by", "supersedes"):
        if not isinstance(fields[key], list):
            errors.append(f"{rel}: {key} must be a list")
    if isinstance(fields["area"], list) and not fields["area"]:
        errors.append(f"{rel}: area must contain at least one label")

    pending = any(part.startswith("pending_") for part in report.path.parts)
    if pending and status not in OPEN_STATUSES:
        errors.append(f"{rel}: pending report must have an open status")
    if not pending and status not in CLOSED_STATUSES:
        errors.append(f"{rel}: archived report must have a closed status")
    if status in CLOSED_STATUSES:
        if DATE_RE.fullmatch(str(fields["closed"])) is None:
            errors.append(f"{rel}: closed status requires an ISO closing date")
    elif fields["closed"]:
        errors.append(f"{rel}: open status cannot have a closing date")
    if status == "blocked" and not fields["blocked_by"]:
        errors.append(f"{rel}: blocked status requires blocked_by")
    if status == "resolved" and not (fields["guard"] or fields["normative"]):
        errors.append(f"{rel}: resolved status requires guard or normative")
    if status == "superseded" and not fields["supersedes"]:
        errors.append(f"{rel}: superseded status requires supersedes")
    if "resolved_" in report.path.parent.name and status != "resolved":
        errors.append(f"{rel}: resolved archive requires resolved status")
    if "withdrawn_" in report.path.parent.name and status not in {"withdrawn", "superseded"}:
        errors.append(f"{rel}: withdrawn archive requires withdrawn or superseded status")

    for key in ("blocked_by", "supersedes"):
        if isinstance(fields[key], list):
            for reference in fields[key]:
                if re.fullmatch(r"^uibcdf/[A-Za-z0-9_.-]+#[1-9][0-9]*$", reference) is None:
                    errors.append(f"{rel}: invalid issue reference in {key}: {reference}")

    is_bug = "bugs" in report.path.parent.name
    if is_bug:
        if fields.get("severity") not in SEVERITIES:
            errors.append(f"{rel}: bug requires a valid severity")
    elif "severity" in fields:
        errors.append(f"{rel}: proposal must not define severity")

    if fields["guard"] and not (ROOT / str(fields["guard"])).exists():
        errors.append(f"{rel}: guard does not exist: {fields['guard']}")
    if fields["normative"] and not (DEVGUIDE / str(fields["normative"])).exists():
        errors.append(f"{rel}: normative document does not exist: {fields['normative']}")
    return errors


def validate_all() -> list[str]:
    errors: list[str] = []
    reports: list[Report] = []
    try:
        reports = iter_reports()
    except ValueError as error:
        errors.append(str(error))
    seen: dict[str, Path] = {}
    for report in reports:
        errors.extend(validate_report(report))
        issue = str(report.fields.get("issue", ""))
        if issue in seen:
            errors.append(
                f"{report.path.relative_to(ROOT)}: issue duplicates "
                f"{seen[issue].relative_to(ROOT)}"
            )
        else:
            seen[issue] = report.path
    return errors
