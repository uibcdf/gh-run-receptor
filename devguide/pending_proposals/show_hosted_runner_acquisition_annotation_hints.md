---
summary: Expose bounded job-linked hosted-runner acquisition hints.
issue: uibcdf/gh-run-receptor#82
status: active
opened: 2026-11-11
closed:
verification: inspected
area: [reports]
guard: tests/test_runner_hints.py
normative: timeout_diagnosis.md
blocked_by: []
supersedes: []
---

# Issue #82 owner investigation

## Scope and acceptance

A PharmacophoreMT cancelled macOS job has source-linked failure annotations reporting acquisition failure and repeated arm64 capacity notices. Extend the existing termination hint contract with short deduplicated source-linked hints. Keep cause unknown, require exact annotation identity, and test notice-only, ambiguous, missing, partial, malformed and hostile cases. Do not infer cause from runner_id=0 or absent steps.

## Evidence state

The incoming issue and its linked public observations are inspected. Proposed
implementation and exact-candidate/native/public receiving are not yet verified.
Add only reviewed sanitized fixtures; raw captures stay in the task-owned
temporary capsule. No existing release tag, package or historical receipt changes.

## Workspace provenance — 2026-11-11

Clean starting source: 08bad8de95a70c31ea5f0c25b10d83d7457932d1, after a
fast-forward of two synchronized-guide commits. Linux Python 3.14.7, Ruff
0.16.5. The shared development runtime imports this src checkout. Shared
pip check reports twelve unrelated pre-existing dependency conflicts/missing
requirements; these are not repaired or credited as a clean dependency gate.
Isolated task-owned published inspection/test tools preserve the caller environment.


## Measured owner implementation — 2026-11-11

The implementation/review is complete locally. The new semantic subset fails
43 cases against the unchanged published 1.4.0 wheel and passes after the fix;
the complete new source suite passes 924 tests with one explicit Conda-only
source skip. Frozen contracts, 465-function scope inventory, thirty distribution
routes, Ruff and strict Sphinx pass. The reviewed original five acquisition
captures keep their authoritative failure/exit 1 and now expose initial causes;
original exact runner annotations keep failure/unknown cause/exit 1 and expose
two deduplicated hints. See the sanitized diagnostic validation receipt and the
separate #79/#80 owner-review receipt in devguide/evidence.

Exact-source native and source/installed publication gates remain pending under
#84. This record does not claim a new delivered version or completed consumer
adoption. Historical source/package facts remain unchanged.
