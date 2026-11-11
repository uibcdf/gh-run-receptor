---
summary: Retain missing artifact diagnostics before empty evidence uploads.
issue: uibcdf/gh-run-receptor#83
status: active
opened: 2026-11-11
closed:
severity: medium
verification: inspected
area: [reports]
guard: tests/test_acquisition_diagnostics.py
normative: rules_and_profiles.md
blocked_by: []
supersedes: []
---

# Issue #83 owner investigation

## Scope and acceptance

DockingMT run 42976065511 attempt 2 first reports Artifact not found for name, then an always-upload step finds no files. Recognize the explicit missing-download message and artifact identity, retain bounded source-linked later diagnostic context, preserve standalone upload failures and never turn native failure into success.

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
