---
summary: Freeze release-profile evidence authority before 1.0
issue: uibcdf/gh-run-receptor#44
status: resolved
opened: 2026-09-19
closed: 2026-09-19
verification: measured
area: ['profiles']
guard: tests/test_report.py
normative: rules_and_profiles.md
blocked_by: []
supersedes: []
---

# Freezing release-profile evidence authority before 1.0

**Reported:** 2026-09-19, during the final evidence audit before 1.0.
**Status:** Resolved; the authority map, adversarial guards, and public contract are in
place without changing `report@1`.

Remove `severity` for proposals. The directory identifies the report kind.

## What

Define one auditable authority map for every fact and interpretation emitted by the
`release` profile. The current behavior is conservative, but its authority boundary is
distributed between `_release_matrix`, renderer literals, tests, and explanatory prose.
Before 1.0, the implementation must make it impossible to confuse:

- authoritative GitHub run facts;
- name-derived presentation facets;
- successful execution of a workflow step; and
- independent verification of an external delivery target.

## How

Introduce a single internal release-claim specification consumed by the release matrix.
Each claim identifies its current source, maximum assertion strength, and stable fallback.
The initial table is:

| Claim | Current source | Maximum assertion |
| --- | --- | --- |
| event, head ref, head SHA | GitHub run API | observed source fact |
| identity, gate, package, publish, archive, artifact phases | normalized job/step state plus bounded name classification | presentation facet and source state only |
| Git tag verification | no dedicated capture source | `not_observed` |
| package registry delivery | successful name-classified publish step | `step_success`, never external verification |
| GitHub Release delivery | no dedicated capture source | `not_observed` |
| citation/archive delivery | successful name-classified archive step | `step_success`, never external verification |
| current Actions artifact inventory | GitHub artifacts API | observed inventory only |

The serialized `report@1` shape and its existing values remain unchanged. Adversarial
tests will use successful steps named as if they had verified Git tags, GitHub Releases,
PyPI/npm/Conda registries, and Zenodo DOI records. Those names may classify a phase, but
must not produce an independently verified external fact.

## Why

Release workflows contain user-controlled names such as `Publish to PyPI` or `Verify
Zenodo DOI`. A successful step proves that GitHub recorded the step as successful; it does
not prove registry presence, tag identity, release asset integrity, or archival state.
Making that distinction executable prevents a future renderer or profile extension from
silently upgrading name inference into release authorization evidence.

## What is measured and what is assumed

Inspection on 2026-09-19 found that `_release_matrix` always emits
`tag_verification=not_observed` and limits registry/archive statements to
`step_success`. The existing release tests cover ordinary npm and Zenodo names, but no
single structure defines all authorities and no adversarial test covers all external
claim families together.

The proposal assumes no new external endpoint for this increment. New capture sources
would require a separate versioned design and must not be simulated from workflow names.

## What was refuted

- Treating a successful publish step as registry verification is rejected because the
  step can succeed before, after, or without independently observable delivery.
- Parsing log prose for DOI, tag, or registry confirmation is rejected because logs are
  untrusted and their text is neither a stable schema nor an independent authority.
- Adding fields to `report@1` is rejected because the evidence boundary can be frozen
  without changing a published serialized contract.

## Scope and exclusions

This increment does not query registries, Git refs, GitHub Releases, or Zenodo; define a
new producer event; change release assessment or exit codes; or redesign profile phase
classification. It documents which future claims need those sources.

## Acceptance criteria

- One implementation-level specification names every release claim, its source class,
  maximum assertion, and unavailable fallback.
- `_release_matrix` derives verification states from that specification rather than
  scattered string literals.
- Adversarial successful step names cannot upgrade tag, GitHub Release, registry, or
  archive delivery to independent verification.
- Public and developer documentation contain the same claim/source/authority table.
- Existing `report@1` fixtures and compatibility freezes remain byte-compatible.
- Focused and full tests, Ruff, strict documentation, contract validation, and devguide
  validation pass.

## Dependencies and risks

There is no external dependency. The main risk is terminology that accidentally makes
`step_success` sound like external verification; the public table and adversarial tests
must make the distinction explicit.

## Implementation and validation

`gh_run_receptor.release_profile` now owns an immutable mapping from ten release-claim
families to their evidence source, maximum assertion, fallback, and optional source-field
or step-facet binding. `_release_matrix` consumes this mapping for run identity and
delivery-step evidence, while compact tag and aggregate external-delivery rendering use
the same authority definitions. The `report@1` shape and rendered values remain
unchanged. Implementation commit `d83b800` contains the tested product and documentation
change.

`test_release_claim_authorities_cover_source_phase_and_external_boundaries` freezes the
complete map. `test_successful_release_claim_names_cannot_invent_external_verification`
then supplies four successful adversarial names covering Git tags, three package
registries, GitHub Releases, and Zenodo DOI records. The report retains
`tag_verification=not_observed`, bounds publish/archive evidence at `step_success`, and
keeps independent external delivery `not_observed`.

The local gate on 2026-09-19 produced:

- `python -m pytest --receptor=llm`: 439 passed;
- `ruff check .`: passed;
- focused `ruff format --check` for all changed Python files: passed;
- `python devtools/scripts/validate_contracts.py`: nine contracts passed against the
  0.21.0 frozen baseline;
- `sphinx-build -W --keep-going -b html docs ...`: ten pages built without warnings;
- `python devtools/scripts/validate_devguide.py`: passed; and
- `git diff --check`: passed.

The repository-wide format check also identified pre-existing formatting changes in
`gh_run_receptor/cli.py` and `tests/test_bundle.py`. This increment does not touch those
files; the applicable changed-file format gate passes.

## Provenance

Inspection was performed on 2026-09-19 against `main` after release 0.22.0, starting at
commit `05bac06985bf045f1be6999c724dc0c7fa86d921`. Validation used Python 3.13.14,
pytest with pytest-receptor, Ruff 0.16.1, and Sphinx 8.2.3.
