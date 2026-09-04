---
summary: Add the first CI workflow profile
issue: uibcdf/gh-run-receptor#6
status: resolved
opened: 2026-09-04
closed: 2026-09-04
verification: measured
area: ['profiles', 'tests']
guard: tests/test_report.py
normative: rules_and_profiles.md
blocked_by: []
supersedes: []
---

# Adding the first CI workflow profile

**Reported:** 2026-09-04, after trusted client rules shipped in 0.3.0.
**Status:** Resolved in `gh-run-receptor` 0.4.0 and validated from both client repositories.

## What

Add `ci` as the next truth-preserving profile and validate it first against MolSysViewer
and MolSysMT. The profile must make repeated CI failures more compact than a competent
native filtered view while retaining every normalized job in JSON and the evidence bundle.

## How

Assign each job one conservative presentation role: `publish`, `docs`, `lint`, `coverage`,
`test`, `build`, or `other`. Matching uses normalized whole words and a fixed priority;
every job appears exactly once, and `other` is never discarded. The role is presentation
metadata and cannot alter GitHub status, conclusions, or exit codes.

For LLM failure output, group jobs only when their official conclusion and ordered failed
step names are identical. Each group reports its size and one deterministic sample. All
member names, IDs, outcomes, timings, and failed steps remain in report JSON. A successful
CI report remains one line.

## Why

MolSysMT and MolSysViewer CI matrices are inspected repeatedly during stabilization. Their
job output contains the same failure phase across several Python/platform jobs, making
per-job text repetitive. Exact repository rules also avoid relying on name-based profile
auto-detection.

## What is measured and what is assumed

Public MolSysViewer run `33923020037` contains seven failed jobs. A native JSON view
filtered to status, conclusion, job name, job conclusion, and failed-step names measured
223 `cl100k_base` tokens. The first ungrouped CI renderer measured 310 tokens and was
rejected. Grouping identical failed-step signatures reduced the receptor output to 198
tokens (11.2%) while additionally reporting CI roles, artifact absence, run identity, and
URL.

The sanitized fixture and unit tests use:

```text
python -m pytest --receptor=llm
```

## What was refuted

- Merely changing `profile=generic` to `profile=ci` was rejected: measurement showed that
  role labels alone increased output by 39% against the filtered baseline.
- Substring matching was rejected after `test` matched the runner suffix `latest`; role
  keywords now match normalized whole words.
- Grouping by a generic failure conclusion alone was rejected because unrelated failure
  phases would collapse together.
- Turning an official CI failure into `PARTIAL` was rejected. Reusable-artifact semantics
  remain specific to profiles that can prove them.

## Scope and exclusions

This slice does not define configurable job roles, required job names, CI matrix
expectations, coverage thresholds, annotation parsing, structured producer events, or
minimal rerun commands. It does not implement the documentation or release profiles.

## Acceptance criteria

- `ci` is accepted by CLI and trusted repository configuration.
- Every job receives exactly one role and unknown names remain under `other`.
- Whole-word matching cannot mistake `latest` for `test`.
- Only identical conclusion/failed-step signatures group in LLM text.
- JSON retains every job even when LLM text uses a representative sample.
- Official failure, nonterminal, cancellation, incompleteness, and exit behavior remain
  unchanged.
- A reviewed MolSysViewer CI fixture crosses bundle, model, and report schema gates.
- MolSysMT and MolSysViewer adopt exact rules only after the implementing tag is released.

## Dependencies and risks

No tracked dependency blocks this slice. Role inference from display names is intentionally
limited and remains presentation-only. Renamed or unknown jobs fall into `other` rather
than disappearing or changing the assessment.

## Provenance

Measured on 2026-09-04 on the local Linux development host with Python 3.13, tiktoken
0.13.0 `cl100k_base`, GitHub CLI authenticated against the public MolSysViewer repository,
and run attempt 1 of `33923020037`.

## Delivered and verified

The implementation shipped in commit `2909376` and tag `0.4.0`. The local release gate
passed 81 tests, Ruff, both developer-report validators, source distribution and wheel
builds, and an isolated wheel replay smoke test.

Client adoption followed the tag, as required:

- MolSysMT commit `00fa4dd66` assigns the CI profile to eight exact workflow paths while
  retaining its four Conda rules.
- MolSysViewer commit `2750785d` assigns the CI profile to `CI`, `CI_e2e`, and Ruff, and
  the Conda profile to its noarch package workflow without native platform expectations.

Default-branch configuration was then exercised against public runs, rather than only
checked offline:

- MolSysViewer CI run `33923020037` matched `.github/workflows/CI.yaml` from `main`, kept
  the official `failure`, classified all seven jobs as `test`, and rendered them as three
  failure-signature groups.
- MolSysViewer Conda run `20548716947` selected `profile=conda`, reported the official
  success, and correctly used a `0/0` platform expectation for its noarch artifact.
- MolSysMT CI smoke run `32004333411` selected `profile=ci`, reported the official success,
  and classified its single job as `test`.

This closes only the bounded first CI slice. Configurable roles, required jobs,
documentation and release profiles, and embedded Action output remain later work.
