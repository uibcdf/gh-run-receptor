import subprocess
import sys
from pathlib import Path

import pytest

from gh_run_receptor import cli, exit_codes
from gh_run_receptor.report import exit_code as report_exit_code

ROOT = Path(__file__).resolve().parents[1]
BUNDLES = ROOT / "tests" / "fixtures" / "bundles"
WORKFLOW = ROOT / ".github" / "workflows" / "validate-exit-codes.yml"


def _command(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "gh_run_receptor", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_exit_codes_are_distinct_and_frozen():
    expected = {
        "SUCCESS": 0,
        "FAILURE": 1,
        "TERMINAL_NON_SUCCESS": 2,
        "PENDING": 3,
        "INCOMPLETE": 4,
        "RECEPTOR_ERROR": 5,
        "USAGE_ERROR": 64,
        "INTERRUPTED": 130,
    }

    assert {name: getattr(exit_codes, name) for name in expected} == expected
    assert frozenset(expected.values()) == exit_codes.ALL
    assert len(exit_codes.ALL) == len(expected)


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        (("replay", str(BUNDLES / "molsysmt_conda_success")), exit_codes.SUCCESS),
        (("replay", str(BUNDLES / "molsysviewer_ci_failure")), exit_codes.FAILURE),
        (
            ("replay", str(BUNDLES / "molsysmt_conda_cancelled")),
            exit_codes.TERMINAL_NON_SUCCESS,
        ),
        (
            ("replay", str(BUNDLES / "pyunitwizard_ci_incomplete_logs")),
            exit_codes.INCOMPLETE,
        ),
        (("replay", "missing-bundle"), exit_codes.RECEPTOR_ERROR),
    ],
)
def test_console_boundary_preserves_result_categories(arguments, expected):
    result = _command(*arguments)

    assert result.returncode == expected


@pytest.mark.parametrize(
    "arguments",
    [(), ("invalid-command",), ("inspect", "not-a-run")],
)
def test_console_usage_errors_are_distinct_from_run_outcomes(arguments):
    result = _command(*arguments)

    assert result.returncode == exit_codes.USAGE_ERROR
    assert "usage:" in result.stderr
    assert "error:" in result.stderr


@pytest.mark.parametrize("arguments", [("--help",), ("--version",)])
def test_console_informational_options_succeed(arguments):
    result = _command(*arguments)

    assert result.returncode == exit_codes.SUCCESS
    assert result.stderr == ""


def test_pending_report_has_a_distinct_status():
    report = {"receptor": {"assessment": "PENDING", "evidence_sufficient": True}}

    assert report_exit_code(report) == exit_codes.PENDING


def test_keyboard_interrupt_has_the_shell_conventional_status(monkeypatch, capsys):
    def interrupt(_path):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "load_bundle", interrupt)

    assert cli.main(["replay", "bundle"]) == exit_codes.INTERRUPTED
    assert capsys.readouterr().err == "operation interrupted\n"


def test_hosted_exit_code_gate_is_manual_read_only_bounded_and_pinned():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert source.count("workflow_dispatch:") == 1
    assert "\n  push:" not in source
    assert "\n  pull_request:" not in source
    assert "permissions:\n  contents: read" in source
    assert "timeout-minutes: 5" in source
    assert "persist-credentials: false" in source
    assert "assert_status 0 replay" in source
    assert "assert_status 1 replay" in source
    assert "assert_status 2 replay" in source
    assert "assert_status 4 replay" in source
    assert "assert_status 5 replay" in source
    assert "assert_status 64 invalid-command" in source
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7" in source
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7" in source
