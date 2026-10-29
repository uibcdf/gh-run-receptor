"""Preserve staged-file identity while receiving through supported shared operations."""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_staged_workflow_keeps_original_artifact_and_separate_qualification_identity():
    path = ROOT / ".github/workflows/test-staged-conda.yml"
    workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read"}
    prepare = workflow["jobs"]["prepare"]
    assert prepare["name"] == "installed / prepare"
    assert "--qualification-sha" in json.dumps(prepare)
    job = workflow["jobs"]["installed"]
    assert job["name"] == "installed / ${{ matrix.platform }} · Python ${{ matrix.python }}"
    checkout_refs = [
        (s.get("with", {}).get("path"), s.get("with", {}).get("ref"))
        for s in job["steps"]
        if s.get("uses", "").startswith("actions/checkout@")
    ]
    assert ("component", "${{ inputs.candidate_sha }}") in checkout_refs
    assert (".molsyssuite", "fee3bd875e68778844c0fffc2aba26b6cea02cd6") in checkout_refs
    assert job["env"]["TEST_SUPPORT_QUALIFICATION_SHA"] == "${{ github.sha }}"
    assert job["env"]["TEST_SUPPORT_CANDIDATE_SHA"] == "${{ inputs.candidate_sha }}"
    setup = next(s for s in job["steps"] if "setup-miniconda@" in s.get("uses", ""))
    assert setup["with"]["run-init"] == setup["with"]["remove-profiles"] == "false"
    steps = {s.get("name"): s for s in job["steps"]}
    repair = steps["Repair Windows installer launcher metadata"]
    assert repair["if"] == "runner.os == 'Windows'"
    assert repair["env"]["CONDA_SAFETY_CHECKS"] == "enabled"
    assert "--name base --force-reinstall" in repair["run"]
    assert "conda-launchers" in repair["run"]
    assert 'installed_noarch.py" tests' in steps["Run installed tests"]["run"]
    assert "installed_test_helpers.py" not in json.dumps(workflow)
    assert "installed-shared-support.json" in steps["Run installed tests"]["run"]
    assert " verify " in steps["Validate installed files"]["run"]
    assert " verify " in steps["Recheck installed provenance after scientific tests"]["run"]
    assert "--sha256" in steps["Install exact artifact"]["run"]
    assert "pip install" not in json.dumps(job) and "upload: true" not in json.dumps(job)
