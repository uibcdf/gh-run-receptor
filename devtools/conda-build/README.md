# Additional noarch Python Conda route

Owner: uibcdf/gh-run-receptor#60. Shared contract: uibcdf/molsyssuite#45 and
MolSysSuite `devguide/noarch_conda_workflow.md` at the immutable provider commit
in `devtools/dependency_routes.toml`.

## Current scope

This is a prepared, additive route. GitHub extension, Action, wheel/sdist and
Zenodo modes remain. No Conda package, credential access or PyPI publication is
claimed. `release_plan.example.toml` is an onboarding context, **not a release
plan**. Publication and promotion require a separately reviewed, committed
`release_plan.toml`; the example cannot authorize them.

The package is pure Python with architecture-independent JSON schemas. It uses
`noarch: python`, generated `_version.py`, the declared console entry point,
Python >=3.11,<3.15 and all nine frozen schema files. GitHub CLI is an external
native dependency (`gh>=2.48.0`), supplied separately by conda-forge. Native
executables are not bundled in this package. Conda does not register a `gh`
extension automatically; invoke `gh-run-receptor` directly, or keep the existing
explicit extension installation as a separate mode. The existing GitHub CLI
still owns authentication; installation and tests do not authenticate or call
GitHub APIs.

## Local input review

Use the qualified Python 3.14 workspace and a clean checkout of the **full SDK
commit** in `devtools/dependency_routes.toml`:

```text
python devtools/check_distribution_inputs.py --suite-root /path/to/pinned/molsyssuite
```

The member wrapper calls the maintained suite route/resource/recipe operations,
checks actual installed public Python bounds, compares external gh to the
acquisition adapter's real floor, and validates the nine schemas against their
original frozen tags and digest inventory. It reviews all discovered workflows;
new or changed workflows require a substantive route review before refreshing
an inventory hash. Test/development Jinja2 and packaging extras are tools, not
Python runtime dependencies. There are no required Python sibling source routes
and no Conda runtime/development environment files to classify.

## First release handoff

1. The owner chooses an unused version/build and commits a real release plan
   from the example, with maintainer/date, reason and required exact-source
   job/step profiles. Never reuse public file coordinates or move tags. The
   example recipe context remains a static onboarding review; the candidate
   wrapper and shared publisher additionally inspect the **real** plan.
2. Verify the actual secret mapping `ANACONDA_UIBCDF_TOKEN` is available to the
   authorized route. Its name in a workflow does not prove access. Do not echo
   tokens, create another authentication system or weaken missing gates.
3. Execute required candidate evidence: routine suite, twelve source
   compatibility cells, suite policy, frozen contracts, strict documentation
   build and Conda governance. Feature-specific existing release gates remain
   owner-controlled additions to the plan. A skip marker does not waive a gate;
   authorized manual exact-candidate recovery is still possible. Ordinary
   internal push/PR/checkpoint rules remain.
4. Dispatch `stage-conda.yml` with the full candidate SHA and matching version.
   It reviews member inputs, then the pinned shared workflow verifies native
   gates, freezes metadata only in its ephemeral checkout, builds **once**, runs
   recipe tests, inspects that archive and uploads it to staging. Save original
   producer run, SHA, filename and SHA-256. No automatic push/tag Conda upload.
5. Dispatch `test-staged-conda.yml` with that original SHA, file and digest.
   It uses twelve cells: Linux, macOS arm64 and Windows × Python 3.11–3.14.
   Each solves public dependencies, installs those exact bytes outside source,
   checks provenance/version/resources, runs the declared installed suite and
   rechecks provenance. Test tools follow the pinned shared workflow (currently
   pytest-receptor 1.2.0) with committed `jsonschema>=4.23,<5`; ordinary source
   tests retain their existing pytest-receptor 1.1.0 pin.
6. After all cells succeed, dispatch `promote-conda.yml` with the original source,
   version, digest and successful installed run ID. It revalidates gates and
   adds `main` to the same staged file, then independently verifies the public
   label and solver index. It never rebuilds or replaces bytes.
7. Save source, producer, installed and public receipts separately; only then
   advertise a public Conda installation command and record actual delivery evidence.

The installed selection keeps all package/runtime tests and administrative
checks. Two functions in `tests/test_source_version.py` are explicitly deselected:
`test_repository_checkout_has_a_source_version` and
`test_source_launcher_does_not_borrow_installed_distribution_version`. They test
unbuilt Git extension source/tag discovery, not the installed Conda payload, and
remain mandatory in the full source compatibility gate. The pure parsing tests
stay selected. CLI subprocess tests use Python safe-path mode to prevent the
source cwd from replacing the installed package. The installed-only guard in
`tests/test_conda_distribution.py` independently verifies prefix-owned `gh` and
`gh-run-receptor` commands, the adapter's functional gh floor, generated and
metadata versions, and exact frozen schema digests. Source-only execution
explicitly skips this guard when no Conda package record exists.

A reviewed administrative correction may run installed validation from a newer
workflow ref. Keep `candidate_sha` bound to the original producer; use the
promotion workflow's separate `qualification_sha` only for the reviewed workflow
identity, retaining the source-binding receipts. Never replace the producer SHA
with the correction SHA or reconstruct a registered archive to obtain green.

## Evidence limits

Dependency probes on Python 3.14 resolved bootstrap tools and gh on linux-64,
osx-arm64 and win-64; the cross-solve declared macOS 14.0's virtual package.
These were solver dry runs, not native package installations. All public
GitHub 1.2.0 files and their original evidence remain untouched. Installed Conda
qualification, first authorized delivery and independently verified public
poststate are pending and owned by uibcdf/gh-run-receptor#60.


## Governance and first delivery — 2026-10-09

Governance adoption under uibcdf/molsyssuite#45 precedes the first release:
CI/recipe are ready and Conda publication access remains explicitly unknown.
uibcdf/gh-run-receptor#60 stays open for the actual developer-owned delivery
above, including candidate-specific source gates and all twelve exact-file
installed cells. Source/control acceptance does not permit a public Conda
installation claim. Version, plan, credential confirmation and timing remain
with the developer. Existing provider pins and original artifact evidence retain
their own scope.
