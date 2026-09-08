"""Testing explicit, versioned comparison regression policies."""

from __future__ import annotations

import copy
import json
from importlib.resources import files
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from gh_run_receptor.bundle import load_bundle
from gh_run_receptor.cli import main
from gh_run_receptor.comparison import compare_reports, exit_code, render_llm
from gh_run_receptor.comparison_policy import load_policy, validate_policy
from gh_run_receptor.errors import PolicyError
from gh_run_receptor.report import build_report

FIXTURES = Path(__file__).parent / "fixtures" / "bundles"
POLICIES = Path(__file__).parent / "fixtures" / "policies"


def _report(name: str, profile: str = "generic") -> dict:
    manifest, evidence = load_bundle(FIXTURES / name)
    return build_report(manifest, evidence, profile=profile)


def _policy(**rules) -> dict:
    return {"schema": "gh-run-receptor.comparison-policy@1", "rules": rules}


def test_policy_schema_and_runtime_reject_conforming_emptiness():
    schema = json.loads(
        files("gh_run_receptor.schemas")
        .joinpath("comparison-policy-v1.schema.json")
        .read_text(encoding="utf-8")
    )
    policy = _policy(candidate_conclusion="success")

    Draft202012Validator(schema).validate(policy)
    assert validate_policy(policy) == policy
    with pytest.raises(PolicyError, match="at least one rule"):
        validate_policy(_policy())


@pytest.mark.parametrize("name", ["argdigest-rerun-pass.json", "argdigest-rerun-fail.json"])
def test_committed_policy_examples_validate_against_runtime_and_schema(name):
    policy = load_policy(POLICIES / name)
    schema = json.loads(
        files("gh_run_receptor.schemas")
        .joinpath("comparison-policy-v1.schema.json")
        .read_text(encoding="utf-8")
    )

    Draft202012Validator(schema).validate(policy)


def test_policy_loader_rejects_duplicates_nonfinite_unknowns_and_symlinks(tmp_path):
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(
        '{"schema":"gh-run-receptor.comparison-policy@1",'
        '"rules":{"same_workflow":true,"same_workflow":true}}',
        encoding="utf-8",
    )
    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text(
        '{"schema":"gh-run-receptor.comparison-policy@1",'
        '"rules":{"max_job_duration_increase_percent":NaN}}',
        encoding="utf-8",
    )
    target = tmp_path / "target.json"
    target.write_text(json.dumps(_policy(same_workflow=True)), encoding="utf-8")
    link = tmp_path / "link.json"
    link.symlink_to(target)

    with pytest.raises(PolicyError, match="duplicate policy key"):
        load_policy(duplicate)
    with pytest.raises(PolicyError, match="non-finite"):
        load_policy(nonfinite)
    with pytest.raises(PolicyError, match="non-symlink"):
        load_policy(link)
    with pytest.raises(PolicyError, match="unsupported.*future_rule"):
        validate_policy(_policy(future_rule=True))


def test_real_rerun_passes_explicit_identity_outcome_and_duration_policy():
    comparison = compare_reports(
        _report("argdigest_ci_rerun_attempt_1"),
        _report("argdigest_ci_rerun_attempt_2"),
        policy=_policy(
            same_repository=True,
            same_workflow=True,
            same_head_sha=True,
            candidate_conclusion="success",
            max_job_duration_increase_seconds=39,
            max_job_duration_increase_percent=100,
        ),
    )

    assert comparison["assessment"] == "CHANGED"
    assert comparison["policy"] == {
        "evaluated": True,
        "assessment": "PASS",
        "violations": [],
        "unknowns": [],
    }
    assert "policy=PASS violations=none unknowns=none" in render_llm(comparison)
    assert exit_code(comparison) == 0


def test_duration_violation_is_distinct_from_descriptive_change():
    comparison = compare_reports(
        _report("argdigest_ci_rerun_attempt_1"),
        _report("argdigest_ci_rerun_attempt_2"),
        policy=_policy(max_job_duration_increase_seconds=30),
    )

    assert comparison["assessment"] == "CHANGED"
    assert comparison["policy"]["assessment"] == "FAIL"
    assert comparison["policy"]["violations"] == [
        {
            "rule": "max_job_duration_increase_seconds",
            "expected": 30,
            "observed": 39,
        }
    ]
    assert exit_code(comparison) == 1


def test_percentage_and_candidate_conclusion_rules_violate_independently():
    comparison = compare_reports(
        _report("argdigest_ci_rerun_attempt_1"),
        _report("argdigest_ci_rerun_attempt_2"),
        policy=_policy(
            candidate_conclusion="failure",
            max_job_duration_increase_percent=90,
        ),
    )

    assert comparison["policy"]["assessment"] == "FAIL"
    assert [item["rule"] for item in comparison["policy"]["violations"]] == [
        "candidate_conclusion",
        "max_job_duration_increase_percent",
    ]
    assert comparison["policy"]["violations"][1]["observed"] == pytest.approx(97.5)


def test_missing_required_metric_makes_policy_incomplete_not_pass_or_fail():
    left = _report("argdigest_ci_rerun_attempt_1")
    right = _report("argdigest_ci_rerun_attempt_2")
    left["jobs"][0]["duration_seconds"] = None

    comparison = compare_reports(
        left,
        right,
        policy=_policy(max_job_duration_increase_seconds=30),
    )

    assert comparison["evidence_sufficient"] is True
    assert comparison["policy"]["assessment"] == "INCOMPLETE"
    assert comparison["policy"]["unknowns"][0]["observed"] is None
    assert exit_code(comparison) == 4


def test_zero_duration_baseline_cannot_invent_a_percentage():
    left = _report("argdigest_ci_rerun_attempt_1")
    right = copy.deepcopy(left)
    left["jobs"][0]["duration_seconds"] = 0
    right["jobs"][0]["duration_seconds"] = 1

    comparison = compare_reports(
        left,
        right,
        policy=_policy(max_job_duration_increase_percent=10),
    )

    assert comparison["policy"]["assessment"] == "INCOMPLETE"
    assert comparison["policy"]["unknowns"] == [
        {
            "rule": "max_job_duration_increase_percent",
            "expected": 10,
            "observed": None,
        }
    ]


def test_identity_policy_distinguishes_difference_from_missing_identity():
    left = _report("argdigest_ci_rerun_attempt_1")
    different = copy.deepcopy(left)
    different["subject"]["head_sha"] = "f" * 40
    missing = copy.deepcopy(left)
    missing["subject"]["head_sha"] = None

    violation = compare_reports(left, different, policy=_policy(same_head_sha=True))
    unknown = compare_reports(left, missing, policy=_policy(same_head_sha=True))

    assert violation["policy"]["assessment"] == "FAIL"
    assert violation["policy"]["violations"][0]["observed"] == [
        left["subject"]["head_sha"],
        "f" * 40,
    ]
    assert unknown["policy"]["assessment"] == "INCOMPLETE"
    assert unknown["policy"]["unknowns"][0]["observed"] is None


def test_repository_and_workflow_identity_rules_report_exact_sources():
    left = _report("argdigest_ci_rerun_attempt_1")
    right = copy.deepcopy(left)
    right["subject"]["repository"] = "example/project"
    right["subject"]["workflow"] = ".github/workflows/other.yml"

    comparison = compare_reports(
        left,
        right,
        policy=_policy(same_repository=True, same_workflow=True),
    )

    assert comparison["policy"]["assessment"] == "FAIL"
    assert comparison["policy"]["violations"] == [
        {
            "rule": "same_repository",
            "expected": True,
            "observed": ["uibcdf/argdigest", "example/project"],
        },
        {
            "rule": "same_workflow",
            "expected": True,
            "observed": [".github/workflows/CI.yaml", ".github/workflows/other.yml"],
        },
    ]


def test_artifact_size_rule_distinguishes_violation_from_unknown_size():
    left = _report("argdigest_ci_rerun_attempt_1")
    right = copy.deepcopy(left)
    artifact = {
        "id": 7,
        "name": "package",
        "size_bytes": 20,
        "expired": False,
        "digest": None,
        "source": {"member": "artifacts.json", "json_pointer": "/artifacts/0"},
    }
    left_artifact = copy.deepcopy(artifact)
    left_artifact["size_bytes"] = 10
    left["artifacts"] = [left_artifact]
    right["artifacts"] = [artifact]

    violation = compare_reports(
        left,
        right,
        policy=_policy(max_artifact_size_increase_bytes=9),
    )
    right["artifacts"][0]["size_bytes"] = None
    unknown = compare_reports(
        left,
        right,
        policy=_policy(max_artifact_size_increase_bytes=9),
    )

    assert violation["policy"]["violations"][0]["observed"] == 10
    assert unknown["policy"]["assessment"] == "INCOMPLETE"
    assert unknown["policy"]["unknowns"][0]["observed"] is None


def test_inventory_and_matrix_rules_report_exact_removed_units():
    left = _report("molsysmt_conda_partial", profile="conda")
    right = copy.deepcopy(left)
    right["jobs"] = right["jobs"][1:]
    right["artifacts"] = right["artifacts"][1:]
    removed_platform = right["matrix"]["platforms"].pop()["name"]

    comparison = compare_reports(
        left,
        right,
        policy=_policy(
            forbid_job_removals=True,
            forbid_artifact_removals=True,
            forbid_matrix_removals=True,
        ),
    )

    assert comparison["policy"]["assessment"] == "FAIL"
    assert {item["rule"] for item in comparison["policy"]["violations"]} == {
        "forbid_job_removals",
        "forbid_artifact_removals",
        "forbid_matrix_removals",
    }
    assert comparison["matrix"]["removed"] == [removed_platform]


def test_matrix_change_rule_requires_comparable_evidence():
    left = _report("molsysmt_conda_partial", profile="conda")
    right = copy.deepcopy(left)
    right["matrix"]["platforms"][0]["status"] = "future-state"

    violation = compare_reports(
        left,
        right,
        policy=_policy(forbid_matrix_changes=True),
    )
    unknown = compare_reports(
        _report("argdigest_ci_rerun_attempt_1"),
        _report("argdigest_ci_rerun_attempt_2"),
        policy=_policy(forbid_matrix_changes=True, forbid_matrix_removals=True),
    )

    assert violation["policy"]["assessment"] == "FAIL"
    assert violation["policy"]["violations"][0]["rule"] == "forbid_matrix_changes"
    assert unknown["policy"]["assessment"] == "INCOMPLETE"
    assert [item["rule"] for item in unknown["policy"]["unknowns"]] == [
        "forbid_matrix_changes",
        "forbid_matrix_removals",
    ]


def test_cli_policy_violation_returns_one_and_invalid_policy_returns_five(tmp_path, capsys):
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps(_policy(max_job_duration_increase_seconds=30)), encoding="utf-8")
    arguments = [
        "compare",
        str(FIXTURES / "argdigest_ci_rerun_attempt_1"),
        str(FIXTURES / "argdigest_ci_rerun_attempt_2"),
        "--profile",
        "generic",
        "--policy",
        str(policy),
        "--format",
        "json",
    ]

    assert main(arguments) == 1
    assert json.loads(capsys.readouterr().out)["policy"]["assessment"] == "FAIL"

    policy.write_text("{}", encoding="utf-8")
    assert main(arguments) == 5
    assert "comparison-policy" in capsys.readouterr().err
