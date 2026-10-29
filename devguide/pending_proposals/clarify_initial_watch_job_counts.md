---
summary: Show explicit job-state counts in the initial watch line.
issue: uibcdf/gh-run-receptor#74
status: active
opened: 2026-10-29
closed:
verification: measured
area: [cli]
guard: tests/test_watch.py
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
contracts. The controlled regression evidence below verifies this presentation contract.

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


## Local implementation receiving — 2026-10-29

Before the implementation, all twelve new controlled cases fail on the compact
completed/total display; the eight original watch cases pass. The correction
changes only the initial line and its existing golden. Focused watch/CLI gate:
53 passed. Complete normal shared development gate: 842 passed / the existing
explicit Conda-only source skip, with the accepted fee3bd8 SDK present. Ruff,
formatting, all nine frozen contracts, 30-route preflight and report validation
pass. No assertion is removed or new skip added. The inventory has 446 active
functions: 314 product, 111 tooling and 21 integration.

The first documentation command finds Sphinx 9.1.0 in the shared development
prefix but fails because its optional sphinx_rtd_theme is absent. This is an
unconfigured docs profile, not product failure or passing documentation evidence.
Validate the repository's declared docs extras in a task-owned environment; do
not install or repair caller packages. Native gates and independent open-issue
inventory remain required before closure.


The isolated declared docs profile resolves Sphinx 8.2.3 and sphinx-rtd-theme
3.1.0 and passes the strict HTML build. Shared caller packages remain unchanged.
The canonical consumer guide remains scoped to the delivered public version;
README, usage, CLI contract and Unreleased notes describe this source change.
The old dated watch benchmark retains its original token measurements and is
explicitly scoped to its historical source. Source/native CI is still pending;
no new artifact or release is qualified by these local results.
