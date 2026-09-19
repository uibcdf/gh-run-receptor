---
summary: Close the timed-out corpus gate without manufactured evidence
issue: uibcdf/gh-run-receptor#45
status: active
opened: 2026-09-19
closed:
verification: measured
area: ['tests', 'github']
guard:
normative:
blocked_by: []
supersedes: []
---

# Closing the `timed_out` corpus gate without manufactured evidence

**Reported:** 2026-09-19, after the release-evidence authority audit left authentic
`timed_out` as the only withheld roadmap percentage.
**Status:** Active implementation backed by an upstream-contract review, a measured
failed generator experiment, and an end-to-end exact-source guard.

## What

Define when a valid upstream outcome that cannot be generated safely and reproducibly may
be accepted for the 1.0 evidence corpus without a committed authentic fixture. Apply that
rule to GitHub's `timed_out` conclusion and add an end-to-end semantic guard from exact
source value through assessment, rendering, and process status.

The goal is not to claim that a standard Actions timeout produces `timed_out`. It is to
prove that gh-run-receptor preserves the conclusion if GitHub supplies it, while retaining
the measured fact that the ordinary timeout setting produces `cancelled`.

## How

An authentic fixture is not a 1.0 blocker when all of these conditions hold:

1. the upstream read API documents the exact value as a valid status or conclusion;
2. no safe, bounded, read-only or ordinary workflow mechanism can reproducibly create it;
3. the nearest safe live experiment records the actual different outcome and the product
   proves it does not infer the target value;
4. a complete synthetic evidence object carries the exact upstream field through
   normalization, assessment, every renderer, and the stable exit-code boundary; and
5. authentic read-only evidence remains eligible for later sanitization without changing
   the established semantics.

This is an exception for upstream states, not permission to substitute synthetic evidence
for ordinary success, failure, cancellation, artifact, permission, or publication cases
that can be observed safely.

## Why

The current roadmap withholds one percentage point indefinitely even though the proposed
safe generator was empirically refuted. Requiring a custom GitHub App to write a
manufactured check would cross the product's read-only security boundary and would not
prove the behavior of a native workflow run. A criterion that rewards that manufacture
would be weaker than preserving the honest absence.

Conversely, silently deleting the requirement would leave only a narrow platform-state
test. The end-to-end guard and explicit exception policy preserve the intended safety
property: a source `timed_out` value can never become success or failure by inference.

## What is measured and what is assumed

GitHub's current workflow syntax says `jobs.<job_id>.timeout-minutes` automatically
cancels a job. Repository-owned run `34027741137` measured the same result at run, job,
and interrupted-step level and gh-run-receptor returned `CANCELLED` with process status 2.

The GitHub workflow-runs REST endpoint nevertheless accepts `timed_out` as a conclusion
filter, and the Checks documentation defines `timed_out` separately from `cancelled`.
These current upstream surfaces were re-inspected on 2026-09-19. Prior bounded searches
found no authentic example across 31 UIBCDF repositories, and a later search across 17
large public repositories also found none.

A broader authenticated read-only scan on 2026-09-19 queried ten deduplicated cohorts:
repositories above 50,000 stars; repositories with the `github-actions` topic; high-star
Python, JavaScript, TypeScript, Rust, and Go repositories; and the public `github`,
`actions`, and `apache` organizations. It queried 889 distinct repositories through:

```text
gh api "repos/OWNER/REPO/actions/runs?status=timed_out&per_page=5"
```

All 889 requests succeeded and every response reported `total_count=0`. The first summary
parser incorrectly labelled zero-count rows as hits because POSIX `sh` did not interpret a
Bash-specific tab literal; recalculation directly from the retained tabular responses
reported 889 responses, zero errors, and zero authentic hits. The parser was corrected
before accepting the summary. This is a broad negative sample, not proof that GitHub has
never emitted the value.

Before this increment the repository preserved `timed_out` in a parametrized Conda
platform-state test, but lacked one test asserting the run assessment, both text
renderers, JSON source truth, and exit status together.

## What was refuted

- `timeout-minutes` as a generator was refuted by official semantics and live run
  `34027741137`.
- Treating the measured cancellation as timeout evidence is rejected because the values
  are distinct upstream conclusions.
- Waiting indefinitely for an accidental public run is rejected as a release gate because
  it is neither controlled nor reproducible.
- Creating a write-capable GitHub App check is rejected: it expands the security boundary,
  manufactures rather than observes evidence, and does not establish workflow-run
  behavior. Such an App could later validate check-level `timed_out` semantics under a
  separately reviewed scope.
- Treating a printed log marker as the authoritative outcome is rejected because workflow
  output is untrusted and trivially spoofed. A future structured producer event could
  expose a distinct `producer_timeout` diagnostic, but it must not become GitHub's
  authoritative `TIMED_OUT` assessment.
- Removing `timed_out` support is rejected because GitHub's read API still exposes it as
  a valid conclusion and the open-enum model can preserve it safely.

## Scope and exclusions

This proposal does not claim an authentic `timed_out` workflow-run observation, add a
scheduled failure generator, request write permissions, or equate Checks API and Actions
run production paths. It does not relax real evidence requirements for reproducible
outcomes or external delivery.

## Acceptance criteria

- One end-to-end test starts with exact `run.json` and job `timed_out` values and proves
  `TIMED_OUT`, source-value preservation, bounded human/LLM rendering, and process status
  2.
- The testing strategy and GitHub-evidence contract state the five-condition exception.
- Public limitations distinguish implemented support from authentic-corpus absence.
- The roadmap records Phase 0 as complete without claiming an authentic fixture and
  reports 100% evidence credit toward the defined 1.0 scope.
- No workflow, token permission, serialized schema, or production implementation changes.
- Full tests, Ruff, frozen contracts, strict documentation, and devguide validation pass.

## Dependencies and risks

There is no external blocker. The main risk is using this exception to lower an otherwise
observable gate. The five conditions are conjunctive, name the unavailable generator, and
retain later authentic capture as additive evidence. A second risk is mistaking the
absence of hits in 889 repositories for impossibility; the contract says absent and
opportunistic, never impossible.

## Implementation and validation

`test_timed_out_source_reaches_assessment_renderers_and_exit_boundary` constructs exact
run, job, and step `timed_out` source values. It proves the report retains those values,
derives `TIMED_OUT`, renders bounded human and LLM output, and returns the stable terminal
non-success process status 2. No production module, serialized schema, workflow, or token
permission changed.

The policy was absorbed by `testing_strategy.md`, `github_evidence.md`, the public
limitations, roadmap, and checkpoint. The roadmap now assigns Phase 0 its final evidence
point and reports 100% implementation/evidence credit toward the defined 1.0 scope while
explicitly distinguishing that result from publication of a 1.0 tag.

The local gate on 2026-09-19 produced:

- `python -m pytest --receptor=llm`: 440 passed;
- `ruff check .`: passed;
- focused Ruff format validation: passed;
- `python devtools/scripts/validate_contracts.py`: nine contracts passed against the
  frozen 0.21.0 baseline;
- strict Sphinx: ten pages built without warnings;
- developer-report validation and `git diff --check`: passed.

## Provenance

The original experiment ran on GitHub-hosted Ubuntu at commit
`a87e5b9748ceaf1d6c5277a34dd2d533eca11865`, run `34027741137`, on 2026-09-06.
Current official GitHub workflow-syntax, workflow-runs REST, and status-check documentation
was inspected on 2026-09-19. Local implementation begins from gh-run-receptor commit
`92563439f2c2b9047bf298107fdd80da0e43b946` with Python 3.13.14, Ruff 0.16.1, and Sphinx
8.2.3.
