---
summary: Adopt inherited Python ecosystem tooling in GH Run Receptor
issue: uibcdf/gh-run-receptor#55
status: active
opened: 2026-09-24
closed:
verification: inspected
area: [governance, tests]
guard:
normative:
blocked_by: []
supersedes: []
---

# Adopt inherited Python ecosystem tooling in GH Run Receptor

**Reported:** 2026-09-24 during the MolSysSuite rollout of the pinned MOLI
Python ecosystem policies.

**Status:** Active; developer-tool CI is verified and the support-library
applicability review remains open.

## What

The `origin/main` snapshot at `11d33a6` runs the local-agent
`--receptor=llm` profile in four hosted pytest workflows: routine, weekly,
compatibility, and release publication. The `[test]` and `[dev]` extras
specify `pytest-receptor` without an exact release. This conflicts with the
inherited rule to use a published exact receptor release in CI and its `ci`
profile for ephemeral hosted logs.

## How

Pin published pytest-receptor `1.1.0` in both extras, select
`--receptor=ci` in all four hosted pytest calls, and retain each workflow's
existing test selection and build or release gates. Update the existing
workflow contract assertions. Run the component suite through the local
`--receptor=llm` profile, Ruff, the developer-guide validator, and the
MolSysSuite component checker before publishing. Verify hosted routine and
weekly lanes before claiming developer-tool adoption.

Review the four support-library applicability boundaries separately. In
particular, the CLI and public embedded API validate untrusted GitHub data
and report user-visible failures; whether ArgDigest or SMonitor should replace
the product's bounded local parsers and report model requires a product
decision and evidence. No physical-quantity conversion or optional runtime
backend has been identified in this initial inspection.

## Why

An LLM profile may refer to a local overflow file unavailable to readers of
a hosted log. An unpinned test extra can select a different release on the
next CI run. The inherited policy requires a member-local review before the
suite's inventory can claim adoption or a bounded exception.

## What is measured and what is assumed

The four commands and dependency declarations were inspected at
`origin/main` commit `11d33a6` using `git grep` and `git show`. The
published pytest-receptor `1.1.0` tag is present in its local repository.
The new workflows have not yet been executed on GitHub. The behavior of the
`ci` profile is described in the canonical `PYTEST_RECEPTOR_GUIDE.md`; it is
not being inferred from a passing local LLM-profile run.
The changed checkout passed `PYTHONPATH=. pytest --receptor=llm` with 453
tests, `ruff check .`, `ruff format --check .`, developer-guide validation,
and the MolSysSuite component checker with guide-content comparison omitted
until the concurrent canonical-guide commit is rebased. The initial pytest
invocation without `PYTHONPATH=.` could not collect seven modules importing
`devtools.scripts`; the repository's import path resolves with that setting.

## What was refuted

An installed receptor alone does not change pytest's output. The component
guide's instruction to use `--receptor=llm` remains appropriate for local
agent work; changing it to `ci` would conflate local and hosted contexts.
The previously closed `uibcdf/gh-run-receptor#52` established the routine and
weekly Python CI lanes, but did not settle the later MOLI receptor policy.

## Scope and exclusions

This review changes developer test tooling and records applicability. It does
not alter GH Run Receptor's GitHub status authority, schema, runtime
dependencies, product CLI semantics, or release tag. The support-library
review will not be marked adopted from these CI changes alone.

## Acceptance criteria

- All hosted pytest workflows use `--receptor=ci` with exactly pinned
  published pytest-receptor `1.1.0` in their installation path.
- The existing local suite, Ruff, developer-guide validator, component
  checker, and hosted routine and full Python matrix pass.
- ArgDigest, DepDigest, SMonitor, and PyUnitWizard applicability decisions
  have member-specific evidence or bounded exceptions; the suite inventory
  points to this issue and records the two reviews independently.

## Dependencies and risks

The full 12-cell weekly matrix was required to confirm that the exact
published release installs on Python 3.11 through 3.14 on all three systems;
run `36032624692` supplied that evidence. Product
runtime integration of support libraries may affect the deliberately small
dependency surface and needs its own review before implementation.

## Provenance

Inspected on 2026-09-24 from a Linux checkout based on
`uibcdf/gh-run-receptor@11d33a6`. Local verification used Python 3.13.15,
Ruff 0.16.5, and a locally installed pytest-receptor development build
`1.1.0+13.g43d37d6`; this does not verify that hosted CI resolves the newly
pinned public `1.1.0`.

## Hosted checkpoint

Commit `fc7986a` passed the routine Python test run `36026686868` and the
MolSysSuite policy gate `36026687941`. A manual dispatch of the weekly
matrix, run `36032624692`, passed all twelve Linux, macOS and Windows jobs
for Python 3.11 through 3.14. GH Run Receptor inspected each run and
reported the authoritative successful conclusion and expected job counts.
This verifies that the exact public pytest-receptor `1.1.0` dependency
resolves and its `ci` profile works throughout the supported CI matrix.
The developer-tool review can now be marked adopted in MolSysSuite; this
member issue stays open for the independent support-library applicability
review.
