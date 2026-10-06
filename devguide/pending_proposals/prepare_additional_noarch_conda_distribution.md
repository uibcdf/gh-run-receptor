---
summary: Prepare an additional noarch Python Conda distribution with exact-file gates.
issue: uibcdf/gh-run-receptor#60
status: partial
opened: 2026-10-06
closed:
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

[The recipe handoff](../../devtools/conda-build/README.md) owns the operational
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
The [sanitized preparation receipt](../evidence/conda_route_preparation_2026-10-06.json)
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
