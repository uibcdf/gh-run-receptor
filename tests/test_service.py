from pathlib import Path

import pytest

from gh_run_receptor.errors import BundleError
from gh_run_receptor.service import CapturedEvidence, acquire_evidence, create_report


class _Client:
    hostname = "github.com"

    def json(self, endpoint):
        assert endpoint == "/repos/uibcdf/example/actions/runs/42"
        return {"run_attempt": 2}

    def repository(self, repository):
        assert repository == "uibcdf/example"
        return repository


def test_acquire_evidence_captures_then_loads_the_shared_bundle(tmp_path, monkeypatch):
    destination = tmp_path / "bundle"
    manifest = {
        "repository": "uibcdf/example",
        "run_id": 42,
        "run_attempt": 2,
        "capture_policy": "metadata",
    }
    evidence = {"run.json": {"id": 42}}
    calls = []

    def capture(client, repository, run_id, **kwargs):
        calls.append((client, repository, run_id, kwargs))
        destination.mkdir()
        return manifest

    monkeypatch.setattr("gh_run_receptor.service.capture_bundle", capture)
    monkeypatch.setattr("gh_run_receptor.service.load_bundle", lambda path: (manifest, evidence))

    result = acquire_evidence(
        _Client(),
        "uibcdf/example",
        42,
        attempt=None,
        policy="metadata",
        cache_root=tmp_path / "cache",
        output=destination,
    )

    assert result == CapturedEvidence(manifest=manifest, evidence=evidence, path=destination)
    assert calls[0][1:3] == ("uibcdf/example", 42)
    assert calls[0][3]["run"] == {"run_attempt": 2}


def test_acquire_evidence_reuses_terminal_run_and_jobs_handoff(tmp_path, monkeypatch):
    destination = tmp_path / "bundle"
    run = {"id": 42, "run_attempt": 2, "status": "completed", "conclusion": "success"}
    jobs = {"total_count": 0, "jobs": []}
    manifest = {
        "repository": "uibcdf/example",
        "run_id": 42,
        "run_attempt": 2,
        "capture_policy": "metadata",
    }
    evidence = {"run.json": run, "jobs.json": jobs}
    calls = []

    class NoRequestClient:
        hostname = "github.com"

        def json(self, endpoint):
            pytest.fail(f"terminal handoff repeated request: {endpoint}")

    def capture(client, repository, run_id, **kwargs):
        calls.append(kwargs)
        destination.mkdir()
        return manifest

    monkeypatch.setattr("gh_run_receptor.service.capture_bundle", capture)
    monkeypatch.setattr("gh_run_receptor.service.load_bundle", lambda path: (manifest, evidence))

    acquire_evidence(
        NoRequestClient(),
        "uibcdf/example",
        42,
        attempt=2,
        policy="metadata",
        cache_root=tmp_path / "cache",
        output=destination,
        run=run,
        jobs=jobs,
    )

    assert calls == [
        {
            "attempt": 2,
            "policy": "metadata",
            "destination": destination,
            "run": run,
            "jobs": jobs,
        }
    ]


@pytest.mark.parametrize(
    ("run", "attempt", "message"),
    [
        ({"id": 99, "run_attempt": 1, "status": "completed"}, 1, "conflicting identity"),
        ({"id": 42, "run_attempt": 2, "status": "completed"}, 1, "conflicting attempt"),
        ({"id": 42, "run_attempt": 1, "status": "in_progress"}, 1, "terminal"),
    ],
)
def test_acquire_evidence_rejects_invalid_terminal_handoff(tmp_path, run, attempt, message):
    with pytest.raises(BundleError, match=message):
        acquire_evidence(
            _Client(),
            "uibcdf/example",
            42,
            attempt=attempt,
            policy="metadata",
            cache_root=tmp_path,
            run=run,
            jobs={"total_count": 0, "jobs": []},
        )


def test_acquire_evidence_refreshes_a_cached_active_run(tmp_path, monkeypatch):
    destination = tmp_path / "cache" / "github.com/uibcdf/example/42/2/metadata"
    destination.mkdir(parents=True)
    old_manifest = {
        "repository": "uibcdf/example",
        "run_id": 42,
        "run_attempt": 2,
        "capture_policy": "metadata",
    }
    old_evidence = {"run.json": {"id": 42, "status": "in_progress"}}
    new_manifest = dict(old_manifest)
    new_evidence = {"run.json": {"id": 42, "status": "completed", "conclusion": "failure"}}
    capture_destinations = []

    def load(path):
        if path == destination and not capture_destinations:
            return old_manifest, old_evidence
        return new_manifest, new_evidence

    def capture(client, repository, run_id, **kwargs):
        replacement = kwargs["destination"]
        capture_destinations.append(replacement)
        replacement.mkdir()
        return new_manifest

    monkeypatch.setattr("gh_run_receptor.service.load_bundle", load)
    monkeypatch.setattr("gh_run_receptor.service.capture_bundle", capture)

    result = acquire_evidence(
        _Client(),
        "uibcdf/example",
        42,
        attempt=None,
        policy="metadata",
        cache_root=tmp_path / "cache",
    )

    assert result == CapturedEvidence(new_manifest, new_evidence, destination)
    assert len(capture_destinations) == 1
    assert capture_destinations[0] != destination
    assert destination.is_dir()
    assert not list(destination.parent.glob(".metadata.*-*"))


def test_acquire_evidence_reuses_a_cached_completed_run(tmp_path, monkeypatch):
    destination = tmp_path / "cache" / "github.com/uibcdf/example/42/2/metadata"
    destination.mkdir(parents=True)
    manifest = {
        "repository": "uibcdf/example",
        "run_id": 42,
        "run_attempt": 2,
        "capture_policy": "metadata",
    }
    evidence = {"run.json": {"id": 42, "status": "completed", "conclusion": "success"}}

    monkeypatch.setattr("gh_run_receptor.service.load_bundle", lambda path: (manifest, evidence))
    monkeypatch.setattr(
        "gh_run_receptor.service.capture_bundle",
        lambda *args, **kwargs: pytest.fail("completed evidence was recaptured"),
    )

    result = acquire_evidence(
        _Client(),
        "uibcdf/example",
        42,
        attempt=None,
        policy="metadata",
        cache_root=tmp_path / "cache",
    )

    assert result == CapturedEvidence(manifest, evidence, destination)


def test_active_refresh_restores_the_cached_bundle_when_installation_fails(tmp_path, monkeypatch):
    destination = tmp_path / "cache" / "github.com/uibcdf/example/42/2/metadata"
    destination.mkdir(parents=True)
    marker = destination / "old"
    marker.write_text("retained", encoding="utf-8")
    manifest = {
        "repository": "uibcdf/example",
        "run_id": 42,
        "run_attempt": 2,
        "capture_policy": "metadata",
    }
    old_evidence = {"run.json": {"id": 42, "status": "in_progress"}}
    new_evidence = {"run.json": {"id": 42, "status": "completed"}}

    monkeypatch.setattr(
        "gh_run_receptor.service.load_bundle",
        lambda path: (manifest, old_evidence if path == destination else new_evidence),
    )

    def capture(client, repository, run_id, **kwargs):
        kwargs["destination"].mkdir()
        return manifest

    monkeypatch.setattr("gh_run_receptor.service.capture_bundle", capture)
    original_rename = Path.rename

    def fail_replacement_install(path, target):
        if path.name.startswith(".metadata.refresh-") and target == destination:
            raise OSError("simulated replacement failure")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_replacement_install)

    with pytest.raises(OSError, match="simulated replacement failure"):
        acquire_evidence(
            _Client(),
            "uibcdf/example",
            42,
            attempt=None,
            policy="metadata",
            cache_root=tmp_path / "cache",
        )

    assert marker.read_text(encoding="utf-8") == "retained"
    assert not list(destination.parent.glob(".metadata.*-*"))


def test_create_report_delegates_to_the_same_capture_and_report_core(tmp_path, monkeypatch):
    captured = CapturedEvidence(
        manifest={"schema": "bundle"},
        evidence={"run.json": {"id": 42}},
        path=Path("bundle"),
    )
    client = _Client()
    acquire_calls = []
    build_calls = []

    monkeypatch.setattr("gh_run_receptor.service.GitHubClient", lambda hostname: client)

    def acquire(*args, **kwargs):
        acquire_calls.append((args, kwargs))
        return captured

    def build(*args, **kwargs):
        build_calls.append((args, kwargs))
        return {"schema": "gh-run-receptor.report@1"}

    monkeypatch.setattr("gh_run_receptor.service.acquire_evidence", acquire)
    monkeypatch.setattr("gh_run_receptor.service.build_report", build)

    report = create_report(
        repository="uibcdf/example",
        hostname="github.com",
        run_id=42,
        profile="ci",
        capture="metadata",
        cache_root=tmp_path,
    )

    assert report == {"schema": "gh-run-receptor.report@1"}
    assert acquire_calls == [
        (
            (client, "uibcdf/example", 42),
            {"attempt": None, "policy": "metadata", "cache_root": tmp_path},
        )
    ]
    assert build_calls == [
        (
            (captured.manifest, captured.evidence),
            {"profile": "ci", "bundle_directory": Path("bundle")},
        )
    ]


def test_create_report_passes_inline_config_to_the_shared_builder(tmp_path, monkeypatch):
    captured = CapturedEvidence(
        manifest={"schema": "bundle"},
        evidence={"run.json": {"id": 42}},
        path=Path("bundle"),
    )
    client = _Client()
    build_calls = []
    config = {"schema": "gh-run-receptor.config@1"}
    source = {"kind": "action_inline"}

    monkeypatch.setattr("gh_run_receptor.service.GitHubClient", lambda hostname: client)
    monkeypatch.setattr(
        "gh_run_receptor.service.acquire_evidence", lambda *args, **kwargs: captured
    )
    monkeypatch.setattr(
        "gh_run_receptor.service.build_report",
        lambda *args, **kwargs: build_calls.append((args, kwargs)) or {"schema": "report"},
    )

    report = create_report(
        repository="uibcdf/example",
        hostname="github.com",
        run_id=42,
        profile="auto",
        capture="metadata",
        cache_root=tmp_path,
        config_override=config,
        config_source_override=source,
    )

    assert report == {"schema": "report"}
    assert build_calls[0][1]["config_override"] is config
    assert build_calls[0][1]["config_source_override"] is source
