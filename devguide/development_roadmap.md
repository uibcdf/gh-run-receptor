# Development roadmap

## Phase 0: evidence corpus and feasibility

Collect full evidence bundles from representative public UIBCDF runs:

- successful and failing CI;
- full test matrices with repeated causes;
- documentation build and deployment;
- five-platform Conda build, validation, partial publication, and failure;
- release and Zenodo verification;
- cancelled, timed-out, skipped, and rerun attempts.

Define an honest filtered-CLI baseline and measure bytes and tokens. Sanitize the subset
that becomes a committed regression corpus.

**Exit condition:** the required API resources, missing evidence, and log-association
limitations are documented from real runs.

## Phase 1: generic read-only CLI

- Resolve repository and run identifiers through GitHub CLI authentication.
- Capture `full`, `adaptive`, and `metadata` bundles.
- Validate manifests and digests.
- Replay bundles without network access.
- Normalize run, attempt, job, step, check, and artifact state.
- Render deterministic compact and JSON reports.
- Preserve raw evidence and degrade safely on parser failure.

**Exit condition:** generic reports maintain exact conclusion parity across the corpus
and replay byte-identically with fixed time metadata.

## Phase 2: configuration and profiles

- Implement safe configuration loading and schema validation.
- Add workflow discovery and `init`.
- Add `config check` and `config explain`.
- Deliver CI, documentation, Conda, and release profiles.
- Group repeated matrix failures by defensible causal evidence.
- Suggest, but never execute, minimal rerun commands.

**Exit condition:** profile output is shorter and more actionable than generic output
without hiding unmatched evidence.

## Phase 3: embedded GitHub Action

- Publish compact stdout and `GITHUB_STEP_SUMMARY` output.
- Publish the versioned JSON report as a small artifact.
- Accept built-in profiles, repository configuration, and inline rule overrides.
- Define fail-open reporting behavior that does not alter primary job conclusions.
- Pin dependencies and test public-repository and pull-request permission boundaries.

**Exit condition:** a workflow can add one reporting step and the external CLI can
consume its report without downloading full logs.

## Phase 4: reusable aggregator and comparison

- Publish a reusable final reporting workflow for matrices.
- Aggregate per-job structured evidence.
- Compare attempts and selected historical runs.
- Report duration, artifact-size, and matrix-coverage regressions.
- Add transition-only monitoring without repeated snapshots.

**Exit condition:** CI, documentation, and Conda examples work across multiple UIBCDF
repositories and the report survives partial matrix failure.

## Route to 1.0

The 1.0 contract requires:

- a versioned normalized evidence and report schema;
- frozen truth, incompleteness, and degraded-mode semantics;
- deterministic output and differential tests against GitHub conclusions;
- bounded output under pathological matrices and logs;
- security review of logs, rules, caches, and pull-request trust boundaries;
- measured token savings across tokenizer families;
- Linux, macOS, and Windows installation paths;
- documented GitHub CLI, token permission, API version, and retention requirements;
- compatibility tests for supported GitHub CLI and Python or binary-runtime versions;
- migration rules for profiles and configuration schemas.

Mutation commands are reconsidered only after 1.0 read-only semantics are stable. If
added later, they require explicit user intent and a separate permission boundary.

