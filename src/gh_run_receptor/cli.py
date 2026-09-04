"""Providing the gh-run-receptor command-line interface."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from gh_run_receptor import __version__
from gh_run_receptor.bundle import capture_bundle, default_bundle_path, load_bundle
from gh_run_receptor.errors import BundleError, ReceptorError
from gh_run_receptor.github import GitHubClient
from gh_run_receptor.report import build_report, exit_code, render_human, render_json, render_llm


@dataclass(frozen=True)
class RunReference:
    """Identifying a run and optional repository parsed from a URL."""

    run_id: int
    hostname: str | None = None
    repository: str | None = None


def _run_reference(value: str) -> RunReference:
    if value.isdigit():
        return RunReference(run_id=int(value))
    parsed = urlparse(value)
    match = re.fullmatch(r"/([^/]+)/([^/]+)/actions/runs/([0-9]+)(?:/.*)?", parsed.path)
    if parsed.scheme != "https" or not parsed.hostname or not match:
        raise argparse.ArgumentTypeError("run must be a numeric ID or GitHub Actions run URL")
    return RunReference(
        run_id=int(match.group(3)),
        hostname=parsed.hostname,
        repository=f"{match.group(1)}/{match.group(2)}",
    )


def _cache_root(value: str | None) -> Path:
    if value:
        return Path(value).expanduser()
    base = os.environ.get("XDG_CACHE_HOME")
    return (Path(base) if base else Path.home() / ".cache") / "gh-run-receptor"


def _add_common_options(
    parser: argparse.ArgumentParser, *, suppress_defaults: bool = False
) -> None:
    default = argparse.SUPPRESS if suppress_defaults else None
    parser.add_argument("--repo", default=default, help="GitHub repository in OWNER/REPO form")
    parser.add_argument("--hostname", default=default)
    parser.add_argument("--cache-dir", default=default)
    parser.add_argument(
        "--receptor",
        choices=("human", "llm"),
        default=default,
        help="target reader; inferred from whether stdout is a terminal by default",
    )
    parser.add_argument(
        "--format", choices=("text", "json"), default=default or "text"
    )
    parser.add_argument("--profile", choices=("generic", "conda"), default=default)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gh-run-receptor")
    parser.add_argument("--version", action="version", version=__version__)
    _add_common_options(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect = subparsers.add_parser("inspect", help="capture and report one workflow run")
    _add_common_options(inspect, suppress_defaults=True)
    inspect.add_argument("run", type=_run_reference)
    inspect.add_argument("--attempt", type=int)
    inspect.add_argument("--capture", choices=("full", "adaptive", "metadata"), default="adaptive")
    inspect.add_argument("--output", type=Path)

    capture = subparsers.add_parser("capture", help="capture one workflow run")
    _add_common_options(capture, suppress_defaults=True)
    capture.add_argument("run", type=_run_reference)
    capture.add_argument("--attempt", type=int)
    capture.add_argument("--capture", choices=("full", "adaptive", "metadata"), default="full")
    capture.add_argument("--output", type=Path)

    replay = subparsers.add_parser("replay", help="render a saved evidence bundle")
    _add_common_options(replay, suppress_defaults=True)
    replay.add_argument("bundle", type=Path)
    return parser


def _render(report: dict, output_format: str, receptor: str | None) -> str:
    if output_format == "json":
        return render_json(report)
    selected = receptor or ("human" if sys.stdout.isatty() else "llm")
    return render_human(report) if selected == "human" else render_llm(report)


def _capture(args: argparse.Namespace, *, render: bool) -> int:
    hostname = args.hostname or args.run.hostname or "github.com"
    if args.hostname and args.run.hostname and args.hostname != args.run.hostname:
        raise BundleError("run URL hostname conflicts with --hostname")
    if args.repo and args.run.repository and args.repo != args.run.repository:
        raise BundleError("run URL repository conflicts with --repo")
    client = GitHubClient(hostname)
    repository = client.repository(args.repo or args.run.repository)
    run_id = args.run.run_id

    run = client.json(f"/repos/{repository}/actions/runs/{run_id}")
    current_attempt = int(run.get("run_attempt") or 1)
    selected_attempt = args.attempt or current_attempt
    destination = args.output or default_bundle_path(
        _cache_root(args.cache_dir), hostname, repository, run_id, selected_attempt, args.capture
    )
    if destination.exists():
        manifest, evidence = load_bundle(destination)
        expected = (repository, run_id, selected_attempt, args.capture)
        actual = (
            manifest.get("repository"),
            manifest.get("run_id"),
            manifest.get("run_attempt"),
            manifest.get("capture_policy"),
        )
        if actual != expected:
            raise BundleError(
                "existing bundle identity or capture policy does not match the request"
            )
    else:
        manifest = capture_bundle(
            client,
            repository,
            run_id,
            attempt=args.attempt,
            policy=args.capture,
            destination=destination,
            run=run,
        )
        _, evidence = load_bundle(destination)

    if not render:
        total = sum(int(member["bytes"]) for member in manifest["members"])
        print(
            f"bundle run={manifest['run_id']} attempt={manifest['run_attempt']} "
            f"complete={str(manifest['complete']).lower()} bytes={total} path={destination}"
        )
        return 0 if manifest["complete"] else 4

    report = build_report(
        manifest,
        evidence,
        profile=args.profile or "auto",
        bundle_directory=destination,
    )
    print(_render(report, args.format, args.receptor), end="")
    return exit_code(report)


def main(arguments: list[str] | None = None) -> int:
    """Running the command-line interface and returning its process status."""
    parser = _parser()
    args = parser.parse_args(arguments)
    try:
        if args.command == "inspect":
            return _capture(args, render=True)
        if args.command == "capture":
            return _capture(args, render=False)
        manifest, evidence = load_bundle(args.bundle)
        report = build_report(
            manifest,
            evidence,
            profile=args.profile or "auto",
            bundle_directory=args.bundle,
        )
        print(_render(report, args.format, args.receptor), end="")
        return exit_code(report)
    except ReceptorError as error:
        print(f"RECEPTOR_ERROR: {error}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
