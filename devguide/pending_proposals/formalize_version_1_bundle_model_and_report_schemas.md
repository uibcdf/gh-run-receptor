---
summary: Formalize version 1 bundle, model, and report schemas
issue: uibcdf/gh-run-receptor#2
status: active
opened: 2026-09-04
closed:
verification: measured
area: ['reports', 'tests']
guard:
normative:
blocked_by: []
supersedes: []
---

# Formalize version 1 bundle, model, and report schemas

**Reported:** 2026-09-04, while selecting the reliability gate for routine MolSysMT use.
**Status:** Active; schemas, normalization, sanitization, and corpus tests are implemented
and undergoing final artifact validation.

## What

Publish machine-readable version 1 schemas for captured bundles, normalized models, and
reports. Make replay validate untrusted bundle structure before normalization and retain a
small sanitized real-run corpus that proves official-state parity and determinism.

## How

Ship Draft 2020-12 schema resources inside the Python package. Introduce a normalization
boundary that creates `model@1`, including dimensional completeness, stable ordering,
source JSON Pointers, and explicit records for unknown GitHub enum values. Keep profile
interpretation in the report layer.

Validate JSON duplicate keys, non-finite numbers, manifest field types, member identity,
byte counts, digests, and required source collection shapes with the standard library.
Use `jsonschema` only in the development gate to prevent the published schemas drifting
from real output. Produce fixtures through a narrow allow-list sanitizer.

## Why

Before this change, the MVP wrote schema identifiers but its compatibility boundary was
only prose and ad hoc dictionary access. A malformed capture could fail late, and no test
proved that source facts survived normalization into a formally described report. Routine
use during MolSysMT development needs this trust boundary before convenience profiles are
allowed to grow.

## What is measured and what is assumed

Two public MolSysMT runs were captured with metadata policy: failed/partial Conda run
`33863426589` (62,811 captured bytes before sanitization) and successful Conda run
`33849332945` (60,239 bytes). Allow-list sanitization reduced the committed pair to about
76 KiB on disk. Tests observe official conclusions, derived assessments, all five platform
states, schema validity, deterministic fixed-evidence replay, and stable compact text when
API collections are reordered.

## What was refuted

Adding `jsonschema` at runtime was rejected: validating a fixed, critical untrusted input
surface does not justify its dependency tree or startup cost. Publishing schemas without
testing constructed outputs against them was rejected because such files can drift while
all product tests remain green. Committing full public API responses was rejected because
public availability does not make incidental identity and runner data necessary test data.

## Scope and exclusions

This increment does not freeze schema version 1 for a stable 1.0 release, add producer
events, build the broad Phase 0 corpus, or implement configuration and non-Conda profiles.
It does not claim causal completeness for metadata-only fixtures.

## Acceptance criteria

- All three schema files pass Draft 2020-12 schema checks and validate constructed data.
- Bundle replay rejects unsafe identity, mutation, malformed JSON, duplicate keys,
  non-finite values, and structurally invalid source collections.
- The model preserves official values and identifies unknown enum values with provenance.
- Both sanitized runs replay deterministically and retain exact official conclusions.
- Reordering job and artifact source collections does not change compact rendered text.
- Schema resources are present in the built wheel and tests pass without runtime network.

## Dependencies and risks

No tracked dependency. The main risk is mistaking a two-run Conda slice for broad corpus
coverage; the roadmap and scope explicitly retain that work.

## Provenance

Captured from GitHub on 2026-09-04 and tested locally with Python 3.13 and `jsonschema
4.26.0`. Run identities and sanitization notes are in `tests/fixtures/corpus.json`.
