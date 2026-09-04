import argparse
import hashlib
import json

import pytest

from gh_run_receptor.cli import _parser, _run_reference, main


def _bundle(path, conclusion="success"):
    path.mkdir()
    values = {
        "run.json": {
            "status": "completed",
            "conclusion": conclusion,
            "name": "CI",
            "html_url": "https://example.invalid/run/1",
        },
        "workflow.json": {"path": ".github/workflows/ci.yaml"},
        "jobs.json": {"jobs": []},
        "checks.json": {"check_runs": []},
        "artifacts.json": {"artifacts": []},
    }
    members = []
    for name, value in values.items():
        data = (json.dumps(value, sort_keys=True) + "\n").encode()
        (path / name).write_bytes(data)
        members.append({"path": name, "sha256": hashlib.sha256(data).hexdigest()})
    manifest = {
        "schema": "gh-run-receptor.bundle@1",
        "repository": "uibcdf/example",
        "run_id": 1,
        "run_attempt": 1,
        "head_sha": "abc",
        "complete": True,
        "members": members,
        "warnings": [],
    }
    (path / "manifest.json").write_text(json.dumps(manifest))


def test_replay_success_is_compact(tmp_path, capsys):
    bundle = tmp_path / "bundle"
    _bundle(bundle)

    result = main(["replay", str(bundle)])

    captured = capsys.readouterr()
    assert result == 0
    assert captured.err == ""
    assert len(captured.out.splitlines()) == 1
    assert captured.out.startswith("PASS conclusion=success")


def test_replay_failure_returns_authoritative_failure(tmp_path, capsys):
    bundle = tmp_path / "bundle"
    _bundle(bundle, conclusion="failure")

    result = main(["--format", "json", "replay", str(bundle)])

    report = json.loads(capsys.readouterr().out)
    assert result == 1
    assert report["github"]["conclusion"] == "failure"


def test_explicit_human_receptor_is_explanatory(tmp_path, capsys):
    bundle = tmp_path / "bundle"
    _bundle(bundle)

    result = main(["--receptor", "human", "replay", str(bundle)])

    output = capsys.readouterr().out
    assert result == 0
    assert output.startswith("gh-run-receptor: PASS\n")
    assert "Repository:  uibcdf/example" in output
    assert "Jobs (0)" in output


def test_explicit_llm_receptor_is_compact_in_a_tty(tmp_path, capsys, monkeypatch):
    bundle = tmp_path / "bundle"
    _bundle(bundle)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)

    result = main(["--receptor", "llm", "replay", str(bundle)])

    output = capsys.readouterr().out
    assert result == 0
    assert output.startswith("PASS conclusion=success")
    assert "Repository:" not in output


def test_default_receptor_is_human_in_a_tty(tmp_path, capsys, monkeypatch):
    bundle = tmp_path / "bundle"
    _bundle(bundle)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)

    result = main(["replay", str(bundle)])

    assert result == 0
    assert capsys.readouterr().out.startswith("gh-run-receptor: PASS\n")


def test_run_url_carries_repository_and_hostname():
    reference = _run_reference("https://github.com/uibcdf/molsysmt/actions/runs/33863426589")

    assert reference.run_id == 33863426589
    assert reference.repository == "uibcdf/molsysmt"
    assert reference.hostname == "github.com"


@pytest.mark.parametrize("value", ["run-123", "http://github.com/a/b/actions/runs/1", "12x"])
def test_invalid_run_reference_is_rejected(value):
    with pytest.raises(argparse.ArgumentTypeError, match="numeric ID or GitHub Actions run URL"):
        _run_reference(value)


def test_common_options_are_accepted_after_subcommand():
    args = _parser().parse_args(
        ["inspect", "42", "--repo", "uibcdf/molsysmt", "--receptor", "llm"]
    )

    assert args.repo == "uibcdf/molsysmt"
    assert args.receptor == "llm"
    assert args.format == "text"
