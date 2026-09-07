---
summary: Validate portability outside UIBCDF
issue: uibcdf/gh-run-receptor#28
status: active
opened: 2026-09-07
closed:
verification: asserted
area: ['github']
guard:
normative:
blocked_by: []
supersedes: []
---

# Validating portability outside UIBCDF

**Reported:** 2026-09-07 while reviewing whether the MolSysSuite integration corpus had
introduced product-specific assumptions.
**Status:** Active; the first independent public-run evidence has passed and is being
converted into a repeatable pre-1.0 gate.

## What

Establish public evidence that the generic receptor works on GitHub Actions runs whose
repositories, workflow layouts, job matrices, and maintainers are unrelated to UIBCDF.
MolSysSuite remains an integration laboratory, but it cannot be the only portability
evidence for a general-purpose 1.0 release.

## How

Maintain a small, diverse manifest of immutable public run identifiers. Exercise compact
inspection for each entry and require parity for repository, run identifier, attempt, and
GitHub conclusion. At least one nontrivial matrix must also pass capture followed by
offline replay. The corpus belongs to development validation: no third-party project name,
run identifier, or special case may enter the runtime implementation.

Public runs can eventually expire or be deleted, so hosted acquisition is evidence rather
than a deterministic unit-test dependency. Saved, sanitized bundles or purpose-built
fixtures protect the deterministic semantic contract; the live corpus detects integration
drift.

## Why

GitHub Actions permits widely different workflow names, job matrices, event types, and
artifact layouts. Passing only UIBCDF workflows could hide accidental coupling in default
profiles, discovery, or reporting. Independent projects provide a meaningful adversarial
boundary without expanding the product scope.

## What is measured and what is assumed

On 2026-09-07, these commands each returned exit 0 and one bounded LLM line with
`conclusion=success`, the correct repository, and the exact run identifier:

```text
gh-run-receptor --repo cli/cli --receptor llm --profile generic inspect 34111073880
PASS conclusion=success | profile=generic | jobs=1/3 | artifacts=0 | cli/cli run=34111073880

gh-run-receptor --repo astral-sh/ruff --receptor llm --profile generic inspect 34105319798
PASS conclusion=success | profile=generic | jobs=36/42 | artifacts=2 | astral-sh/ruff run=34105319798

gh-run-receptor --repo pypa/build --receptor llm --profile generic inspect 34104628031
PASS conclusion=success | profile=generic | jobs=53/53 | artifacts=1 | pypa/build run=34104628031
```

The Ruff metadata capture was 377,288 bytes and offline replay produced the identical
single-line report. The three projects and their selected runs are evidence samples, not a
claim that every possible GitHub Actions shape has been covered.

## What was refuted

- Runtime searches contain no MolSys or MolSysSuite product name. UIBCDF occurrences in
  package metadata, schema identifiers, and repository links identify this project; they
  do not dispatch behavior.
- A single outside repository is not sufficient evidence because it may share an
  accidentally compatible workflow shape.
- Downloading live public runs during normal unit tests is rejected because availability
  and retention are controlled by third parties.

## Scope and exclusions

This gate tests public GitHub-hosted repositories and the generic profile. It does not yet
claim GitHub Enterprise Server compatibility, private-repository permission coverage, or
exhaustive behavior for every specialized profile. Third-party names remain test evidence
and are not endorsements or supported-client declarations.

## Acceptance criteria

- At least three non-UIBCDF repositories with materially different job counts pass generic
  compact inspection.
- Report identity and conclusion agree with GitHub for every corpus entry.
- At least one multi-job run passes capture and byte-for-byte deterministic offline replay.
- The compact LLM report remains bounded independently of source bundle size.
- The runtime contains no project-name branch for UIBCDF or any corpus repository.
- A repeatable validation entry point distinguishes an unavailable external run from a
  semantic receptor failure.

## Dependencies and risks

Public run retention and anonymous visibility are external. The validation entry point
must therefore fail with a diagnostic that identifies acquisition separately from semantic
failure, and maintainers may replace an unavailable run only with documented equivalent
coverage.

## Provenance

Measurements were made from the development host on 2026-09-07 with Python 3.13.14,
GitHub CLI 2.93.0, and gh-run-receptor `0.18.0+2.g628def2.dirty`. The captured Ruff bundle
was stored only in `/tmp`; it contains third-party metadata and is not a repository fixture.
