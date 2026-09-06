---
summary: Add a manual live outcome fixture workflow
issue: uibcdf/gh-run-receptor#14
status: active
opened: 2026-09-06
closed:
verification: inspected
area: ['tests', 'github', 'security']
guard:
normative:
blocked_by: []
supersedes: []
---

# Add a manual live outcome fixture workflow

**Reported:** 2026-09-06, while closing the real outcome corpus before Phase 1 stability.
**Status:** Active; no reusable public UIBCDF timed-out run was found.

## What

Add a repository-owned workflow that creates a real `timed_out` Actions run only after
manual dispatch. Capture one resulting attempt, sanitize it, and add it to the committed
contract corpus.

## How

The workflow uses only `workflow_dispatch`, top-level empty permissions, one Ubuntu job,
`timeout-minutes: 1`, and an inert wait longer than the timeout. It has no checkout,
dependencies, secrets, uploads, matrix, schedule, or push/pull-request trigger.

The source remains in `.github/workflows/` so future evidence can be regenerated
deliberately. A repository-convention test protects the manual-only trigger, empty
permissions, single bounded job, and absence of third-party actions. A separate semantic
contract test guards the sanitized observed result.

## Why

The product promises never to report a timed-out run as successful, but the public corpus
currently proves that rule only with synthetic objects. A project-owned generator makes
the upstream conclusion, job/step behavior, capture endpoint, assessment, and exit code
reproducible without depending on accidental failures in client projects.

## What is measured and what is assumed

Queries on 2026-09-06 found no `timed_out` run in the nine active UIBCDF tool repositories
or in 22 additional public UIBCDF repositories likely to contain Actions workflows:

```text
gh run list --repo uibcdf/REPOSITORY --status timed_out --limit 10 \
  --json databaseId,workflowName,conclusion,createdAt,headSha,url
gh api 'repos/uibcdf/REPOSITORY/actions/runs?status=timed_out&per_page=5'
```

GitHub workflow syntax accepts job-level `timeout-minutes`; one minute is the intended
runner cost, while actual queue and cancellation timing will be measured from the result
rather than assumed.

## What was refuted

- Waiting for an accidental timeout is rejected because it is neither bounded nor
  reproducible.
- Reusing `cancelled` evidence is rejected because GitHub exposes cancellation and timeout
  as different conclusions.
- A scheduled workflow is rejected because it would continuously spend runner resources.
- A push-triggered workflow is rejected because ordinary development would incur a
  deliberate one-minute failure.
- A synthetic-only test is retained for unit coverage but rejected as the Phase 0 evidence
  gate because it cannot validate GitHub's source behavior.

## Scope and exclusions

This increment covers only a real timed-out attempt. It does not test restricted tokens,
active transitions, arbitrary timeout durations, Windows or macOS runners, the embedded
Action, or external release verification. It does not automatically dispatch the fixture.

## Acceptance criteria

- The workflow can run only by explicit manual dispatch.
- It declares no token permissions and executes no external action or repository content.
- One invocation reaches GitHub conclusion `timed_out` with a bounded runner duration.
- The sanitized fixture preserves run, attempt, job, step, and timeout outcome identity.
- Replay returns assessment `TIMED_OUT` and exit status 3 without claiming a root cause.
- Bundle, model, and report schemas accept the fixture deterministically.
- The testing strategy and OD-007 describe gh-run-receptor as the owned generator for
  deliberately triggered live outcome evidence.

## Dependencies and risks

There is no blocker. The workflow has only `workflow_dispatch`, so committing it does not
run it. Dispatch remains a separate explicit action. GitHub-hosted runner availability can
delay the observation but cannot silently turn absence into a passing fixture.

## Provenance

Planning inspection on Linux, Python 3.13.14, GitHub CLI 2.81.0, gh-run-receptor 0.9.0,
2026-09-06. Repository searches used authenticated read-only GitHub API access.
