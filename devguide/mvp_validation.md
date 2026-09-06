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
explicit validation gap at that checkpoint; run `34027741137` closes it below.

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

## Outcome parity validation

The 0.9.0 increment adds four sanitized public attempts and raises the full local suite to
149 tests. MolSysMT run `33636046706` validates `CANCELLED`, exit status 2, two successful
Linux platforms, failed Windows, and cancelled Intel and Arm macOS platforms. PyUnitWizard
run `19058199598` validates that an HTTP 410 while requesting expired logs retains GitHub's
failure but yields receptor `INCOMPLETE` and exit status 4.

ArgDigest run `22638022385` supplies a paired rerun: attempt 1 is `failure`/`FAIL` with
exit status 1 and attempt 2 is `success`/`PASS` with exit status 0 at the same head SHA.
This evidence exposed a critical 0.8.0 defect in which historical jobs were combined with
the current run response. Capture and watch now request the attempt-specific run endpoint,
and replay rejects a retained run ID, attempt, or head SHA that contradicts its manifest.

## Standard job-timeout experiment

No `timed_out` workflow run was found across the active tool repositories or 22 additional
public UIBCDF repositories inspected on 2026-09-06. A minimal manual workflow at commit
`a87e5b9` then ran one inert Ubuntu job with `timeout-minutes: 1`. GitHub run
`34027741137` completed as `cancelled`; its job and interrupted wait step were also
`cancelled`. The receptor returned `CANCELLED` and exit status 2 from a complete 20,380-byte
metadata bundle.

The same run supplied the first live active-watch observation. During approximately one
minute of execution, watch emitted one initial `in_progress` state and no unchanged
snapshots. At completion it emitted the job transition, run transition, and one final
report. The simulated-clock contract therefore agrees with observed remote behavior.

This refutes the assumption that standard Actions job timeout generates the API's
`timed_out` conclusion. GitHub documents the setting as automatic cancellation. The
temporary manual workflow was therefore removed rather than retained as a redundant
cancelled generator. `TIMED_OUT` remains truth-table tested but not real-run validated.

## Acquisition-failure validation

The 0.10.0 increment measures missing GitHub CLI authentication, invalid credentials
(HTTP 401), insufficient Actions-policy permission (HTTP 403), and an unavailable run
(HTTP 404). Source-tree CLI probes returned exit status 5 with respectively
`authentication_required`, `authentication_failed`, and `not_found_or_inaccessible`;
the real 403 transport text is covered through the same classifier boundary.

Unit tests additionally validate HTTP/rate-limit precedence, conservative generic
fallback, structured optional-404 handling, bounded diagnostics, GitHub-token and
authorization redaction, and visible terminal/bidirectional controls. No credential value
was printed, stored, or committed. Automatic authentication, scope changes, and retries
remain outside the product.

## What this proves

- Complete remote evidence can be acquired without entering the language-model output
  channel.
- Structured GitHub metadata alone already yields useful, low-token triage reports for
  the measured Conda, CI, documentation, and npm workflow shapes.
- Human and LLM presentations can differ without disagreeing on facts or exit status.
- A captured run can be replayed without network access from an installed wheel.

## Cross-platform package validation

Manual run `34037657805` at commit `44562d5` passed all nine combinations of
GitHub-hosted Ubuntu, macOS, and Windows with Python 3.11, 3.12, and 3.13. Every job ran
the complete 163-test suite with `--receptor=llm`, built exactly one wheel and one source
distribution, installed the wheel, and invoked the installed `gh-run-receptor` command
outside the checkout. The derived version was `0.10.0+4.g44562d5`, not `0+unknown`.

The first run, `34037154711`, passed Ubuntu and macOS but exposed CRLF conversion of
byte-exact JSON fixtures on Windows. The loader correctly rejected the altered byte
counts. Declaring LF checkout for `tests/fixtures/**` fixed transport without weakening
bundle validation; the second run then passed 9/9. Job durations ranged from 15 to 45
seconds.

## Client adoption validation

The canonical 0.13.0 guide is synchronized byte-identically to eleven client repositories:
MolSysMT, MolSysViewer, PyUnitWizard, SMonitor, ArgDigest, DepDigest, ElastNetMT, TopoMT,
PharmacophoreMT, pytest-receptor, and the Conda build Action. The eight configured
Python clients declare 37 exact workflow-path rules. Every configuration passes the strict
`config check`; Conda expectations come from explicit platform flags in each workflow,
not from filename inference.

Metadata-only remote smokes against one retained run from each newly configured client
loaded policy from the default branch and preserved all eight GitHub conclusions: five
`PASS` and three `FAIL`. The GitHub-generated `pages-build-deployment` workflow in
ArgDigest correctly remained `generic` because it is not the configured source workflow.
No logs were needed for this adoption check.

## Embedded Action offline validation

The first composite Action uses the same capture and report service as the external CLI.
Offline tests verify pinned Action dependencies, validated inputs, completed success and
failure, honest `PENDING` state for the current run, fail-open reporter errors, strict-mode
step behavior, escaped summaries, scalar outputs, bounded report size, and publisher
provenance. A manual three-operating-system workflow is committed but has not yet supplied
live evidence.

Checkout-local run `34043552961` then passed Ubuntu, macOS, and Windows. It covered script
extension installation, completed `PASS`, current-run `PENDING`, and a Linux completed
`FAIL` source without reporter failure. Seven reports were 1,559--2,009 bytes and Action
steps took 3--9 seconds at GitHub's one-second timing resolution. Distributed-source run
`34043774335` independently passed 3/3 after downloading the Action by full commit SHA and
verified exact publisher repository/ref provenance.

The post-tag distribution workflow resolves `uibcdf/gh-run-receptor@0.12.0` directly and
requires the embedded report to retain `publisher.ref: 0.12.0` on every operating system.

Manual tagged-source run `34045930131` passed 3/3 and triggered the separate read-only
`workflow_run` reporter `34045953527`. That downstream run inspected the completed source
ID rather than itself, verified exact conclusion parity and receptor `PASS`, completed in
8 seconds, and uploaded a 1,449-byte canonical report. It performed no checkout or source
artifact execution.

## Published report consumption

The explicit `published` command consumed reporter run `34045953527`, verified its
1,449-byte artifact digest and bounded ZIP, then matched source repository, run
`34045930131`, attempt, SHA, terminal status, conclusion, and URL against fresh GitHub
metadata. It fetched no source jobs or logs and marked profile interpretation as published,
not independently recomputed.

Against a fresh metadata capture of the same successful source, the command reduced API
requests from seven to four (42.9%), transferred bytes from 36,735 to 26,653 (27.4%), and
elapsed time from 4.04 to 2.63 seconds (34.9%); peak RSS was effectively unchanged. Manual
extension run `34047166101` passed the same command on Ubuntu, macOS, and Windows, with the
consumption step taking 2--3 seconds in every job.

The 0.13.0 wheel installed outside the checkout and the GitHub CLI extension cloned into an
isolated data directory both reported exact version `0.13.0` and consumed the retained live
artifact successfully. The release artifacts are a 53 KiB wheel and 72 KiB source archive.

## What this does not prove

- Log analysis currently recognizes a deliberately small generic signature set and is not
  yet a complete diagnosis engine.
- The committed real-run corpus remains narrow; timed-out, restricted-token,
  active-transition, and real Zenodo cases remain gaps.
- Restricted-token and fork behavior of the embedded Action are not yet validated.
- External registries, GitHub Releases, Git refs, and archive records are not queried by
  the first release profile.
