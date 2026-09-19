---
summary: Freeze watch polling and API-budget semantics for 1.0
issue: uibcdf/gh-run-receptor#42
status: resolved
opened: 2026-09-17
closed: 2026-09-19
verification: measured
area: ['cli', 'github', 'tests']
guard: tests/test_watch.py
normative: cli_and_output_contract.md
blocked_by: []
supersedes: []
---

# Freeze watch polling and API-budget semantics for 1.0

**Reported:** 2026-09-17, while reviewing OD-005 before declaring `watch` stable.
**Status:** Resolved; deterministic polling, transition output, request accounting, and
terminal handoff are implemented, tested, measured, and documented.

## What

Define the stable pre-1.0 contract for polling intervals, transition emission, transient
acquisition failures, terminal refresh, and GitHub API use. The contract must remain
truth-preserving while avoiding both repeated unchanged output and avoidable requests.

## How

Measure the current receptor and `gh run watch --compact`, then make the receptor budget
observable in deterministic tests. Keep the current transition-only output. Specify the
poll schedule and error retry behavior precisely, resolve the mismatch between the
documented jitter and deterministic implementation, and transfer terminal evidence into
the final capture when doing so does not weaken identity validation.

The initial inspection found that a normal current-attempt snapshot performs one run
request plus one paginated jobs request. After observing completion, the CLI ignores that
snapshot and starts an ordinary capture, which requests the run and jobs again. The final
capture also needs workflow, artifact, check-run, and trusted default-branch configuration
evidence, so not all terminal requests are duplicates.

## Why

`watch` is intended for long-running workflows. An opaque schedule can waste the REST API
budget, while an overaggressive backoff can hide meaningful transitions for too long.
Repeated terminal acquisition adds latency and requests at exactly the point where the
user expects the final answer. Stable documentation must state a budget users and client
repositories can reason about.

## What is measured and what is assumed

Observed from `gh_run_receptor/watch.py` and `gh_run_receptor/bundle.py`:

- unchanged successful polls multiply the delay by 1.5 up to `--max-interval`;
- a reported transition resets the delay to `--interval`;
- an acquisition failure doubles the delay and the third consecutive failure aborts;
- a current-attempt poll performs one run request plus however many 100-job pages GitHub
  returns;
- terminal capture currently repeats the run and jobs acquisition;
- the documentation says polling uses jitter, but no jitter exists in the implementation.

On 2026-09-17, completed successful MolSysMT run `33849332945` was inspected from a fresh
cache with both tools:

```text
GH_DEBUG=api gh run watch 33849332945 --repo uibcdf/molsysmt --compact
./gh-run-receptor watch 33849332945 --repo uibcdf/molsysmt \
  --cache-dir FRESH_CACHE --receptor=llm
```

Native `gh` made two observed HTTP requests and emitted 87 bytes on one stdout line. The
receptor emitted 115 bytes on one stdout line and no progress stderr because the run was
already complete. Successful receptor subprocess diagnostics are intentionally discarded,
so its request count must be measured at the transport adapter rather than inferred from
`GH_DEBUG` output. These completed-run output sizes are case measurements, not a general
token-saving claim.

The prior live observation of run `34027741137` remains valid evidence for transition
behavior: during approximately one minute it emitted the initial state, no unchanged
snapshots, one job completion, one run completion, and one final report.

## What was refuted

- Reprinting the whole job tree is rejected because unchanged snapshots consume reader
  attention and tokens without adding state.
- Treating a paginated jobs command as exactly one API request is rejected; workflows may
  exceed one page.
- Removing the final capture is rejected because polling metadata lacks workflow,
  artifact, check-run, configuration, and failure-log evidence needed by the report.
- Claiming a rate-limit saving from output size alone is rejected; stdout and API use are
  separate budgets.

## Scope and exclusions

This proposal does not add mutation, server-side event delivery, organization-level
configuration, or arbitrary live-log streaming. It does not promise a fixed request count
for producer artifacts, log downloads, configuration presence, or job collections that
need several pages; those variable costs must instead be expressed explicitly.

## Acceptance criteria

- Freeze exact default/minimum/maximum interval validation and the backoff/reset rules.
- Preserve one initial state, transition-only progress, and exactly one final report.
- Count adapter calls and pages in deterministic tests for active, unchanged, terminal,
  historical-attempt, and transient-error paths.
- Avoid re-requesting terminal run/jobs evidence when it can be handed safely to capture.
- Compare a real completed run with native compact watch and record the bounded conclusion.
- Document a request-budget formula, variable-cost exceptions, and the native fallback.
- Run Ruff, the full `pytest --receptor=llm` suite, strict documentation, and developer
  guide validation before resolving the proposal.

## Dependencies and risks

No tracked dependency blocks the local contract. GitHub may add pagination pages or
change native CLI internals, so tests must freeze receptor behavior rather than native
implementation details. Reusing polling evidence must not let a stale or partial snapshot
bypass bundle identity and completeness checks.

## Provenance

Initial measurements ran on 2026-09-17 on Linux in the project checkout, with Python
3.12.8 and GitHub CLI 2.93.0, against public `uibcdf/molsysmt` evidence. Raw debug output
and caches remain under `/tmp` only and are not repository artifacts.

The final 2026-09-19 validation ran on Linux with Python 3.13.14, pytest 9.1.1,
pytest-receptor 0.7.0, Ruff 0.16.1, tiktoken 0.13.0, and GitHub CLI 2.93.0. The active
comparison used public run `35432811964`; GitHub reported `completed`/`success` with one
successful job.

## Resolution

The accepted contract uses finite intervals of at least one second, defaults of 10 and 60
seconds, 1.5 unchanged backoff, transition reset, 2 error backoff, and termination on the
third consecutive acquisition failure. It deliberately omits jitter. Successful polls
count one run request, one request per jobs page, and one additional run request for a
historical attempt.

Terminal run and job payloads are retained by `RunSnapshot`. The final capture reuses them
only when the run ID and attempt agree, the run is terminal, all jobs are terminal, and
any available job identity fields agree. A lagging job collection is reacquired. All
other report evidence remains freshly acquired or comes from an identity-checked completed
cache.

The active comparison measured 321 `cl100k_base` tokens across 38 native compact-watch
lines versus 86 tokens across four receptor lines, a 73.2% reduction. The completed-run
boundary measured 20 native tokens versus 39 receptor tokens and therefore carries no
savings claim. Instrumentation counted nine receptor API invocations for the active case
and seven for the optimized completed case; the latter used nine before terminal handoff.
The full commands, formula, rejected quota-header inference, and limitations live in
`devguide/benchmark_watch_2026-09-19.md`.

Final local gates passed: 432 tests through `pytest --receptor=llm`, Ruff, all nine frozen
serialized contracts against 0.21.0, developer-report validation, strict Sphinx, and
`git diff --check`.
