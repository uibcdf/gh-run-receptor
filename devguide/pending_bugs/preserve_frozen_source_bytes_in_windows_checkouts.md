---
summary: Preserve frozen source bytes in Windows checkouts.
issue: uibcdf/gh-run-receptor#69
status: active
opened: 2026-10-24
closed:
severity: high
verification: reproduced
area: [packaging, tests]
guard: tests/test_conda_distribution.py
normative:
blocked_by: []
supersedes: []
---

# Frozen-byte preflight fails before the Windows suite

## Evidence and mechanism

Weekly runs [38399664848](https://github.com/uibcdf/gh-run-receptor/actions/runs/38399664848)
and [39405755361](https://github.com/uibcdf/gh-run-receptor/actions/runs/39405755361)
at source `d2551b272541bafe54f784f2d1ace38af5490d83` fail all four Windows
Python 3.11--3.14 cells at `Check distribution inputs`; the suite is skipped.
Eight Linux/macOS cells pass. The original Windows diagnostic is
`Frozen schema digest differs: aggregate-v1.schema.json`.

A real isolated Git checkout with `core.autocrlf=true` reproduces the schema
conversion from LF to CRLF and fails the new regression before the repair.
The existing attributes protected fixtures only. Both frozen schemas and
reviewed workflow hashes require original LF bytes, so both now have explicit
LF checkout attributes. Schema files, historical tags and recorded digests are
unchanged; byte guards still reject even one extra newline.

## Existing provider correction

The old distribution SDK also discovers native Windows paths with backslashes.
The accepted optional correction announced in `uibcdf/molsyssuite#112` is
`6d6172d6cd00c5ac2d4ebadb71df554ec5b7fa26`, replacing
`38db709ecc07451ff36ea84573d585f9af6b4df7` in the seven related workflows and
inventory. Source review confirms POSIX relative identities, backward-compatible
@2 input handling and retained exact workflow hashes/external executable bounds.
The provider's other added context and installed-import tools are not a new
consumer mode. Changed workflow digests were refreshed after this pin-only review.
No shared provider source was copied or changed.

## Measured validation and limits

On Linux/Python 3.14.7, the real checkout regression fails before attributes are
added and passes afterward, with a CRLF control proving conversion is enabled.
All sixteen focused distribution cases pass; the one Conda-installed-only case
skips because no Conda archive is installed. The pinned SDK wrapper accepts all
27 routes and all nine historical frozen contracts. The full local suite passes
648 tests with that same explicit installed-only skip; Ruff lint and format pass.
Native Windows recovery
must still be executed; local simulated checkout is not native matrix evidence.
No release, tag, package build, upload or installed-artifact qualification is
performed by this fix. Temporary SDK checkout is task-owned under
`/tmp/ghrr-issues-20261024-cZ6igZ` and retained until verification ends.

## Acceptance

Retain byte-level rejection, pass actual native Windows preflight and suite on
all four supported Python minors, and preserve ordinary Linux/macOS gates.
Archive this report only after the exact-source native matrix is inspected.

The owning assertion is `test_windows_checkout_preserves_frozen_schema_and_reviewed_workflow_bytes`; it runs a real CRLF-enabled Git checkout and compares every frozen schema and reviewed workflow with its original bytes.

## Native execution exposed a second portability defect

Exact-source weekly run `40121815534` at `c18e9b531fa4d21128b82ad60db57045d7ef0c38`
passes preflight on all twelve cells and the full suite on eight Linux/macOS
cells. All four Windows suites now execute and expose one archive-path test
failure: the wheel writer and reader normalize a raw backslash through ZipInfo.
The reader now validates `orig_filename` before trusting its normalized spelling;
the negative fixture deliberately preserves the original filename bytes when
writing. The archive rejection contract is retained, not relaxed to accept a
metadata failure. `tests/test_release_tools.py` guards the original unsafe names
for both wheel and sdist. An initial writer adjustment accidentally disabled
compression and failed the existing compressed-size negative control locally;
explicit DEFLATE preserves that control without relaxing its bound. A new exact-source
native matrix is still required before closure. This failed first matrix remains
failed evidence and is not replaced by a local pass.
