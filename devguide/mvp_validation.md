# MVP validation checkpoint

## Scope under test

Version `0.1.1` is the first tagged source MVP. It is not the complete Phase 1 contract.
This checkpoint records what has actually run, separately from planned behavior.

## Local validation

On 2026-09-04, the implementation passed:

```text
ruff check .
pytest --receptor=llm
```

The suite initially contained 20 deterministic tests covering report truth, outcome exit codes,
human/LLM selection, TTY inference, JSON output, URL parsing, pagination merging, bundle
digests, traversal rejection, capture-policy cache separation, and terminal-control
escaping.

The first causal-analysis and Conda increment raised this to 26 tests. CLI ergonomics,
successful-run compression, and incomplete-evidence semantics subsequently raised the
suite to 28 tests. Transition-only monitoring subsequently raised it to 33 tests. The
added cases
cover cross-job cause normalization, bounded huge-line handling, malicious ZIP traversal,
Conda partial-success semantics, reusable artifacts, conservative profile detection, and
bundle-to-report cause integration.

The watch tests use scripted API snapshots and an injected clock. They establish that
unchanged snapshots produce no output, polling backs off, a state change resets the delay,
transient failures are bounded, untrusted names are escaped, and completed runs do not emit
a redundant transition. Three consecutive acquisition failures terminate the watch instead
of retrying forever. A live completed Conda run produced only its one-line final
report. No active UIBCDF run was available, so live transition behavior is still an
explicit validation gap.

A `0.1.1` wheel was built without dependency download, installed into a fresh temporary
virtual environment, and invoked through its installed console entry point. The wheel
included the MIT license and the complete `gh_run_receptor` package.

## MolSysMT proof of concept

The installed wheel inspected `uibcdf/molsysmt` run `33863426589`, attempt 1, workflow
`.github/workflows/test_conda_rattler.yaml`.

The generic report preserved GitHub's `failure` conclusion and identified:

- six jobs: four successful and two failed;
- failing `osx-64` and `osx-arm64` jobs;
- the failed artifact-inspection/installation-test step in each job;
- three retained Linux, Linux AArch64, and Windows artifacts;
- durations and the canonical GitHub run URL.

The LLM projection used seven lines. The human projection listed all six jobs and their
artifact sizes. Both returned exit status 1 and were derived from the same report.

An adaptive capture downloaded the complete run-log archive to disk without printing it.
The bundle was complete and contained 425,372 bytes of structured and log evidence; the
log archive itself was 362,561 bytes. These values come from the captured manifest and
must be regenerated rather than hand-maintained in future benchmark reports.

After bounded log analysis and the first Conda profile were added, replay classified the
same run as `PARTIAL` while retaining `conclusion=failure` and exit status 1. It identified
three reusable platforms (`linux-64`, `linux-aarch64`, and `win-64`), two failed macOS
platforms, and one cause shared by both failures:

```text
$RUNNER_TEMP/script: line 2: mapfile: command not found
```

The report points to line 4157 of the `osx-64` member as its deterministic displayed
sample and retains both occurrences in JSON.

Run `33849332945` provided the first complete-success counterexample. All six jobs and all
five Conda platforms succeeded, while no GitHub artifact remained available. The report
therefore states platform success and `artifacts=0` without claiming reusable artifacts.
Its LLM projection is one line; human and JSON projections retain all jobs.

Against a native verification baseline that also included jobs and artifact inventory,
the one-line report reduced input by 72.2% to 73.1% across the measured tokenizers. A
minimal native status-only query remained smaller than the richer receptor report; this
negative boundary is documented alongside the benchmark rather than hidden.

MolSysViewer run `20548716947` validates the explicit noarch branch introduced in 0.5.0.
The trusted default-branch rule selects `package_kind: noarch`; the report preserves all
three successful jobs, replaces `platforms=0/0` with `package=noarch`, and describes the
empty complete GitHub artifact inventory as `not_observed`. A reviewed sanitized fixture
preserves the run, job, configuration, and configuration-provenance fields needed to replay
that interpretation offline. Against an equivalent filtered run/jobs plus artifact query,
the compact line reduced `cl100k_base` input from 101 to 45 tokens (55.4%).

The measured comparison with a locally filtered native baseline is recorded in
[benchmark_2026-09-04.md](benchmark_2026-09-04.md). The pilot reduced reader input by
93.9% to 94.7% across four tokenizers, while the unfiltered native failed log remained on
disk rather than entering the reader channel.

## Later profile validation

The 0.4.0 through 0.7.0 increments expanded the committed corpus and local suite to 119
tests. A failing seven-job MolSysViewer run validates CI role assignment and repeated
failed-step grouping. Successful and failing documentation fixtures validate skipped
notebooks, diagnostic artifacts, and indivisible Sphinx/Pages evidence. Successful and
failing MolSysViewer npm fixtures validate observed event/ref/SHA identity, separate
package/publication phases, and explicit absence of external registry, tag, or archive
verification.

The accepted npm release projections reduced `cl100k_base` input from 95 to 84 tokens for
success and from 103 to 93 for failure. Two earlier release renderers were rejected
because they exceeded the corresponding competent native baselines. No real run of the
new Zenodo verification workflows exists yet, so archive-role behavior is unit-tested but
not real-run validated.

## Workflow discovery validation

The first `init` slice raised the local suite to 130 tests. Preview runs against the client
checkouts discovered all 15 immediate MolSysMT workflows and all 8 immediate MolSysViewer
workflows. Every existing manually reviewed profile assignment was reproduced; MolSysMT's
previously unconfigured `benchmarks.yml` was conservatively proposed as `ci`. Nested
MolSysMT backup workflows were not discovered. The MolSysViewer noarch package setting was
recovered from explicit workflow text.

Both generated documents passed `config check`. On this Linux host with Python 3.13.14,
single preview runs took 0.11 seconds. The MolSysMT proposal was 1,213 bytes with peak RSS
23,632 KiB; MolSysViewer was 703 bytes with peak RSS 23,432 KiB. These are local case
measurements, not performance guarantees. Discovery deliberately did not reproduce the
five required staging platforms because static mention is not evidence that a platform is
a required gate.

## What this proves

- Complete remote evidence can be acquired without entering the language-model output
  channel.
- Structured GitHub metadata alone already yields useful, low-token triage reports for
  the measured Conda, CI, documentation, and npm workflow shapes.
- Human and LLM presentations can differ without disagreeing on facts or exit status.
- A captured run can be replayed without network access from an installed wheel.

## What this does not prove

- Log analysis currently recognizes a deliberately small generic signature set and is not
  yet a complete diagnosis engine.
- The committed real-run corpus remains narrow; cancelled, timed-out, incomplete,
  restricted-token, active-transition, rerun-attempt, and real Zenodo cases remain gaps.
- No cross-platform installation support claim follows from local Linux validation.
- External registries, GitHub Releases, Git refs, and archive records are not queried by
  the first release profile.
