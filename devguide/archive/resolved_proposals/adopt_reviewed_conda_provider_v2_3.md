---
summary: Review the delivered Conda provider and shared publisher adoption.
issue: uibcdf/gh-run-receptor#80
status: resolved
opened: 2026-11-11
closed: 2026-11-11
verification: measured
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


## Exact-source acceptance and disposition — 2026-11-11

Resolved at product/documentation candidate
54a21ddb2d7488fef823cd490ca7d274fd4c6f54. All nine source workflows pass with
independent native run/job/required-step verification: routine 43119661027,
twelve-cell compatibility 43119743508, policy 43119661383, Conda governance
43119661689, strict docs/Pages 43119660906, frozen contracts 43119747698,
three-OS Action 43119752174, exit codes 43119755988 and reusable distribution
43119760036. The linked evidence receipts retain full native job/step inventories.

A local exact-tag wheel/sdist rehearsal passes archive inspection and isolated
version/import/resource/command checks. Shared installed support executes 731
product/integration tests with one honest Conda-only skip and 193 separately
required tooling deselections; all tooling has the twelve-cell source credit
above. Imported support/resources retire successfully. The first wheel rehearsal
lacked the required SDK path and failed eight tests; the corrected declared input
passes against the unchanged wheel. No artifact rebuild or test weakening
provided this receiving. The local renderer is published Pytest Receptor 1.1.0
with --receptor=llm; the native installed descriptor retains --receptor=ci.

This closes implementation/review, not publication. #84 retains the required
original-file Conda native receiving, public channels/files, exact-tag extension
and independent archival gates. Central advance notice is
uibcdf/molsyssuite#191; consumer adoption is separately owned.
