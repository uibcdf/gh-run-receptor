"""Validating published contracts against sanitized real-run evidence."""

from __future__ import annotations

import copy
import json
from importlib.resources import files
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from gh_run_receptor.bundle import load_bundle
from gh_run_receptor.model import normalize_evidence
from gh_run_receptor.report import build_report, exit_code, render_json, render_llm

FIXTURES = Path(__file__).parent / "fixtures"


def _schema(name: str) -> dict:
    resource = files("gh_run_receptor.schemas").joinpath(name)
    return json.loads(resource.read_text(encoding="utf-8"))


def _validator(name: str) -> Draft202012Validator:
    model = _schema("model-v1.schema.json")
    registry = Registry().with_resource(model["$id"], Resource.from_contents(model))
    return Draft202012Validator(_schema(name), registry=registry)


def _corpus():
    catalog = json.loads((FIXTURES / "corpus.json").read_text(encoding="utf-8"))
    yield from catalog["captures"]


@pytest.mark.parametrize("case", list(_corpus()), ids=lambda case: case["path"])
def test_sanitized_bundle_crosses_all_three_schema_boundaries(case):
    manifest, evidence = load_bundle(FIXTURES / case["path"])
    model = normalize_evidence(manifest, evidence)
    report = build_report(manifest, evidence, profile=case.get("profile", "auto"))

    _validator("bundle-v1.schema.json").validate(manifest)
    _validator("model-v1.schema.json").validate(model)
    _validator("report-v1.schema.json").validate(report)
    assert report["github"]["conclusion"] == case["expected_github_conclusion"]
    assert report["receptor"]["assessment"] == case["expected_assessment"]
    assert report["subject"]["run_id"] == case["run_id"]
    assert report["subject"]["run_attempt"] == case["run_attempt"]
    if "expected_exit_code" in case:
        assert exit_code(report) == case["expected_exit_code"]


@pytest.mark.parametrize("case", list(_corpus()), ids=lambda case: case["path"])
def test_replay_is_byte_deterministic_for_fixed_evidence(case):
    manifest, evidence = load_bundle(FIXTURES / case["path"])

    profile = case.get("profile", "auto")
    first = render_json(build_report(manifest, evidence, profile=profile))
    second = render_json(build_report(manifest, evidence, profile=profile))

    assert first.encode() == second.encode()


def test_text_rendering_is_stable_under_shuffled_api_collections():
    manifest, evidence = load_bundle(FIXTURES / "bundles/molsysmt_conda_partial")
    shuffled = copy.deepcopy(evidence)
    shuffled["jobs.json"]["jobs"].reverse()
    shuffled["artifacts.json"]["artifacts"].reverse()

    original = render_llm(build_report(manifest, evidence, profile="auto"))
    reordered = render_llm(build_report(manifest, shuffled, profile="auto"))

    assert reordered == original


def test_report_schema_accepts_additive_publisher_and_consumer_verification():
    manifest, evidence = load_bundle(FIXTURES / "bundles/molsysmt_conda_success")
    report = build_report(manifest, evidence, profile="auto")
    report["publisher"] = {
        "kind": "github_action",
        "repository": "uibcdf/gh-run-receptor",
        "ref": "0.12.0",
    }
    report["consumer_verification"] = {
        "source_facts": "verified",
        "interpretation": "published_not_recomputed",
        "reporter_run_id": 99,
        "artifact_id": 7,
        "artifact_name": "gh-run-receptor-report",
        "artifact_digest": "sha256:" + "a" * 64,
        "reporter_identity": "verified",
        "reporter_workflow": ".github/workflows/gh-run-receptor-report.yml",
    }

    _validator("report-v1.schema.json").validate(report)


def test_unknown_github_enum_is_preserved_with_source_reference():
    manifest, evidence = load_bundle(FIXTURES / "bundles/molsysmt_conda_success")
    evidence["jobs.json"]["jobs"][0]["conclusion"] = "future_conclusion"

    model = normalize_evidence(manifest, evidence)

    assert model["jobs"][0]["conclusion"] == "future_conclusion"
    assert model["unknowns"] == [
        {
            "kind": "github.job.conclusion",
            "value": "future_conclusion",
            "source": {"member": "jobs.json", "json_pointer": "/jobs/0/conclusion"},
        }
    ]


def test_real_rerun_fixtures_keep_attempts_and_conclusions_separate():
    first_manifest, first_evidence = load_bundle(
        FIXTURES / "bundles/argdigest_ci_rerun_attempt_1"
    )
    second_manifest, second_evidence = load_bundle(
        FIXTURES / "bundles/argdigest_ci_rerun_attempt_2"
    )
    first = build_report(first_manifest, first_evidence, profile="generic")
    second = build_report(second_manifest, second_evidence, profile="generic")

    assert first["subject"]["run_id"] == second["subject"]["run_id"] == 22638022385
    assert first["subject"]["head_sha"] == second["subject"]["head_sha"]
    assert (first["subject"]["run_attempt"], first["github"]["conclusion"]) == (
        1,
        "failure",
    )
    assert (second["subject"]["run_attempt"], second["github"]["conclusion"]) == (
        2,
        "success",
    )
    assert first["receptor"]["assessment"] == "FAIL"
    assert second["receptor"]["assessment"] == "PASS"


def test_real_cancelled_conda_fixture_accounts_for_every_platform_state():
    manifest, evidence = load_bundle(FIXTURES / "bundles/molsysmt_conda_cancelled")
    report = build_report(manifest, evidence, profile="auto")
    states = {item["name"]: item["status"] for item in report["matrix"]["platforms"]}
    rendered = render_llm(report)

    assert report["receptor"]["assessment"] == "CANCELLED"
    assert states == {
        "linux-64": "success",
        "linux-aarch64": "success",
        "osx-64": "cancelled",
        "osx-arm64": "cancelled",
        "win-64": "failed",
    }
    assert "non-success jobs (10):" in rendered
    assert "successful=2 failed=1 cancelled=2 missing=0" in rendered


def test_real_expired_log_fixture_fails_closed_as_incomplete():
    manifest, evidence = load_bundle(
        FIXTURES / "bundles/pyunitwizard_ci_incomplete_logs"
    )
    report = build_report(manifest, evidence, profile="generic")

    assert manifest["complete"] is False
    assert not any(member["path"] == "logs.zip" for member in manifest["members"])
    assert report["github"]["conclusion"] == "failure"
    assert report["receptor"]["assessment"] == "INCOMPLETE"
    assert report["completeness"]["logs"] == "unavailable"
    assert report["warnings"] == [
        "logs unavailable: GitHub CLI download failed: gh: Server Error (HTTP 410)"
    ]
    assert exit_code(report) == 4


def test_molsysviewer_noarch_fixture_uses_the_trusted_package_kind():
    manifest, evidence = load_bundle(
        FIXTURES / "bundles/molsysviewer_conda_noarch_success"
    )

    report = build_report(manifest, evidence, profile="auto")
    rendered = render_llm(report)

    assert report["configuration"]["matched"] is True
    assert report["configuration"]["settings"] == {"package_kind": "noarch"}
    assert report["matrix"]["package_kind"] == "noarch"
    assert report["matrix"]["package"]["job_counts"] == {"success": 3}
    assert report["matrix"]["package"]["artifact_evidence"] == "not_observed"
    assert "package=noarch" in rendered
    assert "platforms=0/0" not in rendered


def test_documentation_fixtures_preserve_distinct_phase_evidence():
    failure_manifest, failure_evidence = load_bundle(
        FIXTURES / "bundles/molsysviewer_docs_notebooks_failure"
    )
    success_manifest, success_evidence = load_bundle(
        FIXTURES / "bundles/molsysmt_docs_success"
    )

    failure = build_report(failure_manifest, failure_evidence, profile="auto")
    success = build_report(success_manifest, success_evidence, profile="auto")
    failure_phases = {item["name"]: item for item in failure["matrix"]["phases"]}
    success_phases = {item["name"]: item for item in success["matrix"]["phases"]}

    assert failure["github"]["conclusion"] == "failure"
    assert failure["receptor"]["assessment"] == "FAIL"
    assert failure["receptor"]["profile"] == "docs"
    assert failure["configuration"]["matched"] is True
    assert failure_phases["notebooks"]["counts"] == {"skipped": 1}
    assert failure_phases["artifact"]["counts"] == {"success": 1}
    assert failure_phases["setup"]["counts"]["failure"] == 2
    assert len(failure["jobs"][0]["steps"]) == 9
    assert success["github"]["conclusion"] == "success"
    assert success["receptor"]["assessment"] == "PASS"
    assert success["receptor"]["profile"] == "docs"
    assert success["configuration"]["matched"] is True
    assert success_phases["build_deploy"]["counts"] == {"success": 1}
    assert "build" not in success_phases


def test_release_fixtures_preserve_identity_and_delivery_evidence():
    failure_manifest, failure_evidence = load_bundle(
        FIXTURES / "bundles/molsysviewer_release_npm_failure"
    )
    success_manifest, success_evidence = load_bundle(
        FIXTURES / "bundles/molsysviewer_release_npm_success"
    )

    failure = build_report(failure_manifest, failure_evidence, profile="auto")
    success = build_report(success_manifest, success_evidence, profile="auto")
    failure_phases = {item["name"]: item for item in failure["matrix"]["phases"]}
    success_phases = {item["name"]: item for item in success["matrix"]["phases"]}

    assert failure["github"]["conclusion"] == "failure"
    assert failure["receptor"]["assessment"] == "FAIL"
    assert failure["receptor"]["profile"] == "release"
    assert failure["configuration"]["matched"] is True
    assert failure["subject"]["event"] == "push"
    assert failure["subject"]["head_ref"] == "0.20.1"
    assert failure_phases["package"]["counts"] == {"failure": 1}
    assert failure_phases["publish"]["counts"] == {"skipped": 1}
    assert success["github"]["conclusion"] == "success"
    assert success["receptor"]["assessment"] == "PASS"
    assert success["receptor"]["profile"] == "release"
    assert success["configuration"]["matched"] is True
    assert success["subject"]["event"] == "workflow_dispatch"
    assert success_phases["package"]["counts"] == {"success": 1}
    assert success_phases["publish"]["counts"] == {"success": 1}
    assert success["matrix"]["verification"]["registry"] == "step_success"
    assert success["matrix"]["identity"]["tag_verification"] == "not_observed"
