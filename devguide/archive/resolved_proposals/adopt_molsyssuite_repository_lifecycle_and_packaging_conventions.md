---
summary: Adopt MolSysSuite repository lifecycle and packaging conventions
issue: uibcdf/gh-run-receptor#1
status: resolved
opened: 2026-09-04
closed: 2026-09-04
verification: measured
area: ['governance', 'packaging']
guard: tests/test_repository_conventions.py
normative: reporting_protocol.md
blocked_by: []
supersedes: []
---

# Adopt MolSysSuite repository lifecycle and packaging conventions

**Reported:** 2026-09-04, while deciding whether the first functional release should
receive another tag.
**Status:** Resolved in `198653b`; the conventions and their executable guards are on
`main`.

## What

Adopt three established MolSysSuite repository conventions: issue-backed developer
reports, versions derived from three-component Git tags, and a flat Python package layout.

## How

Port the lifecycle invariants from MolSysMT in a smaller implementation appropriate for a
new repository. Keep generated pending and archive indexes, validate report front matter
offline, and provide a GitHub-aware helper for opening, synchronizing, and closing issues.

Make `versioningit` the build-time source of version truth. Preserve the existing `0.1.1`
tag at its original commit and derive all later development and release versions from Git.
Move `gh_run_receptor` from `src/` to the repository root and remove path injection from
the checkout launcher.

## Why

The repository otherwise has three avoidable sources of divergence: developer documents
can lose their public identity, a static version can disagree with a tag, and its package
layout differs from the MolSysSuite projects maintained by the same team. Adopting these
conventions early makes the next release reproducible and leaves a checkpoint usable by a
developer who did not participate in the design conversation.

## What is measured and what is assumed

Inspected MolSysMT's `devguide/reporting_protocol.md`, report tools, `pyproject.toml`,
package initialization, and ignore rules. Inspected the equivalent package and version
configuration in MolSysViewer. No performance claim is made.

## What was refuted

Keeping a static version was rejected because it creates a second manually maintained
source of truth. Moving or recreating tag `0.1.1` was rejected because published Git
identities are immutable. Copying MolSysMT's full reporting implementation verbatim was
rejected because this repository has no migrated historical corpus or exceptional queues;
the lifecycle invariants are retained without project-specific machinery.

## Scope and exclusions

This work does not publish a package, create a new release tag, define release automation,
or import MolSysMT's historical reports. It does not make archived reports required
reading.

## Acceptance criteria

- Pending documents require unique `uibcdf/gh-run-receptor#N` identities and valid
  lifecycle metadata.
- Resolved reports require a real guard or normative document and correct archive
  placement.
- Queue indexes are generated and checkable without network access.
- The GitHub helper opens, synchronizes, and closes the public issue record.
- `pyproject.toml` has a dynamic version written by `versioningit`.
- The import package is at repository root and no `src/` directory remains.
- Ruff, the full receptor-formatted test suite, source/wheel builds, and installed-wheel
  version smoke tests pass.

## Dependencies and risks

No tracked dependency. Creating and synchronizing public issues requires an authenticated
GitHub CLI; all local validation remains offline.

## Provenance

Repository inspection and runtime validation on 2026-09-04 with Python 3.13 and
`versioningit 3.3.0`. `ruff check --no-cache .` passed; the complete suite passed with 36
tests through `pytest-receptor`; isolated sdist and wheel builds succeeded. The clean
commit produced version `0.1.1+1.g198653b`, and a fresh virtual environment reported that
same version from the installed wheel.
