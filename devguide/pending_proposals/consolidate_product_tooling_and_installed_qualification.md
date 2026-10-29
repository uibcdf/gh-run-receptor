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


## Private input/checkout receiving correction — 2026-10-29

Source checkpoint 1d154c4 passes native routine 40924956207, policy 40924957040,
Conda governance 40924957214 and strict docs/Pages 40924956089. Local source
after the future-freeze regression passes 845 tests / one Conda-only skip.
The first private dispatch 40925642094 fails source input inspection because
inspect_recipe expects the plan alongside its owned meta.yaml; no package is
built or registered. The separate private plan now lives beside that existing
recipe as devtools/conda-build/qualification_plan.toml. The ordinary preflight
and a concrete CLI regression inspect this exact plan, preventing recurrence.

Compatibility dispatch 40925646904 is cancelled as obsolete before qualification;
its cancellation is not passing evidence. The correction also preserves literal
support bytes with LF attributes and scopes core.autocrlf=false only to provider
checkout steps. An actual Git checkout regression retains a CRLF control and
proves both attribute-protected helper bytes and raw provider checkout behavior.
No global Git configuration, digest or source guard is weakened.

A local focused run failed on filesystem quota, not product assertions. Removed
only obsolete task-owned source-final pytest inputs and the specifically assigned
pytest-1179 directory. Fixtures now exclude irrelevant bytecode caches. Corrected
focused gate: 19 passed / the explicit Conda-only skip; real private-plan, 30-route
and frozen-contract preflight, Ruff and whitespace checks pass. The first failed
run and local quota failure remain uncredited evidence. No publication or original
1.3.0 file mutation occurs. Replacement receiving and adapter retirement remain
required, not inferred from these administrative checks.


## Build-only provider and Windows text receiving — 2026-10-29

Corrected source 04f827a passes routine 40927180524, policy 40927181171,
Conda governance 40927181295, contracts 40927337073, exits 40927342477,
reusable 40927349219, minimum-gh 40927356037 and docs/Pages 40927362474.
Private run 40927320067 stops before producing any file: its shell conda function
uses the base manager, not the active conda-build plugin. The consumer now calls
the already supported build-only Action at 8da628d with upload/github_release
false and the exact shared noarch-publisher environment. No new Action or
publication route is implemented; build selection stays local.

Source compatibility 40927325642 has four successful Linux cells and four Windows
failures in one legacy adapter test reading UTF-8 YAML with the platform default
encoding; its macOS jobs are still queued when inspected. It is not full native
qualification. Explicit UTF-8 preserves that assertion and its complete declared
selection. Published GHR 1.3.0's --job path correctly reports the completed failed
Windows job while retaining queued/PENDING/exit 3 for the whole workflow.
Focused corrected guards: 34 passed / the explicit Conda-only skip; real private
plan, owner preflight, Conda controls and Ruff pass. No private archive exists
yet, so no producer file is rebuilt or replaced.

Normal shared development editable is refreshed with --no-deps, imports from
src, and passes nine source-version/metadata checks. An obsolete root egg-info
created by this task's initial flat editable masked the fresh distribution
metadata; that generated GHR-only directory was removed after checking project
identity. Caller dependencies and sibling editables remain unchanged. This is
normal development receiving, never archive qualification.


Private run 40931878568 exposes a second runner bootstrap boundary before any
file is built: enabling setup-miniconda profile initialization fails activation
in the login shell. Keep initialization disabled as in the earlier working
bootstrap, explicitly activate the reviewed publisher environment, check its
external conda build command and export that exact prefix bin through the
job-owned GITHUB_PATH for downstream Action steps. The official Action already
bypasses the base shell function. No source/import guard is changed; no file
exists to rebuild. This remains consumer environment wiring, not a new SDK API.


## Complete development receiving — 2026-10-29

Source cc801c4f9f522ae486a7a65af2b09a0cee99ebbd passes all twelve native
compatibility jobs in 40931884229, including all four Windows minors after the
explicit UTF-8 correction and all four actual macOS jobs. Each cell executes the
complete source selection, builds wheel/sdist, inspects/installs the wheel and
checks the installed command outside the checkout. Action/extension receiving
40931889607 passes its three native OS jobs; contracts 40931894629 and strict
docs/Pages 40931900264 pass. Later workflow-only checkpoint dd0175a passes
routine 40934356013, policy 40934356973 and Conda governance 40934357001.
These are development/source receipts, not installed Conda certification.

The exhaustive 446-function inventory explicitly identifies the required source
and installed native gates for each scope, retaining baseline parameterization
and whole-function digests as well as assertion expressions. All 437 original
functions remain traceable to the immutable baseline; no failing check is
removed to make development receiving pass.


## Original private file and transport correction — 2026-10-29

Producer 40935030060/attempt 1 at dd0175a6816a5fe3a7e212b7246fbd7985487ea8
successfully builds the first private file, gh-run-receptor-0.0.0-py_76.tar.bz2,
SHA-256 c4387f0ed4f7979f6463242cc6597006de1ab456c2bbe59ada8724280cc24ae5.
Actions artifact 12923464844 retains it and the original descriptor. Its first
installed cells reject a missing expected file: the uploaded two-path artifact
preserves nested parent directories. This is a failed receiving attempt, not
product/installed success. Published GHR identifies the exact failed gate while
preserving the whole workflow's active state.

The receiving workflow can now explicitly reuse that producer run, source and
digest, skipping the build job. A bounded two-member check binds the original
manifest, source, provider, plan and archive digest before locating the unchanged
file at the installer's expected path. Read-only Actions permission allows this
same-repository download. Canonical checkout bytes preserve the original plan
hash on Windows. Qualification/workflow identity remains the new run; product
and test/support source remain the original committed candidate. No archive is
rebuilt, no record is relabeled as staged/public, and no test is waived.


## Installed receiving and adapter retirement — 2026-10-29

Run 40935956394/attempt 1 at 4a687a3fc741531eee01808ba5294da993b4916e
passes all twelve native installed cells. Its build job is deliberately skipped:
all cells consume the original dd0175a private file and SHA-256 recorded above.
The original producer/test-support source, newer qualification workflow and
accepted shared fee3bd8 provider remain distinct. All twelve Actions artifact
digests and six JSON records per cell were downloaded and checked. Each cell
executes 638 product/integration tests, exits zero, verifies exact installed
files/resources/metadata/launchers before and after execution, performs seven
support checks and reports imports_retired/resources_retired true. The ordinary
public dependency closure and local-candidate origin remain explicit.

Only after that receiving, remove active installed_test_helpers.py and its
GHR-specific import/path interception; the maintained staged-file workflow calls
shared installed_noarch tests/support directly. Preserve its applicable
workflow/source/artifact assertions in a dedicated workflow test. Two legacy
implementation-specific functions (sixteen cases) retire with complete original
assertion/function/parameterization evidence, per-case successor or explicit
non-applicability, and the prior successful twelve-cell source run. This removes
no failing test and creates no new skip. The active inventory has 444 functions:
312 product, 111 tooling and 21 integration; all 437 baseline functions remain
traceable through active or retired records. Both source-version repository
checks remain active tooling.

The final retirement changes no product source, installed selection, support
code/hash or product/integration function body relative to dd0175a. Reuse of
those exact-file native receipts is limited to that unchanged execution input
set. The final complete source gate and native compatibility validate the
changed workflow assertions and active collection inventory separately. Public
1.3.0 producer, file, tag, failed attempts, original qualification and promotion
remain immutable. The central shared implementation is merged and received;
#144 receives this immutable consumer handoff for its own coordination record.


Local retirement gate: 830 passed / the same explicit Conda-only source skip,
with all shared-provider receiving checks executed in the isolated normal
editable profile. The sixteen removed cases exclusively exercise the retired
implementation; the preserved workflow test still executes. All 437 baseline
functions account as 435 active and two explicitly retired; there is no
unaccounted function. Ruff passes 237 files, strict Sphinx passes, all nine frozen
contracts and all 30 reviewed distribution routes pass. The existing public
pytest renderer ResourceWarning remains visible and is not suppressed.
