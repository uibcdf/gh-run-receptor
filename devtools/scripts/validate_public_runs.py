#!/usr/bin/env python3
"""Validating the live, non-UIBCDF portability corpus."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "devtools" / "public_runs.toml"
MAX_REPORT_BYTES = 512


class AcquisitionFailure(RuntimeError):
    """Representing unavailable external evidence."""


class SemanticFailure(RuntimeError):
    """Representing disagreement in acquired evidence."""


@dataclass(frozen=True)
class PublicRun:
    repository: str
    run_id: int
    attempt: int
    event: str
    conclusion: str
    minimum_jobs: int
    offline_replay: bool = False


Runner = Callable[..., subprocess.CompletedProcess[str]]


def load_manifest(path: Path) -> list[PublicRun]:
    """Loading and validating the public-run manifest."""

    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != 1 or not isinstance(payload.get("runs"), list):
        raise SemanticFailure("manifest must use schema 1 and contain runs")
    entries: list[PublicRun] = []
    for item in payload["runs"]:
        try:
            entry = PublicRun(**item)
        except (TypeError, ValueError) as exc:
            raise SemanticFailure(f"invalid manifest entry: {exc}") from exc
        owner, separator, name = entry.repository.partition("/")
        if not owner or not separator or not name or owner.casefold() == "uibcdf":
            raise SemanticFailure("corpus repositories must be non-UIBCDF OWNER/REPO names")
        if entry.run_id <= 0 or entry.attempt <= 0 or entry.minimum_jobs <= 0:
            raise SemanticFailure("run identifiers, attempts, and minimum_jobs must be positive")
        if entry.conclusion != "success":
            raise SemanticFailure("the initial portability corpus requires successful runs")
        entries.append(entry)
    if len(entries) < 3 or len({item.repository for item in entries}) < 3:
        raise SemanticFailure("corpus must contain at least three distinct repositories")
    if not any(item.offline_replay for item in entries):
        raise SemanticFailure("corpus must require at least one offline replay")
    return entries


def _run(runner: Runner, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return runner(command, capture_output=True, text=True, check=False)


def _json_output(result: subprocess.CompletedProcess[str], label: str) -> dict:
    if result.returncode != 0:
        detail = " ".join(result.stderr.split())[:240]
        raise AcquisitionFailure(f"{label} unavailable (exit {result.returncode}): {detail}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SemanticFailure(f"{label} returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise SemanticFailure(f"{label} JSON must be an object")
    return payload


def _receptor_command(entry: PublicRun, *arguments: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "gh_run_receptor",
        "--repo",
        entry.repository,
        "--receptor",
        "llm",
        "--profile",
        "generic",
        *arguments,
    ]


def _check_report(entry: PublicRun, report: dict, native: dict) -> None:
    subject = report.get("subject")
    github = report.get("github")
    counts = report.get("job_counts")
    if not all(isinstance(item, dict) for item in (subject, github, counts)):
        raise SemanticFailure(f"{entry.repository} report lacks required objects")
    expected = {
        "repository": entry.repository,
        "run_id": entry.run_id,
        "run_attempt": entry.attempt,
        "event": entry.event,
    }
    for key, value in expected.items():
        if subject.get(key) != value:
            raise SemanticFailure(f"{entry.repository} report {key} disagrees with manifest")
    if github.get("conclusion") != entry.conclusion:
        raise SemanticFailure(f"{entry.repository} receptor conclusion disagrees with manifest")
    native_expected = {
        "databaseId": entry.run_id,
        "attempt": entry.attempt,
        "conclusion": entry.conclusion,
    }
    for key, value in native_expected.items():
        if native.get(key) != value:
            raise SemanticFailure(f"{entry.repository} native {key} disagrees with manifest")
    if github.get("conclusion") != native.get("conclusion"):
        raise SemanticFailure(f"{entry.repository} receptor conclusion disagrees with GitHub")
    if sum(value for value in counts.values() if isinstance(value, int)) < entry.minimum_jobs:
        raise SemanticFailure(f"{entry.repository} job inventory is unexpectedly small")


def validate(entries: list[PublicRun], *, runner: Runner | None = None) -> None:
    """Validating live inspection, native parity, bounded text, and offline replay."""

    if runner is None:
        runner = subprocess.run
    with tempfile.TemporaryDirectory(prefix="ghrr-portability-") as temporary:
        for index, entry in enumerate(entries):
            bundle = Path(temporary) / f"run-{index}.json"
            inspect_arguments = [
                "--format",
                "json",
                "inspect",
                str(entry.run_id),
                "--attempt",
                str(entry.attempt),
                "--capture",
                "metadata",
            ]
            if entry.offline_replay:
                inspect_arguments.extend(("--output", str(bundle)))
            report_result = _run(runner, _receptor_command(entry, *inspect_arguments))
            if report_result.returncode == 5:
                detail = " ".join(report_result.stderr.split())[:240]
                raise AcquisitionFailure(f"{entry.repository} receptor acquisition: {detail}")
            if report_result.returncode != 0:
                raise SemanticFailure(
                    f"{entry.repository} receptor returned {report_result.returncode}"
                )
            report = _json_output(report_result, f"{entry.repository} receptor")

            native = _json_output(
                _run(
                    runner,
                    [
                        "gh",
                        "run",
                        "view",
                        str(entry.run_id),
                        "--repo",
                        entry.repository,
                        "--attempt",
                        str(entry.attempt),
                        "--json",
                        "attempt,conclusion,databaseId,status,url",
                    ],
                ),
                f"{entry.repository} native GitHub query",
            )
            _check_report(entry, report, native)

            text_result = _run(
                runner,
                _receptor_command(
                    entry,
                    "inspect",
                    str(entry.run_id),
                    "--attempt",
                    str(entry.attempt),
                    "--capture",
                    "metadata",
                ),
            )
            if text_result.returncode == 5:
                detail = " ".join(text_result.stderr.split())[:240]
                raise AcquisitionFailure(f"{entry.repository} text acquisition: {detail}")
            if text_result.returncode != 0:
                raise SemanticFailure(f"{entry.repository} compact report did not pass")
            rendered = text_result.stdout.encode("utf-8")
            if len(rendered) > MAX_REPORT_BYTES or len(text_result.stdout.splitlines()) != 1:
                raise SemanticFailure(f"{entry.repository} compact report is not bounded")
            if (
                entry.repository not in text_result.stdout
                or str(entry.run_id) not in text_result.stdout
            ):
                raise SemanticFailure(f"{entry.repository} compact report loses identity")

            if entry.offline_replay:
                replay = _receptor_command(entry, "--format", "json", "replay", str(bundle))
                first = _run(runner, replay)
                second = _run(runner, replay)
                if first.returncode == 5 or second.returncode == 5:
                    raise AcquisitionFailure(f"{entry.repository} replay bundle unavailable")
                if first.returncode != 0 or second.returncode != 0:
                    raise SemanticFailure(f"{entry.repository} offline replay did not pass")
                if first.stdout.encode("utf-8") != second.stdout.encode("utf-8"):
                    raise SemanticFailure(f"{entry.repository} offline replay is not deterministic")
                replayed = _json_output(first, f"{entry.repository} offline replay")
                _check_report(entry, replayed, native)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    try:
        entries = load_manifest(args.manifest)
        validate(entries)
    except AcquisitionFailure as exc:
        print(f"Portability corpus: UNAVAILABLE — {exc}", file=sys.stderr)
        return 2
    except (OSError, SemanticFailure, tomllib.TOMLDecodeError) as exc:
        print(f"Portability corpus: FAIL — {exc}", file=sys.stderr)
        return 1
    replays = sum(item.offline_replay for item in entries)
    print(
        f"Portability corpus: PASS — {len(entries)} runs, "
        f"{len({item.repository for item in entries})} repositories, replay={replays}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
