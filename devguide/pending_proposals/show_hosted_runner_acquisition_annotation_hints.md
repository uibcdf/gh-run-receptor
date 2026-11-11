---
summary: Expose bounded job-linked hosted-runner acquisition hints.
issue: uibcdf/gh-run-receptor#82
status: active
opened: 2026-11-11
closed:
verification: inspected
area: [reports]
guard:
normative:
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
