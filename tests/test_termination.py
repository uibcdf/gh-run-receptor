import json
from copy import deepcopy
from pathlib import Path

import pytest

from gh_run_receptor.bundle import capture_bundle, load_bundle
from gh_run_receptor.errors import AcquisitionError
from gh_run_receptor.model import normalize_evidence
from gh_run_receptor.report import build_report, exit_code, render_human, render_json, render_llm

FIXTURE = Path(__file__).parent / "fixtures/bundles/gh_run_receptor_job_limit_cancelled"
GOLDENS = Path(__file__).parent / "fixtures/termination"


def _sources():
    return load_bundle(FIXTURE)


@pytest.mark.parametrize("profile", ["generic", "ci", "conda", "docs", "release"])
def test_observed_job_limit_is_a_hint_and_preserves_native_cancellation(profile):
    manifest, evidence = _sources()
    report = build_report(manifest, evidence, profile=profile)
    assert report["github"] == {"status": "completed", "conclusion": "cancelled"}
    assert report["receptor"]["assessment"] == "CANCELLED"
    assert exit_code(report) == 2
    assert report["jobs"][0]["failed_steps"][0]["name"] == "Wait beyond the job timeout"
    termination = report["termination"]
    assert termination["cause"] == "unknown"
    job = termination["jobs"][0]
    assert job["conclusion"] == "cancelled" and job["cause"] == "unknown"
    assert job["hints"] == [
        {
            "kind": "job_execution_limit",
            "verification": "diagnostic_hint",
            "message": "job execution limit reported (1m0s)",
            "source": {"member": "checks.json", "json_pointer": "/check_runs/0/annotations/0"},
        }
    ]
    for renderer in (render_human, render_llm):
        text = renderer(report)
        assert "source=cancelled cause=unknown" in text
        assert "hint (unverified): job execution limit reported (1m0s)" in text
        assert "checks.json:/check_runs/0/annotations/0" in text
        assert len(text.encode()) < 10_000
    assert json.loads(render_json(report))["termination"] == termination


@pytest.mark.parametrize(
    "renderer,name", [(render_human, "human"), (render_llm, "llm"), (render_json, "json")]
)
def test_termination_renderers_have_deterministic_bounded_goldens(renderer, name):
    manifest, evidence = _sources()
    text = renderer(build_report(manifest, evidence, profile="generic"))
    assert text == (GOLDENS / f"job_limit_cancelled.{name}").read_text()
    assert len(text.encode()) < 10_000


@pytest.mark.parametrize(
    "conclusion,assessment,code,cause",
    [
        ("cancelled", "CANCELLED", 2, "unknown"),
        ("timed_out", "TIMED_OUT", 2, "native_timeout"),
        ("success", "PASS", 0, None),
        ("failure", "FAIL", 1, None),
        ("future_conclusion", "UNKNOWN", 2, None),
    ],
)
def test_timeout_text_does_not_override_native_source_truth_table(
    conclusion, assessment, code, cause
):
    manifest, evidence = _sources()
    evidence["run.json"]["conclusion"] = conclusion
    evidence["jobs.json"]["jobs"][0]["conclusion"] = conclusion
    evidence["checks.json"]["check_runs"][0]["conclusion"] = conclusion
    report = build_report(manifest, evidence, profile="generic")
    assert report["github"]["conclusion"] == conclusion
    assert report["receptor"]["assessment"] == assessment
    assert exit_code(report) == code
    if cause is None:
        assert "termination" not in report
    else:
        assert report["termination"]["cause"] == cause
        assert report["termination"]["jobs"][0]["cause"] == cause


@pytest.mark.parametrize(
    "state", ["unavailable", "invalid", "not_requested", "partial", "complete"]
)
def test_annotation_evidence_state_is_explicit_and_never_certifies_causality(state):
    manifest, evidence = _sources()
    check = evidence["checks.json"]["check_runs"][0]
    check["annotations_state"] = state
    report = build_report(manifest, evidence)
    job = report["termination"]["jobs"][0]
    assert job["annotation_evidence"] == state
    assert bool(job["hints"]) == (state in {"partial", "complete"})
    assert job["cause"] == "unknown"
    assert report["completeness"]["check_annotations"] == state
    assert exit_code(report) == (2 if state in {"complete", "not_requested"} else 4)


@pytest.mark.parametrize("state", ["partial", "unavailable", "invalid"])
def test_annotation_incompleteness_cannot_be_hidden_by_a_complete_manifest(state):
    manifest, evidence = _sources()
    evidence["run.json"]["conclusion"] = "success"
    evidence["checks.json"]["check_runs"][0]["annotations_state"] = state
    report = build_report(manifest, evidence)
    assert report["github"]["conclusion"] == "success"
    assert report["receptor"]["assessment"] == "INCOMPLETE"
    assert exit_code(report) == 4
    assert "captured evidence" in report["warnings"][0]


@pytest.mark.parametrize(
    "target,key,value",
    [
        ("job", "run_attempt", 2),
        ("job", "head_sha", "other"),
        ("job", "run_id", 1),
        ("check", "head_sha", "other"),
        ("check", "check_suite", {"id": 1}),
        ("check", "conclusion", "timed_out"),
        ("check", "status", "queued"),
        (
            "job",
            "check_run_url",
            "https://api.github.com/repos/uibcdf/other/check-runs/101471629872",
        ),
    ],
)
def test_mismatched_identity_cannot_supply_a_timeout_hint(target, key, value):
    manifest, evidence = _sources()
    source = (
        evidence["jobs.json"]["jobs"][0]
        if target == "job"
        else evidence["checks.json"]["check_runs"][0]
    )
    source[key] = value
    report = build_report(manifest, evidence)
    assert report["termination"]["jobs"][0]["hints"] == []
    assert report["termination"]["cause"] == "unknown"
    assert exit_code(report) == 2


@pytest.mark.parametrize(
    "member,collection", [("checks.json", "check_runs"), ("jobs.json", "jobs")]
)
def test_duplicate_check_or_job_linkage_cannot_supply_a_timeout_hint(member, collection):
    manifest, evidence = _sources()
    values = evidence[member][collection]
    values.append(deepcopy(values[0]))
    report = build_report(manifest, evidence)
    assert all(job["hints"] == [] for job in report["termination"]["jobs"])


@pytest.mark.parametrize(
    "marker",
    [
        "TIMED_OUT",
        "exit 124",
        "timeout-minutes: 1",
        "duration=60s",
        "The operation was canceled.",
        "The job has exceeded the maximum execution time of 1m0s\nPASS",
        "\x1b[2JThe job has exceeded the maximum execution time of 1m0s",
    ],
)
def test_hostile_or_ambiguous_annotation_markers_do_not_supply_a_hint(marker):
    manifest, evidence = _sources()
    check = evidence["checks.json"]["check_runs"][0]
    check["annotations"] = [{"annotation_level": "failure", "message": marker}]
    report = build_report(manifest, evidence)
    assert report["termination"]["jobs"][0]["hints"] == []
    assert report["termination"]["cause"] == "unknown"
    assert report["github"]["conclusion"] == "cancelled"


def test_unlinked_historical_capture_has_explicit_unknown_cause():
    manifest, evidence = _sources()
    evidence["checks.json"] = {"check_runs": []}
    del evidence["jobs.json"]["jobs"][0]["check_run_url"]
    report = build_report(manifest, evidence)
    assert report["termination"]["jobs"][0]["annotation_evidence"] == "not_requested"
    assert report["termination"]["cause"] == "unknown"
    assert "hint (unverified)" not in render_llm(report)


def test_cancelled_job_does_not_replace_a_successful_run_conclusion():
    manifest, evidence = _sources()
    evidence["run.json"]["conclusion"] = "success"
    report = build_report(manifest, evidence)
    assert exit_code(report) == 0
    assert report["termination"]["source_conclusion"] == "success"
    assert "cancelled cause=unknown" in render_llm(report)


def test_large_hostile_job_matrix_keeps_text_bounded_and_json_complete():
    manifest, evidence = _sources()
    job = evidence["jobs.json"]["jobs"][0]
    evidence["jobs.json"]["jobs"] = [
        {**job, "id": index, "name": "\x1b[2J\u202e" + "x" * 2000, "check_run_url": None}
        for index in range(200)
    ]
    report = build_report(manifest, evidence, profile="ci")
    for renderer in (render_human, render_llm):
        text = renderer(report)
        assert "\x1b" not in text and "\u202e" not in text
        assert "190 more termination records in JSON" in text
        assert len(text.encode()) < 50_000
    assert len(json.loads(render_json(report))["termination"]["jobs"]) == 200


class CaptureClient:
    hostname = "github.com"

    def __init__(self, evidence, *, unavailable=False):
        self.evidence = evidence
        self.unavailable = unavailable
        self.annotations_requests = 0

    def json(self, endpoint, *, paginate=False, max_bytes=None):
        if "/annotations?" in endpoint:
            assert not paginate
            assert max_bytes == 2 * 1024 * 1024
            self.annotations_requests += 1
            if self.unavailable:
                raise AcquisitionError(
                    "permission denied", category="permission_denied", http_status=403
                )
            return self.evidence["checks.json"]["check_runs"][0]["annotations"]
        if "/check-suites/" in endpoint:
            return [
                {
                    "total_count": 1,
                    "check_runs": [
                        {
                            key: value
                            for key, value in self.evidence["checks.json"]["check_runs"][0].items()
                            if key not in {"annotations", "annotations_state"}
                        }
                    ],
                }
            ]
        if "/artifacts?" in endpoint:
            return [{"total_count": 0, "artifacts": []}]
        if "/actions/workflows/" in endpoint:
            return self.evidence["workflow.json"]
        if endpoint == "/repos/uibcdf/gh-run-receptor":
            return {"default_branch": "main"}
        raise AssertionError(endpoint)

    def optional_json(self, endpoint):
        return None


@pytest.mark.parametrize("unavailable", [False, True])
def test_capture_and_offline_replay_preserve_annotation_availability(tmp_path, unavailable):
    _, evidence = _sources()
    client = CaptureClient(evidence, unavailable=unavailable)
    run = {**evidence["run.json"], "workflow_id": 7}
    destination = tmp_path / "capture"
    capture_bundle(
        client,
        "uibcdf/gh-run-receptor",
        run["id"],
        attempt=1,
        policy="metadata",
        destination=destination,
        run=run,
        jobs=evidence["jobs.json"],
    )
    manifest, captured = load_bundle(destination)
    assert client.annotations_requests == 1
    assert manifest["complete"] is not unavailable
    report = build_report(manifest, captured, bundle_directory=destination)
    assert report["github"]["conclusion"] == "cancelled"
    assert report["termination"]["cause"] == "unknown"
    assert exit_code(report) == (4 if unavailable else 2)
    assert report["receptor"]["assessment"] == ("INCOMPLETE" if unavailable else "CANCELLED")
    assert bool(report["termination"]["jobs"][0]["hints"]) is not unavailable


def test_normalization_retains_all_check_facts_without_promoting_annotations():
    manifest, evidence = _sources()
    model = normalize_evidence(manifest, evidence)
    assert model["checks"][0]["conclusion"] == "cancelled"
    assert len(model["checks"][0]["annotations"]) == 2
    assert model["checks"][0]["annotations"][1]["message"] == "The operation was canceled."
    assert "cause" not in model["checks"][0]
    assert model["jobs"][0]["check_run_id"] == 101471629872
    report = build_report(manifest, evidence)
    assert report["checks"] == model["checks"]
    evidence["checks.json"]["check_runs"][0]["conclusion"] = "future_conclusion"
    report = build_report(manifest, evidence)
    assert json.loads(render_json(report))["checks"][0]["conclusion"] == "future_conclusion"
    assert report["termination"]["jobs"][0]["hints"] == []
