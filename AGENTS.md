# gh-run-receptor repository guide

This file defines the baseline rules for automated agents and human contributors. A
more local `AGENTS.md` may refine these rules within its directory.

Read `MOLSYSSUITE_GUIDE.md` before development. It is the synchronized, read-only
suite-governance guide owned by `uibcdf/molsyssuite` and routes shared policies,
cross-component feedback, and issue ownership.

## Language and documentation

- Write all repository-facing text in English, including code, comments, docstrings,
  tests, configuration, commit messages, and developer documentation.
- Treat `devguide/README.md` as the development checkpoint and required reading before
  substantial work.
- Read the current documents linked by the checkpoint. Do not read a future historical
  archive in full unless a concrete question requires it; its summary or index is the
  normal entry point.
- Update the devguide in the same change whenever a decision, contract, supported mode,
  threat boundary, or roadmap state changes.
- Mark proposals and unverified behavior as provisional. Do not present design intent as
  measured behavior.
- Read `devguide/reporting_protocol.md` before filing or closing a substantial defect or
  proposal. Every pending developer report must be backed by a GitHub issue; the report
  carries analysis while the issue carries public state and settled facts.
- Route policies, compatibility contracts and proposals shared by multiple components to
  `uibcdf/molsyssuite`. Keep gh-run-receptor product behavior, implementation and evidence
  in this repository, linked across repositories by stable `uibcdf/<repo>#<number>`
  references. This repository adopts MolSysSuite policy 1.0.

## Product invariants

- Preserve GitHub's status and conclusion as source facts. Derived assessments such as
  `PARTIAL` never replace them.
- Never report incomplete, cancelled, timed-out, stale, action-required, or failed work
  as successful.
- Prefer structured API evidence over log-text inference.
- Preserve unknown jobs, steps, conclusions, and unmatched errors in the generic report.
- Keep capture separate from rendering: evidence may be complete on disk while stdout
  remains bounded.
- Treat logs, artifacts, workflow configuration, and pull-request content as untrusted.
- Keep the initial product read-only with respect to GitHub state. Suggested commands
  may be rendered, but reruns, cancellation, approval, upload, deployment, and deletion
  require a future explicit mutation boundary.
- The CLI, GitHub Action, and reusable workflow must share one normalized model and one
  rendering contract.

## Implementation baseline

- Release 1.1.0 supports Python 3.11--3.14 as a package and CLI; older 1.0.0 artifacts
  retain their original 3.11--3.13 support boundary.
- Keep the import package at repository root, matching the flat MolSysSuite layout; do not
  reintroduce a `src/` directory without a measured packaging reason.
- Use the installed `gh` command for authentication and GitHub API transport. Do not add
  a second authentication system or expose tokens through command arguments or output.
- Keep GitHub response acquisition behind an adapter so a future standalone executable
  or alternate transport does not affect normalization, profiles, or rendering.
- Use versioned, typed internal models. Keep source facts, normalized facts, profile
  interpretations, and rendered text separate.
- Avoid dependencies unless they materially reduce risk. Record every runtime dependency
  decision in the devguide.
- Do not execute configuration content. Avoid unsafe YAML loaders, unbounded regular
  expressions, archive extraction without path and size validation, and implicit trust
  in the current pull-request checkout.

## Testing and validation

- Use `pytest --receptor=llm` for test execution.
- Use Ruff for linting and formatting checks.
- Test behavior primarily through captured and sanitized evidence bundles. Networked
  tests are a separate, explicitly marked layer.
- Every verdict and exit-code rule requires a truth-table test.
- Every parser requires malformed, truncated, unknown-field, and size-boundary tests.
- Every renderer requires deterministic golden tests and an output-size assertion.
- Compare reports against the authoritative GitHub conclusions represented in fixtures;
  a compact report is not correct merely because it matches expected text.
- Never weaken a truth or security invariant to make a fixture pass.

## Git and changes

- Keep commits focused and do not add attribution trailers.
- Select batching and any permitted interim CI skip conditionally through the
  common checkpoint route; local validation does not imply skipping every push.
- Do not use destructive Git commands or force pushes.
- Preserve unrelated user changes in a dirty worktree.
- Do not commit raw evidence bundles, credentials, caches, downloaded logs, or private
  repository data. Only reviewed and sanitized fixtures belong in the repository.
- Derive versions from three-component Git tags through `versioningit`; do not maintain a
  static package version or move an existing release tag.

## Required design references

- `devguide/product_and_scope.md`
- `devguide/architecture.md`
- `devguide/github_evidence.md`
- `devguide/cli_and_output_contract.md`
- `devguide/data_contracts.md`
- `devguide/rules_and_profiles.md`
- `devguide/embedded_reporting.md`
- `devguide/security.md`
- `devguide/testing_strategy.md`
- `devguide/development_workflow.md`
- `devguide/reporting_protocol.md`
- `devguide/versioning_and_releases.md`
- `devguide/decisions_and_open_questions.md`
- `devguide/mvp_validation.md`
- `devguide/benchmark_2026-09-04.md`
- `devguide/development_roadmap.md`
- `devguide/release_readiness_1_0.md`
- `standards/GH_RUN_RECEPTOR_GUIDE.md`
- `PYTEST_RECEPTOR_GUIDE.md` — synchronized, read-only contract for the pytest renderer
  used by this repository's test commands.

## Direct pushes and scoped local validation

Follow [the common checkpoint policy](MOLSYSSUITE_GUIDE.md#direct-pushes-and-validation-checkpoints)
for authorized internal direct pushes by `dprada` and `LMMV`. Batch focused local
commits when remote visibility is unnecessary; a permitted interim CI skip is
conditional, never the default after every locally checked change. Retain local
results while tested code, inputs, environment and scope remain applicable.
Normally finish with an unskipped head and inspect its applicable CI, or explicitly
execute and verify those exact-head gates manually. Record missing evidence,
untested scope, owning issue and recovery route; administrative checks do not
clear full-suite backlog. External PRs, admission and publication require all
mandatory executed gates for the exact candidate and required installed file.
An authorized manual qualification retains the original producer and artifact
bytes/digest; a marker alone neither waives a gate nor disqualifies that evidence.

## Modular reusable tools

Before adding a feature, inspect existing tools and identify the owning module or
component. Implement or extend independently useful operations as documented reusable
tools in that owner, with their own contracts and tests; have consumers call them.
Keep task-specific decisions local and report missing sibling capabilities to the
provider with linked consumer evidence. Follow
[MOLSYSSUITE_GUIDE.md#modular-reusable-tools](MOLSYSSUITE_GUIDE.md#modular-reusable-tools)
for applicability, compatibility, performance and tracked exceptions.

## Durable working instructions

Keep technical findings in owning issues, fixes, tests and maintained guidance.
Place only accepted lasting contributor actions in root or appropriately scoped
instructions, following
[the common policy](MOLSYSSUITE_GUIDE.md#durable-working-instructions).
For work under `devguide/`, also read [devguide/AGENTS.md](devguide/AGENTS.md)
and its local reporting protocol. Shared instruction proposals belong in
`uibcdf/molsyssuite`; cross-MOLI contracts belong in `uibcdf/moli`.

## Human-facing issue feedback

Surface actionable suspected defects, inconsistencies, missing analyses and
improvements, including uncertain or nonblocking findings. When working with a
human, offer an owning issue at a natural pause; retain existing reporting
authorization and respect declined/deferred disclosure. Follow
[the accepted feedback route](MOLSYSSUITE_GUIDE.md#human-facing-issue-feedback)
for ownership, uncertainty, privacy and exceptions.
