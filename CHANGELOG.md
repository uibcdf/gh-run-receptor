# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- Synchronize the 0.13.0 consumer guide to all eleven tracked client repositories and
  verify the tag through isolated wheel and GitHub CLI extension installations.

## 0.13.0 - 2026-09-06

- Validate the public `0.12.0` Action tag across hosted Ubuntu, macOS, and Windows.
- Synchronize the 0.12.0 consumer guide to all eleven tracked client repositories.
- Add a read-only downstream `workflow_run` gate for terminal source-run reporting.
- Add an explicit `published` command that consumes one bounded Action report artifact and
  verifies its terminal source identity and conclusion against fresh GitHub metadata.
- Apply caller-specific transport limits before hashing or expanding published ZIP data,
  and reject unsafe archives, malformed reports, and impossible assessment combinations.

## 0.12.0 - 2026-09-06

- Add the first composite GitHub Action around the shared capture and report core.
- Publish bounded compact logs, escaped job summaries, scalar outputs, and a canonical JSON
  artifact without turning source-workflow failure into reporter failure.
- Add a manual Linux, macOS, and Windows validation matrix for the Action and GitHub CLI
  extension, including completed success, completed failure, and honest active-run state.
- Track ElastNetMT, TopoMT, and PharmacophoreMT in the canonical consumer-guide sync set.
- Deploy strict workflow rules and the 0.11.0 guide to eight additional client repositories.

## 0.11.0 - 2026-09-06

- Add a bounded, manually dispatched Ubuntu, macOS, and Windows compatibility matrix for
  Python 3.11, 3.12, and 3.13.
- Run the full receptor-formatted suite, build wheel and source distribution, install the
  wheel, and smoke-test the console command outside the checkout in every matrix job.
- Preserve byte-exact fixture JSON with LF checkouts on every platform while retaining
  strict manifest byte-count and digest validation.
- Validate all nine platform/interpreter combinations in GitHub Actions run `34037657805`.

## 0.10.0 - 2026-09-06

- Classify GitHub CLI acquisition failures as authentication required, authentication
  failed, permission denied, not found or inaccessible, rate limited, or generic failure.
- Keep receptor exit status 5 while exposing the stable category in one bounded stderr
  line for human and agent recovery.
- Redact GitHub-token, authorization-header, and token-assignment shapes and make terminal
  controls visible before remote stderr reaches the user-facing channel.
- Make optional-resource handling depend on structured HTTP 404 status rather than parsing
  exception prose.
- Validate missing-session, HTTP 401, 403, and 404 behavior with real read-only probes and
  cover rate limits and hostile diagnostics synthetically.

## 0.9.0 - 2026-09-05

- Fetch and validate the attempt-specific workflow-run response when inspecting or
  watching a historical rerun, preventing current-attempt conclusions from contaminating
  historical evidence.
- Reject bundles whose manifest identity contradicts the retained run ID, attempt, or
  head SHA while keeping older sanitized bundles without those additive fields readable.
- Preserve cancelled, timed-out, active, and future platform states in Conda aggregation,
  and label mixed outcome inventories as non-success jobs rather than failures.
- Add sanitized real cancelled, expired-log, and paired failed/successful rerun fixtures
  with schema, assessment, exit-code, and cross-attempt contract tests.

## 0.8.0 - 2026-09-05

- Add dependency-free local workflow discovery and `init` configuration proposals.
- Classify CI, documentation, Conda, and release workflows from bounded conservative
  filename and source signals, with visible confidence and generic ambiguity fallback.
- Scan only active immediate workflow files, reject symlinks and unsafe or oversized
  sources, and validate generated output through the strict version 1 parser.
- Keep preview mode read-only and require `--write` for atomic creation without replacing
  an existing repository policy.
- Validate discovery against all 15 active MolSysMT workflows and all 8 active
  MolSysViewer workflows.

## 0.7.0 - 2026-09-05

- Add the first release profile with observed trigger/ref/SHA identity and bounded
  identity, gate, package, publish, archive, artifact, setup, and `other` evidence.
- Keep composite release steps indivisible and derive `PARTIAL` only from separate
  successful package and unsuccessful publication units.
- Distinguish workflow-step publication/archive evidence from external registry, tag, or
  archive verification that the receptor did not perform.
- Preserve run event, observed head ref, and complete step status in sanitized fixtures.
- Add measured successful and failing MolSysViewer npm fixtures; reject two renderers that
  exceeded competent filtered native baselines.

## 0.6.1 - 2026-09-05

- Keep `config explain` focused on settings supported by the matched profile instead of
  displaying an implicit native Conda package kind for documentation or CI rules.

## 0.6.0 - 2026-09-05

- Add the first documentation profile with bounded build, notebook, link, warning,
  artifact, deployment, setup, and visible `other` phases.
- Preserve complete normalized step state and provenance in report JSON while retaining
  the existing failed-step projection.
- Keep composite build/deploy actions indivisible and derive `PARTIAL` only from separate
  successful build and failed deployment evidence.
- Add sanitized successful MolSysMT documentation and failing MolSysViewer notebook
  fixtures with measured native comparisons.
- Reject an over-broad build classifier and a failed renderer that was larger than a
  competent filtered native baseline.

## 0.5.0 - 2026-09-05

- Add the explicit Conda `package_kind` rule setting with `native` and `noarch` values.
- Represent noarch package jobs without inventing an empty native-platform matrix.
- Distinguish available, expired, unknown-expiry, and currently unobserved GitHub artifact
  evidence without claiming channel publication.
- Reject contradictory noarch rules that also require native platforms.
- Preserve trusted repository configuration in reviewed sanitized fixtures.

## 0.4.0 - 2026-09-04

- Add the first CI profile with conservative whole-word job roles and a visible `other`
  remainder.
- Group LLM failure output only when jobs share an official conclusion and the same
  ordered failed-step signature, while retaining every job in JSON.
- Add a sanitized seven-job MolSysViewer failure fixture and measured filtered-native
  comparison.
- Allow trusted repository rules and explicit CLI selection to choose `ci`.
- Correct fixture sanitization so optional captured configuration cannot select a member
  absent from the reviewed allow-list.

## 0.3.0 - 2026-09-04

- Load `.github/gh-run-receptor.yaml` only from the target repository's default branch
  and preserve its revision and digest in replayable bundles.
- Add strict dependency-free parsing for exact workflow path, ID, or name rules selecting
  the generic or Conda profile.
- Add `config check` and `config explain` for safe local validation.
- Enforce configured Conda platform expectations without changing GitHub's authoritative
  conclusion, and report missing platforms explicitly.
- Publish the `config@1` JSON Schema and reject unknown or ambiguous configuration.
- Resolve the version of a source extension from its own checkout before consulting an
  unrelated installed distribution.

## 0.2.1 - 2026-09-04

- Resolve the package version from the nearest numeric Git tag when running directly as a
  GitHub CLI script extension without installed metadata or a generated build file.

## 0.2.0 - 2026-09-04

- Adopt the flat MolSysSuite package layout and derive versions from three-component Git
  tags with `versioningit`.
- Add issue-backed developer reports with validated lifecycle metadata and generated queue
  indexes.
- Publish Draft 2020-12 schemas for `bundle@1`, `model@1`, and `report@1` inside the
  installed package.
- Separate source normalization from profile interpretation, with dimensional
  completeness, stable ordering, unknown-enum preservation, and source references.
- Reject malformed bundle manifests, duplicate JSON keys, non-finite numbers, unsafe or
  duplicate members, and byte-count or digest mismatches before replay.
- Add sanitized success and partial-failure MolSysMT Conda fixtures and deterministic,
  official-conclusion parity tests.

## 0.1.1 - 2026-09-04

- Add the first read-only `inspect`, `capture`, and `replay` vertical slice.
- Acquire run, workflow, paginated job, check-run, artifact, and optional log evidence
  through the authenticated GitHub CLI.
- Store immutable evidence members with SHA-256 validation and attempt-aware identities.
- Add distinct `human` and `llm` receptors plus a versioned JSON report.
- Infer the text receptor from terminal interactivity while allowing explicit selection.
- Preserve authoritative GitHub conclusions and provisional exit-code semantics.
- Build an installable, dependency-free Python wheel and a GitHub CLI extension launcher.
- Validate the MVP against a real MolSysMT Conda workflow capture.
- Add bounded, traversal-safe log analysis with terminal-control removal and causal-line
  provenance.
- Add conservative Conda-profile detection, reusable-platform reporting, and grouping of
  repeated cross-platform causes.
- Record the first reproducible MolSysMT pilot against a competent native filtered baseline.
- Accept common options before or after the selected subcommand.
- Collapse successful LLM reports to one semantic line while retaining full human and JSON
  detail.
- Report incomplete evidence as `INCOMPLETE` even when GitHub's source conclusion is
  successful.
- Add transition-only `watch` with unchanged-state backoff, bounded transient-error retry,
  terminal-safe job names, and one final adaptive report.
