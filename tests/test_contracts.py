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
from gh_run_receptor.report import build_report, render_json, render_llm

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
    report = build_report(manifest, evidence, profile="auto")

    _validator("bundle-v1.schema.json").validate(manifest)
    _validator("model-v1.schema.json").validate(model)
    _validator("report-v1.schema.json").validate(report)
    assert report["github"]["conclusion"] == case["expected_github_conclusion"]
    assert report["receptor"]["assessment"] == case["expected_assessment"]
    assert report["subject"]["run_id"] == case["run_id"]


@pytest.mark.parametrize("case", list(_corpus()), ids=lambda case: case["path"])
def test_replay_is_byte_deterministic_for_fixed_evidence(case):
    manifest, evidence = load_bundle(FIXTURES / case["path"])

    first = render_json(build_report(manifest, evidence, profile="auto"))
    second = render_json(build_report(manifest, evidence, profile="auto"))

    assert first.encode() == second.encode()


def test_text_rendering_is_stable_under_shuffled_api_collections():
    manifest, evidence = load_bundle(FIXTURES / "bundles/molsysmt_conda_partial")
    shuffled = copy.deepcopy(evidence)
    shuffled["jobs.json"]["jobs"].reverse()
    shuffled["artifacts.json"]["artifacts"].reverse()

    original = render_llm(build_report(manifest, evidence, profile="auto"))
    reordered = render_llm(build_report(manifest, shuffled, profile="auto"))

    assert reordered == original


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
