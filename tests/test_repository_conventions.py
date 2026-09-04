"""Guarding repository layout, versioning, and report lifecycle conventions."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_reports_module():
    path = ROOT / "devtools" / "scripts" / "devguide_reports.py"
    spec = importlib.util.spec_from_file_location("devguide_reports_for_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_package_uses_flat_layout_and_dynamic_tag_versioning():
    configuration = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert not (ROOT / "src").exists()
    assert (ROOT / "gh_run_receptor" / "__init__.py").is_file()
    assert "version" in configuration["project"]["dynamic"]
    assert "version" not in configuration["project"]
    assert any(
        requirement.startswith("versioningit")
        for requirement in configuration["build-system"]["requires"]
    )
    assert configuration["tool"]["versioningit"]["write"]["file"] == (
        "gh_run_receptor/_version.py"
    )


def test_all_developer_reports_obey_the_local_lifecycle():
    reports = _load_reports_module()

    assert reports.validate_all() == []


def test_generated_developer_indexes_are_current():
    result = subprocess.run(
        [sys.executable, "devtools/scripts/devguide_index.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
