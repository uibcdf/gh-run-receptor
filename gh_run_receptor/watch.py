"""Watching workflow state without repeating unchanged status trees."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import sleep as system_sleep

from gh_run_receptor.errors import AcquisitionError
from gh_run_receptor.github import GitHubClient, merge_pages
from gh_run_receptor.report import _safe_text

Emit = Callable[[str], None]
Sleep = Callable[[float], None]


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


def fetch_state(
    client: GitHubClient, repository: str, run_id: int, attempt: int | None = None
) -> RunState:
    """Fetching one run and job snapshot without logs or artifacts."""
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
        run = client.json(
            f"/repos/{repository}/actions/runs/{run_id}/attempts/{selected_attempt}"
        )
        if not isinstance(run, dict) or run.get("run_attempt") != selected_attempt:
            raise AcquisitionError("workflow-run attempt response has conflicting identity")
    payload = client.json(
        f"/repos/{repository}/actions/runs/{run_id}/attempts/{selected_attempt}/jobs?per_page=100",
        paginate=True,
    )
    jobs = merge_pages(payload, "jobs")["jobs"]
    states = tuple(
        sorted(
            (
                JobState(
                    job_id=int(job["id"]),
                    name=str(job.get("name") or "unnamed job"),
                    status=job.get("status"),
                    conclusion=job.get("conclusion"),
                )
                for job in jobs
            ),
            key=lambda item: item.job_id,
        )
    )
    return RunState(
        status=run.get("status"),
        conclusion=run.get("conclusion"),
        attempt=selected_attempt,
        jobs=states,
    )


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
        messages.append(
            f"run state: {_safe_text(previous.status)} -> {_safe_text(current.status)}"
        )
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
    interval: float = 10.0,
    max_interval: float = 60.0,
    emit: Emit,
    sleep: Sleep = system_sleep,
    max_consecutive_errors: int = 3,
) -> RunState:
    """Polling until terminal state while emitting each transition once."""
    current = fetch_state(client, repository, run_id, attempt)
    if current.terminal:
        return current

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
            updated = fetch_state(client, repository, run_id, current.attempt)
        except AcquisitionError as error:
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                raise
            emit(
                f"watch degraded: attempt={consecutive_errors}/{max_consecutive_errors} | "
                f"{_safe_text(error)}"
            )
            delay = min(max_interval, max(interval, delay * 2))
            continue

        consecutive_errors = 0
        changes = transitions(current, updated)
        for change in changes:
            emit(change)
        delay = interval if changes else min(max_interval, max(interval, delay * 1.5))
        current = updated
    return current
