"""Testing bounded aggregation without synthetic GitHub source truth."""

from __future__ import annotations

import copy
import json
from importlib.resources import files
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from gh_run_receptor.aggregation import (
    build_aggregate,
    exit_code,
    render_human,
    render_json,
    render_llm,
)
from gh_run_receptor.bundle import load_bundle
from gh_run_receptor.cli import main
from gh_run_receptor.errors import BundleError
from gh_run_receptor.report import build_report

FIXTURES = Path(__file__).parent / "fixtures" / "bundles"
WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/validate-aggregation.yml"


def _bundle(name: str) -> tuple[dict, dict, Path]:
    path = FIXTURES / name
    manifest, evidence = load_bundle(path)
    return manifest, evidence, path


def _report(name: str, profile: str = "auto") -> dict:
    manifest, evidence, path = _bundle(name)
    return build_report(manifest, evidence, profile=profile, bundle_directory=path)


def test_aggregate_preserves_each_source_and_validates_strict_contract():
    aggregate = build_aggregate(
        [
            _report("molsysmt_conda_success", "conda"),
            _report("molsysmt_docs_success", "docs"),
            _report("argdigest_ci_rerun_attempt_2", "ci"),
        ]
    )
    schema = json.loads(
        files("gh_run_receptor.schemas")
        .joinpath("aggregate-v1.schema.json")
        .read_text(encoding="utf-8")
    )

    Draft202012Validator(schema).validate(aggregate)
    assert aggregate["schema"] == "gh-run-receptor.aggregate@1"
    assert aggregate["assessment"] == "PASS"
    assert aggregate["evidence_sufficient"] is True
    assert aggregate["source_count"] == 3
    assert aggregate["summary"]["profile_counts"] == {"ci": 1, "conda": 1, "docs": 1}
    assert aggregate["totals"]["jobs"] == sum(
        source["jobs"]["total"] for source in aggregate["sources"]
    )
    assert [source["repository"] for source in aggregate["sources"]] == sorted(
        source["repository"] for source in aggregate["sources"]
    )
    assert render_json(aggregate).encode() == render_json(aggregate).encode()

    conforming_emptiness = copy.deepcopy(aggregate)
    conforming_emptiness["sources"] = []
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(conforming_emptiness)

    hidden_failure = copy.deepcopy(aggregate)
    hidden_failure["sources"][0]["exit_code"] = 1
    hidden_failure["sources"][0]["assessment"] = "FAIL"
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(hidden_failure)


@pytest.mark.parametrize(
    ("reports", "assessment", "status"),
    [
        (
            ["molsysmt_conda_success", "argdigest_ci_rerun_attempt_1"],
            "FAIL",
            1,
        ),
        (["molsysmt_conda_success", "molsysmt_conda_cancelled"], "NON_SUCCESS", 2),
        (["molsysmt_conda_success", "pyunitwizard_ci_incomplete_logs"], "INCOMPLETE", 4),
    ],
)
def test_aggregate_exit_truth_table(reports, assessment, status):
    aggregate = build_aggregate([_report(name) for name in reports])

    assert aggregate["assessment"] == assessment
    assert exit_code(aggregate) == status


def test_known_failure_is_not_hidden_by_an_incomplete_source():
    aggregate = build_aggregate(
        [
            _report("argdigest_ci_rerun_attempt_1"),
            _report("pyunitwizard_ci_incomplete_logs"),
        ]
    )

    assert aggregate["assessment"] == "FAIL"
    assert aggregate["evidence_sufficient"] is False
    assert exit_code(aggregate) == 1
    assert len(aggregate["warnings"]) == 1


def test_pending_source_remains_distinct_from_incomplete_evidence():
    success = _report("molsysmt_conda_success")
    pending = copy.deepcopy(_report("argdigest_ci_rerun_attempt_2"))
    pending["subject"]["run_id"] += 10
    pending["github"].update(status="in_progress", conclusion=None)
    pending["receptor"].update(assessment="PENDING", evidence_sufficient=True)

    aggregate = build_aggregate([success, pending])

    assert aggregate["assessment"] == "PENDING"
    assert aggregate["evidence_sufficient"] is True
    assert exit_code(aggregate) == 3


def test_duplicate_and_unbounded_sources_are_rejected():
    report = _report("molsysmt_conda_success")

    with pytest.raises(BundleError, match="between 2 and 50"):
        build_aggregate([report])
    with pytest.raises(BundleError, match="must be unique"):
        build_aggregate([report, copy.deepcopy(report)])
    oversized = []
    for index in range(51):
        item = copy.deepcopy(report)
        item["subject"]["run_id"] += index
        oversized.append(item)
    with pytest.raises(BundleError, match="between 2 and 50"):
        build_aggregate(oversized)


def test_llm_rendering_is_bounded_and_terminal_safe():
    source = _report("molsysmt_conda_success")
    reports = []
    for index in range(25):
        report = copy.deepcopy(source)
        report["subject"]["run_id"] += index
        report["subject"]["workflow"] = f"workflow-{index}\nforged\u202e"
        reports.append(report)

    rendered = render_llm(build_aggregate(reports))

    assert "... 5 more sources in JSON aggregate" in rendered
    assert len(rendered.splitlines()) == 22
    assert "\nforged" not in rendered
    assert "\u202e" not in rendered
    assert "\\u202e" in rendered
    assert len(rendered.encode()) < 16_000

    human = render_human(build_aggregate(reports[:2]))
    assert human.startswith("Workflow aggregate: PASS\n")
    assert "Source runs\n" in human


def test_cli_aggregates_local_bundles_offline(capsys):
    result = main(
        [
            "aggregate",
            str(FIXTURES / "molsysmt_conda_success"),
            str(FIXTURES / "molsysmt_docs_success"),
            "--format",
            "json",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["schema"] == "gh-run-receptor.aggregate@1"
    assert output["source_count"] == 2


def test_cli_rejects_mixed_sources_and_ambiguous_numeric_ids(capsys):
    local = str(FIXTURES / "molsysmt_conda_success")

    assert main(["aggregate", local, "123"]) == 5
    assert "cannot mix" in capsys.readouterr().err
    assert main(["aggregate", "123", "456"]) == 5
    assert "require --repo" in capsys.readouterr().err
    assert (
        main(
            [
                "aggregate",
                "https://github.com/uibcdf/example/actions/runs/123",
                "https://github.example/uibcdf/example/actions/runs/456",
            ]
        )
        == 5
    )
    assert "same GitHub hostname" in capsys.readouterr().err


def test_remote_aggregate_uses_each_url_repository(monkeypatch, capsys):
    first = _bundle("argdigest_ci_rerun_attempt_2")
    second = _bundle("molsysmt_docs_success")
    captures = {
        first[0]["run_id"]: SimpleNamespace(manifest=first[0], evidence=first[1], path=first[2]),
        second[0]["run_id"]: SimpleNamespace(
            manifest=second[0], evidence=second[1], path=second[2]
        ),
    }
    repositories = []

    class FakeClient:
        def __init__(self, hostname):
            assert hostname == "github.com"

        def repository(self, repository):
            repositories.append(repository)
            return repository

    def fake_acquire(client, repository, run_id, **kwargs):
        assert kwargs["attempt"] is None
        assert kwargs["policy"] == "metadata"
        return captures[run_id]

    monkeypatch.setattr("gh_run_receptor.cli.GitHubClient", FakeClient)
    monkeypatch.setattr("gh_run_receptor.cli.acquire_evidence", fake_acquire)
    result = main(
        [
            "aggregate",
            f"https://github.com/uibcdf/argdigest/actions/runs/{first[0]['run_id']}",
            f"https://github.com/uibcdf/molsysmt/actions/runs/{second[0]['run_id']}",
            "--receptor",
            "llm",
        ]
    )

    assert result == 0
    assert repositories == ["uibcdf/argdigest", "uibcdf/molsysmt"]
    assert capsys.readouterr().out.startswith("PASS aggregate sources=2")


def test_hosted_aggregate_gate_is_manual_read_only_bounded_and_pinned():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert source.count("workflow_dispatch:") == 1
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert "permissions:\n  actions: read\n  contents: read" in source
    assert "timeout-minutes: 5" in source
    assert "persist-credentials: false" in source
    assert "--capture metadata" in source
    assert "35196968944" in source
    assert "35194479266" in source
    assert "34890243748" in source
    assert 'test "$status" -eq 1' in source
    assert "gh-run-receptor.aggregate@1" in source
    assert "len(text.encode()) < 2000" in source
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7" in source
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7" in source
