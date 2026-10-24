---
summary: Review release resource ownership while retaining the broader lifecycle follow-up.
issue: uibcdf/gh-run-receptor#65
status: resolved
opened: 2026-10-24
closed: 2026-10-24
verification: measured
area: [governance, packaging]
guard: tests/test_bundle_resources.py
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

## Remaining owner review — 2026-10-24

The maintainer now authorizes completing the broader component review. The
normative resource review adds an explicit disposition for every applicable
runtime, developer/test/docs/build/validator and hosted delivery operation family.
Scientific/Qt/browser engines are not implemented here; there is no missing
scientific suite solely to establish this applicability. Native source tests and
Conda/public installed delivery remain distinct gates in #68/#60 and the release.

The ten historical paths explicitly registered for GHR in central #104 were
rechecked: all are absent, with removal attribution unknown and no deletions by
this review. The prior 1.2.1 task root's successful owner cleanup is separately
recorded. Current `/tmp/ghrr-1.3.0-z8LfuC` has useful explicit retention through
feature/Conda/release qualification; caller environments, caches and other sessions
remain protected. The sanitized path receipt is
`devguide/evidence/resource_owner_review_2026-10-24.json`.

Existing resource regressions and new job-log aborted-download/byte-boundary guards
remain the implementation evidence. No further local implementation exception is
identified. Final report closure and central #104 handoff follow the pushed
review/guard evidence; this does not close other members' central coordination.

## Component disposition accepted — 2026-10-24

The authorized owner review is complete for this component's applicable tools
and explicitly registered resources. The maintained normative table and path
receipt absorb the decision. Existing focused resource guards execute within the
805-test local source gate, with one explicit Conda-installed-only skip; Ruff,
29-route/nine-contract preflight and strict Sphinx also pass. This closes missing
component review evidence, not an unobserved universal cleanup or the separate
Conda/native/release qualification. Useful current task retention stays explicitly
owned through its delivery work. Central #104 receives the pushed disposition;
its multi-component coordination remains independently owned.
