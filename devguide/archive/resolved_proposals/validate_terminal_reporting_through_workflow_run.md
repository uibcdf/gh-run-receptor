---
summary: Validate terminal reporting through workflow_run
issue: uibcdf/gh-run-receptor#18
status: resolved
opened: 2026-09-06
closed: 2026-09-06
verification: measured
area: ['github']
guard: tests/test_workflow_run_reporting.py
normative:
blocked_by: []
supersedes: []
---

# Validate terminal reporting through `workflow_run`

**Reported:** 2026-09-06, after the 0.12.0 Action proved same-run `PENDING` and
completed-run terminal reports independently.
**Status:** Resolved; the read-only downstream integration preserves completed source
identity and conclusion in a separate live `workflow_run` execution.

## What

Add a repository-owned downstream workflow triggered when `Distributed Action validation`
completes. It passes `github.event.workflow_run.id` to the released 0.12.0 Action and
verifies that the report identifies the completed source run and preserves its terminal
GitHub conclusion.

## How

The downstream workflow requests only `actions: read` and `contents: read`, performs no
checkout, executes no source-run code or artifacts, and uses default-branch receptor policy.
It uploads the normal bounded report artifact and checks scalar outputs plus the canonical
JSON report. The upstream validation workflow remains manually dispatched, so adding the
listener creates no scheduled or push-triggered runner consumption.

## Why

An Action inside its own source run cannot know that run's terminal conclusion. Client
guidance already recommends `workflow_run`, but only a live downstream invocation can prove
the event context, permissions, tag resolution, source identity, and terminal semantics
together. This is the missing bridge from the Action component test to routine client use.

## What is measured and what is assumed

GitHub's official event documentation states that `workflow_run` exposes the triggering
run's conclusion and warns that this event may receive secrets and write-capable tokens even
when the preceding workflow could not. The proposed workflow therefore overrides
permissions to read-only and never checks out or executes untrusted source content.

Run `34045392810` already proves that the released Action tag works on all three hosted
operating systems. The downstream run ID, report bytes, duration, source identity, and
conclusion parity remain unmeasured until the listener is committed and a new source run is
manually dispatched.

## Implementation progress

The listener now targets only completed `Distributed Action validation` runs. It grants
read-only Actions and contents access, performs no checkout or artifact download, calls the
released 0.12.0 Action with the event run ID, and independently asserts source ID, completed
status, conclusion parity, and receptor `PASS`. Static tests guard each security and truth
property. Source run `34045930131` passed 3/3 and delivered downstream run `34045953527`.
The downstream job completed in 8 seconds, its Action step in 4 seconds, and its canonical
report artifact was 1,449 bytes. The workflow assertions verified source run ID, completed
status, GitHub conclusion parity, and receptor `PASS`.

## What was refuted

- Treating a final same-run job as terminal is rejected because the source run is active.
- Checking out the source run's head SHA is rejected because reporting needs API metadata,
  not execution of potentially untrusted code.
- Granting default workflow permissions is rejected because the event has a stronger token
  context than the source workflow may have had.
- Triggering on every project CI run is deferred until cost and fork behavior are measured.

## Scope and exclusions

This increment does not yet publish a general reusable workflow, inspect report artifact
contents from the external CLI, support cross-repository source runs, execute producer
artifacts, or claim safe behavior for every fork and restricted-token configuration. It is
a bounded repository-owned live proof of the recommended terminal pattern.

## Acceptance criteria

- The listener names the exact upstream workflow and completed event type.
- Workflow and job permissions are read-only and no checkout or source artifact execution
  occurs.
- The released 0.12.0 Action receives the event's exact run ID and repository.
- The canonical report subject ID equals the triggering run ID, status is `completed`, and
  report conclusion equals `github.event.workflow_run.conclusion`.
- The listener remains dormant except after a manual distributed-validation run.
- A live triggered run completes and leaves a small canonical report artifact.

## Dependencies and risks

There is no tracked blocker. Event delivery may be delayed, and the listener exists only on
the default branch. A missing trigger must be diagnosed from workflow/event metadata rather
than interpreted as a receptor result.

## Provenance

Design and live validation on Linux, Python 3.13.14, GitHub CLI 2.81.0,
gh-run-receptor 0.12.0,
2026-09-06. Event and security behavior was checked against GitHub's official
`workflow_run` documentation.
