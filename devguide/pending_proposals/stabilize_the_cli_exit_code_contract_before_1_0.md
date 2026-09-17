---
summary: Stabilize the CLI exit-code contract before 1.0
issue: uibcdf/gh-run-receptor#39
status: active
opened: 2026-09-17
closed:
verification: measured
area: ['cli']
guard:
normative:
blocked_by: []
supersedes: []
---

# Stabilizing the CLI exit-code contract before 1.0

**Reported:** 2026-09-17, while selecting the next evidence gate after publishing 0.21.0.
**Status:** Active; the documented map is coherent, but its usage-error boundary is not
implemented and the complete command surface has no single executable contract.

## What

Freeze one non-overlapping exit-code map before CLI 1.0 and make every command use named
internal constants. The current documentation assigns 64 to invalid CLI usage, but the
ordinary `argparse.ArgumentParser` exits with 2. Code 2 is also the documented product
result for cancelled, timed-out, stale, action-required, or other terminal non-success
runs. A shell caller therefore cannot distinguish malformed invocation from valid run
evidence by status alone.

The stable map should remain 0 success, 1 known failure or policy violation, 2 other
terminal non-success, 3 active work, 4 insufficient evidence, 5 receptor error, 64 usage
error, and 130 interruption. Command-specific semantics remain explicit: a complete
`capture` returns 0 even when the captured run failed, while `compare` returns 0 for a
complete descriptive difference unless an opted-in policy fails.

## How

Add a private exit-code module so report, comparison, aggregation, capture, Action, and CLI
boundaries cannot drift through repeated integer literals. Use a small
`ArgumentParser` subclass whose `error()` prints normal argparse diagnostics and exits 64;
help and version retain 0. Do not remap arbitrary `SystemExit`, because dependency or
programming errors must not be mislabeled as usage.

Add exhaustive unit truth tables and a manually dispatched hosted gate that invokes the
real console boundary for success, failure, terminal non-success, incomplete evidence,
receptor error, and usage error. Pending and interruption remain deterministic unit cases;
the existing live same-run Action evidence independently covers active-run reporting.
Only after local and hosted checks agree should the guide replace “preliminary” with
“stable” and OD-006 become settled.

## Why

Exit status is the cheapest automation surface and may be consumed without parsing stdout.
A collision at that boundary can cause a CI script or agent to treat its own invalid
invocation as an authoritative GitHub outcome. Centralization also prevents the newer
`compare` and `aggregate` commands from silently diverging before 1.0.

## What is measured and what is assumed

Measured from commit `9f454ea`:

```text
./gh-run-receptor invalid-command >/tmp/ghrr-invalid.out 2>/tmp/ghrr-invalid.err
./gh-run-receptor inspect not-a-run >/tmp/ghrr-invalid-run.out 2>/tmp/ghrr-invalid-run.err
```

Both commands return 2 and print an argparse usage diagnostic. `cli_and_output_contract.md`
and the synchronized consumer guide both assign that case to 64. Inspection also finds
literal return values distributed across `cli.py`, `report.py`, `comparison.py`, and
`embedded.py`; aggregation has its own correct truth table but no shared symbolic map.

The design assumes shell callers benefit from stable categories. The hosted gate will
test the observable process status rather than only calling Python helpers.

## What was refuted

- Retaining argparse's 2 was rejected because it collides with a valid terminal run result.
- Changing terminal non-success to a new number was rejected because code 2 is already
  documented and exercised by cancelled-run fixtures.
- Treating every nonzero result as 1 was rejected because it destroys the product's
  deliberate distinction between source failure, active work, incomplete evidence, and
  receptor failure.
- Freezing only prose was rejected because the observed implementation already disagrees
  with it.

## Scope and exclusions

This work does not change assessment meanings, GitHub source facts, Action fail-open
semantics, mutation policy, or the JSON contracts. It does not add a serialized
`exit-codes@1` resource: process exit status is a CLI compatibility contract governed by
the normative CLI document and executable tests.

## Acceptance criteria

- Every documented status has a named internal constant and distinct integer value.
- Invalid command, argument, and missing-command cases exit 64; help and version exit 0.
- Replay fixtures exercise 0, 1, 2, and 4 through the real CLI process boundary.
- Missing or malformed input exits 5 without being mislabeled as usage.
- Pending returns 3 and interruption returns 130 in deterministic unit tests.
- `capture`, `compare`, `aggregate`, and embedded Action special semantics remain covered.
- A hosted exact-revision gate executes the stable public console surface.
- The CLI contract, consumer guide, open-decision record, and checkpoint agree.

## Dependencies and risks

No external dependency blocks this work. The main risk is accidentally changing Action
fail-open behavior while centralizing constants; existing embedded tests and the full
suite must guard it. The other risk is catching a broad `SystemExit` and turning internal
errors into usage errors; the parser subclass avoids that design.

## Provenance

Measured 2026-09-17 on Linux 7.0.0-28-generic x86_64 with Python 3.13.14 and the
checkout-local 0.21.0 code plus post-release documentation commits.
