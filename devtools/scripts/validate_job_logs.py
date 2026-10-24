"""Receive real completed-job logs while this observer keeps its workflow active."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gh_run_receptor.bundle import load_bundle
from gh_run_receptor.github import GitHubClient, merge_pages
from gh_run_receptor.report import build_report, exit_code, render_human, render_json, render_llm
from gh_run_receptor.service import acquire_evidence


def validate(repository: str, run_id: int, attempt: int, output: Path) -> None:
    """Keep a sanitized explicit receipt outside managed disposable raw evidence."""
    client = GitHubClient()
    jobs = merge_pages(
        client.json(
            f"/repos/{repository}/actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100",
            paginate=True,
        ),
        "jobs",
    )["jobs"]
    results = []
    with tempfile.TemporaryDirectory(prefix="ghrr-job-logs-") as temporary:
        for name, conclusion in [
            ("completed-failure", "failure"),
            ("completed-success", "success"),
        ]:
            selected = [job for job in jobs if job.get("name") == name]
            if len(selected) != 1 or selected[0].get("conclusion") != conclusion:
                raise ValueError(f"native producer job truth differs: {name}")
            job_id = selected[0]["id"]
            captured = acquire_evidence(
                client,
                repository,
                run_id,
                attempt=attempt,
                policy="adaptive",
                cache_root=Path(temporary),
                job_id=job_id,
            )
            report = build_report(
                captured.manifest,
                captured.evidence,
                profile="ci",
                bundle_directory=captured.path,
            )
            if (
                report["github"]["status"] != "in_progress"
                or report["github"]["conclusion"] is not None
            ):
                raise ValueError("active observation was not made during the workflow window")
            if exit_code(report) != 3 or report["completeness"]["logs"] != "partial":
                raise ValueError("job-only active capture changed process status or scope")
            if report["log_scope"] != {"kind": "job", "job_id": job_id}:
                raise ValueError("selected log identity differs")
            messages = [cause["message"] for cause in report["causes"]]
            if conclusion == "failure":
                if not any(
                    "NotADirectoryError" in message and "active job probe" in message
                    for message in messages
                ):
                    raise ValueError("real failed job lost its typed primary cause")
            elif messages:
                raise ValueError("successful job's failed-looking text became a diagnosis")
            manifest, evidence = load_bundle(captured.path)
            replay = build_report(manifest, evidence, profile="ci", bundle_directory=captured.path)
            for renderer in (render_human, render_llm, render_json):
                text = renderer(report)
                if text != renderer(replay) or len(text.encode()) > 32 * 1024:
                    raise ValueError("replay differs or report exceeds the probe bound")
            results.append(
                {
                    "job_id": job_id,
                    "job_name": name,
                    "job_conclusion": conclusion,
                    "github": report["github"],
                    "exit_status": exit_code(report),
                    "log_scope": report["log_scope"],
                    "causes": messages,
                    "log_sha256": next(
                        m["sha256"] for m in manifest["members"] if m["kind"] == "github.job_log"
                    ),
                    "deterministic_replay": True,
                }
            )
    output.write_text(
        json.dumps(
            {
                "repository": repository,
                "run_id": run_id,
                "run_attempt": attempt,
                "results": results,
                "raw_temporary_evidence_removed": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--attempt", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    validate(args.repository, args.run_id, args.attempt, args.output)


if __name__ == "__main__":
    main()
