from pathlib import Path

import pytest

from gh_run_receptor import discovery
from gh_run_receptor.config import parse_config
from gh_run_receptor.discovery import (
    MAX_WORKFLOW_BYTES,
    discover_workflows,
    render_config,
    write_config,
)
from gh_run_receptor.errors import ConfigError


def _workflow(root: Path, name: str, source: str = "name: Workflow\n") -> Path:
    directory = root / ".github" / "workflows"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(source)
    return path


def test_discovery_is_sorted_non_recursive_and_classifies_client_shapes(tmp_path):
    _workflow(tmp_path, "verify-zenodo-release.yaml", "name: Verify Zenodo release\n")
    _workflow(tmp_path, "CI.yaml", "name: CI\n")
    _workflow(tmp_path, "docs-notebooks.yaml", "name: Documentation notebooks\n")
    _workflow(
        tmp_path,
        "build_and_upload_conda_packages.yaml",
        "name: Conda deployment of the noarch package\n",
    )
    backup = tmp_path / ".github" / "workflows" / "backups"
    backup.mkdir()
    (backup / "old-release.yaml").write_text("name: Old release\n")

    workflows = discover_workflows(tmp_path)

    assert [(item.path, item.profile) for item in workflows] == [
        (".github/workflows/CI.yaml", "ci"),
        (".github/workflows/build_and_upload_conda_packages.yaml", "conda"),
        (".github/workflows/docs-notebooks.yaml", "docs"),
        (".github/workflows/verify-zenodo-release.yaml", "release"),
    ]
    assert workflows[1].settings == (("package_kind", "noarch"),)
    assert all("backups" not in item.path for item in workflows)


def test_content_signals_classify_generic_filenames_and_ambiguity_falls_back(tmp_path):
    _workflow(tmp_path, "quality.yaml", "steps:\n  - run: pytest\n")
    _workflow(tmp_path, "pipeline.yaml", "steps:\n  - run: npm publish\n")
    _workflow(tmp_path, "docs-conda.yaml", "name: Ambiguous\n")
    _workflow(tmp_path, "unknown.yaml")

    by_name = {Path(item.path).name: item for item in discover_workflows(tmp_path)}

    assert by_name["quality.yaml"].profile == "ci"
    assert by_name["quality.yaml"].confidence == "medium"
    assert by_name["pipeline.yaml"].profile == "release"
    assert by_name["docs-conda.yaml"].profile == "generic"
    assert by_name["docs-conda.yaml"].reasons == ("ambiguous:conda", "ambiguous:docs")
    assert by_name["unknown.yaml"].reasons == ("no-profile-signal",)


def test_rendered_configuration_round_trips_through_the_strict_parser(tmp_path):
    _workflow(tmp_path, "ci.yaml", "name: CI\n")
    _workflow(tmp_path, "conda.yaml", "name: A noarch package\n")

    data = render_config(discover_workflows(tmp_path))
    config = parse_config(data)

    assert config["schema_version"] == 1
    assert len(config["workflows"]) == 2
    assert config["workflows"][1]["settings"] == {"package_kind": "noarch"}


def test_discovery_rejects_symlinks_and_oversized_or_invalid_sources(tmp_path):
    target = tmp_path / "target.yaml"
    target.write_text("name: CI\n")
    link = _workflow(tmp_path, "linked.yaml")
    link.unlink()
    link.symlink_to(target)

    with pytest.raises(ConfigError, match="regular non-symlink"):
        discover_workflows(tmp_path)

    link.unlink()
    oversized = _workflow(tmp_path, "large.yaml")
    oversized.write_bytes(b"x" * (MAX_WORKFLOW_BYTES + 1))
    with pytest.raises(ConfigError, match="byte discovery limit"):
        discover_workflows(tmp_path)

    oversized.unlink()
    invalid = _workflow(tmp_path, "invalid.yaml")
    invalid.write_bytes(b"\xff")
    with pytest.raises(ConfigError, match="not valid UTF-8"):
        discover_workflows(tmp_path)


def test_discovery_requires_an_immediate_workflow_file(tmp_path):
    (tmp_path / ".github" / "workflows" / "backups").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "backups" / "ci.yaml").write_text("name: CI\n")

    with pytest.raises(ConfigError, match="no workflow files"):
        discover_workflows(tmp_path)


def test_discovery_rejects_a_symlinked_workflow_directory(tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir()
    (actual / "ci.yaml").write_text("name: CI\n")
    github = tmp_path / ".github"
    github.mkdir()
    (github / "workflows").symlink_to(actual, target_is_directory=True)

    with pytest.raises(ConfigError, match="directories must not be symlinks"):
        discover_workflows(tmp_path)


def test_discovery_bounds_workflow_count(tmp_path, monkeypatch):
    monkeypatch.setattr(discovery, "MAX_DISCOVERED_WORKFLOWS", 2)
    _workflow(tmp_path, "one.yaml")
    _workflow(tmp_path, "two.yaml")
    _workflow(tmp_path, "three.yaml")

    with pytest.raises(ConfigError, match="workflow count exceeds the 2-file"):
        discover_workflows(tmp_path)


def test_discovery_bounds_total_source_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr(discovery, "MAX_TOTAL_WORKFLOW_BYTES", 5)
    _workflow(tmp_path, "one.yaml", "abc")
    _workflow(tmp_path, "two.yaml", "def")

    with pytest.raises(ConfigError, match="5-byte total discovery limit"):
        discover_workflows(tmp_path)


def test_write_is_atomic_and_refuses_to_replace_existing_configuration(tmp_path):
    _workflow(tmp_path, "ci.yaml", "name: CI\n")
    data = render_config(discover_workflows(tmp_path))

    target = write_config(tmp_path, data)

    assert target.read_bytes() == data
    with pytest.raises(ConfigError, match="already exists"):
        write_config(tmp_path, b"replacement")
    assert target.read_bytes() == data
