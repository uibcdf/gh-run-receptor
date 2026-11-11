---
summary: Review the delivered Conda provider and shared publisher adoption.
issue: uibcdf/gh-run-receptor#80
status: active
opened: 2026-11-11
closed:
verification: inspected
area: [packaging]
guard: tests/test_conda_distribution.py
normative: installed_qualification.md
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

Ten shared source/resource/installed/support/verification operations are
byte-identical from fee3bd8 to reviewed 95f693b. Current publisher/promotion,
checks and operator pins are updated consistently, as are their owner digest
inventory and existing assertion guards. The shared release contract suite
passes 28 tests; this is offline administrative proof, not a real upload.
