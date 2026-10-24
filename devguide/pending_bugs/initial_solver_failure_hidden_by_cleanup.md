---
summary: Retain direct libmamba constraints ahead of cleanup failures.
issue: uibcdf/gh-run-receptor#61
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

# Retain direct libmamba constraints ahead of cleanup failures

## Original observations

- `uibcdf/molsysviewer` run [37538525423](https://github.com/uibcdf/molsysviewer/actions/runs/37538525423), attempt 1, source `6c4ddba31c289a27f761576c07fa641603c4392e`: 7 failed jobs among 9; expected bounded diagnostic `molsysmt >=0.23.0`.

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

## First native candidate and fixture encoding

Source `3d39896dbc426b8e35b3c508eef88cc7568c19a2` passes ordinary routine,
policy, Conda governance and strict hosted docs/Pages gates. Weekly matrix
`40123972682` passes eight Linux/macOS cells; Windows executes 705 passing cases
but fails the two long-message goldens because fixture loading used the locale
encoding for a UTF-8 ellipsis. Both input and golden JSON readers now explicitly
use UTF-8. The existing owning cases also pass with UTF-8 mode and locale coercion
disabled under an ASCII locale. No expected output, source parser, diagnostic,
assertion or bound is changed to accommodate Windows. A new exact-source native
matrix remains required; the first matrix stays recorded as failed.
