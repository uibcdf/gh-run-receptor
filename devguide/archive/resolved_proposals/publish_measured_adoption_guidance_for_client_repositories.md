---
summary: Publish measured adoption guidance for client repositories
issue: uibcdf/gh-run-receptor#4
status: resolved
opened: 2026-09-04
closed: 2026-09-04
verification: measured
area: ['documentation', 'governance']
guard: tests/test_sync_guide.py
normative: ../standards/GH_RUN_RECEPTOR_GUIDE.md
blocked_by: []
supersedes: []
---

# Publish measured adoption guidance for client repositories

**Reported:** 2026-09-04, before beginning configuration work and MolSysMT adoption.
**Status:** Resolved in `d2f321a`; the guide was synchronized into MolSysMT in
`uibcdf/molsysmt@7e8af130e`.

## What

Put concise, qualified token-reduction evidence on the project front page and publish a
canonical guide that a client repository can carry as its local integration authority.

## How

The README presents two measured MolSysMT cases and the status-only counterexample, linking
to the reproducible benchmark rather than duplicating it. The canonical
`standards/GH_RUN_RECEPTOR_GUIDE.md` defines installation, pinning, receptors, capture,
replay, profiles, exit semantics, fallback, security, and a client checklist.

A dependency-free synchronization tool copies the exact guide to selected sibling roots as
`GH_RUN_RECEPTOR_GUIDE.md`. It supports `--dry-run`, exact `--check`, and repeatable
`--repo` selection so adoption can be incremental.

## Why

Without front-page evidence, users cannot quickly distinguish measured value from product
aspiration. Without a copied canonical guide, a client contributor needs the development
history or remote documentation to know what is safe and supported. The other MolSysSuite
infrastructure packages already use this pattern successfully.

## What is measured and what is assumed

The README numbers come unchanged from `devguide/benchmark_2026-09-04.md`: 5,138 to 296
`cl100k_base` tokens for the partial failure and 143 to 39 for green matrix verification.
The 10-token native status-only result is retained as a counterexample. No aggregate rate
or estimate is introduced.

## What was refuted

Advertising reduction against the 478,294-token unfiltered log was rejected as the headline
because a competent user filters before reading. Copying the full internal devguide to
clients was rejected because consumers need an integration contract, not development
history. Automatically writing every sibling repository during tests was rejected; tests
use disposable trees and synchronization is an explicit maintainer action.

## Scope and exclusions

This work does not implement repository rules, modify client workflows, or claim that
configuration designed in the devguide works in release `0.2.1`. The guide explicitly
marks those surfaces unavailable.

## Acceptance criteria

- README values and qualifications agree with the benchmark record.
- The guide is sufficient for a contributor without this conversation to install, use,
  interpret, and safely fall back from release `0.2.1`.
- Configuration and Action examples are not represented as implemented behavior.
- Synchronization writes exact copies, detects missing/stale copies, and supports dry-run.
- MolSysMT can receive the guide without copying internal gh-run-receptor history.

## Dependencies and risks

No dependency. The guide must be resynchronized whenever its integration contract changes;
`--check` makes that drift visible.

## Provenance

Benchmark provenance remains in `devguide/benchmark_2026-09-04.md`. Ruff and all 51 tests
passed locally with Python 3.13 on 2026-09-04. Exact synchronization was checked after the
MolSysMT copy was written, and MolSysMT's Ruff gate also passed.
