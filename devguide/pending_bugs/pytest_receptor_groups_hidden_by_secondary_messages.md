---
summary: Retain failed pytest-receptor groups ahead of warnings or generic exits.
issue: uibcdf/gh-run-receptor#66
status: active
opened: 2026-10-24
closed:
severity: medium
verification: reproduced
area: [profiles, reports]
guard: tests/test_diagnostic_ranking.py
normative: diagnostic_selection.md
blocked_by: []
supersedes: []
---

# Retain failed pytest-receptor groups ahead of warnings or generic exits

## Original observations

- `uibcdf/dockingmt` run [38037422889](https://github.com/uibcdf/dockingmt/actions/runs/38037422889), attempt 1, source `bbf539cd533b703028029956fc06d52075b03c1c`: 4 failed jobs among 7; expected bounded diagnostic `ArgumentError: Invalid argument`.
- `uibcdf/sabueso` run [40013378053](https://github.com/uibcdf/sabueso/actions/runs/40013378053), attempt 1, source `646ce84bfb14da6e5ec86bbeef1693ac5f41e1fe`: 4 failed jobs among 15; expected bounded diagnostic `NotADirectoryError: [WinError 267]`.

Fresh read-only captures of the exact original attempts are complete on 2026-10-24.
The six original cases collectively fail the new semantic regression on the
previous source; all pass after the shared log parser correction. Selected
sanitized excerpts in `tests/fixtures/logs/diagnostic_ranking.json` preserve every
represented API job/step conclusion and each original archive member/physical
line. They are diagnostic projections, not full evidence bundles or release
qualification. Raw captures are task-owned and never committed.

## Correction and contract

The owning reusable operation is `gh_run_receptor.logs.extract_causes`; every
profile and entry point already calls it. No consumer-specific parser or runtime
dependency is added. [Diagnostic selection](../diagnostic_selection.md) owns the
bounded recognition, optional source-linked context, authority and fallback rules.
The regression asserts the actual selected diagnostic, all represented native
job conclusions, exit 1, original locators, deterministic replay and text bounds.
Human/LLM goldens supplement those independent semantic assertions. Malformed,
truncated, unknown, orphaned, ANSI, secret and exact size/window controls protect
conservative degradation. Native exact-source gates and original-bundle CLI
replay are still required before closure. Public release behavior is not changed
until a later separately qualified publication.

## Local source verification

Full Linux/Python 3.14.7 source suite: **707 passed**, one explicit Conda-installed-
only skip. Ruff lint/format, 27-route distribution preflight, all nine frozen
contracts and developer-report lifecycle pass. All six complete original-attempt
bundles also pass independent CLI replay twice in generic/CI × human/LLM/JSON
modes, preserving every native job conclusion, original diagnostic and exit 1.
The bounded receipt is `devguide/evidence/diagnostic_ranking_2026-10-24.json`.

The shared environment retains the seven external dependency conflicts already
reported in `uibcdf/molsyssuite#82`; no dependency was changed here. Local strict
Sphinx cannot start without its optional theme; hosted exact-source docs and
native matrix remain pending. Local unit/replay evidence does not certify the
entire shared environment, another OS or any published package.
