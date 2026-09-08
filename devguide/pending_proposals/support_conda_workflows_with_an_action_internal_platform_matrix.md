---
summary: Support Conda workflows with an action-internal platform matrix
issue: uibcdf/gh-run-receptor#35
status: partial
opened: 2026-09-08
closed:
verification: measured
area: ['profiles']
guard:
normative:
blocked_by: []
supersedes: []
---

# Support Conda workflows with an action-internal platform matrix

**Reported:** 2026-09-08 while SMonitor used GH Run Receptor as the preferred first
inspection path for its 0.14.0 Conda publication.
**Status:** Safe discovery and client guidance are delivered; structured hidden-matrix
evidence remains open. SMonitor tracks the temporary integration change in
`uibcdf/smonitor#10`.

## What

Represent a Conda workflow whose GitHub-visible matrix is not its package-platform matrix.
SMonitor run `34278594890` has three successful jobs keyed by Python 3.11, 3.12, and 3.13.
Each job invokes `uibcdf/action-build-and-upload-conda-packages`, which builds and uploads
Linux, Intel macOS, Apple Silicon macOS, and Windows packages internally. GitHub exposes
no platform-named jobs or artifacts for the receptor to associate with those platforms.

The repository configuration is structurally valid and declares those four
`expected_platforms`. Inspection therefore reports all four as missing and changes the
derived assessment from `PASS` to `FAIL`, while retaining GitHub's authoritative
`conclusion=success`.

## How

Add an explicit, truth-preserving way to describe an action-internal platform matrix. The
contract must distinguish three facts:

1. the GitHub jobs and steps succeeded;
2. GitHub run evidence does not expose one job or artifact per native platform;
3. external registry evidence may independently prove which distributions were published.

The receptor must not invent platform successes from action inputs. A configuration that
declares hidden platform work could instead report platform coverage as not observed and
derive `INCOMPLETE` when platform coverage is required. The exact setting name and whether
structured producer evidence should be admitted remain design questions.

Until that contract exists, SMonitor maps this release-triggered workflow to the `release`
profile. That profile reports the package steps and explicitly retains
`registry=not_observed`; Anaconda remains a separate release gate.

The immediate discovery defense is repository-neutral: a Conda-looking filename without
source evidence no longer selects `conda`, and recognized action-internal platform inputs
fall back to `generic`. A reviewed client rule may select `release` for the visible
publication orchestration. The canonical guide now makes this evidence-topology decision
explicit. Full support still requires a versioned producer event or another structured
source tying every platform, Python version, artifact, validation result, and upload
result to the source run.

## Why

Action-composed publishing is used to avoid duplicating platform build machinery in every
consumer. Treating invisible platform dimensions as failed dimensions makes a successful
release look failed and discourages routine receptor use. Removing `expected_platforms`
under the current Conda profile is also insufficient: it would make the report pass
without explaining that zero platform evidence was observed.

## What is measured and what is assumed

Measured with development commit `921f434` and metadata-only capture:

```text
./gh-run-receptor --repo uibcdf/smonitor --receptor llm \
  inspect 34278594890 --capture metadata
FAIL conclusion=success status=completed | ... | profile=conda
workflow: .github/workflows/build_and_upload_conda_packages.yaml | jobs: 3 (success=3)
conda platforms: successful=0 failed=0 missing=4 artifacts=0 observed=0
missing expected: linux-64, osx-64, osx-arm64, win-64
```

The command exited 1. Native `gh run view` reported `completed`/`success`, exact head SHA
`59bf831cd21cb0608e6f56a3f6d00135f35e2951`, and three successful jobs. The public
Anaconda release endpoint returned 12 SMonitor 0.14.0 distributions: Python 3.11--3.13 on
each of `linux-64`, `osx-64`, `osx-arm64`, and `win-64`.

An explicit `--profile release` inspection exited 0 and reported:

```text
PASS conclusion=success | release | event=release | ref=0.14.0 |
sha=59bf831cd21cb0608e6f56a3f6d00135f35e2951 | tag=unverified |
phases=package:3,other:3 | registry=not_observed | archive=not_observed | artifacts=0
```

The proposal assumes this workflow shape is relevant beyond SMonitor; the existing shared
publishing action makes that likely, but a suite-wide count has not yet been measured.

## What was refuted

- The source workflow did not fail: GitHub reports success for the run, all three jobs, and
  every `Build and upload the conda packages` step.
- The packages were not merely attempted: the external Anaconda API lists all 12 expected
  distributions under label `main`.
- Removing `expected_platforms` while retaining the Conda profile would avoid the derived
  failure, but would silently reduce the platform contract to zero observed platforms.
- Parsing action inputs as proof of output was rejected. Requested platforms do not prove
  that packages were built or uploaded.
- Hard-coding the UIBCDF action identity in discovery was rejected because profile
  selection must remain portable to non-MolSysSuite repositories.

## Scope and exclusions

This proposal does not add Anaconda authentication, mutate a workflow, or make the
receptor sole release authority. It does not change the existing behavior for workflows
that expose platform-named jobs or GitHub artifacts. External registry verification and
structured evidence emitted by the publishing action may be related future work, but are
not assumed to be available here.

The delivered partial increment covers safe discovery, normative profile choice, and
client fallback. It does not parse arbitrary action implementations or represent hidden
platform outcomes.

## Acceptance criteria

- A sanitized fixture represents Python-matrix jobs with an action-internal native matrix
  and no GitHub artifacts.
- The report preserves GitHub's exact status and conclusion.
- Required but unobservable platforms are not described as observed failures or successes.
- The report makes the absence of platform and registry evidence explicit and bounded.
- Existing native-platform and noarch Conda profile fixtures retain their current truth
  semantics.
- Configuration and profile documentation explain when action-internal matrices require
  the new contract or a release/generic-profile fallback.
- Filename-only Conda discovery falls back to `generic`.
- Recognized action-internal platform inputs fall back to `generic` with no Conda settings.

## Dependencies and risks

There is no external blocker. The main design risk is weakening a required expectation
until a green GitHub conclusion becomes a false package-publication claim. Any design must
keep external delivery outside the inferred evidence boundary. Full semantic support
depends on a producer evidence contract and must not infer outcomes from action inputs or
log wording.

## Provenance

Measured 2026-09-08 on Linux 7.0.0-28-generic x86_64 with Python 3.13.15 and
gh-run-receptor `0.18.0+21.g921f434`. Consumer run:
`https://github.com/uibcdf/smonitor/actions/runs/34278594890`. Consumer integration issue:
`uibcdf/smonitor#10`.
