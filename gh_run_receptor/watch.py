"""Watching workflow state without repeating unchanged status trees."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import sleep as system_sleep
from typing import Any

from gh_run_receptor.errors import AcquisitionError
from gh_run_receptor.github import GitHubClient, merge_pages
from gh_run_receptor.report import _safe_text

Emit = Callable[[str], None]
Sleep = Callable[[float], None]
DEFAULT_POLL_INTERVAL = 10.0
DEFAULT_MAX_POLL_INTERVAL = 60.0
UNCHANGED_BACKOFF_FACTOR = 1.5
ERROR_BACKOFF_FACTOR = 2.0
DEFAULT_MAX_CONSECUTIVE_ERRORS = 3


@dataclass(frozen=True)
class JobState:
    """Representing the transition-relevant state of one job."""

    job_id: int
    name: str
    status: str | None
    conclusion: str | None


@dataclass(frozen=True)
class RunState:
    """Representing one bounded workflow-run snapshot."""

    status: str | None
    conclusion: str | None
    attempt: int
    jobs: tuple[JobState, ...]

    @property
    def terminal(self) -> bool:
        return self.status == "completed"


@dataclass(frozen=True)
class RunSnapshot:
    """Retaining one state together with its reusable source responses."""

    state: RunState
    run: dict[str, Any]
    jobs: dict[str, Any]
    api_requests: int

    @property
    def reusable_terminal_jobs(self) -> bool:
        """Reporting whether all handed-off jobs agree with terminal run state."""
        return self.state.terminal and all(job.status == "completed" for job in self.state.jobs)


@dataclass(frozen=True)
class WatchResult:
    """Returning terminal evidence and the measured successful-poll budget."""

    snapshot: RunSnapshot
    successful_snapshots: int
    successful_poll_requests: int

    @property
    def terminal(self) -> bool:
        return self.snapshot.state.terminal

    @property
    def conclusion(self) -> str | None:
        return self.snapshot.state.conclusion


def fetch_snapshot(
    client: GitHubClient, repository: str, run_id: int, attempt: int | None = None
) -> RunSnapshot:
    """Fetching one reusable run and job snapshot without logs or artifacts."""
    api_requests = 1
    run = client.json(f"/repos/{repository}/actions/runs/{run_id}")
    if not isinstance(run, dict):
        raise AcquisitionError("workflow-run response is not an object")
    current_attempt = int(run.get("run_attempt") or 1)
    selected_attempt = attempt or current_attempt
    if selected_attempt < 1 or selected_attempt > current_attempt:
        raise AcquisitionError(
            f"attempt {selected_attempt} is outside the available range 1..{current_attempt}"
        )
    if selected_attempt != current_attempt:
        run = client.json(f"/repos/{repository}/actions/runs/{run_id}/attempts/{selected_attempt}")
        api_requests += 1
        if not isinstance(run, dict) or run.get("run_attempt") != selected_attempt:
            raise AcquisitionError("workflow-run attempt response has conflicting identity")
    payload = client.json(
        f"/repos/{repository}/actions/runs/{run_id}/attempts/{selected_attempt}/jobs?per_page=100",
        paginate=True,
    )
    api_requests += max(1, len(payload)) if isinstance(payload, list) else 1
    jobs = merge_pages(payload, "jobs")
    states = tuple(
        sorted(
            (
                JobState(
                    job_id=int(job["id"]),
                    name=str(job.get("name") or "unnamed job"),
                    status=job.get("status"),
                    conclusion=job.get("conclusion"),
                )
                for job in jobs["jobs"]
            ),
            key=lambda item: item.job_id,
        )
    )
    state = RunState(
        status=run.get("status"),
        conclusion=run.get("conclusion"),
        attempt=selected_attempt,
        jobs=states,
    )
    return RunSnapshot(state=state, run=run, jobs=jobs, api_requests=api_requests)


def fetch_state(
    client: GitHubClient, repository: str, run_id: int, attempt: int | None = None
) -> RunState:
    """Fetching one run and job snapshot without logs or artifacts."""
    return fetch_snapshot(client, repository, run_id, attempt).state


def _job_transition(previous: JobState | None, current: JobState) -> str | None:
    name = _safe_text(current.name)
    if previous is None:
        if current.status == "completed":
            return f"job completed: {name} | conclusion={_safe_text(current.conclusion)}"
        if current.status == "in_progress":
            return f"job started: {name}"
        return f"job discovered: {name} | status={_safe_text(current.status)}"
    if previous.name != current.name:
        return f"job renamed: {_safe_text(previous.name)} -> {name}"
    if previous.status != current.status:
        if current.status == "in_progress":
            return f"job started: {name}"
        if current.status == "completed":
            return f"job completed: {name} | conclusion={_safe_text(current.conclusion)}"
        return f"job state: {name} | {_safe_text(previous.status)} -> {_safe_text(current.status)}"
    if previous.conclusion != current.conclusion:
        return (
            f"job conclusion: {name} | {_safe_text(previous.conclusion)} -> "
            f"{_safe_text(current.conclusion)}"
        )
    return None


def transitions(previous: RunState, current: RunState) -> list[str]:
    """Returning only semantic changes between two snapshots."""
    messages: list[str] = []
    old_jobs = {job.job_id: job for job in previous.jobs}
    for job in current.jobs:
        if message := _job_transition(old_jobs.get(job.job_id), job):
            messages.append(message)
    if previous.status != current.status and current.status != "completed":
        messages.append(f"run state: {_safe_text(previous.status)} -> {_safe_text(current.status)}")
    if not previous.terminal and current.terminal:
        completed = sum(job.status == "completed" for job in current.jobs)
        messages.append(
            f"run completed: conclusion={_safe_text(current.conclusion)} | "
            f"jobs={completed}/{len(current.jobs)}"
        )
    return messages


def watch_run(
    client: GitHubClient,
    repository: str,
    run_id: int,
    *,
    attempt: int | None = None,
    interval: float = DEFAULT_POLL_INTERVAL,
    max_interval: float = DEFAULT_MAX_POLL_INTERVAL,
    emit: Emit,
    sleep: Sleep = system_sleep,
    max_consecutive_errors: int = DEFAULT_MAX_CONSECUTIVE_ERRORS,
) -> WatchResult:
    """Polling until terminal state while emitting each transition once."""
    snapshot = fetch_snapshot(client, repository, run_id, attempt)
    current = snapshot.state
    successful_snapshots = 1
    successful_poll_requests = snapshot.api_requests
    if current.terminal:
        return WatchResult(
            snapshot=snapshot,
            successful_snapshots=successful_snapshots,
            successful_poll_requests=successful_poll_requests,
        )

    completed = sum(job.status == "completed" for job in current.jobs)
    emit(
        f"watch: {_safe_text(repository)} run={run_id} attempt={current.attempt} | "
        f"status={_safe_text(current.status)} | jobs={completed}/{len(current.jobs)}"
    )
    delay = interval
    consecutive_errors = 0
    while not current.terminal:
        sleep(delay)
        try:
            updated_snapshot = fetch_snapshot(client, repository, run_id, current.attempt)
        except AcquisitionError as error:
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                raise
            emit(
                f"watch degraded: attempt={consecutive_errors}/{max_consecutive_errors} | "
                f"{_safe_text(error)}"
            )
            delay = min(max_interval, max(interval, delay * ERROR_BACKOFF_FACTOR))
            continue

        consecutive_errors = 0
        successful_snapshots += 1
        successful_poll_requests += updated_snapshot.api_requests
        updated = updated_snapshot.state
        changes = transitions(current, updated)
        for change in changes:
            emit(change)
        delay = (
            interval
            if changes
            else min(max_interval, max(interval, delay * UNCHANGED_BACKOFF_FACTOR))
        )
        snapshot = updated_snapshot
        current = updated
    return WatchResult(
        snapshot=snapshot,
        successful_snapshots=successful_snapshots,
        successful_poll_requests=successful_poll_requests,
    )
