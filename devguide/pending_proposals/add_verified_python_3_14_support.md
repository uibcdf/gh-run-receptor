---
summary: Add verified Python 3.14 support
issue: uibcdf/gh-run-receptor#49
status: active
opened: 2026-09-20
closed:
verification: measured
area: [packaging, tests]
guard:
normative:
blocked_by: []
supersedes: []
---

# Add verified Python 3.14 support

**Reported:** 2026-09-20 during the progressive MolSysSuite Python 3.14 rollout tracked
by `uibcdf/molsyssuite#29`.
**Status:** Active. Linux source compatibility is measured; the public support contract,
hosted platform matrix, installed artifacts, and canonical client guide still stop at
Python 3.13.

## What

Extend gh-run-receptor's supported Python range from 3.11--3.13 to 3.11--3.14 without
weakening its stable 1.0 source-truth, security, serialization, installation, Action, or
GitHub CLI extension contracts.

This component is enabling infrastructure for the wider rollout: it must be able to
inspect the hosted evidence produced while other MolSysSuite libraries qualify Python
3.14. It may claim the wider range only after its own complete platform and packaging
gates pass and MolSysSuite records it as admitted.

## How

Use the phased transition in `uibcdf/molsyssuite#29`:

1. retain the clean Linux CPython 3.14 feasibility measurement below;
2. register the component as transition-authorized in the central suite registry;
3. align `requires-python`, the Python classifier, compatibility workflow, workflow
   contract tests, public documentation, canonical client guide, changelog, and release
   procedure;
4. pass the full suite, wheel and source build, isolated wheel installation, console
   command, and extension smoke tests on Ubuntu, macOS, and Windows for Python 3.14 while
   retaining the existing 3.11--3.13 matrix; and
5. record clean artifact evidence before changing the central state to admitted.

The package has no runtime Python dependencies. Development and test dependencies remain
part of the compatibility gate and cannot be inferred compatible from the dependency-free
runtime alone.

## Why

Leaving this developer tool capped below Python 3.14 would force agents and maintainers to
keep a separate interpreter solely to inspect the transition they are validating. Changing
metadata without the full gate would be worse: the composite Action and extension span
three operating systems and carry stable security and source-truth promises that a Linux
import alone cannot establish.

## What is measured and what is assumed

Measured on 2026-09-20 in a new Conda environment:

```text
CPython 3.14.7
pytest 9.1.1
pytest-xdist 3.8.0
pytest-receptor 1.1.0 from uibcdf/label/staging
python -m pytest -n 12 --receptor=llm
PASS exit=0 | 443 passed | 2.73s
```

The source was a clean local clone of commit `61d9a4e`. Installation used
`--ignore-requires-python` because the active metadata correctly still declares
`>=3.11,<3.14`. That override is feasibility scaffolding, not a user installation route or
support claim. The environment solved the current test dependencies on Python 3.14.

Assumed pending measurement: GitHub-hosted macOS and Windows runners can install the same
development dependencies and execute the existing complete compatibility contract under
Python 3.14. This must be replaced by hosted evidence.

## What was refuted

- A new Conda publication workflow is not required. The stable product deliberately makes
  no Conda or PyPI distribution promise; it ships GitHub Release wheel/sdist assets, a
  GitHub CLI extension, a composite Action, and a reusable workflow.
- Runtime dependency freedom is not sufficient evidence. The development dependencies,
  console entry point, wheel, extension, and operating-system matrix still require tests.
- The suite-wide default must not be changed merely because this component succeeds. The
  central transition admits components individually.

## Scope and exclusions

This proposal widens only Python interpreter support. It does not change serialized v1
contracts, GitHub CLI requirements, supported GitHub hosts, workflow selection, profiles,
permissions, release publication authority, or the stable read-only product boundary. It
does not publish a release, tag, package-index artifact, or Conda artifact.

Historical release measurements remain true for the versions they describe and are not
rewritten. Current normative and public surfaces will describe the new range after the
gates pass.

## Acceptance criteria

- Metadata and documentation agree on `>=3.11,<3.15` and Python 3.11--3.14.
- The compatibility workflow covers all twelve operating-system/interpreter pairs.
- Every pair runs the complete suite, builds the distributions, installs the wheel, and
  invokes the installed command outside the checkout.
- A clean Python 3.14 artifact installation reports the expected version and imports from
  the isolated installation rather than the checkout.
- Existing Python 3.11 support and all nine serialized contract freezes remain intact.
- The canonical client guide and every synchronized copy are updated only after the new
  support claim is measured.
- MolSysSuite changes the component transition state from authorized to admitted only
  after all component gates agree.

## Dependencies and risks

The policy dependency is `uibcdf/molsyssuite#29`. The principal risk is a hosted
operating-system or test dependency that does not yet support 3.14. A failed matrix cell
is compatibility evidence and must not be bypassed or converted into a support claim.

## Provenance

Linux x86-64, Conda 26.5.3, CPython 3.14.7, pytest 9.1.1, pytest-xdist 3.8.0,
pytest-receptor 1.1.0, and gh-run-receptor commit `61d9a4e`, measured 2026-09-20. The
temporary clone and environment contain no release artifact and are not retained as
project evidence.
