# Product, tooling and installed qualification

Owner: uibcdf/gh-run-receptor#76; shared provider/receiving:
uibcdf/molsyssuite#144. Native replacement receiving is complete in run 40935956394: twelve cells,
638 executed product/integration tests each, with the same original private file.
The [receiving receipt](evidence/issue_76_qualification.json) records the boundary.

## Physical and import boundary

Only `src/gh_run_receptor` enters the installed runtime. Setuptools discovers
packages under `src`, versioningit writes `src/gh_run_receptor/_version.py`, and
the nine schema resources retain their original bytes and installed names.
Python bounds, console entry point, dependency-free Python runtime and read-only
GitHub behavior are unchanged. The Git extension deliberately launches its own
`src` in a child environment; the Action explicitly selects its own `src`.
Normal development installs the package editable. A source checkout or editable
is not a release candidate.

Unshipped reusable operations live in `gh_run_receptor_tools`, outside the
runtime discovery tree. Normal module imports and the shared support @1 profile
replace generic `devtools`/`tests` imports. Schema assertion helpers also use this
namespace rather than importing another test module. Tools are not runtime
dependencies and cannot enter a wheel. An sdist may retain repository inputs;
its runtime files still map from `src` to the unchanged installed coordinates.
Archive verification retains support for immutable historical flat sdists.

## Explicit operations and compatibility commands

- Archive inspection takes archive path, independently established version and
  repository inventory explicitly. Frozen schemas compare their original Git
  paths with current `src` bytes; moving files never refreshes a frozen digest.
- Installed smoke takes source root and expected version; it checks actual
  prefix-owned commands, runtime/metadata/generated version and schema digests.
- Report parsing takes a report path; lifecycle/index validation takes the
  selected repository. An operation never walks from a staged helper's location.
- Bundle sanitizing, benchmarks, corpus validation and guide synchronization take
  their bundle/directory/manifest/repository/output inputs explicitly.
- `devtools/scripts/*.py` and the two top-level devtools commands remain thin
  compatibility CLIs. They supply checkout defaults explicitly while preserving
  caller-relative paths; only their namespaced tooling root is made visible.
  Since runtime code is under `src`, this cannot supply a source runtime to an
  installed test. Shared installed qualification does not use these CLI paths
  to bind support, and never adds the component/staging parent or `src` to paths.

Common support libraries were reviewed at this boundary: argument helpers here
are trusted administrative CLIs with bounded argparse inputs, not a new product
argument API; there is no optional backend, physical quantity or new runtime
diagnostic boundary requiring ArgDigest/DepDigest/PyUnitWizard/SMonitor. Existing
provider ownership and reassessment rules remain; no unused runtime dependency
is added. The independently reusable source-layout/local-file operation belongs
to MolSysSuite and is not copied into GHR.

## Complete execution scopes

`devtools/test_scopes.json` records the baseline source, every original function,
each original assertion/expression/digest, original function digest and
parameterization, reviewed scope/rationale, required native gates and current
home. The immutable baseline commit also retains subprocess assertion bodies. Product assertions describe installed API/CLI/resources. Tooling
assertions describe source tools/configuration. Integration assertions describe
repository operations consuming the actual product. Mixed assertions belong to
integration; classification is not inferred from a directory name alone.

`tests/conftest.py` marks every collected test from that exhaustive inventory.
An unknown function is a collection error. `gh_run_receptor_tools.test_inventory`
rejects missing/stale functions or removed assertions. These structural guards
do not prove scientific meaning: review and the recorded before/after mapping
remain required. Parameterized cases and all assertions are retained. All three
disjoint scopes must execute; deselection for one profile is not a waived gate.

The two source-version checks remain in the tooling scope and execute on every
source compatibility platform/minor. They explicitly identify their Git root.
Installed product tests exercise source-independent version parsing and actual
installed metadata/launchers separately. The Conda-record-only smoke test still
has its explicit source-run skip; it must execute against a real Conda candidate.

After changing assertions or parameterization, review their scope/meaning and
run `python -m gh_run_receptor_tools.test_inventory --root . --record-current`.
This preserves historical assertions and never invents classifications. New or
retired functions need an explicit reviewed inventory entry/disposition first.
The normal audit rejects altered expressions, removed assertions/cases and unknown
functions. Source-only workflow tools install the identified runtime explicitly;
they no longer depend on importing a flat checkout from the current directory.

Routine/source compatibility executes every scope. The private installed matrix
executes product and integration through the shared runner; repository tooling
has its separate native source evidence. Linux tooling execution alone never
certifies macOS/Windows integration. Existing internal checkpoint/full-CI policy
is unchanged; publication still requires all applicable exact-candidate gates.

## Supported shared composition

The resource inventory declares `source_root = "src"`, installed runtime roots,
the installed selection and literal hash-bound support files in the dedicated
namespace. The reviewed shared provider supplies source-resource mapping,
ephemeral version freezing, exact-file install/verification, loaded-root checks,
serial pytest and support @1 staging/cleanup. No GHR `sys.modules` binding or
source-root interception is needed by the replacement route.

`qualify-architecture.yml` is a manual, nonpublishing receiving experiment. The
committed `devtools/conda-build/qualification_plan.toml` identifies private placeholder
version 0.0.0/build 76; this selects no public version or tag and grants no upload
or promotion authority. It builds one Conda file, inspects its original digest,
then installs those same bytes on Linux/macOS arm64/Windows × Python 3.11–3.14.
The shared explicit local-file profile still solves ordinary public dependencies
and verifies local URI/coordinate/digest, prefix files/resources/runtime/launchers.
Receipts state `local-candidate`, never staged/public delivery.

Product source, build transformation/plan, original file/digest, tooling/support
source, workflow/attempt/job and provider commit remain distinct receipt fields.
Installed execution runs outside source with before/after provenance guards.
Support receipts preserve file hashes, loaded origins, test result and actual
retirement. Missing/tampered inputs, changed staged bytes, source substitution,
namespace collisions, abort and cleanup failures remain visible failures.

The maintained staged-file workflow calls the shared runner directly. The GHR
original-path adapter is retired after complete native replacement receiving.
Its two implementation-specific regression functions (sixteen cases) have an
explicit retired inventory, original assertions and per-case successor or
non-applicability rationale. The workflow-identity test moves to
`test_installed_qualification_workflow.py` and retains its applicable assertions.
Both original source-version checks remain active tooling. Historical 1.3.0
recovery is reproducible from qualification source 08b83a0; historical producers
retain their original tests/provider/profile and are not silently requalified by
current development inputs. Public 1.3.0 source, original Conda
file/hash, failed runs, qualification 08b83a0 and promotion are never rebuilt,
replaced or relabeled as this refactor. Shared acceptance and immutable consumer
handoff under #144 are required before coordinated closure.

Design references: [PyPA source layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/),
[pytest integration practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
and [pytest import modes](https://docs.pytest.org/en/stable/explanation/pythonpath.html).
