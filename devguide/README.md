# gh-run-receptor developer guide

This directory is the development checkpoint for `gh-run-receptor`. It records the
product boundary, architectural decisions, rule model, and route to a stable release.
Documents should distinguish settled decisions from hypotheses that still require
evidence.

## Current state

The project is in its inception phase. No implementation or public contract exists yet.
The immediate goal is a read-only prototype that can capture a GitHub Actions run,
replay the captured evidence offline, and render a compact report without changing the
run or hiding its authoritative GitHub state.

## Reading order

1. [Product and scope](product_and_scope.md)
2. [Architecture](architecture.md)
3. [Rules and profiles](rules_and_profiles.md)
4. [Development roadmap](development_roadmap.md)

These four documents are the current checkpoint. There is no historical archive yet.
When an archive is introduced, routine onboarding should require only its generated
summary or index unless a concrete question requires the underlying historical record.

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

