"""Terminal source conclusions cannot certify contradictory child observations (#78)."""

from copy import deepcopy
from pathlib import Path

import pytest

from gh_run_receptor import cli
from gh_run_receptor.model import normalize_evidence
from gh_run_receptor.report import build_report, exit_code, render_human, render_json, render_llm
from gh_run_receptor_tools.schema_validation import validator


def _sources(status="in_progress", conclusion=None, *, job_status="completed"):
    # Narrow transcription of the public original example in issue #78, not a
    # recovered original capture. The live 2026-11-11 response is coherent.
    manifest = {
        "repository": "uibcdf/sabueso",
        "run_id": 41101439965,
        "run_attempt": 1,
        "head_sha": "6f94043a342e4bc53b42dd48531a19c5ba331824",
        "complete": True,
        "capture_policy": "metadata",
        "members": [],
        "warnings": [],
    }
    evidence = {
        "run.json": {"status": "completed", "conclusion": "success"},
        "workflow.json": {"path": ".github/workflows/ci.yml"},
        "jobs.json": {
            "jobs": [
                {
                    "id": 124219196265,
                    "name": "Offline tests (windows-latest, Python 3.13)",
                    "status": job_status,
                    "conclusion": "success",
                    "steps": [
                        {
                            "number": 9,
                            "name": "Run repository-input offline tests",
                            "status": status,
                            "conclusion": conclusion,
                        }
                    ],
                }
            ]
        },
        "checks.json": {"check_runs": []},
        "artifacts.json": {"artifacts": []},
    }
    return manifest, evidence


@pytest.mark.parametrize(
    "status,conclusion,contradiction",
    [
        ("in_progress", None, True),
        ("queued", None, True),
        ("pending", None, True),
        ("completed", None, True),
        (None, None, True),
        ("future-state", "success", True),
        ("completed", "success", False),
        ("completed", "skipped", False),
        (None, "success", False),
    ],
)
def test_step_observation_consistency_preserves_source_truth(status, conclusion, contradiction):
    manifest, evidence = _sources(status, conclusion)
    original = deepcopy(evidence)
    model = normalize_evidence(manifest, evidence)
    report = build_report(manifest, evidence)
    assert evidence == original
    assert model["jobs"][0]["steps"][0]["status"] == status
    assert model["jobs"][0]["steps"][0]["conclusion"] == conclusion
    assert report["github"] == {"status": "completed", "conclusion": "success"}
    assert report["receptor"]["assessment"] == "PASS"
    assert exit_code(report) == 0
    assert model["bundle_complete"] is True
    assert (report["completeness"].get("terminal_steps") == "partial") == contradiction
    for render in (render_llm, render_human, render_json):
        text = render(report)
        assert ("terminal step metadata inconsistent" in text) == contradiction
        assert len(text.encode()) < 8_000
    validator("model-v1.schema.json").validate(model)
    validator("report-v1.schema.json").validate(report)


@pytest.mark.parametrize("job_status", ["queued", "in_progress"])
def test_nonterminal_jobs_do_not_claim_terminal_child_inconsistency(job_status):
    manifest, evidence = _sources(job_status=job_status)
    report = build_report(manifest, evidence)
    assert "terminal_steps" not in report["completeness"]
    assert report["warnings"] == []
    assert report["jobs"][0]["status"] == job_status


def test_child_warning_counts_and_original_pointers_remain_bounded_with_hostile_names():
    manifest, evidence = _sources()
    job = evidence["jobs.json"]["jobs"][0]
    job["name"] = "\x1b[2J\u202e" + "x" * 20_000
    job["steps"] *= 1_000
    report = build_report(manifest, evidence, profile="ci")
    assert len(report["unknowns"]) == 1_000
    assert report["unknowns"][-1]["source"]["json_pointer"] == "/jobs/0/steps/999"
    assert "jobs=1 steps=1000" in report["warnings"][0]
    assert "jobs.json:/jobs/0/steps/0" in render_llm(report)
    assert "qualification unknown" in render_llm(report)
    assert len(render_llm(report).encode()) < 2_000
    for render in (render_human, render_llm):
        text = render(report)
        assert "\x1b" not in text and "\u202e" not in text


@pytest.mark.parametrize("command", ["inspect", "watch"])
def test_inspect_and_watch_terminal_handoff_replay_the_same_consistency_warning(
    tmp_path, monkeypatch, capsys, command
):
    manifest, evidence = _sources()
    run = {
        **evidence["run.json"],
        "id": manifest["run_id"],
        "workflow_id": 7,
        "run_attempt": 1,
        "head_sha": manifest["head_sha"],
    }

    class Client:
        hostname = "github.com"

        def repository(self, value):
            return value

        def optional_json(self, endpoint):
            return None

        def json(self, endpoint, *, paginate=False):
            if "/jobs?" in endpoint:
                return [evidence["jobs.json"]]
            if "/actions/runs/" in endpoint and "/artifacts?" not in endpoint:
                return run
            if "/workflows/7" in endpoint:
                return evidence["workflow.json"]
            if "/artifacts?" in endpoint:
                return [{"artifacts": []}]
            if endpoint == "/repos/uibcdf/sabueso":
                return {"default_branch": "main"}
            raise AssertionError(endpoint)

    monkeypatch.setattr(cli, "GitHubClient", lambda *args, **kwargs: Client())
    destination = tmp_path / "capture"
    code = cli.main(
        [
            command,
            str(manifest["run_id"]),
            "--repo",
            "uibcdf/sabueso",
            "--capture",
            "metadata",
            "--output",
            str(destination),
            "--receptor",
            "llm",
        ]
    )
    first = capsys.readouterr()
    assert code == 0
    assert "terminal step metadata inconsistent" in first.out
    assert "jobs.json:/jobs/0/steps/0" in first.out
    assert cli.main(["replay", str(destination), "--receptor", "llm"]) == 0
    assert capsys.readouterr().out == first.out


def test_child_consistency_warning_matches_reviewed_golden_reports():
    manifest, evidence = _sources()
    report = build_report(manifest, evidence, profile="ci")
    root = Path(__file__).parent / "fixtures/termination"
    assert render_llm(report) == (root / "inconsistent_steps.llm").read_text()
    assert render_human(report) == (root / "inconsistent_steps.human").read_text()
