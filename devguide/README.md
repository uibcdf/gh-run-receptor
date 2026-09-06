# gh-run-receptor developer guide

This directory is the development checkpoint for `gh-run-receptor`. It records the
product boundary, architectural decisions, rule model, and route to a stable release.
Documents should distinguish settled decisions from hypotheses that still require
evidence.

## Current state

The project has a `0.11.0` tagged source preview but no published package-index artifact or
stable public contract;
the contracts in this guide are explicit but provisional unless marked settled. The MVP
can capture structured evidence for one GitHub Actions run, replay it offline, and render
human, LLM, or JSON reports without changing the run or hiding its authoritative GitHub
state. Broader log interpretation, deeper profile contracts, published packaging, and
wider corpus validation remain open.

The current MVP implements:

- `inspect`, `capture`, and offline `replay` for one run attempt;
- authenticated acquisition through `gh api` of run, workflow, paginated jobs, checks,
  artifacts, and policy-selected logs;
- SHA-256-validated bundles separated by repository, attempt, and capture policy;
- a shared generic report rendered for `human`, `llm`, or JSON;
- numeric IDs and HTTPS run URLs, including repository and hostname extraction;
- authoritative outcome exit codes and bounded terminal-safe text;
- bounded log-cause extraction with archive and line limits;
- conservative Conda auto-detection, reusable-platform classification, and cross-job
  cause grouping;
- transition-only `watch` with polling backoff and a single final adaptive report;
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
  strict configuration proposals with visible confidence and ambiguity fallback.
- structured acquisition-error categories with bounded, control-safe, credential-redacted
  diagnostics and structured optional-404 handling.
- a manually dispatched nine-combination compatibility gate proving the Python console
  command, suite, build, wheel installation, and smoke path on Ubuntu, macOS, and Windows
  with Python 3.11 through 3.13.
- strict repository policy deployed across eight additional MolSysSuite clients, with 37
  exact workflow rules and metadata-only remote smoke validation.
- a first checkout-local composite Action implementation with bounded summaries, scalar
  outputs, canonical JSON artifacts, explicit publisher provenance, and offline tests;
  hosted cross-platform validation is pending.

It does not yet provide a broad cross-workflow corpus; run comparison; remote workflow
discovery; pattern rules; or a released and permission-validated embedded Action. The CI,
documentation, Conda, release, configuration, and Action contracts are initial vertical
slices, not their complete stable forms.

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
19. [Development roadmap](development_roadmap.md)

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
| Ordered implementation plan and release gates | `development_roadmap.md` |

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

The next milestone validates and releases the first composite Action on Ubuntu, macOS, and
Windows, including checkout-local GitHub CLI extension installation, honest active-run
state, terminal source outcomes, startup cost, and artifact bytes. It then closes the
remaining outcome and distribution gaps: Zenodo verification and a minimum supported
GitHub CLI.
Standard job timeout is now measured as cancellation; authentic
`timed_out` evidence remains opportunistic because it must not be inferred from elapsed
time or `timeout-minutes`. The milestone must also identify which release facts need
structured producer evidence or new capture sources rather than name inference.

The executable task list and exit criteria remain in
[development_roadmap.md](development_roadmap.md). The configuration and report contracts
remain provisional until this broader evidence gate is complete.
