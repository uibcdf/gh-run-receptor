---
summary: Aggregate multiple workflow runs without merging source truth
issue: uibcdf/gh-run-receptor#38
status: resolved
opened: 2026-09-17
closed: 2026-09-17
verification: measured
area: ['reports']
guard: tests/test_aggregation.py
normative: data_contracts.md
blocked_by: []
supersedes: []
---

# Aggregate multiple workflow runs without merging source truth

**Reported:** 2026-09-17, after the first real MolSysMT producer-event adoption run.
**Status:** Resolved; the bounded contract, CLI, evidence, and release gate are complete.

## What

Add a bounded `aggregate` command and an `aggregate@1` serialized contract for two or
more workflow runs. Each source remains an independent normalized report with its own
repository, workflow, run, attempt, commit, status, conclusion, assessment, completeness,
job count, and artifact count. The collection may summarize those facts, but it must not
invent an official GitHub conclusion for a group of runs.

## How

The command accepts between 2 and 50 homogeneous sources: either local bundle directories
for fully offline operation or GitHub run IDs/URLs for remote capture. Numeric IDs use the
explicit `--repo`; URLs retain their own repository identity. Remote sources must share a
GitHub hostname, but need not share a repository, workflow, commit, or profile.

Every source passes through the existing validated bundle, normalized model, configuration,
profile, and report pipeline. The aggregate records deterministic counts by source
assessment, official conclusion, profile, repository, and workflow; totals known jobs and
artifacts; and names incomplete sources explicitly. Text rendering contains one bounded
header and one bounded line per source, with a fixed maximum and an omitted-source count.
JSON retains every accepted source up to the input bound.

The aggregate assessment is derived and labeled as such. Known failure is never hidden by
missing evidence in another source. Exit status preserves the existing meanings: a known
failure or profile violation returns 1, another non-success terminal state returns 2,
active work returns 3, incomplete evidence returns 4, and acquisition or validation errors
return 5. There is no mutation, implicit workflow search, or policy threshold in this
increment.

## Why

Real release and CI windows consist of several workflows. Today an operator must issue and
read one `inspect` command per run, which repeats headings and leaves cross-workflow
coverage to the reader. The Phase 4 exit condition requires CI, documentation, and Conda
examples across multiple repositories while preserving partial matrix failure. A bounded
collection makes that evidence directly consumable by a person, an LLM, or automation
without weakening the one-run truth model.

## What is measured and what is assumed

Measured facts:

- MolSysMT run `35196968944` produced a complete 144 KiB bundle and a 668-byte
  `events@1` payload; public 0.20.0 rendered it as one successful platform, one producer
  event, two successful jobs, and two artifacts.
- `gh-run-receptor --help` in 0.20.0 exposes one-run inspection and two-run comparison,
  but no collection command.
- The local 0.20.0 post-release suite passes 360 tests in 2.50 seconds on 2026-09-17.

The expected token reduction for a real multi-workflow window is not yet measured. It
must be benchmarked after the command exists rather than inferred from the one-run pilot.

Implementation checkpoint on 2026-09-17:

- 84 focused aggregation, compatibility, contract, and CLI tests pass.
- A corrected live invocation over MolSysMT run `35196968944` and gh-run-receptor run
  `35194479266` reports two complete successful sources, five jobs, five artifacts, two
  repositories, and two workflows.
- The first live invocation exposed that remote aggregation had omitted the required
  explicit `attempt=None` acquisition argument. The focused remote-path test now asserts
  this call contract.
- Exact-revision hosted gate `35204416931` passes both the positive and negative cases.
  The multi-state benchmark, canonical client guide, and 0.21.0 candidate freeze are
  complete.

The first exact-revision gate, run `35202361626` at commit `37d8af7`, passed the successful
cross-repository case with read-only permissions. A second live local probe combined the
MolSysMT success with MolSysViewer CI failure `34890243748`; it retained complete evidence,
reported one `PASS` plus one `FAIL`, and returned the aggregate `FAIL` path with nine jobs
and two artifacts. Gate `35204416931` passed that negative case together with the
cross-repository success case at exact commit `64a82eb`.

The same two-success collection was measured against a deliberately compact native JSON
projection built from `gh run view --json` plus the artifacts endpoint, and against two
ordinary receptor inspections. With tiktoken 0.13.0:

| Output | Lines | Bytes | `cl100k_base` | `o200k_base` | `p50k_base` / `r50k_base` |
| --- | ---: | ---: | ---: | ---: | ---: |
| Compact native projection | 1 | 632 | 208 | 207 | 246 |
| Multi-run aggregate | 3 | 527 | 139 | 140 | 163 |
| Two individual receptor reports | 2 | 278 | 87 | 88 | 97 |

The aggregate saves 33.2% `cl100k_base` tokens against the native projection while adding
collection counts, profiles, workflow paths, and evidence sufficiency. It is 59.8% larger
than two already-compact receptor lines. Therefore aggregation is justified by one
machine-readable collection contract, coverage, and conservative outcome composition, not
by claiming that it is always the shortest way to read a few known successful runs. The
individual `inspect` commands remain the economical choice for that narrower question.

## What was refuted

- Extending `compare` to more than two sources is rejected because comparison answers a
  baseline/candidate delta question, while aggregation answers a collection-state question.
- Concatenating ordinary reports is rejected because it supplies no machine-readable
  collection identity, completeness, deterministic counts, or bounded total rendering.
- Treating a collection as one synthetic GitHub run is rejected because GitHub supplies
  no such official source object or conclusion.
- Automatic repository-wide workflow discovery is deferred; explicit run identities keep
  acquisition cost, authorization, and user intent bounded.

## Scope and exclusions

This increment does not discover runs, select the newest run of a workflow, compare
baselines, execute reruns, cancel work, publish artifacts, or define organization-wide
release policy. It does not merge jobs or producer events across source reports. A later
policy layer may assert required workflow coverage against `aggregate@1` after the
descriptive contract is proven.

## Acceptance criteria

- Local aggregation performs no network calls and is deterministic.
- Remote aggregation uses the ordinary acquisition path and exact source identity.
- Every source retains official status and conclusion independently.
- Known failure, non-success terminal state, active work, and incomplete evidence have
  truth-table tests for assessment and exit status.
- The command rejects mixed local/remote input, fewer than 2 or more than 50 sources,
  conflicting remote hostnames, and ambiguous numeric IDs without `--repo`.
- Human, LLM, and JSON renderings are deterministic, terminal-safe, and bounded.
- A Draft 2020-12 `aggregate@1` schema rejects conforming emptiness and validates real
  profile combinations.
- Offline CI, documentation, and Conda fixtures demonstrate cross-workflow aggregation;
  a hosted gate validates at least one real multi-workflow collection before 0.21.0.
- The canonical CLI, data-contract, testing, roadmap, README, and client-guide surfaces
  describe the delivered behavior.

## Dependencies and risks

No issue dependency blocks local implementation. The principal risks are accidentally
presenting a derived collection result as GitHub authority, allowing unbounded source
lists, obscuring a known failure behind incomplete evidence, and freezing a contract
before hosted corpus evidence can challenge its shape. Therefore `aggregate@1` remains
unfrozen until the 0.21.0 candidate gate.

## Provenance

Measurements were made on `linux-64` host `tzinacan`, Python 3.13 in the MolSysSuite
development environment, gh-run-receptor public 0.20.0 and checkout commit `630c8ea`, on
2026-09-17. Hosted source evidence includes runs `35196968944`, `35194479266`, and
`34890243748`; exact-revision aggregate gates `35202361626` and `35204416931` ran on
`ubuntu-latest`.
