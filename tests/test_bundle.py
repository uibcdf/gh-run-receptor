import hashlib
import json

import pytest

from devtools.scripts.sanitize_bundle import _selected_evidence
from gh_run_receptor.bundle import REQUIRED_STRUCTURED_MEMBERS, default_bundle_path, load_bundle
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
    for name in REQUIRED_STRUCTURED_MEMBERS:
        data = (json.dumps(values[name], sort_keys=True) + "\n").encode()
        (path / name).write_bytes(data)
        members.append(
            {
                "path": name,
                "kind": f"test.{name}",
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "complete": True,
            }
        )
    manifest = {
        "schema": "gh-run-receptor.bundle@1",
        "repository": "uibcdf/molsysmt",
        "hostname": "github.com",
        "run_id": 42,
        "run_attempt": 1,
        "head_sha": "abc",
        "api_version": "2022-11-28",
        "receptor_version": "test",
        "capture_policy": "metadata",
        "captured_at": "2026-09-04T10:00:00+00:00",
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

    with pytest.raises(BundleError, match="byte-count mismatch"):
        load_bundle(bundle)


def test_load_bundle_rejects_traversal_member(tmp_path):
    bundle = tmp_path / "bundle"
    _write_bundle(bundle)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["members"].append(
        {
            "path": "../secret",
            "kind": "untrusted",
            "bytes": 0,
            "sha256": "0" * 64,
            "complete": True,
        }
    )
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


def test_load_bundle_rejects_duplicate_json_keys(tmp_path):
    bundle = tmp_path / "bundle"
    _write_bundle(bundle)
    manifest = (bundle / "manifest.json").read_text()
    manifest = manifest.replace('"schema":', '"schema": "duplicate", "schema":', 1)
    (bundle / "manifest.json").write_text(manifest)

    with pytest.raises(BundleError, match="duplicate JSON key"):
        load_bundle(bundle)


def test_load_bundle_rejects_member_byte_count_mismatch(tmp_path):
    bundle = tmp_path / "bundle"
    _write_bundle(bundle)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["members"][0]["bytes"] += 1
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(BundleError, match="byte-count mismatch"):
        load_bundle(bundle)


def test_sanitizer_retains_optional_trusted_configuration():
    evidence = {
        "run.json": {},
        "workflow.json": {},
        "jobs.json": {"jobs": []},
        "checks.json": {"check_runs": []},
        "artifacts.json": {"artifacts": []},
        "config.json": {"schema": "gh-run-receptor.config-capture@1"},
    }

    selected = _selected_evidence(evidence)

    assert selected["config.json"] == evidence["config.json"]
    assert "config.json" not in _selected_evidence(evidence, include_config=False)
