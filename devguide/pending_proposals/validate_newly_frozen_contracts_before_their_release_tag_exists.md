---
summary: Validate newly frozen contracts before their release tag exists
issue: uibcdf/gh-run-receptor#34
status: open
opened: 2026-09-08
closed:
verification: asserted
area: ['packaging', 'tests']
guard:
normative:
blocked_by: []
supersedes: []
---

# Validating newly frozen contracts before their release tag exists

**Reported:** 2026-09-08 while preparing the 0.19.0 contract freeze.
**Status:** Open; the implementation passes focused local tests and awaits the hosted
candidate gate.

## What

Allow a release candidate to declare new schemas frozen by the version being prepared
without requiring that tag to exist before local and hosted pre-tag validation.

## How

Add an explicit `--candidate X.Y.Z` mode to `validate_contracts.py`. It requires the
candidate tag to be absent, requires every packaged schema to declare a freeze, continues
comparing older resources with their original tags, and permits the candidate freeze only
when the resource did not exist in the selected published baseline. Normal validation
does not gain an exception and remains fail-closed until the new tag exists.

## Why

`config-capture@1`, `comparison@1`, and `comparison-policy@1` must be visibly frozen in
the source and installed inventory of 0.19.0. Tagging first would bypass the required
pre-tag gate; declaring the freeze after publication would make the released inventory
misrepresent its own contract status.

## What is measured and what is assumed

Before this change, assigning `frozen_since="0.19.0"` made ordinary validation fail because
`git show 0.19.0:<resource>` could not resolve a tag that correctly did not yet exist. The
new focused test proves candidate success against 0.18.0 and separately proves ordinary
mode failure before the tag. Local candidate validation reports seven contracts and seven
frozen schemas while preserving four 0.18.0 baselines.

## What was refuted

- Creating the tag before validation is rejected because validation must be a precondition
  for the tag, not a repair after it.
- Declaring `frozen_since` only after publication is rejected because the 0.19.0 artifact
  would continue to advertise provisional contracts.
- Blindly skipping every schema named with the candidate version is rejected because it
  would allow an already published schema to be relabeled and changed. Candidate resources
  must be absent from the prior baseline.
- Allowing candidate mode after the tag exists is rejected because it could bypass normal
  byte comparison.

## Scope and exclusions

This changes release validation only. It does not change schema contents, contract
versions, migration semantics, Git tags, or the GitHub Release publication workflow's
normal exact-tag comparison.

## Acceptance criteria

- Candidate version syntax is strict `X.Y.Z` without a prefix.
- Candidate validation refuses an existing candidate tag.
- Old frozen resources remain byte-compared with their original freeze tags.
- A resource present in the published baseline cannot be relabeled as newly frozen.
- Every packaged resource must be frozen for a release candidate.
- Ordinary validation fails before the candidate tag and passes from the exact tag.
- Unit, full-suite, and hosted candidate gates pass.

## Dependencies and risks

The hosted gate depends only on read access to the repository history. Publishing 0.19.0
depends on this proposal; the proposal is not blocked by the release.

## Provenance

Initial reproduction and focused validation: Linux, Python 3.13.14, 2026-09-08, starting
from commit `3c8c25d`.
