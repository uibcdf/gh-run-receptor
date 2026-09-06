import json
from pathlib import Path

from gh_run_receptor.embedded import MAX_REPORT_BYTES, run_action
from gh_run_receptor.errors import AcquisitionError


def _report(*, assessment="PASS", conclusion="success", status="completed", warning=""):
    return {
        "schema": "gh-run-receptor.report@1",
        "subject": {
            "repository": "uibcdf/example",
            "run_id": 42,
            "run_attempt": 1,
            "head_sha": "abc",
            "workflow": ".github/workflows/ci.yml",
            "url": "https://github.com/uibcdf/example/actions/runs/42",
        },
        "github": {"status": status, "conclusion": conclusion},
        "receptor": {
            "assessment": assessment,
            "profile": "ci",
            "profile_version": 1,
            "evidence_sufficient": True,
            "cause_evidence": "not_captured",
        },
        "completeness": {
            "metadata": "complete",
            "jobs": "complete",
            "checks": "complete",
            "artifact_inventory": "complete",
            "artifact_content": "not_requested",
            "logs": "not_requested",
        },
        "configuration": {
            "matched": False,
            "source": None,
            "match": None,
            "profile": None,
            "settings": {},
        },
        "expectations": {"satisfied": True, "missing_platforms": []},
        "jobs": [],
        "job_counts": {},
        "artifacts": [],
        "matrix": {"kind": "ci", "roles": []},
        "causes": [],
        "unknowns": [],
        "warnings": [warning] if warning else [],
    }


def _environment(tmp_path: Path, **overrides):
    values = {
        "GITHUB_RUN_ID": "42",
        "GITHUB_REPOSITORY": "uibcdf/example",
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_OUTPUT": str(tmp_path / "output"),
        "GITHUB_STEP_SUMMARY": str(tmp_path / "summary"),
        "RUNNER_TEMP": str(tmp_path),
        "INPUT_RUN_ID": "",
        "INPUT_REPOSITORY": "",
        "INPUT_PROFILE": "ci",
        "INPUT_CAPTURE": "metadata",
        "INPUT_REPORT_NAME": "receptor-report",
        "INPUT_STRICT_REPORTER": "false",
        "RECEPTOR_ACTION_REPOSITORY": "uibcdf/gh-run-receptor",
        "RECEPTOR_ACTION_REF": "0.12.0",
    }
    values.update(overrides)
    return values


def _outputs(path: Path):
    return dict(line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines())


def test_success_publishes_one_canonical_report_summary_and_scalar_outputs(tmp_path, capsys):
    report = _report(warning="untrusted <script>alert(1)</script>")
    calls = []

    def factory(**kwargs):
        calls.append(kwargs)
        return report

    environment = _environment(tmp_path)
    assert run_action(environment, report_factory=factory) == 0

    output = _outputs(tmp_path / "output")
    report_path = Path(output["report-path"])
    assert json.loads(report_path.read_text(encoding="utf-8")) == report
    assert report["publisher"] == {
        "kind": "github_action",
        "repository": "uibcdf/gh-run-receptor",
        "ref": "0.12.0",
    }
    assert report_path.stat().st_size <= MAX_REPORT_BYTES
    assert output == {
        "assessment": "PASS",
        "github-conclusion": "success",
        "profile": "ci",
        "failed-groups": "0",
        "incomplete-groups": "0",
        "report-artifact": "receptor-report",
        "report-path": str(report_path),
        "report-ready": "true",
    }
    summary = (tmp_path / "summary").read_text(encoding="utf-8")
    assert "## gh-run-receptor" in summary
    assert "&lt;script&gt;" in summary
    assert "<script>" not in summary
    assert len(summary.encode()) < 32 * 1024
    assert capsys.readouterr().out.startswith("PASS conclusion=success")
    assert calls == [
        {
            "repository": "uibcdf/example",
            "hostname": "github.com",
            "run_id": 42,
            "profile": "ci",
            "capture": "metadata",
            "cache_root": tmp_path / "gh-run-receptor-action",
        }
    ]


def test_source_failure_is_a_successful_reporter_result(tmp_path):
    environment = _environment(tmp_path)

    assert run_action(environment, report_factory=lambda **_: _report(
        assessment="FAIL", conclusion="failure"
    )) == 0
    assert _outputs(tmp_path / "output")["assessment"] == "FAIL"


def test_current_run_remains_pending_while_the_reporter_executes(tmp_path):
    environment = _environment(tmp_path)

    assert run_action(environment, report_factory=lambda **_: _report(
        assessment="PENDING", conclusion=None, status="in_progress"
    )) == 0
    outputs = _outputs(tmp_path / "output")
    assert outputs["assessment"] == "PENDING"
    assert outputs["github-conclusion"] == ""


def test_local_action_uses_the_workflow_repository_as_publisher(tmp_path):
    environment = _environment(
        tmp_path,
        RECEPTOR_ACTION_REPOSITORY="",
        RECEPTOR_ACTION_REF="",
    )
    report = _report()

    assert run_action(environment, report_factory=lambda **_: report) == 0
    assert report["publisher"] == {
        "kind": "github_action",
        "repository": "uibcdf/example",
        "ref": "local",
    }


def test_internal_failure_is_bounded_visible_and_has_no_report(tmp_path, capsys):
    token = "ghp_" + "A" * 30
    environment = _environment(tmp_path)

    def fail(**_):
        raise AcquisitionError(
            f"denied {token}\nsecond line\x1b[31m" * 100,
            category="permission_denied",
            http_status=403,
        )

    assert run_action(environment, report_factory=fail) == 5
    outputs = _outputs(tmp_path / "output")
    assert outputs == {"report-ready": "false"}
    rendered = capsys.readouterr().err
    assert rendered.startswith("RECEPTOR_ERROR category=permission_denied:")
    assert token not in rendered
    assert "\x1b" not in rendered
    assert len(rendered) <= 650
    summary = (tmp_path / "summary").read_text(encoding="utf-8")
    assert "RECEPTOR_ERROR" in summary
    assert token not in summary


def test_unsafe_report_name_is_rejected_before_acquisition(tmp_path):
    environment = _environment(tmp_path, INPUT_REPORT_NAME="../escape")
    called = False

    def factory(**_):
        nonlocal called
        called = True

    assert run_action(environment, report_factory=factory) == 5
    assert called is False
    assert _outputs(tmp_path / "output") == {"report-ready": "false"}


def test_invalid_strict_reporter_value_is_rejected_before_acquisition(tmp_path):
    environment = _environment(tmp_path, INPUT_STRICT_REPORTER="yes")
    called = False

    def factory(**_):
        nonlocal called
        called = True

    assert run_action(environment, report_factory=factory) == 5
    assert called is False
    assert _outputs(tmp_path / "output") == {"report-ready": "false"}


def test_oversized_json_is_a_reporter_failure(tmp_path):
    environment = _environment(tmp_path)
    report = _report(warning="x" * MAX_REPORT_BYTES)

    assert run_action(environment, report_factory=lambda **_: report) == 5
    assert _outputs(tmp_path / "output") == {"report-ready": "false"}
    assert not list(tmp_path.glob("*.json"))
