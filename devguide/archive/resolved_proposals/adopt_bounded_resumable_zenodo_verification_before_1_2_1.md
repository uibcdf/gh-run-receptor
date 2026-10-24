---
summary: Adopt bounded resumable Zenodo verification before 1.2.1.
issue: uibcdf/gh-run-receptor#70
status: resolved
opened: 2026-10-24
closed: 2026-10-24
verification: measured
area: [governance, github]
guard: tests/test_zenodo_recovery_workflow.py
normative: versioning_and_releases.md
blocked_by: []
supersedes: []
---

# Bounded archival recovery for the next release

The auxiliary project explicitly elects continued archival for 1.2.1. The
current shared policy requires resumable discovery before that release; the
old manual exact-version check is retained but does not implement that lifecycle.

The new caller reuses the already accepted immutable provider
`6d6172d6cd00c5ac2d4ebadb71df554ec5b7fa26`, concept DOI
`10.5281/zenodo.22843377` and fixed cutoff `2026-10-24T00:00:00Z`.
Release publication, nominal six-hour scans and exact-tag manual checks share
its read-only state/discovery tool. The provider owns pagination, request/size
bounds, the original-publication 72-hour window and thirty-day sanitized receipt
retention; no implementation is copied or account mutation introduced.

The local caller guard checks fixed discovery, events, concept, immutable source
and read-only permissions. Source preflight reviews 28 routes after inventorying
the new workflow. Native receiving against historical 1.2.0 and the later actual
1.2.1 record are separate measured gates; no DOI/archival success is claimed yet.

The pinned provider's local exact-tag read-only probe independently verifies the
existing 1.2.0 record with its original publication age (over 500 hours), without
resetting the clock. This is tool receiving evidence, not archival of 1.2.1;
the hosted caller and first new-version observation remain pending.

## Measured receiving — 2026-10-24

The released caller at `a23e1910be1c4640135ccfe5a693cca08c1480d9` passed its
workflow guard and 28-route source preflight. Native historical receiving
`40131690998` verified 1.2.0 without resetting its publication age. Exact-tag
1.2.1 receiving `40132825451` and manual empty-tag discovery `40133571409`
executed the pinned provider and preserved verified public JSON receipts.
The scan discovered 1.2.1 after the fixed cutoff. Cron execution and future
ingestion-pending/overdue incidents are not claimed as observed.

Bounded, digest-checked, non-extracting receipt reads and an independent anonymous
semantic check verify version DOI `10.5281/zenodo.23627112`, concept DOI
`10.5281/zenodo.22843377`, publication date 2026-10-24 and exactly one source ZIP:
`uibcdf/gh-run-receptor-1.2.1.zip`, 761878 bytes,
`md5:8151ad8b0f485fcb94369011291cb21f`. No wheel/sdist archival is inferred.
The [public receipt](../../evidence/release_1_2_1_public.json) preserves both
new-version observations and actual artifact identities. The
[normative release guide](../../versioning_and_releases.md) owns ongoing recovery;
`uibcdf/molsyssuite#138` receives the public facts. Earlier pending statements
above describe preparation history. Adoption and first receiving are complete.
