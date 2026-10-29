---
summary: Separate runtime, portable tooling and complete installed qualification.
issue: uibcdf/gh-run-receptor#76
status: active
opened: 2026-10-29
closed:
verification: inspected
area: [packaging, github]
guard:
normative: architecture.md
blocked_by: []
supersedes: []
---

# Consolidated product and qualification architecture

The maintainer requests implementation of #76, following the structural decision
in uibcdf/molsyssuite#144. Normal 1.3.0 installation is already qualified; this
work changes development and qualification boundaries, not historical artifacts.
Base checkout: `15758c330f369c39f9a920eb4d7c164c007a2ccf`, clean and synchronized
with origin/main. The three commits after the previous delivery change governance
instructions only. Issue #75 remains separately owned.

## Direction and measurements to retain

Use `src/gh_run_receptor` to separate runtime discovery from repository helpers.
The measured packaging reason is the original installed collection failure in
40143357716 and source-root substitution risk documented in #144/#76. This
explicit maintainer direction supersedes the earlier flat-layout preference;
schema bytes, import name, runtime dependencies and public version identity stay
unchanged. Review launchers, Action, build metadata and editable development together.

Repository-only reusable operations receive the dedicated
`gh_run_receptor_tools` namespace and explicit repository/data/output inputs.
Thin source command wrappers may identify their own checkout as a CLI default;
reusable operations must not derive meaning from a staged helper's location.
Classify every existing test function/assertion as installed product, repository
tooling or integration, splitting mixed modules where necessary. Retain original
source-version checks and all assertions; retire adapter-specific code only after
successful replacement receiving, with an explicit successor regression record.

Investigate shared installed_noarch/imports/test-support @1 tools at the immutable
provider named by central #144. Use declared support staging, origin/digest guards
and cleanup rather than a GHR import adapter. Keep product source, archive,
tooling/support source, workflow and provider identities separate. Report minimal
residual provider gaps to #144; do not fork SDK code.

## Required execution

Development editables and clean installed distributions are distinct profiles.
Execute product, tooling and integration obligations and rejection cases for
missing/tampered support, runtime substitution and cleanup failure. Retain the
complete before/after function/assertion inventory and platform/minor/job/step
and artifact receipts. Qualify Linux/macOS arm64/Windows × Python 3.11–3.14,
including installed CLI/resources and real cross-platform integration. Remove the
maintained adapter only after complete replacement receiving. Historical 1.3.0
source, producer, file/hash, failed runs, qualification and promotion stay immutable.

No public version, tag, upload or promotion is selected. New test artifacts must
be separately identified nonpublishing qualification candidates. Preserve the
active shared editable environment, sibling work and other task resources.
Task-owned `/tmp/ghrr-issue76-u6mtuo1c` retains isolated tools, SDK, inventories
and qualification artifacts until durable receiving, then is removed at closeout.

## Current evidence

Planning/source inspection only. Existing SDK pin 6d6172d lacks test-support @1;
the central handoff identifies 56fe19215b9a414c050b95a5404d3ae50909aa83 for review.
No refactored native/installed claim is made before execution. The initial AST
inventory is retained in the task root for complete mapping before closure.
