# gh-run-receptor developer guide

This directory is the development checkpoint for `gh-run-receptor`. It records the
product boundary, architectural decisions, rule model, and route to a stable release.
Documents should distinguish settled decisions from hypotheses that still require
evidence.

## Current state

The project is in its inception phase. No implementation or stable public contract exists
yet; the contracts in this guide are explicit but provisional unless marked settled.
The immediate goal is a read-only prototype that can capture a GitHub Actions run,
replay the captured evidence offline, and render a compact report without changing the
run or hiding its authoritative GitHub state.

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
12. [Decisions and open questions](decisions_and_open_questions.md)
13. [Development roadmap](development_roadmap.md)

These documents are the current checkpoint. There is no historical archive yet.
When an archive is introduced, routine onboarding should require only its generated
summary or index unless a concrete question requires the underlying historical record.

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
| Settled decisions and unresolved choices | `decisions_and_open_questions.md` |
| Ordered implementation plan and release gates | `development_roadmap.md` |

## Settled direction

- The core is a read-only consumer of GitHub Actions evidence.
- GitHub conclusions remain authoritative; the receptor interprets but never rewrites
  them.
- Complete evidence may be downloaded to disk without being printed. Token economy is
  achieved by bounding stdout, not by discarding the evidence needed for diagnosis.
- The command-line client, GitHub Action, and reusable reporting workflow share one
  normalized evidence model and renderer.
- Built-in workflow profiles are complemented by safe declarative configuration.
- Arbitrary commands or executable expressions are not part of the rule language.
- Mutation such as rerunning, cancelling, or publishing is outside the initial scope.

## Immediate milestone

The first milestone is an evidence-capture spike against real archived runs from the
UIBCDF repositories. It must answer three questions before the public interface is
frozen:

1. Which GitHub API responses are sufficient for reliable generic reporting?
2. When are full logs required, and when can job, step, check, and artifact metadata
   provide the answer?
3. Can the same stored evidence be replayed deterministically across receptor versions?

The executable task list and exit criteria for this milestone are in
[development_roadmap.md](development_roadmap.md). No public API should be frozen before
the evidence spike is complete.
