---
summary: Measure and freeze the adaptive log-capture policy for 1.0
issue: uibcdf/gh-run-receptor#41
status: active
opened: 2026-09-17
closed:
verification: measured
area: [capture, performance, contracts]
guard:
normative:
blocked_by: []
supersedes: []
---

# Measuring and freezing the adaptive log-capture policy for 1.0

**Reported:** 2026-09-17 while selecting the next evidence-backed increment after the
0.21.1 release and public-documentation rollout.
**Status:** Active; the current rule and contradictory defaults are measured, while the
corpus benchmark and stable decision remain in progress.

## What

Resolve open decision OD-002 before 1.0 by defining exactly when `adaptive` capture
downloads the complete workflow-attempt log archive. Measure request and byte cost,
diagnostic coverage, and incomplete behavior across the retained corpus. Then either
freeze the adaptive rule and defaults or restore a conservative full-capture default until
the missing evidence exists.

This work must reconcile the current public surface:

- `inspect` and `watch` default to `adaptive`;
- the explicit archival `capture` command defaults to `full`;
- `compare` and `aggregate` default to `metadata`;
- `docs/usage.md` already calls `adaptive` the default for `inspect` and `watch`;
- `devguide/architecture.md` and OD-002 still say development remains `full` until the
  adaptive threshold is proven.

## How

Extract the log-fetch choice into one small pure policy function and exercise it with a
truth table covering successful, failed, cancelled, timed-out, neutral, skipped,
action-required, stale, startup-failure, active, completed-without-conclusion, and unknown
states. Keep GitHub status and conclusion authoritative; do not infer failure or timeout
from duration or step prose.

Build a reproducible benchmark that can inspect sanitized bundles and an explicitly named
local capture corpus without committing raw logs. It should report at least:

- number and fraction of log-download requests made and avoided;
- structured and log bytes present in measured bundles;
- source status/conclusion coverage;
- whether every terminal non-success requested logs;
- whether any successful or active run requested logs;
- unavailable-log outcomes and their effect on bundle completeness;
- diagnoses available from structured metadata alone and additional bounded causes found
  in logs.

The benchmark must keep observed bytes separate from counterfactual bytes. An adaptive
bundle that skipped successful logs proves one avoided request, but it does not reveal how
many bytes a `full` request would have returned. Measure that counterfactual only through
paired captures of the same run or label it unknown.

The likely stable boundary is command-specific rather than one global default:

- `capture` remains archival and defaults to `full`;
- `inspect` and the terminal report after `watch` default to `adaptive`;
- `compare` and `aggregate` retain `metadata` because their required truth is structured;
- explicit `--capture` always overrides the default.

That candidate is not accepted until the benchmark and tests pass.

## Why

Log archives can dominate transferred bytes and are not required to preserve official
run, job, step, check, artifact, or producer-event state. They are valuable for causal
diagnosis after a non-success. Fetching them for every successful inspection spends time,
bandwidth, cache space, and GitHub API budget without normally changing the report.

The current implementation uses a simple run-level predicate:

```text
full OR (adaptive AND status == completed AND conclusion != success)
```

This downloads the complete attempt archive for every completed non-success, including
`cancelled`, and for a completed run whose conclusion is absent or unknown. It does not
inspect individual job conclusions and cannot truthfully be described as downloading only
failed-job logs. GitHub's attempt-log endpoint supplies the complete archive; selective
per-job acquisition would be a different source and bundle-design decision.

Leaving the contradiction unresolved would freeze accidental behavior at 1.0. Tightening
the rule without measurement could lose causal evidence, while widening it to every run
would discard most of the intended network savings.

## What is measured and what is assumed

Source inspection at commit `62c3fb2` confirmed the defaults and predicate above. The
generic transport bounds any individual download at 512 MiB; no smaller log-specific
limit exists.

A read-only inventory of existing local adaptive bundles found 42 captures:

| Source state | Captures | Log bytes present | Structured bytes present |
| --- | ---: | ---: | ---: |
| completed / success | 30 | 0 | 1,969,443 |
| completed / failure | 9 | 815,585 | 377,399 |
| completed / cancelled | 2 | 63,527 | 66,007 |
| in progress / no conclusion | 1 | 0 | 88,695 |
| **Total** | **42** | **879,112** | **2,501,544** |

The observed policy requested logs for 11 of 42 captures (26.2%) and avoided a log request
for 31 (73.8%). All 11 terminal non-success captures retained logs; no successful or
active capture did. All 42 manifests were complete and none carried a warning. The corpus
spans UIBCDF and three external repositories, but it is opportunistic and heavily weighted
toward successful gh-run-receptor validation workflows.

This inventory does **not** establish the full-policy byte total because the 30 skipped
successful archives were not downloaded. It also does not establish a diagnostic miss
rate: most committed fixtures intentionally omit raw logs, and the local corpus was not
selected independently of the adaptive policy.

The committed corpus separately contains a real failed PyUnitWizard attempt whose log
request returned HTTP 410. Its manifest preserves the official failure, marks the bundle
incomplete, and renders `INCOMPLETE`; this is evidence that a required adaptive log can be
unavailable without erasing GitHub truth.

The first benchmark implementation also exposed that sanitization relabelled this fixture
as `metadata` while retaining its adaptive log-request warning. The sanitization rule now
preserves the original policy whenever no log member was removed, and changes the policy
to `metadata` only when it actually strips a retained archive. The corrected 13-bundle
committed corpus passes with no policy contradiction.

Two exact-run pairs then measured the counterfactual directly. Successful documentation
run `35224624974` occupied 29,966 bytes under adaptive and 43,644 under full; adaptive
avoided the 13,678-byte log archive. Failed Zenodo-verification run `35221505754` occupied
27,322 bytes in both modes, including 5,397 log bytes, and both diagnosed the same one
failed job. The paired benchmark reports 13,678 observed bytes saved and zero missing
diagnoses across one successful and one terminal non-success pair.

The candidate stable rule is supported locally. The remaining acceptance work is the
complete suite, strict documentation build, and exact-revision hosted pair gate.

## Alternatives and refuted paths

- Treating the already shipped CLI default as proof was rejected. Existing behavior is
  the subject under test, not its own evidence.
- Fetching logs for every run was rejected as an unmeasured retreat from the product's
  settled structured-first direction.
- Fetching no logs automatically was rejected because the existing failure benchmark
  derives useful grouped causes from log evidence.
- Fetching only when the run conclusion is exactly `failure` was rejected as prematurely
  narrow: cancellation, timeout, startup failure, action-required, and unknown terminal
  conclusions can also require causal evidence.
- Inferring terminal state or failure from elapsed time, step names, or log text was
  rejected because GitHub status and conclusion are authoritative.
- Claiming byte savings by treating skipped successful archives as zero-byte archives was
  rejected; their counterfactual size is unknown until paired capture.
- Immediately switching to per-job log endpoints was deferred. It changes acquisition
  provenance and archive construction rather than merely settling the existing threshold.

## Scope and exclusions

This proposal covers the automatic log-fetch decision, command defaults, measurements,
tests, and user/developer documentation. It may add benchmark tooling that reads local raw
captures, but raw logs remain excluded from Git.

It does not introduce log streaming, per-job archive synthesis, remote deletion, cache
eviction, a new serialized contract version, or a general log query language. The 512 MiB
transport ceiling may be reviewed if measurements expose a concrete risk, but changing it
is not required to settle the threshold.

## Acceptance criteria

- One named pure predicate owns the adaptive log-fetch decision.
- A truth table tests all documented GitHub conclusions plus active, absent, and unknown
  values without inferring source state.
- The benchmark reports requests, observed bytes, completeness, and diagnostic deltas
  without treating unknown counterfactual bytes as zero.
- Paired full/adaptive captures measure at least one successful run and one terminal
  non-success run from the same source revisions where retention permits.
- The committed corpus and incomplete-log fixture pass the stable rule without hiding
  official conclusions.
- CLI defaults, README, public docs, architecture, evidence rules, and OD-002 agree.
- Any claimed savings name corpus composition and limitations.
- Ruff, strict Sphinx, the full pytest suite, and the relevant hosted exact-revision gate
  pass before release.
- The decision is recorded as a 0.22.0 compatibility change or explicit confirmation and
  is suitable for freezing at 1.0.

## Dependencies and risks

GitHub log retention may prevent paired capture of older failures. Recent bounded runs can
provide byte measurements, while the committed unavailable-log fixture preserves the
retention failure. Raw logs can contain secrets or personal data and must stay in private
owner-readable temporary/cache locations; only aggregate measurements and sanitized
diagnostic categories may be committed.

The local inventory is not an independent statistical sample. A broad rule can show zero
misses by requesting logs for every terminal non-success, but that does not prove log
diagnosis quality. The report must distinguish source-truth preservation, request policy,
and causal diagnosis.

## Provenance

Measured 2026-09-17 on Linux 7.0.0-28-generic x86_64 from gh-run-receptor `62c3fb2`.
The local corpus paths were `/home/diego/.cache/gh-run-receptor`,
`/tmp/ghrr-adaptive-live`, and `/tmp/molsysmt-35196968944-ghrr.json`; raw evidence remains
uncommitted. GitHub CLI and API behavior are interpreted through the project's installed
transport adapter and API version `2022-11-28`.
