---
summary: Compare workflow runs and rerun attempts
issue: uibcdf/gh-run-receptor#31
status: resolved
opened: 2026-09-07
closed: 2026-09-07
verification: measured
area: ['cli', 'reports']
guard: tests/test_comparison.py
normative:
blocked_by: []
supersedes: []
---

# Comparing workflow runs and rerun attempts

**Reported:** 2026-09-07 while reviewing the remaining Phase 4 work before 1.0.
**Status:** Resolved; offline, installed, remote, and hosted comparison paths pass.

## What

Add a first-class ``compare`` command that can compare either two replayable evidence
bundles, two accessible workflow runs, or two attempts of one workflow run. The result
must be useful in compact LLM output and stable machine-readable JSON without hiding the
identity or completeness of either source.

## How

Build both sides through the existing report pipeline and compare those normalized
reports in one profile-independent engine. Publish the result as a versioned
``gh-run-receptor.comparison@1`` contract. Preserve repository, workflow, run, attempt,
commit and URL for both sides; make same-run and same-commit relationships explicit.

Report exact GitHub status/conclusion transitions, aggregate job-state changes by stable
job name, total known job duration, artifact inventory and known size changes, and
profile matrix coverage where the report exposes named platforms, roles, or phases.
Artifact results are observations at capture time, not claims about publication
regressions, because retention can change the inventory after a run finishes.

Evidence is sufficient only when metadata, jobs, and artifact inventory are complete on
both sides. A valid but insufficient comparison exits 4 and says ``INCOMPLETE``; a
difference is not itself a failing exit status. Lists in text output are bounded.

## Why

Repeated GitHub Actions runs are currently inspected independently, forcing a developer
or an LLM to retain and reconcile two verbose outputs. This is expensive, error-prone,
and can silently compare different commits. Comparison is one of the largest remaining
Phase 4 gaps and directly serves the tool's token-reduction purpose.

## What is measured and what is assumed

The repository contains sanitized bundles for attempts 1 and 2 of ArgDigest run
``22638022385``. They have the same commit; attempt 1 concluded ``failure`` and attempt 2
concluded ``success``. These are captured facts asserted by
``tests/test_contracts.py::test_real_rerun_fixtures_keep_attempts_and_conclusions_separate``.

No token saving or performance figure is assumed by this proposal. Output bounds and
determinism will be measured in tests over those saved inputs.

The completed local suite passes 314 tests. The dedicated comparison tests validate the
new schema, exact paired-rerun semantics, order independence, incompleteness, artifact
wording, bounded text, and CLI behavior. A built wheel installed without dependencies in
a clean virtual environment and compared the same bundles outside the checkout.

The live local command and hosted run `34167676919` independently reacquired ArgDigest
run `22638022385` attempts 1 and 2. Both produced `CHANGED`, `same_run=true`,
`same_head_sha=true`, and the official `failure` to `success` transition. The hosted gate
completed successfully at implementation commit `551005d`.

## What was refuted

- Comparing rendered text was rejected because it would couple semantics to presentation.
- Pairing jobs by GitHub job ID was rejected because reruns allocate new IDs.
- Declaring every changed duration a regression was rejected because this first contract
  reports evidence and deltas, not policy-dependent judgement.
- Treating a missing artifact as proof of a release regression was rejected because
  artifact expiry and capture time affect the observation.

## Scope and exclusions

This increment does not define statistical baselines, performance thresholds, long-term
run storage, trend dashboards, or automatic regression policy. It does not combine
evidence from two attempts into one report. Published-report comparison can be added
later because it requires a separate provenance decision.

## Acceptance criteria

- Offline bundle comparison and online run/attempt comparison use the same engine.
- JSON validates against the packaged comparison schema and is byte deterministic.
- The ArgDigest fixtures report failure-to-success with the same run and commit.
- Different commits are always visible and produce a warning.
- Duplicate job names are compared deterministically as aggregate state counts.
- Missing required evidence yields ``INCOMPLETE`` and exit 4.
- Human and LLM text is bounded and does not label artifact absence a regression.
- A hosted gate compares the two real public ArgDigest attempts before closure.

## Dependencies and risks

No tracked dependency blocks the work. Online comparison depends on the existing GitHub
CLI acquisition boundary; offline comparison remains available without network access.

## Provenance

Initial design inspection: Linux host, repository commit `c522785`, 2026-09-07. Final
local validation used Python 3.13.14, Ruff 0.16.5, 314 pytest cases with
`--receptor=llm`, an isolated wheel install under `/tmp`, and implementation commit
`551005d`. GitHub-hosted Ubuntu validation used run `34167676919` on the same date.

## Implementation checkpoint

`compare` now accepts two bundle directories, two run IDs/URLs, or one run plus two
attempts. Both sides use the existing report pipeline and remain separately identified.
The machine output is `comparison@1`; human and LLM projections are bounded and do not
reinterpret official outcomes.

The comparison exposes official transitions, state-count multisets for repeated job
names, complete-known duration and artifact-size deltas, capture-time artifact inventory,
and comparable profile matrix units. It fails closed with status 4 when required evidence
is incomplete and returns zero for complete changed or unchanged evidence. Regression
policy and cross-job aggregation remain deliberately separate Phase 4 work.
