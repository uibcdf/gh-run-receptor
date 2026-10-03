---
summary: Move routine package tests to the accepted Python 3.14 baseline.
issue: uibcdf/gh-run-receptor#58
status: resolved
opened: 2026-10-03
closed: 2026-10-03
verification: measured
area: [governance]
guard: tests/test_python_ci_lanes.py
normative:
blocked_by: []
supersedes: []
---

# Python 3.14 routine baseline

## What

The routine Linux package suite uses Python 3.13. MolSysSuite now requires
Python 3.14 for routine development and push/PR tests under
uibcdf/molsyssuite#39 and the published immutable policy-v1.5.4.

## How

Change only the routine package-test interpreter and existing assertion,
adopt the published caller and synchronize the canonical guide through the
suite tool. Preserve the twelve-cell weekly Linux/macOS/Windows matrix on
Python 3.11–3.14, its manual dispatch, and separate compatibility workflows.
The default-branch coverage producer remains part of the routine test job;
its independent publisher still waits for those tests and cannot run on PRs.

## Why

The routine gate must exercise the accepted development interpreter without
losing compatibility evidence for earlier supported minors. This migration
neither publishes a package nor changes released action behavior.

## Acceptance criteria

- The existing routine lane guard requires Python 3.14 and passes.
- Exact-source hosted routine and policy checks pass.
- Older minors remain in the required weekly matrix.

## Evidence

At exact source 5da9bc2, hosted routine run
[37122879093](https://github.com/uibcdf/gh-run-receptor/actions/runs/37122879093)
passes the complete package suite on Python 3.14.7 and its independent
default-branch coverage publisher. Policy run
[37122877185](https://github.com/uibcdf/gh-run-receptor/actions/runs/37122877185)
passes the immutable 1.5.4 gate on the same source. The first routine run
37122618885 failed because the packaging guard still expected 1.5.2; the
corrected guard expects 1.5.4. The failed receipt is retained, not renamed green.

Five focused local lane/packaging tests pass. The existing lane guard asserts
the actual routine setup interpreter, unfiltered push/PR/manual events and
gating package-suite command. It also protects all twelve weekly cells and
coverage publisher permissions/ordering. Reverting the routine interpreter to
3.13 violates that assertion. The weekly workflow is unchanged; no new weekly
execution, platform certification or package publication is claimed.
