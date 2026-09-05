# Testing strategy

## Objective

Tests must demonstrate that the receptor preserves the meaning of a workflow while
reducing the text a human or language model must inspect. A short report is not correct
merely because it is short.

## Test layers

### Unit tests

Unit tests cover schema validation, state normalization, rule matching and precedence,
cause grouping, redaction, archive safety, truncation, rendering, exit codes, and stable
ordering. Discovery tests cover non-recursion, deterministic ordering, conservative
classification, ambiguity, strict-parser round trips, symlinks, invalid encoding, byte
limits, preview behavior, and non-overwriting creation. They use small hand-written inputs
and run without network access.

### Contract tests

Recorded GitHub responses exercise pagination, attempts, missing fields, new enum values,
expired log links, artifact metadata, annotations, and partial permissions. Fixtures retain
HTTP boundaries and source identifiers while removing secrets and private content.

### Replay and golden tests

Sanitized evidence bundles are replayed through profiles. Golden reports test deliberately
bounded public output, while semantic assertions independently verify conclusions,
completeness, provenance, and grouped causes. Updating a snapshot is never sufficient
evidence that a behavior change is correct.

### Live integration tests

A dedicated fixture repository provides small successful, failed, cancelled, timed-out,
matrix, documentation, Conda-like, and release-like workflows. Live tests are scheduled or
manual by default to avoid consuming API quota and runner time on every commit. They verify
the real GitHub adapter and are not the sole coverage for any semantic rule.

### Action and reusable-workflow tests

These tests verify `if: always()`, explicit `needs`, reporter self-exclusion, permissions,
step summaries, JSON artifacts, outputs, fork restrictions, fail-open behavior, and the
external CLI fallback after cancellation. Linux, macOS, and Windows are required before a
stable cross-platform claim.

### Adversarial tests

The cases required by [security.md](security.md) run locally and in CI. Fuzz or property
tests are appropriate for parsers, schemas, archives, and state combinations, provided
failures are reproducible with a stored seed or minimized example.

## Corpus policy

The project keeps three corpus classes:

- synthetic fixtures for isolated semantics;
- sanitized captures from known public workflows for realism;
- private local captures that are never committed.

Each committed capture records repository, run and attempt identity, capture date, reason
for inclusion, sanitization notes, expected assessment, and upstream retention caveats.
Large logs are reduced only after the original semantic condition is preserved.

Initial public captures should represent generic CI, documentation, matrix Conda builds,
and release coordination. The MolSysMT run identifiers listed in
[motivation_and_evidence.md](motivation_and_evidence.md) are starting research evidence,
not automatically safe fixtures.

The first reviewed corpus entries are catalogued in `tests/fixtures/corpus.json`. They are
metadata-only reductions of public MolSysMT Conda runs `33863426589` and `33849332945`.
The catalog records why each run is retained, exactly what sanitization removed, expected
official and receptor outcomes, and the upstream-retention caveat. The committed bundles
contain no actors, commit messages, runner details, pull-request data, or API URLs.

## Quality metrics

Evaluation records both correctness and economy:

- official jobs and conclusions preserved;
- expected matrix dimensions accounted for;
- failed root causes found and false causes avoided;
- missing or inaccessible evidence reported;
- report source-token count and byte count;
- acquisition bytes, API requests, elapsed time, and cache hits;
- reduction relative to competent native GitHub CLI baselines;
- repeated-output avoided during watch mode.

Token counts must identify the tokenizer or model family. The primary product claim uses
source/input tokens, not an unspecified token count. A result is rejected if improved
compression hides a distinct failure, blocked dimension, or uncertainty.

## Required semantic cases

At minimum the suite covers:

- success, failure, skipped, cancelled, timed out, pending, stale, and action-required;
- zero jobs, inaccessible jobs, missing logs, expired artifacts, and unknown conclusions;
- reruns with multiple attempts and mixed old/new evidence;
- matrix fan-out with some successful reusable artifacts and some failures;
- one root cause repeated across jobs and multiple independent root causes;
- workflow build success followed by deployment failure;
- producer events that agree and disagree with GitHub source state;
- configuration ties, invalid schemas, and untrusted policy sources;
- deterministic rendering under shuffled API order.

## Local gate

Once the package skeleton exists, the normal local gate is:

```text
ruff check .
pytest --receptor=llm
```

Focused tests may be run during development, but the full local gate is required before a
commit described as validated. Documentation-only changes additionally run link and schema
checks when those tools exist. Missing optional credentials must produce explicit skips,
not false passes.

## Release gate

A release candidate requires the full local suite, supported Python versions, declared
operating systems, live GitHub integration, CLI installation, replay compatibility,
Action/reusable-workflow integration when shipped, adversarial cases, and benchmark
comparison. Every supported combination must be either passing or explicitly excluded
from the release claim; no platform is implied by silence.
