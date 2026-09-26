---
summary: Targeted Conda dispatch is misclassified by the full matrix rule
issue: uibcdf/gh-run-receptor#54
status: resolved
opened: 2026-09-24
closed: 2026-09-26
severity: high
verification: measured
area: [profiles, reports, tests]
guard: tests/test_report.py
normative: rules_and_profiles.md
blocked_by: []
supersedes: []
---

# Targeted Conda dispatch is misclassified by the full matrix rule

**Reported:** 2026-09-24, from MolSysMT run `35963306739`.
**Status:** Resolved with an explicit per-invocation expectation override.

## What

A successful `workflow_dispatch` targeting `linux-aarch64` ran its requested jobs and
produced artifacts, but the repository's five-platform static rule marked the other four
platforms missing and derived `FAIL`. Reproduce with a successful one-platform Conda
bundle and the full `expected_platforms` rule: the default report fails; invoking
`replay BUNDLE --expected-platforms linux-aarch64` assesses the requested subset.

## How

The rule has no per-invocation target, and GitHub's workflow-run response does not expose
dispatch inputs. The receptor now accepts a caller-asserted platform subset for `inspect`,
`watch`, and `replay`, checks that it belongs to the configured native Conda list, and
records both lists with explicit provenance in the report. The trusted rule remains full.

## Why

The targeted run is useful validation evidence but was presented as a failed full release
matrix. A per-invocation assertion lets its report describe the requested scope without
weakening the default full-matrix gate.

## What is measured and what is assumed

On 2026-09-26, `gh api repos/uibcdf/molsysmt/actions/runs/35963306739` returned
`event=workflow_dispatch`, `conclusion=success`, and no `inputs` field. The issue records
the requested `linux-aarch64` target and three successful jobs. The CLI override is an
explicit caller assertion; the receptor cannot independently verify that dispatch input
from the captured run response. Synthetic tests exercise targeted success, missing target,
and default full-matrix omission. A metadata capture of that public run, inspected with
`--expected-platforms linux-aarch64`, returned `PASS`, `platforms=1/1`, `jobs=4/4`, and
exit code 0. Replaying the same bundle without the flag returned `FAIL`, four missing
platforms, the dispatch-input warning, and exit code 1. Replaying with
`--expected-platforms osx-arm64` returned `FAIL` with the requested platform missing.

## What was refuted

- Inferring target scope from observed jobs would classify an accidentally incomplete
  full run as a targeted success.
- Removing platforms from the repository rule would weaken the release gate.
- GitHub's run conclusion cannot be rewritten to justify either assessment.

## Scope and exclusions

The override applies to one report invocation and is not stored in the source bundle.
The default full-matrix interpretation remains in force without the flag. The receptor
does not read workflow logs or artifacts to guess dispatch inputs.

## Acceptance criteria

- A declared target with successful platform evidence yields `PASS` and exit code 0.
- A declared target absent from the run yields `FAIL` and exit code 1.
- Without the override, omitted configured platforms still fail the full-matrix check,
  while a dispatch warning identifies the unavailable selection evidence.
- Human, LLM, and JSON reports expose the override and preserve source conclusions.

## Dependencies and risks

There are no blockers. An incorrect caller assertion could narrow the report's scope;
the override is therefore restricted to configured subsets and disclosed on every output.

## Provenance

Public MolSysMT run `35963306739`, inspected through `gh api` and
`python -m gh_run_receptor inspect 35963306739 --repo uibcdf/molsysmt --capture metadata`
with the explicit platform flag on 2026-09-26. The saved bundle was replayed with and
without the flag. Local host: Linux, Python 3.13, gh-run-receptor checkout based on
`6de1f1c`. Raw evidence remained outside the repository.
