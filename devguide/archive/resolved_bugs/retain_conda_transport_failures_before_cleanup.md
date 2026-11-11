---
summary: Retain primary Conda acquisition failures before later cleanup diagnostics.
issue: uibcdf/gh-run-receptor#81
status: resolved
opened: 2026-11-11
closed: 2026-11-11
severity: medium
verification: measured
area: [reports]
guard: tests/test_acquisition_diagnostics.py
normative: rules_and_profiles.md
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
