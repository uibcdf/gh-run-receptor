from pathlib import Path

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
