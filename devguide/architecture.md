# Architecture

## Evidence pipeline

The system is divided into five stages:

```text
GitHub API and logs
        |
        v
capture -> normalize -> classify -> render -> publish
   |          |            |          |          |
 bundle    event model   profile    llm/json   stdout,
                                                 summary,
                                                 artifact
```

Capture, normalization, and rendering belong to the shared core. The CLI, GitHub Action,
and reusable workflow are adapters around that core.

## Evidence bundle

GitHub does not expose one complete run document. A full capture therefore stores the
separate resources with a manifest:

```text
run-<id>-attempt-<n>/
├── manifest.json
├── run.json
├── workflow.json
├── jobs.json
├── checks.json
├── artifacts.json
├── logs.zip
└── receptor-report.json
```

The manifest records the repository, run and attempt identifiers, head commit, API
version, capture time, receptor version, and SHA-256 digest of every member. Original
responses are immutable within a bundle. Derived reports are replaceable and identify
the receptor version that produced them.

Raw bundles may contain sensitive data and must be owner-readable, excluded from source
control by default, and subject to an explicit retention policy.

## Capture policies

- `full`: capture all structured resources and the complete log archive.
- `adaptive`: capture all structured resources and fetch logs only for failed or
  otherwise unresolved jobs.
- `metadata`: capture structured resources without logs.

The development default is `full` because it supports differential testing and offline
replay. The intended stable default is `adaptive`. A successful report should normally
require no full-log download.

## Normalized model

The normalized model must represent:

- repository, workflow path and ID;
- run number, run attempt, event, ref, and head SHA;
- run status and conclusion;
- jobs, matrix identities, dependencies, timestamps, and conclusions;
- steps, outcomes, conclusions, and durations;
- checks and annotations;
- artifact names, sizes, digests, expiration, and availability;
- causal evidence extracted from logs with provenance;
- receptor observations, profile interpretations, and confidence kept as distinct
  fields.

The model requires a versioned serialization contract. Source facts must never be
overwritten by profile conclusions.

## Output channels

The same report can be rendered to:

- compact stdout for an agent;
- JSON for automation and replay;
- Markdown through `GITHUB_STEP_SUMMARY`;
- a small `gh-run-receptor-report.json` workflow artifact.

The compact renderer prints one verdict, the minimum useful matrix summary, distinct
causes, evidence locations, and suggested read-only follow-up or rerun commands. It does
not stream unchanged polling snapshots.

## Embedded reporting

A final reporting job should declare `if: always()` and depend on all primary jobs. This
makes completed job evidence available before aggregation. The reporter must ignore its
own job to avoid circular interpretation.

The embedded reporter is observability rather than a gate. Failure to render produces a
visible `RECEPTOR_ERROR` but must not convert successful primary work into a false
product failure. Cancellation may prevent the reporting job from running, so the
external CLI remains the universal fallback.

## Trust boundaries

- API metadata is authoritative for status and conclusion.
- Logs and artifact contents are untrusted input.
- Control characters and terminal escapes are neutralized before rendering.
- Recognizable credential shapes are redacted from rendered and derived evidence.
- Rules are data, not executable code.
- Configuration obtained from an untrusted pull-request checkout is not automatically
  granted authority over reporting behavior.
- Network, parser, and profile failures are explicit and never collapse to success.

## Open architectural questions

- Whether the shared core should initially be distributed as Python or as a standalone
  cross-platform executable.
- Whether check-run annotations add enough value to justify write permissions.
- How much log evidence can be normalized portably when GitHub cannot associate a line
  with a specific step.
- Whether embedded producers should emit a standard `gh-run-receptor.events@1` stream
  in addition to the final report.

