---
summary: Preserve failed-step and process-exit evidence after positive output.
issue: uibcdf/gh-run-receptor#56
status: resolved
opened: 2026-10-01
closed: 2026-10-02
severity: medium
verification: reproduced
area: [reports, security]
guard: tests/test_report.py
normative:
blocked_by: []
supersedes: []
---

# Positive output selected after a silent failure

## What and why

MolSysViewer run `36920527376`, attempt 1, reports three failed Python 3.14
jobs in `Validate and locally tag the exact Viewer source candidate`.
GH Run Receptor 1.1.1 preserved GitHub's failure but selected
`Python wheel runtime contract: PASS (source, 0.23.4)` as its only cause.
The consumer's native inspection found that a later silent shell assertion
failed. The positive line describes the preceding successful command.

## Reproduction and mechanism

The adjacent structured-diagnostic allow-list included `PASS`, with priority
20 over the generic process-exit marker's priority 10. Consequently a successful
command immediately before a silent failure displaced the only failure evidence.
The two-line sanitized regression excerpt retains the positive validator output
and exit-1 epilogue. Case variants reproduce the same mechanism. A report-level
fixture repeats the excerpt for three jobs and retains the exact failed step.

Before the fix, the focused regression command produced four failed tests and
one pass on Python 3.13.14. No workflow source, shell assertion or printed
command is executed by these tests.

## Resolution boundary

Exclude `PASS` from adjacent diagnostic recognition. Keep negative structured
diagnostics, specific exceptions and solver evidence under their existing bounds.
When a command fails silently, retain the process-exit marker and the API's failed
step without guessing the command or assertion that caused it. If no failure
diagnostic exists, preserve the existing unknown-cause warning.

Acceptance requires the original source failure and exit 1 to survive all three
renderers; no positive validator output may appear as causal evidence; equivalent
job occurrences must still group; and output must remain bounded. No serialized
schema, version, acquisition policy or authentication boundary changes.

## Evidence and validation

Source issue: `uibcdf/gh-run-receptor#56`, reported by consumer
`uibcdf/molsysviewer` on 2026-10-01. Original source commit:
`518728496525cc36c2b42afb92371432b75f1bcf`.
The regression excerpt is `tests/fixtures/logs/molsysviewer_36920527376_silent_failure.txt`;
it retains only the two diagnostic lines and no credentials or private data.
Fresh full capture of the original public run completed successfully and retained
120,792 bytes locally under `/tmp`, without committing raw evidence. Independent
bounded inspection verified this exact two-line excerpt in all three top-level job
logs. Replay with the corrected reader groups three exit-1 occurrences, retains
the exact failed step and source conclusion, and returns exit 1. Human and LLM
outputs remain below 10,000 bytes and JSON below the shared 8 MiB publication bound.

Local validation on 2026-10-02, Python 3.13.14: 65 focused log/report tests passed;
the full suite passed 470 tests with `python -m pytest --receptor=llm`;
Ruff lint and format, devguide lifecycle, all nine frozen contracts against
0.21.0, and `git diff --check` passed. The named report guard independently checks
source failure, exit status, step identity, all renderers, grouping and output
bounds in `test_positive_verdict_is_not_the_cause_of_a_failed_ci_step`.
The module selector remains addressable by both pytest and the local lifecycle
validator. This is a source correction, not a claim of a newly published release.
