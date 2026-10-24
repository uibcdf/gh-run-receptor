---
summary: Adopt bounded resumable Zenodo verification before 1.2.1.
issue: uibcdf/gh-run-receptor#70
status: active
opened: 2026-10-24
closed:
verification: inspected
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
