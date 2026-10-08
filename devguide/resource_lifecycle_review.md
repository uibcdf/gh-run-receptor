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
