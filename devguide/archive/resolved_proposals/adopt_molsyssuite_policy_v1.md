---
summary: Adopt the shared MolSysSuite policy and Ruff quality gate
issue: uibcdf/gh-run-receptor#22
status: resolved
opened: 2026-09-06
closed: 2026-09-06
verification: measured
area: [governance, tests]
guard: .github/workflows/molsyssuite-policy.yml
normative: testing_strategy.md
blocked_by: []
supersedes: []
---

# Adopt the shared MolSysSuite policy and Ruff quality gate

**Reported:** 2026-09-06, during the first repository rollout of the central
MolSysSuite conformance policy.
**Status:** Resolved on `main`; the executable shared gate and the Ruff formatting
baseline are active.

## What

Adopt the versioned MolSysSuite repository policy, including its central reporting route,
supported Python range, development interpreter, and shared Ruff lint and format gate.

## How

Keep gh-run-receptor's product tests, installation checks, release process, and additional
Ruff rules local. Call the exact central policy release from a small workflow, use the
centrally pinned Ruff version in the local development extra, document both Ruff commands
in the local gate, and establish the current Ruff formatting baseline mechanically.

## Why

The initial policy caller used `policy-v1.0.0`, whose conformance script inspected Ruff
configuration but did not prove that CI executed Ruff. Correcting that omission exposed
26 existing Python files that pass linting but do not pass `ruff format --check`. Leaving
the mismatch unresolved would make the corrected shared gate fail and would allow local
and suite-wide development instructions to disagree.

## What is measured and what is assumed

On 2026-09-06, `ruff check --no-cache gh_run_receptor tests devtools` passed. With Ruff
0.16.5, `ruff format --check --no-cache .` reported 26 files that would be reformatted.
The original central workflow run `34053873977` passed under `policy-v1.0.0`; that result
did not execute the formatter and is therefore insufficient evidence for the corrected
policy. After the migration, 223 tests passed locally and central policy run `34059932644`
passed using `policy-v1.1.0`. No behavioral or performance change is assumed from the
mechanical formatting.

## What was refuted

Keeping only a local `ruff check` command was rejected because linting and formatting are
separate gates. Adding a duplicate repository-owned Ruff workflow was rejected because
the versioned reusable workflow now owns the common Ruff gate and pin, while the local
repository remains free to add stricter rules.

## Scope and exclusions

This proposal does not change gh-run-receptor behavior, its public interfaces, its test
runner, or its release process. It does not introduce a common type checker or remove
repository-specific quality rules.

## Acceptance criteria

- The root contributor guidance routes suite-wide concerns to `uibcdf/molsyssuite`.
- The policy caller uses the current immutable central policy release.
- The local development extra uses the centrally selected Ruff version.
- The documented local gate runs both Ruff linting and formatting checks.
- Ruff linting and formatting pass across the repository.
- The central policy workflow passes on `main`.

## Dependencies and risks

This work depends on `uibcdf/molsyssuite#6` and the immutable `policy-v1.1.0` release. The
formatting migration is intentionally isolated from behavioral changes to make review and
future diagnosis straightforward.

## Provenance

Repository inspection and validation on 2026-09-06 using Python 3.13 and Ruff 0.16.5.
`PYTHONPATH=$PWD pytest -q -p no:cacheprovider` passed 223 tests; Ruff lint and format
checks passed; GitHub Actions run `34059932644` passed the shared conformance and Ruff
gate. Central policy history is recorded in `uibcdf/molsyssuite#6`, `#7`, and `#8`.
