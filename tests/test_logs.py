import zipfile

from gh_run_receptor.logs import MAX_CAUSE_CHARACTERS, extract_causes


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
