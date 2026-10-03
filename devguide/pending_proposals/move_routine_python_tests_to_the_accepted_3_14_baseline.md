---
summary: Move routine package tests to the accepted Python 3.14 baseline.
issue: uibcdf/gh-run-receptor#58
status: active
opened: 2026-10-03
closed:
verification: inspected
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

Local and hosted verification will be recorded before closure. Source-level
configuration alone is not passing hosted evidence.
