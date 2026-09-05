import zipfile

import pytest

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


def test_cancelled_conda_run_preserves_platform_and_job_states():
    evidence = _evidence(conclusion="cancelled")
    evidence["jobs.json"]["jobs"].append(
        {
            "id": 30,
            "name": "build (osx-arm64)",
            "status": "completed",
            "conclusion": "cancelled",
            "started_at": "2026-09-04T10:00:00Z",
            "completed_at": "2026-09-04T10:01:00Z",
            "steps": [],
        }
    )

    report = build_report(_manifest(), evidence, profile="conda")
    platforms = {item["name"]: item for item in report["matrix"]["platforms"]}
    rendered = render_llm(report)

    assert report["receptor"]["assessment"] == "CANCELLED"
    assert exit_code(report) == 2
    assert platforms["osx-arm64"]["status"] == "cancelled"
    assert "non-success jobs (2):" in rendered
    assert "failed jobs" not in rendered
    assert "successful=1 failed=1 cancelled=1 missing=0" in rendered


@pytest.mark.parametrize(
    ("status", "conclusion", "expected"),
    [
        ("completed", "timed_out", "timed_out"),
        ("completed", "cancelled", "cancelled"),
        ("in_progress", None, "in_progress"),
        ("completed", "future_state", "future_state"),
    ],
)
def test_conda_platform_aggregation_preserves_non_failure_states(
    status, conclusion, expected
):
    evidence = _evidence(conclusion=conclusion, status=status)
    evidence["jobs.json"]["jobs"] = [
        {
            "id": 10,
            "name": "build (linux-64)",
            "status": status,
            "conclusion": conclusion,
            "steps": [],
        }
    ]
    evidence["artifacts.json"]["artifacts"] = []

    report = build_report(_manifest(), evidence, profile="conda")

    assert report["matrix"]["platforms"][0]["status"] == expected
    assert f"{expected}=1" in render_llm(report)


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


def test_noarch_conda_rule_does_not_render_an_empty_native_matrix():
    evidence = _evidence(conclusion="success")
    evidence["jobs.json"]["jobs"] = [
        {
            "id": 10,
            "name": "Conda deployment of the noarch package",
            "status": "completed",
            "conclusion": "success",
            "steps": [],
        }
    ]
    evidence["artifacts.json"]["artifacts"] = []
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
                    "settings": {"package_kind": "noarch"},
                }
            ],
        },
    }

    report = build_report(_manifest(), evidence, profile="auto")
    package = report["matrix"]["package"]
    rendered = render_llm(report)

    assert report["github"]["conclusion"] == "success"
    assert report["receptor"]["assessment"] == "PASS"
    assert report["matrix"]["package_kind"] == "noarch"
    assert report["matrix"]["platforms"] == []
    assert package["job_counts"] == {"success": 1}
    assert package["artifact_evidence"] == "not_observed"
    assert "package=noarch" in rendered
    assert "artifact_evidence=not_observed" in rendered
    assert "platforms=0/0" not in rendered


@pytest.mark.parametrize(
    ("artifacts", "expected"),
    [
        ([{"id": 7, "name": "package", "expired": False}], "available"),
        ([{"id": 7, "name": "package", "expired": True}], "expired"),
        ([{"id": 7, "name": "package", "expired": None}], "observed"),
    ],
)
def test_noarch_artifact_evidence_distinguishes_availability(artifacts, expected):
    evidence = _evidence(conclusion="success")
    for job in evidence["jobs.json"]["jobs"]:
        job["conclusion"] = "success"
        job["steps"] = []
    evidence["artifacts.json"]["artifacts"] = artifacts
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
                    "settings": {"package_kind": "noarch"},
                }
            ],
        },
    }

    report = build_report(_manifest(), evidence, profile="auto")

    assert report["matrix"]["package"]["artifact_evidence"] == expected


def test_failed_noarch_run_is_not_called_partial_from_an_available_artifact():
    evidence = _evidence()
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
                    "settings": {"package_kind": "noarch"},
                }
            ],
        },
    }

    report = build_report(_manifest(), evidence, profile="auto")

    assert report["github"]["conclusion"] == "failure"
    assert report["receptor"]["assessment"] == "FAIL"
    assert "conda package: kind=noarch" in render_llm(report)


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


def test_docs_profile_preserves_every_step_and_reports_skipped_notebooks():
    evidence = _evidence()
    evidence["workflow.json"]["path"] = ".github/workflows/docs-notebooks.yaml"
    evidence["jobs.json"]["jobs"] = [
        {
            "id": 10,
            "name": "Execute the documented notebooks",
            "status": "completed",
            "conclusion": "failure",
            "steps": [
                {
                    "number": 1,
                    "name": "Setup conda env",
                    "status": "completed",
                    "conclusion": "failure",
                },
                {
                    "number": 2,
                    "name": "Execute every documented notebook",
                    "status": "completed",
                    "conclusion": "skipped",
                },
                {
                    "number": 3,
                    "name": "Collect the failure logs",
                    "status": "completed",
                    "conclusion": "success",
                },
                {
                    "number": 4,
                    "name": "Unrecognized finalizer",
                    "status": "completed",
                    "conclusion": "success",
                },
                {
                    "number": 5,
                    "name": "Additional info about the build",
                    "status": "completed",
                    "conclusion": "success",
                },
            ],
        }
    ]

    report = build_report(_manifest(), evidence, profile="docs")
    phases = {phase["name"]: phase for phase in report["matrix"]["phases"]}

    assert report["github"]["conclusion"] == "failure"
    assert report["receptor"]["assessment"] == "FAIL"
    assert len(report["jobs"][0]["steps"]) == 5
    assert sum(len(phase["evidence"]) for phase in phases.values()) == 5
    assert phases["setup"]["counts"] == {"failure": 1}
    assert phases["notebooks"]["counts"] == {"skipped": 1}
    assert phases["artifact"]["counts"] == {"success": 1}
    assert phases["other"]["counts"] == {"success": 2}
    assert "build" not in phases
    rendered = render_llm(report)
    assert "phases:" in rendered
    assert "notebooks=skipped:1" in rendered


def test_docs_profile_marks_separate_successful_build_and_failed_deploy_partial():
    evidence = _evidence()
    evidence["workflow.json"]["path"] = ".github/workflows/docs.yaml"
    evidence["jobs.json"]["jobs"] = [
        {
            "id": 10,
            "name": "Build documentation",
            "status": "completed",
            "conclusion": "success",
            "steps": [],
        },
        {
            "id": 20,
            "name": "Deploy GitHub Pages",
            "status": "completed",
            "conclusion": "failure",
            "steps": [],
        },
    ]

    report = build_report(_manifest(), evidence, profile="docs")

    assert report["github"]["conclusion"] == "failure"
    assert report["receptor"]["assessment"] == "PARTIAL"
    assert exit_code(report) == 1


def test_docs_profile_keeps_combined_build_deploy_evidence_indivisible():
    evidence = _evidence(conclusion="success")
    evidence["workflow.json"]["path"] = ".github/workflows/docs.yaml"
    evidence["jobs.json"]["jobs"] = [
        {
            "id": 10,
            "name": "Documentation",
            "status": "completed",
            "conclusion": "success",
            "steps": [
                {
                    "number": 1,
                    "name": "Run Sphinx to gh-pages action",
                    "status": "completed",
                    "conclusion": "success",
                }
            ],
        }
    ]

    report = build_report(_manifest(), evidence, profile="docs")
    phases = report["matrix"]["phases"]
    rendered = render_llm(report)

    assert phases == [
        {
            "name": "build_deploy",
            "counts": {"success": 1},
            "evidence": [
                {"job_id": 10, "step_number": 1, "kind": "step", "state": "success"}
            ],
        }
    ]
    assert "phases=build_deploy:1" in rendered
    assert rendered.count("\n") == 1


def test_docs_profile_does_not_treat_combined_build_deploy_as_independent_build():
    evidence = _evidence()
    evidence["workflow.json"]["path"] = ".github/workflows/docs.yaml"
    evidence["jobs.json"]["jobs"] = [
        {
            "id": 10,
            "name": "Documentation",
            "status": "completed",
            "conclusion": "failure",
            "steps": [
                {
                    "number": 1,
                    "name": "Run Sphinx to gh-pages action",
                    "status": "completed",
                    "conclusion": "success",
                },
                {
                    "number": 2,
                    "name": "Deploy GitHub Pages",
                    "status": "completed",
                    "conclusion": "failure",
                },
            ],
        }
    ]

    report = build_report(_manifest(), evidence, profile="docs")

    assert report["github"]["conclusion"] == "failure"
    assert report["receptor"]["assessment"] == "FAIL"
    assert exit_code(report) == 1


def test_unknown_step_state_is_preserved_with_source_reference():
    evidence = _evidence()
    evidence["jobs.json"]["jobs"][0]["steps"] = [
        {
            "number": 1,
            "name": "Future step",
            "status": "future_status",
            "conclusion": "future_conclusion",
        }
    ]

    report = build_report(_manifest(), evidence, profile="docs")

    assert [item["kind"] for item in report["unknowns"]] == [
        "github.step.status",
        "github.step.conclusion",
    ]


def _release_evidence(*, conclusion="failure"):
    evidence = _evidence(conclusion=conclusion)
    evidence["run.json"].update({"event": "push", "head_branch": "0.20.1"})
    evidence["workflow.json"]["path"] = ".github/workflows/npm-publish.yaml"
    evidence["jobs.json"]["jobs"] = [
        {
            "id": 10,
            "name": "publish",
            "status": "completed",
            "conclusion": conclusion,
            "steps": [
                {
                    "number": 1,
                    "name": "Checkout",
                    "status": "completed",
                    "conclusion": "success",
                },
                {
                    "number": 2,
                    "name": "Inject version and repo info",
                    "status": "completed",
                    "conclusion": "success",
                },
                {
                    "number": 3,
                    "name": "Build runtime bundle",
                    "status": "completed",
                    "conclusion": "failure" if conclusion == "failure" else "success",
                },
                {
                    "number": 4,
                    "name": "Publish to npm",
                    "status": "completed",
                    "conclusion": "skipped" if conclusion == "failure" else "success",
                },
            ],
        }
    ]
    evidence["artifacts.json"]["artifacts"] = []
    return evidence


def test_release_profile_preserves_trigger_identity_and_phase_evidence():
    report = build_report(_manifest(), _release_evidence(), profile="release")
    phases = {phase["name"]: phase for phase in report["matrix"]["phases"]}

    assert report["subject"]["event"] == "push"
    assert report["subject"]["head_ref"] == "0.20.1"
    assert report["subject"]["head_sha"] == "abc"
    assert report["matrix"]["identity"]["tag_verification"] == "not_observed"
    assert phases["identity"]["counts"] == {"success": 1}
    assert phases["package"]["counts"] == {"failure": 1}
    assert phases["publish"]["counts"] == {"skipped": 1}
    assert phases["setup"]["counts"] == {"success": 1}
    assert sum(len(phase["evidence"]) for phase in phases.values()) == 4
    assert report["matrix"]["verification"] == {
        "registry": "not_observed",
        "archive": "not_observed",
    }
    assert report["receptor"]["assessment"] == "FAIL"
    rendered = render_llm(report)
    assert "event=push ref=0.20.1" in rendered
    assert "failed=Build runtime bundle" in rendered
    assert "publish=skipped" in rendered


def test_release_profile_reports_successful_publish_as_step_evidence_only():
    report = build_report(
        _manifest(), _release_evidence(conclusion="success"), profile="release"
    )
    rendered = render_llm(report)

    assert report["receptor"]["assessment"] == "PASS"
    assert report["matrix"]["verification"]["registry"] == "step_success"
    assert report["matrix"]["identity"]["tag_verification"] == "not_observed"
    assert "registry=step_success" in rendered
    assert "sha=abc" in rendered
    assert "tag=unverified" in rendered


def test_release_profile_marks_only_separate_package_and_publish_partial():
    evidence = _release_evidence()
    evidence["jobs.json"]["jobs"][0]["steps"][2]["conclusion"] = "success"
    evidence["jobs.json"]["jobs"][0]["steps"][3]["conclusion"] = "failure"

    report = build_report(_manifest(), evidence, profile="release")

    assert report["github"]["conclusion"] == "failure"
    assert report["receptor"]["assessment"] == "PARTIAL"
    assert exit_code(report) == 1


def test_release_profile_keeps_composite_delivery_evidence_indivisible():
    evidence = _release_evidence()
    evidence["jobs.json"]["jobs"][0]["steps"] = [
        {
            "number": 1,
            "name": "Build, test, and publish the release platform",
            "status": "completed",
            "conclusion": "failure",
        }
    ]

    report = build_report(_manifest(), evidence, profile="release")
    phases = report["matrix"]["phases"]

    assert report["receptor"]["assessment"] == "FAIL"
    assert phases[0]["name"] == "gate+package+publish"
    assert phases[0]["evidence"][0]["facets"] == ["gate", "package", "publish"]
    assert sum(len(phase["evidence"]) for phase in phases) == 1


def test_release_archive_verification_is_not_registry_or_tag_verification():
    evidence = _release_evidence(conclusion="success")
    evidence["jobs.json"]["jobs"][0]["steps"] = [
        {
            "number": 1,
            "name": "Wait for and verify the Zenodo record",
            "status": "completed",
            "conclusion": "success",
        }
    ]

    report = build_report(_manifest(), evidence, profile="release")

    assert report["matrix"]["phases"][0]["name"] == "gate+archive"
    assert report["matrix"]["verification"] == {
        "registry": "not_observed",
        "archive": "step_success",
    }
    assert report["matrix"]["identity"]["tag_verification"] == "not_observed"


def test_release_job_fallback_does_not_invent_successful_publication_step():
    evidence = _release_evidence(conclusion="success")
    evidence["jobs.json"]["jobs"][0]["steps"] = []

    report = build_report(_manifest(), evidence, profile="release")

    assert report["matrix"]["phases"][0]["name"] == "publish"
    assert report["matrix"]["phases"][0]["evidence"][0]["kind"] == "job"
    assert report["matrix"]["verification"]["registry"] == "not_observed"
