import zipfile
from pathlib import Path

import pytest

from gh_run_receptor.logs import MAX_CAUSE_CHARACTERS, extract_causes

_PUBLIC_EXCERPTS = Path(__file__).parent / "fixtures" / "logs"


def _jobs():
    return [
        {"id": 1, "name": "osx-64 · Rattler · LTO true"},
        {"id": 2, "name": "osx-arm64 · Rattler · LTO true"},
    ]


def test_extract_causes_groups_normalized_command_missing(tmp_path):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(
            "2_osx-64 · Rattler · LTO true.txt",
            "2026-09-04T10:36:02Z /Users/runner/work/_temp/aaaa-bbbb.sh: "
            "line 2: mapfile: command not found\n"
            "2026-09-04T10:36:02Z ##[error]Process completed with exit code 127.\n",
        )
        zipped.writestr(
            "4_osx-arm64 · Rattler · LTO true.txt",
            "2026-09-04T10:39:45Z /Users/runner/work/_temp/cccc-dddd.sh: "
            "line 2: mapfile: command not found\n"
            "2026-09-04T10:39:45Z ##[error]Process completed with exit code 127.\n",
        )

    causes, warnings = extract_causes(archive, _jobs())

    assert warnings == []
    assert len(causes) == 1
    assert causes[0]["kind"] == "command_not_found"
    assert causes[0]["message"] == "$RUNNER_TEMP/script: line 2: mapfile: command not found"
    assert len(causes[0]["occurrences"]) == 2


def test_extract_causes_reads_past_a_bounded_huge_line(tmp_path):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(
            "2_osx-64 · Rattler · LTO true.txt",
            ("x" * 20_000) + "\nmapfile: command not found\n",
        )

    causes, _ = extract_causes(archive, _jobs()[:1])

    assert causes[0]["message"] == "mapfile: command not found"
    assert causes[0]["occurrences"][0]["line"] == 2


def test_extract_causes_rejects_archive_traversal(tmp_path):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("../2_osx-64 · Rattler · LTO true.txt", "mapfile: command not found\n")

    causes, warnings = extract_causes(archive, _jobs()[:1])

    assert causes == []
    assert warnings == [
        "log archive contains an unsafe member: ../2_osx-64 · Rattler · LTO true.txt"
    ]


def test_extract_causes_preserves_adjacent_structured_diagnostic(tmp_path):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(
            "2_osx-64 · Rattler · LTO true.txt",
            "Zenodo archive: ABSENT — 0.18.0\n##[error]Process completed with exit code 2.\n",
        )

    causes, warnings = extract_causes(archive, _jobs()[:1])

    assert warnings == []
    assert causes[0]["kind"] == "structured_diagnostic"
    assert causes[0]["message"] == "Zenodo archive: ABSENT — 0.18.0"
    assert causes[0]["occurrences"][0]["line"] == 1


def test_adjacent_diagnostic_is_conservative_redacted_and_bounded(tmp_path):
    token = "ghp_" + "a" * 40
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(
            "2_osx-64 · Rattler · LTO true.txt",
            f"Build gate: FAIL token={token} PASSWORD=hunter2 {'x' * 1_000}\n"
            "##[error]Process completed with exit code 1.\n",
        )

    causes, _ = extract_causes(archive, _jobs()[:1])

    assert causes[0]["kind"] == "structured_diagnostic"
    assert token not in causes[0]["message"]
    assert "PASSWORD=[REDACTED]" in causes[0]["message"]
    assert len(causes[0]["message"]) == MAX_CAUSE_CHARACTERS


def test_arbitrary_adjacent_output_does_not_replace_process_exit(tmp_path):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(
            "2_osx-64 · Rattler · LTO true.txt",
            "Uploading ordinary output\n##[error]Process completed with exit code 1.\n",
        )

    causes, _ = extract_causes(archive, _jobs()[:1])

    assert causes[0]["kind"] == "exit_code"


@pytest.mark.parametrize("verdict", ["PASS", "pass", "Pass"])
def test_positive_verdict_before_silent_failure_keeps_process_exit(tmp_path, verdict):
    body = (_PUBLIC_EXCERPTS / "molsysviewer_36920527376_silent_failure.txt").read_text()
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("2_osx-64 · Rattler · LTO true.txt", body.replace("PASS", verdict))

    causes, warnings = extract_causes(archive, _jobs()[:1])

    assert warnings == []
    assert causes[0]["kind"] == "exit_code"
    assert causes[0]["message"] == "Process completed with exit code 1."
    assert causes[0]["occurrences"][0]["line"] == 2


def test_positive_verdict_without_failure_diagnostic_remains_unknown(tmp_path):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("2_osx-64 · Rattler · LTO true.txt", "Build gate: PASS\n")

    causes, warnings = extract_causes(archive, _jobs()[:1])

    assert causes == []
    assert warnings == ["no causal line found for failed job: osx-64 · Rattler · LTO true"]


def test_explicit_error_outranks_adjacent_structured_diagnostic(tmp_path):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(
            "2_osx-64 · Rattler · LTO true.txt",
            "Error: package index is corrupt\n"
            "Build gate: FAIL\n"
            "##[error]Process completed with exit code 1.\n",
        )

    causes, _ = extract_causes(archive, _jobs()[:1])

    assert causes[0]["kind"] == "error"
    assert causes[0]["message"] == "Error: package index is corrupt"


def test_plain_pytest_failure_outranks_runner_epilogue(tmp_path):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(
            "2_osx-64 · Rattler · LTO true.txt",
            "FAILED tests/test_pdf.py::test_pdf_compilation - AssertionError: assert False\n"
            " +  where False = exists()\n"
            " =================== 1 failed, 210 passed in 0.87s ===================\n"
            "##[error]Process completed with exit code 1.\n",
        )

    causes, warnings = extract_causes(archive, _jobs()[:1])

    assert warnings == []
    assert causes[0]["kind"] == "pytest_test"
    assert causes[0]["message"] == "pytest failed: tests/test_pdf.py::test_pdf_compilation"
    assert causes[0]["occurrences"][0]["line"] == 1


def test_pytest_receptor_failure_names_test_from_bounded_rerun(tmp_path):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(
            "2_osx-64 · Rattler · LTO true.txt",
            "FAIL exit=1 | 1 failed, 463 passed | 6.00s | 1 root cause\n"
            "\n[1] AssertionError | 1 test | call\n"
            "    tests/test_core.py:196\n"
            "    assert actual <= expected\n"
            "2026-09-21T08:51:33.7311655Z     rerun: pytest "
            "tests\\test_core.py::test_frame_time -q\n"
            "##[error]Process completed with exit code 1.\n",
        )

    causes, warnings = extract_causes(archive, _jobs()[:1])

    assert warnings == []
    assert causes[0]["kind"] == "pytest_test"
    assert causes[0]["message"] == "pytest failed: tests/test_core.py::test_frame_time"
    assert causes[0]["occurrences"][0]["line"] == 6


def test_pytest_receptor_rerun_without_failure_verdict_is_not_cause(tmp_path):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(
            "2_osx-64 · Rattler · LTO true.txt",
            "    rerun: pytest tests/test_core.py::test_frame_time -q\n"
            "##[error]Process completed with exit code 1.\n",
        )

    causes, _ = extract_causes(archive, _jobs()[:1])

    assert causes[0]["kind"] == "exit_code"


def test_pytest_receptor_rerun_outside_bounded_window_is_not_cause(tmp_path):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(
            "2_osx-64 · Rattler · LTO true.txt",
            "FAIL exit=1 | 1 failed | 1 root cause\n"
            + "ordinary output\n" * 129
            + "    rerun: pytest tests/test_core.py::test_frame_time -q\n"
            + "##[error]Process completed with exit code 1.\n",
        )

    causes, _ = extract_causes(archive, _jobs()[:1])

    assert causes[0]["kind"] == "exit_code"


def test_pytest_failure_nodeid_is_redacted_and_bounded(tmp_path):
    token = "ghp_" + "a" * 40
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(
            "2_osx-64 · Rattler · LTO true.txt",
            f"FAILED tests/test_secret.py::test_key[{token}] - AssertionError\n"
            "##[error]Process completed with exit code 1.\n",
        )

    causes, _ = extract_causes(archive, _jobs()[:1])

    assert causes[0]["kind"] == "pytest_test"
    assert token not in causes[0]["message"]
    assert "[REDACTED]" in causes[0]["message"]
    assert len(causes[0]["message"]) <= MAX_CAUSE_CHARACTERS


def test_public_conda_failure_excerpts_prefer_primary_causes(tmp_path):
    archive = tmp_path / "logs.zip"
    jobs = []
    with zipfile.ZipFile(archive, "w") as zipped:
        for index, (platform, count, excerpt) in enumerate(
            (("linux-64", 9, "python"), ("linux-aarch64", 3, "arm"), ("win-64", 3, "win"))
        ):
            body = (_PUBLIC_EXCERPTS / f"molsysmt_35499866604_{excerpt}.txt").read_text()
            for number in range(count):
                job_id = 100 + index * 10 + number
                name = f"{platform} · Python 3.{11 + number % 3} · batch {number}"
                jobs.append({"id": job_id, "name": name})
                zipped.writestr(f"{job_id}_{name}.txt", body)

    causes, warnings = extract_causes(archive, jobs)

    assert warnings == []
    assert len(causes) == 3
    by_kind = {cause["kind"]: cause for cause in causes}
    assert (
        "molsysviewer version is 0.23.1+0.g736e8274.dirty" in by_kind["python_exception"]["message"]
    )
    assert "validate_conda_staging.py:75" in by_kind["python_exception"]["message"]
    assert len(by_kind["python_exception"]["occurrences"]) == 9
    solver = [cause for cause in causes if cause["kind"] == "conda_solver"]
    assert len(solver) == 2
    assert any(
        "argdigest >=0.12.1" in cause["message"] and "depdigest" in cause["message"]
        for cause in solver
    )
    assert any("pyunitwizard >=0.24.0" in cause["message"] for cause in solver)
    assert sorted(len(cause["occurrences"]) for cause in solver) == [3, 3]
    assert all(len(cause["message"]) <= MAX_CAUSE_CHARACTERS for cause in causes)


def test_solver_package_line_without_failure_block_keeps_generic_cause(tmp_path):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(
            "2_osx-64 · Rattler · LTO true.txt",
            "argdigest >=0.12.1 *, which does not exist (example text)\n"
            "##[error]Process completed with exit code 1.\n",
        )

    causes, _ = extract_causes(archive, _jobs()[:1])

    assert causes[0]["kind"] == "exit_code"


def test_python_exception_without_traceback_frame_keeps_generic_cause(tmp_path):
    archive = tmp_path / "logs.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(
            "2_osx-64 · Rattler · LTO true.txt",
            "Traceback (most recent call last):\n"
            "RuntimeError: copied note without a source frame\n"
            "##[error]Process completed with exit code 1.\n",
        )

    causes, _ = extract_causes(archive, _jobs()[:1])

    assert causes[0]["kind"] == "exit_code"
