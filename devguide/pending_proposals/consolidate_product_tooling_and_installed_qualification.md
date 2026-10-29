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


## Implementation checkpoint before native receiving — 2026-10-29

Runtime is under src; portable operations and schema assertions use the unshipped
component namespace. All original 437 functions are mapped with before/after
assertions and required gates; seven new functions bring the current inventory
to 444 functions (312 product / 111 tooling / 21 integration). Source-version
repository checks remain tooling, and installed version provenance gains explicit
regressions. Baseline: 831 passed / one Conda-only skip. Current complete local
source gate: 844 passed / the same explicit skip, with all five SDK-dependent
checks executed. Ruff, strict Sphinx, wheel/sdist build, all nine frozen schemas
and 30-route preflight pass. The known published renderer warning remains visible.

Provider PR uibcdf/molsyssuite#157 is approved by the principal maintainer and
merged as 31613c2322eab767fb316c5737bf4f56cba48d6d, retaining reviewed source
fee3bd875e68778844c0fffc2aba26b6cea02cd6. GHR pins that original accepted source.
57 affected provider tests and native PR 40919434758/post-merge 40920603151
mandatory governance/full-test steps pass. Local broad provider execution has
562 passed, one opt-in Mamba skip and one workspace fixture failing on the seven
known inherited caller-environment closure findings; no environment repair or
false local full-suite credit is claimed. Native clean-environment source gates
provide the required provider execution. An initial pytest discovery also tried
to collect test-input fixture projects; the documented unittest discovery and
pytest ignore of tests/fixtures preserve the actual provider check selection.

The real provider gaps are source/installed coordinate mapping, explicit private
plan selection and a nonpublishing local-file origin retaining all dependency,
archive, prefix, resource and launcher checks. No SDK implementation is copied
into GHR. Shared support receives original committed helper hashes and cleans its
owned staging/imports, without the GHR binding/path adapter. Eleven local receiving
regressions pass, including original missing-generic-import reproduction,
missing/tampered support, collision, changed bytes, abort, visible cleanup failure
and precollection src runtime substitution.

The manual qualification workflow builds private placeholder 0.0.0/build 76 once
and executes twelve exact-file installed cells. No tag/public version/upload/
promotion is authorized or performed. Complete native product, tooling and
integration evidence remains required; the old adapter is retained until then.
The synchronized suite guide and all historical publication receipts stay intact.
