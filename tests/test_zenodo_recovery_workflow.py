"""Protect the receiving archival-discovery and read-only trust boundary."""

from pathlib import Path

import yaml


def test_zenodo_recovery_keeps_fixed_discovery_cutoff_and_read_only_provider():
    root = Path(__file__).resolve().parents[1]
    caller = yaml.load(
        (root / ".github/workflows/zenodo-recovery.yml").read_text(), Loader=yaml.BaseLoader
    )
    assert set(caller["on"]) == {"release", "schedule", "workflow_dispatch"}
    assert caller["on"]["release"]["types"] == ["published"]
    assert caller["on"]["schedule"] == [{"cron": "17 */6 * * *"}]
    assert caller["permissions"] == {"contents": "read"}
    job = caller["jobs"]["verify"]
    assert job["uses"] == (
        "uibcdf/molsyssuite/.github/workflows/verify-zenodo-releases.yaml@"
        "6d6172d6cd00c5ac2d4ebadb71df554ec5b7fa26"
    )
    assert job["with"]["concept-doi"] == "10.5281/zenodo.22843377"
    assert job["with"]["since"] == "2026-10-24T00:00:00Z"
    assert job["with"]["tag"] == (
        "${{ github.event_name == 'release' && github.event.release.tag_name || inputs.tag || '' }}"
    )
    assert "secrets" not in job and "steps" not in job
