---
summary: Retain primary Conda acquisition failures before later cleanup diagnostics.
issue: uibcdf/gh-run-receptor#81
status: active
opened: 2026-11-11
closed:
severity: medium
verification: inspected
area: [reports]
guard:
normative:
blocked_by: []
supersedes: []
---

# Issue #81 owner investigation

## Scope and acceptance

Public SMonitor and DockingMT controls report libmamba download error (28) before setup-micromamba ENOENT; a related Sabueso control reports a missing micromamba release/platform binary before a cleanup JSON error. The bounded candidate reader currently recognizes cleanup but misses the initial transport messages. Add source-linked primary candidates, bounded later context, negative and independent-cleanup controls without changing native results.

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
