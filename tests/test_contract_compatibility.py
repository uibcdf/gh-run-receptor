import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from devtools.scripts import validate_contracts as contract_validation
from devtools.scripts.validate_contracts import validate_contracts
from gh_run_receptor.cli import main
from gh_run_receptor.contracts import (
    CONTRACTS,
    ContractSpec,
    SchemaVersion,
    contract_inventory,
    require_contract,
    upgrade_contract,
)
from gh_run_receptor.errors import ContractError

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/validate-contracts.yml"


def test_inventory_exposes_every_serialized_boundary_in_stable_order():
    inventory = contract_inventory()

    assert [item["kind"] for item in inventory] == [
        "bundle",
        "config",
        "config-capture",
        "comparison",
        "comparison-policy",
        "events",
        "model",
        "report",
    ]
    assert all(item["current"] == 1 and item["readable"] == [1] for item in inventory)
    schemas = [schema for item in inventory for schema in item["schemas"]]
    assert sum(item["frozen_since"] == "0.18.0" for item in schemas) == 4
    assert sum(item["frozen_since"] == "0.19.0" for item in schemas) == 3
    assert sum(item["frozen_since"] is None for item in schemas) == 1


@pytest.mark.parametrize(
    ("document", "kind", "message"),
    [
        ([], "bundle", "not a JSON object"),
        ({}, "bundle", "malformed bundle contract schema"),
        ({"schema": "foreign.bundle@1"}, "bundle", "malformed"),
        ({"schema": "gh-run-receptor.report@1"}, "bundle", "wrong contract kind"),
        ({"schema": "gh-run-receptor.bundle@2"}, "bundle", "future bundle"),
    ],
)
def test_contract_check_rejects_malformed_wrong_kind_and_future_versions(document, kind, message):
    with pytest.raises(ContractError, match=message):
        require_contract(document, kind)


def test_contract_check_distinguishes_a_retired_version():
    registry = {
        "bundle": ContractSpec(
            "bundle", 2, frozenset({2}), (SchemaVersion(2, "bundle-v2.schema.json", None),)
        )
    }

    with pytest.raises(ContractError, match="retired bundle contract version 1"):
        require_contract({"schema": "gh-run-receptor.bundle@1"}, "bundle", registry=registry)


def test_migrations_are_forward_only_stepwise_and_do_not_mutate_input():
    registry = {
        "bundle": ContractSpec(
            "bundle",
            3,
            frozenset({1, 2, 3}),
            tuple(
                SchemaVersion(version, f"bundle-v{version}.schema.json", None)
                for version in (1, 2, 3)
            ),
        )
    }
    calls = []

    def to_v2(document):
        calls.append((1, copy.deepcopy(document)))
        document.update(schema="gh-run-receptor.bundle@2", second=True)
        return document

    def to_v3(document):
        calls.append((2, copy.deepcopy(document)))
        document.update(schema="gh-run-receptor.bundle@3", third=True)
        return document

    source = {"schema": "gh-run-receptor.bundle@1", "identity": {"run": 7}}
    original = copy.deepcopy(source)

    migrated = upgrade_contract(
        source,
        "bundle",
        registry=registry,
        migrations={("bundle", 1): to_v2, ("bundle", 2): to_v3},
    )

    assert source == original
    assert migrated == {
        "schema": "gh-run-receptor.bundle@3",
        "identity": {"run": 7},
        "second": True,
        "third": True,
    }
    assert [version for version, _ in calls] == [1, 2]


def test_migration_requires_every_step_and_exact_next_identifier():
    registry = {
        "report": ContractSpec(
            "report",
            2,
            frozenset({1, 2}),
            (
                SchemaVersion(1, "report-v1.schema.json", None),
                SchemaVersion(2, "report-v2.schema.json", None),
            ),
        )
    }
    source = {"schema": "gh-run-receptor.report@1"}

    with pytest.raises(ContractError, match="missing report contract migration 1->2"):
        upgrade_contract(source, "report", registry=registry, migrations={})
    with pytest.raises(ContractError, match="did not produce"):
        upgrade_contract(
            source,
            "report",
            registry=registry,
            migrations={("report", 1): lambda value: value},
        )


def _baseline_runner(command, **kwargs):
    assert command[:2] == ["git", "show"]
    assert kwargs["capture_output"] is True and kwargs["check"] is False
    _, relative = command[2].split(":", 1)
    path = ROOT / relative
    if not path.is_file():
        return subprocess.CompletedProcess(command, 1, b"", b"missing baseline")
    return subprocess.CompletedProcess(command, 0, path.read_bytes(), b"")


_PUBLISHED_018_RESOURCES = {
    "bundle-v1.schema.json",
    "config-v1.schema.json",
    "model-v1.schema.json",
    "report-v1.schema.json",
}


def _candidate_runner(command, **kwargs):
    assert kwargs["capture_output"] is True and kwargs["check"] is False
    if command[:3] == ["git", "tag", "--list"]:
        return subprocess.CompletedProcess(command, 0, b"", b"")
    assert command[:2] == ["git", "show"]
    tag, relative = command[2].split(":", 1)
    path = ROOT / relative
    if tag == "0.18.0" and path.name in _PUBLISHED_018_RESOURCES:
        return subprocess.CompletedProcess(command, 0, path.read_bytes(), b"")
    return subprocess.CompletedProcess(command, 1, b"", b"missing baseline resource")


def test_candidate_gate_requires_every_new_resource_to_be_frozen():
    assert validate_contracts(
        ROOT,
        baseline_tag="0.18.0",
        candidate_tag="0.19.0",
        runner=_candidate_runner,
    ) == ["gh_run_receptor/schemas/events-v1.schema.json is not frozen for candidate 0.19.0"]

    errors = validate_contracts(ROOT, baseline_tag="0.19.0", runner=_candidate_runner)
    assert len([error for error in errors if "cannot read" in error]) == 3


def test_candidate_gate_rejects_an_existing_tag():
    def existing_tag_runner(command, **kwargs):
        if command[:3] == ["git", "tag", "--list"]:
            return subprocess.CompletedProcess(command, 0, b"0.19.0\n", b"")
        return _candidate_runner(command, **kwargs)

    errors = validate_contracts(
        ROOT,
        baseline_tag="0.18.0",
        candidate_tag="0.19.0",
        runner=existing_tag_runner,
    )
    assert errors == ["candidate tag 0.19.0 already exists; use normal validation"]


def test_candidate_gate_rejects_relabeling_a_published_resource(monkeypatch):
    bundle = CONTRACTS["bundle"]
    relabeled = ContractSpec(
        bundle.kind,
        bundle.current_version,
        bundle.readable_versions,
        (SchemaVersion(1, "bundle-v1.schema.json", "0.19.0"),),
    )
    monkeypatch.setattr(
        contract_validation,
        "CONTRACTS",
        {**CONTRACTS, "bundle": relabeled},
    )

    errors = validate_contracts(
        ROOT,
        baseline_tag="0.18.0",
        candidate_tag="0.19.0",
        runner=_candidate_runner,
    )
    assert errors == [
        "gh_run_receptor/schemas/bundle-v1.schema.json existed in 0.18.0 "
        "and cannot be newly frozen in 0.19.0",
        "gh_run_receptor/schemas/events-v1.schema.json is not frozen for candidate 0.19.0",
    ]


def test_baseline_gate_detects_in_place_change_and_unregistered_schema(tmp_path):
    package = tmp_path / "gh_run_receptor"
    shutil.copytree(ROOT / "gh_run_receptor/schemas", package / "schemas")

    assert validate_contracts(tmp_path, runner=_baseline_runner) == []

    bundle = package / "schemas/bundle-v1.schema.json"
    bundle.write_bytes(bundle.read_bytes() + b"\n")
    errors = validate_contracts(tmp_path, runner=_baseline_runner)
    assert errors == [
        "gh_run_receptor/schemas/bundle-v1.schema.json changed after frozen baseline 0.18.0"
    ]

    (package / "schemas/unknown-v1.schema.json").write_text("{}", encoding="utf-8")
    errors = validate_contracts(tmp_path, runner=_baseline_runner)
    assert errors[0].startswith("registered schema resources disagree with package files")


def test_contracts_cli_is_offline_bounded_and_machine_readable(capsys):
    assert main(["contracts"]) == 0
    text = capsys.readouterr().out
    assert len(text.splitlines()) == 1
    assert "baseline=0.19.0" in text
    assert "config-capture@1(readable=1)" in text

    assert main(["contracts", "--format=json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"baseline": "0.19.0", "contracts": contract_inventory()}
    assert set(CONTRACTS) == {item["kind"] for item in payload["contracts"]}


def test_hosted_contract_gate_is_manual_read_only_bounded_and_pinned():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert source.count("workflow_dispatch:") == 1
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert "permissions:\n  contents: read" in source
    assert "timeout-minutes: 5" in source
    assert "fetch-depth: 0" in source
    assert "persist-credentials: false" in source
    assert "validate_contracts.py --baseline 0.19.0" in source
    assert "--candidate" not in source
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7" in source
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7" in source
