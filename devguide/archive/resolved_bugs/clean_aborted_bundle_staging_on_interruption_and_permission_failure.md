---
summary: Clean resources after aborted GitHub evidence capture
issue: uibcdf/gh-run-receptor#63
status: resolved
opened: 2026-10-07
closed: 2026-10-07
severity: medium
verification: reproduced
area: ['github', 'tests']
guard: tests/test_bundle_resources.py
normative:
blocked_by: []
supersedes: []
---

# Clean resources after aborted GitHub evidence capture

**Reported:** 2026-10-07, during uibcdf/molsyssuite#104 component-tool review.
**Status:** source repair and regression proof complete; exact hosted gates pending.

## What

At c2c952946ccc4c57da0f64dbeec632fc93fb2f70, capture_bundle leaves its private
preparation directory on KeyboardInterrupt/SystemExit or initial chmod failure.
An interrupted refresh after moving the old bundle aside does not restore the
caller destination. JSON/download acquisition can leave a live gh child and open
stdout pipe; interrupted binary acquisition also retains partial bytes.

## How

The permission operation preceded capture's try block. Capture cleanup and refresh
rollback caught Exception, excluding interruption/process exit. Popen had no owned
child lifecycle around either transport loop; binary removal had the same exception
coverage gap. The repair protects chmod, cleans unpublished staging and restores
old evidence on BaseException, then re-raises. A private reusable GitHub adapter
context owns child termination/reaping on failed consumption and stdout closure
on every exit; both transport operations call it. Partial downloads are removed
on all aborted exits, retaining existing OSError/AcquisitionError classification.
The reading body waits for a successful child; the caller owns stderr's temporary file.
Cleanup errors propagate with the original failure as exception context.

## Why

Incomplete raw evidence and live child resources can accumulate during interrupted
inspection. Caller evidence must remain addressable after a failed refresh. This
is acquisition resource ownership, with no change to authoritative GitHub facts.

## What is measured and what is assumed

All filesystem operations and transport child processes in the regression are real;
API responses and injected interruptions/permission/pipe faults are controlled.
No live network request is needed to prove this local mechanism.

- Before capture repair: 7 failed, 3 passed with
  `python -m pytest tests/test_bundle_resources.py --receptor=llm` (10 initial cases).
- Before refresh repair: both real rename/rollback regressions fail with
  `python -m pytest tests/test_bundle_resources.py -k interrupted_refresh --receptor=llm`.
- Before adapter repair: all 8 transport cases fail with
  `python -m pytest tests/test_bundle_resources.py -k transport --receptor=llm`:
  six interrupted/error children remain running and two success paths leave stdout open.
  Test teardown terminates/reaps the intentionally failing-before children.
- After all three repairs: 126 passing selected checks across the new module and
  existing GitHub/bundle/service/CLI tests. Twenty resource cases pass: 17 fail
  against their respective original operations; three capture controls pass before.
- The unchanged pinned SDK preflight verifies 27 declared-and-installed public-bound
  routes and all nine serialized resources against their original freeze tags.

An initial full-source check had 633 passes, six skips and one stale queue-index
failure while the report template was still being completed. That is an intermediate
failure, not a final gate. Index/report completion and the final source checks are
recorded in the qualification checkpoint below and owning issue delivery.

## What was refuted

The initial corpus validator's TemporaryDirectory already owns its temporary work.
Completed evidence/cache is useful caller output, not disposable preparation.
Blind cache cleanup, a global cleaner, a second acquisition adapter, changing native
GitHub outcomes, and rebuilding public artifacts do not solve these lifecycle gaps.
A proposed second issue for the related transport finding was rejected by automatic
approval review as avoidable separate coordination; the evidence and repair remain
in this coherent aborted-acquisition theme, #63.

## Scope and exclusions

Bundle preparation/refresh and JSON/binary transport resources only. Ctrl+C still
returns CLI exit 130; process exits and cleanup failures remain visible. Successful
bundle content, frozen schemas, cache keys, API/renderer policy and caller outputs
are unchanged. No signal handler, timeout/retry policy, process-group supervision,
scientific run, package release or consumer pin/guide migration. SIGKILL/crash and
failure to perform filesystem/OS cleanup cannot promise disposal; report failures
rather than erase caller data. Complete historical resource cleanup remains owner work.

## Acceptance criteria

- Remove only this capture's unpublished directory on permissions/failure/interruption.
- Keep successful bundles and unrelated caller evidence; restore the previous bundle
  after interrupted refresh without changing its bytes.
- Terminate and reap a failed/interrupted child and close stdout; successful children
  retain their result/output and close the pipe.
- Remove partial aborted downloads; preserve CLI/source truth and error/exit semantics.
- Propagate cleanup failures, with a durable relevant/addressable module guard.

## Dependencies and risks

MolSysSuite #104 coordinates member lifecycle adoption; installed/public consumer
adoption is independent. The qualified workspace retains the seven accepted #82
conflicts. No new provider contract or dependency is required. Retrospective resources
may belong to active/human tasks; no blanket deletion is authorized.

## Provenance

2026-10-07, Linux x86_64, Python 3.14.7 in molsyssuite@uibcdf_3.14.
Primary editable pytest-receptor and gh-run-receptor origins and caller environment
are preserved. Source tests import this isolated clone. Restricted-sandbox real-child
checks work without network or environment reinstall.

## Final local qualification checkpoint — 2026-10-07

`GH_RECEPTOR_SUITE_ROOT=/tmp/molsyssuite104-ghr-review-sdk python -m pytest --receptor=llm`
passes 647 tests with one explicit installed-Conda-only skip (no archive installed).
The SDK checkout is immutable 38db709ecc07451ff36ea84573d585f9af6b4df7, unchanged
from member inventory. All twenty resource regressions and the full ordinary
source suite are included; actual Conda installed/platform evidence is not claimed.
Generated indexes, offline report lifecycle, whole-repository Ruff lint/formatting
and the nine-contract/27-route preflight pass. Exact native source/administrative
proof will be attached to the owning closing issue and central #104 receipt,
separately from public release or receiving adoption.
