import hashlib
import json
import zipfile

import pytest

from devtools.scripts.benchmark_capture_policies import BenchmarkError, benchmark, main


def _member(path, name, value):
    data = (json.dumps(value, sort_keys=True) + "\n").encode()
    (path / name).write_bytes(data)
    return {
        "path": name,
        "kind": f"test.{name}",
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "complete": True,
    }


def _bundle(
    path,
    *,
    run_id,
    policy,
    conclusion,
    logs=False,
    unavailable=False,
):
    path.mkdir(parents=True)
    status = "completed"
    failed = conclusion == "failure"
    values = {
        "run.json": {
            "id": run_id,
            "run_attempt": 1,
            "status": status,
            "conclusion": conclusion,
            "head_sha": "abc",
        },
        "workflow.json": {"path": ".github/workflows/ci.yml"},
        "jobs.json": {
            "total_count": 1,
            "jobs": [
                {
                    "id": 10,
                    "name": "test",
                    "status": "completed",
                    "conclusion": conclusion,
                    "steps": [
                        {
                            "number": 1,
                            "name": "Test",
                            "status": "completed",
                            "conclusion": conclusion,
                        }
                    ],
                }
            ],
        },
        "checks.json": {"total_count": 0, "check_runs": []},
        "artifacts.json": {"total_count": 0, "artifacts": []},
    }
    members = [_member(path, name, value) for name, value in values.items()]
    if logs:
        log_path = path / "logs.zip"
        with zipfile.ZipFile(log_path, "w") as archive:
            message = "Error: test failed\n" if failed else "tests passed\n"
            archive.writestr("1_test.txt", message)
        data = log_path.read_bytes()
        members.append(
            {
                "path": "logs.zip",
                "kind": "github.logs",
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "complete": True,
            }
        )
    warnings = ["logs unavailable: GitHub returned HTTP 410"] if unavailable else []
    manifest = {
        "schema": "gh-run-receptor.bundle@1",
        "repository": "uibcdf/example",
        "hostname": "github.com",
        "run_id": run_id,
        "run_attempt": 1,
        "head_sha": "abc",
        "api_version": "2022-11-28",
        "receptor_version": "test",
        "capture_policy": policy,
        "captured_at": "2026-09-17T12:00:00+00:00",
        "complete": not warnings,
        "members": members,
        "warnings": warnings,
    }
    (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_benchmark_measures_paired_savings_and_diagnostic_parity(tmp_path):
    _bundle(
        tmp_path / "success" / "adaptive",
        run_id=1,
        policy="adaptive",
        conclusion="success",
    )
    _bundle(
        tmp_path / "success" / "full",
        run_id=1,
        policy="full",
        conclusion="success",
        logs=True,
    )
    _bundle(
        tmp_path / "failure" / "adaptive",
        run_id=2,
        policy="adaptive",
        conclusion="failure",
        logs=True,
    )
    _bundle(
        tmp_path / "failure" / "full",
        run_id=2,
        policy="full",
        conclusion="failure",
        logs=True,
    )

    result = benchmark([tmp_path])

    assert result["captures"] == 4
    assert result["policy_mismatches"] == []
    assert result["policies"]["adaptive"]["expected_log_requests"] == 1
    assert result["policies"]["full"]["expected_log_requests"] == 2
    assert result["paired"]["captures"] == 2
    assert result["paired"]["successful"] == 1
    assert result["paired"]["terminal_non_success"] == 1
    assert result["paired"]["observed_bytes_saved"] > 0
    assert result["paired"]["missing_diagnoses"] == 0
    assert result["policies"]["adaptive"]["diagnosed_failed_jobs"] == 1


def test_benchmark_accepts_an_explicit_unavailable_log_request(tmp_path):
    _bundle(
        tmp_path / "adaptive",
        run_id=1,
        policy="adaptive",
        conclusion="failure",
        unavailable=True,
    )

    result = benchmark([tmp_path])

    assert result["policy_mismatches"] == []
    assert result["policies"]["adaptive"]["observed_log_requests"] == 1
    assert result["policies"]["adaptive"]["log_unavailable"] == 1


def test_benchmark_rejects_a_log_that_the_policy_did_not_request(tmp_path):
    _bundle(
        tmp_path / "adaptive",
        run_id=1,
        policy="adaptive",
        conclusion="success",
        logs=True,
    )

    result = benchmark([tmp_path])

    assert len(result["policy_mismatches"]) == 1
    assert "did not require" in result["policy_mismatches"][0]["reason"]


def test_benchmark_rejects_duplicate_source_policy_pairs(tmp_path):
    _bundle(
        tmp_path / "one",
        run_id=1,
        policy="adaptive",
        conclusion="success",
    )
    _bundle(
        tmp_path / "two",
        run_id=1,
        policy="adaptive",
        conclusion="success",
    )

    with pytest.raises(BenchmarkError, match="duplicate bundle identity and policy"):
        benchmark([tmp_path])


def test_cli_can_require_both_kinds_of_paired_capture(tmp_path):
    _bundle(
        tmp_path / "adaptive",
        run_id=1,
        policy="adaptive",
        conclusion="success",
    )

    assert main([str(tmp_path), "--require-paired-success"]) == 1
    assert main([str(tmp_path), "--format", "json"]) == 0
