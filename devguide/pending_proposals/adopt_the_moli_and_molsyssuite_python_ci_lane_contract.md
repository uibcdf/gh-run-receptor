---
summary: Adopt the MOLI and MolSysSuite Python CI lane contract
issue: uibcdf/gh-run-receptor#52
status: open
opened: 2026-09-23
closed:
verification: inspected
area: [tests, governance]
guard:
normative:
blocked_by: []
supersedes: []
---

# Adopt the MOLI and MolSysSuite Python CI lane contract

**Reported:** 2026-09-23 during the `uibcdf/molsyssuite#39` member inventory.
**Status:** Open; the local workflow design and hosted validation are pending.

## What

Give GH Run Receptor the routine and full-matrix test evidence required by the
inherited MOLI Python CI baseline and the accepted MolSysSuite adoption profile.
The effective supported range for this component is Python 3.11 through 3.14.

## How

1. Add a gating Linux Python 3.13 package-test lane on every push and pull
   request. Use the complete required suite unless a measured cost justifies a
   bounded smoke lane with its omitted coverage and full-suite counterpart
   recorded here.
2. Add a gating Linux matrix running the complete required suite on Python
   3.11, 3.12, 3.13, and 3.14 at least weekly, with manual dispatch for
   candidate verification. Stagger the schedule with other suite members.
3. Preserve the purpose of the existing dispatch-only `compatibility.yml`,
   which also builds and installs artifacts on three operating systems, unless
   a reviewed local decision explicitly changes its contract. A separate
   routine/weekly workflow is one viable route.
4. Review the repository's macOS and Windows support claims against the
   accepted platform-evidence rule. Record representative gating and regular
   full-range evidence for each claimed platform, or a tracked exception with
   its removal condition.
5. Manually dispatch every newly scheduled matrix before counting it as
   evidence. Before a release, inspect a green full matrix on the exact
   candidate commit, including job and step conclusions.

## Why

The current `compatibility.yml` runs only through `workflow_dispatch`, and
`tests/test_compatibility_workflow.py` explicitly protects that boundary. The
other push and pull-request workflows do not provide a direct package-suite
pytest lane. A manually dispatched compatibility run therefore cannot provide
routine push/PR evidence or recurring supported-minor evidence. The common
suite checker has not yet enforced the accepted target; its current green
result does not establish CI-lane conformance.

## What is measured and what is assumed

Inspected on 2026-09-23:

- `pyproject.toml` declares `requires-python = ">=3.11,<3.15"`.
- `.github/workflows/compatibility.yml` declares only
  `workflow_dispatch`, a 12-cell Ubuntu/macOS/Windows by Python 3.11-3.14
  matrix, and `python -m pytest --receptor=llm` in each cell.
- `tests/test_compatibility_workflow.py` asserts the absence of push,
  pull-request, and schedule triggers from that workflow.
- From MolSysSuite, `python devtools/scripts/ci_lane_inventory.py ..
  --repository uibcdf/gh-run-receptor --json` found no direct Linux Python
  3.13 pytest candidate on push or pull request and no scheduled matrix.

These are configuration observations, not hosted run results or a finding
that any published artifact fails on a supported interpreter. The cost of a
routine full suite and the exact non-Linux platform claims require local
review before choosing the final workflow topology.

## What was refuted

- Treating the existing manual compatibility matrix as weekly evidence:
  it has no schedule and a configured dispatch is not an executed result.
- Counting the policy workflow or documentation workflow as a package test:
  neither runs the required package pytest suite on push and pull request.
- Changing the suite-wide target inside this repository: MOLI owns the
  baseline and MolSysSuite owns its member adoption profile.

## Scope and exclusions

This report concerns GH Run Receptor's CI topology and evidence. It does not
change product behavior, Python admission, package publication, the shared
MOLI baseline, or the MolSysSuite policy gate. Those authorities remain with
their owning repositories.

## Acceptance criteria

- Gating Linux Python 3.13 package tests run on push and pull request without
  an unreviewed path, ref, condition, or tolerated-failure bypass.
- At least weekly, a gating Linux matrix runs the complete required suite on
  Python 3.11, 3.12, 3.13, and 3.14; manual dispatch is available.
- The first manual dispatch of the new schedule passes, and the report names
  its commit, run, and conclusions. Release preparation uses a green full
  matrix for the exact candidate commit.
- Claimed non-Linux support has the required recurring evidence or a tracked,
  bounded exception.
- Local workflow checks and the MolSysSuite inventory agree on the configured
  lanes. Hosted evidence, rather than YAML alone, supports completion.

## Dependencies and risks

The suite-wide rollout is tracked by `uibcdf/molsyssuite#39`; it is a related
decision, not a blocker. New runner cost and test-environment availability
must be measured before selecting the final matrix. Keep the existing manual
compatibility validation until its release and artifact checks have an
explicit replacement.

## Provenance

Source and workflow inspection on 2026-09-23 in the local Linux checkout;
the MolSysSuite inventory ran under the Python 3.13 development environment.
No hosted run outcome is claimed in this opening report.

## Implementation checkpoint (2026-09-23)

The component now has separate routine and weekly workflows. `python-routine.yml`
runs the complete package suite on Linux Python 3.13 for every push and pull request.
`python-weekly.yml` runs the complete suite on Python 3.11–3.14 across Linux, macOS,
and Windows each Tuesday at 05:17 UTC and allows manual dispatch. The existing
manual compatibility workflow remains unchanged, including its build and installed
command smoke tests. The MolSysSuite policy caller now pins `policy-v1.4.9`.

Local `python -m pytest --receptor=llm` passed 453 tests; Ruff lint and format passed.
The MolSysSuite repository checker passed, and its CI lane inventory detected the
routine push and pull-request jobs and all 12 scheduled and dispatch matrix cells
as gating test lanes. Hosted results and the first manual weekly dispatch remain
required before this issue can be closed.
