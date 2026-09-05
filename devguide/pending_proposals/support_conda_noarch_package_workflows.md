---
summary: Support Conda noarch package workflows
issue: uibcdf/gh-run-receptor#7
status: open
opened: 2026-09-04
closed:
verification: asserted
area: ['profiles', 'tests']
guard:
normative:
blocked_by: []
supersedes: []
---

# Supporting Conda noarch package workflows

**Reported:** 2026-09-04, while validating the first MolSysViewer client rule against a
public package run.
**Status:** Open; implementation and client validation are in progress.

Remove `severity` for proposals. The directory identifies the report kind.

## What

Extend the Conda profile so a repository can explicitly declare a `noarch` package
workflow. The current native-matrix interpretation is truth-preserving but produces the
uninformative `platforms=0/0` for MolSysViewer.

## How

Add `settings.package_kind` with the bounded values `native` and `noarch`. Absence retains
the current native behavior. A noarch rule cannot also declare `expected_platforms`.
Noarch is never inferred merely from the absence of platform names: a targeted native
retry can also contain zero or one recognizable platform.

The report retains `matrix.kind=conda` for profile compatibility and adds
`package_kind=noarch` plus one package summary containing all job IDs, official job-state
counts, artifact IDs, and artifact evidence. Artifact evidence distinguishes:

- `available`: at least one observed artifact is explicitly not expired;
- `expired`: every observed artifact is explicitly expired;
- `observed`: artifacts exist but their expiry state is unknown;
- `not_observed`: the complete current inventory is empty;
- `unknown`: the inventory is incomplete and empty.

`not_observed` deliberately does not mean that an artifact never existed. GitHub may have
deleted an expired artifact, and a Conda action may publish directly to a channel without
creating a GitHub Actions artifact.

## Why

MolSysViewer's package is `noarch: python`, so a native platform matrix is the wrong unit
of interpretation. A compact report should say what kind of package workflow ran and what
artifact evidence remains without inventing per-platform reuse or channel publication.

## What is measured and what is assumed

Public MolSysViewer run `20548716947` has GitHub conclusion `success`, three successful
jobs named `Conda deployment of package with Python 3.10`, `3.11`, and `3.12`, and an empty
current GitHub artifact inventory. With the 0.4.0 client rule it rendered:

```text
PASS conclusion=success | profile=conda | platforms=0/0 | jobs=3/3 | artifacts=0 | uibcdf/molsysviewer run=20548716947
```

The metadata was captured with:

```text
gh run-receptor --repo uibcdf/molsysviewer --format=json inspect 20548716947 \
  --capture metadata --output BUNDLE
```

The empty inventory is measured. Whether the historical run once had a GitHub artifact is
unknown; direct Anaconda publication is also not proven by current structured evidence.

## What was refuted

- Inferring noarch from zero observed native platforms is rejected because targeted native
  workflows have the same shape.
- Treating an empty artifact response as `expired` is rejected because GitHub does not
  retain the record indefinitely and some workflows never upload a GitHub artifact.
- Calling a successful job or action step proof of channel publication is rejected until
  structured producer or channel evidence exists.
- Reusing the native `reusable` label is rejected: a noarch package has no independent
  platform member to reuse.

## Scope and exclusions

This slice does not verify package metadata, build contents, Python compatibility, upload
credentials, Anaconda channel state, or producer events. It does not auto-detect noarch,
change native-matrix behavior, or add workflow mutation and rerun commands.

## Acceptance criteria

- Configuration accepts only `native` or `noarch`, only for `conda`.
- `package_kind=noarch` and `expected_platforms` cannot coexist.
- Noarch output never renders `platforms=0/0`.
- JSON retains every job and artifact identity plus bounded package interpretation.
- Empty complete inventories say `not_observed`, never `expired` or `never created`.
- Available, expired, unknown-expiry, and empty complete-inventory cases are tested.
- A failing noarch run remains official `failure` and receptor `FAIL`; an artifact alone
  cannot produce native-matrix `PARTIAL` semantics.
- The public MolSysViewer run becomes a reviewed sanitized fixture after the released
  parser can capture the adopted default-branch rule.
- MolSysViewer adopts the setting only after the implementing tag exists.

## Dependencies and risks

No external dependency blocks implementation. The live fixture and client adoption are
ordered after the tag so an existing pinned 0.4.0 installation never encounters an
unsupported setting on the client's default branch.

## Provenance

Measured on 2026-09-04/05 on the local Linux development host with Python 3.13 and GitHub
CLI 2.93.0, authenticated against the public `uibcdf/molsysviewer` repository. The source
run is attempt 1 of `20548716947`; GitHub retention limits what can be concluded from its
current artifact inventory.
