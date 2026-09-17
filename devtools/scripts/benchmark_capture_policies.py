#!/usr/bin/env python3
"""Measuring log requests, bytes, and diagnostic deltas across evidence bundles."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gh_run_receptor.bundle import load_bundle, should_fetch_logs  # noqa: E402
from gh_run_receptor.errors import BundleError  # noqa: E402
from gh_run_receptor.report import build_report  # noqa: E402


class BenchmarkError(RuntimeError):
    """Representing an invalid or insufficient benchmark corpus."""


def discover_bundles(roots: Sequence[Path]) -> list[Path]:
    """Discovering bundle directories beneath explicit local roots."""
    discovered: set[Path] = set()
    for root in roots:
        candidate = root.expanduser().resolve()
        if (candidate / "manifest.json").is_file():
            discovered.add(candidate)
            continue
        if not candidate.is_dir():
            raise BenchmarkError(f"bundle root does not exist or is not a directory: {root}")
        discovered.update(path.parent for path in candidate.rglob("manifest.json"))
    if not discovered:
        raise BenchmarkError("no evidence bundles were discovered")
    return sorted(discovered, key=str)


def _log_warning(manifest: dict[str, Any]) -> bool:
    return any(str(item).startswith("logs unavailable:") for item in manifest["warnings"])


def _measure_bundle(path: Path) -> dict[str, Any]:
    manifest, evidence = load_bundle(path)
    run = evidence["run.json"]
    policy = manifest["capture_policy"]
    expected_request = should_fetch_logs(
        policy,
        status=run.get("status"),
        conclusion=run.get("conclusion"),
    )
    log_member = next(
        (member for member in manifest["members"] if member.get("path") == "logs.zip"),
        None,
    )
    unavailable = _log_warning(manifest)
    request_observed = log_member is not None or unavailable
    mismatch = None
    if expected_request and not request_observed:
        mismatch = "policy required a log request but the bundle records neither logs nor failure"
    elif not expected_request and request_observed:
        mismatch = "policy did not require logs but the bundle records a log request"

    report = build_report(
        manifest,
        evidence,
        profile="auto",
        bundle_directory=path if log_member is not None else None,
    )
    failed_job_ids = {job["id"] for job in report["jobs"] if job.get("conclusion") == "failure"}
    diagnosed_job_ids = {
        occurrence["job_id"] for cause in report["causes"] for occurrence in cause["occurrences"]
    }
    structured_bytes = sum(
        member["bytes"] for member in manifest["members"] if member.get("path") != "logs.zip"
    )
    return {
        "identity": {
            "hostname": manifest["hostname"],
            "repository": manifest["repository"],
            "run_id": manifest["run_id"],
            "run_attempt": manifest["run_attempt"],
        },
        "policy": policy,
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "complete": manifest["complete"],
        "expected_log_request": expected_request,
        "observed_log_request": request_observed,
        "log_unavailable": unavailable,
        "log_bytes": log_member["bytes"] if log_member is not None else 0,
        "structured_bytes": structured_bytes,
        "failed_jobs": len(failed_job_ids),
        "diagnosed_failed_jobs": len(failed_job_ids & diagnosed_job_ids),
        "cause_groups": len(report["causes"]),
        "policy_mismatch": mismatch,
    }


def _identity_key(measurement: dict[str, Any]) -> tuple[Any, ...]:
    identity = measurement["identity"]
    return (
        identity["hostname"],
        identity["repository"],
        identity["run_id"],
        identity["run_attempt"],
    )


def _paired_measurements(measurements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = {}
    for measurement in measurements:
        policies = grouped.setdefault(_identity_key(measurement), {})
        policy = measurement["policy"]
        if policy in policies:
            identity = measurement["identity"]
            raise BenchmarkError(
                "duplicate bundle identity and policy: "
                f"{identity['repository']}#{identity['run_id']}/"
                f"{identity['run_attempt']} {policy}"
            )
        policies[policy] = measurement

    pairs = []
    for policies in grouped.values():
        if "full" not in policies or "adaptive" not in policies:
            continue
        full = policies["full"]
        adaptive = policies["adaptive"]
        missing_diagnoses = max(
            0,
            full["diagnosed_failed_jobs"] - adaptive["diagnosed_failed_jobs"],
        )
        bytes_comparable = (
            full["observed_log_request"]
            and not full["log_unavailable"]
            and not adaptive["log_unavailable"]
        )
        saved_bytes = full["log_bytes"] - adaptive["log_bytes"] if bytes_comparable else None
        pairs.append(
            {
                "identity": full["identity"],
                "status": full["status"],
                "conclusion": full["conclusion"],
                "full_log_bytes": full["log_bytes"],
                "adaptive_log_bytes": adaptive["log_bytes"],
                "observed_bytes_saved": saved_bytes,
                "full_diagnosed_failed_jobs": full["diagnosed_failed_jobs"],
                "adaptive_diagnosed_failed_jobs": adaptive["diagnosed_failed_jobs"],
                "missing_diagnoses": missing_diagnoses,
            }
        )
    return sorted(
        pairs,
        key=lambda item: (
            item["identity"]["repository"],
            item["identity"]["run_id"],
            item["identity"]["run_attempt"],
        ),
    )


def benchmark(roots: Sequence[Path]) -> dict[str, Any]:
    """Building one deterministic aggregate from validated local bundles."""
    measurements = [_measure_bundle(path) for path in discover_bundles(roots)]
    measurements.sort(
        key=lambda item: (
            item["identity"]["repository"],
            item["identity"]["run_id"],
            item["identity"]["run_attempt"],
            item["policy"],
        )
    )
    policy_counts: dict[str, Counter[str]] = {}
    state_counts: Counter[str] = Counter()
    for item in measurements:
        counts = policy_counts.setdefault(item["policy"], Counter())
        counts["captures"] += 1
        counts["expected_log_requests"] += int(item["expected_log_request"])
        counts["observed_log_requests"] += int(item["observed_log_request"])
        counts["log_unavailable"] += int(item["log_unavailable"])
        counts["log_bytes"] += item["log_bytes"]
        counts["structured_bytes"] += item["structured_bytes"]
        counts["failed_jobs"] += item["failed_jobs"]
        counts["diagnosed_failed_jobs"] += item["diagnosed_failed_jobs"]
        counts["cause_groups"] += item["cause_groups"]
        state = f"{item['status'] or '<absent>'}/{item['conclusion'] or '<absent>'}"
        state_counts[state] += 1

    pairs = _paired_measurements(measurements)
    mismatches = [
        {
            "identity": item["identity"],
            "policy": item["policy"],
            "reason": item["policy_mismatch"],
        }
        for item in measurements
        if item["policy_mismatch"] is not None
    ]
    paired_success = sum(
        item["status"] == "completed" and item["conclusion"] == "success" for item in pairs
    )
    paired_non_success = sum(
        item["status"] == "completed" and item["conclusion"] != "success" for item in pairs
    )
    known_saved_bytes = sum(
        item["observed_bytes_saved"] for item in pairs if item["observed_bytes_saved"] is not None
    )
    missing_diagnoses = sum(item["missing_diagnoses"] for item in pairs)
    return {
        "benchmark_version": 1,
        "captures": len(measurements),
        "states": dict(sorted(state_counts.items())),
        "policies": {
            policy: dict(sorted(counts.items())) for policy, counts in sorted(policy_counts.items())
        },
        "paired": {
            "captures": len(pairs),
            "successful": paired_success,
            "terminal_non_success": paired_non_success,
            "observed_bytes_saved": known_saved_bytes,
            "missing_diagnoses": missing_diagnoses,
            "runs": pairs,
        },
        "policy_mismatches": mismatches,
        "measurements": measurements,
    }


def render_text(result: dict[str, Any]) -> str:
    """Rendering a compact benchmark summary without raw log content."""
    lines = [
        f"Capture policy benchmark: {'PASS' if not result['policy_mismatches'] else 'FAIL'} "
        f"— {result['captures']} bundles"
    ]
    for policy, counts in result["policies"].items():
        captures = counts["captures"]
        requests = counts["expected_log_requests"]
        avoided = captures - requests
        lines.append(
            f"{policy}: requests={requests}/{captures}, avoided={avoided}/{captures}, "
            f"logs={counts['log_bytes']} B, structured={counts['structured_bytes']} B, "
            f"diagnosed={counts['diagnosed_failed_jobs']}/{counts['failed_jobs']} failed jobs"
        )
    paired = result["paired"]
    lines.append(
        f"paired: runs={paired['captures']}, success={paired['successful']}, "
        f"terminal_non_success={paired['terminal_non_success']}, "
        f"observed_saved={paired['observed_bytes_saved']} B, "
        f"missing_diagnoses={paired['missing_diagnoses']}"
    )
    if result["policy_mismatches"]:
        lines.append(f"policy mismatches: {len(result['policy_mismatches'])}")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", type=Path, help="bundle directories or roots")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--require-paired-success", action="store_true")
    parser.add_argument("--require-paired-non-success", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = benchmark(args.roots)
    except (BenchmarkError, BundleError, OSError) as error:
        print(f"Capture policy benchmark: ERROR — {error}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_text(result), end="")
    paired = result["paired"]
    requirements_met = (
        not result["policy_mismatches"]
        and (not args.require_paired_success or paired["successful"] > 0)
        and (not args.require_paired_non_success or paired["terminal_non_success"] > 0)
    )
    return 0 if requirements_met else 1


if __name__ == "__main__":
    raise SystemExit(main())
