---
summary: Conda and Python primary causes are hidden by generic process errors
issue: uibcdf/gh-run-receptor#53
status: resolved
opened: 2026-09-23
closed: 2026-09-26
severity: high
verification: measured
area: [reports, tests]
guard: tests/test_report.py
normative: security.md
blocked_by: []
supersedes: []
---

# Conda and Python primary causes are hidden by generic process errors

**Reported:** 2026-09-23, from MolSysMT run `35499866604`.
**Status:** Resolved with reviewed, sanitized public-log excerpts and deterministic tests.

## What

The failed run has 15 failed matrix jobs. Its compact report grouped only a generic
process exit and micromamba setup errors, although retained logs name the Python version
exception and Conda packages unavailable in the selected channels. Reproduce locally by
building a failed Conda report from a `logs.zip` containing the three sanitized excerpts
in `tests/fixtures/logs/molsysmt_35499866604_*.txt`.

## How

The line selector ranked generic `##[error]` cleanup messages above unrecognized Python
exceptions and solver conflict lines. It now recognizes a terminal exception within a
bounded traceback and package constraints inside a bounded libmamba failure block, then
selects those lines ahead of later generic errors.

## Why

The original report sent readers toward the process runner or micromamba cleanup instead
of the actual version mismatch or unavailable dependencies. The 15 failed jobs and GitHub
failure conclusion were already correct and remain unchanged.

## What is measured and what is assumed

On 2026-09-26, `gh api repos/uibcdf/molsysmt/actions/runs/35499866604/jobs --paginate`
returned 15 failed jobs and one successful preparation job. Public logs for one Linux
native, one Linux ARM, and one Windows job showed the three root-cause families. The
sanitized fixture repeats these representative excerpts across 9, 3, and 3 synthetic
jobs to verify grouping; it is not a full replay of the public run.

## What was refuted

- The later micromamba cleanup message is not the first failure; solver output precedes it.
- The runner exit code does not explain the Python validation exception.
- Log text cannot replace GitHub's official status or conclusion.

## Scope and exclusions

The parser recognizes only narrow, bounded traceback and libmamba patterns. It does not
infer repository channel policy, installation advice, or unseen causes when logs are absent.

## Acceptance criteria

- Compact, human, and JSON reports retain the three primary cause families.
- All 15 failed jobs, GitHub's failure conclusion, and exit code 1 remain intact.
- Output and inferred causes stay bounded and credential-redacted.
- Unknown log shapes keep the existing fallback behavior.

## Dependencies and risks

There are no blockers. Future Conda or Python log formats may require new reviewed
patterns; the generic fallback remains available.

## Provenance

Public MolSysMT run `35499866604`, job logs `106049602699`, `106049602586`, and
`106049602595`, downloaded with `gh api` on 2026-09-26. Local analysis: Linux host,
Python 3.13, gh-run-receptor checkout based on `fd36990`.
