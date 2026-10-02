from copy import deepcopy

import pytest

from gh_run_receptor.checks import (
    capture_termination_annotations,
    job_check_id,
    normalize_checks,
    validate_annotations,
)
from gh_run_receptor.errors import AcquisitionError, BundleError


def _sources(conclusion="cancelled"):
    run = {"id": 42, "run_attempt": 2, "head_sha": "abc", "check_suite_id": 7}
    jobs = {
        "jobs": [
            {
                "id": 20,
                "run_id": 42,
                "run_attempt": 2,
                "head_sha": "abc",
                "check_run_url": "https://api.github.com/repos/uibcdf/example/check-runs/101",
                "status": "completed",
                "conclusion": conclusion,
            }
        ]
    }
    checks = {
        "check_runs": [
            {
                "id": 101,
                "head_sha": "abc",
                "check_suite": {"id": 7},
                "status": "completed",
                "conclusion": conclusion,
                "output": {"annotations_count": 1},
            }
        ]
    }
    return run, jobs, checks


class AnnotationClient:
    hostname = "github.com"

    def __init__(self, response=None):
        self.endpoints = []
        self.response = (
            response
            if response is not None
            else [
                {
                    "annotation_level": "failure",
                    "message": "The job has exceeded the maximum execution time of 1m0s",
                    "future_field": {"preserved": True},
                }
            ]
        )

    def json(self, endpoint, *, max_bytes):
        assert max_bytes == 2 * 1024 * 1024
        self.endpoints.append(endpoint)
        if isinstance(self.response, Exception):
            raise self.response
        return deepcopy(self.response)


@pytest.mark.parametrize(
    "conclusion,requested",
    [
        ("cancelled", True),
        ("timed_out", True),
        ("failure", False),
        ("success", False),
        ("future_conclusion", False),
        (None, False),
    ],
)
def test_annotation_request_selection_truth_table(conclusion, requested):
    run, jobs, checks = _sources(conclusion)
    client = AnnotationClient()
    assert capture_termination_annotations(client, "uibcdf/example", run, jobs, checks) == []
    assert len(client.endpoints) == int(requested)
    if requested:
        assert client.endpoints == ["/repos/uibcdf/example/check-runs/101/annotations?per_page=100"]
        assert checks["check_runs"][0]["annotations_state"] == "complete"
        assert checks["check_runs"][0]["annotations"][0]["future_field"] == {"preserved": True}


@pytest.mark.parametrize(
    "target,key,value",
    [
        ("job", "run_attempt", 1),
        ("job", "run_id", 43),
        ("job", "head_sha", "other"),
        ("check", "head_sha", "other"),
        ("check", "check_suite", {"id": 8}),
        ("check", "conclusion", "success"),
        ("check", "status", "in_progress"),
        ("run", "head_sha", None),
        ("run", "check_suite_id", None),
    ],
)
def test_conflicting_check_identity_is_not_acquired(target, key, value):
    run, jobs, checks = _sources()
    source = {"job": jobs["jobs"][0], "check": checks["check_runs"][0], "run": run}[target]
    source[key] = value
    client = AnnotationClient()
    warnings = capture_termination_annotations(client, "uibcdf/example", run, jobs, checks)
    assert warnings and "invalid identity" in warnings[0]
    assert client.endpoints == []
    assert checks["check_runs"][0]["annotations_state"] == "invalid"


@pytest.mark.parametrize("duplicate", ["job", "check"])
def test_ambiguous_linkage_is_not_acquired(duplicate):
    run, jobs, checks = _sources()
    collection = jobs["jobs"] if duplicate == "job" else checks["check_runs"]
    collection.append(deepcopy(collection[0]))
    client = AnnotationClient()
    assert capture_termination_annotations(client, "uibcdf/example", run, jobs, checks)
    assert client.endpoints == []


@pytest.mark.parametrize("suffix", ["101?x=1", "101/annotations", "../101", "0", "١٠١", "1" * 21])
def test_check_link_rejects_noncanonical_identifiers(suffix):
    job = {"check_run_url": f"https://api.github.com/repos/uibcdf/example/check-runs/{suffix}"}
    assert job_check_id(job, "uibcdf/example", "github.com") is None


def test_check_link_never_follows_another_repository_or_host():
    job = {"check_run_url": "https://api.github.com/repos/uibcdf/other/check-runs/101"}
    assert job_check_id(job, "uibcdf/example", "github.com") is None
    job["check_run_url"] = "https://hostile.invalid/repos/uibcdf/example/check-runs/101"
    assert job_check_id(job, "uibcdf/example", "github.com") is None


@pytest.mark.parametrize(
    "response,state",
    [
        ([], "partial"),
        (AcquisitionError("HTTP 403"), "unavailable"),
        ({"message": "wrong shape"}, "invalid"),
        ([{"message": 1, "annotation_level": "failure"}], "invalid"),
        ([{"message": "x" * 4097, "annotation_level": "failure"}], "invalid"),
    ],
)
def test_unavailable_malformed_and_truncated_annotations_are_explicit(response, state):
    run, jobs, checks = _sources()
    assert capture_termination_annotations(
        AnnotationClient(response), "uibcdf/example", run, jobs, checks
    )
    assert checks["check_runs"][0]["annotations_state"] == state


def test_annotation_count_limit_marks_truncation_and_never_paginates():
    run, jobs, checks = _sources()
    checks["check_runs"][0]["output"]["annotations_count"] = 101
    client = AnnotationClient([{"message": "x", "annotation_level": "notice"}] * 100)
    assert capture_termination_annotations(client, "uibcdf/example", run, jobs, checks)
    assert len(client.endpoints) == 1
    assert len(checks["check_runs"][0]["annotations"]) == 100
    assert checks["check_runs"][0]["annotations_state"] == "partial"


def test_annotation_acquisition_has_a_fifty_check_budget():
    run, jobs, checks = _sources()
    job, check = jobs["jobs"][0], checks["check_runs"][0]
    jobs["jobs"] = []
    checks["check_runs"] = []
    for index in range(51):
        jobs["jobs"].append(
            {
                **job,
                "id": index,
                "check_run_url": (
                    f"https://api.github.com/repos/uibcdf/example/check-runs/{index + 101}"
                ),
            }
        )
        checks["check_runs"].append({**check, "id": index + 101})
    client = AnnotationClient()
    assert capture_termination_annotations(client, "uibcdf/example", run, jobs, checks)
    assert len(client.endpoints) == 50
    assert checks["check_runs"][-1]["annotations_state"] == "partial"


def test_empty_annotations_and_active_jobs_require_no_additional_request():
    run, jobs, checks = _sources()
    checks["check_runs"][0]["output"]["annotations_count"] = 0
    client = AnnotationClient()
    assert capture_termination_annotations(client, "uibcdf/example", run, jobs, checks) == []
    assert checks["check_runs"][0]["annotations"] == []
    jobs["jobs"][0]["status"] = "in_progress"
    checks["check_runs"][0]["output"]["annotations_count"] = 1
    assert capture_termination_annotations(client, "uibcdf/example", run, jobs, checks) == []
    assert client.endpoints == []


@pytest.mark.parametrize(
    "value",
    [
        None,
        {},
        [None],
        [{}],
        [{"message": "x"}],
        [{"message": "x", "annotation_level": 1}],
        [{"message": "x", "annotation_level": "failure"}] * 101,
    ],
)
def test_annotation_parser_rejects_malformed_shapes_and_size_overflow(value):
    with pytest.raises(BundleError):
        validate_annotations(value)


def test_annotation_parser_exact_boundaries_redaction_and_source_pointer():
    values = [{"message": "x" * 4096, "annotation_level": "future_level"}] * 100
    assert validate_annotations(values) is values
    check = {
        "annotations_state": "complete",
        "annotations": [
            {"message": "GH_TOKEN=secret " + "x" * 1000, "annotation_level": "failure"}
        ],
    }
    normalized = normalize_checks([check])[0]["annotations"][0]
    assert "secret" not in normalized["message"]
    assert len(normalized["message"]) <= 500
    assert normalized["source"] == {
        "member": "checks.json",
        "json_pointer": "/check_runs/0/annotations/0",
    }
    with pytest.raises(BundleError, match="evidence state"):
        normalize_checks([{**check, "annotations_state": "future_state"}])


def test_annotation_unknown_fields_cannot_bypass_the_byte_budget():
    import json

    from gh_run_receptor.checks import MAX_ANNOTATION_PAGE_BYTES

    value = [{"message": "x", "annotation_level": "failure", "future_field": ""}]
    overhead = len(json.dumps(value, separators=(",", ":")).encode())
    value[0]["future_field"] = "x" * (MAX_ANNOTATION_PAGE_BYTES - overhead)
    assert validate_annotations(value) is value
    value[0]["future_field"] += "x"
    with pytest.raises(BundleError, match="page-byte limit"):
        validate_annotations(value)
    with pytest.raises(BundleError, match="level"):
        validate_annotations([{"message": "x", "annotation_level": "x" * 65}])


@pytest.mark.parametrize("value", ["\ud800", float("nan")])
def test_invalid_json_text_or_unknown_field_values_are_rejected(value):
    with pytest.raises(BundleError, match="UTF-8 JSON"):
        validate_annotations([{"message": "x", "annotation_level": "failure", "future": value}])


@pytest.mark.parametrize("count", [None, -1, True, "1"])
def test_unusable_count_remains_explicitly_not_requested(count):
    run, jobs, checks = _sources()
    checks["check_runs"][0]["output"]["annotations_count"] = count
    client = AnnotationClient()
    assert capture_termination_annotations(client, "uibcdf/example", run, jobs, checks) == []
    assert client.endpoints == []
    assert checks["check_runs"][0]["annotations_state"] == "not_requested"
