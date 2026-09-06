---
summary: Consume and verify published Action reports
issue: uibcdf/gh-run-receptor#19
status: resolved
opened: 2026-09-06
closed: 2026-09-06
verification: measured
area: ['github']
guard: tests/test_published.py
normative:
blocked_by: []
supersedes: []
---

# Consume and verify published Action reports

**Reported:** 2026-09-06, after the first terminal downstream reporter uploaded a bounded
canonical report that the external CLI could inventory but not consume.
**Status:** Resolved; the command passes adversarial local tests, real artifact consumption,
and GitHub CLI extension validation on Ubuntu, macOS, and Windows.

## What

Add `gh run-receptor published REPORTER_RUN_ID`. The explicit command downloads one named
report artifact, validates it defensively, verifies its terminal source facts against fresh
GitHub metadata, and renders the original report without recapturing source jobs or logs.
The artifact name defaults to `gh-run-receptor-report` and can be selected exactly with
`--artifact`.

## How

Fetch the reporter run and paginated artifact inventory through the existing GitHub adapter.
Require the reporter run to be completed, select exactly one non-expired artifact with the
requested name, and reject inventory sizes above 10 MiB. Download its ZIP to a private
temporary directory. Accept exactly one regular, unencrypted, non-symlink JSON member and
stream at most 8 MiB of expanded data. Strict JSON parsing rejects duplicate keys and
non-finite numbers.

The report must carry `report@1`, the required structural fields, and Action publisher
provenance. Its source repository must equal the reporter repository in this slice. Fetch
the source run independently and require exact agreement for run ID, attempt, head SHA,
status, conclusion, and URL where present. Only completed source runs are accepted. A
truth table constrains receptor assessment by official conclusion, so an artifact can never
turn official non-success into `PASS`.

The rendered report adds a warning that source facts were verified but profile
interpretation was not independently recomputed. This is intentional: an artifact digest
authenticates stored bytes, not the producer's semantic correctness.

## Why

The external CLI currently repeats structured source capture even when the released Action
has already produced the exact bounded report. This path turns embedded reporting into a
reusable low-token cache while preserving a fresh authoritative check and an explicit trust
boundary. It is directly applicable to MolSysMT and MolSysViewer development workflows.

## What is measured and what is assumed

Downstream reporter run `34045953527` has one non-expired artifact named
`terminal-source-report`. GitHub reports 1,449 stored bytes and a SHA-256 digest. Its ZIP
contains exactly one 8,043-byte JSON member compressed to 1,281 bytes. These values were
measured with the Actions artifacts API and `unzip -lv`; limits deliberately leave orders
of magnitude of headroom while matching the Action's existing 8 MiB report cap.

The implemented command consumed that live artifact and preserved source run `34045930131`.
It made four requests rather than the seven needed by equivalent metadata capture, a 42.9%
reduction. Response and artifact bytes fell from 36,735 to 26,653 (27.4%), elapsed time from
4.04 to 2.63 seconds (34.9%), and peak RSS from 42,380 to 42,204 KiB (0.4%). This successful
run required no logs; unsuccessful adaptive capture would add the retained log archive to
the baseline.

## Implementation progress

`published` now has an exact artifact selector and shares the ordinary renderers and exit
mapping. Its dependency-free consumer validates inventory, transport bytes, GitHub digest,
ZIP structure, strict JSON, report structure, publisher presence, fresh source identity,
terminal truth, and conclusion/assessment compatibility. The transport accepts a narrower
caller limit so oversized bytes stop during streaming. Unit and contract tests cover the
hostile boundaries. Manual run `34047166101` passed 3/3 on Ubuntu, macOS, and Windows;
published-report consumption took 2--3 seconds in each hosted job and preserved the same
verified source identity and `PASS` conclusion.

## What was refuted

- Automatically preferring any artifact during `inspect` is rejected because it silently
  changes the requested subject and trust model.
- Trusting a matching schema or publisher field alone is rejected because workflow code can
  upload forged JSON.
- Treating GitHub's artifact digest as semantic attestation is rejected; it proves bytes,
  not which interpretation produced them.
- Downloading every artifact to discover a report is rejected as unbounded and wasteful.
- Requiring `jsonschema` at runtime is rejected for this slice; the package remains
  dependency-free and validates the consumed structural boundary directly.

## Scope and exclusions

This slice does not auto-discover downstream reporter runs from a source run, trust
cross-repository publishers, consume arbitrary producer events, recompute profile semantics,
or use published reports as configuration policy. Automatic fallback from `inspect` remains
future work after explicit-command behavior is measured.

## Acceptance criteria

- The new command selects one exact non-expired artifact without fetching source jobs or
  logs.
- ZIP traversal, links, encryption, duplicate members, extra files, oversized inventory,
  oversized expansion, duplicate JSON keys, malformed JSON, and wrong schemas fail closed.
- Reporter/source repository, run ID, attempt, SHA, completed status, conclusion, and URL
  mismatches fail closed.
- No allowed conclusion/assessment pair can report official non-success as `PASS`.
- Text and JSON rendering reuse the existing renderers and exit-code contract.
- A live invocation consumes run `34045953527`, preserves source run `34045930131`, and
  materially reduces API requests and downloaded bytes versus metadata capture.
- The full local and cross-platform package gates remain green.

## Dependencies and risks

There is no tracked blocker. Artifact retention can expire independently of run metadata;
this becomes an explicit acquisition failure with native `inspect` as fallback. The first
slice assumes a same-repository reporter because cross-repository token and provenance rules
need a separate trust decision.

## Provenance

Linux, Python 3.13.14, GitHub CLI 2.81.0, gh-run-receptor 0.12.0 through the 0.13.0
release candidate, unzip 6.00, 2026-09-06. Artifact inventory, archive bytes, and
cross-platform execution came from public runs in
`uibcdf/gh-run-receptor`.

## Correction, 2026-09-06

The 0.13.0 JSON and human report exposed the interpretation warning, but the successful LLM
fast path omitted it. Issue `uibcdf/gh-run-receptor#20` adds the two structured trust values
to the compact success line and is guarded in `tests/test_published.py` for 0.13.1.
