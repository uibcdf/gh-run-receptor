---
summary: Name failed pytest tests instead of the runner exit epilogue
issue: uibcdf/gh-run-receptor#50
status: resolved
opened: 2026-09-21
closed: 2026-09-21
severity: medium
verification: reproduced
area: [logs, testing, ci]
guard: tests/test_report.py
normative:
blocked_by: []
supersedes: []
---

# Name failed pytest tests instead of the runner exit epilogue

**Reported:** 2026-09-21 from `uibcdf/ackredit` CI run `35572056510`.

## What

The compact CI report correctly retained GitHub's failed conclusion but called
`Process completed with exit code 1.` the root cause. The same log contained
`FAILED tests/test_pdf.py::test_pdf_compilation - AssertionError: assert False` four
lines earlier. The reader had to inspect raw logs to learn which test failed.

The first SMonitor Python 3.14 candidate matrix, run `35580019186`, reproduced the
problem with pytest-receptor output: one Windows Python 3.12 test failed, and the
receptor report again selected the generic runner exit line. The log's compact pytest
output named `tests/test_core.py::test_frame_time_is_iso_utc_in_emitted_context` in a
`rerun:` line.

## How

The log analyzer recognized generic runner exits but not pytest's `FAILED` summary
or pytest-receptor's `FAIL exit=...` plus `rerun:` form. Its structured-workflow
diagnostic rule requires a `name:` prefix immediately before the exit marker, which
neither pytest format supplies.

The repair recognizes an anchored pytest `FAILED <nodeid> - <reason>` line and an
anchored pytest-receptor failing verdict followed within 128 log lines by its
`rerun: pytest <nodeid>` line. It retains only the named test as a bounded,
credential-redacted log *inference*, normalizes Windows path separators, and leaves
GitHub's status, conclusion, and exit code authoritative. A standalone `rerun:` line
or one outside the bounded verdict window cannot replace the runner epilogue.

## Why this choice

Reading a `pytest-receptor.events@1` artifact would be more structured, but it is
opt-in on the producer side and neither failing run published one. Artifact support
alone would not repair these existing workflows. The bounded stdout recognition is
therefore the immediate interoperable path. Artifact ingestion remains separate
future work and must apply archive, source-identity, integrity, and size checks before
it can claim a stronger evidence level.

## Evidence and verification

- Before the change, `inspect` selected the exit epilogue on both runs.
- With the source checkout, `inspect 35572056510 --repo uibcdf/ackredit --profile ci`
  named `tests/test_pdf.py::test_pdf_compilation` at log line 861 while retaining
  `FAIL conclusion=failure` and process status 1.
- Offline replay of the captured SMonitor run named the frame-time test at log line
  582 and likewise retained the authoritative failure.
- `python -m pytest tests/test_logs.py tests/test_report.py -n 12 --receptor=llm`:
  53 passed. The full local suite passed 451 tests with twelve workers.
- Ruff lint and format checks passed, and `validate_devguide.py` accepted the report.

Only compact outputs are quoted here. Raw GitHub log archives remain under `/tmp` and
are not committed.

## Scope and exclusions

This does not ingest pytest-receptor JSONL artifacts, promise every test runner format,
or turn log text into an authoritative verdict. Unrecognized, malformed, or too-distant
diagnostics keep the existing generic fallback and native inspection escape hatch.

## Acceptance criteria

- Both observed failing jobs name the corresponding failed test in compact output.
- Plain pytest and pytest-receptor examples have deterministic regression tests.
- False-positive, window-boundary, redaction, and line-size cases remain covered.
- The full local suite, Ruff, devguide validator, and report-size guards pass.

## Provenance

Run IDs above are public UIBCDF Actions runs, inspected on 2026-09-21 from the local
Linux development host with the source checkout on Python 3.13. No raw run data is
retained in the repository.

## Resolution

The log extractor now selects a named pytest test over a generic runner exit in the
two observed formats. The integration guard asserts that a compact CI report names the
test while retaining GitHub's official failure and process exit status 1. Unit tests
also protect the bounded verdict window, redaction, generic fallback, and original
structured-diagnostic precedence. Both original runs were replayed or inspected using
the changed checkout; their source failures remained unchanged.
