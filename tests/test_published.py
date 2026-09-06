import hashlib
import io
import json
import stat
import zipfile

import pytest

from gh_run_receptor.cli import _parser
from gh_run_receptor.errors import BundleError
from gh_run_receptor.limits import MAX_PUBLISHED_ARTIFACT_BYTES, MAX_REPORT_BYTES
from gh_run_receptor.published import (
    consume_published_report,
    consume_published_source,
    published_artifact_name,
)
from gh_run_receptor.report import render_llm


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


def test_published_source_command_has_explicit_discovery_contract():
    args = _parser().parse_args(
        [
            "published-source",
            "42",
            "--repo",
            "uibcdf/example",
            "--artifact-prefix",
            "compact",
            "--reporter-workflow",
            ".github/workflows/reporter.yaml",
        ]
    )

    assert args.command == "published-source"
    assert args.run.run_id == 42
    assert args.artifact_prefix == "compact"
    assert args.reporter_workflow == ".github/workflows/reporter.yaml"


def test_artifact_identity_includes_run_and_attempt():
    assert published_artifact_name("compact", 42, 3) == "compact-42-3"


class _DiscoveryClient(_Client):
    def __init__(
        self,
        archive,
        *,
        report=None,
        inventory_overrides=None,
        reporter_overrides=None,
        workflow_overrides=None,
    ):
        super().__init__(archive, report=report)
        self.artifact["name"] = "compact-42-1"
        self.artifact["workflow_run"] = {"id": 99, "head_sha": "reporter-sha"}
        self.inventory = {
            "total_count": 1,
            "artifacts": [self.artifact],
        }
        self.inventory.update(inventory_overrides or {})
        self.reporter = {
            "id": 99,
            "status": "completed",
            "conclusion": "success",
            "event": "workflow_run",
            "workflow_id": 17,
            "head_sha": "reporter-sha",
            "path": ".github/workflows/reporter.yml@main",
        }
        self.reporter.update(reporter_overrides or {})
        self.workflow = {
            "id": 17,
            "path": ".github/workflows/reporter.yml",
        }
        self.workflow.update(workflow_overrides or {})

    def json(self, endpoint, *, paginate=False):
        self.calls.append((endpoint, paginate))
        if endpoint.endswith("/runs/42"):
            return self.source
        if endpoint.endswith("/actions/artifacts?name=compact-42-1&per_page=100"):
            return self.inventory
        if endpoint.endswith("/runs/99"):
            return self.reporter
        if endpoint.endswith("/actions/workflows/17"):
            return self.workflow
        raise AssertionError(endpoint)


def _consume_source(client):
    return consume_published_source(
        client,
        "uibcdf/example",
        42,
        artifact_prefix="compact",
        reporter_workflow=".github/workflows/reporter.yml",
    )


def test_source_discovery_verifies_producer_and_reuses_source_facts():
    report = _report()
    client = _DiscoveryClient(_archive(report), report=report)

    consumed = _consume_source(client)

    assert consumed["consumer_verification"]["reporter_run_id"] == 99
    assert consumed["consumer_verification"]["reporter_identity"] == "verified"
    assert consumed["consumer_verification"]["reporter_workflow"] == (
        ".github/workflows/reporter.yml"
    )
    assert "publishing workflow identity verified" in consumed["warnings"][-1]
    assert "reporter_identity=verified" in render_llm(consumed)
    endpoints = [call[0] for call in client.calls]
    assert endpoints.count("/repos/uibcdf/example/actions/runs/42") == 1
    assert not any("/jobs" in endpoint or "/logs" in endpoint for endpoint in endpoints)


@pytest.mark.parametrize(
    ("inventory_overrides", "reporter_overrides", "message"),
    [
        ({"total_count": 0, "artifacts": []}, {}, "exactly one"),
        ({"total_count": 2}, {}, "exactly one"),
        ({}, {"event": "push"}, "workflow_run reporter"),
        ({}, {"status": "in_progress"}, "workflow_run reporter"),
        ({}, {"path": ".github/workflows/other.yml@main"}, "path conflicts"),
    ],
)
def test_source_discovery_fails_closed(
    inventory_overrides, reporter_overrides, message
):
    client = _DiscoveryClient(
        _archive(_report()),
        inventory_overrides=inventory_overrides,
        reporter_overrides=reporter_overrides,
    )

    with pytest.raises(BundleError, match=message):
        _consume_source(client)


def test_source_discovery_rejects_an_untrusted_workflow_identity():
    client = _DiscoveryClient(
        _archive(_report()),
        workflow_overrides={"path": ".github/workflows/other.yml"},
    )

    with pytest.raises(BundleError, match="expected reporter workflow"):
        _consume_source(client)


def test_source_discovery_rejects_conflicting_artifact_producer_identity():
    client = _DiscoveryClient(_archive(_report()))
    client.artifact["workflow_run"]["head_sha"] = "other-sha"

    with pytest.raises(BundleError, match="publishing identity conflicts"):
        _consume_source(client)


def test_source_discovery_requires_a_terminal_source_before_artifact_lookup():
    client = _DiscoveryClient(_archive(_report()))
    client.source.update({"status": "in_progress", "conclusion": None})

    with pytest.raises(BundleError, match="source run is not terminal"):
        _consume_source(client)
    assert [call[0] for call in client.calls] == [
        "/repos/uibcdf/example/actions/runs/42"
    ]


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


def test_compact_success_exposes_verified_facts_and_published_interpretation():
    report = _report()
    consumed = _consume(_Client(_archive(report), report=report))

    compact = render_llm(consumed)

    assert "source_facts=verified" in compact
    assert "interpretation=published_not_recomputed" in compact


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
