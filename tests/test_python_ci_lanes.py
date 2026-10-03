"""Protect the inherited MOLI Python CI lanes for this admitted member."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def _workflow(name: str) -> dict:
    return yaml.load((WORKFLOWS / name).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def _assert_gating_pytest(job: dict) -> None:
    assert "if" not in job
    assert "continue-on-error" not in job
    assert "strategy" not in job or job["strategy"].get("fail-fast") == "false"
    assert any(
        "python -m pytest --receptor=ci" in step.get("run", "")
        or "-m pytest --receptor=ci" in step.get("run", "")
        and "python -m coverage run --branch --source=gh_run_receptor" in step.get("run", "")
        for step in job["steps"]
    )
    assert any('".[test]"' in step.get("run", "") for step in job["steps"])


def test_routine_linux_python_314_runs_on_push_and_pull_request():
    workflow = _workflow("python-routine.yml")
    assert set(workflow["on"]) == {"push", "pull_request", "workflow_dispatch"}
    assert all(not value for value in workflow["on"].values())
    job = workflow["jobs"]["test"]
    assert job["runs-on"] == "ubuntu-latest"
    assert job["steps"][1]["with"]["python-version"] == "3.14"
    _assert_gating_pytest(job)


def test_weekly_full_supported_range_has_manual_dispatch_and_platform_evidence():
    workflow = _workflow("python-weekly.yml")
    assert set(workflow["on"]) == {"schedule", "workflow_dispatch"}
    assert workflow["on"]["schedule"][0]["cron"]
    job = workflow["jobs"]["test"]
    assert job["runs-on"] == "${{ matrix.os }}"
    assert job["steps"][1]["with"]["python-version"] == "${{ matrix.python }}"
    assert {(entry["os"], entry["python"]) for entry in job["strategy"]["matrix"]["include"]} == {
        (os_name, python)
        for os_name in ("ubuntu-latest", "macos-latest", "windows-latest")
        for python in ("3.11", "3.12", "3.13", "3.14")
    }
    _assert_gating_pytest(job)


def test_coverage_publication_cannot_run_for_pull_requests_or_feature_branches():
    workflow = _workflow("python-routine.yml")
    assert workflow["permissions"] == {"contents": "read"}
    producer = workflow["jobs"]["test"]
    assert "permissions" not in producer
    publisher = workflow["jobs"]["coverage-upload"]
    assert publisher["needs"] == "test"
    assert publisher["if"] == (
        "github.event_name != 'pull_request' && github.ref == 'refs/heads/main'"
    )
    assert publisher["permissions"] == {"contents": "read", "id-token": "write"}
    upload = publisher["steps"][-1]
    assert upload["with"]["use_oidc"] == "true"
    assert upload["with"]["fail_ci_if_error"] == "true"
    assert upload["with"]["disable_search"] == "true"
    assert len(upload["uses"].split("@")[1]) == 40
