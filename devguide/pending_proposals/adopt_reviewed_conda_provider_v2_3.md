---
summary: Review the delivered Conda provider and shared publisher adoption.
issue: uibcdf/gh-run-receptor#80
status: active
opened: 2026-11-11
closed:
verification: inspected
area: [distribution]
guard:
normative:
blocked_by: []
supersedes: []
---

# Issue #80 owner investigation

## Scope and acceptance

Review MolSysSuite 95f693be10c9205ab9b912cb53453710a207bf45 and external Conda provider v2.3.0 source 87c70b1443d5f22d738ee3ddf812bdbe0152f6c2. Preserve src-resource mapping, installed support @1, original producer/file identities, separate promotion and required gates. Adopt compatible operations with explicit source/hash inventory changes; report any shared gaps to their owner rather than copying provider implementation.

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
