---
summary: Validate the Python CLI across supported platforms
issue: uibcdf/gh-run-receptor#16
status: active
opened: 2026-09-06
closed:
verification: inspected
area: ['packaging', 'tests', 'cli']
guard:
normative:
blocked_by: []
supersedes: []
---

# Validate the Python CLI across supported platforms

**Reported:** 2026-09-06, after the Linux-only 0.10.0 release gate.
**Status:** Active; the nine-combination compatibility workflow is designed but unmeasured.

## What

Add a manually dispatched compatibility workflow for Ubuntu, macOS, and Windows with
Python 3.11, 3.12, and 3.13. Each independent job runs the complete suite with
`--receptor=llm`, builds wheel and source distribution, installs the wheel, and exercises
the installed command outside the checkout.

## How

Use one explicit nine-entry matrix with `fail-fast: false`, a 15-minute per-job timeout,
read-only contents permission, and no secrets, caches, or uploaded artifacts. Checkout and
Python setup are pinned to reviewed full commit SHAs. Checkout fetches tags so
`versioningit` can produce a meaningful source version rather than `0+unknown`.

The workflow has `workflow_dispatch` only. Building in every matrix member is deliberate:
it tests platform-independent packaging assumptions and avoids treating one Linux-built
wheel as evidence for Windows and macOS tooling. The package has no runtime dependencies;
test/build dependencies are installed from the declared project metadata plus `build`.

## Why

Package metadata declares Python 3.11 through 3.13, while the release checkpoint currently
claims only a clean Linux wheel installation. The 1.0 gate requires explicit installation
paths and compatibility evidence for every named operating system and Python version.
OD-008 cannot be settled from local Linux success.

## What is measured and what is assumed

Local Linux validation of 0.10.0 passed 161 tests and clean wheel installation. Current
MolSysSuite workflows use `actions/checkout@v7` and `actions/setup-python@v7`. Their
official tag refs resolved on 2026-09-06 to:

- checkout: `3d3c42e5aac5ba805825da76410c181273ba90b1`;
- setup-python: `5fda3b95a4ea91299a34e894583c3862153e4b97`.

The first remote run, `34037154711` at commit `cdb6559`, passed all six Ubuntu and macOS
jobs and failed all three Windows jobs during pytest. The strict bundle loader found that
Git checkout had changed fixture JSON from LF to CRLF, invalidating the byte counts stored
in each fixture manifest. This is transport damage to byte-exact test data, not evidence
that the CLI itself is incompatible with Windows. The repository now declares LF checkout
for the fixture tree and guards that declaration before the matrix is rerun.

## What was refuted

- Testing only Python 3.13 on three operating systems is rejected because it does not
  support the declared 3.11--3.13 compatibility range.
- Building once on Linux and installing everywhere is rejected as the only packaging
  evidence because it skips native shell, filesystem, and build-tool behavior.
- Automatic push or scheduled execution is rejected because this is a release gate, not a
  cost justified on every commit.
- `fail-fast: true` is rejected because one platform failure must not erase evidence from
  the other eight combinations.
- Floating action tags are rejected for this security-sensitive gate.

## Scope and exclusions

This increment validates the Python CLI source distribution and universal wheel. It does
not yet validate GitHub CLI availability on each runner, the script-extension installation
path, PyPI publication, standalone binaries, the embedded Action, or GitHub Enterprise.
Those claims remain separate gates.

## Acceptance criteria

- The workflow can run only by explicit manual dispatch and uses read-only permissions.
- All nine OS/Python jobs run independently with bounded time.
- Every job passes the full pytest suite using `--receptor=llm`.
- Every job builds exactly one wheel and one sdist with a non-unknown derived version.
- Every job installs the wheel and invokes `gh-run-receptor --version` outside checkout.
- The observed run is inspected with gh-run-receptor and recorded in the checkpoint.
- Support documentation names only combinations that actually pass.
- OD-008 and the roadmap are updated from measured evidence, not workflow intent.

## Dependencies and risks

There is no blocker. Package-index availability and transient runner setup can fail
independently of source compatibility; the report must preserve that distinction. A
partial matrix remains useful evidence and must not be rerun wholesale without diagnosis.

## Provenance

Planning on Linux, Python 3.13.14, GitHub CLI 2.81.0, gh-run-receptor 0.10.0,
2026-09-06. Action SHAs were read from the official `actions/checkout` and
`actions/setup-python` repositories through the GitHub API.
