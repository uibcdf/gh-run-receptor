import base64
import hashlib
import json
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator

from gh_run_receptor.config import (
    CONFIG_PATH,
    capture_repository_config,
    parse_config,
    select_rule,
    validate_config_capture,
)
from gh_run_receptor.errors import ConfigError

CONFIG = b"""schema_version: 1
workflows:
  - match:
      name: Conda packages
    profile: generic
  - match:
      id: 17
    profile: conda
  - match:
      path: .github/workflows/conda.yaml
    profile: conda
    settings:
      expected_platforms: [linux-64, osx-arm64, win-64]
"""


def test_parse_and_select_exact_rules_by_specificity():
    config = parse_config(CONFIG)

    rule = select_rule(
        config,
        path=".github/workflows/conda.yaml",
        workflow_id="17",
        name="Conda packages",
    )

    assert rule["match"] == {"path": ".github/workflows/conda.yaml"}
    assert rule["settings"]["expected_platforms"] == [
        "linux-64",
        "osx-arm64",
        "win-64",
    ]


def test_normalized_configuration_conforms_to_published_schema():
    schema = json.loads(
        files("gh_run_receptor.schemas")
        .joinpath("config-v1.schema.json")
        .read_text(encoding="utf-8")
    )

    Draft202012Validator(schema).validate(parse_config(CONFIG))


def test_ci_is_a_supported_profile_without_conda_settings():
    config = parse_config(
        b"""schema_version: 1
workflows:
  - match:
      path: .github/workflows/CI.yaml
    profile: ci
"""
    )

    assert config["workflows"][0] == {
        "match": {"path": ".github/workflows/CI.yaml"},
        "profile": "ci",
        "settings": {},
    }


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (b"schema_version: 2\nworkflows:\n", "schema_version"),
        (CONFIG + b"unknown: value\n", "unsupported"),
        (CONFIG.replace(b"conda.yaml", b"*.yaml"), "unsupported plain scalar"),
        (CONFIG.replace(b"profile: conda", b"profile: unknown", 1), "unsupported profile"),
        (
            CONFIG.replace(b"linux-64, osx-arm64, win-64", b"linux-64, linux-64"),
            "unique and nonempty",
        ),
        (CONFIG.replace(b"    profile", b"\tprofile", 1), "tabs"),
        (CONFIG.replace(b"Conda packages", b"&shared"), "anchors"),
        (CONFIG.replace(b"Conda packages", b"{name: CI}"), "flow mappings"),
        (
            CONFIG.replace(b"profile: conda", b"profile: generic", 2),
            "requires the conda profile",
        ),
    ],
)
def test_parser_rejects_ambiguous_or_unsupported_yaml(text, message):
    with pytest.raises(ConfigError, match=message):
        parse_config(text)


def test_parser_rejects_oversized_configuration():
    with pytest.raises(ConfigError, match="byte limit"):
        parse_config(CONFIG + b"#" * (64 * 1024))


class FakeClient:
    def __init__(self, data):
        self.data = data
        self.endpoints = []

    def json(self, endpoint):
        self.endpoints.append(endpoint)
        return {"default_branch": "release/candidate"}

    def optional_json(self, endpoint):
        self.endpoints.append(endpoint)
        return {
            "encoding": "base64",
            "content": base64.b64encode(self.data).decode(),
            "sha": "blob123",
        }


def test_capture_uses_default_branch_and_records_provenance():
    client = FakeClient(CONFIG)

    capture = capture_repository_config(client, "uibcdf/example")

    assert client.endpoints[-1] == (
        f"/repos/uibcdf/example/contents/{CONFIG_PATH}?ref=release%2Fcandidate"
    )
    assert capture["source"] == {
        "path": CONFIG_PATH,
        "ref": "release/candidate",
        "blob_sha": "blob123",
        "sha256": hashlib.sha256(CONFIG).hexdigest(),
    }
    assert validate_config_capture(capture) is capture


def test_capture_absence_is_not_an_error():
    client = FakeClient(CONFIG)
    client.optional_json = lambda endpoint: None

    assert capture_repository_config(client, "uibcdf/example") is None


def test_capture_validator_rejects_unrecognized_normalized_fields():
    client = FakeClient(CONFIG)
    capture = capture_repository_config(client, "uibcdf/example")
    capture["config"]["workflows"][0]["silent_success"] = True

    with pytest.raises(ConfigError, match="invalid workflow rule"):
        validate_config_capture(capture)
