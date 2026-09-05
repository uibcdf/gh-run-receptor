# Changelog

All notable changes to this project will be documented in this file.

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
