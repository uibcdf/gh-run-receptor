---
summary: Support Conda workflows with an action-internal platform matrix
issue: uibcdf/gh-run-receptor#35
status: resolved
opened: 2026-09-08
closed: 2026-09-12
verification: measured
area: ['profiles']
guard: tests/test_contracts.py
normative: data_contracts.md
blocked_by: []
supersedes: []
---

# Support Conda workflows with an action-internal platform matrix

**Reported:** 2026-09-08 while SMonitor used GH Run Receptor as the preferred first
inspection path for its 0.14.0 Conda publication.
**Status:** Resolved with a strict producer contract, hosted Linux/Windows evidence, and
deterministic sanitized replay. SMonitor tracks removal of its temporary integration
choice in `uibcdf/smonitor#10` after the contract is released.

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

The earlier partial increment covered safe discovery, normative profile choice, and client
fallback. The resolved increment adds a strict producer document and reserved artifact
path; it does not parse arbitrary action implementations or treat requested Action inputs
as outcomes.

## Acceptance criteria

- A sanitized fixture represents Python-matrix jobs with an action-internal native matrix
  and no per-platform package artifacts in GitHub.
- The report preserves GitHub's exact status and conclusion.
- Required but unobservable platforms are not described as observed failures or successes.
- The report makes the absence of platform and registry evidence explicit and bounded.
- Existing native-platform and noarch Conda profile fixtures retain their current truth
  semantics.
- Configuration and profile documentation explain when action-internal matrices require
  the new contract or a release/generic-profile fallback.
- Filename-only Conda discovery falls back to `generic`.
- Recognized action-internal platform inputs fall back to `generic` with no Conda settings.

## Resolution and hosted evidence

On 2026-09-12, the consumer side registered provisional `gh-run-receptor.events@1` as its
eighth contract, while retaining the seven 0.18.0/0.19.0 schemas byte-frozen. Metadata
capture discovers only artifacts beginning with the exact run- and attempt-qualified
prefix, checks their GitHub digest, validates one bounded JSON member, and persists its
exact bytes and artifact provenance in the replay bundle.

The Conda profile now combines GitHub-visible job/artifact evidence with producer package
events. Twelve successful package events spanning three Python versions and four hidden
platforms satisfy four explicit platform expectations without inventing GitHub artifacts.
A producer-reported failed upload makes an otherwise green GitHub run derive `FAIL`;
producer success cannot turn a GitHub non-success into `PASS`. Invalid or contradictory
matching events make the bundle `INCOMPLETE`.

The shared Conda Action now has an implementation that derives platform from each
actual output directory, hashes each package, records observed upload results, and exposes
an evidence path plus a reserved artifact name. Upload remains an explicit caller step so
retention and storage policy are visible. JSON path transport preserves Windows separators
and spaces; a local invocation supplies an explicit producer identity; and the ZIP member
uses the exact contract name `gh-run-receptor-events.json`.

Hosted run `34709939550` at producer commit
`236df788a4b3154765cf0cbeff87df9f4f698a80` passed on Ubuntu in 2 minutes 24 seconds and
Windows in 4 minutes 25 seconds. Each job built two Python variants for `linux-64`,
`osx-64`, `osx-arm64`, and `win-64`, verified its two host packages, validated eight
events, and uploaded one attempt-qualified artifact. GitHub independently reports
`conclusion=success`, attempt 1, two successful jobs, and artifacts of 934 and 936 bytes.
The evidence generation step completed within GitHub's one-second timestamp resolution;
artifact upload took one second per job.

Development gh-run-receptor consumed those artifacts through its normal network capture
path and reported:

```text
PASS conclusion=success | profile=conda | platforms=4/4 | producer_events=16 |
producer_uploads=not_requested:16 | jobs=2/2 | artifacts=2 |
uibcdf/action-build-and-upload-conda-packages run=34709939550
```

The complete metadata capture occupied 43,856 bytes. The reviewed fixture
`tests/fixtures/bundles/action_conda_internal_matrix_success` occupies 13,832 bytes and
retains the two producer documents, artifact IDs, GitHub digests, locally verified archive
digests, official source facts, and job/step state. It contains no logs or Conda packages.
Offline replay produces the same report.

The final local gate passes 356 tests, Ruff lint and format, developer-report lifecycle
validation, and compatibility validation with eight registered contracts, seven frozen
contracts, and the 0.19.0 baseline.

The hosted iterations were material to the result. Run `34685188510` exposed that
`conda convert` requires legacy package format 1; run `34685842325` exposed POSIX `shlex`
corruption of Windows paths; and green run `34709599504` was correctly downgraded to
`INCOMPLETE` because the ZIP member had a dynamic rather than contractual name. The
consumer validator was not weakened for any of these producer defects.

## Dependencies and risks

There is no external blocker. The remaining release task is freezing the provisional
contract in 0.20.0. External delivery remains outside this evidence boundary: a successful
producer upload event describes the observed upload command, not independent registry
verification. The implementation never infers outcomes from Action inputs or log wording.

## Provenance

Measured 2026-09-08 on Linux 7.0.0-28-generic x86_64 with Python 3.13.15 and
gh-run-receptor `0.18.0+21.g921f434`. Consumer run:
`https://github.com/uibcdf/smonitor/actions/runs/34278594890`. Consumer integration issue:
`uibcdf/smonitor#10`.

Resolved 2026-09-12 with producer runs `34685188510`, `34685842325`, `34709599504`, and
`34709939550`; the final public run is the source of the committed sanitized fixture.
