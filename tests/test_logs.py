import zipfile

from gh_run_receptor.logs import extract_causes


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
