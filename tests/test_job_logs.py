"""Qualify job-only evidence independently from workflow conclusions (#68)."""

import copy
import json
from pathlib import Path

import pytest
import yaml

from gh_run_receptor import cli, job_logs, logs
from gh_run_receptor.bundle import capture_bundle, load_bundle
from gh_run_receptor.errors import AcquisitionError, BundleError
from gh_run_receptor.model import normalize_evidence
from gh_run_receptor.report import build_report, exit_code, render_human, render_json, render_llm
from gh_run_receptor.service import acquire_evidence
from gh_run_receptor_tools.sanitize_bundle import sanitize
from gh_run_receptor_tools.schema_validation import validator as _validator

RUN = {
    "id": 42,
    "run_attempt": 2,
    "head_sha": "abc",
    "workflow_id": 7,
    "status": "in_progress",
    "conclusion": None,
    "future_field": {"retained": True},
}
JOB = {
    "id": 9,
    "run_id": 42,
    "run_attempt": 2,
    "head_sha": "abc",
    "name": "Windows",
    "status": "completed",
    "conclusion": "failure",
    "steps": [],
    "future_field": "retained",
}
PLAIN_LOG = (
    b"2026-10-24T10:00:00Z Traceback (most recent call last):\r\n"
    b'2026-10-24T10:00:00Z   File "C:\\work\\reader.py", line 17, in read\r\n'
    b"2026-10-24T10:00:00Z \x1b[31mNotADirectoryError: [WinError 267] invalid directory\x1b[0m\r\n"
    b"2026-10-24T10:00:00Z ##[error]Process completed with exit code 1.\r\n"
)


class Client:
    hostname = "github.com"

    def __init__(self, *, run=None, job=None, error=None, data=PLAIN_LOG):
        self.run = copy.deepcopy(RUN if run is None else run)
        self.job = copy.deepcopy(JOB if job is None else job)
        self.error, self.data = error, data
        self.requests, self.downloads = [], []

    def repository(self, value):
        return value

    def json(self, endpoint, *, paginate=False):
        self.requests.append(endpoint)
        if endpoint.endswith("/runs/42"):
            return self.run.copy()
        if endpoint.endswith("/runs/42/attempts/1"):
            return {**self.run, "run_attempt": 1, "status": "completed", "conclusion": "failure"}
        if endpoint.endswith("/workflows/7"):
            return {"path": ".github/workflows/ci.yml"}
        if "/jobs?" in endpoint:
            return {"jobs": [self.job, {"id": 10, "name": "Linux", "status": "in_progress"}]}
        if "/artifacts?" in endpoint:
            return {"artifacts": []}
        if endpoint == "/repos/example/project":
            return {"default_branch": "main"}
        raise AssertionError(endpoint)

    def optional_json(self, endpoint):
        return None

    def download(self, endpoint, path, *, max_bytes):
        self.downloads.append((endpoint, max_bytes))
        if self.error:
            path.write_bytes(b"incomplete raw evidence")
            raise self.error
        path.write_bytes(self.data)


def capture(tmp_path, client=None, *, policy="adaptive", attempt=2):
    path = tmp_path / "bundle"
    client = client or Client()
    capture_bundle(
        client, "example/project", 42, attempt=attempt, policy=policy, destination=path, job_id=9
    )
    manifest, evidence = load_bundle(path)
    return client, path, manifest, evidence


@pytest.mark.parametrize("profile", ["generic", "ci", "conda", "docs", "release"])
@pytest.mark.parametrize(
    ("status", "conclusion", "expected"),
    [
        ("in_progress", None, 3),
        ("queued", None, 3),
        ("completed", "failure", 1),
        ("completed", "success", 0),
        ("completed", "cancelled", 2),
        ("completed", "timed_out", 2),
        ("completed", "future-conclusion", 2),
    ],
)
def test_job_only_diagnosis_preserves_native_workflow_truth(
    tmp_path, profile, status, conclusion, expected
):
    client, path, manifest, evidence = capture(
        tmp_path, Client(run={**RUN, "status": status, "conclusion": conclusion})
    )
    report = build_report(manifest, evidence, profile=profile, bundle_directory=path)
    assert report["github"] == {"status": status, "conclusion": conclusion}
    assert exit_code(report) == expected
    assert report["log_scope"] == {"kind": "job", "job_id": 9}
    assert report["completeness"]["logs"] == "partial"
    assert report["receptor"]["cause_evidence"] == "partial"
    assert (
        report["causes"][0]["message"]
        == "NotADirectoryError: [WinError 267] invalid directory | at reader.py:17"
    )
    assert report["causes"][0]["occurrences"][0]["job_id"] == 9
    assert report["causes"][0]["occurrences"][0]["member"] == "job-9.log"
    assert evidence["run.json"]["future_field"] == {"retained": True}
    assert evidence["jobs.json"]["jobs"][0]["future_field"] == "retained"
    assert len(report["jobs"]) == 2
    assert client.downloads == [
        ("/repos/example/project/actions/jobs/9/logs", logs.MAX_MEMBER_BYTES)
    ]
    assert (path / "job-9.log").read_bytes() == PLAIN_LOG
    assert not (path / "logs.zip").exists()
    for renderer in [render_llm, render_human, render_json]:
        text = renderer(report)
        assert text == renderer(
            build_report(manifest, evidence, profile=profile, bundle_directory=path)
        )
        assert "job-only" in text or '"log_scope"' in text
        assert "\x1b" not in text and len(text.encode()) < 20_000
    _validator("bundle-v1.schema.json").validate(manifest)
    _validator("model-v1.schema.json").validate(normalize_evidence(manifest, evidence))
    _validator("report-v1.schema.json").validate(report)


@pytest.mark.parametrize("conclusion", ["success", "cancelled", "neutral", "future-conclusion"])
def test_completed_nonfailure_job_is_not_diagnosed_from_failed_looking_text(tmp_path, conclusion):
    _, path, manifest, evidence = capture(tmp_path, Client(job={**JOB, "conclusion": conclusion}))
    report = build_report(manifest, evidence, bundle_directory=path)
    assert report["causes"] == [] and exit_code(report) == 3


@pytest.mark.parametrize("policy", ["full", "adaptive", "metadata"])
def test_explicit_job_scope_keeps_capture_policies_and_never_downloads_attempt_archive(
    tmp_path, policy
):
    client, _, manifest, _ = capture(tmp_path, policy=policy)
    assert manifest["capture_policy"] == policy
    assert len(client.downloads) == (policy != "metadata")
    assert all("/attempts/2/logs" not in endpoint for endpoint, _ in client.downloads)


def test_historical_job_membership_is_checked_against_selected_attempt(tmp_path):
    client, _, manifest, evidence = capture(
        tmp_path, Client(job={**JOB, "run_attempt": 1}), attempt=1
    )
    assert manifest["run_attempt"] == evidence["run.json"]["run_attempt"] == 1
    assert "/repos/example/project/actions/runs/42/attempts/1/jobs?per_page=100" in client.requests
    assert client.downloads[0][0].endswith("/jobs/9/logs")


@pytest.mark.parametrize(
    "change",
    [
        {"id": 8},
        {"run_id": 99},
        {"run_id": True},
        {"run_attempt": 1},
        {"run_attempt": True},
        {"head_sha": "other"},
        {"status": "in_progress"},
    ],
)
def test_identity_or_active_job_refusal_precedes_download_and_cleans_staging(tmp_path, change):
    receipt = tmp_path / "caller.json"
    receipt.write_text("retained")
    client = Client(job={**JOB, **change})
    with pytest.raises(BundleError):
        capture(tmp_path, client)
    assert client.downloads == []
    assert list(tmp_path.iterdir()) == [receipt]


@pytest.mark.parametrize("job_id", [0, -1, True, 10**20, "9", None])
def test_selected_job_requires_bounded_integer_identity(job_id):
    with pytest.raises(BundleError):
        job_logs.completed_job({"jobs": [JOB]}, job_id, run_id=42, attempt=2, head_sha="abc")


def test_missing_duplicate_and_malformed_job_collections_fail_closed():
    for collection in [{"jobs": []}, {"jobs": [JOB, JOB]}, {"jobs": None}, []]:
        with pytest.raises(BundleError):
            job_logs.completed_job(collection, 9, run_id=42, attempt=2, head_sha="abc")


@pytest.mark.parametrize(
    ("status", "category", "state"),
    [
        (403, "forbidden", "not_permitted"),
        (404, "not_found_or_inaccessible", "unavailable"),
        (410, "http_error", "expired"),
        (None, "acquisition_failed", "unavailable"),
    ],
)
def test_unavailable_logs_preserve_structured_error_and_incomplete_exit(
    tmp_path, status, category, state
):
    error = AcquisitionError("safe transport failure", category=category, http_status=status)
    client, path, manifest, evidence = capture(tmp_path, Client(error=error))
    report = build_report(manifest, evidence, bundle_directory=path)
    assert report["job_log_error"] == {"category": category, "http_status": status}
    assert report["completeness"]["logs"] == state
    assert report["github"] == {"status": "in_progress", "conclusion": None}
    assert report["causes"] == [] and exit_code(report) == 4
    assert len(client.downloads) == 1 and not (path / "job-9.log").exists()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda m: m.pop("log_scope"),
        lambda m: m["log_scope"].update(job_id=10),
        lambda m: m["log_scope"].update(kind="attempt"),
        lambda m: m["members"][-1].update(run_attempt=1),
        lambda m: m["members"][-1].update(job_id=10),
        lambda m: m.update(capture_policy="metadata"),
        lambda m: m.update(job_log_error={"category": "forbidden", "http_status": 403}),
    ],
)
def test_forged_replay_scope_or_member_identity_is_rejected(tmp_path, mutate):
    _, path, manifest, _ = capture(tmp_path)
    mutate(manifest)
    (path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(BundleError):
        load_bundle(path)


def test_truncated_and_malformed_text_remain_unknown_and_oversized_logs_are_refused(
    tmp_path, monkeypatch
):
    _, path, manifest, evidence = capture(
        tmp_path, Client(data=b"Traceback (most recent call last):\n\xff\x00\n")
    )
    report = build_report(manifest, evidence, bundle_directory=path)
    assert report["causes"] == [] and report["receptor"]["cause_evidence"] == "partial"
    monkeypatch.setattr(job_logs, "MAX_MEMBER_BYTES", 4)
    with pytest.raises(BundleError, match="byte limit"):
        capture(tmp_path / "oversized", Client(data=b"12345"))
    assert list((tmp_path / "oversized").iterdir()) == []


def test_plain_stream_uses_the_same_huge_line_and_credential_guards(tmp_path):
    token = "ghp_" + "a" * 30
    data = b"x" * (logs.MAX_LINE_BYTES * 2) + b"\n" + f"##[error]TOKEN={token}\n".encode()
    _, path, manifest, evidence = capture(tmp_path, Client(data=data))
    report = build_report(manifest, evidence, bundle_directory=path)
    assert token not in render_json(report)
    assert "[REDACTED]" in render_json(report)
    assert len(render_llm(report).encode()) < 2000


def test_job_cache_is_separate_and_explicit_output_refuses_other_scope(tmp_path):
    client = Client()
    captured = acquire_evidence(
        client, "example/project", 42, attempt=2, policy="adaptive", cache_root=tmp_path, job_id=9
    )
    assert captured.path.parts[-3:] == ("2", "job-9", "adaptive")
    with pytest.raises(BundleError, match="log scope"):
        acquire_evidence(
            client,
            "example/project",
            42,
            attempt=2,
            policy="adaptive",
            cache_root=tmp_path,
            output=captured.path,
        )


def test_cli_inspect_and_offline_replay_preserve_active_workflow_exit(
    tmp_path, monkeypatch, capsys
):
    client = Client()
    monkeypatch.setattr(cli, "GitHubClient", lambda host: client)
    path = tmp_path / "cli"
    assert (
        cli.main(
            [
                "inspect",
                "42",
                "--repo",
                "example/project",
                "--job",
                "9",
                "--output",
                str(path),
                "--receptor",
                "llm",
            ]
        )
        == 3
    )
    live = capsys.readouterr().out
    assert "PENDING" in live and "job-only job=9" in live and "NotADirectoryError" in live
    monkeypatch.setattr(
        cli, "GitHubClient", lambda host: pytest.fail("offline replay used network")
    )
    assert cli.main(["replay", str(path), "--receptor", "llm"]) == 3
    assert capsys.readouterr().out == live


def test_sanitizer_discards_raw_job_logs_but_keeps_reviewed_scope_and_identity(tmp_path):
    _, source, _, _ = capture(tmp_path)
    target = tmp_path / "sanitized"
    sanitize(source, target)
    manifest, evidence = load_bundle(target)
    assert manifest["capture_policy"] == "metadata"
    assert manifest["log_scope"] == {"kind": "job", "job_id": 9}
    assert evidence["jobs.json"]["jobs"][0]["run_id"] == 42
    assert not list(target.glob("*.log"))
    assert (source / "job-9.log").read_bytes() == PLAIN_LOG


@pytest.mark.parametrize(
    ("suffix", "renderer"),
    [
        ("human", render_human),
        ("llm", render_llm),
        ("json", render_json),
    ],
)
def test_active_failure_golden_reports_keep_native_truth_and_subset_label(
    tmp_path, suffix, renderer
):
    _, path, manifest, evidence = capture(tmp_path)
    report = build_report(manifest, evidence, profile="ci", bundle_directory=path)
    assert report["github"] == {"status": "in_progress", "conclusion": None}
    assert exit_code(report) == 3
    golden = Path(__file__).parent / "fixtures/job_logs" / f"active_failure.{suffix}"
    assert renderer(report) == golden.read_text(encoding="utf-8")


@pytest.mark.parametrize("job_id", ["../../outside", True, -1, 10**20])
def test_invalid_job_selection_cannot_reach_transport_or_create_cache_paths(tmp_path, job_id):
    client = Client()
    with pytest.raises(BundleError):
        acquire_evidence(
            client,
            "example/project",
            42,
            attempt=2,
            policy="adaptive",
            cache_root=tmp_path,
            job_id=job_id,
        )
    assert client.requests == [] and client.downloads == [] and not list(tmp_path.iterdir())


def test_intentional_native_failure_probe_is_valid_yaml_and_manual_only():
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((root / ".github/workflows/validate-job-logs.yml").read_text())
    assert workflow.get("on", workflow.get(True)) == {"workflow_dispatch": None}
    assert workflow["permissions"] == {"contents": "read", "actions": "read"}
    assert workflow["jobs"]["observe"]["needs"] == ["completed-failure", "completed-success"]
    assert workflow["jobs"]["observe"]["if"] == "always()"
    assert all(job["timeout-minutes"] <= 5 for job in workflow["jobs"].values())
