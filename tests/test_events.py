import hashlib
import json
import zipfile
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator

from gh_run_receptor.errors import BundleError
from gh_run_receptor.events import (
    EVENT_DOCUMENT_NAME,
    event_artifact_prefix,
    read_event_archive,
    select_event_artifacts,
    validate_event_document,
    verify_event_archive_digest,
)
from gh_run_receptor.report import build_report, render_llm


def _document(*, head_sha="abc", events=None):
    return {
        "schema": "gh-run-receptor.events@1",
        "producer": {
            "repository": "uibcdf/action-build-and-upload-conda-packages",
            "ref": "v2.1.0",
        },
        "subject": {
            "repository": "uibcdf/example",
            "run_id": 42,
            "run_attempt": 2,
            "head_sha": head_sha,
            "job_key": "conda_deployment",
            "matrix_index": 1,
        },
        "events": events
        or [
            {
                "kind": "conda.package",
                "platform": "linux-64",
                "artifact": "example-1.0-py311_0.conda",
                "sha256": "a" * 64,
                "build": "success",
                "upload": "success",
                "python_versions": ["3.11"],
            }
        ],
    }


def _validate(document):
    return validate_event_document(
        document,
        repository="uibcdf/example",
        run_id=42,
        run_attempt=2,
        head_sha="abc",
    )


def _archive(path, document, *, name=EVENT_DOCUMENT_NAME):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name, json.dumps(document, sort_keys=True))


def test_event_document_matches_schema_and_exact_source_identity():
    document = _document()

    assert _validate(document) is document
    schema = json.loads(
        files("gh_run_receptor.schemas")
        .joinpath("events-v1.schema.json")
        .read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(document)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda value: value["subject"].update(run_attempt=3), "attempt conflicts"),
        (lambda value: value["subject"].update(head_sha="other"), "head sha conflicts"),
        (lambda value: value["events"][0].update(artifact="../escape.conda"), "unsafe"),
        (lambda value: value["events"][0].update(build="maybe"), "unsupported result"),
        (lambda value: value.update(schema="gh-run-receptor.events@2"), "future events"),
    ],
)
def test_event_document_rejects_conflicts_and_unsafe_values(change, message):
    document = _document()
    change(document)

    with pytest.raises(BundleError, match=message):
        _validate(document)


def test_event_document_rejects_duplicate_package_identity():
    event = _document()["events"][0]

    with pytest.raises(BundleError, match="duplicates"):
        _validate(_document(events=[event, dict(event)]))


def test_artifact_selection_is_attempt_qualified_bounded_and_deterministic():
    current = event_artifact_prefix(42, 2)
    artifacts = [
        {
            "id": 8,
            "name": current + "job-1",
            "size_in_bytes": 100,
            "expired": False,
            "digest": "sha256:" + "b" * 64,
        },
        {
            "id": 7,
            "name": current + "job-0",
            "size_in_bytes": 100,
            "expired": False,
            "digest": None,
        },
        {
            "id": 6,
            "name": event_artifact_prefix(42, 1) + "old-attempt",
            "size_in_bytes": 100,
            "expired": False,
            "digest": None,
        },
    ]

    assert [item["id"] for item in select_event_artifacts(artifacts, 42, 2)] == [7, 8]


def test_event_archive_requires_one_safe_named_document_and_verifies_digest(tmp_path):
    path = tmp_path / "events.zip"
    _archive(path, _document())

    data, document = read_event_archive(
        path,
        repository="uibcdf/example",
        run_id=42,
        run_attempt=2,
        head_sha="abc",
    )

    assert json.loads(data)["events"][0]["platform"] == "linux-64"
    assert document["schema"] == "gh-run-receptor.events@1"
    digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    assert verify_event_archive_digest(path, digest) == digest
    with pytest.raises(BundleError, match="digest mismatch"):
        verify_event_archive_digest(path, "sha256:" + "0" * 64)

    unsafe = tmp_path / "unsafe.zip"
    _archive(unsafe, _document(), name="../events.json")
    with pytest.raises(BundleError, match="unsafe member"):
        read_event_archive(
            unsafe,
            repository="uibcdf/example",
            run_id=42,
            run_attempt=2,
            head_sha="abc",
        )


def test_hidden_conda_matrix_uses_producer_results_without_inventing_github_artifacts():
    platforms = ("linux-64", "osx-64", "osx-arm64", "win-64")
    events = []
    for platform in platforms:
        for version in ("3.11", "3.12", "3.13"):
            events.append(
                {
                    "kind": "conda.package",
                    "platform": platform,
                    "artifact": f"example-1.0-py{version.replace('.', '')}-{platform}.conda",
                    "sha256": hashlib.sha256(f"{platform}-{version}".encode()).hexdigest(),
                    "build": "success",
                    "upload": "success",
                    "python_versions": [version],
                }
            )
    document = _document(events=events)
    manifest = {
        "schema": "gh-run-receptor.bundle@1",
        "repository": "uibcdf/example",
        "hostname": "github.com",
        "run_id": 42,
        "run_attempt": 2,
        "head_sha": "abc",
        "api_version": "2022-11-28",
        "receptor_version": "test",
        "capture_policy": "metadata",
        "captured_at": "2026-09-09T00:00:00+00:00",
        "complete": True,
        "members": [
            {"path": "run.json", "kind": "github.workflow_run"},
            {"path": "workflow.json", "kind": "github.workflow"},
            {"path": "jobs.json", "kind": "github.jobs"},
            {"path": "checks.json", "kind": "github.check_runs"},
            {"path": "artifacts.json", "kind": "github.artifacts"},
            {
                "path": "producer-events-99.json",
                "kind": "gh-run-receptor.producer_events",
                "artifact_id": 99,
                "artifact_name": event_artifact_prefix(42, 2) + "conda-1",
                "artifact_digest": "sha256:" + "b" * 64,
            },
        ],
        "warnings": [],
    }
    evidence = {
        "run.json": {
            "id": 42,
            "run_attempt": 2,
            "status": "completed",
            "conclusion": "success",
            "head_sha": "abc",
            "event": "release",
            "head_branch": "1.0.0",
        },
        "workflow.json": {"id": 7, "path": ".github/workflows/conda.yaml"},
        "jobs.json": {
            "jobs": [
                {"id": index, "name": f"Python {version}", "conclusion": "success"}
                for index, version in enumerate(("3.11", "3.12", "3.13"), start=10)
            ]
        },
        "checks.json": {"check_runs": []},
        "artifacts.json": {"artifacts": []},
        "producer-events-99.json": document,
    }
    config = {
        "schema": "gh-run-receptor.config@1",
        "schema_version": 1,
        "workflows": [
            {
                "match": {"path": ".github/workflows/conda.yaml"},
                "profile": "conda",
                "settings": {"expected_platforms": list(platforms)},
            }
        ],
    }

    report = build_report(
        manifest,
        evidence,
        profile="auto",
        config_override=config,
        config_source_override={"kind": "test"},
    )
    rendered = render_llm(report)

    assert report["github"]["conclusion"] == "success"
    assert report["receptor"]["assessment"] == "PASS"
    assert report["expectations"] == {"satisfied": True, "missing_platforms": []}
    assert {item["name"]: item["status"] for item in report["matrix"]["platforms"]} == {
        platform: "success" for platform in platforms
    }
    assert report["matrix"]["producer_event_count"] == 12
    assert report["artifacts"] == []
    assert "producer_events=12" in rendered
    assert "producer_uploads=success:12" in rendered


def test_producer_upload_failure_cannot_be_hidden_by_a_successful_github_conclusion():
    event = _document()["events"][0]
    event["upload"] = "failure"
    document = _document(events=[event])
    manifest = {
        "schema": "gh-run-receptor.bundle@1",
        "repository": "uibcdf/example",
        "hostname": "github.com",
        "run_id": 42,
        "run_attempt": 2,
        "head_sha": "abc",
        "api_version": "2022-11-28",
        "receptor_version": "test",
        "capture_policy": "metadata",
        "captured_at": "2026-09-09T00:00:00+00:00",
        "complete": True,
        "members": [
            {
                "path": "producer-events-99.json",
                "kind": "gh-run-receptor.producer_events",
            }
        ],
        "warnings": [],
    }
    evidence = {
        "run.json": {
            "status": "completed",
            "conclusion": "success",
            "head_sha": "abc",
        },
        "workflow.json": {"path": ".github/workflows/conda.yaml"},
        "jobs.json": {"jobs": [{"id": 10, "name": "Python 3.11", "conclusion": "success"}]},
        "checks.json": {"check_runs": []},
        "artifacts.json": {"artifacts": []},
        "producer-events-99.json": document,
    }

    report = build_report(manifest, evidence, profile="conda")

    assert report["github"]["conclusion"] == "success"
    assert report["receptor"]["assessment"] == "FAIL"
    assert "producer_uploads=failure:1" in render_llm(report)
