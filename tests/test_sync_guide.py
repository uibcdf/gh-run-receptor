"""Testing canonical consumer-guide synchronization."""

from pathlib import Path

from devtools.scripts.sync_gh_run_receptor_guide import DEFAULT_REPOSITORIES, synchronize


def test_default_clients_cover_the_scientific_tooling_suite():
    assert {
        "argdigest",
        "depdigest",
        "elastnetmt",
        "molsysmt",
        "molsysviewer",
        "pharmacophoremt",
        "pytest-receptor",
        "pyunitwizard",
        "smonitor",
        "topomt",
    } <= set(DEFAULT_REPOSITORIES)


def _tree(root: Path):
    source = root / "gh-run-receptor" / "standards"
    source.mkdir(parents=True)
    (source / "GH_RUN_RECEPTOR_GUIDE.md").write_text("canonical\n", encoding="utf-8")
    (root / "client").mkdir()


def test_sync_writes_and_check_accepts_exact_guide(tmp_path):
    _tree(tmp_path)

    assert synchronize(tmp_path, ["client"], check=False, dry_run=False) == 0
    assert (tmp_path / "client" / "GH_RUN_RECEPTOR_GUIDE.md").read_text() == "canonical\n"
    assert synchronize(tmp_path, ["client"], check=True, dry_run=False) == 0


def test_check_rejects_missing_or_stale_guide(tmp_path):
    _tree(tmp_path)

    assert synchronize(tmp_path, ["client"], check=True, dry_run=False) == 1
    (tmp_path / "client" / "GH_RUN_RECEPTOR_GUIDE.md").write_text("stale\n")
    assert synchronize(tmp_path, ["client"], check=True, dry_run=False) == 1


def test_dry_run_does_not_write(tmp_path):
    _tree(tmp_path)

    assert synchronize(tmp_path, ["client"], check=False, dry_run=True) == 0
    assert not (tmp_path / "client" / "GH_RUN_RECEPTOR_GUIDE.md").exists()
