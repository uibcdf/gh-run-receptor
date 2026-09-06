# Development roadmap

## Dependency order

Phases are ordered by evidence and contract dependency, not by UI visibility. Phase 0
may build disposable probes; Phase 1 creates the first supported vertical slice. Profile
and Action work must not fork a second source model while those foundations are unstable.

The first implementation sequence is:

1. scaffold the Python package, console entry point, Ruff, pytest, and fixture layout;
2. add a bounded subprocess adapter for `gh api` and a fake adapter for offline tests;
3. capture `run.json`, paginated `jobs.json`, and a manifest for one explicit run attempt;
4. validate and replay that bundle without network access;
5. normalize run, job, and step identity and official state;
6. render a bounded generic JSON and text report with tested exit status;
7. extend acquisition to workflow, checks, artifacts, and logs while recording
   dimensional completeness;
8. benchmark the vertical slice against native `gh` baselines before broadening profiles.

Each step must leave an executable test and update the relevant provisional contract.

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

Deliverables are a private full corpus, an approved sanitized regression subset, an API
probe report, native-command baselines, and a recommendation for the initial capture
policy. Run identifiers alone do not count as a reproducible corpus.

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

This phase also produces formal schemas for `bundle@1`, `model@1`, and `report@1`, package
installation instructions, the initial dependency record, and explicit CLI help. It is
the earliest point at which a preview package may be released.

## Phase 2: configuration and profiles

- Implement safe configuration loading and schema validation.
- Add workflow discovery and `init`.
- Add `config check` and `config explain`.
- Deliver CI, documentation, Conda, and release profiles.
- Group repeated matrix failures by defensible causal evidence.
- Suggest, but never execute, minimal rerun commands.

**Exit condition:** profile output is shorter and more actionable than generic output
without hiding unmatched evidence.

Every profile ships with required/optional evidence tables, configuration examples,
generic fallback cases, and at least one real sanitized workflow capture.

## Phase 3: embedded GitHub Action

- Publish compact stdout and `GITHUB_STEP_SUMMARY` output.
- Publish the versioned JSON report as a small artifact.
- Accept built-in profiles, repository configuration, and inline rule overrides.
- Define fail-open reporting behavior that does not alter primary job conclusions.
- Pin dependencies and test public-repository and pull-request permission boundaries.

**Exit condition:** a workflow can add one reporting step and the external CLI can
consume its report without downloading full logs.

The Action distribution gate in the decision register must be closed before this phase
is called stable. The release claim names every verified operating system.

## Phase 4: reusable aggregator and comparison

- Publish a reusable final reporting workflow for matrices.
- Aggregate per-job structured evidence.
- Compare attempts and selected historical runs.
- Report duration, artifact-size, and matrix-coverage regressions.
- Add transition-only monitoring without repeated snapshots.

**Exit condition:** CI, documentation, and Conda examples work across multiple UIBCDF
repositories and the report survives partial matrix failure.

## Progress accounting

Roadmap percentages are evidence-based. A phase contributes to overall progress only when
its exit condition and deliverables are satisfied:

| Phase | Weight toward 1.0 | Evidenced credit | Current state |
| --- | ---: | ---: | --- |
| Phase 0: corpus and feasibility | 15% | 14% | Measured sanitized fixtures cover native/noarch Conda, failing CI, successful/failing documentation and npm release workflows, cancellation, expired logs, and paired reruns; a live experiment documents why standard job timeout cannot generate `timed_out`; restricted-token, active-transition, and Zenodo evidence remain |
| Phase 1: generic CLI | 30% | 28% | Capture, strict validated replay, formal bundle/model/report schemas, source-referenced normalization, bounded reports, attempt-specific historical truth, outcome exit-code parity, degraded log analysis, and structured redacted acquisition failures are tested; remaining real outcome cases and byte-identical replay timing remain |
| Phase 2: rules and profiles | 20% | 18% | Initial native/noarch Conda, CI, documentation, and release interpretations plus repeated-failure grouping, strict trusted exact-match configuration, local discovery, and non-overwriting `init` are tested; richer rules and external release verification remain |
| Phase 3: embedded Action | 15% | 0% | Contract designed; no distributed Action implementation yet |
| Phase 4: aggregation and comparison | 10% | 2% | Transition-only watch tested; aggregation and comparison remain |
| Cross-cutting release gate | 10% | 2% | Flat installable package, tag-derived version, local tests, and wheel smoke test verified on Linux; platform and release gates remain |

Design completion is reported separately from implementation progress. The evidenced
implementation credit at this checkpoint is **64% toward 1.0**. This is not a schedule
estimate: credit is deliberately withheld where a phase's required corpus, schema,
platform, or distribution evidence is absent. Percentages change only with linked tests,
builds, or benchmark evidence, not by subjective confidence.

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

## Release readiness checklist

The 1.0 route is complete only when all items above are backed by reproducible evidence
and the following final checks agree:

- schemas validate every committed fixture and compatibility/migration tests pass;
- profile assessments preserve all official conclusions and incomplete dimensions;
- the benchmark report meets the token-reduction target without semantic misses;
- security and resource-bound cases pass under supported platforms;
- CLI and any shipped Action install from their released artifacts, not a source checkout;
- examples run against a dedicated fixture repository with documented permissions;
- release notes enumerate supported Python, GitHub CLI, GitHub host, and operating systems;
- documentation contains no behavior claimed solely from design intent;
- every open decision whose gate is at or before 1.0 is closed or explicitly removes the
  affected feature from the release.
