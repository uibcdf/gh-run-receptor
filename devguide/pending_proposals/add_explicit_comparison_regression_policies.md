---
summary: Add explicit comparison regression policies
issue: uibcdf/gh-run-receptor#33
status: open
opened: 2026-09-08
closed:
verification: asserted
area: ['cli', 'reports', 'governance']
guard:
normative:
blocked_by: []
supersedes: []
---

# Adding explicit comparison regression policies

**Reported:** 2026-09-08 after the descriptive comparison and reusable reporter gates.
**Status:** Open; contract and evaluation implementation are in progress.

## What

Allow a user or workflow to evaluate the right-hand candidate against the left-hand
baseline through explicit, versioned rules. Preserve descriptive facts separately from the
policy result and distinguish violation, unknown evidence, and receptor failure.

## How

Add a strict bounded JSON input contract, `comparison-policy@1`, selected with
`compare --policy PATH`. Its opt-in rules cover source identity, required candidate
conclusion, job-duration increase, artifact-size increase, removed job/artifact/matrix
units, and changed matrix state. An absent key imposes no hidden requirement.

Embed a policy result in every `comparison@1`: `NOT_EVALUATED`, `PASS`, `FAIL`, or
`INCOMPLETE`, plus bounded rule-specific violations and unknowns. A policy violation exits
1, evidence insufficient to evaluate a requested rule exits 4, and acquisition/parsing
failure remains 5. Descriptive `CHANGED` without policy continues to exit 0.

## Why

The current comparison can show a 39-second duration increase or removed platform but
cannot decide whether either is unacceptable. Forcing callers to parse presentation text
would recreate the token and correctness problem the receptor exists to solve. This must
land before the next release freezes `comparison@1`, otherwise adding the policy result
would require an avoidable contract v2.

## What is measured and what is assumed

The paired ArgDigest fixtures provide a known 40-to-79-second job-duration change and an
official failure-to-success transition. Existing Conda fixtures expose named platform
coverage. These are deterministic guards; no threshold is claimed as universally useful.

## What was refuted

- Hidden default thresholds are rejected because workflow cost and expected variance are
  project-specific.
- Calling every change a regression is rejected because success transitions and expected
  matrix expansion are changes too.
- Parsing LLM text is rejected because policy belongs on structured evidence.
- Extending frozen `config@1` in place is rejected by the compatibility gate. A dedicated
  policy contract avoids weakening existing workflow-rule readers.
- A missing metric is not a pass or violation; it is an incomplete policy evaluation.

## Scope and exclusions

This increment does not learn statistical baselines, persist histories, choose thresholds,
or apply policies automatically by workflow name. The caller selects a reviewed policy
file explicitly. Producer events and per-job semantic aggregation remain separate work.

## Acceptance criteria

- Policy JSON is bounded, duplicate-key rejecting, non-finite rejecting, schema-identified,
  strict about fields/types, and requires at least one rule.
- Every rule is independently tested for pass, violation, and unknown evidence where
  applicable.
- Policy results validate inside `comparison@1` and render in bounded human/LLM output.
- Exit codes distinguish pass/not-evaluated (0), violation (1), incomplete (4), and
  invalid policy (5).
- Offline and remote comparisons use the same evaluation engine.
- A manual hosted gate evaluates the real ArgDigest paired attempts with both a passing
  and an intentionally failing threshold without making the workflow itself fail early.

## Dependencies and risks

No tracked dependency blocks this change. It extends only contracts introduced after
0.18.0; the four frozen schema resources remain byte-identical.

## Provenance

Initial design: Linux host, Python 3.13.14, commit `d2ed809`, 2026-09-08. Final local and
hosted provenance will be added before closure.
