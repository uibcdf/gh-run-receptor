---
summary: Freeze version 1 contracts and migration policy
issue: uibcdf/gh-run-receptor#30
status: active
opened: 2026-09-07
closed:
verification: asserted
area: ['governance', 'tests']
guard:
normative:
blocked_by: []
supersedes: []
---

# Freezing version 1 contracts and migration policy

**Reported:** 2026-09-07 during the 1.0 readiness audit.
**Status:** Active; the published baseline is confirmed and the compatibility gate is being
implemented.

## What

Turn the already published `bundle@1`, `model@1`, `report@1`, and `config@1` identifiers
into an explicit compatibility contract. Today their identifiers are repeated across
modules, and documentation promises supported-version readers and explicit migrations
without an executable registry or a release gate that prevents silent v1 schema rewrites.

## How

Create one dependency-free runtime registry containing each contract kind, canonical
identifier, current version, readable versions, and schema resource. Every untrusted
bundle, published report, and captured configuration must use its kind-aware check. Add an
offline `contracts` command that exposes the supported set without GitHub access.

Version 1 schema bytes published in tag `0.18.0` become immutable. A release validator
must obtain those bytes with `git show`, compare every registered schema exactly, and fail
if a file is missing, added without registration, or changed in place. The release workflow
must execute that validator before building artifacts.

Within one major contract, only additions already permitted by that schema are compatible;
existing field meaning cannot change. An incompatible required field, type, enum, identity,
or meaning requires the next integer contract version. Readers reject malformed, wrong-kind,
retired, and future identifiers distinctly. Migration is forward-only, pure, stepwise, and
registered by `(kind, source_version)`; no migration exists yet because v1 is the first and
current version. Adding v2 is incomplete until its v1-to-v2 migrator and semantic fixtures
land together, or v1 is explicitly documented as retired.

## Why

Bundles and published reports are intended to outlive the executable that created them.
Without a frozen boundary, a newer release could accept the same `@1` label with changed
meaning, making replay non-reproducible and allowing consumers to mistake schema spelling
for compatibility.

## What is measured and what is assumed

`git diff 0.18.0 -- gh_run_receptor/schemas` is empty: all four current schema resources
are byte-identical to the first fully verified release baseline. Existing tests validate
current fixtures with Draft 2020-12 JSON Schema, but production readers use distributed
literal comparisons and there is no migration module or release-time baseline comparison.

The implementation audit also found the persisted `config-capture@1` envelope. Its
identity was validated manually but it had no formal schema resource, making it a fifth
serialized boundary. It is included in this increment without falsely claiming that its
new schema file existed in 0.18.0.

## What was refuted

- Editing a v1 schema and updating an adjacent checksum is rejected because that checks
  coordinated file edits, not historical compatibility.
- Adding `jsonschema` as a runtime dependency is rejected; critical untrusted structures
  retain targeted dependency-free validation and the formal schemas remain a test gate.
- Treating any `gh-run-receptor.*@1` value as interchangeable is rejected because contract
  kind is part of the trust boundary.
- Inventing a v0 migration solely to exercise the mechanism is rejected because no such
  public contract existed.
- Automatic downgrade and best-effort reading of future versions are rejected because they
  can silently discard facts needed for a truthful verdict.

## Scope and exclusions

This increment does not introduce contract v2, rewrite historical fixtures, add network
schema resolution, or promise that arbitrary third-party extensions are understood. It
does not make generated reports writable or mutable.

## Acceptance criteria

- One registry owns every public contract identifier and schema resource.
- Current producers and all untrusted readers use the registry.
- The offline CLI reports the exact readable/current versions deterministically.
- Malformed, wrong-kind, retired, future, and missing-migration cases fail distinctly.
- A synthetic registered migration proves forward-only stepwise execution without
  mutating its input.
- Every schema published by 0.18.0 is byte-identical to that tag, the newly formalized
  configuration-capture schema is registered and distributed, and the release workflow
  enforces the historical baseline before building.
- Existing sanitized bundles and published-report guards pass unchanged.
- The migration and retirement policy is normative and sufficient for a future v2 change.

## Dependencies and risks

The gate depends on Git metadata and the local 0.18.0 tag during release checkout. Source
archives remain usable at runtime because schema baseline comparison is development/release
tooling, not an import-time check.

## Provenance

Audited on 2026-09-07 at commit `212d81d` with Python 3.13.14, Git 2.43.0, and the local
lightweight `0.18.0` tag. All four schema paths exist in that tag and have no diff against
`main` before this increment.

## Implementation checkpoint

One dependency-free registry now owns five contract families and every packaged schema
version within each family, so adding v2 does not orphan the retained v1 resource. Current
producers and the bundle, published-report, and captured-configuration readers use
kind-aware compatibility checks. `contracts` exposes the registry offline in bounded text
or deterministic JSON.
The migration engine is forward-only and copy-preserving; synthetic tests cover chained,
missing, and malformed migration steps without inventing a historical v0.

`config-capture-v1.schema.json` now formalizes the previously implicit envelope. The
release workflow runs the baseline validator before tests and distributions; a local check
passes for all five registered resources and confirms exact 0.18.0 bytes for the four
historically published schemas.

A separate manual read-only workflow exercises the same comparison from a full-tag hosted
checkout, allowing the release prerequisite to be tested without creating a release.

A clean isolated build produced both source distribution and wheel. The wheel contains the
new contract module and all five schemas; installation into a fresh virtual environment
successfully ran `gh-run-receptor contracts --format=json` outside the checkout.
