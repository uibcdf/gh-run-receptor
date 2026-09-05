---
summary: Conda summaries erase cancelled platform state
issue: uibcdf/gh-run-receptor#12
status: resolved
opened: 2026-09-05
closed: 2026-09-05
severity: medium
verification: measured
area: ['profiles', 'reports', 'tests']
guard: tests/test_contracts.py
normative:
blocked_by: []
supersedes: []
---

# Conda summaries erase cancelled platform state

**Reported:** 2026-09-05, while adding real cancelled-run evidence after 0.8.0.
**Status:** Resolved and verified against a public MolSysMT Conda run.

## What

MolSysMT run `33636046706` is officially cancelled. Its macOS platform jobs are cancelled,
but the Conda matrix records both platforms as `unknown`, and compact output reports only
`successful=2 failed=1 missing=0`. It then introduces all ten non-success jobs, including
seven cancelled jobs, under `failed jobs`.

```text
gh run-receptor inspect 33636046706 --repo uibcdf/molsysmt \
  --capture metadata --receptor=llm
```

## How

The Conda platform reducer recognizes all-success, any-failure, and missing states. Other
official conclusions collapse to `unknown`. The generic compact renderer selects every
non-success/non-neutral job correctly but gives the collection the fixed label
`failed jobs`, even when the run is cancelled or timed out.

## Why

The global `CANCELLED` assessment remains correct, but the report loses which platforms
were cancelled and uses a misleading category label. This prevents reliable minimal
follow-up decisions for interrupted matrices.

## What is measured and what is assumed

The metadata bundle contains 17 jobs: 7 success, 3 failure, and 7 cancelled. Linux and
Linux AArch64 are reusable, Windows failed, and both macOS platforms contain cancelled
jobs. The JSON report records those macOS platform states as `unknown`. No log evidence is
needed to establish these official conclusions.

## What was refuted

- Treating cancelled platforms as failed is rejected because GitHub distinguishes those
  source conclusions.
- Omitting cancelled platforms from the compact counts is rejected because the observed
  matrix total then cannot be reconciled.
- Calling every non-success job failed is rejected even when the selection itself is
  correct; the heading must not rewrite source state.

## Scope and exclusions

The fix does not infer why cancellation happened or whether a cancelled artifact can be
reused. Reusability continues to require a successful platform job and matching artifact.

## Acceptance criteria

- Platform aggregation preserves `cancelled`, `timed_out`, pending, and unknown source
  states conservatively instead of collapsing them into failure or success.
- Compact Conda counts account for every observed platform state.
- Non-success job headings use neutral terminology and retain each official conclusion.
- The sanitized real fixture preserves official run, job, platform, and artifact identity.
- Global assessment and exit code remain `CANCELLED` and 2.

## Dependencies and risks

There is no blocker. Mixed conclusions inside one platform need an explicit deterministic
precedence that never upgrades the platform to success.

## Provenance

Linux host, Python 3.13.14, gh-run-receptor 0.8.0, metadata capture on 2026-09-05.
Public evidence: `uibcdf/molsysmt` run `33636046706`, attempt 1.

## Resolution

The Conda reducer now preserves cancellation, timeout, active, and future states with a
deterministic conservative precedence. Compact summaries count every observed platform
state, while mixed or cancelled job lists use the neutral `non-success jobs` heading. The
real fixture retains `CANCELLED`, exit status 2, and both cancelled macOS platforms.
