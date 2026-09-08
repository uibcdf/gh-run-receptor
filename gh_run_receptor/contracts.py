"""Defining serialized contract identities and forward-only migrations."""

from __future__ import annotations

import copy
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from gh_run_receptor.errors import ContractError

SCHEMA_PREFIX = "gh-run-receptor"
SCHEMA_BASELINE_TAG = "0.19.0"
_SCHEMA_018_BASELINE_TAG = "0.18.0"
_SCHEMA_ID = re.compile(r"^gh-run-receptor\.([a-z][a-z0-9-]*)@([1-9][0-9]*)$")


@dataclass(frozen=True)
class SchemaVersion:
    """Describing one packaged schema version and its immutable baseline."""

    version: int
    resource: str
    frozen_since: str | None


@dataclass(frozen=True)
class ContractSpec:
    """Describing one serialized contract family and all packaged versions."""

    kind: str
    current_version: int
    readable_versions: frozenset[int]
    schemas: tuple[SchemaVersion, ...]

    @property
    def current_schema(self) -> str:
        return schema_id(self.kind, self.current_version)


_SPECS = (
    ContractSpec(
        "bundle",
        1,
        frozenset({1}),
        (SchemaVersion(1, "bundle-v1.schema.json", _SCHEMA_018_BASELINE_TAG),),
    ),
    ContractSpec(
        "config",
        1,
        frozenset({1}),
        (SchemaVersion(1, "config-v1.schema.json", _SCHEMA_018_BASELINE_TAG),),
    ),
    ContractSpec(
        "config-capture",
        1,
        frozenset({1}),
        (SchemaVersion(1, "config-capture-v1.schema.json", SCHEMA_BASELINE_TAG),),
    ),
    ContractSpec(
        "comparison",
        1,
        frozenset({1}),
        (SchemaVersion(1, "comparison-v1.schema.json", SCHEMA_BASELINE_TAG),),
    ),
    ContractSpec(
        "comparison-policy",
        1,
        frozenset({1}),
        (SchemaVersion(1, "comparison-policy-v1.schema.json", SCHEMA_BASELINE_TAG),),
    ),
    ContractSpec(
        "model",
        1,
        frozenset({1}),
        (SchemaVersion(1, "model-v1.schema.json", _SCHEMA_018_BASELINE_TAG),),
    ),
    ContractSpec(
        "report",
        1,
        frozenset({1}),
        (SchemaVersion(1, "report-v1.schema.json", _SCHEMA_018_BASELINE_TAG),),
    ),
)
CONTRACTS: Mapping[str, ContractSpec] = MappingProxyType({item.kind: item for item in _SPECS})

Migration = Callable[[dict[str, Any]], dict[str, Any]]
MIGRATIONS: Mapping[tuple[str, int], Migration] = MappingProxyType({})


def schema_id(kind: str, version: int) -> str:
    """Building one canonical contract identifier."""

    if kind not in CONTRACTS:
        raise ContractError(f"unknown contract kind: {kind!r}")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise ContractError(f"invalid {kind} contract version: {version!r}")
    return f"{SCHEMA_PREFIX}.{kind}@{version}"


def require_contract(
    document: Any,
    expected_kind: str,
    *,
    registry: Mapping[str, ContractSpec] = CONTRACTS,
) -> int:
    """Returning the supported version of a kind-checked contract document."""

    if expected_kind not in registry:
        raise ContractError(f"unknown expected contract kind: {expected_kind!r}")
    if not isinstance(document, dict):
        raise ContractError(f"{expected_kind} contract is not a JSON object")
    identifier = document.get("schema")
    match = _SCHEMA_ID.fullmatch(identifier) if isinstance(identifier, str) else None
    if match is None:
        raise ContractError(f"malformed {expected_kind} contract schema: {identifier!r}")
    actual_kind, version_text = match.groups()
    if actual_kind != expected_kind:
        raise ContractError(f"wrong contract kind: expected {expected_kind!r}, got {actual_kind!r}")
    version = int(version_text)
    spec = registry[expected_kind]
    if version > spec.current_version:
        raise ContractError(
            f"future {expected_kind} contract version {version}; "
            f"current reader is {spec.current_version}"
        )
    if version not in spec.readable_versions:
        raise ContractError(f"retired {expected_kind} contract version {version}")
    return version


def upgrade_contract(
    document: Any,
    expected_kind: str,
    *,
    registry: Mapping[str, ContractSpec] = CONTRACTS,
    migrations: Mapping[tuple[str, int], Migration] = MIGRATIONS,
) -> dict[str, Any]:
    """Returning a current copy after explicit forward-only migration steps."""

    version = require_contract(document, expected_kind, registry=registry)
    current = registry[expected_kind].current_version
    if version == current:
        return document
    upgraded = copy.deepcopy(document)
    while version < current:
        migration = migrations.get((expected_kind, version))
        if migration is None:
            raise ContractError(
                f"missing {expected_kind} contract migration {version}->{version + 1}"
            )
        candidate = migration(copy.deepcopy(upgraded))
        if not isinstance(candidate, dict):
            raise ContractError(
                f"{expected_kind} contract migration {version}->{version + 1} "
                "did not return an object"
            )
        expected_schema = f"{SCHEMA_PREFIX}.{expected_kind}@{version + 1}"
        if candidate.get("schema") != expected_schema:
            raise ContractError(
                f"{expected_kind} contract migration {version}->{version + 1} "
                f"did not produce {expected_schema!r}"
            )
        upgraded = candidate
        version += 1
    return upgraded


def contract_inventory() -> list[dict[str, Any]]:
    """Returning the stable machine-readable compatibility inventory."""

    return [
        {
            "kind": spec.kind,
            "current": spec.current_version,
            "readable": sorted(spec.readable_versions),
            "schema": spec.current_schema,
            "schemas": [
                {
                    "version": item.version,
                    "identifier": schema_id(spec.kind, item.version),
                    "resource": item.resource,
                    "frozen_since": item.frozen_since,
                }
                for item in spec.schemas
            ],
        }
        for spec in _SPECS
    ]
