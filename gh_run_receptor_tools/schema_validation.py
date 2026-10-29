"""Validate installed contract resources with an explicit resource name."""

import json
from importlib.resources import files

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from gh_run_receptor.contracts import CONTRACTS


def schema(name: str) -> dict:
    return json.loads(files("gh_run_receptor.schemas").joinpath(name).read_text(encoding="utf-8"))


def validator(name: str) -> Draft202012Validator:
    registry = Registry()
    for spec in CONTRACTS.values():
        for item in spec.schemas:
            value = schema(item.resource)
            registry = registry.with_resource(value["$id"], Resource.from_contents(value))
    return Draft202012Validator(schema(name), registry=registry)
