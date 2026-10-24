---
summary: Publish and independently verify the 1.2.1 patch release.
issue: uibcdf/gh-run-receptor#71
status: resolved
opened: 2026-10-24
closed: 2026-10-24
verification: measured
area: [packaging, github]
guard: tests/test_release_tools.py
normative: versioning_and_releases.md
blocked_by: []
supersedes: []
---

# 1.2.1 release ownership and gates

The user authorizes publication through the existing GitHub wheel/sdist/checksum
and exact-tag CLI route after #67 and the release-scoped #65 review. First Conda
delivery (#60) and active-workflow job logs (#68) are explicitly outside scope.

The candidate includes resolved diagnostic issues #59/#61/#62/#64/#66, Windows
recovery #69, safe acquisition identity #67 and bounded archival receiving #70.
Python 3.11--3.14, dependency-free runtime, source conclusions, stable process
statuses, read-only operation and all nine frozen schemas remain unchanged.

Before authoritative tagging, freeze metadata/source, build from an isolated
clone with a local-only 1.2.1 tag, inspect both archives, install the candidate
wheel outside source and record its actual metadata/resources/diagnostic probes.
Record exact source, tools, inputs, artifact digests and hosted native/policy/
Action/reusable/archival receiving evidence in a task-owned receipt. A source or
metadata change invalidates dependent candidate gates; do not move a public tag.

Publish only through the exact-tag draft-first workflow with release title 1.2.1.
Independently verify public API inventories, sizes/digests/checksums and payloads,
a clean public-wheel installation and an isolated pinned extension. Candidate and
hosted builds keep distinct hashes and scope. Archive/DOI states remain separate;
#70 supplies bounded recovery without treating pending ingestion as successful.

All task resources are owned under `/tmp/ghrr-release-1.2.1-J5EVaN` through final
verification/handoff. Public assets are persistent. Shared environments, caller
pins, unrelated work and historical task paths are preserved. Record producer
and public receipts durably before disposing of obsolete owned resources.

Publication, package availability, installed-file qualification and central
version-specific notice are pending until observed. The complete local source
suite currently passes 729 tests with one explicit Conda-installed-only skip in
a clean Python 3.14.7 environment using committed pytest-receptor 1.1.0; the known
provider #4 late-terminal warning remains visible. This local result is not a
public artifact or exact-candidate native qualification receipt.

The live corrected adapter reads original MOLI run `39513025386` with native
completed/success and original source/attempt identity. A real GitHub 404 for
currently unpublished 1.2.1 retains `api.json`, the safe relative request path
and `not_found_or_inaccessible`; optional-404 behavior remains unchanged. This
positive/request-context probe does not claim the earlier transient outage was
reproduced or repaired. Strict Sphinx preparation build also passes in the clean
task environment. Exact frozen-candidate gates remain a separate next step.

The writer workflow now checks out the same reviewed SDK and executes the owner
preflight before pytest. Without that checkout, optional SDK-dependent test cases
would skip inside the publisher even though the separate compatibility matrix
executes them. This closes that publication-scope gap without changing the public
route, credentials, runtime dependencies or archive truth controls. The inventory
hash is refreshed after reviewing this explicit preflight-only addition.

## Measured closeout — 2026-10-24

Tag 1.2.1 preserves `a23e1910be1c4640135ccfe5a693cca08c1480d9`.
Publisher `40132672999` succeeded through public verification with 729 tests
and one installed-Conda-only skip. Twelve native source-build/install cells
and the applicable Action/reusable/minimum-gh/exit/docs/policy gates passed.
Public wheel/sdist/checksums were independently downloaded and verified;
a fresh Linux/Python 3.14.7 public-wheel installation and isolated exact-tag
extension passed the diagnostic, schema, source-origin and process-status probes.
Zenodo record `10.5281/zenodo.23627112` is independently verified for one source
ZIP. Central receiving notice is `uibcdf/molsyssuite#138`; broad resource review
#65 and independent #60/#68 remain open. Preparation observations above are
historical phases, superseded by these measured results.

The [normative receipt](../../versioning_and_releases.md#verified-121-publication--2026-10-24),
[candidate evidence](../../evidence/release_1_2_1_candidate.json) and
[public evidence](../../evidence/release_1_2_1_public.json) preserve exact bytes,
source/run identities, qualification limits and the distinction between staged
and delivered files. This closes release delivery, not ecosystem-wide adoption.
