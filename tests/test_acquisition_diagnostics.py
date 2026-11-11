"""Original acquisition diagnostics remain visible before secondary failures (#81/#83)."""

import io
import json
import zipfile
from pathlib import Path

import pytest

from gh_run_receptor.logs import _job_occurrence, extract_causes, extract_job_causes
from gh_run_receptor.report import build_report, exit_code, render_human, render_json, render_llm

FIXTURES = Path(__file__).parent / "fixtures/logs"
CASES = json.loads((FIXTURES / "acquisition_failures.json").read_text())["cases"]


def _body(case):
    lines = [""] * case["lines"][-1]["line"]
    for item in case["lines"]:
        lines[item["line"] - 1] = item["text"]
    return ("\n".join(lines) + "\n").encode()


def _report(tmp_path, case, profile="ci"):
    job = case["job"]
    member = f"0_{job['name']}.txt"
    with zipfile.ZipFile(tmp_path / "logs.zip", "w") as z:
        z.writestr(member, _body(case))
    manifest = {
        **case["source"],
        "capture_policy": "full",
        "complete": True,
        "warnings": [],
        "members": [{"path": "logs.zip"}],
    }
    evidence = {
        "run.json": {"status": "completed", "conclusion": "failure"},
        "workflow.json": {"path": ".github/workflows/ci.yml"},
        "jobs.json": {"jobs": [job]},
        "checks.json": {"check_runs": []},
        "artifacts.json": {"artifacts": []},
    }
    return build_report(manifest, evidence, profile=profile, bundle_directory=tmp_path)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
def test_original_acquisition_failure_precedes_secondary_context_in_both_log_routes(tmp_path, case):
    report = _report(tmp_path, case)
    causes, warnings = extract_causes(tmp_path / "logs.zip", [case["job"]])
    plain = tmp_path / f"job-{case['job']['id']}.log"
    plain.write_bytes(_body(case))
    targeted, targeted_warnings = extract_job_causes(plain, case["job"])
    assert warnings == targeted_warnings == []
    assert report["causes"] == causes
    assert causes[0]["kind"] == targeted[0]["kind"] == case["expected_kind"]
    assert case["expected_identity"] in causes[0]["message"]
    for cause in (causes[0], targeted[0]):
        occurrence = cause["occurrences"][0]
        assert occurrence["job_id"] == case["job"]["id"]
        assert occurrence["line"] in {item["line"] for item in case["lines"]}
        assert any(c["kind"] == "later diagnostic" for c in occurrence["context"])
        assert all(c["line"] > occurrence["line"] for c in occurrence["context"])
        assert len(occurrence["context"]) <= 3


@pytest.mark.parametrize("profile", ["generic", "ci", "docs"])
@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
def test_acquisition_reports_preserve_native_failure_and_bounded_rendering(tmp_path, case, profile):
    report = _report(tmp_path, case, profile)
    assert report["github"] == {"status": "completed", "conclusion": "failure"}
    assert exit_code(report) == 1
    for render in (render_llm, render_human, render_json):
        text = render(report)
        assert case["expected_identity"] in text
        assert text == render(_report(tmp_path, case, profile))
        assert len(text.encode()) < (30_000 if render is render_json else 8_000)


@pytest.mark.parametrize(
    "body,kind",
    [
        ("##[error]No files were found with the provided path: evidence/", "github_error"),
        ("##[error]ENOENT: no such file or directory, lstat 'independent-file'", "missing_file"),
        ("##[error]Unexpected end of JSON input", "github_error"),
        ("Download error (0) successful", "exit_code"),
        ("Download error (not-a-code) unknown", "exit_code"),
        ("Download error (28)", "exit_code"),
        ("Unable to download artifact(s): Artifact not found for name:", "exit_code"),
        ("Downloaded artifact successfully", "exit_code"),
    ],
)
def test_independent_cleanup_and_malformed_acquisition_text_are_not_reclassified(body, kind):
    stream = io.BytesIO((body + "\n##[error]Process completed with exit code 1.\n").encode())
    occurrence = _job_occurrence(stream, {"id": 1, "name": "Tests"}, "job-1.log")
    assert occurrence["kind"] == kind
    assert "context" not in occurrence


@pytest.mark.parametrize("distance,count", [(128, 1), (129, 0)])
def test_acquisition_context_window_retains_original_locators(distance, count):
    body = (
        "Unable to download artifact(s): Artifact not found for name: wheel-42-2\n"
        + "\n" * (distance - 1)
        + "##[error]No files were found with the provided path: evidence/\n"
    )
    item = _job_occurrence(io.BytesIO(body.encode()), {"id": 1}, "job-1.log")
    assert item["kind"] == "artifact_download"
    assert item["line"] == 1
    assert len(item.get("context", [])) == count
    if count:
        assert item["context"][0]["line"] == distance + 1
        assert item["context"][0]["member"] == "job-1.log"


def test_acquisition_messages_are_redacted_bounded_and_cannot_forge_source_truth():
    token = "ghp_" + "x" * 40
    body = (
        f"\x1b[31mUnable to download artifact(s): Artifact not found for name: wheel-{token} "
        + "TOKEN=secret \u202e"
        + "x" * 20_000
        + "\x1b[0m\n"
        + "##[error]No files were found with the provided path: TOKEN=secret\n"
    )
    item = _job_occurrence(io.BytesIO(body.encode()), {"id": 1}, "job-1.log")
    assert item["kind"] == "artifact_download"
    assert token not in json.dumps(item)
    assert "TOKEN=secret" not in json.dumps(item)
    assert "[REDACTED]" in item["message"]
    assert len(item["message"]) <= 500
    assert len(item["context"][0]["message"]) <= 500


@pytest.mark.parametrize("distance,kind", [(128, "conda_download"), (129, "missing_file")])
def test_nested_conda_transport_needs_a_bounded_fatal_context(distance, kind):
    body = (
        "critical libmamba Multiple errors occurred:\n"
        + "\n" * (distance - 1)
        + "    Download error (28) Timeout was reached [https://example.invalid/index]\n"
        + "##[error]ENOENT: no such file or directory, lstat 'independent-file'\n"
    )
    item = _job_occurrence(io.BytesIO(body.encode()), {"id": 1}, "job-1.log")
    assert item["kind"] == kind


def test_recoverable_download_warning_does_not_hide_an_independent_filesystem_failure():
    body = (
        "warning libmamba Download error (28) Timeout was reached [https://example.invalid/index]\n"
        "Download retry succeeded\n"
        "##[error]ENOENT: no such file or directory, lstat 'independent-file'\n"
    )
    item = _job_occurrence(io.BytesIO(body.encode()), {"id": 1}, "job-1.log")
    assert item["kind"] == "missing_file"
    assert "independent-file" in item["message"]


@pytest.mark.parametrize(
    "status,conclusion,code",
    [
        ("completed", "failure", 1),
        ("completed", "success", 0),
        ("completed", "cancelled", 2),
        ("completed", "timed_out", 2),
        ("completed", "future-conclusion", 2),
        ("in_progress", None, 3),
        ("queued", None, 3),
    ],
)
def test_primary_acquisition_diagnostics_never_replace_workflow_source_state(
    tmp_path, status, conclusion, code
):
    case = CASES[-1]
    _report(tmp_path, case)
    manifest = {
        **case["source"],
        "capture_policy": "full",
        "complete": True,
        "members": [{"path": "logs.zip"}],
        "warnings": [],
    }
    evidence = {
        "run.json": {"status": status, "conclusion": conclusion},
        "workflow.json": {},
        "jobs.json": {"jobs": [case["job"]]},
        "checks.json": {"check_runs": []},
        "artifacts.json": {"artifacts": []},
    }
    report = build_report(manifest, evidence, bundle_directory=tmp_path, profile="ci")
    assert report["github"] == {"status": status, "conclusion": conclusion}
    assert report["causes"][0]["kind"] == "artifact_download"
    assert exit_code(report) == code


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
def test_acquisition_text_matches_reviewed_golden_reports(tmp_path, case):
    expected = json.loads((FIXTURES / "acquisition_failures_golden.json").read_text())[case["name"]]
    report = _report(tmp_path, case)
    assert render_llm(report) == expected["llm"]
    assert render_human(report) == expected["human"]
