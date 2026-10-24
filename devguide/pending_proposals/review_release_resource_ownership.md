---
summary: Review release resource ownership while retaining the broader lifecycle follow-up.
issue: uibcdf/gh-run-receptor#65
status: partial
opened: 2026-10-24
closed:
verification: inspected
area: [governance, packaging]
guard:
normative: resource_lifecycle_review.md
blocked_by: []
supersedes: []
---

# Scoped release resource review

The incoming owner review is broader than one release and reports missing review
evidence, not a reproduced leak. The 1.2.1 task inspects preparation, build,
archive validation, installed probes, GitHub draft/public verification and Zenodo
receiving operations. The maintained resource table records owners, useful lifetime,
caller protection and cleanup failure visibility. Existing #63 guards stay active.

Release-task clones, SDK, isolated environments, distributions and receipts are
owned explicitly under `/tmp/ghrr-release-1.2.1-J5EVaN`. Original artifacts remain
until their final qualification/public verification. Public release assets are
persistent immutable outputs, not cleanup targets. Caller environments, credentials,
extension pins, active work and other task directories are preserved.

Broader retrospective review of remaining development/test/scientific operations
and historical resources remains with Diego/Liliana under this issue and
`uibcdf/molsyssuite#104`. Review target: 2026-11-07. The removal condition is an
explicit disposition for each remaining applicable operation/resource, with any
actual implementation gap separately owned. This is a review scope/checkpoint,
not a policy exception, waiver or assertion that all tools already comply.

Executed release operations and closeout disposal are recorded after observation;
source inspection alone does not prove runner disposal, retention expiry, public
archive custody or release success. No broad age/prefix deletion is authorized.

The clean qualification suite also emits an interpreter-shutdown `/dev/null`
ResourceWarning with the committed pytest-receptor 1.1.0 renderer. The existing
provider issue `uibcdf/pytest-receptor#4` owns that late-terminal stream defect;
this observation does not establish a GHR runtime leak. The test result remains
729 passed/one installed-only skip, and the diagnostic is retained rather than
suppressed. Test-tool adoption is separate from runtime/public package behavior.

## Executed release scope — 2026-10-24

Exact-source qualification, isolated installed probes, the public writer,
independent public downloads and bounded non-extracting archival receipt reads
completed successfully for source `a23e1910be1c4640135ccfe5a693cca08c1480d9`.
The durable candidate/public receipts under `devguide/evidence/` preserve distinct
original staged/public hashes and measured limits. The public release and DOI
are persistent outputs. Task-root disposal follows the final receipt push and
handoff; this statement does not assert unobserved runner disposal or expiry.
Caller environments, authentication, extension pins, other tasks and old paths
remain protected. The broader Diego/Liliana review stays partial under #65 and
`uibcdf/molsyssuite#104`, target 2026-11-07.
