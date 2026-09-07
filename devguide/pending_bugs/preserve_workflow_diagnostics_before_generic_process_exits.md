---
summary: Preserve workflow diagnostics before generic process exits
issue: uibcdf/gh-run-receptor#29
status: active
opened: 2026-09-07
closed:
severity: medium
verification: asserted
area: ['reports']
guard:
normative:
blocked_by: []
supersedes: []
---

# Preserving workflow diagnostics before generic process exits

**Reported:** 2026-09-07 from the first hosted Zenodo verification run.
**Status:** Active; the live defect is reproduced and a conservative extraction rule is
being implemented.

## What

Adaptive inspection of run `34159750417` reports only `Process completed with exit code
2.` even though the immediately preceding workflow diagnostic is `Zenodo archive: ABSENT
— 0.18.0`. A native failed-log query is currently required to learn why the command chose
exit 2.

## How

`logs._candidate()` intentionally ranks the generic runner exit at the lowest priority,
but the preceding application line does not match an error keyword and never becomes a
candidate. Preserve an immediately adjacent structured verdict line only when it has a
bounded label and an explicit state such as `FAIL`, `ABSENT`, `INVALID`, or `UNAVAILABLE`.
Explicit errors remain higher priority. Redact credential-shaped content and bound the
stored diagnostic before it enters JSON or text rendering.

## Why

Many well-designed tools emit a concise final diagnostic and then return a meaningful
nonzero code. Dropping that line forces agents and humans back to raw logs, losing both
diagnostic quality and the token reduction that motivates the receptor.

## What is measured and what is assumed

The hosted run completed in eight seconds with one failed job. Adaptive receptor output
identified the correct job, step, and exit code but not `ABSENT`. The following native
query exposed both adjacent lines:

```text
gh run view 34159750417 --repo uibcdf/gh-run-receptor --log-failed
Zenodo archive: ABSENT — 0.18.0
##[error]Process completed with exit code 2.
```

## What was refuted

- Treating every line before a process exit as causal is rejected because it can expose
  arbitrary command output and secrets.
- Giving structured diagnostics precedence over concrete import, missing-file, fatal, or
  explicit GitHub errors is rejected because those lines are stronger causes.
- Special-casing Zenodo text is rejected; the rule must describe a general workflow
  diagnostic shape.

## Scope and exclusions

This change does not attempt natural-language log summarization, infer meaning from any
arbitrary preceding line, or claim that pattern redaction can replace GitHub secret
masking. It only improves the bounded deterministic cause selector.

## Acceptance criteria

- The reproduced `ABSENT` diagnostic outranks its adjacent generic exit marker.
- Stronger explicit causal lines continue to win.
- An ordinary arbitrary line before an exit marker is ignored.
- Credential-shaped assignments and GitHub tokens are redacted from stored causes.
- Candidate messages are bounded before JSON rendering.
- Existing grouping, archive-safety, and line-number behavior remain stable.

## Dependencies and risks

There are no external dependencies. Over-broad matching or inadequate redaction would
increase disclosure risk, so adversarial negative fixtures are part of the guard.

## Provenance

Reproduced on 2026-09-07 with gh-run-receptor commit `d0b72af`, Python 3.13.14, GitHub CLI
2.93.0, hosted run `34159750417`, and its downloaded failed-job archive.

## Implementation checkpoint

The extractor now admits only an immediately adjacent, label-bounded structured state as a
candidate above the generic exit marker and below every concrete error class. All selected
causes are credential-redacted and bounded to 500 characters before report storage.
Focused tests cover the live `ABSENT` shape, arbitrary adjacent text, stronger explicit
errors, GitHub-token and password redaction, and bounding. Reinspection of run
`34159750417` now reports `Zenodo archive: ABSENT — 0.18.0` directly with its original
member and line provenance.
