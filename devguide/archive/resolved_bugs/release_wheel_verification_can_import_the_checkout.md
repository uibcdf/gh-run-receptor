---
summary: Release wheel verification can import the checkout
issue: uibcdf/gh-run-receptor#36
status: resolved
opened: 2026-09-08
closed: 2026-09-08
severity: medium
verification: reproduced
area: ['packaging']
guard: tests/test_publish_release_workflow.py
normative:
blocked_by: []
supersedes: []
---

# Preventing checkout-shadowed wheel verification

**Reported:** 2026-09-08, while independently verifying the 0.19.1 release wheel.
**Status:** Resolved locally after the immutable 0.19.1 tag; the next publisher revision
imports from an isolated working directory and asserts the imported path.

Remove `severity` for proposals. The directory identifies the report kind.

## What

The exact-tag publisher installed the wheel under `$RUNNER_TEMP/install`, set
`PYTHONPATH` to that directory, and invoked Python while its working directory remained
the repository root. Python placed the empty current-directory entry before `PYTHONPATH`,
so `import gh_run_receptor` resolved to the checkout rather than the installed wheel.

The same sequence was reproduced locally. From the checkout it printed
`/home/diego/repos@uibcdf/gh-run-receptor/gh_run_receptor/__init__.py`; after changing the
working directory to `/tmp` it printed the isolated installation path.

## How

`PYTHONPATH` does not remove Python's first search entry. Running `python -c` from the
checkout therefore allowed a valid source tree to mask a missing or invalid wheel payload.
The workflow now changes into `$RUNNER_TEMP` in a subshell before importing and additionally
asserts that `gh_run_receptor.__file__` starts with `$RUNNER_TEMP/install/`.

## Why

The old check could claim installed-artifact validation without exercising the installed
package. This is a release-gate integrity defect: a malformed wheel might pass despite the
source checkout being healthy.

## What is measured and what is assumed

Observed for the locally installed 0.19.1 wheel:

```text
PYTHONPATH=/tmp/gh-run-receptor-0.19.1.KufpUQ/install python -c \
  "import gh_run_receptor; print(gh_run_receptor.__file__)"
```

From the checkout this selected the checkout. Running the same command with `/tmp` as the
working directory selected
`/tmp/gh-run-receptor-0.19.1.KufpUQ/install/gh_run_receptor/__init__.py`.

The public 0.19.1 wheel was separately downloaded, checksum-verified, installed, and
imported from outside the checkout, so this defect does not invalidate that release.

## What was refuted

Merely setting or prepending `PYTHONPATH` is insufficient because the current-directory
entry still wins. Checking only `__version__` is also insufficient because versioningit
derives the same tagged version in the checkout. Removing the checkout from the working
directory and checking the module path directly protects the intended property.

## Scope and exclusions

This change covers the wheel import in the exact-tag publisher. It does not attempt to make
Python builds byte-for-byte reproducible or change the separate extension-installation
and public-download gates.

## Acceptance criteria

- The publisher changes out of the checkout after installing the wheel.
- The import uses the isolated target directory.
- The gate asserts that the imported module path belongs to that target.
- A regression test checks the ordering and path assertion in the workflow.

## Dependencies and risks

No dependency blocks the fix. Because tag 0.19.1 is immutable, the corrected workflow
applies to subsequent releases rather than rewriting the published tag.

## Provenance

Observed on 2026-09-08 on the Linux development host with Python 3.13.14 and pip 25.3.
