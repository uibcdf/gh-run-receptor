---
summary: Assess and improve timeout diagnosis before choosing producer instrumentation.
issue: uibcdf/gh-run-receptor#46
status: open
opened: 2026-09-19
closed:
verification: measured
area: [github, profiles]
guard:
normative:
blocked_by: []
supersedes: []
---

# Assessing timeout diagnosis before choosing producer instrumentation

## Current decision — 2026-10-02

The principal MolSysSuite maintainer requests that GH Run Receptor first assess
and improve diagnosis using available evidence. Only an established residual
need should lead to a producer contract, external Action changes or a new Action.
This issue is ready for provider investigation; it is no longer blocked by
uibcdf/molsyssuite#25 or by the already published 1.0 release. MolSysSuite #25
now waits for this assessment. The report path retains its original identity.

The earlier scope concerned consuming a future structured operation-timeout
producer after a central ownership decision. That ordering is superseded by
this maintainer decision. No producer, schema or execution feature was accepted
by the earlier design. Potential future producer consumption remains conditional
on the assessment; it is not a prerequisite for starting this issue.

## What

Determine how much reliable timeout/cancellation diagnosis GH Run Receptor can
provide from the evidence it already captures or can acquire through existing
read-only mechanisms. Improve the reader and reports where justified. Identify
which remaining distinctions require evidence emitted by a cooperating workflow.

The outcome must separate confirmed source facts, diagnostic hints and unknown
causes, without rewriting GitHub run, job or step conclusions. This is a request
for an independently useful provider capability and assessment, not a prescribed
new Action or an expansion into command execution.

## Consumer evidence and why

uibcdf/molsyssuite#25 coordinates the need to diagnose long tests, Conda builds
and other expensive workflow operations. Its initial recommendation to create a
dedicated producer preceded a demonstrated assessment of the existing reader.
The principal maintainer explicitly changed that order on 2026-10-02.

The existing measured evidence in uibcdf/gh-run-receptor#45 establishes:

- Repository-owned run `34027741137`, with a one-minute job timeout, reported
  the run, job and interrupted step as `cancelled`, not `timed_out`.
- A bounded scan of 889 public repositories found no authentic `timed_out`
  workflow-run fixture; exact synthetic source `timed_out` still passes the
  assessment, renderers and process-status path.
- Cancellation alone does not distinguish an enforced deadline, manual
  cancellation, concurrency replacement, matrix fail-fast or runner loss.

These historical measurements motivate investigation. They do not prove that
all relevant native fields or evidence sources lack the information needed for
better diagnosis in every case.

At inspected source `1f378f2ccd0e8cf8c0d4cbb73431c712611955b1`,
`gh_run_receptor.events` and `gh_run_receptor.bundle` already select bounded
producer artifacts, validate digest/ZIP/JSON and support offline replay.
The strict existing `events@1` accepts `conda.package`, not generic timeout
events. That scope is a compatibility fact, not evidence that a new schema is
necessary. GH Run Receptor 1.0.0 was published on 2026-09-19; implementation
no longer waits for that release milestone.

## Requested investigation and delivery

1. Audit native run, job, step and other available structured evidence through
   the existing acquisition adapter. Record which sources are already captured,
   which can be acquired read-only and which are unavailable or ambiguous.
2. Review bounded logs and existing artifact paths as supplementary evidence.
   Keep untrusted text and command outputs distinct from authoritative source
   facts; do not promote a matching marker to verified causality.
3. Identify and implement reporting/acquisition improvements that current
   evidence actually supports, using reusable owner-local operations and
   preserving existing versioned public contracts.
4. State unknown/ambiguous causes explicitly. Configured `timeout-minutes`,
   elapsed duration, exit 124 or a printed `TIMED_OUT` token alone cannot confirm
   a supervised deadline or change native cancellation into `TIMED_OUT`.
5. Test source preservation, available/unavailable evidence, cancellation
   ambiguity, exact native timeout, hostile markers and bounded outputs with
   sanitized deterministic fixtures. Record actual observed results separately
   from proposed implementation behavior.
6. Return a precise residual evidence requirement to uibcdf/molsyssuite#25 if
   the reader cannot establish a useful distinction from current sources.
   Include the consuming case, why the missing fact matters, what a workflow
   must emit, and reuse or extension options. Do not select a producer owner,
   schema or new component merely because a cause is unknown.

## Acceptance criteria

- A verified capability/limitation assessment names inspected sources and
  concrete evidence, including the measured cancellation example.
- Justified improvements from available evidence have documented contracts and
  relevant source-preserving regression guards, or the assessment demonstrates
  that current reporting is already sufficient for the obtainable facts.
- Reports distinguish confirmed source outcomes, supplementary hints and
  unknown causes. No elapsed-time or spoofable marker inference rewrites source
  conclusions or reports incomplete work as success.
- Any residual producer evidence requirement is concrete and linked back to
  uibcdf/molsyssuite#25, with reuse options and maintenance/compatibility impact.
- Public limitations and this report match the delivered capability. Resolution
  names a relevant durable guard or normative record and archives this report.

## Scope and exclusions

GH Run Receptor owns acquisition, validation, normalization, rendering and
replay improvements. MolSysSuite owns any later interoperability decision,
producer ownership or component admission. This issue begins without a central
producer choice and does not admit a new Action, implement command supervision,
mutate GitHub state, launch scientific suites or publish packages.

Future structured producer consumption may be appropriate after the measured
assessment. An additional serialized contract requires its own explicit version,
compatibility and trust review; the current `events@1` identifier cannot silently
acquire incompatible semantics.

## Provenance

The original report was opened on 2026-09-19 from uibcdf/gh-run-receptor#45 and
uibcdf/molsyssuite#25. The 2026-10-02 redirection follows the principal maintainer's
explicit request to establish provider capabilities and needs before deciding
whether another Action is necessary. The issue is reused to preserve one coherent
timeout-observability theme, rather than opening a duplicate.
