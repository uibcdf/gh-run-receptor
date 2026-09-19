# gh-run-receptor developer guide

This directory is the development checkpoint for `gh-run-receptor`. It records the
stable product boundary, architectural decisions, rule model, and post-1.0 route.
Documents should distinguish settled decisions from hypotheses that still require
evidence.

## Current state

The project has published and independently verified stable `1.0.0` GitHub Release assets,
MolSysSuite dogfooding, and a public Zenodo record. The stable scope is frozen in
`release_readiness_1_0.md`; no package-index artifact is claimed. All nine published
serialized boundaries are frozen
against their first publishing tags, including the `aggregate@1` boundary introduced in
0.21.0. The 1.0 product boundary is frozen. Release 0.22.0 adds the
public documentation site, freezes adaptive log acquisition, and stabilizes measured
transition-only watch behavior without changing a serialized contract.
The stable product
can capture structured evidence for one GitHub Actions run, replay it offline, and render
human, LLM, or JSON reports without changing the run or hiding its authoritative GitHub
state. Broader log interpretation, deeper profile contracts, package-index distribution,
and wider corpus validation are possible post-1.0 work, not missing stable-release gates.

The current MVP implements:

- `inspect`, `capture`, and offline `replay` for one run attempt;
- authenticated acquisition through `gh api` of run, workflow, paginated jobs, checks,
  artifacts, and policy-selected logs;
- a frozen adaptive log-acquisition truth table with paired full/adaptive request, byte,
  incomplete-retention, and diagnostic measurements;
- SHA-256-validated bundles separated by repository, attempt, and capture policy;
- a shared generic report rendered for `human`, `llm`, or JSON;
- a public task-oriented Sphinx/MyST site covering installation, CLI use, profiles,
  embedded reporting, configuration, contracts, security, limitations, and benchmarks,
  deployed through a least-privilege GitHub Pages workflow;
- numeric IDs and HTTPS run URLs, including repository and hostname extraction;
- authoritative outcome exit codes and bounded terminal-safe text;
- a stable non-overlapping process-status map that distinguishes source failure, other
  terminal non-success, active work, incomplete evidence, receptor error, invalid usage,
  and user interruption;
- bounded log-cause extraction with archive and line limits;
- conservative Conda auto-detection, reusable-platform classification, and cross-job
  cause grouping;
- stable transition-only `watch` with deterministic polling backoff, an explicit per-page
  API formula, identity-checked terminal evidence reuse, and a single final adaptive report;
- machine-readable `bundle@1`, `model@1`, and `report@1` schemas, with strict bundle
  validation and source-referenced normalization;
- sanitized success and partial-failure MolSysMT Conda fixtures plus a successful
  MolSysViewer noarch fixture with deterministic replay and official-conclusion parity
  tests;
- sanitized real cancellation, expired-log incompleteness, and paired failed/successful
  rerun fixtures, with attempt-consistent source validation and exit-code parity;
- strict `config@1` repository rules captured only from the default branch, with exact
  workflow matching, provenance, local validation, Conda platform expectations, and an
  explicit native/noarch package kind;
- a first CI profile that preserves all jobs, assigns bounded presentation roles, and
  groups identical failed-step signatures in LLM output;
- noarch Conda summaries that retain job and artifact identity without inventing a native
  matrix or claiming channel publication;
- a documentation profile that preserves complete step state, distinguishes bounded
  phases, and keeps combined build/deploy evidence indivisible;
- a release profile that preserves observed event/ref/SHA identity, keeps composite work
  indivisible, and distinguishes step success from external delivery verification.
- deterministic local workflow discovery and a non-overwriting `init` command that emits
  strict configuration proposals with visible confidence, ambiguity fallback, and safe
  handling of the known action-internal Conda publication shape.
- structured acquisition-error categories with bounded, control-safe, credential-redacted
  diagnostics and structured optional-404 handling.
- a manually dispatched nine-combination compatibility gate proving the Python console
  command, suite, build, wheel installation, and smoke path on Ubuntu, macOS, and Windows
  with Python 3.11 through 3.13.
- strict repository policy deployed across eleven additional MolSysSuite clients, with 63
  exact workflow rules accepted by the published parser, plus the canonical 0.22.0 guide
  synchronized byte-for-byte across twelve client repositories.
- a first checkout-local composite Action implementation with bounded summaries, scalar
  outputs, canonical JSON artifacts, explicit publisher provenance, and offline tests;
  hosted checkout-local and remote-source validation passing on all three operating systems.
- a live read-only downstream `workflow_run` integration that reports a completed source
  run with exact identity/conclusion parity and no source checkout.
- explicit bounded consumption of one Action report artifact with GitHub digest and fresh
  terminal source-fact verification, validated as an extension on all three operating systems.
- one-command source-first discovery through deterministic attempt-qualified artifacts and
  an exact canonical reporter workflow, validated live and as an extension on all three
  operating systems.
- trusted inline Action `config@1` rules with default-branch caller provenance, stable
  ready/error outputs, exact public permission probes, and live same-repository
  pull-request rejection before acquisition.
- an enforced GitHub CLI 2.48.0 functional floor for network commands, with lazy
  pre-acquisition rejection, offline independence, and checksum-pinned hosted validation
- a hosted exact-tag GitHub Release path with consistent citation/Zenodo metadata,
  draft-first asset verification, public-release revalidation, and completed
  uninterrupted publications through 0.22.0.
- a bounded read-only Zenodo verification gate with distinct absent, invalid, and verified
  states plus an explicit maintainer activation handoff; the 0.22.0 record and both its
  version and concept DOI have been independently observed.
- a first portable live corpus spanning three non-UIBCDF repositories, including native
  conclusion parity, bounded output, and deterministic offline replay.
- one centralized release-claim authority map separating GitHub source facts,
  name-derived presentation facets, workflow-step success, Actions artifact inventory,
  and unavailable external delivery, with adversarial claim-name guards.
- one runtime registry for nine serialized boundaries, formal configuration-capture
  schema, offline compatibility introspection, forward-only migration rules, and a release
  gate retaining the four v1 freezes from 0.18.0, three from 0.19.0, and the producer-event
  freeze from 0.20.0 while assigning only the new aggregate boundary to 0.21.0.
- a first-class offline and remote `compare` command with an independently versioned
  comparison contract, explicit source/commit identity, bounded human and LLM output, and
  descriptive job, duration, artifact-inventory, and matrix-coverage deltas.
- strict opt-in `comparison-policy@1` files with explicit identity, candidate outcome,
  duration, artifact-size, inventory, and matrix rules plus distinct pass, violation, and
  unknown-evidence results.
- a call-only reusable terminal reporter that forwards typed policy to the shared Action,
  exposes durable cross-job outputs, and resolves its Action from the exact same repository
  revision without a checkout or internal moving reference.
- bounded attempt-qualified producer-event acquisition, exact source-identity validation,
  offline normalization, and Conda hidden-platform aggregation, validated end to end with
  two hosted producer jobs on Linux and Windows and a sanitized deterministic replay.
- real downstream adoption in MolSysMT, where the public 0.20.0 wheel consumed a
  failure-safe `events@1` artifact from a non-publishing Linux ABI3 build and reported
  exact platform, build, upload-intent, job, and artifact state.
- a bounded `aggregate` command that preserves independent source truth for
  two to fifty offline or remote runs; its first live cross-repository pilot summarizes
  two workflows, five jobs, and five artifacts with complete successful evidence, and its
  hosted negative case preserves a real MolSysViewer failure.

It does not yet provide a broad cross-workflow corpus beyond that initial external sample;
policy-driven run discovery; pattern rules; or validated private-repository
and fork token behavior. The CI,
documentation, Conda, release, configuration, and Action contracts are initial vertical
slices, not their complete stable forms. Action-internal native matrices now have a hosted
structured per-platform representation and a published 0.20.0 contract freeze.

## Reading order

1. [Product and scope](product_and_scope.md)
2. [Motivation and measured evidence](motivation_and_evidence.md)
3. [Architecture](architecture.md)
4. [GitHub evidence sources](github_evidence.md)
5. [CLI and output contract](cli_and_output_contract.md)
6. [Data contracts](data_contracts.md)
7. [Rules and profiles](rules_and_profiles.md)
8. [Embedded reporting](embedded_reporting.md)
9. [Security](security.md)
10. [Testing strategy](testing_strategy.md)
11. [Development workflow](development_workflow.md)
12. [Reporting protocol](reporting_protocol.md)
13. [Versioning and releases](versioning_and_releases.md)
14. [Pending bugs](pending_bugs/README.md)
15. [Pending proposals](pending_proposals/README.md)
16. [Decisions and open questions](decisions_and_open_questions.md)
17. [MVP validation checkpoint](mvp_validation.md)
18. [MolSysMT Conda pilot benchmark](benchmark_2026-09-04.md)
19. [Watch polling and output benchmark](benchmark_watch_2026-09-19.md)
20. [Development roadmap](development_roadmap.md)
21. [1.0 release readiness](release_readiness_1_0.md)

These documents and the pending queue indexes are the current checkpoint. The
[archive summary](archive/README.md) is the normal historical entry point. Routine
onboarding does not require reading archived reports; inspect one only when a current
question or document gives a concrete reason.

## Checkpoint coverage

The checkpoint is complete for beginning Phase 0 and Phase 1. Completeness means that a
new contributor can find the current answer or an explicit decision gate for every
known design question; it does not mean that unimplemented behavior has been validated.

| Concern | Authoritative document |
| --- | --- |
| Product boundary and delivery modes | `product_and_scope.md` |
| Origin, baseline, and prior art | `motivation_and_evidence.md` |
| Component boundaries and data flow | `architecture.md` |
| GitHub endpoints, permissions, and limitations | `github_evidence.md` |
| Commands, verdicts, exit codes, and channels | `cli_and_output_contract.md` |
| Bundle, event, report, and producer schemas | `data_contracts.md` |
| Workflow selection, profiles, rules, and precedence | `rules_and_profiles.md` |
| Action and reusable-workflow behavior | `embedded_reporting.md` |
| Threat model and resource limits | `security.md` |
| Corpus, fixtures, differential tests, and token measurement | `testing_strategy.md` |
| Environment, layout, contribution, and validation | `development_workflow.md` |
| Issue/report lifecycle | `reporting_protocol.md` |
| Package versions, tags, and release gate | `versioning_and_releases.md` |
| Settled decisions and unresolved choices | `decisions_and_open_questions.md` |
| Implemented surface and real-run validation | `mvp_validation.md` |
| Measured native baseline and token reduction | `benchmark_2026-09-04.md` |
| Watch polling, API budget, and native comparison | `benchmark_watch_2026-09-19.md` |
| Ordered implementation plan and release gates | `development_roadmap.md` |
| Stable 1.0 scope, exclusions, and evidence map | `release_readiness_1_0.md` |

## Settled direction

- The core is a read-only consumer of GitHub Actions evidence.
- GitHub conclusions remain authoritative; the receptor interprets but never rewrites
  them.
- Complete evidence may be downloaded to disk without being printed. Token economy is
  achieved by bounding stdout, not by discarding the evidence needed for diagnosis.
- The command-line client, GitHub Action, and reusable reporting workflow share one
  normalized evidence model and renderer.
- `human` and `llm` identify the intended reader; JSON is an orthogonal serialization
  format. Interactive text defaults to `human`, redirected text to `llm`.
- Built-in workflow profiles are complemented by safe declarative configuration.
- Arbitrary commands or executable expressions are not part of the rule language.
- Mutation such as rerunning, cancelling, or publishing is outside the initial scope.

## Immediate milestone

The defined 1.0 implementation and evidence gates now have full credit. OD-002 has a
measured stable adaptive capture rule, OD-005 has measured stable watch semantics, and the
released 1.0.0 client guide is synchronized across all twelve tracked repositories.
Phase 1 includes byte-identical CLI replay across temporal, filesystem, renderer,
operating-system, and supported-Python contexts. The release-profile authority map
identifies which facts need structured producer evidence or new capture sources rather
than name inference.

Standard job timeout is measured as cancellation. Exact-source `timed_out` now passes the
complete assessment, renderer, and process-status path under the documented
non-generatable-outcome exception; authentic capture remains visibly absent and
opportunistic. The stable scope, exact-commit gates, 1.0.0 publication, independent
archive verification, client-guide synchronization, and installed public-version
dogfooding now pass, and 1.0.0 is public. New work follows stable compatibility rules.
The only current product proposal is the explicitly post-1.0 structured timeout evidence
integration in `uibcdf/gh-run-receptor#46`, blocked on `uibcdf/molsyssuite#25`.

The executable task list and release criteria remain in
[development_roadmap.md](development_roadmap.md).
