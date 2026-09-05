import pytest

from gh_run_receptor.errors import AcquisitionError
from gh_run_receptor.watch import JobState, RunState, fetch_state, transitions, watch_run


def _state(status, job_status, conclusion=None, job_conclusion=None):
    return {
        "run": {"status": status, "conclusion": conclusion, "run_attempt": 1},
        "jobs": {
            "total_count": 1,
            "jobs": [
                {
                    "id": 7,
                    "name": "build (linux-64)",
                    "status": job_status,
                    "conclusion": job_conclusion,
                }
            ],
        },
    }


class FakeClient:
    def __init__(self, states, failures=()):
        self.states = states
        self.index = 0
        self.run_calls = 0
        self.failures = set(failures)

    def json(self, endpoint, *, paginate=False):
        if "/jobs?" not in endpoint:
            self.run_calls += 1
            if self.run_calls in self.failures:
                raise AcquisitionError("temporary API failure")
            return self.states[min(self.index, len(self.states) - 1)]["run"]
        state = self.states[min(self.index, len(self.states) - 1)]
        self.index += 1
        return [state["jobs"]] if paginate else state["jobs"]


class HistoricalAttemptClient:
    def json(self, endpoint, *, paginate=False):
        if endpoint.endswith("/attempts/1"):
            return {
                "status": "completed",
                "conclusion": "failure",
                "run_attempt": 1,
            }
        if "/attempts/1/jobs?" in endpoint:
            return [
                {
                    "total_count": 1,
                    "jobs": [
                        {
                            "id": 7,
                            "name": "test",
                            "status": "completed",
                            "conclusion": "failure",
                        }
                    ],
                }
            ]
        return {"status": "completed", "conclusion": "success", "run_attempt": 2}


def test_watch_emits_only_changes_and_backs_off_when_unchanged():
    queued = _state("in_progress", "queued")
    running = _state("in_progress", "in_progress")
    completed = _state("completed", "completed", "success", "success")
    client = FakeClient([queued, queued, running, completed])
    messages = []
    delays = []

    final = watch_run(
        client,
        "uibcdf/molsysmt",
        42,
        interval=2,
        max_interval=10,
        emit=messages.append,
        sleep=delays.append,
    )

    assert final.terminal
    assert delays == [2, 3.0, 2]
    assert messages == [
        "watch: uibcdf/molsysmt run=42 attempt=1 | status=in_progress | jobs=0/1",
        "job started: build (linux-64)",
        "job completed: build (linux-64) | conclusion=success",
        "run completed: conclusion=success | jobs=1/1",
    ]


def test_watch_of_completed_run_emits_no_redundant_transition():
    client = FakeClient([_state("completed", "completed", "failure", "failure")])
    messages = []
    delays = []

    final = watch_run(
        client,
        "uibcdf/molsysmt",
        42,
        emit=messages.append,
        sleep=delays.append,
    )

    assert final.conclusion == "failure"
    assert messages == []
    assert delays == []


def test_watch_uses_attempt_specific_run_state_for_a_historical_attempt():
    state = fetch_state(HistoricalAttemptClient(), "uibcdf/example", 42, attempt=1)

    assert state.attempt == 1
    assert state.conclusion == "failure"
    assert state.jobs[0].conclusion == "failure"


def test_watch_retries_transient_errors_without_repeating_state():
    running = _state("in_progress", "in_progress")
    completed = _state("completed", "completed", "success", "success")
    client = FakeClient([running, completed], failures={2})
    messages = []

    watch_run(
        client,
        "uibcdf/molsysmt",
        42,
        interval=1,
        max_interval=4,
        emit=messages.append,
        sleep=lambda _: None,
    )

    assert messages.count("job completed: build (linux-64) | conclusion=success") == 1
    assert any(message.startswith("watch degraded: attempt=1/3") for message in messages)


def test_transitions_escape_untrusted_job_name():
    previous = RunState("in_progress", None, 1, ())
    current = RunState(
        "in_progress",
        None,
        1,
        (JobState(1, "build\x1b[31m", "queued", None),),
    )

    assert transitions(previous, current) == [
        "job discovered: build\\u001b[31m | status=queued"
    ]


def test_watch_stops_after_bounded_consecutive_errors():
    client = FakeClient(
        [_state("in_progress", "in_progress")],
        failures={2, 3, 4},
    )
    messages = []

    with pytest.raises(AcquisitionError, match="temporary API failure"):
        watch_run(
            client,
            "uibcdf/molsysmt",
            42,
            interval=1,
            max_interval=4,
            emit=messages.append,
            sleep=lambda _: None,
        )

    assert sum(message.startswith("watch degraded:") for message in messages) == 2
