"""Regressions from public runs, retaining source identity and original locators."""

import json
import zipfile
from pathlib import Path

import pytest

from gh_run_receptor.logs import extract_causes
from gh_run_receptor.report import build_report, exit_code, render_human, render_json, render_llm

FIXTURES = Path(__file__).parent / "fixtures/logs"
CASES = json.loads((FIXTURES / "diagnostic_ranking.json").read_text())["cases"]


def archive_for_case(tmp_path, case):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        for log in case["logs"]:
            lines = []
            for fragment in log["fragments"]:
                lines.extend([""] * (fragment["start_line"] - len(lines) - 1))
                lines.extend(fragment["lines"])
            zipped.writestr(log["member"], "\n".join(lines) + "\n")
    return archive


def report_for_case(tmp_path, case, profile):
    archive_for_case(tmp_path, case)
    manifest = {
        **{key: case[key] for key in ("repository", "run_id", "run_attempt", "head_sha")},
        "capture_policy": "adaptive",
        "complete": True,
        "warnings": [],
        "members": [{"path": "logs.zip"}],
    }
    evidence = {
        "run.json": case["run"],
        "workflow.json": case["workflow"],
        "jobs.json": {"jobs": case["jobs"]},
        "checks.json": {"total_count": 0, "check_runs": []},
        "artifacts.json": {"artifacts": []},
    }
    return build_report(manifest, evidence, bundle_directory=tmp_path, profile=profile)


@pytest.mark.parametrize("case", CASES, ids=lambda c: str(c["run_id"]))
def test_original_public_diagnostics_outrank_secondary_messages(tmp_path, case):
    archive = archive_for_case(tmp_path, case)
    failed = [job for job in case["jobs"] if job["conclusion"] == "failure"]
    causes, warnings = extract_causes(archive, failed)
    assert warnings == []
    assert {o["job_id"] for c in causes for o in c["occurrences"]} == {j["id"] for j in failed}
    for cause in causes:
        assert cause["kind"] == case["expected"]["kind"]
        assert case["expected"]["message"] in cause["message"]
        if case["run_id"] == 38037422889:
            assert "| at dockingmt/preparation/_molsys.py:148" in cause["message"]
        for occurrence in cause["occurrences"]:
            source = next(log for log in case["logs"] if log["job_id"] == occurrence["job_id"])
            assert occurrence["member"] == source["member"]
            assert any(
                f["start_line"] <= occurrence["line"] < f["start_line"] + len(f["lines"])
                for f in source["fragments"]
            )


@pytest.mark.parametrize("profile", ["generic", "ci"])
@pytest.mark.parametrize("case", CASES, ids=lambda c: str(c["run_id"]))
def test_public_diagnosis_preserves_api_truth_and_bounded_deterministic_rendering(
    tmp_path, case, profile
):
    report = report_for_case(tmp_path, case, profile)
    assert report["github"] == {"status": "completed", "conclusion": "failure"}
    assert exit_code(report) == 1
    assert {j["id"]: j["conclusion"] for j in report["jobs"]} == {
        j["id"]: j["conclusion"] for j in case["jobs"]
    }
    for renderer in (render_llm, render_human, render_json):
        output = renderer(report)
        assert case["expected"]["message"] in output
        assert output == renderer(report_for_case(tmp_path, case, profile))
        assert len(output.encode()) < (180_000 if renderer is render_json else 16_000)
        if case["expected"]["kind"] == "pytest_failure":
            for cause in report["causes"]:
                frame = cause["occurrences"][0]["context"][0]
                assert frame["kind"] == "frame"
                assert frame["message"] in output


@pytest.mark.parametrize("profile", ["generic", "ci"])
@pytest.mark.parametrize("case", CASES, ids=lambda c: str(c["run_id"]))
def test_public_diagnostic_rendering_matches_reviewed_goldens(tmp_path, case, profile):
    goldens = json.loads((FIXTURES / "diagnostic_ranking_golden.json").read_text())
    report = report_for_case(tmp_path, case, profile)
    expected = goldens[str(case["run_id"])][profile]
    assert render_llm(report) == expected["llm"]
    assert render_human(report) == expected["human"]


def _extract_body(tmp_path, body):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("0_Tests.txt", body)
    return extract_causes(archive, [{"id": 1, "name": "Tests"}])


SUMMARY = (
    "FAIL exit=1 | 1 failed | 1 root cause\n"
    "[1] AssertionError | 1 test | call\n"
    "tests/test_example.py:17\n"
    "AssertionError: the requested canvas is absent\n"
    "tests:\n"
    "tests/test_example.py::test_canvas\n"
)
EXIT = "##[error]Process completed with exit code 1.\n"


@pytest.mark.parametrize(
    "change", ["no-verdict", "positive", "no-group", "no-frame", "wrong-type", "expired"]
)
def test_incomplete_or_unmatched_pytest_groups_do_not_invent_a_diagnosis(tmp_path, change):
    body = SUMMARY
    if change == "no-verdict":
        body = body.split("\n", 1)[1]
    elif change == "positive":
        body = body.replace("FAIL exit=1", "PASS exit=0")
    elif change == "no-group":
        body = body.replace("[1] AssertionError | 1 test | call\n", "")
    elif change == "no-frame":
        body = body.replace("tests/test_example.py:17\n", "")
    elif change == "wrong-type":
        body = body.replace("[1] AssertionError", "[1] ValueError")
    else:
        body = body.replace("[1]", "\n" * 129 + "[1]", 1)
    causes, warnings = _extract_body(tmp_path, body + EXIT)
    assert warnings == []
    assert causes[0]["kind"] == "exit_code"


@pytest.mark.parametrize("offset, expected", [(128, "pytest_failure"), (129, "exit_code")])
def test_pytest_group_window_has_an_exact_boundary(tmp_path, offset, expected):
    lines = SUMMARY.splitlines()[:4]
    lines[3:3] = [""] * (offset - 3)
    causes, _ = _extract_body(tmp_path, "\n".join(lines) + "\n" + EXIT)
    assert causes[0]["kind"] == expected


def test_pytest_context_is_redacted_bounded_and_terminal_safe(tmp_path):
    token = "ghp_" + "a" * 40
    body = SUMMARY.replace("the requested canvas is absent", f"TOKEN={token} " + "x" * 20_000)
    body = body.replace("::test_canvas", f"::test_canvas[TOKEN={token}]")
    body += "\n".join(f"tests/test_example.py::test_extra[{i}]" for i in range(100)) + "\n"
    # The reader must remove color after the real GitHub timestamp.
    body = "\n".join(
        "2026-10-24T12:00:00Z \x1b[31m" + line + "\x1b[0m" for line in body.splitlines()
    )
    causes, warnings = _extract_body(tmp_path, body + "\n" + EXIT)
    assert warnings == []
    cause = causes[0]
    assert cause["kind"] == "pytest_failure"
    assert token not in json.dumps(cause)
    assert "TOKEN=[REDACTED]" in cause["message"]
    assert len(cause["message"]) <= 500
    context = cause["occurrences"][0]["context"]
    assert len(context) == 3
    assert context[0]["kind"] == "frame"
    assert context[0]["message"] == "tests/test_example.py:17"
    assert "[REDACTED]" in context[1]["message"]
    assert "\x1b" not in json.dumps(cause)


@pytest.mark.parametrize(
    "blank_lines, expected",
    [(0, "structured_diagnostic"), (2, "structured_diagnostic"), (3, "exit_code")],
)
def test_explicit_rejection_needs_a_nearby_process_failure(tmp_path, blank_lines, expected):
    causes, _ = _extract_body(
        tmp_path, "Dependency routes rejected: unreviewed input\n" + "\n" * blank_lines + EXIT
    )
    assert causes[0]["kind"] == expected


@pytest.mark.parametrize(
    "body, kind",
    [
        ("gpg: verify signatures failed: No such file or directory\n", "missing_file"),
        ("molsysmt >=0.23.0 * does not exist (missing channel)\n", "exit_code"),
        ("curl: (0) successful download\n", "exit_code"),
        ("curl: (not-a-code) unknown text\n", "exit_code"),
    ],
)
def test_specific_diagnostics_require_their_failure_evidence(tmp_path, body, kind):
    causes, _ = _extract_body(tmp_path, body + EXIT)
    assert causes[0]["kind"] == kind


@pytest.mark.parametrize("distance, context_count", [(128, 1), (129, 0)])
def test_later_download_context_is_bounded_and_keeps_its_source(tmp_path, distance, context_count):
    causes, _ = _extract_body(
        tmp_path,
        "curl: (35) TLS handshake failed\n"
        + "\n" * (distance - 1)
        + "gpg: cannot open signature: No such file or directory\n"
        + EXIT,
    )
    occurrence = causes[0]["occurrences"][0]
    assert occurrence["line"] == 1
    context = occurrence.get("context", [])
    assert len(context) == context_count
    if context:
        assert context[0]["line"] == distance + 1
        assert context[0]["member"] == occurrence["member"]


@pytest.mark.parametrize("case", CASES, ids=lambda c: str(c["run_id"]))
def test_failed_tests_and_later_diagnostics_have_separate_original_locators(tmp_path, case):
    causes, _ = extract_causes(
        archive_for_case(tmp_path, case), [j for j in case["jobs"] if j["conclusion"] == "failure"]
    )
    if case["issue"] == 64:
        assert all("context" not in o for c in causes for o in c["occurrences"])
        return
    for cause in causes:
        for occurrence in cause["occurrences"]:
            context = occurrence["context"]
            assert len(context) <= 3
            assert all(
                item["line"] > occurrence["line"] for item in context if item["kind"] != "frame"
            )
            assert all(item["member"] == occurrence["member"] for item in context)
            if case["issue"] in (59, 61):
                assert context[0]["kind"] == "later diagnostic"
                assert (
                    "No such file or directory" in context[0]["message"]
                    or "no such file or directory" in context[0]["message"]
                )
            else:
                assert context[0]["kind"] == "frame"
                assert context[0]["line"] < occurrence["line"]
                assert all(
                    item["kind"] == "test" and ".py::" in item["message"] for item in context[1:]
                )


def test_optional_published_context_is_bounded_and_malformed_entries_are_ignored(tmp_path):
    report = report_for_case(tmp_path, CASES[0], "generic")
    occurrence = report["causes"][0]["occurrences"][0]
    token = "ghp_" + "b" * 40
    occurrence["context"] = [
        None,
        {"kind": "unrecognized"},
        {
            "kind": "test",
            "message": f"TOKEN={token} " + "x\x1b\n" * 1000,
            "member": "log.txt",
            "line": 2,
        },
    ] * 1000
    for renderer in (render_llm, render_human):
        output = renderer(report)
        assert "\x1b" not in output
        assert "\\u001b" in output
        assert token not in output
        assert "TOKEN=[REDACTED]" in output
        assert len(output) < 16_000


@pytest.mark.parametrize(
    "lines, expected", [(1, "exit_code"), (3, "exit_code"), (4, "pytest_failure")]
)
def test_truncated_pytest_groups_retain_only_observed_evidence(tmp_path, lines, expected):
    causes, _ = _extract_body(tmp_path, "\n".join(SUMMARY.splitlines()[:lines]) + "\n" + EXIT)
    assert causes[0]["kind"] == expected
    context = causes[0]["occurrences"][0].get("context", [])
    assert [item["kind"] for item in context] == (["frame"] if expected == "pytest_failure" else [])


def test_unknown_summary_fields_do_not_replace_known_exception_and_location(tmp_path):
    body = SUMMARY.replace(
        "[1] AssertionError | 1 test | call", "[1] AssertionError | 1 test | call | future=unknown"
    )
    body = body.replace("tests:\n", "new-field: unrelated data\ntests:\n")
    causes, _ = _extract_body(tmp_path, body + EXIT)
    assert causes[0]["kind"] == "pytest_failure"
    assert "| at tests/test_example.py:17" in causes[0]["message"]
