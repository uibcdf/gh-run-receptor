"""Testing truth-preserving comparisons across runs and rerun attempts."""

from __future__ import annotations

import copy
import json
from importlib.resources import files
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from gh_run_receptor.bundle import load_bundle
from gh_run_receptor.cli import main
from gh_run_receptor.comparison import (
    compare_reports,
    exit_code,
    render_json,
    render_llm,
)
from gh_run_receptor.report import build_report

FIXTURES = Path(__file__).parent / "fixtures" / "bundles"
WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/validate-comparison.yml"


def _report(name: str, profile: str = "generic") -> dict:
    manifest, evidence = load_bundle(FIXTURES / name)
    return build_report(manifest, evidence, profile=profile)


def test_real_rerun_comparison_preserves_identity_and_transition():
    comparison = compare_reports(
        _report("argdigest_ci_rerun_attempt_1"),
        _report("argdigest_ci_rerun_attempt_2"),
    )

    assert comparison["assessment"] == "CHANGED"
    assert comparison["evidence_sufficient"] is True
    assert comparison["relation"] == {
        "same_repository": True,
        "same_workflow": True,
        "same_run": True,
        "same_head_sha": True,
    }
    assert comparison["left"]["run_attempt"] == 1
    assert comparison["right"]["run_attempt"] == 2
    assert comparison["left"]["conclusion"] == "failure"
    assert comparison["right"]["conclusion"] == "success"
    assert comparison["jobs"]["counts"]["delta"] == {"failure": -1, "success": 1}
    assert comparison["jobs"]["duration_seconds"]["delta"] == 39
    assert exit_code(comparison) == 0


def test_comparison_contract_accepts_real_rerun_and_json_is_deterministic():
    comparison = compare_reports(
        _report("argdigest_ci_rerun_attempt_1"),
        _report("argdigest_ci_rerun_attempt_2"),
    )
    schema = json.loads(
        files("gh_run_receptor.schemas")
        .joinpath("comparison-v1.schema.json")
        .read_text(encoding="utf-8")
    )

    Draft202012Validator(schema).validate(comparison)
    assert render_json(comparison).encode() == render_json(comparison).encode()

    conforming_emptiness = copy.deepcopy(comparison)
    conforming_emptiness["relation"] = {}
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(conforming_emptiness)

    incoherent_policy = copy.deepcopy(comparison)
    incoherent_policy["policy"] = {
        "evaluated": True,
        "assessment": "PASS",
        "violations": [{"rule": "anything", "expected": True, "observed": False}],
        "unknowns": [],
    }
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(incoherent_policy)


def test_different_commit_is_explicit_and_never_treated_as_equivalent():
    left = _report("argdigest_ci_rerun_attempt_1")
    right = copy.deepcopy(left)
    right["subject"]["run_id"] += 1
    right["subject"]["head_sha"] = "f" * 40

    comparison = compare_reports(left, right)

    assert comparison["relation"]["same_run"] is False
    assert comparison["relation"]["same_head_sha"] is False
    assert comparison["left"]["head_sha"] != comparison["right"]["head_sha"]
    assert comparison["warnings"] == ["source commits differ or a commit identity is unavailable"]
    assert "same_commit=false" in render_llm(comparison)


def test_incomplete_required_dimension_fails_closed():
    left = _report("argdigest_ci_rerun_attempt_1")
    right = _report("argdigest_ci_rerun_attempt_2")
    right["completeness"]["artifact_inventory"] = "unavailable"

    comparison = compare_reports(left, right)

    assert comparison["assessment"] == "INCOMPLETE"
    assert comparison["evidence_sufficient"] is False
    assert exit_code(comparison) == 4
    assert "artifact inventory evidence is incomplete" in comparison["warnings"][-1]


def test_duplicate_job_names_are_aggregated_independently_of_order():
    left = _report("argdigest_ci_rerun_attempt_1")
    right = _report("argdigest_ci_rerun_attempt_2")
    left["jobs"].append(copy.deepcopy(left["jobs"][0]))
    right["jobs"].append(copy.deepcopy(right["jobs"][0]))
    first = compare_reports(left, right)
    left["jobs"].reverse()
    right["jobs"].reverse()
    second = compare_reports(left, right)

    assert first == second
    assert first["jobs"]["state_changes"] == [
        {
            "name": "Test on ubuntu-latest, Python 3.13",
            "left": {"failure": 2},
            "right": {"success": 2},
        }
    ]


def test_artifacts_are_described_as_capture_inventory_not_release_regression():
    left = _report("argdigest_ci_rerun_attempt_1")
    right = copy.deepcopy(left)
    right["artifacts"] = [
        {
            "id": 7,
            "name": "wheel",
            "size_bytes": 12,
            "expired": False,
            "digest": None,
            "source": {"member": "artifacts.json", "json_pointer": "/artifacts/0"},
        }
    ]

    comparison = compare_reports(left, right)
    rendered = render_llm(comparison)

    assert comparison["artifacts"]["interpretation"] == "inventory_at_capture"
    assert comparison["artifacts"]["added"] == [{"name": "wheel", "count": 1}]
    assert "observation=inventory_at_capture" in rendered
    assert "regression" not in rendered.lower()


def test_llm_inventory_lists_are_bounded_and_single_line_safe():
    left = _report("argdigest_ci_rerun_attempt_1")
    right = copy.deepcopy(left)
    right["jobs"] = []
    for index in range(25):
        job = copy.deepcopy(left["jobs"][0])
        job["name"] = f"job-{index}\nforged"
        right["jobs"].append(job)
    right["job_counts"] = {"failure": 25}

    rendered = render_llm(compare_reports(left, right))

    assert "...+15" in rendered
    assert len(rendered.splitlines()) == 7
    assert "\nforged" not in rendered


def test_cli_compares_two_bundles_offline_as_json(capsys):
    result = main(
        [
            "compare",
            str(FIXTURES / "argdigest_ci_rerun_attempt_1"),
            str(FIXTURES / "argdigest_ci_rerun_attempt_2"),
            "--profile",
            "generic",
            "--format",
            "json",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["schema"] == "gh-run-receptor.comparison@1"
    assert output["relation"]["same_run"] is True


def test_cli_rejects_ambiguous_one_run_comparison(capsys):
    result = main(["compare", "22638022385", "--repo", "uibcdf/argdigest"])

    assert result == 5
    assert "requires exactly two --attempt" in capsys.readouterr().err


def test_hosted_comparison_gate_is_manual_read_only_bounded_and_pinned():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert source.count("workflow_dispatch:") == 1
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert "permissions:\n  actions: read\n  contents: read" in source
    assert "timeout-minutes: 5" in source
    assert "persist-credentials: false" in source
    assert "--attempt 1 --attempt 2" in source
    assert "--capture metadata" in source
    assert "argdigest-rerun-pass.json" in source
    assert "argdigest-rerun-fail.json" in source
    assert 'test "$status" -eq 1' in source
    assert "uibcdf/argdigest" in source
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7" in source
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7" in source
