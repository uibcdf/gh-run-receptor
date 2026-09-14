---
summary: Active-run inspect silently reuses a stale evidence bundle
issue: uibcdf/gh-run-receptor#37
status: active
opened: 2026-09-14
closed:
severity: medium
verification: reproduced
area: ['github']
guard: tests/test_service.py
normative:
blocked_by: []
supersedes: []
---

# Active-run inspect silently reuses a stale evidence bundle

**Reported:** 2026-09-14, while monitoring the 0.20.0 compatibility candidate.
**Status:** Active; the cause is reproduced and a fail-closed refresh is under test.

Remove `severity` for proposals. The directory identifies the report kind.

## What

Run `34888469115` was first inspected while six of nine jobs had succeeded and three were
active. After GitHub completed the run with three Windows failures, repeated invocations
of

```text
./gh-run-receptor inspect 34888469115 --repo uibcdf/gh-run-receptor \
  --profile=ci --receptor=llm
```

continued to return `PENDING`, `in_progress=3`, and `success=6`. The bounded native check

```text
gh run view 34888469115 --repo uibcdf/gh-run-receptor \
  --json status,conclusion,headSha,jobs
```

reported `status=completed`, `conclusion=failure`, six successful jobs, and three failed
jobs at the exact candidate SHA `fac4df052f43b6312770e019883e2d34a51dbfe8`.

## How

`acquire_evidence()` fetches the current run object to resolve its attempt, but loads an
existing attempt-and-policy cache directory without checking the retained `run.json`
state. The first active snapshot therefore remains the report source indefinitely.

Completed attempts are immutable and remain safe to reuse. A cached nonterminal attempt
must instead be recaptured. The replacement is captured and validated at a sibling path
before the old cache entry moves aside; failure to install the replacement restores the
old directory. Cache symlinks are unlinked rather than followed during cleanup.

## Why

The behavior violates the normative requirement in `devguide/github_evidence.md` to
refresh active runs. It can hide the authoritative terminal outcome behind an obsolete
`PENDING` report until a user invokes native GitHub inspection. It does not create a false
success, but it breaks the primary live-inspection workflow and delayed the release gate.

## What is measured and what is assumed

Observed on github.com from Linux with gh-run-receptor candidate `fac4df0` and GitHub CLI
2.79.0. The receptor result retained the same state counts across repeated calls after the
native command reported completion. The run identity, job conclusions, and candidate SHA
above are GitHub source facts. No rate-limit or acquisition error was reported.

## What was refuted

The run was not merely slow: native evidence reported every job completed. The profile was
not responsible because the stale values were source run and job states. Using `watch`
would have avoided this particular invocation pattern, but `inspect` explicitly supports
active runs and the acquisition design promises active refresh.

## Scope and exclusions

This report does not cover the three Windows test failures in the same run. Those arose
from an oversized implicit pytest parameter ID overflowing Windows'
`PYTEST_CURRENT_TEST` environment variable and require only a short explicit test ID. It
also does not change retention or reuse of completed-attempt evidence.

## Acceptance criteria

- A cached bundle whose retained run is active is recaptured before reporting.
- Fresh evidence is fully captured and validated before replacing the old directory.
- A replacement failure does not turn the old cache into a partial new bundle.
- A cached completed attempt is reused without redundant structured acquisition.
- Re-inspection of run `34888469115` reports GitHub's terminal failure and three failed
  jobs.

## Dependencies and risks

No external dependency blocks the fix. Directory exchange semantics must pass on Linux,
macOS, and Windows before the 0.20.0 tag.

## Provenance

Reproduced on 2026-09-14 from Linux, Python 3.12.11, GitHub CLI 2.79.0, and
gh-run-receptor commit `fac4df052f43b6312770e019883e2d34a51dbfe8`. The remote source
was github.com run `34888469115`, attempt 1.

## Progress

On 2026-09-14 the candidate implementation recaptured the already cached path without
manual deletion. The same receptor command then returned `FAIL`,
`conclusion=failure`, `status=completed`, and `jobs: 9 (failure=3, success=6)`, agreeing
with GitHub and grouping the three Windows failures. Focused service and embedded tests
pass locally; the complete local and hosted cross-platform gates remain before closure.
