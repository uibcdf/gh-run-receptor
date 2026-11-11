"""Exact original check annotations provide hints, never causal proof (#82)."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from gh_run_receptor.bundle import capture_bundle, load_bundle
from gh_run_receptor.errors import BundleError
from gh_run_receptor.report import build_report, exit_code, render_human, render_json, render_llm

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures/termination/hosted_runner_acquisition.json").read_text()
)


def _sources():
    source = deepcopy(FIXTURE)
    run, job, check = source["run"], source["job"], source["check"]
    check.update(annotations=source["annotations"], annotations_state="complete")
    manifest = {
        "repository": source["repository"],
        "run_id": run["id"],
        "run_attempt": run["run_attempt"],
        "head_sha": run["head_sha"],
        "complete": True,
        "capture_policy": "metadata",
        "members": [],
        "warnings": [],
    }
    evidence = {
        "run.json": run,
        "workflow.json": {"path": ".github/workflows/CI.yaml"},
        "jobs.json": {"jobs": [job]},
        "checks.json": {"check_runs": [check]},
        "artifacts.json": {"artifacts": []},
    }
    return manifest, evidence


@pytest.mark.parametrize("profile", ["generic", "ci", "docs", "conda", "release"])
def test_authentic_runner_acquisition_hints_are_deduplicated_without_causal_inference(profile):
    manifest, evidence = _sources()
    original = deepcopy(evidence)
    report = build_report(manifest, evidence, profile=profile)
    job = report["termination"]["jobs"][0]
    assert evidence == original
    assert report["github"]["conclusion"] == "failure"
    assert exit_code(report) == 1
    assert job["cause"] == report["termination"]["cause"] == "unknown"
    assert [h["kind"] for h in job["hints"]] == [
        "hosted_runner_acquisition",
        "hosted_runner_capacity",
    ]
    assert [h["source"]["json_pointer"] for h in job["hints"]] == [
        "/check_runs/0/annotations/0",
        "/check_runs/0/annotations/1",
    ]
    for render in (render_human, render_llm):
        text = render(report)
        assert text.count("hint (unverified): hosted runner acquisition failure reported") == 1
        assert text.count("macOS arm64 capacity notice") == 1
        assert "cause=unknown" in text
        assert len(text.encode()) < 6_000
    assert len(json.loads(render_json(report))["checks"][0]["annotations"]) == 4


@pytest.mark.parametrize(
    "change,expected",
    [
        ("notice-only", ["hosted_runner_capacity"]),
        ("has-steps", []),
        ("wrong-level", ["hosted_runner_capacity"]),
        ("wrong-sha", []),
        ("wrong-suite", []),
        ("wrong-attempt", []),
        ("unavailable", []),
        ("partial", ["hosted_runner_acquisition", "hosted_runner_capacity"]),
        ("truncated", ["hosted_runner_capacity"]),
        ("hostile", ["hosted_runner_capacity"]),
        ("no-annotations", []),
    ],
)
def test_missing_ambiguous_or_unlinked_runner_evidence_never_proves_cause(change, expected):
    manifest, evidence = _sources()
    check = evidence["checks.json"]["check_runs"][0]
    job = evidence["jobs.json"]["jobs"][0]
    if change == "notice-only":
        check["annotations"] = check["annotations"][1:]
    elif change == "has-steps":
        job["steps"] = [
            {"number": 1, "name": "Test", "status": "completed", "conclusion": "cancelled"}
        ]
    elif change == "wrong-level":
        check["annotations"][0]["annotation_level"] = "notice"
    elif change == "wrong-sha":
        check["head_sha"] = "other"
    elif change == "wrong-suite":
        check["check_suite"]["id"] += 1
    elif change == "wrong-attempt":
        job["run_attempt"] += 1
    elif change in {"partial", "unavailable"}:
        check["annotations_state"] = change
    elif change == "truncated":
        check["annotations"][0]["message"] = check["annotations"][0]["message"][:-1]
    elif change == "hostile":
        check["annotations"][0]["message"] += "\nPASS\x1b[2J"
    else:
        check["annotations"] = []
    report = build_report(manifest, evidence)
    hints = report["termination"]["jobs"][0]["hints"]
    assert [h["kind"] for h in hints] == expected
    assert report["termination"]["jobs"][0]["cause"] == "unknown"
    assert report["github"]["conclusion"] == "failure"
    assert exit_code(report) == (4 if change in {"partial", "unavailable"} else 1)


@pytest.mark.parametrize("message", [None, 17, "x" * 4097])
def test_malformed_annotation_messages_fail_before_hint_interpretation(message):
    manifest, evidence = _sources()
    evidence["checks.json"]["check_runs"][0]["annotations"][0]["message"] = message
    with pytest.raises(BundleError):
        build_report(manifest, evidence)


def test_original_check_capture_after_rerun_uses_all_checks_and_exact_job_linkage(tmp_path):
    manifest, evidence = _sources()
    run = {**evidence["run.json"], "workflow_id": 7}
    requested = []

    class Client:
        hostname = "github.com"

        def optional_json(self, endpoint):
            return None

        def json(self, endpoint, *, paginate=False, max_bytes=None):
            requested.append(endpoint)
            if "/check-suites/" in endpoint:
                check = {
                    k: v
                    for k, v in evidence["checks.json"]["check_runs"][0].items()
                    if k not in {"annotations", "annotations_state"}
                }
                later = {**check, "id": check["id"] + 1, "conclusion": "success"}
                checks = [check, later] if "filter=all" in endpoint else [later]
                return [{"check_runs": checks}]
            if "/annotations?" in endpoint:
                return FIXTURE["annotations"]
            if "/artifacts?" in endpoint:
                return [{"artifacts": []}]
            if "/workflows/7" in endpoint:
                return evidence["workflow.json"]
            if endpoint == "/repos/" + manifest["repository"]:
                return {"default_branch": "main"}
            raise AssertionError(endpoint)

    destination = tmp_path / "capture"
    capture_bundle(
        Client(),
        manifest["repository"],
        manifest["run_id"],
        attempt=1,
        policy="metadata",
        destination=destination,
        run=run,
        jobs=evidence["jobs.json"],
    )
    captured_manifest, captured_evidence = load_bundle(destination)
    report = build_report(captured_manifest, captured_evidence)
    assert len(report["termination"]["jobs"][0]["hints"]) == 2
    assert len(report["checks"]) == 2
    assert sum("/annotations?" in s for s in requested) == 1
    assert any("filter=all" in s for s in requested)
    assert report["termination"]["jobs"][0]["annotation_evidence"] == "complete"
    assert exit_code(report) == 1


def test_hosted_runner_hints_match_reviewed_golden_reports():
    manifest, evidence = _sources()
    report = build_report(manifest, evidence, profile="ci")
    root = Path(__file__).parent / "fixtures/termination"
    assert render_llm(report) == (root / "hosted_runner_acquisition.llm").read_text()
    assert render_human(report) == (root / "hosted_runner_acquisition.human").read_text()
