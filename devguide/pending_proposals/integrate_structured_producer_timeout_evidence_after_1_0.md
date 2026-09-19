---
summary: Integrate structured producer timeout evidence after 1.0
issue: uibcdf/gh-run-receptor#46
status: blocked
opened: 2026-09-19
closed:
verification: measured
area: ['github', 'profiles']
guard:
normative:
blocked_by: [uibcdf/molsyssuite#25]
supersedes: []
---

# Integrating structured producer timeout evidence after 1.0

**Reported:** 2026-09-19, after issue #45 closed the native `timed_out` evidence gate and
identified a separate producer-observability opportunity.
**Status:** Blocked until gh-run-receptor 1.0 is published and
`uibcdf/molsyssuite#25` selects the producer's ownership and contract direction.

Remove `severity` for proposals. The directory identifies the report kind.

## What

Track the gh-run-receptor side of a future structured operation-timeout producer. The
central proposal `uibcdf/molsyssuite#25` evaluates whether that producer should be an
existing-Action integration, a new small Action, or functionality owned elsewhere.
gh-run-receptor's role would be to consume and report the versioned event without
replacing GitHub's authoritative run, job, or step conclusion.

## How

After 1.0 and central acceptance, add a dedicated source-bound evidence path modeled on
the existing producer-event safeguards: exact repository, run, attempt, job, producer,
artifact name, digest, schema, and size identity; bounded parsing; explicit incomplete and
contradictory states; and deterministic offline replay.

The report vocabulary must distinguish the two layers:

```text
CANCELLED source | producer_timeout operation=tests limit=20m
```

`TIMED_OUT` remains available only when GitHub supplies the exact source conclusion.
Neither elapsed time, `timeout-minutes`, a job name, nor a printed marker may produce it.
The future event may use a provisional name such as `producer-outcome@1`; this issue does
not reserve that schema name before the central design is accepted.

## Why

Developers arriving in this repository need one visible route for the timeout
observability gap. Without it, the absence of an authentic `timed_out` fixture can invite
ad hoc log parsing or reclassification of ordinary GitHub cancellation. Linking the
post-1.0 design now preserves the read-only 1.0 scope while preventing that historical
context from being lost.

Structured producer evidence would also let gh-run-receptor serve long scientific tests,
Conda builds, documentation jobs, and community workflows with a more useful diagnosis
than source cancellation alone.

## What is measured and what is assumed

Issue #45 records two measurements: a standard one-minute Actions job timeout produced
`cancelled`, and a later authenticated scan of 889 public repositories returned zero
errors and zero `status=timed_out` runs. The exact synthetic source value nevertheless
passes normalization, assessment, human/LLM rendering, and process status 2 in 440 local
tests.

The existing `events@1` path proves that bounded producer artifacts can be tied to source
identity and consumed offline. Reuse of that schema is not assumed: a generic operation
outcome has different semantics from the current Conda platform event and requires an
explicit compatibility decision.

## What was refuted

- Printed `TIMED_OUT` log markers are rejected as authoritative evidence because logs are
  untrusted and spoofable.
- Inferring timeout from duration or `timeout-minutes` is rejected because the measured
  GitHub conclusion is cancellation and cancellation has several causes.
- A write-capable GitHub App is not assumed to solve the workflow-run case. It can create
  check-level conclusions but adds a distinct mutation and credential boundary.
- Implementing a producer inside gh-run-receptor before 1.0 is rejected because the 1.0
  product boundary is a stable read-only consumer.

## Scope and exclusions

This report covers only gh-run-receptor consumption, validation, rendering, and replay of
an accepted future producer contract. Producer ownership, component admission, execution,
process-tree termination, and suite-wide pilots belong to `uibcdf/molsyssuite#25` and its
future implementation issue.

It excludes native GitHub state mutation, whole-workflow cancellation, log inference, and
evidence recovery after a runner is killed before publication.

## Acceptance criteria

- gh-run-receptor 1.0 is published and `uibcdf/molsyssuite#25` accepts an owner and event
  contract before this report becomes active.
- The consumer verifies source and producer identity, schema, digest, bounds, and
  completeness independently.
- Contradictory, duplicated, malformed, untrusted-PR, missing, and oversized events fail
  closed without hiding GitHub source truth.
- JSON, human, and LLM reports use a distinct `producer_timeout`-style fact and never
  upgrade it to GitHub `TIMED_OUT`.
- Offline fixtures cover success, producer timeout, ordinary failure, missing publication,
  source cancellation, and hostile artifact cases.
- Hosted Linux, macOS, and Windows pilots preserve exact run/attempt/job identity.
- Public documentation names the producer assertion, trust boundary, native fallback,
  and cases where abrupt runner termination prevents evidence.

## Dependencies and risks

The design is blocked by `uibcdf/molsyssuite#25`; implementation is additionally scheduled
after the 1.0 release milestone. Risks include coupling the consumer to one Action,
accepting a producer assertion as external truth, schema overlap with `events@1`, artifact
substitution, pull-request self-attestation, and adding unbounded output or downloads.

## Provenance

Opened on 2026-09-19 from the outcome evidence work archived by
`uibcdf/gh-run-receptor#45` and the central project proposal
`uibcdf/molsyssuite#25`. No production behavior, schema, workflow, permission, or
dependency changed.
