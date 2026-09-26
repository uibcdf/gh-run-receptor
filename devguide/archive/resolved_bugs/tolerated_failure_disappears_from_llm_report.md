---
summary: A tolerated job failure disappears from the LLM report
issue: uibcdf/gh-run-receptor#51
status: resolved
opened: 2026-09-22
closed: 2026-09-26
severity: high
verification: inspected
area: [reports, tests]
guard: tests/test_report.py
normative: cli_and_output_contract.md
blocked_by: []
supersedes: []
---

# A tolerated job failure disappears from the LLM report

**Reported:** 2026-09-22, from the successful Ackredit run `35729368946` in `uibcdf/ackredit#64`.
**Status:** Resolved with a regression for generic and CI profiles.

## What

The run concluded `success`, but one job concluded `failure` under `continue-on-error`.
The compact LLM report said `PASS` and `jobs=5/6` without naming the failed job. Its JSON
and human reports retained the failure. A minimal local reproducer builds a report with
`run.json` conclusion `success` and a failed job in `jobs.json`, then calls `render_llm`.

## How

`render_llm` returned from its `PASS` branch before reaching the existing bounded
non-success job section. The renderer now uses that section in both branches and adds a
`non_success_jobs` summary field when necessary.

## Why

The omitted lane produced no test evidence after a Conda solver failure. A reader using
only the compact report could mistake the green run for complete test coverage.

## What is measured and what is assumed

The issue records one failed job among six for the public Ackredit run. The local
regression uses sanitized synthetic evidence and asserts official conclusion, assessment,
exit code, job name, failed step, and bounded output. It does not replay the public run.

## What was refuted

Changing GitHub's run conclusion was rejected because it is an authoritative source fact.
The successful-job ratio alone was inadequate because it did not name the failed lane.

## Scope and exclusions

The change does not redefine the `PASS` assessment or process exit code for an officially
successful run. It exposes the observed non-success work in the compact output.

## Acceptance criteria

- The compact report names tolerated failed jobs and failed steps for generic and CI
  profiles while retaining GitHub's conclusion.
- The existing output bound and non-success labels apply.
- Runs without non-success jobs keep the one-line successful summary.

## Dependencies and risks

There are no blockers. Consumers that assumed every successful compact report has one
line must handle the additional detail when tolerated failures exist.

## Provenance

Issue evidence: public `uibcdf/ackredit` run `35729368946`, reported 2026-09-22.
Local regression: Linux host, Python 3.13, 2026-09-26; no public capture was replayed.
