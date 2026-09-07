---
summary: Publish a same-revision reusable reporting workflow
issue: uibcdf/gh-run-receptor#32
status: open
opened: 2026-09-07
closed:
verification: asserted
area: ['reports', 'github']
guard:
normative:
blocked_by: []
supersedes: []
---

# Publishing a same-revision reusable reporting workflow

**Reported:** 2026-09-07 during the Phase 4 gap audit after run comparison landed.
**Status:** Open; implementation and remote distribution validation are in progress.

## What

Publish a `workflow_call` adapter that produces one terminal report for an already
completed source run. Client repositories should not need to duplicate runner selection,
Action invocation, defaults, and job-to-workflow output wiring.

## How

Add `.github/workflows/reusable-report.yml` with typed inputs for source run, repository,
profile, capture policy, artifact prefix, inline rules, and strict reporter behavior. It
must invoke the root Action through GitHub's `$/` self-repository reference so the Action
and reusable workflow resolve from the same repository commit selected by the caller.

Expose only outputs that survive the job boundary: assessment, official conclusion,
profile, group counts, artifact name, readiness, and error category. Do not expose the
runner-local report path. The caller retains authority over token permissions; the called
workflow requests only `actions: read` and `contents: read` and cannot elevate them.

Add one manual caller workflow that references the reusable workflow remotely and verifies
the outputs against a retained completed public run. This is a distribution gate, not
ordinary per-commit CI.

## Why

The product contract names the reusable final reporting workflow as the preferred embedded
mode for CI matrices, Conda, documentation, and releases. Today only the lower-level
composite Action and one copied downstream listener exist. Copying that job across clients
creates configuration drift. Hardcoding an older internal Action tag would be worse: a
new wrapper could silently execute an older report contract.

## What is measured and what is assumed

The current canonical listener contains a full runner job and hardcodes
`uibcdf/gh-run-receptor@0.18.0`. The repository has no `workflow_call` trigger. GitHub's
current official workflow syntax documents `$/path/to/action` as a same-repository,
same-commit reference that needs no checkout; it requires runner 2.336.0 or newer and is
not available on older GitHub Enterprise Server versions.

No runner-time saving is assumed. The expected benefit is a smaller, revision-coherent
client configuration and one maintained output contract.

## What was refuted

- Calling `uibcdf/gh-run-receptor@main` internally is rejected because the caller's pinned
  workflow revision could execute moving Action code.
- Hardcoding the latest release tag internally is rejected because wrapper and core could
  drift and every release would require an otherwise unnecessary rewrite.
- Exposing `report-path` is rejected because that path belongs to the called job's runner
  and is meaningless to later caller jobs.
- Moving terminal truth back inside the active source run is rejected because GitHub has
  not assigned a terminal conclusion while that run is executing.

## Scope and exclusions

This increment does not aggregate arbitrary user-supplied job outputs, consume producer
event artifacts, classify comparison regressions, or claim GitHub Enterprise Server
support for `$/`. It does not replace the trigger workflow: clients still decide which
completed source workflows invoke the reusable reporter.

## Acceptance criteria

- The workflow is callable, manual-testable, read-only, and bounded by a timeout.
- Every accepted input is forwarded exactly once to the shared Action.
- Workflow outputs exclude local paths and mirror the durable Action scalars.
- The Action reference is `$/`-based, contains no branch/tag/SHA, and needs no checkout.
- A remote caller sees the expected terminal success, CI profile, ready state, and exact
  attempt-qualified artifact name for a retained source run.
- Tests reject automatic triggers, permission expansion, unpinned external actions, and
  a hardcoded internal Action ref.

## Dependencies and risks

No tracked issue blocks github.com delivery. The self-reference depends on current hosted
runners; the product already describes github.com as the initial network target.

## Provenance

Design audit: Linux host, Python 3.13.14, commit `ede4b8a`, 2026-09-07. GitHub syntax was
checked against the official documentation current on the same date. Hosted provenance
will be recorded before closure.
