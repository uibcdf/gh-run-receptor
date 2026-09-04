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
        "capture_policy": "metadata",
        "complete": complete,
        "members": [],
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
    assert (
        "conda platforms: successful=1 failed=1 missing=0 artifacts=1 observed=2"
        in render_llm(report)
    )


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


def test_repository_rule_selects_profile_and_enforces_expected_platforms():
    evidence = _evidence(conclusion="success")
    for job in evidence["jobs.json"]["jobs"]:
        job["conclusion"] = "success"
        job["steps"] = []
    evidence["config.json"] = {
        "schema": "gh-run-receptor.config-capture@1",
        "source": {
            "path": ".github/gh-run-receptor.yaml",
            "ref": "main",
            "blob_sha": "abc",
            "sha256": "0" * 64,
        },
        "config": {
            "schema": "gh-run-receptor.config@1",
            "schema_version": 1,
            "workflows": [
                {
                    "match": {"path": ".github/workflows/conda.yaml"},
                    "profile": "conda",
                    "settings": {
                        "expected_platforms": ["linux-64", "win-64", "osx-arm64"]
                    },
                }
            ],
        },
    }

    report = build_report(_manifest(), evidence, profile="auto")

    assert report["github"]["conclusion"] == "success"
    assert report["receptor"]["profile"] == "conda"
    assert report["receptor"]["assessment"] == "FAIL"
    assert report["receptor"]["evidence_sufficient"] is True
    assert report["configuration"]["matched"] is True
    assert report["expectations"] == {
        "satisfied": False,
        "missing_platforms": ["osx-arm64"],
    }
    assert exit_code(report) == 1
    assert "missing expected: osx-arm64" in render_llm(report)
    assert "Source: .github/gh-run-receptor.yaml at main" in render_human(report)


def test_explicit_profile_overrides_repository_profile_but_preserves_settings():
    evidence = _evidence(conclusion="success")
    evidence["config.json"] = {
        "schema": "gh-run-receptor.config-capture@1",
        "source": None,
        "config": {
            "schema": "gh-run-receptor.config@1",
            "schema_version": 1,
            "workflows": [
                {
                    "match": {"path": ".github/workflows/conda.yaml"},
                    "profile": "conda",
                    "settings": {"expected_platforms": ["osx-arm64"]},
                }
            ],
        },
    }

    report = build_report(_manifest(), evidence, profile="generic")

    assert report["receptor"]["profile"] == "generic"
    assert report["matrix"] == {}
    assert report["expectations"]["satisfied"] is True


def test_ci_profile_groups_every_job_and_preserves_official_failure():
    evidence = _evidence()
    evidence["workflow.json"]["path"] = ".github/workflows/CI.yaml"
    evidence["jobs.json"]["jobs"][0]["name"] = "Test on Windows, Python 3.13"
    evidence["jobs.json"]["jobs"][1]["name"] = "Test on Linux, Python 3.13"
    evidence["jobs.json"]["jobs"].extend(
        [
            {
                "id": 30,
                "name": "Ruff lint checks",
                "status": "completed",
                "conclusion": "success",
                "steps": [],
            },
            {
                "id": 40,
                "name": "Build controlled wheel",
                "status": "completed",
                "conclusion": "success",
                "steps": [],
            },
            {
                "id": 50,
                "name": "Unrecognized gate",
                "status": "completed",
                "conclusion": "skipped",
                "steps": [],
            },
        ]
    )

    report = build_report(_manifest(), evidence, profile="ci")

    assert report["github"]["conclusion"] == "failure"
    assert report["receptor"]["assessment"] == "FAIL"
    roles = {role["name"]: role for role in report["matrix"]["roles"]}
    assert roles["test"]["counts"] == {"failure": 1, "success": 1}
    assert roles["lint"]["job_ids"] == [30]
    assert roles["build"]["job_ids"] == [40]
    assert roles["other"]["counts"] == {"skipped": 1}
    assert sum(len(role["job_ids"]) for role in roles.values()) == len(report["jobs"])
    rendered = render_llm(report)
    assert "failed groups (1, 1 jobs):" in rendered
    assert "ci roles:" in rendered
    assert "CI roles" in render_human(report)
    assert exit_code(report) == 1


def test_successful_ci_report_remains_one_line_and_summarizes_roles():
    evidence = _evidence(conclusion="success")
    evidence["jobs.json"]["jobs"][0]["name"] = "Test on Windows, Python 3.13"
    evidence["jobs.json"]["jobs"][1]["name"] = "Test on Linux, Python 3.13"
    for job in evidence["jobs.json"]["jobs"]:
        job["conclusion"] = "success"
        job["steps"] = []

    report = build_report(_manifest(), evidence, profile="ci")
    rendered = render_llm(report)

    assert report["receptor"]["assessment"] == "PASS"
    assert rendered.count("\n") == 1
    assert "profile=ci" in rendered
    assert "roles=test:2" in rendered


def test_ci_role_matching_does_not_read_test_inside_latest():
    evidence = _evidence(conclusion="success")
    evidence["jobs.json"]["jobs"] = [
        {
            "id": 1,
            "name": "Build wheel on ubuntu-latest",
            "status": "completed",
            "conclusion": "success",
            "steps": [],
        }
    ]

    report = build_report(_manifest(), evidence, profile="ci")

    assert report["matrix"]["roles"] == [
        {"name": "build", "job_ids": [1], "counts": {"success": 1}}
    ]


def test_ci_llm_output_groups_jobs_with_the_same_failed_steps():
    evidence = _evidence()
    evidence["jobs.json"]["jobs"][0]["name"] = "Test on Windows"
    evidence["jobs.json"]["jobs"][1]["name"] = "Test on Linux"
    for job in evidence["jobs.json"]["jobs"]:
        job["conclusion"] = "failure"
        job["steps"] = [{"number": 1, "name": "Run tests", "conclusion": "failure"}]

    rendered = render_llm(build_report(_manifest(), evidence, profile="ci"))

    assert "failed groups (1, 2 jobs):" in rendered
    assert "- 2 jobs | failure | steps: Run tests | sample: Test on Linux (+1)" in rendered
    assert "Test on Windows" not in rendered
