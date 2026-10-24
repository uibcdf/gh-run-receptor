# Acquisition and developer resource lifecycle review

Owner review: uibcdf/gh-run-receptor#63; shared coordination: uibcdf/molsyssuite#104.
Observed 2026-10-07 at source c2c952946ccc4c57da0f64dbeec632fc93fb2f70;
source repairs and native qualification are recorded in the owning issue and
`archive/resolved_bugs/clean_aborted_bundle_staging_on_interruption_and_permission_failure.md`.
This is a resource-focused source review, not a full installed/platform or release certificate.

## Ownership by operation

| Operation | Ownership and observed lifecycle | Evidence |
| --- | --- | --- |
| `capture_bundle` / `acquire_evidence` refresh | Own private preparation/replacement; keep published cache/output. Restore old bytes after interrupted replacement. | Twenty new resource regressions collectively protect acquisition exits; existing bundle/service/CLI checks retained. |
| GitHub JSON/download transport | Private stderr TemporaryFile; shared private `_owned_process` reaps failed children and closes stdout. Remove incomplete aborted download; caller owns successful output. | Real child and filesystem regressions, controlled pipe errors/interruption; byte-limit/classification checks retained. |
| Published report acquisition | Managed TemporaryDirectory contains bounded ZIP; validated report survives as data. | Source inspected; existing published-reader checks retained. No new live artifact validation. |
| Config discovery/write | Private NamedTemporaryFile, fsync/link for nonreplacement, finally unlink. Config remains caller output. | Source inspected; existing discovery checks retained. |
| Public-run corpus validator | TemporaryDirectory owns explicit bundle through offline replays; context cleans on exits and reports removal errors. | Source inspected; existing controlled runner tests. No fresh public-corpus dispatch. |
| Bundle sanitizer | Explicit destination is a caller-owned reviewed fixture candidate, including incomplete output for failure diagnosis. Caller decides retention/removal; input bundle unchanged. | Source inspected; no new capture or sanitization of private data. |
| Capture-policy benchmark | Reads caller bundle roots, emits stdout only. No disposable environment/bundle allocated. | Source inspected and existing benchmark tests. |
| Contract/archive/dependency/installed validators | Read source/resources/archive members without payload extraction or execution; wrappers may emit explicit caller receipts. SDK is caller-supplied/pinned. | Nine frozen contracts / 27-route unchanged pinned preflight; no new installed archive/solver/publication. |
| Release/checksum/citation tools | `dist`, notes and metadata paths are invoking release task's outputs. Retain exact original bytes/receipts through qualification and public verification, then owner closeout. | Source inspected; actual releases and artifact custody stay separate under #60. |
| Index/report/guide maintenance | Generated docs/configured root guides are persistent repository outputs, not temporary cleanup targets. | Source inspected; current indexes/offline reporting gates checked. Canonical consumer guide distribution uses MolSysSuite registry. |
| Hosted workflows / Action outputs | Hosted runner work directories and installed tools are job-owned; output reports/artifacts have caller retention. Routine coverage XML retains 14 days; Action report retains 7 days. | Workflow source inspection; only applicable ordinary/admin CI is newly inspected. Runner disposal/expiry not separately executed. |

## Contributor and operator closeout

Follow the synchronized MolSysSuite temporary-resource policy. Choose an explicit
owner/task destination for captures, sanitized fixture candidates, release archives
and receipts. Useful evidence/cache may remain while needed. At task/release closeout,
review those explicit paths and remove obsolete owned copies after their final use;
keep exact original registered artifacts and needed receipts. Do not delete caller
cache, development environments, other tasks or primary clones as a reusable tool side
effect. Cleanup failures and still-needed output ownership remain visible in the task.

The current task uses an isolated source clone and pinned SDK clone, with identified
qualification fixtures and receipts; these are disposed after final verification/handoff.
The primary local clone and caller Conda environment remain untouched. This source review
cannot assign ownership or safe disposal to every historical cache/output. Retrospective
review remains pending with Diego/Liliana under the existing #104 member coordination;
no blanket /tmp or home-cache removal, new cleaner or automatic expiry is introduced.

## Release-scoped receiving review — 2026-10-24

Owner follow-up: uibcdf/gh-run-receptor#65; release: 1.2.1. This review covers the
actual publication route and does not close the broader retrospective review.

| Operation/resource | Owner and useful lifetime | Protection and evidence |
| --- | --- | --- |
| Source/SDK staging clones | Release task, under `/tmp/ghrr-release-1.2.1-J5EVaN`, through final qualification and handoff | Original checkout and sibling sources are read-only inputs; only a temporary local candidate tag is used in staging. |
| Build/test/installed environments | Release task in that same explicit root, through candidate/public-file checks | Caller Conda environment and dependencies are not modified. A clean venv supplies the committed test pin and optional docs/build tools. |
| Candidate distributions, downloaded public files and receipts | Release task until public digest/payload/install verification and durable receipts are recorded | Candidate and hosted/public bytes keep distinct hashes. No rebuild is substituted for an original registered file or a promotion. |
| Archive validation | Owner-maintained bounded non-extracting reader | ZIP/tar streams close through contexts; AST reads literal versions without executing payloads. Unsafe names, links, truncation and size/count controls remain guarded. |
| Publisher `dist` and runner-temporary install/notes/API JSON | Hosted publication job | `RUNNER_TEMP`/workspace lifetime is job-owned. Draft/public GitHub assets are persistent release outputs, never temporary cleanup targets. Draft failures require explicit inspection, not automatic deletion or overwrite. |
| Public CLI extension probe | Release task, isolated XDG data root | Existing authentication remains with gh. Caller configuration, extension and pins are preserved; only the isolated checkout is removed at closeout. |
| Zenodo recovery receipt | Shared pinned verifier and hosted run | Bounded public GETs write an explicit JSON output; hosted sanitized evidence retains 30 days. Discovery does not depend on retention or a sleeping process. No hook/account/deposit mutation. |

Existing `tests/test_bundle_resources.py`, `tests/test_github.py` and
`tests/test_release_tools.py` guard process/stream cleanup, incomplete downloads,
caller-resource protection and archive refusal. New transport context preserves
those semantics. Source inspection is distinct from executed native/installed
qualification and from unobserved hosted-runner disposal or retention expiry.

At closeout, review and remove only the explicitly owned task root after its
last needed artifact/probe is recorded. Retain useful evidence until then; expose
cleanup failures. Do not delete old release/task paths or shared caches by age or
prefix. Broader owner disposition remains #65/#104, with review target 2026-11-07;
this is neither a new cleaner nor a release-gate waiver.

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

## Complete component-owner disposition — 2026-10-24 (#65)

The maintainer authorizes completing the remaining component review alongside
#60/#68 and a conditional 1.3.0 release. This section supersedes the earlier
pending owner-review checkpoints for this component. It does not close central
#104 for other members or certify unobserved cleanup on every platform.

| Applicable operation family | Owner disposition and useful lifetime | Verification / remaining limits |
| --- | --- | --- |
| Runtime transport, capture, cache refresh and new explicit job logs | Operations own private streams, subprocesses and unpublished staging; success transfers a validated bundle to caller cache/output. Aborted job downloads are removed by the owner operation as well as the transport. Active refresh rolls back before deleting obsolete generations. | Existing #63 process/pipe/interruption/rollback regressions plus #68 partial-download, bounds and refusal tests execute locally; native source matrix separately qualifies OS behavior. |
| Config loading/discovery and installed-origin/version introspection | Readers allocate only bounded in-memory data or context-managed file handles. Non-overwriting config creation owns its temporary file; committed/output config is persistent caller data. | Existing source tests cover malformed inputs, atomic nonreplacement and safety. No caller config/cache is treated as temporary task garbage. |
| Logs/checks/events/normalization/profiles/rendering/comparison/aggregation/watch | File/archive contexts or bounded in-memory transforms; renderers do not own temporary workspaces or children. Watch uses the same caller-owned acquisition cache. | Source inventory covers all runtime modules; existing semantics/security/resource tests execute. No scientific, Qt or browser execution engine exists in this CLI, so those tool families are not applicable here. |
| Published report download/verification | TemporaryDirectory owns the bounded artifact ZIP; validated report data escapes, raw download does not. Context exit cleans success/failure; removal errors propagate. | Published-reader/source tests retained; native receiving remains distinct from claims about retention expiry. |
| Sanitized fixtures and public-corpus validation | Sanitizer input remains unchanged; explicit fixture destination is persistent caller-reviewed output, including diagnostic partial output. Validator owns managed raw captures and synchronous children, with visible failures. Job-log sanitizer drops raw logs and preserves reviewed subset identity as metadata. | Corpus/sanitizer guards plus new job-scope regression; no raw/private bundles committed. |
| Benchmarks, frozen contracts, distribution/archive/input/installed checks | Read-only source/resource/fixture/archive operations. They do not extract or execute archive payloads. Caller-specified receipts are persistent outputs; SDK clones belong to the invoking task. | Existing adversarial/archive/source guards retained. Conda installed/promotion/public qualification is owned separately by #60, not silently credited by this review. |
| Index/report/issue/canonical-guide maintenance | Repository reports/generated indexes and explicitly selected guide destinations are persistent outputs. Subprocess commands are synchronous. These tools allocate no disposable environments or raw capture trees. | Lifecycle/index and repository convention checks. Guide synchronization remains a deliberate centrally coordinated operation; sibling sources are untouched. |
| Local testing/docs/build/release experiments | Invoking developer owns pytest fixtures/cache, documentation build directories, distributions and disposable environments. Pytest manages its own temporary fixture retention; a publication task uses an explicit private root and retains exact files until qualification/receipts finish. | Current root `/tmp/ghrr-1.3.0-z8LfuC` remains useful through #60/#68 and release receiving, then obsolete task copies are removed. Caller editable environments, caches and primary/sibling clones remain persistent and protected. |
| Hosted source/admin/native/Action/Conda/release/DOI workflows | Runner workspace, temporary environments/files and SDK checkouts are job-owned. Public distributions/DOI records are persistent, immutable delivery. Sanitized Actions artifacts have explicit workflow retention (job-log/DOI receipts: 30 days). | Source controls inspected; required executed native/installed/public evidence remains separately recorded by each owning delivery. No assertion that expiry or runner disposal was directly measured. Failed drafts/staging files require explicit owner disposition; no automatic overwrite/deletion. |

All locally applicable operation families now have an owner and lifetime;
no additional component implementation exception was identified by this review.
The known published pytest renderer warning remains provider-owned rather than a
new GHR runtime leak. This disposition does not claim a universal platform audit
or complete inventory of a shared machine.

The [explicit path receipt](evidence/resource_owner_review_2026-10-24.json)
rechecks the ten GHR-owned historical paths registered by central #104: all are
absent. Attribution remains unknown; none was deleted by this review. The prior
1.2.1 task root was removed by its own recorded closeout. No age/prefix scan,
shared-cache deletion or removal of other sessions is authorized. Current task
retention is ordinary useful work, with disposal after final durable receipts,
not an unbounded exception. Central #104 receives this component's disposition
through its owning issue/report after the local record is pushed.

## Installed administrative helper receiving — 2026-10-24 (#60)

The original-file Conda qualification recovery owns only temporary in-process
`devtools`/`tests` bindings and an explicit caller receipt. Original committed
helper files are read-only inputs. Collision/byte/path/origin guards and finally
cleanup preserve caller bindings; the original sys.path/sys.argv objects are
restored. A guarded temporary import-path list prevents legacy administrative
helpers from exposing the runtime source root. No extra environment or source
copy is created by that operation. Hosted qualification checkouts/environments
remain job-owned; sanitized helper artifacts retain 30 days. The bounded owner-
equivalent integration and removal condition belong to #60/central #144, separate
from the already completed general owner disposition #65.
