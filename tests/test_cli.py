import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from gh_run_receptor.cli import _parser, _run_reference, main
from gh_run_receptor.errors import AcquisitionError
from gh_run_receptor.github import MINIMUM_GH_VERSION_TEXT

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


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
        members.append(
            {
                "path": name,
                "kind": f"test.{name}",
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "complete": True,
            }
        )
    manifest = {
        "schema": "gh-run-receptor.bundle@1",
        "repository": "uibcdf/example",
        "hostname": "github.com",
        "run_id": 1,
        "run_attempt": 1,
        "head_sha": "abc",
        "api_version": "2022-11-28",
        "receptor_version": "test",
        "capture_policy": "metadata",
        "captured_at": "2026-09-04T10:00:00+00:00",
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


def _replay_process(bundle: Path, options: tuple[str, ...], *, timezone: str, epoch: str):
    environment = os.environ.copy()
    environment.update(TZ=timezone, SOURCE_DATE_EPOCH=epoch, PYTHONUTF8="1")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "gh_run_receptor",
            "--profile",
            "ci",
            *options,
            "replay",
            str(bundle),
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        check=False,
    )


def _set_bundle_context(bundle: Path, *, captured_at: str, mtime: int) -> None:
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["captured_at"] = captured_at
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    for path in [*bundle.rglob("*"), bundle]:
        os.utime(path, (mtime, mtime))


@pytest.mark.parametrize(
    "options",
    [
        pytest.param(("--format", "json"), id="json"),
        pytest.param(("--receptor", "llm"), id="llm"),
        pytest.param(("--receptor", "human"), id="human"),
    ],
)
def test_replay_bytes_ignore_temporal_and_filesystem_context(tmp_path, options):
    source = FIXTURES / "bundles" / "molsysviewer_ci_failure"
    early = tmp_path / "early context" / "bundle"
    late = tmp_path / "late-context" / "nested" / "bundle"
    shutil.copytree(source, early)
    shutil.copytree(source, late)
    _set_bundle_context(early, captured_at="2000-01-01T00:00:00+00:00", mtime=946684800)
    _set_bundle_context(late, captured_at="2040-01-01T00:00:00+00:00", mtime=1893456000)

    first = _replay_process(early, options, timezone="UTC0", epoch="946684800")
    second = _replay_process(late, options, timezone="EST5EDT", epoch="1893456000")

    assert first.returncode == second.returncode == 1
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout


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
    args = _parser().parse_args(["inspect", "42", "--repo", "uibcdf/molsysmt", "--receptor", "llm"])

    assert args.repo == "uibcdf/molsysmt"
    assert args.receptor == "llm"
    assert args.format == "text"


@pytest.mark.parametrize("value", ["nan", "inf", "-inf", "0.99"])
def test_watch_rejects_non_finite_or_subsecond_intervals(value):
    with pytest.raises(SystemExit) as captured:
        _parser().parse_args(["watch", "42", "--interval", value])

    assert captured.value.code == 64


def test_watch_hands_terminal_poll_evidence_to_final_capture(monkeypatch):
    from gh_run_receptor.watch import RunSnapshot, RunState, WatchResult

    run = {"id": 42, "run_attempt": 1, "status": "completed", "conclusion": "success"}
    jobs = {"total_count": 0, "jobs": []}
    result = WatchResult(
        snapshot=RunSnapshot(
            state=RunState("completed", "success", 1, ()),
            run=run,
            jobs=jobs,
            api_requests=2,
        ),
        successful_snapshots=1,
        successful_poll_requests=2,
    )

    class Client:
        pass

    client = Client()
    observed = {}

    class ClientFactory:
        def __new__(cls, hostname):
            assert hostname == "github.com"
            return client

    def repository(explicit):
        assert explicit == "uibcdf/example"
        return explicit

    def watch(received_client, repository_name, run_id, **kwargs):
        assert (received_client, repository_name, run_id) == (client, "uibcdf/example", 42)
        assert kwargs["interval"] == 10
        assert kwargs["max_interval"] == 60
        return result

    def capture(args, **kwargs):
        observed.update(kwargs)
        return 0

    monkeypatch.setattr("gh_run_receptor.cli.GitHubClient", ClientFactory)
    monkeypatch.setattr(client, "repository", repository, raising=False)
    monkeypatch.setattr("gh_run_receptor.cli.watch_run", watch)
    monkeypatch.setattr("gh_run_receptor.cli._capture", capture)

    assert main(["watch", "42", "--repo", "uibcdf/example"]) == 0
    assert observed == {
        "render": True,
        "client": client,
        "repository": "uibcdf/example",
        "run": run,
        "jobs": jobs,
    }


def test_ci_profile_is_an_explicit_cli_choice():
    args = _parser().parse_args(["replay", "bundle", "--profile", "ci"])

    assert args.profile == "ci"


def test_docs_profile_is_an_explicit_cli_choice():
    args = _parser().parse_args(["replay", "bundle", "--profile", "docs"])

    assert args.profile == "docs"


def test_release_profile_is_an_explicit_cli_choice():
    args = _parser().parse_args(["replay", "bundle", "--profile", "release"])

    assert args.profile == "release"


def test_config_check_and_explain(tmp_path, capsys):
    config = tmp_path / "rules.yaml"
    config.write_text(
        """schema_version: 1
workflows:
  - match:
      path: .github/workflows/conda.yaml
    profile: conda
    settings:
      expected_platforms: [linux-64, win-64]
"""
    )

    assert main(["config", "check", str(config)]) == 0
    assert capsys.readouterr().out == "configuration valid: schema=1 rules=1\n"
    assert (
        main(
            [
                "config",
                "explain",
                ".github/workflows/conda.yaml",
                "--config",
                str(config),
            ]
        )
        == 0
    )
    assert capsys.readouterr().out == (
        "match=path:.github/workflows/conda.yaml profile=conda "
        "package_kind=native expected_platforms=linux-64,win-64\n"
    )


def test_config_explain_reports_explicit_noarch_package_kind(tmp_path, capsys):
    config = tmp_path / "rules.yaml"
    config.write_text(
        """schema_version: 1
workflows:
  - match:
      path: .github/workflows/conda.yaml
    profile: conda
    settings:
      package_kind: noarch
"""
    )

    assert (
        main(
            [
                "config",
                "explain",
                ".github/workflows/conda.yaml",
                "--config",
                str(config),
            ]
        )
        == 0
    )
    assert capsys.readouterr().out == (
        "match=path:.github/workflows/conda.yaml profile=conda "
        "package_kind=noarch expected_platforms=none\n"
    )


def test_config_explain_omits_conda_only_settings_for_docs(tmp_path, capsys):
    config = tmp_path / "rules.yaml"
    config.write_text(
        """schema_version: 1
workflows:
  - match:
      path: .github/workflows/docs.yaml
    profile: docs
"""
    )

    assert (
        main(
            [
                "config",
                "explain",
                ".github/workflows/docs.yaml",
                "--config",
                str(config),
            ]
        )
        == 0
    )
    assert capsys.readouterr().out == ("match=path:.github/workflows/docs.yaml profile=docs\n")


def test_config_check_returns_bounded_receptor_error(tmp_path, capsys):
    config = tmp_path / "rules.yaml"
    config.write_text("schema_version: 9\n")

    assert main(["config", "check", str(config)]) == 5
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("RECEPTOR_ERROR: line 1: unsupported schema_version")


def test_acquisition_error_exposes_category_and_keeps_exit_five(monkeypatch, capsys):
    def denied(self, explicit):
        raise AcquisitionError(
            "GitHub CLI request failed: permission denied (HTTP 403)",
            category="permission_denied",
            http_status=403,
        )

    monkeypatch.setattr("gh_run_receptor.cli.GitHubClient.repository", denied)

    assert main(["inspect", "42", "--repo", "uibcdf/example"]) == 5
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "RECEPTOR_ERROR category=permission_denied: "
        "GitHub CLI request failed: permission denied (HTTP 403)\n"
    )


def test_init_previews_without_writing(tmp_path, capsys):
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yaml").write_text("name: CI\n")

    assert main(["init", str(tmp_path)]) == 0

    captured = capsys.readouterr()
    assert captured.out == (
        "schema_version: 1\n"
        "workflows:\n"
        "  - match:\n"
        "      path: .github/workflows/ci.yaml\n"
        "    profile: ci\n"
    )
    assert "profile=ci confidence=high" in captured.err
    assert not (tmp_path / ".github" / "gh-run-receptor.yaml").exists()


def test_init_write_creates_once_and_then_returns_a_receptor_error(tmp_path, capsys):
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "unknown.yml").write_text("name: Custom\n")

    assert main(["init", str(tmp_path), "--write"]) == 0
    first = capsys.readouterr()
    target = tmp_path / ".github" / "gh-run-receptor.yaml"
    original = target.read_bytes()
    assert first.out == f"configuration written: path={target} workflows=1\n"
    assert "profile=generic confidence=low reason=no-profile-signal" in first.err

    assert main(["init", str(tmp_path), "--write"]) == 5
    second = capsys.readouterr()
    assert second.out == ""
    assert "configuration already exists" in second.err
    assert target.read_bytes() == original


def test_help_declares_the_minimum_github_cli(capsys):
    with pytest.raises(SystemExit) as captured:
        main(["--help"])

    assert captured.value.code == 0
    normalized = " ".join(capsys.readouterr().out.split())
    assert f"GitHub CLI {MINIMUM_GH_VERSION_TEXT} or newer" in normalized
