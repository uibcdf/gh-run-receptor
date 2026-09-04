#!/usr/bin/env python3
"""Generate compact indexes for issue-backed developer reports."""

from __future__ import annotations

import argparse
from pathlib import Path

from devguide_reports import QUEUES, ROOT, parse_report

START = "<!-- generated: devguide_index -->"
END = "<!-- /generated -->"


def render(directory: Path) -> str:
    entries = []
    for path in sorted(directory.glob("*.md")):
        if path.name == "README.md":
            continue
        report = parse_report(path)
        issue = str(report.fields["issue"])
        number = issue.rsplit("#", 1)[1]
        summary = str(report.fields["summary"])
        status = str(report.fields["status"])
        entries.append(f"- [#{number} — {summary}]({path.name}) (`{status}`)")
    return "\n".join(entries) if entries else "*No entries.*"


def update(path: Path, body: str, *, check: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    before, marker, remainder = text.partition(START)
    if not marker or END not in remainder:
        raise ValueError(f"{path.relative_to(ROOT)}: generated markers are missing")
    _, _, after = remainder.partition(END)
    expected = f"{before}{START}\n{body}\n{END}{after}"
    if text == expected:
        return False
    if check:
        return True
    path.write_text(expected, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for directory in QUEUES.values():
        readme = directory / "README.md"
        if update(readme, render(directory), check=args.check):
            stale.append(str(readme.relative_to(ROOT)))
    if args.check and stale:
        print("Stale devguide indexes: " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
