---
summary: Prepare an additional noarch Python Conda distribution with exact-file gates.
issue: uibcdf/gh-run-receptor#60
status: resolved
opened: 2026-10-06
closed: 2026-10-24
verification: measured
area: [packaging, github]
guard: tests/test_conda_distribution.py
normative: versioning_and_releases.md
blocked_by: []
supersedes: []
---

# Additional noarch Python Conda distribution

**Reported:** Central distribution review uibcdf/molsyssuite#45, 2026-10-06.
**Status:** Additive route accepted and prepared; first release decision,
credentials and exact-file native qualification remain pending.

## What

Prepare the official uibcdf Conda route while retaining the existing GitHub CLI
extension, Action, wheel/sdist and archival modes. The maintainer accepted this
route instead of a temporary official-channel exception. Public 1.2.0 source,
assets, tags and existing evidence are not rebuilt, changed or republished.

## How

[The recipe handoff](../../../devtools/conda-build/README.md) owns the operational
steps and applicability. The recipe uses `noarch: python`, actual Python bounds,
versioningit/setuptools, the console entry point, generated version and all nine
frozen schema files. `gh>=2.48.0` is a separate Conda runtime dependency tied to
`MINIMUM_GH_VERSION`, not a Python dependency or bundled native binary.

The optional shared provider capability was added centrally under
uibcdf/molsyssuite#45 and accepted at full commit
`38db709ecc07451ff36ea84573d585f9af6b4df7`; hosted governance `37536963845`
succeeds. `external_run_requirements` binds the external floor in both recipe
and exact archive. Missing or changed constraints fail before upload/install.
Owner checks additionally protect the acquisition floor, frozen schema inventory
and installed commands. Existing consumers without the optional fields retain
their reviewed behavior and pins; notices precede delivery.

The source input inventory classifies one recipe and twenty-six workflows;
there are no required Python runtime providers, sibling source replacements or
Conda environments to classify. Its example plan is not a release decision.
The candidate path additionally requires the real committed plan and exact
candidate SHA/version. Routine, weekly and source compatibility CI run this
review before tests. Versioned suite policy stays on its existing pin.

Stage and promotion wrappers are manual, least-privilege and depend on owner
input review. The shared provider independently acquires required executed
native source gates. First staging requires one original archive and twelve
native installed cells with exact source/file/digest and complete required
steps. Promotion adds a public label to that file without rebuilding. Producer
and newer administrative qualification workflow identities remain separate.

The installed selection runs all applicable package/runtime tests. Only two
unbuilt Git extension source-version tests are deselected, because they require
source Git/tag discovery; they remain executed in source compatibility. Runtime
CLI subprocesses use safe-path mode. An installed-only semantic test checks
prefix-owned commands, real gh floor, generated/metadata version and exact
schema digests. An ordinary source run skips that test explicitly when no Conda
record exists. Shared test tools and source test extras are separate declared
routes; their receptor versions do not imply a runtime requirement.

## Why

One architecture-independent file can supply the Python runtime on all claimed
platforms while their native gh packages are resolved separately. Reusing the
suite operations avoids a private publisher or weaker consumer-only workaround.
A prepared route is distinct from evidence of an available public package.

## Verification and pending evidence

Initial solver-only bootstrap probes use strict `uibcdf`, then `conda-forge`
channels and Python 3.14. Linux, Windows and a macOS arm64 cross-solve with
`CONDA_OVERRIDE_OSX=14.0` resolve Python 3.14.8, gh 2.102.0, setuptools 84.0.0 and
versioningit 3.3.0. The initial macOS solve without its virtual OS failed on the
Linux host. No probe created an environment or installed a candidate.

Regression guards cover missing recipe gh, changed actual adapter floor,
changed schema bytes, new unclassified workflows, synthetic archives missing
schemas/gh or carrying a wrong embedded version, and missing/out-of-prefix or
insufficient installed gh. They exercise rejection mechanisms rather than an
actual public build. Native current-head receipts will be recorded with delivery.

Still pending: an owner-reviewed real release plan, unused coordinate,
credential confirmation through the authorized route, exact producer file,
twelve native installed cells and independently verified public registry/index.
These retain partial central adoption and unknown Conda access. Preparing source
does not clear that evidence, introduce automatic publication or impose a full
suite on each internal push. Scientific component suites are not dispatched.

## Coordination

- uibcdf/molsyssuite#45 owns the shared provider and central adoption.
- uibcdf/gh-run-receptor#60 owns implementation and the first Conda delivery.
- The seven existing shared publishers and maintained route-audit consumers
  received availability/compatibility notices; their pins are not changed here.


### Local verification — 2026-10-06

Qualified interpreter: `molsyssuite@uibcdf_3.14`, Python 3.14.7. The isolated
source clone is selected explicitly for source tests; Pytest Receptor still
imports from its existing eligible editable clone. No participating shared
editable installation is changed. Seven known environment closure findings
under uibcdf/molsyssuite#82 are unchanged and do not certify installed closure.
The [sanitized preparation receipt](../../evidence/conda_route_preparation_2026-10-06.json)
records test-tool versions and applicability.

```text
GH_RECEPTOR_SUITE_ROOT=/path/to/pinned/sdk PYTHONPATH=/path/to/isolated/source python -m pytest --receptor=llm
python devtools/check_distribution_inputs.py --suite-root /path/to/pinned/sdk
python /path/to/pinned/sdk/devtools/scripts/conda_release_contract.py .
python /path/to/pinned/sdk/devtools/scripts/noarch_conda.py --root . --plan devtools/conda-build/release_plan.example.toml
python devtools/scripts/validate_devguide.py
ruff check .
ruff format --check .
```

Full source suite: **580 passed / one explicit installed-only skip**. Initial
focused source/CLI/version checks: 67 passed / the same skip. All 27 input
routes, publication controls and example recipe pass. Ruff 0.16.5 checks all
191 Python files; guide index/lifecycle and whitespace checks pass. Synthetic
archives and controlled mutations exercise rejection without building or
publishing a candidate. Existing action-pin and Python-lane tests now identify
actions by identity rather than assuming the SDK checkout is the Python step.
These measurements prepare the source route; future installed/candidate evidence
is still required before a public Conda claim.

### Maintained GitHub archive checks — 2026-10-06

Inspection found that the original GitHub asset verifier checked tag identity,
asset sizes and digests but did not inspect internal distribution contents.
The original release-specific inspection remains historical evidence. The owner
now provides `devtools/scripts/distribution_archives.py::inspect_distribution`,
called by `release_tools.py archives` before upload and by the existing draft/public
verifier. It binds both archives to the same reviewed required paths and frozen
schema digests already used by the additional Conda route. No new public
format or shared policy is introduced.

The regression guard is `tests/test_release_tools.py`: valid outer names and
recomputed asset/manifest digests still fail for wrong or ambiguous internal
versions, project identity, Python bounds, missing code/resources and altered
schema bytes. Both formats reject unsafe/duplicate paths, links and count,
member and total-size violations; missing/truncated archives return failures.
`tests/test_publish_release_workflow.py` keeps this gate before installation or
any upload. The publisher's inventory hash is consciously refreshed for the
new mandatory operation; all other workflow hashes and CI lane semantics stay
as reviewed.

The existing public 1.2.0 wheel and sdist pass the new read-only inspection;
they have not been rebuilt or replaced. Build tools normalize Requires-Python
specifier order, so metadata comparison uses equivalent specifier sets rather
than string order. Owner-specific GitHub validation stays local; central
uibcdf/molsyssuite#45 tracks the missing general wheel/sdist SDK profile for
any future second consumer. Conda source/artifact/installed/public evidence
remains separately pending.

Qualified source verification after this addition: **627 passed / one explicit
installed-only skip**; Ruff 0.16.5 lint/format passes all 192 files. The reviewed
27-route preflight, guide lifecycle/index and whitespace checks pass. Python
3.14.7 and the participating editable import origins remain as above, with the
same seven tracked environment findings. This is source and read-only archive
evidence; it is not an installed candidate, release run or twelve-cell claim.


### Governance adoption before first Conda release — 2026-10-09

The existing MolSysSuite Member review contract permits policy adoption before
first publication when CI/recipe controls are ready, installation claims remain
truthful and access is explicitly unknown. The earlier partial-central-adoption
statements above combined governance with future delivery; this dated correction
supersedes that classification without qualifying a Conda artifact.

Central uibcdf/molsyssuite#45 now records governance adopted / CI-recipe ready /
Conda publication access unknown. This owner issue remains partial solely for
its first actual delivery. The developer still chooses the version, real plan
and release timing; no new release is required to adopt governance.

Read-only comparison from executed archive-control source
`ec42d211b5288db395ca07928e62127d520e55ba` to reviewed main
`cb202db78f539e1185ba03de26e57233ad5c9e80` finds 39 distribution input,
workflow, recipe and regression-guard files byte-identical. Later acquisition
resource corrections remain distinct runtime work. Independent fresh verification
of native routine `37733511777`, policy `37733512289` and Conda governance
`37733512337` binds exact source
`f19fcf94bb2735f61ef79cd9c2629dede715e700`, workflow, push event, attempt,
complete job inventories and mandatory actually executed steps. The only delta
from that source to reviewed main is the synchronized suite guide. These are
source/control results, not a current twelve-cell or installed Conda claim.

Future delivery still requires the owner-reviewed real plan and unused coordinate,
authorized credentials, all exact-candidate source gates, one original staged
archive/digest, twelve native exact-file installed cells, same-byte promotion and
independent public registry/index plus clean user installation. Keep optional
SDK notices separate; existing accepted pins need no migration for this review.
Original GitHub 1.2.0 and historical source/archive receipts retain their scope.
Central durable receipt: `devguide/rollouts/gh_run_receptor_governance_45_20261009.json`
in uibcdf/molsyssuite. The qualified caller environment and its seven #82 closure
findings are unchanged. No archive build, installation, upload, promotion,
version/tag selection or credential confirmation is performed.

## First delivery authorized — 2026-10-24

The maintainer authorizes completing #60/#65/#68 and publishing 1.3.0 after all
three are resolved. The real committed `release_plan.toml` selects unused
version 1.3.0/build 0, staged route, Linux/macOS arm64/Windows × Python 3.11–3.14
and explicit native job/step source gates. The maintainer confirms the existing
organizational ANACONDA_UIBCDF_TOKEN is available to this repository; no value
was inspected. Anonymous public package inventory returned 404 before this first
build. Actual upload/access and public poststate remain unverified until observed.

The existing accepted shared provider is retained at 6d6172d6cd00c5ac2d4ebadb71df554ec5b7fa26.
Read-only sibling comparison confirms the same contract in SMonitor, ArgDigest,
DepDigest and Pytest Receptor despite their different pins/custom wrappers. PyPI
is excluded. The resource inventory adds the new job-log owner module. Native
source, original producer, twelve same-file installed cells and public index/user
installation receipts must remain separate; no rebuilding or tag movement.
Release ownership: uibcdf/gh-run-receptor#72; advance notice: uibcdf/molsyssuite#141.

## Same-file qualification recovery — 2026-10-24

Producer 40143062622 successfully staged the original
`gh-run-receptor-1.3.0-py_0.tar.bz2`, 78037 bytes, SHA-256
`65f33b29dad70eb9e779f917e4c553d27effa4fddc2740a0260d259866746fd3`, source
`5a48759a399a17a16d923851b32519983a836f5f`. Independent staging download and
owner SDK archive inspection agree. The original file remains retained; no
rebuild, replacement, promotion or authoritative tag has occurred.

First installed run 40143357716 installs and validates that file on Linux/macOS
but cannot collect frozen administrative tests importing `devtools`. Windows
cells fail earlier in setup-miniconda's `conda init --all` (`needs sudo`), a
separate environment bootstrap failure. Both original failures remain visible.
Provider feedback: uibcdf/molsyssuite#144. The new diagnostic job selector was
used during the active matrix and correctly retained PENDING/exit 3 while naming
the completed failed job's ModuleNotFoundError.

A reviewed newer qualification workflow retains the original source/file/digest
and unchanged declared test selection. It still calls pinned owner SDK
prepare/download/install/verify/tests operations, including before/after installed
runtime guards. GHR supplies only an administrative helper-binding context and
explicit Conda activation; the source root is never added to sys.path. The
helper namespaces are restricted to original committed `devtools`/`tests`, with
collision/symlink/untracked-file/byte/origin checks and owned binding removal on
all exits. Path-sensitive helpers retain their original __file__ semantics.
No helper or runtime file is copied into or substituted for the installed payload.

This is the qualified owner-equivalent route for path-sensitive support described
by the shared support policy, not a provider implementation fork. Owner: GHR #60,
maintainer-supervised authorization from this task; review 2026-11-07; removal
condition: #144 supplies a reviewed shared interface and native same-file receiving
passes. All twelve native installed cells and final provenance rechecks remain
mandatory. The administrative workflow identity is separate from the producer;
publication remains blocked until qualification actually succeeds.

Local recovery rehearsal uses a separate clean installed 1.3.0 wheel environment
with the SDK-declared pytest-receptor 1.2.0 tools, exact original source and pinned
SDK. All frozen selected tests execute: 812 passed, one explicit Conda-record-only
skip, two documented source-version deselections. No optional SDK cases skip.
The shared before/after installed runtime checks and helper final byte/origin/
binding cleanup pass. Two original administrative imports attempted to insert
the runtime source root; the guarded list refuses those additions and records
the count. A first local rehearsal correctly rejected that path drift rather
than crediting the passing pytest line. Native Conda prefix/launcher and complete
same-file installed qualification remain separately required.

Newer qualification run 40144488087 at 18e620a passes Linux and macOS installed
cells, including original frozen tests, helper checks and final prefix/file
rechecks. Windows now passes setup but fails installing test tools because the
bootstrap Conda cannot find `share/conda-launchers/cli-64.exe` in its package
metadata. This matches upstream `conda/conda-launchers#35`: installer-created
paths_data can be empty even with original stub files present. No GHR archive
installation or installed-test success is credited for those Windows cells.

The next administrative correction re-installs only the runner base's
`conda-launchers` package with safety checks enabled, the upstream reported
repair. It does not patch metadata manually, disable safety checks, alter the
staged candidate or skip any installed gate. The setup/run-init correction,
original producer and exact file/digest remain unchanged. A new complete native
matrix is required before promotion; the original failed run remains evidence.


## Verified first delivery — 2026-10-24 local / 2026-10-25 UTC

The first public noarch file is delivered. Original source
`5a48759a399a17a16d923851b32519983a836f5f`, producer 40143062622 and the 78037-byte
`gh-run-receptor-1.3.0-py_0.tar.bz2` remain unchanged; SHA-256 is
`65f33b29dad70eb9e779f917e4c553d27effa4fddc2740a0260d259866746fd3`.
Installed run 40144989781, attempt 1, qualification workflow
`08b83a0e853aff5c563ad9b19d0ddffb15e030f8`, succeeds in all twelve native
Linux/macOS arm64/Windows × Python 3.11–3.14 cells. Every exact-file install,
prefix/resource check, original selected test suite and final provenance recheck
executes successfully. Digest-checked helper/source-binding artifacts retain
original-source hashes, zero test exit, two final helper checks and owned-binding
removal. Earlier failed runs remain separate evidence, not qualification.

Promotion 40145282787 independently revalidates exact-source gates and the installed
matrix, adds main to that same file without rebuilding, and verifies both public
label and solver index at 2026-10-25T00:06:03Z. A separate anonymous public-file
download matches original bytes/digest. A clean user installation from strict
uibcdf/conda-forge channels uses Python 3.14.9 and prefix-owned gh 2.103.2; runtime
source bytes, generated/distribution version, nine frozen schemas, fourteen corpus
replays, six original diagnostics in all renderers/profiles, active-job/unavailable
truth cases, bounded output, privacy and scratch cleanup pass outside source.

Durable receipts: `devguide/evidence/conda_1_3_0_qualification.json` and
`devguide/evidence/conda_1_3_0_public.json`. Normative route:
`devguide/versioning_and_releases.md`; regression guard:
`tests/test_conda_distribution.py`. The administrative helper compatibility route
remains explicitly owned/reviewed under central #144; it does not leave this
first-delivery issue incomplete. No PyPI publication or sibling pin change occurs.
The authoritative GitHub tag/release remains separately owned by #72.
