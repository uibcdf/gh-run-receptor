import hashlib
import io
import json
import stat
import zipfile

import pytest

from gh_run_receptor.cli import _parser
from gh_run_receptor.errors import BundleError
from gh_run_receptor.limits import MAX_PUBLISHED_ARTIFACT_BYTES, MAX_REPORT_BYTES
from gh_run_receptor.published import consume_published_report


def _report(*, conclusion="success", assessment="PASS"):
    return {
        "schema": "gh-run-receptor.report@1",
        "subject": {
            "repository": "uibcdf/example",
            "run_id": 42,
            "run_attempt": 1,
            "head_sha": "abc123",
            "workflow": ".github/workflows/ci.yml",
            "url": "https://github.com/uibcdf/example/actions/runs/42",
        },
        "github": {"status": "completed", "conclusion": conclusion},
        "receptor": {
            "assessment": assessment,
            "profile": "generic",
            "profile_version": 1,
            "evidence_sufficient": True,
            "cause_evidence": "not_captured",
        },
        "completeness": {
            "metadata": "complete",
            "jobs": "complete",
            "checks": "complete",
            "artifact_inventory": "complete",
            "artifact_content": "not_requested",
            "logs": "not_requested",
        },
        "configuration": {
            "matched": False,
            "source": None,
            "match": None,
            "profile": None,
            "settings": {},
        },
        "expectations": {"satisfied": True, "missing_platforms": []},
        "jobs": [],
        "job_counts": {},
        "artifacts": [],
        "matrix": {},
        "causes": [],
        "unknowns": [],
        "warnings": [],
        "publisher": {
            "kind": "github_action",
            "repository": "uibcdf/gh-run-receptor",
            "ref": "0.12.0",
        },
    }


def _archive(payload, *, name="report.json", extra=None, mode=None):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        info = zipfile.ZipInfo(name)
        info.compress_type = zipfile.ZIP_DEFLATED
        if mode is not None:
            info.external_attr = mode << 16
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        archive.writestr(info, data)
        if extra is not None:
            archive.writestr("extra.json", b"{}")
    return buffer.getvalue()


class _Client:
    hostname = "github.com"

    def __init__(self, archive, *, report=None, artifact_overrides=None, source_overrides=None):
        self.archive = archive
        self.calls = []
        self.report = report or _report()
        self.artifact = {
            "id": 7,
            "name": "compact-report",
            "expired": False,
            "size_in_bytes": len(archive),
            "digest": "sha256:" + hashlib.sha256(archive).hexdigest(),
        }
        self.artifact.update(artifact_overrides or {})
        self.source = {
            "id": 42,
            "run_attempt": 1,
            "head_sha": "abc123",
            "status": "completed",
            "conclusion": self.report["github"]["conclusion"],
            "html_url": "https://github.com/uibcdf/example/actions/runs/42",
        }
        self.source.update(source_overrides or {})

    def json(self, endpoint, *, paginate=False):
        self.calls.append((endpoint, paginate))
        if endpoint.endswith("/runs/99"):
            return {"id": 99, "status": "completed", "conclusion": "success"}
        if endpoint.endswith("/runs/99/artifacts?per_page=100"):
            return {"total_count": 1, "artifacts": [self.artifact]}
        if endpoint.endswith("/runs/42"):
            return self.source
        raise AssertionError(endpoint)

    def download(self, endpoint, destination, *, max_bytes):
        self.calls.append((endpoint, max_bytes))
        assert max_bytes == MAX_PUBLISHED_ARTIFACT_BYTES
        destination.write_bytes(self.archive)


def _consume(client):
    return consume_published_report(
        client, "uibcdf/example", 99, artifact_name="compact-report"
    )


def test_published_command_has_an_explicit_exact_artifact_selector():
    args = _parser().parse_args(
        ["published", "99", "--repo", "uibcdf/example", "--artifact", "compact-report"]
    )

    assert args.command == "published"
    assert args.run.run_id == 99
    assert args.artifact == "compact-report"


def test_consumption_verifies_digest_source_facts_and_avoids_jobs_and_logs():
    report = _report()
    client = _Client(_archive(report), report=report)

    consumed = _consume(client)

    assert consumed["subject"]["run_id"] == 42
    assert consumed["consumer_verification"] == {
        "source_facts": "verified",
        "interpretation": "published_not_recomputed",
        "reporter_run_id": 99,
        "artifact_id": 7,
        "artifact_name": "compact-report",
        "artifact_digest": client.artifact["digest"],
    }
    assert "not independently recomputed" in consumed["warnings"][-1]
    endpoints = [call[0] for call in client.calls]
    assert not any("/jobs" in endpoint or "/logs" in endpoint for endpoint in endpoints)


@pytest.mark.parametrize(
    ("artifact_overrides", "message"),
    [
        ({"expired": True}, "expired"),
        ({"expired": None}, "unknown availability"),
        ({"size_in_bytes": MAX_PUBLISHED_ARTIFACT_BYTES + 1}, "compressed-byte limit"),
        ({"digest": "sha256:" + "0" * 64}, "digest mismatch"),
    ],
)
def test_artifact_inventory_and_digest_fail_closed(artifact_overrides, message):
    report = _report()
    client = _Client(_archive(report), report=report, artifact_overrides=artifact_overrides)

    with pytest.raises(BundleError, match=message):
        _consume(client)


@pytest.mark.parametrize(
    ("archive", "message"),
    [
        (_archive(_report(), name="../report.json"), "unsafe member"),
        (_archive(_report(), extra=True), "exactly one"),
        (_archive(_report(), name="report.txt"), "unsafe member"),
        (_archive(_report(), mode=stat.S_IFLNK | 0o777), "unsafe member"),
        (_archive(b'{"schema":"x","schema":"y"}'), "duplicate JSON key"),
        (_archive(b"not json"), "invalid JSON"),
    ],
)
def test_hostile_or_malformed_archives_fail_closed(archive, message):
    with pytest.raises(BundleError, match=message):
        _consume(_Client(archive))


def test_expanded_report_limit_fails_closed():
    archive = _archive(b"x" * (MAX_REPORT_BYTES + 1))

    with pytest.raises(BundleError, match="expanded-byte limit"):
        _consume(_Client(archive))


@pytest.mark.parametrize(
    ("source_overrides", "message"),
    [
        ({"id": 41}, "run ID"),
        ({"run_attempt": 2}, "attempt"),
        ({"head_sha": "different"}, "head SHA"),
        ({"status": "in_progress", "conclusion": None}, "status conflicts"),
        ({"conclusion": "failure"}, "conclusion conflicts"),
        ({"html_url": "https://example.invalid"}, "URL"),
    ],
)
def test_fresh_source_fact_mismatches_fail_closed(source_overrides, message):
    report = _report()
    client = _Client(_archive(report), report=report, source_overrides=source_overrides)

    with pytest.raises(BundleError, match=message):
        _consume(client)


def test_official_failure_cannot_be_published_as_pass():
    report = _report(conclusion="failure", assessment="PASS")
    client = _Client(_archive(report), report=report)

    with pytest.raises(BundleError, match="assessment conflicts"):
        _consume(client)


def test_cross_repository_subject_fails_closed():
    report = _report()
    report["subject"]["repository"] = "uibcdf/other"

    with pytest.raises(BundleError, match="cross-repository"):
        _consume(_Client(_archive(report), report=report))


def test_download_larger_than_inventory_limit_fails_closed(tmp_path):
    report = _report()
    client = _Client(_archive(report), report=report)

    def oversized_download(endpoint, destination, *, max_bytes):
        assert max_bytes == MAX_PUBLISHED_ARTIFACT_BYTES
        with destination.open("wb") as stream:
            stream.truncate(MAX_PUBLISHED_ARTIFACT_BYTES + 1)

    client.download = oversized_download
    with pytest.raises(BundleError, match="compressed-byte limit"):
        _consume(client)
