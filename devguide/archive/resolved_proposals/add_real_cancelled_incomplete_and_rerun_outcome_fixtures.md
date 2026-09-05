---
summary: Add real cancelled incomplete and rerun outcome fixtures
issue: uibcdf/gh-run-receptor#13
status: resolved
opened: 2026-09-05
closed: 2026-09-05
verification: measured
area: ['github', 'reports', 'tests']
guard: tests/test_contracts.py
normative:
blocked_by: []
supersedes: []
---

# Add real cancelled, incomplete, and rerun outcome fixtures

**Reported:** 2026-09-05, as the first post-0.8.0 corpus milestone.
**Status:** Resolved; four public attempt captures are sanitized, reviewed, and tested.

## What

Add sanitized fixtures for:

- cancelled MolSysMT Conda run `33636046706`, attempt 1;
- PyUnitWizard CI run `19058199598`, attempt 1, whose retained logs return HTTP 410;
- failed ArgDigest run `22638022385`, attempt 1;
- successful rerun of the same ArgDigest run, attempt 2.

## How

Capture each attempt separately, sanitize to the structured facts needed by report and
schema tests, and catalog the exact public identity, expected official conclusion,
assessment, reason, and removed fields. Keep the incomplete capture's warning and
manifest completeness false. Assert the two ArgDigest attempts together so a future test
cannot pass merely by validating each fixture without comparing their shared run identity.

The new evidence exposed and depends on corrections for `uibcdf/gh-run-receptor#11` and
`uibcdf/gh-run-receptor#12`; those remain separate defect records.

## Why

All previous committed real captures are attempt 1 and complete metadata reductions with
successful or failed run conclusions. Stable attempt and degraded-evidence semantics
cannot be claimed from that corpus. These cases exercise exit codes 0, 1, 2, and 4 across
one coherent outcome increment.

## What is measured and what is assumed

GitHub's attempt endpoints report ArgDigest attempt 1 as `failure` and attempt 2 as
`success`, at the same run ID and head SHA. The MolSysMT source run reports `cancelled`
with 7 successful, 3 failed, and 7 cancelled jobs. The PyUnitWizard adaptive capture
preserves six failed jobs but cannot retrieve logs because GitHub returns HTTP 410.

The cases were observed with filtered `gh run list`, `gh api` attempt endpoints, and:

```text
gh run-receptor inspect RUN_ID --repo OWNER/REPO --attempt N --capture metadata
gh run-receptor inspect 19058199598 --repo uibcdf/pyunitwizard --capture adaptive
```

## What was refuted

- Synthetic-only state coverage is rejected because it cannot expose upstream endpoint,
  retention, and attempt-association behavior.
- Committing raw bundles is rejected because they contain fields unrelated to the tests
  and create avoidable privacy and maintenance cost.
- Treating expired logs as a generic failure is rejected because the report must separate
  GitHub's failed run from receptor evidence incompleteness.
- Storing only the latest rerun attempt is rejected because it cannot guard against
  cross-attempt source mixing.

## Scope and exclusions

This slice does not add attempt comparison, timed-out or restricted-token fixtures, live
active transitions, or real Zenodo evidence. It does not infer causes from unavailable
logs.

## Acceptance criteria

- Every fixture passes bundle, model, and report schemas and replays deterministically.
- Official conclusions and receptor assessments are respectively cancelled/CANCELLED,
  failure/INCOMPLETE, failure/FAIL, and success/PASS.
- Exit codes are respectively 2, 4, 1, and 0.
- The cancelled matrix retains successful, failed, and cancelled platform states.
- The incomplete fixture retains the unavailable-log warning without any raw log.
- The rerun fixtures share run ID and head SHA but retain distinct attempt and conclusion.
- Sanitization metadata documents what was retained and removed.

## Dependencies and risks

Corrections tracked by `uibcdf/gh-run-receptor#11` and
`uibcdf/gh-run-receptor#12` are implemented in the same release increment. There is no
external blocker.

## Provenance

Linux host, Python 3.13.14, gh-run-receptor source after 0.8.0, GitHub API version
`2022-11-28`, 2026-09-05. All selected runs are public UIBCDF repository evidence.

## Resolution

All four captures are catalogued with explicit sanitization and retention metadata. They
cross the bundle, normalized-model, and report schemas and jointly assert assessments and
exit statuses 0, 1, 2, and 4. The paired ArgDigest fixtures additionally enforce shared
run/SHA identity with distinct attempt conclusions.
