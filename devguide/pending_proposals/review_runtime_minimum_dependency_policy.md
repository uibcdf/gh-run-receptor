---
summary: Review and confirm runtime dependency minimum policy adoption.
issue: uibcdf/gh-run-receptor#79
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

# Issue #79 owner investigation

## Scope and acceptance

Audit required and optional runtime routes, package extras, Conda recipes and maintained acquisition paths against the provider>=X rule. Classify test/docs/build pins separately, justify actual API floors, correct only unjustified runtime bounds, execute applicable checks and return explicit Review completed evidence to MolSysSuite #137.

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
