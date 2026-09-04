import hashlib
import json

import pytest

from gh_run_receptor.bundle import STRUCTURED_MEMBERS, default_bundle_path, load_bundle
from gh_run_receptor.errors import BundleError


def _write_bundle(path):
    path.mkdir()
    values = {
        "run.json": {"status": "completed", "conclusion": "success"},
        "workflow.json": {"path": ".github/workflows/ci.yaml"},
        "jobs.json": {"total_count": 0, "jobs": []},
        "checks.json": {"total_count": 0, "check_runs": []},
        "artifacts.json": {"total_count": 0, "artifacts": []},
    }
    members = []
    for name in STRUCTURED_MEMBERS:
        data = (json.dumps(values[name], sort_keys=True) + "\n").encode()
        (path / name).write_bytes(data)
        members.append(
            {"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        )
    manifest = {
        "schema": "gh-run-receptor.bundle@1",
        "repository": "uibcdf/molsysmt",
        "run_id": 42,
        "run_attempt": 1,
        "complete": True,
        "members": members,
        "warnings": [],
    }
    (path / "manifest.json").write_text(json.dumps(manifest))


def test_load_bundle_validates_and_returns_evidence(tmp_path):
    bundle = tmp_path / "bundle"
    _write_bundle(bundle)

    manifest, evidence = load_bundle(bundle)

    assert manifest["run_id"] == 42
    assert evidence["run.json"]["conclusion"] == "success"


def test_load_bundle_rejects_changed_member(tmp_path):
    bundle = tmp_path / "bundle"
    _write_bundle(bundle)
    (bundle / "run.json").write_text('{"conclusion": "failure"}\n')

    with pytest.raises(BundleError, match="digest mismatch"):
        load_bundle(bundle)


def test_load_bundle_rejects_traversal_member(tmp_path):
    bundle = tmp_path / "bundle"
    _write_bundle(bundle)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["members"].append({"path": "../secret", "sha256": "unused"})
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(BundleError, match="unsafe or duplicate"):
        load_bundle(bundle)


def test_default_bundle_path_separates_capture_policies(tmp_path):
    metadata = default_bundle_path(
        tmp_path, "github.com", "uibcdf/molsysmt", 42, 2, "metadata"
    )
    full = default_bundle_path(tmp_path, "github.com", "uibcdf/molsysmt", 42, 2, "full")

    assert metadata != full
    assert metadata.parts[-5:] == ("uibcdf", "molsysmt", "42", "2", "metadata")
