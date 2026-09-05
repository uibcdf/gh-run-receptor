---
summary: Historical attempt capture mixes source facts and can report false PASS
issue: uibcdf/gh-run-receptor#11
status: resolved
opened: 2026-09-05
closed: 2026-09-05
severity: critical
verification: measured
area: ['github', 'reports', 'tests']
guard: tests/test_bundle.py
normative:
blocked_by: []
supersedes: []
---

# Historical attempt capture mixes source facts and can report false PASS

**Reported:** 2026-09-05, while adding real rerun-attempt evidence after 0.8.0.
**Status:** Resolved and verified against a public ArgDigest rerun.

## What

ArgDigest run `22638022385` has a failed attempt 1 and successful attempt 2. Requesting
attempt 1 with gh-run-receptor 0.8.0 returns `PASS conclusion=success` while also reporting
`jobs=0/1` because the single historical job failed:

```text
gh run-receptor inspect 22638022385 --repo uibcdf/argdigest \
  --attempt 1 --capture metadata --receptor=llm
```

## How

The CLI fetches the generic workflow-run endpoint to learn the current attempt. Bundle
capture writes that current response directly to `run.json`, even when `--attempt` selects
an older attempt. Jobs and logs do use attempt-specific endpoints. The resulting bundle
therefore mixes the successful attempt 2 run conclusion with failed attempt 1 jobs.

Bundle validation checks member digests but does not compare the manifest's
`run_attempt` with the attempt recorded by `run.json`, so the contradiction survives
replay.

## Why

This produces a false `PASS`, violates exact GitHub conclusion parity, and can cause an
agent or release process to accept a failed historical attempt. The defect crosses the
project's primary truth and attempt-identity boundaries, so its severity is critical.

## What is measured and what is assumed

The GitHub API returned `failure` for attempt 1 and `success` for attempt 2, both at head
SHA `536ae4f6f191ff5e9a4449c81d3847ca90daa460`. Attempt-specific job endpoints returned
one failed job and one successful job respectively. The reproduction above returned
`PASS conclusion=success | profile=generic | jobs=0/1` for attempt 1.

The source facts were checked with:

```text
gh api repos/uibcdf/argdigest/actions/runs/22638022385/attempts/1
gh api repos/uibcdf/argdigest/actions/runs/22638022385/attempts/2
```

## What was refuted

- Deriving run conclusion from jobs is rejected because GitHub's attempt-specific run
  response is authoritative and jobs need not encode every run-level outcome.
- Merely changing the renderer is rejected because the captured source bundle itself is
  internally inconsistent.
- Accepting old mixed bundles is rejected because a compatibility path may never turn
  contradictory evidence into success.

## Scope and exclusions

The fix does not implement attempt comparison or mutation. It only ensures that capture,
validation, watch snapshots, and replay preserve one selected attempt consistently.

## Acceptance criteria

- Explicit historical capture fetches the attempt-specific run endpoint before writing
  `run.json`.
- The manifest, run response, jobs, logs, head SHA, and rendered conclusion all identify
  the selected attempt.
- Bundle loading rejects a mismatch between manifest and `run.json` attempt identities.
- Attempt 1 of the sanitized fixture reports `FAIL`; attempt 2 reports `PASS`.
- Existing current-attempt capture and replay behavior remains unchanged.

## Dependencies and risks

There is no blocker. Existing cached 0.8.0 bundles with mixed identities must fail closed;
automatic deletion or silent repair would hide provenance and is out of scope.

## Provenance

Linux host, Python 3.13.14, gh-run-receptor 0.8.0, GitHub API version `2022-11-28`,
2026-09-05. Public evidence: `uibcdf/argdigest` run `22638022385`, attempts 1 and 2.

## Resolution

Historical capture and watch fetch the attempt-specific run response and validate the
selected attempt before consuming it. Bundle loading validates retained run ID, attempt,
and head SHA against the manifest. Paired real fixtures prove that attempt 1 remains
`FAIL` and attempt 2 remains `PASS` at the shared run ID and SHA.
