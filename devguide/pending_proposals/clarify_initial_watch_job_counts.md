---
summary: Show explicit job-state counts in the initial watch line.
issue: uibcdf/gh-run-receptor#74
status: active
opened: 2026-10-29
closed:
verification: inspected
area: [cli]
guard:
normative: cli_and_output_contract.md
blocked_by: []
supersedes: []
---

# Explicit initial watch job counts

## What and why

The initial watch line currently renders jobs=completed/total. In the Sabueso
observation recorded in uibcdf/gh-run-receptor#74, jobs=0/14 could be mistaken for
no started jobs even while the jobs API reported active work. GitHub can retain
run status queued while individual jobs are already in progress. This is a
presentation improvement; no incorrect terminal result or stalled poll is proven.

## Accepted direction

Display completed, in_progress and queued counts explicitly in the initial
stderr line, with total last. Include other only when one or more observed jobs
have a different or missing source status. Count completed status regardless of
conclusion; never equate completed with successful. Keep source states untouched.
Use the already acquired jobs snapshot; add no request, synthetic transition,
status normalization, retry or polling change. Already-completed runs keep their
single final report. The final report and serialized schemas retain their own
contracts. This direction is provisional until its regressions execute.

## Verification plan

Preserve the existing transition/backoff/API-budget golden and update only its
initial count text. Add controlled structured-snapshot cases for the reported
fourteen-job mixture, empty and all-completed job lists, non-success conclusions,
and missing/future/other statuses. Verify the single bounded initial line, quiet
unchanged polls, original GitHub run status, final source conclusion and request
budget. Classify all new assertions as product behavior in the exhaustive scope
inventory. Run focused and complete source tests, Ruff, applicable native gates
and documentation checks before closure.

## Ownership and scope

GHR owns this progress rendering; no shared SDK, reusable workflow, canonical
consumer-guide contract, dependency, optional backend, public version or archive
changes are selected. Existing support libraries do not supply this presentation
operation and no new library boundary needs adoption. The shared development
prefix has the same seven known unrelated dependency-closure findings already
tracked under uibcdf/molsyssuite#82; they are not repaired or credited as passing.
Release-candidate installed qualification remains a later, separate gate.

## Provenance

Inspected at source 24e5f05968b12cc4af4cfbad00d3981dd568573f, Linux,
Python 3.14.7, pytest 9.1.1 and Ruff 0.16.5 on 2026-10-29. The original
Sabueso observation is reported evidence; the planned regression is a controlled
reproduction, not a newly captured historical run.
