import json
import subprocess
from pathlib import Path

import pytest

from devtools.scripts import validate_public_runs
from devtools.scripts.validate_public_runs import (
    AcquisitionFailure,
    SemanticFailure,
    load_manifest,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "devtools/public_runs.toml"
WORKFLOW = ROOT / ".github/workflows/validate-portability.yml"


def _report(repository, run_id, attempt, event, conclusion, jobs):
    return {
        "subject": {
            "repository": repository,
            "run_id": run_id,
            "run_attempt": attempt,
            "event": event,
        },
        "github": {"status": "completed", "conclusion": conclusion},
        "job_counts": {"success": jobs},
    }


def _runner(entries, *, receptor_exit=None, native_conclusion=None):
    by_repository = {entry.repository: entry for entry in entries}

    def run(command, **kwargs):
        assert kwargs == {"capture_output": True, "text": True, "check": False}
        if command[0] == "gh":
            repository = command[command.index("--repo") + 1]
            entry = by_repository[repository]
            payload = {
                "databaseId": entry.run_id,
                "attempt": entry.attempt,
                "conclusion": native_conclusion or entry.conclusion,
                "status": "completed",
                "url": f"https://github.com/{repository}/actions/runs/{entry.run_id}",
            }
            return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

        repository = command[command.index("--repo") + 1]
        entry = by_repository[repository]
        if receptor_exit is not None:
            return subprocess.CompletedProcess(command, receptor_exit, "", "API unavailable")
        if "--output" in command:
            Path(command[command.index("--output") + 1]).write_text("{}", encoding="utf-8")
        if "--format" in command and command[command.index("--format") + 1] == "json":
            payload = _report(
                repository,
                entry.run_id,
                entry.attempt,
                entry.event,
                entry.conclusion,
                entry.minimum_jobs,
            )
            return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
        text = f"PASS conclusion={entry.conclusion} | {repository} run={entry.run_id}\n"
        return subprocess.CompletedProcess(command, 0, text, "")

    return run


def test_manifest_is_diverse_and_requires_replay():
    entries = load_manifest(MANIFEST)

    assert len(entries) == len({entry.repository for entry in entries}) == 3
    assert all(not entry.repository.startswith("uibcdf/") for entry in entries)
    assert sum(entry.offline_replay for entry in entries) == 1
    assert max(entry.minimum_jobs for entry in entries) >= 50


def test_validator_checks_native_parity_bounded_text_and_replay():
    entries = load_manifest(MANIFEST)

    validate(entries, runner=_runner(entries))


def test_validator_distinguishes_acquisition_from_semantic_failure():
    entries = load_manifest(MANIFEST)

    with pytest.raises(AcquisitionFailure, match="receptor acquisition"):
        validate(entries, runner=_runner(entries, receptor_exit=5))
    with pytest.raises(SemanticFailure, match="receptor returned 1"):
        validate(entries, runner=_runner(entries, receptor_exit=1))
    with pytest.raises(SemanticFailure, match="native conclusion"):
        validate(entries, runner=_runner(entries, native_conclusion="failure"))


@pytest.mark.parametrize(
    ("runner", "expected_code", "expected_text"),
    [
        ("acquisition", 2, "Portability corpus: UNAVAILABLE"),
        ("semantic", 1, "Portability corpus: FAIL"),
    ],
)
def test_cli_exposes_distinct_gate_states(
    runner, expected_code, expected_text, monkeypatch, capsys
):
    entries = load_manifest(MANIFEST)
    fake = (
        _runner(entries, receptor_exit=5)
        if runner == "acquisition"
        else _runner(entries, native_conclusion="failure")
    )
    monkeypatch.setattr(validate_public_runs.subprocess, "run", fake)

    assert validate_public_runs.main(["--manifest", str(MANIFEST)]) == expected_code
    captured = capsys.readouterr()
    assert expected_text in captured.err
    assert len(captured.err.splitlines()) == 1


def test_hosted_gate_is_manual_read_only_bounded_and_pinned():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert source.count("workflow_dispatch:") == 1
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert "permissions:\n  contents: read" in source
    assert "timeout-minutes: 10" in source
    assert "GH_TOKEN: ${{ github.token }}" in source
    assert "python devtools/scripts/validate_public_runs.py" in source
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7" in source
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7" in source
