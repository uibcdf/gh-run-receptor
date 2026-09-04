import zipfile

from gh_run_receptor.report import build_report, exit_code, render_human, render_llm


def _evidence(conclusion="failure", status="completed"):
    return {
        "run.json": {
            "status": status,
            "conclusion": conclusion,
            "name": "Conda packages",
            "html_url": "https://github.com/uibcdf/molsysmt/actions/runs/42",
        },
        "workflow.json": {"path": ".github/workflows/conda.yaml"},
        "jobs.json": {
            "jobs": [
                {
                    "id": 20,
                    "name": "build (win-64)",
                    "status": "completed",
                    "conclusion": "failure",
                    "started_at": "2026-09-04T10:00:00Z",
                    "completed_at": "2026-09-04T10:02:03Z",
                    "steps": [
                        {"number": 1, "name": "Build", "conclusion": "success"},
                        {"number": 2, "name": "Upload", "conclusion": "failure"},
                    ],
                },
                {
                    "id": 10,
                    "name": "build (linux-64)",
                    "status": "completed",
                    "conclusion": "success",
                    "started_at": "2026-09-04T10:00:00Z",
                    "completed_at": "2026-09-04T10:01:00Z",
                    "steps": [],
                },
            ]
        },
        "checks.json": {"total_count": 0, "check_runs": []},
        "artifacts.json": {
            "artifacts": [
                {
                    "id": 7,
                    "name": "molsysmt-linux-64",
                    "size_in_bytes": 123,
                    "expired": False,
                    "digest": "sha256:abc",
                }
            ]
        },
    }


def _manifest(complete=True):
    return {
        "repository": "uibcdf/molsysmt",
        "run_id": 42,
        "run_attempt": 2,
        "head_sha": "abc",
        "complete": complete,
        "warnings": [],
    }


def test_failed_run_preserves_official_state_and_failed_step():
    report = build_report(_manifest(), _evidence())

    assert report["github"] == {"status": "completed", "conclusion": "failure"}
    assert report["receptor"]["assessment"] == "FAIL"
    assert report["jobs"][0]["name"] == "build (linux-64)"
    assert report["jobs"][1]["failed_steps"][0]["name"] == "Upload"
    assert exit_code(report) == 1

    rendered = render_llm(report)
    assert rendered.startswith("FAIL conclusion=failure status=completed")
    assert "build (win-64) | failure | duration=2m03s | steps: Upload" in rendered
    assert "| steps: Build" not in rendered


def test_incomplete_evidence_has_precedence_in_exit_code():
    report = build_report(_manifest(complete=False), _evidence())

    assert report["github"]["conclusion"] == "failure"
    assert report["receptor"]["assessment"] == "INCOMPLETE"
    assert report["receptor"]["evidence_sufficient"] is False
    assert exit_code(report) == 4


def test_pending_run_is_not_success():
    report = build_report(_manifest(), _evidence(conclusion=None, status="in_progress"))

    assert report["receptor"]["assessment"] == "PENDING"
    assert exit_code(report) == 3


def test_human_report_includes_successful_and_failed_jobs():
    report = build_report(_manifest(), _evidence())

    rendered = render_human(report)

    assert "gh-run-receptor: FAIL" in rendered
    assert "build (linux-64)" in rendered
    assert "build (win-64)" in rendered
    assert "failed step 2: Upload" in rendered


def test_text_renderers_escape_terminal_and_bidirectional_controls():
    evidence = _evidence()
    evidence["jobs.json"]["jobs"][0]["name"] = "fake\x1b[31m PASS\u202e"
    report = build_report(_manifest(), evidence)

    for rendered in (render_human(report), render_llm(report)):
        assert "\x1b" not in rendered
        assert "\u202e" not in rendered
        assert "\\u001b" in rendered
        assert "\\u202e" in rendered


def test_conda_profile_preserves_failure_and_marks_reusable_platforms():
    report = build_report(_manifest(), _evidence(), profile="conda")

    assert report["github"]["conclusion"] == "failure"
    assert report["receptor"]["assessment"] == "PARTIAL"
    assert exit_code(report) == 1
    platforms = {item["name"]: item for item in report["matrix"]["platforms"]}
    assert platforms["linux-64"]["reusable"] is True
    assert platforms["win-64"]["status"] == "failed"
    assert "conda platforms: successful=1 failed=1 artifacts=1 observed=2" in render_llm(report)


def test_auto_profile_requires_conda_workflow_and_multiple_platforms():
    conda = build_report(_manifest(), _evidence(), profile="auto")
    evidence = _evidence()
    evidence["workflow.json"]["path"] = ".github/workflows/ci.yaml"
    generic = build_report(_manifest(), evidence, profile="auto")

    assert conda["receptor"]["profile"] == "conda"
    assert generic["receptor"]["profile"] == "generic"


def test_report_integrates_cause_from_captured_log_archive(tmp_path):
    with zipfile.ZipFile(tmp_path / "logs.zip", "w") as zipped:
        zipped.writestr("1_build (win-64).txt", "tool: command not found\n")
    manifest = _manifest()
    manifest["members"] = [{"path": "logs.zip"}]

    report = build_report(
        manifest,
        _evidence(),
        profile="conda",
        bundle_directory=tmp_path,
    )

    assert report["receptor"]["cause_evidence"] == "complete"
    assert report["causes"][0]["message"] == "tool: command not found"
    assert "root causes (1):" in render_llm(report)


def test_successful_conda_jobs_are_not_called_reusable_without_artifacts():
    evidence = _evidence(conclusion="success")
    for job in evidence["jobs.json"]["jobs"]:
        job["conclusion"] = "success"
        job["steps"] = []
    evidence["artifacts.json"]["artifacts"] = []

    report = build_report(_manifest(), evidence, profile="conda")
    rendered = render_llm(report)

    assert report["receptor"]["assessment"] == "PASS"
    assert rendered.count("\n") == 1
    assert "platforms=2/2" in rendered
    assert "jobs=2/2" in rendered
    assert "artifacts=0" in rendered
    assert "reusable:" not in rendered
