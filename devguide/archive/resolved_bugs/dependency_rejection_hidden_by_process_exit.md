---
summary: Retain explicit preflight rejection across bounded blank lines.
issue: uibcdf/gh-run-receptor#64
status: resolved
opened: 2026-10-24
closed: 2026-10-24
severity: medium
verification: reproduced
area: [profiles, reports]
guard: tests/test_diagnostic_ranking.py
normative: diagnostic_selection.md
blocked_by: []
supersedes: []
---

# Retain explicit preflight rejection across bounded blank lines

## Original observations

- `uibcdf/smonitor` run [37994715796](https://github.com/uibcdf/smonitor/actions/runs/37994715796), attempt 1, source `b16b032c0d9ea177307f12991ca96d9fc6c956b8`: 4 failed jobs among 13; expected bounded diagnostic `Dependency routes rejected:`.

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
dependency is added. [Diagnostic selection](../../diagnostic_selection.md) owns the
bounded recognition, optional source-linked context, authority and fallback rules.
The regression asserts the actual selected diagnostic, all represented native
job conclusions, exit 1, original locators, deterministic replay and text bounds.
Human/LLM goldens supplement those independent semantic assertions. Malformed,
truncated, unknown, orphaned, ANSI, secret and exact size/window controls protect
conservative degradation. Native exact-source gates and original-bundle CLI
replay form the closure gate recorded below. Public release behavior is not changed
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
Sphinx cannot start without its optional theme; its separate hosted build and
native receiving gates were pending at this local checkpoint. Local unit/replay evidence does not certify the
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

## Resolved source delivery

Source `754410e46eb9fb6704b0c960fe129b803f06efa7` passes the complete
[twelve-cell native matrix](https://github.com/uibcdf/gh-run-receptor/actions/runs/40124573976)
with 707 tests and the one explicit Conda-installed-only skip in each cell.
Every native preflight and complete-suite step executes successfully.
Exact-source routine `40124525987`, policy `40124526200`, Conda governance
`40124526278` and strict docs/build/Pages `40124749130` also pass. Run SHA,
attempt, workflow path, job states and mandatory executed steps were checked
against structured GitHub API evidence. The bounded hosted receipt is
`devguide/evidence/diagnostic_ranking_hosted_2026-10-24.json`.

The owning guard `test_original_public_diagnostics_outrank_secondary_messages`
would reintroduce this issue by selecting the original secondary diagnostic;
API-parity, exact original locators, context and text/size goldens are checked
separately. Earlier failed candidates remain failed. All nine schema resources,
process-status rules and the read-only boundary are preserved.

Consumer impact was handed off before any new package publication through
`uibcdf/molsyssuite#136`, linking registered consumers and MOLI/Sabueso evidence.
No new public release, installed-file qualification, consumer pin or guide-copy
synchronization is claimed. Existing public pins may stay unchanged. Shared
workspace dependency conflicts remain owned by the existing central #82 report.
