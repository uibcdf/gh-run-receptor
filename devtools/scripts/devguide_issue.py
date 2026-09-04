#!/usr/bin/env python3
"""Open or close a GitHub issue coordinated with a developer report."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
from pathlib import Path

from devguide_reports import (
    CLOSED_STATUSES,
    DEVGUIDE,
    OPEN_STATUSES,
    ROOT,
    parse_report,
    validate_report,
)

REPO = "uibcdf/gh-run-receptor"
STATE_LABELS = {"active": "in-progress", "blocked": "blocked", "partial": "partial"}
AREA_LABELS = {
    "cli",
    "github",
    "governance",
    "packaging",
    "profiles",
    "reports",
    "security",
    "tests",
}


def gh(*args: str) -> str:
    result = subprocess.run(["gh", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return slug[:80]


def open_issue(args: argparse.Namespace) -> int:
    labels = {args.kind, *args.area}
    response = gh("label", "list", "--repo", REPO, "--limit", "200", "--json", "name")
    available = {item["name"] for item in json.loads(response)}
    missing = sorted(labels - available)
    if missing:
        raise SystemExit("Missing GitHub labels: " + ", ".join(missing))
    queue = "pending_bugs" if args.kind == "bug" else "pending_proposals"
    filename = f"{slugify(args.title)}.md"
    record = f"devguide/{queue}/{filename}"
    body = f"What   — {args.what}\nHow    — {args.how}\nWhy    — {args.why}\nRecord — {record}"
    command = ["issue", "create", "--repo", REPO, "--title", args.title, "--body", body]
    for label in sorted(labels):
        command.extend(["--label", label])
    url = gh(*command)
    number = url.rsplit("/", 1)[1]
    template = (DEVGUIDE / "templates" / "report.md").read_text(encoding="utf-8")
    template = template.replace("uibcdf/gh-run-receptor#000", f"{REPO}#{number}")
    template = template.replace("2026-01-01", dt.date.today().isoformat())
    template = template.replace(
        "One line in present tense; this becomes the issue title.", args.title
    )
    template = template.replace("area: []", f"area: {args.area!r}")
    if args.kind == "proposal":
        template = template.replace("severity: medium\n", "")
    path = DEVGUIDE / queue / filename
    path.write_text(template, encoding="utf-8")
    print(f"Opened {REPO}#{number}; complete {path.relative_to(ROOT)}")
    return 0


def close_issue(args: argparse.Namespace) -> int:
    path = Path(args.report).resolve()
    report = parse_report(path)
    errors = validate_report(report)
    status = str(report.fields.get("status", ""))
    if errors or status not in CLOSED_STATUSES or "archive" not in path.parts:
        detail = "; ".join(errors) or "report must be closed and archived"
        raise SystemExit(detail)
    issue = report.issue_number
    outcome = args.outcome or str(report.fields["summary"])
    anchor = report.fields["guard"] or report.fields["normative"]
    anchor_name = "Guard" if report.fields["guard"] else "Normative"
    body = (
        f"Decision — {status} in {args.commit}: {outcome}\n"
        f"{anchor_name} — {anchor}\nRecord — {path.relative_to(ROOT)}"
    )
    current = json.loads(
        gh("issue", "view", str(issue), "--repo", REPO, "--json", "labels")
    )
    current_labels = {item["name"] for item in current["labels"]}
    for label in sorted(current_labels & set(STATE_LABELS.values())):
        gh("issue", "edit", str(issue), "--repo", REPO, "--remove-label", label)
    gh("issue", "close", str(issue), "--repo", REPO, "--comment", body)
    print(f"Closed {REPO}#{issue}")
    return 0


def sync_issue(args: argparse.Namespace) -> int:
    path = Path(args.report).resolve()
    report = parse_report(path)
    errors = validate_report(report)
    status = str(report.fields.get("status", ""))
    if errors or status not in OPEN_STATUSES:
        detail = "; ".join(errors) or "sync requires a pending report"
        raise SystemExit(detail)
    kind = "bug" if "pending_bugs" in path.parts else "proposal"
    expected = {kind, *report.fields["area"]}
    state = STATE_LABELS.get(status)
    if state:
        expected.add(state)
    response = gh(
        "issue",
        "view",
        str(report.issue_number),
        "--repo",
        REPO,
        "--json",
        "labels,state",
    )
    issue = json.loads(response)
    if issue["state"] != "OPEN":
        raise SystemExit("pending report is attached to a closed issue")
    current = {item["name"] for item in issue["labels"]}
    managed = {"bug", "proposal", *STATE_LABELS.values(), *AREA_LABELS}
    command = ["issue", "edit", str(report.issue_number), "--repo", REPO]
    for label in sorted(expected - current):
        command.extend(["--add-label", label])
    for label in sorted((current & managed) - expected):
        command.extend(["--remove-label", label])
    if len(command) > 6:
        gh(*command)
    print(f"Synchronized {REPO}#{report.issue_number}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)
    opening = subparsers.add_parser("open")
    opening.add_argument("--kind", choices=("bug", "proposal"), required=True)
    opening.add_argument("--title", required=True)
    opening.add_argument("--area", action="append", required=True)
    opening.add_argument("--what", required=True)
    opening.add_argument("--how", required=True)
    opening.add_argument("--why", required=True)
    opening.set_defaults(handler=open_issue)
    closing = subparsers.add_parser("close")
    closing.add_argument("report")
    closing.add_argument("--commit", required=True)
    closing.add_argument("--outcome")
    closing.set_defaults(handler=close_issue)
    syncing = subparsers.add_parser("sync")
    syncing.add_argument("report")
    syncing.set_defaults(handler=sync_issue)
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
