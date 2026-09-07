---
summary: Publish and verify reproducible GitHub releases
issue: uibcdf/gh-run-receptor#26
status: active
opened: 2026-09-07
closed:
verification: asserted
area: ['packaging', 'github']
guard:
normative:
blocked_by: []
supersedes: []
---

# Publishing and verifying reproducible GitHub releases

**Reported:** 2026-09-07, after the exact-tag 0.16.0 distribution gate passed while the
repository still exposed no GitHub Releases.
**Status:** Active; the publication contract and first hosted exercise are being built.

## What

Tags currently identify verified source, but users cannot download project-built wheel or
source-distribution assets from a GitHub Release. The repository also lacks citation and
Zenodo ingestion metadata, a reproducible publication workflow, and an independent check
that a published release still identifies the intended commit and bytes.

## How

Add an exact-tag release workflow which validates a three-component tag, checks out that
tag with full history, runs the full receptor-formatted suite, builds exactly one wheel and
one source distribution, installs the wheel outside the checkout, and verifies its version.
It then creates a draft GitHub Release with notes derived from the matching changelog
section, attaches both distributions and a checksum manifest, verifies draft identity and
asset bytes, and only then publishes it.

Keep the release verifier as a locally unit-tested script rather than workflow-inline
assertions. It must compare tag-to-commit identity, release state, expected asset names,
sizes, GitHub-reported SHA-256 digests, and the checksum manifest. Add `CITATION.cff` and
`.zenodo.json` with matching creators and project metadata before the first new release.
Zenodo verification remains observation-only: a GitHub Release is not evidence of a DOI,
and enabling the repository in a user's Zenodo account is not an operation delegated to
this workflow.

## Why

This closes the difference between source tags and installable public artifacts, makes the
release byte identity auditable, and supplies the metadata required for a future Zenodo
ingestion. It is the largest remaining cross-cutting release gap before 1.0.

## What is measured and what is assumed

Observed before implementation:

- `gh release list --repo uibcdf/gh-run-receptor` returns no releases;
- tag `0.16.0` builds and installs as exactly 0.16.0, but only locally;
- `gh api repos/uibcdf/gh-run-receptor/immutable-releases` reports `enabled: false`;
- the repository contains neither `CITATION.cff` nor `.zenodo.json`.

GitHub documents that releases package tagged source and binary assets, and that release
asset API records expose SHA-256 digests. Zenodo documents that an enabled GitHub
repository ingests newly published releases and that `.zenodo.json` takes precedence when
both supported metadata files exist. Whether this repository is enabled in the owning
Zenodo account cannot be inferred from the checkout or GitHub API.

## What was refuted

- Treating the existing tag as a release is refuted by GitHub's empty release inventory.
- Uploading assets directly in a published release is rejected because a draft permits
  complete verification before public exposure and is compatible with future immutable
  releases.
- Claiming Zenodo success from a successful GitHub job is rejected because ingestion is an
  independent external event.
- Enabling immutable releases automatically is excluded: it is an administrative policy
  change, not a normal product release step.

## Scope and exclusions

This increment publishes GitHub Release assets and prepares Zenodo metadata. It does not
publish to PyPI or Conda, mutate Zenodo account integration settings, manufacture a DOI,
enable immutable releases, or add mutation commands to the receptor's public CLI.

## Acceptance criteria

- The workflow accepts only an existing exact `X.Y.Z` tag and has one bounded writer job.
- The full suite, build, installed version, changelog section, and citation metadata pass
  before release creation.
- A draft contains exactly the wheel, source distribution, and checksum manifest expected
  for the tag, with matching nonzero sizes and SHA-256 values.
- Publication happens only after draft verification; final external verification repeats
  identity and asset checks against the public release.
- A hosted release exercise succeeds on a new preview tag and the installed asset reports
  exactly that tag.
- Zenodo presence or absence is reported as independent evidence without changing the
  GitHub Release verdict.

## Dependencies and risks

The GitHub workflow needs narrowly scoped `contents: write` permission. Interrupted draft
creation is deliberately fail-closed and requires explicit maintainer review rather than
automatic deletion. Zenodo ingestion depends on repository enablement in the account UI;
that dependency does not block GitHub publication and is not represented as a repository
issue until its state is observed.

## Provenance

Initial observations were made 2026-09-07 from the development host with Python 3.13 and
GitHub CLI 2.93.0 against `uibcdf/gh-run-receptor`. Hosted evidence will record its run,
tag, commit, asset names, and external release identifier.
