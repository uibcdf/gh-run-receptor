---
summary: Prove replay byte determinism across temporal and filesystem contexts
issue: uibcdf/gh-run-receptor#43
status: resolved
opened: 2026-09-19
closed: 2026-09-19
verification: measured
area: ['tests']
guard: tests/test_cli.py
normative:
blocked_by: []
supersedes: []
---

# Proving replay byte determinism across temporal and filesystem contexts

**Reported:** 2026-09-19 while selecting the next actionable 1.0 evidence gap after the
0.22.0 release.
**Status:** Resolved; the adversarial local and nine-combination hosted gates pass.

## What

Close the remaining byte-identical replay timing gap with a local CLI test that proves
equal semantic evidence produces equal output bytes independently of wall-clock-related
and filesystem context.

The product already promises deterministic replay. The missing work is evidence strength,
not a known output defect.

## How

Run the real `python -m gh_run_receptor replay` process over two copies of one reviewed,
nontrivial sanitized bundle. Deliberately vary:

- bundle directory names;
- file modification times;
- manifest capture timestamps;
- `TZ` and `SOURCE_DATE_EPOCH` environment values;
- JSON, LLM, and human rendering modes.

Require the two processes to return the same semantic exit status, empty stderr, and
byte-identical stdout in every rendering mode. Use source timestamps retained in the
bundle for durations; never derive report facts from the current clock, file metadata, or
local timezone.

The complete compatibility workflow already runs the full suite on Ubuntu, macOS, and
Windows with Python 3.11, 3.12, and 3.13, so an exact-revision dispatch will provide the
hosted cross-platform evidence without adding a second workflow.

## Why

The roadmap withholds one percentage point from Phase 1 for byte-identical replay timing.
The current implementation appears to satisfy the property, but a same-object unit repeat
does not prove the CLI boundary and an immediate same-path process repeat does not challenge
temporal or filesystem leakage. Closing the gap requires a guard that would fail if a
future renderer included `datetime.now()`, local timezone conversion, file modification
time, or the bundle path.

## What is measured and what is assumed

Inspection on 2026-09-19 found:

- `tests/test_contracts.py::test_replay_is_byte_deterministic_for_fixed_evidence` builds
  the same report twice from one in-memory manifest/evidence pair;
- `devtools/scripts/validate_public_runs.py` invokes JSON replay twice as separate
  processes, but immediately, at the same path and under the same environment;
- report construction imports no current-clock function and the bundle directory is used
  only to open retained log evidence;
- capture writes `captured_at` with `datetime.now(UTC)`, while replay treats that field as
  provenance and does not serialize it into the report.

These observations were obtained with:

```text
rg -n "replay|captured_at|datetime|now\\(|bundle_directory" gh_run_receptor tests devtools
pytest --receptor=llm
```

The implemented guard parametrizes JSON, LLM, and human rendering. Its two subprocesses
use distinct nested paths, file modification times, capture timestamps, POSIX timezone
strings, and `SOURCE_DATE_EPOCH` values. All three cases returned the expected source
failure status 1, empty stderr, and byte-identical stdout.

Local validation passed:

```text
pytest --receptor=llm
PASS exit=0 | 437 passed | 4.68s

ruff check .
All checks passed!

python devtools/scripts/validate_contracts.py --baseline 0.21.0
Contract compatibility: PASS — contracts=9 frozen=9 baseline=0.21.0

python devtools/scripts/validate_devguide.py
Developer report lifecycle is valid.

sphinx-build -W --keep-going -b html docs docs/_build/html
build succeeded.
```

Exact-revision compatibility run `35437166644` passed at commit
`540015b78eea288e4a0233d9469244d24928e51a`. All nine Ubuntu, macOS, and Windows jobs with
Python 3.11, 3.12, and 3.13 completed successfully and therefore exercised the same
subprocess byte-comparison guard through both the source suite and installed-wheel smoke
path.

## What was refuted

- Changing report schemas is rejected because no volatile field is part of the current
  serialized report contract.
- Sleeping between two commands is rejected because it is slow and only challenges the
  clock at one unknown resolution.
- Adding a clock-mocking dependency is rejected because subprocess environments and
  divergent retained timestamps exercise the boundary without a runtime or test dependency.
- Treating the existing same-object repeat as sufficient is rejected because it bypasses
  argument parsing, bundle loading, process initialization, and environment handling.

## Scope and exclusions

This work does not change capture identity, duration semantics, schemas, profile output,
or the authentic-`timed_out` corpus gap. It does not claim byte equality across different
gh-run-receptor versions; compatibility across contract versions remains governed by the
migration policy.

## Acceptance criteria

- A real subprocess test varies path, file times, capture time, timezone, and source date.
- JSON, LLM, and human stdout remain byte-identical for equal semantic evidence.
- Exit status and stderr remain identical.
- The complete local suite, Ruff, contracts, devguide validation, and strict documentation
  build pass.
- The nine-combination compatibility workflow passes at the exact implementation commit.
- Phase 1 receives its final evidenced percentage point only after those checks pass.

## Dependencies and risks

There are no tracked dependencies. Platform-specific timezone availability is a test
portability risk; use POSIX `TZ` strings accepted by Python's runtime rather than assuming
an optional named-zone database.

## Provenance

Initial inspection ran on 2026-09-19 from the MolSysSuite development environment on
Linux with Python 3.13.14 and pytest 8.4.2. The repository was clean at
`0ceef84335be3f3f6fca5684c4190e77c7a3d1a5`, immediately after the verified 0.22.0
rollout checkpoint. Focused implementation validation ran three subprocess cases in
0.83 seconds; the complete local suite then passed 437 tests in 4.68 seconds.
