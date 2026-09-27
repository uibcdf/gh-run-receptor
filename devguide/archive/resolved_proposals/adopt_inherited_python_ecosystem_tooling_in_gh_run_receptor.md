---
summary: Review MolSysSuite Python ecosystem policy in GH Run Receptor
issue: uibcdf/gh-run-receptor#55
status: resolved
opened: 2026-09-24
closed: 2026-09-27
verification: measured
area: [governance, tests]
guard:
normative: python_ecosystem_policy_adoption.md
blocked_by: []
supersedes: []
---

# Review MolSysSuite Python ecosystem policy in GH Run Receptor

**Reported:** 2026-09-24 during the MolSysSuite Python ecosystem rollout.

**Status:** Resolved. Developer-tool CI, the current policy caller and all four
support-library applicability decisions have evidence below.

## What

The historical `origin/main` snapshot at `11d33a6` ran the local-agent
`--receptor=llm` profile in four hosted pytest workflows: routine, weekly,
compatibility, and release publication. The `[test]` and `[dev]` extras
specify `pytest-receptor` without an exact release. This conflicts with the
suite rule to use a published exact receptor release in CI and its `ci`
profile for ephemeral hosted logs.

## How

Pin published pytest-receptor `1.1.0` in both extras, select
`--receptor=ci` in all four hosted pytest calls, and retain each workflow's
existing test selection and build or release gates. Update the existing
workflow contract assertions. Run the component suite through the local
`--receptor=llm` profile, Ruff, the developer-guide validator, and the
MolSysSuite component checker before publishing. Verify hosted routine and
weekly lanes before claiming developer-tool adoption.

Review the four support-library applicability boundaries separately. The CLI
and public embedded API validate untrusted GitHub data and report user-visible
failures. Preserve their bounded parsing, source-truth, and diagnostic
contracts when deciding whether a support library adds an applicable
capability.

## Why

An LLM profile may refer to a local overflow file unavailable to readers of
a hosted log. An unpinned test extra can select a different release on the
next CI run. The MolSysSuite policy requires a member-local review before the
suite's inventory can claim adoption or a bounded exception.

## What is measured and what is assumed

The four commands and dependency declarations were inspected at
`origin/main` commit `11d33a6` using `git grep` and `git show`. The
published pytest-receptor `1.1.0` tag is present in its local repository.
At that checkpoint the new workflows had not yet run on GitHub. The behavior of the
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
weekly Python CI lanes, but did not settle the later ecosystem policy.

## Scope and exclusions

This review records developer tooling and support-library applicability. It
does not alter GH Run Receptor's GitHub status authority, schema, runtime
dependencies, product CLI semantics, or release tag. Support-library adoption
rests on the separate boundary decisions, not the CI-profile change alone.

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
The developer-tool review is adopted in MolSysSuite. The four support-library
decisions are documented in
`devguide/python_ecosystem_policy_adoption.md`: CLI options use argparse,
untrusted documents use bounded parsers and schema checks, the `gh`
executable is required transport rather than an optional backend, receptor
itself owns its diagnostic outputs, and no quantity conversion boundary
exists. No runtime library is added merely to satisfy the inventory.

The 2026-09-27 policy-v1.5.2 caller commits `4e75153` and `f7fdd9f`
passed the shared policy gate but exposed a stale local assertion that still
expected policy-v1.4.9. GH Run Receptor identified
`tests/test_packaging.py::test_suite_policy_caller_pins_current_release` as
the failed test in routine run `36310571084`. The assertion now names the
current reviewed release. The complete local suite passed 464 tests, Ruff
check and format passed, the developer-guide validator passed, and the
MolSysSuite repository checker passed. Exact source commit `b0e04d3` passed
[routine run `36333697901`](https://github.com/uibcdf/gh-run-receptor/actions/runs/36333697901)
and [policy run `36333698541`](https://github.com/uibcdf/gh-run-receptor/actions/runs/36333698541).
GH Run Receptor reported authoritative `PASS` for both.

## Resolution

The verified pytest-receptor pin and hosted `ci` profile satisfy the
developer-tool rule. ArgDigest, DepDigest, SMonitor, and PyUnitWizard have no
applicable runtime boundary in this product's current design; the local
[applicability decision](../../python_ecosystem_policy_adoption.md) records the
source and tests for each and the triggers to reassess. The stale version
assertion was corrected without changing product behavior. MolSysSuite can
record developer tools and support libraries as separately adopted under
`uibcdf/gh-run-receptor#55`.
