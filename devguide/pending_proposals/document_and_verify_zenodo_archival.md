---
summary: Document and verify Zenodo archival
issue: uibcdf/gh-run-receptor#27
status: active
opened: 2026-09-07
closed:
verification: asserted
area: ['packaging', 'documentation']
guard:
normative:
blocked_by: []
supersedes: []
---

# Documenting and verifying Zenodo archival

**Reported:** 2026-09-07, after publishing the first verified GitHub Releases and observing
no matching public Zenodo record.
**Status:** Active; the maintainer handoff and read-only verification contract are being
implemented.

## What

The repository contains valid Zenodo ingestion metadata, but that only prepares a future
archive. It does not enable the repository in a maintainer's Zenodo account, ingest a
release, assign a DOI, or verify a record. The current developer policy explains this
boundary but does not give maintainers an executable activation and verification checklist.

## How

Document the account-side activation steps in the maintainer release policy and link the
official Zenodo instructions. Extend `devtools/scripts/release_tools.py` with a read-only
Zenodo verifier that consumes a saved public API response offline. It must report exactly
one of three states: absent, verified, or invalid/ambiguous. Verified requires an exact
project title and release version, a DOI, matching creators, a source-repository relation,
and nonempty archived files. Network acquisition remains a small manual command so the
runtime package acquires no HTTP client or Zenodo coupling.

## Why

This gives a new maintainer enough information to finish archival without this
conversation, while ensuring the project never equates a GitHub Release or metadata file
with a DOI. Keeping the verifier in release tooling preserves the general-purpose receptor
boundary.

## What is measured and what is assumed

An anonymous query to `https://zenodo.org/api/records/` for exact title
`gh-run-receptor`, including all versions, returned `hits.total: 0` after releases 0.17.0
and 0.18.0 were published. Zenodo documents that repositories must be enabled from the
connected account and that ingestion may take time. Whether the repository is enabled is
not visible through the GitHub or anonymous Zenodo records APIs.

## What was refuted

- A successful GitHub Release is not archival evidence; the public query refuted the
  equivalence immediately.
- Adding Zenodo lookup to the receptor runtime is rejected because this task concerns the
  receptor project's publication, not GitHub Actions evidence for arbitrary users.
- A title-only hit is insufficient because another version or unrelated record could match.
- Automatically mutating a Zenodo account is outside the granted authority and would
  require credentials plus a separate security boundary.

## Scope and exclusions

This work does not enable the account integration, upload a deposit through an API token,
reserve or invent a DOI, or add Zenodo as a product evidence source. It also does not block
GitHub Release publication when Zenodo is delayed or absent.

## Acceptance criteria

- The documented procedure states who performs each account-side step and when.
- Offline fixtures cover absent, verified, malformed, ambiguous, wrong-version,
  wrong-repository, missing-DOI, creator-mismatch, and missing-file responses.
- The verifier emits bounded output and a distinct non-success status for absence.
- Verification checks meaning rather than a favorable title string.
- The runtime dependency list and public receptor CLI remain unchanged.

## Dependencies and risks

Completion of a real verified record depends on a maintainer enabling the repository in
Zenodo and on asynchronous ingestion. That external step is not represented as a blocking
repository issue because this increment can deliver and validate the procedure while
honestly retaining the observed `absent` state.

## Provenance

The initial query was performed 2026-09-07 from the development host against Zenodo's
anonymous public records API after GitHub Release 0.18.0. Local implementation uses Python
3.13 and saved JSON fixtures; it must not require network access during pytest.
