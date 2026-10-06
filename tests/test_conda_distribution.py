"""Protect the additive route, frozen resources and installed executable floor."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import tomllib
from pathlib import Path

import pytest
import yaml

import gh_run_receptor
from devtools.check_distribution_inputs import check_owner_inputs, checked_provider
from devtools.installed_smoke import verify_commands, verify_installation, verify_schemas
from gh_run_receptor.errors import AcquisitionError
from gh_run_receptor.github import GitHubClient

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = "devtools/conda-build/resources.toml"


@pytest.fixture
def member(tmp_path):
    shutil.copytree(ROOT / "gh_run_receptor", tmp_path / "gh_run_receptor")
    shutil.copytree(ROOT / "devtools/conda-build", tmp_path / "devtools/conda-build")
    shutil.copytree(ROOT / ".github/workflows", tmp_path / ".github/workflows")
    for name in ("pyproject.toml", "devtools/dependency_routes.toml"):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    return tmp_path


@pytest.fixture
def suite():
    candidates = [
        Path(os.environ.get("GH_RECEPTOR_SUITE_ROOT", "/nonexistent")),
        ROOT / ".molsyssuite",
        ROOT.parent / ".molsyssuite",
    ]
    for candidate in candidates:
        if (candidate / "devtools/scripts/dependency_routes.py").is_file():
            checked_provider(ROOT, candidate)
            return candidate
    pytest.skip("A checkout of the explicitly pinned distribution SDK is required")


def _audit(member: Path, suite: Path):
    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(suite / "devtools/scripts/dependency_routes.py"),
            "--root",
            str(member),
            "--declared-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_shared_route_review_accepts_inputs_and_refuses_missing_gh(member, suite):
    assert _audit(member, suite).returncode == 0
    recipe = member / "devtools/conda-build/meta.yaml"
    recipe.write_text(recipe.read_text().replace("    - gh >=2.48.0\n", ""))
    rejected = _audit(member, suite)
    assert rejected.returncode != 0
    assert "gh>=2.48.0" in rejected.stdout + rejected.stderr


def test_shared_review_refuses_new_unclassified_workflow(member, suite):
    (member / ".github/workflows/unclassified.yml").write_text("name: New route\n")
    rejected = _audit(member, suite)
    assert rejected.returncode != 0
    assert "unclassified" in rejected.stdout + rejected.stderr


def test_owner_review_refuses_a_stale_external_floor(member):
    check_owner_inputs(member)
    adapter = member / "gh_run_receptor/github.py"
    adapter.write_text(
        adapter.read_text().replace(
            "MINIMUM_GH_VERSION = (2, 48, 0)", "MINIMUM_GH_VERSION = (2, 49, 0)"
        )
    )
    with pytest.raises(ValueError, match="adapter floor"):
        check_owner_inputs(member)


def test_owner_review_refuses_schema_drift_even_with_the_same_filename(member):
    path = member / "gh_run_receptor/schemas/report-v1.schema.json"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="digest differs"):
        check_owner_inputs(member)


def test_installed_schema_guard_refuses_wrong_bytes_and_missing_inventory():
    inventory = tomllib.loads((ROOT / RESOURCES).read_text())
    verify_schemas(inventory)
    inventory["schema_sha256"]["report-v1.schema.json"] = "0" * 64
    with pytest.raises(ValueError, match="Installed frozen schema differs"):
        verify_schemas(inventory)
    inventory["schema_sha256"].pop("report-v1.schema.json")
    with pytest.raises(ValueError, match="registry differs"):
        verify_schemas(inventory)


@pytest.mark.parametrize("mutation", ["missing-schema", "wrong-version", "missing-gh"])
def test_exact_archive_guard_refuses_wrong_payload(member, suite, mutation):
    # A synthetic archive exercises the guard; it is never built or published.
    inventory = tomllib.loads((member / RESOURCES).read_text())
    data = {name: b"# synthetic Python resource\n" for name in inventory["required_paths"]}
    data[inventory["version_file"]] = b'__version__ = "0.0.0"\n'
    data["site-packages/gh_run_receptor-0.0.0.dist-info/METADATA"] = (
        b"Name: gh-run-receptor\nVersion: 0.0.0\n"
    )
    dependencies = ["python >=3.11,<3.15", "gh >=2.48.0"]
    if mutation == "missing-schema":
        del data["site-packages/gh_run_receptor/schemas/report-v1.schema.json"]
    elif mutation == "wrong-version":
        data[inventory["version_file"]] = b'__version__ = "9.9.9"\n'
    else:
        dependencies.pop()
    data["info/index.json"] = json.dumps(
        dict(
            name="gh-run-receptor",
            version="0.0.0",
            build="py_0",
            build_number=0,
            subdir="noarch",
            depends=dependencies,
        )
    ).encode()
    data["info/link.json"] = b'{"noarch": {"type": "python"}}'
    path = member / "gh-run-receptor-0.0.0-py_0.tar.bz2"
    with tarfile.open(path, "w:bz2") as archive:
        for name, raw in data.items():
            item = tarfile.TarInfo(name)
            item.size = len(raw)
            archive.addfile(item, io.BytesIO(raw))
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(suite / "devtools/scripts/noarch_conda.py"),
            "--root",
            str(member),
            "--plan",
            "devtools/conda-build/release_plan.example.toml",
            "--built-paths",
            shlex.quote(str(path)),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    expected = {
        "missing-schema": "resource is missing",
        "wrong-version": "embedded Python version",
        "missing-gh": "gh>=2.48.0",
    }[mutation]
    assert expected in result.stdout + result.stderr


def test_installed_conda_package_retains_frozen_resources_and_prefix_commands():
    records = list((Path(sys.prefix) / "conda-meta").glob("gh-run-receptor-*.json"))
    if not records:
        pytest.skip("Installed Conda qualification only; no Conda archive installed here")
    record = json.loads(records[0].read_text())
    verify_installation(ROOT, record["version"])


def test_installed_guard_refuses_import_from_the_component_checkout():
    root = Path(gh_run_receptor.__file__).resolve().parent.parent
    with pytest.raises(ValueError, match="isolated installed prefix"):
        verify_installation(root, gh_run_receptor.__version__)


@pytest.mark.parametrize("mode", ["absent", "outside-prefix", "old-version", "supported"])
def test_installed_external_command_guard_refuses_wrong_provenance_or_floor(
    tmp_path, monkeypatch, mode
):
    prefix = tmp_path / "qualified-prefix"
    prefix.mkdir()
    commands = {name: str(prefix / name) for name in ("gh", "gh-run-receptor")}
    if mode == "absent":
        commands["gh"] = None
    elif mode == "outside-prefix":
        commands["gh"] = str(tmp_path / "runner-gh")
    monkeypatch.setattr("devtools.installed_smoke.shutil.which", commands.get)

    def run(self, arguments, *, check_cli):
        assert arguments == ["--version"] and not check_cli
        return "gh version " + ("2.47.0" if mode == "old-version" else "2.48.0")

    monkeypatch.setattr(GitHubClient, "_run", run)
    if mode == "supported":
        assert verify_commands(prefix) == commands
    elif mode == "old-version":
        with pytest.raises(AcquisitionError, match="unsupported"):
            verify_commands(prefix)
    else:
        with pytest.raises(ValueError, match="qualified prefix"):
            verify_commands(prefix)


def test_distribution_workflow_changes_require_a_reviewed_inventory():
    inventory = tomllib.loads((ROOT / "devtools/dependency_routes.toml").read_text())
    rows = {row["path"]: row for row in inventory["workflows"]}
    discovered = {
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / ".github/workflows").iterdir()
        if p.suffix in {".yaml", ".yml"}
    }
    assert set(rows) == discovered
    for name, row in rows.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == row["sha256"]


def test_first_conda_publication_is_manual_and_requires_the_installed_matrix():
    plan = tomllib.loads((ROOT / "devtools/conda-build/release_plan.example.toml").read_text())
    inventory = tomllib.loads((ROOT / RESOURCES).read_text())
    assert plan["route"] == "staged" and plan["requires_installed_gate"]
    assert plan["test_platforms"] == ["linux-64", "osx-arm64", "win-64"]
    assert plan["python_versions"] == ["3.11", "3.12", "3.13", "3.14"]
    assert (
        "Recheck installed provenance after scientific tests"
        in inventory["installed_gate"]["required_steps"]
    )
    for name, job in (("stage-conda.yml", "stage"), ("promote-conda.yml", "promote")):
        workflow = yaml.load(
            (ROOT / ".github/workflows" / name).read_text(), Loader=yaml.BaseLoader
        )
        assert set(workflow["on"]) == {"workflow_dispatch"}
        assert workflow["permissions"] == {"contents": "read", "actions": "read"}
        assert workflow["jobs"][job]["needs"] == "review-inputs"
        assert workflow["jobs"][job]["secrets"] == {
            "ANACONDA_TOKEN": "${{ secrets.ANACONDA_UIBCDF_TOKEN }}"
        }
    installed = yaml.load(
        (ROOT / ".github/workflows/test-staged-conda.yml").read_text(), Loader=yaml.BaseLoader
    )
    assert installed["run-name"] == "Installed ${{ inputs.filename }} ${{ inputs.sha256 }}"
    assert set(installed["on"]) == {"workflow_dispatch"}
    assert "secrets" not in installed["jobs"]["installed"]
    promote = yaml.load(
        (ROOT / ".github/workflows/promote-conda.yml").read_text(), Loader=yaml.BaseLoader
    )
    inputs = promote["jobs"]["promote"]["with"]
    assert inputs["installed_run_id"] == "${{ inputs.installed_run_id }}"
    assert inputs["qualification_sha"] == "${{ inputs.qualification_sha }}"
