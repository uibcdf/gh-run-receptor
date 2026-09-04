"""Loading bounded declarative workflow configuration without executing content."""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

from gh_run_receptor.errors import AcquisitionError, ConfigError

CONFIG_PATH = ".github/gh-run-receptor.yaml"
CONFIG_SCHEMA = "gh-run-receptor.config@1"
MAX_CONFIG_BYTES = 64 * 1024
MAX_CONFIG_LINES = 1_000
MAX_LINE_LENGTH = 2_048
PROFILES = {"generic", "ci", "conda"}
PLATFORMS = {"linux-64", "linux-aarch64", "osx-64", "osx-arm64", "win-64"}
_KEY = re.compile(r"^[a-z_][a-z0-9_]*$")
_PLAIN = re.compile(r"^[A-Za-z0-9_./ ()+-]+$")


@dataclass(frozen=True)
class Token:
    line: int
    indent: int
    text: str


def _scalar(value: str, *, line: int) -> str:
    value = value.strip()
    if not value:
        raise ConfigError(f"line {line}: expected a scalar value")
    if value[0:1] in {'"', "'"}:
        if len(value) < 2 or value[-1] != value[0]:
            raise ConfigError(f"line {line}: unterminated quoted value")
        value = value[1:-1]
    elif _PLAIN.fullmatch(value) is None:
        raise ConfigError(f"line {line}: unsupported plain scalar")
    if not value or len(value) > 300:
        raise ConfigError(f"line {line}: scalar length is outside the supported range")
    return value


def _inline_list(value: str, *, line: int) -> list[str]:
    if not value.startswith("[") or not value.endswith("]"):
        raise ConfigError(f"line {line}: expected an inline list")
    contents = value[1:-1].strip()
    return [] if not contents else [_scalar(item, line=line) for item in contents.split(",")]


def _tokens(data: bytes) -> list[Token]:
    if len(data) > MAX_CONFIG_BYTES:
        raise ConfigError(f"configuration exceeds the {MAX_CONFIG_BYTES}-byte limit")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ConfigError("configuration is not valid UTF-8") from error
    lines = text.splitlines()
    if len(lines) > MAX_CONFIG_LINES:
        raise ConfigError(f"configuration exceeds the {MAX_CONFIG_LINES}-line limit")
    tokens = []
    for number, raw in enumerate(lines, start=1):
        if len(raw) > MAX_LINE_LENGTH:
            raise ConfigError(f"line {number}: exceeds the line-length limit")
        if "\t" in raw:
            raise ConfigError(f"line {number}: tabs are not supported")
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent % 2:
            raise ConfigError(f"line {number}: indentation must use multiples of two spaces")
        if any(marker in stripped for marker in ("&", "!", "{", "}", "|", ">")):
            raise ConfigError(f"line {number}: YAML tags, anchors, and flow mappings are forbidden")
        tokens.append(Token(number, indent, stripped))
    return tokens


def _pair(token: Token) -> tuple[str, str]:
    if ":" not in token.text:
        raise ConfigError(f"line {token.line}: expected key: value")
    key, value = token.text.split(":", 1)
    if _KEY.fullmatch(key) is None:
        raise ConfigError(f"line {token.line}: invalid key {key!r}")
    return key, value.strip()


def _settings(tokens: list[Token], index: int) -> tuple[dict[str, Any], int]:
    settings: dict[str, Any] = {}
    while index < len(tokens) and tokens[index].indent > 4:
        token = tokens[index]
        if token.indent != 6:
            raise ConfigError(f"line {token.line}: invalid settings indentation")
        key, value = _pair(token)
        if key != "expected_platforms" or key in settings:
            raise ConfigError(f"line {token.line}: unsupported or duplicate setting {key!r}")
        if value:
            platforms = _inline_list(value, line=token.line)
            index += 1
        else:
            platforms = []
            index += 1
            while index < len(tokens) and tokens[index].indent > 6:
                item = tokens[index]
                if item.indent != 8 or not item.text.startswith("- "):
                    raise ConfigError(f"line {item.line}: expected a platform list item")
                platforms.append(_scalar(item.text[2:], line=item.line))
                index += 1
        if not platforms or len(platforms) != len(set(platforms)):
            raise ConfigError(f"line {token.line}: expected_platforms must be unique and nonempty")
        unsupported = sorted(set(platforms) - PLATFORMS)
        if unsupported:
            raise ConfigError(f"line {token.line}: unsupported platforms: {', '.join(unsupported)}")
        settings[key] = platforms
    return settings, index


def _workflows(tokens: list[Token], index: int) -> tuple[list[dict[str, Any]], int]:
    workflows = []
    while index < len(tokens) and tokens[index].indent > 0:
        start = tokens[index]
        if start.indent != 2 or start.text != "- match:":
            raise ConfigError(f"line {start.line}: workflow entries must start with '- match:'")
        index += 1
        if index >= len(tokens) or tokens[index].indent != 6:
            raise ConfigError(f"line {start.line}: match requires one exact identity")
        match_token = tokens[index]
        match_key, raw_match = _pair(match_token)
        if match_key not in {"path", "id", "name"}:
            raise ConfigError(f"line {match_token.line}: unsupported match key {match_key!r}")
        match_value: str | int = _scalar(raw_match, line=match_token.line)
        if match_key == "id":
            try:
                match_value = int(match_value)
            except ValueError as error:
                raise ConfigError(
                    f"line {match_token.line}: workflow id must be an integer"
                ) from error
            if match_value < 1:
                raise ConfigError(f"line {match_token.line}: workflow id must be positive")
        index += 1
        profile = None
        settings: dict[str, Any] = {}
        while index < len(tokens) and tokens[index].indent > 2:
            token = tokens[index]
            if token.indent != 4:
                raise ConfigError(f"line {token.line}: invalid workflow-rule indentation")
            key, value = _pair(token)
            if key == "profile" and profile is None:
                profile = _scalar(value, line=token.line)
                if profile not in PROFILES:
                    raise ConfigError(f"line {token.line}: unsupported profile {profile!r}")
                index += 1
            elif key == "settings" and not value and not settings:
                index += 1
                settings, index = _settings(tokens, index)
            else:
                raise ConfigError(f"line {token.line}: unsupported or duplicate rule key {key!r}")
        if profile is None:
            raise ConfigError(f"line {start.line}: workflow rule requires a profile")
        if settings and profile != "conda":
            raise ConfigError(
                f"line {start.line}: expected_platforms requires the conda profile"
            )
        workflows.append(
            {"match": {match_key: match_value}, "profile": profile, "settings": settings}
        )
    return workflows, index


def parse_config(data: bytes) -> dict[str, Any]:
    """Parsing the intentionally narrow YAML subset accepted by config version 1."""
    tokens = _tokens(data)
    schema_version = None
    workflows = None
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.indent != 0:
            raise ConfigError(f"line {token.line}: unexpected top-level indentation")
        key, value = _pair(token)
        if key == "schema_version" and schema_version is None:
            if value != "1":
                raise ConfigError(f"line {token.line}: unsupported schema_version {value!r}")
            schema_version = 1
            index += 1
        elif key == "workflows" and not value and workflows is None:
            workflows, index = _workflows(tokens, index + 1)
        else:
            raise ConfigError(f"line {token.line}: unsupported or duplicate root key {key!r}")
    if schema_version != 1:
        raise ConfigError("configuration requires schema_version: 1")
    if not workflows:
        raise ConfigError("configuration requires at least one workflow rule")
    identities = [
        (next(iter(rule["match"])), next(iter(rule["match"].values())))
        for rule in workflows
    ]
    if len(identities) != len(set(identities)):
        raise ConfigError("configuration contains duplicate workflow matches")
    return {"schema": CONFIG_SCHEMA, "schema_version": 1, "workflows": workflows}


def load_config(path: Path) -> dict[str, Any]:
    try:
        data = path.read_bytes()
    except OSError as error:
        raise ConfigError(f"cannot read configuration: {error}") from error
    return parse_config(data)


def validate_config_capture(value: Any) -> dict[str, Any]:
    """Validating the normalized configuration envelope stored in a bundle."""
    if not isinstance(value, dict) or set(value) != {"schema", "source", "config"}:
        raise ConfigError("configuration capture has invalid root fields")
    if value["schema"] != "gh-run-receptor.config-capture@1":
        raise ConfigError("configuration capture has an unsupported schema")
    source = value["source"]
    if not isinstance(source, dict) or set(source) != {
        "path",
        "ref",
        "blob_sha",
        "sha256",
    }:
        raise ConfigError("configuration capture has invalid source fields")
    if source["path"] != CONFIG_PATH or not isinstance(source["ref"], str) or not source["ref"]:
        raise ConfigError("configuration capture has an invalid source identity")
    if source["blob_sha"] is not None and not isinstance(source["blob_sha"], str):
        raise ConfigError("configuration capture has an invalid blob SHA")
    if (
        not isinstance(source["sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", source["sha256"]) is None
    ):
        raise ConfigError("configuration capture has an invalid content digest")
    config = value["config"]
    if not isinstance(config, dict) or set(config) != {"schema", "schema_version", "workflows"}:
        raise ConfigError("captured configuration has invalid root fields")
    if config["schema"] != CONFIG_SCHEMA or config["schema_version"] != 1:
        raise ConfigError("captured configuration has an unsupported schema")
    workflows = config["workflows"]
    if not isinstance(workflows, list) or not workflows:
        raise ConfigError("captured configuration requires workflow rules")
    identities = []
    for rule in workflows:
        if not isinstance(rule, dict) or set(rule) != {"match", "profile", "settings"}:
            raise ConfigError("captured configuration has an invalid workflow rule")
        match = rule["match"]
        if not isinstance(match, dict) or len(match) != 1:
            raise ConfigError("captured configuration has an invalid workflow match")
        key, match_value = next(iter(match.items()))
        if key not in {"path", "id", "name"}:
            raise ConfigError("captured configuration has an unsupported workflow match")
        if key == "id":
            if isinstance(match_value, bool) or not isinstance(match_value, int) or match_value < 1:
                raise ConfigError("captured configuration has an invalid workflow id")
        elif not isinstance(match_value, str) or not match_value:
            raise ConfigError("captured configuration has an invalid workflow identity")
        if rule["profile"] not in PROFILES:
            raise ConfigError("captured configuration has an unsupported profile")
        settings = rule["settings"]
        if not isinstance(settings, dict) or set(settings) - {"expected_platforms"}:
            raise ConfigError("captured configuration has unsupported settings")
        if "expected_platforms" in settings:
            if rule["profile"] != "conda":
                raise ConfigError(
                    "captured expected platforms require the conda profile"
                )
            platforms = settings["expected_platforms"]
            if (
                not isinstance(platforms, list)
                or not platforms
                or not all(isinstance(item, str) for item in platforms)
                or len(platforms) != len(set(platforms))
                or set(platforms) - PLATFORMS
            ):
                raise ConfigError("captured configuration has invalid expected platforms")
        identities.append((key, match_value))
    if len(identities) != len(set(identities)):
        raise ConfigError("captured configuration contains duplicate workflow matches")
    return value


def select_rule(
    config: dict[str, Any], *, path: Any = None, workflow_id: Any = None, name: Any = None
) -> dict[str, Any] | None:
    """Selecting the most specific exact workflow rule."""
    try:
        normalized_id = int(workflow_id) if workflow_id is not None else None
    except (TypeError, ValueError):
        normalized_id = None
    observed = {"path": path, "id": normalized_id, "name": name}
    priority = {"path": 3, "id": 2, "name": 1}
    matches = []
    for rule in config["workflows"]:
        key, expected = next(iter(rule["match"].items()))
        if observed[key] == expected:
            matches.append((priority[key], rule))
    if not matches:
        return None
    matches.sort(key=lambda item: item[0], reverse=True)
    return matches[0][1]


def capture_repository_config(client: Any, repository: str) -> dict[str, Any] | None:
    """Fetching configuration only from the repository's default branch."""
    repository_info = client.json(f"/repos/{repository}")
    if not isinstance(repository_info, dict) or not isinstance(
        repository_info.get("default_branch"), str
    ):
        raise AcquisitionError("repository response does not identify a default branch")
    branch = repository_info["default_branch"]
    encoded_branch = quote(branch, safe="")
    response = client.optional_json(
        f"/repos/{repository}/contents/{CONFIG_PATH}?ref={encoded_branch}"
    )
    if response is None:
        return None
    if not isinstance(response, dict) or response.get("encoding") != "base64":
        raise AcquisitionError("repository configuration response is not base64 content")
    encoded = response.get("content")
    if not isinstance(encoded, str):
        raise AcquisitionError("repository configuration response has no content")
    try:
        data = base64.b64decode("".join(encoded.split()), validate=True)
    except (ValueError, binascii.Error) as error:
        raise AcquisitionError("repository configuration has invalid base64 content") from error
    config = parse_config(data)
    return {
        "schema": "gh-run-receptor.config-capture@1",
        "source": {
            "path": CONFIG_PATH,
            "ref": branch,
            "blob_sha": response.get("sha"),
            "sha256": hashlib.sha256(data).hexdigest(),
        },
        "config": config,
    }
