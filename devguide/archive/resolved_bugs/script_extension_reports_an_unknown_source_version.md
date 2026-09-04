---
summary: Script extension reports an unknown source version
issue: uibcdf/gh-run-receptor#3
status: resolved
opened: 2026-09-04
closed: 2026-09-04
severity: medium
verification: reproduced
area: ['packaging', 'cli']
guard: tests/test_source_version.py
normative: versioning_and_releases.md
blocked_by: []
supersedes: []
---

# Script extension reports an unknown source version

**Reported:** 2026-09-04, during the remote installation smoke test for tag `0.2.0`.
**Status:** Resolved in `f77cf3f` and released as `0.2.1`; reproduced from `0.2.0` and
verified through a fresh remote extension installation pinned to the corrective tag.

## What

The GitHub CLI script extension installs and runs from tag `0.2.0`, but cannot report its
revision:

```text
gh extension install uibcdf/gh-run-receptor --pin 0.2.0
gh run-receptor --version
0+unknown
```

## How

`versioningit` writes `_version.py` while building an sdist or wheel, and installed Python
metadata is available after package installation. A GitHub CLI script extension instead
clones the repository and executes its root launcher directly. The ignored generated file
and installed metadata therefore do not exist in that environment.

Add a final source-checkout fallback that invokes `git describe` without a shell, accepts
only the repository's numeric three-component tag convention, and translates long output
to the same PEP 440 local-version shape used by `versioningit`. Installed metadata and the
generated build file retain precedence.

## Why

The command works, but a user cannot verify that the extension is actually pinned to the
expected release. That defeats the reproducible installation instruction intended for
MolSysMT development.

## What is measured and what is assumed

Observed after a real remote clone into GitHub CLI's extension directory. `gh` printed the
expected clone operation and the extension printed `0+unknown`. No performance estimate is
made; the fallback runs one bounded Git subprocess only when package metadata and generated
build version are both absent.

## What was refuted

Moving tag `0.2.0` was rejected because release identities are immutable. Committing a
manually updated version module was rejected because it restores a second source of truth.
Installing the Python package on first extension execution was rejected because it mutates
the user's environment and may require network access.

## Scope and exclusions

This fix does not publish a binary extension or a package-index artifact. It addresses only
version discovery for a Git-backed script extension checkout.

## Acceptance criteria

- An exact clean numeric tag renders exactly `X.Y.Z`.
- Later and dirty commits render valid local version identifiers.
- Unexpected tag formats and Git failures degrade to `0+unknown`.
- Installed metadata and generated build versions remain higher precedence.
- A remote extension pinned to the corrective tag reports that exact tag.

## Dependencies and risks

No new dependency. Git is already required by GitHub CLI to clone a script extension. A
two-second timeout prevents version display from hanging on a damaged checkout.

## Provenance

Reproduced on 2026-09-04 with Python 3.13 and the installed GitHub CLI. Ruff passed and the
full suite reported 48 passing tests. The isolated sdist-to-wheel build and installed-wheel
smoke test both reported exactly `0.2.1`. A fresh
`gh extension install uibcdf/gh-run-receptor --pin 0.2.1` clone then reported `0.2.1`, with
Git describing its checkout as `0.2.1-0-gf77cf3f`.
