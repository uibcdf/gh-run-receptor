---
summary: Add the first release workflow profile
issue: uibcdf/gh-run-receptor#9
status: resolved
opened: 2026-09-05
closed: 2026-09-05
verification: measured
area: ['profiles', 'tests']
guard: tests/test_contracts.py
normative:
blocked_by: []
supersedes: []
---

# Adding the first release workflow profile

**Reported:** 2026-09-05, after closing the first documentation-profile slice.
**Status:** Resolved in 0.7.0 and validated from MolSysViewer's default-branch rules.

## What

Add `release` as a truth-preserving profile for release identity, package construction,
publication, archive/citation verification, validation gates, artifacts, setup, and
unknown work. Validate the first slice against one successful and one failing public
MolSysViewer npm workflow with retained step metadata.

## How

Preserve the observed GitHub event and head ref alongside the existing exact head SHA.
These are source facts, but neither a `push` event nor a ref-shaped string is independently
verified Git tag evidence. The report therefore exposes `tag_verified: false` until a
future capture source checks Git refs or release metadata directly.

Assign every retained step exactly once. A unit may carry one bounded phase from
`identity`, `gate`, `package`, `publish`, `archive`, `artifact`, `setup`, or `other`; a
step matching several material phases remains one combined evidence unit rather than
being counted as independent successes. JSON retains all source steps and evidence
references.

A successful publication step means only that GitHub recorded that step as successful.
The initial profile reports external registry and archive evidence as `not_observed`
unless a dedicated verification step exists, and even then distinguishes workflow-step
verification from a receptor-side registry query. Official GitHub conclusion and exit
status remain authoritative.

## Why

Release workflows are high-impact and may contain long dependency installation and build
output. A compact diagnostic needs to identify whether work stopped before packaging, at
publication, or during archive verification without turning a tag, missing error text, or
successful workflow step into stronger evidence than GitHub supplied.

## What is measured and what is assumed

`gh run list --repo uibcdf/molsysviewer --workflow npm-publish.yaml --limit 20 --json ...`
found recent complete cases with retained steps:

- run `30998524379`: official `success`, `workflow_dispatch`, successful runtime build and
  successful `Publish to npm` step;
- run `31278635513`: official `failure`, `push`, observed head ref `0.20.1`, failed runtime
  build, and skipped `Publish to npm` step.

`gh run list` found no runs yet for either repository's new
`verify-zenodo-release.yaml`; archive classification will therefore be unit-tested but
will not be claimed as real-run validated in this slice.

The native baseline combines `gh run view` fields
`status,conclusion,event,headBranch,headSha,name,url,jobs` with the run artifact inventory,
retaining every identity field and every release-material step. With tiktoken 0.13.0
`cl100k_base`:

| Case | Native baseline | Accepted receptor | Reduction |
| --- | ---: | ---: | ---: |
| Successful npm workflow | 95 tokens | 84 tokens | 11.6% |
| Failed build, skipped npm publication | 103 tokens | 93 tokens | 9.7% |

The accepted failure report adds explicit unverified-tag and absent-external-evidence
semantics while remaining shorter than the native projection.

## What was refuted

- Treating `head_branch=0.20.1` as a verified tag is rejected: the captured run record
  exposes an observed ref-like value, not an independently checked Git ref.
- Treating a successful `Publish to npm` step as registry verification is rejected:
  step conclusion proves workflow execution, not current registry state.
- Counting a composite `Build, test, and publish` step in three independent phases is
  rejected because one conclusion cannot prove separable reusable results.
- Starting with Zenodo is rejected for this slice because neither client has a real run
  of its new verification workflow yet.
- The first renderer is rejected because it used 101 tokens for the 95-token success
  baseline and 151 tokens for the 103-token failure baseline. It repeated identity, job,
  phase, and verification facts.
- The second renderer is rejected because its failed projection still used 116 tokens;
  it repeated the failed build as both an exact step and a phase and retained irrelevant
  post-setup state. The accepted renderer keeps those facts once in text and all source
  structure in JSON.

## Scope and exclusions

This slice does not query npm, Anaconda, GitHub Releases, Zenodo, or Git refs; download or
inspect package artifacts; verify package digests; correlate several workflows into one
release; enforce a required gate list; or implement release mutation. Conda publication
continues to use the Conda profile rather than being silently reinterpreted as release.

## Acceptance criteria

- `release` is accepted by CLI, schema, and trusted exact repository rules.
- Event, observed head ref, and exact head SHA survive normalization and JSON rendering.
- Every step appears in exactly one simple or combined release evidence unit.
- Successful package plus failed or skipped publication may derive `PARTIAL` only when
  those are separate source units; official failure and exit code remain unchanged.
- A failed package with skipped publication remains `FAIL`.
- Registry/archive verification strength is explicit and never inferred from absence.
- Successful and failing real npm fixtures cross bundle, model, report, deterministic
  replay, configuration-selection, and conclusion-parity gates.
- Each measured LLM report is shorter than a competent filtered native baseline.

## Dependencies and risks

No tracked dependency blocks the npm slice. Real Zenodo validation depends on a future
published release run but does not block this bounded profile.

## Delivered checkpoint

Commit `c901166` and tag `0.7.0` delivered the release profile, the additive event/ref
identity fields, two real npm fixtures, and the measured compact renderer. MolSysMT
adopted its Zenodo-verification rule in `aee6f904f`; MolSysViewer adopted npm and Zenodo
rules in `ce3eb6a9`. Conda publication deliberately remains under the Conda profile.

After client adoption, both npm runs were captured again without a CLI profile override.
Their reviewed sanitized fixtures retain MolSysViewer's default-branch policy and select
`release` automatically. The final local gate passed 119 tests, Ruff, developer-report
validation, and diff safety. The real cases retain exact official conclusion parity and
the measured 95→84 and 103→93 token reductions.

## Provenance

Initial inspection was performed on 2026-09-05 from the local Linux development host
with Python 3.13, GitHub CLI 2.93.0, `gh-run-receptor` 0.6.1, and tiktoken 0.13.0.
Final client-policy capture used the released `gh-run-receptor` 0.7.0 extension.
