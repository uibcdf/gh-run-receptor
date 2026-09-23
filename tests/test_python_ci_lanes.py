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
    assert any("python -m pytest --receptor=llm" in step.get("run", "") for step in job["steps"])
    assert any('".[test]"' in step.get("run", "") for step in job["steps"])


def test_routine_linux_python_313_runs_on_push_and_pull_request():
    workflow = _workflow("python-routine.yml")
    assert set(workflow["on"]) == {"push", "pull_request"}
    assert all(not value for value in workflow["on"].values())
    job = workflow["jobs"]["test"]
    assert job["runs-on"] == "ubuntu-latest"
    assert job["steps"][1]["with"]["python-version"] == "3.13"
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
