"""Guarding repository layout, versioning, and report lifecycle conventions."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_package_uses_src_layout_and_dynamic_tag_versioning():
    configuration = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert not (ROOT / "gh_run_receptor").exists()
    assert (ROOT / "src/gh_run_receptor" / "__init__.py").is_file()
    assert "version" in configuration["project"]["dynamic"]
    assert "version" not in configuration["project"]
    assert configuration["tool"]["setuptools"]["packages"]["find"]["where"] == ["src"]
    assert any(
        requirement.startswith("versioningit")
        for requirement in configuration["build-system"]["requires"]
    )
    assert configuration["tool"]["versioningit"]["write"]["file"] == (
        "src/gh_run_receptor/_version.py"
    )


def test_all_developer_reports_obey_the_local_lifecycle():
    from gh_run_receptor_tools import devguide_reports as reports

    assert reports.validate_all(ROOT) == []


def test_generated_developer_indexes_are_current():
    result = subprocess.run(
        [sys.executable, "devtools/scripts/devguide_index.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
