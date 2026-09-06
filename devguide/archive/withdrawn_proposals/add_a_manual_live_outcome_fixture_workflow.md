---
summary: Add a manual live outcome fixture workflow
issue: uibcdf/gh-run-receptor#14
status: withdrawn
opened: 2026-09-06
closed: 2026-09-06
verification: measured
area: ['tests', 'github', 'security']
guard:
normative: github_evidence.md
blocked_by: []
supersedes: []
---

# Add a manual live outcome fixture workflow

**Reported:** 2026-09-06, while closing the real outcome corpus before Phase 1 stability.
**Status:** Withdrawn after the live experiment produced `cancelled`, not `timed_out`.

## What

Add a repository-owned workflow that creates a real `timed_out` Actions run only after
manual dispatch. Capture one resulting attempt, sanitize it, and add it to the committed
contract corpus.

## How

The workflow uses only `workflow_dispatch`, top-level empty permissions, one Ubuntu job,
`timeout-minutes: 1`, and an inert wait longer than the timeout. It has no checkout,
dependencies, secrets, uploads, matrix, schedule, or push/pull-request trigger.

The proposed source would remain in `.github/workflows/` so future evidence could be
regenerated deliberately. A repository-convention test would protect the manual-only
trigger, empty permissions, single bounded job, and absence of third-party actions. A
separate semantic contract test would guard the sanitized observed result.

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

Run `34027741137`, attempt 1, executed the proposed one-job workflow. GitHub reported the
run and job as `completed`/`cancelled`, and the wait step as `cancelled`. The job ran from
10:33:24Z to 10:34:38Z. gh-run-receptor preserved `CANCELLED` and exit status 2. The
metadata bundle was complete and contained 20,380 bytes.

GitHub's workflow-syntax reference states that `timeout-minutes` automatically cancels a
job. The REST workflow-run filter nevertheless accepts `timed_out`, and the Checks API
also defines it as a check-run conclusion. Those API enum surfaces do not establish that
a standard Actions job timeout emits that conclusion.

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
- The hypothesis that `timeout-minutes` produces `timed_out` is refuted by run
  `34027741137` and by GitHub's documented cancellation semantics.

## Scope and exclusions

This experiment covers the standard one-minute Ubuntu job timeout. It does not establish
how an external GitHub App can create a `timed_out` check, nor test restricted tokens,
active transitions, Windows or macOS runners, the embedded Action, or external release
verification.

## Acceptance criteria

- The failed generator hypothesis and observed source conclusion are documented.
- The redundant workflow is removed so it cannot consume further runner time.
- Synthetic `timed_out` truth-table coverage remains, while real capture is explicitly
  opportunistic rather than claimed.
- The testing strategy and OD-007 no longer promise an unimplemented dedicated fixture
  repository or synthetic-only corpus.

## Dependencies and risks

There is no implementation blocker. A real `timed_out` workflow-run source remains absent;
manufacturing an external check would require a materially different GitHub App and
write-permission boundary, so it is outside this proposal.

## Provenance

Planning inspection on Linux, Python 3.13.14, GitHub CLI 2.81.0, gh-run-receptor 0.9.0,
2026-09-06. Repository searches used authenticated read-only GitHub API access.

The live experiment used GitHub-hosted `ubuntu-latest`, run `34027741137`, attempt 1, at
commit `a87e5b9748ceaf1d6c5277a34dd2d533eca11865`. Capture and replay used the installed
gh-run-receptor 0.9.0 extension.

## Outcome

The proposal is withdrawn because its safe generation mechanism cannot create its target
source state. Standard job timeout behavior is now a measured cancellation case. A real
`timed_out` fixture may be added later only from authentic read-only evidence or under a
separately reviewed GitHub App/write-permission proposal.
