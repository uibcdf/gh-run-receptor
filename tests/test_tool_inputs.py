"""Protect explicit tool inputs and exhaustive assertion-scope accounting."""

import json

import pytest

from gh_run_receptor_tools.devguide_reports import parse_report, validate_report
from gh_run_receptor_tools.test_inventory import audit, record_current


def test_report_validation_uses_the_explicit_root_after_changing_cwd(tmp_path, monkeypatch):
    source = tmp_path / "selected"
    source.mkdir()
    (source / "tests").mkdir()
    (source / "tests/guard.py").write_text("pass\n")
    report = source / "pending_proposals/report.md"
    report.parent.mkdir()
    report.write_text("""---
summary: Controlled input.
issue: uibcdf/gh-run-receptor#76
status: open
opened: 2026-10-29
closed:
verification: measured
area: [packaging]
guard: tests/guard.py
normative:
blocked_by: []
supersedes: []
---
""")
    monkeypatch.chdir(tmp_path)
    assert validate_report(parse_report(report), root=source) == []
    assert any(
        "guard does not exist" in error
        for error in validate_report(parse_report(report), root=tmp_path)
    )


def test_inventory_refuses_removed_assertions_and_unclassified_tests(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "devtools").mkdir()
    test = tmp_path / "tests/test_example.py"
    test.write_text("def test_case():\n    assert True\n")
    document = {
        "schema": "gh-run-receptor.test-scopes@1",
        "entries": {
            "tests/test_example.py::test_case": {
                "scope": "product",
                "reason": "Controlled assertion",
                "minimum_assertions": 1,
                "baseline_assertions": [],
            }
        },
    }
    (tmp_path / "devtools/test_scopes.json").write_text(json.dumps(document))
    record_current(tmp_path)
    assert audit(tmp_path)["functions"] == 1
    test.write_text("def test_case():\n    assert False\n")
    with pytest.raises(ValueError, match="Review changed assertions"):
        audit(tmp_path)
    test.write_text("def test_case():\n    pass\n")
    with pytest.raises(ValueError, match="lost assertions"):
        audit(tmp_path)
    test.write_text("def test_case():\n    assert True\ndef test_new():\n    assert True\n")
    with pytest.raises(ValueError, match="missing or stale"):
        audit(tmp_path)
