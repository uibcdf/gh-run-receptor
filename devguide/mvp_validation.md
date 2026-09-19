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

On 2026-09-19 a broader authenticated scan queried 889 deduplicated public repositories
from ten popularity, language, Actions-topic, and organization cohorts. Every request to
the workflow-runs endpoint succeeded and every `status=timed_out` result had
`total_count=0`. This does not establish global absence, but it strengthens the evidence
that opportunistic read-only capture is a more honest policy than manufacturing a check
or retaining an ineffective timeout generator.

## Stable watch contract

Issue `uibcdf/gh-run-receptor#42` turns that first observation into a stable measured
contract. Active validation run `35432811964` completed successfully with one job. Native
`gh run watch --compact` emitted 38 lines and 321 `cl100k_base` tokens; the receptor emitted
four lines and 86 tokens, a 73.2% reader-input reduction with matching terminal truth.

The receptor made nine instrumented `gh api` invocations: two one-page snapshots and five
fresh final-evidence calls. A completed successful run made seven after terminal handoff,
versus nine before the change. Unit tests count pages, attempts and successful snapshots;
cover deterministic unchanged, transition and failure backoff; reject non-finite
intervals; and reject conflicting run, attempt, or job handoff identity. The complete
formula and the negative completed-status token boundary are recorded in
[benchmark_watch_2026-09-19.md](benchmark_watch_2026-09-19.md).

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

The canonical 0.14.0 guide is synchronized byte-identically to eleven client repositories:
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

The 0.14.0 synchronization teaches every client the canonical reporter filename,
attempt-qualified artifact identity, source-first command, explicit fallback, and remaining
fork/restricted-token boundary. Each repository received only the guide in a `[skip ci]`
commit after exact-copy validation; TopoMT's pre-existing untracked smoke notebook was left
untouched.

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

The 0.13.1 wheel independently installed outside the checkout, reported exact version
`0.13.1`, and exposed both trust fields in live compact output. Its canonical guide is
synchronized to every tracked consumer.

## Source-first report discovery

Release 0.14.0 makes every Action artifact attempt-qualified. Distributed Action run
`34050056151` passed 3/3 on Ubuntu, macOS, and Windows and triggered canonical
`.github/workflows/gh-run-receptor-report.yml` run `34050080872`. The reporter published
exactly one 1,489-byte artifact named `gh-run-receptor-report-34050056151-1`, with artifact
ID `9994266757` and GitHub SHA-256 digest
`26764d1ebe94135e1b621a73c1f49f342581710b501195b8b72b98fcac465e0a`.

Starting only from source ID `34050056151`, `published-source` recovered the reporter,
verified its `workflow_run` event, workflow ID, run path, workflow path, artifact producer
identity, digest, and fresh source facts, then rendered `PASS` with
`reporter_identity=verified`. Hosted extension run `34050112408` passed both explicit
historical consumption and this source-first route on Ubuntu, macOS, and Windows.

An isolated wheel built from exact tag `0.14.0` reported that version and consumed the same
live report successfully. The wheel measured 55 KiB and the source distribution 75 KiB.

## Inline Action rules and permission boundaries

The post-0.14 implementation accepts a complete `config@1` document from an Action input
only when GitHub caller context proves a same-repository workflow on the default branch.
The full local suite reached 235 tests before hosted workflows were added; isolated wheel
and source-distribution construction, Ruff lint and format, and developer-report validation
also passed.

Public-repository permission run `34062840512` passed three exact jobs. The canonical case
used `actions: read` and `contents: read`; independently removing either declared scope
still allowed this public source run to be reported. This is evidence about public access,
not a private-repository or fork permission claim.

Temporary same-repository PR `uibcdf/gh-run-receptor#24` triggered run `34063608569`, which
verified that pull-request inline configuration returns `untrusted_inline_rules`, produces
no report, and does not reach acquisition. The PR was closed without merge and its marker
never entered `main`.

Distributed source run `34064088835` passed 3/3 and triggered canonical reporter run
`34064107455`. The reporter selected `ci` through its inline rule, retained default-branch
workflow path/ref/event/digest provenance, and passed exact terminal-source checks.
Starting only from the source ID, `published-source` then verified both source facts and
reporter identity.

Exact lightweight tag `0.15.0` points to commit `bee7a76`. An isolated tagged build
produced `gh_run_receptor-0.15.0-py3-none-any.whl` and the matching source distribution;
a clean virtual environment installed the wheel without dependencies and reported version
`0.15.0` through the console command. Post-tag distributed Action run `34065271843` passed
on Ubuntu, macOS, and Windows and triggered canonical inline reporter run `34065293853`.
Source-first consumption again verified the CI profile, source facts, and reporter identity.

The 0.15.0 canonical guide was then synchronized byte-identically to all eleven tracked
clients in focused `[skip ci]` commits. It documents inline configuration, ready/error
outputs, the default-branch trust boundary, and the deliberately narrower private/fork
claim.

## Minimum GitHub CLI validation

GitHub CLI 2.48.0 is the first release containing the required
`gh api --paginate --slurp` interface. The receptor now checks the stable version line once
per remote client and rejects older or unrecognizable versions with
`unsupported_gh_cli` before any API command. Missing executables remain a distinct
acquisition failure, and offline operations do not perform the check.

Hosted run `34066699901` downloaded the official Linux amd64 2.48.0 archive, verified
SHA-256 `1c477e2562aca8679b0219569f0482f1975de76daca8ba307892c1787338a28d`, installed the
checkout as an extension under that binary, and inspected public compatibility run
`34037657805` through a real metadata capture. The resulting report retained GitHub
`success` and receptor `PASS`. This establishes a functional transport floor, not a
recommendation to prefer an old CLI over the latest patched stable release.

Exact lightweight tag `0.16.0` points to commit `2a4570a`. An isolated tagged build
produced `gh_run_receptor-0.16.0-py3-none-any.whl` and the matching source distribution;
an isolated wheel installation reported exactly `0.16.0`. Hosted run `34067180540` then
installed that remote tag using the checksum-pinned GitHub CLI 2.48.0 binary and completed
a real metadata inspection with `PASS`/`success`. Distributed Action run `34067181837`
passed 3/3 on Ubuntu, macOS, and Windows and triggered canonical reporter run
`34067199652`. Source-first consumption verified the terminal source facts, published
interpretation, and reporter identity. The 0.16.0 guide was subsequently synchronized
byte-identically to all eleven tracked clients in focused `[skip ci]` commits.

## First public GitHub Release

Tag `0.17.0` points to commit `aa9cba3`. Hosted publication run `34101051525` validated
tag/ref/commit identity, citation metadata, all 265 tests, exact-version installation,
checksums, and release notes. It created draft release `383936348` with the expected wheel,
source distribution, and checksum manifest, then failed closed because the public
release-by-tag endpoint does not expose drafts.

The retained draft assets were downloaded and passed the repository verifier against the
draft API record, tag ref, local sizes, manifest, and GitHub-reported SHA-256 digests. Only
then was the draft published at `https://github.com/uibcdf/gh-run-receptor/releases/tag/0.17.0`;
the same verification passed again through the public tag endpoint. The corrected workflow
resolves a draft database ID through authenticated `gh release view` before reading its API
record. That correction still requires a fresh exact-tag hosted exercise.

An anonymous Zenodo records query for exact title `gh-run-receptor` returned zero records
after publication. This is real negative evidence at the query time, not proof that the
repository integration is disabled: Zenodo documents asynchronous processing and the
account enablement state is not visible through GitHub. No DOI or archival success is
claimed.

Tag `0.18.0` points to commit `1a95305`. Hosted run `34102195605` completed the corrected
path without intervention: exact tag identity, citation, 265 tests, build, installed
version, checksums, notes, authenticated draft lookup, draft verification, publication,
and public verification all passed. Public release `383944270` contains exactly the 57,332
byte wheel, 83,003 byte source distribution, and 202 byte checksum manifest, each uploaded
with a GitHub SHA-256 digest matching downloaded bytes. A fresh external download passed
the same verifier and installed as exactly 0.18.0.

Minimum GitHub CLI run `34102327634` passed through the exact 0.18.0 extension. Distributed
Action run `34102330094` passed 3/3 on Ubuntu, macOS, and Windows and triggered canonical
reporter run `34102367041`; source-first consumption verified source facts, published
interpretation, and reporter identity. The 0.18.0 guide was then synchronized
byte-identically to all eleven tracked clients.

## Run and rerun comparison

The first comparison slice uses the two retained attempts of ArgDigest run
`22638022385` as a paired real-world guard. Offline replay and a fresh live capture both
retain repository, workflow, run, attempt, and SHA independently. They report attempt 1
as `failure`/`FAIL`, attempt 2 as `success`/`PASS`, `same_run=true`, and
`same_head_sha=true`; known job duration changes from 40 to 79 seconds.

The versioned `comparison@1` contract also covers deterministic repeated job names,
different-commit warnings, incomplete required dimensions, capture-time artifact
semantics, comparable matrix units, and bounded human/LLM rendering. A clean wheel install
ran the offline command outside the checkout. Manual read-only hosted run `34167676919`
then reacquired both public attempts at commit `551005d` and passed every exact identity
and transition assertion.

This proves descriptive comparison, not causal performance regression analysis. A changed
duration or artifact inventory remains a measured delta until a caller supplies an
explicit policy.

## Explicit comparison policy

The strict, versioned `comparison-policy@1` contract lets a caller classify a candidate
without changing the descriptive comparison facts. Opt-in rules cover source identity,
candidate conclusion, absolute and percentage job-duration increases, artifact-size
increases, removed jobs or artifacts, and removed or changed matrix units. Missing
evidence produces `INCOMPLETE`/exit 4 rather than a false pass; a measured violation
produces `FAIL`/exit 1.

The ArgDigest paired-attempt fixture exercises a known 40-to-79-second job-duration
increase. A clean wheel installed outside the checkout returned `PASS`/exit 0 at a
39-second threshold and returned one exact `max_job_duration_increase_seconds` violation
at a 30-second threshold. Manual hosted run `34213219459` repeated both assertions against
the live public attempts and passed at implementation commit `d98fc2f`.

This establishes deterministic, user-selected regression policy over current evidence.
It does not infer causal regressions, learn historical baselines, or choose project
thresholds automatically.

## Reusable terminal reporter

The call-only `reusable-report.yml` forwards typed report policy to the composite Action
and returns eight durable workflow outputs. It omits the runner-local report path and uses
GitHub's `$/` self-repository reference so the Action resolves from the exact same commit
as the called workflow without a source checkout.

Manual remote caller run `34168584873` passed the report and verify jobs, published the
expected `gh-run-receptor-reusable-34037657805-1` artifact, and exposed terminal
`success`/`PASS` with the CI profile. The downloaded report identified publisher ref
`67fb3b11b90269872b1b3055b1325d6bc0d486d6`, exactly the called implementation commit.

The permanent gate then downloaded its own called-job artifact and asserted
`publisher.ref == github.sha`. Run `34201435368` passed both jobs at commit `d71fe6d`.
This proves the reusable distribution path and same-revision invariant on github.com; it
does not claim `$/` support on older GitHub Enterprise Server runners.

## Release 0.19.0

Tag `0.19.0` points to commit `6cda3c71fb5c6174c2b699cac5e5cb0015c655e5`.
Before tag creation, candidate contract run `34278690899`, remote comparison/policy run
`34278693945`, and same-revision reusable-reporter run `34278697374` passed. A local exact
tag build then passed 337 tests, Ruff, citation validation, normal contract validation,
wheel installation outside the checkout, version equality, seven packaged schema
resources, policy evaluation, and deterministic checksums.

After the tag was pushed, distributed Action run `34279247047` passed 3/3 on Ubuntu,
macOS, and Windows, producing three artifacts. Minimum GitHub CLI run `34279250025`
installed the exact tagged extension and passed its metadata capture.

Exact-tag publisher run `34279324609` completed without intervention. Public release
`385066828` is neither a draft nor a prerelease and contains exactly:

- `SHA256SUMS`, 202 bytes, GitHub digest
  `038b965c548025ae8ee570f437a5a9c5f7662fa943ab75c00eb0f6c89802611f`;
- `gh_run_receptor-0.19.0-py3-none-any.whl`, 71,776 bytes, GitHub digest
  `580a9783ae68ccfb1b0b3445528a2c3916772b152227bde94613cc0f71e3b341`;
- `gh_run_receptor-0.19.0.tar.gz`, 105,441 bytes, GitHub digest
  `ee255503864b6f29057f79f6cd4d44909f5aa6447b9d27e7841407b44d213bce`.

Fresh downloads passed the published manifest and the independent release verifier.
GitHub reports `isImmutable=false`; policy, exact tag identity, and asset verification are
therefore the current protection rather than GitHub's administrative immutable-release
setting.

Zenodo verification run `34279652622` queried the public API after publication and
returned `ABSENT` for 0.19.0. No archive record or DOI is claimed. Enabling the repository
in the maintainer's Zenodo/GitHub integration remains an external handoff documented in
the release policy.

## Release 0.19.1

Tag `0.19.1` points to commit `4f910661d220b12d2626aa1f45ac99e07524b1c1` and publishes
the compatible safe-discovery correction. Contract run `34285137551` retained all seven
0.19.0 schema freezes. Minimum GitHub CLI run `34285137250` installed the exact tagged
extension and passed a real metadata capture. Distributed Action run `34285137260` passed
on Ubuntu, macOS, and Windows.

Exact-tag publisher run `34285248253` passed citation and contract validation, all 339
tests, build and manifest generation, draft verification, publication, and public-state
verification. Public release `385099198` is neither a draft nor a prerelease and contains
exactly:

- `SHA256SUMS`, 202 bytes, GitHub digest
  `16b0d02d6235c53c9ca4d22dfb7a3a8b5aa2c32d5facac33f6446a7dfc596435`;
- `gh_run_receptor-0.19.1-py3-none-any.whl`, 71,985 bytes, GitHub digest
  `57abf4074b870799ccba3e41177daf3ec19a147c9a7f3c1d443c3a58e4084983`;
- `gh_run_receptor-0.19.1.tar.gz`, 105,909 bytes, GitHub digest
  `f0f4c3bf4472a145054c079f12a37ab26dc0e9b4b632f9fa4fb8033f9e233c55`.

Fresh public downloads passed the published checksum manifest. The wheel then installed
without dependencies outside the checkout, reported exactly 0.19.1, and imported from the
isolated installation path. That independent check exposed and led to the correction of a
checkout-shadowing weakness in the publisher's own wheel-import assertion; the public
wheel itself passed the corrected procedure.

Zenodo verification run `34285502130` queried the public API after publication and returned
`ABSENT` for 0.19.1. No archive record or DOI is claimed.

## Release 0.20.0 producer-event checkpoint

Release 0.20.0 registers and freezes `events@1` without changing any of
the seven frozen schemas. It accepts only bounded, digest-checked, attempt-qualified
artifacts whose subject agrees with repository, run, attempt, and SHA. Local tests cover
safe ZIP handling, duplicate keys and identities, future contracts, wrong attempts,
offline replay, and profile aggregation.

A synthetic hidden-matrix case contains three GitHub-visible Python jobs and twelve
producer package events spanning four native platforms. The Conda profile reports all four
platforms successful, zero GitHub package artifacts, twelve producer events, and twelve
successful upload observations. A counterexample with a green official conclusion and a
producer-reported upload failure derives `FAIL` rather than hiding the contradiction.

Hosted producer run `34709939550` passes its two jobs on Ubuntu and Windows. Its two
attempt-qualified event artifacts are 934 and 936 bytes, and the generation plus explicit
artifact upload adds no more than one second per step at GitHub's timestamp resolution.
Normal metadata capture validates 16 events across four platforms and reports `PASS` while
preserving GitHub's `conclusion=success`. The 43,856-byte capture reduces to a reviewed
13,832-byte fixture with no logs or package archives; offline replay is deterministic.

The local gate covers that live fixture at the bundle, events, model, and report boundaries.
All eight registered schemas now have published freezes. Candidate validation proved that
`events@1` is the only resource newly frozen in 0.20.0 and did not exist in 0.19.0. The
exact `0.20.0` tag makes that declaration published history. The complete candidate gate
passed 360 tests, Ruff lint and format, developer-report validation, and 0.19.0
compatibility.

During that gate, run `34888469115` exposed a stale-active-cache defect: repeated
inspection retained a six-success/three-active snapshot after GitHub had completed with
three Windows failures. The corrected acquisition path recaptured and validated a
replacement in the same cache location and then reported the authoritative failure with
all three jobs grouped. The Windows failures themselves were an oversized implicit pytest
parameter identity followed by host-native separators in validator diagnostics. Bounded
explicit IDs keep `PYTEST_CURRENT_TEST` below Windows' environment-variable limit without
weakening the 64 KiB configuration boundary test; POSIX-normalized diagnostic paths keep
the release gate byte-deterministic across operating systems.

Tag `0.20.0` points to commit `bbbc8a6851446ca5c9483020ac352e97fb058849`.
Compatibility run `34892386411` passed all nine supported OS/interpreter combinations;
embedded Action run `34890911327` passed Ubuntu, macOS, and Windows. Exact-tag publisher
run `35194079890` passed citation and 0.20.0 contract validation, the full suite, isolated
distribution verification, draft verification, publication, and public-state
revalidation. Public release `390505433` is neither a draft nor a prerelease and contains
exactly:

- `SHA256SUMS`, 202 bytes, GitHub digest
  `d6cc28b71c1fcbbad326eddb11abe7ed009fc13b65f7a02cbc20d2bc386bd0f9`;
- `gh_run_receptor-0.20.0-py3-none-any.whl`, 78,115 bytes, GitHub digest
  `11845fa62e8d56b901efe86657b0c834e11e0d93d1539102314fd104936f2883`;
- `gh_run_receptor-0.20.0.tar.gz`, 115,082 bytes, GitHub digest
  `ff28dd232418c53e0103fc69c1ef74a69f23330821541496cacd149182b57f5b`.

Fresh public downloads passed the manifest and independent release verifier. The wheel
installed without dependencies outside the checkout, reported exactly 0.20.0, and imported
from the isolated installation. A public Zenodo query on 2026-09-17 returned `ABSENT`; no
archive record or DOI is claimed, and the maintainer activation handoff remains open.

Post-release minimum-transport run `35194481436` installed tag 0.20.0 through the
checksum-pinned GitHub CLI 2.48.0 and passed a real metadata capture. Distributed Action
run `35194479266` passed on Ubuntu, macOS, and Windows with publisher ref 0.20.0. Its
completion triggered terminal `workflow_run` reporter `35194534510`, which preserved the
source conclusion and produced the expected bounded report artifact. These are separate
hosted checks of the published tag rather than source-checkout tests.

After publication, the canonical 0.20.0 client guide was synchronized byte-for-byte to
twelve repositories. The published wheel accepted all eleven client `config@1` policies,
covering 63 exact workflow rules. MolSysMT commit `db9bec49e` and MolSysViewer commit
`4822f299` upgraded their native/ABI3 and noarch Conda publishers respectively to producer
Action v2.1.0, with explicit failure-safe event artifact upload. Six focused MolSysMT
workflow tests and the MolSysViewer workflow guard pass locally.

MolSysMT manual run `35196968944` then supplied the first real client delivery proof. It
built one Linux ABI3 candidate from exact commit `db9bec49e` with LTO enabled, validated
the artifact on Python 3.11, 3.12, and 3.13, and completed both GitHub-visible jobs
successfully without publishing to Anaconda. Producer Action v2.1.0 emitted the exact
attempt-qualified artifact
`gh-run-receptor-events-v1-35196968944-1-build-and-test-0`; its 668-byte `events@1`
payload records the package digest, `linux-64` platform, successful build, and
`upload=not_requested`. A complete 144 KiB capture replayed offline to the same bounded
summary: one of one platforms successful, one producer event, two of two jobs successful,
and two artifacts. The independently installed public 0.20.0 wheel reported the same
result. MolSysViewer source adoption remains locally guarded but still awaits its first
real noarch client run.

## 0.21.0 multi-run aggregation and release checkpoint

Issue `uibcdf/gh-run-receptor#38` defines an `aggregate@1` contract rather than
overloading two-run comparison. The first implementation accepts two to fifty homogeneous
local or remote sources, rejects duplicate run attempts, preserves every source identity
and official outcome, and derives a bounded collection assessment without inventing a
GitHub conclusion. Its schema independently constrains source exit-code/assessment pairs
and requires a witness for each derived non-pass state.

The initial focused gate passes 84 aggregation, contract-registry, report-contract, and CLI
tests. Truth tables cover known failure, other terminal non-success, pending work, and
incomplete evidence; a known failure remains exit 1 even when another source is incomplete.
Twenty-five adversarial source names prove terminal control escaping and the twenty-source
text bound. The offline CLI combines sanitized CI, documentation, and Conda bundles without
network access.

The first live command combined MolSysMT run `35196968944` and gh-run-receptor distributed
Action run `35194479266` by full URLs. An initial invocation exposed a missing explicit
`attempt=None` at the shared acquisition boundary; the focused remote test now asserts that
argument. The corrected invocation reported `PASS`, two complete sources, five jobs, five
artifacts, two repositories, and two workflows. This is a read-only local-client probe of
real hosted evidence.

Exact-revision hosted gate `35202361626` passed that two-success case at commit `37d8af7`
with only `actions: read` and `contents: read`. A retained MolSysViewer CI failure,
`34890243748`, was then combined with the MolSysMT success locally: the aggregate preserved
one official failure, one success, nine jobs, two artifacts, complete evidence, and exit 1.
Exact-revision gate `35204416931` then passed both the success and mixed-failure cases at
commit `64a82eb`. Candidate validation assigns only `aggregate@1` to 0.21.0 and retains the
other eight schema resources against their original published tags.

For the two-success question, a compact native JSON projection measured 632 bytes and 208
`cl100k_base` tokens; the three-line aggregate measured 527 bytes and 139 tokens, a 33.2%
token reduction. Two separate receptor success lines remain smaller at 278 bytes and 87
tokens. This counterexample is intentional: multi-run aggregation supplies a coherent
versioned collection and coverage summary, while repeated `inspect` is preferable when the
reader needs only two already-known per-run verdicts.

Tag `0.21.0` points to commit `957adf849e7bab3ab4d9f2bcbb53b8f8c31f1998`.
Before publication, the full local suite passed with 372 tests together with Ruff,
citation, devguide, and compatibility-against-0.20 contract validation. An exact-tag
local wheel installed outside the checkout, imported from the isolated target, reported
0.21.0, and executed a two-bundle `aggregate@1` report successfully.

Draft-first release run `35209615936` passed the full release gate and published a
non-draft, non-prerelease GitHub Release. Independent public checks resolved the tag to
the exact commit above, verified the checksum manifest, installed the downloaded wheel
outside the checkout, and imported version 0.21.0 from that installation. The release
contains:

- `gh_run_receptor-0.21.0-py3-none-any.whl`, 83,137 bytes, GitHub digest
  `sha256:1cba5e6c6a6035bf98802e69dd59db65869883b8d0e52e4f3e3f76020cdffb76`;
- `gh_run_receptor-0.21.0.tar.gz`, 121,352 bytes, GitHub digest
  `sha256:b82be07189ec53eee02a9e40977f43d4204bd1c833e91fe78091f9a35039663f`;
- `SHA256SUMS`, 202 bytes, GitHub digest
  `sha256:d7bb145bbe5cd54049f1c256c3111f6cdebe3fcf8b6a43ff042b2f8600644312`.

Five exact-tag post-release gates then passed: distributed Action run `35209958663` on
Ubuntu, macOS, and Windows; checksum-pinned minimum GitHub CLI run `35209958849`; frozen
contract run `35209958624`; live success and mixed-failure aggregate run `35209958468`;
and the nine-combination Python 3.11--3.13 compatibility matrix `35209958620`. Finally,
the independently installed public wheel aggregated those five runs into one complete
`PASS` assessment covering five workflows, 15 successful jobs, and three artifacts. This
is the first release whose new multi-run contract is both its subject and the mechanism
used to summarize its post-publication evidence.

After publication, the canonical 0.21.0 client guide was synchronized byte-for-byte to
all twelve tracked repositories. Each repository received an isolated `[skip ci]` commit;
the unrelated untracked TopoMT smoke-test notebook was preserved. Exact-tag Zenodo run
`35211669763` then queried the public service and returned the designed `ABSENT` result for
0.21.0. The GitHub Release is valid, but archival is not complete: a UIBCDF maintainer must
enable the repository integration before a future release and then repeat the verifier.

## Stable CLI exit-code release checkpoint

Issue `uibcdf/gh-run-receptor#39` audited the complete command boundary before 1.0. The
documented map already assigned invalid usage to 64, but the default `argparse` behavior
returned 2, colliding with the legitimate terminal non-success category. A dedicated
parser boundary now returns 64 for malformed commands and arguments while help and version
remain 0. Named internal constants are shared by report, comparison, aggregation, capture,
CLI error, interruption, and embedded Action paths without changing the Action's fail-open
behavior.

The local gate passed 386 tests. Four real replay fixtures and a missing bundle exercise
process statuses 0, 1, 2, 4, and 5; malformed command and run references exercise 64;
deterministic unit cases cover pending status 3 and interruption status 130. Exact-revision
hosted run `35219407440` passed the reproducible console categories at commit `28dbddb`.
Tag `0.21.1` points to commit `08c42405829d8675392cb201cbdbd6ed56e2bea4`.
Draft-first release run `35221114971` passed the full gate, including installation outside
the checkout and status 64 from that installed wheel. The public release contains:

- `gh_run_receptor-0.21.1-py3-none-any.whl`, 83,964 bytes, GitHub digest
  `sha256:8eb85e9e5d88fe5d44b85fcbe660aa58155fb04c01a380b8cdc3b514a005b702`;
- `gh_run_receptor-0.21.1.tar.gz`, 123,090 bytes, GitHub digest
  `sha256:77eafedd72058831740839cdf759df0a056f8b0c2092c8460c59625e8c00dd78`;
- `SHA256SUMS`, 202 bytes, GitHub digest
  `sha256:2af2c53e25f59eb521681afa06e85d90c1dafaedef4fff14b96ba7e327709459`.

Independent download verified both checksums, exact tag identity, isolated import, version,
and status 64. Post-release runs passed the distributed Action on three systems
(`35221273239`), GitHub CLI 2.48.0 extension installation and usage boundary
(`35221272574`), the nine OS/Python combinations (`35221272724`), exact-tag exit-code gate
(`35221272758`), and all nine frozen contracts (`35221272678`). The public wheel aggregated
those five runs as `PASS` with 15 successful jobs, three artifacts, and complete evidence.
Its canonical guide was then synchronized byte-for-byte to all twelve tracked clients.

The non-overlapping map is now a released stable boundary for CLI 1.0. New meanings require
a compatibility decision rather than reuse of an existing number. Exact-tag Zenodo run
`35221505754` returned the designed `ABSENT` result; account-side activation remains the
separate archival blocker.

## Public documentation and repository identity checkpoint

Issue `uibcdf/gh-run-receptor#40` used pytest-receptor's proven Sphinx/MyST information
architecture as a reference without copying its pytest-specific product text. The public
site has task-oriented pages for installation, command use, profiles, embedded reporting,
configuration, contracts, security, limitations, and benchmarks. `devguide/` remains the
maintainer checkpoint rather than being exposed as the user learning path.

The local strict Sphinx 8.2.3 build completed ten source pages with no warnings. The full
suite passed with 391 tests, including guards for navigation, optional dependency bounds,
workflow triggers, least-privilege job separation, four exact third-party Action commits,
and badges backed by real project surfaces. Implementation commit `62b314d` deployed in
hosted run `35224624974`: the read-only build and Pages-only deploy jobs both passed and
produced one Pages artifact.

GitHub Pages reports workflow build mode and the public site at
`https://www.uibcdf.org/gh-run-receptor/`. Independent retrieval returned HTTP 200 for the
index and all nine task pages. The repository description is “A GitHub Actions evidence
receptor for coding agents: compact reports without hiding failures or uncertainty”, and
the observed HTTPS site is its homepage. README and package metadata link to the same URL.
The README also exposes the policy, documentation, release, Python-support, and license
status without presenting a manual validation workflow as continuous test coverage.
Repository discovery uses the generic topics `ai-agents`, `developer-tools`,
`github-actions`, `github-cli`, `llm`, and `observability`; none couples the public tool to
MolSysSuite.

## Adaptive capture policy checkpoint

Issue `uibcdf/gh-run-receptor#41` extracted the automatic log decision into one pure truth
table and added `devtools/scripts/benchmark_capture_policies.py`. The policy skips logs for
active and completed successful runs and requests the complete attempt archive only after
GitHub confirms completion with a conclusion other than `success`, including absent or
unrecognized values. Explicit `full` and `metadata` retain their unconditional meanings.

The 13 committed bundles pass the offline policy audit, including a real failed
PyUnitWizard attempt whose adaptive request returned HTTP 410 and remains honestly
incomplete. A separate 42-bundle local adaptive inventory requested logs for nine
failures and two cancellations, skipped 30 successes and one active run, and avoided 31
of 42 possible requests. It observed 879,112 log bytes but does not assign zero bytes to
the skipped archives whose counterfactual sizes are unknown.

Paired temporary captures used successful documentation run `35224624974` and failed
Zenodo-verification run `35221505754`. Adaptive avoided the successful run's 13,678-byte
archive, reducing that bundle from 43,644 to 29,966 bytes. Both modes captured 5,397 log
bytes for the failure, produced equal 27,322-byte bundles, and diagnosed the same one
failed job. The benchmark therefore recorded 13,678 observed bytes saved and zero missing
diagnoses across one success and one terminal non-success pair. Raw logs were neither
committed nor uploaded.

The complete local gate passed 420 tests, Ruff, strict Sphinx, developer-report validation,
and all nine contracts frozen against 0.21.0. Exact-revision hosted run `35265984761`
passed at commit `5709a84`. Its committed-corpus phase validated 13 bundles; its live
phase reproduced two full/adaptive pairs, 13,678 observed bytes saved, and zero missing
diagnoses without uploading an artifact. OD-002 is settled for the 0.22.0 candidate.

## 0.22.0 release checkpoint

The candidate combines the public Sphinx site, adaptive capture policy, and stable watch
contract without adding or changing a serialized resource. The complete local gate passed
434 tests, Ruff, strict Sphinx with warnings as errors, developer-report validation,
citation validation, and all nine contracts frozen against 0.21.0. A clean temporary clone
was committed and tagged locally as 0.22.0; using the already installed build toolchain
because this development environment has no package-index network access, it produced the
exact wheel and source-distribution names, a valid checksum manifest, and bounded release
notes. The wheel was installed outside the checkout, imported as version 0.22.0 from the
isolated target, and returned status 64 for malformed usage.

Five manual gates then passed at exact candidate commit
`5b8615e66c3bb6c2d11b2e3ac2d406d67f1a1409`: compatibility run `35435442151` completed all
nine operating-system/Python combinations; contract run `35435443429` retained all nine
published freezes; adaptive-capture run `35435444536` repeated the offline and live policy
checks; checkout-local Action run `35435445665` passed on Ubuntu, macOS, and Windows; and
documentation run `35435447262` built and deployed the strict site. A five-source receptor
aggregate first preserved the still-running compatibility matrix as `PENDING`, then the
watch command reported its terminal nine-of-nine `PASS` without repeated snapshots.

Tag `0.22.0` points to commit `cbe269fcddfbcaaa6c5a691817221eca011935a8`.
Five exact-tag gates passed before publication: compatibility run `35435894883`, frozen
contract run `35435896629`, adaptive-capture run `35435898243`, distributed Action run
`35435899693`, and checksum-pinned minimum GitHub CLI run `35435900814`. Draft-first
release run `35435957227` then published a non-draft, non-prerelease GitHub Release after
verifying tag identity, citation, the complete suite, distributions, checksums, notes, and
both draft and public asset states. Independent download and installation repeated those
checks. The public assets are:

- `gh_run_receptor-0.22.0-py3-none-any.whl`, 85,880 bytes, SHA-256
  `61c08ae07dbd71ce523292b59e4b6a6505e74f82b81d07b2dbb7c230e845081d`;
- `gh_run_receptor-0.22.0.tar.gz`, 129,718 bytes, SHA-256
  `7a2eff8b385a7a869d2649e75972d95a7bedd207af53b49f612224028405c457`;
- `SHA256SUMS`, 202 bytes, SHA-256
  `2509a53880d3c4046dc36559dffad810c391a59038d36a138233c66df89889ce`.

Zenodo verification run `35436181206` passed on the first post-publication query. The
public record contains version 0.22.0 and the archived source ZIP; the version DOI is
`10.5281/zenodo.22843378` and the stable concept DOI is `10.5281/zenodo.22843377`. This is
observed archival evidence, not an inference from the presence of a release webhook.

After publication, the canonical 0.22.0 client guide was synchronized byte-for-byte to all
twelve tracked repositories. Each repository received an isolated `[skip ci]` commit that
changed only `GH_RUN_RECEPTOR_GUIDE.md`; the unrelated untracked TopoMT smoke-test notebook
was preserved. The synchronizer's exact comparison passes across all twelve copies.

## Replay determinism checkpoint

Issue `uibcdf/gh-run-receptor#43` strengthened the replay claim from repeated construction
in one context to a real CLI process-boundary guard. Two copies of the sanitized
MolSysViewer CI failure bundle receive distinct nested paths, file modification times,
capture timestamps, POSIX timezone strings, and `SOURCE_DATE_EPOCH` values. JSON, LLM, and
human invocations each return the same source-failure status, empty stderr, and
byte-identical stdout across both contexts.

The complete local gate passed 437 tests, Ruff, all nine frozen contracts, developer-report
validation, and strict Sphinx. Exact-revision compatibility run `35437166644` passed the
full suite and installed-wheel smoke test on Ubuntu, macOS, and Windows with Python 3.11,
3.12, and 3.13 at commit `540015b78eea288e4a0233d9469244d24928e51a`.

## 1.0 scope-freeze checkpoint

Issue `uibcdf/gh-run-receptor#47` converted the completed implementation roadmap into a
finite stable-release boundary. `release_readiness_1_0.md` maps every 1.0 requirement to
an independent test, contract comparison, benchmark, hosted gate, or public-service
observation. Pattern selectors and organization-level configuration discovery are
explicit post-1.0 work rather than unresolved stable-release gates. Two behavioral tests
now prove that `config@1` rejects both deferred shapes instead of silently accepting
future-looking policy.

At the scope-freeze commit, the complete local suite passed 442 tests on Python 3.13.14,
Ruff lint passed, strict Sphinx 8.2.3 completed with warnings as errors, developer-report
validation passed, and all nine contracts remained frozen against the 0.21.0 registry
baseline. Ruff formatting still reports the two pre-existing unrelated files recorded by
the development checkpoint; the files changed for this increment pass their focused
format check. No 0.23.0 hosted or public-release result is claimed yet.

## What this does not prove

- Log analysis currently recognizes a deliberately small generic signature set and is not
  yet a complete diagnosis engine.
- The committed real-run corpus remains narrow. Authentic `timed_out` remains absent and
  opportunistic under the documented non-generatable-outcome exception; exact-source
  synthetic evidence covers the complete product path without claiming a live source.
- Private-repository and fork token behavior of the embedded Action is not established by
  the public and same-repository probes.
- External registries, GitHub Releases, Git refs, and archive records are not queried by
  the first release profile.
