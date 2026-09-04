# MVP validation checkpoint

## Scope under test

Version `0.1.0a1` is an unreleased source-tree MVP. It is not the complete Phase 1
contract. This checkpoint records what has actually run, separately from planned behavior.

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
suite to 28 tests. The added cases
cover cross-job cause normalization, bounded huge-line handling, malicious ZIP traversal,
Conda partial-success semantics, reusable artifacts, conservative profile detection, and
bundle-to-report cause integration.

A `0.1.0a1` wheel was built without dependency download, installed into a fresh temporary
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

The measured comparison with a locally filtered native baseline is recorded in
[benchmark_2026-09-04.md](benchmark_2026-09-04.md). The pilot reduced reader input by
93.9% to 94.7% across four tokenizers, while the unfiltered native failed log remained on
disk rather than entering the reader channel.

## What this proves

- Complete remote evidence can be acquired without entering the language-model output
  channel.
- Structured GitHub metadata alone already yields a useful, low-token triage report for
  the Conda workflow.
- Human and LLM presentations can differ without disagreeing on facts or exit status.
- A captured run can be replayed without network access from an installed wheel.

## What this does not prove

- No formal token-reduction percentage has been measured against the competent native
  baseline yet.
- Log analysis currently recognizes a deliberately small generic signature set and is not
  yet a complete diagnosis engine.
- Only one real MolSysMT workflow has been checked; no platform support claim follows.
- The live capture is private temporary evidence, not a reviewed committed fixture.
- Full schema, malformed-API, archive-limit, active-run, rerun-attempt, and restricted-token
  cases remain Phase 0 and Phase 1 work.
